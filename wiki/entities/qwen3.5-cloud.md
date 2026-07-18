# Qwen 3.5 (Cloud)

*Típus:* entity
*Forrás(ok):* Ollama cloud route (`qwen3.5:cloud`), belső benchmark eredmények
*Létrehozva:* 2026-06-07
*Frissítve:* 2026-07-15 (v1.3 — végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** Qwen 3.5 (cloud modell, Ollama registry alias: `qwen3.5:cloud`)
- **Szolgáltató:** Alibaba Qwen csoport
- **Paraméterszám:** ~397B (MoE) — a pool legnagyobb aktív modellje
- **Elérhetőség:** cloud-only, Ollama-n keresztül `ollama run qwen3.5:cloud`
- **Státusz a projektben:** aktív, benchmark modell (mindkét módban: think + nothink)
- **Megjegyzés:** a korábbi `qwen3.5:397b-cloud` név (v1.2.2 előtt) hibás volt, a helyes név `qwen3.5:cloud`

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 75.0% | 85.1% | 9.5% | 37.6% | **51.5%** |
| think | 78.1% | 92.5% | 9.2% | 0.0% | **46.0%** |

- 🥇 **Legjobb HuLU** (think): 78.1% — a teljes pool legmagasabb HuLU pontszáma
- 🥇 **Statisztikai dimenzió győztese** (think): 85.3% (HuLU + MMLU-HU átlag)
- **Tradeoff:** a think mód javítja a HuLU-t (+3.1%) és az MMLU-HU-t (+7.4%), de az UD-t 37.6% → 0.0%-ra rontja (CoT-zavar)

## Képességek

- **Kontextus:** széles (a service default szerint)
- **Nyelv:** erős magyar támogatás (a legnagyobb modell a poolban)
- **Think mód:** a gondolkodás jelentősen javítja a statisztikai benchmarkokat

## Összekapcsolások

- [MiniMax M3](minimax-m3.md) — aktív default cloud modell
- [DeepSeek V4 Pro](deepseek-v4-pro.md) — 🏆 legjobb composite
- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [MMLU-HU](../concepts/mmlu-hu.md) — 38 tantárgy, 5-shot
- [UD Hungarian](../concepts/ud-hungarian.md) — szintaktikai elemzés (CoT-érzékeny)
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — projekt kontextus
