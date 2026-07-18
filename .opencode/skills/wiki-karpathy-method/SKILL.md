---
name: wiki-karpathy-method
description: Use when creating, editing, or maintaining wiki pages in this repo (the wiki/ folder). Encodes the Karpathy LLM Wiki method (three-layer architecture, four operations, preserve-and-extend) plus the hu-eval wiki conventions (SCHEMA.md, mandatory page header, index/log updates, no Obsidian wikilinks). Load automatically for any wiki writing task.
---

# Karpathy LLM Wiki Method — hu-eval

Ezt a módszert KÖTELEZŐ használni minden `wiki/` mappában lévő oldal írásakor,
szerkesztésekor vagy létrehozásakor. Az elméleti alap a Karpathy LLM Wiki
módszer (forrás: `karpathy-llm-wiki-method` gist); a repo-specifikus szabályok a
`wiki/SCHEMA.md`-ből származnak (az az igazság, ha ez a fájl elavulna).

## Alapötlet

A wiki egy **tartós, kamatozó tudásartefaktum**, nem statikus dokumentáció. Az
LLM növekvő módon építi és fenntartja: új forrás ingest-kor nem csak indexel,
hanem olvassa, kinyeri a lényeget, és integrálja a meglévő wikibe. Minden új
forrással a wiki gazdagodik — a kereszthivatkozások, ellentmondás-jelölések és
szintézis már adva vannak a következő kérdésnél.

## Háromrétegű architektúra

1. **Nyers források (nem módosítható)** — cikkek, tanulmányok, adatfájlok. Az
   LLM olvassa, de SOHA nem írja át. Ez az igazság forrása.
2. **A wiki (LLM által fenntartott)** — markdown fájlok könyvtára, egy oldal
   konceptusonként. Az LLM birtokolja: létrehoz, frissít, kereszthivatkozást
   tart fenn. Ember olvassa, LLM írja.
   - `index.md` — tartalomkatalógus
   - `log.md` — időrendi, append-only napló (ingest, query, lint)
3. **Séma (irányítás)** — `wiki/SCHEMA.md` határozza meg az oldal-univerzumot.
   Ez az egyetlen dolog, amit embernek kell kezelnie; az LLM végrehajtja.

## Négy alapművelet

- **Init** — könyvtárstruktúra létrehozása a sémából (egyszeri).
- **Ingest** (a kamatozás motorja) — új forrás hozzáadásakor:
  1. Forrás feloldása (fájl / URL → szöveg)
  2. Útválasztás (route): mely wiki-oldalak relevánsak
  3. Szintetizálás: meglévő oldal + új forrás alapján átírás, minden eddigi
     tudás MEGTARTÁSÁVAL
  4. Embedding frissítése (opcionális)
  5. `index.md` + `log.md` frissítése
- **Query** — releváns oldalak keresése, kontextus összeállítása, válasz
  szintézise forráshivatkozásokkal. Ha a válasz értékes új tudás, wiki-oldalként
  menthető (a kamatozási hurok).
- **Lint** — egészségügyi ellenőrzés: árva oldalak, hiányzó oldalak, törött
  hivatkozások, ellentmondások, lejárt embedding-ek.

**Kulcsinvariáns:** *"Preserve and extend existing content — never discard
information already on the page."* Meglévő tartalmat MEGTARTJUK és kiegészítjük;
nem írunk felül elveszett információt.

## Oldal-univerzum (hova tedd az új oldalt)

- `concepts/` — fogalmak, metrikák, módszertan
- `entities/` — konkrét dolgok: modellek, adathalmazok, eszközök
- `comparisons/` — keresztmetszet-nézetek (modell vs. modell, benchmark vs. benchmark)
- `runbooks/` — végrehajtható eljárások ("hogyan csináld")
- `reports/` — kész riportok (összesített eredmények, státusz)

Gyökérkötelező fájlok: `index.md`, `log.md`, `SCHEMA.md`, `overview.md`.

## Kötelező oldal-fejléc (minden .md teteje, NINCS YAML frontmatter)

```markdown
# [Cím]

*Típus:* [concept | entity | comparison | runbook | report]
*Forrás(ok):* [URL, cikk, YouTube, belső kísérlet]
*Létrehozva:* YYYY-MM-DD
*Frissítve:* YYYY-MM-DD

---

[tartalom]
```

## Írási szabályok

- **Nyelv:** magyar a szöveg, angol a technikai kifejezések/kódnevek/függvények.
- **Tömörség:** concept-oldal 100-300 sor, entity-oldal 80-200 sor.
- **Példák:** fogalom-oldalanként kötelező legalább 1 konkrét példa.
- **Linkek:** mindig standard relatív markdown link (`[HuLU](concepts/hulu-benchmark.md) - Rövid leírás`).
  **NE használj `*wikilink*` (Obsidian) formátumot!** Ez a leggyakoribb hiba.
- **Források:** tudományos/hivatalos forrást linkelj, ahol lehet.
- **Ellentmondás:** ha két forrás mást mond, `> ⚠️ ELLENTMONDÁS: ...` blokkban jelöljük.

## Karbantartási szabályok (commit előtti lint checklist)

- [ ] minden belső link célpontja létezik (nincs törött hivatkozás)
- [ ] nincs árva oldal (amire senki nem hivatkozik)
- [ ] nincs hiányzó oldal a séma szerint
- [ ] nincs 0- vagy 1-soros oldal (kivéve `_wip_` prefix)
- [ ] `index.md` frissítve, ha új oldal született
- [ ] `log.md`-be bejegyzés az új/fragmentált oldalról
- [ ] preserve & extend: meglévő oldal tartalma nem veszett el

## Git-figyelmeztetés

A `wiki/` egy meglévő git repo (`github.com/zsoltii/hu-eval.git`) alkönyvtára.
**NE futtass `git init`-et** a wiki mappában — a parent repo kezeli a
verziókezelést. (SCHEMA.md régebbi megjegyzése, miszerint a parent
`~/.openclaw/` pushol, már NEM érvényes — ez a repo az `hu-eval` gyökér.)

## Hol nézz utána, mielőtt írsz

- `wiki/SCHEMA.md` — az oldal-univerzum és formátum kanonikus definíciója
- `wiki/index.md` — katalógus, ne duplikálj meglévő oldalt
- `wiki/log.md` — mi változott, mik a friss tények
