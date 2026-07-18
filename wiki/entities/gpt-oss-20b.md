# GPT-OSS 20B (Cloud)

*Típus:* entity
*Forrás(ok):* Ollama cloud route (`gpt-oss:20b-cloud`), belső benchmark eredmények
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15 (v1.3 — végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** GPT-OSS 20B (cloud modell, Ollama registry alias: `gpt-oss:20b-cloud`)
- **Szolgáltató:** OpenAI (OSS sorozat)
- **Paraméterszám:** 20B (MoE) — a pool leggyengébb aktív modellje
- **Elérhetőség:** cloud-only, Ollama-n keresztül
- **Státusz a projektben:** aktív, benchmark modell

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 67.0% | 46.1% | 8.5% | 0.0% | **34.3%** (legrosszabb) |
| think | 71.4% | 46.5% | 8.2% | 1.0% | **35.4%** |

- 🔻 **Leggyengőbb aktív modell** (composite ~34-35%)
- ⚠️ **MMLU-HU 46% mindkét módban** — a modell rosszul értelmezi a magyar MMLU kérdéseket (valószínűleg nincs magyar tanítási adat)
- ⚠️ **Anomália:** HuGME nothink 138 ó (cloud rate limit) — kihagyva az átlagból, tényleges érték 8.5% (117 judged)

## Összekapcsolások

- [GPT-OSS 120B](gpt-oss-120b.md) — a nagyobb testvér
- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — projekt kontextus
