#!/usr/bin/env python
"""
rejudge_mt_bench.py — MT-Bench-HU judge újrafuttatás több baseline-zsal.

A régi baseline (deepseek-v4-flash) MMLU-HU 52% — túl gyenge, mindenki nyer ellene.
Ez a script:
  1. A meglévő mt_bench_hu_results.jsonl-t használja (modell válaszai).
  2. Több baseline modell válaszait gyűjti össze (a meglévő baseline JSONL-ekből, vagy generálja).
  3. Minden baseline-zsal GSB pontozást végez (gemini-3-flash-preview bíróval).
  4. A végső win rate = átlagos win rate az összes baseline-ra.
  5. A meglévő mt_bench_hu_judged.jsonl-t kiegészíti VAGY felülírja.

Használat:
  python scripts/rejudge_mt_bench.py                              # minden modell × mód
  python scripts/rejudge_mt_bench.py qwen3.5-cloud-nothink        # egy modell
  python scripts/rejudge_mt_bench.py --baselines deepseek-v4-pro:cloud minimax-m3:cloud
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from stop_on_error import call_ollama_strict, OllamaFatalError
from judge_mt_bench import gsb_judge, generate_baseline, JUDGE_MODEL

ROOT = Path(__file__).parent.parent
DEFAULT_RESULTS_DIR = ROOT / "results"
QUESTIONS_PATH = ROOT / "data" / "mt_bench_hu" / "questions.jsonl"
LOG_PATH = ROOT / "logs" / "mt_bench_rejudge.log"

DEFAULT_BASELINES = [
    "deepseek-v4-flash:cloud",
    "deepseek-v4-pro:cloud",
    "kimi-k2.6:cloud",
]

N_WORKERS = 4


def load_questions() -> list[dict]:
    if not QUESTIONS_PATH.exists():
        return []
    return [json.loads(l) for l in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()]


def get_baseline_responses(baseline_model: str, mode: str, results_dir: Path,
                            questions: list[dict]) -> dict[str, dict]:
    model_safe = baseline_model.replace(":", "-").replace("/", "-") + f"-{mode}"
    bl_path = results_dir / model_safe / "mt_bench_hu_baseline.jsonl"
    if bl_path.exists():
        return {b["id"]: b for b in
                (json.loads(l) for l in bl_path.read_text(encoding="utf-8").splitlines())}
    print(f"   Baseline generálás: {baseline_model} ({mode})")
    generated = generate_baseline(baseline_model, mode, questions, results_dir)
    if not generated:
        return {}
    return {b["id"]: b for b in generated}


def judge_item(item: dict, baseline: dict[str, dict]) -> dict | None:
    base = baseline.get(item["id"])
    if not base:
        return None
    gsb1 = gsb_judge(item["turn1_prompt"], item["turn1_response"],
                     base.get("turn1_response", ""))
    time.sleep(0.05)
    gsb2 = gsb_judge(item["turn2_followup"], item["turn2_response"],
                     base.get("turn2_response", ""))
    time.sleep(0.05)
    gsb1s = gsb_judge(item["turn1_prompt"], item["turn1_response"],
                      base.get("turn1_response", ""), swap=True)
    time.sleep(0.05)
    gsb2s = gsb_judge(item["turn2_followup"], item["turn2_response"],
                      base.get("turn2_response", ""), swap=True)
    time.sleep(0.05)

    def resolve(a, b):
        if a is None or b is None:
            return None
        if a == b:
            return a
        return "S"

    return {
        "id": item["id"],
        "turn1_gsb": resolve(gsb1, gsb1s),
        "turn2_gsb": resolve(gsb2, gsb2s),
    }


def judge_one_model(model_safe: str, results_dir: Path, mode: str,
                    baselines: list[str], verbose: bool) -> dict:
    res_path = results_dir / model_safe / "mt_bench_hu_results.jsonl"
    jud_path = results_dir / model_safe / "mt_bench_hu_judged.jsonl"
    if not res_path.exists():
        return {"model": model_safe, "status": "NO_RESULTS"}

    items = [json.loads(l) for l in res_path.read_text(encoding="utf-8").splitlines()]
    questions = load_questions()
    if not questions:
        return {"model": model_safe, "status": "NO_QUESTIONS"}

    print(f"  {model_safe}: {len(items)} item × {len(baselines)} baseline")

    per_baseline = []
    from concurrent.futures import ThreadPoolExecutor, as_completed
    for bl in baselines:
        baseline_map = get_baseline_responses(bl, mode, results_dir, questions)
        if not baseline_map:
            print(f"    ⚠️  Baseline nem elérhető: {bl}")
            continue
        results = []
        n_workers = min(N_WORKERS, len(items)) if items else 1
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {ex.submit(judge_item, it, baseline_map): it for it in items}
            done_count = 0
            for fut in as_completed(futures):
                r = fut.result()
                if r:
                    results.append(r)
                done_count += 1
                if verbose and done_count % 5 == 0:
                    print(f"      [{bl}] {done_count}/{len(items)}")
        per_baseline.append({"baseline": bl, "results": results})

    if not per_baseline:
        return {"model": model_safe, "status": "NO_BASELINES"}

    by_id: dict[str, dict] = {}
    for pb in per_baseline:
        for r in pb["results"]:
            rid = r["id"]
            if rid not in by_id:
                by_id[rid] = {"id": rid, "by_baseline": {}}
            by_id[rid]["by_baseline"][pb["baseline"]] = {
                "turn1": r["turn1_gsb"],
                "turn2": r["turn2_gsb"],
            }

    def score_one(j: dict) -> tuple[int, int, int, float]:
        wins = losses = ties = 0
        scores = []
        for bl, t in j["by_baseline"].items():
            t1, t2 = t["turn1"], t["turn2"]
            if t1 is None or t2 is None:
                continue
            if t1 == "A" and t2 == "A":
                wins += 1
                scores.append(1.0)
            elif t1 == "B" and t2 == "B":
                losses += 1
                scores.append(0.0)
            else:
                ties += 1
                scores.append(0.5)
        s = (sum(scores) / len(scores)) if scores else 0.5
        return wins, losses, ties, s

    all_judged = list(by_id.values())
    total_w = total_l = total_t = 0
    win_rate_sum = 0.0
    for j in all_judged:
        w, l, t, s = score_one(j)
        total_w += w
        total_l += l
        total_t += t
        win_rate_sum += s
    avg_win_rate = (win_rate_sum / len(all_judged)) if all_judged else 0.5
    decided = total_w + total_l
    strict_win_rate = (total_w / decided) if decided else 0.5

    with jud_path.open("w", encoding="utf-8") as f:
        for j in all_judged:
            w, l, t, s = score_one(j)
            j_out = {
                "id": j["id"],
                "by_baseline": j["by_baseline"],
                "wins": w, "losses": l, "ties": t,
                "score": round(s, 4),
            }
            f.write(json.dumps(j_out, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

    summary = {
        "model": model_safe,
        "benchmark": "mt_bench_hu",
        "judge_model": JUDGE_MODEL,
        "baselines": [pb["baseline"] for pb in per_baseline],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_judged": len(all_judged),
        "score": round(avg_win_rate, 4),
        "score_strict": round(strict_win_rate, 4),
        "wins": total_w, "losses": total_l, "ties": total_t,
    }
    sum_path = results_dir / model_safe / "mt_bench_hu_summary.json"
    sum_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} | {model_safe} | mt_bench_rejudge | "
                f"baselines={len(per_baseline)} | judged={len(all_judged)} | "
                f"avg_score={avg_win_rate:.4f} | strict={strict_win_rate:.4f}\n")

    return {
        "model": model_safe,
        "status": "OK",
        "judged": len(all_judged),
        "baselines": len(per_baseline),
        "avg_score": round(avg_win_rate, 4),
        "strict": round(strict_win_rate, 4),
        "wins": total_w, "losses": total_l, "ties": total_t,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("models", nargs="*", help="model_safe (alapért: mind)")
    p.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    p.add_argument("--baselines", nargs="*", default=DEFAULT_BASELINES)
    p.add_argument("--mode", choices=["think", "nothink"], default=None,
                   help="Ha nincs megadva, mindkettő")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    if args.models:
        targets = args.models
    else:
        targets = sorted(p.name for p in args.results_dir.iterdir() if p.is_dir())

    if args.mode:
        targets = [t for t in targets if t.endswith(f"-{args.mode}")]

    print(f"🔧 MT-Bench rejudge: {len(targets)} modell/mód, "
          f"baselines={args.baselines}\n")

    for m in targets:
        mode = "think" if m.endswith("-think") else "nothink"
        r = judge_one_model(m, args.results_dir, mode, args.baselines, args.verbose)
        if r["status"] == "OK":
            print(f"  ✅ {m}: judged={r['judged']}, baselines={r['baselines']}, "
                  f"avg_score={r['avg_score']:.4f}, strict={r['strict']:.4f} "
                  f"({r['wins']}W/{r['losses']}L/{r['ties']}T)\n")
        else:
            print(f"  ⚠️  {m}: {r['status']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
