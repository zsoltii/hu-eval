# Nincs-plafon kör — 2026-11. (5 benchmark × 10 futás)

*Típus:* report
*Forrás(ok):* belső projekt futtatás; `logs/run14/driver.log`, `logs/run15/driver.log`, `logs/run16/driver.log`, `results/*/*_summary.json`, `reports/composite_scores.csv`, `reports/hulu_breakdown.md`, `reports/mmlu_hu_breakdown.md`, `reports/ud_hungarian_breakdown.md`
*Létrehozva:* 2026-11-09
*Frissítve:* 2026-11-10 (tematikus átnevezés: `report-nincs-plafon-kor.md`)

---

## Fejléc

| Mező | Érték |
|---|---|
| Riport azonosító | `hu-eval-20261109-nocap` |
| Riport dátum | 2026-11-09 |
| Értékelt modellek | 9 cloud futás + 1 lokális (lásd lentebb) |
| Operator | fater.zsolt |
| Riport státusz | **Teljes** — minden futás mind az 5 benchmarkkal rendelkezik (kivéve minimax nothink UD, ami sosem futott) |
| Bíró modell | `deepseek-v4-pro:0813-cloud` (HuGME + MT-Bench-HU) |
| Backend | `ollama` (cloud, `/api/generate`, streaming a hosszú hívásokon); lokális: `openai` (llama-server) |
| Módszertan | **Ollama Cloud: nincs kimeneti plafon** (2026-11-04-i szabály); **lokális: 32 768**; sampling paraméter nélkül; explicit `think` flag |

### Modell-kvantálás

| Modell | Kvantálás | Megjegyzés |
|---|---|---|
| `deepseek-v4.1-flash:cloud` | `ollama-cloud` | lokális kvantálás nem ismert |
| `muse-spark-open:cloud` | `ollama-cloud` | — |
| `beam:cloud` | `ollama-cloud` | 501B, 1M kontextus, **think-only** (nothink flag nem működik) |
| `mistral-large-4:cloud` | `ollama-cloud` | — |
| `minimax-m3.1-flash:cloud` | `ollama-cloud` | UD-je 2026-10-22-ig nem volt mérhető |
| `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL` | **`UD-Q4_K_XL`** | lokális, llama-server `-c 32000 --parallel 1` |

---

## 1. A plafon-szabály és annak mérhető hatása

2026-11-04-től a cloud modellek **kimeneti plafon nélkül** futnak (a `num_predict` mező kimarad a kérésből), a lokális modell továbbra is **32k**-n. Ok: a hosszan gondolkodó modellek (deepseek think) 32k-nál elhasaltak — az UD itemek 20%-a üres válasz lett.

**A hatás modellenként és benchmarkonként eltér** (32k → nincs plafon):

| Futás | 32k | nincs plafon | Δ |
|---|---|---|---|
| **deepseek think UD** | 73,69 / 66,35 / 54,30 (91 üres) | **91,68 / 82,10 / 67,43** (1 üres) | **+18,0 / +15,8 / +13,1** |
| deepseek think MT-Bench | 0,4167 | **0,5208** | **+10,4** |
| deepseek nothink MT-Bench | 0,4375 | 0,4688 | +3,1 |
| mistral think MT-Bench | 0,4896 | 0,5208 | +3,1 |
| minimax think MT-Bench | 0,4167 | 0,5000 | +8,3 |
| minimax nothink MT-Bench | 0,3438 | 0,4896 | **+14,6** |
| **muse think MT-Bench** | 0,5729 | **0,5521** | **−2,1** |
| **muse nothink MT-Bench** | 0,5625 | **0,5000** | **−6,3** |
| beam UD | 87,40 / 80,36 / 62,46 | 87,97 / 80,58 / 62,93 | +0,6 / +0,2 / +0,5 |
| beam MT-Bench | 0,4896 | 0,5208 | +3,1 |

**Következtetés:** a plafon elhagyása **nem egyirányú** — a deepseek/minimax/mistral javult, a muse **rontott**. A rövid válaszos benchmarkokon (HuLU, MMLU, HuGME) a hatás elhanyagolható: a beam teljes A/B-je **+0,08 / −0,13 / +0,0005 pt**-ot adott. Ezért a HuLU/MMLU/HuGME futásokat **nem futtattuk újra** — ezt a beam A/B mérés dokumentálja.

