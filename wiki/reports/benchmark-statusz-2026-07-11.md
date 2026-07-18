# Benchmark Státusz Táblázat — 2026-07-11. 09:00 CEST

**Utolsó frissítés:** 2026-07-11. 09:00 CEST — `post_followup.sh` fut (UD refuttatás)

## Státusz (11 modell × 2 mód × 5 benchmark = 110 cella)

| Modell | Mód | HuLU (acc) | MMLU-HU (acc) | HuGME (score) | MT-Bench-HU (GSB) | UD (acc/UPOS/UAS/LAS) |
|--------|-----|-----------|---------------|---------------|--------------------|------------------------|
| deepseek-v4-flash-cloud | nothink | 73.34% | 52.00% | 9.7% (91/299) | 0% (W0/L2/T22) | 69.9% (U90/47/73) |
| deepseek-v4-flash-cloud | think | 76.71% | 86.60% | 9.7% (85/299) | 50% (W0/L0/T24) | 0.0% (U0/0/0) |
| deepseek-v4-pro-cloud | nothink | 74.58% | 77.53% | 9.7% (91/299) | 100% (W3/L0/T21) | 59.6% (U90/37/52) |
| deepseek-v4-pro-cloud | think | 75.90% | 92.47% | 9.3% (96/299) | 86% (W6/L1/T17) | 0.0% (U0/0/0) |
| glm-5.1-cloud | nothink | 71.60% | 84.47% | 9.8% (79/299) | 75% (W3/L1/T20) | 38.8% (U87/12/18) |
| glm-5.1-cloud | think | 75.75% | 92.67% | 9.6% (81/299) | 100% (W8/L0/T16) | 0.0% (U0/0/0) |
| glm-5.2-cloud | nothink | 75.32% | 84.93% | 9.7% (77/299) | 100% (W2/L0/T22) | 40.9% (U88/15/20) |
| glm-5.2-cloud | think | 75.98% | 91.40% | 9.7% (72/299) | 100% (W6/L0/T18) | 0.0% (U0/0/0) |
| gpt-oss-120b-cloud | nothink | 71.79% | 85.67% | 8.5% (97/299) | 17% (W1/L5/T18) | 1% (10/449) 🔄 |
| gpt-oss-120b-cloud | think | 71.64% | 87.00% | 8.6% (89/299) | 0% (W0/L4/T20) | 0.0% (U0/0/0) |
| gpt-oss-20b-cloud | nothink | 66.99% | 46.07% | 8.9% (71/299) | 0% (W0/L8/T16) | 0.0% (U0/0/0) |
| gpt-oss-20b-cloud | think | 71.41% | 46.47% | 9.3% (86/299) | 0% (W0/L7/T17) | 0.0% (U0/0/0) |
| kimi-k2.6-cloud | nothink | 75.94% | 73.73% | 9.0% (78/299) | 100% (W2/L0/T22) | 61.8% (U91/40/55) |
| kimi-k2.6-cloud | think | 75.24% | 92.73% | 9.6% (68/299) | 100% (W3/L0/T21) | 0.0% (U0/0/0) |
| minimax-m3-cloud | nothink | 75.78% | 91.33% | 9.6% (104/299) | 100% (W1/L0/T23) | 0.0% (U0/0/0) |
| minimax-m3-cloud | think | 77.14% | 92.20% | 9.4% (100/299) | 100% (W2/L0/T22) | 0.0% (U0/0/0) |
| nemotron-3-ultra-cloud | nothink | 70.52% | 82.67% | 8.2% (75/299) | 50% (W1/L1/T22) | 42.5% (U76/22/30) |
| nemotron-3-ultra-cloud | think | 71.79% | 91.73% | 8.6% (91/299) | 80% (W4/L1/T19) | 0.0% (U0/0/0) |
| qwen3.5-cloud | nothink | 75.05% | 85.07% | 9.7% (52/299) | 100% (W2/L0/T22) | 37.6% (U82/16/15) |
| qwen3.5-cloud | think | 78.15% | 92.47% | 9.3% (70/299) | 100% (W2/L0/T22) | 0.0% (U0/0/0) |
| qwen3-next-80b-cloud | nothink | 61.45% | RETIRED | RETIRED | RETIRED | RETIRED |
| qwen3-next-80b-cloud | think | 63.23% | RETIRED | RETIRED | RETIRED | RETIRED |

## Jelmagyarázat

- **`XX% (N/target)`** = futás készültsége (N = feldolgozott item), NEM accuracy
- **`XX.X%`** = benchmark accuracy (futás 100% kész)
- **`UD (acc/UPOS/UAS/LAS)`** = accuracy / UPOS-címke / UAS (fej-dependencia) / LAS (fej+deprel)
- **`HuGME (score)`** = bíró átlag score, 6 metrika/item × 299 item
- **`MT-Bench-HU (GSB)`** = score% + W/L/T (wins/losses/ties) 24 item-en
- **`RETIRED`** = `qwen3-next:80b` (HTTP 410, kihagyva 2026-06-16 óta)
- **`🔄`** = futó refuttatás (post_followup.sh-ból)

## Aktuális állapot (2026-07-11. 09:00 CEST)

**Futó folyamat (PID 362121):**
- `run_ud_hungarian.py --model gpt-oss:120b-cloud --mode nothink --reset` — 10/449 (2.2%), 4 perc eltelt

**Befejezett followup-ok (2026-07-10/11):**
- HuLU gpt-oss:20b-think: 71.41% (2581/2581) ✅ — 27ó 43p
- MMLU-HU nemotron-3-ultra-think: 91.73% (1500/1500) ✅ — 5ó 14p

## Összesítés futásidőkről (24ó outlier-szűrés után)

| Benchmark | Összes item | nothink átlag | think átlag | Megjegyzés |
|-----------|-------------|----------------|-------------|------------|
| HuLU | 2581 | 4ó 36p | 4ó 17p | leglassabb: qwen3.5-think 67ó30p, gpt-oss:20b-think 27ó43p (CoT) |
| MMLU-HU | 1500 | 2ó 26p | 4ó 42p | think mode 2× lassabb |
| HuGME | 299 | 1ó 13p | 2ó 17p | + rejudge 22 modell |
| MT-Bench-HU | 24 | 18p | 28p | + rejudge 20 modell |
| UD Hungarian | 449 | 41p | 55p | CoT-strip parser 2026-07-10 óta |

**Befejezett futások száma:** 22/22 HuLU, 20/22 MMLU-HU, 20/22 HuGME, 20/22 MT-Bench-HU, 19/22 UD.

## Hátralévő post_followup.sh feladatok

| # | Feladat | Modellek | Becsült idő |
|---|---------|----------|-------------|
| 1 | UD nothink refuttatás | 3 modell (gpt-oss:120b fut, +2: gpt-oss:20b, minimax-m3) | ~30 perc |
| 2 | UD think refuttatás | 10 modell × 449 item (num_predict 256→2048) | ~3.7-7.5 óra |
| 3 | HuGME rejudge | 22 modell × 299 item × 6 metrika | ~22 óra |
| 4 | MT-Bench rejudge multi-baseline | 20 modell × 24 item × 3 baseline | ~1.3 óra |
| 5 | Státusz táblázat végleges | — | 1p |

**Becsült teljes ETA:** **2026-07-12. ~08:00 CEST** (kb. 23 óra múlva)
