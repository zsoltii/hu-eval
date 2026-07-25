#!/usr/bin/env python
"""
run_mmlu_hu.py — MMLU-HU benchmark futtatása egy modellen, CHECKPOINT-AWARE.

5-shot prompting a NYTK dev split példáiból (5 példa/tantárgy).
Stop-on-error + resume.

Használat:
  python run_mmlu_hu.py --model qwen3.5:cloud
  python run_mmlu_hu.py --model qwen3.5:cloud --reset
  python run_mmlu_hu.py --model qwen3.5:cloud --status
  python run_mmlu_hu.py --model qwen3.5:cloud --limit 50
  python run_mmlu_hu.py --model qwen3.5:cloud --mode think
"""
import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from checkpoint import Checkpoint
from stop_on_error import call_ollama_strict, OllamaFatalError, FatalBackendError
from openai_compat import call_openai_strict

OLLAMA_URL = "http://localhost:11434"
DEFAULT_OPENAI_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OPENAI_API_KEY = "ollama"
VAL_PATH = Path("./data/mmlu_hu/mmlu_hu_std.jsonl")
DEFAULT_RESULTS_DIR = Path("./results")
DEFAULT_STATE_DIR = Path("./state")
LOG_PATH = Path("./logs/mmlu_runs.log")

NUM_FEWSHOT = 5


def extract_choice(text: str) -> int:
    if not text:
        return -1
    # Think mode: szűrjük ki a <think>...</think> blokkot, ha a szöveg
    # a gondolatmenet UTÁN tartalmazza a tényleges választ.
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if not cleaned:
        cleaned = text

    # 1) Egyértelmű minta: "Válasz: X" / "Answer: X" / "The answer is X" /
    #    "(X)" az utolsó 200 karakterben.
    tail = cleaned[-300:]
    for pat in [
        r"(?i)válasz[:\s]+([A-Da-d])\b",
        r"(?i)answer[:\s]+(?:is\s*)?([A-Da-d])\b",
        r"(?i)the\s+answer\s+is\s*([A-Da-d])\b",
        r"(?i)helyes(?:\s+válasz)?[:\s]+([A-Da-d])\b",
        r"\(([A-Da-d])\)\s*$",
    ]:
        m = re.search(pat, tail)
        if m:
            return ord(m.group(1).upper()) - ord("A")

    # 2) Magyar szöveges leírás (kifejezetten NEM "a" mint 0 — az túl hamis).
    magyar = {
        "az első": 0, "az elso": 0, "első": 0, "elso": 0,
        "a második": 1, "a masodik": 1, "második": 1, "masodik": 1,
        "a harmadik": 2, "harmadik": 2,
        "a negyedik": 3, "negyedik": 3,
    }
    tlow = cleaned.lower()
    for szo, n in magyar.items():
        if szo in tlow:
            return n

    # 3) Szabad betű (A-D) a szöveg elején VAGY az utolsó 100 karakterben —
    #    az "a" önmagában NEM elfogadható (magyar szövegben túl gyakori).
    m = re.search(r"\b([B-D])\b", cleaned[:50])
    if m:
        return ord(m.group(1).upper()) - ord("A")
    m = re.search(r"\b([A-D])\b", cleaned[-100:])
    if m:
        return ord(m.group(1).upper()) - ord("A")
    return -1


def load_dev_and_items() -> tuple[dict[str, list[dict]], list[dict], set[str]]:
    """returns: (dev_examples, eval_items, dev_ids)
    
    Takes the first NUM_FEWSHOT per subject as few-shot examples,
    the rest as eval items. Uses composite (subject, id) keys
    because MMLU-HU reuses the same id sequence per subject.
    """
    by_subject = defaultdict(list)
    all_items = []
    for line in VAL_PATH.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        by_subject[rec["subject"]].append(rec)
        all_items.append(rec)

    dev: dict[str, list[dict]] = {}
    dev_ids: set[str] = set()
    for subj, exs in by_subject.items():
        dev[subj] = exs[:NUM_FEWSHOT]
        for d in exs[:NUM_FEWSHOT]:
            dev_ids.add(f"{subj}::{d['id']}")

    eval_items = [it for it in all_items if f"{it['subject']}::{it['id']}" not in dev_ids]
    return dev, eval_items, dev_ids


