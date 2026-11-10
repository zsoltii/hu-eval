# Összesítő riport — 2026-11-10. (a teljes magyar LLM-mezőny: 2026-11-es nincs-plafon kör + a 2026-07-es archív mezőny)

*Típus:* report
*Forrás(ok):* `results/*/*_summary.json`, `reports/composite_scores.csv`, `reports/hulu_breakdown.md`, `reports/mmlu_hu_breakdown.md`, `reports/ud_hungarian_breakdown.md`, `logs/run{14,15,16,17}/driver.log`, korábbi riportok: [2026-07-14](report-2026-07-14.md), [2026-07-27](report-2026-07-27-lokalis-qwen3-next.md), [2026-10-22](report-2026-10-22.md), [2026-10-24](report-2026-10-24.md), [2026-10-27](report-2026-10-27.md), [2026-10-27 beam](report-2026-10-27-beam.md), [2026-11-09](report-2026-11-09-nocap.md)
*Létrehozva:* 2026-11-10
*Frissítve:* 2026-11-10

---

## Fejléc

| Mező | Érték |
|---|---|
| Riport azonosító | `hu-eval-20261110-osszesito` |
| Riport dátum | 2026-11-10 |
| Riport státusz | **Kanonikus összesítő** — a 2026-11-es mezőny teljes (minden futás × 5 benchmark), a 2026-07-es mezőny archívként, protokoll-figyelmeztetéssel szerepel |
| Értékelt modellek (aktuális kör) | `deepseek-v4.1-flash:cloud`, `muse-spark-open:cloud`, `beam:cloud`, `mistral-large-4:cloud`, `minimax-m3.1-flash:cloud` (think + nothink ahol értelmezhető) + `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL` (lokális) |
| Értékelt modellek (archív, 2026-07) | `qwen3.5:cloud`, `qwen3-next:80b-cloud`, `gpt-oss:120b-cloud`, `gpt-oss:20b-cloud`, `kimi-k2.6:cloud`, `glm-5.1:cloud`, `glm-5.2:cloud`, `nemotron-3-ultra:cloud`, `deepseek-v4-flash:cloud`, `deepseek-v4-pro:cloud`, `minimax-m3:cloud` + `Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` (lokális) |
| Bíró modell | `deepseek-v4-pro:0813-cloud` (HuGME + MT-Bench-HU) |
| Backend | cloud: `ollama` (`/api/generate`, streaming a hosszú hívásokon); lokális: `openai` (llama-server `:8080/v1`) |
| Módszertan | **Ollama Cloud: nincs kimeneti plafon**; **lokális: 32 768 token**; sampling paraméter nélkül; explicit `think` flag; UD-n degeneráció-detektor + max. 2 újrapróbálkozás |

### Modell-kvantálás

| Modell | Kvantálás | Megjegyzés |
|---|---|---|
| `deepseek-v4.1-flash:cloud` | `ollama-cloud` | lokális kvantálás nem ismert |
| `muse-spark-open:cloud` | `ollama-cloud` | — |
| `beam:cloud` | `ollama-cloud` | 501B, 1M kontextus, **think-only** (a nothink flag nem működik) |
| `mistral-large-4:cloud` | `ollama-cloud` | — |
| `minimax-m3.1-flash:cloud` | `ollama-cloud` | a nothink itt **működik** (szemben a beam-mel) |
| `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL` | **`UD-Q4_K_XL`** | Unsloth Dynamic 2.0 GGUF, ~4 bit, MTP; llama-server `-c 32000 --parallel 1` |
| archív (2026-07) modellek | `ollama-cloud` | kivéve Qwen3-Next-80B lokális: **`IQ3_XXS`** |

---

## Executive Summary

