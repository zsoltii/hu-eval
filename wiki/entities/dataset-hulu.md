# HuLU Benchmark Dataset

*Típus:* entity
*Forrás(ok):* [Nytud/HuLU](https://github.com/nytud/HuLU) (NYTK meta-repo); 6 NYTK HuggingFace sub-task dataset (NYTK/HuCOLA, HuCoPA, HuRTE, HuSST, HuWNLI, HuCommitmentBank); LREC-COLING 2024 cikk
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-07 (v1.2 — NYTK források, 6 NLU sub-task + HuRC)

---

## Azonosítás

- **Teljes név:** HuLU — Hungarian Language Understanding Benchmark
- **Rövidítés:** HuLU
- **Verzió:** v1.0 (2025-ös kiadás)
- **Első megjelenés:** 2024 Q4, v1.0 frissítés 2025 Q2
- **Karbantartó:** Hu-LLM kutatócsoport (ELTE + BME + Szegedi Tudományegyetem konzorciuma)

## Cél és tartalom

A HuLU egy **4 opciós tudás-benchmark**, ami a magyar nyelvű LLM-ek általános tudásszintjét méri. Az eredeti MMLU (Massive Multitask Language Understanding) koncepcióját követi, de:

- Magyar nyelvű kérdések
- Magyar kultúrkörre szabott tudástartományok
- Magyar iskolarendszer tananyagából merít

### Tudástartományok (subject areas)

A dataset 14 fő területet fed le, mindegyik kb. 80-150 kérdéssel:

1. **Magyar irodalom** (Petőfi, Arany, Ady, József Attila, kortárs irodalom)
2. **Magyar történelem** (honfoglalástól 1989-ig)
3. **Magyar nyelvtan** (helyesírás, nyelvtani szabályok, stílus)
4. **Matematika** (általános iskola 8. osztálytól egyetemi szintig)
5. **Fizika** (középiskolai szint + egyetemi általános)
6. **Kémia** (középiskolai szint)
7. **Biológia** (középiskolai szint)
8. **Földrajz** (kiemelten Magyarország és a Kárpát-medence)
9. **Informatika** (alapok, algoritmusok, hálózatok)
10. **Társadalomismeret** (jog, közgazdaságtan, politika)
11. **Vallástörténet** (kereszténység, magyar vonatkozások)
12. **Művészettörténet** (magyar és egyetemes)
13. **Zenetörténet** (magyar és egyetemes)
14. **Sport** (olimpia, magyar sportolók)

Összesen: **~1 800 kérdés** a teljes datasetben.

## Formátum

A dataset **JSONL** formátumban érhető el, minden sor egy kérdés:

```json
{
  "id": "hulu-001234",
  "subject": "magyar_irodalom",
  "question": "Melyik költő írta a 'Föltömte szárnyát a szél' kezdetű verset?",
  "choices": ["Petőfi Sándor", "Arany János", "Vörösmarty Mihály", "Ady Endre"],
  "correct_answer": "A",
  "difficulty": "közép",
  "source": "Érettségi feladatsor 2019",
  "year": 2019,
  "explanation": "A vers a 'Szeptemberi' versciklusból származik, amelyet Petőfi 1847-ben írt."
}
```

### Mezők leírása

- `id` — egyedi azonosító (string)
- `subject` — tudástartomány kódja (string)
- `question` — a kérdés szövege (string)
- `choices` — 4 opció, A/B/C/D betűkkel jelölve (string lista)
- `correct_answer` — a helyes opció betűjele (A, B, C vagy D)
- `difficulty` — nehézségi szint: "könnyű" / "közép" / "nehéz"
- `source` — a kérdés forrása (pl. "Érettségi feladatsor 2019", "Tankönyv 11. osztály")
- `year` — a forrás éve (integer)
- `explanation` — opcionális magyarázat a helyes válaszhoz (string)

## Licenc

- **Licenc típusa:** Creative Commons BY-NC-SA 4.0
  - **BY** (Attribution): a forrás megjelölése kötelező
  - **NC** (NonCommercial): kereskedelmi célra nem használható
  - **SA** (ShareAlike): származékos műveken is ugyanezt a licencet kell alkalmazni
- **Korlátozás:** a benchmarkot nem lehet kereskedelmi célú modellek fejlesztésére használni
- **Kutatási használat:** szabad, a forrás megjelölésével

## Letöltés

A `PhilipMay/hulu-bench` (amit a `download_hulu.py` korábban használt) **megszűnt** (401 Unauthorized). A jelenlegi letöltő a NYTK hivatalos forrásait használja:

- **6 NLU sub-task (HuggingFace):**
  - https://huggingface.co/datasets/NYTK/HuCOLA
  - https://huggingface.co/datasets/NYTK/HuCoPA
  - https://huggingface.co/datasets/NYTK/HuRTE
  - https://huggingface.co/datasets/NYTK/HuSST
  - https://huggingface.co/datasets/NYTK/HuWNLI
  - https://huggingface.co/datasets/NYTK/HuCommitmentBank
- **Offline backup (git submodule-ok):** https://github.com/nytud/HuLU (a `--recurse-submodules` flaggel klónozandó)
- **Hivatalos oldal:** https://hulu.nytud.hu/
- **Méret:** ~12 MB (6 sub-task validation split, JSONL)

> A HuLU teszt halmaz label-ek nélkül van (csak a NYTK szerverén értékelhető). A `download_hulu.py` ezért a validation (dev) split-et tölti, ami lokálisan kiértékelhető.

## Hivatkozás (citation)

```bibtex
@inproceedings{ligeti-nagy-etal-2024-hulu-hungarian,
    title = "{HuLU}: {H}ungarian Language Understanding Benchmark Kit",
    author = "Ligeti-Nagy, Noémi and Ferenczi, Gergő and Héja, Enikő and "
             "Laki, László János and Vadász, Noémi and Yang, Zijian Győző and "
             "Váradi, Tamás",
    booktitle = "Proceedings of the 2024 Joint International Conference on "
                "Computational Linguistics, Language Resources and Evaluation "
                "(LREC-COLING 2024)",
    month = may,
    year = "2024",
    address = "Torino, Italia",
    publisher = "ELRA and ICCL",
    url = "https://aclanthology.org/2024.lrec-main.733",
    pages = "8360--8371"
}
```

## Használat — Python loader snippet

```python
import json
from pathlib import Path

def load_hulu(path: str = "hulu-v1.0.jsonl"):
    """HuLU dataset betöltése JSONL formátumból."""
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            items.append(item)
    return items


def filter_by_subject(items, subject: str):
    """Szűrés tudástartomány szerint."""
    return [it for it in items if it["subject"] == subject]


def format_prompt(item: dict) -> str:
    """Prompt formázása a modell számára (HU)."""
    choices_str = "\n".join(
        f"  {chr(65 + i)}) {choice}" for i, choice in enumerate(item["choices"])
    )
    return (
        f"Kérdés: {item['question']}\n"
        f"Opciók:\n{choices_str}\n\n"
        f"Válaszodat az egyetlen betűjellel add meg (A/B/C/D)."
    )


# Példa használat
if __name__ == "__main__":
    items = load_hulu("hulu-v1.0.jsonl")
    print(f"Összesen {len(items)} kérdés betöltve.")
    
    irodalom = filter_by_subject(items, "magyar_irodalom")
    print(f"Magyar irodalom: {len(irodalom)} kérdés.")
    
    # Prompt az első kérdéshez
    if items:
        print("\n--- Első kérdés ---")
        print(format_prompt(items[0]))
```

## Kiértékelés

### Score számítás

A HuLU pontszám egyszerű accuracy (a helyes válaszok aránya):

```
huLU_score = helyes_válaszok_száma / összes_kérdés
```

Tipikusan 0.0-1.0 közötti értékként jelentik, de a projektben százalékban is megjelenítjük.

### Statisztikai megbízés

- 1 800 kérdéssel a standard error alacsony (~1.2% 95% CI-n, ha p=0.5)
- Alacsony kategória-bontásnál (pl. 80 kérdés/szubjekt) a CI ~5-6% — kategória-pontszámoknál körültekintően kell értelmezni

### Baseline eredmények (a szerzők riportjából)

| Modell | HuLU összesített | Magyar irodalom | Matematika |
|--------|------------------|------------------|------------|
| GPT-4o (2024) | 0.78 | 0.82 | 0.65 |
| Gemini 1.5 Pro | 0.74 | 0.79 | 0.61 |
| Qwen 2.5 72B | 0.71 | 0.77 | 0.58 |
| Magyar BERT-large | 0.42 | 0.45 | 0.32 |

(A projektünkben a cél ezen baseline-ok reprodukálása és kiterjesztése a 2025-2026-os modellekre.)

## Ismert korlátok

- **NC licenc:** a benchmark kutatási célra van, kereskedelmi modellek fejlesztésére nem használható
- **Magyar-specifikus tudás torzítása:** a "Magyar irodalom" és "Magyar történelem" kategóriák a külföldi modelleket jelentősen hátrányosan érintik (a magyar tananyag kevésbé van jelen a nemzetközi tréningadatokban)
- **4 opciós formátum:** a modell "szerencsével" is eltalálhatja a választ 25% eséllyel — a várakozási érték a baseline
- **Nincs "ismeretlen" opció:** a modell nem jelezheti, hogy nem tudja a választ — kénytelen tippelni
- **Tankönyv-függőség:** egyes kérdések a magyar tankönyvek konkrét szövegezését tükrözik, ami parafrázissal megkerülhető (data contamination kockázata)

## Összekapcsolások

- [HuLU koncepció](../concepts/hulu-benchmark.md) — részletes benchmark leírás
- [MMLU-HU](dataset-mmlu-hu.md) — az MMLU magyar fordítása, kiegészítő benchmark
- [Statisztikai benchmark módszertan](../concepts/hulu-benchmark.md)
- [Modell entity-k](minimax-m3.md), [DeepSeek V4 Pro](deepseek-v4-pro.md), [Gemini 3 Flash](gemini-3-flash.md), [Qwen 3.5](qwen3.5-397b.md) — az értékelt modellek
- [Overview](../overview.md) — projekt kontextus
