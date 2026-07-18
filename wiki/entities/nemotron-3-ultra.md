# Nemotron 3 Ultra (Cloud)

*Típus:* entity
*Forrás(ok):* Ollama cloud route (`nemotron-3-ultra:cloud`), belső benchmark eredmények
*Létrehozva:* 2026-06-07
*Frissítve:* 2026-07-15 (v1.3 — végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** Nemotron 3 Ultra (cloud modell, Ollama registry alias: `nemotron-3-ultra:cloud`)
- **Szolgáltató:** NVIDIA
- **Paraméterszám:** ~550B — a pool legnagyobb (lassú) modellje
- **Elérhetőség:** cloud-only, Ollama-n keresztül
- **Státusz a projektben:** aktív, benchmark modell

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 70.5% | 82.7% | 8.5% | 42.5% | **50.9%** |
| think | 71.8% | 91.7% | 8.8% | **7.5%** | **46.0%** |

- 🥇 **Legjobb think módú UD:** 7.5% — a think modellek közül a legmagasabb (a CoT-strip parser miatt a többi 0-3.4%)
- ⚠️ **Leghosszabb futásidő:** ~510 ó összesen (cloud rate limit miatt 4 outlier: HuGME 205ó, MT-Bench 175ó, UD 125ó)
- **Tradeoff:** a think mód javítja a statisztikait, de az UD-t 42.5% → 7.5%-ra rontja

## Összekapcsolások

- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [UD Hungarian](../concepts/ud-hungarian.md) — szintaktikai elemzés (CoT-érzékeny)
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — projekt kontextus
