# Modell vs. Modell — Összehasonlítási Keretrendszer

*Típus:* comparison
*Forrás(ok):* hu-eval projekt belső, Karpathy LLM Wiki módszer, [Overview](../overview.md)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Cél

Ez az oldal a magyar LLM-ek **páronkénti összehasonlításának** módszertanát és formátumát definiálja. A cél, hogy minden modellpárról (pl. `minimax-m3` vs. `qwen3.5:4b`) egységes szerkezetű, könnyen értelmezhető összehasonlítás készüljön — ne a futtatáskor kelljen kitalálni, mit nézünk.

## Miért kell keretrendszer?

- **Reprodukálhatóság** — ugyanazt a kérdéssort ugyanazzal a bíró modellel értékeljük ki
- **Párhuzamosság** — több subagent is tudjon összehasonlítást írni anélkül, hogy összebeszélnének
- **Differenciálás** — nem elég az összesített score, dimenziónként is látni kell, hol miben erős egy modell

## Összehasonlítási dimenziók

Négy fő dimenzió, mindegyik 0-100 skálán mérve, a composite score-ba eltérő súllyal beszámítva.

### 1. Magyar nyelv minősége (súly: 40%)

- **Statisztikai aldimenzió** — HuLU, MMLU-HU, ARC-HU, GSM8K-HU pontszámok átlaga
- **Generatív aldimenzió** — HuGME, MT-Bench-HU, szabad kérdéssor LLM-as-a-Judge
- **Nyelvészeti aldimenzió** — UD Hungarian morfológia, szórend, egyeztetés pontossága

Mérőszám: `(0.5 × statisztikai) + (0.3 × generatív) + (0.2 × nyelvészeti)` skálázva 0-100-ra.

### 2. Sebesség (súly: 20%)

- **TTFT** (time to first token) — prompt → első tokenig eltelt idő, ms-ban
- **TPOT** (time per output token) — generálás átlagos sebessége, ms/token
- **Teljes átfutás** — 1000 tokenes válasz teljes ideje, másodpercben

Mérőszám: `(1 / átfutás_ms) × normalizáló_konstans` — nagyobb jobb.

### 3. Költség (súly: 20%)

- **Cloud modellek** — USD / 1M token (input + output átlag)
- **Lokális modellek** — elektromos áram + amortizált hardverköltség / 1M token
- **Kontextus-költség** — hosszú promptokra hogyan skálázódik az ár

Mérőszám: `1 / (USD_per_1M_token × 1000)` inverz skálán, 0-100 közé normálva.

### 4. Kontextus hossz (súly: 20%)

- **Névleges max kontextus** — amit a modell dokumentációja ígér
- **Hatékony kontextus** — ahol a teljesítmény még nem esik 20%-kal a rövid kontextusú teljesítmény alá
- **Memóriaigény** — lokális modelleknél VRAM/RAM a teljes kontextus betöltéséhez

Mérőszám: `min(névleges, hatékony) / 200000 × 100` — 200k token a teljes 100-as pontszám küszöbe.

## Páronkénti módszertan

### Lépésről lépésre

1. **Modellpár kiválasztása** — jellemzően 2-4 modell azonos kategóriából (pl. két cloud flagship, vagy két lokális kis modell)
2. **Azonos promptkészlet** — ugyanaz a 50-100 prompt minden modellre, rögzített seed-del
3. **Azonos bíró modell** — `deepseek-v4-pro:cloud` (hivatalos bíró 2026-07-19 óta; a `gemini-3-flash-preview:latest` megszűnt 2026-07-14) értékeli a válaszokat. *Megjegyzés: a `kimi-k2.6:cloud` bíró státusza 2026-06-07-én (v1.2.4) törölve — csak benchmark modell; a `deepseek-v4-pro` is benchmark-modell, ezért a self-bias elv miatt saját magát nem értékelheti.*
4. **Vak értékelés** — a bíró nem tudja, melyik válasz melyik modellhez tartozik
5. **Dimenziónkénti pontozás** — minden dimenzióra 0-100, indoklással
6. **Kompozit számítás** — súlyozott átlag a fenti 4 dimenzióból
7. **Megjegyzések** — meglepő eredmények, edge case-ek, anomáliák

### Mikor melyik párt érdemes összehasonlítani?

- **Cloud vs. cloud flagship** — `minimax-m3` vs. `deepseek-v4-pro` vs. `gemini-3-flash-preview`
- **Lokális kis modellek** — `qwen3.5:0.8b` vs. `qwen3.5:2b` vs. `qwen3.5:4b`
- **Cross-tier** — `qwen3.5:4b` (lokális) vs. `gemini-3-flash-preview` (cloud) — mikor éri meg a felhő?
- **Ugyanaz a modell, cloud és lokális** — `qwen3.5:cloud` vs. (ha lenne lokális) `qwen3.5:397b`

## Várható győztesek dimenziónként

