# Riport — Lokális Qwen3-Next-80B IQ3_XXS (mindig think)

*Típus:* report
*Forrás(ok):* hu-eval projekt belső, [Overview](../overview.md), [Riport Aggregáció](../runbooks/aggregate-results.md), [Riport Sablon](riport-template.md)
*Létrehozva:* 2026-07-25
*Frissítve:* 2026-07-25

---

## Fejléc

| Mező | Érték |
|------|-------|
| Riport azonosító | `hu-eval-20260725-lokalis-qwen3-next` |
| Riport dátum | 2026-07-25 |
| Értékelt modellek | `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` |
| Operator | `fater.zsolt` |
| Riport státusz | `draft` |

> **Bíró modell** (LLM-as-a-Judge): `deepseek-v4-pro:cloud` — a `gemini-3-flash-preview:latest` 2026-07-14. 09:00 CEST óta nem elérhető (Ollama megszűnés), helyette ez a hivatalos bíró (2026-07-19 óta). **Self-bias korlát (SZENT):** a bíró modell nem értékelheti saját magát — a `deepseek-v4-pro` saját HuGME/MT-Bench-HU sorait független bíróval vagy kivételzéssel kell kezelni.

### Modell-kvantálás

| Modell | Kvantálás | Backend |
|--------|-----------|---------|
| `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` | IQ3_XXS (3.06 bpw GGUF, 32.95 GB) | `openai` (llama-server `http://localhost:8080/v1`) |

> **Mód:** a modell **csak gondolkodó (think) módban fut** — a llama-server `reasoning_format: none` beállítása nem kapcsolja ki a CoT-t ezen a thinking modellen. Az `--mode nothink` flag hatástalan; a modell minden promptnál CoT-t generál. Nincs külön nothink mód.

### Időkeret

- **Mérés indítása:** 2026-07-19 09:32
- **Mérés befejezése:** 2026-07-19 22:08
- **Teljes futásidő:** ~10 óra (processzoridő, soros futtatás)

## Executive Summary

Ez a riport az `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` modell (3.06 bpw GGUF kvantálás, llama-server backend) eredményeit tartalmazza a 4 elérhető benchmarkon (HuLU, MMLU-HU, HuGME, MT-Bench-HU) **think módban**. A modell egy thinking modell, amely a llama-server backend miatt minden promptnál gondolkodik — az `--mode nothink` flag ellenére nincs nothink mód. Az UD Hungarian benchmark **N/A** — a modell CoT-fogyasztása miatt a kontextusablak (eredetileg 16K) nem volt elegendő a CoNLL-U kimenethez.

A modell a statisztikai benchmarkokon (HuLU 56.5%, MMLU-HU 86.9%) erős eredményt ért el a kvantáltsági szintjéhez képest. A generatív benchmarkokon (HuGME 0.828, MT-Bench-HU 0.375 win-rate) közepesen teljesített. A composite score (40/40/20 súlyozott) **0.659**.

### Főbb számok egy sorban

- **Think composite score (40/40/20):** `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` — **65.93%**
- **HuLU think:** 56.53%
- **MMLU-HU think:** 86.87%
- **HuGME think:** 82.83%
- **UD Hungarian:** **N/A** (a modell CoT-fogyasztása minden esetben kimeríti a kontextusablakot)
- **Legnagyobb meglepetés:** a modell a HuWNLI sub-task-on (lexicalis következtetés) csak 13.3%-ot ért el, ami messze a leggyengébb sub-task.

## Per-benchmark eredmények

### HuLU eredmények (statisztikai — 6 NLU sub-task)

> **Mit tesztel:** a magyar nyelvű természetes nyelvmegértést (NLU) méri 6 al-benchmarkon: HuCOLA (nyelvtani elfogadhatóság), HuCoPA (közös előfordulás / ok-okozat), HuRTE (szöveg-entailment, háromirányú), HuSST (szentiment, 5 osztály), HuWNLI (lexicalis következtetés, legnehezebb), HuCB (CommitmentBank — beszédaktus/elköteleződés). Kimenet: egyesített accuracy + per-sub-task bontás.

| Modell | Mód | Pontosság (%) | Megjegyzés |
|--------|-----|---------------:|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **56.53%** | llama-server, mindig gondolkodik |

**Legjobb:** _Összehasonlítási alap nélkül nem értelmezhető._

**Per-sub-task bontás (KÖTELEZŐ):**

| Sub-task | Pontosság (%) | Helyes / Összes |
|----------|---------------:|----------------:|
| HuCOLA | 51.54% | 469/910 |
| HuCoPA | 90.00% | 90/100 |
| HuRTE | 72.84% | 177/243 |
| HuSST | 57.00% | 664/1165 |
| HuWNLI | 13.33% | 8/60 |
| HuCB | 49.51% | 51/103 |

