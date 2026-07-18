#!/usr/bin/env python
"""
hulu_breakdown_report.py — HuLU per-sub-task bontás + composite riport.

A canonical `aggregate_results.py` csak egy HuLU oszlopot ad (composite).
Ez a script a `results/{model}-{mode}/hulu_results.jsonl` fájlokat járja be,
és minden modellre / módra kiírja a 6 NLU sub-task (HuCOLA, HuCoPA, HuRTE,
HuSST, HuWNLI, HuCB) pontosságát + a 6 átlagából képzett HuLU composite score-t.

Csak a pontosság (accuracy) az érdekes — sebesség, token, idő szándékosan
nincs a riportban. A modell kiegyensúlyozottságát (Composite) és a HuSST-vel
súlyozott produkciós pontosságot (Overall) is kiírjuk, mert más-más
szempontból informatívak.

Duplikátumok kezelése: a RESUME ciklusok miatt ugyanaz az `id` többször is
előfordulhat. Az utolsó előfordulást tekintjük authoritatívnak.

Használat:
  python scripts/hulu_breakdown_report.py
  python scripts/hulu_breakdown_report.py --out ./reports
  python scripts/hulu_breakdown_report.py --results-dir ./results

Kimenet:
  reports/hulu_breakdown.md
  reports/hulu_breakdown.csv
  reports/hulu_breakdown_think_nothink.png   (think vs nothink wide-format)
  reports/hulu_breakdown_accuracy.png        (per-sub-task accuracy)

Részletek: wiki/concepts/hulu-benchmark.md "Sub-task részletek" szekció.
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

TASKS = ["hucola", "hucopa", "hurte", "husst", "huwnli", "hucb"]
TASK_LABELS = {
    "hucola": "HuCOLA",
    "hucopa": "HuCoPA",
    "hurte":  "HuRTE",
    "husst":  "HuSST",
    "huwnli": "HuWNLI",
    "hucb":   "HuCB",
}
TASK_MAX = {"hucola": 910, "hucopa": 100, "hurte": 243, "husst": 1165, "huwnli": 60, "hucb": 103}


def collect_per_task(jsonl_path: Path) -> dict[str, dict]:
    """Visszatér: {task: {'correct': N, 'total': N, 'acc': 0-1}}.

    Csak pontosság — sebesség/idő/token szándékosan nincs a riportban.

    Duplikátumok: az utolsó előfordulás számít (id alapján).
    """
    by_id: dict[str, dict] = {}
    for line_no, line in enumerate(jsonl_path.open(encoding="utf-8"), start=1):
        rec = json.loads(line)
        rec_id = rec.get("id")
        if not rec_id:
            raise ValueError(
                f"{jsonl_path}:{line_no}: missing 'id' field — cannot deduplicate RESUME records"
            )
        by_id[rec_id] = rec

    per_task: dict[str, dict] = {}
    for rec in by_id.values():
        t = rec["task"]
        if t not in TASK_LABELS:
            continue
        bucket = per_task.setdefault(t, {"correct": 0, "total": 0})
        bucket["total"] += 1
        if rec.get("correct"):
            bucket["correct"] += 1

    for t, b in per_task.items():
        b["acc"] = b["correct"] / b["total"] if b["total"] else 0.0
    return per_task


def composite_acc(per_task: dict[str, dict]) -> float:
    """6 NLU sub-task átlaga (egyszerű, nem súlyozott — HuCOLA-t is accuracy-ként).

    Megfelel a `wiki/concepts/hulu-benchmark.md` specifikációjának:
    "A 6 NLU task átlaga a HuLU score (0-100 skálán)".
    """
    accs = [per_task[t]["acc"] for t in TASKS if t in per_task]
    return sum(accs) / len(accs) if accs else float("nan")


def overall_acc(per_task: dict[str, dict]) -> float:
    """Súlyozott (task-méret szerinti) accuracy: total_correct / total_examples.

    Ez felel meg a `run_hulu.py` által a `hulu_summary.json` fájlba írt
    `accuracy` mezőnek, és a kanonikus `aggregate_results.py` HuLU
    composite_score-jának. A HuSST (1165 prompt) dominálja.
    """
    total_c = sum(b["correct"] for b in per_task.values())
    total_n = sum(b["total"] for b in per_task.values())
    return total_c / total_n if total_n else float("nan")


def parse_model_mode(dirname: str) -> tuple[str, str]:
    """Pl. 'minimax-m3-cloud-think' -> ('minimax-m3:cloud', 'think').

    Ha a mappa nem '-think' vagy '-nothink' suffix-szel végződik,
    a teljes nevet modellnévként, 'nothink'-et módként adja vissza.
    Ez a projektben jelenleg várható; új naming convention esetén
    a függvényt frissíteni kell.
    """
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
    """matplotlib table-t renderel PNG-be, fix figure mérettel."""
    n_rows = len(row_labels)
    n_cols = len(headers)
    fig_height = max(8, n_rows * 0.55 + 2.5)
    # Széles, de nem túl széles figure; a table a bbox=[0.02,0.02,0.96,0.92]-n belül marad
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

    # bbox_inches='tight' helyett fix méret, hogy a table ne nyújtsa szét a képet
    plt.savefig(out_path, dpi=200, facecolor="white")
    plt.close(fig)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", type=Path, default=Path("./results"))
    p.add_argument("--out", type=Path, default=Path("./reports"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows = []
    for model_dir in sorted(args.results_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        jsonl = model_dir / "hulu_results.jsonl"
        if not jsonl.exists():
            continue
        model, mode = parse_model_mode(model_dir.name)
        per_task = collect_per_task(jsonl)
        if not per_task:
            continue
        comp = composite_acc(per_task)
        overall = overall_acc(per_task)
        row = {"model": model, "mode": mode, "composite": comp, "overall": overall}
        for t in TASKS:
            if t in per_task:
                row[f"{t}_acc"] = per_task[t]["acc"]
                row[f"{t}_n"] = per_task[t]["total"]
            else:
                row[f"{t}_acc"] = None
                row[f"{t}_n"] = 0
        rows.append(row)

    if not rows:
        print("❌ Nincs feldolgozható hulu_results.jsonl.")
        return 1

    rows.sort(key=lambda r: (-r["composite"], r["model"], r["mode"]))

    # CSV
    csv_path = args.out / "hulu_breakdown.csv"
    fieldnames = ["model", "mode", "composite", "overall"]
    for t in TASKS:
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

    # Markdown riport
    lines = [
        "# HuLU Per-Sub-Task Bontás",
        "",
        f"*Generálva:* {datetime.now(timezone.utc).isoformat()}",
        "",
        f"*{len(rows)} benchmark (egyedi rekord: utolsó előfordulás alapján).*",
        "",
        "## Módszer",
        "",
        "A `results/{model}-{mode}/hulu_results.jsonl` fájlokból csoportosítunk a `task` "
        "mező szerint. Duplikátumok (RESUME-ból): az utolsó előfordulás számít. A sub-task "
        "accuracy egyszerű átlag (`correct / total`); a HuCOLA-t is így kezeljük (a kanonikus "
        "specifikáció MCC-t ír elő, de a JSONL `correct: bool` mezőt tartalmaz, így a "
        "kompatibilitás kedvéért itt is accuracy-t jelentetünk).",
        "",
        "- **Composite** (per spec): a 6 sub-task accuracy egyszerű (egyenként súlyozatlan) "
        "átlaga — megfelel a `wiki/concepts/hulu-benchmark.md` Aggregáció szekciójának.",
        "- **Overall** (kanonikus): az összes promptra számított accuracy "
        "(`total_correct / total_examples`) — ez a `hulu_summary.json` `accuracy` mezője, "
        "és a kanonikus `aggregate_results.py` HuLU score-ja. A HuSST (1165 prompt) "
        "dominálja, így a nehezebb HuSST-s modellek alacsonyabb overall score-t kapnak.",
        "",
        "## Táblázat — think vs nothink (accuracy %, külön oszlopok)",
        "",
        "![Think vs nothink accuracy](hulu_breakdown_think_nothink.png)",
        "",
        "| Modell | " + " | ".join(f"{TASK_LABELS[t]} nt" for t in TASKS)
        + " | " + " | ".join(f"{TASK_LABELS[t]} th" for t in TASKS)
        + " | Composite nt | Composite th | Overall nt | Overall th |",
        "|" + "---|" * (len(TASKS) * 2 + 5),
    ]
    # modellek szerint csoportosítás a wide-format táblázathoz
    by_model: dict[str, dict[str, dict]] = {}
    for r in rows:
        by_model.setdefault(r["model"], {})[r["mode"]] = r
    for model in sorted(by_model):
        modes = by_model[model]
        nt = modes.get("nothink")
        th = modes.get("think")
        cells = [f"**{model}**"]
        for t in TASKS:
            acc = nt.get(f"{t}_acc") if nt else None
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        for t in TASKS:
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
        "| Modell (mód) | " + " | ".join(TASK_LABELS[t] for t in TASKS)
        + " | Composite | Overall |",
        "|" + "---|" * (len(TASKS) + 3),
    ]
    for r in rows:
        cells = [f"**{r['model']} ({r['mode']})**"]
        for t in TASKS:
            acc = r.get(f"{t}_acc")
            n = r.get(f"{t}_n", 0)
            if acc is None:
                cells.append("—")
            else:
                cells.append(f"{acc * 100:.1f}% (n={n})")
        cells.append(f"**{r['composite'] * 100:.1f}%**")
        cells.append(f"{r['overall'] * 100:.1f}%")
        lines.append("| " + " | ".join(cells) + " |")

    # PNG riportok - táblázatonként külön kép
    png_files = []

    # 0. Wide-format think vs nothink táblázat
    wide_rows = []
    wide_headers = ["Modell"]
    for t in TASKS:
        wide_headers.append(f"{TASK_LABELS[t]} nt")
    for t in TASKS:
        wide_headers.append(f"{TASK_LABELS[t]} th")
    wide_headers += ["Composite nt", "Composite th", "Overall nt", "Overall th"]
    for model in sorted(by_model):
        modes = by_model[model]
        nt = modes.get("nothink")
        th = modes.get("think")
        cells = [model]
        for t in TASKS:
            acc = nt.get(f"{t}_acc") if nt else None
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        for t in TASKS:
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
        col_widths=[3.0] + [0.85] * (len(TASKS) * 2) + [1.2] * 4,
        footer="nt = nothink, th = think | azonos modell két módja egymás melletti oszlopokban",
    )
    png_files.append(wide_png.name)

    # 1. Accuracy táblázat
    acc_rows = []
    for r in rows:
        cells = [f"{r['model']} ({r['mode']})"]
        for t in TASKS:
            acc = r.get(f"{t}_acc")
            cells.append("—" if acc is None else f"{acc * 100:.1f}%")
        cells.append(f"{r['composite'] * 100:.1f}%")
        cells.append(f"{r['overall'] * 100:.1f}%")
        acc_rows.append(cells)
    acc_png = args.out / "hulu_breakdown_accuracy.png"
    render_table_png(
        acc_png,
        "HuLU per-sub-task accuracy (v1.2.8, 2026-06-15)",
        ["Modell (mód)"] + [TASK_LABELS[t] for t in TASKS] + ["Composite", "Overall"],
        [str(i + 1) for i in range(len(rows))],
        acc_rows,
        col_widths=[3.0] + [1.0] * len(TASKS) + [1.2, 1.2],
        footer="Composite = 6 sub-task egyenlő súlyú átlaga | Overall = prompt-számmal súlyozott átlag",
    )
    png_files.append(acc_png.name)

    md_path = args.out / "hulu_breakdown.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"💾 Kész: {md_path}, {csv_path}, " + ", ".join(str(p) for p in png_files))
    print(f"\n{'Modell (mód)':<40s}  Composite")
    for r in rows:
        print(f"  {r['model'] + '-' + r['mode']:<38s}  {r['composite'] * 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
