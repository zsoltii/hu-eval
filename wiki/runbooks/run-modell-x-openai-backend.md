# Benchmark futtatása OpenAI-kompatibilis backenden — lépésről lépésre

*Típus:* runbook
*Forrás(ok):* [OpenAI-kompatibilis backend támogatása](../concepts/openai-backend-support.md), [Setup környezet](setup-kornyezet.md), belső projekt (2026-07-19)
*Létrehozva:* 2026-07-19
*Frissítve:* 2026-07-19

---

## Cél

Ha a vizsgálandó modell **nem az Ollama szerveren fut**, hanem bármilyen OpenAI-kompatibilis végponton (helyi Ollama `/v1`, llama-server, vLLM, TGI, felhő OpenAI API), ez a runbook lépésről lépésre leírja, hogyan kell a benchmarkot futtatni, judge-ot hívni, és az eredményt a riportba illeszteni.

## Előfeltételek

- Az `eval-hu` conda env aktív ([beállítás](setup-kornyezet.md))
- A cél OpenAI-kompatibilis végpont elérhető (curl-teszt)
- A cél modell **pontos neve** a végponton (`/v1/models` listából)
- Ha llama-server, akkor a modell `n_ctx` értéke ≥ 4096 (a benchmark-promptok max. hossza)
- A dataset-ek a `data/` mappában (lásd: setup-kornyezet.md 6. szakasz)

## Lépések

### 1. Végpont ellenőrzése

```bash
# Ollama /v1 endpoint
curl -s http://localhost:11434/v1/models | head

# llama-server (vagy más openai backend)
curl -s http://localhost:8080/v1/models

# Felhő OpenAI-kompatibilis (Together, OpenRouter, stb.)
curl -s https://api.together.xyz/v1/models -H "Authorization: Bearer $TOGETHER_API_KEY"
```

A válasz `data[].id` (vagy `models[].name`) mezője a modell **pontos neve**, amit a `--model` kapcsolónak át kell adni. Például: `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS`.

### 2. Smoke teszt (1-1 prompt, gyors validáció)

Mielőtt teljes futtatást indítasz, érdemes 1-1 prompttal ellenőrizni, hogy a parser, a judge, és a gondolkodás-kezelés működik-e:

```bash
# HuLU — task-szintű limit: --limit 1 → 1 HuCOLA + 1 HuCoPA + ... = 6 prompt
python scripts/run_hulu.py \
  --model <MODELL_NÉV> --mode nothink \
  --backend openai --base-url http://localhost:8080/v1 --limit 1

# MMLU-HU
python scripts/run_mmlu_hu.py \
  --model <MODELL_NÉV> --mode nothink \
  --backend openai --base-url http://localhost:8080/v1 --limit 1

# HuGME, MT-Bench-HU, UD Hungarian — hasonlóan
```

A smoke teszt tipikusan 2-5 perc / benchmark, és a JSONL-be azonnal íródnak a sorok. Ha a `prediction` mező értelmes (nem `-1` mindenhol), a parser és a modell interakció rendben van.

### 3. Teljes futtatás — szekvenciális vagy párhuzamos

A llama-server `total_slots: 1`, tehát **szekvenciális** futtatás kötelező. A futtatás hossza modell- és hardver-függő; konzervatív becslés: 5-15 perc / 100 prompt lokális GPU-val, 10-30 perc / 100 prompt CPU-val.

