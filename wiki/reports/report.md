# Összesítő riport — 2026-11-10. (minden futtatás egyben: 2026-07-es archív kör + 2026-11-es nincs-plafon kör)

*Típus:* report
*Forrás(ok):* `results/*/*_summary.json`, `reports/composite_scores.csv`, `reports/hulu_breakdown.md`, `reports/mmlu_hu_breakdown.md`, `reports/ud_hungarian_breakdown.md`, `logs/run{14,15,16,17}/driver.log`, korábbi riportok: [2026-07-14](report-2026-07-14.md), [2026-07-27](report-2026-07-27-lokalis-qwen3-next.md), [2026-10-22](report-2026-10-22.md), [2026-10-24](report-2026-10-24.md), [2026-10-27](report-2026-10-27.md), [2026-10-27 beam](report-2026-10-27-beam.md), [nincs-plafon kör](report-nincs-plafon-kor.md)
*Létrehozva:* 2026-11-10
*Frissítve:* 2026-11-10 (a teljes archív mezőny per-benchmark eredményeivel kiegészítve)

---

## Fejléc

| Mező | Érték |
|---|---|
| Riport azonosító | `hu-eval-20261110-osszesito` |
| Riport státusz | **Kanonikus összesítő** — a 2026-11-es nincs-plafon kör + a 2026-07-es archív kör **együtt** |
| Aktuális kör | `deepseek-v4.1-flash:cloud`, `muse-spark-open:cloud`, `beam:cloud`, `mistral-large-4:cloud`, `minimax-m3.1-flash:cloud` (think/nothink) + `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL` (lokális) |
| Archív kör (2026-07) | `qwen3.5:cloud`, `qwen3-next:80b-cloud`, `gpt-oss:120b-cloud`, `gpt-oss:20b-cloud`, `kimi-k2.6:cloud`, `glm-5.1:cloud`, `glm-5.2:cloud`, `nemotron-3-ultra:cloud`, `deepseek-v4-flash:cloud`, `deepseek-v4-pro:cloud`, `minimax-m3:cloud` + `Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` (lokális) |
| Bíró modell | `deepseek-v4-pro:0813-cloud` (HuGME + MT-Bench-HU) |
| Backend | cloud: `ollama` (streaming a hosszú hívásokon); lokális: `openai` (llama-server `:8080/v1`) |
| Módszertan (aktuális) | **Ollama Cloud: nincs kimeneti plafon**; **lokális: 32 768 token**; sampling paraméter nélkül; explicit `think` flag |
| Módszertan (archív) | `temperature: 0.0`, 4096–16384 tokenes limitek, más bíró-prompt — **nem összemérhető** |

### Modell-kvantálás

| Modell | Kvantálás | Megjegyzés |
|---|---|---|
| `deepseek-v4.1-flash:cloud` | `ollama-cloud` | lokális kvantálás nem ismert |
| `muse-spark-open:cloud` | `ollama-cloud` | — |
| `beam:cloud` | `ollama-cloud` | 501B, 1M kontextus, **think-only** |
| `mistral-large-4:cloud` | `ollama-cloud` | — |
| `minimax-m3.1-flash:cloud` | `ollama-cloud` | a nothink itt működik |
| `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL` | **`UD-Q4_K_XL`** | ~4 bit, MTP, llama-server `-c 32000 --parallel 1` |
| archív cloud modellek | `ollama-cloud` | — |
| `Qwen3-Next-80B-A3B-Thinking-GGUF` | **`UD-IQ3_XXS`** | 3,06 bpw, 32,95 GB, 128K context |

---

## Executive Summary

- **Holtverseny az élen:** `deepseek-v4.1-flash (think)` **0,7901** és `muse-spark-open (think)` **0,7896** — 0,0005 különbség, a mérési zajon belül. A deepseek a GEN (0,729) és LING (0,804) dimenziót nyeri, a muse a STAT-ot (0,852).
- **Csak a 2026-11-es nincs-plafon kör (9 futtatás) nem kompromittált.** A 2026-10-es kör 32k kimeneti plafonja és a 2026-07-es kör 4–16k limitje / 16K contextje miatt **31 futtatás kompromittált** (lásd a 0. táblázat `Limit / context` oszlopát és a 0.1 szekciót).
- **A plafon hatása modellfüggő és nagy:** a deepseek think UD 64,78 → **80,40** composite (+15,6; 91 → 1 üres válasz), a minimax nothink MT-Bench +14,6 pt; a **muse MT-Bench viszont rontott** (−2,1 / −6,3). A HuLU/MMLU/HuGME-n a hatás ≤0,13 pt (beam A/B).
- A **lokális 9B** (0,5345) a UD-n (19,91%) és az MMLU-n (65,53%) szakad le; a **HuWNLI-n viszont ő a legjobb** (60,0%) — a nagy modellek ezt a 2 osztályos NLI-formátumot rontják el (8,3–16,7%).

---

## 0. Minden futtatás egy táblázatban

A **teljes** eddigi mezőny, **futtatás-szinten** (ugyanaz a modell több körben is szerepel, mert a protokoll változott). Composite szerint csökkenő sorrendben; a `Kör` oszlop a futtatás idejét/protokollját jelzi.


