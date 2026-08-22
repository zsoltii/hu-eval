#!/usr/bin/env python
"""
run_ud_v3.py — UD Hungarian v4 prompt (explicit format leiras + pelda).
Max 1200s/mondat, ha nincs kimenet -> skip. Checkpoint + resume.
Llama-server port 8080 vagy --base-url parameterezhetoe.
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

DATASET_PATH = Path("./data/ud_hungarian/ud_hungarian_v4.jsonl")
RESULTS_DIR = Path("./results")
STATE_DIR = Path("./state")
LOG_PATH = Path("./logs/ud_hungarian_runs.log")
MAX_TIME = 1800

THINK_OPEN = "\u003cthink\u003e"
THINK_CLOSE = "\u003c/think\u003e"


def parse_conllu_from_response(text: str, gold_tokens: list[dict]) -> dict | None:
    if not text or not text.strip():
        return None
    cleaned = text
    if THINK_OPEN in cleaned and THINK_CLOSE in cleaned:
        cleaned = re.sub(rf"{re.escape(THINK_OPEN)}.*?{re.escape(THINK_CLOSE)}", "", cleaned, flags=re.DOTALL)
    elif THINK_OPEN in cleaned and THINK_CLOSE not in cleaned:
        cleaned = re.sub(rf"{re.escape(THINK_OPEN)}.*", "", cleaned, flags=re.DOTALL)
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
            pred_tokens.append({"id": parts[0], "upos": parts[3], "head": parts[6], "deprel": parts[7]})
            continue
        m = re.match(r"(\d+)\s+\S+\s+\S+\s+([A-Z][A-Z0-9_-]*)\s+\S+\s+\S+\s+(\d+)\s+(\S+)", line)
        if m:
            pred_tokens.append({"id": m.group(1), "upos": m.group(2), "head": m.group(3), "deprel": m.group(4)})
            continue
        m = re.match(r"(\d+)\s+([A-Z][A-Z0-9_-]*)\s+(\d+)\s+(\S+)", line)
        if m:
            pred_tokens.append({"id": m.group(1), "upos": m.group(2), "head": m.group(3), "deprel": m.group(4)})
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


def call_with_stream(model: str, prompt: str, base_url: str, max_time: int = MAX_TIME) -> dict:
    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a linguistic expert. Answer in Hungarian."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 65536,
                "stream": True,
            },
            stream=True,
            timeout=max_time + 60,
        )
    except requests.exceptions.Timeout as e:
        return {"error": f"request_timeout: {e}", "content": "", "reasoning": "", "finish_reason": "timeout"}
    except Exception as e:
        return {"error": str(e), "content": "", "reasoning": "", "finish_reason": "error"}

    reasoning = ""
    content = ""
    started = time.time()
    finish_reason = "timeout"
    seen_content = False

    try:
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except Exception:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                rc = delta.get("reasoning_content")
                if rc:
                    reasoning += rc
                cc = delta.get("content")
                if cc:
                    content += cc
                    if not seen_content:
                        seen_content = True
                finish = chunk.get("choices", [{}])[0].get("finish_reason")
                if finish:
                    finish_reason = finish

            elapsed = time.time() - started
            if elapsed > max_time and not seen_content:
                resp.close()
                return {
                    "content": "",
                    "reasoning": reasoning,
                    "finish_reason": "timeout",
                    "reasoning_length": len(reasoning),
                }
    except Exception as e:
        resp.close()
        return {"error": str(e), "content": content, "reasoning": reasoning,
                "finish_reason": "stream_error"}

    elapsed = time.time() - started
    return {
        "content": content,
        "reasoning": reasoning,
        "finish_reason": finish_reason,
        "reasoning_length": len(reasoning),
        "elapsed": round(elapsed),
    }


def main():
    parser = argparse.ArgumentParser(description="UD Hungarian v4 benchmark runner")
    parser.add_argument("--model", default="unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS")
    parser.add_argument("--base-url", default="http://localhost:8080/v1")
    parser.add_argument("--max-time", type=int, default=MAX_TIME)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    model = args.model
    base_url = args.base_url
    max_time = args.max_time
    model_safe = model.replace(":", "-").replace("/", "-") + "-think"
    state_path = STATE_DIR / model_safe / "ud_hungarian_v4.json"

    if not DATASET_PATH.exists():
        print(f"❌ Dataset nem található: {DATASET_PATH}")
        return 1

    sys.path.insert(0, str(Path(__file__).parent))
    from checkpoint import Checkpoint

    if args.reset and state_path.exists():
        state_path.unlink()

    cp = Checkpoint(state_path)
    cp.state["model"] = model
    cp.state["benchmark"] = "ud_hungarian_v4"
    if "run_id" not in cp.state:
        cp.state["run_id"] = f"ud_v4-{model_safe}-{int(time.time())}"
    if "skipped_ids" not in cp.state:
        cp.state["skipped_ids"] = []
    if "error_ids" not in cp.state:
        cp.state["error_ids"] = []

    if cp.is_completed:
        print(f"✅ Már kész: {state_path}")
        return 0
    if cp.resume_from > 0:
        print(f"🚀 Folytatás: index={cp.resume_from}")

    items = [json.loads(l) for l in DATASET_PATH.read_text(encoding="utf-8").splitlines()]
    total = len(items)

    if cp.resume_from >= total:
        print(f"✅ Minden kész ({cp.resume_from}/{total}).")
        cp.mark_completed_full()
        return 0

    out_dir = RESULTS_DIR / model_safe
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ud_hungarian_results.jsonl"
    file_mode = "a" if (out_path.exists() and cp.resume_from > 0) else "w"

    print(f"🚀 UD Hungarian v4: {model} | {total} mondat | resume={cp.resume_from}")
    print(f"   Timeout/mondat: {max_time}s, ha nincs kimenet → skip")
    print(f"   Base URL: {base_url}")
    print(f"   State: {state_path}")
    print()

    completed_set = set(cp.state["completed_ids"])
    processed = 0
    global_start = time.time()

    try:
        with out_path.open(file_mode, encoding="utf-8") as fout:
            for i, item in enumerate(items):
                if item["id"] in completed_set:
                    continue

                prompt = item["prompt"]
                t0 = time.time()

                result = call_with_stream(model, prompt, base_url, max_time)

                elapsed = time.time() - t0
                raw = result.get("content", "")
                reasoning = result.get("reasoning", "")
                finish = result.get("finish_reason", "?")
                error = result.get("error")

                if error and finish in ("timeout", "error", "stream_error"):
                    cp.state.setdefault("error_ids", []).append(item["id"])
                    cp.mark_stopped(f"error_on_{item['id']}: {error}")
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{datetime.now(timezone.utc).isoformat()} | ud_v4 | ERROR | {item['id']} | {error}\n")
                    print(f"  [{i+1:4d}/{total}] ❌ ERROR: {error} [{elapsed:.0f}s]")
                    cp.save()
                    return 1

                parsed = None
                upos = uas = las = 0.0

                if finish == "timeout" and not raw:
                    cp.state.setdefault("skipped_ids", []).append(item["id"])
                    print(f"  [{i+1:4d}/{total}] ⏭️  SKIP (csak reasoning, nincs kimenet) [{elapsed:.0f}s]")
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{datetime.now(timezone.utc).isoformat()} | ud_v4 | SKIP | {item['id']} | reasoning={len(reasoning)}c\n")
                    cp.save()
                    continue

                if raw:
                    parsed = parse_conllu_from_response(raw, item["tokens"])
                    if parsed:
                        upos = round(parsed["upos_correct"] / max(1, parsed["upos_total"]), 4)
                        uas = round(parsed["head_correct"] / max(1, parsed["head_total"]), 4)
                        las = round(parsed["deprel_correct"] / max(1, parsed["deprel_total"]), 4)

                fout.write(json.dumps({
                    "id": item["id"], "task": "ud_hungarian",
                    "model": model,
                    "prompt": prompt,
                    "gold_conllu": item["gold_conllu"],
                    "raw_response": raw,
                    "reasoning_length": len(reasoning),
                    "finish_reason": finish,
                    "upos_accuracy": upos,
                    "uas": uas,
                    "las": las,
                    "parsed_tokens": parsed,
                    "mode": "think",
                    "backend": "openai",
                    "dataset_version": "v4",
                    "result_elapsed": round(elapsed),
                }, ensure_ascii=False) + "\n")
                fout.flush()
                os.fsync(fout.fileno())
                cp.mark_completed(item["id"], True)
                processed += 1

                done = len(cp.state["completed_ids"])
                skipped_total = len(cp.state.get("skipped_ids", []))
                upos_pct = f"{upos*100:.0f}%" if upos > 0 else "N/A"
                uas_pct = f"{uas*100:.0f}%" if uas > 0 else "N/A"
                las_pct = f"{las*100:.0f}%" if las > 0 else "N/A"
                avg_time = (time.time() - global_start) / max(1, done + skipped_total)
                remaining = total - done - skipped_total
                eta_h = avg_time * remaining / 3600

                print(f"  [{done:4d}/{total}] UPOS={upos_pct} UAS={uas_pct} LAS={las_pct} "
                      f"({len(reasoning)}c r, {len(raw)}c {finish}) [{elapsed:.0f}s] "
                      f"ETA={eta_h:.1f}h skip={skipped_total}")
                cp.save()
    except KeyboardInterrupt:
        cp.mark_stopped("manual_stop")
        print(f"\n⛸  Manual stop. State: {state_path}")
        return 130

    cp.mark_completed_full()

    all_results = [json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines()]
    n = len(all_results)
    skipped_total = len(cp.state.get("skipped_ids", []))
    if n > 0:
        avg_upos = sum(r["upos_accuracy"] for r in all_results) / n
        avg_uas = sum(r["uas"] for r in all_results) / n
        avg_las = sum(r["las"] for r in all_results) / n
        composite = (avg_upos + avg_uas + avg_las) / 3.0
    else:
        avg_upos = avg_uas = avg_las = composite = 0.0

    summary = {
        "model": model, "benchmark": "ud_hungarian_v4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": cp.state["run_id"],
        "num_examples": n,
        "skipped": skipped_total,
        "accuracy": round(composite, 4),
        "upos_accuracy": round(avg_upos, 4),
        "uas": round(avg_uas, 4),
        "las": round(avg_las, 4),
        "dataset_version": "v4",
    }
    (out_dir / "ud_hungarian_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    total_h = (time.time() - global_start) / 3600
    print(f"\n✅ KÉSZ: {n} mondat + {skipped_total} skip | Composite={composite:.4f} | {total_h:.1f}h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
