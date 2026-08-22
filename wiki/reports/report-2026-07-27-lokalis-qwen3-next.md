# Riport — Lokális Qwen3-Next-80B IQ3_XXS (mindig think)

*Típus:* report
*Forrás(ok):* hu-eval projekt belső, [Overview](../overview.md), [Riport Aggregáció](../runbooks/aggregate-results.md), [Riport Sablon](riport-template.md)
*Létrehozva:* 2026-07-25
*Frissítve:* 2026-07-27 (v1.5 — UD Hungarian v4 benchmark kész, composite score frissítve)

---

## Fejléc

| Mező | Érték |
|------|-------|
| Riport azonosító | `hu-eval-20260727-lokalis-qwen3-next` |
| Riport dátum | 2026-07-27 |
| Értékelt modellek | `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` |
| Operator | `fater.zsolt` |
| Riport státusz | `final` |

> **Bíró modell** (LLM-as-a-Judge): `deepseek-v4-pro:cloud` — a `gemini-3-flash-preview:latest` 2026-07-14. 09:00 CEST óta nem elérhető (Ollama megszűnés), helyette ez a hivatalos bíró (2026-07-19 óta). **Self-bias korlát (SZENT):** a bíró modell nem értékelheti saját magát — a `deepseek-v4-pro` saját HuGME/MT-Bench-HU sorait független bíróval vagy kivételzéssel kell kezelni.

### Modell-kvantálás

| Modell | Kvantálás | Backend | Kontextus | Mód |
|--------|-----------|---------|-----------|-----|
| `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` | IQ3_XXS (3.06 bpw GGUF, 32.95 GB) | `openai` (llama-server `http://localhost:8080/v1`) | 128K (`-c 131072`) | think (nincs nothink) |

> **Mód:** a modell **csak gondolkodó (think) módban fut** — a llama-server `reasoning_format: none` beállítása nem kapcsolja ki a CoT-t ezen a thinking modellen. Az `--mode nothink` flag hatástalan; a modell minden promptnál CoT-t generál. Nincs külön nothink mód.

### Időkeret

- **STAT + GEN mérések:** 2026-07-19 (HuLU, MMLU-HU, HuGME, MT-Bench-HU)
- **UD Hungarian (v4, 128K ctx):** 2026-07-25 — 2026-07-27 (~45.4 óra, 449 mondat)
- **Összes futásidő:** ~55 óra

## Executive Summary

Ez a riport az `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` modell (3.06 bpw GGUF kvantálás, llama-server backend) teljes benchmark eredményeit tartalmazza. A modell egy thinking modell, amely minden promptnál gondolkodik — nincs külön nothink mód.

A HuLU, MMLU-HU, HuGME és MT-Bench-HU benchmarkok "nothink" néven futottak (a modell azonban think módot használt), az UD Hungarian think módban, 128K kontextussal, v4 prompttal (explicit CoNLL-U formátumleírás).

### Főbb számok egy sorban

- **Composite score (40/40/20):** **64.85%**
- **HuLU:** 56.53% (1459/2581)
- **MMLU-HU:** 86.87% (1303/1500)
- **HuGME:** 82.83% (300/300)
- **MT-Bench-HU:** 37.50% (1W/7L/16T)
- **UD Hungarian:** Composite 64.73%, UPOS 79.36%, UAS 63.14%, LAS 51.70%

## Per-benchmark eredmények

### HuLU eredmények (statisztikai — 6 NLU sub-task)

> **Mit tesztel:** a magyar nyelvű természetes nyelvmegértést (NLU) méri 6 al-benchmarkon: HuCOLA (nyelvtani elfogadhatóság), HuCoPA (közös előfordulás / ok-okozat), HuRTE (szöveg-entailment, háromirányú), HuSST (szentiment, 5 osztály), HuWNLI (lexikális következtetés, legnehezebb), HuCB (CommitmentBank — beszédaktus/elköteleződés). Kimenet: egyesített accuracy + per-sub-task bontás.

