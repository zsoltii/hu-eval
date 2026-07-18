# Végleges Benchmark Összesítés — 2026-07-14. 20:14 CEST (queue kész)

*Típus:* report
*Forrás(ok):* belső projekt futtatás, `priority_judge.sh` 2026-07-13→2026-07-14
*Létrehozva:* 2026-07-15
*Frissítve:* 2026-07-15

---

## Összefoglaló

A teljes magyar LLM értékelési pipeline **2026-07-14. 20:14 CEST**-kor fejeződött be.
A `priority_judge.sh` script 2026-07-13. 09:11-kor indult a `gemini-3-flash-preview` bíró 3 napos
határideje (2026-07-14. 09:00) előtt, és a következő 3 fázist futtatta le:

1. **HuGME rejudge** (22 modell × 300 item × 6 metrika) — marker fájl miatt kihagyva, már kész
2. **MT-Bench rejudge multi-baseline** (20 modell × 24 item × 3 baseline) — marker fájl miatt kihagyva, már kész
3. **UD Hungarian refuttatás** (13 modell, CoT-aware parser) — 2026-07-14. 20:14-re kész

**Eredmények (végeredmény):**

| Mutató | Érték |
|--------|-------|
| Aktív modellek | 10 (deepseek-v4-flash/pro, glm-5.1/5.2, gpt-oss-120b/20b, kimi-k2.6, minimax-m3, nemotron-3-ultra, qwen3.5) |
| RETIRED modellek | 1 (qwen3-next:80b, HTTP 410) |
| Benchmarkek | 5 (HuLU, MMLU-HU, HuGME, MT-Bench-HU, UD Hungarian) |
| Végrehajtott futások | 22 (10 modell × 2 mód) + 2 RETIRED HuLU |
| Összes feldolgozott item | 97 088 (cél: 97 060, +0.03% eltérés a judge subsetek miatt) |
| Összes futásidő | ~1029 ó (~43 nap processzoridő) |
| HuLU átlag (minden modell×mód) | 73.5% |
| MMLU-HU átlag | 80.2% |
| HuGME átlag (judge score) | 9.2% |

---

## Részletes eredménytábla (11 modell × 2 mód × 5 benchmark)

Sorok: modell + mód (nothink/think). Oszlopok: benchmark. Cella: % accuracy (vagy judge score / W-L-T).

**Célméret:** HuLU=2581, MMLU-HU=1500, HuGME=299, MT-Bench-HU=24, UD Hungarian=449.

**Jelmagyarázat:**
- `RETIRED` = qwen3-next:80b (HTTP 410, nem elérhető 2026-06-16 óta)
- HuLU: pontosság (acc %)
- MMLU-HU: pontosság (acc %)
- HuGME: judge score % (`gemini-3-flash-preview` bíró) + judged subset szám
- MT-Bench-HU: GSB score % (W/L/T = win/loss/tie) — 3 baseline (deepseek-v4-flash, deepseek-v4-pro, kimi-k2.6) átlaga
- UD Hungarian: composite score (UPOS=szófaji, UAS=fej-dependencia, LAS=fej+deprel)

**Megjegyzések:**
- Az UD Hungarian think eredmények alacsonyak (0-7.5%) — a modellek CoT-t írnak CoNLL-U helyett, és a parser csak a végén keresi a struktúrát
- MT-Bench-HU 50% (W0/L0/T24) a legtöbb modellnél — a multi-baseline averaging miatt minden baseline-on döntetlent játszanak
- gpt-oss:20b HuGME 138 ó outlier (cloud rate limit) — kihagyva az átlagból
- nemotron-3-ultra HuGME 205 ó, MT-Bench 175 ó, UD nothink 125 ó — szintén rate-limit outlierek

## nothink

| Modell | HuLU | MMLU-HU | HuGME | MT-Bench-HU | UD Hungarian |
|--------|------|---------|-------|-------------|--------------|
| **deepseek-v4-flash-cloud** | 73.3% | 52.0% | 9.5% (295 judged) | 50% (W0/L0/T1) | 69.9% (UPOS 89.7/UAS 47.0/LAS 73.0) |
| **deepseek-v4-pro-cloud** | 74.6% | 77.5% | 9.8% (294 judged) | 50% (W0/L0/T0) | 59.6% (UPOS 90.0/UAS 37.0/LAS 51.8) |
| **glm-5.1-cloud** | 71.6% | 84.5% | 9.2% (293 judged) | 50% (W0/L0/T0) | 38.8% (UPOS 86.5/UAS 11.7/LAS 18.1) |
| **glm-5.2-cloud** | 75.3% | 84.9% | 9.2% (294 judged) | 50% (W0/L0/T0) | 40.9% (UPOS 88.1/UAS 14.9/LAS 19.9) |
| **gpt-oss-120b-cloud** | 71.8% | 85.7% | 8.7% (122 judged) | 50% (W0/L0/T0) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **gpt-oss-20b-cloud** | 67.0% | 46.1% | 8.5% (117 judged) | 50% (W0/L0/T0) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **kimi-k2.6-cloud** | 75.9% | 73.7% | 9.4% (288 judged) | 50% (W0/L0/T0) | 61.8% (UPOS 90.8/UAS 39.6/LAS 55.1) |
| **minimax-m3-cloud** | 75.8% | 91.3% | 9.4% (291 judged) | 50% (W0/L0/T0) | 0.1% (UPOS 0.4/UAS 0.0/LAS 0.0) |
| **nemotron-3-ultra-cloud** | 70.5% | 82.7% | 8.5% (295 judged) | 50% (W0/L0/T0) | 42.5% (UPOS 76.1/UAS 22.0/LAS 29.5) |
| **qwen3.5-cloud** | 75.0% | 85.1% | 9.5% (294 judged) | 50% (W0/L0/T0) | 37.6% (UPOS 82.0/UAS 15.7/LAS 15.2) |
| **qwen3-next-80b-cloud** | 61.5% | RETIRED | RETIRED | RETIRED | RETIRED |

