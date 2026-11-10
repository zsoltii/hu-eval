# Beam (Cloud)

*Típus:* entity
*Forrás(ok):* belső benchmark futtatás (`results/beam-cloud-think/*`), `ollama show beam:cloud`, `reports/composite_scores.csv`, [riport 2026-10-27 (beam)](../reports/report-2026-10-27-beam.md)
*Létrehozva:* 2026-10-27
*Frissítve:* 2026-10-27

---

## Azonosítás

- **Ollama alias:** `beam:cloud`
- **Paraméterszám:** 501B
- **Kontextus:** 1 048 576 token
- **Kvantálás:** `ollama-cloud` (lokális kvantálás nem ismert)
- **Capabilities:** `completion`, `thinking` (szintek: **low / medium / high / xhigh / max**, default **max**), `tools`
- **Mód a projektben:** **think-only** — a nothink flag nem működik (lásd lentebb)
- **Státusz:** aktív benchmark modell; a teljes 5-benchmarkos mezőny **3. helye** (composite 0,7667)

## Mód-diagnózis (2026-10-27)

| Kérés | Eredmény |
|---|---|
| `think: true` (`/api/generate`) | ✅ gondolkodik (243 char) |
| `think: false` (`/api/generate`) | ❌ **mégis gondolkodik** (432 char) |
| `/v1/chat/completions` + `think: false` | ❌ reasoning 137 char |
| `/v1/chat/completions` + `chat_template_kwargs.enable_thinking: false` | ❌ reasoning 304 char |

→ **nothink nem elérhető**; a mérés a default (`max`) think szinten történt. A think-szintek (low…high) összevetése nyitott.

## Eredmények (think-only, teljes kör)

| Benchmark | Eredmény | Mezőny-helyezés |
|---|---|---|
| HuLU | **75,09%** (1938/2581) — HuCoLA 81,4 / HuCoPA 93,0 / HuRTE 90,9 / HuSST 68,8 / HuWNLI 8,3 / HuCB 74,8 | 4. (muse think 77,41% mögött) |
| MMLU-HU | **91,73%** (688/750, 38 tantárgy) | 4. (muse think 93,07%) |
| HuGME | **0,9082** — faithfulness **0,606** (mezőny-legjobb) | 2. (deepseek think 0,9369 mögött) |
| MT-Bench-HU | **0,4896** (4W / 5L / 39T) | 3. (muse think 0,5729) |
| UD Hungarian | **UPOS 87,40% / UAS 80,36% / LAS 62,46%** → composite **76,74%**, parse 98,2% | 2. (muse think 78,76%) |
| **Composite (40/40/20)** | **0,7667** | **3.** |

## Profil

- **Erősségek:** HuGME (0,9082) és kiemelkedően **faithfulness 0,606** — a legkevésbé „kerekít" a forrásszövegen a mezőnyben; HuRTE 90,9% (a think mezőny legjobbja); MMLU 91,73%.
- **Gyengeségek:** **HuWNLI 8,3%** (a mezőny mélypontja); **MT-Bench 0,4896** (5 vereség — a hosszú gondolkodó válaszok kevésbé illenek a párbeszédes feladatokhoz); UD-ben 8 üres válasz + 8 parse-hiba (98,2% parse-hányad).
- **Sebesség:** HuLU 2581 item 2 h 43 m (~3,8 s/item), MMLU 750 item 47 m, HuGME 300 item 63 m, MT-Bench 24 item 11 m, UD 449 item 7 h 49 m (~63 s/item, a hosszú mondatoknál 100 s felett).
- **Technikai sajátosság:** UD-nél **streaming szükséges** (`BENCH_STREAM=1`) — a válaszok 20k+ karakter gondolkodást tartalmaznak (6 823 eval token), a nem-streamelt hívás 502-vel elhal a 60 s-os proxy-korlát miatt.

## Történet

| Dátum | Esemény |
|---|---|
| 2026-10-27 | A modell felkerült az Ollama Cloud-ra; mód-diagnózis (think-only), majd teljes kör: composite **0,7667** (3. hely). Az UD futás közben bevezetésre került a `BENCH_STREAM=1` streaming út a `stop_on_error.py`-ban. |

## Kapcsolódó

- [Riport 2026-10-27 (beam)](../reports/report-2026-10-27-beam.md)
- [Riport 2026-10-27 (muse think)](../reports/report-2026-10-27.md)
- [Modell vs. modell](../comparisons/modell-vs-modell.md)
- [Cloud vs. lokális](../comparisons/cloud-vs-lokal.md)
- [Concept: OpenAI-kompatibilis backend](../concepts/openai-backend-support.md)
