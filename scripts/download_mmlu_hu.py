#!/usr/bin/env python
"""
download_mmlu_hu.py — MMLU-HU letöltése NYTK/hu-mmlu-ról (dev + validation).

A NYTK/hu-mmlu dataset:
- 'default' config: 38 tantárgy egyesítve
- dev split: 5 példa/tantárgy (few-shot prompting-hoz)
- validation split: ~1880 példa (értékeléshez)
- test split: 14.1k példa (label nélkül, csak a NYTK szerverén)

Output:
  data/mmlu_hu/mmlu_hu_std.jsonl    — validation (értékeléshez + few-shot példákhoz)

Használat:
  pip install datasets
  python scripts/download_mmlu_hu.py
  python scripts/download_mmlu_hu.py --cache-dir /tmp/hf
"""
import argparse
import json
from pathlib import Path

from datasets import load_dataset

CACHE_DIR = Path("./data/hulu_cache")
STD_PATH = Path("./data/mmlu_hu/mmlu_hu_std.jsonl")

REPO = "NYTK/hu-mmlu"
CONFIG = "default"


def build_prompt(rec: dict) -> str:
    q = rec["question"]
    chs = rec["choices"]
    opts = "\n".join(f"  {chr(65 + i)}) {c}" for i, c in enumerate(chs))
    return (
        f"Kérdés: {q}\nOpciók:\n{opts}\n\n"
        "Válaszolj CSAK a helyes betűvel (A/B/C/D)."
    )


def write_std(out_path: Path, ds: list, prefix: str = "mmlu_hu_") -> int:
    n = 0
    with out_path.open("w", encoding="utf-8") as fout:
        for rec in ds:
            ans = rec.get("answer")
            if not isinstance(ans, int) or not (0 <= ans <= 3):
                continue
            std = {
                "id": f"{prefix}{rec['id']}",
                "task": "mmlu_hu",
                "prompt": build_prompt(rec),
                "choices": rec["choices"],
                "answer_index": ans,
                "source": "nytk_hf",
                "subject": rec.get("subject", "unknown"),
            }
            fout.write(json.dumps(std, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", default=str(CACHE_DIR))
    args = parser.parse_args()

    cache_path = Path(args.cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    STD_PATH.parent.mkdir(parents=True, exist_ok=True)

    for split_name, out_path, label in [
        ("validation", STD_PATH, "Validation (értékelés + few-shot)"),
    ]:
        print(f"📥 {REPO} ({split_name}, '{CONFIG}') letöltése...")
        ds = load_dataset(REPO, CONFIG, split=split_name, cache_dir=str(cache_path))
        print(f"   {len(ds)} példa betöltve")
        n = write_std(out_path, ds)
        print(f"✅ {label}: {out_path} ({n} példa)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
