# Nyelvészeti mélytesztek — összefoglaló

*Típus:* concept
*Forrás(ok):*
- [Overview](../overview.md) — projekt cél és hatókör
- [UD Hungarian](ud-hungarian.md) — Universal Dependencies magyar treebank
- [Magyar morfológia teszt](morfologia-hu.md) — toldalékolási szabályok
- [Magyar szórend teszt](szorend-hu.md) — fókusz és preverbális pozíció
- [É. Kiss Katalin: Magyar szórend (2002)](https://www.nytud.hu/) — akadémiai szórendleírás
- [Kiefer Ferenc: A magyar morfológia és szintaxis elvei (2016)](https://www.nytud.hu/) — akadémiai kézikönyv
- [NYTK — Nyelvtudományi Intézet](https://www.nytud.hu/) — alapforrás
- [Karpathy LLM Wiki módszer](../../../llm-wiki/karpathy-llm-wiki-method.md) — elméleti háttér

*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## 1. A nyelvészeti dimenzió szerepe a projektben

A [projekt overview](../overview.md) három fő dimenziót definiál a magyar LLM-ek értékelésére:

1. **Statisztikai benchmarkok (40% súly)** — HuLU, MMLU-HU, ARC-HU, GSM8K-HU, perplexitás
2. **Generatív benchmarkok (40% súly)** — HuGME, MT-Bench-HU, szabad kérdéssor
3. **Nyelvészeti mélytesztek (20% súly)** — magyar-specifikus nyelvi kompetencia

Ez az oldal a harmadik dimenziót foglalja össze: miért fontos, milyen tesztekből áll, hogyan számítjuk a kompozit score-t, és mire számíthatunk különböző modellosztályoknál.

### 1.1. Miért van szükség külön nyelvészeti dimenzióra?

A statisztikai benchmarkok (HuLU, MMLU-HU) általános tudást és nyelvi megértést mérnek, de **nem specifikusan a magyar nyelv nyelvtani sajátosságait**. Egy modell, amelyik jól teljesít a HuLU-n, még mindig lehet, hogy:
- rosszul toldalékol („kertban" „kertben" helyett)
- nem kezeli a preverbális fókuszt
- összekeveri a magyar és az angol szórendet

A nyelvészeti mélytesztek ezt a hiányt pótolják: konkrétan a magyar nyelv **nyelvtani rendszerét** tesztelik, és megmutatják, hol „hallatszik", hogy a modell nem anyanyelvi szinten kezeli a magyart.

### 1.2. A magyar nyelv tipológiai háttere

A magyar **agglutináló, szabad szórendű, finnugor nyelv**, számos olyan tulajdonsággal, amelyek ritkák az indoeurópai nyelvekben:

- **Agglutináló morfológia** — egy szó 5-6 toldalékot is viselhet (pl. „házainkban")
- **Magánhangzó-harmónia** — a toldalékok illeszkednek a szó utolsó magánhangzójához
- **Mássalhangzó-illeszkedés** — a toldalékok zöngéssége illeszkedik a szó végéhez
- **Szabad szórend** — a szórend az információfókuszt tükrözi, nem a nyelvtani szerepet
- **Preverbális fókusz** — a fókusz az ige előtti pozícióban áll
- **18+ eset** — a magyar az esetekben gazdag nyelvek közé tartozik (Nom, Acc, Dat, Gen, Ins, Sup, Ine, Ela, Ill, Ade, Abl, All, stb.)
- **Birtokos személyragozás** — a birtokon jelöljük a birtokos személyét és számát is

Ezeket a tulajdonságokat **külön-külön és együttesen** is tesztelni kell, mert a modellek gyakran az egyikben jók, a másikban gyengék.

## 2. A három fő nyelvészeti teszt

A projekt jelenleg három nyelvészeti mélytesztből áll, mindegyik más-más nyelvi jelenséget fed le.

### 2.1. UD Hungarian (mondattan)

Részletek: [ud-hungarian.md](ud-hungarian.md)

- **Forrás:** Universal Dependencies Hungarian treebank (Szeged)
- **Mit mér:** POS tagging, dependency parsing, lemmatizálás
- **Metrikák:** UPOS accuracy, UAS, LAS
- **Méret:** 200-500 mondat (mintavétel a teszt halmazból)
- **Súly a nyelvészeti score-ban:** 33%
- **Fő kihívás:** az agglutináló toldalékok, az esetragozás, a magánhangzó-harmónia hatása a tokenizálásra és a POS-taggingre

### 2.2. Magyar morfológia teszt (200 mondat)

Részletek: [morfologia-hu.md](morfologia-hu.md)

- **Forrás:** egyedi, a projekt által készített 200 mondatos teszt
- **Mit mér:** toldalékolási szabályok (többes szám, birtokos, eset, határozottság, igeragozás, igekötők)
- **Metrika:** token-szintű accuracy
- **Súly a nyelvészeti score-ban:** 33%
- **Fő kihívás:** a magánhangzó-harmónia és a mássalhangzó-illeszkedés rendszerszerű alkalmazása, a ritka szavak toldalékolása

### 2.3. Magyar szórend teszt (100 mondat)

Részletek: [szorend-hu.md](szorend-hu.md)

- **Forrás:** egyedi, a projekt által készített 100 mondatos teszt
- **Mit mér:** topik-fókusz struktúra, preverbális fókusz, kérdő mondatok
- **Metrika:** szórendi döntés pontossága
- **Súly a nyelvészeti score-ban:** 33%
- **Fő kihívás:** az információfókusz felismerése a preverbális pozícióban, a tartalom és a szórend megkülönböztetése

## 3. Kompozit nyelvészeti score

A három teszt eredményéből egyetlen kompozit nyelvészeti score-t számítunk, amely 0-100 közötti skálán mozog.

### 3.1. A score formula

```
linguistic_score = (ud_score × 0.33) + (morph_score × 0.33) + (word_order_score × 0.34)
```

Az egyenlő súlyozás (33-33-34) tükrözi, hogy a három teszt egyenrangúan fontos. A 0.34-es korrekció a kerekítés kompenzálására szolgál, hogy az összeg 1.00 legyen.

### 3.2. A dimenzió súlya a teljes projektben

A nyelvészeti dimenzió a teljes kompozit score 20%-át adja:

```
composite_score = (statistical × 0.40) + (generative × 0.40) + (linguistic × 0.20)
```

A nyelvészeti dimenzió kisebb súlya ellenére fontos: a magyar-specifikus nyelvi hibák (rossz toldalékolás, helytelen szórend) azonnal rontják a felhasználói élményt, míg a statisztikai benchmarkok általános tudást mérnek, és a nyelvi hibák nem mindig jelennek meg bennük.

### 3.3. Értelmezési sávok

A nyelvészeti score a következő sávokba eshet:

| Sáv | Pontszám | Értelmezés |
|-----|----------|------------|
| Natív / near-native | 90-100 | Professzionális szint, magyar anyanyelvi ember szintje |
| Erős | 80-89 | Jól használható, ritka hibákkal |
| Jó | 70-79 | Általános feladatokra megbízható |
| Közepes | 60-69 | Korlátozott, de érthető |
| Gyenge | 50-59 | Sok hiba, gyakran félreérthető |
| Elégtelen | <50 | Csak tájékoztató, nem ajánlott magyar feladatra |

## 4. Melyik modellosztály hogyan teljesít?

A projekt 4-6 modellt hasonlít össze, három fő kategóriában: cloud modellek, nagy lokális modellek, kis lokális modellek. A várakozások az egyes kategóriákra:

### 4.1. Cloud modellek (zárt, nagy)

**Modellek:** minimax-m3, deepseek-v4-pro, kimi-k2.6, gemini-3-flash, qwen3.5:cloud

**Várakozás:** 80-95% a nyelvészeti score-ban.

**Miért:** Ezek a modellek több milliárd token magyar nyelvű szövegen tanultak (a teljes internet magyar tartalmán), és a finomhangolás során is erős magyar visszajelzést kaptak. Az explicit magyar specifikus tanító adatok (UD Hungarian, NYTK anyagok) valószínűleg részei a corpusnak.

**Tipikus erősségek:** jól kezelik a magánhangzó-harmóniát gyakori szavaknál, felismerik a preverbális fókuszt, a tipikus szórendi mintákat.

**Tipikus gyengeségek:** ritka szavak toldalékolása (alacsony gyakoriságú nevek, szakszavak), nyelvjárási sajátosságok (pl. „-nak/-nek" helyett „-nok/-nek" palóc).

### 4.2. Nagy lokális modellek (30B+ paraméter, magyar fine-tune)

**Modellek:** nincs jelenleg a poolban, de potenciálisan ilyen modellek lennének (pl. PULI-GPT-2, GPT-Sw3-356M magyar verzió)

**Várakozás:** 70-85% a nyelvészeti score-ban.

**Miért:** Ezeket kifejezetten magyar nyelvű fine-tune-olták, és a magyar specifikus nyelvtani szabályokat jobban internalizálták. Viszont a modellméret kisebb, mint a cloud modelleknél, és a ritka szavak kezelése gyengébb.

**Tipikus erősségek:** a magyar nyelvtani rendszer jobb internalizálása (magánhangzó-harmónia, birtokos személyragozás), kulturálisan konzisztens szövegek.

**Tipikus gyengeségek:** ritka szavak, regionális változatok, összetett mondatok.

### 4.3. Kis lokális modellek (< 10B paraméter)

**Modellek:** qwen3.5:0.8b, qwen3.5:2b, qwen3.5:4b

**Várakozás:** 40-65% a nyelvészeti score-ban.

**Miért:** Ezek a modellek kicsik, és bár támogatják a magyart (multilingual tanítás), a magyar nyelvre eső paraméter-kapacitás korlátozott. A magyar nyelvtani szabályok internalizálása részleges.

**Tipikus erősségek:** gyakori szavak toldalékolása, általános szórend (SVO), egyszerű mondatok.

**Tipikus gyengeségek:** ritka szavak, összetett mondatok, fókusz, birtokos személyragozás, magánhangzó-harmónia ritka szavaknál.

### 4.4. A várt sorrend

A várakozás szerint a sorrend a nyelvészeti score-ban:

1. **Nagy cloud modellek (qwen3.5:397b, deepseek-v4-pro):** ~90%
2. **Közepes cloud modellek (kimi-k2.6, gemini-3-flash):** ~80-85%
3. **Kis cloud modellek (minimax-m3, mini verziók):** ~70-80%
4. **Magyar fine-tune-olt lokális nagy modellek:** ~75-85%
5. **Kis lokális modellek (qwen3.5:0.8b, 2b, 4b):** ~40-65%

A sorrend a modellmérettől és a magyar specifikus tanítástól függ. A magyar fine-tune-olt közepes modellek meglephetnek: ha elég specifikus a finomhangolás, akár a cloud modelleket is megközelíthetik.

## 5. Magyar-specifikus buktatók a nem-magyar modelleknek

A nem-magyar anyanyelvű (vagy nem kifejezetten magyarra optimalizált) modellek számos specifikus buktatóval szembesülnek. Ezeket a tesztek explicit mérik, de itt összegyűjtjük a leggyakoribb hibákat:

### 5.1. Toldalékolási hibák

- **Magánhangzó-harmónia figyelmen kívül hagyása:** „kertban" „kertben" helyett, „asztalben" „asztalban" helyett
- **Mássalhangzó-illeszkedés kihagyása:** „nagyval" „naggyal" helyett, „kézszel" „kézzel" helyett
- **Birtokos személyragozás kihagyása:** „a macska" „a macskám" helyett, „a ház" „a házunk" helyett
- **Többes szám és eset összekeverése:** „a házaknak" „a házakba" helyett

### 5.2. Szórendi hibák

- **Angol SVO merev alkalmazása:** „A fiút látja a lány" (szórendileg helyes, de a fókusz nem az, amit a magyar beszélő vár)
- **A preverbális fókusz figyelmen kívül hagyása:** „A lány a könyvet olvassa" „A könyvet olvassa a lány" helyett (utóbbi jelöli, hogy a könyvet olvassa, nem mást)
- **Az igekötő szétszakítása:** „Elmegy akarok" „El akarok menni" helyett (helytelen, az igekötőt nem szabad elválasztani az igétől preverbálisan)

### 5.3. Morfológiai túláltalánosítás

- **Angol analógia szerinti ragozás:** „olvastam" „olvastam" (helyes!), de „látottam" „látottam" helyett „látom" (helyes, de a modell néha a birtokos ragozást keveri)
- **Többes szám túlzott alkalmazása:** „információk" „információ" helyett (az utóbbi is helyes, többes szám nélkül)
- **Esetragok rossz alkalmazása:** „Szeretem a magyar nyelvet" (helyes) vs. „Szeretem magyar nyelv" (a modell kihagyja a tárgyeseti -t toldalékot)

### 5.4. Szintaktikai hibák

- **A határozott tárgyas ragozás kihagyása:** „Látom a macskát" (helyes) vs. „Látom a macska" (a modell kihagyja a tárgyeset -t toldalékot)
- **A birtokos szerkezet rossz kezelése:** „Péter könyve" (helyes) vs. „Péter könyv" (a modell kihagyja a birtokos -e toldalékot)
- **Az igei prefixumok és igekötők összekeverése:** „megnéz" (ige + igekötő) vs. „meg néz" (két külön szó, helytelen)

### 5.5. Lexikai-szemantikai hibák

- **Hamis barátok (false friends):** A magyar és az angol között vannak hasonló szavak, de más jelentéssel. Pl. „actual" (angol: tényleges) vs. „aktuális" (magyar: időszerű). A modell néha az angol jelentést alkalmazza.
- **Kulturális referenciák hiánya:** a magyar kulturális kontextust (pl. „56-os forradalom", „gólya", „Kossuth-díj") a modell néha nem ismeri.

## 6. Hogyan illeszkedik ez a projekt nagyobb képébe?

A nyelvészeti mélytesztek a projekt „diagnosztikus" rétegét alkotják: míg a statisztikai és generatív benchmarkok azt mondják meg, *mennyire jó* a modell, a nyelvészeti tesztek azt mondják meg, *milyen hibái vannak*. A projekt riportjai mindkettőt bemutatják:

- **Összesített score** (0-100) — a három dimenzió súlyozott átlaga
- **Dimenziónkénti bontás** — statisztikai / generatív / nyelvészeti
- **Nyelvészeti bontás** — UD / morfológia / szórend
- **Modellenkénti profil** — minden modellhez egy „nyelvészeti profil", ami megmutatja, hol erős és hol gyenge

Ez a részletes bontás segít a felhasználónak eldönteni, melyik modellt használja milyen feladatra. Ha a felhasználó magyar nyelvű, formális szöveget ír (pl. jogi dokumentum), akkor a magas morfológiai score fontos. Ha kreatív szöveget ír (pl. irodalmi), akkor a szórendi score fontos. Ha chatbotot fejleszt, akkor a teljes nyelvészeti profil releváns.

## 7. Jövőbeli bővítések

A projekt tervei között szerepel a nyelvészeti tesztek bővítése:

- **Helyesírási teszt** — a magyar helyesírás szabályainak ismerete (pl. „ly" vs. „j", „sz" vs. „s")
- **Stilisztikai teszt** — a modell képes-e stílust váltani (formális ↔ informális)
- **Párbeszéd-pragmatikai teszt** — a modell kezeli-e a köszönést, a megszólítást, a társalgási maximákat
- **Diszkurz-pragmatikai teszt** — a modell kezeli-e a szövegkohéziót, a koreferenciát, a deixist
- **Nyelvjárási teszt** — a modell felismeri-e a magyar nyelvjárásokat (pl. palóc, székely)

Ezek a bővítések a későbbi fázisokban (Q3-Q4 2026) kerülnek kidolgozásra.

## 8. Kapcsolódó

- [Overview](../overview.md) — projekt cél, hatókör, fő lépések
- [SCHEMA](../SCHEMA.md) — wiki-formátum és oldal-univerzum
- [UD Hungarian teszt](ud-hungarian.md) — Universal Dependencies, POS, dependency parsing
- [Magyar morfológia teszt](morfologia-hu.md) — toldalékolási szabályok
- [Magyar szórend teszt](szorend-hu.md) — fókusz, preverbális pozíció
- [Karpathy LLM Wiki módszer](../../../llm-wiki/karpathy-llm-wiki-method.md) — elméleti háttér
- [NYTK — Nyelvtudományi Intézet](https://www.nytud.hu/) — alapvető magyar nyelvészeti forrás
- [Universal Dependencies](https://universaldependencies.org/) — nemzetközi projekt
