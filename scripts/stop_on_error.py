#!/usr/bin/env python
"""
stop_on_error.py — Ollama hívás, ami az első nem-tranziens hibánál megáll.

Használat:
    from stop_on_error import call_ollama_strict, OllamaFatalError
    try:
        response = call_ollama_strict(prompt, model)
    except OllamaFatalError as e:
        cp.mark_stopped(str(e))
        return 1

Stop policy:
  - HTTP 400/404/422: nincs retry (konfigurációs hiba) → stop
  - HTTP 429/5xx: max_retries+1 attempt, Retry-After header alapján várakozás
  - Timeout: max_retries+1 attempt, exponenciális backoff
  - ConnectionError: 0 retry, azonnal stop
"""
import re
import json
import os
import time
import random
import requests
from requests.exceptions import Timeout, ConnectionError


class FatalBackendError(Exception):
    """A futásnak azonnal meg kell állnia — checkpoint mentendő.

    Közös ős minden backend (Ollama, OpenAI-kompatibilis) végzetes hibájához.
    A run_hulu.py ezt a típust kapja el, hogy backend-független maradjon.
    """


class OllamaFatalError(FatalBackendError):
    """Visszafelé kompatibilis: Ollama-specifikus végzetes hiba."""


# Nincs értelme retry-nak — konfigurációs hiba
NO_RETRY_CODES = {400, 404, 422}
# Tranziens — retry lehetséges
RETRYABLE_CODES = {429, 500, 502, 503, 504}

# A generálás felső token-korlátja MINDEN futásnál (Ollama, llama-server, bármely
# OpenAI-kompatibilis backend). 32 768 = 32k. A backend a saját contextjéhez
# igazítja: a prompt + a generált válasz együtt belefér a contextbe (a szerver
# 32k contexten a prompt mérével csökkenti a keretet), vagyis "a kérdés és a
# válasz is belefér a 32k-ba".
MAX_OUTPUT_TOKENS = 32768

# Cloud modelleknél a num_predict=-1-et a felsőbb API 400-zal elutasítja
# ("max_tokens must be positive"). Ilyenkor a modell tényleges maximum output
# token korlátját használjuk (egyszer kémleljük ki, utána cache) — de a
# projektben a generálás felső korlátja mindenütt MAX_OUTPUT_TOKENS (32k),
# tehát a modell saját plafonja csak akkor számít, ha az 32k-nál kisebb.
_MODEL_MAX_OUTPUT: dict[str, int] = {}


def default_num_predict(model: str) -> int:
    """A kimeneti token-plafon a modell típusa szerint.

    Szabály (2026-11-04, felhasználói döntés):
      - **Ollama Cloud** (`:cloud` végződés): **nincs plafon** → -1, amit a
        `resolve_num_predict` a modell saját max output korlátjára old fel.
        Indok: a hosszú gondolkodású modellek (deepseek think) 32k-nál
        elhasalnak (a UD 20%-a üres válasz lett).
      - **lokális modell**: 32 768 token (32k) — a lokális futás marad 32k-n.
    """
    return -1 if model.endswith(":cloud") else MAX_OUTPUT_TOKENS


def resolve_num_predict(model: str, url: str = "http://localhost:11434") -> int:
    """A generálás token-korlátja az adott modellhez (feluplo: MAX_OUTPUT_TOKENS).

    - a mérőszám mindenütt 32 768 (32k); a tényleges keretet a backend
      contextje szabja meg (prompt + válasz együtt belefér a contextbe)
    - `:cloud` modell: ha a modell saját max output korlátja 32k-nál kisebb,
      azt használjuk (különben a cloud API 400-zal elutasítja a kérést).
      A korlátot egyszer, szándékosan túl nagy kéréssel kémleljük ki: a 400-as
      válasz hibaüzenete tartalmazza a pontos maximumot (nem generál tokent).
    """
    if model in _MODEL_MAX_OUTPUT:
        return _MODEL_MAX_OUTPUT[model]
    if not model.endswith(":cloud"):
        _MODEL_MAX_OUTPUT[model] = MAX_OUTPUT_TOKENS
        return MAX_OUTPUT_TOKENS
    limit = MAX_OUTPUT_TOKENS
    try:
        r = requests.post(
            f"{url}/api/generate",
            json={
                "model": model,
                "prompt": "x",
                "stream": False,
                "options": {"num_predict": 10 ** 9},
            },
            timeout=60,
        )
        if r.status_code == 200:
            pass  # nincs gyakorlati plafon → marad a 32k
        else:
            m = re.search(r"maximum output tokens \((\d+)\)", r.text)
            if m:
                limit = min(int(m.group(1)), MAX_OUTPUT_TOKENS)
    except Exception:
        pass
    _MODEL_MAX_OUTPUT[model] = limit
    return limit