- **Az élen holtverseny:** `deepseek-v4.1-flash (think)` **0,7901** és `muse-spark-open (think)` **0,7896** — 0,0005 különbség, a mérési zajon belül.
- A **deepseek** nyeri a generatív (0,729) és a nyelvészeti (0,804) dimenziót; a **muse** a statisztikait (0,852). A két modell más-más profillal azonos szinten teljesít.
- A **beam** (4., 0,7737) és a **mistral think** (5., 0,7732) a dobogótól 0,2 pt-on belül van.
- **A legnagyobb módszertani lelet:** a kimeneti plafon elhagyása (2026-11-04) **modellfüggő** — a deepseek UD-je +15,6 composite-ot javult (91 → 1 üres válasz), a muse MT-Bench-je viszont rontott (−2,1/−6,3 pt). A rövid válaszos benchmarkokon (HuLU, MMLU, HuGME) a hatás ≤0,13 pt.
- A **lokális 9B** (0,5345) a UD-n (19,91%) és az MMLU-n (65,53%) szakad le; a HuWNLI-n viszont **ő a legjobb** (60,0%) — a nagy modellek ezt a 2 osztályos NLI-formátumot rontják el (8,3–16,7%).

---

## 1. Kompozit score-ok — aktuális mezőny (2026-11)

`composite = 0,40 × STAT + 0,40 × GEN + 0,20 × LING`, ahol STAT = (HuLU + MMLU)/2, GEN = (HuGME + MT-Bench)/2, LING = UD composite (UPOS/UAS/LAS átlaga).

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

**Nincs hiányzó cella, nincs súly-újraosztás** — minden futás mind az 5 benchmarkkal rendelkezik.

### Táblázat B — a 4 fő benchmark egyszerű átlaga (kiegészítő nézet)

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

### Dimenziónkénti győztesek

| Dimenzió | Győztes | Érték | Második |
|---|---|---|---|
| STAT (HuLU + MMLU) | muse-spark-open (think) | 0,852 | deepseek think 0,844 |
| GEN (HuGME + MT-Bench) | deepseek-v4.1-flash (think) | 0,729 | muse think 0,728 |
| LING (UD) | deepseek-v4.1-flash (think) | 0,804 | muse think 0,788 |

---

## 2. HuLU (6 NLU sub-task) — kötelező bontás

*A HuLU magyar NLU-tesztek gyűjteménye 6 sub-taskkal: HuCoLA (nyelvtani elfogadhatóság), HuCoPA (kauzális következtetés), HuRTE (szöveges következtetés), HuSST (érzelem), HuWNLI (természetes nyelvi következtetés), HuCB (commonsense) — 2–4 válaszos, magyar nyelvű feladatok. Metrika: helyes válaszok aránya sub-tasconként, illetve összesítve (macro = sub-task átlag, micro = item-súlyozott).*

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

## 3. MMLU-HU (38 tantárgy, 5-shot)

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

## 4. HuGME (generatív, LLM-as-a-Judge — 6 metrika, 300 item)

*A HuGME magyar generatív benchmark: 300 feladat (összefoglalás, kérdés-válasz, utasításkövetés) valós magyar szövegeken; a válaszokat egy LLM-bíró (`deepseek-v4-pro:0813-cloud`) értékeli 6 metrikán 0–1 skálán (toxicitás, torzítás, hűség, válasz-relevancia, összefoglalás, prompt-illeszkedés), az `overall` a 6 metrika itemenkénti átlaga.*

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

## 5. MT-Bench-HU (többfordulós párbeszéd, GSB bíró) — nincs plafon

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

## 6. UD Hungarian (morfológiai szintaxis, CoNLL-U)

*Az UD Hungarian a Universal Dependencies magyar fa-bankja: a modellnek minden mondathoz teljes CoNLL-U elemzést kell adnia (UPOS szófaj, fej, deprel kapcsolat). Metrika: token-szintű UPOS, UAS (fej-hozzárendelés), LAS (fej + kapcsolat); a parse-hányad az értékelhető válaszok aránya.*

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

**Három szám (kötelező bemutatás):** a táblában az **összes itemre** számolt UPOS szerepel; a **parse-olható** részhalmazon mért UPOS 0,2–1,0 pt-tal magasabb (pl. deepseek think: 92,16% a 448 parse-olható itemen, 73,69%-os 32k-s értékkel szemben); a **parse-hányad** az utolsó előtti oszlop.

---

## 7. Archív mezőny (2026-07-14) — **NEM összemérhető**

> ⚠️ **Figyelmeztetés:** ezek a futások **`temperature: 0.0`** (greedy) dekódolással és **4096–16384 tokenes** kimeneti limitekkel készültek. A think modellek UD-eredménye (0–7,5%) a limit miatt **érvénytelen**, és a HuGME/MT-Bench értékek is más bíró-prompttal készültek. Az adatok itt csak történeti referenciaként szerepelnek.

