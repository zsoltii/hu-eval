#!/usr/bin/env python
"""
reparse_ud.py — a UD Hungarian eredmények újraparse-olása a jelenlegi
parserrel, a tárolt nyers válaszokból.

Miért kell: a parser több fejlesztésen ment át (a HEAD/DEPREL oszlopok
robusztus keresése, majd a UPOS oszlopé is). A nyers válaszok (`raw_response`)
teljes egészében megmaradnak, így a pontszámok **offline** újraszámolhatók
a futások újrafuttatása nélkül.

A script:
  1. beolvassa a datasetet (gold tokenek),
  2. újraparse-olja a `raw_response`-t a `run_ud_hungarian.parse_conllu_from_response`
     függvénnyel,
  3. frissíti a sorok `upos_accuracy` / `uas` / `las` / `parsed_tokens` mezőit,
  4. újraírja a JSONL-t atomikusan (tmp + os.replace) és újraírja a summary-t.

Használat:
    python scripts/reparse_ud.py results/*/ud_hungarian_results.jsonl
    python scripts/reparse_ud.py --dry-run results/*/ud_hungarian_results.jsonl
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_ud_hungarian import parse_conllu_from_response  # noqa: E402

DATASET_PATH = Path("./data/ud_hungarian/ud_hungarian_std.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--dry-run", action="store_true", help="csak kiírja az új pontszámokat")
    args = ap.parse_args()

    if not DATASET_PATH.exists():
        print(f"❌ Dataset nem található: {DATASET_PATH}")
        return 1
    data = {json.loads(l)["id"]: json.loads(l) for l in
            DATASET_PATH.read_text(encoding="utf-8").splitlines() if l.strip()}

    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"{f}: nem létezik")
            continue
        rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not rows:
            print(f"{f}: üres")
            continue
        old_u = sum(r.get("upos_accuracy") or 0 for r in rows) / len(rows)
        old_h = sum(r.get("uas") or 0 for r in rows) / len(rows)
        old_d = sum(r.get("las") or 0 for r in rows) / len(rows)

        for r in rows:
            gold = data.get(r["id"], {}).get("tokens", [])
            parsed = parse_conllu_from_response(r.get("raw_response") or "", gold)
            if parsed:
                r["upos_accuracy"] = round(parsed["upos_correct"] / max(1, parsed["upos_total"]), 4)
                r["uas"] = round(parsed["head_correct"] / max(1, parsed["head_total"]), 4)
                r["las"] = round(parsed["deprel_correct"] / max(1, parsed["deprel_total"]), 4)
            else:
                r["upos_accuracy"] = r["uas"] = r["las"] = 0.0
            r["parsed_tokens"] = parsed

        n = len(rows)
        new_u = sum(r["upos_accuracy"] for r in rows) / n
        new_h = sum(r["uas"] for r in rows) / n
        new_d = sum(r["las"] for r in rows) / n
        print(f"{f}")
        print(f"   UPOS {old_u:.4f} → {new_u:.4f} | UAS {old_h:.4f} → {new_h:.4f} | "
              f"LAS {old_d:.4f} → {new_d:.4f}")

        if args.dry_run:
            continue

        # atomikus írás
        tmp = p.with_suffix(p.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fout:
            for r in rows:
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
            fout.flush()
            os.fsync(fout.fileno())
        os.replace(tmp, p)

        # summary frissítés
        sp = p.parent / (p.name.replace("_results.jsonl", "_summary.json"))
        if sp.exists():
            s = json.loads(sp.read_text(encoding="utf-8"))
            s["accuracy"] = round((new_u + new_h + new_d) / 3.0, 4)
            s["upos_accuracy"] = round(new_u, 4)
            s["uas"] = round(new_h, 4)
            s["las"] = round(new_d, 4)
            s["num_examples"] = n
            s["reparsed_at"] = datetime.now(timezone.utc).isoformat()
            sp.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"   summary frissítve: {sp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
