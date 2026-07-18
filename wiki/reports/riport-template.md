# Riport Sablon — Magyar LLM Értékelés

*Típus:* report
*Forrás(ok):* hu-eval projekt belső, [Overview](../overview.md), [Riport Aggregáció](../runbooks/aggregate-results.md)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15

---

> Ez egy **sablon**. Minden új riport a másolatából készül, és a `placeholder` szakaszok helyére kerülnek a tényleges adatok.
>
> **v1.1 (2026-07-15) változtatások:**
> - Sebesség, költség, kontextus mezők törölve (a projekt nem méri ezeket — minden modell cloud)
> - Kompozit score képlet fixálva: **40% stat + 40% gen + 20% ling** (AGENTS.md kötelező)
> - Két kompozit tábla: (A) 40/40/20 súlyozott, (B) 4 fő benchmark egyszerű átlaga (kiegészítő)
> - UD szekció átnevezve (UPOS/UAS/LAS, nem POS/Dep/Lemma F1)
> - MT-Bench-HU szekció hozzáadva (W/L/T + multi-baseline)
> - 95% CI és "Bíró megbízhatóság másik bíróval" törölve (nincs bootstrap, nincs második bíró)
> - Két heatmap szekció (stat + gen/ling) hozzáadva
> - HuLU dedup, MMLU parser javítás, UD refuttatás, bíró modell megszűnés lábjegyzet

## Fejléc

| Mező | Érték |
|------|-------|
| Riport azonosító | `hu-eval-YYYYMMDD-<modell-száma>` |
| Riport dátum | YYYY-MM-DD |
| Értékelt modellek | `modell1:verzió`, `modell2:verzió`, ... |
| Operator | `openclaw` |
| Riport státusz | `draft` / `final` |

