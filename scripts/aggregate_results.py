#!/usr/bin/env python
"""
aggregate_results.py — Eredmények aggregációja + composite score + riport.

Checkpoint-aware: részleges JSONL-eket is kezel (num_completed a state-ből jön).
Ha egy modell futása checkpoint miatt megszakadt, a riport tetején
"⚠️ Részleges eredmények" figyelmeztetés jelenik meg.

Használat:
  python aggregate_results.py
  python aggregate_results.py --results-dir ./results --out ./reports
  python aggregate_results.py --state-dir ./state

Részletek: wiki/runbooks/aggregate-results.md és wiki/concepts/checkpoint-progress.md
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Súlyok (az overview.md alapján: 40% stat + 40% gen + 20% ling)
W_STAT, W_GEN, W_LING = 0.40, 0.40, 0.20
STAT = ["hulu", "mmlu_hu"]
GEN = ["hugme", "mt_bench_hu"]
LING = ["ud_hungarian"]


def extract_score(summary: dict, benchmark: str) -> float | None:
    """0-1 közé normalizált score kinyerése summary dict-ből.
    Minden runner a saját summary-jában már 0-1 skálán tárolja a score-t."""
    if "accuracy" in summary:
        return float(summary["accuracy"])
    if "score" in summary:
        return float(summary["score"])
    return None


def judge_avg(path: Path) -> float | None:
    """Judge-olt JSONL-ből átlagos overall score 0-1 skálán.

    Két formátumot kezel:
    - HuGME: minden sor `{..., "judge": {"overall": float}}` (a judge_mt_bench nem ezt használja)
    - MT-Bench-HU: minden sor `{turn1_gsb, turn2_gsb}` ahol GSB = "A"|"B"|"S"
                   A win rate = wins / (wins + losses) (ties kihagyva), default 0.5 ha nincs döntés
    """
    if not path.exists():
        return None
    scores = []
    for line in path.open(encoding="utf-8"):
        r = json.loads(line)
        j = r.get("judge", {})
        if isinstance(j, dict) and isinstance(j.get("overall"), (int, float)):
            scores.append(j["overall"])
            continue
        # MT-Bench-HU GSB fallback
        gsb1 = r.get("turn1_gsb")
        gsb2 = r.get("turn2_gsb")
        if gsb1 in ("A", "B", "S") and gsb2 in ("A", "B", "S"):
            scores.append(1.0 if gsb1 == "A" and gsb2 == "A" else
                          0.0 if gsb1 == "B" and gsb2 == "B" else 0.5)
    return sum(scores) / len(scores) if scores else None


def collect(results_dir: Path, state_dir: Path) -> pd.DataFrame:
    """results/{model}/ mappák bejárása, DataFrame építése.
    Részleges JSONL-eket is elfogad (num_completed a state-ből jön)."""
    rows = []
    for model_dir in sorted(results_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        row = {"model": model_dir.name}
        partial_flags = []

        # Summary JSON fájlok
        for sp in model_dir.glob("*_summary.json"):
            try:
                data = json.loads(sp.read_text(encoding="utf-8"))
            except Exception:
                continue
            score = extract_score(data, sp.stem.replace("_summary", ""))
            if score is not None:
                row[sp.stem.replace("_summary", "")] = score
            if data.get("partial"):
                partial_flags.append(sp.stem.replace("_summary", ""))

        # Judge-olt JSONL fájlok
        for jp in model_dir.glob("*_judged.jsonl"):
            s = judge_avg(jp)
            if s is not None:
                row[jp.stem.replace("_judged", "")] = s
            # Részleges futás ellenőrzése a state-ből
            state_path = (state_dir / model_dir.name
                          / (jp.stem.replace("_judged", "") + ".json"))
            if state_path.exists():
                try:
                    st = json.loads(state_path.read_text(encoding="utf-8"))
                    if st.get("status") == "failed_stopped":
                        partial_flags.append(jp.stem.replace("_judged", ""))
                except Exception:
                    pass

        if partial_flags:
            row["partial_benchmarks"] = ",".join(sorted(set(partial_flags)))
        rows.append(row)
    return pd.DataFrame(rows).set_index("model")


def composite(df: pd.DataFrame) -> pd.DataFrame:
    """Composite score: 40/40/20 súlyozás, súlyarányos újraosztás
    hiányzó dimenziókra."""
    def calc(row):
        parts = []
        for cat, w in [(STAT, W_STAT), (GEN, W_GEN), (LING, W_LING)]:
            vals = [row[b] for b in cat
                    if b in row.index and not pd.isna(row[b])]
            if vals:
                parts.append((w, sum(vals) / len(vals)))
        if not parts:
            return float("nan")
        total_w = sum(w for w, _ in parts)
        return sum(w * v for w, v in parts) / total_w
    df["composite_score"] = df.apply(calc, axis=1)
    return df


def md_table(df: pd.DataFrame) -> str:
    cols = [c for c in df.columns
            if c not in ("composite_score", "partial_benchmarks")]
    lines = [
        "| Modell | " + " | ".join(cols) + " | Composite |",
        "|" + "---|" * (len(cols) + 2),
    ]
    for model, row in df.sort_values(
            "composite_score", ascending=False).iterrows():
        cells = [f"**{model}**"]
        for c in cols:
            v = row[c]
            cells.append("—" if pd.isna(v) else f"{v:.3f}")
        comp = row["composite_score"]
        cells.append("—" if pd.isna(comp) else f"**{comp:.3f}**")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def heatmap(df: pd.DataFrame, out: Path) -> None:
    df_s = df.sort_values("composite_score", ascending=False)
    cols = [c for c in df_s.columns
            if c not in ("composite_score", "partial_benchmarks")]
    m = df_s[cols].values
    fig, ax = plt.subplots(
        figsize=(max(8, len(cols) * 1.2), max(4, len(df_s) * 0.6))
    )
    im = ax.imshow(m, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right")
    ax.set_yticks(range(len(df_s)))
    ax.set_yticklabels(df_s.index)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if not np.isnan(m[i, j]):
                ax.text(
                    j, i, f"{m[i, j]:.2f}", ha="center", va="center",
                    color="black" if m[i, j] > 0.5 else "white",
                    fontsize=8,
                )
    plt.colorbar(im, ax=ax, label="Score (0-1)")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", type=Path, default=Path("./results"))
    p.add_argument("--out", type=Path, default=Path("./reports"))
    p.add_argument("--state-dir", type=Path, default=Path("./state"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    df = collect(args.results_dir, args.state_dir)
    if df.empty:
        print("❌ Nincs feldolgozható eredmény.")
        return 1
    df = composite(df)

    df.to_csv(args.out / "composite_scores.csv", float_format="%.4f")

    # Partial figyelmeztetés a riport tetején
    partial_warning = ""
    if "partial_benchmarks" in df.columns:
        partial_models = df[df["partial_benchmarks"].notna()]
        if not partial_models.empty:
            partial_warning = (
                "## ⚠️ Figyelem: részleges eredmények\n\n"
                "Az alábbi modellek futása megszakadt (rate limit, timeout, "
                "stb.), csak részleges JSONL áll rendelkezésre. A composite "
                "score ezeknél **alulbecsült** lehet:\n\n"
            )
            for m, r in partial_models.iterrows():
                partial_warning += (
                    f"- **{m}** — részleges: "
                    f"{r.get('partial_benchmarks', '?')}\n"
                )
            partial_warning += (
                "\nA teljes futtatáshoz használd a benchmark scriptek "
                "`--reset` nélküli újrafuttatását (automatikus resume).\n\n"
            )

    (args.out / "report.md").write_text(
        f"# Modell Értékelési Riport\n\n"
        f"*Generálva:* {datetime.now(timezone.utc).isoformat()}\n\n"
        f"{partial_warning}"
        f"## Composite Score (súlyok: stat={W_STAT}, gen={W_GEN}, "
        f"ling={W_LING})\n\n"
        f"{md_table(df)}\n\n## Heatmap\n\n"
        f"![Heatmap](results_heatmap.png)\n",
        encoding="utf-8",
    )
    heatmap(df, args.out / "results_heatmap.png")
    print(f"💾 Kész: {args.out}/ (CSV, MD, PNG)")
    print("\nCOMPOSITE RANGSOR:")
    for m, r in df.sort_values(
            "composite_score", ascending=False).iterrows():
        c = r["composite_score"]
        is_partial = (
            "partial_benchmarks" in df.columns
            and m in df.index
            and isinstance(r.get("partial_benchmarks"), str)
        )
        marker = " [RÉSZLEGES]" if is_partial else ""
        if pd.isna(c):
            print(f"  {m:30s}  N/A{marker}")
        else:
            print(f"  {m:30s}  {c:.3f}{marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
