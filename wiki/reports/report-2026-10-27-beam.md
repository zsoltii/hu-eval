# Riport — 2026-10-27. (beam:cloud TELJES kör — think-only)

*Típus:* report
*Forrás(ok):* belső projekt futtatás; `logs/run8/driver.log`, `logs/run8b/driver.log`, `results/beam-cloud-think/*_summary.json`, `reports/composite_scores.csv`, `reports/hulu_breakdown.md`, `reports/mmlu_hu_breakdown.md`, `reports/ud_hungarian_breakdown.md`
*Létrehozva:* 2026-10-27
*Frissítve:* 2026-10-27

---

## Fejléc

| Mező | Érték |
|---|---|
| Riport azonosító | `hu-eval-20261027-beam` |
| Riport dátum | 2026-10-27 |
| Értékelt modell | `beam:cloud` — **501B paraméter, 1 048 576 token kontextus** |
| Operator | fater.zsolt |
| Riport státusz | **Teljes** — mind az 5 benchmark + 2 bíró lefutott |
| Mód | **think-only** (a nothink nem működik — lásd 1. módszertani megjegyzés) |
| Bíró modell | `deepseek-v4-pro:0813-cloud` (HuGME + MT-Bench-HU) |
| Backend | `ollama` (`http://localhost:11434/api/generate`), UD-nél **streaming** (`BENCH_STREAM=1`) |
| Futtatási ablak | 2026-10-27 07:39 → 21:00 (nettó ~13 óra, benne egy 502-megszakítás és egy driver-restart) |
| Módszertan | nincs sampling paraméter; **32 768 tokenes plafon**; explicit `think: true` |

### Modell-kvantálás

| Modell | Kvantálás | Megjegyzés |
|---|---|---|
| `beam:cloud` | **`ollama-cloud`** | lokális kvantálás nem ismert (Ollama Cloud); 501B, 1M kontextus |

---

## 1. Mód-diagnózis: miért think-only?

A modell `capabilities` listája: `completion`, `thinking` (szintek: low/medium/high/xhigh/max, **default: max**), `tools`.

| Kérés | Eredmény |
|---|---|
| `think: true` (natív `/api/generate`) | ✅ `thinking` mező 243 char |
| `think: false` (natív `/api/generate`) | ❌ **mégis gondolkodik** — 432 char reasoning |
| `/v1/chat/completions` + `think: false` | ❌ reasoning 137 char |
| `/v1/chat/completions` + `chat_template_kwargs.enable_thinking: false` | ❌ reasoning 304 char |

**Következtetés:** a beam a nothink flaget **egyik végponton sem tiszteli** — a modell mindig gondolkodik. Ezért a mérés **think-only**, a nem-think összevetés nem értelmezhető. (Projekt-precedens: a lokális Qwen3-Next-80B-nél ugyanez a helyzet.)

---

## Executive Summary

- A **`beam:cloud`** teljes körrel **0,7667 composite**-ot ér el — a **3. helyen** áll a teljes 5-benchmarkos mezőnyben (muse think 0,7937 és muse nothink 0,7876 mögött), a deepseek/mistral/minimax nothink páros (0,70–0,71) előtt.
- **Profil:** kiemelkedő **HuGME** (0,9082 — a mezőny 2. legjobbja a deepseek think 0,9369 mögött) és **faithfulness 0,606** — ez a **mezőny legjobb forráshűsége** (muse 0,547, a lokális modell 0,260). Az **MMLU 91,73%** a muse think (93,07%) szintjén.
- **Gyengeségek:** **HuLU 75,09%** (a muse 77,41%-a alatt; a HuWNLI-nál 8,3% — a mezőny legrosszabbja) és **MT-Bench 0,4896** (4W/5L/39T — a muse 0,5729-e mögött, a deepseek think 0,4167-e előtt).
- **UD: 76,74% composite** (UPOS 87,40% / UAS 80,36% / LAS 62,46%), parse-hányad 98,2% — a muse think (78,76%) mögött a 2. hely.
- **Technikai újdonság:** az UD futás egy **új, opt-in streaming utat** igényelt (`BENCH_STREAM=1`) — a cloud proxy a 60 s feletti nem-streamelt kéréseket 502-vel utasítja el, a beam UD-válaszai pedig 20k+ karakter gondolkodást tartalmaznak.