| Dimenzió | Várható győztes | Indoklás |
|----------|-----------------|----------|
| Magyar minőség | `qwen3.5:cloud` | A legnagyobb modell, multiilingual training |
| Magyar minőség (lokális) | `qwen3.5:4b` | Kis lokális kategóriában a 4B a legjobb kompromisszum |
| Sebesség (lokális) | `qwen3.5:0.8b` | GPU-n a legkisebb modell a leggyorsabb |
| Sebesség (cloud) | `gemini-3-flash-preview` | A "flash" elnevezés a sebességre utal |
| Költség (olcsó) | `qwen3.5:0.8b` (lokális) | Egyszeri hardverár, marginális áramköltség |
| Költség (cloud) | `gemini-3-flash-preview` | Flash tier jellemzően 5-10x olcsóbb a pro tier-nél |
| Kontextus hossz | `minimax-m3:cloud` | A cloud modellek jellemzően 128k-1M kontextust kínálnak |
| Kontextus hossz (lokális) | `qwen3.5:4b` | Qwen modellek jellemzően 32k-128k natív kontextussal |

## Üres összehasonlító tábla (sablon)

Az alábbi tábla a kitöltendő sablon. Minden párhoz másolatot készítünk, és a cellákat az aktuális mérés eredményeivel töltjük fel.

| Dimenzió | Modell A | Modell B | Modell C | Győztes | Megjegyzés |
|----------|----------|----------|----------|---------|------------|
| Magyar minőség (súlyozott) | _/100 | _/100 | _/100 | — | — |
| Statisztikai aldimenzió | _/100 | _/100 | _/100 | — | — |
| Generatív aldimenzió | _/100 | _/100 | _/100 | — | — |
| Nyelvészeti aldimenzió | _/100 | _/100 | _/100 | — | — |
| Sebesség — TTFT (ms) | _ | _ | _ | — | — |
| Sebesség — TPOT (ms/tok) | _ | _ | _ | — | — |
| Sebesség — 1k token (s) | _ | _ | _ | — | — |
| Költség — USD / 1M tok | _ | _ | _ | — | — |
| Költség — memória (GB) | _ | _ | _ | — | — |
| Kontextus — névleges (tok) | _ | _ | _ | — | — |
| Kontextus — hatékony (tok) | _ | _ | _ | — | — |
| **Composite score** | _/100 | _/100 | _/100 | — | Súlyozott: 0.4 + 0.2 + 0.2 + 0.2 |

### Pontozási konvenciók

- **Félkövér számok** — az adott sor győztese
- `—` — nincs adat, vagy nem értelmezhető
- A "Megjegyzés" oszlopba rövid, tényszerű indoklás (max 1-2 mondat)

## Kompozit score képlete

```
composite = 0.40 × magyar_minoseg
         + 0.20 × sebesseg
         + 0.20 × koltseg
         + 0.20 × kontextus_hossz
```

Minden dimenzió 0-100 közötti szám, súlyozott átlag → composite 0-100 között.

## A modell entitás oldalakra mutató hivatkozások

Az alábbi hat modell entity oldalára hivatkozunk (a projekt entity subagent-je készítette, hét fájlban — a három lokális Qwen variáns egy oldalon):

- [MiniMax M3](../entities/minimax-m3.md) — jelenlegi default, cloud
- [DeepSeek V4 Pro](../entities/deepseek-v4-pro.md) — cloud, nagy modell
- [Kimi K2.6](../entities/kimi-k2.6.md) — cloud, benchmark modell (bíró státusz törölve 2026-06-07, v1.2.4)
- [Gemini 3 Flash Preview](../entities/gemini-3-flash.md) — cloud, gyors
- [Qwen 3.5 397B Cloud](../entities/qwen3.5-397b.md) — cloud, legnagyobb
- [Qwen 3.5 Lokális (4b / 2b / 0.8b)](../entities/qwen3.5-local.md) — lokális, három méret egy oldalon

## Tervezett összehasonlítás-párok (backlog)

Az alábbi összehasonlításokat érdemes elkészíteni a projekt során:

1. `minimax-m3` vs. `deepseek-v4-pro` — cloud flagship head-to-head
2. `gemini-3-flash-preview` vs. `qwen3.5:4b` — cloud flash vs. lokális közepes
3. `qwen3.5:0.8b` vs. `qwen3.5:2b` vs. `qwen3.5:4b` — lokális létra
4. `qwen3.5:cloud` vs. `minimax-m3` — legnagyobb cloud modellek

## Kapcsolódó

- [Overview](../overview.md) — projekt cél és modellkészlet
- [Benchmark vs. Benchmark](benchmark-vs-benchmark.md) — milyen benchmarkot használjunk
- [Cloud vs. Lokális](cloud-vs-lokal.md) — üzemeltetési tradeoff-k
- [SCHEMA](../SCHEMA.md) — formátum és karbantartási szabályok