---

## Executive Summary

- **Holtverseny az élen:** `deepseek-v4.1-flash (think)` **0,7901** és `muse-spark-open (think)` **0,7896** — a különbség 0,0005, a mérési zajon belül.
- A **deepseek** a generatív (MT-Bench/HuGME) és **nyelvészeti (UD 80,40%)** dimenziót nyeri; a **muse** a statisztikait (HuLU 77,41% / MMLU 93,07%).
- A **beam** a 4. helyen (0,7737), a **mistral think** az 5. (0,7732) — mindkettő +0,2 pt-on belül van a 3. helyezetthez.
- A **minimax** a no-cap MT-Bench-csel **+0,017 composite**-ot javult (0,7033 → 0,7200).
- A **lokális 9B** (0,5345) a UD-n (19,91%) és a MMLU-n (65,53%) szakad le leginkább.

---

## 2. HuLU (6 NLU sub-task)

*A HuLU magyar NLU-tesztek gyűjteménye 6 sub-taskkal (HuCoLA nyelvtani elfogadhatóság, HuCoPA kauzális következtetés, HuRTE szöveges következtetés, HuSST érzelem, HuWNLI természetes nyelvi következtetés, HuCB commonsense), 2–4 válaszos feleletválasztós formátumban, magyarul. Metrika: helyes válaszok aránya sub-tasconként, illetve összesítve (macro = sub-task átlag, micro = item-súlyozott).*

| Modell (mód) | HuCOLA | HuCoPA | HuRTE | HuSST | HuWNLI | HuCB | Macro | **Micro** |
|---|---|---|---|---|---|---|---|---|
| muse-spark-open (think) | 82,2 | **97,0** | 90,5 | 72,7 | 11,7 | 76,7 | 71,8 | **77,41** |
| muse-spark-open (nothink) | 81,9 | 98,0 | 93,4 | 70,9 | 10,0 | **84,5** | 73,1 | 77,06 |
| deepseek-v4.1-flash (think) | **85,4** | **100,0** | 89,7 | 67,9 | 16,7 | 82,5 | 73,7 | 76,75 |
| mistral-large-4 (think) | 83,3 | 97,0 | 92,6 | 68,5 | 13,3 | 78,6 | 72,2 | 76,21 |
| beam (think) | 80,5 | 94,0 | 91,8 | 68,9 | 8,3 | 79,6 | 70,5 | 75,17 |
| mistral-large-4 (nothink) | 77,8 | 93,0 | 83,1 | 72,8 | 26,7 | 68,0 | 70,2 | 75,05 |
| deepseek-v4.1-flash (nothink) | 73,5 | 92,0 | 83,1 | 72,5 | **45,0** | 76,7 | 73,8 | 74,16 |
| minimax-m3.1-flash (think) | 79,6 | 92,0 | 93,8 | 64,5 | **45,0** | 70,9 | **74,3** | 73,46 |
| minimax-m3.1-flash (nothink) | 76,8 | 92,0 | 92,6 | 64,2 | 41,7 | 72,8 | 73,3 | 72,22 |
| unsloth Qwen3.5-9B (nothink) | 74,5 | 82,0 | 68,7 | 67,2 | **60,0** | 64,1 | 69,4 | 70,21 |

---

## 3. MMLU-HU (38 tantárgy, 5-shot)

*Az MMLU-HU a magyarra fordított MMLU: 38 tantárgy 4 válaszos kérdései tantárgyanként 5 few-shot példával. Metrika: helyes válaszok aránya; a composite a 38 tantárgy egyenlő súlyú átlaga, az overall a kérdésszámmal súlyozott átlag.*

| Modell (mód) | Overall | Kérdés |
|---|---|---|
| muse-spark-open (think) | **93,07%** | 750 |
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

*A HuGME magyar generatív benchmark: 300 feladat (összefoglalás, kérdés-válasz, utasításkövetés) valós magyar szövegeken; a válaszokat egy LLM-bíró (`deepseek-v4-pro:0813-cloud`) értékeli 6 metrikán 0–1 skálán, az `overall` a 6 metrika itemenkénti átlaga, majd itemátlag.*

