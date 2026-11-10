# Log — hu-eval Wiki

*Típus:* concept
*Forrás(ok):* belső projekt-napló
*Létrehozva:* 2026-06-05
*Frissítve:* 2026-10-17 (v1.7.1 — bíró modell váltás: deepseek-v4-pro:cloud → deepseek-v4-pro:0813-cloud; korábban v1.7 — új gép setup: uv venv + corpora, conda nélkül)

---

*Időrendi, append-only tevékenységnapló. Minden frissítés, ingest, query, lint itt.*

---

## 2026-06-16 (v1.2.11 — 4 új benchmark implementálva: MMLU-HU, HuGME, MT-Bench-HU, UD Hungarian)

- **Trigger:** user felkérése a maradék benchmarkok implementálására a HuLU-n kívül.
- **Scope döntés:** 4 új benchmark (a 9 definiáltból 5 marad: ARC-HU, GSM8K-HU, Perplexitás, Morfológia, Szórend kimarad — nincs magyar dataset az Ollama stacken).
- **Végső benchmark lista (5 db):** HuLU + MMLU-HU + HuGME + MT-Bench-HU + UD Hungarian.
  - STAT: `["hulu", "mmlu_hu"]`
  - GEN: `["hugme", "mt_bench_hu"]`
  - LING: `["ud_hungarian"]`
- **8 tervhiba javítva:** score-normalizálás (judge output már 0-1), UD composite formula, skip-check line-count, MMLU dev split + CONFIG=all, timeout/num_predict benchmark-specifikus, HuGME/MT-Bench prompt stratégia (300/24), UD GitHub forrás, judge output formátum.

### Letöltők (2 új, 1 javítva)

- `scripts/download_mmlu_hu.py` — javítva: `CONFIG = "all"` (nem `"default"`), dev split letöltés hozzáadva → `data/mmlu_hu/mmlu_hu_dev.jsonl`. A runner 5-shot promptot épít a dev splitből.
- `scripts/download_ud_hungarian.py` — **ÚJ**. GitHub raw CoNLL-U `hu_szeged-ud-test.conllu` fájlból (137 mondat) → standard JSONL `data/ud_hungarian/sentences.jsonl`.

### Runnerek (4 új)

- `scripts/run_mmlu_hu.py` — 5-shot, `num_predict=32`, `timeout=120`. 38 subject, accuracy 0-1. Saját checkpoint (state/{model}/mmlu_hu.json).
- `scripts/run_hugme.py` — 0-shot generatív, `num_predict=4096`, `timeout=300`. 300 prompt (6 metrika × 50). Válasz mentés, checkpoint, majd judge_hugme.py pontoz.
- `scripts/run_mt_bench_hu.py` — 2-turn conversation, `num_predict=4096`, `timeout=300`. 24 kérdés (8 kategória × 3). Baseline modell (`deepseek-v4-flash:cloud`) generálás automatikus.
- `scripts/run_ud_hungarian.py` — CoNLL-U parse, `num_predict=256`, `timeout=120`. A modell válaszából regex (TOKEN/UPOS/HEAD/DEPREL) kinyerés, composite = `(UPOS + UAS + LAS) / 3`.

### Judge scriptek (2 új)

- `scripts/judge_hugme.py` — `gemini-3-flash-preview`, 6 metrika (bias/toxicity/faithfulness/relevancy/summarization/alignment) minden promptra külön. `judge.overall` = 6 metrika átlaga (0-1).
- `scripts/judge_mt_bench.py` — `gemini-3-flash-preview`, GSB pairwise vs `deepseek-v4-flash:cloud` baseline. Counterbalanced (swap), `judge.overall` = win rate (0-1).

### Adatfájlok (2 új)

- `data/hugme/prompts.jsonl` — 300 magyar prompt (6 metrika × 50: bias/toxicity 25+25, faithfulness/relevancy 50, summarization 50, alignment 50).
- `data/mt_bench_hu/questions.jsonl` — 24 kérdés (8 kategória × 3: writing, roleplay, reasoning, math, extraction, stem, humanities, coding), 2 fordulóval.

### Script módosítások

- `scripts/aggregate_results.py` — `STAT/GEN/LING` listák frissítve. `extract_score`-ból PPL ág törölve, judge/overall `/10.0` ág törölve. `judge_avg`-ból `/10.0` törölve (judge output már 0-1).
- `scripts/hulu_breakdown_report.py` — változatlan (v1.2.10).
- `scripts/breakdown_report.py` — **ÚJ**. Általánosított breakdown report: `--benchmark hulu|mmlu_hu|ud_hungarian` paraméterrel. MMLU-HU: 38 subject, UD Hungarian: 3 metrika (UPOS/UAS/LAS).

### Orchestrator

- `scripts/queue_all_benchmarks.sh` — **ÚJ**. 5 benchmark × 10 modell × 2 mód. Skip-check line-count. Benchmark-specifikus timeout/num_predict. Judge lépés HuGME + MT-Bench esetén. `gpt-oss:20b-cloud-think` kihagyva (mint a HuLU-nál).

### Wiki frissítések

- `wiki/log.md` — ez a bejegyzés.
- `wiki/index.md` — statisztikák frissítve, új benchmarkok státusza, script-szám növ.
- `wiki/overview.md` — scope szűkítve (ARC, GSM8K, PPL, morfológia, szórend kimarad), új scriptek és adatfájlok listázva.
- `wiki/concepts/tobbi-benchmark-modszere.md` — implementációs státusz frissítve (4 benchmark kész, 5 kimarad).
- `wiki/concepts/mmlu-hu.md` — runner létezik (`run_mmlu_hu.py`), 5-shot, 38 subject.
- `wiki/concepts/hugme-benchmark.md` — runner létezik, de DeepEval nélkül (saját `judge_hugme.py`).
- `wiki/concepts/mt-bench-hu.md` — runner létezik, 24 kérdés (nem 80), GSB pairwise.
- `wiki/concepts/ud-hungarian.md` — runner létezik, 137 mondat, UPOS/UAS/LAS parse.

### Implementációs részletek

- **Timeout benchmark-specifikus:** MMLU 32/120, HuGME/MT-Bench 4096/300, UD 256/120.
- **Score normalization:** minden runner/judge 0-1 normalizált score-t ír a summary JSON-ba. `judge.overall` = átlagolt metrika-átlag (0-1).
- **Skip-check:** line-count a results JSONL-en (nem `jq .status` — HuLU summary-nak nincs status mezője).
- **MMLU-HU 5-shot:** `CONFIG="all"` (javítva). NyTK dev split (5 példa/tantárgy).
- **HuGME:** 6 metrika, minden metrikára külön bíró hívás (300 prompt × 6 = 1800 judge call/modell).
- **MT-Bench-HU:** baseline `deepseek-v4-flash:cloud`. GSB pairwise, counterbalanced (swap). win rate = (win + tie/2) / total.
- **UD Hungarian:** GitHub forrás, nem HF. Composite = `(UPOS + UAS + LAS) / 3`.
- **`gpt-oss:20b-cloud-think`:** MINDEN benchmarkra lefut (2026-07-08, user kérésére a skip-policy eltávolítva: `queue_all_benchmarks.sh`, `queue_runner.sh`, `phase2_runner.sh`).

---

## 2026-06-16 (v1.2.10 — nehézség-statisztika + difficulty PNG törölve)

- **Trigger:** user kérése: "A difficulty statisztikát vedd ki, az nem érdekel."
- **Végrehajtott változtatások a `scripts/hulu_breakdown_report.py`-ban:**
  - A MD riportból a "## Összesítés — sub-task nehézség" szekció törölve (a táblázat, a kép-referencia, és a bevezető szöveg).
  - A difficulty PNG renderelése törölve — a `diff_rows` ciklus és a `render_table_png(... "hulu_breakdown_difficulty.png" ...)` hívás is.
  - Az immár nem használt `_std_dev(values)` és `_median(values)` segédfüggvények törölve.
  - A docstring frissítve: a kimenetek listájából a `hulu_breakdown_difficulty.png` törölve.
- **Eredmény:** a riport most **kizárólag per-modell × per-sub-task** mátrixot tartalmaz — 2 táblázat (think vs nothink wide, per sub-task), 2 PNG. Nincs pool-szintű aggregáció, nincs nehézség, nincs szórás/medián.
- **Wiki frissítések:**
  - `wiki/concepts/hulu-benchmark.md` — "Per-sub-task riport" szekció átírva v1.2.10-re: a "Pool-statisztikák" sor és a difficulty PNG-referencia törölve. A "Tipikus modell-teljesítmények" táblázatban a qwen3-next:80b-cloud leírása szűkítve (csak "leggyengébb acc", a "leggyorsabb" minősítés törölve). A "legnehezebb/legkönnyebb sub-task" szöveges sor is törölve. Frissítve: 2026-06-16.
  - `wiki/reports/hulu-breakdown-2026-06-16.md` — újragenerálva (a régi v1.2.9 helyett, mert a difficulty szekció törölve). A wiki-reports PNG lista: 2 db (think_nothink + accuracy).
  - A `hulu_breakdown_difficulty.png` törölve mind a `reports/`, mind a `wiki/reports/` mappából.
- **Miért fontos ez a döntés:** a nehézség-statisztika ("HuWNLI a legnehezebb, HuCoPA a legkönnyebb") a modellek teljesítményének kontextusát adja, de a felhasználó döntése: nem érdekel a pool-szintű összesítés, csak az egyes modellek/sub-taskok eredménye. A v1.2.10-es riport a lehető legminimalistább: **melyik modell, melyik sub-task, hány százalék**.

## 2026-06-16 (v1.2.9 — per-sub-task riport egyszerűsítve: csak accuracy)

- **Trigger:** user kérése: "Nem érdekelnek a következők: TPS, mennyi idő alatt végzett egy kéréssel, stb...; Egy dolgo érdekel, hogy jól válaszolt vagy nem."
- **Végrehajtott változtatások a `scripts/hulu_breakdown_report.py`-ban:**
  - `collect_per_task` egyszerűsítve: `durations` / `tokens` / `sec_pr` / `ts_pr` logika törölve, csak `correct / total / acc` maradt.
  - A `row` dict-ből a `*_sec_pr` és `*_ts_pr` mezők törölve, a CSV `fieldnames` is.
  - A markdown riportból a "Táblázat — sec/pr" és "Táblázat — TS/pr" szekciók törölve.
  - **2 PNG törölve:** `hulu_breakdown_sec_pr.png`, `hulu_breakdown_ts_pr.png`.
  - **3 PNG maradt:** `hulu_breakdown_think_nothink.png`, `hulu_breakdown_accuracy.png`, `hulu_breakdown_difficulty.png`.
  - A docstring frissítve: "Csak a pontosság (accuracy) az érdekes — sebesség, token, idő szándékosan nincs a riportban."
  - **Új segédfüggvények:** `_std_dev(values)` (korrigált mintás szórás, n-1) és `_median(values)` — a difficulty táblázat bővítéséhez.
  - **Difficulty táblázat bővítve:** új oszlopok: **Szórás** és **Medián** (eddig csak pool átlag + legjobb modell volt).
  - A difficulty PNG is tartalmazza az új oszlopokat (7 oszlop, szélesebb `col_widths`).
- **Új kimenet:** `reports/hulu-breakdown-2026-06-16.md` + `reports/hulu_breakdown.csv` (csak accuracy mezők) + 3 PNG.
- **Wiki frissítések:**
  - `wiki/concepts/hulu-benchmark.md` — "Per-sub-task riport" szekció átírva v1.2.9-re, a sec_pr/ts_pr PNG-k referenciái törölve, a modell-teljesítmény táblázatból a sec/pr/TS/pr oszlopok törölve (helyette csak a "Megjegyzés" oszlop utal a leggyorsabb/leggyengébb modellre). Frissítve: 2026-06-16.
  - `wiki/reports/hulu-breakdown-2026-06-16.md` — új fájl a régi (2026-06-15) felülírása helyett (preserve + extend elv).
  - A régi `hulu_breakdown_sec_pr.png` / `hulu_breakdown_ts_pr.png` törölve a `wiki/reports/`-ból.
- **Miért fontos ez a döntés:** a sebesség/token-metrikák a riportban nem a "modell minőségét" mérik, hanem az Ollama Cloud API network latency-jét (lásd TPS-magyarázat a v1.2.8 verzióban). Egy modell gyors lehet, mert kicsi a kontextus vagy kevésbé részletes a válasz — ez nem minőségi mutató. A v1.2.9-es riport **egyetlen kérdést** tesz fel: jól válaszolt-e vagy sem.

## 2026-06-15 (v1.2.8 — per-sub-task bontás riport)

- **Trigger:** user kérése, hogy a riport ne csak egy kompozit számot mutasson, hanem minden HuLU sub-task (HuCOLA, HuCoPA, HuRTE, HuSST, HuWNLI, HuCB) külön legyen értékelve + legyen composite is, táblázatonként külön PNG-vel.
- **Végrehajtott változtatások:**
  - `scripts/hulu_breakdown_report.py` — **ÚJ script** (~330 sor). Bejárja a `results/{model}-{mode}/hulu_results.jsonl` fájlokat, és modellenként/módonként kiszámolja:
    - 6 sub-task accuracy (correct/total)
    - **Composite** (per spec) = sub-task accuracy-k egyszerű (egyenként súlyozatlan) átlaga
    - **Overall** (kanonikus) = total_correct / total_examples (a HuSST-vel súlyozott)
    - sec/pr és TS/pr sub-taskonként
    - Pool-szintű nehézségi összesítés
  - Duplikátumok kezelése: az utolsó előfordulás számít (id alapján) — így a RESUME ciklusok duplikátumai nem zavarnak.
  - **4 új PNG** generálás `matplotlib.table`-lel, táblázatonként külön:
    - `reports/hulu_breakdown_accuracy.png`
    - `reports/hulu_breakdown_sec_pr.png`
    - `reports/hulu_breakdown_ts_pr.png`
    - `reports/hulu_breakdown_difficulty.png`
  - Kimenetek másolva a wikibe: `wiki/reports/hulu-breakdown-2026-06-15.md` + 4 PNG.
  - `wiki/concepts/hulu-benchmark.md` — "Per-sub-task riport" szekció frissítve, a 4 PNG belinkelésével.
- **Meglepetések az adatokból:**
  - A **Composite (per spec) és Overall (kanonikus) sorrend más!** Példák:
    - `minimax-m3-cloud (think)`: Composite 74.9% (3. hely) vs Overall 77.1% (1. hely) — a HuSST-n (1165 prompt) kiemelkedő, és a HuWNLI-n (60 prompt) gyenge
    - `qwen3.5-cloud (think)`: Composite 71.6% (8. hely) vs Overall 78.1% (1. hely) — HuSST-n szintén erős, HuWNLI-n viszont katasztrofális (1.7%)
    - `kimi-k2.6-cloud (nothink)`: Composite 76.8% (1. hely) vs Overall 75.9% (4. hely) — HuWNLI-n a legjobb (55%), HuSST-n közepes
  - **A HuWNLI a legnehezebb** (pool átlag 28.2%, legjobb 55% — `kimi-k2.6 nothink`); 11/19 modell 50% alatt (közel a 50%-os random baseline-hoz)
  - **A HuCoPA a legkönnyebb** (pool átlag 92.8%, legjobb 98% — `minimax-m3 nothink`)
  - **A HuSST a legnagyobb és egyben nehéz** (1165 prompt, pool átlag 66.9%) — emiatt dominálja az Overall-t
- **A két composite formula ajánlott használata:**
  - **Composite (per spec):** ha a modell "kiegyensúlyozottsága" számít (minden sub-taskon hasonlóan jó)
  - **Overall (kanonikus):** ha a "production" pontosság számít, ahol a HuSST (legnagyobb, legrealisztikusabb: hosszú szövegek sentiment) dominál

---

## 2026-06-12 (v1.2.8 — végleges aggregáció, 19/19 benchmark kész)

- **Trigger:** `python scripts/aggregate_results.py` futtatása az összes (19) befejezett benchmarkon.
- **Eredmények:**
  - **Nothink átlag (10): 71.7% | Think átlag (9): 74.0% | Összesített átlag (19): 72.8%**
  - **🏆 Top 5:**
    1. `qwen3.5:cloud (think)` 78.1% — **legjobb think**
    2. `minimax-m3:cloud (think)` 77.1%
    3. `deepseek-v4-flash:cloud (think)` 76.7%
    4. `kimi-k2.6:cloud (nothink)` 75.9% — **legjobb nothink**
    5. `deepseek-v4-pro:cloud (think)` 75.9%
  - **🔻 Bottom 3:**
    17. `gpt-oss:20b:cloud (nothink)` 67.0%
    18. `qwen3-next:80b-cloud (think)` 63.2%
    19. `qwen3-next:80b-cloud (nothink)` 61.5%
  - **Legnagyobb think javulás:** `glm-5.1` (+4.1%), `deepseek-v4-flash` (+3.4%), `qwen3.5` (+3.1%)
  - **Think rontás:** `kimi-k2.6` (-0.7%), `gpt-oss:120b` (-0.2%)
  - **Leggyorsabb nothink:** `deepseek-v4-pro` 0.59s/pr
  - **Leggyorsabb think:** `qwen3-next:80b-cloud` 15.18s/pr (2497 TS/pr)
