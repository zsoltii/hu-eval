# Benchmark Státusz Táblázat — 2026-07-13. 09:13 CEST

**Utolsó frissítés:** 2026-07-13. 09:13 CEST — UD refuttatás fut (3/449 item)

## Státusz (11 modell × 2 mód × 5 benchmark = 110 cella)

| Modell | Mód | HuLU (acc) | MMLU-HU (acc) | HuGME (score) | MT-Bench-HU (GSB) | UD (acc/UPOS/UAS/LAS) |
|--------|-----|-----------|---------------|---------------|--------------------|------------------------|
| deepseek-v4-flash-cloud | nothink | 73.34% | 52.00% | 9.5% (295) | 50% (W0/L0/T1) | 69.9% (U90/47/73) |
| deepseek-v4-flash-cloud | think | 76.71% | 86.60% | 9.5% (300) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| deepseek-v4-pro-cloud | nothink | 74.58% | 77.53% | 9.8% (294) | 50% (W0/L0/T0) | 59.6% (U90/37/52) |
| deepseek-v4-pro-cloud | think | 75.90% | 92.47% | 9.5% (297) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| glm-5.1-cloud | nothink | 71.60% | 84.47% | 9.2% (293) | 50% (W0/L0/T0) | 38.8% (U87/12/18) |
| glm-5.1-cloud | think | 75.75% | 92.67% | 9.4% (294) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| glm-5.2-cloud | nothink | 75.32% | 84.93% | 9.2% (294) | 50% (W0/L0/T0) | 40.9% (U88/15/20) |
| glm-5.2-cloud | think | 75.98% | 91.40% | 9.5% (292) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| gpt-oss-120b-cloud | nothink | 71.79% | 85.67% | 8.7% (122) | 50% (W0/L0/T0) | 2% (11/449) |
| gpt-oss-120b-cloud | think | 71.64% | 87.00% | 8.7% (93) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| gpt-oss-20b-cloud | nothink | 66.99% | 46.07% | 8.5% (117) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |
| gpt-oss-20b-cloud | think | 71.41% | 46.47% | 8.2% (295) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| kimi-k2.6-cloud | nothink | 75.94% | 73.73% | 9.4% (288) | 50% (W0/L0/T0) | 61.8% (U91/40/55) |
| kimi-k2.6-cloud | think | 75.24% | 92.73% | 9.4% (294) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| minimax-m3-cloud | nothink | 75.78% | 91.33% | 9.4% (291) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |
| minimax-m3-cloud | think | 77.14% | 92.20% | 9.6% (292) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| nemotron-3-ultra-cloud | nothink | 70.52% | 82.67% | 8.5% (295) | 50% (W0/L0/T0) | 42.5% (U76/22/30) |
| nemotron-3-ultra-cloud | think | 71.79% | 91.73% | 8.8% (294) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| qwen3.5-cloud | nothink | 75.05% | 85.07% | 9.5% (294) | 50% (W0/L0/T0) | 37.6% (U82/16/15) |
| qwen3.5-cloud | think | 78.15% | 92.47% | 9.2% (291) | 50% (W0/L0/T0) | 0.0% (U0/0/0) |

| qwen3-next-80b-cloud | nothink | 61.45% | RETIRED | RETIRED | RETIRED | RETIRED |
| qwen3-next-80b-cloud | think | 63.23% | RETIRED | RETIRED | RETIRED | RETIRED |

## Összesítés — Összes / Kész / Hátralévő / Átlag futásidő

| Benchmark | Összes item | Kész | Hátralévő | Átlag futásidő (24ó outlier-szűrés) | Megjegyzés |
|-----------|-------------|------|-----------|-------------------------------------|-----------|
| hulu | 56782 | 56782 | 0 | 4ó 27p | kész (22/22 modell) |
| mmlu_hu | 33000 | 30000 | 3000 | 3ó 34p | 20/22 modell kész |
| hugme | 6578 | 5980 | 598 | 1ó 48p | bíró rejudge kész (gemini-3-flash-preview) |
| mt_bench_hu | 528 | 480 | 48 | 0ó 23p | bíró rejudge kész (gemini-3-flash-preview) |
| ud_hungarian | 9878 | 8531 | 1347 | 0ó 48p | refuttatás fut (CoT-aware parser) |

## Jelmagyarázat

- **`XX% (N/target)`** = futás készültsége (N = feldolgozott item), NEM accuracy
- **`XX.X%`** = benchmark accuracy (futás 100% kész)
- **`UD (acc/UPOS/UAS/LAS)`** = accuracy / UPOS-címke / UAS (fej-dependencia) / LAS (fej+deprel)
- **`HuGME (score)`** = bíró átlag score, 6 metrika/item × 299 item, rejudge kész (2026-07-13. 06:31)
- **`MT-Bench-HU (GSB)`** = score% + W/L/T (wins/losses/ties) 24 item-en, rejudge multi-baseline kész (2026-07-13. 07:00)
- **`RETIRED`** = `qwen3-next:80b` (HTTP 410, kihagyva 2026-06-16 óta)

## Aktuális állapot (2026-07-13. 09:13 CEST)

**Futó folyamat:**
- `run_ud_hungarian.py --model gpt-oss:120b-cloud --mode nothink --reset` (PID 413412) — 10/449 (2.2%)

**Befejezett fázisok:**
- ✅ HuGME rejudge: 2026-07-13. 06:31 (~21ó futásidő)
- ✅ MT-Bench rejudge: 2026-07-13. 07:00 (~29p futásidő)

**Hátralévő:**
- UD refuttatás: 3 nothink + 10 think modell × ~40p/modell = ~8.7 ó

## Becsült teljes befejezés

- **UD refuttatás várható kész:** 2026-07-13. ~18:00 CEST
- **3 nap határidő (gemini-3-flash-preview megszűnése):** 2026-07-14.
- **Státusz:** BŐVEN belefér a határidőbe (~9 ó tartalék)
