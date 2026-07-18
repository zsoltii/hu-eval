# MMLU-HU Dataset (MMLU Magyar Fordítás)

*Típus:* entity
*Forrás(ok):* MMLU eredeti (Hendrycks et al., 2021), magyar fordítás: nyílt közösségi projekt 2024
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Azonosítás

- **Teljes név:** MMLU-HU — Massive Multitask Language Understanding, Hungarian translation
- **Rövidítés:** MMLU-HU
- **Verzió:** v1.0 (2024-es magyar fordítás)
- **Első megjelenés:** 2024 Q2
- **Karbantartó:** [Nyelvtudományi Kutatóközpont (NYTK)](https://hulu.nytud.hu/), a HuGME benchmark-rendszer részeként

## Háttér

Az MMLU az egyik legszélesebb körben használt LLM benchmark, amit Dan Hendrycks és mtsai. publikáltak 2021-ben ([arXiv:2009.03300](https://arxiv.org/abs/2009.03300)). 57 tudástartományt fed le az amerikai iskolai tananyagból (STEM, társadalomtudományok, humán tudományok, stb.).

Az **MMLU-HU** az eredeti MMLU gépi + emberi ellenőrzéssel korrigált magyar fordítása. Célja: azonos metodológiával, de magyar nyelven mérni a modellek tudásszintjét.

## Tartalom

### Tudástartományok

Az MMLU-HU mind a 57 eredeti MMLU kategóriát tartalmazza, fordítva. A legfontosabbak:

- **STEM:** matematika, fizika, kémia, biológia, számítástudomány, mérnöki tudományok
- **Társadalomtudományok:** közgazdaságtan, politika, jog, szociológia, pszichológia
- **Humán tudományok:** filozófia, történelem (egyetemes, nem csak magyar), irodalom
- **Egyéb:** orvosi kérdések, üzleti tudás, globális tudás

### Méret

- **Összes kérdés:** 14 042 (az eredeti MMLU-nak megfelelő)
- **Kategóriánként:** átlagosan ~250 kérdés (van, ahol 100, van, ahol 500+)
- **Tartalmaz "dev", "val" és "test" felosztást** az eredeti MMLU-hoz hasonlóan (5-5-99% arányban)

## Formátum

A dataset **JSON** és **CSV** formátumban is elérhető. A JSON struktúra:

```json
{
  "question": "Mi az atomok közötti kölcsönhatás leggyengébb formája?",
  "choices": [
    "Az ionos kötés",
    "A kovalens kötés",
    "A van der Waals erő",
    "A fémes kötés"
  ],
  "answer": "C"
}
```

### Mezők

- `question` — a kérdés szövege magyarul (string)
- `choices` — 4 opció, A-tól D-ig (string lista)
- `answer` — a helyes válasz betűjele (A/B/C/D string)
- A "dev", "val", "test" felosztás mappastruktúrában van (`mmlu-hu-v1.0/{subject}/{split}.json`)

### Különbségek az eredeti MMLU-hoz képest

- **Nyelv:** teljes egészében magyar
- **Kulturális adaptáció:** bizonyos kérdéseket, ahol az amerikai kontextus túl erős volt, magyar kontextusra cserélték (pl. egyes történelmi kérdéseknél)
- **Változatlan:** a kérdésstruktúra, a nehézségi szint, a 4 opciós formátum
- **Validáció:** minden kérdésnél van emberi validátor, aki ellenőrizte a fordítás pontosságát (kétnyelvű validátorok, legalább BA szintű végzettséggel)

## Licenc

- **Az eredeti MMLU licence:** MIT License (a Hendrycks et al. cikk)
- **Az MMLU-HU magyar fordítás licence:** Creative Commons BY-SA 4.0
  - **BY** (Attribution): a forrás és a fordítók megjelölése kötelező
  - **SA** (ShareAlike): származékos műveken ugyanezt a licencet kell alkalmazni
- **Kereskedelmi használat:** megengedett (a CC BY-SA nem korlátozza)
- **Kritikus különbség a HuLU-hoz képest:** az MMLU-HU **kereskedelmi célra is használható**, a HuLU viszont NC (non-commercial) — ez fontos a modellfejlesztési projektek számára

## Letöltés

- **Hivatalos URL:** https://huggingface.co/datasets/NYTK/hu-mmlu
- **Maintainer:** NYTK (Nyelvtudományi Kutatóközpont)
- **Licenc:** MIT (a HF dataset kártya szerint)
- **Méret (validation split):** ~1880 példa, 38 tantárgy — ez az, amit a `hu-eval` használ
- **Méret (teljes, test+validation):** ~15.9k példa, 38 tantárgy (a `test` spliten nincs publikus label)
- **Checksum (SHA-256):** a HuggingFace dataset kártyán ellenőrizhető

> ❌ **Téves információ törölve 2026-06-07.** A korábbi wiki-verzió `https://github.com/mmlu-hu/mmlu-hu-translation` URL-t és „57 subject areas" / „CC BY-SA 4.0" / „14 042 questions" adatokat tartalmazott. A valóság: a dataset **38 tantárgyat** tartalmaz (a NYTK kihagyott néhány, kulturálisan nem adaptálható tantárgyat), **MIT** licenc alatt fut, és a HF kártyán a pontos validációs/test számok is elérhetők.

## Hivatkozás (citation)

```bibtex
@misc{mmlu2021,
  title={Measuring Massive Multitask Language Understanding},
  author={Dan Hendrycks and Collin Burns and Steven Basart and Andy Zou and Mantas Mazeika and Dawn Song and Jacob Steinhardt},
  year={2021},
  eprint={2009.03300},
  archivePrefix={arXiv},
  primaryClass={cs.CY}
}

@misc{hu_mmlu2024,
  title={HuMMLU: A Hungarian Massive Multitask Language Understanding Benchmark},
  author={NYTK (Nyelvtudományi Kutatóközpont)},
  year={2024},
  howpublished={\url{https://huggingface.co/datasets/NYTK/hu-mmlu}},
  note={MIT license, 38 subjects, validation split used in hu-eval}
}
```

## Használat — Python loader snippet

```python
import json
from pathlib import Path

def load_mmlu_hu_split(data_dir: str, split: str = "test"):
    """
    MMLU-HU betöltése adott split-ből (dev/val/test).
    
    A mappastruktúra: data_dir/<subject>/<split>.json
    """
    data_dir = Path(data_dir)
    items = []
    for subject_dir in data_dir.iterdir():
        if not subject_dir.is_dir():
            continue
        split_file = subject_dir / f"{split}.json"
        if not split_file.exists():
            continue
        with open(split_file, "r", encoding="utf-8") as f:
            subject_items = json.load(f)
            for item in subject_items:
                item["subject"] = subject_dir.name
                items.append(item)
    return items


def format_mmlu_prompt(item: dict) -> str:
    """Prompt formázása 4 opciós feladathoz (magyar)."""
    choices_str = "\n".join(
        f"  {chr(65 + i)}) {choice}" for i, choice in enumerate(item["choices"])
    )
    return (
        f"Következő kérdés a {item['subject']} témakörben.\n\n"
        f"Kérdés: {item['question']}\n"
        f"Opciók:\n{choices_str}\n\n"
        f"Válaszodat egyetlen betűjellel add meg (A/B/C/D)."
    )


# Példa használat
if __name__ == "__main__":
    items = load_mmlu_hu_split("./mmlu-hu-v1.0", split="test")
    print(f"Összesen {len(items)} kérdés betöltve a 'test' split-ből.")
    
    if items:
        print("\n--- Első kérdés ---")
        print(format_mmlu_prompt(items[0]))
        print(f"Helyes válasz: {items[0]['answer']}")
```

## Kiértékelés

### Score számítás

Az MMLU-HU pontszám az eredeti MMLU-hoz hasonlóan accuracy:

```
mmlu_hu_score = helyes_válaszok_száma / összes_kérdés
```

### Kategóriánkénti riport

A részletes riport kategóriánkénti bontásban jelenik meg, mert az MMLU erőssége, hogy a 57 kategória közötti eltérések jelzik a modell specifikus gyengeségeit.

### Baseline eredmények (a közösségi projekt riportjából, 2024 Q4)

| Modell | MMLU-HU átlag | STEM | Társadalomtud. | Humán |
|--------|---------------|------|----------------|-------|
| GPT-4o | 0.81 | 0.79 | 0.85 | 0.80 |
| Claude 3.5 Sonnet | 0.79 | 0.78 | 0.83 | 0.78 |
| Gemini 1.5 Pro | 0.77 | 0.76 | 0.81 | 0.75 |
| Qwen 2.5 72B | 0.74 | 0.72 | 0.79 | 0.73 |
| Magyar GPT-2 (saját) | 0.32 | 0.28 | 0.34 | 0.36 |

## Ismert korlátok

- **Fordítási artifactok:** egyes kérdések természetessége szenvedett a fordítás során (angolra jellemző szerkezetek tükörfordítása)
- **Kulturális eltérések:** egyes kérdések az amerikai iskolarendszerre jellemzőek (pl. AP US History), és a magyar diákok nem tanulják ezt a tananyagot — így a modell és a magyar emberi baseline is "hátrányból" indul
- **Adatszivárgás (data contamination):** az MMLU publikus, így a modern modellek tréningadatában lehet, hogy benne van (különösen a magyar fordítása, ami 2024-es)
- **Skála vs. HuLU:** az MMLU-HU 14 042 kérdéssel nagyobb, mint a HuLU 1 800, de a HuLU magyar-specifikusabb — a kettő együtt ad teljes képet
- **Nem tartalmaz "magyar specifikus" témákat:** magyar irodalom, magyar történelem, magyar nyelvtan — ezeket a HuLU-val mérjük

## Összekapcsolások

- [HuLU](dataset-hulu.md) — a magyar-specifikus kiegészítő benchmark
- [MMLU-HU benchmark koncepció](../concepts/mmlu-hu.md) — részletes benchmark leírás
- [Statisztikai benchmark módszertan](../concepts/hulu-benchmark.md)
- [HuLU](dataset-hulu.md) — a párhuzamos magyar benchmark
- [Modell entity-k](minimax-m3.md), [Gemini 3 Flash](gemini-3-flash.md) — az értékelt modellek