**Limit-jelölés (kompromittált futtatások):** `⚠️` = **csökkentett kimeneti/context-ablak** volt a futásnál → az eredmény **kompromittált** (a modell képességét alulméri). `⚠️⚠️` = a 2026-07-es kör (greedy + 4–16k kimenet, illetve a lokális modellnél 16K context) — **erősen kompromittált**. `✅` = nincs plafon, teljes context.

### 0.1 Kompromittált futtatások (csökkentett context / kimeneti ablak)

| Kör | Mi volt a limit | Mely futtatások | Hatás |
|---|---|---|---|
| 2026-07 | `temperature: 0.0`, **4096–16384 token kimenet**, más bíró-prompt | 21 cloud futtatás (qwen3.5, gpt-oss-120b/20b, kimi-k2.6, glm-5.1/5.2, nemotron-3-ultra, deepseek-v4-flash/pro, minimax-m3, qwen3-next-80b) | A think modellek UD-je 0,0–7,5% (a CoT felemésztette a keretet) — **érvénytelen**; a HuGME 0–10-es skálán, más prompttal készült; az MT-Bench mindenhol 50% (nem differenciál) |
| 2026-07 | **16K context** (később 64K, UD-nél 128K) | Qwen3-Next-80B IQ3_XXS (lokális) | Rövid kontextus mellett a hosszú UD-mondatok és a HuGME-kontextusok csonkultak |
| 2026-10 | **32 768 token kimeneti plafon** | 10 futtatás (muse nt/th 32k, beam 32k, minimax nt/th, mistral nt/th, deepseek nt/th, lokális 9B) | A deepseek think UD 20,3%-a **üres válasz** lett (composite 64,78 a valós 80,40 helyett); a lokális 9B UD parse-hányada 83,1% |
| 2026-10 | **32 000 token context** (llama-server `-c 32000`) | unsloth Qwen3.5-9B (lokális) | A prompt + válasz együtt 32k-ba kellett férjen; a hosszú UD-mondatoknál ez szűk |

**A 2026-11-es nincs-plafon kör (9 futtatás) az egyetlen, amely nem kompromittált** — ezek az összehasonlítás alapjai.

**Jelmagyarázat:** † = 2026-07-es protokoll (greedy + 4096–16384 limit, más bíró-prompt → **nem összemérhető**); ‡ = hiányzó UD, súly-újraosztás (STAT 50% / GEN 50%); * = a riport nem közölte, a részpontszámokból számított érték.

