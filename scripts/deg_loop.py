#!/usr/bin/env python
"""
deg_loop.py — degenerált (token-loopos) válaszok detektálása a results JSONL-ekben.

A korábbi "raw_response > 20000 char" küszöb a verbose, de érvényes válaszokat
is loopnak jelölte. A valódi degeneráció felismerése: a válasz LENGTH-je nagy,
ÉS a farka erősen ismétlődő (kevés különböző darab), vagyis a modell egy
minta-ciklusba került (számolás: "1 2 3 4…", kitöltő: "____", word loop).

Használat:
    python scripts/deg_loop.py results/*/ud_hungarian_results.jsonl
    python scripts/deg_loop.py --detail results/.../ud_hungarian_results.jsonl
"""
import argparse
import json
import re
import sys
from pathlib import Path

# A válasz ennyi karakternél hosszabb, és a farka ismétlődő
LONG_CHARS = 12000
TAIL_CHARS = 4000
CHUNK = 40
MAX_DISTINCT = 8


def _has_period(tail: str, min_period: int = 8, max_period: int = 120,
                min_match: float = 0.95) -> bool:
    """Igaz, ha a szöveg egy rövid egység periodikus ismétlése.

    A pozíció-alapú chunk-összehasonlítás nem elég: ha az ismétlődő egység
    nem pontosan a chunk-határon kezdődik, a chunk-ek mind különböznek. A
    periódus-keresés az eltolástól független.

    A szigorúbb küszöb (0.95, min_period=8) azért kell, hogy a **hosszú, de
    érvényes** CoNLL-U táblák (sok hasonló "_" kitöltő sor) ne legyenek
    false positive-ok.
    """
    n = len(tail)
    if n < 2 * min_period:
        return False
    for p in range(min_period, min(max_period, n // 2)):
        a, b = tail[:-p], tail[p:]
        m = sum(1 for x, y in zip(a, b) if x == y)
        if m / max(1, len(a)) >= min_match:
            return True
    return False


def is_degenerate(text: str) -> bool:
    """Igaz, ha a válasz hosszú ÉS a farka degenerált ismétlődés."""
    if not text or len(text) < LONG_CHARS:
        return False
    tail = text[-TAIL_CHARS:]

    # (1) Periodikus ismétlődés: a farka egy rövid egység ismétlése (kitöltő
    #     "_", növekvő sorszámú szósor, D/E/F, bármi).
    if _has_period(tail):
        return True

    # (2) Számláló ciklus: növekvő egészek (1 2 3 … 6598) tabulátorral.
    nums = [int(x) for x in re.findall(r"\b\d{1,7}\b", tail)]
    if len(nums) >= 20:
        steps = [b - a for a, b in zip(nums, nums[1:])]
        if sum(1 for s in steps if s == 1) >= 0.8 * len(steps):
            return True

    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--detail", action="store_true", help="listázza a loopos itemeket")
    args = ap.parse_args()

    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"{f}: nem létezik")
            continue
        rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        n = len(rows)
        if not n:
            print(f"{f}: üres")
            continue
        deg = [r for r in rows if is_degenerate(r.get("raw_response") or "")]
        long_ = [r for r in rows if len(r.get("raw_response") or "") > LONG_CHARS]
        print(f"{f}")
        print(f"   itemek: {n} | hosszú (>20k): {len(long_)} ({100*len(long_)/n:.1f}%) | "
              f"DEGENERÁLT: {len(deg)} ({100*len(deg)/n:.1f}%)")
        if args.detail:
            for r in deg:
                print(f"     - {r.get('id')}: {len(r.get('raw_response') or '')} char")
    return 0


if __name__ == "__main__":
    sys.exit(main())