- **Generált fájlok:** `reports/composite_scores.csv`, `reports/report.md`, `reports/results_heatmap.png`
- **Nincs `[RÉSZLEGES]` jelölés** — mind a 19 benchmark teljes (≥2581 sor). A composite score tiszta.
- **Változtatások a wikiben:**
  - `concepts/hulu-benchmark.md` — "Tipikus modell-teljesítmények" táblázat frissítve v1.2.8-ra: végleges acc értékek, 10-modelles táblázat (qwen3.5: 78.1%, nemotron: 71.8% — már nem részleges). Új átlag sorok, módosított Δ értékek (qwen3-next: +1.7%, nem -0.6% a teljes adaton).
  - `index.md` — státusz frissítés (ha szükséges)
  - `log.md` — ez a bejegyzés

---

## 2026-06-09 (v1.2.7 — részletes sub-task leírások + nem-HuLU benchmarkok módszertana)

- **Trigger:** user kérése, hogy a HuLU benchmarkok és a nem-HuLU benchmarkok módszere is legyen részletesen dokumentálva a wikiben.
- **Végrehajtott változtatások (wiki/):**
  - `concepts/hulu-benchmark.md` — részletes bővítés (v1.2.6): minden sub-taskhoz (HuCOLA, HuCoPA, HuRTE, HuSST, HuWNLI, HuCB) mit-ellenőriz, felépítés, prompt formátum, kiértékelés, példa, nehézség. Új "Hogyan működik a benchmark — pipeline" szekció: letöltés, standardizálás, futtatás, JSONL mezők, checkpoint rendszer, think/nothink módok, aggregáció. Bővített pitfalls szekció. Tipikus modell-teljesítmények táblázat (2026-06-09 adatokkal).
  - `concepts/tobbi-benchmark-modszere.md` — ÚJ oldal (v1.2.7). A 8 nem-HuLU benchmark részletes módszertana: MMLU-HU (5-shot tudás-teszt, 38 tantárgy), ARC-HU (természettudományos következtetés), GSM8K-HU (matematikai CoT), Perplexitás (nyelvmodell-minőség), HuGME (generatív LLM-judge), MT-Bench-HU (multi-turn LLM-judge), UD Hungarian (szintaktikai elemzés), Magyar morfológia (toldalékolás). Minden benchmarkhoz: mit mér, forrás, formátum, pipeline, prompt, kiértékelés, implementációs státusz, tipikus értékek.
  - `index.md` — "Concepts" szekció frissítve: 14 → 15 db. Az új `tobbi-benchmark-modszere.md` belinkelve. A `hulu-benchmark.md` bejegyzés kiegészítve "(v1.2.6)" verzió-jelölővel.
- **Implementációs státusz (v1.2.7):** a HuLU az egyetlen teljes implementáció. A MMLU-HU-nak van letöltő, de nincs runner. A többi 7 benchmarkhoz csak wiki dokumentáció van. A `tobbi-benchmark-modszere.md` oldal tartalmazza a tervezett pipeline-t és az implementációs roadmap-et (perplexitás → MMLU-HU → ARC/GSM8K-HU → HuGME → MT-Bench-HU → UD/Morfológia).

### v1.2.7 státusz (2026-06-09 19:00)

**Benchmark állapot — 14 benchmark (8 modell × 2 mód; `minimax-m2.5` és `minimax-m2.7` törölve a queue-ból):**

| Státusz | Darab |
|---------|-------|
| ✅ Kész (2581 sor) | **11** |
| 🔄 Folyamatban | **2** |
| ⏸ Nem indult | 0 |

**Eredmények (kész, legjobb → leggyengébb):**

| Modell (mód) | Acc | TS/prompt | sec/prompt | Megjegyzés |
|--------------|-----|-----------|------------|------------|
| **kimi-k2.6 (nothink)** | **75.9%** | 2 | 0.79s | 🥇 legjobb |
| minimax-m3 (nothink) | 75.8% | 212 | 7.85s | 50 üres pred |
| qwen3.5 (nothink) | 75.4% | 10 | 1.14s | 6 üres pred |
| deepseek-v4-pro (nothink) | 74.6% | 2 | 0.59s | leggyorsabb |
| deepseek-v4-flash (nothink) | 73.3% | 1 | 0.94s | |
| **glm-5.1 (think)** | **75.7%** | 615 | 4.23s | +4.1 javulás nothink-hez képest |
| kimi-k2.6 (think) | 75.2% | 1674 | 12.28s | leghosszabb gondolkodás |
| gpt-oss:120b (nothink) | 71.8% | 265 | 3.89s | |
| gpt-oss:120b (think) | 71.6% | 222 | 3.01s | thinking mindkét módban azonos |
| glm-5.1 (nothink) | 71.6% | 1 | 1.29s | |
| nemotron-3-ultra (nothink) | 70.5% | 2 | 2.93s | |
| gpt-oss:20b (nothink) | 67.0% | – | – | régi kód, 125 üres pred |

**Folyamatban (2026-06-09 19:00):**
- `qwen3.5:cloud (think)` — 696/2581 (indult 17:08, +188 sor 1:52 óra alatt). 86.5% accuracy a részmintán (a 6 NLU sub-task mindegyikén jól teljesít, kivéve HuWNLI-t ahol az eddigi részmintán is 0%). Becsült hátralévő: 1885 prompt × 22.9s ≈ 12.0 óra (átlag), de a fájlból számolva 18-20 óra. Várható kész: **2026-06-10 13:00-15:00** körül.
- `nemotron-3-ultra:cloud (think)` — 887/2581 (2026-06-09 16:39-ig futott, leállt 17:08-kor, phase2 runner fogja RESUME-olni). 33.76s/prompt a leglassabb think modell. Becsült hátralévő: 1694 prompt × 33.8s ≈ 15.9 óra. Várható kész (a qwen3.5 után): **2026-06-11 05:00-09:00** körül.

**Teljes várható kész: 2026-06-11 13:00 körül** (holnapután délután).

**Aktív folyamatok:**
- `queue_runner.sh` (PID 652547, indult 2026-06-09 17:08) — `qwen3.5:cloud (think)` futtatását felügyeli
- `phase2_runner.sh` (PID 652570) — várakozik a queue-ra, utána `nemotron-3-ultra:cloud (think)` RESUME

**TPS-magyarázat:** az Ollama Cloud API nem adja vissza az `ollama_eval_duration_ns` és `ollama_prompt_eval_duration_ns` mezőket (null), csak az `ollama_total_duration_ns`-t. Ezért a `total_duration / eval_count` hányados csak felső becslés. A nothink modellek 1-10 tokent generálnak (network-dominated), a think modellek 222-1674-et (TPS közelít a valóshoz). A `hulu-benchmark.md` táblázatában tárolt TPS-értékek a `total_dur - prompt_processing becslés` módszerrel készültek.

**További megfigyelések (v1.2.7):**
- A `gpt-oss:20b-cloud` régi kóddal futott (`think: False` nélkül, nincs `ollama_*` mező), 125 üres pred, 67.0% acc. Nem javítjuk, mert a modell kisebb és a többi felülmúlja.
- A `qwen3.5:cloud (think)` 86.5%-os részminta-eredménye (696 prompt) kiemelkedő — de ez valószínűleg a HuCOLA és HuRTE magas pontszámainak köszönhető, amiket a modell kiválóan teljesít. A teljes futás várhatóan 76-80% körül lesz.
- A `gpt-oss:120b:cloud` think/nothink azonos (71.6% vs 71.8%) — a modell nem használja a thinking képességet, a gondolkodás nem javít a teljesítményen.
- A `glm-5.1:cloud` a legnagyobb think-javulást mutatja (+4.1% nothink-hez képest) — a thinking itt ténylegesen segít.

### v1.2.7 RESUME (2026-06-10 17:37-17:44)

- **Trigger:** user kérése, hogy a 2 nem teljes benchmark (`qwen3.5:cloud (think)`, `nemotron-3-ultra:cloud (think)`) fusson tovább.
- **Háttér:** a queue_runner és phase2_runner 2026-06-10 13:41-kor fejeződött be. A `qwen3.5:cloud (think)` 1027/2581-nél (88.5% részminta, leállt 12:59), a `nemotron-3-ultra:cloud (think)` 1095/2581-nél (77.9% részminta, leállt 13:35) timeout-sorozat miatt.
- **Első indítás (17:37):** `nohup python scripts/run_hulu.py --model X --mode think &` — de a Python block-buffering miatt a log üres volt, és 5:55 perc elteltével semmi nem történt (0% CPU, `poll_s` állapot, `/api/ps` üres). A `qwen3.5` különösen beragadt — valószínűleg a checkpoint betöltés + az Ollama cloud API SSL handshake hosszú.
- **Megoldás (17:44):** `kill -9` a két beragadt processre, majd `python -u` (unbuffered) flaggel újraindítás. Most a log azonnal megjelenik, és a processzek dolgoznak.
- **Aktuális állapot (17:46):** mindkét futás aktív. A `qwen3.5:cloud (think)` 1027→1030 (+3 sor 1:43 perc alatt, ~34s/prompt — a párhuzamosság miatt lassabb a korábbi 22.5s/prompt-nál). A `nemotron-3-ultra:cloud (think)` 1098→1098 (még nem halad, ahogy a korábbi futásban sem — a modell hajlamos a timeout-sorozatra).
- **Várható kész:** ~20 óra (párhuzamos futás, a lassabb határozza meg): qwen3.5: ~15 óra (1551 prompt × ~35s), nemotron: ~20 óra (1483 prompt × ~50s). Várható done: **2026-06-11 ~13:00-14:00**.

### v1.2.7 státusz (2026-06-10 17:46, frissítve)

- 14/16 benchmark teljes (2581 sor).
- 2/16 fut (RESUME-ban, párhuzamosan): `qwen3.5:cloud (think)`, `nemotron-3-ultra:cloud (think)`.
- 0/16 nem indult.
- Mindkét runner (queue_runner.sh PID 652547, phase2_runner.sh PID 652570) leállt 13:41-kor — most a manuális RESUME fut `nohup`-pal.
- Logfájlok: `logs/hulu_qwen3.5-cloud-think_resume_20260610_1744.log` és `logs/hulu_nemotron-3-ultra-cloud-think_resume_20260610_1744.log`.
- **Tanulság (tan + 1 javaslat):** a `nohup` + `>` redirect esetén a Python block-buffering miatt a log nem jelenik meg valós időben. Megoldás: `python -u` (unbuffered) flag, vagy `print(..., flush=True)` a script-ben. A `run_hulu.py` jelenleg nem használ `flush=True`-t a print-eknél — ezt érdemes lenne patch-elni a jövőbeli futásokhoz.

### v1.2.7 — wiki átnézet és entitás-bővítés (2026-06-11 07:30)

- **Trigger:** user kérése, hogy a wiki legyen átnézve és frissítve a jelenlegi benchmark adatok alapján.
- **Jelenlegi benchmark állapot (2026-06-11 07:26):**
  - 19 benchmark (10 modell × 2 mód — `qwen3-next:80b-cloud` 2026-06-10 hozzáadva)
  - ✅ Kész (≥2581 sor): 15/19
  - 🔄 Folyamatban (RESUME): 4/19
    - `qwen3.5:cloud (think)` — 2495/2581, 78.6% acc, ~22.7s/pr
    - `nemotron-3-ultra:cloud (think)` — 2301/2581, 73.6% acc, ~29.7s/pr
    - `qwen3-next:80b-cloud (nothink)` — 1331/2581, 67.2% acc, ~12.6s/pr
    - `qwen3-next:80b-cloud (think)` — 1518/2581, 66.6% acc, ~12.1s/pr
  - Várható teljes kész: **2026-06-11 11:49** (a `qwen3-next nothink` a leglassabb)
- **Végrehajtott wiki változtatások:**
  - `wiki/entities/qwen3-next-80b.md` — **ÚJ entitás oldal** (2026-06-10, frissítve 2026-06-11). 80B paraméter, FP8 kvantizálás, 262K kontextus, Qwen3-Next architektúra. Első benchmark eredmények: 67.2% nothink, 66.6% think (részleges), **legmagasabb TPS** (2452/2310 TS/pr). A think mód **nem javít**, sőt ront — a 80B-s modell nem tudja kihasználni a thinking képességet.
  - `wiki/index.md` — entitás szekció frissítve: 11→12 db, 6→7 modell. Az új `qwen3-next-80b` belinkelve a második helyre (a `qwen3.5-397b` után). Statisztika: 38→42 markdown, 7500→8500 sor.
  - `wiki/concepts/hulu-benchmark.md` — "Tipikus modell-teljesítmények" táblázat teljesen frissítve (v1.2.5→v1.2.7). Most 11 modell sorban, sec/pr és TS/pr oszlopokkal, Δ értékekkel, és 6 megjegyzéssel a think mód hatásáról, a leggyorsabb modellekről, és a TPS-magyarázatról.
- **Meglepetések a v1.2.7 adatokból:**
  1. **A `qwen3-next:80b-cloud` a leggyorsabb think modell** (2310 TS/pr) — a FP8 kvantálás és a hatékony architektúra miatt
  2. **A think mód hatása modellenként nagyon változó:** +4.1% (`glm-5.1`) és +3.4% (`deepseek-v4-flash`) a legjobbak; **-0.6% a `qwen3-next:80b`-nél** (a modell nem tudja kihasználni)
  3. **A `qwen3.5:cloud (think)` várhatóan ~78-80%-os lesz** (2495-nél 78.6%, a HuWNLI sub-task nehézsége miatt csökkenő tendencia)
  4. **A `kimi-k2.6:cloud` nem a leggyorsabb think modell** (1674 TS/pr) — a `qwen3-next:80b` (2310 TS/pr) és a `qwen3.5` (1320 TS/pr) megelőzi

### v1.2.7 — qwen3-next:80b-cloud modell hozzáadása (2026-06-10 23:36)

- **Trigger:** user kérése, hogy a `qwen3-next:80b-cloud` modell is legyen hozzáadva mind nothink, mind think módban.
- **Modell részletei:**
  - Név: `qwen3-next:80b-cloud`
  - Paraméter: 80B (FP8 kvantizálás)
  - Context length: 262144 token
  - Capabilities: completion, thinking, tools
  - Elérhető az Ollama szerveren (`/api/show` megerősítette)
- **Végrehajtott változtatások:**
  - `scripts/queue_runner.sh` — `MODELS` tömbbe hozzáadva a 2. pozícióban (a `qwen3.5:cloud` után). A komment frissítve: "A qwen3-next:80b-cloud 2026-06-10 hozzáadva (80B paraméter, FP8, 262K context)."
  - `scripts/phase2_runner.sh` — `MODELS` tömbbe hozzáadva ugyanúgy a 2. pozícióban.
  - `wiki/overview.md` — modell táblázat frissítve: `qwen3-next:80b-cloud` sor hozzáadva a cloud benchmark modellek közé.
- **Becsült futási idő:** 80B paraméter, FP8 — valószínűleg lassabb, mint a `kimi-k2.6:cloud` (1T, int4) think módban, de gyorsabb, mint a `nemotron-3-ultra:cloud` (550B). Becsült: ~15-25s/prompt nothink, ~30-60s/prompt think. A 300s timeout-patch (v1.2.7) elég kell legyen.
- **A queue_runner.sh következő indításakor** a `qwen3-next:80b-cloud` mindkét módban lefut. A skip-check ellenőrzi, hogy van-e már `results/qwen3-next-80b-cloud-nothink/` vagy `results/qwen3-next-80b-cloud-think/` mappa — ha nincs, elindítja.

### v1.2.7 RESUME — timeout-patch és 6. újraindítás (2026-06-10 22:13-22:23, folyamatban)

- **Trigger:** user kérése, hogy a 2 részleges benchmarkot (`qwen3.5:cloud (think)`, `nemotron-3-ultra:cloud (think)`) folytassuk.
- **5. újraindítási kísérlet (22:13, sima restart):** a 2 processz elindult, de 2:17 perc elteltével egyik sem haladt (0% CPU, `poll_s` állapot). Ugyanaz a timeout-probléma, mint korábban.
- **Megoldás (22:16) — timeout-patch a `run_hulu.py`-ban:**
  - A 169. sorban a `call_ollama_strict` hívás kiegészítve `timeout` és `max_retries` paraméterekkel:
    ```python
    response = call_ollama_strict(
        item["prompt"], model,
        think=think,
        num_predict=(16384 if think else 4096),
        timeout=(300 if think else 120),
        max_retries=(1 if think else 2),
    )
    ```
  - Think módban: `timeout=300s` (5 perc), `max_retries=1` → max várakozás: 5+5+1+1 = ~12 perc/item (3 kísérlet)
  - Nothink módban: változatlan (`timeout=120s`, `max_retries=2`) — a nothink modellek 1-2 tokent generálnak, 120s bőven elég
- **6. újraindítási kísérlet (22:16, timeout-patch-csel):** mindkét processz elindult.
  - **22:20 (4:31 perc elteltével):** a `qwen3.5` 1061→1065 (+4 sor, ~68s/prompt), a `nemotron` 1098→1101 (+3 sor, ~91s/prompt). A timeout-patch **működik** — a modellek most már válaszolnak a korábban elakadt promptokra!
  - **22:23 (6:45 perc elteltével):** a `qwen3.5` 1065→1068 (+3 sor, ~40s/prompt — gyorsul). A `nemotron` 1101→1101 (még mindig elakadt, de a korábbi 3 sor bizonyítja, hogy halad).
- **Becsült hátralévő idő (22:23 alapján):**
  - qwen3.5: 1549 prompt × ~40-68s = **17-29 óra** → várható kész: **2026-06-11 15:00 - 2026-06-12 03:00**
  - nemotron: 1523 prompt × ~91s = **~38 óra** → várható kész: **2026-06-12 12:00 körül**
