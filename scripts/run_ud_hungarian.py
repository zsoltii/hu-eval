#!/usr/bin/env python
"""
run_ud_hungarian.py — UD Hungarian benchmark futtatása egy modellen.

A modell CoNLL-U formátumú elemzést ad egy magyar mondatra.
A válaszból regex-szel nyerjük ki a UPOS-t, a HEAD-et és a DEPREL-t.

Stop-on-error + resume.

Használat:
  python run_ud_hungarian.py --model qwen3.5:cloud
  python run_ud_hungarian.py --model qwen3.5:cloud --reset
  python run_ud_hungarian.py --model qwen3.5:cloud --status
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

sys.path.insert(0, str(Path(__file__).parent))
from checkpoint import Checkpoint
from stop_on_error import call_ollama_strict, OllamaFatalError, FatalBackendError
from openai_compat import call_openai_strict

OLLAMA_URL = "http://localhost:11434"
DEFAULT_OPENAI_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OPENAI_API_KEY = "ollama"
DATASET_PATH = Path("./data/ud_hungarian/ud_hungarian_std.jsonl")
DEFAULT_RESULTS_DIR = Path("./results")
DEFAULT_STATE_DIR = Path("./state")
LOG_PATH = Path("./logs/ud_hungarian_runs.log")


def parse_conllu_from_response(text: str, gold_tokens: list[dict]) -> dict | None:
    """Próbálja kinyerni a CoNLL-U mezőket a modell válaszából.
    CoT-aware: strip-peli a think blokkot, szabad szöveges formátumot is megpróbálja.
    Az eredmény: {upos_correct, head_correct, deprel_correct, upos_total, head_total, deprel_total}"""

    if not text or not text.strip():
        return None

    cleaned = text

    if "<think>" in cleaned and "</think>" in cleaned:
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL)
    elif "<think>" in cleaned and "</think>" not in cleaned:
        cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)

    conllu_marker = re.search(
        r"(?:CoNLL[- ]?U|Token\s*ID|ID\s*FORM|1\s+[^\n]+\t[A-Z]+)",
        cleaned, re.IGNORECASE
    )
    if conllu_marker:
        cleaned = cleaned[conllu_marker.start():]

    lines = cleaned.splitlines()
    result = {"upos_correct": 0, "head_correct": 0, "deprel_correct": 0,
              "upos_total": 0, "head_total": 0, "deprel_total": 0}

    pred_tokens = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 8 and parts[0].isdigit() and re.match(r"^[A-Z][A-Z0-9_-]*$", parts[3]):
            pred_tokens.append({
                "id": parts[0],
                "upos": parts[3],
                "head": parts[6],
                "deprel": parts[7],
            })
            continue
        m = re.match(
            r"(\d+)\s+\S+\s+\S+\s+([A-Z][A-Z0-9_-]*)\s+\S+\s+\S+\s+(\d+)\s+(\S+)",
            line
        )
        if m:
            pred_tokens.append({
                "id": m.group(1),
                "upos": m.group(2),
                "head": m.group(3),
                "deprel": m.group(4),
            })
            continue
        m = re.match(
            r"(\d+)\.\s+\S+\s*[:(-]\s*([A-Z][A-Z0-9_-]*)\s*[,;]\s*head\s*=\s*(\d+)\s*[,;]\s*deprel\s*=\s*(\S+?)\s*\)?",
            line, re.IGNORECASE
        )
        if m:
            pred_tokens.append({
                "id": m.group(1),
                "upos": m.group(2),
                "head": m.group(3),
                "deprel": m.group(4),
            })
            continue
        m = re.match(
            r"(\d+)\s+([A-Z][A-Z0-9_-]*)\s+(\d+)\s+(\S+)",
            line
        )
        if m:
            pred_tokens.append({
                "id": m.group(1),
                "upos": m.group(2),
                "head": m.group(3),
                "deprel": m.group(4),
            })

    if not pred_tokens:
        return None

    gold_map = {t["id"]: t for t in gold_tokens}
    for pt in pred_tokens:
        gt = gold_map.get(pt["id"])
        if not gt:
            continue
        result["upos_total"] += 1
        result["head_total"] += 1
        result["deprel_total"] += 1
        if pt["upos"].upper() == gt["upos"].upper():
            result["upos_correct"] += 1
        if pt["head"] == gt["head"]:
            result["head_correct"] += 1
        if pt["deprel"].upper() == gt["deprel"].upper():
            result["deprel_correct"] += 1

    return result


def run_benchmark(model: str, limit: int | None, reset: bool,
                  results_dir: Path, state_dir: Path, mode: str = "nothink",
                  backend: str = "ollama",
                  base_url: str = DEFAULT_OPENAI_BASE_URL,
                  api_key: str = DEFAULT_OPENAI_API_KEY) -> int:
    if mode not in ("think", "nothink"):
        raise ValueError(f"ismeretlen mode: {mode}")
    think = (mode == "think")
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
    state_path = state_dir / model_safe / "ud_hungarian.json"

    if reset:
        if state_path.exists():
            state_path.unlink()
        for f in ["ud_hungarian_results.jsonl", "ud_hungarian_summary.json"]:
            p = results_dir / model_safe / f
            if p.exists():
                p.unlink()
        print("♻️  Reset: törölve a régi state és results fájlok")

    cp = Checkpoint(state_path)
    cp.state["model"] = model
    cp.state["benchmark"] = "ud_hungarian"
    if "run_id" not in cp.state:
        cp.state["run_id"] = f"ud_hungarian-{model_safe}-{int(time.time())}"

    if cp.is_completed:
        print(f"✅ Ez a futás már kész volt: {state_path}")
        return 0

    if cp.resume_from > 0:
        print(f"🚀 Folytatás: state betöltve, current_index={cp.resume_from}/{limit or '?'}")

    if not DATASET_PATH.exists():
        print(f"❌ Dataset nem található: {DATASET_PATH}")
        print("   Futtasd előbb: python scripts/download_ud_hungarian.py")
        return 1

    items = [json.loads(l) for l in DATASET_PATH.read_text(encoding="utf-8").splitlines()]
    if limit:
        items = items[:limit]
    total = len(items)

    if cp.resume_from >= total:
        print(f"✅ Már minden kész volt ({cp.resume_from}/{total}).")
        cp.mark_completed_full()
        return 0

    out_dir = results_dir / model_safe
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ud_hungarian_results.jsonl"
    file_mode = "a" if (out_path.exists() and cp.resume_from > 0) else "w"

    log_line = (
        f"{datetime.now(timezone.utc).isoformat()} | {model} | ud_hungarian | "
        f"run_id={cp.state['run_id']} | resume_from={cp.resume_from}"
    )
    print(f"🚀 UD Hungarian: {model} | {total} mondat | resume_from={cp.resume_from}")

    completed_set = set(cp.state["completed_ids"])
    processed = 0
    try:
        with out_path.open(file_mode, encoding="utf-8") as fout:
            start = time.time()
            for i, item in enumerate(items):
                if item["id"] in completed_set:
                    continue
                try:
                    if backend == "openai":
                        response = call_openai_strict(
                            item["prompt"], model,
                            think=think,
                            num_predict=(8192 if think else 4096),
                            timeout=(600 if think else 300),
                            max_retries=(2 if think else 3),
                            base_url=base_url,
                            api_key=api_key,
                        )
                    else:
                        response = call_ollama_strict(
                            item["prompt"], model,
                            think=think,
                            num_predict=(8192 if think else 4096),
                            timeout=(600 if think else 300),
                            max_retries=(2 if think else 3),
                        )
                    raw = response.get("response", "").strip()
                except FatalBackendError as e:
                    cp.mark_stopped(str(e))
                    elapsed = time.time() - start
                    done = len(cp.state["completed_ids"])
                    print(f"\n⛔ STOP @ item {i}/{total}: {e}")
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{log_line} | FAILED @ {done}/{total} | stop_reason={e}\n")
                    return 1

                # Parse CoNLL-U from response
                parsed = parse_conllu_from_response(raw, item["tokens"])
                if parsed:
                    upos_acc = parsed["upos_correct"] / max(1, parsed["upos_total"])
                    head_acc = parsed["head_correct"] / max(1, parsed["head_total"])
                    deprel_acc = parsed["deprel_correct"] / max(1, parsed["deprel_total"])
                else:
                    upos_acc = head_acc = deprel_acc = 0.0

                fout.write(json.dumps({
                    "id": item["id"], "task": "ud_hungarian",
                    "prompt": item["prompt"],
                    "gold_conllu": item["gold_conllu"],
                    "raw_response": raw,
                    "upos_accuracy": round(upos_acc, 4),
                    "uas": round(head_acc, 4),
                    "las": round(deprel_acc, 4),
                    "parsed_tokens": parsed,
                    "mode": mode,
                    "backend": backend,
                }, ensure_ascii=False) + "\n")
                fout.flush()
                os.fsync(fout.fileno())
                cp.mark_completed(item["id"], upos_acc > 0.5)
                processed += 1

                done = len(cp.state["completed_ids"])
                if processed % 10 == 0 or i == total - 1:
                    print(f"  [{done:4d}/{total}] UPOS={upos_acc:.3f} UAS={head_acc:.3f} LAS={deprel_acc:.3f}")
                    cp.save()
    except KeyboardInterrupt:
        cp.mark_stopped("manual_stop")
        print(f"\n⛸  Manual stop (Ctrl+C). State mentve: {state_path}")
        return 130

    cp.mark_completed_full()

    # Compute averages from results file
    all_results = [json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines()]
    n = len(all_results)
    avg_upos = sum(r["upos_accuracy"] for r in all_results) / n if n else 0.0
    avg_uas = sum(r["uas"] for r in all_results) / n if n else 0.0
    avg_las = sum(r["las"] for r in all_results) / n if n else 0.0
    composite_score = (avg_upos + avg_uas + avg_las) / 3.0

    summary = {
        "model": model, "benchmark": "ud_hungarian",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": cp.state["run_id"],
        "num_examples": n,
        "accuracy": round(composite_score, 4),
        "upos_accuracy": round(avg_upos, 4),
        "uas": round(avg_uas, 4),
        "las": round(avg_las, 4),
        "results_file": str(out_path),
    }
    (out_dir / "ud_hungarian_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{log_line} | COMPLETED | acc={summary['accuracy']:.3f} | {n} ex\n")
    print(f"\n✅ KÉSZ: {out_path} | composite={composite_score:.4f} (UPOS={avg_upos:.4f} UAS={avg_uas:.4f} LAS={avg_las:.4f})")
    return 0


def show_status(model: str, state_dir: Path, mode: str = "nothink") -> None:
    model_safe = model.replace(":", "-").replace("/", "-") + f"-{mode}"
    state_path = state_dir / model_safe / "ud_hungarian.json"
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