| Modell | Mód | Pontosság (%) | Megjegyzés |
|--------|-----|---------------:|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **56.53%** | llama-server, mindig gondolkodik |

**Per-sub-task bontás (KÖTELEZŐ):**

| Sub-task | Pontosság (%) | Helyes / Összes |
|----------|---------------:|----------------:|
| HuCOLA | 51.54% | 469/910 |
| HuCoPA | 90.00% | 90/100 |
| HuRTE | 72.84% | 177/243 |
| HuSST | 57.00% | 664/1165 |
| HuWNLI | 13.33% | 8/60 |
| HuCB | 49.51% | 51/103 |

### MMLU-HU eredmények (statisztikai — 38 tantárgy, 5 kevés lövés)

> **Mit tesztel:** a többválasztós, tantárgy-specifikus tudást (magyar MMLU) 38 tantárgyban, 5-shot felállításban. Méri az általános tudást és reasoninget; kimenet: tantárgyak átlagolt accuracy-ja (0-1).

| Modell | Mód | Pontosság (%) | Megjegyzés |
|--------|-----|---------------:|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **86.87%** | 1303/1500 |

### HuGME eredmények (generatív, LLM-as-a-Judge — 6 metrika, 300 item)

> **Mit tesztel:** a nyílt, szabad szöveges generálást (NYTK HuGME) LLM-as-a-Judge módszerrel, 6 metrikán (relevance, coherence, fluency, informativeness, harmlessness, overall) 300 itemen. Kimenet: a 6 metrika átlagolt judge-score-ja (0-1).

| Modell | Mód | Judge score | Judged subset | Megjegyzés |
|--------|-----|------------:|---------------|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **0.828** | 300/300 | judge: `deepseek-v4-pro:cloud` |

### MT-Bench-HU eredmények (generatív, GSB multi-baseline — 24 item × 3 baseline)

> **Mit tesztel:** a kétfordulós (2-turn) párbeszédes képességet és utasításkövetést magyarul, 24 kérdésen (8 kategória × 3). A válaszokat egy bíró modell GSB (good/bad/same) pairwise módon hasonlítja össze baseline modell ellen. Kimenet: win-rate (0-1).

| Modell | Mód | Score (%) | W/L/T | Megjegyzés |
|--------|-----|----------:|-------|------------|
| `Qwen3-Next-80B IQ3_XXS` | think | **37.50%** | 1W/7L/16T | baseline: `deepseek-v4-flash:cloud` |

### UD Hungarian eredmények (nyelvészeti — CoNLL-U, UPOS/UAS/LAS)

> **Mit tesztel:** a magyar nyelvtani elemzést (Universal Dependencies, Szeged UD test corpus). A modellnek CoNLL-U formátumban kell megadnia a tokenizációt, UPOS címkéket, fej-tokeneket és dependency relációkat. Kimenet: UPOS + UAS + LAS súlyozatlan átlaga (0-1). A v4 prompt explicit CoNLL-U 10 oszlop leírást + példamondatot tartalmaz, feltételezve hogy a modell nem ismeri a formátumot.

| Modell | Mód | Kontextus | Composite | UPOS | UAS | LAS | Feldolgozva | Skip |
|--------|-----|-----------|:---------:|:----:|:---:|:---:|:-----------:|:----:|
| `Qwen3-Next-80B IQ3_XXS` | think | 128K | **64.73%** | 79.36% | 63.14% | 51.70% | 437/449 | 12 |

*Értelmezhető mondatok (UPOS>0):* 422/437, ezen UPOS=82.18%, UAS=65.23%, LAS=55.78%.