| # | Kör | Modell | Mód | HuLU | MMLU | HuGME | MT-Bench | UD | **Composite** | Limit / context |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11 | deepseek-v4.1-flash | think | 76,75 | 92,13 | 0,9369 | 0,5208 | **80,40** | **0,7901** | ✅ nincs plafon |
| 2 | 2026-11 | muse-spark-open | think | **77,41** | 93,07 | 0,9034 | **0,5521** | 78,76 | **0,7896** | ✅ nincs plafon |
| 3 | 2026-11 | muse-spark-open | nothink | 77,06 | 91,40 | 0,9054 | 0,5000 | 78,54 | 0,7751 | ✅ nincs plafon |
| 4 | 2026-11 | beam | think | 75,17 | 91,60 | 0,9087 | 0,5208 | 77,16 | 0,7737 | ✅ nincs plafon |
| 5 | 2026-11 | mistral-large-4 | think | 76,21 | 92,43 | 0,9191 | 0,5208 | 73,98 | 0,7732 | ✅ nincs plafon |
| 6 | 2026-10 | muse-spark-open | think | 77,41 | 93,07 | 0,9034 | 0,5729 | 78,76 | 0,7937 | ⚠️ 32k kimenet |
| 7 | 2026-10 | beam | think | 75,09 | 91,73 | 0,9082 | 0,4896 | 76,74 | 0,7667 | ⚠️ 32k kimenet |
| 8 | 2026-11 | minimax-m3.1-flash | think | 73,46 | 87,86 | 0,8729 | 0,5000 | 61,37 | 0,7200 | ✅ nincs plafon |
| 9 | 2026-11 | deepseek-v4.1-flash | nothink | 74,16 | 82,33 | 0,9302 | 0,4688 | 59,77 | 0,7123 | ✅ nincs plafon |
| 10 | 2026-11 | minimax-m3.1-flash | nothink | 72,22 | 87,60 | 0,8687 | 0,4896 | 56,92 | 0,7051 | ✅ nincs plafon |
| 11 | 2026-11 | mistral-large-4 | nothink | 75,05 | 83,13 | 0,8946 | 0,4375 | 58,61 | 0,7000 | ✅ nincs plafon |
| 12 | 2026-10 | minimax-m3.1-flash | think | 0,735 | 0,879 | 0,873 | 0,417 | — | 0,726 ‡ | ⚠️ 32k kimenet |
| 13 | 2026-10 | minimax-m3.1-flash | nothink | 0,722 | 0,876 | 0,869 | 0,344 | — | 0,703 ‡ | ⚠️ 32k kimenet |
| 14 | 2026-10 | muse-spark-open | nothink | 0,771 | 0,914 | 0,905 | 0,563 | 0,754 | 0,781 | ⚠️ 32k kimenet |
| 15 | 2026-10 | mistral-large-4 | nothink | 0,751 | 0,831 | 0,895 | 0,438 | 0,581 | 0,699 | ⚠️ 32k kimenet |
| 16 | 2026-10 | deepseek-v4.1-flash (ref.) | nothink | 0,742 | 0,823 | 0,930 | 0,438 | 0,320 | 0,650 | ⚠️ 32k kimenet |
| 17 | 2026-10 | mistral-large-4 | think | 0,762 | 0,924 | 0,919 | 0,490 | 0,084 | 0,636 | ⚠️ 32k kimenet |
| 18 | 2026-10 | deepseek-v4.1-flash (ref.) | think | 0,768 | 0,921 | 0,937 | 0,417 | 0,131 | 0,635 | ⚠️ 32k kimenet |
| 19 | 2026-10 | unsloth Qwen3.5-9B UD-Q4_K_XL (lok.) | nothink | 70,21 | 65,53 | 0,7203 | 0,3958 | 19,91 | 0,5345 | ⚠️ 32k **context** |
| 20 | 2026-07 | Qwen3-Next-80B IQ3_XXS (lok.) | think | 56,53 | 86,87 | 82,83 † | 37,50 | 64,73 | 64,85 † | ⚠️⚠️ 16K **context** |
| 21 | 2026-07 | deepseek-v4-pro | nothink | 74,6 | 77,5 | 9,8 † | 50,0 † | 59,6 | 54,3 † | ⚠️⚠️ 4–16k kimenet |
| 22 | 2026-07 | kimi-k2.6 | nothink | 75,9 | 73,7 | 9,4 † | 50,0 † | 61,8 | 54,2 † | ⚠️⚠️ 4–16k kimenet |
| 23 | 2026-07 | glm-5.2 | nothink | 76,6 | 84,9 | 9,2 † | 50,0 † | 40,9 | 52,1 † | ⚠️⚠️ 4–16k kimenet |
| 24 | 2026-07 | qwen3.5 | nothink | 75,0 | 85,1 | 9,5 † | 50,0 † | 37,6 | 51,5 † | ⚠️⚠️ 4–16k kimenet |
| 25 | 2026-07 | deepseek-v4-flash | nothink | 73,3 | 52,0 | 9,5 † | 50,0 † | 69,9 | 51,0 † | ⚠️⚠️ 4–16k kimenet |
| 26 | 2026-07 | nemotron-3-ultra | nothink | 70,5 | 82,7 | 8,5 † | 50,0 † | 42,5 | 50,9 † | ⚠️⚠️ 4–16k kimenet |
| 27 | 2026-07 | glm-5.1 | nothink | 71,6 | 84,5 | 9,2 † | 50,0 † | 38,8 | 50,8 † | ⚠️⚠️ 4–16k kimenet |
| 28 | 2026-07 | qwen3.5 | think | 78,1 | 92,5 | 9,2 † | 50,0 † | 0,0 | 46,0 † | ⚠️⚠️ 4–16k kimenet |
| 29 | 2026-07 | nemotron-3-ultra | think | 71,8 | 91,7 | 8,8 † | 50,0 † | 7,5 | 46,0 † | ⚠️⚠️ 4–16k kimenet |
| 30 | 2026-07 | glm-5.2 | think | 75,5 | 91,4 | 9,5 † | 50,0 † | 2,8 | 45,9 † | ⚠️⚠️ 4–16k kimenet |
| 31 | 2026-07 | deepseek-v4-pro | think | 75,9 | 92,5 | 9,5 † | 50,0 † | 1,7 | 45,9 † | ⚠️⚠️ 4–16k kimenet |
| 32 | 2026-07 | minimax-m3 | think | 77,1 | 92,2 | 9,6 † | 50,0 † | 0,5 | 45,9 † | ⚠️⚠️ 4–16k kimenet |
| 33 | 2026-07 | glm-5.1 | think | 75,8 | 92,7 | 9,4 † | 50,0 † | 0,8 | 45,7 † | ⚠️⚠️ 4–16k kimenet |
| 34 | 2026-07 | kimi-k2.6 | think | 75,2 | 92,7 | 9,4 † | 50,0 † | 0,0 | 45,5 † | ⚠️⚠️ 4–16k kimenet |
| 35 | 2026-07 | minimax-m3 | nothink | 75,8 | 91,3 | 9,4 † | 50,0 † | 0,1 | 45,3 † | ⚠️⚠️ 4–16k kimenet |
| 36 | 2026-07 | deepseek-v4-flash | think | 76,7 | 86,6 | 9,5 † | 50,0 † | 0,3 | 44,6 † | ⚠️⚠️ 4–16k kimenet |
| 37 | 2026-07 | gpt-oss-120b | think | 71,6 | 87,0 | 8,7 † | 50,0 † | 3,4 | 44,1 † | ⚠️⚠️ 4–16k kimenet |
| 38 | 2026-07 | gpt-oss-120b | nothink | 71,8 | 85,7 | 8,7 † | 50,0 † | 0,0 | 43,2 †* | ⚠️⚠️ 4–16k kimenet |
| 39 | 2026-07 | gpt-oss-20b | think | 71,5 | 46,5 | 8,2 † | 50,0 † | 1,0 | 35,4 †* | ⚠️⚠️ 4–16k kimenet |
| 40 | 2026-07 | gpt-oss-20b | nothink | 67,0 | 46,1 | 8,5 † | 50,0 † | 0,0 | 34,3 †* | ⚠️⚠️ 4–16k kimenet |
| — | 2026-07 | qwen3-next-80b | nothink | 61,5 | RETIRED | — | — | — | — | ⚠️⚠️ 4–16k kimenet |
| — | 2026-07 | qwen3-next-80b | think | 63,2 | RETIRED | — | — | — | — | ⚠️⚠️ 4–16k kimenet |

