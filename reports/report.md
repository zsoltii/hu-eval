# Modell Értékelési Riport — 2026-07-25

*Generálva:* 2026-07-25

---

## Executive Summary

Ez a riport az egyetlen jelenleg elérhető lokális modell, az `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` (IQ3_XXS kvantálás, llama-server backend) eredményeit tartalmazza. A modell **csak think módban fut** — a llama-server `reasoning_format: none` ellenére minden promptnál gondolkodik; nincs külön nothink mód.

A modell az MMLU-HU benchmarkon kiemelkedő (86.87%), a HuGME-n jó (0.828), a HuLU-n közepes (56.53%), az MT-Bench-HU-n gyenge (37.50%) teljesítményt nyújtott. Az UD Hungarian az eredeti 16K kontextussal nem volt értékelhető.

### Főbb számok

- **Composite score (40/40/20, LING N/A → 50/50):** 65.93%
- **HuLU (6 NLU sub-task):** 56.53% (1459/2581)
- **MMLU-HU (38 tantárgy, 5-shot):** 86.87% (1303/1500)
- **HuGME (LLM-as-a-Judge):** 82.83% (300/300)
- **MT-Bench-HU (vs deepseek-v4-flash:cloud):** 37.50% (1W/7L/16T)
- **UD Hungarian:** N/A (16K kontextus; 64K-on már produkál CoNLL-U-t)

---

## Composite Score

**Súlyok:** stat=0.4, gen=0.4, ling=0.2 (AGENTS.md kötelező). LING hiányában 50/50 STAT/GEN.

| Modell | Mód | HuLU | MMLU-HU | HuGME | MT-Bench-HU | UD | STAT | GEN | LING | **Composite** |
|--------|-----|-----:|--------:|------:|------------:|---:|-----:|----:|-----:|--------------:|
| Qwen3-Next-80B IQ3_XXS | think | 56.53% | 86.87% | 82.83% | 37.50% | N/A | **71.70%** | **60.17%** | N/A | **65.93%** |

**Átlag (3 benchmark):** HuLU + MMLU-HU + HuGME átlaga = **(56.53% + 86.87% + 82.83%) / 3 = 75.41%**

---

## Per-benchmark eredmények

### HuLU — 6 NLU sub-task (statisztikai)

**Mit tesztel:** magyar nyelvű NLU 6 al-benchmarkon: nyelvtani elfogadhatóság (HuCOLA), ok-okozat (HuCoPA), szöveg-entailment (HuRTE), szentiment (HuSST), lexicalis következtetés (HuWNLI), CommitmentBank (HuCB).

| Mód | Overall pontosság |
|-----|------------------:|
| think | **56.53%** (1459/2581) |

| Sub-task | Pontosság |
|----------|----------:|
| HuCOLA | 51.54% |
| HuCoPA | **90.00%** |
| HuRTE | 72.84% |
| HuSST | 57.00% |
| HuWNLI | **13.33%** |
| HuCB | 49.51% |

**Megfigyelések:**
- HuCoPA (90.0%) kiemelkedő — a CoT jól segíti az ok-okozat felismerést
- HuWNLI (13.3%) random guess szint — a modell nem érti a lexicalis következtetést magyarul
- HuCB (49.5%) szintén random guess

### MMLU-HU — 38 tantárgy, 5-shot (statisztikai)

**Mit tesztel:** többválasztós tantárgy-specifikus tudás 38 magyar tantárgyban.

| Mód | Pontosság |
|-----|----------:|
| think | **86.87%** (1303/1500) |

### HuGME — Generatív, LLM-as-a-Judge (generatív)

**Mit tesztel:** nyílt generatív válaszok minősége 6 metrikán (relevance, coherence, fluency, informativeness, harmlessness, overall), 300 item.

| Mód | Score | Judged |
|-----|------:|:-------|
| think | **0.828** | 300/300 |
| Judge | `deepseek-v4-pro:cloud` | — |

### MT-Bench-HU — GSB multi-baseline (generatív)

**Mit tesztel:** 2-turn párbeszéd, 24 item, baseline: deepseek-v4-flash:cloud.

| Mód | Score | W/L/T |
|-----|------:|:------|
| think | **37.50%** | 1W / 7L / 16T |
| Judge | `deepseek-v4-pro:cloud` | — |

### UD Hungarian — CoNLL-U, UPOS/UAS/LAS (nyelvészeti)

**Mit tesztel:** magyar mondatok nyelvtani elemzése Universal Dependencies szerint.

| Mód | Composite | UPOS | UAS | LAS |
|-----|:---------:|:----:|:---:|:---:|
| think (16K ctx) | **N/A** | N/A | N/A | N/A |
| think (64K ctx) | tesztelés alatt | — | — | — |

---

## Heatmap

![Heatmap](results_heatmap.png)

---

## Figyelemre méltó eredmények

- **MMLU-HU 86.87%** erős a 3.06 bpw kvantáláshoz képest
- **MT-Bench-HU 37.50%** magas döntetlen-arány (66.7%) — a bíró nehezen különbözteti meg a kvantált modellt a cloud baseline-tól
- **UD Hungarian** 64K kontextussal már produkál CoNLL-U kimenetet, de a prompt pontosítása folyamatban van

## Limitációk

- **Nincs nothink mód** — a modell minden promptnál gondolkodik
- 1 modell × 1 mód — nincs összehasonlítási alap
- UD Hungarian még nem teljes
- A `num_predict=4096` néha kevés a CoT + válasz kombinációnak

---

*Composite score formula: STAT 40% + GEN 40% + LING 20%. Mivel LING N/A, 50/50. Részletek: [wiki riport](../wiki/reports/report-2026-07-25-lokalis-qwen3-next.md)*