| Statisztika | Érték |
|-------------|------:|
| Átlagos reasoning hossz | 27118 karakter |
| Átlagos feldolgozási idő | 325 s/mondat |
| Összes futásidő (UD) | ~45.4 óra |
| UPOS=100% mondatok | 34/422 (8.1%) |
| UPOS<50% mondatok | 32/422 (7.6%) |
| Finish reason | 436 stop, 1 length |

**Érdekes megfigyelések:**
- A v4 prompt (explicit CoNLL-U formátumleírás + példamondat) jelentősen javította a modell teljesítményét a korábbi v2/v3 promptokhoz képest
- 12 mondat timeout (1800s) miatt kimaradt — ezek hosszabb mondatok, ahol a modell túl sokat gondolkodik
- UPOS (79.36%) már megbízható, de a dependency parsing (UAS 63.14%, LAS 51.70%) gyengébb
- A 7.6%-os UPOS<50% arány arra utal, hogy néhány mondatnál a modell nem produkál valid CoNLL-U-t

## Kompozit score-ok

A [Modell vs. Modell](../comparisons/modell-vs-modell.md) és az [AGENTS.md](../../AGENTS.md) által definiált **kötelező 40/40/20 súlyozás** (NE változtatható):

```
composite = 0.40 × statisztikai + 0.40 × generatív + 0.20 × nyelvészeti
```

Ahol:

- **statisztikai** = átlag(HuLU, MMLU-HU) = (56.53% + 86.87%) / 2 = 71.70%
- **generatív** = átlag(HuGME, MT-Bench-HU) = (82.83% + 37.50%) / 2 = 60.17%
- **nyelvészeti** = UD Composite = 64.73%

### Táblázat A — 40/40/20 súlyozott (kötelező)

| Modell | Mód | STAT | GEN | LING | **Composite (40/40/20)** |
|--------|-----|-----:|----:|-----:|--------------------------:|
| `Qwen3-Next-80B IQ3_XXS` | think | 71.70% | 60.17% | 64.73% | **64.85%** |

### Táblázat B — 5 benchmark egyszerű átlaga (kiegészítő nézet)

| Modell                   | Mód   |   HuLU | MMLU-HU |  HuGME | MT-Bench-HU |     UD | **Átlag (5-bench)** |
| ------------------------ | ----- | -----: | ------: | -----: | ----------: | -----: | ------------------: |
| `Qwen3-Next-80B IQ3_XXS` | think | 56.53% |  86.87% | 82.83% |      37.50% | 64.73% |          **65.69%** |

### Dimenziónkénti győztesek

- 🥇 **Statisztikai (HuLU + MMLU-HU átlaga):** `Qwen3-Next-80B IQ3_XXS` — 71.70%
- 🥇 **Generatív (HuGME + MT-Bench átlaga):** `Qwen3-Next-80B IQ3_XXS` — 60.17%
- 🥇 **Nyelvészeti (UD composite):** `Qwen3-Next-80B IQ3_XXS` — 64.73%
- 🏆 **Composite győztes (40/40/20):** `Qwen3-Next-80B IQ3_XXS` — 64.85%

## Figyelemre méltó eredmények

### Meglepetések

- **MMLU-HU 86.87%** erős a 3.06 bpw kvantáláshoz képest
- **HuCoPA 90.0%** kiemelkedő — a modell jól kezeli a magyar nyelvű precedencia-viszonyokat
- **UD Hungarian 64.73% composite** — az IQ3_XXS kvantálás a 128K kontextussal és explicit CoNLL-U formátumleírással már értelmezhető eredményt ad
- **UD UPOS 79.36%** — a szófaji címkézés már megbízható, de a dependency parsing (UAS 63.14%, LAS 51.70%) még gyengébb

### Anomáliák

- **HuWNLI 13.33%** — a lexikális következtetés sub-task-on a modell szinte véletlenszerűen teljesít
- **MT-Bench-HU 37.50%** magas döntetlen-arány (66.7%) — a bíró nehezen különbözteti meg a kvantált modellt a cloud baseline-tól
- **UD Hungarian 12 mondat timeout** — hosszabb mondatoknál a modell túl sokat gondolkodik (>1800s), a CoT elfogyasztja a kontextust

