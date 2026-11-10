# Muse Spark Open (Cloud)

*Típus:* entity
*Forrás(ok):* belső benchmark futtatások (`results/muse-spark-open-cloud-*`), `reports/composite_scores.csv`, [riport 2026-10-27](../reports/report-2026-10-27.md)
*Létrehozva:* 2026-10-27
*Frissítve:* 2026-10-27 (mindkét mód teljes: nothink + think)

---

## Azonosítás

- **Ollama alias:** `muse-spark-open:cloud`
- **Elérhetőség:** cloud-only, Ollama-n keresztül
- **Kvantálás:** `ollama-cloud` (a lokális kvantálás nem ismert)
- **Státusz a projektben:** aktív benchmark modell — a **2026-10-27-i állapot szerint a mezőny legjobb composite-eredménye** (mindkét módban)
- **Backend:** `ollama` (`http://localhost:11434/api/generate`), explicit `think: true/false`, 32 768 tokenes plafon, sampling paraméter nélkül

## Eredmények — nothink

| Benchmark | Eredmény |
|---|---|
| HuLU | 77,06% (1990/2581) — HuCoLA 81,9 / HuCoPA 98,0 / HuRTE 93,4 / HuSST 70,9 / HuWNLI 10,0 / HuCB 84,5 |
| MMLU-HU | 91,40% (1500 sor, duplikált dataset) |
| HuGME | 0,9054 (faithfulness 0,513 a leggyengébb) |
| MT-Bench-HU | 0,5625 (8W / 2L / 38T) |
| UD Hungarian | UPOS 89,71% / UAS 82,54% / LAS 63,37% → composite 78,54% |
| **Composite (40/40/20)** | **0,7876** |

## Eredmények — think

| Benchmark | Eredmény | Δ vs. nothink |
|---|---|---|
| HuLU | 77,41% (1998/2581) — HuCoLA 82,2 / HuCoPA 97,0 / HuRTE 90,5 / HuSST 72,7 / HuWNLI 11,7 / HuCB 76,7 | +0,35 |
| MMLU-HU | 93,07% (750 egyedi kérdés, dedupolt) | +1,67 |
| HuGME | 0,9034 (faithfulness 0,547) | −0,20 |
| MT-Bench-HU | 0,5729 (8W / 1L / 39T) | +1,04 |
| UD Hungarian | UPOS 89,88% / UAS 82,76% / LAS 63,63% → composite 78,76%, parse 100% | +0,22 |
| **Composite (40/40/20)** | **0,7937** | **+0,61** |

## Profil

- **Erősségei:** HuCoPA (97–98%), HuRTE (90–93%), HuGME (0,90), UD (78,8% composite — a mezőny legjobbja), MMLU (91–93%).
- **Gyengeségei:** **HuWNLI 10–11,7%** — a mezőny legrosszabbja, miközben a lokális 9B modell 60%-ot ér el ugyanezen a sub-taskon (valószínűleg formátum-érzékenység a 2 osztályos feladatra); **HuGME faithfulness ~0,5** (forráshűség).
- **Think viselkedés:** a gondolkodás **alig változtat** (+0,6 composite); a HuCB-n ront (−7,8), az MMLU-n javít (+1,7). Ez lényegesen kisebb hatás, mint a `mistral-large-4`-nél (ott a think rontott a tönkrement UD miatt).
- **Sebesség:** HuLU think 2581 item 3 h 18 m (≈4,6 s/item), MMLU 750 item ≈1 h 45 m, HuGME 300 item 43 m, MT-Bench 24 item 8 m, UD 449 item 3 h 24 m (≈27 s/item).

## Történet

| Dátum | Esemény |
|---|---|
| 2026-10-22 | nothink kör lefutott (HuLU 77,06% — akkor a legjobb HuLU); a think kör a HuLU 871/2581-nél megállt heti kvóta miatt |
| 2026-10-26 | think kör újraindítva tiszta protokollal (`--reset`, 32k, nincs sampling param); gép-újraindítás miatt 11:35-kor leállt, majd folytatódott |
| 2026-10-27 | think kör befejezve: composite **0,7937** → a mezőny élén (nothink 0,7876 a 2. helyen) |

## Kapcsolódó

- [Riport 2026-10-27 (think kör)](../reports/report-2026-10-27.md)
- [Riport 2026-10-24 (lokális kör + cloud mezőny)](../reports/report-2026-10-24.md)
- [Modell vs. modell összehasonlítás](../comparisons/modell-vs-modell.md)
- [Cloud vs. lokális](../comparisons/cloud-vs-lokal.md)
