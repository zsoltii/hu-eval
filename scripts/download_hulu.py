#!/usr/bin/env python
"""
download_hulu.py — HuLU benchmark letöltése NYTK forrásokból.

A korábbi PhilipMay/hulu-bench dataset megszűnt (401). Az új forrás a NYTK
(Nyelvtudományi Kutatóközpont) hivatalos HuggingFace szervezete, illetve
a hivatalos meta-repo (offline backup).

Alapértelmezetten HuggingFace-ről tölti a 6 NLU sub-task validation split-jét
(a teszt halmaz label-ek nélkül van — csak a NYTK szerverén értékelhető):

  NYTK/HuCOLA           (hucola)   — elfogadhatóság, bináris (0/1)
  NYTK/HuCoPA           (hucopa)   — oksági választás, 1/2 → 0/1
  NYTK/HuRTE            (hurte)    — entailment, bináris
  NYTK/HuSST            (husst)    — sentiment, 3 osztály (negative/neutral/positive)
  NYTK/HuWNLI           (huwnli)   — anaphora NLI, bináris
  NYTK/HuCommitmentBank (hucb)     — 3-osztályos NLI (0/1/2)

Offline backup: --offline kapcsolóval a github.com/nytud/HuLU meta-repo
klónozása történik --recurse-submodules módban, és abból olvasunk. A
mezőnevek a két forrásban eltérnek (HF: Sent_id/Sent/Label, git: sent_id/
sent/sent_label) — a script automatikusan kezeli a különbséget.

Megjegyzés: a wiki (hulu-benchmark.md) korábban 7 sub-taskot említett
közöttük HuPi-vel és HuSTER-rel — ezek NEM LÉTEZNEK. A valódi 7. dataset
a HuRC (cloze-formátumú olvasásértés, külön schema), jelenleg nincs
implementálva.

Output:
  data/hulu/hulu_std.jsonl  — standardizált JSONL, run_hulu.py olvassa
    séma: {id, task, prompt, choices, answer_index, source}
  data/hulu/hulu_raw.jsonl  — nyers NYTK rekordok (debug célokra)

Használat:
  pip install datasets
  python scripts/download_hulu.py            # HF-ről tölt (ajánlott)
  python scripts/download_hulu.py --offline  # git clone-ból olvas (offline backup)
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from datasets import load_dataset

CACHE_DIR = Path("./data/hulu_cache")
RAW_PATH = Path("./data/hulu/hulu_raw.jsonl")
STD_PATH = Path("./data/hulu/hulu_std.jsonl")
OFFICIAL_DIR = Path("./data/hulu_official")
OFFICIAL_REPO = "https://github.com/nytud/HuLU.git"

# (HF repo, task name, split, git submodule path)
# A git submodule path relatív a klónozott meta-repo gyökeréhez.
HF_TASKS = [
    ("NYTK/HuCOLA",           "hucola",   "validation", "HuCOLA"),
    ("NYTK/HuCoPA",           "hucopa",   "validation", "HuCoPA"),
    ("NYTK/HuRTE",            "hurte",    "validation", "HuRTE"),
    ("NYTK/HuSST",            "husst",    "validation", "HuSST"),
    ("NYTK/HuWNLI",           "huwnli",   "validation", "HuWNLI"),
    ("NYTK/HuCommitmentBank", "hucb",     "validation", "HuCommitmentBank"),
]


def _g(rec, *names, default=None):
    """Get first present field from record (HF és git mezőnevek eltérnek)."""
    for n in names:
        if n in rec and rec[n] is not None:
            return rec[n]
    return default


def _g_int(rec, *names, default=0) -> int:
    """Ugyanaz, de int konverzióval (HF: string label, git: int label)."""
    val = _g(rec, *names, default=default)
    if val is None:
        return default
    return int(val)


def build_prompt(task: str, rec: dict) -> tuple[str, list[str]]:
    """(prompt, choices) — a run_hulu.py extract_choice függvényével kompatibilis."""
    if task == "hucola":
        s = _g(rec, "sentence", "sent", "Sent", default="")
        prompt = (
            "Döntsd el, hogy az alábbi magyar mondat nyelvtanilag helyes-e.\n"
            "Válaszolj CSAK egy számmal: 0 (helytelen) vagy 1 (helyes).\n\n"
            f"Mondat: {s}\n\nVálasz:"
        )
        return prompt, ["0", "1"]

    if task == "hucopa":
        p = _g(rec, "premise", default="")
        c1 = _g(rec, "choice1", default="")
        c2 = _g(rec, "choice2", default="")
        prompt = (
            "Az alábbi premisszához melyik folytatás illik jobban "
            "(az oksági viszony alapján)?\n"
            "Válaszolj CSAK egy számmal: 0 (első) vagy 1 (második).\n\n"
            f"Premissza: {p}\n"
            f"0) {c1}\n"
            f"1) {c2}\n\nVálasz:"
        )
        return prompt, ["0", "1"]

    if task == "hurte":
        p = _g(rec, "premise", default="")
        h = _g(rec, "hypothesis", default="")
        prompt = (
            "Az alábbi hipotézis NEM következik-e a premisszából? "
            "(ellentmondás vagy semleges)\n"
            "Válaszolj CSAK egy számmal: 0 (nem, a hipotézis "
            "ellentmond a premisszának) vagy 1 (igen, a hipotézis "
            "következik a premisszából).\n\n"
            f"Premissza: {p}\n"
            f"Hipotézis: {h}\n\nVálasz:"
        )
        return prompt, ["0", "1"]

    if task == "huwnli":
        s1 = _g(rec, "sentence1", "s1", default="")
        s2 = _g(rec, "sentence2", "s2", default="")
        prompt = (
            "Az első mondatban lévő névmás a második mondatba "
            "behelyettesítve természetes marad-e?\n"
            "Válaszolj CSAK egy számmal: 0 (igen, természetes, "
            "a második mondat igaz) vagy 1 (nem, természetlen, "
            "a második mondat nem igaz).\n\n"
            f"1) {s1}\n"
            f"2) {s2}\n\nVálasz:"
        )
        return prompt, ["0", "1"]

    if task == "hucb":
        p = _g(rec, "premise", default="")
        h = _g(rec, "hypothesis", default="")
        prompt = (
            "Milyen viszony van az alábbi két mondat között?\n"
            "Válaszolj CSAK egy számmal: 0 (ellentmondás), "
            "1 (semleges), vagy 2 (következmény).\n\n"
            f"1) {p}\n"
            f"2) {h}\n\nVálasz:"
        )
        return prompt, ["0", "1", "2"]

    if task == "husst":
        t = _g(rec, "text", "sent", "sentence", default="")
        prompt = (
            "Az alábbi szöveg milyen hangulatú?\n"
            "Válaszolj CSAK egy számmal: 0 (negatív), 1 (semleges), "
            "vagy 2 (pozitív).\n\n"
            f"Szöveg: {t}\n\nVálasz:"
        )
        return prompt, ["0", "1", "2"]

    raise ValueError(f"ismeretlen task: {task}")


def normalize_label(task: str, rec: dict) -> int:
    """0-indexed integer label a standardizált JSONL-be.

    Task-specifikus formátumok (HF validation split, 2026-06-07 ellenőrizve):
      hucola   int 0/1
      hucopa   int 0/1 (HF)  |  string "1"/"2" (git submodule, 1-indexed)
      hurte    int 0/1
      huwnli   int 0/1
      husst    string "negative"/"neutral"/"positive"
      hucb     string "entailment"/"contradiction"/"neutral"
    """
    if task == "hucola":
        return _g_int(rec, "Label", "sent_label", "label")
    if task == "hucopa":
        raw = _g(rec, "label", default=None)
        if raw is None:
            raise ValueError("hucopa: label missing")
        if isinstance(raw, str):
            return int(raw) - 1
        return int(raw)
    if task in ("hurte", "huwnli"):
        return _g_int(rec, "label", "Label")
    if task == "husst":
        raw = _g(rec, "label", "Label", default="").strip().lower()
        m = {"negative": 0, "neutral": 1, "positive": 2}
        if raw not in m:
            raise ValueError(f"husst: ismeretlen label: {raw!r}")
        return m[raw]
    if task == "hucb":
        raw = _g(rec, "label", "Label", default="").strip().lower()
        m = {"contradiction": 0, "neutral": 1, "entailment": 2}
        if raw not in m:
            raise ValueError(f"hucb: ismeretlen label: {raw!r}")
        return m[raw]
    raise ValueError(f"ismeretlen task: {task}")


def standardize(task: str, rec: dict, idx: int, source: str) -> dict:
    prompt, choices = build_prompt(task, rec)
    return {
        "id": f"hulu_{task}_{idx:05d}",
        "task": task,
        "prompt": prompt,
        "choices": choices,
        "answer_index": normalize_label(task, rec),
        "source": source,
    }


def load_hf(repo: str, task: str, split: str) -> list[dict]:
    ds = load_dataset(repo, split=split, cache_dir=str(CACHE_DIR))
    return [dict(r) for r in ds]


def load_git(task: str, submodule: str) -> list[dict]:
    """Beolvassa a sub-task dev.jsonl fájlját a klónozott meta-repóból.

    A git submodule-ok data/dev.jsonl formátumúak (HuCOLA README alapján),
    de a pontos útvonal sub-task-onként eltérhet — a HuCOLA-nál `data/dev.jsonl`,
    máshol lehet `dev.jsonl` közvetlenül. Több útvonalat is próbálunk.
    """
    base = OFFICIAL_DIR / submodule
    candidates = [base / "data" / "dev.jsonl", base / "dev.jsonl"]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        print(f"     ⚠️  {task}: egyik dev.jsonl sem található: {candidates}")
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def clone_official() -> bool:
    """Meta-repo klónozása --recurse-submodules módban."""
    if (OFFICIAL_DIR / ".git").exists():
        return True
    print(f"📥 Git clone: {OFFICIAL_REPO} → {OFFICIAL_DIR} (submodules)")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--recurse-submodules",
             OFFICIAL_REPO, str(OFFICIAL_DIR)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git clone sikertelen: {e.stderr.strip() or e}")
        return False
    except FileNotFoundError:
        print("⚠️  git nem található a PATH-ban — offline backup kimarad")
        return False


def download_hf() -> list[dict]:
    """6 NLU sub-task betöltése HF-ről, standardizálás."""
    print("📥 HuLU letöltés NYTK HuggingFace dataset-ekből (6 NLU sub-task)\n")
    all_std = []
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("w", encoding="utf-8") as fraw:
        for repo, task, split, _submod in HF_TASKS:
            print(f"  {repo} ({split})...", end="", flush=True)
            try:
                records = load_hf(repo, task, split)
            except Exception as e:
                print(f"\n  ❌ {repo} betöltése sikertelen: {e}")
                print("     A többi sub-task betöltése folytatódik.")
                continue
            print(f" {len(records)} példa")
            for r in records:
                fraw.write(json.dumps(
                    {"task": task, "raw": r}, ensure_ascii=False) + "\n")
            for i, r in enumerate(records):
                all_std.append(standardize(task, r, i, source="nytk_hf"))
    return all_std


def download_git() -> list[dict]:
    """6 NLU sub-task betöltése a klónozott meta-repóból."""
    print("📥 HuLU olvasás git submodule-okból (offline backup)\n")
    all_std = []
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("w", encoding="utf-8") as fraw:
        for _repo, task, _split, submod in HF_TASKS:
            print(f"  {submod}/...", end="", flush=True)
            records = load_git(task, submod)
            print(f" {len(records)} példa")
            for r in records:
                fraw.write(json.dumps(
                    {"task": task, "raw": r}, ensure_ascii=False) + "\n")
            for i, r in enumerate(records):
                all_std.append(standardize(task, r, i, source="nytk_official"))
    return all_std


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--offline", action="store_true",
        help="HuggingFace helyett a github.com/nytud/HuLU meta-repo "
             "git clone-ból olvas (offline backup).",
    )
    args = p.parse_args()

    if args.offline:
        if not clone_official():
            print("❌ Offline mód nem lehetséges (git clone sikertelen).")
            return 1
        all_std = download_git()
    else:
        all_std = download_hf()

    STD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STD_PATH.open("w", encoding="utf-8") as fout:
        for item in all_std:
            fout.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"\n✅ Standardizált: {STD_PATH} ({len(all_std)} példa)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