**Összesen 40 értékelt futtatás** (2026-07: 21, 2026-10: 10, 2026-11: 9 — a lokális `unsloth Qwen3.5-9B` a 2026-10 körben, a `Qwen3-Next-80B` a 2026-07 körben szerepel) + 2 RETIRED sor.

> † **A 2026-07-es sorok nem összemérhetők.** Két ok: (1) **HuGME-skála:** 2026-07-ben a bíró 0–10%-os skálán adott pontszámot (8,2–9,8%), 2026-11-ben 0–1 skálán (0,87–0,94); (2) **token-plafon + sampling:** `temperature: 0.0` és 4096–16384 tokenes limitek — a think modellek UD-je (0,0–7,5%) **érvénytelen**.
>
> A 2026-07-es MT-Bench minden modellnél **50,0%** (W0/L0/T4) — a 3 baseline-os átlagolás miatt nem differenciál.
>
> **glm-5.3** nem szerepel: ilyen modell nem volt mérve (a projektben `glm-5.1` és `glm-5.2` van).
>
> **A 2026-10-es sorok** 32k plafonnal, sampling nélkül készültek (a UD-parse akkor még a régi parserrel futott); a **2026-11-esek** nincs plafonnal.

## 1. Nincs-plafon kör (2026-11) — a jelenlegi mezőny

`composite = 0,40 × STAT + 0,40 × GEN + 0,20 × LING`, ahol STAT = (HuLU + MMLU)/2, GEN = (HuGME + MT-Bench)/2, LING = UD composite.

### Táblázat A — 40/40/20 súlyozott (kötelező)

| # | Modell (mód) | STAT | GEN | LING | **Composite** |
|---|---|---|---|---|---|
| 1 | **deepseek-v4.1-flash (think)** | 0,844 | **0,729** | **0,804** | **0,7901** |
| 2 | **muse-spark-open (think)** | **0,852** | 0,728 | 0,788 | **0,7896** |
| 3 | muse-spark-open (nothink) | 0,843 | 0,703 | 0,785 | 0,7751 |
| 4 | beam (think) | 0,834 | 0,715 | 0,772 | 0,7737 |
| 5 | mistral-large-4 (think) | 0,843 | 0,720 | 0,740 | 0,7732 |
| 6 | minimax-m3.1-flash (think) | 0,807 | 0,686 | 0,614 | 0,7200 |
| 7 | deepseek-v4.1-flash (nothink) | 0,782 | 0,700 | 0,598 | 0,7123 |
| 8 | minimax-m3.1-flash (nothink) | 0,799 | 0,679 | 0,569 | 0,7051 |
| 9 | mistral-large-4 (nothink) | 0,791 | 0,666 | 0,586 | 0,7000 |
| 10 | unsloth Qwen3.5-9B (nothink, lokális) | 0,679 | 0,558 | 0,199 | 0,5345 |

**Nincs hiányzó cella, nincs súly-újraosztás.**

### Táblázat B — a 4 fő benchmark egyszerű átlaga (kiegészítő)

| Modell (mód) | Átlag |
|---|---|
| muse-spark-open (think) | **0,7901** |
| deepseek-v4.1-flash (think) | 0,7866 |
| mistral-large-4 (think) | 0,7816 |
| beam (think) | 0,7743 |
| muse-spark-open (nothink) | 0,7725 |
| minimax-m3.1-flash (think) | 0,7465 |
| deepseek-v4.1-flash (nothink) | 0,7410 |
| minimax-m3.1-flash (nothink) | 0,7391 |
| mistral-large-4 (nothink) | 0,7285 |
| unsloth Qwen3.5-9B (nothink) | 0,6184 |

### Dimenziónkénti győztesek (aktuális kör)

| Dimenzió | Győztes | Érték | Második |
|---|---|---|---|
| STAT (HuLU + MMLU) | muse-spark-open (think) | 0,852 | deepseek think 0,844 |
| GEN (HuGME + MT-Bench) | deepseek-v4.1-flash (think) | 0,729 | muse think 0,728 |
| LING (UD) | deepseek-v4.1-flash (think) | 0,804 | muse think 0,788 |

