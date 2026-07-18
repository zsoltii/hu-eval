# GPT-OSS 120B (Cloud)

*Típus:* entity
*Forrás(ok):* Ollama cloud route (`gpt-oss:120b-cloud`), belső benchmark eredmények
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15 (v1.3 — végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** GPT-OSS 120B (cloud modell, Ollama registry alias: `gpt-oss:120b-cloud`)
- **Szolgáltató:** OpenAI (OSS sorozat)
- **Paraméterszám:** 120B (MoE)
- **Elérhetőség:** cloud-only, Ollama-n keresztül
- **Státusz a projektben:** aktív, benchmark modell

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 71.8% | 85.7% | 8.7% | 0.0% | **43.2%** |
| think | 71.6% | 87.0% | 8.7% | 3.4% | **44.1%** |

- **Think/nothink azonos:** a két mód közötti különbség minimális (a thinking nem segít érdemben)
- ⚠️ **UD nothink 0.0%:** a nothink módban a parser egyáltalán nem nyer ki CoNLL-U-t

## Összekapcsolások

- [GPT-OSS 20B](gpt-oss-20b.md) — a kisebb testvér
- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — projekt kontextus
