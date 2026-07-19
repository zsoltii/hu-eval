# Magyar LLM Értékelési Projekt — Overview

*Típus:* concept
*Forrás(ok):* [Karpathy LLM Wiki Method](../llm-wiki/karpathy-llm-wiki-method.md), [Ollama docs](https://github.com/ollama/ollama/blob/main/docs/api.md), NYTK HuLU, MMLU, MT-Bench
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15 (v1.3 — 11 modell × 2 mód × 5 benchmark kész, végleges baseline riport)

---

## Cél

Minden elérhető nyelvi modell (cloud + lokális) **magyar nyelvű képességeinek szisztematikus, reprodukálható mérése**. Eredmény: egységes riport, ami alapján bárki el tudja dönteni, melyik modellt mikor érdemes használni magyar feladatra.

## Hatókör

### Benne van
- Statisztikai benchmarkok (HuLU, MMLU-HU)
- Generatív benchmarkok (HuGME, MT-Bench-HU)
- Nyelvészeti mélytesztek (UD Hungarian)
- 11 cloud modell (2 mód: think/nothink) összehasonlítása — 22 benchmark-futtatás

### Nincs benne
- Angol nyelvű tesztek (MMLU eredeti, MT-Bench eredeti, stb.)
- Multimodális (képes) modellek
- Fine-tuning kísérletek
- Production deployment (csak a mérés)
- Lokális modellek (qwen3.5:4b/2b/0.8b) — tervezve, még nem futtatták

> **Státusz (2026-07-15):** mind a 5 benchmark implementálva és lefuttatva 11 modellen × 2 módban. A `qwen3-next:80b-cloud` RETIRED (HTTP 410, 2026-06-16) — csak HuLU készült róla. A **végleges baseline riport**: [`reports/report-2026-07-14.md`](reports/report-2026-07-14.md).

## Elérhető modellek (jelenlegi pool)

A `Szerep` oszlop jelzi, hogy a modell benchmark-modell (saját maga futtatja a HuLU/MMLU/stb. teszteket) vagy judge modell (csak LLM-as-a-Judge kiértékelésre, NEM futtatunk rajta benchmarkot).

| Modell | Típus | Szerep | Státusz |
|--------|-------|--------|---------|
| `minimax-m3:cloud` | cloud | benchmark | aktív default (think/nothink) |
| `deepseek-v4-pro:cloud` | cloud | benchmark | 🏆 legjobb composite (nothink, 54.3%) |
| `deepseek-v4-flash:cloud` | cloud | benchmark | legjobb UD (nothink, 69.9%) |
| `kimi-k2.6:cloud` | cloud | benchmark | bíró státusz törölve 2026-06-07 (v1.2.4) |
| `glm-5.1:cloud` | cloud | benchmark | legnagyobb think-javulás (+4.1%) |
| `glm-5.2:cloud` | cloud | benchmark | új (v1.3), 2. hely composite nothink |
| `nemotron-3-ultra:cloud` | cloud | benchmark | 550B, lassú, legjobb think UD (7.5%) |
| `gpt-oss:120b-cloud` | cloud | benchmark | 120B, think/nothink azonos |
| `gpt-oss:20b-cloud` | cloud | benchmark | leggyengőbb aktív (MMLU 46%) |
| `qwen3.5:cloud` | cloud | benchmark | legerősebb HuLU (78.1% think) |
| `qwen3-next:80b-cloud` | cloud | benchmark | ⚠️ RETIRED 2026-06-16 (HTTP 410) |
| `gemini-3-flash-preview:latest` | cloud | **judge (megszűnt)** | bíró volt, megszűnt 2026-07-14. 09:00 CEST; helyette `deepseek-v4-pro:cloud` a hivatalos bíró (2026-07-19) |

### Benchmark lista (v1.3)

| Kategória | Benchmark | Státusz | Metrika |
|-----------|-----------|---------|---------|
| **STAT** | HuLU | ✅ kész (22 futtatás) | accuracy / composite |
| **STAT** | MMLU-HU | ✅ kész (22 futtatás) | accuracy per subject (5-shot) |
| **GEN** | HuGME | ✅ kész (22 futtatás) | judge score (0-1, 6 metrika) |
| **GEN** | MT-Bench-HU | ✅ kész (22 futtatás) | win rate (0-1, GSB multi-baseline) |
| **LING** | UD Hungarian | ✅ kész (22 futtatás) | (UPOS+UAS+LAS)/3 composite |

## Értékelési keretrendszer

### Három fő dimenzió

1. **Statisztikai (40% súly)** — determinisztikus, olcsó, gyors (HuLU + MMLU-HU)
2. **Generatív (40% súly)** — LLM-as-a-Judge, drágább, lassabb (HuGME + MT-Bench-HU)
3. **Nyelvészeti (20% súly)** — magyar-specifikus (UD Hungarian)

### Composite score
Súlyozott aggregátum (40/40/20), 0-100 skálán, riportban megjelenítve. Kötelező súlyozás az AGENTS.md szerint — nem változtatható. Hiányzó dimenzió esetén a súlyok arányosan újraoszlanak a jelenlévőkre.

### Legfontosabb eredmények (v1.3 baseline, 2026-07-14)

- 🏆 **Legegyensúlyozottabb (composite 40/40/20):** `deepseek-v4-pro:cloud` (nothink) — 54.3%
- 🥇 **Legjobb HuLU:** `qwen3.5:cloud` (think) — 78.1%
- 🥇 **Legjobb MMLU-HU:** `kimi-k2.6:cloud` (think) — 92.7%
- 🥇 **Legjobb UD Hungarian:** `deepseek-v4-flash:cloud` (nothink) — 69.9%
- **Fő tradeoff:** nothink > nyelvészeti (UD), think > statisztikai (MMLU-HU +25%); HuGME ~9% mindenkinél.

## Fő lépések (terv → kész)

1. ✅ **Előkészületek** — mappastruktúra, conda env (`eval-hu`), Ollama kliens
2. ✅ **Statisztikai benchmarkok** — HuLU (2581 item/modell), MMLU-HU (1500 item/modell)
3. ✅ **Generatív benchmarkok** — HuGME (300 prompt × 6 metrika), MT-Bench-HU (24 kérdés × 2 turn GSB)
4. ✅ **Nyelvészeti mélytesztek** — UD Hungarian (137 mondat, CoNLL-U parse)
5. ✅ **Aggregáció és riport** — végleges baseline riport (`reports/report-2026-07-14.md`), 2 heatmap + composite CSV

### Következő lépések (jövőbeli)

- [ ] Új bíró modell (gemini-3-pro vagy hasonló) — HuGME/MT-Bench rejudge a reprodukálhatósághoz
- [ ] MT-Bench-HU baseline felülvizsgálat (jelenleg 50% mindenkinél, nem differenciál)
- [ ] UD think parser javítás (CoT-strip után teljes válaszban keresés)
- [ ] Lokális benchmarkok (RTX 4090: qwen3.5:4b, minimax-m3) a cloud vs. lokális összehasonlításhoz
- [ ] arc_hu / gsm8k_hu / morphology / perplexity implementálása (stat/ling dimenzió bővítése)

## Kapcsolódó

- [SCHEMA](SCHEMA.md) — oldal-univerzum definíció
- [Index](index.md) — tartalomjegyzék
- [Log](log.md) — tevékenységnapló
- [Végleges baseline riport](reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Karpathy módszer](../llm-wiki/karpathy-llm-wiki-method.md) — elméleti háttér
