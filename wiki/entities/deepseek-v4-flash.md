# DeepSeek V4 Flash (Cloud)

*Típus:* entity
*Forrás(ok):* Ollama cloud route (`deepseek-v4-flash:cloud`), belső benchmark eredmények
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15 (v1.3 — végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** DeepSeek V4 Flash (cloud modell, Ollama registry alias: `deepseek-v4-flash:cloud`)
- **Szolgáltató:** DeepSeek
- **Paraméterszám:** nem publikus (Flash = gyors, olcsó változat)
- **Elérhetőség:** cloud-only, Ollama-n keresztül
- **Státusz a projektben:** aktív, benchmark modell + MT-Bench-HU baseline

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 73.3% | 52.0% | 9.5% | **69.9%** | **51.0%** |
| think | 76.7% | 86.6% | 9.5% | 0.3% | **44.6%** |

- 🥇 **Legjobb UD Hungarian** (nothink): 69.9% composite (UPOS 89.7 / UAS 47.0 / LAS 73.0) — a teljes pool legmagasabb UD pontszáma
- ⚠️ **Legalacsonyabb MMLU-HU** (nothink): 52.0% — a think mód +34.6%-ot javít (86.6%)
- **Tradeoff:** a think mód drasztikusan rontja az UD-t (69.9% → 0.3%), de javítja az MMLU-HU-t

## Összekapcsolások

- [DeepSeek V4 Pro](deepseek-v4-pro.md) — a nagyobb testvér, 🏆 legjobb composite
- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [UD Hungarian](../concepts/ud-hungarian.md) — szintaktikai elemzés
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — projekt kontextus
