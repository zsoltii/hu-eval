# OpenAI-kompatibilis backend támogatása

*Típus:* concept
*Forrás(ok):* [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat), [llama.cpp server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md), belső projekt (2026-07-19)
*Létrehozva:* 2026-07-19
*Frissítve:* 2026-07-19

---

## Mi ez?

A `hu-eval` benchmark scriptek (`run_hulu.py`, `run_mmlu_hu.py`, `run_hugme.py`, `run_mt_bench_hu.py`, `run_ud_hungarian.py`) mostantól **két backendet** támogatnak:

1. **Ollama natív** (alapértelmezett) — közvetlen `/api/generate` hívás a `http://localhost:11434` felé. A `call_ollama_strict` végzi.
2. **OpenAI-kompatibilis** — `/v1/chat/completions` hívás bármely kompatibilis végpont felé (pl. helyi Ollama `/v1`, llama-server, vLLM, TGI, OpenAI API). A `call_openai_strict` végzi.

A két hívás **azonos stop-policy-vel** rendelkezik: a `FatalBackendError` közös ős, a `NO_RETRY_CODES` / `RETRYABLE_CODES` / timeout / connection error kezelés megegyezik. A checkpoint-rendszer (`Checkpoint`, `state/{model_safe}-{mode}/`, `results/{model_safe}-{mode}/`, atomi write, fsync) **nem változik**.

## CLI kapcsolók

Minden futtató script a következő három új kapcsolót fogadja el:

| Kapcsoló | Default | Leírás |
|----------|---------|--------|
| `--backend {ollama,openai}` | `ollama` | Melyik hívási módot használja a script |
| `--base-url URL` | `http://localhost:11434/v1` | OpenAI backend esetén a végpont gyökere (a script automatikusan hozzáfűzi a `/chat/completions`-t) |
| `--api-key KEY` | `ollama` | Bearer token; Ollama esetén tetszőleges, valódi OpenAI API esetén a `sk-...` kulcs |

Példák:

```bash
# Alapértelmezett (Ollama natív)
python scripts/run_hulu.py --model qwen3.5:cloud

# Helyi Ollama /v1 endpoint (cloud modellek proxyzva)
python scripts/run_hulu.py --model gpt-oss:20b-cloud \
  --backend openai --base-url http://localhost:11434/v1

# llama-server (lokális OpenAI-kompatibilis, nincs Ollama)
python scripts/run_hulu.py --model unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS \
  --backend openai --base-url http://localhost:8080/v1

# Távoli OpenAI-kompatibilis végpont
python scripts/run_hulu.py --model llama-3-70b \
  --backend openai --base-url https://my-llm.example.com/v1 --api-key sk-...
```

## Sanity check (csak induláskor)

| Backend | Ellenőrzés |
|---------|-----------|
| `ollama` | `GET /api/tags` → modell listája. Ha a cél modell nem szerepel és nem `:cloud` végződésű, rákérdez: cloud-ként akarod-e futtatni? |
| `openai` | `GET /models` (Bearer token) — csak ping, nem áll meg hiba esetén, csak figyelmeztet. Az első valódi hiba stop-ol (checkpoint). |

## Stop-policy (backend-független)

Mindkét backend a `stop_on_error.py`-ban definiált szabályokat követi:

- `NO_RETRY_CODES = {400, 404, 422}` — konfigurációs hiba, **azonnal stop**
- `RETRYABLE_CODES = {429, 500, 502, 503, 504}` — 1-2 retry, ha nem javul → **stop, checkpoint**
- Timeout, connection error, modell nem található → **stop, checkpoint**

A `FatalBackendError` a közös ős; a run scriptek `except FatalBackendError as e:` ágában kezelik. A `mark_stopped(str(e))` hívás a `state/{model_safe}-{mode}/<bench>.json`-be ír, a `mark_completed(item_id, is_ok)` pedig a `results/{model_safe}-{mode}/<bench>_results.jsonl`-be. Mindkettő atomi write-tal működik (tmp + `os.replace`), és minden item után `flush` + `fsync`.

## Think flag viselkedése

A `think`/`nothink` flag hatása backend- és modellfüggő:

| Backend | Think flag kezelése |
|---------|--------------------|
| Ollama natív | `think: true` az options-ban — Ollama-specifikus, megbízható |
| Ollama OpenAI-kompatibilis | `extra_body: {think: true}` — Ollama-specifikus, működik |
| llama-server | A `chat_template` alapértelmezetten kezeli a gondolkodást; a request-body-ban nincs rá hatással. A `reasoning_format: none` + `reasoning_in_content: false` beállítással a modell **mindig gondolkodik**, és a gondolkodás a `reasoning_content` mezőbe kerül (a `content` tiszta marad). |
| OpenAI API (nem-Ollama) | A think flag nincs hatással; a modell saját logikája szerint dönt |