---

## 2. HuLU (6 NLU sub-task) — aktuális kör

*A HuLU magyar NLU-tesztek gyűjteménye 6 sub-taskkal: HuCoLA (nyelvtani elfogadhatóság), HuCoPA (kauzális következtetés), HuRTE (szöveges következtetés), HuSST (érzelem), HuWNLI (természetes nyelvi következtetés), HuCB (commonsense) — 2–4 válaszos magyar feladatok. Metrika: helyes válaszok aránya sub-tasconként, illetve összesítve (macro = sub-task átlag, micro = item-súlyozott).*

| Modell (mód) | HuCOLA | HuCoPA | HuRTE | HuSST | HuWNLI | HuCB | Macro | **Micro** |
|---|---|---|---|---|---|---|---|---|
| muse-spark-open (think) | 82,2 | **97,0** | 90,5 | 72,7 | 11,7 | 76,7 | 71,8 | **77,41** |
| muse-spark-open (nothink) | 81,9 | 98,0 | 93,4 | 70,9 | 10,0 | **84,5** | 73,1 | 77,06 |
| deepseek-v4.1-flash (think) | **85,4** | **100,0** | 89,7 | 67,9 | 16,7 | 82,5 | 73,7 | 76,75 |
| mistral-large-4 (think) | 83,3 | 97,0 | 92,6 | 68,5 | 13,3 | 78,6 | 72,2 | 76,21 |
| beam (think) | 80,5 | 94,0 | 91,8 | 68,9 | 8,3 | 79,6 | 70,5 | 75,17 |
| mistral-large-4 (nothink) | 77,8 | 93,0 | 83,1 | 72,8 | 26,7 | 68,0 | 70,2 | 75,05 |
| deepseek-v4.1-flash (nothink) | 73,5 | 92,0 | 83,1 | 72,5 | **45,0** | 76,7 | 73,8 | 74,16 |
| minimax-m3.1-flash (think) | 79,6 | 92,0 | **93,8** | 64,5 | **45,0** | 70,9 | **74,3** | 73,46 |
| minimax-m3.1-flash (nothink) | 76,8 | 92,0 | 92,6 | 64,2 | 41,7 | 72,8 | 73,3 | 72,22 |
| unsloth Qwen3.5-9B (nothink, lokális) | 74,5 | 82,0 | 68,7 | 67,2 | **60,0** | 64,1 | 69,4 | 70,21 |

---

## 3. MMLU-HU (38 tantárgy, 5-shot) — aktuális kör

*Az MMLU-HU a magyarra fordított MMLU: 38 tantárgy 4 válaszos kérdései tantárgyanként 5 few-shot példával. Metrika: helyes válaszok aránya; a composite a 38 tantárgy egyenlő súlyú átlaga, az overall a kérdésszámmal súlyozott átlag.*

| Modell (mód) | Overall | Kérdés |
|---|---|---|
| muse-spark-open (think) | **93,07%** | 750 (dedupolt) |
| mistral-large-4 (think) | 92,43% | 1500 |
| deepseek-v4.1-flash (think) | 92,13% | 1500 |
| beam (think) | 91,60% | 750 |
| muse-spark-open (nothink) | 91,40% | 1500 |
| minimax-m3.1-flash (think) | 87,86% | — |
| minimax-m3.1-flash (nothink) | 87,60% | — |
| mistral-large-4 (nothink) | 83,13% | 1500 |
| deepseek-v4.1-flash (nothink) | 82,33% | 1500 |
| unsloth Qwen3.5-9B (nothink) | 65,53% | 1500 |

---

## 4. HuGME (generatív, LLM-as-a-Judge — 6 metrika, 300 item) — aktuális kör

*A HuGME magyar generatív benchmark: 300 feladat (összefoglalás, kérdés-válasz, utasításkövetés) valós magyar szövegeken; a válaszokat egy LLM-bíró (`deepseek-v4-pro:0813-cloud`) értékeli 6 metrikán 0–1 skálán (toxicitás, torzítás, hűség, válasz-relevancia, összefoglalás, prompt-illeszkedés); az `overall` a 6 metrika itemenkénti átlaga.*

| Modell (mód) | HuGME | Megjegyzés |
|---|---|---|
| deepseek-v4.1-flash (think) | **0,9369** | legjobb |
| deepseek-v4.1-flash (nothink) | 0,9302 | |
| mistral-large-4 (think) | 0,9191 | |
| beam (think) | 0,9087 | faithfulness 0,606 — mezőny-legjobb |
| muse-spark-open (nothink) | 0,9054 | |
| muse-spark-open (think) | 0,9034 | |
| mistral-large-4 (nothink) | 0,8946 | |
| minimax-m3.1-flash (think) | 0,8729 | |
| minimax-m3.1-flash (nothink) | 0,8687 | |
| unsloth Qwen3.5-9B (nothink) | 0,7203 | faithfulness 0,260 |

---

## 5. MT-Bench-HU (többfordulós párbeszéd, GSB bíró) — aktuális kör