> **Bíró modell** (LLM-as-a-Judge): `gemini-3-flash-preview:latest` — 2026-07-14. 09:00 CEST óta nem elérhető (Ollama megszűnés). A reprodukálhatósághoz új bíró modell (pl. `gemini-3-pro-preview`) szükséges. A bíró modell részletes adatai a [Függelék — Verzióinformáció](#verzióinformáció) szekcióban.

### Időkeret

- **Mérés indítása:** YYYY-MM-DD HH:MM
- **Mérés befejezése:** YYYY-MM-DD HH:MM
- **Teljes futásidő:** X óra Y perc (processzoridő, a párhuzamos futás miatt a valós idő rövidebb)

## Executive Summary

_3-5 mondat, ami a legfontosabb megállapításokat összegzi. Kérdések, amikre válaszol:_

- Melyik modell teljesített a legjobban a magyar nyelvű benchmarkokon?
- Milyen kompromisszumok figyelhetők meg (minőség vs. pontosság az egyes benchmark-típusok között)?
- Vannak-e meglepő eredmények vagy anomáliák?
- Milyen konkrét ajánlás fogalmazható meg a felhasználók számára?

### Főbb számok egy sorban

- **Legjobb composite score (40/40/20):** `<modell>` — `<pontszám>`/100
- **Legjobb HuLU:** `<modell>` — `<pontszám>`%
- **Legjobb MMLU-HU:** `<modell>` — `<pontszám>`%
- **Legjobb HuGME (judge score):** `<modell>` — `<pontszám>`%
- **Legjobb UD Hungarian:** `<modell>` — `<pontszám>`% (composite)
- **Legnagyobb meglepetés:** `<rövid leírás>`

## Per-benchmark eredmények

### HuLU eredmények (statisztikai — 6 NLU sub-task)

| Modell | Mód | Pontosság (%) | Megjegyzés |
|--------|-----|---------------:|------------|
| `<modell1>` | nothink | _._% | _opcionális_ |
| `<modell1>` | think | _._% | — |
| `<modell2>` | nothink | _._% | — |
| `<modell2>` | think | _._% | — |

**Legjobb:** `<modell>` — Rövid indoklás.

**Érdekes megfigyelések:**

- _pl. A kisebb modell meglepően jól teljesített egyszerű kérdéseken_
- _pl. A cloud flash modell a nehéz kérdéseken a flagship szintjén teljesített_

### MMLU-HU eredmények (statisztikai — 38 tantárgy, 5 kevés lövés)

| Modell | Mód | Pontosság (%) | Megjegyzés |
|--------|-----|---------------:|------------|
| `<modell1>` | nothink | _._% | — |
| `<modell1>` | think | _._% | — |
| `<modell2>` | nothink | _._% | — |
| `<modell2>` | think | _._% | — |

**Legjobb:** `<modell>`.

### HuGME eredmények (generatív, LLM-as-a-Judge — 6 metrika, 300 item)

| Modell | Mód | Judge score (%) | Judged subset | Megjegyzés |
|--------|-----|----------------:|---------------|------------|
| `<modell1>` | nothink | _._% | _/300 | — |
| `<modell1>` | think | _._% | _/300 | — |
| `<modell2>` | nothink | _._% | _/300 | — |
| `<modell2>` | think | _._% | _/300 | — |

**Legjobb:** `<modell>`.

> A HuGME judge 6 metrika átlaga: relevance, coherence, fluency, informativeness, harmlessness, overall. A bíró modell részletei a [Függelék](#verzióinformáció) szekcióban.

### MT-Bench-HU eredmények (generatív, GSB multi-baseline — 24 item × 3 baseline)

| Modell | Mód | Score (%) | W/L/T | Megjegyzés |
|--------|-----|----------:|-------|------------|
| `<modell1>` | nothink | _% | W_/L_/T_ | — |
| `<modell1>` | think | _% | W_/L_/T_ | — |
| `<modell2>` | nothink | _% | W_/L_/T_ | — |
| `<modell2>` | think | _% | W_/L_/T_ | — |

**Legjobb:** `<modell>`.

> A score 3 baseline (deepseek-v4-flash:cloud, deepseek-v4-pro:cloud, kimi-k2.6:cloud) GSB átlaga. W/L/T az összes baseline-on összesítve.

### UD Hungarian eredmények (nyelvészeti — CoNLL-U, UPOS/UAS/LAS)

| Modell | Mód | Composite | UPOS | UAS | LAS | Megjegyzés |
|--------|-----|----------:|-----:|----:|----:|------------|
| `<modell1>` | nothink | _._% | _._% | _._% | _._% | — |
| `<modell1>` | think | _._% | _._% | _._% | _._% | CoT-zavar kockázata |
| `<modell2>` | nothink | _._% | _._% | _._% | _._% | — |
| `<modell2>` | think | _._% | _._% | _._% | _._% | — |

**Legjobb:** `<modell>`.

> Az UD composite a 3 metrika átlaga. A think modellek jellemzően CoT-t írnak CoNLL-U helyett, így a parser csak a válasz végén keres — ez alacsonyabb score-okat eredményez.

## Kompozit score-ok

A [Modell vs. Modell](../comparisons/modell-vs-modell.md) és az [AGENTS.md](../../AGENTS.md) által definiált **kötelező 40/40/20 súlyozás** (NE változtatható):

```
composite = 0.40 × statisztikai + 0.40 × generatív + 0.20 × nyelvészeti
```

Ahol:

- **statisztikai** = átlag(HuLU, MMLU-HU) — jelenleg 2 benchmark implementált (arc_hu, gsm8k_hu jövőbeli)
- **generatív** = átlag(HuGME, MT-Bench-HU) — mindkét implementált
- **nyelvészeti** = UD Hungarian composite (morphology, perplexity jövőbeli)

> Ha egy dimenzióból minden benchmark hiányzik, a súlyok a jelenlévőkre oszlanak arányosan (lásd `scripts/aggregate_results.py:131-142`).

### Táblázat A — 40/40/20 súlyozott (kötelező)

| Modell | Mód | STAT | GEN | LING | **Composite (40/40/20)** |
|--------|-----|----:|----:|-----:|--------------------------:|
| `<modell1>` | nothink | _._% | _._% | _._% | **_._%** |
| `<modell1>` | think | _._% | _._% | _._% | **_._%** |
| `<modell2>` | nothink | _._% | _._% | _._% | **_._%** |
| `<modell2>` | think | _._% | _._% | _._% | **_._%** |

### Táblázat B — 4 fő benchmark egyszerű átlaga (kiegészítő nézet)

A 40/40/20 mellett egy egyszerűbb nézet is hasznos lehet, ahol minden benchmark egyenlő súllyal szerepel (kivéve MT-Bench-HU, mert 50% mindenkinél = semmi információ):

```
átlag_4_bench = (HuLU + MMLU-HU + HuGME + UD) / 4
```

| Modell | Mód | HuLU | MMLU-HU | HuGME | UD | **Átlag (4-bench)** |
|--------|-----|----:|--------:|------:|---:|--------------------:|
| `<modell1>` | nothink | _._% | _._% | _._% | _._% | **_._%** |
| `<modell1>` | think | _._% | _._% | _._% | _._% | **_._%** |
| `<modell2>` | nothink | _._% | _._% | _._% | _._% | **_._%** |
| `<modell2>` | think | _._% | _._% | _._% | _._% | **_._%** |

### Dimenziónkénti győztesek

- 🥇 **Statisztikai (HuLU + MMLU-HU átlaga):** `<modell>` — `<pontszám>`/100
- 🥇 **Generatív (HuGME + MT-Bench átlaga):** `<modell>` — `<pontszám>`/100
- 🥇 **Nyelvészeti (UD composite):** `<modell>` — `<pontszám>`/100
- 🏆 **Composite győztes (40/40/20):** `<modell>` — `<pontszám>`/100

## Heatmap-ek

A vizuális áttekintéshez **két heatmap** készül (matplotlib, RdYlGn színskála, vmin=0, vmax=1):

### Statisztikai benchmarkok

![Stat heatmap](results_heatmap_stat-2026-07-14.png)

*HuLU + MMLU-HU eredmények, sorok composite score szerint rendezve.*

### Generatív + nyelvészeti benchmarkok

![Gen/Ling heatmap](results_heatmap_genling-2026-07-14.png)

*HuGME + MT-Bench-HU + UD Hungarian eredmények, sorok composite score szerint rendezve.*

## Figyelemre méltó eredmények

### Meglepetések

- _<leírás>_ — _<mért adat, ami nem volt várható>_

### Anomáliák

- _<leírás>_ — _<Hibás prompt? Modelles crash? Cloud rate limit?>_

### Korrelációk

- _pl. A HuLU és MMLU-HU között közepes pozitív korreláció (R² ≈ 0.5)_
- _pl. A think mód erősen javítja a statisztikai, de rontja a nyelvészeti benchmarkokat_

### Limitációk

- _pl. A bíró modell saját maga is egy cloud modell, ezért elfogult lehet_
- _pl. A bíró modell (gemini-3-flash-preview) megszűnt — a HuGME és MT-Bench eredmények nem reprodukálhatóak_
- _pl. A CoT-strip parser a CoNLL-U-t a válasz végén keresi, de a modellek középre is tehetik_
- _pl. A lokális mérések nem készültek el (RTX 4090 benchmark tervben)_

## Következő lépések

- [ ] _<pl. A bíró modell cseréje (gemini-3-pro vagy hasonló) — HuGME és MT-Bench rejudge>_
- [ ] _<pl. MT-Bench baseline diverzifikálás (változatosabb modellek a differenciáláshoz)>_
- [ ] _<pl. UD think CoT-parser javítás (teljes szövegben keresés)>_
- [ ] _<pl. Lokális benchmarkok (RTX 4090 24GB) a cloud vs. lokális összehasonlításhoz>_
- [ ] _<pl. Bootstrap CI a composite score-okhoz (95% konfidencia-intervallum)>_

## Függelék — nyers adatok helye

Minden nyers mérési adat itt található:

- **Eredmények (JSONL + summary):** `results/<model>-<mode>/<bench>_results.jsonl` + `<bench>_summary.json`
- **State (checkpoint):** `state/<model>-<mode>/<bench>.json`
- **Logok:** `logs/followup_*.log`, `logs/priority_*.log`, `logs/priority_rerun_ud_*.log`
- **Státusz riportok:** `wiki/reports/benchmark-statusz-*.md`
- **Composite CSV:** `wiki/reports/composite_scores-YYYY-MM-DD.csv` (pandas export)
- **Heatmap-ek:** `wiki/reports/results_heatmap_stat-2026-07-14.png` + `results_heatmap_genling-2026-07-14.png`

### Reprodukálhatóság

A mérések reprodukálásához szükséges:

- Conda env: `eval-hu` (Python 3.11, `/home/openclaw/anaconda3/envs/eval-hu`) — **nem** `hu-eval`!
- Ollama verzió: `>=0.5.0` (cloud API endpoint: `https://ollama.com:443`)
- Ollama kliens beállítások: `temperature=0.0`, `num_predict=32/1024/2048` (bench mód szerint), `stream=False`
- Prompt template-ek: `scripts/judge_hugme.py:27-36` (HuGME), `scripts/judge_mt_bench.py:23-39` (MT-Bench)
- Modell-pool: `scripts/queue_all_benchmarks.sh:9-21` (12 modell, 1 RETIRED)

### Verzióinformáció

| Komponens | Verzió |
|-----------|--------|
| Benchmark suite | vX.Y.Z |
| Bíró modell | `<modell>:<verzió>` (gemini-3-flash-preview:latest 2026-07-14-ig) |
| Prompt template | vX.Y |
| Kiértékelő script | commit `<hash>` |
| Conda env | `eval-hu` (Python 3.11) |
| Ollama | ≥ 0.5.0 |

## Változtatási napló (change log)

| Dátum | Szerző | Változás |
|-------|--------|----------|
| 2026-06-06 | openclaw | Sablon létrehozva |
| 2026-07-15 | openclaw | v1.1: sebesség/költség/kontextus törlése, két kompozit tábla, két heatmap, UD/MT-Bench szekciók, bíró megszűnés lábjegyzet |

## Kapcsolódó

- [Riport Aggregáció runbook](../runbooks/aggregate-results.md) — composite score számítás (40/40/20)
- [Eredmény aggregáció + vizualizáció](eredmeny-aggregacio.md) — heatmap generálás
- [Modell vs. Modell](../comparisons/modell-vs-modell.md) — páronkénti összehasonlítás
- [Benchmark vs. Benchmark](../comparisons/benchmark-vs-benchmark.md) — mit mér melyik benchmark
- [Cloud vs. Lokális](../comparisons/cloud-vs-lokal.md) — üzemeltetési kontextus
- [Overview](../overview.md) — projekt cél és hatókör
- [SCHEMA](../SCHEMA.md) — formátum
- [AGENTS.md](../../AGENTS.md) — 40/40/20 súlyozás szabálya (kötelező, nem változtatható)