| Modell (mód) | HuGME |
|---|---|
| deepseek-v4.1-flash (think) | **0,9369** |
| deepseek-v4.1-flash (nothink) | 0,9302 |
| mistral-large-4 (think) | 0,9191 |
| beam (think) | 0,9087 |
| muse-spark-open (nothink) | 0,9054 |
| muse-spark-open (think) | 0,9034 |
| mistral-large-4 (nothink) | 0,8946 |
| minimax-m3.1-flash (think) | 0,8729 |
| minimax-m3.1-flash (nothink) | 0,8687 |
| unsloth Qwen3.5-9B (nothink) | 0,7203 |

Megjegyzés: a **faithfulness** minden modellnél a leggyengébb metrika (0,51–0,61 a cloud mezőnyben, 0,26 a lokálisnál).

---

## 5. MT-Bench-HU (többfordulós párbeszéd, GSB bíró) — no-cap

*Az MT-Bench-HU 24 magyar nyelvű, többfordulós párbeszédes feladat. A válaszokat a bíró két referenciamodell (`deepseek-v4-pro:cloud`, `kimi-k2.6:cloud`) válaszaival hasonlítja össze páronként, fordulónként (A/B/S = első/második/egál); a pontszám egál = 0,5 konvencióval számolt győzelmi arány.*

| Modell (mód) | Score (no-cap) | 32k-s érték |
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

**Három szám (kötelező):** a táblában az összes itemre számolt UPOS szerepel; a parse-olható részhalmazon mért UPOS a legtöbb modellnél 0,2–1,0 pt-tal magasabb (pl. deepseek think: 92,16% a 448 parse-olható itemen). A parse-hányad az utolsó előtti oszlop.

**A deepseek UD rekord:** a 32k-s futásban 91 üres válasz volt (20,3%), a nincs-plafon futásban **1** — a composite 64,78% → **80,40%**.

---

## 7. Kompozit score-ok

### Táblázat A — 40/40/20 súlyozott (kötelező)

STAT = (HuLU + MMLU-HU)/2 · GEN = (HuGME + MT-Bench)/2 · LING = UD composite.

| # | Modell (mód) | STAT | GEN | LING | **Composite** |
|---|---|---|---|---|---|
| 1 | **deepseek-v4.1-flash (think)** | 0,844 | **0,729** | **0,804** | **0,7901** |
| 2 | **muse-spark-open (think)** | **0,852** | 0,728 | 0,788 | **0,7896** |
| 3 | muse-spark-open (nothink) | 0,843 | 0,703 | 0,785 | 0,7751 |
| 4 | beam (think) | 0,834 | 0,715 | 0,772 | 0,7737 |
| 5 | mistral-large-4 (think) | 0,843 | 0,720 | 0,740 | 0,7732 |
| 6 | minimax-m3.1-flash (think) | 0,807 | 0,686 | 0,614 | 0,7200 |
| 7 | deepseek-v4.1-flash (nothink) | 0,782 | 0,700 | 0,598 | 0,7123 |
| 8 | mistral-large-4 (nothink) | 0,791 | 0,666 | 0,586 | 0,7000 |
| 9 | minimax-m3.1-flash (nothink) | 0,799 | 0,679 | 0,569 | 0,7051 |
| 10 | unsloth Qwen3.5-9B (nothink, lokális) | 0,679 | 0,558 | 0,199 | 0,5345 |

Nincs súly-újraosztásos sor: minden futás rendelkezik mind az 5 benchmarkkal.


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

### Dimenziónkénti győztesek

| Dimenzió | Győztes | Érték |
|---|---|---|
| STAT (HuLU + MMLU) | muse-spark-open (think) | 0,852 |
| GEN (HuGME + MT-Bench) | deepseek-v4.1-flash (think) | 0,729 |
| LING (UD) | deepseek-v4.1-flash (think) | 0,804 |

---

## 8. Módszertani megjegyzések

