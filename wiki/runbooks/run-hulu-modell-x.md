# HuLU benchmark futtatása egy modellen — checkpoint-aware

*Típus:* runbook
*Forrás(ok):* [NYTK HuLU (hivatalos)](https://hulu.nytud.hu/), [nytud/HuLU GitHub](https://github.com/nytud/HuLU), [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md), [Checkpoint pattern](../concepts/checkpoint-progress.md)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Cél

A **HuLU** (Hungarian Language Understanding) benchmark futtatása egy kiválasztott modellen az Ollama API-n keresztül. Eredmény: per-prompt nyers válaszok + accuracy JSON-ben, készen az aggregációra.

## Háttér: Mi a HuLU?

Magyar nyelvű, többszempontú understanding benchmark:

- **NLI** (mondatpárok): ellentmondás / semleges / következmény
- **Mondatkiegészítés:** melyik szó illik a kontextusba
- **Olvasásértés (RC):** rövid szöveg + kérdés → válasz
- **Szövegosztályozás:** sentiment, téma, stb.

Minden feladatnál 1 helyes válasz van, 0-9 közötti index-szel jelölve.

> **⚠️ FONTOS — Checkpoint:** Ez a script **stop-on-error + resume** szemantikát követ. Ha az Ollama hibát jelez (rate limit, timeout, 5xx, stb.), a futás azonnal megáll, az állapot mentődik, és a script bármikor folytatható ugyanazzal a paranccsal. Részletek: [Checkpoint és folytatható futtatás](../concepts/checkpoint-progress.md).

## Előfeltételek

- Az `eval-hu` conda env aktív ([beállítás](setup-kornyezet.md))
- Ollama szerver fut a `localhost:11434`-en
- A célzott modell le van töltve (`ollama pull qwen3.5:4b`)
- ~500 MB szabad lemezterület

## Lépések

### 1. Mappastruktúra

```bash
cd .
mkdir -p data/hulu results logs state
```

### 2. Dataset letöltés + konverzió (egy lépésben)

> A korábbi `PhilipMay/hulu-bench` dataset megszűnt (401). A `scripts/download_hulu.py` most a NYTK hivatalos HuggingFace dataset-jeit használja (6 NLU sub-task). Offline backup: `--offline` kapcsolóval a `nytud/HuLU` meta-repo git clone-ból olvas.

```bash
pip install datasets
python scripts/download_hulu.py           # HF-ről (ajánlott)
python scripts/download_hulu.py --offline # git clone backup, ha HF nem elérhető
```

A script 6 NLU sub-task validation split-jét tölti le és standardizálja
NYTK/HuCOLA, NYTK/HuCoPA, NYTK/HuRTE, NYTK/HuSST, NYTK/HuWNLI, NYTK/HuCommitmentBank),
per-task magyar promptot épít, és kiírja a `data/hulu/hulu_std.jsonl` fájlt.

Standardizált sor (minta — hucopa):

```json
{"id": "hulu_hucopa_00042", "task": "hucopa",
 "prompt": "Az alábbi premisszához melyik folytatás illik jobban (az oksági viszony alapján)?\nVálaszolj CSAK egy számmal: 0 (első) vagy 1 (második).\n\nPremissza: ...\n0) ...\n1) ...\n\nVálasz:",
 "choices": ["0", "1"], "answer_index": 1, "source": "nytk_hf"}
```

### 3. Benchmark futtatás — checkpoint-aware teljes script

