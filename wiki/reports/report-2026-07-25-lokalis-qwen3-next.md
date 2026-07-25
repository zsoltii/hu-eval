# Riport — Lokális Qwen3-Next-80B IQ3_XXS (nothink only)

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

> **Backend:** `openai` — OpenAI-kompatibilis `/v1/chat/completions` végpont. A modell llama-server-en fut, nem natív Ollama-n. A `chat_template` és `reasoning_format: none` miatt a modell **minden promptnál gondolkodik** — a nothink és think mód érdemben nem különbözik (lásd OpenAI-kompatibilis backend limitációk lentebb).

### Időkeret

- **Mérés indítása:** 2026-07-19 09:32
- **Mérés befejezése:** 2026-07-19 22:08
- **Teljes futásidő:** ~10 óra (processzoridő, soros futtatás)

## Executive Summary

Ez a riport az `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` modell (3.06 bpw GGUF kvantálás, llama-server backend) eredményeit tartalmazza a 4 elérhető benchmarkon (HuLU, MMLU-HU, HuGME, MT-Bench-HU) **nothink módban**. A think módú futások a véletlen adatvesztés miatt nem állnak rendelkezésre. Az UD Hungarian benchmark **N/A** — a modell minden esetben a rendelkezésre álló kontextusablakot (n_ctx=16128) gondolkodásra használta, és soha nem produkált CoNLL-U kimenetet, még `num_predict=4096` mellett sem.

A modell a statisztikai benchmarkokon (HuLU 56.5%, MMLU-HU 86.9%) erős eredményt ért el a kvantáltsági szintjéhez képest. A generatív benchmarkokon (HuGME 0.828, MT-Bench-HU 0.375 win-rate) közepesen teljesített. A composite score (40/40/20 súlyozott) **0.659**.

### Főbb számok egy sorban

- **Nothink composite score (40/40/20):** `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` — **65.93%**
- **HuLU nothink:** 56.53%
- **MMLU-HU nothink:** 86.87%
- **HuGME nothink:** 82.83%
- **UD Hungarian:** **N/A** (a modell CoT-fogyasztása minden esetben kimeríti a kontextusablakot)
- **Legnagyobb meglepetés:** a modell a HuWNLI sub-task-on (lexicalis következtetés) csak 13.3%-ot ért el, ami messze a leggyengébb sub-task.

## Per-benchmark eredmények

### HuLU eredmények (statisztikai — 6 NLU sub-task)

> **Mit tesztel:** a magyar nyelvű természetes nyelvmegértést (NLU) méri 6 al-benchmarkon: HuCOLA (nyelvtani elfogadhatóság), HuCoPA (közös előfordulás / ok-okozat), HuRTE (szöveg-entailment, háromirányú), HuSST (szentiment, 5 osztály), HuWNLI (lexicalis következtetés, legnehezebb), HuCB (CommitmentBank — beszédaktus/elköteleződés). Kimenet: egyesített accuracy + per-sub-task bontás.

| Modell | Mód | Pontosság (%) | Megjegyzés |
|--------|-----|---------------:|------------|
| `Qwen3-Next-80B IQ3_XXS` | nothink | **56.53%** | llama-server |

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
- A think módú eredmények (60.9%) nem állnak rendelkezésre az aggregátor számára, lásd az adatvesztésről szóló megjegyzést.

### MMLU-HU eredmények (statisztikai — 38 tantárgy, 5 kevés lövés)

> **Mit tesztel:** a többválasztós, tantárgy-specifikus tudást (magyar MMLU) 38 tantárgyban, 5-shot felállításban. Méri az általános tudást és reasoninget; kimenet: tantárgyak átlagolt accuracy-ja (0-1).

| Modell | Mód | Pontosság (%) | Megjegyzés |
|--------|-----|---------------:|------------|
| `Qwen3-Next-80B IQ3_XXS` | nothink | **86.87%** | 1303/1500 |

**Legjobb:** _Összehasonlítási alap nélkül nem értelmezhető._

