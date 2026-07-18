# MMLU-HU

*Típus:* concept
*Forrás(ok):* https://github.com/hendrycks/test — MMLU eredeti benchmark; https://huggingface.co/datasets/NYTK/hu-mmlu — magyarított HuggingFace dataset (NYTK, MIT licenc); https://github.com/EleutherAI/lm-evaluation-harness — kiértékelő keretrendszer
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-16 (v1.2.11 — runner implementálva: `run_mmlu_hu.py`, 5-shot, 38 subject)

---

## Mi az MMLU?

A **MMLU** (Massive Multitask Language Understanding) a Hendrycks et al. (2021) által publikált benchmark, amely 57 tantárgyat fed le, az általános iskolai szinttől („Elementary Mathematics") a posztgraduális szintig („Professional Law"). Minden tantárgy 4-opciós multiple-choice kérdésekből áll, és együttesen a modell **széles körű tudását + a kérdés szövegének pontos értelmezését** méri.

Az **MMLU-HU** az eredeti MMLU magyar fordítása, amelyet a NYTK készített és HuggingFace dataset formájában tett elérhetővé: [NYTK/hu-mmlu](https://huggingface.co/datasets/NYTK/hu-mmlu) (MIT licenc). A fordítás két lépésben készült: gépi fordítás (angol→magyar) + professzionális humán poszt-editorság a minőségbiztosításhoz. A cél az volt, hogy a magyar nyelvű modellek ugyanazokon a kérdéseken legyenek mérhetők, mint az angol nyelvűek, így a nemzetközi összehasonlítás is értelmezhető.

> 🛠️ **Implementációs státusz (2026-06-16, v1.2.11):** a `hu-eval` projektben a teljes pipeline kész: `scripts/download_mmlu_hu.py` (letöltés, CONFIG=all, dev split) → `scripts/run_mmlu_hu.py` (5-shot runner, 38 subject, num_predict=32, timeout=120) → `scripts/aggregate_results.py` (STAT lista). A `breakdown_report.py --benchmark mmlu_hu` per-subject bontást generál.

## A 38 tantárgy kategóriái

> ⚠️ **Pontos szám (2026-06-07):** a NYTK/hu-mmlu dataset **38 tantárgyat** tartalmaz, nem 57-et — a NYTK a fordítás során kihagyott néhány, kulturálisan nem adaptálható tantárgyat (pl. amerikai jog, US History). A tantárgylistát lásd lent.

Az MMLU-HU tantárgyai 4 fő kategóriába sorolhatók:

### 1. Humán tudományok (Humanities)
Filozófia, morálfilozófia, világvallások, jog, nemzetközi jog, politikatudomány, közgazdaságtan, társadalomismeret, történelem (világ-, európai), irodalomelmélet, szépirodalmi elemzés, logika, logikai hibák.

### 2. Társadalomtudományok (Social Sciences)
Közgazdaságtan, pszichológia, szociológia, politika, közpolitika, közegészségügy, középiskolai makroökonómia, középiskolai mikroökonómia, középiskolai kormányzat, középiskolai politológia, középiskolai pszichológia, középiskolai európai történelem, középiskolai világtörténelem, középiskolai földrajz.

### 3. Természettudományok, technika, matematika (STEM)
Absztrakt algebra, anatómia, csillagászat, biológia, üzleti statisztika, kémia, klinikai orvostan, számítástudomány, egyetemi kémia, egyetemi fizika, egyetemi matematika, gépi tanulás, középiskolai biológia, középiskolai kémia, középiskolai számítástudomány, középiskolai matematika, középiskolai statisztika, középiskolai fizika.

### 4. Egyéb (Other)
Általános orvosi ismeretek, humán öregedés, jogi etika, klinikai ismeretek, orvosi ismeretek, ápolás, táplálkozás, szakmai pszichológia, szakmai orvoslás, szakmai jog.

> ⚠️ A tantárgyak pontos listája a `NYTK/hu-mmlu` `config_name == "all"` splitjében érhető el, a `subject` mezőben. A `dev` split (5 példa/tantárgy) a few-shot prompting alapja; a `validation` (1.88k példa) a kiértékeléshez; a `test` (14.1k) publikus label-ek nélkül — ez utóbbi a NYTK értékelőszerverére küldendő.

## 5-shot prompting — miért pont 5?

Az MMLU alapértelmezett protokollja az **5-shot prompting**: minden egyes kérdés megválaszolása előtt a modell 5 másik, ugyanabból a tantárgyból származó kérdés-helyes válasz párost lát példaként. Ezt a technikát Hendrycks et al. azért választották, mert:

- **0-shot** (példa nélkül) túl sokat büntet: a modell nem tudja, milyen formátumban kell válaszolni.
- **1-shot** néha félrevezető, ha a példa „nehéz" vagy „könnyű".
- **5-shot** empirikusan a legjobb tradeoff pontosság és kontextméret között.
- **Few-shot több** (pl. 10-shot) nem javít számottevően, de lassítja a futtatást.

### Példa 5-shot promptra (magyar, leegyszerűsített)

```
Kérdés: Mi a fővárosa Magyarországnak?
A) Budapest
B) Debrecen
C) Szeged
D) Pécs
Válasz: A

Kérdés: Melyik évben volt a mohácsi vész?
A) 1492
B) 1526
C) 1541
D) 1571
Válasz: B

Kérdés: Mi a fotoszintézis?
A) ... B) ... C) ... D) ...
Válasz: C

Kérdés: Ki írta az "Egri csillagokat"?
A) Jókai Mór
B) Gárdonyi Géza
C) Móricz Zsigmond
D) Mikszáth Kálmán
Válasz: B

Kérdés: Melyik bolygó a legnagyobb a Naprendszerben?
A) Föld  B) Mars  C) Jupiter  D) Szaturnusz
Válasz: C

Kérdés: Mi az entrópia a termodinamikában?
A) A rendezetlenség mértéke
B) A hőmérséklet mértéke
C) A nyomás mértéke
D) Az energia mértéke
Válasz:
```

A modell feladata egyetlen betű kiadása: A, B, C vagy D.

## Pontosság-számítás

### Subject-level accuracy

Minden tantárgyban a helyesen megválaszolt kérdések aránya:

```python
def subject_accuracy(preds: list[str], labels: list[str]) -> float:
    """preds: ['A','B','C','D'], labels: ['A','B','C','D']"""
    assert len(preds) == len(labels)
    correct = sum(p == l for p, l in zip(preds, labels))
    return correct / len(labels)
```

### Overall accuracy (mikro-átlag)

Az egész MMLU-HU-n a helyes válaszok összaránya (súlyozva a tantárgyak méretével):

```python
def overall_accuracy(all_preds: dict[str, list[str]], all_labels: dict[str, list[str]]) -> float:
    total_correct = 0
    total = 0
    for subj in all_preds:
        c = sum(p == l for p, l in zip(all_preds[subj], all_labels[subj]))
        total_correct += c
        total += len(all_labels[subj])
    return total_correct / total
```

### Macro-átlag (kategóriánként)

Néha kategóriánkénti (Humanities/Social Sciences/STEM/Other) átlagot is néznek, és ezek átlaga a **macro-score**. Ez kiegyensúlyozottabb, mint a sima mikro-átlag, mert a kisebb tantárgyak is azonos súllyal esnek latba.

## Subject-by-subject bontás stratégiája

### Miért fontos a tantárgy-szintű riport?

Két modell azonos **overall accuracy**-t érhet el, de teljesen más profillal:
- Modell A: STEM-ből 80%, Humanities-ből 40%
- Modell B: STEM-ből 50%, Humanities-ből 70%

A felhasználó számára (pl. „magyar nyelvésznek kell modell") ez a bontás sokkal informatívabb.

### Ajánlott riport-formátum

> ⚠️ A táblázatban szereplő `N=14042` és `57 tantárgy` a **teljes MMLU-HU** (test + validation együtt) értéke. A `hu-eval` projekt jelenleg csak a **validation** splitet használja (`NYTK/hu-mmlu` "default" config — ez az egyetlen config, és a 38 tantárgyat egyesítve tartalmazza, ~1880 példa) — tehát a táblázat N-jait le kell szorítani a hu-eval futásban.

```markdown
| Tantárgy | kategória | Pontosság | 95% CI | N |
|----------|-----------|-----------|--------|---|
| Elemi matematika | STEM | 78% | [76, 80] | 480 |
| Magyar irodalom | Humanities | 62% | [59, 65] | 410 |
| ... |
| **Átlag (mikro, validation)** | — | **64.3%** | — | 1880 |
| **Átlag (makro, validation)** | — | **62.1%** | — | 38 |
```

### Bootstrap konfidenciaintervallum

Az egyes tantárgyak pontosságához érdemes **95%-os bootstrap CI**-t is számolni (különösen kis N-ű tantárgyaknál, ahol 5-6 válasz eltérése is nagyot mozgat a százalékon):

```python
import numpy as np

def bootstrap_ci(preds, labels, n_boot=1000, alpha=0.05):
    """95%-os bootstrap CI a pontosságra."""
    preds = np.array(preds)
    labels = np.array(labels)
    n = len(labels)
    accs = []
    for _ in range(n_boot):
        idx = np.random.randint(0, n, size=n)
        accs.append((preds[idx] == labels[idx]).mean())
    lo = np.percentile(accs, 100 * alpha / 2)
    hi = np.percentile(accs, 100 * (1 - alpha / 2))
    return lo, hi
```

### Tantárgy-csoportok riportja

Készítsünk külön összesítést kategóriánként:

```python
CATEGORIES = {
    "Humanities":     ["filozófia", "vallás", "jog", ...],
    "Social Sciences":["pszichológia", "szociológia", "politika", ...],
    "STEM":           ["matematika", "fizika", "kémia", ...],
    "Other":          ["orvoslás", "egészségügy", ...],
}

def category_score(subj_scores: dict[str, float]) -> dict[str, float]:
    out = {}
    for cat, subjects in CATEGORIES.items():
        scores = [subj_scores[s] for s in subjects if s in subj_scores]
        out[cat] = sum(scores) / len(scores) if scores else 0.0
    return out
```

## Futtatás a `hu-eval` projektben

> ✅ **A teljes pipeline kész (v1.2.11).** A `scripts/download_mmlu_hu.py` letölti és standardizálja a `NYTK/hu-mmlu` validation + dev splitjét, a `scripts/run_mmlu_hu.py` futtatja a 5-shot benchmarkot, a `scripts/aggregate_results.py` felismeri az eredményeket.

### Pipeline

```bash
# 1. Letöltés (egyszeri)
python scripts/download_mmlu_hu.py

# 2. Benchmark futtatás (resume-aware, mint a HuLU)
python scripts/run_mmlu_hu.py --model qwen3.5:4b
python scripts/run_mmlu_hu.py --model qwen3.5:4b --limit 50    # smoke test
python scripts/run_mmlu_hu.py --model qwen3.5:4b --mode think   # think mód
python scripts/run_mmlu_hu.py --model qwen3.5:4b --status       # csak állapot

# 3. Aggregáció (a meglévő aggregate_results.py automatikusan felismeri)
python scripts/aggregate_results.py

# 4. Per-subject breakdown
python scripts/breakdown_report.py --benchmark mmlu_hu
```

### Kimenet

A runner minden modellre 38 tantárgyankénti accuracy-t számol, és a summary JSON-ba írja a macro-átlagot (38 subject egyenlő súlyú átlaga). A `breakdown_report.py --benchmark mmlu_hu` per-subject bontást generál CSV + MD + PNG formátumban.

A kimeneti séma:

```json
{
  "model": "qwen3.5:4b",
  "task": "mmlu_hu",
  "num_fewshot": 5,
  "split": "validation",
  "accuracy": 0.58,
  "subject_scores": {
    "abstract_algebra": {"acc": 0.42, "n": 50},
    "anatomy": {"acc": 0.61, "n": 50},
    ...
  }
}
```

### Korábbi módszer: `mlmm-evaluation` (nem használt)

A NYTK korábban a `nytud/mlmm-evaluation` GitHub repóban publikálta a magyar benchmarkokat (MMLU-HU, ARC-HU, HellaSwag-HU). Ez a pipeline az `lm-evaluation-harness` wrapperét használja, és a teljes MMLU-HU-t (test+validation, 14k példa, 57 tantárgy) futtatja. A `hu-eval` projekt **nem ezt** használja, mert:

- A `mlmm-evaluation` régi, nem karbantartott (utolsó commit 2024 közepe)
- Az `lm-evaluation-harness` 5-shot logikája overhead a mi egyszerű Ollama-`stop_on_error` pipeline-unkhoz képest
- A validation split 1880 példás, így a futás sokkal gyorsabb (5-10 perc/modell, nem 1-2 óra)

Ha valaki mégis a teljes 14k-s MMLU-HU-t akarja futtatni (pl. publikus leaderboard-ra):

```bash
git clone https://github.com/nytud/mlmm-evaluation.git
cd mlmm-evaluation
pip install -e .
python -m mlmm_eval.main \
    --model qwen3.5:4b \
    --tasks mmlu_hu \
    --num-fewshot 5
```

## Gyakori buktatók

1. **A 4 betű nem egyenértékű** — egyes modellek a „C" vagy „D" betűt preferálják (position bias). Ezt a `position_bias_korrekció` részben kezeli, de érdemes riportálni a nyers arányokat.
2. **A modell szöveges magyarázatot ír** — ahelyett, hogy egy betűt adna. A parsernek regex-szel kell kiemelnie az első egyedi A/B/C/D betűt.
3. **A magyar fordítás minősége** — egyes kérdések (pl. „What is the capital of..." típusú amerikanisztikus kérdések) természetellenesen hatnak magyarul. A NYTK jegyzékében van egy `low_quality_flag`, amit érdemes külön riportálni.
4. **A 5-shot prompt tanítópéldái magyarok** — de az eredeti MMLU-példák angol promptját sokszor lefordítják. Ellenőrizd, hogy a példák konzisztens nyelven vannak-e (magyar-magyar, ne magyar-angol keverék).
5. **A „vita" típusú tantárgyak** (filozófia, vallás, politika) kultúrafüggők — egy amerikai vagy magyar vizsgán más a „helyes" válasz. Az MMLU-HU nem kulturálisan adaptált, csak nyelvileg.
6. **Tokenlimit** — az 5-shot promptok hosszúak lehetnek (akár 2000-3000 token), ami a kisebb modelleknél (pl. `qwen3.5:0.8b`) kontextmérethez ütközhet. Ilyenkor érdemes a `max_input_tokens` paramétert csökkenteni vagy kevesebb shot-ot használni.

## Eredmények értelmezése

### Referencia-értékek (angol MMLU, hozzávetőleg)

| Modellméret | MMLU (angol) | magyar MMLU-HU várható |
|-------------|--------------|-------------------------|
| 0.5–1B paraméter | 25–35% (random: 25%) | 26–32% |
| 3–7B paraméter | 45–55% | 38–48% |
| 13–70B paraméter | 60–75% | 50–65% |

A magyar változat jellemzően **5-10 százalékponttal alacsonyabb**, mint az angol, ami a fordítási zajból és a magyar nyelv nehezebb morfológiájából fakad.

> ⚠️ Ezek az értékek csak tájékoztató jellegűek; a tényleges magyar teljesítmény modellenként nagyon változó, és erősen függ attól, hogy a modell milyen arányban látott magyar szöveget a pre-training során.

## Kapcsolódó

- [Overview](../overview.md) — projekt cél
- [SCHEMA](../SCHEMA.md) — wiki-formátum
- [HuLU Benchmark](hulu-benchmark.md) — magyar nyelvértési benchmark
- [ARC + GSM8K-HU](arc-gsm8k-hu.md) — logikai és matematikai feladatok
- [Ollama API kliens](ollama-api-client.md) — modellek hívása
- [Perplexitás](perplexity-hu.md) — nyelvmodell-minőség mérése