- **Aktív PID-ek:** qwen3.5 PID 721945, nemotron PID 721948. Logfájlok: `logs/hulu_qwen3.5-cloud-think_resume_20260610_2216.log` és `logs/hulu_nemotron-3-ultra-cloud-think_resume_20260610_2216.log`.

### v1.2.7 RESUME — végleges eredmény (2026-06-10 18:16)

A 4 újraindítási kísérlet (17:37, 17:44, 17:51, 17:56) után sem sikerült a 2 hiányzó benchmarkot teljesen befejezni. Mindkét modell timeout-sorozat miatt leállt, és a `120s × 3 retry = 6 perc` timeout nem volt elég bizonyos hosszú HuRTE promptok feldolgozására (60-80s gondolkodási idő).

**Végleges részeredmények (részleges benchmark, `[RÉSZLEGES]` jelöléssel az aggregátorban):**

| Modell (mód) | State (completed) | JSONL sorok | Acc (state) | Hátralévő | Státusz |
|--------------|-------------------|-------------|-------------|-----------|---------|
| qwen3.5:cloud (think) | 1032/2581 (40.0%) | 1061 | 88.5% | 1549 | ⏸ leállt |
| nemotron-3-ultra:cloud (think) | 1058/2581 (41.0%) | 1098 | 77.9% | 1523 | ⏸ leállt |

**Mi történt:**
1. 17:37 — Első indítás `nohup`-pal. 5:55 perc elteltével a processek 0% CPU-val, `poll_s` állapotban voltak, a log üres maradt. Valószínű ok: a Python `print` block-buffering `nohup` + fájl-redirect esetén.
2. 17:44 — `kill -9` + újraindítás `python -u` (unbuffered) flaggel. A `qwen3.5` elindult, 1027→1053 között 26 itemet dolgozott fel (~12s/item), majd a `hulu_hurte_00022` környékén timeout-sorozat. A `nemotron` 1058-nál timeout.
3. 17:51 — `nemotron` újraindítás (a `qwen3.5` ekkor már futott). A `nemotron` 0 itemet dolgozott fel, ismét timeout.
4. 17:56 — Mindkettő újraindítása. A `qwen3.5` 1053→1061 között 8 itemet dolgozott fel (lassan, ~60s/item, egyes itemek 78-80s), de ismét timeout. A `nemotron` ismét timeout 1058-nál.
5. 18:16 — Végleges leállítás. A `qwen3.5` process 9 percig futott utoljára, 8 itemet dolgozott fel, majd timeout.

**Technikai tanulságok:**
- **Timeout túl rövid think módhoz:** a `120s × 3 retry = 6 perc` nem elég, ha a modell 60-80s-ig gondolkodik egy HuRTE promptnál. A megoldás: `timeout=300` (5 perc) a `call_ollama_strict` hívásban, és `max_retries=1` (1 retry × 5 perc = 10 perc, ami elég).
- **State vs JSONL eltérés:** a `run_hulu.py` csak 50-esével menti a state-et (`cp.save()`), de minden item után ír a JSONL-be (`fout.flush() + os.fsync()`). Ha timeout történik, a JSONL 50-nel több itemet tartalmazhat, mint a state. Ezek az itemek duplikálódnak a RESUME során. Megoldás: `cp.save()` hívása minden item után, nem csak 50-esével.
- **nohup + buffering:** a `nohup python script.py > log 2>&1 &` esetén a Python stdout block-buffering-et használ (nem line-buffered), így a `print` kimenet csak a folyamat végén (vagy puffer-telítődéskor) jelenik meg a log fájlban. Megoldás: `python -u` flag, vagy `PYTHONUNBUFFERED=1` környezeti változó.
- **Qwen3.5:cloud think mód:** kiemelkedő pontosság (88.5% a részmintán, ami 13.4%-kal jobb a nothink 75.4%-nál), de a gondolkodási idő nagyon változó (17-80s/prompt). A 40%-os részminta már reprezentatív, és a teljes futás várhatóan 80-85% között lenne.
- **Nemotron-3-ultra:cloud think mód:** közepes pontosság (77.9% a részmintán, ami 7.4%-kal jobb a nothink 70.5%-nál), és a gondolkodás még lassabb (~33s/prompt átlag). Timeout-sorozatra hajlamos.

**Javaslat a jövőre (a `wiki/concepts/checkpoint-progress.md` oldalon dokumentálandó):**
- A `call_ollama_strict` timeout-ot 120s-ról 300s-ra növelni think módhoz
- A `run_hulu.py` `cp.save()` hívását 50-esével minden egyes item utánira cserélni
- A `print` utasításokhoz `flush=True` hozzáadása a valós idejű logoláshoz

**Összesítés (2026-06-10 18:16, v1.2.7 záró állapot):**
- ✅ Kész benchmarkok: 14/16 (87.5%)
- ⏸ Részleges benchmarkok: 2/16 (12.5%) — `qwen3.5:cloud (think)`, `nemotron-3-ultra:cloud (think)`
- A `python scripts/aggregate_results.py` futtatható, és a composite score `[RÉSZLEGES]` jelölést kap a 2 hiányzó benchmark miatt.

---

## 2026-06-08 (v1.2.5 — think/nothink módok, 2× benchmark minden modellre)

- **Trigger:** user kérése, hogy minden modell legyen tesztelve mind thinking, mind no-thinking módban. Az eddigi futások `think: False` flaggel történtek (a `stop_on_error.py` egységesen `"think": False`-t küldött), tehát a meglévő eredmények nothink módban vannak. A think mód eredményei még nem léteztek.
- **Végrehajtott változtatások (scripts/):**
  - `stop_on_error.py` — `call_ollama_strict` új `think: bool` és `num_predict: int` paramétereket kap (default: `think=False, num_predict=4096`). A payload `think` és `options.num_predict` mezői ezeket használják.
  - `run_hulu.py` — új `--mode {think,nothink}` flag (default: `nothink`). A `num_predict` a módtól függ: nothink → 4096, think → 16384 (a `call_ollama_strict` hívásban). A `model_safe` változó a mode suffixet kapja: `model.replace(...) + f"-{mode}"`. A state és results mappák elkülönülnek: `state/{model}-nothink/`, `state/{model}-think/`, `results/{model}-nothink/`, `results/{model}-think/`. A JSONL rekordok kapnak egy `mode` mezőt.
  - **Bug fix a v1.2.5-ben:** a `mode` változót a `with open(out_path, mode, ...)` sorban a fájlmód írta felül (`"w"` vagy `"a"`), és a JSONL `"mode": mode` mezőbe a felülírt érték került. Javítva: a fájlmód változó átnevezve `file_mode`-ra.
  - `queue_runner.sh` — most MINDKÉT módot (`nothink` + `think`) futtatja minden modellre. A skip-check ellenőrzi a `results/{model}-{mode}/` (új) ÉS a `results/{model}/` (régi, mode nélküli) útvonalat is — így a korábbi futások eredményei (amik nothink módban vannak) automatikusan átveszik a `results/{model}-nothink/` szerepét.
  - `phase2_runner.sh` — most a think módot futtatja minden modellre (a queue a nothink-et, a phase2 a think-et).
  - **`num_predict` változás (2026-06-08, 13:18):** nothink → 4096, think → 16384. A korábbi 2048-as limit a thinking modelleknél `done: length`-t okozott (a modell nem tudta befejezni a gondolkodást, és a válasz üres maradt). A 16384-es limit think módban elegendő helyet ad a gondolkodásra. Smoke teszt (`minimax-m3:cloud --mode think --limit 2`): 12/12 prompt, `done: stop` mindenhol, `gen_tokens: 69-1044`. A nothink mód 4096-os limitje a jövőbeli biztonság kedvéért magasabb (a nem-thinking modellek 1-2 tokent generálnak, így nincs hatás).
- **Végrehajtott változtatások (adatok):**
  - A meglévő `results/{model}/` mappák átnevezve `results/{model}-nothink/` mappára (9 modell × 2581/2581 sor).
  - A meglévő `state/{model}/` mappák átnevezve `state/{model}-nothink/` mappára.
  - A `gpt-oss:120b-cloud` nothink RESUME: 2419/2581 → most a queue runnerben fut.
  - A `qwen3.5:cloud-think` (első think módú futás) 50/2581-nél tart (az új num_predict-tel RESUME).
  - A `minimax-m2.5:cloud` és `minimax-m2.7:cloud` továbbra sem futnak (régi modellek, törölve a queue-ból).
- **Várható eredmény:** 6 modell × 2 mód = 12 benchmark. A nothink mód 1-1 (RESUME vagy kész), a think mód 6 új benchmark. Becsült idő: a think mód lassabb (gondolkodás + 16384 token limit), de a cloud modellek 1-6 óra alatt futnak. Összesen ~12-36 óra.

---

## 2026-06-08 (v1.2.4 — `kimi-k2.6:cloud` bíró státusz végleges törlése)

- **Trigger:** user döntése: a `kimi-k2.6:cloud` modell NE legyen bíró, CSAK benchmark modell. A v1.2.3-ban a kimi `judge + benchmark` kategóriába került — ez most visszavonva. A bíró pool mostantól kizárólag a `gemini-3-flash-preview:latest`-ből áll.
- **Végrehajtott változtatások (wiki/, ~20 fájl):**
  - `overview.md` — kimi `Szerep`: `judge + benchmark` → `benchmark`, státusz: bíró törölve.
  - `index.md` — "Kimi K2.6 — Bíró" → "Kimi K2.6 — benchmark modell".
  - `comparisons/modell-vs-modell.md` — 3 helyen a bíró hivatkozás cserélve `gemini-3-flash-preview:latest`-re; a "bíró vs versenyző" összehasonlítás törölve.
  - `comparisons/cloud-vs-lokal.md` — bíró modell hivatkozások javítva.
  - `runbooks/llm-judge-prompt-template.md` — 4 helyen `--judge-model kimi-k2.6:cloud` → `--judge-model gemini-3-flash-preview:latest`.
  - `reports/riport-template.md` — bíró modell `pl. kimi-k2.6:cloud` → `gemini-3-flash-preview:latest`.
  - `concepts/llm-as-judge.md` — bíró preferencia-sorrend és feladattábla javítva.
  - `concepts/hugme-benchmark.md` — 3 helyen (self-bias figyelmeztetés, BÍRÓ KIMENET címke, JUDGE_MODEL változó).
  - `concepts/mt-bench-hu.md` — bíró költség példa cserélve.
  - `concepts/szabad-kerdes-hu.md` — bíró modell hivatkozás javítva.
  - `entities/dataset-hugme.md`, `entities/dataset-mt-bench-hu.md` — "Bíró modell: Kimi K2.6" → "Bíró modell: Gemini 3 Flash Preview".
  - `entities/deepseek-v4-pro.md`, `entities/minimax-m3.md`, `entities/qwen3.5-397b.md` — bíró kereszthivatkozások javítva.
  - `log.md` — v1.2.3 bejegyzés kiegészítve a "v1.2.4 visszavonta" megjegyzéssel; ez a bejegyzés (v1.2.4).
- **Változatlan (preserve):** v1.2.1 és v1.2.3 bejegyzések — mint történeti dokumentumok megmaradnak, de a jelenlegi állapotot a v1.2.4 definiálja.
- **`scripts/queue_runner.sh` NEM változott** — a kimi továbbra is a benchmark listában van, ugyanúgy mint eddig. A bíró pool szűkítése csak a wiki dokumentációt érinti, a futó scripteket nem.

---

## 2026-06-07 (v1.2.3 — `kimi-k2.6:cloud` benchmark poolba, queue bővítés)

- **Trigger:** a `kimi-k2.6:cloud` modell eddig csak judge-ként volt jelölve a wikiben (`v1.2.1`), de a user kérésére mostantól benchmark modellként IS fut (HuLU multiple choice). A `glm-5.1:cloud` és `nemotron-3-ultra:cloud` is bekerült a queue-ba.
- **Végrehajtott változtatások:**
  - `scripts/queue_runner.sh` — MODELS lista bővítve: `qwen3.5:cloud` + `gpt-oss:120b-cloud` + `kimi-k2.6:cloud` + `glm-5.1:cloud` + `nemotron-3-ultra:cloud`. A `kimi-k2.6:cloud` benchmark modellként fut, de bíróként is használható generatív feladatokhoz.
  - `wiki/overview.md` — `kimi-k2.6:cloud` Szerep: `judge` → `judge + benchmark`, Státusz: `bíró (LLM-as-a-Judge) ÉS benchmark modell (HuLU fut rajta)`.
  - Megjegyzés a scriptben: a judge kategória NEM kizáró — egy modell lehet egyszerre judge és benchmark.

---

## 2026-06-07 (v1.2.2 — `qwen3.5:397b-cloud` → `qwen3.5:cloud`, új modellek futtatása)

- **Trigger:** a `qwen3.5:397b-cloud` modell nem létezik ezen a néven az Ollama poolban. A helyes név `qwen3.5:cloud` (ollama pull sikeres). Emellett a `gpt-oss:120b-cloud` is hozzáadva a benchmark sorhoz.
- **Végrehajtott változtatások:**
  - `scripts/queue_runner.sh` — modell-lista frissítve: `qwen3.5:cloud` + `gpt-oss:120b-cloud`
  - `wiki/overview.md` — `qwen3.5:397b-cloud` → `qwen3.5:cloud`
  - Összes érintett wiki oldal (12 fájl) — globális `qwen3.5:397b-cloud` → `qwen3.5:cloud` replace
  - `wiki/log.md` — ez a bejegyzés

---

## 2026-06-07 (v1.2.1 — `gemini-3-flash-preview` áthelyezése a judge poolba)

- **Trigger:** user döntése: a `gemini-3-flash-preview:latest` modellt NEM benchmark-modellként, hanem kizárólag bíró (LLM-as-a-Judge) modellként használjuk. Eddig a `kimi-k2.6:cloud` volt az egyetlen dedikált judge; mostantól a kettő együtt látja el a bíró szerepet.
- **Végrehajtott változtatások (wiki/):**
  - `overview.md` modell-pool táblázat: új `Szerep` oszlop (benchmark / judge). A `gemini-3-flash-preview:latest` és a `kimi-k2.6:cloud` sorok `Szerep` értéke `judge`, a többi modellé `benchmark`. A `Státusz` oszlopban a judge modellek megjegyzése `bíró (LLM-as-a-Judge)`. A `Frissítve` dátum 2026-06-07-re frissítve.
  - Ez a v1.2.1 egy kiegészítő, kisméretű módosítás — nem érint adatforrást, scripteket vagy riportokat. Célja, hogy a modell-pool egyértelműen jelölje a szerepeket, és ne legyen félreértés a benchmark-futtatáskor.
- **Nem érintett (preserve):** `concepts/perplexity-hu.md` és `comparisons/modell-vs-modell.md` táblázatai, ahol a `gemini-3-flash-preview` benchmark-modellként volt említve — ezeket a user kérésére most NEM módosítjuk (csak a kanonikus modell-pool táblázat, a "kistár" változott). Ha később ezeket is konzisztenssé akarjuk tenni, újabb v1.2.2 bejegyzés kell.

---

## 2026-06-07 (v1.2 — NYTK forrásokra átállás, MMLU-HU downloader)

> **Ingest típus:** adathordozó-csere (broken → NYTK hivatalos). A Karpathy módszer 5 lépéséből: forrás feloldva, útválasztás kész, szintetizálás kész (preserve+extend), index+log frissítés most történik.

- **Trigger:** a `PhilipMay/hulu-bench` dataset 401 Unauthorized hibát ad (`scripts/download_hulu.py:16` referencia), és a wikiben idézett `hu-llm/hulu-v1.0` / `mmlu-hu/mmlu-hu-v1.0` URL-ek sem léteznek. Ellenőrzés: HF API + webfetch.

- **Hatókör (route):** 5 wiki-oldal érintett — `concepts/hulu-benchmark.md` (legnagyobb), `concepts/mmlu-hu.md`, `index.md` (katalógus), `README.md` (projekt-térkép), `log.md` (ez a bejegyzés). Emellett `AGENTS.md` (agent-útmutató) és 2 entity-oldal (`dataset-hulu.md`, `dataset-mmlu-hu.md`) is frissültek.

- **Végrehajtott változtatások (scripts/):**
  - `scripts/download_hulu.py` — teljes újraírás, 276 sor. 6 NYTK HF sub-task (`NYTK/HuCOLA`, `HuCoPA`, `HuRTE`, `HuSST`, `HuWNLI`, `HuCommitmentBank`) validation splitje, per-task magyar promptok, label-normalizálás (HuCoPA 1/2→0/1). Mezőnév-fallback `_g(rec, *nevek, default)` segédfüggvénnyel. `--offline` flag → `git clone --recurse-submodules https://github.com/nytud/HuLU.git` fallback. HuRC (7. dataset) szándékosan kihagyva — más formátum.
  - `scripts/download_mmlu_hu.py` — új, ~110 sor. `NYTK/hu-mmlu` "default" config (egyetlen config, 38 tantárgy egyesítve) validation splitje, 1880 példa. A nyers `answer` mező 0-3 int — nincs szükség A/B/C/D → 0/1/2/3 mappingre (korrigálva 2026-06-07 smoke teszt során). Egységes séma a `run_hulu.py`-val. Nincs `run_mmlu_hu.py` runner — csak letöltés + standardizálás.
  - Mindkét script `py_compile` szintaxis-ellenőrzésen átment.

