#!/usr/bin/env python
"""
recompute_hulu_summary.py — HuLU summary.json frissítése a dedup-olt
hulu_results.jsonl alapján (accuracy = correct / len).

Használat:
  python scripts/recompute_hulu_summary.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"


def main() -> int:
    for d in sorted(RESULTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        f = d / "hulu_results.jsonl"
        s = d / "hulu_summary.json"
        if not f.exists():
            continue
        lines = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        n = len(lines)
        correct = sum(1 for l in lines if l.get("correct"))
        acc = correct / n if n else 0.0
        if s.exists():
            try:
                summary = json.loads(s.read_text())
            except json.JSONDecodeError:
                summary = {}
        else:
            summary = {}
        summary.update({
            "model": d.name.replace("hulu_results.jsonl", "").rstrip("-").rstrip("0123456789"),
            "benchmark": "hulu",
            "num_examples": n,
            "accuracy": round(acc, 4),
            "num_correct": correct,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results_file": str(f),
        })
        s.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✅ {d.name}: {correct}/{n} = {acc*100:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
