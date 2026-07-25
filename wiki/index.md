# Index — hu-eval Wiki

*Típus:* concept
*Forrás(ok):* belső projekt-katalógus
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-25

---

*Tartalomkatalógus. Frissül, ahogy új oldalak jönnek létre.*

*Utolsó frissítés:* 2026-07-25 (v1.4 — Qwen3-Next-80B IQ3_XXS nothink benchmark kész, think adatok elvesztek, riport elkészült)

## ⚙️ Futtatható kód és adatok

A teljes projekt-struktúra (scriptek, adatok, eredmények, state) a gyökér [`README.md`](../README.md) fájlban. Röviden:

- `scripts/` — 19 Python + 9 shell script (stop_on_error, checkpoint, 3 download_*, 5 run_*, 2 judge_*, 4 reparse/rejudge/recompute/dedup, aggregate, breakdown_report, queue_all_benchmarks + orchestrator scripts)
- `data/` — letöltött datasetek (HuLU, MMLU-HU, HuGME, MT-Bench-HU, UD Hungarian)
- `results/{model}-{mode}/` — per-modell per-mód benchmark eredmények (JSONL + summary)
- `state/{model}-{mode}/` — checkpoint state fájlok (atomi write)
- `logs/` — append-only futás-naplók
- `reports/` — composite score, riport, heatmap

## 🛑 Tervezési elvek

- [Checkpoint és folytatható futtatás](concepts/checkpoint-progress.md) — stop-on-error + resume politika, közös `FatalBackendError` (v1.1, 2026-07-19)
- [LLM-as-a-Judge módszertan](concepts/llm-as-judge.md) — bíró modellek használata
- [Ollama API kliens](concepts/ollama-api-client.md) — újrafelhasználható Python wrapper
- [OpenAI-kompatibilis backend](concepts/openai-backend-support.md) — `ollama` és `openai` backend támogatás a run scriptekben, llama-server / vLLM / felhő OpenAI (v1.3.4, 2026-07-19)

## Kötelező oldalak

---

## Kötelező oldalak

- [Overview](overview.md) — projekt cél, hatókör, fő lépések
- [SCHEMA](SCHEMA.md) — oldal-univerzum, formátum, karbantartási szabályok
- [Log](log.md) — időrendi tevékenységnapló

## Concepts (fogalmak, módszertan) — 15 db (v1.3)

### Statisztikai benchmarkok

- [HuLU benchmark](concepts/hulu-benchmark.md) — NYTK 6 NLU sub-task (HuCoLA, HuCB, HuCoPA, HuRTE, HuSST, HuWNLI) + 1 nem implementált RC (HuRC); részletes módszertan (v1.2.6)
- [Nem-HuLU benchmarkok módszertana](concepts/tobbi-benchmark-modszere.md) — MMLU-HU, ARC-HU, GSM8K-HU, Perplexitás, HuGME, MT-Bench-HU, UD Hungarian, Morfológia (v1.2.11: 4 benchmark implementálva)
- [MMLU-HU](concepts/mmlu-hu.md) — 38 tantárgy, NYTK/hu-mmlu validation split, 5-shot prompting
- [ARC + GSM8K magyarul](concepts/arc-gsm8k-hu.md) — érvelés + matematika, CoT opcióval
- [Perplexitás (magyar)](concepts/perplexity-hu.md) — HuWiki sliding-window PPL
- [Ollama API kliens](concepts/ollama-api-client.md) — újrafelhasználható Python wrapper

### Generatív benchmarkok (LLM-as-a-Judge)

- [HuGME benchmark](concepts/hugme-benchmark.md) — 6 metrika, DeepEval wrapper
- [MT-Bench magyarítva](concepts/mt-bench-hu.md) — 80-100 multi-turn prompt
- [Szabad kérdéssor](concepts/szabad-kerdes-hu.md) — 30-50 kulturális magyar kérdés
- [LLM-as-a-Judge módszertan](concepts/llm-as-judge.md) — bias-mitigation, prompt design

### Nyelvészeti mélytesztek

