#!/usr/bin/env python
"""
run_hugme.py — HuGME benchmark futtatása egy modellen, CHECKPOINT-AWARE.

0-shot szabad generálás 300 prompton. A válaszokat a judge_hugme.py
pontozza gemini-3-flash-preview bíróval (6 metrika).

Stop-on-error + resume.

Használat:
  python run_hugme.py --model qwen3.5:cloud
  python run_hugme.py --model qwen3.5:cloud --reset
  python run_hugme.py --model qwen3.5:cloud --status
  python run_hugme.py --model qwen3.5:cloud --limit 10
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from checkpoint import Checkpoint
from stop_on_error import call_ollama_strict, OllamaFatalError

OLLAMA_URL = "http://localhost:11434"
PROMPTS_PATH = Path("./data/hugme/prompts.jsonl")
DEFAULT_RESULTS_DIR = Path("./results")
DEFAULT_STATE_DIR = Path("./state")
LOG_PATH = Path("./logs/hugme_runs.log")


def run_benchmark(model: str, limit: int | None, reset: bool,
                  results_dir: Path, state_dir: Path, mode: str = "nothink") -> int:
    if mode not in ("think", "nothink"):
        raise ValueError(f"ismeretlen mode: {mode}")
    think = (mode == "think")
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
    state_path = state_dir / model_safe / "hugme.json"

    if reset:
        if state_path.exists():
            state_path.unlink()
        for f in ["hugme_results.jsonl", "hugme_summary.json"]:
            p = results_dir / model_safe / f
            if p.exists():
                p.unlink()
        print("♻️  Reset: törölve a régi state és results fájlok")

    cp = Checkpoint(state_path)
    cp.state["model"] = model
    cp.state["benchmark"] = "hugme"
    if "run_id" not in cp.state:
        cp.state["run_id"] = f"hugme-{model_safe}-{int(time.time())}"

    if cp.is_completed:
        print(f"✅ Ez a futás már kész volt: {state_path}")
        print("   --reset kapcsolóval újrafuttatható.")
        return 0

    if cp.resume_from > 0:
        print(f"🚀 Folytatás: state betöltve, current_index={cp.resume_from}/{limit or '?'}")

    if not PROMPTS_PATH.exists():
        print(f"❌ Prompt fájl nem található: {PROMPTS_PATH}")
        return 1

    items = [json.loads(l) for l in PROMPTS_PATH.read_text(encoding="utf-8").splitlines()]
    if limit:
        items = items[:limit]
    total = len(items)

    if cp.resume_from >= total:
        print(f"✅ Már minden kész volt ({cp.resume_from}/{total}).")
        cp.mark_completed_full()
        return 0

    out_dir = results_dir / model_safe
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hugme_results.jsonl"
    file_mode = "a" if (out_path.exists() and cp.resume_from > 0) else "w"

    log_line = (
        f"{datetime.now(timezone.utc).isoformat()} | {model} | hugme | "
        f"run_id={cp.state['run_id']} | resume_from={cp.resume_from}"
    )
    print(f"🚀 HuGME: {model} | {total} prompt | resume_from={cp.resume_from}")

    completed_set = set(cp.state["completed_ids"])
    processed = 0
    try:
        with out_path.open(file_mode, encoding="utf-8") as fout:
            start = time.time()
            for i, item in enumerate(items):
                if item["id"] in completed_set:
                    continue
                try:
                    response = call_ollama_strict(
                        item["prompt"], model,
                        think=think,
                        num_predict=4096,
                        timeout=(300 if think else 120),
                        max_retries=(1 if think else 2),
                    )
                    raw = response.get("response", "").strip()
                except OllamaFatalError as e:
                    cp.mark_stopped(str(e))
                    elapsed = time.time() - start
                    done = len(cp.state["completed_ids"])
                    print(f"\n⛔ STOP @ item {i}/{total}: {e}")
                    print(f"   Eltelt: {elapsed:.0f}s | Kész: {done}/{total}")
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{log_line} | FAILED @ {done}/{total} | stop_reason={e}\n")
                    return 1

                fout.write(json.dumps({
                    "id": item["id"], "task": "hugme",
                    "prompt": item["prompt"],
                    "metric": item.get("metric", "general"),
                    "response": raw,
                    "mode": mode,
                }, ensure_ascii=False) + "\n")
                fout.flush()
                os.fsync(fout.fileno())
                cp.mark_completed(item["id"], True)
                processed += 1

                done = len(cp.state["completed_ids"])
                if processed % 50 == 0 or i == total - 1:
                    print(f"  [{done:4d}/{total}] | last: {raw[:60]!r}")
                    cp.save()
    except KeyboardInterrupt:
        cp.mark_stopped("manual_stop")
        print(f"\n⛸  Manual stop (Ctrl+C). State mentve: {state_path}")
        return 130

    cp.mark_completed_full()
    print(f"\n✅ KÉSZ: {out_path} | {total} generált válasz")
    print("   Ezután futtasd: python scripts/judge_hugme.py --model {model} --mode {mode}")
    return 0


def show_status(model: str, state_dir: Path, mode: str = "nothink") -> None:
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
    state_path = state_dir / model_safe / "hugme.json"
    if not state_path.exists():
        print(f"Nincs state fájl: {state_path}")
        return
    print(json.dumps(json.loads(state_path.read_text(encoding="utf-8")), indent=2, ensure_ascii=False))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--reset", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--mode", choices=["think", "nothink"], default="nothink")
    p.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    p.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    args = p.parse_args()

    if args.status:
        show_status(args.model, args.state_dir, args.mode)
        return 0

    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        if args.model not in models and not args.model.endswith(":cloud"):
            print(f"⚠️  {args.model} nincs telepítve. Futtasd: ollama pull {args.model}")
            try:
                ans = input("Folytatod cloud modellként? [y/N] ")
                if ans.lower() != "y":
                    return 1
            except EOFError:
                return 1
    except Exception as e:
        print(f"❌ Ollama nem elérhető: {e}")
        return 1

    return run_benchmark(args.model, args.limit, args.reset,
                         args.results_dir, args.state_dir, args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
