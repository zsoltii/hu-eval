#!/usr/bin/env python
"""
dedup_hulu.py — HuLU results JSONL dedup: törli az ismétlődő ID-kat,
az utolsó előfordulást tartja meg (mert az a legfrissebb retry eredménye).

Használat:
  python scripts/dedup_hulu.py                          # minden modell × mód
  python scripts/dedup_hulu.py qwen3.5-cloud-nothink   # egy modell/mód
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"


def dedup_file(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "status": "NO_FILE"}
    lines = path.read_text(encoding="utf-8").splitlines()
    n_orig = len(lines)
    seen: dict[str, int] = {}
    records: list[dict] = []
    for line in lines:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = r.get("id")
        if rid is None:
            continue
        if rid in seen:
            seen[rid] = len(records)
        records.append(r)
        seen[rid] = len(records) - 1

    keep_indices = sorted(set(seen.values()))
    kept = [records[i] for i in keep_indices]
    n_kept = len(kept)

    with path.open("w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        import os
        os.fsync(f.fileno())

    return {
        "path": str(path),
        "status": "OK",
        "original": n_orig,
        "kept": n_kept,
        "removed": n_orig - n_kept,
    }


def main() -> int:
    args = sys.argv[1:]
    if args:
        targets = args
    else:
        targets = sorted(p.name for p in RESULTS_DIR.iterdir() if p.is_dir())

    print(f"🔧 HuLU dedup: {len(targets)} modell/mód\n")
    for m in targets:
        path = RESULTS_DIR / m / "hulu_results.jsonl"
        r = dedup_file(path)
        if r["status"] == "OK" and r["removed"] > 0:
            print(f"  ✅ {m}: {r['original']} → {r['kept']} ({r['removed']} duplikátum törölve)")
        elif r["status"] == "OK":
            print(f"  ·  {m}: {r['original']} sor, nincs duplikátum")
        else:
            print(f"  ⚠️  {m}: {r['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
