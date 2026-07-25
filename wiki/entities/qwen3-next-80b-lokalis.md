# Qwen3-Next 80B Thinking GGUF (Lokális)

*Típus:* entity
*Forrás(ok):* unsloth community GGUF conversion, Alibaba Cloud Qwen team model card, belső benchmark mérések (2026-07-21/24)
*Létrehozva:* 2026-07-19
*Frissítve:* 2026-07-25

---

## Azonosítás

- **Teljes név:** `unsloth/Qwen3-Next-80B-A3B-Thinking-GGUF:UD-IQ3_XXS`
- **Rövid név:** `Qwen3-Next-80B IQ3_XXS` / `qwen3-next-80b-lokalis`
- **Szolgáltató:** Alibaba Cloud / Qwen Team (alapmodell); unsloth (GGUF kvantálás)
- **Architektúra:** Qwen3-Next Mixture-of-Experts (MoE)
  - **Összes paraméter:** 80 milliárd
  - **Aktív paraméter:** 3 milliárd (A3B)
  - **Típus:** Thinking modell (beépített CoT képesség)
- **Kvantálás:** IQ3_XXS (3.06 bpw, 32.95 GB GGUF fájl)
- **Kontextus ablak:** 16 128 token (llama-server alapértelmezett `n_ctx`)
- **Státusz a projektben:** aktív, az egyetlen lokális benchmark-modell a modell-poolban
- **Szerep:** benchmark (nothink módban futtatva, think eredmények véletlen adatvesztés miatt elvesztek)

## Backend

A modell **nem natív Ollama-n** fut, hanem **llama-server-en** (OpenAI-kompatibilis API):

| Tulajdonság | Érték |
|-------------|-------|
| Backend | `openai` (`--backend openai --base-url http://localhost:8080/v1`) |
| Szerver | lokális llama-server, 1 slot (egyszálú) |
| API | `/v1/chat/completions` (OpenAI-kompatibilis) |
| Chat template | llama-server beépített, a modell GGUF metaadataiból |
| `reasoning_format` | `none` (nincs hatása — lásd limitációk) |

> **Fontos:** a llama-server `reasoning_format: none` + `reasoning_in_content: false` beállításai **nem kapcsolják ki** a modell CoT-ját. A Qwen3-Next Thinking modell a `chat_template` miatt minden promptnál gondolkodik, függetlenül a nothink/think beállítástól. A nothink mód (num_predict=4096) néha kevés — a válasz `content` üres, `finish_reason: length`.

## Benchmark eredmények

### Nothink mód (egyetlen teljes adathalmaz)

A 4 implementált benchmarkból 4 futott le, az UD Hungarian **nem értékelhető** (lásd lent).

| Benchmark | Score | Részletek |
|-----------|------:|-----------|
| **HuLU** | **56.53%** | 1459/2581 helyes |
| **MMLU-HU** | **86.87%** | 1303/1500 helyes, 5-shot |
| **HuGME** | **0.828** | 300/300 judged, bíró: `deepseek-v4-pro:cloud` |
| **MT-Bench-HU** | **37.50%** | 1W/7L/16T vs `deepseek-v4-flash:cloud`, bíró: `deepseek-v4-pro:cloud` |
| **UD Hungarian** | **N/A** | CoT minden promptnál kimeríti a kontextusablakot |

### HuLU per-sub-task bontás

| Sub-task | Pontosság | Helyes / Összes |
|----------|----------:|----------------:|
| **HuCOLA** (nyelvtani elfogadhatóság) | 51.54% | 469/910 |
| **HuCoPA** (ok-okozat) | 90.00% | 90/100 |
| **HuRTE** (szöveg-entailment) | 72.84% | 177/243 |
| **HuSST** (szentiment) | 57.00% | 664/1165 |
| **HuWNLI** (lexicalis következtetés) | 13.33% | 8/60 |
| **HuCB** (CommitmentBank) | 49.51% | 51/103 |

### Think mód — adatvesztés

A think módú futások mind befejeződtek, de a fájlok véletlen `rm -rf` által törlődtek az aggregálás előtt. Ismert utolsó státusz:

| Benchmark | Utolsó ismert score |
|-----------|--------------------:|
| HuLU think | 60.9% (1571/2581) |
| MMLU-HU think | 89.7% (1345/1500) |
| HuGME think | 0.847 |
| MT-Bench-HU think | 0.083 (1W/11L) |

### Composite score (40/40/20)

A nyelvészeti dimenzió (UD Hungarian) teljes hiánya miatt a súlyok STAT/GEN között 50/50 arányban oszlottak újra:

- **STAT** = átlag(HuLU, MMLU-HU) = 71.70%
- **GEN** = átlag(HuGME, MT-Bench-HU) = 60.17%
- **LING** = N/A
- **Composite (50/50):** **65.93%**

## UD Hungarian inkompatibilitás

A Qwen3-Next Thinking modell **alapvetően inkompatibilis** az UD Hungarian benchmark jelenlegi implementációjával:

1. A modell a CoT-re használja a rendelkezésre álló kontextusablak nagy részét.
2. `n_ctx=16128` mellett a gondolkodás kimeríti a kontextust, mire a tényleges CoNLL-U generálásra kerülne sor.
3. `num_predict=4096` (nothink) gyakran kevés — a válasz `finish_reason: length` miatt csonkul.
4. A `reasoning_format: none` nem kapcsolja ki a CoT-t (llama-server limitáció).
5. Még think módban (`num_predict=32768`) sem sikerült CoNLL-U kimenetet kinyerni.

## Főbb jellemzők

### Erősségek
- **MMLU-HU 86.87%** — erős tantárgy-specifikus tudás a 3.06 bpw kvantáláshoz képest
- **HuCoPA 90.0%** — kiváló ok-okozat felismerés magyarul
- **HuGME 0.828** — jó generatív teljesítmény az IQ3_XXS kvantálás ellenére

### Gyengeségek
- **HuWNLI 13.33%** — a lexicalis következtetés sub-task szinte véletlenszerű (random guess 50% lenne 2 osztállyal)
- **HuCB 49.51%** — random guess szint
- **UD Hungarian N/A** — a modell architektúra alapjaiban inkompatibilis a benchmark implementációval
- **CoT overhead** — a modell minden promptnál gondolkodik, ami megbízhatatlan a rövid `num_predict` miatt

### Limitációk
- Egyszálú backend → soros futtatás, hosszú futásidő (~10 óra a 4 benchmarkra)
- 16K context limit → a hosszabb MMLU-HU 5-shot promptok néha megközelítik a határt
- Az IQ3_XXS kvantálás (3.06 bpw) a legalacsonyabb elérhető minőségi szint a GGUF formátumban
- A think adatok hiánya megnehezíti a nothink/think összehasonlítást

## Kapcsolódó

- [Riport: Lokális Qwen3-Next IQ3_XXS (2026-07-25)](../reports/report-2026-07-25-lokalis-qwen3-next.md) — teljes teljesítményriport
- [Cloud vs. Lokális](../comparisons/cloud-vs-lokal.md) — lokális benchmark-modell szekció
- [Concept: OpenAI-kompatibilis backend](../concepts/openai-backend-support.md) — `ollama` vs `openai` backend
- [Qwen3-Next 80B (Cloud)](qwen3-next-80b.md) — a cloud megfelelője (RETIRED)
- [Qwen 3.5 Lokális](qwen3.5-local.md) — kisebb lokális Qwen modellek (4B/2B/0.8B)
- [Overview](../overview.md) — projekt cél, modell pool
- [Log](../log.md) — 2026-07-25 bejegyzés a benchmark eredményekről