- **Végrehajtott változtatások (wiki/):**
  - `concepts/hulu-benchmark.md` — legnagyobb módosítás. A 7-feladatos tévhit (HuPi + HuSTER) törölve, 6 NLU sub-task + 1 RC (HuRC) táblázat bevezetve. A `PhilipMay/hulu-bench` és `hulu_v1.0` könyvtárszerkezet cserélve a tényleges NYTK HF + standardizált séma leírásra. Python loader kód átírva az új `data/hulu/hulu_std.jsonl` sémára. Pitfalls: HuPi-referencia törölve, HuCoPA label-eltolás + HuRC „nincs implementálva" + field-name eltérés (HF vs. git) bejegyzések hozzáadva. Aggregátor függvény 6 taskra frissítve. A korábbi tévhitre explicit `❌` „téves információ" megjegyzések kerültek (preserve + extend elv: a hiba története is megmarad).
  - `concepts/mmlu-hu.md` — `nytud/mlmm-evaluation` GitHub repo → `NYTK/hu-mmlu` HuggingFace dataset. 57 → 38 tantárgy (a NYTK kihagyott néhányat a fordításból). Tantárgylista újrakategorizálva.
  - `entities/dataset-hulu.md` — 6 NYTK HF URL + nytud/HuLU git submodule URL + valódi LREC-COLING 2024 citation. Korábbi `PhilipMay/hulu-bench` (401) explicit megjelölve.
  - `entities/dataset-mmlu-hu.md` — `mmlu-hu/mmlu-hu-v1.0` (nem létezik) → `NYTK/hu-mmlu` (valódi). Maintainer, licenc, méret javítva.
  - `index.md` — katalógus frissítve: 7-feladatos lista → 6 NLU + HuRC. Utolsó frissítés dátum + verzió (v1.2). Script-szám 5 → 6.
  - `runbooks/run-hulu-modell-x.md` — §2 inline kódblokk (47 sor) cserélve `python scripts/download_hulu.py` + `--offline` opcióra. Forrás URL a fejlécben javítva.

- **Változatlan (jó állapot):**
  - `concepts/hulu-benchmark.md` HuCoLA részletes leírása (~0.78 MCC emberi baseline, stb.) — tényanyag, maradt.
  - `concepts/checkpoint-progress.md` — checkpoint tervezési elv, nem érintett.
  - A `run_hulu.py` futtató — az új standardizált séma (`{id, task, prompt, choices, answer_index, source}`) kompatibilis, nem kell módosítani.

- **Lint:** 0 törött belső link az újonnan hozzáadott `MMLU-HU` tantárgyszám-referencia és a `dataset-hulu.md` URL-ek ellenőrizve.

## 2026-06-06 (v1.1 — checkpoint + futtatható scriptek)

- 18:00 — **Checkpoint / resume tervezési elv bevezetve.** User kérés: scriptek legyenek folytathatók, ha az Ollama rate-limit eléri a kvótát.
  - Új oldal: `concepts/checkpoint-progress.md` (stop-on-error + atomic state + JSONL append-only + resume flag)
  - Frissítve: `runbooks/run-hulu-modell-x.md` (checkpoint-aware script váz)
  - Frissítve: `runbooks/aggregate-results.md` (részleges JSONL-eket is kezeli, `partial: true` jelöléssel)
  - Frissítve: `SCHEMA.md` (tervezési döntések szekció)
  - Frissítve: `index.md` (az új `concepts/checkpoint-progress.md` belinkelve)
- 19:46 — **Futtatható Python scriptek létrehozva a `scripts/` mappában:**
  - `scripts/stop_on_error.py` — Ollama hívás, ami `OllamaFatalError`-t dob nem-tranziens hibánál
  - `scripts/checkpoint.py` — atomi JSON state mentés/betöltés
  - `scripts/download_hulu.py` — HuLU dataset letöltés + standardizálás
  - `scripts/run_hulu.py` — checkpoint-aware HuLU benchmark futtató
  - `scripts/aggregate_results.py` — composite score + riport + heatmap (partial-aware)
  - Mind az 5 script `py_compile` szintaxis-ellenőrzésen átment.
- 19:50 — **Mappastruktúra kiegészítve** futtatható projekt-sémával: `scripts/`, `data/`, `results/`, `state/`, `logs/`, `reports/`. A `hu-eval/README.md` összefoglalja a teljes struktúrát.

## 2026-06-06 (v1.0 — kezdeti feltöltés)

- 12:05 — Státusz kérés a felhasználótól. Elismerve, hogy eddig nem haladtam érdemben, csak tervek születtek (korábbi 2026-06-05 21:09-es üzenet).
- 12:06 — Megkezdem a tényleges munkát. Létrehozva: `SCHEMA.md` (100 sor), `overview.md` (67 sor), `log.md` (üres), `index.md` (üres placeholder).
- 12:06 — Terv: 6 subagent indítása párhuzamosan (stat bench, gen bench, ling tesztek, modellek, runbookok, riport).
- 12:08-12:20 — **6 subagent párhuzamosan fut**, mind a 6 sikeresen befejeződött. Összesen 32 új markdown fájl jött létre (~6500 sor).
- 12:21 — **Első audit:**
  - Üres/rövid fájlok: `index.md` (33 sor, placeholder), `log.md` (18 sor)
  - Törött belső linkek: 47 (ebből 3 false positive, 44 valódi)
  - Frontmatter hiányosságok: 8 fájl
- 12:25 — **Hiányzó runbook pótolva:** `runbooks/debug-modell-nem-valaszol.md` (5. runbook, a runbooks subagent kihagyta).
- 12:27 — **Törött linkek javítása (47 → 1):**
  - 4× `benchmark-hulu.md` → `hulu-benchmark.md`
  - 4× `benchmark-mt-bench-hu.md` → `mt-bench-hu.md`
  - 3× `position-bias.md` → `llm-as-judge.md`
  - 3× `judge-bias.md` → `llm-as-judge.md`
  - 3× `linguistic-benchmarks.md` → `nyelveszeti-osszefoglalo.md`
  - 2× `judge-selection.md` → `llm-as-judge.md`
  - 2× `cloud-vs-local.md` → `cloud-vs-lokal.md`
  - 2× `reproducibility.md` → `llm-as-judge.md`
  - 2× `statistical-benchmarks.md` → `hulu-benchmark.md`
  - 2× `generative-benchmarks.md` → `hugme-benchmark.md`
  - + sok más, kisebb gyakoriságú
- 12:30 — **Végső állapot:** 38 markdown fájl, ~7500 sor, 0 valódi törött belső link.
- 12:32 — **`index.md` véglegesítve** teljes katalógussal (38 oldal, kategóriánkénti bontásban).
- 12:33 — **Végső státuszjelentés** a thread-be.

## 2026-07-10

- 05:42 — **Régi queue kilépett** (PID 291395, "Minden benchmark kész" üzenet). A `gpt-oss:20b-think` HuLU 828/2581-nél maradt, a `nemotron-3-ultra-think` MMLU 879/1500-nél.
- 08:30 — **Riport-készítéskor 6 hiba feltárva**: (1) UD parser 16 cella 0.0% (CoT blokk strip hiányzik + szabad formátum nincs kezelve + 9 vs 10 mezős CoNLL-U); (2) gpt-oss:20b-think HuLU 32% részleges; (3) nemotron-think MMLU 58% rate-limited; (4) MT-Bench judge baseline (deepseek-v4-flash) túl gyenge → 8 modell 100% win; (5) HuLU dedup: 4 modellnél 200 duplikátum (qwen3.5 112+29, gpt-oss-120b 19, nemotron 40); (6) HuGME bíró: 22 modellből 14-nél <100 judged (52-104 a 300 helyett), 6 metrika helyett 1-2.
- 08:42 — **`scripts/reparse_ud.py` + `scripts/rejudge_hugme.py` + `scripts/rejudge_mt_bench.py` + `scripts/dedup_hulu.py` + `scripts/recompute_hulu_summary.py` létrehozva.** UD parser CoT-strip + szabad-formátum regex + 8-mezős tolerancia. Rejudge scriptek: existing_ids check, retry-vel, hosszabb timeout.
- 08:45 — **UD reparse futtatva** 7 modellnél (akiknek van raw_response). Eredmények: deepseek-v4-flash-nothink 0.7034 (volt 0.646), deepseek-v4-pro-nothink 0.5959 (volt 0.445, +34%), kimi-k2.6-nothink 0.6183, glm-5.1 0.3878, glm-5.2 0.4095, qwen3.5 0.3765, nemotron 0.4254.
- 08:50 — **HuLU dedup futtatva**: qwen3.5-nothink 2693→2581 (112 törölve), qwen3.5-think 2610→2581 (29), gpt-oss-120b-nothink 2600→2581 (19), nemotron-think 2621→2581 (40). Summary újraszámítva.
- 08:55 — **3 háttér-futás indítva** (conda eval-hu env): (a) `rejudge_hugme.py` [PID 329060, később megölve], (b) `run_hulu.py gpt-oss:20b-cloud-think` [PID 329061, folytatás 828→2581], (c) `run_mmlu_hu.py nemotron-3-ultra-think` [PID 329062, folytatás 879→1500].
- 09:18 — **Rejudge megölve** (túl sokáig tart, 7 perc alatt 0 item kész — 3 párhuzamos folyamat blokkolta egymást). A HuLU/MMLU kapacitást kap, jelenleg HuLU 878/2581 (9:28 elapsed).
- 11:24 — **HuLU gpt-oss:20b-think befejezve** (2581/2581, 71.41% accuracy, futásidő 27ó 43p).
- 14:59 — **MMLU nemotron-3-ultra-think befejezve** (1500/1500, 91.73% accuracy, futásidő 5ó 14p — javított parser-rel).
- 14:59 — **`post_followup.sh` indítása** (UD refuttatás 13 modell + rejudge-ek + táblázat).

## 2026-07-11

- 08:58 — **`post_followup.sh` első indítása** (a `wait_then_post.sh` várta be a fenti followup-okat) — DE a `gpt-oss-120b:cloud` modell nevet rosszul adta át (kötőjellel a kettőspont helyett), a script 1 item után leállt.
- 09:00 — **`post_followup.sh` modell nevek javítva** (`gpt-oss-120b:cloud` → `gpt-oss:120b-cloud`, ami az Ollama listában van), script újraindítva nohuppal, UD refuttatás elindult (PID 362121, gpt-oss:120b-nothink, 10/449 4p alatt).
- 09:00 — **Státusz riport kész** (`wiki/reports/benchmark-statusz-2026-07-11.md`): 11 modell × 2 mód × 5 benchmark, 24ó outlier-szűrt átlagok, ETA 2026-07-12. 08:00.
- 09:24 — **⚠️ PRIORITÁS VÁLTÁS**: user jelezte, hogy a `gemini-3-flash-preview` bíró modell **3 nap múlva megszűnik**. Új prioritási sorrend: HuGME rejudge → MT-Bench rejudge → UD refuttatás. A `post_followup.sh` és az UD refuttatás **leállítva** (PID 362121 killed).
- 09:24 — **`scripts/priority_judge.sh` létrehozva és elindítva** (PID 363377). A `rejudge_hugme.py` elindult (PID 363386, 22 modell × 300 item × 6 metrika, min-metrics=6, becsült ~4-5 ó). Ezt követi a `rejudge_mt_bench.py` (3 baseline, ~1-2 ó), végül az UD refuttatás (13 modell, ~4-8 ó).

## 2026-07-15

- 01:21 — **Végleges benchmark összesítés kész** (`wiki/reports/eredmeny-osszesites-2026-07-14.md`): 11 modell × 2 mód × 5 benchmark, 97088 item, ~1029 ó futásidő. Top modellek (HuLU+MMLU-HU+HuGME+UD átlaga): qwen3.5-think, deepseek-v4-pro-think, gpt-oss-120b-think (részletek a riportban).
- (később) — **Végleges riport kész a template alapján** (`wiki/reports/report-2026-07-14.md`): 11 modell × 2 mód × 5 benchmark, 40/40/20 composite score (AGENTS.md kötelező), 2 heatmap (stat + gen/ling), composite CSV (22 sor × 13 oszlop). Riport template (`riport-template.md`) bővítve v1.1-re: sebesség/költség törölve, két composite tábla, két heatmap szekció. Runbook (`aggregate-results.md`) frissítve: 5 benchmark (nem 9), MT-Bench multi-baseline, conda `eval-hu` (nem `hu-eval`), bíró modell megszűnés, RETIRED kezelés. Top modell 40/40/20: **deepseek-v4-pro-cloud (nothink) 54.3%**. Top 3: kimi-k2.6 (54.2%), glm-5.2 (52.1%). A qwen3-next:80b RETIRED modell composite = NaN (csak HuLU van).
- (később) — **BASELINE kijelölés**: a `wiki/reports/report-2026-07-14.md` a projekt hivatalos kiindulási alapértéke (baseline) minden jövőbeli benchmark-összehasonlításhoz. A riport fejlécébe beírva a "🎯 BASELINE (alapérték)" jelölés. A korábbi `reports/report.md` (2026-06-12), `hulu-breakdown-2026-06-15/16.md` és `eredmeny-osszesites-2026-07-14.md` **superseded / történeti** státuszúak — a baseline referencia kizárólag a 2026-07-14-es riport.

## 2026-07-18 (v1.3 — wiki aktualizálás a végleges baseline állapotra)

- **Trigger:** user kérése ("frissítsd a wiki-t és aktualizáld"). A filesystem (results/state/logs) naprakész volt 2026-07-14-ig, de a wiki dokumentációs rétege (overview, index, entitás-oldalak, AGENTS.md, README, SCHEMA) még a 2026-06-16 / 2026-07-11 állapotot tükrözte.
- **Végrehajtott wiki változtatások:**
  - `wiki/overview.md` — v1.3-ra frissítve: 11 modell (1 RETIRED) pool + 5 kész benchmark; "bíró státusz" hivatkozások törölve; legfontosabb eredmények (deepseek-v4-pro 54.3% composite győztes) + következő lépések.
  - `wiki/index.md` — dátum v1.3; script-szám 13→19 py + 9 sh; entity szekció 12→13 db (7→12 modell, glm-5.2/gpt-oss-20b/stb. hozzáadva); statisztika 52→58 md, ~10500→~11000 sor; "RETIRED" jelölés.
  - `wiki/entities/` — 7 ÚJ modell-entitás oldal: `deepseek-v4-flash.md`, `deepseek-v4-pro.md`, `glm-5.1.md`, `glm-5.2.md`, `nemotron-3-ultra.md`, `gpt-oss-120b.md`, `gpt-oss-20b.md`, `qwen3.5-cloud.md`. A `kimi-k2.6.md` és `gemini-3-flash.md` átírva a jelenlegi szerepre (kimi = benchmark modell, gemini = megszűnt bíró). A `minimax-m3.md` linkjei javítva. A `qwen3.5-397b.md` elavult név → átirányító oldal (`qwen3.5-cloud.md` a kanonikus). A `qwen3.5-local.md` státusza: még nem futtatták (RTX 4090 terv).
  - `AGENTS.md` — "Jelenlegi állapot" + "Modellnév → mappa" szekciók v1.3-ra frissítve (5 kész benchmark, 11+1 modell pool, `qwen3.5-cloud` helyes név, data/results tele vannak).
  - `README.md` (gyökér) — script-lista bővítve 19 py + 9 sh; `results/{model}-{mode}/` és `state/{model}-{mode}/` formátum.
  - `SCHEMA.md` — wiki fájl-szám 38+1 → 58+, script-szám 5 → 19+9, concept/entity kategóriák v1.3 státusszal.
  - `reports/hulu-breakdown-2026-06-15.md` — 3 törölt PNG (sec_pr/ts_pr/difficulty) linkjei eltávolítva (v1.2.9/v1.2.10 szerint), táblázatok megmaradtak történeti adatként.
  - `concepts/hulu-benchmark.md`, `concepts/checkpoint-progress.md`, `reports/report-2026-07-14.md`, `reports/riport-template.md`, `runbooks/aggregate-results.md` — törött belső linkek javítva (`../runbooks/` prefix, `../reports/` prefix, létező dátum).
- **Lint:** 0 valódi törött belső link a wikiben (a `{args.date}` template változók kihagyva, mert azok a generált riportban helyesek).
- **Megőrzött (preserve):** a `report-2026-07-14.md` baseline státusza, a log 2026-07-11→07-15 bejegyzései, a `qwen3.5-397b.md` átirányító (történeti link-kompatibilitás).

## 2026-07-18 (v1.3.1 — glm-5.2-cloud HuLU per-sub-task bontás kiegészítve)

- **Trigger:** user kérése ("glm-5.2-nél hiányzik a HuCOLA/HuCoPA/HuRTE/HuSST/HuWNLI/HuCB; csináld meg think/nothink módban is, egészítsd ki a baseline report-ot").
- **Ok:** a `report-2026-07-14.md` HuLU per-sub-task táblázatában a glm-5.2-cloud sorok csak "—" helyettesítő értékekkel szerepeltek (a composite oszlopban az overall érték, nothink 75.3% / think 76.0% — ez is csak becsült). A `data/hulu/` mappa üres volt (letöltés hiányzott).
- **Végrehajtott lépések:**
  - `scripts/download_hulu.py` futtatása (HF NYTK: 6 sub-task, 2581 példa → `data/hulu/hulu_std.jsonl`).
  - `scripts/run_hulu.py --model glm-5.2:cloud --mode nothink` → **76.6%** (1964/2565).
  - `scripts/run_hulu.py --model glm-5.2:cloud --mode think` → **75.5%** (1949/2581).
  - Per-sub-task bontás kiszámítva (`hulu_results.jsonl` elemzése):
    - **nothink:** HuCOLA 79.6% / HuCoPA 92.0% / HuRTE 90.1% / HuSST 72.8% / HuWNLI 31.7% / HuCB 72.8%
    - **think:** HuCOLA 81.1% / HuCoPA 95.0% / HuRTE 95.1% / HuSST 68.2% / HuWNLI 6.7% / HuCB 84.5%