| Modell | Mód | STAT | GEN | LING | Composite |
|---|---|---|---|---|---|
| Qwen3-Next-80B IQ3_XXS (lokális) | think | 71,7% | 60,2% | 64,7% | **64,85%** |
| deepseek-v4-pro-cloud | nothink | 76,1% | 29,9% | 59,6% | 54,3% |
| kimi-k2.6-cloud | nothink | 74,8% | 29,7% | 61,8% | 54,2% |
| glm-5.2-cloud | nothink | 80,1% | 29,6% | 40,9% | 52,1% |
| qwen3.5-cloud | nothink | 80,1% | 29,8% | 37,6% | 51,5% |
| deepseek-v4-flash-cloud | nothink | 62,7% | 29,8% | 69,9% | 51,0% |
| nemotron-3-ultra-cloud | nothink | 76,6% | 29,3% | 42,5% | 50,9% |
| glm-5.1-cloud | nothink | 78,0% | 29,6% | 38,8% | 50,8% |
| qwen3.5-cloud | think | 85,3% | 29,6% | 0,0% | 46,0% |
| nemotron-3-ultra-cloud | think | 81,8% | 29,4% | 7,5% | 46,0% |
| glm-5.2-cloud | think | 83,7% | 29,8% | 2,8% | 45,9% |
| deepseek-v4-pro-cloud | think | 84,2% | 29,7% | 1,7% | 45,9% |
| minimax-m3-cloud | think | 84,7% | 29,8% | 0,5% | 45,9% |
| glm-5.1-cloud | think | 84,2% | 29,7% | 0,8% | 45,7% |
| kimi-k2.6-cloud | think | 84,0% | 29,7% | 0,0% | 45,5% |
| minimax-m3-cloud | nothink | 83,6% | 29,7% | 0,1% | 45,3% |
| deepseek-v4-flash-cloud | think | 81,7% | 29,8% | 0,3% | 44,6% |
| gpt-oss-120b-cloud | think | 79,3% | 29,4% | 3,4% | 44,1% |

**Miért alacsonyak ezek a GEN-értékek (~30%)?** A 2026-07-es HuGME/MT-Bench bíró más prompt-verziót és más skálát használt, ezért a számok **nem vethetők össze** a 2026-11-es értékekkel (ott a GEN 0,66–0,73). A táblázat csak a korabeli relatív sorrendet mutatja.

---

## 8. Protokoll-történet és hatása

| Időszak | Sampling | Kimeneti plafon | Megjegyzés |
|---|---|---|---|
| 2026-06 – 2026-10-22 | `temperature: 0.0` (greedy) | 4096 / 8192 / 16384 / korlátlan | a lokális modelleknél **token-loopok** (UD 31%) |
| 2026-10-24 – 2026-11-04 | **nincs sampling param** | **32 768** | a loop megszűnt, de a hosszú gondolkodású cloud modellek UD-je **üres** lett (deepseek 20,3%) |
| **2026-11-04 –** | **nincs sampling param** | **cloud: nincs plafon** / lokális: 32k | a deepseek UD 64,78 → **80,40**; a muse MT-Bench rontott |

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

- **A HuWNLI a nagy modellek Achilles-sarka:** beam 8,3%, muse 10,0–11,7%, mistral 13,3–26,7%, deepseek 16,7–45,0% — miközben a **lokális 9B 60,0%**. A 2 osztályos NLI-formátum ütközik a hosszú, gondolkodó válaszadással.
- **A faithfulness minden modellnél a leggyengébb HuGME-metrika** (0,26 lokális, 0,51–0,61 cloud) — a beam 0,606-ja a mezőny legjobbja.
- **A deepseek think UD 80,40%** a valaha mért legjobb magyar UD-eredmény a projektben.
- **A HuCoPA-n a deepseek think 100%-ot** ért el (100/100).
- **A think vs. nothink különbség kicsi** (<1 pt composite a legtöbb modellnél), kivéve a HuCB-t (a gondolkodás ront) és az UD-t (a gondolkodás segít, ha van elég token).

