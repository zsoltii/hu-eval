# DeepSeek V4 Pro (Cloud)

*Típus:* entity
*Forrás(ok):* Ollama cloud route (`deepseek-v4-pro:cloud`), belső benchmark eredmények
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15 (v1.3 — végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** DeepSeek V4 Pro (cloud modell, Ollama registry alias: `deepseek-v4-pro:cloud`)
- **Szolgáltató:** DeepSeek
- **Paraméterszám:** ~685B (MoE) — kód/érvelés specialista
- **Elérhetőség:** cloud-only, Ollama-n keresztül
- **Státusz a projektben:** aktív, benchmark modell

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 74.6% | 77.5% | **9.8%** | 59.6% | **🏆 54.3%** |
| think | 75.9% | 92.5% | 9.5% | 1.7% | **45.9%** |

- 🏆 **Legegyensúlyozottabb modell** (composite 40/40/20, nothink): **54.3%** — a végleges baseline győztese
- 🥇 **Legjobb HuGME (judge score):** 9.8% (nothink) — a legmagasabb generatív pontszám
- **Tradeoff:** a think mód rontja a composite-t (54.3% → 45.9%) az UD 59.6% → 1.7% zuhanása miatt, noha az MMLU-HU 77.5% → 92.5%-ra javul

## Összekapcsolások

- [DeepSeek V4 Flash](deepseek-v4-flash.md) — a gyorsabb testvér
- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [HuGME](../concepts/hugme-benchmark.md) — generatív LLM-judge
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — projekt kontextus