- [UD Hungarian](concepts/ud-hungarian.md) — POS, dependency parsing, UAS/LAS
- [Magyar morfológia teszt](concepts/morfologia-hu.md) — 200 mondat, magánhangzó-harmónia + toldalékolás
- [Magyar szórend teszt](concepts/szorend-hu.md) — 100 mondat, téma-fókusz struktúra
- [Nyelvészeti összefoglaló](concepts/nyelveszeti-osszefoglalo.md) — a 3 nyelvészeti teszt együtt, composite score
- [**Checkpoint és folytatható futtatás**](concepts/checkpoint-progress.md) ⭐ — stop-on-error + resume politika (2026-06-06)

## Entities (modellek, datasetek) — 13 db

### Modellek (12 db, 1 RETIRED)

- [MiniMax M3 (Cloud)](entities/minimax-m3.md) — aktív default cloud modell, 256k kontextus
- [DeepSeek V4 Pro (Cloud)](entities/deepseek-v4-pro.md) — 🏆 legjobb composite (nothink, 54.3%)
- [DeepSeek V4 Flash (Cloud)](entities/deepseek-v4-flash.md) — legjobb UD (nothink, 69.9%)
- [Kimi K2.6 (Cloud)](entities/kimi-k2.6.md) — 1.04T MoE, benchmark modell (bíró státusz törölve 2026-06-07, v1.2.4)
- [Gemini 3 Flash Preview](entities/gemini-3-flash.md) — Google leggyorsabb, 1M kontextus; bíró (megszűnt 2026-07-14)
- [Qwen 3.5 Cloud](entities/qwen3.5-cloud.md) — legerősebb HuLU (think, 78.1%)
- [GLM 5.1 (Cloud)](entities/glm-5.1.md) — legnagyobb think-javulás (+4.1%)
- [GLM 5.2 (Cloud)](entities/glm-5.2.md) — új (v1.3), 2. hely composite nothink (52.1%)
- [Nemotron 3 Ultra (Cloud)](entities/nemotron-3-ultra.md) — 550B, lassú; legjobb think UD (7.5%)
- [GPT-OSS 120B (Cloud)](entities/gpt-oss-120b.md) — 120B, think/nothink azonos
- [GPT-OSS 20B (Cloud)](entities/gpt-oss-20b.md) — leggyengőbb aktív (MMLU 46%)
- [Qwen3-Next 80B (Cloud)](entities/qwen3-next-80b.md) — ⚠️ RETIRED 2026-06-16 (HTTP 410)
- [Qwen3-Next 80B Thinking GGUF (lokális)](entities/qwen3-next-80b-lokalis.md) — **lokális referencia** (v1.4, 2026-07-25), IQ3_XXS, llama-server `localhost:8080/v1`; csak think módban fut (nincs nothink); az egyetlen lokális benchmark-modell a modell-poolban

### Datasetek (5 db)

- [HuLU](entities/dataset-hulu.md) — 6 NLU sub-task (NYTK), validation split
- [MMLU-HU](entities/dataset-mmlu-hu.md) — ~1880 kérdés, 38 tantárgy (NYTK/hu-mmlu)
- [HuGME](entities/dataset-hugme.md) — 240 generatív feladat, 8 kategória
- [UD Hungarian](entities/dataset-ud-hu.md) — ~13200 mondat, CoNLL-U
- [MT-Bench-HU](entities/dataset-mt-bench-hu.md) — 100 multi-turn, 8 kategória

## Comparisons (összehasonlítások) — 3 db

- [Modell vs. modell](comparisons/modell-vs-modell.md) — kereszt-összehasonlítás keretrendszer
- [Benchmark vs. benchmark](comparisons/benchmark-vs-benchmark.md) — mit mér melyik, mikor melyiket
- [Cloud vs. lokális](comparisons/cloud-vs-lokal.md) — költség, latency, privacy tradeoff

## Runbooks (végrehajtható eljárások) — 6 db (v1.3.4)

- [Setup környezet](runbooks/setup-kornyezet.md) — conda env, `requirements.txt` telepítés, dataset-ek, hibafelderítés (v1.3.4)
- [HuLU futtatása modell X-en](runbooks/run-hulu-modell-x.md) — teljes pipeline (ollama backend, alapértelmezett)
- [Benchmark futtatás OpenAI backenden](runbooks/run-modell-x-openai-backend.md) — llama-server / vLLM / felhő OpenAI esetén (v1.3.4, 2026-07-19)
- [LLM-judge prompt template](runbooks/llm-judge-prompt-template.md) — újrafelhasználható bíró prompt
- [Eredmények aggregációja](runbooks/aggregate-results.md) — composite score + riport
- [Debug: modell nem válaszol](runbooks/debug-modell-nem-valaszol.md) — gyakori hibák + retry

