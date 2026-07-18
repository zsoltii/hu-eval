# GLM 5.2 (Cloud)

*Típus:* entity
*Forrás(ok):* Ollama cloud route (`glm-5.2:cloud`), belső benchmark eredmények
*Létrehozva:* 2026-07-09
*Frissítve:* 2026-07-15 (v1.3 — végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** GLM 5.2 (cloud modell, Ollama registry alias: `glm-5.2:cloud`)
- **Szolgáltató:** Zhipu AI
- **Paraméterszám:** nem publikus
- **Elérhetőség:** cloud-only, Ollama-n keresztül
- **Státusz a projektben:** aktív, benchmark modell (v1.3-ban került a poolba)

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 75.3% | 84.9% | 9.2% | 40.9% | **52.1%** (2. hely) |
| think | 76.0% | 91.4% | 9.5% | 2.8% | **45.9%** |

- 🥈 **2. hely composite** (nothink): 52.1% — közel a győztes deepseek-v4-pro (54.3%)-hoz
- **Tradeoff:** a think mód javítja a statisztikait, de az UD-t 40.9% → 2.8%-ra rontja

## Összekapcsolások

- [GLM 5.1](glm-5.1.md) — a korábbi verzió
- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — projekt kontextus