### Limitációk

- **Nincs nothink mód** — a modell minden promptnál gondolkodik, ami jelentősen növeli a futásidőt (UD: ~45 óra 449 mondatra)
- 1 modell × 1 kvantálás × 1 mód — nincs összehasonlítási alap
- UD Hungarian 12 mondat timeout (1800s) miatt kimaradt
- A HuLU, MMLU-HU, HuGME, MT-Bench-HU eredmények "nothink" néven futottak, de a modell mindig think módban működött

## Következő lépések

- [ ] Baseline modellek futtatása a relatív teljesítmény értékeléséhez
- [ ] A HuLU HuWNLI sub-task mélyebb vizsgálata
- [ ] Összehasonlítás a cloud Qwen3-Next-80B think eredményeivel

## Függelék — nyers adatok helye

Minden nyers mérési adat itt található:

- **STAT + GEN eredmények:** `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-nothink/<bench>_results.jsonl` + `<bench>_summary.json`
- **UD Hungarian eredmények:** `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-think/ud_hungarian_results.jsonl` + `ud_hungarian_summary.json`
- **Logok:** `logs/hulu-nothink.log`, `logs/mmlu-hu-nothink.log`, `logs/hugme-nothink.log`, `logs/mt-bench-nothink.log`, `logs/ud_v4_run.log`
- **Composite CSV:** `composite_scores-2026-07-27.csv`
- **Eredmény riport:** `report-2026-07-27.md`

> **Megjegyzés a mappaelnevezésről:** a STAT + GEN eredmények `-nothink` utótagú mappában vannak, mert a futás `--mode nothink` flaggel indult. A modell azonban mindig think módban működött. Az UD eredmények `-think` mappában vannak.

### Reprodukálhatóság

A mérések reprodukálásához szükséges:

- Conda env: `eval-hu` (Python 3.11, `$HOME/anaconda3/envs/eval-hu`)
- llama-server: `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` IQ3_XXS GGUF
- Backend: `http://localhost:8080/v1` (OpenAI-kompatibilis)
- Kontextus: 128K (`-c 131072 -ctk q5_1 -ctv q5_1`)
- UD prompt: v4 (explicit CoNLL-U formátumleírás + példamondat)
- UD max_tokens: 65536
- UD timeout: 1800s/mondat

## Változtatási napló (change log)

| Dátum | Szerző | Változás |
|-------|--------|----------|
| 2026-07-25 | fater.zsolt | Létrehozva — Qwen3-Next-80B IQ3_XXS think benchmark riport (UD N/A) |
| 2026-07-27 | fater.zsolt | v1.5 — UD Hungarian v4 (128K ctx) eredmények hozzáadva, composite score frissítve (65.93% → 64.85%), riport státusz final |

## Kapcsolódó

- [Riport Aggregáció runbook](../runbooks/aggregate-results.md) — composite score számítás (40/40/20)
- [Concept: UD Hungarian](../concepts/ud-hungarian.md) — POS, dependency parsing, UAS/LAS
- [Concept: OpenAI-kompatibilis backend](../concepts/openai-backend-support.md) — `ollama` vs `openai` backend részletek
- [Runbook: Benchmark futtatás OpenAI backenden](../runbooks/run-modell-x-openai-backend.md) — llama-server / vLLM / felhő OpenAI esetén
- [Entity: Qwen3-Next 80B Thinking GGUF (lokális)](../entities/qwen3-next-80b-lokalis.md)
- [Overview](../overview.md) — projekt cél, hatókör
- [SCHEMA](../SCHEMA.md) — formátum
- [AGENTS.md](../../AGENTS.md) — 40/40/20 súlyozás szabálya (kötelező); Backend konvenció (kötelező a riportban)