## Reports (riportok) — 13 db (v1.3 — végleges baseline)

### 🎯 BASELINE (hivatalos alapérték — minden jövőbeli összehasonlítás ehhez viszonyít)

- **[Végleges benchmark riport (2026-07-14)](reports/report-2026-07-14.md)** — 11 modell × 2 mód × 5 benchmark, 40/40/20 composite (AGENTS.md kötelező), 2 heatmap (stat + gen/ling), queue kész 20:14 CEST. **Ez a kanonikus kiindulási alapérték.**
- [Riport template](reports/riport-template.md) — v1.1 (2026-07-15), a riport formátumdefiníciója (sebesség/költség törölve, két composite tábla, két heatmap)
- [Composite CSV (2026-07-14)](reports/composite_scores-2026-07-14.csv) — 22 sor × 13 oszlop, pandas export (a baseline nyers számai)
- [Stat heatmap (2026-07-14)](reports/results_heatmap_stat-2026-07-14.png) — HuLU + MMLU-HU, RdYlGn
- [Gen/Ling heatmap (2026-07-14)](reports/results_heatmap_genling-2026-07-14.png) — HuGME + MT-Bench-HU + UD, RdYlGn

### SUPERSEDED / történeti (nem baseline — csak visszamenőleges referencia)

- [Nyers összesítés (2026-07-14)](reports/eredmeny-osszesites-2026-07-14.md) — egyszerűbb táblázat, a baseline riport nyers összesítése
- [Eredmény aggregáció + vizualizáció](reports/eredmeny-aggregacio.md) — korai composite/heatmap leírás (9 benchmark)
- [Nyers összesítés (2026-07-14)](reports/eredmeny-osszesites-2026-07-14.md) — egyszerűbb táblázat, a baseline riport nyers összesítése
- [HuLU per-sub-task bontás (2026-06-15)](reports/hulu-breakdown-2026-06-15.md) — 6 NLU sub-task (v1.2.8)
- [HuLU per-sub-task bontás (2026-06-16)](reports/hulu-breakdown-2026-06-16.md) — v1.2.10: per-modell × per-sub-task accuracy
- [Státusz 2026-07-13. 09:13 CEST](reports/benchmark-statusz-2026-07-13.md) — UD refuttatás indult
- [Státusz 2026-07-13. v2](reports/benchmark-statusz-2026-07-13-v2.md) — 2/3 UD nothink kész
- [Státusz 2026-07-13. v3](reports/benchmark-statusz-2026-07-13-v3.md) — UD think 8/10 kész
- [Státusz 2026-07-11. 09:00 CEST](reports/benchmark-statusz-2026-07-11.md) — post-followup indult
- [Státusz 2026-07-10. 05:42 CEST](reports/benchmark-statusz-2026-07-10.md) — queue kilépett

---

## Statisztikák

- **Fájlok száma:** 61 markdown (.md) — 16 concept (új: openai-backend-support) + 14 entity (új: qwen3-next-80b-lokalis) + 3 comparison + 6 runbook (új: run-modell-x-openai-backend) + 13 report + 4 kötelező
- **Sorok száma:** ~12000
- **Oldalak kategóriánként:** 4 kötelező + 16 concept + 14 entity + 3 comparison + 6 runbook + 13 report
- **PNG-k a riportokban:** 4+ db (hulu: think_nothink + accuracy; per-benchmark breakdown; stat heatmap; gen/ling heatmap)
- **Belső linkek:** minden wiki-oldal legalább 3 másikra hivatkozik
- **Nyelv:** magyar (technikai kifejezések angolul)
- **Módszer:** Karpathy LLM Wiki minta
- **Állapot (2026-07-25, v1.4):** lokális Qwen3-Next-80B IQ3_XXS think benchmark kész (4/5 benchmark, UD N/A 16K-n, 64K-on már megy), a modellnek nincs nothink módja, `report-2026-07-25-lokalis-qwen3-next.md` elkészült.
