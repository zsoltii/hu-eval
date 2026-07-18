# Hibakeresés: modell nem válaszol

*Típus:* runbook
*Forrás(ok):* Ollama API docs, projekt belső tapasztalatok
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Tünetek (gyakori hibajelenségek)

1. **Timeout** — kérés elküldve, de 30+ másodpercig nincs válasz
2. **Üres response** — `response["response"]` üres string, nincs hibaüzenet
3. **Zajos/értelmetlen output** — ismétlődő tokenek, koherens magyar szöveg helyett
4. **HTTP 5xx** — Ollama szerver belső hibát jelez
5. **Connection refused** — egyáltalán nem elérhető a szerver
6. **"model not found"** — a modell nincs letöltve helyben

## Diagnózis lépései (sorrendben)

### 1. Szerver elérhetőség
```bash
curl -sS http://localhost:11434/api/tags | head -50
```
Ha nincs válasz, az Ollama nem fut. Indítás:
```bash
ollama serve  # háttérben, vagy systemd service
```

### 2. Modell elérhetőség
```bash
curl -sS http://localhost:11434/api/show -d '{"name":"minimax-m3:cloud"}' | head -30
```
Ha `model not found`, le kell tölteni:
```bash
ollama pull minimax-m3:cloud
```

### 3. Egyszerű tesztkérés
```bash
curl -sS http://localhost:11434/api/generate \
  -d '{"model":"minimax-m3:cloud","prompt":"Helló","stream":false}' \
  | jq .response
```
Ha erre se válaszol, a modell betöltése okozhat problémát (VRAM, kvantálás).

### 4. Network / proxy ellenőrzés
Cloud modellek esetén:
```bash
curl -v https://ollama.com 2>&1 | head -30
```

## Gyakori Ollama hibakódok

| Kód | Jelentés | Megoldás |
|-----|----------|----------|
| 400 | Hibás request formátum | JSON schema ellenőrzés |
| 404 | Modell nem található | `ollama pull <modell>` |
| 500 | Szerver oldali hiba | Ollama logok, modell újratöltés |
| 502/503 | Cloud bridge nem elérhető | Várakozás, retry |

## Retry logika exponenciális visszalépéssel

```python
import time, random
import requests

def call_with_retry(url, payload, max_retries=5, base_delay=2.0):
    """Exponenciális backoff + jitter."""
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json=payload, timeout=120)
            r.raise_for_status()
            return r.json()
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"  ↻ retry {attempt+1}/{max_retries} after {delay:.1f}s ({type(e).__name__})")
            time.sleep(delay)
```

## Fallback modell stratégia

Ha az elsődleges modell tartósan hibázik:

```python
PRIMARY = "minimax-m3:cloud"
FALLBACKS = ["deepseek-v4-pro:cloud", "kimi-k2.6:cloud", "qwen3.5:4b"]

def call_with_fallback(prompt, model=PRIMARY):
    try:
        return ollama_generate(prompt, model=model)
    except OllamaError as e:
        print(f"primary {model} failed: {e}")
        for fb in FALLBACKS:
            try:
                print(f"  ↪ fallback: {fb}")
                return ollama_generate(prompt, model=fb)
            except OllamaError as e2:
                print(f"  ↪ {fb} also failed: {e2}")
                continue
        raise RuntimeError("all models failed")
```

## Üres response debug

Ha a modell `response` mezője üres:
1. **`stream: true` volt használva** — feldolgozatlan chunk-ok lehetnek. Használj `stream: false`-t, vagy gyűjtsd össze a chunkokat.
2. **Stop token túl korai** — a prompt vagy rendszerüzenet EOV tokent generál. Ellenőrizd a `<|im_end|>` vagy hasonló tokeneket.
3. **Context length túllépve** — `n_ctx` konfigot ellenőrizd, vagy rövidítsd a promptot.

## Zajos output (is répétlés)

```python
# Repetíció-detektáló: ha bármely 5-gram 3+ -szor ismétlődik
from collections import Counter

def is_repetitive(text, n=5, threshold=3):
    tokens = text.split()
    if len(tokens) < n * threshold:
        return False
    ngrams = [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
    counts = Counter(ngrams)
    return any(c >= threshold for c in counts.values())

# Használat
result = ollama_generate(prompt, model="minimax-m3:cloud")
if is_repetitive(result["response"]):
    print("⚠️ repetitive output detected, retrying with higher temperature")
    result = ollama_generate(prompt, model="minimax-m3:cloud",
                              options={"temperature": 0.8})
```

## VRAM / memória problémák

Lokális modelleknél (qwen3.5:4b/2b/0.8b):
- **4b modell** ~3-4 GB VRAM kell (q4_K_M kvantálás)
- **2b modell** ~1.5-2 GB VRAM
- **0.8b modell** ~0.6-1 GB VRAM

Ha `cudaMalloc failed` hibát látsz, vagy a modell a betöltéskor meghal:
```bash
# Ellenőrizd a GPU-t
nvidia-smi  # NVIDIA
rocm-smi   # AMD

# Vagy CPU mód:
OLLAMA_NUM_GPU=0 ollama serve
```

## Logok és monitoring

```bash
# Ollama log
journalctl -u ollama -f    # systemd
# vagy ha manuálisan indítva:
tail -f ~/.ollama/logs/server.log
```

## Kapcsolódó

- [Ollama API kliens](../concepts/ollama-api-client.md) - hogyan hívd az API-t
- [Setup környezet](setup-kornyezet.md) - conda env, telepítés
- [LLM-as-a-Judge](../concepts/llm-as-judge.md) - ha a bíró modell hibázik
- [Overview](../overview.md)