> A 86.87% erős eredmény a 3.06 bpw kvantáláshoz képest. Az 5-shot MMLU-HU promptok azonban hosszúak lehetnek, és az OpenAI backend `reasoning_format: none` ellenére a modell gondolkodik — a `num_predict=4096` néha kevés volt (lásd limitációk).

### HuGME eredmények (generatív, LLM-as-a-Judge — 6 metrika, 300 item)

> **Mit tesztel:** a nyílt, szabad szöveges generálást (NYTK HuGME) LLM-as-a-Judge módszerrel, 6 metrikán (relevance, coherence, fluency, informativeness, harmlessness, overall) 300 itemen. Kimenet: a 6 metrika átlagolt judge-score-ja (0-1).

| Modell | Mód | Judge score | Judged subset | Megjegyzés |
|--------|-----|------------:|---------------|------------|
| `Qwen3-Next-80B IQ3_XXS` | nothink | **0.828** | 300/300 | judge: `deepseek-v4-pro:cloud` |

**Legjobb:** _Összehasonlítási alap nélkül nem értelmezhető._

> A HuGME judge 6 metrika átlaga: relevance, coherence, fluency, informativeness, harmlessness, overall. A bíró modell részletei a [Függelék](#függelék--nyers-adatok-helye) szekcióban.

### MT-Bench-HU eredmények (generatív, GSB multi-baseline — 24 item × 3 baseline)

> **Mit tesztel:** a kétfordulós (2-turn) párbeszédes képességet és utasításkövetést magyarul, 24 kérdésen (8 kategória × 3). A válaszokat egy bíró modell GSB (good/bad/same) pairwise módon hasonlítja össze 3 baseline modell ellen, counterbalanced (swap) elrendezésben. Kimenet: win-rate (0-1).

| Modell | Mód | Score (%) | W/L/T | Megjegyzés |
|--------|-----|----------:|-------|------------|
| `Qwen3-Next-80B IQ3_XXS` | nothink | **37.50%** | 1W/7L/16T | baseline: deepseek-v4-flash:cloud |

**Legjobb:** _Összehasonlítási alap nélkül nem értelmezhető._

> A 37.5% = (1 + 16/2) / 24: 1 győzelem, 7 vereség, 16 döntetlen a `deepseek-v4-flash:cloud` baseline ellen. A magas döntetlen-arány (66.7%) azt sugallja, hogy a bírónak gyakran nem sikerült különbséget tennie a két modell között, ami a kvantált modell és a cloud baseline közti kisebb minőségbeli különbségre utal.

### UD Hungarian eredmények (nyelvészeti — CoNLL-U, UPOS/UAS/LAS)

> **Mit tesztel:** a magyar nyelvtani elemzést (Universal Dependencies, Szeged UD test corpus). A modellnek CoNLL-U formátumban kell megadnia a tokenizációt, UPOS címkéket, fej-tokeneket és dependency relációkat. Kimenet: UPOS + UAS + LAS súlyozatlan átlaga (0-1).

| Modell | Mód | Composite | UPOS | UAS | LAS | Megjegyzés |
|--------|-----|----------:|-----:|----:|----:|------------|
| `Qwen3-Next-80B IQ3_XXS` | nothink | **N/A** | N/A | N/A | N/A | a modell CoT-re használja a kontextust |

**Legjobb:** _Nem értékelhető._

> **Részletes magyarázat:** A Qwen3-Next-80B egy thinking modell. Az OpenAI-kompatibilis backenden (`reasoning_format: none` és a llama-server chat_template beállításaival) a modell **minden prompt előtt gondolkodik**, függetlenül a nothink/think beállítástól. A gondolkodási lánc (CoT) a rendelkezésre álló 16128 token kontextusablak nagy részét elfogyasztja, és `num_predict=4096` (nothink) gyakran kevés a CoT utáni tényleges CoNLL-U generáláshoz — a válaszok `finish_reason: length` miatt csonkulnak. A think módú teszt (num_predict=32768) ellenére sem sikerült CoNLL-U kimenetet kinyerni. Ez a modell **alapvetően inkompatibilis** az UD Hungarian benchmark jelenlegi implementációjával, mert a CoT mindig kimeríti a kontextust.

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
| `Qwen3-Next-80B IQ3_XXS` | nothink | 71.70% | 60.17% | N/A | **65.93%** |

### Táblázat B — 4 fő benchmark egyszerű átlaga (kiegészítő nézet)

```
átlag_3_bench = (HuLU + MMLU-HU + HuGME) / 3
```

_(Az UD N/A miatt 3 benchmark átlaga, nem a sablonban szereplő 4.)_

| Modell | Mód | HuLU | MMLU-HU | HuGME | UD | **Átlag (3-bench)** |
|--------|-----|----:|--------:|------:|---:|--------------------:|
| `Qwen3-Next-80B IQ3_XXS` | nothink | 56.53% | 86.87% | 82.83% | N/A | **75.41%** |

### Dimenziónkénti győztesek

- 🥇 **Statisztikai (HuLU + MMLU-HU átlaga):** `Qwen3-Next-80B IQ3_XXS` — 71.70%
- 🥇 **Generatív (HuGME + MT-Bench átlaga):** `Qwen3-Next-80B IQ3_XXS` — 60.17%
- 🥇 **Nyelvészeti (UD composite):** N/A
- 🏆 **Composite győztes (40/40/20):** `Qwen3-Next-80B IQ3_XXS` — 65.93%

## Heatmap-ek

**A think eredmények hiánya miatt csak 1 soros a heatmap — nem készült új heatmap.** A `reports/results_heatmap.png` csak ezt az egy modellt tartalmazza.

### Statisztikai benchmarkok

_Hőtérkép készítéséhez kevés az adatpont (1 modell, 1 mód)._

### Generatív + nyelvészeti benchmarkok

_Hőtérkép készítéséhez kevés az adatpont (1 modell, 1 mód)._

## Figyelemre méltó eredmények

### Meglepetések

- **HuWNLI 13.33%** — a lexicalis következtetés sub-task-on a modell szinte véletlenszerűen teljesít. Ez a sub-task a 6 közül a legnehezebb (60 item, 2 osztály), de ilyen alacsony score arra utal, hogy a modell nem érti a WNLI típusú feladatokat magyarul.
- **HuCoPA 90.0%** — az ok-okozat feladat kiemelkedően jól megy a modellnek, ami a Qwen3-Next CoT-képességének köszönhető.

### Anomáliák

- **UD Hungarian teljes kudarc** — a thinking modell CoT-fogyasztása miatt egyetlen CoNLL-U elemzés sem készült el. Ez nem modellhiba, hanem a benchmark implementáció és a modell architektúra inkompatibilitása.
- **Think eredmények elvesztek** — a 4 think futás mindegyike befejeződött (HuLU 60.9%, MMLU-HU 89.7%, HuGME 0.847, MT-Bench-HU 0.083), de az eredményfájlok `rm -rf` által véletlenül törlődtek az aggregálás előtt. A checkpoint állapotok is törlésre kerültek. Az újrafuttatás a felhasználó döntése alapján elmaradt.

### Korrelációk

- _Nincs elég adatpont a korrelációs elemzéshez (1 modell)._

### Limitációk

- **Csak nothink adatok állnak rendelkezésre** — a benchmark kompozit score csak a nothink futásokon alapul.
- **OpenAI-kompatibilis backend (llama-server) + Thinking modell:** a `reasoning_format: none` és a `chat_template` miatt a modell **mindig gondolkodik**, a nothink és think mód érdemben nem tér el. A `num_predict=4096` (nothink) néha kevés a gondolkodásnak — üres `content` és `finish_reason: length` jelzi.
- **UD Hungarian inkompatibilis** a thinking modellekkel ebben a benchmark implementációban.
- **Bíró modell limitáció:** a `deepseek-v4-pro:cloud` egyben benchmark modell is, így saját maga értékelése self-bias-t hordoz (jelen riportban ez nem releváns, mert a modell nincs a baseline poolban).
- **Nincs baseline összehasonlítás** — a riport nem tartalmaz más modellek eredményeit, így a relatív teljesítmény nem értékelhető.
- **Nincs UD Hungarian composite** — a nyelvészeti dimenzió teljesen hiányzik, a súlyok STAT/GEN között 50/50 arányban oszlottak újra.

## Következő lépések

- [ ] Think eredmények újrafuttatása, ha az adatvesztés pótlása szükséges
- [ ] UD Hungarian parser javítása thinking modellekhez (CoT utáni CoNLL-U kinyerés, n_ctx növelés, `reasoning_format` kényszerítés)
- [ ] Baseline modellek futtatása a relatív teljesítmény értékeléséhez
- [ ] A HuLU HuWNLI sub-task mélyebb vizsgálata (esetleg prompt hiba?)

## Függelék — nyers adatok helye

Minden nyers mérési adat itt található:

- **Eredmények (JSONL + summary):** `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-nothink/<bench>_results.jsonl` + `<bench>_summary.json`
- **State (checkpoint):** _törölve (az adatvesztés része)_
- **Logok:** `logs/hulu-nothink.log`, `logs/mmlu-hu-nothink.log`, `logs/hugme-nothink.log`, `logs/mt-bench-nothink.log`, `logs/hugme-judge-nothink.log`, `logs/mt-bench-judge-nothink.log`
- **Composite CSV:** `reports/composite_scores.csv`
- **Eredmény riport:** `reports/report.md`

### Adatvesztés jegyzőkönyve

A think módú futások véletlen `rm -rf` által törlődtek 2026-07-19-én az aggregálás előtt. A következő fájlok vesztek el:

- `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-think/*.jsonl` (mind a 4 benchmark)
- `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-think/*_summary.json`
- `logs/*-think.log`
- `state/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-think/*`

Ismert utolsó think eredmények (a nyers fájlok elvesztése előtti utolsó status kiolvasásból):

| Benchmark | Score |
|-----------|-------|
| HuLU think | 60.9% (1571/2581) |
| MMLU-HU think | 89.7% (1345/1500) |
| HuGME think | 0.847 (judged: deepseek-v4-pro:cloud) |
| MT-Bench-HU think | 0.083 (1W/11L vs deepseek-v4-flash:cloud) |

### Reprodukálhatóság

A mérések reprodukálásához szükséges:

- Conda env: `eval-hu` (Python 3.11, `$HOME/anaconda3/envs/eval-hu`)
- llama-server: `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` IQ3_XXS GGUF
- Backend: `http://localhost:8080/v1` (OpenAI-kompatibilis)
- Ollama kliens beállítások: `temperature=0.0`, `num_predict=4096` (nothink), `stream=False`
- Timeout: 300 másodperc (nothink)

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
| 2026-07-25 | fater.zsolt | Létrehozva — Qwen3-Next-80B IQ3_XXS nothink benchmark riport |

## Kapcsolódó

- [Riport Aggregáció runbook](../runbooks/aggregate-results.md) — composite score számítás (40/40/20)
- [Eredmény aggregáció + vizualizáció](../concepts/eredmeny-aggregacio.md) — heatmap generálás
- [Concept: OpenAI-kompatibilis backend](../concepts/openai-backend-support.md) — `ollama` vs `openai` backend részletek
- [Runbook: Benchmark futtatás OpenAI backenden](../runbooks/run-modell-x-openai-backend.md) — llama-server / vLLM / felhő OpenAI esetén
- [Overview](../overview.md) — projekt cél, hatókör
- [SCHEMA](../SCHEMA.md) — formátum
- [AGENTS.md](../../AGENTS.md) — 40/40/20 súlyozás szabálya (kötelező, nem változtatható); Backend konvenció (kötelező a riportban)