*Az MT-Bench-HU 24 magyar nyelvű, többfordulós párbeszédes feladat. A válaszokat a bíró két referenciamodell (`deepseek-v4-pro:cloud`, `kimi-k2.6:cloud`) válaszaival hasonlítja össze páronként, fordulónként (A/B/S = első/második/egál); a pontszám egál = 0,5 konvencióval számolt győzelmi arány.*

| Modell (mód) | Score | 32k-s érték (referencia) |
|---|---|---|
| muse-spark-open (think) | **0,5521** | 0,5729 |
| deepseek-v4.1-flash (think) | 0,5208 | 0,4167 |
| mistral-large-4 (think) | 0,5208 | 0,4896 |
| beam (think) | 0,5208 | 0,4896 |
| muse-spark-open (nothink) | 0,5000 | 0,5625 |
| minimax-m3.1-flash (think) | 0,5000 | 0,4167 |
| minimax-m3.1-flash (nothink) | 0,4896 | 0,3438 |
| deepseek-v4.1-flash (nothink) | 0,4688 | 0,4375 |
| mistral-large-4 (nothink) | 0,4375 | 0,4375 |
| unsloth Qwen3.5-9B (nothink) | 0,3958 | — |

---

## 6. UD Hungarian (morfológiai szintaxis, CoNLL-U) — aktuális kör

*Az UD Hungarian a Universal Dependencies magyar fa-bankja: a modellnek minden mondathoz teljes CoNLL-U elemzést kell adnia (UPOS szófaj, fej, deprel). Metrika: token-szintű UPOS, UAS (fej), LAS (fej + kapcsolat); a parse-hányad az értékelhető válaszok aránya.*

| Modell (mód) | UPOS | UAS | LAS | Composite | Parse | Üres |
|---|---|---|---|---|---|---|
| **deepseek-v4.1-flash (think)** | **91,68** | **82,10** | **67,43** | **80,40** | 99,8% | 1 |
| muse-spark-open (think) | 89,88 | 82,76 | 63,63 | 78,76 | 100% | 1 |
| muse-spark-open (nothink) | 89,71 | 82,54 | 63,37 | 78,54 | 100% | 2 |
| beam (think) | 87,97 | 80,58 | 62,93 | 77,16 | 98,4% | 7 |
| mistral-large-4 (think) | 85,65 | 76,01 | 60,27 | 73,98 | 100% | 0 |
| minimax-m3.1-flash (think) | 74,28 | 61,46 | 48,37 | 61,37 | 99,6% | 2 |
| deepseek-v4.1-flash (nothink) | 78,30 | 47,89 | 53,14 | 59,77 | 100% | 0 |
| mistral-large-4 (nothink) | 77,94 | 45,06 | 52,83 | 58,61 | 99,1% | 4 |
| minimax-m3.1-flash (nothink) | 72,16 | 55,20 | 43,41 | 56,92 | 99,8% | 1 |
| unsloth Qwen3.5-9B (nothink) | 32,56 | 15,75 | 11,43 | 19,91 | 83,1% | 77 |

**Három szám (kötelező bemutatás):** a táblában az **összes itemre** számolt UPOS szerepel; a **parse-olható** részhalmazon mért UPOS 0,2–1,0 pt-tal magasabb (pl. deepseek think: 92,16% a 448 parse-olható itemen); a **parse-hányad** az utolsó előtti oszlop.

---

## 7. Archív kör (2026-07-14) — per-benchmark eredmények

> ⚠️ **Nem összemérhető az aktuális körrel** (temperature 0,0; 4096–16384 tokenes limitek; más bíró-prompt). Az alábbi táblák a korabeli riportból származnak, és a **teljes** akkori mezőnyt tartalmazzák.

### 7.1 HuLU (micro, %)

| Modell | nothink | think |
|---|---|---|
| qwen3.5 | 75,0 | **78,1** |
| minimax-m3 | 75,8 | 77,1 |
| deepseek-v4-flash | 73,3 | 76,7 |
| glm-5.2 | 76,6 | 75,5 |
| deepseek-v4-pro | 74,6 | 75,9 |
| kimi-k2.6 | 75,9 | 75,2 |
| glm-5.1 | 71,6 | 75,8 |
| gpt-oss-120b | 71,8 | 71,6 |
| nemotron-3-ultra | 70,5 | 71,8 |
| gpt-oss-20b | 67,0 | 71,5 |
| qwen3-next-80b (cloud) | 61,5 | 63,2 |
| Qwen3-Next-80B IQ3_XXS (lokális) | — | 56,53 |

### 7.2 MMLU-HU (%)

| Modell | nothink | think |
|---|---|---|
| kimi-k2.6 | 73,7 | **92,7** |
| glm-5.1 | 84,5 | 92,7 |
| deepseek-v4-pro | 77,5 | 92,5 |
| qwen3.5 | 85,1 | 92,5 |
| minimax-m3 | 91,3 | 92,2 |
| nemotron-3-ultra | 82,7 | 91,7 |
| glm-5.2 | 84,9 | 91,4 |
| gpt-oss-120b | 85,7 | 87,0 |
| deepseek-v4-flash | 52,0 | 86,6 |
| gpt-oss-20b | 46,1 | 46,5 |
| qwen3-next-80b (cloud) | RETIRED | RETIRED |
| Qwen3-Next-80B IQ3_XXS (lokális) | — | 86,87 |

