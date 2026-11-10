# Qwen3.5-9B-MTP GGUF (Lokális, UD-Q4_K_XL)

*Típus:* entity
*Forrás(ok):* unsloth GGUF konverzió, Alibaba Cloud Qwen team modellkártya, belső benchmark mérés (2026-10-24), `wiki/reports/report-2026-10-24.md`
*Létrehozva:* 2026-10-26
*Frissítve:* 2026-10-26

---

## Azonosítás

- **Teljes név:** `unsloth/Qwen3.5-9B-MTP-GGUF:UD-Q4_K_XL`
- **Rövid név:** `Qwen3.5-9B-MTP UD-Q4_K_XL` / `qwen3.5-9b-mtp-lokalis`
- **Szolgáltató:** Alibaba Cloud / Qwen Team (alapmodell); unsloth (GGUF kvantálás)
- **Architektúra:** Qwen 3.5 dense transformer, 9 milliárd paraméter + **MTP** (multi-token prediction) draft head a speculative decodinghez
- **Kvantálás:** **`UD-Q4_K_XL`** (Unsloth Dynamic 2.0 GGUF, ~4 bit)
- **Kontextus ablak:** 32 000 token (llama-server `-c 32000`, `--parallel 1`)
- **Státusz a projektben:** aktív lokális benchmark-modell
- **Mért mód:** **csak nothink** (2026-10-23-i felhasználói döntés: „nem mérünk think-et")

## Backend

A modell **nem Ollama-n**, hanem **llama-server-en** fut (OpenAI-kompatibilis API):

| Tulajdonság | Érték |
|-------------|-------|
| Backend | `openai` (`--backend openai --base-url http://localhost:8080/v1`) |
| Szerver | llama-server, `-c 32000 --parallel 1`, MTP speculative decoding |
| Reasoning | `reasoning_format: none`; a think flag minden kérésben explicit `false` |
| Sampling | **nincs** — a llama-server defaultja (0,8) érvényesül |
| Kimeneti plafon | 32 768 token (`MAX_OUTPUT_TOKENS`) |

## Benchmark-eredmények (2026-10-24, nothink)

| Benchmark | Eredmény | Megjegyzés |
|---|---|---|
| HuLU | **70,21%** (1812/2581) | a mezőny utolsó helye; HuWNLI 60,0% (a mezőny legjobbja) |
| MMLU-HU | **65,53%** (983/1500) | tantárgy-átlag 62,5%; formális/matematikai tantárgyaknál 22–31% |
| HuGME | **0,7203** (300/300) | faithfulness 0,260 a leggyengébb metrika |
| MT-Bench-HU | **0,3958** (24/24, 2 baseline) | 0 tiszta győzelem (0W/10L/38T) |
| UD Hungarian | **UPOS 32,56% / UAS 15,75% / LAS 11,43%** (composite 19,91%) | parse-hányad 83,1%; parse-olhatókon UPOS 39,19% |
| **Composite (40/40/20)** | **0,5345** | 8. hely a teljes mezőnyben |

### HuLU sub-task bontás

| HuCoLA | HuCoPA | HuRTE | HuSST | HuWNLI | HuCB |
|---|---|---|---|---|---|
| 74,5% | 82,0% | 68,7% | 67,2% | **60,0%** | 64,1% |

### HuGME metrika-bontás

| toxicity | answer_relevancy | prompt_alignment | bias | summarization | faithfulness |
|---|---|---|---|---|---|
| 0,980 | 0,839 | 0,793 | 0,775 | 0,671 | **0,260** |

## Történet — a `temperature: 0` token-loopok

Az első (2026-10-23-i) futás `temperature: 0.0` (greedy) dekódolással készült, és a UD Hungarian futás **139/449 (31%)** válasza hosszú, **103/449 (22,9%)** valóban degenerált token-loop volt (növekvő sorszám-sorok, kitöltő `_`-sorok, FEATS-ismétlődés). A felhasználó ezt észlelte; a gyökérok a greedy dekódolás volt.

A javítás (2026-10-24): **minden sampling paraméter kikerült a kérésekből** (temperature, top_p, top_k, min_p, repeat_penalty), a kimeneti plafon **32 768 token** lett, és a UD runner **bounded retry**-t kapott (max. 2 újrapróbálkozás degeneráció esetén). A futás `--reset`-tel újraindult.

**Eredmény:** a mostani futásban 0 elfogadott degenerált válasz van; 52/449 item igényelt újrapróbálkozást. **Ára:** a statisztikai benchmarkok 5–6 ponttal gyengébbek a greedy futásnál (HuLU 0,7555 → 0,7021; MMLU 0,7147 → 0,6553), és a UD formátumhűség 83,1%-ra esett (a maradék 17% 8 oszlopos, eltérő sémájú CoNLL-U).

A régi (temp=0) eredmények `*.temp0.*` néven megőrizve: `results/unsloth-Qwen3.5-9B-MTP-GGUF-UD-Q4_K_XL-nothink/`.

## Kapcsolódó

- [Riport (2026-10-24)](../reports/report-2026-10-24.md)
- [Qwen 3.5 Cloud](qwen3.5-cloud.md)
- [Qwen 3.5 lokális variansek (4b / 2b / 0.8b)](qwen3.5-local.md)
- [Qwen3-Next 80B Thinking GGUF (lokális)](qwen3-next-80b-lokalis.md)
- [OpenAI-kompatibilis backend támogatás](../concepts/openai-backend-support.md)
- [Checkpoint / progressz rendszer](../concepts/checkpoint-progress.md)