```bash
# HuLU nothink
python scripts/run_hulu.py --model <MODELL_NÉV> --mode nothink \
  --backend openai --base-url http://localhost:8080/v1

# HuLU think
python scripts/run_hulu.py --model <MODELL_NÉV> --mode think \
  --backend openai --base-url http://localhost:8080/v1

# MMLU-HU
python scripts/run_mmlu_hu.py --model <MODELL_NÉV> --mode nothink \
  --backend openai --base-url http://localhost:8080/v1
python scripts/run_mmlu_hu.py --model <MODELL_NÉV> --mode think \
  --backend openai --base-url http://localhost:8080/v1

# HuGME (generatív — judge kötelező utána)
python scripts/run_hugme.py --model <MODELL_NÉV> --mode nothink \
  --backend openai --base-url http://localhost:8080/v1
python scripts/run_hugme.py --model <MODELL_NÉV> --mode think \
  --backend openai --base-url http://localhost:8080/v1

# MT-Bench-HU
python scripts/run_mt_bench_hu.py --model <MODELL_NÉV> --mode nothink \
  --backend openai --base-url http://localhost:8080/v1
python scripts/run_mt_bench_hu.py --model <MODELL_NÉV> --mode think \
  --backend openai --base-url http://localhost:8080/v1

# UD Hungarian
python scripts/run_ud_hungarian.py --model <MODELL_NÉV> --mode nothink \
  --backend openai --base-url http://localhost:8080/v1
python scripts/run_ud_hungarian.py --model <MODELL_NÉV> --mode think \
  --backend openai --base-url http://localhost:8080/v1
```

A futtatás **stop-on-error + resume**: ha bármi hiba történik (timeout, rate limit, 5xx, connection error), a script `state/{model_safe}-{mode}/<bench>.json`-be checkpointol, és a fenti parancs bármikor újraindítható.

### 4. Judge hívás (generatív benchmarkok után)

A HuGME és MT-Bench-HU **bíró modellt** igényelnek — a bíró a `deepseek-v4-pro:cloud` (Ollama Cloud, 2026-07-19 óta hivatalos bíró). A bíró hívásához a `judge_hugme.py` / `judge_mt_bench.py` saját maga kezeli a backendet (alapértelmezetten ollama).

```bash
# HuGME judge
python scripts/judge_hugme.py --model <MODELL_NÉV> --mode nothink
python scripts/judge_hugme.py --model <MODELL_NÉV> --mode think

# MT-Bench-HU judge (baseline = deepseek-v4-flash:cloud a GSB összehasonlításhoz)
python scripts/judge_mt_bench.py --model <MODELL_NÉV> --mode nothink \
  --baseline deepseek-v4-flash:cloud
python scripts/judge_mt_bench.py --model <MODELL_NÉV> --mode think \
  --baseline deepseek-v4-flash:cloud
```

> **Self-bias korlát (SZENT):** a bíró modell nem értékelheti saját magát. Ha a bíró és a vizsgált modell megegyezik (pl. a vizsgált modell is `deepseek-v4-pro`), a judge-ot független bíróval kell futtatni, vagy a self-bias szabály szerint kivételezni. Részletek: [LLM-as-a-Judge módszertan](../concepts/llm-as-judge.md).

### 5. Aggregáció

```bash
python scripts/aggregate_results.py
```

Ez legenerálja a composite CSV-t (`wiki/reports/composite_scores-YYYY-MM-DD.csv`), a heatmap-eket, és a riport vázát. Az új modell automatikusan megjelenik a táblákban, ha a JSONL-ek megvannak és a `model_safe` mappa a `results/` alatt megtalálható.

### 6. Riport kiegészítés

A `report-YYYY-MM-DD-<modell>.md` fájl a `riport-template.md` alapján készül. Kötelező elemek:

- **Fejléc / Modell-kvantálás** — a `Backend` oszlopban `openai` (vagy a pontos végpont, pl. `openai-llama-server-localhost:8080`)
- **Per-benchmark leíró blokk** — minden benchmarknál a "Mit tesztel" bekezdés (a sablon tartalmazza)
- **HuLU per-sub-task bontás** — 6 NLU sub-task külön-külön (HuCOLA, HuCoPA, HuRTE, HuSST, HuWNLI, HuCB)
- **Kompozit táblák (A + B)** — az új modell sorokkal
- **Limitációk** — openai backend specifikus limitációk (pl. llama-server `reasoning_format: none` → mindig gondolkodik, a nothink és think mód érdemben nem tér el)

## Mappa-konvenció (változatlan)

A `--model` argumentum határozza meg a `model_safe` mappanevet:

```
model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
```

