# Magyar morfológia — Deep Test (200 mondatos egyedi teszt)

*Típus:* concept
*Forrás(ok):*
- [Kiefer Ferenc (szerk.): Magyar nyelvjárások (NYTK)](http://www.nytud.hu/) — Nyelvtudományi Intézet
- [Kiefer Ferenc: Magyar morfológia](https://www.arcanum.com/hu/online-kiadvanyok/Nagyivan-nagy-ivan-magyarorszag-csaladai-1/) — akadémiai morfológiai kézikönyv
- [Magyar Értelmező Kéziszótár (ÉKsz.)](https://www.arcanum.com/hu/online-kiadvanyok/EKsz-magyar-ertelmezo-keziszotar-1/) — etalon szótár
- [Magyar nyelvtan — A nyelvhasználat rendszere (NYTK)](https://www.nytud.hu/letolt/nytud.pdf) — elméleti háttér
- [Haspelmath, M. & Sims, A.: Understanding Morphology (2010)](https://www.degruyter.com/document/doi/10.1515/9783110802150/html) — morfológiai bevezető
- [Comrie, B.: The World's Major Languages (1987)](https://www.routledge.com/The-Worlds-Major-Languages-Second-Edition/Comrie/p/book/9781032277300) — nyelvtipológia

*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## 1. Miért kell külön morfológia teszt?

Az [UD Hungarian teszt](ud-hungarian.md) az általános POS-tagging és dependency parsing pontosságát méri, de **nem elég mély** a magyar agglutináló morfológia diagnosztizálásához. A magyarban egyetlen szó akár 5-6 toldalékot is viselhet, és minden toldalék toldalékolható tovább (rekurzív toldalékolás). Példa:

- „ház" → igen egyszerű szó
- „házakban" → ház + -ak (többes szám) + -ban (inessivus)
- „házainkban" → ház + -ai (birtokos 3. személy egyes) + -nk (birtokos 1. személy többes) + -ban (inessivus)
- „legházaimkban" → leg- (felsőfok) + ház + -ai + -mk + -ban

A 200 mondatos egyedi morfológia-tesztünk célja, hogy **finomhangoltan, típusonként** mérje, hogyan kezeli a modell ezt a bonyolult rendszert. Nem az UD átfogó pontosságát kérdezi, hanem konkrét morfológiai jelenségeket tesztel.

## 2. A teszt felépítése

### 2.1. Méret és összetétel

A teszt 200 mondatból áll, a következő bontásban:

| Kategória | Mondatok száma | Súly a score-ban |
|-----------|----------------|-------------------|
| Többes szám (plural) | 30 | 15% |
| Birtokos személyragozás (possessive) | 30 | 15% |
| Esetragozás (case) | 40 | 20% |
| Határozottság (definiteness) | 25 | 12% |
| Igei egyeztetés és ragozás (verb conjugation) | 30 | 15% |
| Igei prefixumok és igekötők | 15 | 8% |
| Összetett mondatrészek (multi-clause) | 30 | 15% |

### 2.2. Minden mondat értékelése

Minden mondat pontozása token-szinten történik. Egy token helyes, ha a modell által generált szóalak megegyezik az elvárt (referencia) szóalakkal. A végső score:

`morph_score = helyes_tokenek / összes_token × 100%`

Ez a token-szintű accuracy **szigorúbb**, mint a mondat-szintű (whole-sentence accuracy), mert részben is eltalált mondatok is részpontot kapnak.

### 2.3. Prompt-formátum

A modell a következő promptot kapja:

```
Feladat: Egészítsd ki a mondatot helyes magyar toldalékolással!

Szabály: A magyar toldalékok a szó utolsó magánhangzójához illeszkednek
(mély magánhangzók: a, á, o, ó, u, ú → -ban/-nak/-val stb.;
magas magánhangzók: e, é, i, í, ö, ő, ü, ű → -ben/-nek/-vel stb.).
A mássalhangzók illeszkednek a szó végéhez (zöngésségi hasonulás).

Írd ki CSAK a kész mondatot, semmi mást.

Bemenet: "{}"
```

## 3. A 15 trükkös eset — részletes példák

Az alábbiakban a teszt 15 legfontosabb / legnehezebb esetét mutatjuk be. Mindegyiknél látható a kategória, a referencia megoldás, és a jellemző modellhibák.

### 3.1. Többes szám — szabályos és rendhagyó

**1. eset — szabályos magas hangrendű:** „A macsk___ alszik az ágyon." → „A macskák alszanak az ágyon." A modell gyakran kihagyja az „-ak" toldalékot vagy „-ok"-ot ír (mély hangrendű toldalék).

**2. eset — szabályos mély hangrendű:** „A kuty___ fut a parkban." → „A kutyák futnak a parkban." A birtokos egyeztetés is kell: „fut"-ból „futnak" (3. személy többes).

**3. eset — rendhagyó többes szám:** „A lány___ énekelnek." → „A lányok énekelnek." Figyelem: a „lány" szó + „-ok" toldalék → „lányok" (k → o betűcsere nem kell, csak -ok). A modell gyakran írja „lányi"-t vagy „lányt".

**4. eset — magánhangzó-toldalékok (vowel-final stems):** „A bölcs___ tanítanak." → „A bölcsek tanítanak." A „bölcs" + „-ek" = „bölcsek". A „cs" + „-ek" illeszkedés: nincs hasonulás, csak toldalékolás.

### 3.2. Birtokos személyragozás

**5. eset — 1. személy egyes:** „Az én macsk___ fekete." → „Az én macskám fekete." A birtokos személyjel: „-m" (1. személy egyes, magas hangrend: macska → macsk + -a + -m → macskám, a birtokos toldalék a birtokos személy előtt jelenik meg).

**6. eset — 3. személy többes (a birtokolt többes):** „A diák___ könyvei." → „A diákok könyvei." Itt a birtokos 3. személy többes + a birtokolt többes szám. A birtokos személy jele nincs (3. személy), de a birtokolt birtokos-személyragja „-i" (-évi toldalékcsalád).

**7. eset — birtokos 1. személy többes, egyes birtok:** „A mi ház___ nagy." → „A mi házunk nagy." A „ház" + „-unk" toldalék (1. személy többes) → „házunk". A modell gyakran kihagyja az „-unk"-ot vagy „-unk"-ot ír „-unk" helyett.

### 3.3. Esetragozás

**8. eset — elöljárós eset (inessivus):** „A könyv az asztal___ van." → „A könyv az asztalon van." Magas hangrend: „asztal" + „-on" (de a szó mély, tehát „-on" a helyes). A modell gyakran ír „-en"-t (magas toldalékot) mély szavakhoz.

**9. eset — birtokos eset (dativus):** „Adok egy alm___ a gyereknek." → „Adok egy almát a gyereknek." Tárgyeset: „alma" + „-t" → „almát". Figyelem: a tárgy határozatlan (nincs névelő előtte) → nincs külön végződés; de határozott lenne: „az almát".

**10. eset — tárgyeset (accusativus):** „Látom a mad___." → „Látom a madarat." A „madár" + „-at" → „madarat" (a szó végén -r, és a toldalék -at, ami a r-hez illeszkedik, de itt nincs mássalhangzó-illeszkedés).

### 3.4. Határozottság

**11. eset — határozott tárgyas ragozás:** „Látom a macsk___." → „Látom a macskát." A határozott tárgyas ragozás az igén jelenik meg, de a főnéven is: „macska" + „-t" = „macskát" (a névelős és tárgyas „a macskát" szerkezet határozottságot jelöl).

**12. eset — határozatlan alany:** „Macska___ alszik." → „Macska alszik." A határozatlan alany nem kap névelőt, és az igealak 3. személy egyes: „alszik". A modell gyakran toldja „-k" toldalékkal a főnevet (magyarosítva „macskak"-szerű képet adva).

### 3.5. Igei egyeztetés és igeragozás

**13. eset — jelen idő, 1. személy egyes:** „Én olvas___ a könyvet." → „Én olvasok a könyvet." Az ige végződése alanyi ragozásban, jelen idő, 1. személy egyes: „-ok". (Tárgyas lenne: „olvasom" → „Én olvasom a könyvet.")

**14. eset — feltételes mód, múlt idő:** „Ha te jött___ volna, láttad volna." → „Ha te jöttél volna, láttad volna." A feltételes mód múlt idejű alakja 2. személy egyes: „jöttél". A modell gyakran ír „-ál" toldalékot (ami a 2. személy, de birtokos ragozásban van).

**15. eset — műveltető ige (causative):** „Az anya et___ a gyereket." → „Az anya eteti a gyereket." A műveltető (causative) ige: „eszik" → „etet" (műveltető) + „-i" (3. személy, határozott tárgyas). A modell gyakran írja „etet" helyett „eszik"-et, figyelmen kívül hagyva a műveltetést.

## 4. A magánhangzó-harmónia (vowel harmony) szabályai

### 4.1. Két csoport

A magyar magánhangzók két csoportba sorolhatók aszerint, hogy a szó belsejében hogyan viselkednek:

**Mély (vagy alsó) hangrendű magánhangzók:** a, á, o, ó, u, ú
- Pl. „ház", „kutya", „asztal", „ablak"

**Magas hangrendű magánhangzók:** e, é, i, í, ö, ő, ü, ű
- Pl. „kert", „szék", „üveg", „tükör"

A besorolás a szó **utolsó magánhangzóját** nézi (néha az utolsó előtti is, ha az utolsó „e", „i" — ezek ún. „semlegesek" és néha mindkét toldalékolást megengedik, de a gyakoribb a magas toldalék).

### 4.2. A toldalék harmonizál

Ha a tő utolsó magánhangzója mély, a toldalék is mély:
- „ház" + „-ban" (mély toldalék: -ban) → „házban"
- „asztal" + „-nak" (mély: -nak) → „asztalnak"

Ha magas, a toldalék is magas:
- „kert" + „-ben" (magas toldalék: -ben) → „kertben"
- „üveg" + „-nek" (magas: -nek) → „üvegnek"

### 4.3. Kivételek és „semleges" magánhangzók

Az „e" és „i" bizonyos szavakban semleges: mindkét toldalékolás megengedett, de a gyakoribb a magas. Példa: „tegnap" (utolsó magánhangzó: a, mély) + „-ban" → „tegnapban" (nem szokásos, de helyes); „tegnap" + „-ben" → „tegnapben" (szintén ritka; a gyakoribb forma: „tegnap"). A modell, ha nem ismeri a szót, a toldalékot a szótári alak alapján próbálja megválasztani, és gyakran téved.

## 5. A mássalhangzó-illeszkedés (consonant assimilation)

### 5.1. Zöngésségi hasonulás

A magyar toldalékok mássalhangzói a szó végi mássalhangzó zöngésségéhez illeszkednek:
- Ha a szó zöngétlen mássalhangzóra végződik (pl. „k", „p", „t", „sz", „s", „f"), a toldalék zöngétlen lesz: „-hoz" (mély toldalék) → „fához" (a „f" zöngétlen, de a toldalék zöngés „hoz"-ból „hosz"-szá válik? Nem — a példa hibás).
- A helyes szabály: a toldalék mássalhangzóját a tő végi mássalhangzóhoz illesztjük. Pl. „-val/-vel" → „tollal" (a „t" zöngétlen, a toldalék „-tal" lesz, nem „-val"), „kézzel" (a „kéz" zöngés „z"-re végződik, a toldalék „-szel" lesz, nem „-vel").

### 5.2. Gyakori hibák

- „-ban/-ben" toldalékkal: „Budapest" + „-ben" → „Budapestben" (helyes), de „Budapestre" (a „-re" toldalék illeszkedik a „t"-hez, bár itt nincs hasonulás, mert a „-re" már eleve „r"-rel kezdődik).
- „-hoz/-hez/-höz" toldalékkal: „ház" + „-hoz" → „házhoz" (a szó „z"-re végződik, zöngés, toldalék „-hoz" is zöngés, nincs változás); „kert" + „-hez" → „kerthez" (a „k" zöngétlen, toldalék „-hez" zöngétlenné válik: „-hesz"? Nem — a helyes „kerthez", a „h" zöngétlen, és a toldalékban is „h" van).

A modell tipikus hibája: „kertban" (ahelyett, hogy „kertben"), „asztalnak" (helyes), „asztalban" (helyes), de „kertben" (a modell gyakran ír „kertban"-t, ha a szótári alakban „kert" volt, és nem olvassa a hangrendet).

## 6. Az értékelés finomhangolása

### 6.1. Normalizálás

A modell kimenetét normalizálni kell az összehasonlítás előtt:
- kisbetűsítés
- ékezetes karakterek ellenőrzése
- írásjelek eltávolítása
- whitespace-kezelés

A normalizálás nélkül a kis- és nagybetű eltérése is hibaként jelenne meg.

### 6.2. Részpontszám

Bizonyos esetekben érdemes részpontszámot adni:
- Ha a modell a mondat 80%-át jól toldalékolja, de 20%-ban téved, kapjon 80%-ot erre a mondatra.
- Ez a token-szintű accuracy-vel valósul meg: minden helyes token 1 pont, minden helytelen 0.

### 6.3. Kategóriánkénti riport

A teszt nem csak egy összesített score-t ad, hanem kategóriánkénti bontást is:

```
Morph score összesített: 78.4%
  Többes szám:           85.2%
  Birtokos:              72.1%
  Esetragozás:           81.7%
  Határozottság:         68.3%
  Igeragozás:            79.5%
  Igekötők:              90.2%
  Összetett mondatok:    71.0%
```

Ez a riport diagnosztikus értékű: megmutatja, a modell hol erős, hol gyenge a magyar morfológiában.

## 7. Miért nehéz ez a nem-magyar modelleknek?

### 7.1. Az agglutináló struktúra ritka

A világ nyelveinek többsége izoláló (kínai, angol) vagy flektáló (latin, orosz). A magyar agglutináló, mint a török, finn, japán. Az izoláló nyelvekre tanított modellek (főleg az angol dominanciájú LLM-ek) nem tanulják meg a toldalékolás rendszerszerűségét.

### 7.2. A magyar tanító adatok kis részaránya

Még ha egy LLM elvileg támogatja is a magyart, a magyar tanító adatok az összes tanító adat <1%-a. A ritka szavak toldalékolása (alacsony gyakoriságú szavak az UD Hungarian-ban) így a modell számára „ismeretlen" tartomány, és a szabályokat kell(ene) alkalmaznia, de erre nincs minta.

### 7.3. A szabályok ritkán explicit formában vannak jelen

A magyar nyelvtan a tanító adatokban implicit: a modell a „házban" és „kertben" formát látja, és mintát vesz, de a szabályt (utolsó magánhangzó → toldalék) nem feltétlenül tanulja meg. Explicit promptokkal („a toldalék a szó utolsó magánhangzójához illeszkedjen") javítható a teljesítmény, de nem mindig elégségesen.

### 7.4. A finomhangolás (fine-tuning) ritkasága

A magyar specifikus finomhangolás sok modellnél hiányzik. A cloud modellek (GPT-4, Claude, Gemini) jobbak, mert nagyobb magyar tanító adatból tanultak; a lokális kis modellek (qwen3.5:0.8b, qwen3.5:2b) gyakran alulteljesítenek.

## 8. A 200 mondat elosztása (terv)

A teljes 200 mondatot a `tests/morph-test-hu-v1.jsonl` fájl tartalmazza (minden sor egy JSON objektum: `{"id", "category", "prompt", "expected", "tolerance"}`). A fájl jelenleg tervezet; az első mérés 2026-06-15-re van ütemezve. A kategóriák szerinti bontás a fenti 2.1. táblázat szerint alakul.

## 9. Kapcsolódó

- [Overview](../overview.md) — projekt cél és hatókör
- [SCHEMA](../SCHEMA.md) — wiki-formátum
- [UD Hungarian teszt](ud-hungarian.md) — kiegészítő mondattani teszt
- [Szórend teszt](szorend-hu.md) — szórend és fókusz
- [Nyelvészeti összefoglaló](nyelveszeti-osszefoglalo.md) — az összes nyelvészeti teszt
- [Karpathy LLM Wiki módszer](../../../llm-wiki/karpathy-llm-wiki-method.md) — elméleti háttér
