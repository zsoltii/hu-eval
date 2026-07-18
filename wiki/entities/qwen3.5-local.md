# Qwen 3.5 Lokális Variansek (4b / 2b / 0.8b)

*Típus:* entity
*Forrás(ok):* Alibaba Cloud Qwen team, Ollama registry, belső futtatási tapasztalatok
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15 (v1.3 — még nem futtatták, státusz frissítve)

---

## Áttekintés

Ez az oldal a Qwen 3.5 család **lokálisan futtatható** verzióit foglalja össze. Három méretben érhetők el a projektben:

- **Qwen 3.5 4B** (`qwen3.5:4b`)
- **Qwen 3.5 2B** (`qwen3.5:2b`)
- **Qwen 3.5 0.8B** (`qwen3.5:0.8b`)

Mindhárom a Qwen 3.5 dense modellcsalád "kicsi" ága — ugyanaz az architektúra és tokenizáció, mint a nagy cloud testvérnél (lásd: [Qwen 3.5 Cloud](qwen3.5-cloud.md)), csak kevesebb paraméterrel. Ez a paraméter-méret skála lehetővé teszi a **méret vs. minőség tradeoff** szisztematikus vizsgálatát magyar nyelven.

> ⏸ **Státusz (2026-07-15):** a lokális modellek még **nem lettek lefuttatva**. A v1.3 baseline kizárólag a 11 cloud modellre (2 mód) készült el. A lokális benchmarkok a "Következő lépések" részben szerepelnek (RTX 4090 24GB).

## Közös jellemzők (mindhárom méret)

- **Szolgáltató:** Alibaba Cloud / Qwen Team
- **Architektúra:** dense transformer (NEM MoE)
- **Elérhetőség:** lokális, Ollama-n keresztül (`ollama pull qwen3.5:<méret>`)
- **Kontextus ablak:** 32 000 token (mindhárom méretnél)
- **Modalitás:** szöveg-only (a lokális Qwen 3.5-ök nem multimodálisak)
- **Tokenizáció:** BPE, magyar-specifikus szub-szavas tokenekkel
- **Chat template:** Qwen 3.5 natív, "thinking" mód támogatással (`enable_thinking` flag)
- **Licenc:** Apache 2.0 (a 4b és 2b esetén); a 0.8b-re vonatkozóan a Qwen team "research-only" megkötést tett — kereskedelmi használat előtt ellenőrizni kell
- **Nyelv:** 119 nyelv támogatása, köztük a magyar (a lefedettség megegyezik a 397B verzióéval, csak a minőség alacsonyabb)

> **Megjegyzés:** a Qwen 3.5 lokális verziók 2025 Q4 - 2026 Q1 környékén jelentek meg. A Qwen team kiadási stratégiája: a nagy (397B) cloud verzió után hamarosan megjelennek a kisebb, lokálisan futtatható méretek is.

---

## Qwen 3.5 4B

### Specifikáció
- **Paraméterszám:** 4 milliárd
- **Memóriaigény (FP16):** ~8 GB VRAM; (Q4_K_M kvantálva): ~3 GB
- **Ajánlott hardver:** 8 GB+ VRAM-os GPU (RTX 3060, M1 Pro, stb.); CPU-n is futtatható kvantálva, de lassan

### Várható magyar minőség
- **HuLU becsült:** 0.45-0.55 (jelentősen alacsonyabb, mint a 397B 0.72-0.78 tartománya, de a 4B kategóriában a Qwen az egyik legjobb)
- **MT-Bench-HU becsült:** 5.5-6.5 / 10
- **Erősség:** a 4B-s kategóriában kiemelkedő magyar tudás; képes hosszabb, koherens válaszokat generálni
- **Gyengeség:** komplex érvelési feladatoknál a gondolatlánc néha "körbe-körbe megy"

### Felhasználási területek
- **Lokális baseline** — a projekt alapértelmezett lokális modellje
- **Iteratív prompt engineering** — ahol a gyors iteráció fontos
- **Annotálási segédlet** — magyar tréningadatok előkészítéséhez
- **Magánéleti szempontból érzékeny feladatok** — ahol a cloud modell nem jöhet szóba

### Ismert gyengeségek
- **Rövid kontextus:** a 32k ablak néha szűk (a HuLU hosszabb kontextusú feladatainál)
- **Időnkénti "elvesztés":** hosszú beszélgetéseknél hajlamos a korábbi utasításokat "elfelejteni"
- **Kvantálási érzékenység:** Q4 alatti kvantálásnál a magyar minőség érezhetően romlik

---

## Qwen 3.5 2B

### Specifikáció
- **Paraméterszám:** 2 milliárd
- **Memóriaigény (FP16):** ~4 GB VRAM; (Q4_K_M kvantálva): ~1.5 GB
- **Ajánlott hardver:** modern CPU-n is kényelmesen fut; régebbi laptop GPU is elég

### Várható magyar minőség
- **HuLU becsült:** 0.38-0.46
- **MT-Bench-HU becsült:** 4.5-5.5 / 10
- **Erősség:** meglepően jó alapszintű magyar szövegalkotás; egyszerű kérdés-válaszra alkalmas
- **Gyengeség:** komplex feladatoknál a 4B-hez képest is érezhető a minőségromlás; a gondolkodási láncok gyakran hibásak

