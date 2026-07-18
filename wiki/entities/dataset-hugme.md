# HuGME Benchmark Dataset (Hungarian Generative Model Evaluation)

*Típus:* entity
*Forrás(ok):* Magyar Generatív Modell Értékelés (HuGME) projekt, ELTE + HUN-REN
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Azonosítás

- **Teljes név:** HuGME — Hungarian Generative Model Evaluation
- **Rövidítés:** HuGME
- **Verzió:** v0.9 (béta, 2025 Q4 — a teljes v1.0 2026 Q1-re várható)
- **Megjelenés:** 2025 Q3 (kezdeményezés), 2025 Q4 (első béta release)
- **Karbantartó:** ELTE Nyelvtechnológia + HUN-REN kutatóintézet

> ⚠️ **Fontos megjegyzés:** A HuGME jelenleg **béta státuszban** van. A projektünkben a v0.9-es bétát használjuk, de a futtatásokat újrafuttatjuk, amint a v1.0 megjelenik. Lásd: [Generatív benchmark módszertan](../concepts/hugme-benchmark.md).

## Cél és tartalom

A HuGME egy **generatív benchmark** magyar LLM-ek számára, ami a statisztikai benchmarkok (HuLU, MMLU-HU) korlátait hidalja át. A HuLU/MMLU-HU csak 4 opciós tudás-kérdéseket mér; a HuGME nyílt végű, szabad szöveges válaszokat igénylő feladatokat tartalmaz.

### Feladattípusok (8 kategória × 30 feladat = 240 feladat)

1. **Szövegértés és következtetés** — hosszabb magyar szövegek olvasása, kérdések megválaszolása
2. **Összefoglalás** — magyar cikkek, dokumentumok tömörítése
3. **Fordítás** — HU ↔ EN, HU ↔ DE, HU ↔ FR
4. **Kreatív írás** — magyar novellák, versek, esszék
5. **Formális szövegalkotás** — hivatalos levelek, szerződések, jelentések
6. **Kód magyarázat** — Python/JavaScript kódrészletek természetes nyelvű magyarázata magyarul
7. **Párbeszéd** — chat-szerű párbeszéd fenntartása magyar nyelven
8. **Elemzés** — magyar nyelvű adatok, szövegek strukturált elemzése

## Formátum

A HuGME **JSONL** formátumban érhető el, plusz egy kiegészítő `rubrics.json` a pontozási útmutatókkal.

### Feladat formátum (JSONL, soronként)

```json
{
  "id": "hugme-001",
  "category": "szövegértés",
  "difficulty": "közepes",
  "prompt": "Olvasd el az alábbi újságcikket, és válaszolj a kérdésekre.\n\n[cikk szövege, ~500 szó]\n\n1. Mi a cikk fő állítása?\n2. Milyen érveket hoz a szerző?",
  "reference_answer": "A cikk fő állítása, hogy ... A szerző érvei között ...",
  "rubric_id": "hugme-rubric-szovegertes-001",
  "max_length_tokens": 800,
  "language": "hu"
}
```

### Rubric formátum (külön fájl)

```json
{
  "id": "hugme-rubric-szovegertes-001",
  "category": "szövegértés",
  "criteria": [
    {"name": "pontosság", "weight": 0.4, "scale": [1, 5], "description": "A válasz mennyire felel meg a referencia-válasznak ténybelileg?"},
    {"name": "teljesség", "weight": 0.3, "scale": [1, 5], "description": "A válasz mennyire fedi le a kért szempontokat?"},
    {"name": "koherencia", "weight": 0.2, "scale": [1, 5], "description": "Mennyire logikus a válasz?"},
    {"name": "nyelvhelyesség", "weight": 0.1, "scale": [1, 5], "description": "Mennyire helyes a magyar nyelvhasználat?"}
  ]
}
```

### Mezők leírása

- `id` — egyedi feladat azonosító
- `category` — feladattípus kategória
- `difficulty` — "könnyű" / "közepes" / "nehéz"
- `prompt` — a feladat szövege (a modell ezt kapja)
- `reference_answer` — emberi referencia-válasz
- `rubric_id` — a pontozási rubrika azonosítója
- `max_length_tokens` — a generált válasz maximális hossza
- `language` — a feladat nyelve (jelenleg csak "hu")

## Licenc

- **Licenc típusa:** Creative Commons BY-NC-SA 4.0
- **Korlátozás:** a HuGME-vel fine-tune-olt modellek nem publikálhatók kereskedelmi célra
- **Kivétel:** a HuGME publikus értékelési eredmények (a modellek válaszai) szabadon megoszthatók

## Letöltés

