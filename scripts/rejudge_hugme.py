#!/usr/bin/env python
"""
rejudge_hugme.py — HuGME judge újrafuttatás a meglévő hugme_results.jsonl alapján.

A korábbi futáskor sok item kimaradt a bírózásból (rate-limit, timeout), vagy csak
1-2 metrikát sikerült pontozni (6 helyett). Ez a script:
  1. Betölti a hugme_results.jsonl-t (modell válaszai).
  2. Betölti a meglévő hugme_judged.jsonl-t.
  3. Ahol hiányzik a bíró értékelés VAGY kevesebb, mint 4 metrika van pontozva,
     újrapontozza az összes 6 metrikát (nagyobb num_predict, hosszabb timeout).
  4. Frissíti a hugme_judged.jsonl-t és a summary-t.

Használat:
  python scripts/rejudge_hugme.py                           # minden modell × mód
  python scripts/rejudge_hugme.py qwen3.5-cloud-nothink     # egy modell/mód
  python scripts/rejudge_hugme.py --min-metrics 6           # csak ahol <6 metrika van
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from stop_on_error import call_ollama_strict, OllamaFatalError
from judge_hugme import METRICS, METRIC_RUBRICS, JUDGE_PROMPT_TEMPLATE, JUDGE_MODEL, LOG_PATH

ROOT = Path(__file__).parent.parent
DEFAULT_RESULTS_DIR = ROOT / "results"

N_WORKERS = 4


def judge_one(prompt: str, response: str, metric: str, rubric: str) -> float | None:
    judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
        metric=metric, rubric=rubric, prompt=prompt, response=response
    )
    try:
        resp = call_ollama_strict(
            judge_prompt, JUDGE_MODEL,
            num_predict=24, timeout=180, max_retries=3,
        )
        raw = resp.get("response", "").strip()
        m = re.search(r"([0-9]\.[0-9])", raw)
        if m:
            return max(0.0, min(1.0, float(m.group(1))))
        m2 = re.search(r"\b([0-9])\b", raw)
        if m2:
            return max(0.0, min(1.0, float(m2.group(1)) / 10.0))
        return None
    except OllamaFatalError:
        return None


def rejudge_item(prompt: str, response: str) -> tuple[dict, int]:
    """Visszaadja (judged_dict, metric_count)."""
    metric_scores: dict[str, float] = {}
    for metric in METRICS:
        score = judge_one(prompt, response, metric, METRIC_RUBRICS[metric])
        if score is not None:
            metric_scores[metric] = score
        time.sleep(0.1)
    if not metric_scores:
        return {}, 0
    overall = sum(metric_scores.values()) / len(metric_scores)
    return {
        "judge": {
            "overall": round(overall, 4),
            "metrics": {k: round(v, 4) for k, v in metric_scores.items()},
        }
    }, len(metric_scores)


def needs_rejudge(existing: dict | None, min_metrics: int) -> bool:
    if not existing:
        return True
    metrics = existing.get("judge", {}).get("metrics", {})
    return len(metrics) < min_metrics


def process_model(model_safe: str, results_dir: Path, min_metrics: int, verbose: bool) -> dict:
    res_path = results_dir / model_safe / "hugme_results.jsonl"
    jud_path = results_dir / model_safe / "hugme_judged.jsonl"

    if not res_path.exists():
        return {"model": model_safe, "status": "NO_RESULTS"}

    items = [json.loads(l) for l in res_path.read_text(encoding="utf-8").splitlines()]

    existing: dict[str, dict] = {}
    if jud_path.exists():
        for line in jud_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                existing[rec["id"]] = rec
            except Exception:
                continue

    new_judged = dict(existing)
    to_judge = [(i, it) for i, it in enumerate(items) if needs_rejudge(existing.get(it["id"]), min_metrics)]
    n_total = len(items)
    n_already_ok = n_total - len(to_judge)
    n_fixed = 0
    n_failed = 0

    print(f"  {model_safe}: {len(to_judge)}/{n_total} újrapontozandó "
          f"({n_already_ok} már ok, min_metrics={min_metrics}, workers={N_WORKERS})")

    from concurrent.futures import ThreadPoolExecutor, as_completed
    n_workers = min(N_WORKERS, len(to_judge)) if to_judge else 1
    done_count = 0
    if to_judge:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {
                ex.submit(rejudge_item, it["prompt"], it["response"]): it
                for i, it in to_judge
            }
            for fut in as_completed(futures):
                it = futures[fut]
                try:
                    judged, mc = fut.result()
                except Exception:
                    n_failed += 1
                    continue
                done_count += 1
                if not judged:
                    n_failed += 1
                    continue
                rec = {
                    "id": it["id"],
                    "task": "hugme",
                    "metric": it.get("metric", "general"),
                    "judge": judged["judge"],
                }
                new_judged[rec["id"]] = rec
                n_fixed += 1
                if verbose and done_count % 20 == 0:
                    print(f"    [{done_count}/{len(to_judge)}] last overall={judged['judge']['overall']:.3f}, metrics={mc}")

    all_records = list(new_judged.values())
    with jud_path.open("w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

    avg_overall = 0.0
    if all_records:
        overalls = [r["judge"]["overall"] for r in all_records]
        avg_overall = sum(overalls) / len(overalls)
    summary = {
        "model": model_safe,
        "benchmark": "hugme",
        "judge_model": JUDGE_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_judged": len(all_records),
        "score": round(avg_overall, 4),
        "num_fewshot": 0,
    }
    sum_path = results_dir / model_safe / "hugme_summary.json"
    sum_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} | {model_safe} | hugme_rejudge | "
                f"judged={len(all_records)}/{n_total} | fixed={n_fixed} failed={n_failed} | "
                f"avg={avg_overall:.4f}\n")

    return {
        "model": model_safe,
        "status": "OK",
        "judged": len(all_records),
        "fixed": n_fixed,
        "failed": n_failed,
        "avg_overall": round(avg_overall, 4),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("models", nargs="*", help="model_safe nevei (alapért: mind)")
    p.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    p.add_argument("--min-metrics", type=int, default=4,
                   help="Legalább ennyi metrikát kell pontozni (alapért: 4)")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    if args.models:
        targets = args.models
    else:
        targets = sorted(p.name for p in args.results_dir.iterdir() if p.is_dir())

    print(f"🔧 HuGME rejudge: {len(targets)} modell/mód, min_metrics={args.min_metrics}\n")
    for m in targets:
        r = process_model(m, args.results_dir, args.min_metrics, args.verbose)
        if r["status"] == "OK":
            print(f"  ✅ {m}: judged={r['judged']}, fixed={r['fixed']}, failed={r['failed']}, "
                  f"avg={r['avg_overall']:.4f}\n")
        else:
            print(f"  ⚠️  {m}: {r['status']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