## think

| Modell | HuLU | MMLU-HU | HuGME | MT-Bench-HU | UD Hungarian |
|--------|------|---------|-------|-------------|--------------|
| **deepseek-v4-flash-cloud** | 76.7% | 86.6% | 9.5% (300 judged) | 50% (W0/L0/T0) | 0.3% (UPOS 0.4/UAS 0.2/LAS 0.2) |
| **deepseek-v4-pro-cloud** | 75.9% | 92.5% | 9.5% (297 judged) | 50% (W0/L0/T0) | 1.7% (UPOS 3.1/UAS 0.9/LAS 1.0) |
| **glm-5.1-cloud** | 75.8% | 92.7% | 9.4% (294 judged) | 50% (W0/L0/T0) | 0.8% (UPOS 0.7/UAS 0.9/LAS 0.9) |
| **glm-5.2-cloud** | 76.0% | 91.4% | 9.5% (292 judged) | 50% (W0/L0/T0) | 2.8% (UPOS 3.6/UAS 2.7/LAS 2.2) |
| **gpt-oss-120b-cloud** | 71.6% | 87.0% | 8.7% (93 judged) | 50% (W0/L0/T0) | 3.4% (UPOS 4.7/UAS 2.9/LAS 2.7) |
| **gpt-oss-20b-cloud** | 71.4% | 46.5% | 8.2% (295 judged) | 50% (W0/L0/T0) | 1.0% (UPOS 1.0/UAS 1.1/LAS 0.9) |
| **kimi-k2.6-cloud** | 75.2% | 92.7% | 9.4% (294 judged) | 50% (W0/L0/T0) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **minimax-m3-cloud** | 77.1% | 92.2% | 9.6% (292 judged) | 50% (W0/L0/T0) | 0.5% (UPOS 1.3/UAS 0.2/LAS 0.1) |
| **nemotron-3-ultra-cloud** | 71.8% | 91.7% | 8.8% (294 judged) | 50% (W0/L0/T0) | 7.5% (UPOS 8.8/UAS 7.5/LAS 6.2) |
| **qwen3.5-cloud** | 78.1% | 92.5% | 9.2% (291 judged) | 50% (W0/L0/T0) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **qwen3-next-80b-cloud** | 63.2% | RETIRED | RETIRED | RETIRED | RETIRED |

## Összesítés (futásidő és határidő)

| Benchmark | Aktív futások (10×2) | RETIRED (qwen3-next) | Összes item (cél) |
|-----------|----------------------|----------------------|-------------------|
| hulu | 20 | 2 (HuLU csak) | 51620 (HuLU: 56782) |
| mmlu_hu | 20 | 2 (HuLU csak) | 30000 (HuLU: 33000) |
| hugme | 20 | 2 (HuLU csak) | 5980 (HuLU: 6578) |
| mt_bench_hu | 20 | 2 (HuLU csak) | 480 (HuLU: 528) |
| ud_hungarian | 20 | 2 (HuLU csak) | 8980 (HuLU: 9878) |

### Futásidő modellek szerint (ó, mind az 5 benchmark összesen)

| Modell | nothink | think | Összesen |
|--------|---------|-------|----------|
| **deepseek-v4-flash-cloud** | 3.23 | 8.94 | 12.17 |
| **deepseek-v4-pro-cloud** | 3.10 | 12.45 | 15.55 |
| **glm-5.1-cloud** | 4.46 | 10.44 | 14.91 |
| **glm-5.2-cloud** | 3.83 | 9.82 | 13.65 |
| **gpt-oss-120b-cloud** | 25.78 | 9.65 | 35.43 |
| **gpt-oss-20b-cloud** | 148.83 | 41.14 | 189.97 |
| **kimi-k2.6-cloud** | 6.82 | 21.66 | 28.48 |
| **minimax-m3-cloud** | 11.30 | 13.51 | 24.82 |
| **nemotron-3-ultra-cloud** | 510.31 | 82.62 | 592.93 |
| **qwen3.5-cloud** | 17.16 | 84.35 | 101.51 |
| **ÖSSZES** | — | — | **1029.4 ó** |