- **Riport frissítése** (`wiki/reports/report-2026-07-14.md`):
  - HuLU per-sub-task táblázat: glm-5.2-cloud (nothink/think) sorok kitöltve valós értékekkel, a kompozit szerinti helyes pozícióba rendezve (think a think-szekcióba, nothink a nothink-szekcióba).
  - HuLU overall táblázat: glm-5.2 értékei pontosítva (75.3%→76.6% nothink, 76.0%→75.5% think) "2026-07-18 újramérve" jelöléssel.
  - Lábjegyzet a glm-5.2 sorok alatt: a korábbi "—" helyett valós bontás + HuWNLI think-gyengülés megjegyzés.
  - Change log: új sor (2026-07-18, glm-5.2 per-sub-task kiegészítés).
- **Megfigyelés:** a think mód javítja a HuCOLA/HuCoPA/HuRTE/HuCB-t, de lenullázza a HuWNLI-t (31.7%→6.7%) — konzisztens a többi modell think-profiljával (CoT-zavar). Az overall nothink (76.6%) magasabb, mint a think (75.5%), mert a HuSST (n=1165, domináns súly) think-módban gyengébb (68.2% vs 72.8%).
- **Állapot:** a baseline riport most már teljes glm-5.2 HuLU lefedettséggel rendelkezik (korábban csak a MMLU-HU/HuGME/UD/MT-Bench sorok voltak kitöltve, a HuLU sub-task hiányzott).

## 2026-07-18 (user pref — HuLU per-sub-task konvenció rögzítve)

- **Trigger:** user kérése ("a report-ba a HuLU összesítésen kívül, külön-külön is szeretném látni az eredményeket").
- **Döntés:** állandó riportolási konvencióként rögzítve — a HuLU overall mellett a 6 NLU sub-task (HuCOLA/HuCoPA/HuRTE/HuSST/HuWNLI/HuCB) bontása kötelező, külön táblázatban, minden modellre (nothink + think), "—" helyettesítés tilos.
- **Rögzítve:** `wiki/reports/riport-template.md` HuLU szekciója (KÖTELEZŐ blokk) + `AGENTS.md` Konvenciók szekciója (HuLU riportolási konvenció).

## 2026-07-18 (v1.3.2 — gpt-oss-20b-cloud think HuLU per-sub-task pótlása)

- **Ok:** a `report-2026-07-14.md` per-sub-task táblázatából hiányzott a `gpt-oss-20b-cloud (think)` sor (az eredeti `hulu-breakdown-2026-06-16.md` forrásban is "—" volt, a konvenció szerint tilos "—"-t használni, futtatni kell).
- **Végrehajtás:** `scripts/run_hulu.py --model gpt-oss:20b-cloud --mode think` (a modell neve `gpt-oss:20b-cloud`, nem `gpt-oss-20b-cloud` — 404 után javítva). Cloud timeout miatt 1× resume, majd kész: **71.5%** (1846/2581).
- **Per-sub-task:** HuCOLA 73.6% / HuCoPA 89.0% / HuRTE 91.8% / HuSST 65.6% / HuWNLI 48.3% / HuCB 68.9%.
- **Riport frissítés:** `report-2026-07-14.md` per-sub-task táblázatba beillesztve a `gpt-oss-20b-cloud (think)` sor (71.5% composite, a 20b-nothink 68.9% fölé); overall táblázat 71.4%→71.5% pontosítva "2026-07-18 újramérve" jelöléssel.
- **Állapot:** a HuLU per-sub-task táblázat most már teljes — mind a 11 modell × 2 mód (22 sor) + 2 RETIRED = 24 sor jelen van valós értékekkel, "—" helyettesítés sehol sincs.

## 2026-07-18 (user pref — benchmark-leírás konvenció + kész report)

- **Trigger:** user kérése ("a baseline report-ba mindegyik benchmarkhoz írd le röviden mit tesztel; ezt írd fel magadnak, hogy minden report-ban a rövid leírást bele kell tenned mindegyik benchmarkhoz").
- **Döntés:** állandó riportolási konvenció — minden riportban, minden benchmark-szekció elejére egy rövid (2-4 soros) "**Mit tesztel:**" blokk kötelező, ami leírja milyen képességet mér, milyen formátumban, milyen kimenettel. Nem opcionális.
- **Rögzítve:** `AGENTS.md` Konvenciók (Benchmark-leírás konvenció KÖTELEZŐ) + `wiki/reports/riport-template.md` (minden szekció: HuLU/MMLU-HU/HuGME/MT-Bench-HU/UD Hungarian "Mit tesztel" blokkal).
- **Alkalmazva:** `wiki/reports/report-2026-07-14.md` "Per-benchmark eredmények" szakasz — minden 5 benchmark-szekció (HuLU, MMLU-HU, HuGME, MT-Bench-HU, UD Hungarian) megkapta a rövid leírást.

## 2026-07-18 (user pref — kvantálás konvenció + baseline report)

- **Trigger:** user kérése ("innetől a kvantálást is fel kell venned a report-ba; a jelenlegi modellek ollama-cloud, mert cloud alatt futottak; írd fel, hogy mindig rá kell kérdezni a kvantálásra és a report-ban mindig szerepelnie kell; a baseline report-ba tedd bele az ollama-cloud értéket").
- **Döntés:** állandó riportolási konvenció — minden riportban a modellek kvantálási szintje kötelezően szerepel (külön "Modell-kvantálás" szakasz a fejléc után). Új modell futtatása előtt rá kell kérdezni a kvantálásra; ha Ollama Cloud alatt fut, akkor `ollama-cloud` az érték (nem hagyható üresen).
- **Rögzítve:** `AGENTS.md` Konvenciók (Kvantálás konvenció KÖTELEZŐ) + `wiki/reports/riport-template.md` (Modell-kvantálás szakasz sablonnal).
- **Alkalmazva:** `wiki/reports/report-2026-07-14.md` — "Modell-kvantálás" szakasz hozzáadva, minden 11 modell (1 RETIRED) `ollama-cloud` értékkel.

## 2026-07-18 (user pref — több kvantálás ugyanarra a modellre)

- **Trigger:** user kérése ("készülj fel arra, hogy lesznek olyan modellek, amelyek több kvantálással is lesznek futtatva benchmarkra").
- **Döntés:** egy modell több kvantálással is szerepelhet a riportban — minden (modell × kvantálás) kombináció **külön sor** (külön bejegyzés, külön mappa-útvonal a kvantálással), és a "Modell-kvantálás" szakaszban is külön sor.
- **Rögzítve:** `AGENTS.md` Konvenciók (Kvantálás konvenció kiegészítve: "Több kvantálás ugyanarra a modellre") + `wiki/reports/riport-template.md` (Modell-kvantálás szakasz: több-kvantálás példa).

## 2026-07-18 (fejlesztés — OpenAI-kompatibilis backend támogatása)

- **Trigger:** user kérése ("írd át a kódot, hogy openai api segítségével lehessen benchmark-okat végezni; az ollama tartalmaz kompatibilis api-t, próbáld ki a gpt-oss:20b-cloud modellel").
- **Döntés:** általános OpenAI-kompatibilis backend (`/v1/chat/completions`) támogatása a közvetlen Ollama (`/api/generate`) mellett. Cél: cloud modellek futtatása Ollama `/v1`-en keresztül (átproxizálja őket), később llama-server vagy más OpenAI-kompatibilis szerver ugyanazzal a kóddal. A checkpoint/stop-on-error rendszer SZENT maradt (közös `FatalBackendError` ős).
- **Változások:**
  - `scripts/stop_on_error.py`: új közös ős `FatalBackendError`, `OllamaFatalError` az leszármazottja (visszafelé kompatibilis).
  - `scripts/openai_compat.py` (ÚJ): `call_openai_strict()` — azonos stop-policy, `/v1/chat/completions` formátumban; `think` mód Ollama-n `extra_body["think"]`-on keresztül; válasz `{"response": ...}` alakban (backend-független hívókód).
  - `scripts/run_hulu.py`: `--backend` (ollama/openai), `--base-url`, `--api-key` argumentumok; backend-függő hívás; `except FatalBackendError`; `results/*.jsonl` sorai megkapják a `"backend"` mezőt; Ollama-specifikus meta csak Ollama backendnél íródik.
- **Teszt:** `gpt-oss:20b-cloud --backend openai --base-url http://localhost:11434/v1 --limit 10` → 60/60 prompt, acc=0.633 (38/60). Resume/checkpoint OpenAI backenden is működik (észleli a kész futást, nem fut újra).
- **Rögzítve:** `AGENTS.md` (Parancsok: OpenAI példa + Konvenciók: "Backend konvenció KÖTELEZŐ a riportban").

## 2026-07-18 (user pref — git commit message konvenció)

- **Trigger:** user kérése ("git commit és push, a commit message mindig azt tartalmazza, amit csináltunk. Ezt jegyezd fel magadnak").
- **Döntés:** állandó konvenció — **minden git commit message LEÍRJA, hogy mit csináltunk** (mit változtattunk/miért), tömör és leíró formában. A message az adott munkamenet tényleges tartalmát tükrözze, ne általános ("update" / "fix" / "wip" tilos).
- **Rögzítve:** `wiki/log.md` user-pref bejegyzésként. (Javasolt később AGENTS.md "Git munkafolyamat" szekciójába is bevenni.)

## 2026-07-19 (v1.3.4 — openai-backend támogatás a 4 run scriptben, lokális Qwen3-Next-80B IQ3_XXS)

- **Trigger:** user kérése — "másik gépen megvolt az összes dataset, git-be felkerült a szükséges leírásokkal együtt. Szedd le és merge-eld össze a jelenlegi módosításokkal. A script-eket úgy módosítsd, hogy ezt datasets-et használják", majd "lokálisan indítottam llama-server segítségével egy qwen3-next modellt... az összes benchmarkot csináld végig és a végén report-ot egészítsd ki".
- **Megvalósítva (scriptek):**
  - `scripts/run_mmlu_hu.py`, `scripts/run_hugme.py`, `scripts/run_mt_bench_hu.py`, `scripts/run_ud_hungarian.py` — kiterjesztve a `--backend {ollama,openai}` + `--base-url` + `--api-key` kapcsolókkal; a `run_hulu.py` mintáját követve. A `call_ollama_strict` / `call_openai_strict` dispatch a `run_benchmark` függvényben, közös `except FatalBackendError as e:` ág. A JSONL-be bekerült a `"backend"` mező minden sorban.
  - `scripts/openai_compat.py` — a 45969ca commit (2026-07-19 14:14) által hozzáadott `call_openai_strict` modul, a `stop_on_error.py` `FatalBackendError` közös ősével.
  - **Git pull:** 3 új commit jött le az `origin/main`-ről (45969ca openai backend support, 2cb0bb9 datasets/ mappa offline, ba7265c datasets/ verziókövetés). A lokális 4 script-módosítás (stash + pop) konfliktus nélkül mergelve.
  - **Smoke teszt:** mind az 5 benchmarkból 1-1 prompt a llama-server `http://localhost:8080/v1` felé, mindkét módban — minden parser működik, a JSONL-be `"backend": "openai"` kerül. A gondolkodó modell néha `finish_reason: length`-et produkál (a `num_predict=4096` nothink limit kevés a gondolkodásnak) — ez a riportban jelzett limitáció.
  - A `datasets/` → `data/` másolás (a `wiki/runbooks/setup-kornyezet.md` 6. szakasza alapján) — minden 5 dataset elérhető a scriptek által várt útvonalon.
- **Megvalósítva (wiki, Fázis 3):**
  - **Új** `wiki/concepts/openai-backend-support.md` — a két backend (ollama / openai) részletes leírása, CLI kapcsolók, stop-policy, think flag viselkedése, JSONL formátum, mikor melyiket.
  - **Új** `wiki/runbooks/run-modell-x-openai-backend.md` — lépésről lépésre runbook: végpont-ellenőrzés, smoke teszt, teljes futtatás, judge hívás, aggregáció, riport-kiegészítés, gyakori buktatók.
  - `wiki/concepts/checkpoint-progress.md` — kiegészítve az OpenAI-backend lábjegyzettel + a közös `FatalBackendError` ős említésével; "Tipikus használat" szakasz kiegészítve az openai példával.
  - `wiki/reports/riport-template.md` — a **Modell-kvantálás** táblázat **Backend** oszloppal bővítve (értékei: `ollama` / `ollama-cloud` / `openai`); a v1.1.1 changelog bejegyzés; az OpenAI-backend specifikus limitációk a Limitációk szakaszban; új "Kapcsolódó" linkek.
  - `wiki/comparisons/cloud-vs-lokal.md` — a korábbi "minden modell cloud" megállapítás pontosítva; új "Lokális benchmark-modell" alszakasz a Qwen3-Next-80B-Thinking IQ3_XXS lokális referenciával (architektúra, kvantálás, backend, limitációk).
  - `wiki/runbooks/setup-kornyezet.md` — `requirements.txt` mint kanonikus telepítési mód (A) szakasz), a `deepeval` opcionális jelzése (B) szakasz), "5. Végpont(ok) elérhetősége" kiegészítve az openai backend ping-gel; D) és E) buktatók a deepeval opcionális státuszához igazítva.
  - `wiki/index.md` — 3 új link bejegyzése (concept + runbook + lokális modell-referencia a cloud-vs-lokal-ban); statisztika frissítés (v1.3.4).
  - **Megőrzött (preserve):** a meglévő v1.2-v1.3.3 bejegyzések és a kanonikus leíró oldalak tartalma — csak kiegészítés, nem felülírás.
- **Modellnév-mappa konvenció:** `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` → `unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-{nothink|think}` (a `model.replace(":", "-").replace("/", "-") + f"-{mode}"` szabály szerint).
- **Következő fázis (Fázis 1, jelenleg szünet):** a teljes 5×2 benchmark-szett futtatása (~60-100 ó a llama-server egyszálúsága miatt) + judge-ok + `aggregate_results.py` + a `wiki/reports/report-2026-07-19-lokális-qwen3-next.md` riport elkészítése. A felhasználó indítja a saját felügyeletével, a Fázis 0-ás smoke tesztek már igazolták, hogy minden parser és a dispatch működik.

## 2026-07-19 (user pref — conda env `eval-hu` pótlása + `requirements.txt` rögzítése)

- **Trigger:** user kérése a munkafolyamat során — "ha nincs hu_eval conda python környezet, akkor csináld meg. Ehhez csináljl egy requirements.txt-t hogy később könnyen bármikor fel tudd a környezetet építeni, ezt is jegyezd fel magadnak későbbi futtatáspok miatt".
- **Döntés:** állandó konvenció — a `hu-eval` projekt futtatásához **conda env `eval-hu`** (Python 3.11) kötelező. A függőségek a projekt gyökerében lévő **`requirements.txt`**-ben vannak deklarálva; a telepítés kanonikus módja `pip install -r requirements.txt` (az env aktiválása után).
- **Megvalósítva:**
  - `requirements.txt` a projekt gyökerében, tartalma: `requests`, `pandas`, `matplotlib`, `numpy`, `datasets`. A `deepeval` és `ollama` Python kliens opcionális (a scriptek `requests`-szel hívnak, saját judge implementáció van).
  - `conda create -n eval-hu python=3.11 -y` + `pip install -r requirements.txt` — a `Python 3.11.15` környezet kész, minden csomag importálható.
  - A `wiki/runbooks/setup-kornyezet.md` kiegészítve: "A) `requirements.txt` használata (ajánlott)" szakasz, a `deepeval`/`ollama` opcionális jelzése, a 3/A (Csomagok telepítése) szakasz refaktorálva.
  - A meglévő `datasets/` mappa + a `cp -r datasets/* data/` lépés a `data/` mappa kitöltéséhez (5 benchmark dataset, ~6.5 MB).
- **Rögzítve:** `wiki/log.md` (user-pref) + a `setup-kornyezet.md` canonicalizálva. A jövőbeli ügynök- és emberi futtatáshoz a kanonikus parancs: `conda activate eval-hu && pip install -r requirements.txt`.

## 2026-07-19 (felhasználó kérés — datasets/ mappa létrehozása)

- **Trigger:** user kérése ("a projekt mappában hozz létre egy datasets mappát és az összes benchmark dataset-jét másold oda, valamint wiki-be ezt jegyezd fel, hogy másik gépen tudjuk használni").
- **Megvalósítva:**
  - `datasets/` mappa létrehozva a projekt gyökerében, tartalma: `hulu/`, `mmlu_hu/`, `hugme/`, `mt_bench_hu/`, `ud_hungarian/` (5 benchmark, összesen ~6.5 MB, 7 fájl). Forrás: `/home/openclaw/.openclaw/wiki/hu-eval/data/`.
  - `.gitignore` kiegészítve `datasets/` sorral (nem verziókövetett — átvihető, de nem forrás).
  - `wiki/runbooks/setup-kornyezet.md` kiegészítve "6. Datasetek előkészítése (offline másolás)" szekcióval — leírja a `datasets/` → `data/` másolás/symlink módját és az online letöltési alternatívát.