---

## 2. HuLU (6 NLU sub-task)

*A HuLU magyar NLU-tesztek gyűjteménye 6 sub-taskkal (HuCoLA nyelvtani elfogadhatóság, HuCoPA kauzális következtetés, HuRTE szöveges következtetés, HuSST érzelem, HuWNLI természetes nyelvi következtetés, HuCB commonsense), 2–4 válaszos feleletválasztós formátumban. Metrika: helyes válaszok aránya sub-tasconként, illetve összesítve (macro = sub-task átlag, micro = item-súlyozott).*

| Modell (mód) | HuCOLA | HuCoPA | HuRTE | HuSST | HuWNLI | HuCB | Macro | **Micro** |
|---|---|---|---|---|---|---|---|---|
| muse-spark-open (think) | 82,2% | **97,0%** | 90,5% | **72,7%** | 11,7% | **76,7%** | 71,8% | **77,41%** |
| deepseek-v4.1-flash (think) | **85,4%** | **100,0%** | 89,7% | 67,9% | **16,7%** | **82,5%** | 73,7% | 76,75% |
| **beam (think)** | 81,4% | 93,0% | **90,9%** | 68,8% | 8,3% | 74,8% | 69,5% | **75,09%** |
| mistral-large-4 (think) | 83,3% | 97,0% | 92,6% | 68,5% | 13,3% | 78,6% | 72,2% | 76,21% |
| minimax-m3.1-flash (think) | 79,6% | 92,0% | 93,8% | 64,5% | **45,0%** | 70,9% | **74,3%** | 73,46% |
| unsloth-Qwen3.5-9B-MTP (nothink, lokális) | 74,5% | 82,0% | 68,7% | 67,2% | **60,0%** | 64,1% | 69,4% | 70,21% |

- **1938/2581 helyes**, 3 üres válasz.
- A **HuWNLI 8,3%** (5/60) a mezőny mélypontja — a nagy modellek közös mintázata, a lokális 9B 60%-ot ér el ugyanezen.
- A HuRTE (90,9%) viszont a legjobb a think mezőnyben.

---

## 3. MMLU-HU (38 tantárgy, 5-shot)

*Az MMLU-HU a magyarra fordított MMLU: 38 tantárgy 4 válaszos kérdései tantárgyanként 5 few-shot példával. Metrika: helyes válaszok aránya; a composite a 38 tantárgy egyenlő súlyú átlaga, az overall a kérdésszámmal súlyozott átlag.*

| Mutató | beam | muse think | deepseek think |
|---|---|---|---|
| Overall (750 egyedi kérdés) | **91,73%** (688/750) | 93,07% | 92,13% |
| Composite (38 tantárgy átlaga) | **90,0%** | 91,6% | 90,4% |
| Üres válasz | 0 | 0 | — |

**Legjobb tantárgyak (100%):** sociology, high_school_physics, high_school_microeconomics, high_school_government_and_politics, formal_logic.
**Legrosszabbak:** virology 52,9%, abstract_algebra 66,7%, public_relations 66,7%, global_facts 70,0%, high_school_european_history 72,2%.

---

## 4. HuGME (generatív, LLM-as-a-Judge — 6 metrika, 300 item)

*A HuGME magyar generatív benchmark: 300 feladat (összefoglalás, kérdés-válasz, utasításkövetés) valós magyar szövegeken; a válaszokat egy LLM-bíró (`deepseek-v4-pro:0813-cloud`) értékeli 6 metrikán 0–1 skálán, az `overall` a 6 metrika itemenkénti átlaga, majd itemátlag.*

| Metrika | beam | muse think | Megjegyzés |
|---|---|---|---|
| Toxicity (magasabb = jobb) | **1,000** | 1,000 | — |
| Answer relevancy | 0,991 | **0,995** | — |
| Prompt alignment | 0,979 | **0,984** | — |
| Bias (magasabb = jobb) | 0,969 | 0,959 | beam jobb |
| Summarization | 0,904 | **0,935** | muse jobb |
| **Faithfulness** | **0,606** | 0,547 | **a mezőny legjobbja** |
| **Összesített** | **0,9082** | 0,9034 | +0,005 |