### Felhasználási területek
- **Ultragyors baseline** — ahol a latency kritikus (pl. real-time chat)
- **Erőforrás-korlátozott környezet** — Raspberry Pi, régi laptop, telefon (llama.cpp / Ollama Android)
- **Batch előfeldolgozás** — nagy mennyiségű magyar szöveg gyors kategorizálása
- **A/B tesztelés** — a 4B és 2B eredmények összevetése a méret-hatás vizsgálatához

### Ismert gyengeségek
- **Korlátozott "world knowledge":** a magyar vonatkozású kultúrtörténeti tudás szegényes
- **Nyelvtani hibák:** a magyar morfológia kezelése már nem mindig pontos (pl. ikes igék, határozói igeragozás)
- **Rövid válaszok:** hajlamos túlzottan tömören válaszolni, még ha a feladat hosszabb kifejtést kér

---

## Qwen 3.5 0.8B

### Specifikáció
- **Paraméterszám:** 800 millió
- **Memóriaigény (FP16):** ~1.6 GB VRAM; (Q4_K_M kvantálva): ~0.5 GB
- **Ajánlott hardver:** gyakorlatilag bármilyen eszköz; CPU-n is futtatható

### Várható magyar minőség
- **HuLU becsült:** 0.25-0.35 (a legkisebb modell, ennek megfelelő minőség — az "alsó határ" a magyar LLM-ek között)
- **MT-Bench-HU becsült:** 3.0-4.0 / 10
- **Erősség:** meglepően kompetens alapszintű szöveggenerálásban; a magyar mondatszerkezeteket nagyjából helyesen kezeli
- **Gyengeség:** szinte minden komplex feladaton alulmarad; gondolkodási láncok nem megbízhatók

### Felhasználási területek
- **"Floor" baseline** — a magyar LLM-ek abszolút alsó határának meghatározása (ha a Qwen 0.8B jól teljesít, a feladat valószínűleg túl könnyű)
- **Oktatási célok** — a modell méret és képesség közti összefüggés demonstrálásához
- **Beágyazott / edge alkalmazások** — ahol a memória és a latency extrém korlát
- **Sanity check** — ha a Qwen 0.8B is megold egy feladatot, a feladat valószínűleg túl triviális a benchmark szempontjából

### Ismert gyengeségek
- **Az előző kettő összes gyengesége, felerősítve**
- **Magyar nyelvtan:** sok mondat nyelvtanilag helytelen (szórend, egyeztetés, igeragozás)
- **Tényszerű pontatlanság:** a magyar vonatkozású kérdésekre gyakran ad rossz vagy kitalált választ
- **Instabil viselkedés:** a temperature és seed változtatásával nagyon eltérő válaszokat ad

---

## Méretek összehasonlítása

| Dimenzió | 0.8B | 2B | 4B | `qwen3.5:cloud` (referencia) |
|----------|------|-----|-----|------------------------------|
| VRAM (Q4_K_M) | ~0.5 GB | ~1.5 GB | ~3 GB | cloud-only |
| HuLU (becsült) | 0.25-0.35 | 0.38-0.46 | 0.45-0.55 | 0.75-0.78 (78.1% think) |
| MT-Bench-HU (becsült) | 3.0-4.0 | 4.5-5.5 | 5.5-6.5 | 7.6-8.2 (50% baseline) |
| Licenc | research-only | Apache 2.0 | Apache 2.0 | (zárt) |
| Kvantálási érzékenység | magas | közepes | alacsony | n/a |

> **v1.2.9 megjegyzés:** a sebesség (token/sec, latency) sor szándékosan törölve — a projekt riportjai kizárólag a pontosságot mérik. A latency/hardver-igény pool-szintű összehasonlítása a későbbi `cloud-vs-lokal.md` riportba kerül.

### Minta prompt összehasonlítás (HU)

> **Prompt:** "Magyarázd el röviden, mi a különbség a 'múlt' és a 'jelen' igeidő között a magyarban, és adj egy-egy példát."

- **0.8B:** jellemzően 1-2 mondat, pontatlan példákkal, nyelvtani hibákkal
- **2B:** 3-4 mondat, a példák nagyjából helyesek, a magyarázat felszínes
- **4B:** 4-6 mondat, a példák helyesek, az alapfogalmak (múlt idő, jelen idő) tisztán elkülönítve
- **397B (referencia):** 6-10 mondat, a magyar igeragozás árnyalatait is megemlítve (pl. "a múlt időnek több formája van: egyszerű múlt, folyamatos múlt")

## Ajánlott használat a projektben

A három lokális modell a projektben a **méret-skála hatásának** vizsgálatára szolgál. Az alapértelmezett futtatási stratégia:

1. **Gyors iteráció:** 0.8B (a leggyorsabb, legolcsóbb)
2. **Normál lokális baseline:** 2B
3. **Lokális "high quality":** 4B
4. **Cloud összehasonlítás:** 397B (csak kiemelt esetekben)

A méret-hatás görbét külön riportban dokumentáljuk (lásd: [Qwen méret-skála riport](../reports/riport-template.md) — terv).

## Összekapcsolások

- [Qwen 3.5 Cloud](qwen3.5-cloud.md) — a nagy cloud testvér, amivel összehasonlítjuk
- [Cloud vs Lokális összehasonlítás](../comparisons/cloud-vs-lokal.md) — a Qwen lokális és a többi cloud modell közti tradeoff
- [Ollama konfiguráció](../runbooks/setup-kornyezet.md) — a lokális futtatás beállítása
- [Végleges riport](../reports/report-2026-07-14.md) — a cloud baseline (lokális még nincs)
- [MiniMax M3](minimax-m3.md) — összehasonlítási alap (cloud)
