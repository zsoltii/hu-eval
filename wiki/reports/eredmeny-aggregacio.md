# Eredmény Aggregáció és Vizualizáció

*Típus:* report
*Forrás(ok):* hu-eval projekt belső, [Overview](../overview.md), [Modell vs. Modell](../comparisons/modell-vs-modell.md)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Cél

Minden egyes benchmark-részfutás után keletkeznek részpontszámok (HuLU%, HuGME 1-5, UD F1, latency ms, USD/1M tok, stb.). Ezeket az eredményeket kell **egyetlen composite score-ba** aggregálni, és **vizuálisan** megjeleníteni, hogy a riport olvasója gyorsan átlássa a modellek erősségeit és gyengeségeit.

Ez az oldal:

1. Definiálja a **kompozit score képletét** (explicit, súlyokkal)
2. Pseudocode-ot ad a súlyozott aggregációra
3. Javaslatot tesz a **vizualizációs stratégiára** (heatmap, bar chart, radar chart)
4. Matplotlib kódrészleteket ad mindegyikhez
5. Meghatározza, **mikor kell frissíteni** a vizualizációkat

## Kompozit score képlete

### Bemeneti dimenziók (mind 0-100 skálán)

A [Modell vs. Modell](../comparisons/modell-vs-modell.md) oldalon definiált négy dimenzió:

| Dimenzió | Forrás | Súly | Megjegyzés |
|----------|--------|-----:|------------|
| `magyar_minoseg` | HuLU + MMLU-HU + HuGME + UD-HU aggregátum | **0.40** | A legfontosabb, nyelv-specifikus |
| `sebesseg` | Reciprok latency, normalizálva | **0.20** | TTFT és TPOT kombinációja |
| `koltseg` | Reciprok USD/1M token, normalizálva | **0.20** | Alacsonyabb költség → magasabb pont |
| `kontextus` | effektív kontextus hossz / 200k × 100 | **0.20** | 200k a teljes pontszám küszöb |

### A képlet (explicit)

```
composite(model) = 0.40 × magyar_minoseg(model)
                 + 0.20 × sebesseg(model)
                 + 0.20 × koltseg(model)
                 + 0.20 × kontextus(model)
```

A `magyar_minoség` belsőleg tovább bomlik:

```
magyar_minoseg = 0.50 × statisztikai
              + 0.30 × generativ
              + 0.20 × nyelveszeti

ahol:
  statisztikai = 0.5 × HuLU + 0.5 × MMLU_HU     (normalizálva 0-100)
  generativ    = HuGME_normalizalt               (1-5 → 0-100)
  nyelveszeti  = UD_HU_F1_atlag                  (0-100)
```

### Normalizálási szabályok

- **Idő-alapú metrikák** (TTFT, TPOT, latency): `pont = 100 / (1 + ertek_ms / 1000)` — 1 másodperc = 50 pont, 0 másodperc = 100 pont, 9 másodperc = 10 pont
- **Költség-alapú metrikák** (USD/1M tok): `pont = 100 / (1 + koltseg_usd × 0.5)` — 0 USD = 100 pont, 2 USD = 50 pont, 18 USD = 10 pont
- **Kontextus hossz**: `pont = min(100, effektív_kontextus / 2000)` — 200k token = 100 pont
- **Százalék-alapú metrikák** (HuLU%, MMLU-HU%, F1): lineárisan 0-100

## Súlyozott aggregáció pseudocode