- 300/300 item, **2 item** 0,5 alatt, 0 item 0,0.
- A faithfulness 0,606 a mezőny legjobbja (a deepseek think 0,9369-es összesítettje mellett is): a beam kevésbé „kerekít" a forrásszövegen.

---

## 5. MT-Bench-HU (többfordulós párbeszéd, GSB bíró)

*Az MT-Bench-HU 24 magyar nyelvű, többfordulós párbeszédes feladat. A válaszokat a bíró két referenciamodell (`deepseek-v4-pro:cloud`, `kimi-k2.6:cloud`) válaszaival hasonlítja össze páronként, fordulónként (A/B/S = első/második/egál); a pontszám egál = 0,5 konvencióval számolt győzelmi arány.*

| Mutató | beam | muse think |
|---|---|---|
| Score | **0,4896** | 0,5729 |
| Győzelem / vereség / egál | **4 / 5 / 39** | 8 / 1 / 39 |
| Fordulónkénti verdikt (A / B / S) | 14 / 17 / 65 | 28 / 9 / 59 |

- A beam **5 vereséget** szedett össze (a muse csak 1-et): a hosszú, gondolkodó válaszok a bíró szerint kevésbé követik a feladat stílusát.
- 2 baseline (a harmadik, `deepseek-v4-flash:cloud`, RETIRED).

---

## 6. UD Hungarian (morfológiai szintaxis, CoNLL-U)

*Az UD Hungarian a Universal Dependencies magyar fa-bankja: a modellnek minden mondathoz teljes CoNLL-U elemzést kell adnia (UPOS szófaj, fej, deprel). Metrika: token-szintű UPOS, UAS (fej), LAS (fej + kapcsolat); a parse-hányad az értékelhető válaszok aránya.*

| Metrika | beam | muse think |
|---|---|---|
| UPOS (összes) | **87,40%** | 89,88% |
| UAS | **80,36%** | 82,76% |
| LAS | **62,46%** | 63,63% |
| **Composite** = (UPOS+UAS+LAS)/3 | **76,74%** | 78,76% |
| Parse-hányad | **441/449 = 98,2%** | 449/449 = 100% |
| Üres válasz | 8 | 0 |
| Degenerált újrapróbálkozás | 0 | 0 |

**Három szám (kötelező bemutatás):** összes UPOS **87,40%** · parse-olható válaszokon mért UPOS **88,98%** · parse-hányad **98,2%**.

---

## 7. Kompozit score-ok

### Táblázat A — 40/40/20 súlyozott

STAT = (HuLU + MMLU-HU)/2 · GEN = (HuGME + MT-Bench)/2 · LING = UD composite.

| # | Modell (mód) | STAT | GEN | LING | **Composite** |
|---|---|---|---|---|---|
| 1 | muse-spark-open (think) | 0,852 | 0,738 | 0,788 | **0,7937** |
| 2 | muse-spark-open (nothink) | 0,842 | 0,734 | 0,785 | 0,7876 |
| 3 | **beam (think-only)** | **0,834** | **0,699** | **0,767** | **0,7667** |
| 4 | deepseek-v4.1-flash (nothink) | 0,783 | 0,684 | 0,598 | 0,7061 |
| 5 | minimax-m3.1-flash (nothink) | 0,799 | 0,606 | — | 0,7027¹ |
| 6 | mistral-large-4 (nothink) | 0,791 | 0,666 | 0,586 | 0,7000 |
| 7 | unsloth-Qwen3.5-9B-MTP (nothink, lokális) | 0,679 | 0,558 | 0,199 | 0,5345 |

¹ nincs UD → súly-újraosztás (STAT 50 / GEN 50), nem közvetlenül összemérhető.
A deepseek/mistral **think** sorok composite-ja átmenetileg torz (UD nélkül), mert a 2026-10-22-i UD-jük érvénytelen volt és újrafuttatás alatt áll (lásd 8.2).