Példák:
- `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` + `nothink` → `unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-nothink`
- `gpt-oss:20b-cloud` + `think` → `gpt-oss-20b-cloud-think`
- `llama-3-70b` + `nothink` → `llama-3-70b-nothink`

A `results/`, `state/`, `logs/` mappák az AGENTS.md szerint `.gitignore`-olva vannak — a futás adatai nem kerülnek verziókezelésbe.

## Gyakori buktatók

### A) A modell neve nem stimmel a `/v1/models` listával

**Tünet:** `http_404: model '<név>' not found` a `FatalBackendError` üzenetben, a futás azonnal leáll.

**Ok:** a `--model` argumentum nem egyezik a végponton regisztrált modell nevével.

**Megoldás:** `curl -s http://localhost:8080/v1/models` → a `data[].id` (vagy `models[].name`) pontos értékét kell használni, **minden** karaktert (kettőspont, per, nagybetű).

### B) A gondolkodás elfogyasztja a `num_predict` limitet

**Tünet:** `finish_reason: length` és üres `raw_response` (vagy `"0"`, ami az alapértelmezett fallback). A HuLU-nál `prediction: -1` látszik.

**Ok:** Thinking modell llama-server esetén mindig gondolkodik. A `num_predict=4096` (nothink) és `num_predict=16384` (think) értékek a `run_<bench>.py`-ban fixek — néha kevésnek bizonyulnak.

**Megoldás:** rövid távon a `--limit` csökkentése és a kihagyott itemek utólagos újrafuttatása; hosszabb távon a `num_predict` paraméter CLI-ból konfigurálhatóvá tétele (TODO).

### C) A `content` üres, de a `reasoning_content` tele van

**Tünet:** a `run_*.py` a `choices[0].message.content` mezőt olvassa, ami üres, mert a llama-server a gondolkodást a `reasoning_content`-be, a tényleges választ pedig egy későbbi `choices[].message.content` üzenetbe teszi.

**Megoldás:** normál esetben a `content` a gondolkodás **után** tartalmazza a választ. Ha üres, a modell nem fejezte be a gondolkodást a `num_predict` limiten belül — lásd (B).

### D) Connection error a futás közben

**Tünet:** `connection_error: <URL>` a `FatalBackendError` üzenetben. A futás leáll, checkpoint mentődik.

**Megoldás:** ellenőrizd a végpontot (`curl <base-url>/models`), indítsd újra a llama-servert vagy a backendet, majd futtasd újra ugyanazt a parancsot — a script a `state/` checkpointból folytatja.

### E) A `n_ctx` túl kicsi

**Tünet:** `context length exceeded` vagy `prompt too long` hibaüzenet.

**Ok:** a modell tanítási context-je kisebb, mint a prompt + generation együtt. Pl. a Qwen3-Next-80B llama-server `n_ctx: 16128`, de a tanítása 262144 — ez a prompt szempontjából elég, de egyes hosszú MMLU-HU 5-shot promptok megközelíthetik.

**Megoldás:** a llama-server indításánál a `--ctx-size` kapcsolóval növeld a `n_ctx`-et (ha a VRAM engedi).

## Kapcsolódó

- [Concept: OpenAI-kompatibilis backend](../concepts/openai-backend-support.md) — elméleti háttér, CLI, stop-policy
- [Concept: Checkpoint és folytatható futtatás](../concepts/checkpoint-progress.md) — a közös stop-policy
- [Runbook: Setup környezet](setup-kornyezet.md) — conda env, dataset-ek, hibafelderítés
- [Runbook: HuLU futtatása modell X-en](run-hulu-modell-x.md) — az alapértelmezett ollama backend használata
- [Runbook: Aggregáció](aggregate-results.md) — composite score, riport
- [Runbook: LLM-judge prompt template](llm-judge-prompt-template.md) — bíró modell prompt
- [Cloud vs. Lokális](../comparisons/cloud-vs-lokal.md) — üzemeltetési kontextus
- [AGENTS.md](../../AGENTS.md) — Modell-kvantálás, Backend, Think-mód konvenciók