def build_shot_prompt(item: dict, dev: dict[str, list[dict]]) -> str:
    """5-shot prompt: dev példák + aktuális kérdés.
    A shot-ok prompt-jában a 'Válaszolj CSAK...' szöveget
    a helyes válasz betűjére cseréljük.
    """
    subj = item["subject"]
    shots = dev.get(subj, [])
    parts = []
    for s in shots:
        parts.append(
            f"Kérdés: {s['prompt'].replace('Válaszolj CSAK a helyes betűvel (A/B/C/D).', 'Válasz: ' + chr(65 + s['answer_index']))}"
        )
    parts.append(item["prompt"])
    return "\n\n".join(parts)


def run_benchmark(model: str, limit: int | None, reset: bool,
                  results_dir: Path, state_dir: Path, mode: str = "nothink",
                  backend: str = "ollama",
                  base_url: str = DEFAULT_OPENAI_BASE_URL,
                  api_key: str = DEFAULT_OPENAI_API_KEY) -> int:
    if mode not in ("think", "nothink"):
        raise ValueError(f"ismeretlen mode: {mode}")
    think = (mode == "think")
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
    state_path = state_dir / model_safe / "mmlu_hu.json"

    if reset:
        if state_path.exists():
            state_path.unlink()
        old_results = results_dir / model_safe / "mmlu_hu_results.jsonl"
        if old_results.exists():
            old_results.unlink()
        old_summary = results_dir / model_safe / "mmlu_hu_summary.json"
        if old_summary.exists():
            old_summary.unlink()
        print("♻️  Reset: törölve a régi state és results fájlok")

    cp = Checkpoint(state_path)
    cp.state["model"] = model
    cp.state["benchmark"] = "mmlu_hu"
    if "run_id" not in cp.state:
        cp.state["run_id"] = f"mmlu_hu-{model_safe}-{int(time.time())}"

    if cp.is_completed:
        print(f"✅ Ez a futás már kész volt: {state_path}")
        print("   --reset kapcsolóval újrafuttatható.")
        return 0

    if cp.resume_from > 0:
        print(f"🚀 Folytatás: state betöltve, current_index={cp.resume_from}/{limit or '?'}")

    if not VAL_PATH.exists():
        print(f"❌ Dataset nem található: {VAL_PATH}")
        print("   Futtasd előbb: python scripts/download_mmlu_hu.py")
        return 1

    dev, items, dev_ids = load_dev_and_items()
    if limit:
        items = items[:limit]
    total = len(items)

    if cp.resume_from >= total:
        print(f"✅ Már minden kész volt ({cp.resume_from}/{total}).")
        cp.mark_completed_full()
        return 0

    out_dir = results_dir / model_safe
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "mmlu_hu_results.jsonl"
    file_mode = "a" if (out_path.exists() and cp.resume_from > 0) else "w"

    log_line = (
        f"{datetime.now(timezone.utc).isoformat()} | {model} | mmlu_hu | "
        f"run_id={cp.state['run_id']} | resume_from={cp.resume_from}"
    )
    print(f"🚀 MMLU-HU: {model} | {total} példa | resume_from={cp.resume_from}")

    completed_set = set(cp.state["completed_ids"])
    processed = 0
    try:
        with out_path.open(file_mode, encoding="utf-8") as fout:
            start = time.time()
            for i, item in enumerate(items):
                comp_id = f"{item['subject']}::{item['id']}"
                if comp_id in completed_set:
                    continue
                shot_prompt = build_shot_prompt(item, dev)
                try:
                    if backend == "openai":
                        response = call_openai_strict(
                            shot_prompt, model,
                            think=think,
                            num_predict=(16384 if think else 4096),
                            timeout=(300 if think else 120),
                            max_retries=(1 if think else 2),
                            base_url=base_url,
                            api_key=api_key,
                        )
                    else:
                        response = call_ollama_strict(
                            shot_prompt, model,
                            think=think,
                            num_predict=(16384 if think else 4096),
                            timeout=(300 if think else 120),
                            max_retries=(1 if think else 2),
                        )
                    raw = response.get("response", "").strip()
                except FatalBackendError as e:
                    cp.mark_stopped(str(e))
                    elapsed = time.time() - start
                    done = len(cp.state["completed_ids"])
                    print(f"\n⛔ STOP @ item {i}/{total}: {e}")
                    print(f"   Eltelt: {elapsed:.0f}s | Kész: {done}/{total} | "
                          f"Részleges acc: {cp.state['num_correct'] / max(1, done):.3f}")
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{log_line} | FAILED @ {done}/{total} | stop_reason={e}\n")
                    return 1

                pred = extract_choice(raw)
                is_correct = pred == item["answer_index"]
                fout.write(json.dumps({
                    "id": item["id"], "task": "mmlu_hu",
                    "prompt": item["prompt"], "choices": item["choices"],
                    "5shot_prompt": shot_prompt,
                    "subject": item["subject"],
                    "gold": item["answer_index"], "raw_response": raw,
                    "prediction": pred, "correct": is_correct,
                    "mode": mode,
                }, ensure_ascii=False) + "\n")
                fout.flush()
                os.fsync(fout.fileno())
                cp.mark_completed(comp_id, is_correct)
                processed += 1

                done = len(cp.state["completed_ids"])
                acc = cp.state["num_correct"] / max(1, done)
                if processed % 50 == 0 or i == total - 1:
                    print(f"  [{done:4d}/{total}] acc={acc:.3f} | last: {raw[:40]!r}")
                    cp.save()
    except KeyboardInterrupt:
        cp.mark_stopped("manual_stop")
        print(f"\n⛸  Manual stop (Ctrl+C). State mentve: {state_path}")
        return 130

    cp.mark_completed_full()
    summary = {
        "model": model, "benchmark": "mmlu_hu",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": cp.state["run_id"],
        "num_examples": cp.state["current_index"],
        "num_correct": cp.state["num_correct"],
        "accuracy": round(cp.state["num_correct"] / cp.state["current_index"], 4),
        "num_fewshot": NUM_FEWSHOT,
        "results_file": str(out_path),
    }
    (out_dir / "mmlu_hu_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{log_line} | COMPLETED | acc={summary['accuracy']:.3f} | {summary['num_examples']} ex\n")
    print(f"\n✅ KÉSZ: {out_path} | acc={summary['accuracy']:.3f} ({summary['num_correct']}/{summary['num_examples']})")
    return 0


