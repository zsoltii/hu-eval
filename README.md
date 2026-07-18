# hu-eval — Magyar LLM Értékelési Projekt

Ez a mappa tartalmazza a magyar nyelvű LLM-ek (cloud + lokális) szisztematikus
értékeléséhez szükséges **scripteket, adatokat, állapotokat, eredményeket
és riportokat** — és a dokumentáló wikit.

A wiki (dokumentáció) a `wiki/` mappában van, a kód és az adatok közvetlenül
a projekt gyökerében. A teljes wiki-rendszer leírása: `wiki/overview.md`.

## Mappastruktúra

```
hu-eval/
├── README.md                          ← ez a fájl (projekt-térkép)
│
├── scripts/                           ← futtatható Python + shell scriptek (19 py + 9 sh)
│   ├── stop_on_error.py               ← Ollama hívás, ami stop-on-error-t dob
│   ├── checkpoint.py                  ← atomi state mentés/betöltés
│   ├── download_hulu.py               ← HuLU (6 NLU sub-task) letöltés NYTK HF-ről
│   ├── download_mmlu_hu.py            ← MMLU-HU (NYTK/hu-mmlu) letöltés
│   ├── download_ud_hungarian.py       ← UD Hungarian (CoNLL-U) letöltés GitHub-ról
│   ├── run_hulu.py                    ← HuLU benchmark (checkpoint-aware, think/nothink)
│   ├── run_mmlu_hu.py                 ← MMLU-HU (5-shot)
│   ├── run_hugme.py                   ← HuGME (generatív, 300 prompt)
│   ├── run_mt_bench_hu.py             ← MT-Bench-HU (2-turn, GSB)
│   ├── run_ud_hungarian.py            ← UD Hungarian (CoNLL-U parse)
│   ├── judge_hugme.py / judge_mt_bench.py ← LLM-as-a-Judge (gemini-3-flash-preview)
│   ├── reparse_ud.py / rejudge_hugme.py / rejudge_mt_bench.py / dedup_hulu.py / recompute_hulu_summary.py ← javító scriptek
│   ├── aggregate_results.py           ← composite score (40/40/20) + riport + heatmap
│   ├── breakdown_report.py / hulu_breakdown_report.py ← per-benchmark riportok
│   └── queue_all_benchmarks.sh + orchestrator-ok (queue_runner, phase2_runner, priority_judge, post_followup, watchdog)
│
├── data/                              ← letöltött / előkészített datasetek
│   ├── hulu/  mmlu_hu/  hugme/  mt_bench_hu/  ud_hungarian/  hulu_cache/
│
├── results/                           ← benchmark eredmények (per modell-mód)
│   └── {model_safe}-{mode}/            ← pl. qwen3.5-cloud-nothink/  vagy  qwen3.5-cloud-think/
│       ├── hulu_results.jsonl          ← per-prompt nyers válaszok (append-only + fsync)
│       ├── hulu_summary.json           ← aggregált accuracy
│       ├── mmlu_hu_results.jsonl / mmlu_hu_summary.json
│       ├── hugme_results.jsonl / hugme_judged.jsonl / hugme_summary.json
│       ├── mt_bench_hu_results.jsonl / mt_bench_hu_judged.jsonl / mt_bench_hu_summary.json
│       └── ud_hungarian_results.jsonl / ud_hungarian_summary.json
│
├── state/                             ← checkpoint state fájlok (per modell-mód)
│   └── {model_safe}-{mode}/            ← pl. qwen3.5-cloud-nothink/
│       ├── hulu.json                   ← checkpoint state HuLU futáshoz
│       ├── mmlu_hu.json
│       └── ...
│
├── logs/                              ← futás-naplók (append-only)
│   ├── hulu_runs.log
│   ├── mmlu_runs.log
│   └── ...
│
├── reports/                           ← generált riportok
│   ├── composite_scores.csv           ← nyers DataFrame CSV-ben
│   ├── report.md                      ← markdown riport táblával + heatmap
│   └── results_heatmap.png            ← matplotlib heatmap
│
├── raw/                               ← nyers forrásanyagok, idézetek, PDF-ek
│
└── wiki/                              ← teljes wiki (dokumentáció)
    ├── index.md
    ├── overview.md
    ├── SCHEMA.md
    ├── log.md
    ├── concepts/                      ← 14 db (fogalmak, módszertan)
    │   ├── checkpoint-progress.md     ← stop-on-error + resume tervezési elv
    │   ├── hulu-benchmark.md
    │   └── ...
    ├── entities/                      ← 11 db (6 modell + 5 dataset)
    ├── comparisons/                   ← 3 db (modell vs. modell, stb.)
    ├── runbooks/                      ← 5 db (végrehajtható eljárások)
    └── reports/                       ← 2 db (riport template-ek)
```

## Gyors indulás

```bash
conda create -n eval-hu python=3.11 -y
conda activate eval-hu
pip install requests pandas matplotlib deepeval ollama-python datasets

# 1. Dataset letöltés (egyszeri)
python scripts/download_hulu.py
python scripts/download_mmlu_hu.py

# 2. Benchmark futtatás (az első modell, smoke test)
python scripts/run_hulu.py --model qwen3.5:4b --limit 50

# 3. Teljes futtatás (ez több óra lehet)
python scripts/run_hulu.py --model qwen3.5:4b

# 4. Ha megszakadt (rate limit, timeout) — AUTOMATIKUS resume:
python scripts/run_hulu.py --model qwen3.5:4b

# 5. Aggregáció + riport
python scripts/aggregate_results.py
```

## Hol mi van — gyors referencia

