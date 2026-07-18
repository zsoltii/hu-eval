# Ollama API kliens

*Típus:* concept
*Forrás(ok):* https://github.com/ollama/ollama/blob/main/docs/api.md — hivatalos Ollama REST API; https://github.com/ollama/ollama-python — Python klienskönyvtár; https://requests.readthedocs.io — `requests` HTTP-könyvtár
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Mi az Ollama, és miért kell saját kliens?

Az **Ollama** egy lokális, önálló LLM-futtatókörnyezet, amely egy egyszerű REST API-n keresztül tesz elérhetővé különböző nyelvi modelleket (Llama, Qwen, Mistral, Gemma, stb.). Az Ollama a modellt egyetlen HTTP-végpont mögé teszi, és a `/api/generate`, `/api/chat`, `/api/pull` útvonalakon kommunikál.

Bár van hivatalos Python-kliens (`ollama-python`), a magyar LLM-értékelési projektben egy **saját, újrafelhasználható, jól konfigurálható kliens** hasznosabb, mert:

1. **Streaming támogatás** — hosszú generálások darabonként kaphatók, közben időmérés és logolás.
2. **Timeout és retry** — a cloud-modellek néha lassan válaszolnak; a hálózati hibákat kezelni kell.
3. **Modell-pull** — a benchmark-futtatás előtt ellenőrizni kell, hogy a modell le van-e töltve.
4. **Egységes interfész** — ugyanaz a kliens lokális és cloud modellekhez.
5. **Metrika-gyűjtés** — a válaszidő, token-szám, HTTP-státusz naplózása.

> 🔧 Az Ollama REST API specifikációja: https://github.com/ollama/ollama/blob/main/docs/api.md.

## Az Ollama API alapjai

Az Ollama alapértelmezetten a `http://localhost:11434` címen figyel.

| Végpont | Metódus | Funkció |
|---------|---------|---------|
| `/api/generate` | POST | Egyszeri prompt → generálás |
| `/api/chat` | POST | Többkörös beszélgetés |
| `/api/pull` | POST | Modell letöltése |
| `/api/tags` | GET | Lokálisan elérhető modellek listája |

### `POST /api/generate` — példa

Kérés: `{"model": "qwen3.5:4b", "prompt": "Mi a magyar fővárosa?", "stream": false, "options": {"temperature": 0.0, "num_predict": 256}}`

Válasz: `{"model": "qwen3.5:4b", "response": "Budapest.", "done": true, "total_duration": 1234567890, "prompt_eval_count": 8, "eval_count": 4}`

### `POST /api/chat` — példa

Kérés: `{"model": "qwen3.5:4b", "messages": [{"role": "user", "content": "..."}, ...], "stream": false}`

A chat eltér a generate-től: `messages` tömb `role`+`content` mezőkkel, a válasz `message.content`-ben jön. A `POST /api/pull` **streaming JSON-státuszokat** ad: `{"status": "pulling manifest"}` → `{"status": "downloading", "total": ..., "completed": ...}` → `{"status": "success"}`.

## Teljes `OllamaClient` implementáció (~70 sor)

Az alábbi kód egy tömör, jól dokumentált, újrafelhasználható kliens:

```python
"""ollama_client.py — Ollama REST API kliens.

Támogatja: /api/generate, /api/chat, /api/pull, /api/tags.
Beépített: timeout, retry (exponenciális backoff), streaming.

Használat:
    client = OllamaClient()
    text = client.generate("qwen3.5:4b", "Mondj egy magyar közmondást!")
    client.ensure_model("qwen3.5:4b")   # letölti, ha kell
"""
import json
import time
import logging
from dataclasses import dataclass
import requests

LOG = logging.getLogger("ollama_client")


class OllamaError(RuntimeError):
    """Ollama API hiba."""


@dataclass
class GenResult:
    text: str
    prompt_tokens: int = 0
    response_tokens: int = 0
    total_duration_ns: int = 0


class OllamaClient:
    """Újrafelhasználható Ollama REST API kliens."""

    def __init__(self, host="http://localhost:11434", timeout=120,
                 max_retries=3, backoff=1.5):
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.session = requests.Session()

    def _post(self, path, body, stream=False):
        """POST retry-vel; stream esetén a Response objektumot adja vissza."""
        url = f"{self.host}{path}"
        for attempt in range(1, self.max_retries + 1):
            try:
                r = self.session.post(url, json=body, stream=stream,
                                      timeout=self.timeout)
                if r.status_code == 200:
                    return r
                if r.status_code in (429, 500, 502, 503, 504):
                    raise OllamaError(f"HTTP {r.status_code}: {r.text[:200]}")
                raise OllamaError(f"HTTP {r.status_code} (no retry): {r.text[:200]}")
            except (requests.ConnectionError, requests.Timeout, OllamaError) as e:
                if attempt == self.max_retries:
                    raise OllamaError(f"{path} failed after {attempt} tries: {e}")
                wait = self.backoff ** attempt
                LOG.warning("attempt %d failed: %s — retry in %.1fs", attempt, e, wait)
                time.sleep(wait)

    def generate(self, model, prompt, stream=False, options=None, system=None):
        """Egyszeri generálás. Ha stream=True, iterátort ad vissza."""
        body = {"model": model, "prompt": prompt, "stream": stream}
        if options: body["options"] = options
        if system:  body["system"] = system
        if stream:
            return self._stream("/api/generate", body)
        d = self._post("/api/generate", body).json()
        return GenResult(
            text=d.get("response", ""),
            prompt_tokens=d.get("prompt_eval_count", 0),
            response_tokens=d.get("eval_count", 0),
            total_duration_ns=d.get("total_duration", 0),
        )

    def chat(self, model, messages, stream=False, options=None):
        """Többkörös chat. messages: [{"role":..., "content":...}, ...]"""
        body = {"model": model, "messages": messages, "stream": stream}
        if options: body["options"] = options
        if stream:
            return self._stream("/api/chat", body)
        return self._post("/api/chat", body).json().get("message", {}).get("content", "")

    def _stream(self, path, body):
        """Iterátor, ami a rész-szövegeket adja vissza."""
        r = self._post(path, body, stream=True)
        for line in r.iter_lines(decode_unicode=True):
            if not line: continue
            try: chunk = json.loads(line)
            except json.JSONDecodeError: continue
            key = "message" if path == "/api/chat" else "response"
            yield chunk.get(key, {}).get("content", "") if key == "message" else chunk.get(key, "")
            if chunk.get("done"): break

    def pull(self, model):
        """Modell letöltése a registry-ből. Streamelve logolja a státuszt."""
        r = self._post("/api/pull", {"model": model, "stream": True}, stream=True)
        for line in r.iter_lines(decode_unicode=True):
            if not line: continue
            try: chunk = json.loads(line)
            except json.JSONDecodeError: continue
            if "error" in chunk:
                raise OllamaError(f"Pull error: {chunk['error']}")
            status = chunk.get("status", "")
            if status:
                LOG.info("Pull %s: %s", model, status)
            if status == "success":
                return

    def list_models(self):
        """Lokálisan elérhető modellek listája."""
        r = self.session.get(f"{self.host}/api/tags", timeout=self.timeout)
        r.raise_for_status()
        return r.json().get("models", [])

    def has_model(self, model):
        """True, ha a modell már le van töltve lokálisan."""
        try: models = self.list_models()
        except requests.RequestException: return False
        return any(m.get("name") == model for m in models)

    def ensure_model(self, model):
        """Ha a modell nincs meg, letölti."""
        if not self.has_model(model):
            LOG.info("Pull %s...", model)
            self.pull(model)

    def close(self):
        self.session.close()

    def __enter__(self): return self
    def __exit__(self, *a): self.close()
```

A kliens kb. **70 sor** (kommentek nélkül), az alábbi tulajdonságokkal:

- **Timeout**: konfigurálható, alapértelmezetten 120 másodperc.
- **Retry**: exponenciális backoff (`1.5^n` s), 5xx és 429 státuszkódoknál.
- **Streaming**: `stream=True` esetén iterátort ad vissza.
- **Modell-pull**: `ensure_model()` letölti, ha még nincs meg.
- **Session**: `requests.Session()` újrahasznosítja a TCP-kapcsolatokat.
- **Logging**: minden hívás logolva van.

## Használati példák

### Egyszerű és streaming generálás