def show_status(model: str, state_dir: Path, mode: str = "nothink") -> None:
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
    state_path = state_dir / model_safe / "mmlu_hu.json"
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
    p.add_argument("--backend", choices=["ollama", "openai"], default="ollama",
                   help="Inferencia backend: 'ollama' (közvetlen /api/generate) "
                        "vagy 'openai' (OpenAI-kompatibilis /v1/chat/completions, "
                        "pl. helyi Ollama /v1, llama-server, stb.)")
    p.add_argument("--base-url", default=DEFAULT_OPENAI_BASE_URL,
                   help="OpenAI backend esetén a végpont gyökere "
                        "(default: http://localhost:11434/v1)")
    p.add_argument("--api-key", default=DEFAULT_OPENAI_API_KEY,
                   help="OpenAI backend esetén a Bearer token "
                        "(Ollama esetén tetszőleges, default: 'ollama')")
    args = p.parse_args()

    if args.status:
        show_status(args.model, args.state_dir, args.mode)
        return 0

    if args.backend == "ollama":
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
    else:
        try:
            requests.get(f"{args.base_url.rstrip('/')}/models",
                         headers={"Authorization": f"Bearer {args.api_key}"},
                         timeout=5)
        except Exception as e:
            print(f"⚠️  OpenAI backend ({args.base_url}) nem érhető el: {e}")
            print("   A futás így is megkezdődik; az első hiba stop-ol (checkpoint).")

    return run_benchmark(args.model, args.limit, args.reset,
                         args.results_dir, args.state_dir, args.mode,
                         args.backend, args.base_url, args.api_key)


if __name__ == "__main__":
    raise SystemExit(main())