## 2026-07-14

- 20:14 — **`priority_judge.sh` BEFEJEZŐDÖTT**. A teljes pipeline kész: 11 modell × 2 mód × 5 benchmark, 97088 item feldolgozva, ~1029 ó futásidő. Az utolsó UD think modell (qwen3.5:cloud) 449/449-re futott le. A `build_status_table.py` is lefutott, státusz táblázat frissítve. A `priority_judge.sh` és a `watchdog_priority.sh` kiléptek.

## 2026-07-13

- 09:11 — **`priority_judge.sh` indítása** (PID 413400). Marker fájl skip-pel a HuGME és MT-Bench rejudge kimaradt (már kész), csak az UD refuttatás fut. 3 nothink modell: gpt-oss:120b, gpt-oss:20b, minimax-m3. 10 think modell: deepseek-v4-flash/pro, glm-5.1/5.2, gpt-oss:120b/20b, kimi-k2.6, minimax-m3, nemotron-3-ultra, qwen3.5.

## 2026-07-08

- 07:49 — **`gpt-oss:20b-cloud-think` skip-policy eltávolítva** (user kérésére). Mindhárom runner scriptből kivéve: `queue_all_benchmarks.sh:39-43`, `queue_runner.sh:34-38`, `phase2_runner.sh:58-62`. A queue következő újraindításakor (vagy manuális indításnál) a modell think módban is lefut mind az 5 benchmarkon. Becsült plusz idő: 5 benchmark × ~3ó/think = ~15 ó.

## 2026-06-05 (tegnap)

- 22:23 — Wiki váz mappastruktúra létrehozva (`raw/`, `wiki/`, `wiki/{concepts,entities,comparisons,runbooks,reports}/`).
- 21:09 — Első terv üzenet elküldve a thread-be.
- 21:11 — Felhasználó: "mindent csinálj meg, végén ellenőrizd, óránként státuszt kérek".
- 19:53 — Eredeti kérés: terv készítése a magyar nyelvi benchmark suite-hoz.

## 2026-07-25 (teljes think futtatás + riport — lokális Qwen3-Next-80B IQ3_XXS; nincs nothink mód)

- **Trigger:** az `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` modell (3.06 bpw, 32.95 GB) teljes 5×1 benchmark futtatása llama-server backenddel (`http://localhost:8080/v1`, OpenAI-kompatibilis).
- **Futtatási stratégia:** soros (nem párhuzamos), a llama-server egyszálú volta miatt. Sorrend: HuLU → MMLU-HU → HuGME → HuGME judge → MT-Bench-HU → MT-Bench-HU judge → UD Hungarian.
- **Backend:** `--backend openai --base-url http://localhost:8080/v1`. Timeout 300s (nothink). Judge modellek: `deepseek-v4-pro:cloud` (bíró), `deepseek-v4-flash:cloud` (MT-Bench baseline).
- **Eredmények (nothink, mind kész):**

| Benchmark | Score | Megjegyzés |
|-----------|------:|------------|
| HuLU | 56.53% (1459/2581) | Per-sub-task: HuCOLA 51.5%, HuCoPA 90.0%, HuRTE 72.8%, HuSST 57.0%, HuWNLI 13.3%, HuCB 49.5% |
| MMLU-HU | 86.87% (1303/1500) | Erős eredmény a kvantáláshoz képest |
| HuGME | 0.828 (300/300) | Judge: deepseek-v4-pro:cloud |
| MT-Bench-HU | 37.50% (1W/7L/16T) | Baseline: deepseek-v4-flash:cloud. Magas döntetlen-arány (66.7%) |
| UD Hungarian | **N/A** | A thinking modell CoT-re használja a kontextust (n_ctx=16128). 64K-ra emelve a modell már produkál CoNLL-U kimenetet. |

- **Mód tisztázás (2026-07-25):** a modell a llama-server `reasoning_format: none` beállítása ellenére minden promptnál gondolkodik. A korábban "nothink"-ként jelölt eredmények valójában think eredmények — a modellnek nincs nothink módja. A dokumentációt és a riportot frissítettük: minden "nothink" → "think".
- **Aggregáció:** `scripts/aggregate_results.py` futtatva csak nothink adatokkal → composite **0.659** (40/40/20 súlyokkal, STAT 71.70%, GEN 60.17%, LING N/A → súlyok 50/50-re osztva).
- **Riport:** `wiki/reports/report-2026-07-25-lokalis-qwen3-next.md` létrehozva (think-only, UD limitáció dokumentálva, 40/40/20 composite).
- **Generált fájlok:** `reports/composite_scores.csv`, `reports/report.md`, `reports/results_heatmap.png` (mind csak ezt az egy modellt tartalmazzák).
- **Megfigyelések:**
  - A Qwen3-Next-80B thinking modell **nem használható** UD Hungarian benchmarkra — a CoT minden promptnál kimeríti a kontextusablakot.
  - A HuWNLI sub-task 13.3%-a kiemelkedően gyenge (random guess szint).
  - A HuCoPA 90.0%-os eredménye kiemelkedő (a CoT itt ténylegesen segít).
  - Az OpenAI backend `reasoning_format: none` és a llama-server `chat_template` miatt a nothink és think mód érdemben nem különbözik — a modell minden promptnál gondolkodik.

## 2026-07-19 (v1.3.3 — bíró modell váltás: gemini-3-flash-preview → deepseek-v4-pro:cloud)

- **Trigger:** user döntése — a `gemini-3-flash-preview:latest` bíró modell 2026-07-14. 09:00 CEST óta nem elérhető (Ollama megszűnés), a már letesztelt modellek közül a baseline riport és a `llm-as-judge.md` preferencia-sorrend (`gemini > deepseek-v4-pro`) alapján a `deepseek-v4-pro:cloud` a legalkalmasabb utód.
- **Végrehajtott változtatások (scripts/):**
  - `scripts/judge_hugme.py` — `JUDGE_MODEL = "gemini-3-flash-preview:latest"` → `"deepseek-v4-pro:cloud"` (L23), docstring frissítve.
  - `scripts/judge_mt_bench.py` — `JUDGE_MODEL` ugyanaz (L23), docstring frissítve. A `BASELINE_MODEL = "deepseek-v4-flash:cloud"` változatlan (ez a GSB összehasonlítási alap, nem a bíró).
  - `scripts/run_hugme.py` — docstring frissítve (L6).
  - `scripts/rejudge_hugme.py` / `rejudge_mt_bench.py` — NEM kell módosítani, importálják az új `JUDGE_MODEL`-t.
  - `scripts/priority_judge.sh` / `queue_runner.sh` — komment/echo frissítve (gemini → deepseek-v4-pro:cloud).
  - `python -m py_compile` ellenőrizve: OK. Ollama szerveren a `deepseek-v4-pro:cloud` elérhető (FP8, 1.6T paraméter, 524288 kontextus).
- **SZENT SZABÁLY rögzítve (self-bias):** a mindenkori bíró modell NEM értékelheti saját magát. Mivel a `deepseek-v4-pro` is benchmark-modell, a saját HuGME/MT-Bench-HU sorait nem szabad saját magával pontozni — ezeket független bíróval (pl. `qwen3.5:cloud` vagy `glm-5.2:cloud`) vagy a self-bias szabály szerinti kivételzéssel kell kezelni. Rögzítve: `wiki/concepts/llm-as-judge.md` (§4 Self-bias + "Melyik bíró modellt mikor?" táblázat + "Frissítve" fejléc).
- **Végrehajtott változtatások (wiki/):**
  - `concepts/llm-as-judge.md` — bíró-sorrend (`gemini megszűnt > deepseek-v4-pro hivatalos bíró`), self-bias SZENT szabály kifejtve, "Melyik bíró modellt mikor?" táblázat frissítve (minden sor `deepseek-v4-pro:cloud`), fejléc dátum 2026-07-19.
  - `reports/report-2026-07-14.md` — fejléc "Bíró modell" (L19) + lábjegyzet (L41) frissítve deepseek-v4-pro:cloud-ra + self-bias korlát.
  - `entities/gemini-3-flash.md` — státusz: "helyette deepseek-v4-pro:cloud a hivatalos bíró (2026-07-19)", kapcsolódás frissítve.
  - `reports/riport-template.md` — bíró modell lábjegyzet frissítve (jövőbeli riportok sablonja).
  - `overview.md` — modell-pool táblázat: gemini sor "judge (megszűnt)" → helyette deepseek hivatkozás.
  - `concepts/hugme-benchmark.md` — bíró prioritási sorrend (1. deepseek-v4-pro, 2. független bíró self-bias-ra, 3. gemini backup megszűnt) + SZENT self-bias szabály.
  - `concepts/mt-bench-hu.md` — bíró költség szakasz frissítve.
  - `entities/kimi-k2.6.md` — bíró pool hivatkozás: deepseek-v4-pro:cloud (2026-07-19).
  - `runbooks/llm-judge-prompt-template.md` — példakód `JUDGE_DEFAULT` + `--judge-model` példák deepseek-v4-pro:cloud.
  - `runbooks/aggregate-results.md` — bíró modell (v1.1), num_judged mező, hibakereső táblázat, "Új bíró modell" szakasz frissítve.
  - **Megőrzött (preserve):** a történeti riportok (`benchmark-statusz-*`, `eredmeny-osszesites-2026-07-14`) és a `log.md` 2026-06-07/2026-07-11 bejegyzései — ezek akkori állapotot rögzítenek, nem módosítjuk (csak a kanonikus leíró oldalakat és a jövőbeli riport sablonját).
- **Következmény:** a régi gemini-3-flash-preview HuGME/MT-Bench eredmények nem reprodukálhatók; a HuGME és MT-Bench-HU benchmarkokat újra kell futtatni a `deepseek-v4-pro:cloud` bíróval (a deepseek saját sorai független bíróval). A `rejudge_hugme.py` és `rejudge_mt_bench.py` scriptek készen állnak.

## 2026-07-27 (v1.5 — UD Hungarian v4 benchmark: Qwen3-Next-80B IQ3_XXS think, 128K kontextus)

- **Trigger:** lokális Qwen3-Next-80B-A3B-Thinking GGUF UD-IQ3_XXS modell UD Hungarian benchmarkjának befejezése.
- **Kontextus:** a modell thinking-only (nincs nothink mód), 128K kontextus, llama-server `-c 131072 -ctk q5_1 -ctv q5_1 --port 8080 --no-mmap --parallel 1 -fa on --op-offload -t 20`.
- **Dataset:** `data/ud_hungarian/ud_hungarian_v4.jsonl` — v4 prompt: explicit CoNLL-U 10 oszlop leírás + példa mondat ("A macska az asztalon alszik.") + "CSAK a táblázatot add meg" utasítás. Alapvetés: a modell nem ismeri a CoNLL-U formátumot, ezért részletesen le kell írni.
- **Script:** `scripts/run_ud_v3.py` — v4 dataset, 128K kontextus, `max_tokens=65536`, 1800s timeout/mondat, streaming, checkpoint+resume. CLI args: `--model`, `--base-url`, `--max-time`, `--reset`.
- **Eredmények (449 mondat, 437 feldolgozva, 12 skip/timeout):**
  - Composite (UPOS+UAS+LAS)/3: **0.6473**
  - UPOS: **0.7936** (átlag, csak értelmezhető mondatokon 0.8218)
  - UAS: **0.6314** (átlag, csak értelmezhető mondatokon 0.6523)
  - LAS: **0.5170** (átlag, csak értelmezhető mondatokon 0.5578)
  - 34 mondat UPOS=100%, 32 mondat UPOS<50%
  - Átlagos reasoning: 27118 karakter, átlagos idő: 325s/mondat
  - Összes futásidő: ~45.4 óra
  - Finish reason: 436 stop, 1 length
- **Fájlok:**
  - `scripts/prepare_ud_v3.py` — v4 dataset generátor
  - `scripts/run_ud_v3.py` — v4 runner (CLI args, review hibák javítva)
  - `data/ud_hungarian/ud_hungarian_v4.jsonl` — 449 mondat, v4 prompt
  - `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-think/ud_hungarian_results.jsonl` — 437 eredmény
  - `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-think/ud_hungarian_summary.json` — aggregált eredmény
  - `state/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-think/ud_hungarian_v4.json` — checkpoint
- **AGENTS.md frissítve:** "Soha ne állítsd le a lokális AI szervert!" szabály hozzáadva.

## 2026-07-28 (v1.6 — Összevont riport: 11 cloud baseline + 1 lokális modell)

- **Trigger:** Qwen3-Next-80B IQ3_XXS lokális modell eredményeinek beolvasztása a 2026-07-14 baseline riportba.
- **Változtatások:**
  - `reports/report-2026-07-14.md` — Qwen3-Next-80B IQ3_XXS (lokális, think) hozzáadva MINDEN benchmark táblázathoz (HuLU, MMLU-HU, HuGME, MT-Bench-HU, UD Hungarian, Composite A+B). HuGME/MT-Bench-HU skála-különbség lábjegyzetekkel jelölve. Modell-kvantálás táblázat kiegészítve. Frissítve: 2026-07-28.
  - `reports/composite_scores-2026-07-27.csv` — UD adatokkal kiegészített CSV.
  - `reports/report-2026-07-27-lokalis-qwen3-next.md` — végleges önálló riport (Karpathy módszer).
- **Megjegyzés:** a HuGME és MT-Bench-HU eredmények skálái nem közvetlenül összehasonlíthatóak a cloud modellekkel (0–100% vs. 0–10% HuGME, single-baseline vs. multi-baseline MT-Bench). A STAT és LING dimenziók viszont közvetlenül összehasonlíthatóak.
- **Git:** változtatások stagelve, commit kérésre.

## 2026-10-17 (v1.7 — új gép setup: uv venv + corpora, conda nélkül)

- **Trigger:** user kérése — új gépen (linux) még csak a git repo van clone-ozva; a Python környezet `uv`-val épüljön fel, a corpusok legyenek beállítva egy új teszteléshez.
- **Végrehajtva (környezet):**
  - `uv venv --python 3.11 .venv` (CPython 3.11.17, uv 0.13.1) + `uv pip install --python .venv/bin/python -r requirements.txt` → 43 csomag (requests, pandas 3.0.6, matplotlib 3.11.2, numpy 2.4.6, datasets 5.1.0).
  - Mind az 5 runner + 2 judge + aggregator + segédmodulok importálhatók a `.venv`-ből.
  - `.gitignore` kiegészítve `.venv/`-vel.
- **Végrehajtva (corpora):** `mkdir -p data && cp -r datasets/* data/` (a `datasets/` 2026-07-19 óta a repo része); `python scripts/prepare_ud_v3.py` → `data/ud_hungarian/ud_hungarian_v4.jsonl` (449 mondat). Rekordszámok ellenőrizve: HuLU 2581, MMLU-HU 1880, HuGME 300, MT-Bench-HU 24, UD std 449, UD v4 449.
- **Végrehajtva (scriptek):** a 6 shell orchestrator (`queue_runner.sh`, `queue_all_benchmarks.sh`, `phase2_runner.sh`, `post_followup.sh`, `priority_judge.sh`, `watchdog_priority.sh`) interpreter-feloldása: `PYTHON` env > conda `eval-hu` > projekt `.venv`; a `/tmp/opencode/build_status_table.py` helper hiányában a státusz-táblázat lépés kihagyva (nem része a repónak). `bash -n` syntax check OK.
- **Smoke teszt:** `run_hulu.py --model deepseek-v4.1-flash:cloud --limit 1` (6 prompt, 1/task) → 6/6 lefutott, acc=0.333 (2/6), state `completed`, results JSONL 6 sor (`backend: ollama`, ollama meta mezők). Az Ollama szerver (localhost:11434) elérhető, a cloud modellek mennek. A smoke artifactok (state/results/log) kitakarítva — tiszta lappal indulhat az éles futás.
- **Megfigyelés (pre-existing viselkedés, nem változtatva):** a `--limit`-es futás a végén `completed` státuszba kerül; az utána indított teljes futás `--reset` nélkül „már kész" üzenettel kilép. Smoke teszt után a teljes futást `--reset`-tel kell indítani.
- **Wiki frissítve:** ez a bejegyzés + `runbooks/setup-kornyezet.md` (v1.7: uv szakasz, `datasets/` verziókövetett, UD v4 prepare lépés, checklist); `README.md` gyors indulás (uv alternatíva); `AGENTS.md` Környezet szekció (uv bullet).

## 2026-10-17 (v1.7.1 — bíró modell váltás: deepseek-v4-pro:cloud → deepseek-v4-pro:0813-cloud)