```python
from ollama_client import OllamaClient

with OllamaClient() as c:
    r = c.generate("qwen3.5:4b", "Mondj egy magyar közmondást!")
    print(r.text, r.prompt_tokens, r.response_tokens)

    for chunk in c.generate("qwen3.5:4b", "Írj egy verset.", stream=True):
        print(chunk, end="", flush=True)
```

### Chat és automatikus modell-letöltés

```python
c = OllamaClient()
c.ensure_model("qwen3.5:4b")   # letölti, ha kell
messages = [
    {"role": "user", "content": "Mi a magyar fővárosa?"},
    {"role": "assistant", "content": "Budapest."},
    {"role": "user", "content": "És hány lakosa van?"},
]
print(c.chat("qwen3.5:4b", messages))
```

### Benchmark-futtatás (HuSenti)

```python
def run_husenti(model, dev_examples):
    c = OllamaClient(timeout=60)
    c.ensure_model(model)
    correct = total = 0
    for ex in dev_examples:
        prompt = ("Döntsd el, hogy az alábbi magyar mondat pozitív (1) vagy "
                  "negatív (0) érzelmet fejez ki. Válaszolj CSAK egy számmal.\n\n"
                  f"Mondat: {ex['text']}\n\nVálasz:")
        r = c.generate(model, prompt, options={"temperature": 0.0, "num_predict": 4})
        pred = r.text.strip()[:1] or "?"
        if pred == str(ex["label"]): correct += 1
        total += 1
    return {"model": model, "accuracy": correct / total}
```

## Timeout és retry

- **5xx és 429 státuszkódok** → retry (3 próba, exponenciális backoff: `1.5^n` s).
- **4xx státuszkódok** (kliens hiba, pl. rossz modellnév) → **nincs retry**, azonnal `OllamaError`.
- **ConnectionError, Timeout** → retry, mert átmeneti hálózati hibák.
- 429 esetén érdemes a `Retry-After` fejlécet is figyelembe venni.

A `timeout` konfigurálható: egész szám (teljes kérésre), vagy `(connect, read)` tuple.

```python
OllamaClient(timeout=10)            # szigorú
OllamaClient(timeout=(5, 180))      # 5s connect, 180s read (lassú cloud)
```

## Streaming

A streaming hasznos, ha hosszú a generálás (>5s), vagy az első token latency-t (TTFT) mérjük, vagy a kliens 10s után timeout-olna. A `stream=True` esetén a függvény iterátort ad, ami rész-szövegeket yieldel.

## Gyakori buktatók

1. **`requests.Session()` nem thread-safe** — több szálon `threading.Lock` kell.
2. **Streaming timeout** — a `_post(..., stream=True)` kikapcsolja a timeout-ot; a stream-iterátorban külön kell ellenőrizni.
3. **`has_model` csak lokális cache-t nézi** — cloud modelleknél hamisat ad, de a `generate` működhet; a `pull` csak lokális modellekre értelmes.
4. **`prompt_eval_count` / `eval_count` verziónként változhat** — régebbi Ollama verziókban hiányozhatnak; a kliens default 0-t ad.
5. **A `system` mező nem minden modellnél támogatott** — Qwen3.5 és Llama3 igen, egyes modellek figyelmen kívül hagyják.
6. **Hosszú prompt** — ha >4096 token, a kliens nem darabolja fel automatikusan.
7. **HTTP-kapcsolat bontása** — mindig használjuk a `with` kontextuskezelőt, vagy hívjuk meg a `close()`-t.

## Bővítési lehetőségek

- **Async verzió** (`httpx` + `asyncio`) — párhuzamos modell-futtatás.
- **Rate-limiter** (token bucket) — cloud kvótakorlátokhoz.
- **Prompt-cache** — azonos promptok sokszori küldéséhez.
- **Strukturált output** — a `format: "json"` paraméter JSON kimenetet kényszerít ki.

## Kapcsolódó

- [Overview](../overview.md) — projekt cél
- [SCHEMA](../SCHEMA.md) — wiki-formátum
- [HuLU Benchmark](hulu-benchmark.md) — kliens hívásával futtatható
- [MMLU-HU](mmlu-hu.md) — kliens hívásával futtatható
- [ARC + GSM8K-HU](arc-gsm8k-hu.md) — kliens hívásával futtatható
- [Perplexitás](perplexity-hu.md) — PPL mérése
