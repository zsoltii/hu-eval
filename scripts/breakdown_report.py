#!/usr/bin/env python
"""
breakdown_report.py — Per-benchmark per-sub-task bontás + composite riport.

A canonical `aggregate_results.py` csak egy composite oszlopot ad.
Ez a script a `results/{model}-{mode}/{benchmark}_results.jsonl` fájlokat járja be,
és minden modellre / módra kiírja a sub-taskok pontosságát.

Támogatott benchmarkok:
  - hulu: 6 NLU sub-task (HuCOLA, HuCoPA, HuRTE, HuSST, HuWNLI, HuCB)
  - mmlu_hu: 38 tantárgy
  - ud_hungarian: 3 metrika (UPOS, UAS, LAS) per modell + composite

Használat:
  python scripts/breakdown_report.py --benchmark hulu
  python scripts/breakdown_report.py --benchmark mmlu_hu --results-dir ./results --out ./reports
  python scripts/breakdown_report.py --benchmark ud_hungarian

Duplikátumok kezelése: a RESUME ciklusok miatt ugyanaz az `id` többször is
előfordulhat. Az utolsó előfordulást tekintjük authoritatívnak.
"""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox


BENCH_CONFIGS: dict[str, dict] = {}


def _register_benchmarks():
    from types import SimpleNamespace

    ctx = SimpleNamespace(TASKS=None, TASK_LABELS=None, TASK_MAX=None, NO_TASK_FIELD=False)

    # ── HuLU ──────────────────────────────────────────────────────────
    ctx.TASKS = ["hucola", "hucopa", "hurte", "husst", "huwnli", "hucb"]
    ctx.TASK_LABELS = {
        "hucola": "HuCOLA", "hucopa": "HuCoPA", "hurte": "HuRTE",
        "husst": "HuSST", "huwnli": "HuWNLI", "hucb": "HuCB",
    }
    ctx.TASK_MAX = {"hucola": 910, "hucopa": 100, "hurte": 243, "husst": 1165, "huwnli": 60, "hucb": 103}
    BENCH_CONFIGS["hulu"] = ctx

    # ── MMLU-HU ───────────────────────────────────────────────────────
    ctx2 = SimpleNamespace(TASKS=None, TASK_LABELS=None, TASK_MAX=None, NO_TASK_FIELD=False)
    ctx2.TASKS_MMLU = [
        "abstract_algebra", "anatomy", "astronomy", "business_ethics", "clinical_knowledge",
        "college_biology", "college_chemistry", "college_computer_science", "college_mathematics",
        "college_medicine", "college_physics", "computer_security", "conceptual_physics",
        "econometrics", "electrical_engineering", "elementary_mathematics", "formal_logic",
        "global_facts", "high_school_biology", "high_school_chemistry", "high_school_computer_science",
        "high_school_european_history", "high_school_geography", "high_school_government_and_politics",
        "high_school_macroeconomics", "high_school_mathematics", "high_school_microeconomics",
        "high_school_physics", "high_school_psychology", "human_aging", "human_sexuality",
        "jurisprudence", "prehistory", "professional_medicine", "public_relations",
        "sociology", "virology", "world_religions",
    ]
    ctx2.TASK_LABELS = {t: t.replace("_", " ").title() for t in ctx2.TASKS_MMLU}
    ctx2.TASK_MAX = {}
    BENCH_CONFIGS["mmlu_hu"] = ctx2

    # ── UD Hungarian ──────────────────────────────────────────────────
    ctx3 = SimpleNamespace(TASKS=None, TASK_LABELS=None, TASK_MAX=None, NO_TASK_FIELD=False)
    # Nincsenek sub-task-ok — a JSONL-ben 3 mező van: upos, uas, las per mondat
    ctx3.TASKS_UAS = ["upos", "uas", "las"]
    ctx3.TASK_LABELS = {"upos": "UPOS", "uas": "UAS", "las": "LAS"}
    ctx3.TASK_MAX = {}
    BENCH_CONFIGS["ud_hungarian"] = ctx3


_register_benchmarks()