- **Trigger:** user döntése — a hivatalos bíró modell mostantól a `deepseek-v4-pro:0813-cloud` (Ollama Cloud, 1.65T param, FP8, 1M kontextus, thinking/tools). Az előző hivatalos bíró a `deepseek-v4-pro:cloud` volt (2026-07-19, v1.3.3 óta).
- **Éles teszt (a projekt saját judge-útján, frissített konstanssal):** HuGME `judge_response` (num_predict=16, think=False) → 1.0; MT-Bench GSB normál + swap → A / A (konzisztens, pozíció-független); nyers hívás `done_reason=stop`, 4 token, ~0.6s. A `think=False` elnyomja a gondolkodást, a regex score-kinyerés hibátlanul működik.
- **Kód:** `scripts/judge_hugme.py` + `scripts/judge_mt_bench.py` — `JUDGE_MODEL = "deepseek-v4-pro:0813-cloud"` (+docstring). A `rejudge_hugme.py` / `rejudge_mt_bench.py` a konstanst importálja → automatikusan az új bírót használja. `scripts/run_hugme.py` és `scripts/rejudge_mt_bench.py` docstring frissítve. `py_compile` OK.
- **Shell orchestratorok:** `priority_judge.sh` (komment + 3 echo) és `queue_runner.sh` (komment) frissítve; `bash -n` OK. A baseline listák (`deepseek-v4-pro:cloud` a GSB baseline-okban) és a benchmark pool (`queue_all_benchmarks.sh`, `phase2_runner.sh`, `post_followup.sh`) VÁLTOZATLAN — azok nem bíró-hivatkozások.
- **AGENTS.md:** a judge parancs kommentje frissítve `deepseek-v4-pro:0813-cloud`-ra (a régi `gemini-3-flash-preview` hivatkozás elavult volt).
- **Wiki frissítve:** `concepts/llm-as-judge.md` (fejléc + sorrend + "Melyik bíró modellt mikor?" táblázat + self-bias), `concepts/hugme-benchmark.md`, `concepts/mt-bench-hu.md`, `concepts/szabad-kerdes-hu.md`, `concepts/tobbi-benchmark-modszere.md`, `entities/gemini-3-flash.md`, `entities/kimi-k2.6.md`, `overview.md`, `comparisons/cloud-vs-lokal.md`, `comparisons/modell-vs-modell.md`, `runbooks/llm-judge-prompt-template.md`, `runbooks/aggregate-results.md`, `runbooks/run-modell-x-openai-backend.md`, `reports/riport-template.md` (lábjegyzet + v1.1.2 changelog).
- **Preserve (NEM érintve):** a történelmi riportok (`reports/report-2026-07-14.md` — a `report.md` symlink célpontja —, `reports/report-2026-07-25/27*.md`, `benchmark-statusz-*`, `eredmeny-osszesites-*`) bíró-hivatkozásai a régi bírót (`deepseek-v4-pro:cloud`) tükrözik — azokat az eredményeket ténylegesen azzal (vagy a még korábbi gemini-vel) pontozták.
- **Self-bias SZENT szabály:** a bíró a `deepseek-v4-pro` családból való, és a `deepseek-v4-pro:cloud` benchmark-modellként szerepel a poolban → a deepseek-v4-pro saját HuGME/MT-Bench-HU sorait továbbra is független bíróval kell pontozni.
- **Következmény:** a jövőbeni generatív judged eredmények bírója `deepseek-v4-pro:0813-cloud`; a meglévő eredmények provenance-e változatlan (rejudge csak kérésre).


## 2026-10-22 (v1.8 — cloud kör: minimax-m3.1-flash / mistral-large-4 / muse-spark-open; heti kvóta 90% → leállás)

- **Trigger:** a 2026-10-20-án indított cloud kör folytatása (minimax 2 napos ingyenes ablak → mistral befejezés → muse), majd a heti Ollama Cloud kvóta 90%-ánál a felhasználó kérésére leállítás; kérés: „addig is report, melyik modell milyen eredményt ért el”.
- **Végrehajtva (modell-státusz):**
  - `minimax-m3.1-flash:cloud` — **8/8 run + 4/4 bíró** (UD mindkét módban kihagyva).
  - `mistral-large-4:cloud` — **10/10 run + 4/4 bíró** (UD-think a streaming wrapperrel fejeződött be 449/449-re).
  - `muse-spark-open:cloud` — **5/10 run + 2/4 bíró**; a nothink kör teljes (hulu 77,06%, mmlu 91,40%, hugme 0,9054, mt_bench 0,5625, ud UPOS 0,8756/UAS 0,7858), a think körből csak a HuLU indult el (871/2581, csak HuCoLA 79,8%).
  - `deepseek-v4.1-flash:cloud` referencia (10/10) változatlan.
- **Composite (40/40/20):** muse-no **0,781** > minimax-th 0,726 > minimax-no 0,703 > mistral-no 0,699 > deepseek-no 0,650 > mistral-th 0,636 > deepseek-th 0,635. A muse-think még N/A.
- **Kvóta-események:** 2026-10-22 03:59–05:15 `http_429 session usage limit` (globális fiók-limit) — supervisor 15 perces próbákkal, 05:15-kor automatikus resume (muse ud-no 373 → 449, adatvesztés nélkül); 08:24-kor a heti kvóta 90%-ánál kézi leállítás (orchestrator + supervisor + futó lépés), checkpointok érintetlenek.
- **Módszertani megjegyzések (reportban részletesen):** (1) minimax UD kihagyva — a modell `think=False` mellett is reasoningol, hosszú mondatoknál üres válasz minden tokenbüdzsén; (2) a think lépések `/tmp/opencode/run3/stream_patch.py` streaming wrapperrel futottak a 60 s-os proxy-502 ellen (projekt `scripts/` változatlan); (3) az üres válaszok nem lettek újrafuttatva, csak dokumentálva; (4) **MMLU-HU duplikátum:** a forrás minden kérdést kétszer tartalmaz (1880 sor / 940 egyedi; eval 1500 sor / 750 egyedi), ezért a resume-elt futásoknál a sorszámok eltérnek (1500 / 1392 / 793) — dedup + újrafuttatás döntés a jövő hétre; (5) a runner „las” mezője valójában DEPREL-pontosság, nem joint LAS.
- **Wiki frissítve:** új [reports/report-2026-10-22.md](reports/report-2026-10-22.md) (teljes riport, kötelező benchmark-leírásokkal, HuLU sub-task táblával, kvantálás/backend szakasszal); `reports/report.md` symlink átállítva erre; aggregátor kimenet újragenerálva (`reports/report.md`, `reports/composite_scores.csv`, `reports/results_heatmap.png`); ez a log-bejegyzés.
- **Következő hét:** muse-think hátralévő 5 run + 2 bíró; MMLU-HU dedup döntés; a composite és a symlink újraszinkronizálása a muse-think lezárása után.

## 2026-10-22 (v1.8.1 — UD-think diagnózis: nem kommunikációs hiba, hanem tokenbudget + parser-elcsúszás)

- **Trigger:** felhasználói észrevétel — a think módú UD eredmények (UPOS ~0,10) jóval rosszabbak a nothinknél, pedig fordítva kellene; „mintha nem jönne meg a válasz”.
- **Ok 1 (fő ok) — tokenbudget:** a `run_ud_hungarian.py` think módban `num_predict=8192`-t használ; a modellek a CoNLL-U előtt hosszú angol reasoningot generálnak. Élő próba (mistral, 25 tokenes mondat, streaming): 2048 → `done_reason=length`, 0 char válasz; 8192 → `length`, 8192 token, 24 669 char thinking, 0 char válasz; **16 384 → `stop`, 13 463 token, 1 403 char válasz**; 32 768 (68 tokenes mondat) → `stop`, 24 490 token, 2 995 char válasz. Az üres-arány hossz szerint 10–12% / 68–71% / 97–99% (rövid/közepes/hosszú) — tiszta budget-mintázat, nem timeout.
- **Ok 2 — parser-elcsúszás:** a parser 10 oszlopos CoNLL-U-t feltételez (HEAD=parts[6]); a think válaszok 7–9 oszloposak → HEAD/DEPREL 0. Ugyanez rontotta a deepseek **nothink** UAS-t (tárolt 0,0823 → újraszámolva 0,4622).
- **Javított újraszámolás** (robusztus parser, megválaszolt részhalmaz): deepseek-think UPOS 0,922 / UAS 0,877 / DEPREL 0,710 (89 item) vs nothink 0,779/0,462/0,516; mistral-think 0,867/0,829/0,642 (101 item) vs nothink 0,761/0,439/0,512; muse-nothink 0,901/0,814/0,618. **A think tehát jobb, amikor válaszol** — a tárolt think-pontszámok érvénytelenek; a részhalmaz a rövid mondatok felé torzít, ezért benchmarkként nem használható.
- **Költség:** 32k budget mellett 167–276 s/item → 449 item ≈ 25–30 óra és ~9M token modellenként. Javaslat: UD nothink-only (dokumentáltan) vagy think-újrafuttatás 32768-cal külön kvótaablakban; a parser-javítás viszont indokolt. Projekt `scripts/` egyelőre **változatlan** (felhasználói jóváhagyásra vár).
- **Wiki frissítve:** `reports/report-2026-10-22.md` — új „UD-think diagnózis” szakasz, a UD-táblázat érvénytelenségi figyelmeztetéssel; ez a log-bejegyzés.
- **Helperék (nem repo):** `/tmp/opencode/run3/ud_reparse.py`, `/tmp/opencode/run3/probe_ud_think.py`.

## 2026-10-22 (v1.8.2 — token-plafon eltávolítása: a modell azt használja, amit tud)

- **Felhasználói döntés:** „Ne legyen token limit, amit az adott modell tud, az legyen használva.” A benchmarkok 2026-10-22-től nem szabnak `num_predict` plafont.
- **Megvalósítás:** minden runner (`run_hulu`, `run_mmlu_hu`, `run_hugme`, `run_mt_bench_hu`, `run_ud_hungarian`) `num_predict=-1`-et ad; a `stop_on_error.py` defaultja is -1. A `judge_mt_bench` baseline-generálása szintén -1 (a bírói score-kinyerés szándékosan limitált: 8/16/24 token).
- **Cloud-korlát fordítás:** a cloud API a -1-et `400 max_tokens must be positive` hibával utasítja el. Ezért a `resolve_num_predict()` a -1-et a modell tényleges max output token korlátjára fordítja (egyszeri, tokent nem generáló próbakérés 400-as hibaüzenetéből, cache-elve). Mért értékek: **muse-spark-open 1 048 576; minimax-m3.1-flash 524 288; deepseek-v4.1-flash 393 216; mistral-large-4 262 144**; lokális modellnél -1 marad (természetes stop / num_ctx).
- **Időkorlátok:** nothink 900 s, think 3600 s; a streaming wrapper teljes item-idő védőkorlátja `RUN3_MAX_ITEM_SECONDS` (alap 5400 s), hogy egy végtelen ciklus ne égesse a kvótát. Az OpenAI-kompatibilis backendnél negatív `num_predict` = a `max_tokens` mező elhagyása.
- **Élő validáció:** mistral UD think, 25 tokenes mondat, streaming → `done_reason=stop`, **13 750 generált token, 1 173 char válasz**; ugyanez 8 192-es limite mellett 0 char volt. A korlátlan futás ~103 s.
- **Fontos:** a `report-2026-10-22.md` összes száma a plafon **előtti** futásokból származik; a következő futások (muse think, esetleges UD-újrafuttatás) már korlátlanok → a két csoport nem teljesen összemérhető.
- **Dokumentáció frissítve:** `AGENTS.md` (kliens-beállítások), `wiki/concepts/hulu-benchmark.md`, `wiki/concepts/openai-backend-support.md`, `wiki/reports/report-2026-10-22.md` (5. módszertani pont).

## 2026-10-24 (v1.9 — a token-loopok gyökérokása: a `temperature: 0` greedy dekódolás; 32k token-plafon mindenütt)