### 7.3 HuGME (0–10%-os skála — más bíró-prompt)

| Modell | nothink | think |
|---|---|---|
| deepseek-v4-pro | **9,8** | 9,5 |
| minimax-m3 | 9,4 | 9,6 |
| qwen3.5 | 9,5 | 9,2 |
| deepseek-v4-flash | 9,5 | 9,5 |
| kimi-k2.6 | 9,4 | 9,4 |
| glm-5.1 | 9,2 | 9,4 |
| glm-5.2 | 9,2 | 9,5 |
| nemotron-3-ultra | 8,5 | 8,8 |
| gpt-oss-120b | 8,7 | 8,7 |
| gpt-oss-20b | 8,5 | 8,2 |
| Qwen3-Next-80B IQ3_XXS (lokális) | — | 82,83 (0–100 skála) |

### 7.4 MT-Bench-HU (%)

Minden aktív cloud modell **50,0%** (W0/L0/T24) — a 3 baseline-os átlagolás miatt a benchmark nem differenciált. Kivétel a lokális Qwen3-Next-80B: **37,50%** (1W/7L/16T, egyedi baseline).

### 7.5 UD Hungarian (UPOS/UAS/LAS composite)

| Modell | nothink | think |
|---|---|---|
| deepseek-v4-flash | **69,9** (89,7/47,0/73,0) | 0,3 (0,4/0,2/0,2) |
| kimi-k2.6 | 61,8 (90,8/39,6/55,1) | 0,0 |
| deepseek-v4-pro | 59,6 (90,0/37,0/51,8) | 1,7 (3,1/0,9/1,0) |
| nemotron-3-ultra | 42,5 (76,1/22,0/29,5) | 7,5 (8,8/7,5/6,2) |
| glm-5.2 | 40,9 (88,1/14,9/19,9) | 2,8 (3,6/2,7/2,2) |
| glm-5.1 | 38,8 (86,5/11,7/18,1) | 0,8 (0,7/0,9/0,9) |
| qwen3.5 | 37,6 (82,0/15,7/15,2) | 0,0 |
| gpt-oss-120b | 0,0 | 3,4 (4,7/2,9/2,7) |
| gpt-oss-20b | 0,0 | 1,0 (1,0/1,1/0,9) |
| minimax-m3 | 0,1 (0,4/0,0/0,0) | 0,5 (1,3/0,2/0,1) |
| Qwen3-Next-80B IQ3_XXS (lokális) | — | 64,73 (79,36/63,14/51,70) |

**A think UD értékek (0,0–7,5%) érvénytelenek**: a modell CoT-t írt CoNLL-U helyett, és a 4096–16384 tokenes limit mellett a válasz lefutott. Ezt a 2026-11-es nincs-plafon kör orvosolta (deepseek think: 1,7% → 80,40%).

### 7.6 Megjegyzés a hiányzó modellekről
- **glm-5.3**: nem szerepel az archívumban — a projektben `glm-5.1` és `glm-5.2` volt mérve; a queue listán sem szerepel.
- **qwen3-next-80b (cloud)**: 2026-06-16-án RETIRED (HTTP 410), csak a HuLU-eredménye maradt meg.
- **deepseek-v4-flash / deepseek-v4-pro (cloud)**: bíró/baseline szerepben is használtuk, ezért a saját MT-Bench-soruk bíró-torzításra hajlamos.

---

## 8. Protokoll-történet és hatása

| Időszak | Sampling | Kimeneti plafon | Megjegyzés |
|---|---|---|---|
| 2026-06 – 2026-10-22 | `temperature: 0.0` (greedy) | 4096 / 8192 / 16384 / korlátlan | token-loopok a lokális modelleknél (UD 31%) |
| 2026-10-24 – 2026-11-04 | nincs sampling param | **32 768** | a loop megszűnt, de a hosszan gondolkodó modellek UD-je üres lett |
| **2026-11-04 –** | nincs sampling param | **cloud: nincs plafon / lokális: 32k** | deepseek UD 64,78 → **80,40**; muse MT-Bench rontott |

**Mért hatás (32k → nincs plafon):**

| Futás | Δ |
|---|---|
| deepseek think UD | **+18,0 UPOS / +15,8 UAS / +13,1 LAS** (91 → 1 üres) |
| deepseek think MT-Bench | +10,4 |
| minimax nothink MT-Bench | **+14,6** |
| minimax think MT-Bench | +8,3 |
| mistral think MT-Bench | +3,1 |
| beam MT-Bench | +3,1 |
| **muse think MT-Bench** | **−2,1** |
| **muse nothink MT-Bench** | **−6,3** |
| HuLU / MMLU / HuGME (beam A/B) | +0,08 / −0,13 / +0,0005 |

---

## 9. Figyelemre méltó eredmények