**Érdekes megfigyelések:**

- A HuCoPA (ok-okozat) 90.0%-os eredménye kiemelkedő — a modell jól kezeli a magyar nyelvű precedencia-viszonyokat.
- A HuWNLI (lexicalis következtetés) 13.3%-a messze a leggyengébb sub-task. Ez a legnehezebb NLU feladat a 6 közül, de a pontosság így is meglepően alacsony.
- A HuCB (CommitmentBank) 49.5%-a lényegében random guess szint.

### MMLU-HU eredmények (statisztikai — 38 tantárgy, 5 kevés lövés)

> **Mit tesztel:** a többválasztós, tantárgy-specifikus tudást (magyar MMLU) 38 tantárgyban, 5-shot felállításban. Méri az általános tudást és reasoninget; kimenet: tantárgyak átlagolt accuracy-ja (0-1).

| Modell | Mód | Pontosság (%) | Megjegyzés |
|--------|-----|---------------:|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **86.87%** | 1303/1500 |

**Legjobb:** _Összehasonlítási alap nélkül nem értelmezhető._

> A 86.87% erős eredmény a 3.06 bpw kvantáláshoz képest. Az 5-shot MMLU-HU promptok azonban hosszúak lehetnek, és a modell CoT-fogyasztása miatt a `num_predict=4096` néha kevés volt (lásd limitációk).

### HuGME eredmények (generatív, LLM-as-a-Judge — 6 metrika, 300 item)

> **Mit tesztel:** a nyílt, szabad szöveges generálást (NYTK HuGME) LLM-as-a-Judge módszerrel, 6 metrikán (relevance, coherence, fluency, informativeness, harmlessness, overall) 300 itemen. Kimenet: a 6 metrika átlagolt judge-score-ja (0-1).

| Modell | Mód | Judge score | Judged subset | Megjegyzés |
|--------|-----|------------:|---------------|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **0.828** | 300/300 | judge: `deepseek-v4-pro:cloud` |

**Legjobb:** _Összehasonlítási alap nélkül nem értelmezhető._