- **Trigger:** a felhasználó a lokális `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL` UD Hungarian futás 31%-os token-loop arányát mutatta, majd megállította a think mérést („nem mérünk think-et").
- **Gyökérok (felhasználói diagnózis, mérve igazolva):** a `temperature: 0.0` **greedy** dekódolás. A lokális modell a CoNLL-U táblát gyakran degenerált ciklusba viszi (növekvő sorszám-sor: `1 2 3 … 6598`; kitöltő `_`-sor; FEATS-ismétlődés: `Voice=Passive|Voice=Active|…`). A mintavétel nélküli backend-default (llama-server: `temperature: 0.8`) megszünteti a loopok nagy részét.
- **Mérve:** az 5 korábban loopoló mondat (`— Hogyan tovább?`, `Már megérte Hannoverbe jönnie.`, `Ettől a győzelemtől magabiztos lettem.`, `Szerencsére megúsztuk kapott gól nélkül.`, `Az elemzés szerint korántsem.`) a javítás után **227–7007 karakteres tiszta CoNLL-U** választ ad (a 31–75k helyett). A llama-server a kérésben látott `temperature: 0.8` a saját defaultja → bizonyítja, hogy a kérés már nem küld sampling paramétert.
- **Kódváltozás (minden futásra):** a `scripts/stop_on_error.py` és `scripts/openai_compat.py` kéréseiből **kikerült a `temperature`** (és a `top_p`/`top_k`/`min_p`/`repeat_penalty` sem kerül oda) → minden backend (Ollama, llama-server, vLLM, TGI) a saját defaultját alkalmazza. Új konstans: `MAX_OUTPUT_TOKENS = 32768` — a generálás felső korlátja **mindenhol 32k**; a tényleges keretet a backend contextje adja, így a prompt + a válasz együtt belefér a 32k-ba. A `resolve_num_predict` a cloud modellek saját plafonját csak 32k alatt használja.
- **Bírók:** a `judge_hugme.py` / `judge_mt_bench.py` / `rejudge_hugme.py` is a közös hívókat használják → a bíróminta is nem-determinisztikus lett. A pontszám-kivonat ezért **lépcsőzetes** (önálló szám/betű egy sorban → szövegen belül → első karakter), hogy a rendetlen bíróválasz ne rontsa a döntést.
- **Új: `scripts/deg_loop.py`** — degeneráció-detektor (periodicitás-próba a farkon + számlálóciklus-felismerés, 12k karakteres küszöb). Validálva: a 5 cloud UD futáson **0 false positive**, a régi temp=0 futáson 103/449 = 22,9% valódi degeneráció.
- **Új: bounded retry a UD runnerben** (`run_ud_hungarian.py`): degenerált válasz esetén legfeljebb **2 újrapróbálkozás** (az első kérés a teljes 32 768 tokenes plafonnal, az újrapróbálkozások **8 192** tokenes plafonnal, hogy a használhatatlan generáció ~1,5 perc alatt levágódjon). Az első tiszta minta nyer; ha mindhárom degenerált, az utolsó hibaként számít. A stop-policy érintetlen: a retry csak **sikeres** válasz után, degeneráció esetén fut. A `degenerate_retries` mező a JSONL sorban.
- **Új: `scripts/reparse_ud.py`** — a tárolt nyers válaszokból **offline** újraparse-olja a UD pontszámokat és frissíti a summary-t (a futások újrafuttatása nélkül).
- **Parser-javítás:** a UPOS oszlopot is robusztusan keressük (a 4. oszlop az elvárt, de a modell gyakran beszúr egy extra FORM-ot a LEMMA után → a fix 4. index félrement, és a sor teljesen eldobódott). **Hatás a tárolt cloud számokra (újraparse-olt):** deepseek-v4.1-flash nothink UAS **0,0823 → 0,4792**, LAS 0,0959 → 0,5314; muse nothink UAS 0,7858 → 0,8254; mistral nothink UAS 0,4393 → 0,4506. A UPOS-ok alig változnak (a cloud modellek formátuma szabványos).
- **Fontos módszertani megjegyzés (mérve):** a sampling-váltás a **formátumhűséget** is rontja — a lokális modell a backend default (0.8) sampling mellett ~25%-ban 60–65k karakteres, **eltérő sémájú** CoNLL-U-t generál (a kért 7 oszlop helyett 8: `ID FORM LEMMA FORM UPOS …`), ami 6 percet éget és 0 pontot ér. A greedy (temp=0) dekódolás formátumban következetesebb volt, de 25%-ban degenerált. A riport ezért három számot ad meg: összes UPOS / parse-olható válaszokon mért UPOS / parse-hányad.
- **Archiválás:** a `temperature: 0` + korlátlan limitekkel készült lokális eredmények `*.temp0.*` néven megmaradtak (az aggregátor nem látja őket). A 2026-10-24 előtti **cloud** eredmények is `temperature: 0.0` + korlátlan/4096/8192/16384-es limitekkel készültek → a lokális modell új eredményeivel **nem teljesen összemérhetők** (a sampling-paraméter és a token-plafon is más).
- **Döntések:** think fázis **kihagyva** (felhasználói döntés, 2026-10-23); a cloud kvóta 2026-10-24 00:10-kor ismét elérhető volt → a judge-os benchmarkok (HuGME + MT-Bench-HU) a lokális modellre is futtathatók.
- **Futtatás:** `phase4` (UD → HuLU → MMLU nothink, `setsid`-del, 20 újrapróbálkozás/lépés) + `phase5` lánc (HuGME + MT-Bench-HU generálás + cloud bíró).

## 2026-10-26 (v2.0 — a lokális Qwen3.5-9B kör lezárása: bírók, UD-újraparse, breakdown-javítások, riport)

- **Generálás (2026-10-24):** a lokális `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL` (nothink, llama-server) mind az 5 benchmarkon lefutott: UD 449/449 (9 h 21 m, 52/449 item retry, 0 elfogadott degenerált), HuLU 2581/2581 (16 m), MMLU 1500/1500 (21 m), HuGME 300/300 (70 m), MT-Bench 24/24 (9 m).
- **Bírók elakadtak 2026-10-24-én:** a HuGME-bíró 76/300-nál megállt (heti cloud kvóta), az MT-Bench bíró el sem indult, mert a baseline modell (`deepseek-v4-flash:cloud`) **2026-09-25-én RETIRED** lett (HTTP 410: „deepseek-v4-flash:0731 was retired”). A 0 bájtos baseline-fájl maradt utána.
- **Bírók lezárva 2026-10-26-án (run5, `setsid`, 10 retry/lépés):**
  - **HuGME: 300/300, score 0,7203.** Metrika-bontás: toxicity 0,980, answer_relevancy 0,839, prompt_alignment 0,793, bias 0,775, summarization 0,671, **faithfulness 0,260** (a fő gyengeség: tartalmi hűség). 52/300 item < 0,5; 4 item 0,0.
  - **MT-Bench-HU: 24/24, score 0,3958, strict 0,000 (0W/10L/38T)**, 2 baseline-nal (`deepseek-v4-pro:cloud`, `kimi-k2.6:cloud`) a `rejudge_mt_bench.py`-val. A harmadik baseline (deepseek-v4-flash) RETIRED → a sablon 3 baseline-os protokollja egyelőre nem állítható vissza.
- **UD újraparse alkalmazva minden futásra** (`scripts/reparse_ud.py`): a robusztus UPOS-oszlopkeresés miatt deepseek-v4.1-flash nothink UAS **0,0823 → 0,4789**, LAS 0,0959 → 0,5314; mistral nothink UAS 0,4393 → 0,4506, LAS 0,5156 → 0,5283; muse nothink UAS 0,7858 → 0,8254, LAS 0,6012 → 0,6337; lokális UPOS 0,3071 → 0,3256. **A cloud composite-ok emiatt változtak** (deepseek nothink 0,650 → 0,706; muse 0,781 → 0,788) — a 2026-10-22-i UD-táblázat elavult.
- **`breakdown_report.py` javítások (3 valódi bug):**
  1. **MMLU dedup:** a `by_id` csak `id`-re kulcsolt, de a MMLU-HU id-k nem globálisak (`mmlu_hu_val_2` minden tantárgyban létezik) → a bontás 1500 sorból **61-re** omlott, 7 tantárggyal. Javítás: `(subject, id)` kulcs.
  2. **`hasattr(config, 'TASKS')` mindig igaz** volt (a `SimpleNamespace`-ben `TASKS=None`), ezért a MMLU-nál `tasks=None` → `TypeError`, a UD-nál rossz ág. Javítás: `getattr(..., None)`.
  3. **UD-ág:** csak akkor futott, ha nincs `task` mező (a mostani sorokban van: `ud_hungarian`), a float metrikákat binárisan számolta, és a CSV-be `overall` került, ami nem volt a fieldnames-ben. Javítás: `task`-független ág + float-összegzés (`sum`) + `upos_accuracy` alias + CSV-szűrés.
- **Aggregáció:** helyi composite **0,5345** (STAT 0,679 / GEN 0,558 / LING 0,199) — 8. hely; a mezőny élén a muse-spark-open nothink **0,788**, majd minimax think 0,726, deepseek nothink 0,706.
- **Riport + wiki:** új [report-2026-10-24.md](reports/report-2026-10-24.md) (kötelező benchmark-leírások, HuLU per-sub-task tábla minden modellre, kvantálás `UD-Q4_K_XL`, backend `openai`, a három UD-szám, sampling-módszertan); a `reports/report.md` symlink átállítva; új entitás-oldal [qwen3.5-9b-mtp-lokalis.md](entities/qwen3.5-9b-mtp-lokalis.md); `index.md`, `cloud-vs-lokal.md`, `modell-vs-modell.md` frissítve; ez a bejegyzés.
- **Nyitott:** a `scripts/queue_all_benchmarks.sh` `MODELS` tömbjében még szerepel a RETIRED `deepseek-v4-flash:cloud`; az MMLU-HU dataset duplikátum (1500/750) továbbra is nyitott; a muse think kör és a lokális think továbbra sincs mérve.

## 2026-10-26 (v2.1 — muse-spark-open think kör indítva, gép-újraindítás miatt leállítva)

- **Döntés:** a felhasználó „folytasd a benchmark-ot" utasítására a hátralévő kör a **`muse-spark-open:cloud` think** befejezése (2026-10-22-én a HuLU 871/2581-nél szakadt meg heti kvóta miatt).
- **Tiszta protokoll:** a régi HuLU-rész (871 item, `temperature: 0`) **43 üres választ** tartalmazott (4,9%) → `--reset`, a régi fájlok `hulu_results.temp0.jsonl` / `hulu.temp0.json` néven archiválva. Az új futás a 2026-10-24-i protokollal megy (nincs sampling param, 32k plafon, explicit `think: true`).
- **`run_mmlu_hu.py` determinizmus-javítás:** a `completed_set` eddig csak a futás elején készült pillanatkép volt → megszakítás után a duplikált `(subject, id)` kérdések kimaradtak, folyamatos futásnál nem (1500 vs. ~750 sor). Most minden feldolgozott item bekerül a halmazba → a resume ugyanannyi sort ad, mint a folyamatos futás (750 egyedi kérdés).
- **Cloud think hosszú hívások:** a 2026-10-22-i 502-probléma nem jött vissza (19,6 s / 3295 token → HTTP 200), nem kell streaming wrapper.
- **Eredmény (befejezett lépés):** **HuLU think 77,41%** (1998/2581, 0 üres, 3 h 18 m) — a mezőny legjobb HuLU-ja. Sub-task: HuCoLA 82,2 / HuCoPA 97,0 / HuRTE 90,5 / HuSST 72,7 / HuWNLI 11,7 / HuCB 76,7. **Think vs. nothink (ugyanaz a modell): 77,41% vs. 77,06% = +0,35 pt** — a gondolkodás itt alig számít: HuCoLA +0,3, HuSST +1,8, HuWNLI +1,7, de HuCoPA −1,0, HuRTE −2,9, **HuCB −7,8**. (Korábbi téves közlés: a „+7,2 pt" a *lokális* modell nothinkjéhez hasonlított, nem a muse-hoz; a HuWNLI 60,0% szintén a lokális modell értéke volt.)
- **Leállítás (2026-10-26 11:35):** a felhasználó gépet indít újra → a driver és a runner leállítva (SIGTERM), az MMLU 100/750-nél tartott (acc 0,950). A state `failed_stopped` / `machine_restart_2026-10-26`, a results fájl a checkpoint szintjére trimmelve (122 → 100 sor, 0 duplikátum). **A llama-server érintetlen.**
- **Folytatás reboot után:** `bash /tmp/opencode/run6/driver_run6.sh` (a HuLU kész, a MMLU resume-ol 100-ról; utána HuGME → MT-Bench → bírók → UD).

## 2026-10-27 (v2.2 — a muse-spark-open:cloud THINK kör lezárva: 5 benchmark + 2 bíró, composite 0,7937)

- **Futás:** run6 (`logs/run6/driver.log`), 2026-10-26 08:08 → 10-27 00:20, nettó ~9 óra. A HuLU tiszta `--reset`-tel (a 2026-10-22-i temp=0 rész, 43 üres válasszal, `*.temp0.*` néven archiválva), a többi benchmark folytatással.
- **Eredmények (think / nothink):** HuLU **77,41%** / 77,06% (+0,35); MMLU-HU **93,07%** (750 dedupolt) / 91,40% (1500) (+1,67); HuGME **0,9034** / 0,9054 (−0,20); MT-Bench **0,5729** (8W/1L/39T) / 0,5625 (8W/2L/38T) (+1,04); UD **UPOS 89,88% / UAS 82,76% / LAS 63,63%** (composite 78,76%, parse 100%) / 89,71% / 82,54% / 63,37% (+0,22).
- **Composite (40/40/20): 0,7937** → **a mezőny élén** (a nothink pár 0,7876 a 2. helyen). Mindhárom dimenziót a think nyeri, de < 1 pt-tal: STAT 0,852, GEN 0,738, LING 0,788.
- **Fő tanulság:** a think mód ezen a modellen **alig számít** (+0,6 pt composite); a HuCB-n **ront** (−7,8 pt), az MMLU-n javít (+1,7 pt). A HuWNLI mindkét módban katasztrofális (10–11,7%) — a lokális 9B viszont 60%-ot ér el ugyanezen.
- **Megszakítások (a checkpoint-rendszer helyesen kezelte):**
  - 10-26 11:35 gép-újraindítás → MMLU 100/750-nél leállt; a results 122 sora és a 100 elemű checkpoint eltérése miatt 22 többletsor trimelve, state `failed_stopped` / `machine_restart_2026-10-26`. Adatvesztés nincs.
  - 10-26 22:59 `http_429` az UD 288/449-nél → 3 perc múlva a driver újraindította, 23:02-től hibátlanul befejeződött.
- **Kód:** `scripts/run_mmlu_hu.py` determinizmus-javítás (a `completed_set` minden feldolgozott item után bővül → a resume ugyanannyi sort ad, mint a folyamatos futás: 750 egyedi kérdés, nem 1500).
- **Korrekciók (a riportban dokumentálva):**
  1. A v2.1 bejegyzés „+7,2 pt think vs. nothink" állítása **téves volt** (a *lokális* modell nothinkjéhez hasonlított) — a helyes Δ **+0,35 pt** (javítva a v2.1 szövegben).
  2. A futás közben, 112/449 UD itemnél jelentett „UAS +11,9 / LAS +25,5 pt" **nem tartott** — a végleges Δ +0,22 / +0,26 pt (a korai mondatok rövidebbek/könnyebbek).
- **Wiki:** új [report-2026-10-27.md](reports/report-2026-10-27.md) (kötelező benchmark-leírások, HuLU per-sub-task tábla mindkét módra, kvantálás `ollama-cloud`, backend `ollama`, UD három szám, composite A/B); a `reports/report.md` symlink átállítva; új entitás-oldal [muse-spark-open.md](entities/muse-spark-open.md); `index.md` és `cloud-vs-lokal.md` frissítve.
- **Nyitott:** a lokális Qwen3.5-9B think módja nincs mérve; a harmadik MT-Bench baseline (deepseek-v4-flash) RETIRED; az MMLU-HU dataset továbbra is 2× duplikált; a queue MODELS listájában még szerepel a RETIRED `deepseek-v4-flash:cloud`.

## 2026-10-27 (v2.3 — beam:cloud teljes kör think-only + streaming javítás + UD-újrafuttatás indítva)

- **Új modell:** `beam:cloud` — 501B, 1 048 576 token kontextus, capabilities: completion + thinking (szintek low/medium/high/xhigh/max, default max) + tools.
- **Mód-diagnózis:** a **nothink nem működik** — `think: false` a natív `/api/generate`-en 432 char reasoningot adott, a `/v1` + `chat_template_kwargs.enable_thinking=false` 304-et → a modell mindig gondolkodik. Ezért **think-only** mérés (precedens: qwen3-next-80b lokális). A mérés a default (**max**) szinten történt; a szintek összevetése nyitott.
- **Teljes kör (run8 + run8b):** HuLU **75,09%** (1938/2581; HuCoLA 81,4 / HuCoPA 93,0 / HuRTE 90,9 / HuSST 68,8 / **HuWNLI 8,3** / HuCB 74,8); MMLU-HU **91,73%** (688/750); HuGME **0,9082** (**faithfulness 0,606 — mezőny-legjobb**); MT-Bench **0,4896** (4W/5L/39T); UD **UPOS 87,40 / UAS 80,36 / LAS 62,46** (composite 76,74%, parse 98,2%).
- **Composite (40/40/20): 0,7667 → 3. hely** (muse think 0,7937 és muse nothink 0,7876 mögött, a deepseek/mistral/minimax nothink 0,70–0,71 előtt).
- **Új kód: opt-in streaming a `stop_on_error.py`-ban** (`BENCH_STREAM=1`). Ok: az UD think válaszai (20 945 char gondolkodás, 6 823 eval token) átlépik a cloud proxy **60 s-os** nem-streamelt korlátját → `http_502`. A stream NDJSON-sorai a nem-streamelt válasz alakjára állnak össze (response/thinking/done_reason/eval_count); a hibás chunk **fatális hiba** (nem csendes csonkolás); a flag nélkül a régi út fut. Élő validáció: hosszú CoNLL-U kérés 29 s; a run8b alatt egy stream-hiba (item 203) tisztán leállt, majd resume-olt **duplikátum nélkül** (253 sor = 253 egyedi id).
- **UD-újrafuttatás (run7b, folyamatban):** a 2026-10-22-i token-plafon miatt érvénytelen think UD-k — **deepseek-v4.1-flash** (356/449 üres), **mistral-large-4** (347/449 üres), **minimax-m3.1-flash** (soha nem futott) — újrafuttatása streaminggel; a régi fájlok `*.truncated.*` néven archiválva. **Amíg nem készülnek el, a három modell composite-ja UD nélkül számol (torz: deepseek think 0,6418 → átmenetileg 0,7606; mistral think 0,6547 → 0,7738).**
- **Wiki:** új [report-2026-10-27-beam.md](reports/report-2026-10-27-beam.md) (kötelező benchmark-leírások, HuLU per-sub-task, kvantálás `ollama-cloud`, backend `ollama` + streaming, UD három szám), új entitás [beam.md](entities/beam.md); a `reports/report.md` symlink átállítva a beam-riportra; `index.md` frissítve.

## 2026-11-09 (v2.4 — nincs-plafon mezőny lezárva: UD + MT-Bench újrafuttatva, deepseek/muse holtverseny)

- **Szabály életbe lépett:** cloud = nincs kimeneti plafon, lokális = 32k (2026-11-04). A `num_predict` cloud esetén kimarad a kérésből; a `stop_on_error.default_num_predict()` dönt, a runner `--num-predict` flaggel felülírható.
- **Mit futtattunk újra no-cap-pel:** a teljes **UD** kört (deepseek, mistral, minimax, beam) és a teljes **MT-Bench** kört (8 régi futás + beam). A HuLU/MMLU/HuGME 32k-s maradt, mert a beam A/B mérés szerint a hatás ≤0,13 pt (HuLU +0,08, MMLU −0,13, HuGME +0,0005).
- **Látványos javulások (32k → no-cap):** deepseek think UD 73,69/66,35/54,30 → **91,68/82,10/67,43** (91 → 1 üres válasz, composite 64,78 → **80,40**); minimax nothink MT-Bench 0,3438 → **0,4896** (+14,6); deepseek think MT-Bench 0,4167 → 0,5208 (+10,4); minimax think MT-Bench +8,3.
- **Romlás is van:** muse MT-Bench 0,5729 → 0,5521 (think), 0,5625 → 0,5000 (nothink) — a no-cap **nem univerzális javítás**.
- **Végleges rangsor (40/40/20):** 1. deepseek-v4.1-flash think **0,7901** · 2. muse-spark-open think **0,7896** (Δ 0,0005 = holtverseny) · 3. muse nothink 0,7751 · 4. beam 0,7737 · 5. mistral think 0,7732 · 6. minimax think 0,7200 · 7. deepseek nothink 0,7123 · 8. mistral nothink 0,7000 · 9. minimax nothink 0,7391 (UD nélkül, súly-újraosztás) · 10. lokális 9B 0,5345.
- **Dimenzió-győztesek:** STAT = muse think (0,852); GEN = deepseek think (0,729); LING = deepseek think (0,804).
- **Wiki:** új [report-2026-11-09-nocap.md](reports/report-2026-11-09-nocap.md) (teljes, kötelező leírásokkal, HuLU sub-task táblával, kvantálással, UD három számmal), `report.md` symlink átállítva, `index.md` frissítve; a `reports/composite_scores.csv` naprakész.
- **Nyitott:** minimax **nothink** UD sosem futott (érdemes no-cap-pel megpróbálni); lokális 9B think kör; harmadik MT-Bench baseline; HuLU/MMLU/HuGME no-cap újrafuttatás teljes egységességhez.

## 2026-11-09 (v2.5 — a tábla lezárva: minimax nothink UD is elkészült)

- **minimax-m3.1-flash nothink UD (no-cap):** 449/449, **UPOS 72,16% / UAS 55,20% / LAS 43,41% → composite 0,5692**, 1 üres válasz, ~14 s/item (a `think: false` itt **működik**, ellentétben a beam-mel).
- **Ezzel nincs hiányzó cella:** mind a 10 futás mind az 5 benchmarkkal rendelkezik; a súly-újraosztásos torz sorok megszűntek.
- **Composite-változás:** minimax nothink 0,7391 (UD nélkül, téves) → **0,7051** (valódi UD-vel). A teljes rangsor változatlan éllel: deepseek think 0,7901 · muse think 0,7896.

## 2026-11-10 (v2.6 — kanonikus összesítő riport)

- **`wiki/reports/report.md` mostantól valódi, szerkesztett összesítő fájl** (nem symlink). Tartalma: a teljes **2026-11-es no-cap mezőny** (10 futás × 5 benchmark, minden cella kitöltve) + a **2026-07-es archív mezőny** (18 sor) külön, „nem összemérhető" figyelmeztetéssel, + **protokoll-történet** (greedy → nincs sampling → 32k → nincs plafon) a mért hatásokkal.
- A riport tartalmazza a kötelező elemeket: benchmark-leírások minden szekcióban, HuLU per-sub-task tábla (mind a 10 futásra), kvantálás, backend, UD három szám, composite A + B, dimenzió-győztesek.
- **Fő üzenet:** deepseek-v4.1-flash think (0,7901) és muse-spark-open think (0,7896) holtverseny; deepseek nyeri a GEN + LING dimenziót, muse a STAT-ot; a plafon elhagyása modellfüggően ±(2–18) pt-otmozgat.
