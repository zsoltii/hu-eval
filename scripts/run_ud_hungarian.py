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
from stop_on_error import call_ollama_strict, OllamaFatalError, FatalBackendError, MAX_OUTPUT_TOKENS
from openai_compat import call_openai_strict
from deg_loop import is_degenerate

OLLAMA_URL = "http://localhost:11434"
DEFAULT_OPENAI_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OPENAI_API_KEY = "ollama"
DATASET_PATH = Path("./data/ud_hungarian/ud_hungarian_std.jsonl")
DEFAULT_RESULTS_DIR = Path("./results")
DEFAULT_STATE_DIR = Path("./state")
LOG_PATH = Path("./logs/ud_hungarian_runs.log")

# Degenerált (token-loopos) generáció esetén ennyi újrapróbálkozás történik.
# A UD Hungarian az egyetlen benchmark hosszú szabad szöveges kimenettel, így
# csak itt fordulhat elő ilyen hiba; a HuLU/MMLU 1 karakteres válaszokat ad.
DEGENERATE_RETRIES = 2
# Az újrapróbálkozás rövidebb token-plafonnal fut: a cél egy használható
# minta, nem a maximális hossz. Így a használhatatlan (degenerált) generáció
# ~1,5 perc alatt levágódik a 32k context helyett ~6 perc. A valid CoNLL-U
# tábla a válasz elején van, így a rövidebb plafon nem vágja le a pontszámolt
# részt (a 32k teljes generációk 70-95k karakteresek, a parse-olható tábla
# ezek elején található).
DEGENERATE_RETRY_MAX_TOKENS = 8192


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

    upos_re = re.compile(r"^[A-Z][A-Z0-9_-]*$")
    # A 17 univerzális POS tag + a gyakori UD-specifikus kategória. A modell
    # gyakran a tag NEVÉT írja ("noun", "proper", "adj") — ezeket is elfogadjuk.
    pos_aliases = {
        "NOUN": "NOUN", "VERB": "VERB", "ADJ": "ADJ", "ADJECTIVE": "ADJ",
        "ADV": "ADV", "ADVERB": "ADV", "PROPN": "PROPN", "PROPER": "PROPN",
        "PROPERNOUN": "PROPN", "PRON": "PRON", "PRONOUN": "PRON",
        "DET": "DET", "DETERMINER": "DET", "ADP": "ADP", "PREPOSITION": "ADP",
        "CCONJ": "CCONJ", "CONJ": "CCONJ", "CONJUNCTION": "CCONJ",
        "SCONJ": "SCONJ", "SUBORDINATING": "SCONJ", "NUM": "NUM",
        "NUMERAL": "NUM", "AUX": "AUX", "AUXILIARY": "AUX", "PART": "PART",
        "PARTICLE": "PART", "INTJ": "INTJ", "INTERJECTION": "INTJ",
        "PUNCT": "PUNCT", "PUNCTUATION": "PUNCT", "X": "X", "SYM": "SYM",
        "COMPOUND": "COMPOUND", "C": "CCONJ", "U": "SCONJ",
    }

    def _pos_of(value: str) -> str | None:
        """A POS tag kanonikus alakja, ha a cella POS-jellegű."""
        v = (value or "").strip()
        if not v:
            return None
        key = v.upper().split(":")[0].split("=")[0].strip()
        if key in pos_aliases:
            return pos_aliases[key]
        return None

    def _find_upos(parts: list[str]) -> tuple[int, str] | None:
        """Az UPOS oszlop (index, érték).

        A standard hely a 4. oszlop (index 3) — ezt preferáljuk. Ha ott nem
        POS-jellegű érték van (a modell beszúr egy extra FORM-ot, vagy a POS
        tag neve kisbetűvel jön máshol), akkor az első POS-jellegű oszlopot
        vesszük. A 17 univerzális tag whitelistje védi a false positive-okat.
        """
        if len(parts) > 3:
            p = _pos_of(parts[3])
            if p:
                return 3, p
        for i in range(min(len(parts), 8)):
            if i == 3:
                continue
            p = _pos_of(parts[i])
            if p:
                return i, p
        return None

    def _extract(parts: list[str]) -> dict | None:
        """ID FORM LEMMA UPOS ... HEAD DEPREL — 7–10 oszlopos CoNLL-U.

        A HEAD az UPOS utáni első tiszta egész számú oszlop, a DEPREL az
        utána következő kisbetűs kapcsolat. Így a 10 oszlopos
        (XPOS+FEATS+DEPS+MISC), a 9 oszlopos (XPOS nélküli) és a 7 oszlopos
        (csak FEATS) válasz is helyesen parse-ol — a korábbi `parts[6]` fix a
        7–9 oszlopos válaszokon elcsúszott, és a HEAD/DEPREL 0 lett.

        Az UPOS oszlopát is robusztusan keressük (lásd `_find_upos`): a modell
        gyakran beszúr egy extra FORM-ot a LEMMA után, amitől a fix 4. index
        félrement (a teljes sort eldobtuk → UPOS 0). Az ID oszlop szintén
        elcsúszhat (nincs ID oszlop, vagy a 2. helyen van) — a HEAD előtti
        első egész a token sorszáma; ha nincs, a sor pozíciója az ID (lásd a
        hívó oldali ID-javítást).
        """
        if len(parts) < 5:
            return None
        found = _find_upos(parts)
        if not found:
            return None
        upos_idx, upos = found
        head_idx = None
        for i in range(upos_idx + 1, len(parts)):
            if parts[i].strip().isdigit():
                head_idx = i
                break
        if head_idx is None:
            return None
        deprel = None
        for i in range(head_idx + 1, len(parts)):
            v = (parts[i] or "").strip()
            if v and re.match(r"^[a-z][a-z:]*$", v):
                deprel = v
                break
        if deprel is None:
            return None
        # a token ID: az UPOS előtti első egész oszlop (a HEAD már később van)
        token_id = None
        for i in range(upos_idx):
            v = (parts[i] or "").strip()
            if v.isdigit():
                token_id = v
                break
        return {
            "id": token_id,
            "upos": upos,
            "head": parts[head_idx].strip(),
            "deprel": deprel,
        }

    pred_tokens = []
    pos = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue
        # tabulátoros CoNLL-U (a leggyakoribb), majd whitespace-es változat
        tok = _extract(line.split("\t"))
        if tok is None:
            tok = _extract(line.split())
        if tok:
            # ha nincs ID oszlop, a sor pozíciója a token sorszáma
            pos += 1
            if tok.get("id") is None:
                tok["id"] = str(pos)
            pred_tokens.append(tok)
            continue
        # szabad szöveges / listás formátumok
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
                  api_key: str = DEFAULT_OPENAI_API_KEY,
                  num_predict: int | None = None) -> int:
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
                raw = ""
                degen_tries = 0
                while True:
                    # Az első kérés a num_predict plafonnal fut (alapértelmezetten
                    # 32k; --num-predict -1 -> a modell saját max output korlátja
                    # a plafon, azaz nincs mesterséges kimeneti korlát). Az
                    # újrapróbálkozások rövidebb plafonnal futnak
                    # (DEGENERATE_RETRY_MAX_TOKENS), hogy a loop hamarabb
                    # vágódjon le.
                    cap = num_predict if degen_tries == 0 else DEGENERATE_RETRY_MAX_TOKENS

                    try:
                        if backend == "openai":
                            response = call_openai_strict(
                                item["prompt"], model,
                                think=think,
                                num_predict=cap,
                                timeout=(3600 if think else 900),
                                max_retries=(2 if think else 3),
                                base_url=base_url,
                                api_key=api_key,
                            )
                        else:
                            response = call_ollama_strict(
                                item["prompt"], model,
                                think=think,
                                num_predict=cap,
                                timeout=(3600 if think else 900),
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

                    # Degenerált (token-loopos) generáció: a modell a 32k
                    # contextet tölti fel ismétlődő számsorral/szósorral. Ez
                    # mintafüggő, ezért a hibás generációt újrakérjük (bounded
                    # retry) — a mérés így a képességet mutatja, nem a szerver
                    # sampling-artefaktumát. A stop-policy érintetlen: a
                    # retry csak sikeres válasz után, degeneráció esetén fut.
                    if not is_degenerate(raw) or degen_tries >= DEGENERATE_RETRIES:
                        break
                    degen_tries += 1
                    print(f"  ⚠️  [{item['id']}] degenerált válasz ({len(raw)} char) "
                          f"→ újrapróbálkozás {degen_tries}/{DEGENERATE_RETRIES}")
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{log_line} | DEGENERATE @ {item['id']} "
                                f"len={len(raw)} retry={degen_tries}\n")

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
                    "degenerate_retries": degen_tries,
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
    p.add_argument("--num-predict", type=int, default=None,
                   help="Max generált token az első kérésre. Default: modell szerint "
                        "(Ollama Cloud: nincs plafon / a modell saját max outputja; "
                        "lokális: 32768). -1 = kényszerű nincs plafon.")
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
