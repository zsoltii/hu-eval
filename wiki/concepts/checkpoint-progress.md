# Checkpoint és folytatható futtatás

*Típus:* concept
*Forrás(ok):* [Ollama API rate-limit megoldások](https://github.com/ollama/ollama/blob/main/docs/api.md), checkpoint-pattern (belső döntés)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Mi ez?

A magyar LLM értékelési suite minden benchmark scriptje **stop-on-error + resume** szemantikát követ:

1. **Ha bármilyen hiba történik az Ollama felé küldött kérésben** (timeout, HTTP 429 token-limit elfogyott, 5xx szerverhiba, network reset, modell lehalt), a script **azonnal megáll** a feldolgozásban.
2. Az aktuális állapotot egy **JSON state fájlba** írja (atomic write, így részleges állapot nem maradhat).
3. A log fájlban **pontosan rögzíti, hol tartott** (melyik item ID-nál, hány darab kész, hány maradt).
4. A script **bármikor újraindítható** ugyanazzal a paranccsal — a state-ből tölti vissza, hol tartott, és onnan folytatja.

## Miért kell ez?

A magyar LLM értékelés **lassú, drága, és bármikor megszakadhat**:

- **Lassú:** egy teljes HuLU futtatás 6 modellen, 2000-5000 prompt/modell ⇒ 12-24 óra gépidő
- **Drága:** cloud modellek token-limitje naponta/óránként limitált (főleg a drágább modelleknél, mint a `kimi-k2.6:cloud` vagy a `qwen3.5:cloud`)
- **Törékeny:** Ollama szerver újraindulhat, cloud bridge átmenetileg elérhetetlenné válhat, network glitch lehet, a modell folyamata elszállhat VRAM-hibával

Ha egy 4 órás futás a 2 óra 45 percnél meghal, és a script nem checkpointol, **az addigi munka elveszik**. Ez elfogadhatatlan.

## A tervezési elvek

### 1. **Stop on first hard error** — ne nyeljük el a hibát

A retry-with-backoff (`tenacity` decorator) hasznos átmeneti hibáknál (1-2 retry), de:

- **HTTP 429 (rate limit)**: 1-2 retry, ha nem javul → **stop, checkpoint**
- **HTTP 5xx (szerver hiba)**: 1-2 retry, ha nem javul → **stop, checkpoint**
- **Timeout (120s)**: 1 retry, ha megint timeout → **stop, checkpoint**
- **Connection reset / refused**: 0 retry (a szerver nem él) → **stop, checkpoint**
- **"model not found"**: 0 retry (konfigurációs hiba) → **stop, checkpoint, fail loud**

A lényeg: ha a hiba nem triviálisan átmeneti, **ne pazaroljunk további tokeneket** (cloud költség!), hanem álljunk meg, hogy az ember beavatkozhasson.

### 2. **JSON state file — atomic write**

A futás aktuális állapota egy JSON fájl:

```json
{
  "run_id": "hulu-qwen3.5-4b-2026-06-06-12-30",
  "benchmark": "hulu",
  "model": "qwen3.5:4b",
  "started_at": "2026-06-06T12:30:00+00:00",
  "last_updated": "2026-06-06T14:45:23+00:00",
  "status": "in_progress | completed | failed_stopped",
  "stop_reason": "ollama_http_429_rate_limit | timeout | manual | ...",
  "current_index": 1247,
  "total": 5000,
  "completed_ids": ["hulu_00001", "hulu_00002", ...],
  "results_file": "results/qwen3.5-4b/hulu_results.jsonl",
  "summary": {
    "num_completed": 1247,
    "num_correct": 891
  }
}
```

**Atomic write:** először `state.json.tmp` fájlba írunk, majd `os.replace()`-szel atomi rename. Így ha a script menetközben meghal, soha nem marad félig írt state fájl.

### 3. **Resume = `--resume` flag**

A script parancssori kapcsolókkal támogatja a resume-t:

```bash
# Első indítás
python run_hulu.py --model qwen3.5:4b

# Ha leállt: ellenőrizd a state-et, majd indítsd újra ugyanazzal
python run_hulu.py --model qwen3.5:4b
# → a script automatikusan felismeri a state fájlt, betölti, és onnan folytatja

# Explicit resume másik könyvtárból
python run_hulu.py --model qwen3.5:4b --state-dir ./state/hulu

# Nullázás, tiszta újrafuttatás
python run_hulu.py --model qwen3.5:4b --reset
```

A `--reset` flag törli a state fájlt és a korábbi `*_results.jsonl` tartalmát, és a nulláról indul.

### 4. **Stop reason kategorizálás — log + Slack értesítés (opcionális)**

A `stop_reason` mező egyike:

| Kód | Jelentés | Teendő |
|-----|----------|--------|
| `completed` | Minden kész | Aggregátor futtatása |
| `ollama_http_429` | Rate limit | Várj, indítsd újra később (`--resume`) |
| `ollama_http_5xx` | Szerver hiba | Ellenőrizd az Ollama-t, indítsd újra |
| `ollama_timeout` | Timeout | Csökkentsd a `--limit`/`--batch-size` értéket, vagy növeld a timeout-ot |
| `connection_error` | Szerver nem elérhető | `ollama serve` indítása, majd `--resume` |
| `model_not_found` | Modell hiányzik | `ollama pull <modell>`, majd `--resume` |
| `manual_stop` | Ctrl+C | `--resume` folytatja |
| `json_parse_error` | Válasz nem feldolgozható | Ellenőrizd a prompt-ot, lehet a modell rossz |

A log fájl (`logs/hulu_runs.log`) minden futásról pontos sort ír: `timestamp | model | run_id | status | stop_reason | num_completed | num_correct`.

### 5. **A JSONL eredményfájl append-only**

A `*_results.jsonl` **minden sikeres item után azonnal íródik** (flush + fsync), nem csak a végén. Ha a script bármikor leáll, a részeredmények megmaradnak. A `num_completed` mező a state fájlban = a JSONL sorainak száma (konzisztencia-ellenőrzés).

## Implementációs segédlet

### Minimális checkpoint helper (`checkpoint.py`)

```python
import json, os, tempfile
from pathlib import Path
from datetime import datetime, timezone

class Checkpoint:
    """Állapotmentő + betöltő osztály hosszú futású benchmarkokhoz."""

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
        }

    def _load(self) -> dict | None:
        if not self.state_path.exists(): return None
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None  # sérült state = tiszta újraindítás

    def save(self) -> None:
        """Atomi write: tmp fájl + os.replace."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8",
            dir=self.state_path.parent, delete=False,
            prefix=".state_", suffix=".tmp"
        ) as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
            tmp_path = f.name
        os.replace(tmp_path, self.state_path)  # atomic

    def mark_completed(self, item_id: str) -> None:
        self.state["current_index"] += 1
        self.state["completed_ids"].append(item_id)
        # Ne mentsünk minden egyes itemnél — túl lassú. Csak minden N-ediknél.

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
        """Hányadik item-től kell folytatni."""
        return self.state["current_index"]
```

### Stop-on-error helper (`stop_on_error.py`)

```python
import time, random, requests
from requests.exceptions import (
    Timeout, ConnectionError, HTTPError,
)

# Hard-stop policy: mely státuszkódokra ne próbálkozzunk újra
NO_RETRY_CODES = {400, 404, 422}  # konfigurációs hiba
RETRYABLE_CODES = {429, 500, 502, 503, 504}

class OllamaFatalError(Exception):
    """Olyan hiba, ami mellett a futásnak meg kell állnia."""

def call_ollama_with_stop(url: str, payload: dict, max_retries: int = 2):
    """
    Ollama hívás, ami az első nem-tranziens hibánál megáll.

    Visszatérés: (response_dict, None) siker esetén
                 (None, OllamaFatalError(reason)) leállás esetén
    """
    for attempt in range(max_retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=120)
        except Timeout:
            if attempt < max_retries:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            return None, OllamaFatalError(f"timeout after {max_retries+1} attempts")
        except ConnectionError as e:
            return None, OllamaFatalError(f"connection_error: {e}")

        if r.status_code in NO_RETRY_CODES:
            return None, OllamaFatalError(f"http_{r.status_code}: {r.text[:200]}")
        if r.status_code in RETRYABLE_CODES:
            if attempt < max_retries:
                # 429-nél különösen: várjunk a Retry-After header alapján
                wait = float(r.headers.get("Retry-After", 2 ** attempt))
                time.sleep(wait + random.uniform(0, 1))
                continue
            return None, OllamaFatalError(f"http_{r.status_code} (max retries reached)")
        if r.status_code == 200:
            return r.json(), None
        return None, OllamaFatalError(f"http_{r.status_code}: {r.text[:200]}")
```

### Benchmark script váz (`run_hulu.py` — checkpoint-aware)

```python
import argparse, json, re, time
from pathlib import Path
from checkpoint import Checkpoint
from stop_on_error import call_ollama_with_stop, OllamaFatalError

def run_benchmark(model: str, limit: int | None, reset: bool):
    # 1. State betöltése / inicializálása
    state_path = Path(f"./state/{model.replace(':','-')}/hulu.json")
    if reset and state_path.exists():
        state_path.unlink()
    cp = Checkpoint(state_path)
    cp.state["model"] = model
    cp.state["benchmark"] = "hulu"
    cp.state["run_id"] = f"hulu-{model.replace(':','-')}-{int(time.time())}"

    # 2. Dataset betöltése
    items = [json.loads(l) for l in Path("./data/hulu/hulu_std.jsonl").read_text(encoding="utf-8").splitlines()]
    if limit: items = items[:limit]

    # 3. JSONL megnyitása (append, ha van state; új, ha nincs)
    out_dir = Path(f"./results/{model.replace(':','-')}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hulu_results.jsonl"
    mode = "a" if (out_path.exists() and cp.resume_from > 0) else "w"
    with out_path.open(mode, encoding="utf-8") as fout:

        # 4. Fő ciklus — onnan folytatja, ahol abbahagyta
        start_idx = cp.resume_from
        for i, item in enumerate(items[start_idx:], start=start_idx):
            response, err = call_ollama_with_stop(
                "http://localhost:11434/api/generate",
                {"model": model, "prompt": item["prompt"], "stream": False},
            )

            if err is not None:
                # STOP! Checkpoint mentése
                cp.mark_stopped(str(err))
                print(f"\n⛔ STOP: {err}")
                print(f"   Állapot mentve: {state_path}")
                print(f"   Kész: {i}/{len(items)}. Folytatás: python run_hulu.py --model {model}")
                return 1

            # Siker → item feldolgozása
            pred = extract_choice(response.get("response", ""), len(item["choices"]))
            fout.write(json.dumps({...}, ensure_ascii=False) + "\n")
            fout.flush(); os.fsync(fout.fileno())
            cp.mark_completed(item["id"])

            # State mentése minden 50. itemnél (ne perzisztáljunk túl sűrűn)
            if i % 50 == 0:
                cp.save()

    # 5. Befejezés
    cp.mark_completed_full()
    print(f"✅ Kész: {out_path}")
    return 0
```

## Tipikus használat

```bash
# 1. Első indítás
python run_hulu.py --model qwen3.5:4b
# ... 2 óra múlva leállt (rate limit) ...
# ⛔ STOP: ollama_http_429 (max retries reached)
#    Kész: 1247/5000. Folytatás: python run_hulu.py --model qwen3.5:4b

# 2. Várakozás (cloud rate limit reset), vagy lokális modellre váltás
sleep 3600  # vagy: python run_hulu.py --model qwen3.5:2b (másik modell)

# 3. Folytatás
python run_hulu.py --model qwen3.5:4b
# 🚀 Folytatás: state betöltve, current_index=1247
# ... 2 óra múlva kész ...
# ✅ Kész: results/qwen3.5-4b/hulu_results.jsonl
# ✅ 5000/5000, acc=0.781

# 4. Aggregáció (a részleges eredményeket is tudja olvasni)
python aggregate_results.py
# → composite_scores.csv, report.md, heatmap
```

## Edge case-ek

- **Több script párhuzamosan ugyanazon a modellen** — nem támogatott (race condition a state.json-on). A `--lock` opció használható, ha szükséges (flock a state_path-ra).
- **Dataset változás a két futás között** — veszélyes: ha a `hulu_std.jsonl` módosul, a checkpoint elveszti a konzisztenciát. Megoldás: minden futásnál snapshotoljuk a dataset hash-ét a state-be, és a resume ellenőrzi.
- **Lokális szabad hely fogy** — a script futás közben ellenőrzi a `df -h ./results` kimenetét, és figyelmeztet, ha < 1 GB.
- **A `--reset` flag életveszélyes** — törli a korábbi eredményeket. Megerősítést kér, ha STDIN nem TTY.

## Kapcsolódó

- [Runbook: HuLU futtatása](../runbooks/run-hulu-modell-x.md) — konkrét implementáció
- [Runbook: Aggregáció](../runbooks/aggregate-results.md) — részleges JSON-öket is kezel
- [Runbook: Debug](../runbooks/debug-modell-nem-valaszol.md) — hibaüzenetek értelmezése
- [Overview](../overview.md) — a 40/40/20 súlyozás
- [SCHEMA](../SCHEMA.md) — design-decision