```python
# hu-eval/aggregator.py (egyszerűsített vázlat)

@dataclass
class BenchmarkResult:
    model: str
    hulu_pct: float          # 0-100
    mmlu_hu_pct: float       # 0-100
    hugme_avg: float         # 1-5
    ud_hu_f1: float          # 0-100
    ttft_ms: float
    tpot_ms: float
    cost_usd_per_1m: float
    eff_kontextus: int


def normalize(r):
    stat = 0.5 * r.hulu_pct + 0.5 * r.mmlu_hu_pct
    gen = (r.hugme_avg - 1) / 4 * 100       # 1-5 → 0-100
    nyelv = r.ud_hu_f1
    magyar = 0.50 * stat + 0.30 * gen + 0.20 * nyelv

    seb_ttft = 100 / (1 + r.ttft_ms / 1000)
    seb_tpot = 100 / (1 + r.tpot_ms / 200)
    seb = 0.5 * seb_ttft + 0.5 * seb_tpot

    kolt = 100 / (1 + r.cost_usd_per_1m * 0.5)
    kontext = min(100, r.eff_kontextus / 2000)   # 200k = 100 pont

    return {"magyar_minoseg": magyar, "sebesseg": seb,
            "koltseg": kolt, "kontextus": kontext}


def composite(n):
    return 0.40*n["magyar_minoseg"] + 0.20*n["sebesseg"] + 0.20*n["koltseg"] + 0.20*n["kontextus"]


def aggregate_all(results):
    out = []
    for r in results:
        n = normalize(r)
        out.append({"model": r.model, "composite": round(composite(n), 2), **n})
    return sorted(out, key=lambda x: x["composite"], reverse=True)
```

## Vizualizációs stratégia

Három fő vizualizáció-típust használunk, mindegyik más kérdésre ad választ:

### 1. Heatmap — modell × dimenzió mátrix

**Kérdés, amire válaszol:** "Melyik modell melyik dimenzióban erős/gyenge?"

- Sorok: modellek
- Oszlopok: dimenziók (magyar minőség, sebesség, költség, kontextus)
- Cella: 0-100 pontszám, színskála (pl. `viridis` vagy `RdYlGn`)
- Előny: azonnal látható, hogy melyik cella "világít" (erős) vagy "sötét" (gyenge)

### 2. Bar chart — composite score rangsor

**Kérdés, amire válaszol:** "Melyik modell a legjobb összességében?"

- Egy vízszintes sáv modellenként
- Hossz = composite score
- Szín: kategóriától függően (cloud = kék, lokális = zöld)
- Előny: egyszerű, gyorsan olvasható

### 3. Radar chart — modell "ujjlenyomat"

**Kérdés, amire válaszol:** "Milyen a modell profilja — kiegyensúlyozott vagy specialista?"

- 4 tengely: magyar minőség, sebesség, költség, kontextus
- Minden modell egy saját színű sokszög
- Átlapolt ábránál max 4-5 modell, különben áttekinthetetlen
- Előny: profilok összehasonlítása, trade-off-ok vizualizálása

## Matplotlib kódrészletek

### Heatmap

```python
import matplotlib.pyplot as plt
import seaborn as sns

def plot_heatmap(models, dim_scores, dim_names):
    fig, ax = plt.subplots(figsize=(8, max(3, 0.5 * len(models))))
    sns.heatmap(
        dim_scores, annot=True, fmt=".1f", cmap="RdYlGn", vmin=0, vmax=100,
        xticklabels=dim_names, yticklabels=models,
        cbar_kws={"label": "Pontszám (0-100)"}, ax=ax,
    )
    ax.set_title("Modell × Dimenzió Heatmap")
    plt.tight_layout()
    plt.savefig("hu-eval-results_heatmap.png (mentendő a reports/ mappába)", dpi=150, bbox_inches="tight")
    plt.close()
```

### Bar chart (composite score)

```python
def plot_composite_bar(models, composites, categories):
    color_map = {"cloud": "#3b82f6", "local": "#10b981", "flash": "#f59e0b"}
    colors = [color_map.get(c, "#6b7280") for c in categories]
    order = np.argsort(composites)[::-1]
    fig, ax = plt.subplots(figsize=(8, max(3, 0.5 * len(models))))
    bars = ax.barh([models[i] for i in order], [composites[i] for i in order],
                   color=[colors[i] for i in order])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Composite score (0-100)")
    ax.set_title("Modell rangsor")
    for bar, val in zip(bars, [composites[i] for i in order]):
        ax.text(val + 1, bar.get_y() + bar.get_height() / 2, f"{val:.1f}", va="center")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig("hu-eval-composite.png", dpi=150, bbox_inches="tight")
    plt.close()
```

