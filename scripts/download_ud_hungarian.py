#!/usr/bin/env python
"""
download_ud_hungarian.py — UD Hungarian letöltése GitHub-ról.

Forrás: Universal Dependencies UD_Hungarian-Szeged (GitHub)
  https://raw.githubusercontent.com/UniversalDependencies/UD_Hungarian-Szeged/master/

Csak a test splitet töltjük le (~137 mondat).

Output:
  data/ud_hungarian/hu_szeged-ud-test.conllu  — nyers CoNLL-U
  data/ud_hungarian/ud_hungarian_std.jsonl     — standard JSONL

Használat:
  python scripts/download_ud_hungarian.py
"""
import json
import urllib.request
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/UniversalDependencies/UD_Hungarian-Szeged/master/"
TEST_URL = BASE_URL + "hu_szeged-ud-test.conllu"

RAW_PATH = Path("./data/ud_hungarian/hu_szeged-ud-test.conllu")
STD_PATH = Path("./data/ud_hungarian/ud_hungarian_std.jsonl")


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"📥 Letöltés: {url}")
    urllib.request.urlretrieve(url, path)
    print(f"   → {path}")


def parse_conllu(text: str) -> list[dict]:
    """CoNLL-U → list of sentence dicts."""
    sents = []
    current = {"id": None, "text": None, "tokens": [], "lines": []}
    for line in text.splitlines():
        if line.startswith("# sent_id"):
            current["id"] = line.split("=", 1)[1].strip()
        elif line.startswith("# text"):
            current["text"] = line.split("=", 1)[1].strip()
        elif line == "" or line.startswith("#"):
            if current["id"] and current["tokens"]:
                sents.append(current)
            current = {"id": None, "text": None, "tokens": [], "lines": []}
        elif "\t" in line and not line.startswith("#"):
            cols = line.split("\t")
            if len(cols) >= 10 and not cols[0].startswith("."):
                current["tokens"].append({
                    "id": cols[0],
                    "form": cols[1],
                    "lemma": cols[2],
                    "upos": cols[3],
                    "xpos": cols[4],
                    "feats": cols[5],
                    "head": cols[6],
                    "deprel": cols[7],
                    "deps": cols[8],
                    "misc": cols[9],
                })
            current["lines"].append(line)
    if current["id"] and current["tokens"]:
        sents.append(current)
    return sents


def conllu_to_prompt(text: str, tokens: list[dict]) -> str:
    """Építsd meg a promptot a CoNLL-U elemzéshez."""
    words = [t["form"] for t in tokens]
    sentence = " ".join(words).replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?").replace(" :", ":").replace(" ;", ";").replace(" „", "„").replace("” ", "”")
    return (
        f"Elemezd a következő magyar mondatot a Universal Dependencies szerint.\n"
        f"Add meg minden tokenre: ID, FORM, LEMMA, UPOS, FEATS, HEAD, DEPREL.\n"
        f"Válaszolj CoNLL-U formátumban, tabulátorral tagolva.\n\n"
        f"Mondat: {sentence}\n\n"
        f"CoNLL-U:"
    )


def main() -> int:
    download(TEST_URL, RAW_PATH)
    text = RAW_PATH.read_text(encoding="utf-8")
    sents = parse_conllu(text)
    print(f"   Összesen {len(sents)} mondat a test splitben")

    n = 0
    with STD_PATH.open("w", encoding="utf-8") as fout:
        for s in sents:
            conllu_str = "\n".join(s["lines"])
            prompt = conllu_to_prompt(s["text"], s["tokens"])
            std = {
                "id": f"ud_hu_{s['id']}",
                "task": "ud_hungarian",
                "prompt": prompt,
                "gold_conllu": conllu_str,
                "tokens": s["tokens"],
                "source": "ud_hu_szeged",
            }
            fout.write(json.dumps(std, ensure_ascii=False) + "\n")
            n += 1

    print(f"✅ Standardizált: {STD_PATH} ({n} példa)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