def collect_per_task(jsonl_path: Path, config) -> dict[str, dict]:
    """Visszatér: {task: {'correct': N, 'total': N, 'acc': 0-1}}.

    Duplikátumok: az utolsó előfordulás számít (id alapján).
    """
    by_id: dict[str, dict] = {}
    for line_no, line in enumerate(jsonl_path.open(encoding="utf-8"), start=1):
        rec = json.loads(line)
        rec_id = rec.get("id")
        if not rec_id:
            raise ValueError(
                f"{jsonl_path}:{line_no}: missing 'id' field — cannot deduplicate"
            )
        by_id[rec_id] = rec

    per_task: dict[str, dict] = {}
    for rec in by_id.values():
        t = rec.get("task")
        if t and t in (config.TASK_LABELS if hasattr(config, 'TASK_LABELS') else config.TASKS_UAS):
            bucket = per_task.setdefault(t, {"correct": 0, "total": 0})
            bucket["total"] += 1
            if rec.get("correct"):
                bucket["correct"] += 1
        elif hasattr(config, 'TASKS_UAS') and not t:
            # UD Hungarian: no 'task' field, three score fields per sentence
            for metric in config.TASKS_UAS:
                val = rec.get(metric)
                if val is not None:
                    bucket = per_task.setdefault(metric, {"correct": 0, "total": 0})
                    bucket["total"] += 1
                    if val:
                        bucket["correct"] += 1
        else:
            continue

    for t, b in per_task.items():
        b["acc"] = b["correct"] / b["total"] if b["total"] else 0.0
    return per_task


def composite_acc(per_task: dict[str, dict], tasks: list[str]) -> float:
    """Sub-task-ok egyenlő súlyú átlaga."""
    accs = [per_task[t]["acc"] for t in tasks if t in per_task]
    return sum(accs) / len(accs) if accs else float("nan")


def overall_acc(per_task: dict[str, dict]) -> float:
    """Prompt-számmal súlyozott accuracy: total_correct / total_examples."""
    total_c = sum(b["correct"] for b in per_task.values())
    total_n = sum(b["total"] for b in per_task.values())
    return total_c / total_n if total_n else float("nan")


def parse_model_mode(dirname: str) -> tuple[str, str]:
    """Pl. 'minimax-m3-cloud-think' -> ('minimax-m3:cloud', 'think')."""
    for mode in ("think", "nothink"):
        if dirname.endswith(f"-{mode}"):
            model = dirname[: -len(f"-{mode}")]
            return model, mode
    return dirname, "nothink"


def render_table_png(
    out_path: Path,
    title: str,
    headers: list[str],
    row_labels: list[str],
    cells: list[list[str]],
    col_widths: list[float] | None = None,
    footer: str | None = None,
) -> None:
    """matplotlib table-t renderel PNG-be."""
    n_rows = len(row_labels)
    n_cols = len(headers)
    fig_height = max(8, n_rows * 0.55 + 2.5)
    fig_width = max(18, n_cols * 1.8 + 4)
    if headers[0] == "Modell (mód)":
        fig_width += 3
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=16)

    table = ax.table(
        cellText=cells,
        rowLabels=row_labels,
        colLabels=headers,
        loc="center",
        cellLoc="center",
        rowColours=["#e6e6e6"] * n_rows,
        colColours=["#d9d9d9"] * n_cols,
        colWidths=col_widths,
        bbox=Bbox.from_bounds(0.02, 0.04, 0.96, 0.90),
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.0, 2.0)

    for key, cell in table.get_celld().items():
        row, col = key
        if row == 0 or col == -1:
            cell.set_text_props(fontweight="bold")
            cell.set_facecolor("#cccccc")
        cell.set_edgecolor("#aaaaaa")

    if footer:
        fig.text(0.5, 0.01, footer, ha="center", fontsize=9, style="italic")

    plt.savefig(out_path, dpi=200, facecolor="white")
    plt.close(fig)