### Radar chart

```python
def plot_radar(models, dim_scores, dim_names):
    n = len(dim_names)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    cmap = plt.get_cmap("tab10")
    for i, m in enumerate(models):
        vals = dim_scores[i].tolist() + [dim_scores[i][0]]
        ax.plot(angles, vals, color=cmap(i), linewidth=2, label=m)
        ax.fill(angles, vals, color=cmap(i), alpha=0.10)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(dim_names)
    ax.set_ylim(0, 100); ax.set_title("Modell profilok — radar chart")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0), fontsize=9)
    plt.tight_layout()
    plt.savefig("hu-eval-radar.png", dpi=150, bbox_inches="tight")
    plt.close()
```

## Ajánlott megjelenítési sorrend a riportban

A riport olvasója számára az alábbi sorrendben érdemes prezentálni:

1. **Composite bar chart** — azonnal látható a győztes
2. **Heatmap** — részletes bontás dimenziónként
3. **Radar chart** — profilok összehasonlítása (opcionális, max 4-5 modellnél)
4. **Per-benchmark táblázatok** — a heatmap "alatti" nyers számok

## Mikor frissítsük a vizualizációkat?

| Esemény | Melyik vizualizációt frissítsük? |
|---------|----------------------------------|
| Új modell benchmark eredménye érkezett | Composite bar + heatmap (1 modellel bővül) |
| Új benchmark típust vettünk fel (pl. ARC-HU) | Heatmap bővül + per-benchmark táblázat |
| Súlyokat módosítottunk | Mindhárom újraszámítandó |
| Riportot véglegesítünk | Végső snapshot, magasabb DPI (300) |
| Negyedéves összesítés | Összes modell, összes vizualizáció |

### Frissítési gyakoriság

- **Fejlesztés közben** — napi draft verzió
- **Egy modell teljes kiértékelése után** — azonnali frissítés
- **Havonta** — teljes rangsor, riport publikálás

## Edge case-ek

- **Hiányzó benchmark eredmény** — dimenzió legyen `NaN`; a composite score számításnál a súlyokat újra normalizáljuk a maradó dimenziókra; heatmap-en szürke cella.
- **Outlierek** — ha a composite > 1.5 IQR-rel tér el a mediántól, külön jelölés; box plot a dimenziónkénti eloszlásról.
- **Benchmark definíció változás** — régi és új eredmények külön oszlopban; heatmap-en `v1`/`v2` suffix; jelöljük, melyik verzióból készült a composite.
- **Összehasonlíthatatlan modellek** — pl. cloud és lokális nem minden dimenzióban hasonlítható (költségszerkezet más); külön csoportként jelöljük a heatmap-en.

## Kimeneti formátum

Minden riport a `reports/YYYY-MM-DD-<leiras>/` alkönyvtárba kerül: `report.md` (fő riport), `hu-eval-results_heatmap.png (mentendő a reports/ mappába)`, `hu-eval-composite.png`, `hu-eval-radar.png` (300 dpi), `data.json` (nyers aggregátum), és `per-benchmark/` (részletes riportok benchmarkonként).

## Kapcsolódó

- [Riport Sablon](riport-template.md) — hogyan használd ezt az aggregációt egy riportban
- [Modell vs. Modell](../comparisons/modell-vs-modell.md) — dimenzió-definíciók
- [Benchmark vs. Benchmark](../comparisons/benchmark-vs-benchmark.md) — mit mérnek a benchmarkok
- [Cloud vs. Lokális](../comparisons/cloud-vs-lokal.md) — üzemeltetési kontextus
- [Overview](../overview.md) — fő keretrendszer
- [SCHEMA](../SCHEMA.md) — formátum