A **Thinking modell** (pl. `Qwen3-Next-80B-A3B-Thinking`) llama-server esetén mindkét módban gondolkodik. A `num_predict` értéke a `run_<bench>.py`-ban fix (nothink: 4096 / 2048 / 1024, think: 16384 / 2048); ezek a modellek néha túl kevésnek bizonyulhatnak — a `finish_reason: length` és üres `content` jellemző tünet. Ilyenkor a modell teljesítménye a riportban jelezendő limitáció.

## JSONL kimenet (mindkét backend azonos)

Minden results JSONL-be bekerül egy `"backend": "ollama" | "openai"` mező. A `backend` mező alapján a riportban (és az `aggregate_results.py`-ban) visszakereshető, hogy a sor melyik végpontról származik — ez a **backend-konvenció** része (lásd AGENTS.md "Backend konvenció KÖTELEZŐ a riportban").

Példa (HuLU, openai backend):

```json
{"id": "hulu_hucola_00000", "task": "hucola", "prompt": "...", "choices": ["0", "1"],
 "gold": 1, "raw_response": "1", "prediction": 1, "correct": true,
 "mode": "nothink", "backend": "openai"}
```

## Mikor kell használni?

| Szcenárió | Ajánlott backend |
|-----------|-----------------|
| Modell fut a helyi Ollama szerveren | `ollama` (alapértelmezett) |
| Modell fut a helyi Ollama szerveren, de cloud modelleket is proxyz | `openai --base-url http://localhost:11434/v1` |
| Modell llama.cpp / llama-server mögött fut, **nincs** Ollama | `openai --base-url http://<host>:<port>/v1` |
| Modell vLLM / TGI / TGI-truss mögött fut | `openai --base-url http://<host>:<port>/v1` |
| Modell felhő OpenAI-kompatibilis API (Together, OpenRouter, Anyscale, stb.) | `openai --base-url https://<provider>/v1 --api-key sk-...` |
| Modell natív OpenAI API | `openai --base-url https://api.openai.com/v1 --api-key sk-...` |

A `hu-eval` baseline riportban (`report-2026-07-14.md`) minden modell `ollama-cloud` (`:cloud` végződéssel futott az Ollama Cloud API-n). A lokális openai benchmarkok (pl. Qwen3-Next-80B-A3B-Thinking GGUF) mostantól az új `openai` backenddel futtathatók, és a `backend: openai` mezővel megkülönböztethetők a cloud soroktól.

## Implementációs megjegyzések

- A `call_openai_strict` a `scripts/openai_compat.py:43` — ugyanaz a `requests.post`, ugyanaz a stop-policy, de a `/v1/chat/completions` formátumra. A válaszból a `choices[0].message.content` mezőt olvassa (a `reasoning_content` mezőt figyelmen kívül hagyja — ez a llama-server esetén tartalmazza a gondolkodást, de a tényleges válasz a `content`-ben van).
- Az `extra_body: {think: true}` az Ollama OpenAI-kompatibilis végpontjával kompatibilis; más openai backend figyelmen kívül hagyhatja.
- A `Checkpoint` osztály és a `state/` mappa-kezelés teljesen backend-független — ugyanaz a kód, ugyanaz a JSON formátum.

## Példa: lokális llama-server futtatás

A `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS` modell llama-server mögött (`http://localhost:8080/v1`):

```bash
# HuLU
python scripts/run_hulu.py \
  --model unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS \
  --mode nothink --backend openai --base-url http://localhost:8080/v1

# Smoke (1-1 prompt minden sub-taskból, gyors validáció)
python scripts/run_hulu.py \
  --model unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS \
  --mode nothink --backend openai --base-url http://localhost:8080/v1 \
  --limit 1
```

A mappa-konvenció változatlan: `results/unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS-nothink/hulu_results.jsonl`. A riportban a modell sora a `Modell-kvantálás` szakasz **Backend** oszlopában `openai` értéket kap.

## Kapcsolódó

- [Checkpoint és folytatható futtatás](checkpoint-progress.md) — a közös stop-policy és checkpoint-mechanizmus
- [Runbook: HuLU futtatása modell X-en](../runbooks/run-hulu-modell-x.md) — az alapértelmezett ollama backend használata
- [Runbook: Benchmark futtatás OpenAI backenden](../runbooks/run-modell-x-openai-backend.md) — openai backend lépésről lépésre
- [Cloud vs. Lokális](../comparisons/cloud-vs-lokal.md) — üzemeltetési kontextus
- [Overview](../overview.md) — projekt cél, hatókör
- [SCHEMA](../SCHEMA.md) — oldalformátum