- **Holtverseny az élen:** deepseek-v4.1-flash think 0,7901 vs. muse-spark-open think 0,7896 — más profillal (deepseek: GEN+LING, muse: STAT).
- **A HuWNLI a nagy modellek Achilles-sarka:** beam 8,3%, muse 10,0–11,7%, mistral 13,3–26,7% — a **lokális 9B 60,0%**-a a mezőny legjobbja.
- **A faithfulness minden modellnél a leggyengébb HuGME-metrika** (0,26 lokális, 0,51–0,61 cloud); a beam 0,606-ja a legjobb.
- **A deepseek think UD 80,40%** a projekt valaha mért legjobb magyar UD-eredménye.
- **A deepseek think HuCoPA 100%** (100/100).
- **A gondolkodás hatása kicsi** (<1 pt composite), kivéve: HuCB (ront) és UD (segít, ha van elég token).

### Limitációk
- A HuGME-t **egyetlen bíró** értékelte (a deepseek-v4-pro maga is szerepel a mezőnyben).
- Az MT-Bench-HU **2 baseline-nal** fut (a harmadik, `deepseek-v4-flash:cloud`, 2026-09-25-én RETIRED).
- Az MMLU-HU **gépi fordítás**; a HuLU/HuGME NYTK-adathalmazok.
- Az archív (2026-07) mezőny **nem összemérhető** az aktuálissal (8. szekció).
- A HuLU/MMLU/HuGME futások egy része **32k plafonnal** készült (a hatás dokumentáltan kicsi, de nem nulla).

---

## 10. Következő lépések

1. Az **archív (2026-07) mezőny újramérése** az aktuális protokollal — ezzel a 0. táblázat minden sora összemérhetővé válna (11 modell, ~2–3 hét).
2. A lokális `unsloth/Qwen3.5-9B` **think** körének mérése (llama-server indítását igényli).
3. A harmadik MT-Bench baseline pótlása + az összes futás újrapontozása.
4. A HuLU/MMLU/HuGME no-cap újrafuttatása (modellenként ~4–5 óra).

---

## Függelék — adatok, archívumok, reprodukálhatóság

| Mi | Hol |
|---|---|
| Checkpointok | `state/<model>-<mode>/*.json` |
| Nyers eredmények | `results/<model>-<mode>/*_results.jsonl` |
| Bíró-kimenetek | `results/<model>-<mode>/*_judged.jsonl` |
| Aggregált composite | `reports/composite_scores.csv` |
| Bontások | `reports/hulu_breakdown.*`, `mmlu_hu_breakdown.*`, `ud_hungarian_breakdown.*` |
| Logok | `logs/run{14,15,16,17}/driver.log` |
| Archívumok | `*.temp0.*` (greedy korszak), `*.truncated.*` (2026-10-22), `*.plafon32k.*` (32k korszak) |

```bash
cd ~/git/hu-eval && source .venv/bin/activate
BENCH_STREAM=1 python scripts/run_hulu.py        --model <model> --mode <mode>
BENCH_STREAM=1 python scripts/run_mmlu_hu.py     --model <model> --mode <mode>
BENCH_STREAM=1 python scripts/run_hugme.py       --model <model> --mode <mode>
BENCH_STREAM=1 python scripts/run_mt_bench_hu.py --model <model> --mode <mode>
BENCH_STREAM=1 python scripts/run_ud_hungarian.py --model <model> --mode <mode>
python scripts/judge_hugme.py --model <model> --mode <mode>
python scripts/rejudge_mt_bench.py <model_safe> --mode <mode> \
  --baselines deepseek-v4-pro:cloud kimi-k2.6:cloud
python scripts/aggregate_results.py
```

---

## Változtatási napló

| Dátum | Változás |
|---|---|
| 2026-11-10 | Első kiadás: minden futtatás egy táblázatban (32 sor), az archív kör per-benchmark bontással. |
| 2026-11-10 | A 2026-11-es kör riportja tematikusan átnevezve: `report-nincs-plafon-kor.md`. |

---

## Kapcsolódó

- [Nincs-plafon kör (2026-11)](report-nincs-plafon-kor.md) · [beam (2026-10-27)](report-2026-10-27-beam.md) · [muse think (2026-10-27)](report-2026-10-27.md) · [lokális 9B (2026-10-24)](report-2026-10-24.md) · [2026-10-22](report-2026-10-22.md) · [2026-07-14 archív](report-2026-07-14.md) · [2026-07-27 lokális](report-2026-07-27-lokalis-qwen3-next.md)
- [HuLU](../concepts/hulu-benchmark.md) · [MMLU-HU](../concepts/mmlu-hu-benchmark.md) · [HuGME](../concepts/hugme-benchmark.md) · [MT-Bench-HU](../concepts/mt-bench-hu.md) · [UD Hungarian](../concepts/ud-hungarian.md)
- [Modell vs. modell](../comparisons/modell-vs-modell.md) · [Cloud vs. lokális](../comparisons/cloud-vs-lokal.md)
- [Checkpoint és progress](../concepts/checkpoint-progress.md) · [Riport-sablon](riport-template.md)
