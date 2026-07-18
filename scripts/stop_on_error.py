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
import time
import random
import requests
from requests.exceptions import Timeout, ConnectionError


class OllamaFatalError(Exception):
    """A futásnak azonnal meg kell állnia — checkpoint mentendő."""


# Nincs értelme retry-nak — konfigurációs hiba
NO_RETRY_CODES = {400, 404, 422}
# Tranziens — retry lehetséges
RETRYABLE_CODES = {429, 500, 502, 503, 504}


def call_ollama_strict(
    prompt: str,
    model: str,
    max_retries: int = 2,
    timeout: int = 120,
    url: str = "http://localhost:11434",
    think: bool = False,
    num_predict: int = 4096,
) -> dict:
    """
    Ollama /api/generate hívás, ami az első nem-tranziens hibánál
    OllamaFatalError-t dob. Siker esetén visszaadja a response JSON-t.

    A `think` paraméter szabályozza, hogy a modell gondolkodjon-e:
      - True: a modell gondolkodhat, a gondolkodás a response-ban megjelenik
      - False: a gondolkodás el van nyomva (non-thinking modelleknél nincs hatás)

    A `num_predict` paraméter a maximális generált token-szám (Ollama options.num_predict).
    Alapértelmezetten 4096 (nothink mód). Think módban 16384-et kell használni,
    mert a gondolkodás néha > 2048 tokent igényel, és a válasz üres marad (done:length).
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": think,
        "options": {"temperature": 0.0, "num_predict": num_predict},
    }
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{url}/api/generate", json=payload, timeout=timeout
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
            return resp.json()
        raise OllamaFatalError(f"http_{resp.status_code}: {resp.text[:200]}")