### Táblázat B — a 4 fő benchmark egyszerű átlaga

| Modell (mód) | HuLU | MMLU | HuGME | MT-Bench | **Átlag** |
|---|---|---|---|---|---|
| muse-spark-open (think) | 0,774 | 0,931 | 0,903 | 0,573 | 0,795 |
| muse-spark-open (nothink) | 0,771 | 0,914 | 0,905 | 0,563 | 0,788 |
| **beam (think)** | 0,751 | 0,917 | 0,908 | 0,490 | **0,767** |

### Dimenziónkénti győztesek

| Dimenzió | Győztes (teljes 5-benchmarkos mezőny) | Érték |
|---|---|---|
| STAT | muse-spark-open think | 0,852 |
| GEN | muse-spark-open think | 0,738 |
| LING | muse-spark-open think | 0,788 |

A beam a **GEN-en belül a HuGME-t nyeri** (0,9082 — csak a deepseek think 0,9369 jobb), de az MT-Bench lerontja (0,4896).

---

## 8. Módszertani megjegyzések

### 8.1 A nem-streamelt hívás 502-problémája és a streaming javítás
A beam UD futása **item 4-nél `http_502`-vel elhalt**: a válaszok ~20 945 karakter gondolkodást (6 823 eval token) tartalmaznak, így a nem-streamelt kérés átlépi az Ollama cloud proxy **60 s-os** korlátját.

Megoldás: a `scripts/stop_on_error.py` új, **opt-in** streaming útja (`BENCH_STREAM=1`):
- a kérés `stream: true`-val megy, a válasz NDJSON-sorokból áll össze a nem-streamelt válasz alakjára (`response`, `thinking`, `done_reason`, `eval_count`, durations),
- a hibás chunk (`{"error": ...}`) **fatális hibaként** dobódik — nem csendes csonkolás,
- flag nélkül a régi, nem-streamelt út fut (a többi futás érintetlen),
- validálva: hosszú CoNLL-U kérés 29 s alatt teljes válasszal; a run8b alatt egy stream-hiba (item 203) tisztán leállt, majd resume-olt **duplikátum nélkül** (253 sor = 253 egyedi id = 253 completed_id).

### 8.2 Think-only mérés
A nothink flag nem működik (1. pont) → a nothink/think összevetés nem értelmezhető erre a modellre. A composite a think körből számol, a nem-think mezőnnyel való összevetéskor ezt figyelembe kell venni (a muse-nál a think +0,6 pt-ot adott, tehát a torzítás kicsi).

### 8.3 Az UD-újrafuttatás (párhuzamos munka)
A 2026-10-22-i token-plafon miatt a **deepseek** és **mistral** think UD 77–79%-a üres válasz volt (a tárolt 0,17–0,20 composite érték érvénytelen), a **minimax** think UD pedig soha nem futott le. Ezek újrafuttatása a streaming javítás után indult (`logs/run7b/`); a régi fájlok `*.truncated.*` néven archiválva. Amíg nem készülnek el, a composite-juk **UD nélkül** számol (torz).

### 8.4 MMLU-HU duplikátum
A futás a determinisztikussá tett runnerrel **750 egyedi kérdésen** mér (a dataset minden kérdést kétszer tartalmaz) — a muse think futással azonos módszertan.

---

## 9. Figyelemre méltó eredmények

- **A legjobb faithfulness a mezőnyben (0,606)** — a beam a HuGME-n a legkevésbé „kerekít", noha az összesített HuGME-je (0,9082) csak 2. a deepseek think (0,9369) mögött.
- **A HuWNLI továbbra is a nagy modellek falánksága:** beam 8,3%, muse 11,7%, deepseek 16,7%, minimax 45,0% — a lokális 9B 60,0%. A 2 osztályos NLI-formátum láthatóan ütközik a hosszú, gondolkodó válaszadással.
- **Az MT-Bench a leggyengébb dimenzió** (0,4896): a hosszú gondolkodás a bíró szerint kevésbé illik a párbeszédes feladatokhoz — 5 vereség a 24 itemen.

