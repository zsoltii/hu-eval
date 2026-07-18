# Benchmark Státusz (2026-07-10. 05:42 CEST — queue kilépett)

Sorok: modell + mód (nothink/think). Oszlopok: benchmark. Cella: % kész + eredmény (ha 100%).

**Célméret:** HuLU=2581, MMLU-HU=1500, HuGME=299, MT-Bench-HU=24, UD Hungarian=449.

**Jelmagyarázat:**
- Ha a cella `XX% (N/target)` formátumú, az **a futás készültsége** (N=feldolgozott item), nem accuracy.
- Ha a cella `XX.X%` formátumú (vagy kompozit UPOS/UAS/LAS), az **a benchmark accuracy-értéke** (futás 100% kész).
- HuLU nehéz benchmark: a 60-78% accuracy NEM a futás készültségét jelzi, hanem a modell pontszámát.

**Rövidítések:**
- `RETIRED` = qwen3-next:80b (HTTP 410, nem elérhető)
- `—` = nem indult
- HuGME: judge score (gemini-3-flash-preview bíró) + judged subset szám
- MT-Bench: W/L/T = win/loss/tie (baseline: deepseek-v4-flash)
- UD: (UPOS, UAS, LAS) — UPOS=szófaji, UAS=fej-dependencia, LAS=fej+deprel

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

## Összesítés

| Benchmark | Kész futások (nothink+think) | Hátralévő |
|-----------|--------------------------------|-----------|
| hulu | 22 | 0 részleges |
| mmlu_hu | 22 | 0 részleges |
| hugme | 22 | 0 részleges |
| mt_bench_hu | 22 | 0 részleges |
| ud_hungarian | 22 | 0 részleges |