def _consume_ollama_stream(resp: requests.Response) -> dict:
    """NDJSON stream összefűzése a nem-streamelt válasz alakjára.

    Miért kell: az Ollama cloud proxy a **60 s-nál hosszabb, nem-streamelt**
    kéréseket `http_502`-vel elutasítja. A hosszú CoNLL-U válaszok (UD think)
    tipikusan 60–300 s-ig tartanak → a nem-streamelt hívás mindig elhal.
    Streamelve a válasz folyamatosan érkezik, így nincs proxy-időkorlát.

    A visszaadott dict a stream **utolsó** chunkja (done_reason, eval_count,
    durations), kiegészítve a teljes `response` és `thinking` szöveggel —
    így a hívók (runners, bírók) változtatás nélkül működnek.
    """
    response_parts: list[str] = []
    thinking_parts: list[str] = []
    final: dict | None = None
    try:
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                continue
            try:
                chunk = json.loads(raw)
            except json.JSONDecodeError:
                continue  # részleges/hibás sor — a stream ettől még él
            if chunk.get("error"):
                raise OllamaFatalError(f"stream_error: {str(chunk['error'])[:200]}")
            if chunk.get("response"):
                response_parts.append(chunk["response"])
            if chunk.get("thinking"):
                thinking_parts.append(chunk["thinking"])
            final = chunk
    finally:
        resp.close()
    if final is None:
        raise OllamaFatalError("stream_empty")
    out = dict(final)
    out["response"] = "".join(response_parts)
    if thinking_parts:
        out["thinking"] = "".join(thinking_parts)
    return out


def call_ollama_strict(
    prompt: str,
    model: str,
    max_retries: int = 2,
    timeout: int = 120,
    url: str = "http://localhost:11434",
    think: bool = False,
    num_predict: int | None = None,
) -> dict:
    """
    Ollama /api/generate hívás, ami az első nem-tranziens hibánál
    OllamaFatalError-t dob. Siker esetén visszaadja a response JSON-t.

    A `think` paraméter szabályozza, hogy a modell gondolkodjon-e:
      - True: a modell gondolkodhat, a gondolkodás a response-ban megjelenik
      - False: a gondolkodás el van nyomva (non-thinking modelleknél nincs hatás)

    A `num_predict` a maximális generált token-szám. **Alapértelmezés (None):
    modell szerint** — Ollama Cloud (`:cloud`) esetén **nincs plafon** (a
    `num_predict` mező kimarad a kérésből → a modell/context szabja meg, a
    modell saját max outputja érvényesül), lokális modellnél **32 768 (32k)**.
    Explicit `-1` szintén "nincs plafon"; a `-2` és egyéb negatív érték
    fenntartott. Indok (2026-11-04, felhasználói döntés): a hosszan gondolkodó
    cloud modellek (deepseek think) 32k-nál elhasaltak — a UD itemek 20%-a
    üres válasz lett, mert a gondolkodás felemésztette a 32k-t.
    A futásidő védőkorlátja a timeout (think: 3600 s/item).

    **Sampling:** a kérés szándékosan nem tartalmaz `temperature`/`top_p`/
    `top_k`/`min_p`/`repeat_penalty` mezőket — minden backend a saját defaultját
    alkalmazza. Ok: a korábbi `temperature: 0.0` (greedy) dekódolás a lokális
    modelleknél repetitív token-loopokat generált (a UD Hungarian futásban
    139/449 item, 31%), ami a válaszokat használhatatlanná tette.
    """
    if num_predict is None:
        num_predict = default_num_predict(model)
    # Sampling paramétert NEM küldünk (se temperature, se top_p/top_k/min_p/
    # repeat_penalty): a backend saját defaultját használjuk. A "temperature: 0"
    # greedy dekódolás a lokális modelleknél degenerált ciklusokba (token loop)
    # futott — ez volt a UD Hungarian 31%-os loop-arányának oka.
    options: dict = {}
    if num_predict >= 0:
        # Negatív (cloud no-cap) esetén a mezőt ELHAGYJUK: az Ollama ilyenkor
        # a modell saját/kontextus szerinti korlátját használja.
        options["num_predict"] = num_predict
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": think,
        "options": options,
    }
    # Opt-in streaming: `BENCH_STREAM=1` esetén a kérés streamelve megy, mert a
    # cloud proxy a 60 s-nál hosszabb nem-streamelt hívásokat 502-vel elutasítja.
    use_stream = os.environ.get("BENCH_STREAM", "") == "1"
    if use_stream:
        payload["stream"] = True
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{url}/api/generate", json=payload, timeout=timeout,
                stream=use_stream,
            )
        except Timeout:
            if attempt < max_retries:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            raise OllamaFatalError(
                f"ollama_timeout after {max_retries + 1} attempts"
            )
        except ConnectionError as e:
            raise OllamaFatalError(f"connection_error: {e}")

        if resp.status_code in NO_RETRY_CODES:
            raise OllamaFatalError(
                f"http_{resp.status_code}: {resp.text[:200]}"
            )
        if resp.status_code in RETRYABLE_CODES:
            if attempt < max_retries:
                # 429-nél különösen: várjunk a Retry-After header alapján
                wait = float(resp.headers.get("Retry-After", 2 ** attempt))
                time.sleep(wait + random.uniform(0, 1))
                continue
            raise OllamaFatalError(
                f"http_{resp.status_code} after {max_retries + 1} attempts"
            )
        if resp.status_code == 200:
            if use_stream:
                return _consume_ollama_stream(resp)
            return resp.json()
        raise OllamaFatalError(f"http_{resp.status_code}: {resp.text[:200]}")
    # Biztonsági fallback (elméletileg elérhetetlen)
    raise OllamaFatalError("ollama_unreachable_state")
