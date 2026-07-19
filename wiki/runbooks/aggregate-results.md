# Eredmények aggregációja és riport generálás — checkpoint-aware

*Típus:* runbook
*Forrás(ok):* [pandas docs](https://pandas.pydata.org/docs/), [matplotlib docs](https://matplotlib.org/stable/contents.html), [Project overview](../overview.md), [Checkpoint pattern](../concepts/checkpoint-progress.md)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15

---

> **v1.1 (2026-07-15) változtatások:**
> - **Bíró modell**: `deepseek-v4-pro:cloud` (hivatalos bíró 2026-07-19 óta) — a `gemini-3-flash-preview:latest` 2026-07-14. 09:00 CEST óta nem elérhető. A HuGME és MT-Bench-HU eredményeket ezzel a bíróval kell újrapontoszni. **Self-bias korlát (SZENT):** a bíró modell nem értékelheti saját magát.
> - **A `results/` mappából most 5 benchmark** fut ténylegesen (korábban 9 volt tervben): HuLU, MMLU-HU, HuGME, MT-Bench-HU, UD Hungarian. A többi (arc_hu, gsm8k_hu, morphology, perplexity) jövőbeli.
> - **MT-Bench-HU multi-baseline**: 3 baseline (deepseek-v4-flash/pro, kimi-k2.6) GSB átlaga. Eredmény: 50% (W0/L0/T24) minden modellnél — a baseline-ok túl hasonlóak.
> - **UD Hungarian refuttatás**: 2026-07-13/14, 13 modell CoT-aware parser-rel. A think modellek jellemzően CoT-t írnak CoNLL-U helyett, így a parser csak a válasz végén keres → 0-7.5% score.
> - **Két heatmap** ajánlott: statisztikai (HuLU + MMLU-HU) + generatív/nyelvészeti (HuGME + MT-Bench-HU + UD).
> - **Conda env**: `eval-hu` (Python 3.11) — **nem** `hu-eval` (az AGENTS.md és a valós környezet szerint).

## Cél

Az összes benchmark eredmény (`results/{model}/*.json` és `*.jsonl`) összefésülése egyetlen pandas DataFrame-be, **composite score** számítása (**40% statisztikai + 40% generatív + 20% nyelvészeti** — az AGENTS.md által kötelezően előírt séma), és Markdown riport + matplotlib heatmap-ek generálása a `wiki/reports/` mappába.

> **⚠️ Checkpoint-kompatibilis:** Az aggregátor **részleges JSONL-eket is kezel** — ha egy futás a 1247. itemnél állt le (pl. rate limit miatt), a kész 1247 sorból is tud részstatisztikát számolni, és a riportban `partial: true` jelöléssel látja el. A state fájl `num_completed` mezője számít a `total` helyett.

## Bemeneti struktura

A projekt az alábbi mappastruktúrát használja (a benchmark scriptek ezt írják):

```
results/
├── deepseek-v4-flash-cloud-nothink/
│   ├── hulu_summary.json          # {"accuracy": 0.733, "num_examples": 2581}
│   ├── hulu_results.jsonl         # nyers válaszok (id, prompt, response, correct)
│   ├── mmlu_hu_summary.json       # {"accuracy": 0.520, "num_examples": 1500}
│   ├── hugme_summary.json         # {"score": 0.0954, "num_judged": 295}
│   ├── mt_bench_hu_summary.json   # {"score": 0.50, "wins": 0, "losses": 0, "ties": 1}
│   └── ud_hungarian_summary.json  # {"accuracy": 0.699, "upos_accuracy": 0.897, "uas": 0.470, "las": 0.730}
├── deepseek-v4-flash-cloud-think/
│   └── ... ugyanaz a struktúra
├── qwen3-next-80b-cloud-nothink/  # RETIRED 2026-06-16
│   ├── hulu_summary.json          # {"accuracy": 0.615}
│   └── (a többi benchmark state.json "failed_stopped", summary nincs)
```

Minden `*_summary.json` legalább egy `accuracy` (0-1) vagy `score` (0-1) mezőt tartalmaz. A judge-olt fájlokban (HuGME) a `num_judged` mező jelzi, hány itemet bírált el a `deepseek-v4-pro:cloud` (jelenlegi hivatalos bíró, 2026-07-19 óta; korábban `gemini-3-flash-preview`, megszűnt 2026-07-14). A `mt_bench_hu` summary `wins/losses/ties` mezőket is tartalmazza a multi-baseline GSB-hez.

## Előfeltételek

- Az `eval-hu` conda env aktív ([beállítás](setup-kornyezet.md)) — **Python 3.11**, **nem** `hu-eval`!
- Ollama szerver fut (`http://localhost:11434`) — csak a futtatáshoz kell, az aggregátor nem hív Ollama-t
- Legalább 2 modell eredményei a `results/` mappában
- `pandas`, `matplotlib`, `numpy` telepítve (env része)

## Lépések

### 1. Az aggregátor script (v1.1 — 5 benchmark, 2026-07-15)

```python
#!/usr/bin/env python
# aggregate_results.py — Eredmények aggregációja + composite score + riport
# Használat: python aggregate_results.py --results-dir ./results --out ./reports

import argparse, json
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Súlyok (az AGENTS.md szerint KÖTELEZŐ, nem változtatható)
W_STAT, W_GEN, W_LING = 0.40, 0.40, 0.20

# Aktuális benchmark listák (2026-07-15: 5 implementált, 4 jövőbeli)
STAT = ["hulu", "mmlu_hu"]                        # arc_hu, gsm8k_hu jövőbeli
GEN = ["hugme", "mt_bench_hu"]                    # mindkét implementált
LING = ["ud_hungarian"]                            # morphology, perplexity jövőbeli

# MT-Bench-HU multi-baseline (3 baseline GSB átlaga)
MT_BENCH_BASELINES = [
    "deepseek-v4-flash:cloud",
    "deepseek-v4-pro:cloud",
    "kimi-k2.6:cloud",
]

# RETIRED modellek (külön kezelendők — composite nem számítható)
RETIRED_MODELS = ["qwen3-next-80b-cloud"]


def extract_score(summary: dict, benchmark: str) -> float | None:
    """0-1 közé normalizált score kinyerése summary dict-ből."""
    if "accuracy" in summary: return float(summary["accuracy"])
    if "score" in summary: return float(summary["score"])
    if benchmark == "perplexity":
        return max(0.0, 1.0 - min(summary.get("perplexity", 100), 100) / 100)
    if benchmark == "ud_hungarian":
        # Composite = avg(upos, uas, las)
        u = summary.get("upos_accuracy", 0)
        a = summary.get("uas", 0)
        l = summary.get("las", 0)
        return (u + a + l) / 3
    if isinstance(summary.get("judge"), dict) and "overall" in summary["judge"]:
        return summary["judge"]["overall"] / 10.0
    return None


def judge_avg(path: Path) -> float | None:
    """Judge-olt JSONL-ből átlagos overall score 0-1 skálán."""
    if not path.exists(): return None
    scores = []
    for line in path.open(encoding="utf-8"):
        j = json.loads(line).get("judge", {})
        if isinstance(j, dict) and isinstance(j.get("overall"), (int, float)):
            scores.append(j["overall"] / 10.0)
    return sum(scores) / len(scores) if scores else None


def collect(results_dir: Path, state_dir: Path) -> pd.DataFrame:
    """results/{model}-{mode}/ mappák bejárása, DataFrame építés.
    Részleges JSONL-eket is elfogad (num_completed a state-ből jön)."""
    rows = []
    for model_dir in sorted(results_dir.iterdir()):
        if not model_dir.is_dir(): continue
        # model_dir.name formátum: "<model>-<mode>", pl. "deepseek-v4-flash-cloud-nothink"
        parts = model_dir.name.rsplit("-", 1)
        if len(parts) != 2: continue
        model, mode = parts
        is_retired = any(m in model for m in RETIRED_MODELS)

        row = {"model": model, "mode": mode, "is_retired": is_retired}
        partial_flags = []

        # Summary JSON fájlok
        for sp in model_dir.glob("*_summary.json"):
            try: data = json.loads(sp.read_text(encoding="utf-8"))
            except Exception: continue
            bench = sp.stem.replace("_summary", "")
            score = extract_score(data, bench)
            if score is not None: row[bench] = score
            if data.get("partial"): partial_flags.append(bench)

        # Judge-olt JSONL fájlok (HuGME)
        for jp in model_dir.glob("*_judged.jsonl"):
            s = judge_avg(jp)
            if s is not None: row[jp.stem.replace("_judged", "")] = s
            state_path = state_dir / model_dir.name / jp.stem.replace("_judged", ".json")
            if state_path.exists():
                try:
                    st = json.loads(state_path.read_text(encoding="utf-8"))
                    if st.get("status") == "failed_stopped":
                        partial_flags.append(jp.stem.replace("_judged", ""))
                except Exception: pass

        if partial_flags:
            row["partial_benchmarks"] = ",".join(partial_flags)
        rows.append(row)
    return pd.DataFrame(rows).set_index(["model", "mode"])


def composite(df: pd.DataFrame) -> pd.DataFrame:
    """Composite score: 40/40/20 súlyozás, súlyarányos újraosztás hiányzó dimenziókra.
    RETIRED modellek esetén composite_score = NaN."""
    def calc(row):
        if row.get("is_retired", False): return float("nan")
        parts = []
        for cat, w in [(STAT, W_STAT), (GEN, W_GEN), (LING, W_LING)]:
            vals = [row[b] for b in cat if b in row.index and not pd.isna(row[b])]
            if vals: parts.append((w, sum(vals) / len(vals)))
        if not parts: return float("nan")
        total_w = sum(w for w, _ in parts)
        return sum(w * v for w, v in parts) / total_w
    df["composite_score"] = df.apply(calc, axis=1)
    return df


def md_table(df: pd.DataFrame) -> str:
    cols = [c for c in df.columns if c not in ("composite_score", "is_retired", "partial_benchmarks")]
    lines = ["| Modell | Mód | " + " | ".join(cols) + " | Composite |",
             "|" + "---|" * (len(cols) + 3)]
    df_sorted = df.sort_values("composite_score", ascending=False, na_position="last")
    for (model, mode), row in df_sorted.iterrows():
        cells = [f"**{model}**", mode]
        for c in cols:
            v = row[c]; cells.append("—" if pd.isna(v) else f"{v:.3f}")
        comp = row["composite_score"]
        cells.append("**RETIRED**" if row.get("is_retired", False)
                     else ("—" if pd.isna(comp) else f"**{comp:.3f}**"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def heatmap(df: pd.DataFrame, benches: list, out: Path, title: str):
    """Heatmap generálás a megadott benchmarkokra. vmin=0, vmax=1, RdYlGn."""
    df_s = df.sort_values("composite_score", ascending=False, na_position="last")
    # RETIRED sorok megtartása (üres cellákkal), de a composite_sort végére kerülnek
    m = df_s[benches].values
    fig, ax = plt.subplots(figsize=(max(8, len(benches) * 1.8), max(6, len(df_s) * 0.5)))
    im = ax.imshow(m, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m[i, j]
            if np.isnan(v):
                ax.text(j, i, "—", ha="center", va="center", color="gray", fontsize=9)
            else:
                color = "black" if 0.3 < v < 0.7 else "white"
                ax.text(j, i, f"{v*100:.1f}%", ha="center", va="center", color=color, fontsize=8)
    labels = [f"{m} ({mo})" for m, mo in df_s.index]
    ax.set_xticks(range(len(benches))); ax.set_xticklabels(benches, rotation=0, ha="center")
    ax.set_yticks(range(len(df_s))); ax.set_yticklabels(labels, fontsize=8)
    ax.set_title(title, fontsize=11, pad=10)
    plt.colorbar(im, ax=ax, label="Score (0-1)")
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight"); plt.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", type=Path, default=Path("./results"))
    p.add_argument("--out", type=Path, default=Path("./reports"))
    p.add_argument("--state-dir", type=Path, default=Path("./state"))
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="Riport dátum (fájlnévhez)")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    df = collect(args.results_dir, args.state_dir)
    if df.empty: print("❌ Nincs feldolgozható eredmény."); return 1
    df = composite(df)

    # CSV export
    df.to_csv(args.out / f"composite_scores-{args.date}.csv", float_format="%.4f")

    # Heatmap-ek (két darab — stat + gen/ling elkülönítve a jobb olvashatóságért)
    heatmap(df, ["hulu", "mmlu_hu"], args.out / f"results_heatmap_stat-{args.date}.png",
            f"Statisztikai benchmarkok — {args.date}")
    heatmap(df, ["hugme", "mt_bench_hu", "ud_hungarian"],
            args.out / f"results_heatmap_genling-{args.date}.png",
            f"Generatív + nyelvészeti benchmarkok — {args.date}")

    # Partial figyelmeztetés
    partial_warning = ""
    if "partial_benchmarks" in df.columns:
        partial_models = df[df["partial_benchmarks"].notna()]
        if not partial_models.empty:
            partial_warning = (
                "## ⚠️ Figyelem: részleges eredmények\n\n"
                "Az alábbi modellek futása megszakadt (rate limit, timeout, stb.), "
                "csak részleges JSONL áll rendelkezésre:\n\n"
            )
            for (m, mo), r in partial_models.iterrows():
                partial_warning += f"- **{m} ({mo})** — részleges: {r['partial_benchmarks']}\n"
            partial_warning += "\n"

    # Riport (markdown)
    retired_note = (
        "> **Megjegyzés:** A `qwen3-next-80b-cloud` modell 2026-06-16 óta RETIRED "
        "(HTTP 410). Csak HuLU készült el, composite_score nem számítható. "
        "A riportban **RETIRED** jelöléssel szerepel.\n\n"
    )

    (args.out / f"report-{args.date}.md").write_text(
        f"# Modell Értékelési Riport — {args.date}\n\n"
        f"*Generálva:* {datetime.now(timezone.utc).isoformat()}\n\n"
        f"{retired_note}"
        f"{partial_warning}"
        f"## Composite Score (súlyok: stat={W_STAT}, gen={W_GEN}, ling={W_LING}, AGENTS.md kötelező)\n\n"
        f"{md_table(df)}\n\n"
        f"## Heatmap-ek\n\n"
        f"### Statisztikai benchmarkok\n\n"
        f"![Stat](reports/results_heatmap_stat-{args.date}.png)\n\n"
        f"### Generatív + nyelvészeti benchmarkok\n\n"
        f"![Gen/Ling](reports/results_heatmap_genling-{args.date}.png)\n\n",
        encoding="utf-8")
    print(f"💾 Kész: {args.out}/ (CSV, MD, 2× PNG)")
    print("\nCOMPOSITE RANGSOR (40/40/20, legjobb → legrosszabb):")
    for (m, mo), r in df.sort_values("composite_score", ascending=False, na_position="last").iterrows():
        c = r["composite_score"]
        marker = " [RÉSZLEGES]" if r.get("partial_benchmarks") else ""
        if r.get("is_retired", False):
            print(f"  {m:30s} ({mo:8s})  RETIRED{marker}")
        elif pd.isna(c):
            print(f"  {m:30s} ({mo:8s})  N/A{marker}")
        else:
            print(f"  {m:30s} ({mo:8s})  {c:.3f}{marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 2. Futtatás

```bash
source "$HOME/anaconda3/etc/profile.d/conda.sh"
conda activate eval-hu
cd .

# Alapértelmezett: ./results → ./reports
python aggregate_results.py

# Egyedi dátummal (ajánlott a verziózáshoz)
python aggregate_results.py --date 2026-07-14

# Egyedi mappákkal
python aggregate_results.py --results-dir ./results --out ./reports/2026-07-14
```

### 3. Elvárt kimenet

A `reports/` mappa létrejön:

```
reports/
├── composite_scores-YYYY-MM-DD.csv   # nyers DataFrame CSV-ben (22 sor × 13 oszlop)
├── results_heatmap_stat-YYYY-MM-DD.png           # HuLU + MMLU-HU heatmap
├── results_heatmap_genling-YYYY-MM-DD.png        # HuGME + MT-Bench-HU + UD heatmap
└── report-YYYY-MM-DD.md              # markdown riport táblákkal + 2 képpel
```

Konzol kimenet (példa a 2026-07-14-es futásból):

```
🔍 Eredmények beolvasása: ./results
💾 CSV: reports/composite_scores-2026-07-14.csv
🎨 Heatmap-ek generálása...
  📊 reports/results_heatmap_stat-2026-07-14.png
  📊 reports/results_heatmap_genling-2026-07-14.png
📝 Markdown riport generálás...
💾 Markdown: reports/report-2026-07-14.md

================================================================================
COMPOSITE RANGSOR (40/40/20, legjobb → legrosszabb)
================================================================================
  deepseek-v4-pro-cloud          nothink   0.543
  kimi-k2.6-cloud                nothink   0.542
  glm-5.2-cloud                  nothink   0.521
  qwen3.5-cloud                  nothink   0.515
  deepseek-v4-flash-cloud        nothink   0.510
  ...
  qwen3-next-80b-cloud           nothink   RETIRED
  qwen3-next-80b-cloud           think     RETIRED
================================================================================
```

A `report.md` tartalma:

- Fejléc (riport azonosító, dátum, modellek)
- Executive Summary (top modell, fő tradeoff, ajánlás)
- Főbb számok (legjobb HuLU/MMLU-HU/HuGME/UD/Composite)
- Per-benchmark táblázatok (5 db: HuLU, MMLU-HU, HuGME, MT-Bench-HU, UD Hungarian)
- Kompozit score táblázat A (40/40/20 súlyozott, 22 sor)
- Kompozit score táblázat B (4 fő benchmark egyszerű átlaga, 22 sor)
- Dimenziónkénti győztesek
- Heatmap-ek (2 db: stat + gen/ling)
- Meglepetések / anomáliák / korrelációk / limitációk
- Következő lépések
- Függelék (nyers adatok helye, reprodukálhatóság, verzió)
- Változtatási napló

### 4. Heatmap értelmezés

A két heatmap RdYlGn színskálát használ (vmin=0, vmax=1):

- 🟢 **Zöld** (0.7-1.0): kiemelkedő teljesítmény
- 🟡 **Sárga** (0.4-0.7): átlagos
- 🔴 **Piros** (0.0-0.4): gyenge

**Statisztikai heatmap** (`results_heatmap_stat-*.png`):
- HuLU (71-78% tartomány) és MMLU-HU (46-93% tartomány)
- A gpt-oss:20b MMLU-HU 46% kiemelkedően sárga — outlier a többiekhez képest

**Generatív + nyelvészeti heatmap** (`results_heatmap_genling-*.png`):
- HuGME (8-10% — mind piros, mert a bíró score 0-1 skálán van, és a magyar open-ended QA nehéz)
- MT-Bench-HU (50% mindenkinél — sárga, mert multi-baseline averaging → döntetlen)
- UD Hungarian (0-70% — széles tartomány: nothink modellek zöldek, think modellek pirosak a CoT-zavar miatt)

Minden cellában a `%` érték is látható. A sorok composite score szerint vannak rendezve (RETIRED modellek a végén "—" cellákkal).

## Gyakori buktatók

| Tünet | Ok | Megoldás |
|-------|-----|----------|
| `composite_score` oszlop tele `NaN`-nal | Summary JSON-ból hiányzik az `accuracy`/`score` mező | `cat results/X/hulu_summary.json` — told a `extract_score` függvényt, ha más a mező neve |
| `perplexity` hiányzik a composite-ból | A `perplexity_summary.json` más struktúrát használ | Ellenőrizd: `{"perplexity": 12.3, "bits_per_char": 1.2}` kell legyen |
| **MT-Bench-HU mind 50%** | A 3 baseline (deepseek-v4-flash/pro, kimi-k2.6) GSB átlaga — mindenki döntetlent játszik | Változatosabb baseline-ok (lokális 7B modell) — jövőbeli feladat |
| **UD think 0.0% mindenkinél** | A think modellek CoT-t írnak CoNLL-U helyett, a parser a végén keres | UD think parser javítás: teljes szövegben keresés a CoT-strip után — jövőbeli feladat |
| Heatmap torz / összenyomott | Rossz `figsize` | `figsize=(max(10, len(cols)*1.5), max(5, len(df_sorted)*0.8))` |
| `Invalid DISPLAY variable` (Linux szerver) | Matplotlib X szervert keres | A script elején `matplotlib.use("Agg")` — benne van |
| Composite 1 soros, nem informatív | Csak 1 modell van | Futtass még 1-2 modellt ([Runbook: HuLU](run-hulu-modell-x.md)) |
| **qwen3-next:80b composite 60% felett** | Csak HuLU van neki (0.615 / 0.632), a többi RETIRED → a képlet újraosztja a súlyokat | A RETIRED modellek `composite_score` mezőjét `NaN`-ra kell állítani (a script v1.1-ben benne van) |
| **gemini-3-flash-preview bíró nem elérhető** | A bíró modell 2026-07-14. 09:00 CEST óta megszűnt | Új bíró modell: `deepseek-v4-pro:cloud` (2026-07-19 óta hivatalos bíró) — a HuGME és MT-Bench-HU rejudge szükséges; self-bias miatt a deepseek saját sorait független bíróval kell pontozni |
| **gpt-oss:20b HuGME 138 ó outlier** | Cloud rate limit, a JSONL csak 117 itemet tartalmaz | A `num_judged` mezőt ellenőrizd a summary-ban; ha <300, akkor a score alulbecsült lehet |

## Haladó tippek

- **Bootstrap CI** — ha két modell score-ja közel van (pl. 0.543 vs 0.542): bootstrap 1000 iteráció, 95% CI a `composite_score`-ra. A `scripts/aggregate_results.py` v1.1-ben még nincs benne, de a `pandas`/`numpy` könnyen hozzáadható.
- **Súlyok változtatása** — **NE TEDD**. A `W_STAT`, `W_GEN`, `W_LING` konstansok a script tetején az [AGENTS.md](../AGENTS.md) által kötelezően előírt értékek (40% stat + 40% gen + 20% ling). Ha módosítod, a riportok nem lesznek összehasonlíthatóak.
- **Hiányzó dimenziók** — a `composite()` függvény a rendelkezésre álló dimenziókra súlyarányosan újraoszt. Ha egy modellből teljes dimenzió hiányzik, a composite a maradékkal számol. **Kivétel: RETIRED modellek** — ezek composite_score = NaN, mert a HuLU önmagában nem reprezentatív.
- **Részleges futások** — ha egy modell futása checkpoint miatt megszakadt, a riport tetején `⚠️ Részleges eredmények` figyelmeztetés jelenik meg, és a composite score `[RÉSZLEGES]` jelölést kap. A folytatáshoz használd a benchmark script `--resume` (vagy sima újrafuttatás) kapcsolóját.
- **Két heatmap** — a stat és gen/ling szétválasztás azért hasznos, mert a HuGME (8-10%) és MT-Bench (50%) más skálán mozognak, mint a statisztikai benchmarkok (46-93%). Egy heatmap-en a stat dominálna, a generatív részletek elvesznének.
- **Új bíró modell** — ha a `gemini-3-flash-preview` helyett `deepseek-v4-pro:cloud`-t vagy más bíró modellt használsz, a `scripts/judge_hugme.py:23` és `scripts/judge_mt_bench.py:23` `JUDGE_MODEL` konstansát kell frissíteni, majd újrafuttatni a `rejudge_hugme.py` és `rejudge_mt_bench.py` scripteket. **Figyelem:** a self-bias elv miatt a bíró modell saját HuGME/MT-Bench sorait nem szabad saját magával pontozni.

## Ellenőrző lista

- [ ] Az `eval-hu` conda env aktív (Python 3.11, **nem** `hu-eval`)
- [ ] A `results/` mappában van legalább 2 modell mappája
- [ ] Minden modell mappa tartalmaz legalább 1 `*_summary.json` fájlt
- [ ] A `composite_scores-YYYY-MM-DD.csv` megnyitható Excelben / pandas-szal
- [ ] A `results_heatmap_stat-YYYY-MM-DD.png` és `results_heatmap_genling-YYYY-MM-DD.png` létrejött és megnyitható
- [ ] A `report-YYYY-MM-DD.md` tartalmazza a táblákat és a 2 heatmap linkjét
- [ ] A composite score 0 és 1 között van minden aktív modellnél
- [ ] A RETIRED modellek (pl. `qwen3-next-80b-cloud`) a composite tábla végén, **RETIRED** jelöléssel szerepelnek
- [ ] Ha bármelyik futás `failed_stopped`, a riport tetején `⚠️ Részleges eredmények` figyelmeztetés megjelenik

## Kapcsolódó

- [Runbook: Környezet](setup-kornyezet.md) — conda env, függőségek telepítése
- [Runbook: HuLU](run-hulu-modell-x.md) — statisztikai benchmark (egyik forrás)
- [Runbook: LLM Judge](llm-judge-prompt-template.md) — judge-olt fájlok forrása
- [Runbook: Debug](debug-modell-nem-valaszol.md) — ha egy modell eredménye hiányzik
- [Concept: Checkpoint](../concepts/checkpoint-progress.md) — stop-on-error + resume tervezési elv
- [Overview](../overview.md) — a 40/40/20 súlyozás eredete
- [Riport sablon](../reports/riport-template.md) — a riport formátumdefiníciója
- [Végleges riport (2026-07-14)](../reports/report-2026-07-14.md) — a script aktuális kimenete
- [AGENTS.md](../../AGENTS.md) — a 40/40/20 súlyozás szabálya (kötelező, nem változtatható)
- [SCHEMA](../SCHEMA.md) — wiki formátum szabályok