| Mit keresek? | Hol van? |
|--------------|----------|
| A HuLU futás nyers válaszai | `results/{model}/hulu_results.jsonl` |
| A HuLU futás aggregált accuracy | `results/{model}/hulu_summary.json` |
| A futás állapota (hol tartott) | `state/{model}/hulu.json` |
| A futás logja (mikor mi történt) | `logs/hulu_runs.log` |
| Összesített composite score | `reports/composite_scores.csv` |
| Végső riport | `reports/report.md` |
| Vizuális heatmap | `reports/results_heatmap.png` |
| Wiki katalógus | `wiki/index.md` |
| A checkpoint tervezési elv | `wiki/concepts/checkpoint-progress.md` |
| A HuLU futtatás részletes leírása | `wiki/runbooks/run-hulu-modell-x.md` |
| Stop-on-error stratégia | `wiki/concepts/checkpoint-progress.md` |

## Checkpoint / resume működés

A scriptek **stop-on-error + resume** szemantikát követnek:

- Ha bármilyen hiba történik az Ollama felé (HTTP 429 rate limit, 5xx, timeout,
  connection error, modell nem található), a futás **azonnal megáll**.
- Az aktuális állapot atomi write-tal a `state/{model}/{benchmark}.json` fájlba
  mentődik — `current_index`, `completed_ids`, `num_correct`, `stop_reason`.
- A `logs/{benchmark}_runs.log` fájlban rögzül, hol tartott.
- A script **ugyanazzal a paranccsal** újraindítva onnan folytatja, ahol abbahagyta.
- A `results/{model}/*.jsonl` append-only, minden sikeres item után íródik
  (flush + fsync), így részleges eredmény mindig megmarad.
- Az aggregátor a `state/`-et is olvassa: ha egy modell futása checkpoint
  miatt megszakadt, a riport tetején `⚠️ Részleges eredmények` figyelmeztetés
  jelenik meg, és a composite score `[RÉSZLEGES]` jelölést kap.

Részletek: [`wiki/concepts/checkpoint-progress.md`](wiki/concepts/checkpoint-progress.md).

## Scriptek részletes leírása

### `scripts/stop_on_error.py`

`call_ollama_strict(prompt, model, max_retries=2, timeout=120)` — Ollama hívás,
ami `OllamaFatalError`-t dob az első nem-tranziens hibánál. Retry policy:

- HTTP 400/404/422: nincs retry (konfigurációs hiba)
- HTTP 429: retry a `Retry-After` header alapján
- HTTP 5xx: retry exponenciális backoff-fal
- Timeout: retry + backoff
- ConnectionError: nincs retry, azonnal hiba

### `scripts/checkpoint.py`

`Checkpoint(state_path)` osztály — atomi JSON state mentés/betöltés.
- `save()`: tmp fájl + `os.replace()` (atomi)
- `mark_completed(item_id, is_correct)`: növeli a számlálókat
- `mark_stopped(reason)`: státusz = `failed_stopped`
- `mark_completed_full()`: státusz = `completed`
- `resume_from` property: hányadik item-től kell folytatni

### `scripts/run_hulu.py`

`run_hulu.py --model <modell> [--limit N] [--reset] [--status]`
- `--reset`: törli a korábbi state + results fájlt
- `--status`: csak a state fájlt írja ki
- nélküle: folytatás onnan, ahol abbahagyta (vagy első indítás, ha nincs state)

### `scripts/aggregate_results.py`

`aggregate_results.py [--results-dir DIR] [--out DIR] [--state-dir DIR]`
- Bejárja a `results/{model}/` mappákat
- Kiolvassa a `state/{model}/*.json` checkpoint-okat
- Számolja a composite score-t (40% stat + 40% gen + 20% ling)
- Generál CSV-t, markdown riportot, matplotlib heatmap-et
- A riport tetején `⚠️ Részleges eredmények` szekció, ha van partial modell

### `scripts/download_hulu.py`

`download_hulu.py` — letölti a **6 NLU sub-taskot** (HuCoLA, HuCoPA, HuRTE, HuSST, HuWNLI, HuCB) a
NYTK HuggingFace datasetjeiről, és kiírja a `data/hulu/hulu_std.jsonl` fájlt.
Ha a HF nem elérhető, a `--offline` flag a `nytud/HuLU` git clone-ból olvas.
A korábbi `PhilipMay/hulu-bench` dataset megszűnt (401), ez a forrás helyettesíti.
Egyszeri futtatás szükséges a HuLU benchmarkok előtt.

### `scripts/download_mmlu_hu.py`

`download_mmlu_hu.py` — letölti az **NYTK/hu-mmlu** validation splitjét (38 tantárgy,
~1880 kérdés, MIT licenc), és a HuLU-val azonos standardizált formátumban
(`{id, task, prompt, choices, answer_index, subject, source}`) kiírja a
`data/mmlu_hu/mmlu_std.jsonl` fájlba. A 4 opció A/B/C/D betűjelét 0/1/2/3
indexre konvertálja, hogy a `run_hulu.py` extractor-kódja újrahasznosítható legyen.
Nincs `run_mmlu_hu.py` runner — csak a letöltés + standardizálás kész.

## Kapcsolódó wiki-oldalak

- [Wiki áttekintés](wiki/overview.md)
- [Wiki katalógus](wiki/index.md)
- [Checkpoint koncepció](wiki/concepts/checkpoint-progress.md)
- [Runbook: HuLU futtatás](wiki/runbooks/run-hulu-modell-x.md)
- [Runbook: Aggregáció](wiki/runbooks/aggregate-results.md)
- [Runbook: Környezet beállítás](wiki/runbooks/setup-kornyezet.md)
- [Runbook: Debug](wiki/runbooks/debug-modell-nem-valaszol.md)
- [Runbook: LLM Judge](wiki/runbooks/llm-judge-prompt-template.md)
