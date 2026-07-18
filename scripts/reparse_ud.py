#!/usr/bin/env python
"""
reparse_ud.py — Meglévő UD Hungarian JSONL-ek újrafeldolgozása a javított CoT-aware parser-rel.

Nem futtatja újra a modelleket — csak a raw_response mezőkből parsolja ki a CoNLL-U-t az
új, CoT-strip + szabad-formátum regex-eket is támogató parse_conllu_from_response függvénnyel.

Használat:
  python scripts/reparse_ud.py                    # minden modell × mód
  python scripts/reparse_ud.py deepseek-v4-flash-cloud-nothink  # egy modell
  python scripts/reparse_ud.py --only-parsable    # csak a nem-üres raw_response-ok
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from run_ud_hungarian import parse_conllu_from_response

DATASET_PATH = ROOT / "data" / "ud_hungarian" / "ud_hungarian_std.jsonl"
RESULTS_DIR = ROOT / "results"


def load_gold_tokens() -> dict[str, list[dict]]:
    items = [json.loads(l) for l in DATASET_PATH.read_text(encoding="utf-8").splitlines()]
    return {item["id"]: item["tokens"] for item in items}


def reparse_model(model_safe: str, gold_map: dict, only_parsable: bool = False) -> dict:
    res_path = RESULTS_DIR / model_safe / "ud_hungarian_results.jsonl"
    if not res_path.exists():
        return {"model": model_safe, "status": "NO_DATA"}

    lines = res_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return {"model": model_safe, "status": "EMPTY"}

    records = [json.loads(l) for l in lines]

    n = 0
    sum_upos = sum_uas = sum_las = 0.0
    n_parsed = 0
    n_skipped_empty = 0

    new_records = []
    for r in records:
        rid = r["id"]
        gold = gold_map.get(rid, [])
        raw = r.get("raw_response", "")
        if only_parsable and not raw.strip():
            n_skipped_empty += 1
            new_records.append(r)
            continue
        parsed = parse_conllu_from_response(raw, gold)
        if parsed:
            upos_acc = parsed["upos_correct"] / max(1, parsed["upos_total"])
            head_acc = parsed["head_correct"] / max(1, parsed["head_total"])
            deprel_acc = parsed["deprel_correct"] / max(1, parsed["deprel_total"])
            r["upos_accuracy"] = round(upos_acc, 4)
            r["uas"] = round(head_acc, 4)
            r["las"] = round(deprel_acc, 4)
            r["parsed_tokens"] = parsed
            n_parsed += 1
            sum_upos += upos_acc
            sum_uas += head_acc
            sum_las += deprel_acc
        n += 1
        new_records.append(r)

    if n_parsed == 0:
        return {
            "model": model_safe,
            "status": "NO_PARSED",
            "n": n,
            "n_empty": n_skipped_empty,
        }

    avg_upos = sum_upos / n_parsed
    avg_uas = sum_uas / n_parsed
    avg_las = sum_las / n_parsed
    composite = (avg_upos + avg_uas + avg_las) / 3.0

    res_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in new_records) + "\n",
        encoding="utf-8",
    )

    summary = {
        "model": new_records[0].get("model", model_safe) if new_records else model_safe,
        "benchmark": "ud_hungarian",
        "num_examples": n_parsed,
        "accuracy": round(composite, 4),
        "upos_accuracy": round(avg_upos, 4),
        "uas": round(avg_uas, 4),
        "las": round(avg_las, 4),
        "results_file": str(res_path),
    }
    summary_path = RESULTS_DIR / model_safe / "ud_hungarian_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "model": model_safe,
        "status": "REWRITTEN",
        "n_items": n,
        "n_parsed": n_parsed,
        "n_empty": n_skipped_empty,
        "composite": round(composite, 4),
        "upos": round(avg_upos, 4),
        "uas": round(avg_uas, 4),
        "las": round(avg_las, 4),
    }


def main() -> int:
    args = sys.argv[1:]
    only_parsable = "--only-parsable" in args
    args = [a for a in args if a != "--only-parsable"]

    if not DATASET_PATH.exists():
        print(f"❌ Dataset hiányzik: {DATASET_PATH}")
        return 1

    print("📚 Gold tokenek betöltése...")
    gold_map = load_gold_tokens()
    print(f"   {len(gold_map)} mondat\n")

    if args:
        targets = args
    else:
        targets = sorted(p.name for p in RESULTS_DIR.iterdir() if p.is_dir())

    print(f"🔧 Reparse: {len(targets)} modell/mód (only_parsable={only_parsable})\n")
    for model_safe in targets:
        result = reparse_model(model_safe, gold_map, only_parsable)
        if result["status"] == "REWRITTEN":
            print(f"  ✅ {model_safe}: UPOS={result['upos']:.4f} UAS={result['uas']:.4f} "
                  f"LAS={result['las']:.4f} | comp={result['composite']:.4f} "
                  f"({result['n_parsed']}/{result['n_items']} parsed, {result['n_empty']} empty)")
        else:
            print(f"  ⚠️  {model_safe}: {result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