1. **Nincs plafon (cloud) / 32k (lokális)** — 2026-11-04-i szabály. A `num_predict` cloud esetén kimarad a kérésből; lokálisan 32 768.
2. **Mit futtattunk újra no-cap-pel:** a teljes UD kört (deepseek, mistral, minimax, beam) és a teljes MT-Bench kört (8 régi futás + beam). A HuLU/MMLU/HuGME 32k-s maradt — a beam A/B bizonyítja, hogy a hatás ≤0,13 pt.
3. **Streaming kötelező** — a cloud proxy a 60 s-nál hosszabb nem-streamelt kéréseket 502-vel utasítja el; a `BENCH_STREAM=1` NDJSON-összegzést használ, a hibás chunkot fatális hibaként dobja (nem csendes csonkolás).
4. **Archívumok:** `*.temp0.*` (2026-10-24 előtti, temperature 0), `*.truncated.*` (2026-10-22-i, plafon miatt érvénytelen think UD), `*.plafon32k.*` (2026-11-04 előtti 32k-s futások).
5. **MMLU duplikátum:** a dataset minden kérdést kétszer tartalmaz; ahol 750-es a minta, ott a runner dedupol (determinisztikus).

---

## 9. Figyelemre méltó eredmények

- **A deepseek think UD 80,40%-a** a mezőny legjobbja, és +15,6 pt-tal múlja felül a saját 32k-s eredményét — a plafon-hiba leglátványosabb korrekciója.
- **A muse HuWNLI 10–11,7%** — a mezőny legrosszabbja, miközben a lokális 9B 60,0%-ot ér el ugyanezen a sub-taskon.
- **A minimax nothink MT-Bench +14,6 pt-ot javult** a plafon elhagyásával (0,3438 → 0,4896) — a legnagyobb relatív javulás.
- **A muse MT-Bench rontott** a plafon elhagyásával (−2,1 / −6,3 pt) — a no-cap nem univerzális javítás.

### Limitációk
- A HuLU/MMLU/HuGME 32k-s futások (a beam kivételével) — a hatás dokumentáltan kicsi, de nem nulla.
- ~~A minimax nothink UD sosem futott le~~ — 2026-11-09-én no-cap protokollal lefutott (0,5692), így a tábla teljes.
- 2 baseline az MT-Bench-HU-n (a harmadik RETIRED).
- Egy bíró a HuGME-n.

---

## 10. Következő lépések

2. A lokális Qwen3.5-9B **think** körének mérése (llama-server kell).
3. A harmadik MT-Bench baseline pótlása.
4. A HuLU/MMLU/HuGME no-cap újrafuttatása, ha teljesen egységes protokollt akarunk (modellenként ~4–5 óra).

---

## Függelék — adatok és reprodukálhatóság

| Mi | Hol |
|---|---|
| Checkpointok | `state/<model>-<mode>/*.json` |
| Nyers eredmények | `results/<model>-<mode>/*_results.jsonl` |
| Bíró-kimenetek | `results/<model>-<mode>/*_judged.jsonl` |
| Logok | `logs/run{14,15,16}/driver.log` |
| Archívumok | `*.temp0.*`, `*.truncated.*`, `*.plafon32k.*` |

```bash
cd ~/git/hu-eval && source .venv/bin/activate
# MT-Bench (no-cap, cloud)
BENCH_STREAM=1 python scripts/run_mt_bench_hu.py --model <model> --mode <mode> --reset
python scripts/rejudge_mt_bench.py <model_safe> --mode <mode> \
  --baselines deepseek-v4-pro:cloud kimi-k2.6:cloud
# UD (no-cap, cloud)
BENCH_STREAM=1 python scripts/run_ud_hungarian.py --model <model> --mode <mode>
# lokális (32k)
python scripts/run_hulu.py --model unsloth/... --mode nothink --backend openai --base-url http://localhost:8080/v1
# aggregáció
python scripts/aggregate_results.py
```

---

## Változtatási napló

| Dátum | Változás |
|---|---|
| 2026-11-09 | Első verzió: no-cap mezőny (UD + MT-Bench újrafuttatva), deepseek think és muse think holtverseny az élen. |

---

## Kapcsolódó

- [Riport 2026-10-27 (beam, think-only)](report-2026-10-27-beam.md)
- [Riport 2026-10-27 (muse think)](report-2026-10-27.md)
- [Riport 2026-10-24 (lokális Qwen3.5-9B)](report-2026-10-24.md)
- [HuLU benchmark](../concepts/hulu-benchmark.md) · [MMLU-HU](../concepts/mmlu-hu-benchmark.md) · [HuGME](../concepts/hugme-benchmark.md) · [MT-Bench-HU](../concepts/mt-bench-hu.md) · [UD Hungarian](../concepts/ud-hungarian.md)
- [Checkpoint és progress](../concepts/checkpoint-progress.md)
- [Riport-sablon](riport-template.md)
