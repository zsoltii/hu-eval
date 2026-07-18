# GLM 5.1 (Cloud)

*Típus:* entity
*Forrás(ok):* Ollama cloud route (`glm-5.1:cloud`), belső benchmark eredmények
*Létrehozva:* 2026-06-07
*Frissítve:* 2026-07-15 (v1.3 — végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** GLM 5.1 (cloud modell, Ollama registry alias: `glm-5.1:cloud`)
- **Szolgáltató:** Zhipu AI
- **Paraméterszám:** nem publikus
- **Elérhetőség:** cloud-only, Ollama-n keresztül
- **Státusz a projektben:** aktív, benchmark modell

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 71.6% | 84.5% | 9.2% | 38.8% | **50.8%** |
| think | 75.8% | 92.7% | 9.4% | 0.8% | **45.7%** |

- 📈 **Legnagyobb think-javulás** a poolban: +4.1% (nothink → think composite, de ez főleg a MMLU-HU +8.2%-nak köszönhető)
- **Tradeoff:** a think mód javítja a statisztikait, de az UD-t 38.8% → 0.8%-ra rontja

## Összekapcsolások

- [GLM 5.2](glm-5.2.md) — a újabb verzió
- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [MMLU-HU](../concepts/mmlu-hu.md) — 38 tantárgy
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — projekt kontextus
