#!/usr/bin/env python
"""
judge_mt_bench.py — MT-Bench-HU válaszok pontozása deepseek-v4-pro:cloud bíróval.

GSB (Good/Same/Bad) pairwise összehasonlítás egy baseline modellhez képest.
A judge.overall = win rate (0-1).

Használat:
  python judge_mt_bench.py --model qwen3.5:cloud
  python judge_mt_bench.py --model qwen3.5:cloud --baseline deepseek-v4-flash:cloud
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

JUDGE_MODEL = "deepseek-v4-pro:cloud"
BASELINE_MODEL = "deepseek-v4-flash:cloud"  # default baseline
DEFAULT_RESULTS_DIR = Path("./results")
LOG_PATH = Path("./logs/mt_bench_judge.log")

JUDGE_PROMPT_TEMPLATE = """Összehasonlítasz két modell válaszát egy magyar nyelvű kérdésre.

Kérdés: {question}

A modell válasza: {response_a}

B modell válasza: {response_b}

Melyik válasz jobb? Válaszolj CSAK egy betűvel:
- A, ha az A modell válasza jobb
- B, ha a B modell válasza jobb
- S, ha a két válasz egyenlő minőségű"""


def gsb_judge(question: str, response_a: str, response_b: str,
              swap: bool = False) -> str | None:
    """GSB pontozás. Ha swap=True, A és B felcserélve."""
    q = question
    ra, rb = (response_b, response_a) if swap else (response_a, response_b)
    prompt = JUDGE_PROMPT_TEMPLATE.format(question=q, response_a=ra, response_b=rb)
    try:
        resp = call_ollama_strict(prompt, JUDGE_MODEL, num_predict=8, timeout=120, max_retries=1)
        raw = resp.get("response", "").strip().upper()
        for ch in raw:
            if ch in ("A", "B", "S"):
                # Ha swap volt, fordítva értelmezzük
                if swap:
                    return {"A": "B", "B": "A", "S": "S"}[ch]
                return ch
        return None
    except OllamaFatalError:
        return None


def generate_baseline(model: str, mode: str, questions: list[dict],
                      results_dir: Path) -> list[dict] | None:
    """Baseline modell válaszainak generálása, ha még nincsenek meg."""
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
    baseline_path = results_dir / model_safe / "mt_bench_hu_baseline.jsonl"
    if baseline_path.exists():
        return [json.loads(l) for l in baseline_path.read_text(encoding="utf-8").splitlines()]

    print(f"   Baseline ({model}) válaszok generálása...")
    from stop_on_error import call_ollama_strict as ollama_call
    results = []
    for item in questions:
        try:
            r1 = ollama_call(item["turn1_prompt"], model,
                             num_predict=4096, timeout=120, max_retries=2)
            t1 = r1.get("response", "").strip()
            conv = f"{item['turn1_prompt']}\n\nVálaszom: {t1}\n\n{item['turn2_followup']}"
            r2 = ollama_call(conv, model, num_predict=4096, timeout=120, max_retries=2)
            t2 = r2.get("response", "").strip()
        except OllamaFatalError:
            print(f"   ⚠️ Baseline sikertelen: {item['id']}")
            continue
        results.append({"id": item["id"], "turn1_response": t1, "turn2_response": t2})
        time.sleep(0.3)

    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    with baseline_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"   Baseline kész: {baseline_path} ({len(results)}/{len(questions)})")
    return results


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--mode", choices=["think", "nothink"], default="nothink")
    p.add_argument("--baseline", default=BASELINE_MODEL)
    p.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    args = p.parse_args()

    model_safe = args.model.replace(":", "-").replace("/", "-") + f"-{args.mode}"
    results_path = args.results_dir / model_safe / "mt_bench_hu_results.jsonl"
    judged_path = args.results_dir / model_safe / "mt_bench_hu_judged.jsonl"

    if not results_path.exists():
        print(f"❌ Nincs eredmény fájl: {results_path}")
        return 1

    candidate_items = [json.loads(l) for l in results_path.read_text(encoding="utf-8").splitlines()]
    questions_path = Path("./data/mt_bench_hu/questions.jsonl")
    questions = [json.loads(l) for l in questions_path.read_text(encoding="utf-8").splitlines()]

    # Baseline válaszok
    baseline_items = generate_baseline(args.baseline, args.mode, questions, args.results_dir)
    if not baseline_items:
        print("❌ Baseline nem generálható.")
        return 1

    # Build ID → response map for baseline
    baseline_map = {b["id"]: b for b in baseline_items}

    print(f"🚀 MT-Bench-HU judge: {args.model} vs {args.baseline} ({args.mode}) | {len(candidate_items)} kérdés")

    existing_ids = set()
    if judged_path.exists():
        for line in judged_path.read_text(encoding="utf-8").splitlines():
            try:
                existing_ids.add(json.loads(line)["id"])
            except Exception:
                pass

    gsb_results = []
    for i, item in enumerate(candidate_items):
        if item["id"] in existing_ids:
            continue

        base = baseline_map.get(item["id"])
        if not base:
            continue

        # Mindkét fordulóra külön GSB
        gsb1 = gsb_judge(item["turn1_prompt"], item["turn1_response"],
                         base.get("turn1_response", ""))
        time.sleep(0.5)
        gsb2 = gsb_judge(item["turn2_followup"], item["turn2_response"],
                         base.get("turn2_response", ""))
        time.sleep(0.5)

        # Counterbalanced: második menetben swap-pel
        gsb1_swap = gsb_judge(item["turn1_prompt"], item["turn1_response"],
                              base.get("turn1_response", ""), swap=True)
        time.sleep(0.5)
        gsb2_swap = gsb_judge(item["turn2_followup"], item["turn2_response"],
                              base.get("turn2_response", ""), swap=True)
        time.sleep(0.5)

        # Csak akkor számít, ha mindkét menet ugyanazt mondja
        def resolve(a, b):
            if a is None or b is None:
                return None
            if a == b:
                return a
            # Ha eltér: S (bizonytalan)
            return "S"

        gsb1_final = resolve(gsb1, gsb1_swap)
        gsb2_final = resolve(gsb2, gsb2_swap)

        gsb_results.append({
            "id": item["id"],
            "category": item.get("category", "general"),
            "turn1_gsb": gsb1_final,
            "turn2_gsb": gsb2_final,
            "turn1_gsb_raw": [gsb1, gsb1_swap],
            "turn2_gsb_raw": [gsb2, gsb2_swap],
        })

        if (i + 1) % 5 == 0 or i == len(candidate_items) - 1:
            print(f"  [{i+1:4d}/{len(candidate_items)}]")

    # Write judged JSONL
    judged_path.parent.mkdir(parents=True, exist_ok=True)
    with judged_path.open("a", encoding="utf-8") as fout:
        for r in gsb_results:
            fout.write(json.dumps(r, ensure_ascii=False) + "\n")
            fout.flush()
            os.fsync(fout.fileno())

    # Összesítés
    all_judged = [json.loads(l) for l in judged_path.read_text(encoding="utf-8").splitlines()]
    win_rate = 0.5
    if all_judged:
        wins = sum(1 for r in all_judged
                   if r.get("turn1_gsb") == "A" and r.get("turn2_gsb") == "A")
        losses = sum(1 for r in all_judged
                     if r.get("turn1_gsb") == "B" and r.get("turn2_gsb") == "B")
        # win rate: (wins / (wins + losses)) ha van döntés, egyébként 0.5
        total_decided = wins + losses
        win_rate = wins / total_decided if total_decided > 0 else 0.5

        summary = {
            "model": args.model, "benchmark": "mt_bench_hu",
            "baseline": args.baseline, "judge_model": JUDGE_MODEL,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "num_judged": len(all_judged),
            "score": round(win_rate, 4),
            "wins": wins,
            "losses": losses,
            "ties": len(all_judged) - wins - losses,
        }
        sum_path = args.results_dir / model_safe / "mt_bench_hu_summary.json"
        sum_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        print(f"\n✅ MT-Bench-HU judge kész: {len(all_judged)}/{len(candidate_items)} kérdés")
        print(f"   Win rate vs {args.baseline}: {win_rate:.4f} ({wins}W/{losses}L)")
    else:
        print("❌ Egy kérdést sem sikerült pontozni.")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} | {args.model} | mt_bench_judge | "
                f"{len(all_judged)} judged | win_rate={win_rate:.4f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