def build_hulu(rows: list[dict], config, args):
    """HuLU per-sub-task riport + PNG."""
    tasks = config.TASKS
    task_labels = config.TASK_LABELS

    # CSV
    csv_path = args.out / "hulu_breakdown.csv"
    fieldnames = ["model", "mode", "composite", "overall"]
    for t in tasks:
        fieldnames += [f"{t}_acc", f"{t}_n"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out = {}
            for k, v in r.items():
                if isinstance(v, float):
                    out[k] = f"{v:.4f}"
                else:
                    out[k] = v
            w.writerow(out)

    # Markdown
    lines = [
        "# HuLU Per-Sub-Task Bontás",
        "",
        f"*Generálva:* {datetime.now(timezone.utc).isoformat()}",
        "",
        f"*{len(rows)} benchmark (egyedi rekord: utolsó előfordulás alapján).*",
        "",
        "## Táblázat — think vs nothink (accuracy %, külön oszlopok)",
        "",
        "![Think vs nothink accuracy](hulu_breakdown_think_nothink.png)",
        "",
        "| Modell | " + " | ".join(f"{task_labels[t]} nt" for t in tasks)
        + " | " + " | ".join(f"{task_labels[t]} th" for t in tasks)
        + " | Composite nt | Composite th | Overall nt | Overall th |",
        "|" + "---|" * (len(tasks) * 2 + 5),
    ]
    by_model: dict[str, dict[str, dict]] = {}
    for r in rows:
        by_model.setdefault(r["model"], {})[r["mode"]] = r
    for model in sorted(by_model):
        modes = by_model[model]
        nt = modes.get("nothink")
        th = modes.get("think")
        cells = [f"**{model}**"]
        for t in tasks:
            acc = nt.get(f"{t}_acc") if nt else None
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        for t in tasks:
            acc = th.get(f"{t}_acc") if th else None
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        cells.append("—" if nt is None else f"{nt['composite'] * 100:.1f}%")
        cells.append("—" if th is None else f"{th['composite'] * 100:.1f}%")
        cells.append("—" if nt is None else f"{nt['overall'] * 100:.1f}%")
        cells.append("—" if th is None else f"{th['overall'] * 100:.1f}%")
        lines.append("| " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Táblázat — per sub-task (accuracy %)",
        "",
        "![Per-sub-task accuracy](hulu_breakdown_accuracy.png)",
        "",
        "| Modell (mód) | " + " | ".join(task_labels[t] for t in tasks)
        + " | Composite | Overall |",
        "|" + "---|" * (len(tasks) + 3),
    ]
    for r in rows:
        cells = [f"**{r['model']} ({r['mode']})**"]
        for t in tasks:
            acc = r.get(f"{t}_acc")
            n = r.get(f"{t}_n", 0)
            if acc is None:
                cells.append("—")
            else:
                cells.append(f"{acc * 100:.1f}% (n={n})")
        cells.append(f"**{r['composite'] * 100:.1f}%**")
        cells.append(f"{r['overall'] * 100:.1f}%")
        lines.append("| " + " | ".join(cells) + " |")

    # PNG: wide-format think vs nothink
    wide_headers = ["Modell"]
    for t in tasks:
        wide_headers.append(f"{task_labels[t]} nt")
    for t in tasks:
        wide_headers.append(f"{task_labels[t]} th")
    wide_headers += ["Composite nt", "Composite th", "Overall nt", "Overall th"]
    wide_rows = []
    for model in sorted(by_model):
        modes = by_model[model]
        nt = modes.get("nothink")
        th = modes.get("think")
        cells = [model]
        for t in tasks:
            acc = nt.get(f"{t}_acc") if nt else None
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        for t in tasks:
            acc = th.get(f"{t}_acc") if th else None
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        cells.append("—" if nt is None else f"{nt['composite'] * 100:.1f}%")
        cells.append("—" if th is None else f"{th['composite'] * 100:.1f}%")
        cells.append("—" if nt is None else f"{nt['overall'] * 100:.1f}%")
        cells.append("—" if th is None else f"{th['overall'] * 100:.1f}%")
        wide_rows.append(cells)
    wide_png = args.out / "hulu_breakdown_think_nothink.png"
    render_table_png(
        wide_png,
        "HuLU think vs nothink per sub-task accuracy",
        wide_headers,
        [str(i + 1) for i in range(len(wide_rows))],
        wide_rows,
        col_widths=[3.0] + [0.85] * (len(tasks) * 2) + [1.2] * 4,
        footer="nt = nothink, th = think | azonos modell két módja egymás melletti oszlopokban",
    )

    # PNG: accuracy
    acc_rows = []
    for r in rows:
        cells = [f"{r['model']} ({r['mode']})"]
        for t in tasks:
            acc = r.get(f"{t}_acc")
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        cells.append(f"{r['composite'] * 100:.1f}%")
        cells.append(f"{r['overall'] * 100:.1f}%")
        acc_rows.append(cells)
    acc_png = args.out / "hulu_breakdown_accuracy.png"
    render_table_png(
        acc_png,
        "HuLU per-sub-task accuracy",
        ["Modell (mód)"] + [task_labels[t] for t in tasks] + ["Composite", "Overall"],
        [str(i + 1) for i in range(len(rows))],
        acc_rows,
        col_widths=[3.0] + [1.0] * len(tasks) + [1.2, 1.2],
        footer="Composite = sub-task-ok egyenlő súlyú átlaga | Overall = prompt-számmal súlyozott átlag",
    )

    md_path = args.out / "hulu_breakdown.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"💾 Kész: {md_path}, {csv_path}, {wide_png.name}, {acc_png.name}")


def build_mmlu_hu(rows: list[dict], config, args):
    """MMLU-HU: 38 subject breakdown."""
    tasks = config.TASKS_MMLU
    task_labels = config.TASK_LABELS

    # CSV
    csv_path = args.out / "mmlu_hu_breakdown.csv"
    fieldnames = ["model", "mode", "composite", "overall"]
    for t in tasks:
        fieldnames += [f"{t}_acc", f"{t}_n"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out = {}
            for k, v in r.items():
                if isinstance(v, float):
                    out[k] = f"{v:.4f}"
                else:
                    out[k] = v
            w.writerow(out)

    # Markdown
    lines = [
        "# MMLU-HU Per-Subject Bontás",
        "",
        f"*Generálva:* {datetime.now(timezone.utc).isoformat()}",
        "",
        f"*{len(rows)} benchmark (egyedi rekord: utolsó előfordulás alapján).*",
        "",
        "Composite = 38 subject egyenlő súlyú átlaga.",
        "Overall = prompt-számmal súlyozott átlag.",
        "",
        "## Táblázat — per subject (accuracy %)",
        "",
        "![Per-subject accuracy](mmlu_hu_breakdown_accuracy.png)",
        "",
        "| Modell (mód) | " + " | ".join(task_labels[t] for t in tasks)
        + " | Composite | Overall |",
        "|" + "---|" * (len(tasks) + 3),
    ]
    for r in rows:
        cells = [f"**{r['model']} ({r['mode']})**"]
        for t in tasks:
            acc = r.get(f"{t}_acc")
            n = r.get(f"{t}_n", 0)
            if acc is None:
                cells.append("—")
            else:
                cells.append(f"{acc * 100:.1f}% (n={n})")
        cells.append(f"**{r['composite'] * 100:.1f}%**")
        cells.append(f"{r['overall'] * 100:.1f}%")
        lines.append("| " + " | ".join(cells) + " |")

    # PNG: accuracy
    acc_rows = []
    for r in rows:
        cells = [f"{r['model']} ({r['mode']})"]
        for t in tasks:
            acc = r.get(f"{t}_acc")
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        cells.append(f"{r['composite'] * 100:.1f}%")
        cells.append(f"{r['overall'] * 100:.1f}%")
        acc_rows.append(cells)
    acc_png = args.out / "mmlu_hu_breakdown_accuracy.png"
    render_table_png(
        acc_png,
        "MMLU-HU per-subject accuracy",
        ["Modell (mód)"] + [task_labels[t] for t in tasks] + ["Composite", "Overall"],
        [str(i + 1) for i in range(len(rows))],
        acc_rows,
        col_widths=[3.0] + [0.9] * len(tasks) + [1.2, 1.2],
        footer="Composite = 38 subject egyenlő súlyú átlaga | Overall = prompt-számmal súlyozott átlag",
    )

    md_path = args.out / "mmlu_hu_breakdown.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"💾 Kész: {md_path}, {csv_path}, {acc_png.name}")


def build_ud_hungarian(rows: list[dict], config, args):
    """UD Hungarian: per-sentence UPOS/UAS/LAS breakdown."""
    metrics = config.TASKS_UAS
    metric_labels = config.TASK_LABELS

    # CSV
    csv_path = args.out / "ud_hungarian_breakdown.csv"
    fieldnames = ["model", "mode", "composite"]
    for m in metrics:
        fieldnames += [f"{m}_acc", f"{m}_n"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out = {}
            for k, v in r.items():
                if isinstance(v, float):
                    out[k] = f"{v:.4f}"
                else:
                    out[k] = v
            w.writerow(out)

    # Markdown
    lines = [
        "# UD Hungarian Per-Metric Bontás",
        "",
        f"*Generálva:* {datetime.now(timezone.utc).isoformat()}",
        "",
        f"*{len(rows)} benchmark (egyedi rekord: utolsó előfordulás alapján).*",
        "",
        "Composite = (UPOS + UAS + LAS) / 3.",
        "",
        "## Táblázat — per metric (accuracy %)",
        "",
        "![Per-metric accuracy](ud_hungarian_breakdown_accuracy.png)",
        "",
        "| Modell (mód) | " + " | ".join(metric_labels[m] for m in metrics)
        + " | Composite |",
        "|" + "---|" * (len(metrics) + 2),
    ]
    for r in rows:
        cells = [f"**{r['model']} ({r['mode']})**"]
        for m in metrics:
            acc = r.get(f"{m}_acc")
            n = r.get(f"{m}_n", 0)
            if acc is None:
                cells.append("—")
            else:
                cells.append(f"{acc * 100:.1f}% (n={n})")
        cells.append(f"**{r['composite'] * 100:.1f}%**")
        lines.append("| " + " | ".join(cells) + " |")

    # PNG
    acc_rows = []
    for r in rows:
        cells = [f"{r['model']} ({r['mode']})"]
        for m in metrics:
            acc = r.get(f"{m}_acc")
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        cells.append(f"{r['composite'] * 100:.1f}%")
        acc_rows.append(cells)
    acc_png = args.out / "ud_hungarian_breakdown_accuracy.png"
    render_table_png(
        acc_png,
        "UD Hungarian per-metric accuracy",
        ["Modell (mód)"] + [metric_labels[m] for m in metrics] + ["Composite"],
        [str(i + 1) for i in range(len(rows))],
        acc_rows,
        col_widths=[3.0] + [1.0] * len(metrics) + [1.2],
        footer="Composite = (UPOS + UAS + LAS) / 3",
    )

    md_path = args.out / "ud_hungarian_breakdown.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"💾 Kész: {md_path}, {csv_path}, {acc_png.name}")


BUILDERS: dict[str, callable] = {
    "hulu": build_hulu,
    "mmlu_hu": build_mmlu_hu,
    "ud_hungarian": build_ud_hungarian,
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--benchmark", required=True,
                    choices=sorted(BUILDERS.keys()),
                    help="Benchmark típusa")
    p.add_argument("--results-dir", type=Path, default=Path("./results"))
    p.add_argument("--out", type=Path, default=Path("./reports"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    config = BENCH_CONFIGS[args.benchmark]
    if hasattr(config, 'TASKS'):
        tasks = config.TASKS
    elif hasattr(config, 'TASKS_MMLU'):
        tasks = config.TASKS_MMLU
    else:
        tasks = config.TASKS_UAS
    has_task_field = not hasattr(config, 'TASKS_UAS') or not config.TASKS_UAS

    rows = []
    for model_dir in sorted(args.results_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        jsonl = model_dir / f"{args.benchmark}_results.jsonl"
        if not jsonl.exists():
            continue
        model, mode = parse_model_mode(model_dir.name)
        per_task = collect_per_task(jsonl, config)
        if not per_task:
            continue
        comp = composite_acc(per_task, tasks)
        if hasattr(config, 'TASKS_UAS') and not hasattr(config, 'TASKS'):
            # UD: nincs 'overall', mert a 3 metrika egyenlő súlyú
            overall_val = comp
        else:
            overall_val = overall_acc(per_task)
        row = {"model": model, "mode": mode, "composite": comp, "overall": overall_val}
        for t in tasks:
            if t in per_task:
                row[f"{t}_acc"] = per_task[t]["acc"]
                row[f"{t}_n"] = per_task[t]["total"]
            else:
                row[f"{t}_acc"] = None
                row[f"{t}_n"] = 0
        rows.append(row)

    if not rows:
        print(f"❌ Nincs feldolgozható {args.benchmark}_results.jsonl.")
        return 1

    rows.sort(key=lambda r: (-r["composite"], r["model"], r["mode"]))
    builder = BUILDERS[args.benchmark]
    builder(rows, config, args)

    print(f"\n{'Modell (mód)':<40s}  Composite")
    for r in rows:
        print(f"  {r['model'] + '-' + r['mode']:<38s}  {r['composite'] * 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
