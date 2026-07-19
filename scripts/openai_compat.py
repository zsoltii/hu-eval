#!/usr/bin/env python
"""
openai_compat.py — OpenAI-kompatibilis backend hívás, ami az első
nem-tranziens hibánál megáll.

Ez a modul lehetővé teszi, hogy a benchmarkokat NE csak közvetlen Ollama
(/api/generate), hanem bármely OpenAI-kompatibilis végpont felé futtassuk:
  - helyi Ollama OpenAI-endpointja (http://localhost:11434/v1) — ez át tudja
    proxyzni a cloud modelleket is (pl. gpt-oss:20b-cloud),
  - később lokálisan futó llama-server (llama.cpp) vagy más OpenAI-kompatibilis
    szerver.

A stop-policy megegyezik a stop_on_error.py-ével (NO_RETRY_CODES / RETRYABLE_CODES /
timeout / connection error), hogy a checkpoint-rendszer (SZENT) változatlan maradjon.

Használat:
    from openai_compat import call_openai_strict, FatalBackendError
    try:
        response = call_openai_strict(prompt, model, base_url=..., api_key=...)
    except FatalBackendError as e:
        cp.mark_stopped(str(e))
        return 1

A válasz egy dict, amiben a "response" kulcs a generált szöveget tartalmazza —
így a run_hulu.py hívókódja backend-független maradhat.
"""
import time
import random
import requests
from requests.exceptions import Timeout, ConnectionError

from stop_on_error import (
    FatalBackendError,
    NO_RETRY_CODES,
    RETRYABLE_CODES,
)


class OpenAIFatalError(FatalBackendError):
    """OpenAI-kompatibilis backend végzetes hibája."""


def call_openai_strict(
    prompt: str,
    model: str,
    max_retries: int = 2,
    timeout: int = 120,
    base_url: str = "http://localhost:11434/v1",
    api_key: str = "ollama",
    think: bool = False,
    num_predict: int = 4096,
) -> dict:
    """
    OpenAI-kompatibilis /v1/chat/completions hívás, ami az első
    nem-tranziens hibánál FatalBackendError-t (OpenAIFatalError) dob.
    Siker esetén visszaad egy dict-et: {"response": <szöveg>, ...meta}.

    Paraméterek:
      - base_url: az OpenAI-kompatibilis végpont /v1 nélküli vagy /v1-es
        gyökere. A függvény mindig a /chat/completions útvonalat fűzi hozzá.
      - api_key: Bearer token. Ollama esetén tetszőleges érték (pl. "ollama").
      - think: Ollama OpenAI-endpointján a gondolkodás az extra_body["think"]
        mezőn keresztül megy. Más backend figyelmen kívül hagyhatja.
      - num_predict: maximális generált token (Ollama options.max_tokens).
    """
    url = base_url.rstrip("/")
    if not url.endswith("/v1"):
        url = url + "/v1"
    endpoint = f"{url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "stream": False,
        "max_tokens": num_predict,
    }
    # Ollama OpenAI-endpoint: think mód az extra_body-n keresztül
    if think:
        payload["extra_body"] = {"think": True}

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                endpoint, headers=headers, json=payload, timeout=timeout
            )
        except Timeout:
            if attempt < max_retries:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            raise OpenAIFatalError(
                f"openai_timeout after {max_retries + 1} attempts"
            )
        except ConnectionError as e:
            raise OpenAIFatalError(f"connection_error: {e}")

        if resp.status_code in NO_RETRY_CODES:
            raise OpenAIFatalError(
                f"http_{resp.status_code}: {resp.text[:200]}"
            )
        if resp.status_code in RETRYABLE_CODES:
            if attempt < max_retries:
                wait = float(resp.headers.get("Retry-After", 2 ** attempt))
                time.sleep(wait + random.uniform(0, 1))
                continue
            raise OpenAIFatalError(
                f"http_{resp.status_code} after {max_retries + 1} attempts"
            )
        if resp.status_code == 200:
            data = resp.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            usage = data.get("usage", {})
            return {
                "response": text,
                "prompt_eval_count": usage.get("prompt_tokens"),
                "eval_count": usage.get("completion_tokens"),
                "total_duration": None,
                "load_duration": None,
                "prompt_eval_duration": None,
                "eval_duration": None,
                "done_reason": None,
            }
        raise OpenAIFatalError(f"http_{resp.status_code}: {resp.text[:200]}")
    # Biztonsági fallback (elméletileg elérhetetlen: a ciklus mindig dob vagy returnöl)
    raise OpenAIFatalError("openai_unreachable_state")