```python
#!/usr/bin/env python
# run_hulu.py — HuLU benchmark futtatása egy modellen, CHECKPOINT-AWARE
# Stop-on-error + resume: ha Ollama hibázik, a futás megáll, de a state megmarad.
# Használat:
#   python run_hulu.py --model qwen3.5:4b          # első indítás vagy folytatás
#   python run_hulu.py --model qwen3.5:4b --reset  # tiszta újrafuttatás
#   python run_hulu.py --model qwen3.5:4b --status  # state megtekintése

import argparse
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

OLLAMA_URL = "http://localhost:11434"
DATASET_PATH = Path("./data/hulu/hulu_std.jsonl")
DEFAULT_RESULTS_DIR = Path("./results")
DEFAULT_STATE_DIR = Path("./state")
LOG_PATH = Path("./logs/hulu_runs.log")

# --- Checkpoint helper (beilleszthető a checkpoint.py fájlba is) ---

class Checkpoint:
    """Állapotmentő + betöltő. Atomi write, hogy részleges state soha ne maradjon."""

    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.state = self._load() or self._initial()

    def _initial(self) -> dict:
        return {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": None,
            "status": "in_progress",
            "stop_reason": None,
            "current_index": 0,
            "completed_ids": [],
            "num_correct": 0,
        }

    def _load(self) -> dict | None:
        if not self.state_path.exists(): return None
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def save(self) -> None:
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        # Atomi write: tmp + os.replace
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8",
            dir=self.state_path.parent, delete=False,
            prefix=".state_", suffix=".tmp",
        ) as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
            tmp_path = f.name
        os.replace(tmp_path, self.state_path)

    def mark_completed(self, item_id: str, is_correct: bool) -> None:
        self.state["current_index"] += 1
        self.state["completed_ids"].append(item_id)
        self.state["num_correct"] += int(is_correct)

    def mark_stopped(self, reason: str) -> None:
        self.state["status"] = "failed_stopped"
        self.state["stop_reason"] = reason
        self.save()

    def mark_completed_full(self) -> None:
        self.state["status"] = "completed"
        self.state["stop_reason"] = None
        self.save()

    @property
    def resume_from(self) -> int:
        return self.state["current_index"]


# --- Stop-on-error helper (rate limit, timeout, 5xx → megállás) ---

class OllamaFatalError(Exception):
    """A futásnak azonnal meg kell állnia — checkpoint mentendő."""

NO_RETRY_CODES = {400, 404, 422}      # konfigurációs hiba, nincs értelme retry-nak
RETRYABLE_CODES = {429, 500, 502, 503, 504}

def call_ollama_strict(prompt: str, model: str, max_retries: int = 2,
                        timeout: int = 120) -> dict:
    """Ollama hívás, ami az első nem-tranziens hibánál OllamaFatalError-t dob."""
    payload = {"model": model, "prompt": prompt, "stream": False,
               "options": {"temperature": 0.0, "num_predict": 32}}
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(f"{OLLAMA_URL}/api/generate",
                                  json=payload, timeout=timeout)
        except Timeout:
            if attempt < max_retries:
                time.sleep(2 ** attempt); continue
            raise OllamaFatalError(f"ollama_timeout after {max_retries+1} attempts")
        except ConnectionError as e:
            raise OllamaFatalError(f"connection_error: {e}")
        if resp.status_code in NO_RETRY_CODES:
            raise OllamaFatalError(f"http_{resp.status_code}: {resp.text[:200]}")
        if resp.status_code in RETRYABLE_CODES:
            if attempt < max_retries:
                wait = float(resp.headers.get("Retry-After", 2 ** attempt))
                time.sleep(wait); continue
            raise OllamaFatalError(f"http_{resp.status_code} after {max_retries+1} attempts")
        if resp.status_code == 200:
            return resp.json()
        raise OllamaFatalError(f"http_{resp.status_code}: {resp.text[:200]}")


# --- Choice extractor (magyar szavakat is kezeli) ---

def extract_choice(text: str, num_choices: int) -> int:
    if not text: return -1
    m = re.search(r"\b([0-9])\b", text)
    if m and 0 <= int(m.group(1)) < num_choices: return int(m.group(1))
    magyar = {"nulla": 0, "egy": 1, "kettő": 2, "három": 3, "négy": 4,
              "öt": 5, "hat": 6, "hét": 7, "nyolc": 8, "kilenc": 9}
    for szo, n in magyar.items():
        if szo in text.lower() and n < num_choices: return n
    return -1


# --- Fő benchmark ciklus ---

def run_benchmark(model: str, limit: int | None, reset: bool,
                   results_dir: Path, state_dir: Path) -> int:
    model_safe = model.replace(":", "-").replace("/", "-")
    state_path = state_dir / model_safe / "hulu.json"

    # Reset esetén töröljük a régi state + results fájlt
    if reset:
        if state_path.exists(): state_path.unlink()
        old_results = results_dir / model_safe / "hulu_results.jsonl"
        if old_results.exists(): old_results.unlink()
        print(f"♻️  Reset: törölve a korábbi state és results fájlok")

    cp = Checkpoint(state_path)
    cp.state["model"] = model
    cp.state["benchmark"] = "hulu"
    if "run_id" not in cp.state:
        cp.state["run_id"] = f"hulu-{model_safe}-{int(time.time())}"

    if cp.state["status"] == "completed":
        print(f"✅ Ez a futás már kész volt: {state_path}")
        print(f"   --reset kapcsolóval újrafuttatható.")
        return 0

    if cp.resume_from > 0:
        print(f"🚀 Folytatás: state betöltve, current_index={cp.resume_from}/{limit or '?'}")

    # Dataset
    items = [json.loads(l) for l in DATASET_PATH.read_text(encoding="utf-8").splitlines()]
    if limit: items = items[:limit]
    total = len(items)

    if cp.resume_from >= total:
        print(f"✅ Már minden kész volt ({cp.resume_from}/{total}).")
        cp.mark_completed_full(); return 0

    out_dir = results_dir / model_safe
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hulu_results.jsonl"
    mode = "a" if (out_path.exists() and cp.resume_from > 0) else "w"

    log_line = (f"{datetime.now(timezone.utc).isoformat()} | {model} | hulu | "
                f"run_id={cp.state['run_id']} | resume_from={cp.resume_from}")
    print(f"🚀 Benchmark: {model} | {total} példa | resume_from={cp.resume_from}")

    try:
        with out_path.open(mode, encoding="utf-8") as fout:
            start = time.time()
            for i in range(cp.resume_from, total):
                item = items[i]
                try:
                    response = call_ollama_strict(item["prompt"], model)
                    raw = response.get("response", "").strip()
                except OllamaFatalError as e:
                    # STOP! Checkpoint + log + tájékoztató üzenet
                    cp.mark_stopped(str(e))
                    elapsed = time.time() - start
                    print(f"\n⛔ STOP @ item {i}/{total}: {e}")
                    print(f"   Eltelt: {elapsed:.0f}s | Kész: {i}/{total} | "
                          f"Részleges acc: {cp.state['num_correct']/max(1,i):.3f}")
                    print(f"   State: {state_path}")
                    print(f"   Folytatás: python run_hulu.py --model {model}")
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{log_line} | FAILED @ {i}/{total} | stop_reason={e}\n")
                    return 1

                pred = extract_choice(raw, len(item["choices"]))
                is_ok = pred == item["answer_index"]
                fout.write(json.dumps({
                    "id": item["id"], "task": item["task"],
                    "prompt": item["prompt"], "choices": item["choices"],
                    "gold": item["answer_index"], "raw_response": raw,
                    "prediction": pred, "correct": is_ok,
                }, ensure_ascii=False) + "\n")
                fout.flush(); os.fsync(fout.fileno())
                cp.mark_completed(item["id"], is_ok)

                if (i + 1) % 50 == 0 or i == total - 1:
                    acc = cp.state["num_correct"] / (i + 1)
                    print(f"  [{i+1:4d}/{total}] acc={acc:.3f} | last: {raw[:40]!r}")
                    cp.save()  # minden 50. itemnél perzisztálunk
    except KeyboardInterrupt:
        cp.mark_stopped("manual_stop")
        print(f"\n⛸  Manual stop (Ctrl+C). State mentve: {state_path}")
        print(f"   Folytatás: python run_hulu.py --model {model}")
        return 130

    # Kész
    cp.mark_completed_full()
    summary = {
        "model": model, "benchmark": "hulu",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": cp.state["run_id"],
        "num_examples": cp.state["current_index"],
        "num_correct": cp.state["num_correct"],
        "accuracy": round(cp.state["num_correct"] / cp.state["current_index"], 4),
        "results_file": str(out_path),
    }
    (out_dir / "hulu_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{log_line} | COMPLETED | acc={summary['accuracy']:.3f} | "
                f"{summary['num_examples']} ex\n")
    print(f"\n✅ KÉSZ: {out_path} | acc={summary['accuracy']:.3f} "
          f"({summary['num_correct']}/{summary['num_examples']})")
    return 0


def show_status(model: str, state_dir: Path):
    model_safe = model.replace(":", "-").replace("/", "-")
    state_path = state_dir / model_safe / "hulu.json"
    if not state_path.exists():
        print(f"Nincs state fájl: {state_path}")
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))
    print(json.dumps(state, indent=2, ensure_ascii=False))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--reset", action="store_true",
                   help="Törli a korábbi state + results fájlokat, nulláról indul")
    p.add_argument("--status", action="store_true",
                   help="Megmutatja a state fájl tartalmát, nem futtat semmit")
    p.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    p.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    args = p.parse_args()

    if args.status:
        show_status(args.model, args.state_dir); return 0

    # Sanity check: Ollama elérhető?
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        if args.model not in models and not args.model.endswith(":cloud"):
            print(f"⚠️  {args.model} nincs telepítve. Futtasd: ollama pull {args.model}")
            if input("Folytatod cloud modellként? [y/N] ").lower() != "y":
                return 1
    except Exception as e:
        print(f"❌ Ollama nem elérhető: {e}")
        return 1

    return run_benchmark(args.model, args.limit, args.reset,
                          args.results_dir, args.state_dir)


if __name__ == "__main__":
    raise SystemExit(main())
```

