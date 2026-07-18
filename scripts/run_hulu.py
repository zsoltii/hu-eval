#!/usr/bin/env python
"""
run_hulu.py — HuLU benchmark futtatása egy modellen, CHECKPOINT-AWARE.

Stop-on-error + resume: ha Ollama hibát jelez (rate limit, timeout, 5xx, stb.),
a futás azonnal megáll, az állapot mentődik, és a script bármikor folytatható
ugyanazzal a paranccsal.

Használat:
  python run_hulu.py --model qwen3.5:cloud           # első indítás vagy folytatás (nothink)
  python run_hulu.py --model qwen3.5:cloud --reset   # tiszta újrafuttatás
  python run_hulu.py --model qwen3.5:cloud --status  # state megtekintése
  python run_hulu.py --model qwen3.5:cloud --limit 10  # minden taskból 10-10 (60 prompt)
  python run_hulu.py --model qwen3.5:cloud --mode think  # thinking módban futtatás
  python run_hulu.py --model qwen3.5:cloud --mode nothink  # no-thinking mód (default)
  python run_hulu.py --model qwen3.5:cloud           # teljes futás (6 task, 2581 prompt)

A --mode flag szabályozza, hogy a modell gondolkodjon-e:
  --mode nothink (default): a gondolkodás el van nyomva, a modell közvetlenül válaszol
  --mode think: a modell gondolkodhat, a gondolkodás a response-ban megjelenik

A --limit flag TASK-SZINTŰ: --limit 10 → 10 HuCOLA + 10 HuCoPA + 10 HuRTE +
10 HuSST + 10 HuWNLI + 10 HuCB = 60 prompt. Abszolút darabszám nem támogatott
(az adatfájl task-sorrendben van, és az első 910 prompt mind HuCOLA lenne).

A state és results fájlok a mode-tól függően külön mappákba kerülnek:
  state/{model_safe}-nothink/hulu.json
  results/{model_safe}-nothink/hulu_results.jsonl
  state/{model_safe}-think/hulu.json
  results/{model_safe}-think/hulu_results.jsonl

Részletek: wiki/runbooks/run-hulu-modell-x.md és wiki/concepts/checkpoint-progress.md
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# Helyi modulok importálása (scripts/ mappa)
sys.path.insert(0, str(Path(__file__).parent))
from checkpoint import Checkpoint
from stop_on_error import call_ollama_strict, OllamaFatalError


OLLAMA_URL = "http://localhost:11434"
DATASET_PATH = Path("./data/hulu/hulu_std.jsonl")
DEFAULT_RESULTS_DIR = Path("./results")
DEFAULT_STATE_DIR = Path("./state")
LOG_PATH = Path("./logs/hulu_runs.log")


# --- Choice extractor (magyar szavakat is kezeli) ---

def extract_choice(text: str, num_choices: int) -> int:
    if not text:
        return -1
    m = re.search(r"\b([0-9])\b", text)
    if m and 0 <= int(m.group(1)) < num_choices:
        return int(m.group(1))
    magyar = {
        "nulla": 0, "egy": 1, "kettő": 2, "három": 3, "négy": 4,
        "öt": 5, "hat": 6, "hét": 7, "nyolc": 8, "kilenc": 9,
    }
    for szo, n in magyar.items():
        if szo in text.lower() and n < num_choices:
            return n
    return -1


# --- Fő benchmark ciklus ---

def run_benchmark(
    model: str, limit: int | None, reset: bool,
    results_dir: Path, state_dir: Path,
    mode: str = "nothink",
) -> int:
    if mode not in ("think", "nothink"):
        raise ValueError(f"ismeretlen mode: {mode} (lehetséges: think, nothink)")
    think = (mode == "think")
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
    state_path = state_dir / model_safe / "hulu.json"

    # Reset: töröljük a régi state + results fájlt
    if reset:
        if state_path.exists():
            state_path.unlink()
        old_results = results_dir / model_safe / "hulu_results.jsonl"
        if old_results.exists():
            old_results.unlink()
        print("♻️  Reset: törölve a korábbi state és results fájlok")

    cp = Checkpoint(state_path)
    cp.state["model"] = model
    cp.state["benchmark"] = "hulu"
    if "run_id" not in cp.state:
        cp.state["run_id"] = f"hulu-{model_safe}-{int(time.time())}"

    if cp.is_completed:
        print(f"✅ Ez a futás már kész volt: {state_path}")
        print("   --reset kapcsolóval újrafuttatható.")
        return 0

    if cp.resume_from > 0:
        print(f"🚀 Folytatás: state betöltve, current_index="
              f"{cp.resume_from}/{limit or '?'}")

    # Dataset
    if not DATASET_PATH.exists():
        print(f"❌ Dataset nem található: {DATASET_PATH}")
        print("   Futtasd előbb: python scripts/download_hulu.py")
        return 1
    items = [
        json.loads(l)
        for l in DATASET_PATH.read_text(encoding="utf-8").splitlines()
    ]
    if limit:
        # Task-szintű limit: minden taskból max `limit` darabot tartunk meg.
        # A checkpoint ID-alapú (completed_ids), tehát a resume biztonságos.
        filtered = []
        per_task_count: dict[str, int] = {}
        for item in items:
            t = item["task"]
            if per_task_count.get(t, 0) >= limit:
                continue
            filtered.append(item)
            per_task_count[t] = per_task_count.get(t, 0) + 1
        items = filtered
        task_summary = ", ".join(
            f"{t}={n}" for t, n in sorted(per_task_count.items())
        )
        print(f"   Task-szintű limit={limit}: {task_summary} "
              f"(összesen {len(items)} prompt)")
    total = len(items)

    if cp.resume_from >= total:
        print(f"✅ Már minden kész volt ({cp.resume_from}/{total}).")
        cp.mark_completed_full()
        return 0

    out_dir = results_dir / model_safe
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hulu_results.jsonl"
    file_mode = "a" if (out_path.exists() and cp.resume_from > 0) else "w"

    log_line = (
        f"{datetime.now(timezone.utc).isoformat()} | {model} | hulu | "
        f"run_id={cp.state['run_id']} | resume_from={cp.resume_from}"
    )
    print(f"🚀 Benchmark: {model} | {total} példa | "
          f"resume_from={cp.resume_from}")

    try:
        with out_path.open(file_mode, encoding="utf-8") as fout:
            start = time.time()
            # Skip a már completed item-eket (resume esetén).
            # A completed_ids set-be konvertálása O(1) lookupot ad.
            completed_set = set(cp.state["completed_ids"])
            # Dedup fix: ha a JSONL fájlban már van az ID (pl. retry előtt
            # sikeresen kiíródott, de a mark_completed nem futott le),
            # akkor is kihagyjuk. Beolvassuk a meglévő ID-kat egyszer.
            if out_path.exists():
                for line in out_path.read_text(encoding="utf-8").splitlines():
                    try:
                        rid = json.loads(line).get("id")
                        if rid:
                            completed_set.add(rid)
                    except json.JSONDecodeError:
                        continue
            processed = 0
            for i, item in enumerate(items):
                if item["id"] in completed_set:
                    continue
                try:
                    response = call_ollama_strict(
                        item["prompt"], model,
                        think=think,
                        num_predict=(16384 if think else 4096),
                        timeout=(300 if think else 120),
                        max_retries=(1 if think else 2),
                    )
                    raw = response.get("response", "").strip()
                except OllamaFatalError as e:
                    # STOP! Checkpoint + log + tájékoztató üzenet
                    cp.mark_stopped(str(e))
                    elapsed = time.time() - start
                    done = len(cp.state["completed_ids"])
                    print(f"\n⛔ STOP @ item {i}/{total}: {e}")
                    print(f"   Eltelt: {elapsed:.0f}s | Kész: {done}/{total} | "
                          f"Részleges acc: "
                          f"{cp.state['num_correct'] / max(1, done):.3f}")
                    print(f"   State: {state_path}")
                    print(f"   Folytatás: python scripts/run_hulu.py "
                          f"--model {model}")
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{log_line} | FAILED @ {done}/{total} | "
                                f"stop_reason={e}\n")
                    return 1

                pred = extract_choice(raw, len(item["choices"]))
                is_ok = pred == item["answer_index"]
                fout.write(json.dumps({
                    "id": item["id"], "task": item["task"],
                    "prompt": item["prompt"], "choices": item["choices"],
                    "gold": item["answer_index"], "raw_response": raw,
                    "prediction": pred, "correct": is_ok,
                    "mode": mode,
                    "ollama_total_duration_ns": response.get("total_duration"),
                    "ollama_load_duration_ns": response.get("load_duration"),
                    "ollama_prompt_eval_count": response.get("prompt_eval_count"),
                    "ollama_prompt_eval_duration_ns": response.get("prompt_eval_duration"),
                    "ollama_eval_count": response.get("eval_count"),
                    "ollama_eval_duration_ns": response.get("eval_duration"),
                    "ollama_done_reason": response.get("done_reason"),
                }, ensure_ascii=False) + "\n")
                fout.flush()
                os.fsync(fout.fileno())
                cp.mark_completed(item["id"], is_ok)
                processed += 1

                done = len(cp.state["completed_ids"])
                acc = cp.state["num_correct"] / max(1, done)
                if processed % 50 == 0 or i == total - 1:
                    print(f"  [{done:4d}/{total}] acc={acc:.3f} | "
                          f"last: {raw[:40]!r}")
                    cp.save()  # minden 50. itemnél perzisztálunk
    except KeyboardInterrupt:
        cp.mark_stopped("manual_stop")
        print(f"\n⛸  Manual stop (Ctrl+C). State mentve: {state_path}")
        print(f"   Folytatás: python scripts/run_hulu.py --model {model}")
        return 130

    # Kész
    cp.mark_completed_full()
    summary = {
        "model": model, "benchmark": "hulu",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": cp.state["run_id"],
        "num_examples": cp.state["current_index"],
        "num_correct": cp.state["num_correct"],
        "accuracy": round(
            cp.state["num_correct"] / cp.state["current_index"], 4
        ),
        "results_file": str(out_path),
    }
    (out_dir / "hulu_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{log_line} | COMPLETED | acc={summary['accuracy']:.3f} | "
                f"{summary['num_examples']} ex\n")
    print(f"\n✅ KÉSZ: {out_path} | acc={summary['accuracy']:.3f} "
          f"({summary['num_correct']}/{summary['num_examples']})")
    return 0


def show_status(model: str, state_dir: Path, mode: str = "nothink") -> None:
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
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
                   help="Törli a korábbi state + results fájlokat, "
                        "nulláról indul")
    p.add_argument("--status", action="store_true",
                   help="Megmutatja a state fájl tartalmát, nem futtat semmit")
    p.add_argument("--mode", choices=["think", "nothink"], default="nothink",
                   help="Gondolkodás mód: 'think' (modell gondolkodhat) vagy "
                        "'nothink' (gondolkodás elnyomva, default)")
    p.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    p.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    args = p.parse_args()

    if args.status:
        show_status(args.model, args.state_dir, args.mode)
        return 0

    # Sanity check: Ollama elérhető?
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        if args.model not in models and not args.model.endswith(":cloud"):
            print(f"⚠️  {args.model} nincs telepítve. "
                  f"Futtasd: ollama pull {args.model}")
            try:
                ans = input("Folytatod cloud modellként? [y/N] ")
                if ans.lower() != "y":
                    return 1
            except EOFError:
                return 1
    except Exception as e:
        print(f"❌ Ollama nem elérhető: {e}")
        return 1

    return run_benchmark(
        args.model, args.limit, args.reset,
        args.results_dir, args.state_dir,
        args.mode,
    )


if __name__ == "__main__":
    raise SystemExit(main())