### Limitációk
- A HuGME-t **egyetlen bíró** értékelte; a bíró modellje (deepseek-v4-pro) maga is szerepel a mezőnyben.
- Az MT-Bench-HU **2 baseline-nal** fut (a harmadik, `deepseek-v4-flash:cloud`, 2026-09-25-én RETIRED).
- Az MMLU-HU **gépi fordítás**; a HuLU/HuGME forrásai NYTK-adathalmazok.
- A HuLU/MMLU/HuGME futások egy része **32k plafonnal** készült (a hatás dokumentáltan kicsi, de nem nulla).
- Az archív 2026-07-es mezőny **nem összemérhető** az aktuálissal.

---

## 10. Következő lépések

1. A lokális `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL` **think** körének mérése (llama-server indítását igényli).
2. A harmadik MT-Bench baseline pótlása egy aktív cloud modellel + az összes futás újrapontozása.
3. A HuLU/MMLU/HuGME no-cap újrafuttatása, ha teljesen egységes protokollt akarunk (modellenként ~4–5 óra).
4. Az archív 2026-07-es mezőny újramérése az aktuális protokollal (11 modell, ~2–3 hét).

---

## Függelék — adatok, archívumok, reprodukálhatóság

| Mi | Hol |
|---|---|
| Checkpointok | `state/<model>-<mode>/*.json` |
| Nyers eredmények | `results/<model>-<mode>/*_results.jsonl` |
| Bíró-kimenetek | `results/<model>-<mode>/*_judged.jsonl` |
| Aggregált composite | `reports/composite_scores.csv` |
| Bontások | `reports/hulu_breakdown.{md,csv,png}`, `mmlu_hu_breakdown.*`, `ud_hungarian_breakdown.*` |
| Logok | `logs/run{14,15,16,17}/driver.log` |
| Archívumok | `*.temp0.*` (greedy korszak), `*.truncated.*` (2026-10-22, érvénytelen think UD), `*.plafon32k.*` (32k korszak) |

```bash
cd ~/git/hu-eval && source .venv/bin/activate
# cloud benchmark (nincs plafon, streaming kötelező hosszú hívásokhoz)
BENCH_STREAM=1 python scripts/run_hulu.py        --model <model> --mode <mode>
BENCH_STREAM=1 python scripts/run_mmlu_hu.py     --model <model> --mode <mode>
BENCH_STREAM=1 python scripts/run_hugme.py       --model <model> --mode <mode>
BENCH_STREAM=1 python scripts/run_mt_bench_hu.py --model <model> --mode <mode>
BENCH_STREAM=1 python scripts/run_ud_hungarian.py --model <model> --mode <mode>
# bírók
python scripts/judge_hugme.py --model <model> --mode <mode>
python scripts/rejudge_mt_bench.py <model_safe> --mode <mode> \
  --baselines deepseek-v4-pro:cloud kimi-k2.6:cloud
# lokális (32k)
python scripts/run_hulu.py --model unsloth/... --mode nothink \
  --backend openai --base-url http://localhost:8080/v1
# aggregáció
python scripts/aggregate_results.py
```

---

## Változtatási napló

| Dátum | Változás |
|---|---|
| 2026-11-10 | Első kiadás: a teljes mezőny (aktuális no-cap kör + archív 2026-07) egy dokumentumban, protokoll-történettel és hatásméréssel. |

---

## Kapcsolódó

- [Nincs-plafon mezőny (2026-11-09)](report-2026-11-09-nocap.md) · [beam (2026-10-27)](report-2026-10-27-beam.md) · [muse think (2026-10-27)](report-2026-10-27.md) · [lokális 9B (2026-10-24)](report-2026-10-24.md) · [2026-10-22](report-2026-10-22.md) · [2026-07-14 archív](report-2026-07-14.md)
- [HuLU](../concepts/hulu-benchmark.md) · [MMLU-HU](../concepts/mmlu-hu-benchmark.md) · [HuGME](../concepts/hugme-benchmark.md) · [MT-Bench-HU](../concepts/mt-bench-hu.md) · [UD Hungarian](../concepts/ud-hungarian.md)
- [Modell vs. modell](../comparisons/modell-vs-modell.md) · [Cloud vs. lokális](../comparisons/cloud-vs-lokal.md)
- [Checkpoint és progress](../concepts/checkpoint-progress.md) · [Riport-sablon](riport-template.md)