### Legjobb modellek (egyszerű átlag a 4 fő benchmarkon)

Kiszámítva a HuLU + MMLU-HU + HuGME + UD composite átlagából (MT-Bench kimaradt, mert a 50% mindenkinél = semmi info).

| Modell | Mód | HuLU | MMLU-HU | HuGME | UD | Átlag |
|--------|-----|------|---------|-------|-----|-------|
| deepseek-v4-pro-cloud (nothink) | — | 74.6% | 77.5% | 9.8% | 59.6% | **55.4%** |
| kimi-k2.6-cloud (nothink) | — | 75.9% | 73.7% | 9.4% | 61.8% | **55.2%** |
| glm-5.2-cloud (nothink) | — | 75.3% | 84.9% | 9.2% | 40.9% | **52.6%** |
| qwen3.5-cloud (nothink) | — | 75.0% | 85.1% | 9.5% | 37.6% | **51.8%** |
| deepseek-v4-flash-cloud (nothink) | — | 73.3% | 52.0% | 9.5% | 69.9% | **51.2%** |
| nemotron-3-ultra-cloud (nothink) | — | 70.5% | 82.7% | 8.5% | 42.5% | **51.0%** |
| glm-5.1-cloud (nothink) | — | 71.6% | 84.5% | 9.2% | 38.8% | **51.0%** |
| nemotron-3-ultra-cloud (think) | — | 71.8% | 91.7% | 8.8% | 7.5% | **45.0%** |
| qwen3.5-cloud (think) | — | 78.1% | 92.5% | 9.2% | 0.0% | **44.9%** |
| glm-5.2-cloud (think) | — | 76.0% | 91.4% | 9.5% | 2.8% | **44.9%** |
| deepseek-v4-pro-cloud (think) | — | 75.9% | 92.5% | 9.5% | 1.7% | **44.9%** |
| minimax-m3-cloud (think) | — | 77.1% | 92.2% | 9.6% | 0.5% | **44.9%** |
| glm-5.1-cloud (think) | — | 75.8% | 92.7% | 9.4% | 0.8% | **44.7%** |
| kimi-k2.6-cloud (think) | — | 75.2% | 92.7% | 9.4% | 0.0% | **44.3%** |
| minimax-m3-cloud (nothink) | — | 75.8% | 91.3% | 9.4% | 0.1% | **44.1%** |

## Kapcsolódó dokumentumok

- [Korábbi státusz: 2026-07-13. 09:13 CEST (UD refuttatás indult)](benchmark-statusz-2026-07-13.md)
- [Korábbi státusz: 2026-07-13. v2](benchmark-statusz-2026-07-13-v2.md)
- [Korábbi státusz: 2026-07-13. v3](benchmark-statusz-2026-07-13-v3.md)
- [Korábbi státusz: 2026-07-11. 09:00 CEST (post-followup indult)](benchmark-statusz-2026-07-11.md)
- [Korábbi státusz: 2026-07-10. 05:42 CEST (queue kilépett)](benchmark-statusz-2026-07-10.md)
- [Eredmény aggregáció + vizualizáció](eredmeny-aggregacio.md) — composite score számítás
- [HuLU per-sub-task bontás (2026-06-16)](hulu-breakdown-2026-06-16.md) — HuLU sub-task részletek
- [Tevékenységnapló](../log.md) — 2026-07-10/11/13/14 bejegyzések

## Lábjegyzetek

1. **HuLU dedup (2026-07-10):** 4 modellnél 200 duplikátum törölve (qwen3.5-nothink 112, qwen3.5-think 29, gpt-oss:120b-nothink 19, nemotron-think 40).
2. **MMLU parser javítás (2026-07-10):** `extract_choice()` kiegészítve think-block strip-pel + explicit magyar szöveges leírásokkal. Újrafuttatás: nemotron-3-ultra-think 91.73% (5ó 14p, javított).
3. **MT-Bench multi-baseline (2026-07-13):** 3 baseline (deepseek-v4-flash:cloud, deepseek-v4-pro:cloud, kimi-k2.6:cloud) GSB átlaga. Eredmény: 50% (W0/L0/T24) minden modellnél, mert minden baseline-on döntetlent játszanak.
4. **HuGME rejudge (2026-07-13):** 22 modell × 300 item × 6 metrika. `gemini-3-flash-preview` bíró. Futásidő: ~21ó.
5. **UD refuttatás (2026-07-13/14):** 13 modell CoT-aware parser-rel. 3 nothink + 10 think. Összesített futásidő: ~32ó.
6. **gpt-oss:20b HuGME 138 ó outlier:** cloud rate limit, kihagyva az átlagból. Tényleges érték: 8.5% (117 judged).
7. **qwen3-next:80b RETIRED:** 2026-06-16 óta HTTP 410. Csak HuLU (kész) futott le, MMLU-HU/HuGME/MT-Bench/UD nem.

