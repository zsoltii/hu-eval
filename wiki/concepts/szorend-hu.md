# Magyar szórend — Deep Test (100 mondatos egyedi teszt)

*Típus:* concept
*Forrás(ok):*
- [É. Kiss Katalin: Magyar szórend (1992, 2002)](https://www.nytud.hu/cikkek.html) — az akadémiai szórendleírás alapműve
- [É. Kiss Katalin: The Hungarian language (2017)](https://akkrt.hu/1046-hungarian-language-hungarian-grammars) — angol nyelvű összefoglaló
- [Kiefer Ferenc: A magyar morfológia és szintaxis elvei (2016)](https://www.nytud.hu/) — akadémiai kézikönyv
- [Alberti Gábor & Medve Anna: Szórendi sajátosságok a magyarban](https://www.nytud.hu/) — NYTK kiadvány
- [Hungarian language — Wikipedia (Word order)](https://en.wikipedia.org/wiki/Hungarian_language#Word_order) — áttekintés
- [Surányi Balázs: Hungarian verbal prefixes and word order (2014)](https://akjournals.com/view/journals/000/53/1-2/article-p113.xml) — igei prefixumok és szórend

*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## 1. A magyar szórend sajátosságai

A magyar **szabad szórendű nyelv**: a szavak sorrendje rugalmas, és az információ-fókusz és a topik-komment struktúra határozza meg, nem a nyelvtani szerep. Ez alapvetően különbözik az angoltól (SVO, kötött sorrend) vagy a némettől (SOV, kissé rugalmas, de a szórend kötöttebb).

### 1.1. Az alapvető minta: SVO

A semleges, semleges információeloszlású mondatok SVO (Subject-Verb-Object) sorrendben állnak:
- „A lány látja a fiút." (A lány = alany, látja = ige, a fiút = tárgy)
- „A kutya ugatja a macskát." (A kutya = alany, ugatja = ige, a macskát = tárgy)

### 1.2. A fókusz (focus) pozíciója

A magyarban az **ige előtti pozíció** a fókusz helye. A fókusz az az információ, amit a mondat hangsúlyoz, és amire a hallgató figyelmét felhívják. Példa:

- „A MACSKA ül az asztalon." → fókusz: a macska (nem a kutya, nem a nyúl)
- „A macska AZ ASZTALON ül." → fókusz: az asztalon (nem a széken, nem a földön)
- „A macska az asztalon ÜL." → fókusz: ül (nem alszik, nem játszik)

A fókuszt hangsúly is jelöli (proszódia), de a szórend is.

### 1.3. A topik (topic) pozíciója

A topik a mondat elején áll, és a „miről szól a mondat" kérdésre ad választ. A topik tipikusan a magyarban is a mondat elején van (akárcsak az alany), de nem feltétlenül azonos vele:

- „A macskáról azt mondtam, hogy okos." → topik: a macska, komment: azt mondtam, hogy okos
- „Az asztalon van a könyv." → topik: az asztal, a könyv a kommentben van

## 2. A 100 mondatos szórend-teszt

### 2.1. Méret és összetétel

A teszt 100 mondatból áll, négy nagy kategóriában:

| Kategória | Mondatok száma | Súly a score-ban |
|-----------|----------------|-------------------|
| Topik-fókusz struktúra felismerése | 35 | 35% |
| Preverbális fókusz azonosítása | 30 | 30% |
| Szórendi variációk (inverzió, topik-prominencia) | 20 | 20% |
| Kérdő mondatok szórendje | 15 | 15% |

### 2.2. Értékelési módszer

A modellnek minden mondatpárra (vagy trióra) el kell döntenie, hogy a két mondat közti különbség csak a szórendben van-e, vagy tartalmi különbség is. Ezenkívül a modellnek képesnek kell lennie arra is, hogy egy adott jelentést (fókuszt) generáljon a megfelelő szórenddel.

Pontszámítás: `helyes_szórendi_döntés / összes_döntés × 100%`.

### 2.3. Prompt-formátum

A modell a következő promptot kapja:

```
Feladat: Döntsd el, hogy a két magyar mondat közti különbség
csak a szórendben rejlik-e (ugyanaz a jelentés, csak más hangsúly),
vagy tartalmi különbség is van!

Válasz: "SZÓREND" vagy "TARTALOM" + 1-2 mondatos indoklás.

1. mondat: "{sentence1}"
2. mondat: "{sentence2}"
```

## 3. 10 minimális szórendi pár

Az alábbiakban 10 minimális párt mutatunk be, amelyek a szórend fontosságát illusztrálják. Minden párban azonos szavak, csak más sorrendben — de a **jelentés** más a fókusz-kiemelés miatt.

### 3.1. Pár 1: Alany-tárgy fókusz

- (a) „A macska ül az asztalon." — fókusz: a macska
- (b) „Az asztalon ül a macska." — fókusz: az asztalon

Mindkét mondat azt jelenti, hogy van egy macska és van egy asztal, és a macska rajta ül. De az (a) verzió hangsúlyozza, hogy **a macska** van ott (szemben valami mással); a (b) verzió hangsúlyozza, hogy **az asztalon** van (szemben valami más hellyel). A fókusz az ige előtti pozícióban van.

### 3.2. Pár 2: Tárgy fókuszban

- (a) „A diák olvassa a könyvet." — fókusz: a diák (vagy semleges)
- (b) „A könyvet olvassa a diák." — fókusz: a könyvet

A (b) mondatban a „könyvet" preverbálisan áll, így ez a fókusz: a hangsúly azon van, hogy **a könyvet** olvassa a diák (nem a folyóiratot, nem az újságot). A szórend megváltoztatásával a fókusz is eltolódik.

### 3.3. Pár 3: Határozó fókuszban

- (a) „Holnap utazunk Párizsba." — fókusz: holnap
- (b) „Párizsba utazunk holnap." — fókusz: Párizsba

A (b) mondat hangsúlyozza, hogy **Párizsba** megyünk (nem Londonba, nem Rómába). A (a) hangsúlyozza, hogy **holnap** (nem ma, nem jövő héten). Mindkettő helyes magyar mondat, csak más az információfókusz.

### 3.4. Pár 4: Kérdő mondat

- (a) „Mit csinálsz?" — Mit csinálsz? (általános)
- (b) „Te mit csinálsz?" — Te mit csinálsz? (fókusz: te, nem másvalaki)

A (b) mondatban a „te" preverbálisan áll, és fókuszként funkcionál. A válasz implikáltan: „Én csinálom" — szemben azzal, hogy „Más csinálja".

### 3.5. Pár 5: Összetett ige (ige + ige)

- (a) „El akarok menni." — fókusz: el (vagy semleges)
- (b) „Menni akarok el." — ez a mondat nem helyes magyarul (az igekötő nem kerülhet az ige mögé preverbálisan)

A magyarban az igekötő (pl. „el-", „meg-", „fel-") közvetlenül az ige előtt áll, nem szétválasztható tőle, ha az ige preverbális fókuszban van. Ez a szabály nagyon erős.

### 3.6. Pár 6: Birtokos szerkezet

- (a) „A lánynak a könyve." — fókusz: a lánynak (birtokos)
- (b) „A könyve a lánynak." — kissé más, hangsúlyosabb

Mindkét mondat azt jelenti, hogy a lányé a könyv. A (b) hangsúlyosabb, a „könyve" preverbálisan áll, de ilyenkor a birtokos (a lánynak) a mondat végére kerül.

### 3.7. Pár 7: Idő-határozó

- (a) „Tegnap találkoztam Péterrel." — semleges
- (b) „Péterrel találkoztam tegnap." — fókusz: Péterrel

A (b) mondatban a „Péterrel" preverbálisan áll, és a fókusz rajta van (nem másvalakivel találkoztam).

### 3.8. Pár 8: Eszköz-határozó

- (a) „Tollal írok." — semleges
- (b) „Tollal írok, nem ceruzával." — kontrasztív fókusz

A (b) mondat a kontrasztív fókusz példája: a „tollal" + „nem ceruzával" szerkezet explicit kontrasztot jelez.

### 3.9. Pár 9: Hely-határozó

- (a) „A kertben játszanak a gyerekek." — semleges
- (b) „A gyerekek játszanak a kertben." — fókusz: a gyerekek (vagy a kertben)

Mindkét mondat helyes. Az (a) mondat hangsúlyozhatja, hogy **a kertben** (nem az utcán, nem a házban); a (b) hangsúlyozhatja, hogy **a gyerekek** (nem a felnőttek).

### 3.10. Pár 10: Negatív mondat

- (a) „Nem PÉTER jött el." — fókusz: Péter (negatív)
- (b) „PÉTER nem jött el." — fókusz: Péter, de a tagadás az igére vonatkozik

Mindkét mondat negatív, de a fókusz és a tagadás fókusza más. A (a) mondat azt jelenti, hogy valaki más jött el (nem Péter). A (b) mondat azt jelenti, hogy Péter nem jött el (talán más igen).

## 4. A preverbális fókusz szabályai

### 4.1. Mi kerülhet a preverbális pozícióba?

A magyar preverbális (ige előtti) pozícióba sokféle elem kerülhet:
- **Tárgy** (accusativusi): „A könyvet olvassa a diák."
- **Határozó** (bármilyen): „Tegnap olvasta el a könyvet."
- **Alany** (ritkábban, kontrasztív): „A DIÁK olvassa a könyvet." (szemben a tanár)
- **Birtokos** (ritkábban): „A lánynak adtam a könyvet."

### 4.2. Mi nem kerülhet a preverbális pozícióba?

- **Az ige maga**: „olvassa a diák a könyvet" — helytelen, az ige nem állhat mondat-elején hangsúlytalanul
- **A névelő önmagában**: „A a macska alszik." — helytelen
- **A segédige (copula) önmagában**: „Van a macska." — ez állhat, de itt a „van" az ige, nem a segédige

### 4.3. A fókusz és a prozódia

A fókuszt hangsúly is jelöli. A „A macska ÜL az asztalon" mondatban az „ül" szónak van hangsúlya (fókusz), míg a „A macska ül az ASZTALON" mondatban az „asztalon"-nak. A szórend önmagában is jelöli a fókuszt, de a hangsúly is. A modellnek mindkettőt kell(ene) kezelnie.

## 5. A szórendi teszt értékelése

### 5.1. Token-szintű értékelés

Minden szórend-variációra 1 pont, ha helyes, 0 pont, ha helytelen. A végső score:

`word_order_score = helyes_döntések / összes_döntés × 100%`

### 5.2. Kategóriánkénti riport

A teszt kategóriánkénti bontásban is riportol:

```
Word order score: 71.5%
  Topik-fókusz felismerés: 78.2%
  Preverbális fókusz:        69.1%
  Inverzió és topik:         70.0%
  Kérdő mondatok:            65.5%
```

### 5.3. A nehézségi szint

A magyar szórend az egyik legnehezebb nyelvi jelenség a magyarul nem beszélő modelleknek. Az angol „SVO" sémát internalizáló modellek gyakran rosszul kezelik a preverbális fókuszt. A magyar LLM-ek (mint a Puli, a GPT-Sw3 magyar verziója, vagy a magyar fine-tune-olt Mistral) itt jobban teljesítenek, míg a tisztán angol-centrikus modellek (pl. Llama-2/3 alapúak) gyakran alulteljesítenek.

## 6. A szórendi teszt korlátai

### 6.1. A fókusz prozódiai jellege

A fókuszt a hangsúly is jelöli, nem csak a szórend. Egy modell, amelyik nem generál hangot, csak szöveget, a prozódiai információt elveszíti. A teszt ezért a szöveges reprezentációra korlátozódik, és nem méri a tényleges kiejtést.

### 6.2. A kontextus függősége

Egy mondat fókusza erősen kontextusfüggő. „A macska ül az asztalon" mondható válaszként „Mi van az asztalon?" kérdésre (fókusz: a macska) vagy „Mit csinál a macska?" kérdésre (fókusz: ül). A teszt nem mindig tudja visszaadni ezt a kontextust, és ez torzítást okozhat.

### 6.3. A minimális párok korlátai

Egyes minimális párok (pl. „Pár 4: Kérdő mondat") esetén a tartalmi és szórendi különbség nem teljesen független: a „te" névmás preverbális pozíciója egyben pragmatikai információt is hordoz. A modell, amelyik túl szigorúan „csak szórend" választ ad, hibázhat.

## 7. Miért fontos ez a projekt számára?

A magyar szórend az egyik legmarkánsabb nyelvi sajtosság, amely megkülönbözteti a magyart az indoeurópai nyelvektől. Egy LLM, amelyik nem kezeli jól a szórendet, a magyar beszélők számára „idegenesen" hangzik, még akkor is, ha a szavak és a toldalékok helyesek.

A szórendi teszt a kompozit nyelvészeti score egyik fontos komponense (lásd [Nyelvészeti összefoglaló](nyelveszeti-osszefoglalo.md)). A cél, hogy a modell:
- felismerje a fókuszt a preverbális pozícióból
- generáljon helyes szórendet a fókusz jelölésére
- kezelje a kérdő mondatok speciális szórendjét
- értse a topik-komment struktúrát

## 8. Kapcsolódó

- [Overview](../overview.md) — projekt cél és hatókör
- [SCHEMA](../SCHEMA.md) — wiki-formátum
- [UD Hungarian teszt](ud-hungarian.md) — kiegészítő mondattani teszt
- [Magyar morfológia teszt](morfologia-hu.md) — toldalékolási szabályok
- [Nyelvészeti összefoglaló](nyelveszeti-osszefoglalo.md) — az összes nyelvészeti teszt együtt
- [Karpathy LLM Wiki módszer](../../../llm-wiki/karpathy-llm-wiki-method.md) — elméleti háttér
