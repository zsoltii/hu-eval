# SCHEMA — Magyar LLM Értékelési Wiki

*Típus:* concept
*Forrás(ok):* [Karpathy LLM Wiki Method](../llm-wiki/karpathy-llm-wiki-method.md), belső projektterv
*Létrehozva:* 2026-06-05
*Frissítve:* 2026-06-06

---

*Projekt célja:* magyar nyelvű LLM-ek (cloud + lokális) képességeinek mérése, dokumentálása, összehasonlítása. Karpathy LLM Wiki módszerrel.

*Létrehozva:* 2026-06-05
*Utoljára frissítve:* 2026-06-06

---

## Tervezési döntések (2026-06-06)

### Checkpoint / resume politika

Minden benchmark script **stop-on-error + resume** szemantikát követ.
Bármilyen Ollama-oldali hiba (rate limit, timeout, 5xx, connection error)
esetén a futás azonnal megáll, az állapot atomi write-tal mentődik,
és a script bármikor folytatható. Ez azért kell, mert:

- A teljes HuLU futtatás 6 modellen akár 24 óra is lehet
- A cloud modellek (kimi-k2.6, qwen3.5:397b) token-limitje naponta korlátos
- A hosszú futás alatt bármikor jöhet network glitch, Ollama újraindulás,
  VRAM-hiba

Részletek: [Checkpoint és folytatható futtatás](concepts/checkpoint-progress.md).

### Futtatható kód és a wiki szétválasztása

- **Wiki** (dokumentáció, emberi olvasásra): `wiki/` mappa, 58+ markdown fájl
- **Scriptek** (futtatható kód): `scripts/` mappa, 19 Python + 9 shell script
- **Adatok** (letöltött dataset): `data/` mappa
- **Eredmények** (per-modell JSONL + summary): `results/` mappa
- **Checkpoint state** (futás állapota): `state/` mappa
- **Logok** (append-only futás-napló): `logs/` mappa
- **Riportok** (aggregált kimenet): `reports/` mappa

A teljes projekt-térkép a gyökér [`README.md`](../README.md) fájlban.

### Nyelv: magyar, kódnevek angolul

Minden tartalom magyar nyelvű, de a technikai kifejezések, kódnevek,
függvénynevek, script-paraméterek angolul maradnak (széles körben
használt konvenció).

---

## Wiki-univerzum (milyen oldalak léteznek)

### Fő kategóriák

1. **`concepts/`** — fogalmak, metrikák, módszertan (mit jelent, hogyan kell)
    - statisztikai benchmarkok (HuLU ✅, MMLU-HU ✅, ARC-HU ⏸, GSM8K-HU ⏸, perplexitás ⏸)
    - generatív benchmarkok (HuGME ✅, MT-Bench-HU ✅, szabad kérdéssor ⏸)
    - nyelvészeti mélytesztek (UD Hungarian ✅, morfológia ⏸, szórend ⏸)
    - infrastruktúra (Ollama, LLM-as-a-Judge, DeepEval, prompt formátumok)
    - értékelési módszertan (composite score, aggregáció, statisztikai szignifikancia)

2. **`entities/`** — konkrét dolgok (modellek, adathalmazok, eszközök)
    - modellek (minimax-m3, deepseek-v4-pro/flash, kimi-k2.6, qwen3.5, glm-5.1/5.2, nemotron-3-ultra, gpt-oss-120b/20b, gemini-3-flash, qwen3-next-80b, stb.)
    - benchmark datasetek (HuLU, MMLU-HU, HuGME, UD Hungarian, MT-Bench-HU, stb.)
    - tooling (Ollama szerver, conda env, DeepEval, prompt template-ek)

3. **`comparisons/`** — keresztmetszet-nézetek
    - modell vs. modell (melyik modell hol jobb)
    - benchmark vs. benchmark (melyik mit mér)
    - cloud vs. lokális (költség, minőség, latency tradeoff)

4. **`runbooks/`** — végrehajtható eljárások
    - "Hogyan futtass HuLU-t modell X-en"
    - "Hogyan állítsd be az Ollama klienst"
    - "Hogyan értékeld ki a JSON eredményeket"
    - "Hogyan debuggolj, ha egy modell nem válaszol"

5. **`reports/`** — kész riportok (összesített eredmények)
    - végleges baseline riport (2026-07-14), heatmap-ek, composite CSV
    - státusz riportok, version history, per-sub-task breakdown

### Kötelező fájlok (a wiki gyökerében)

- `index.md` — tartalomkatalógus (minden oldal 1-2 soros összefoglalóval)
- `log.md` — időrendi, append-only napló (ingest, query, frissítés)
- `SCHEMA.md` — ez a fájl (az oldal-univerzum definíciója)
- `overview.md` — magas szintű projekt-összefoglaló (cél, hatókör, fő lépések)

---

## Oldalformátum konvenciók

Minden `.md` fájl frontmatter nélküli, de a tetején kötelező blokk:

```markdown
# [Cím]

*Típus:* [concept | entity | comparison | runbook | report]
*Forrás(ok):* [URL, cikk, YouTube, belső kísérlet]
*Létrehozva:* YYYY-MM-DD
*Frissítve:* YYYY-MM-DD

---

[tartalom]
```

### Tartalmi irányelvek

- **Tömörség:** egy fogalom-oldal 100-300 sor, egy entity-oldal 80-200 sor
- **Példák:** kötelező, legalább 1 konkrét példa fogalom-oldalanként
- **Hivatkozások:** relatív markdown linkek `[Példa: HuLU benchmark](concepts/hulu-benchmark.md) - Rövid leírás`
- **NE használj** `*wikilink*` formátumot (Obsidian-specifikus) — mindig standard markdown linkek
- **Tudományos források:** ahol lehet, peer-reviewed cikket vagy hivatalos doksit linkelj

---

## Karbantartási szabályok

- **Ingest új forráskor:** routing → szintetizálás → index frissítés → log bejegyzés
- **Preserve & extend:** meglévő oldal tartalmát megtartjuk, kiegészítjük; nem írunk felül elveszett információt
- **Ellentmondásjelölés:** ha két forrás mást mond, `> ⚠️ ELENTMONDÁS: ...` blokkban jelöljük
- **Verzió:** a parent `~/.openclaw/` git repo óránként pushol, NE inicializáljunk új git repót

---

## Lint checklist (minden commit előtt)

- [ ] Minden belső link célpontja létezik
- [ ] Nincsenek árva oldalak (amikre senki nem hivatkozik)
- [ ] Nincs 0 soros vagy 1 soros oldal (kivéve ha `_wip_` prefix)
- [ ] `index.md` frissítve, ha új oldal jött létre
- [ ] `log.md`-be bejegyzés az új/fragmentált oldalról

---

## Kapcsolódó

- [Karpathy LLM Wiki Módszer](../llm-wiki/karpathy-llm-wiki-method.md) — az elméleti alap
- [Lokális LLM Wiki Katalógus](../INDEX.md) — a wiki-rendszer egésze
- [Overview](overview.md) — projekt cél, hatókör
- [Index](index.md) — tartalomjegyzék