### 4. Futtatás + 5. Eredmények (gyors)

```bash
conda activate eval-hu && cd .

# Smoke test (minden taskból 10-10 = 60 prompt, ~6 perc)
python run_hulu.py --model qwen3.5:4b --limit 10

# Teljes futás (minden taskból az összes validation rekord = 2581 prompt, ~3 óra)
python run_hulu.py --model qwen3.5:4b

# Smoke, kisebb (minden taskból 5-5 = 30 prompt, ~3 perc)
python run_hulu.py --model qwen3.5:4b --limit 5

# A --limit TASK-SZINTŰ: --limit N → N×6 prompt. Abszolút darabszám
# nem támogatott, mert a JSONL task-sorrendben van (HuCOLA 910, HuCoPA 100,
# ...), és az első 910 prompt mind HuCOLa lenne.

# Think / no-think módok (v1.2.5, 2026-06-08):
# A --mode flag szabályozza, hogy a modell gondolkodjon-e.
#   nothink (default): gondolkodás elnyomva, a modell közvetlenül válaszol
#   think: a modell gondolkodhat, a gondolkodás a response-ban megjelenik
# A két mód eredményei külön mappákba kerülnek:
#   state/{model_safe}-nothink/hulu.json
#   results/{model_safe}-nothink/hulu_results.jsonl
#   state/{model_safe}-think/hulu.json
#   results/{model_safe}-think/hulu_results.jsonl
python run_hulu.py --model qwen3.5:cloud --mode nothink  # no-think (alapértelmezett)
python run_hulu.py --model qwen3.5:cloud --mode think    # thinking mód
python run_hulu.py --model qwen3.5:cloud                 # ugyanaz, mint --mode nothink

# Megállt → megtekintjük a state-et
python run_hulu.py --model qwen3.5:4b --status

# Tiszta újrafuttatás (FIGYELEM: törli a korábbi eredményeket!)
python run_hulu.py --model qwen3.5:4b --reset

# Teljes futtatás (~30 perc modellenként)
python run_hulu.py --model qwen3.5:4b
# ... cloud rate limit elérve ...
# ⛔ STOP @ item 1247/5000: ollama_http_429 after 3 attempts
#    State: state/qwen3.5-4b/hulu.json
#    Folytatás: python run_hulu.py --model qwen3.5:4b

# Várunk egy órát, majd:
python run_hulu.py --model qwen3.5:4b
# 🚀 Folytatás: state betöltve, current_index=1247/5000
# ... kész ...
# ✅ KÉSZ: results/qwen3.5-4b/hulu_results.jsonl | acc=0.781 (3905/5000)
```