- **Hivatalos URL:** https://huggingface.co/datasets/hugme/hugme-v0.9
- **Verzió:** v0.9-beta
- **Méret:** ~1.8 MB (JSONL) + ~120 KB (rubrics.json)

## Hivatkozás (citation)

```bibtex
@misc{hugme2025,
  title={HuGME: Hungarian Generative Model Evaluation Benchmark (Beta)},
  author={HuGME Consortium and {Németh, T.} and {Tóth, K.} and {Varga, R.}},
  year={2025},
  howpublished={\url{https://huggingface.co/datasets/hugme/hugme-v0.9}},
  note={v0.9-beta, 240 tasks, 8 categories, CC BY-NC-SA 4.0}
}
```

## Használat — Python loader snippet

```python
import json
from collections import Counter

def load_hugme_tasks(path: str = "hugme-v0.9-tasks.jsonl"):
    """HuGME feladatok betöltése."""
    tasks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


def load_rubrics(path: str = "hugme-v0.9-rubrics.json"):
    """HuGME rubrikák betöltése (rubric_id -> criteria dict)."""
    with open(path, "r", encoding="utf-8") as f:
        rubrics_list = json.load(f)
    return {r["id"]: r for r in rubrics_list}


def get_rubric_for_task(task: dict, rubrics: dict):
    """Adott feladathoz tartozó rubrika lekérése."""
    return rubrics.get(task["rubric_id"])


if __name__ == "__main__":
    tasks = load_hugme_tasks()
    rubrics = load_rubrics()
    print(f"Összesen {len(tasks)} HuGME feladat, {len(rubrics)} rubrika betöltve.")
    
    cats = Counter(t["category"] for t in tasks)
    print("\nKategóriánkénti eloszlás:")
    for cat, count in cats.most_common():
        print(f"  {cat}: {count}")
```

## Kiértékelés — LLM-as-a-Judge

A HuGME pontozása **NEM** egyszerű accuracy, hanem többkritériumos pontozás.

### Pontozási séma

1. **Bíró modell:** Gemini 3 Flash Preview (a Kimi K2.6 bíró státusz törölve 2026-06-07, v1.2.4) ([kimi-k2.6](kimi-k2.6.md))
2. **Rubrika-alapú pontozás:** minden feladatra a saját rubrikája
3. **Adjudicáció:** ha a bíró és az emberi spot-check között >1.5 pont eltérés van, a Qwen 3.5 397B a harmadik vélemény
4. **Aggregáció:** kategóriánként súlyozott átlag → HuGME összesített pontszám (1-5 skálán)

### Kategóriánkénti várható pontszámok (becslés)

| Kategória | Top cloud modellek | 4B lokális |
|-----------|-------------------|------------|
| Szövegértés | 4.0-4.4 | 3.0-3.5 |
| Összefoglalás | 3.8-4.2 | 2.8-3.3 |
| Fordítás | 4.2-4.6 | 3.2-3.7 |
| Kreatív írás | 3.5-4.0 | 2.5-3.0 |
| Formális szöveg | 4.0-4.5 | 3.0-3.5 |
| Kód magyarázat | 3.8-4.3 | 2.7-3.2 |
| Párbeszéd | 3.6-4.0 | 2.6-3.1 |
| Elemzés | 3.9-4.3 | 2.9-3.4 |

## Ismert korlátok

- **Béta státusz** — a feladatok egy része még validálatlan, a rubrikák csiszolódnak
- **Bíró függőség** — az LLM-as-a-Judge megközelítés inherens szubjektivitást hordoz (lásd: [Bíró elfogultságok](../concepts/llm-as-judge.md))
- **NC licenc** — a HuGME-vel fine-tune-olt modellek nem publikálhatók kereskedelmi célra
- **Kis minta (240 feladat)** — kategóriánként 30 feladat, statisztikailag korlátozott
- **Magyar-specifikus kreativitás** — a "kreatív írás" kategória erősen szubjektív, a bírók közötti egyetértés itt a legalacsonyabb
- **Idő- és költségigényes** — 240 feladat × 6 modell × bíró pontozás = 1440 LLM hívás

## Összekapcsolások

- [Generatív benchmark módszertan](../concepts/hugme-benchmark.md)
- [LLM-as-a-Judge](../concepts/llm-as-judge.md) — a pontozás módja
- [Kimi K2.6](kimi-k2.6.md) — benchmark modell (bíró státusz törölve 2026-06-07, v1.2.4)
- [Qwen 3.5 397B](qwen3.5-397b.md) — adjudicátor
- [MT-Bench-HU](dataset-mt-bench-hu.md) — másik generatív benchmark, kiegészítő
- [Bíró elfogultságok](../concepts/llm-as-judge.md) — ismert limitációk