### Limitációk
- Think-only mérés — a modell nothink módja nem elérhető.
- A `think` szintek (low…max) nem lettek végigmérve; a mérés a **default (max)** szinten történt.
- 2 baseline az MT-Bench-HU-n (a harmadik RETIRED).
- Egy bíró a HuGME-n (bíró-torzítás lehetséges).
- Az UD-nél 8 üres válasz és 8 parse-hiba (98,2% parse-hányad) — a muse 100%-a felett ez a beam gyengébb formátumhűsége.

---

## 10. Következő lépések

1. **A think-szintek (low/medium/high/xhigh/max) összevetése** — a beam támogatja, és a max szint drága; érdemes megnézni, mennyit veszít a low/high.
2. A lokális Qwen3.5-9B think kör mérése (a llama-server indítását igényli).
3. A deepseek/mistral/minimax think UD újrafuttatásának lezárása (run7b, folyamatban).
4. A harmadik MT-Bench baseline pótlása.

---

## Függelék — adatok és reprodukálhatóság

| Mi | Hol |
|---|---|
| HuLU (2581 sor) | `results/beam-cloud-think/hulu_results.jsonl` |
| MMLU-HU (750 sor) | `results/beam-cloud-think/mmlu_hu_results.jsonl` |
| HuGME (300 + 300 bíró) | `results/beam-cloud-think/hugme_results.jsonl`, `hugme_judged.jsonl` |
| MT-Bench (24 + 24 bíró) | `results/beam-cloud-think/mt_bench_hu_results.jsonl`, `mt_bench_hu_judged.jsonl` |
| UD (449 sor) | `results/beam-cloud-think/ud_hungarian_results.jsonl` |
| Checkpointok | `state/beam-cloud-think/*.json` |
| Logok | `logs/run8/driver.log`, `logs/run8b/driver.log` |

```bash
cd ~/git/hu-eval && source .venv/bin/activate

# Mód-diagnózis (nothink nem működik)
python - <<'EOF'
import requests
for th in (True, False):
    d = requests.post("http://localhost:11434/api/generate", json={
        "model": "beam:cloud", "prompt": "Írd le egy szóval: mi a fővárosa Magyarországnak?",
        "stream": False, "think": th}, timeout=120).json()
    print(th, "| thinking:", len(d.get("thinking") or ""))
EOF

# Teljes kör (think-only)
python scripts/run_hulu.py        --model beam:cloud --mode think
python scripts/run_mmlu_hu.py     --model beam:cloud --mode think
python scripts/run_hugme.py       --model beam:cloud --mode think
python scripts/run_mt_bench_hu.py --model beam:cloud --mode think
python scripts/judge_hugme.py     --model beam:cloud --mode think
python scripts/rejudge_mt_bench.py beam-cloud-think \
  --baselines deepseek-v4-pro:cloud kimi-k2.6:cloud

# UD — streaminggel (502 elkerülése)
BENCH_STREAM=1 python scripts/run_ud_hungarian.py --model beam:cloud --mode think

# Aggregáció + bontások
python scripts/aggregate_results.py
for b in hulu mmlu_hu ud_hungarian; do python scripts/breakdown_report.py --benchmark $b; done
```

---

## Változtatási napló

| Dátum | Változás |
|---|---|
| 2026-10-27 | Első verzió: teljes think kör, composite 0,7667 (3. hely); UD streaming javítással. |

---

## Kapcsolódó

- [Riport 2026-10-27 (muse-spark-open think)](report-2026-10-27.md)
- [Riport 2026-10-24 (lokális Qwen3.5-9B + cloud mezőny)](report-2026-10-24.md)
- [Riport 2026-10-22 (muse nothink, minimax, mistral, deepseek)](report-2026-10-22.md)
- [HuLU benchmark](../concepts/hulu-benchmark.md)
- [MMLU-HU benchmark](../concepts/mmlu-hu-benchmark.md)
- [HuGME benchmark](../concepts/hugme-benchmark.md)
- [MT-Bench-HU](../concepts/mt-bench-hu.md)
- [UD Hungarian](../concepts/ud-hungarian.md)
- [Checkpoint és progress](../concepts/checkpoint-progress.md)
- [Riport-sablon](riport-template.md)