**Megállás esetén a log fájl** (`logs/hulu_runs.log`) tartalmazza:
```
2026-06-06T14:45:23+00:00 | qwen3.5:4b | hulu | run_id=hulu-qwen3.5-4b-1717... | resume_from=0 | FAILED @ 1247/5000 | stop_reason=http_429
2026-06-06T15:50:11+00:00 | qwen3.5:4b | hulu | run_id=hulu-qwen3.5-4b-1717... | resume_from=1247 | COMPLETED | acc=0.781 | 5000 ex
```

## Gyakori buktatók

| Tünet | Megoldás |
|-------|----------|
| `accuracy ≈ 0`, raw: `"a"`, `"igen"` | Prompt: "Válaszolj CSAK egy számmal"; a `extract_choice` magyar szavakat is kezel |
| `ReadTimeout` | Növeld `call_ollama` `timeout` értékét vagy csökkentsd `num_predict`-et |
| `model not found` | `ollama pull qwen3.5:4b` |
| Üres/hibás eredmény | `head -3 data/hulu/hulu_std.jsonl` — ha hiba, újra `download_hulu.py` |
| `Connection refused` | `ollama serve &` (vagy `systemctl start ollama`) |

Részletes debug: [Runbook: Debug](debug-modell-nem-valaszol.md).

## Ellenőrző lista

- [ ] `data/hulu/hulu_std.jsonl` létezik, van benne adat
- [ ] `state/{model}/hulu.json` létrejött az első futás után
- [ ] `results/{model}/hulu_results.jsonl` és `hulu_summary.json` létrejött
- [ ] `accuracy` 0 és 1 között
- [ ] `num_examples == len(hulu_results.jsonl sorai)`
- [ ] `logs/hulu_runs.log` tartalmazza a futást
- [ ] Stop esetén a `stop_reason` a state fájlban pontosan jelzi a hibát
- [ ] `--resume` (vagy a sima újrafuttatás) onnan folytatja, ahol abbamaradt

## Kapcsolódó

- [Runbook: Környezet](setup-kornyezet.md) — conda env
- [Runbook: LLM Judge](llm-judge-prompt-template.md) — generatív benchmarkok
- [Runbook: Aggregáció](aggregate-results.md) — JSON-ök összefésülése
- [Runbook: Debug](debug-modell-nem-valaszol.md) — ha a modell nem válaszol
- [Concept: Checkpoint](../concepts/checkpoint-progress.md) — a stop-on-error + resume tervezési elv
- [Overview](../overview.md)
