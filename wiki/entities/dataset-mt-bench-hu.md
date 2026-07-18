# MT-Bench-HU (Magyar MT-Bench)

*Típus:* entity
*Forrás(ok):* MT-Bench eredeti (Zheng et al., 2023), magyar fordítás és adaptáció: hu-eval projekt
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Azonosítás

- **Teljes név:** MT-Bench-HU — MT-Bench Hungarian Custom Version
- **Rövidítés:** MT-Bench-HU
- **Verzió:** v1.0 (2025-ös kiadás)
- **Megjelenés:** 2025 Q3
- **Karbantartó:** hu-eval projekt (az [Overview](../overview.md) projekt keretében)

> ⚠️ **Testreszabás:** Az MT-Bench-HU nem pusztán az eredeti MT-Bench gépi fordítása — magyar nyelv és kultúra sajátosságaira szabott, egyedi feladatokkal kiegészített verzió.

## Cél és háttér

Az MT-Bench-et (Multi-turn Benchmark) Lianmin Zheng és mtsi. publikálták 2023-ban ([arXiv:2306.05685](https://arxiv.org/abs/2306.05685)), mint a chat-modellek többfordulós (multi-turn) párbeszéd-képességét mérő benchmarkot.

Az **MT-Bench-HU** projektünkben a magyar nyelvre adaptált verzió:

1. Az eredeti 80 feladat magyarra fordítva + magyar kultúrkörre szabva
2. 20 új, kifejezetten magyar specifikus feladat
3. Magyar nyelvű pontozási útmutató (rubric) a bíró modell számára

## Tartalom

### Kategóriák (8 kategória, 100 feladat összesen)

1. **Írás** (writing) — 10 feladat
2. **Szerepjáték** (roleplay) — 10 feladat
3. **Érvelés** (reasoning) — 10 feladat
4. **Matematika** (math) — 10 feladat
5. **Kódolás** (coding) — 10 feladat
6. **Kivonatolás** (extraction) — 10 feladat
7. **STEM** — 10 feladat
8. **Humán tudományok** (humanities) — **30 feladat** (magyar irodalom, történelem, nyelvészet)

### Felépítés

- Minden feladat **2 fordulós** (multi-turn)
- 1. forduló: általános kérdés
- 2. forduló: follow-up, ami a modell válaszára épít

### Példa (magyar, "Írás" kategóriából)

```
1. forduló: "Írj egy 300 szavas esszét a 'Hagyomány és modernitás' témáról
magyar ifjúsági szemszögből. Az esszé legyen személyes hangvételű..."

2. forduló: "Rövidítsd le az esszét 150 szóra, megtartva a személyes hangvételt
és a konkrét példát. Milyen kompromisszumokat kellett kötnöd?"
```

## Formátum

A dataset **JSONL** formátumban érhető el:

```json
{
  "id": "mt-bench-hu-001",
  "category": "writing",
  "turns": [
    "Írj egy 300 szavas esszét a 'Hagyomány és modernitás' témáról...",
    "Rövidítsd le az esszét 150 szóra..."
  ],
  "reference_answer": "Referencia magyar esszé, amit emberi szakértő írt...",
  "rubric": {
    "fluency": {"weight": 0.2, "scale": [1, 10], "description": "Magyar nyelvhelyesség, stílus folyékonysága"},
    "relevance": {"weight": 0.3, "scale": [1, 10], "description": "A téma pontos megragadása"},
    "coherence": {"weight": 0.2, "scale": [1, 10], "description": "Logikus gondolatmenet, koherencia"},
    "creativity": {"weight": 0.2, "scale": [1, 10], "description": "Egyediség, kreativitás"},
    "cultural_sensitivity": {"weight": 0.1, "scale": [1, 10], "description": "Magyar kulturális kontextus kezelése"}
  },
  "tags": ["magyar_kultura", "essze", "ifjusagi"]
}
```

### Mezők leírása

- `id` — egyedi feladat azonosító
- `category` — kategória kódja (writing, roleplay, reasoning, math, coding, extraction, stem, humanities)
- `turns` — a két forduló prompt-szövege
- `reference_answer` — emberi szakértői referencia-válasz
- `rubric` — pontozási rubrika
- `tags` — tematikus címkék

## Eltérések az eredeti MT-Bench-hez képest

| Dimenzió | Eredeti MT-Bench | MT-Bench-HU |
|----------|------------------|-------------|
| Nyelv | Angol | Magyar |
| Feladatok száma | 80 | 100 (80 fordítva + 20 magyar specifikus) |
| Pontozás | GPT-4 judge | Kimi K2.6 judge + Qwen 397B adjudicáció |
| Cultural sensitivity | nincs | súlyozott szempont (5-10%) |

## Licenc

- **Az eredeti MT-Bench licence:** Apache 2.0
- **Az MT-Bench-HU magyar verzió licence:** Creative Commons BY-NC-SA 4.0
- **Korlátozás:** kereskedelmi célra a benchmark nem használható

## Letöltés

- **Hivatalos URL:** https://huggingface.co/datasets/hu-eval/mt-bench-hu-v1.0
- **Méret:** ~2.1 MB (JSONL, tömörítés nélkül)

## Hivatkozás (citation)

```bibtex
@inproceedings{mtbench2023,
  title={Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena},
  author={Lianmin Zheng and Wei-Lin Chiang and Ying Sheng and Siyuan Zhuang and Zhanghao Wu and Yonghao Zhuang and Zi Lin and Zhuohan Li and Dacheng Li and Eric P. Xing and Hao Zhang and Joseph E. Gonzalez and Ion Stoica},
  booktitle={NeurIPS Datasets and Benchmarks Track},
  year={2023}
}

@misc{mtbenchhu2025,
  title={MT-Bench-HU: Hungarian Custom Multi-turn Benchmark for LLMs},
  author={hu-eval Project Team},
  year={2025},
  howpublished={\url{https://huggingface.co/datasets/hu-eval/mt-bench-hu-v1.0}},
  note={v1.0, 100 tasks, 8 categories, CC BY-NC-SA 4.0}
}
```

## Használat — Python loader snippet

```python
import json
from collections import Counter

def load_mt_bench_hu(path: str = "mt-bench-hu-v1.0.jsonl"):
    """MT-Bench-HU feladatok betöltése."""
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def format_two_turn_prompt(task):
    return [{"role": "user", "content": t} for t in task["turns"]]

# Példa használat
tasks = load_mt_bench_hu()
print(f"Összesen {len(tasks)} feladat.")
for cat, n in Counter(t["category"] for t in tasks).most_common():
    print(f"  {cat}: {n}")
```

## Kiértékelés

### Pontozási séma

1. **Bíró modell:** Gemini 3 Flash Preview (a Kimi K2.6 bíró státusz törölve 2026-06-07, v1.2.4) (lásd: [kimi-k2.6](kimi-k2.6.md))
2. **Skála:** 1-10 (10 a legjobb)
3. **Rubrika-alapú** pontozás
4. **Adjudicáció:** ha a bíró és az emberi spot-check között >2 pont eltérés, a Qwen 3.5 397B a harmadik vélemény

### Baseline eredmények (projekt belső riport)

| Modell | MT-Bench-HU átlag | Writing | Humanities | Math | Coding |
|--------|-------------------|---------|------------|------|--------|
| GPT-4o (2024) | 8.4 | 8.5 | 8.7 | 7.8 | 8.0 |
| Claude 3.5 Sonnet | 8.2 | 8.3 | 8.5 | 7.6 | 7.9 |
| Gemini 3 Flash | 7.6 | 7.8 | 8.1 | 7.0 | 7.2 |
| Qwen 3.5 397B | 8.0 | 8.1 | 8.4 | 7.4 | 7.6 |
| MiniMax M3 | 7.3 | 7.4 | 7.6 | 6.8 | 7.0 |

## Ismert korlátok

- **NC licenc** — a benchmark kereskedelmi célra nem használható
- **Bíró függőség** — a Kimi K2.6 magyar pontozásában van szubjektivitás
- **Kis feladatszám** — 100 feladat statisztikailag korlátozott
- **Fordítási artifactok** — a kulturális kontextus néha elveszhet a fordítás során
- **Multi-turn értékelés nehézsége** — a 2. forduló pontozása nehezebb (nincs referencia)
- **"Magyar specifikus" elfogultság** — a 20 magyar specifikus feladat hátrányosan érinti a külföldi modelleket

## Összekapcsolások

- [MT-Bench-HU benchmark koncepció](../concepts/mt-bench-hu.md) — részletes leírás
- [LLM-as-a-Judge](../concepts/llm-as-judge.md) — a pontozás módja
- [Kimi K2.6](kimi-k2.6.md) — benchmark modell (bíró státusz törölve 2026-06-07, v1.2.4)
- [Qwen 3.5 397B](qwen3.5-397b.md) — adjudicátor
- [HuGME](dataset-hugme.md) — másik generatív benchmark, kiegészítő
- [Bíró elfogultságok](../concepts/llm-as-judge.md) — ismert limitációk
- [Pozíció-bias](../concepts/llm-as-judge.md) — a bíró specifikus gyengesége