> A HuGME judge 6 metrika átlaga: relevance, coherence, fluency, informativeness, harmlessness, overall. A bíró modell részletei a [Függelék](#függelék--nyers-adatok-helye) szekcióban.

### MT-Bench-HU eredmények (generatív, GSB multi-baseline — 24 item × 3 baseline)

> **Mit tesztel:** a kétfordulós (2-turn) párbeszédes képességet és utasításkövetést magyarul, 24 kérdésen (8 kategória × 3). A válaszokat egy bíró modell GSB (good/bad/same) pairwise módon hasonlítja össze 3 baseline modell ellen, counterbalanced (swap) elrendezésben. Kimenet: win-rate (0-1).

| Modell | Mód | Score (%) | W/L/T | Megjegyzés |
|--------|-----|----------:|-------|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **37.50%** | 1W/7L/16T | baseline: deepseek-v4-flash:cloud |

**Legjobb:** _Összehasonlítási alap nélkül nem értelmezhető._

> A 37.5% = (1 + 16/2) / 24: 1 győzelem, 7 vereség, 16 döntetlen a `deepseek-v4-flash:cloud` baseline ellen. A magas döntetlen-arány (66.7%) azt sugallja, hogy a bírónak gyakran nem sikerült különbséget tennie a két modell között, ami a kvantált modell és a cloud baseline közti kisebb minőségbeli különbségre utal.

### UD Hungarian eredmények (nyelvészeti — CoNLL-U, UPOS/UAS/LAS)

> **Mit tesztel:** a magyar nyelvtani elemzést (Universal Dependencies, Szeged UD test corpus). A modellnek CoNLL-U formátumban kell megadnia a tokenizációt, UPOS címkéket, fej-tokeneket és dependency relációkat. Kimenet: UPOS + UAS + LAS súlyozatlan átlaga (0-1).

| Modell | Mód | Composite | UPOS | UAS | LAS | Megjegyzés |
|--------|-----|----------:|-----:|----:|----:|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **N/A** | N/A | N/A | N/A | a modell CoT-re használja a kontextust |

**Legjobb:** _Nem értékelhető._

> **Részletes magyarázat:** A Qwen3-Next-80B egy thinking modell. A llama-server `reasoning_format: none` ellenére a modell **minden prompt előtt gondolkodik**. Eredetileg 16K kontextussal futott — a CoT ezt kimerítette, és `num_predict=4096` (a rendelkezésre álló token limit) kevés volt a CoNLL-U generáláshoz; a válaszok `finish_reason: length` miatt csonkultak. Később 64K-ra emelt kontextussal és `max_tokens` limit nélkül a modell már produkált valid CoNLL-U kimenetet (7 és 10 oszlopos formátumban is), de a prompt pontosítása a formátumleírással és példamondattal még szükséges a megbízható működéshez. A jelen riportban szereplő eredmények **még a 16K-s kontextussal készültek**.

## Kompozit score-ok

A [Modell vs. Modell](../comparisons/modell-vs-modell.md) és az [AGENTS.md](../../AGENTS.md) által definiált **kötelező 40/40/20 súlyozás** (NE változtatható):

```
composite = 0.40 × statisztikai + 0.40 × generatív + 0.20 × nyelvészeti
```

Ahol:

- **statisztikai** = átlag(HuLU, MMLU-HU) = (0.5653 + 0.8687) / 2 = 0.7170
- **generatív** = átlag(HuGME, MT-Bench-HU) = (0.8283 + 0.3750) / 2 = 0.6017
- **nyelvészeti** = N/A (UD Hungarian nem elérhető)

> Mivel a nyelvészeti dimenzió teljesen hiányzik, a súlyok a jelenlévő dimenziókra oszlanak arányosan: **STAT 50%, GEN 50%** (lásd `scripts/aggregate_results.py:131-142`).

### Táblázat A — 40/40/20 súlyozott (kötelező)

| Modell | Mód | STAT | GEN | LING | **Composite (40/40/20)** |
|--------|-----|----:|----:|-----:|--------------------------:|
| `Qwen3-Next-80B IQ3_XXS` | think | 71.70% | 60.17% | N/A | **65.93%** |

### Táblázat B — 4 fő benchmark egyszerű átlaga (kiegészítő nézet)

```
átlag_3_bench = (HuLU + MMLU-HU + HuGME) / 3
```

_(Az UD N/A miatt 3 benchmark átlaga, nem a sablonban szereplő 4.)_

| Modell | Mód | HuLU | MMLU-HU | HuGME | UD | **Átlag (3-bench)** |
|--------|-----|----:|--------:|------:|---:|--------------------:|
| `Qwen3-Next-80B IQ3_XXS` | think | 56.53% | 86.87% | 82.83% | N/A | **75.41%** |

### Dimenziónkénti győztesek

- 🥇 **Statisztikai (HuLU + MMLU-HU átlaga):** `Qwen3-Next-80B IQ3_XXS` — 71.70%
- 🥇 **Generatív (HuGME + MT-Bench átlaga):** `Qwen3-Next-80B IQ3_XXS` — 60.17%
- 🥇 **Nyelvészeti (UD composite):** N/A
- 🏆 **Composite győztes (40/40/20):** `Qwen3-Next-80B IQ3_XXS` — 65.93%

## Heatmap-ek

**Csak 1 modell × 1 mód adata áll rendelkezésre — heatmap nem készült.** A `reports/results_heatmap.png` csak ezt az egy modellt tartalmazza.

### Statisztikai benchmarkok

_Hőtérkép készítéséhez kevés az adatpont (1 modell, 1 mód)._

### Generatív + nyelvészeti benchmarkok

_Hőtérkép készítéséhez kevés az adatpont (1 modell, 1 mód)._

## Figyelemre méltó eredmények

### Meglepetések

- **HuWNLI 13.33%** — a lexicalis következtetés sub-task-on a modell szinte véletlenszerűen teljesít. Ez a sub-task a 6 közül a legnehezebb (60 item, 2 osztály), de ilyen alacsony score arra utal, hogy a modell nem érti a WNLI típusú feladatokat magyarul.
- **HuCoPA 90.0%** — az ok-okozat feladat kiemelkedően jól megy a modellnek, ami a Qwen3-Next CoT-képességének köszönhető.

### Anomáliák

- **UD Hungarian nem értékelhető** az eredeti 16K-s kontextussal — a thinking modell CoT-fogyasztása miatt egyetlen CoNLL-U elemzés sem készült el. 64K kontextussal a modell már produkál CoNLL-U kimenetet, de a prompt pontosítása szükséges a megbízható működéshez.
- **Nincs nothink összehasonlítás** — a modell a llama-server backend miatt minden promptnál gondolkodik, a nothink mód nem létezik ezen a modellen. A korábban "nothink"-ként jelölt eredmények valójában think eredmények.

### Korrelációk

- _Nincs elég adatpont a korrelációs elemzéshez (1 modell)._

### Limitációk

- **A modell csak think módban fut** — a llama-server `reasoning_format: none` nem kapcsolja ki a CoT-t ezen a thinking modellen. Az `--mode nothink` flag hatástalan. Nincs külön nothink adat.
- **OpenAI-kompatibilis backend (llama-server) + Thinking modell:** a modell **mindig gondolkodik**, a `num_predict=4096` néha kevés a CoT + válasz kombinációnak — üres `content` és `finish_reason: length` jelzi.
- **UD Hungarian az eredeti 16K kontextussal nem futott** — 64K-ra emelve és `max_tokens` limit nélkül a modell már produkál CoNLL-U kimenetet, de a prompt pontosítása folyamatban van.
- **Bíró modell limitáció:** a `deepseek-v4-pro:cloud` egyben benchmark modell is, így saját maga értékelése self-bias-t hordoz (jelen riportban ez nem releváns, mert a modell nincs a baseline poolban).
- **Nincs baseline összehasonlítás** — a riport nem tartalmaz más modellek eredményeit, így a relatív teljesítmény nem értékelhető.
- **Nincs UD Hungarian composite** — a nyelvészeti dimenzió teljesen hiányzik, a súlyok STAT/GEN között 50/50 arányban oszlottak újra.

## Következő lépések

- [ ] UD Hungarian újrafuttatása 64K kontextussal, pontosított prompttal (formátumleírás + példamondat)
- [ ] Baseline modellek futtatása a relatív teljesítmény értékeléséhez
- [ ] A HuLU HuWNLI sub-task mélyebb vizsgálata (esetleg prompt hiba?)
- [ ] összehasonlítás a cloud Qwen3-Next-80B think eredményeivel

## Függelék — nyers adatok helye

Minden nyers mérési adat itt található:

- **Eredmények (JSONL + summary):** `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-nothink/<bench>_results.jsonl` + `<bench>_summary.json`
- **Logok:** `logs/hulu-nothink.log`, `logs/mmlu-hu-nothink.log`, `logs/hugme-nothink.log`, `logs/mt-bench-nothink.log`, `logs/hugme-judge-nothink.log`, `logs/mt-bench-judge-nothink.log`
- **Composite CSV:** `reports/composite_scores.csv`
- **Eredmény riport:** `reports/report.md`

> **Megjegyzés a mappaelnevezésről:** a mappa neve tartalmazza a `-nothink` utótagot, mert a futás `--mode nothink` flaggel indult. A modell azonban a llama-server backend miatt minden promptnál gondolkodik, így az eredmények valójában think módúak. A mappa átnevezése `-think`-re nem történt meg, hogy a checkpoint rendszer ne törje meg a resume képességet.

### Reprodukálhatóság

A mérések reprodukálásához szükséges:

- Conda env: `eval-hu` (Python 3.11, `$HOME/anaconda3/envs/eval-hu`)
- llama-server: `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` IQ3_XXS GGUF
- Backend: `http://localhost:8080/v1` (OpenAI-kompatibilis)
- Ollama kliens beállítások: `temperature=0.0`, `num_predict=4096` (think), `stream=False`
- Timeout: 300 másodperc
- Context: 64K (az UD újrafuttatáshoz)

### Verzióinformáció

| Komponens | Verzió |
|-----------|--------|
| Benchmark suite | v1.1.1 |
| Bíró modell | `deepseek-v4-pro:cloud` (2026-07-19 óta; gemini-3-flash-preview:latest 2026-07-14-ig) |
| Prompt template | v1.1 |
| Kiértékelő script | commit `55089f3` |
| Conda env | `eval-hu` (Python 3.11) |
| Ollama | ≥ 0.5.0 |
| llama-server | lokális, OpenCL |

## Változtatási napló (change log)

| Dátum | Szerző | Változás |
|-------|--------|----------|
| 2026-07-25 | fater.zsolt | Létrehozva — Qwen3-Next-80B IQ3_XXS think benchmark riport |

## Kapcsolódó

- [Riport Aggregáció runbook](../runbooks/aggregate-results.md) — composite score számítás (40/40/20)
- [Eredmény aggregáció + vizualizáció](../concepts/eredmeny-aggregacio.md) — heatmap generálás
- [Concept: OpenAI-kompatibilis backend](../concepts/openai-backend-support.md) — `ollama` vs `openai` backend részletek
- [Runbook: Benchmark futtatás OpenAI backenden](../runbooks/run-modell-x-openai-backend.md) — llama-server / vLLM / felhő OpenAI esetén
- [Overview](../overview.md) — projekt cél, hatókör
- [SCHEMA](../SCHEMA.md) — formátum
- [AGENTS.md](../../AGENTS.md) — 40/40/20 súlyozás szabálya (kötelező, nem változtatható); Backend konvenció (kötelező a riportban)
