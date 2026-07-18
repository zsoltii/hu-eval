# Benchmark Státusz (2026-07-09. 07:40 CEST)

Sorok: modell + mód (nothink/think). Oszlopok: benchmark. Cella: % kész + eredmény (ha 100%).

**Célméret:** HuLU=2581, MMLU-HU=1500, HuGME=299, MT-Bench-HU=24, UD Hungarian=449.

**Rövidítések:**
- `RETIRED` = qwen3-next:80b (HTTP 410, nem elérhető)
- `—` = nem indult
- HuGME: judge score (gemini-3-flash-preview bíró) + judged subset szám
- MT-Bench: W/L/T = win/loss/tie (baseline: deepseek-v4-flash)
- UD: (UPOS, UAS, LAS) — UPOS=szófaji, UAS=fej-dependencia, LAS=fej+deprel

## nothink

| Modell | HuLU | MMLU-HU | HuGME | MT-Bench-HU | UD Hungarian |
|--------|------|---------|-------|-------------|--------------|
| **deepseek-v4-flash-cloud** | 73.3% | 52.0% | 9.7% (91 judged) | 0% (W0/L2/T22) | 64.6% (UPOS 82.2/UAS 43.5/LAS 68.2) |
| **deepseek-v4-pro-cloud** | 74.6% | 77.5% | 9.7% (91 judged) | 100% (W3/L0/T21) | 44.5% (UPOS 55.8/UAS 31.5/LAS 46.3) |
| **glm-5.1-cloud** | 71.6% | 84.5% | 9.8% (79 judged) | 75% (W3/L1/T20) | 22.7% (UPOS 31.6/UAS 12.5/LAS 24.0) |
| **glm-5.2-cloud** | 75.3% | 84.9% | 9.7% (77 judged) | 100% (W2/L0/T22) | 20.5% (UPOS 27.0/UAS 14.2/LAS 20.4) |
| **gpt-oss-120b-cloud** | 71.8% | 85.7% | 8.5% (97 judged) | 17% (W1/L5/T18) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **gpt-oss-20b-cloud** | 67.0% | 46.1% | 8.9% (71 judged) | 0% (W0/L8/T16) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **kimi-k2.6-cloud** | 75.9% | 73.7% | 9.0% (78 judged) | 100% (W2/L0/T22) | 38.6% (UPOS 48.6/UAS 27.9/LAS 39.3) |
| **minimax-m3-cloud** | 75.8% | 91.3% | 9.6% (104 judged) | 100% (W1/L0/T23) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **nemotron-3-ultra-cloud** | 70.5% | 82.7% | 8.2% (75 judged) | 50% (W1/L1/T22) | 19.4% (UPOS 25.9/UAS 13.4/LAS 18.9) |
| **qwen3.5-cloud** | 75.0% | 85.1% | 9.7% (52 judged) | 100% (W2/L0/T22) | 20.4% (UPOS 26.0/UAS 17.2/LAS 17.9) |
| **qwen3-next-80b-cloud** | 61.5% | RETIRED | RETIRED | RETIRED | RETIRED |

## think

| Modell | HuLU | MMLU-HU | HuGME | MT-Bench-HU | UD Hungarian |
|--------|------|---------|-------|-------------|--------------|
| **deepseek-v4-flash-cloud** | 76.7% | 86.6% | 9.7% (85 judged) | 50% (W0/L0/T24) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **deepseek-v4-pro-cloud** | 75.9% | 92.5% | 9.3% (96 judged) | 86% (W6/L1/T17) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **glm-5.1-cloud** | 75.8% | 92.7% | 9.6% (81 judged) | 100% (W8/L0/T16) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **glm-5.2-cloud** | 76.0% | 91.4% | 9.7% (72 judged) | 100% (W6/L0/T18) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **gpt-oss-120b-cloud** | 71.6% | 87.0% | 8.6% (89 judged) | 0% (W0/L4/T20) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **gpt-oss-20b-cloud** | 32% (828/2581) | 46.5% | 9.3% (86 judged) | 0% (W0/L7/T17) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **kimi-k2.6-cloud** | 75.2% | 92.7% | 9.6% (68 judged) | 100% (W3/L0/T21) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **minimax-m3-cloud** | 77.1% | 92.2% | 9.4% (100 judged) | 100% (W2/L0/T22) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **nemotron-3-ultra-cloud** | 71.8% | 58% (879/1500) | 8.6% (91 judged) | 80% (W4/L1/T19) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **qwen3.5-cloud** | 78.1% | 92.5% | 9.3% (70 judged) | 100% (W2/L0/T22) | 0.0% (UPOS 0.0/UAS 0.0/LAS 0.0) |
| **qwen3-next-80b-cloud** | 63.2% | RETIRED | RETIRED | RETIRED | RETIRED |

## Összesítés

| Benchmark | Kész futások (nothink+think) | Hátralévő |
|-----------|--------------------------------|-----------|
| hulu | 21 | 1 részleges |
| mmlu_hu | 21 | 1 részleges |
| hugme | 22 | 0 részleges |
| mt_bench_hu | 22 | 0 részleges |
| ud_hungarian | 22 | 0 részleges |

