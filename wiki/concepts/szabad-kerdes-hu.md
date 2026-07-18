# Szabad Kérdéssor Magyar (Szabad-Kérdés-HU)

*Típus:* concept
*Forrás(ok):*
- Belső projekt: hu-eval overview — lásd [Overview](../overview.md)
- MT-Bench kategória-struktúra: Zheng et al. 2023, arXiv:2306.05685
- Emberi-LLM egyezés-metodológia: Cohen (1960), "A coefficient of agreement for nominal scales"
- LLM-as-a-Judge módszertan: lásd [LLM-as-a-Judge](llm-as-judge.md)

*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Mi a Szabad Kérdéssor?

A **Szabad Kérdéssor (Szabad-Kérdés-HU)** a hu-eval projekt saját, **kézzel összeállított, 30-50 darabos** magyar nyelvű kérdésgyűjteménye, amely kulturálisan, történetileg, nyelvileg **magyar-specifikus** tudást tesztel — olyan dolgokat, amiket egy általános, angol-centrikus benchmark (MMLU, MT-Bench) nem, vagy csak rosszul méri.

A kérdéssor nem statisztikai (nincs egyetlen helyes válasz), hanem **generatív**: a modell szabad szöveges választ ad, amit aztán vagy ember, vagy LLM-bíró pontoz.

## A négy alkategória

### 1. Közmondások (Proverbs)

Magyar közmondások felismerése, magyarázata, átfogalmazása. A modellnek ismernie kell a hagyományos magyar bölcsességeket, és tudnia kell őket modern kontextusba helyezni.

**Tipikus prompt:**

> „Mit jelent a 'Kutyából nem lesz szalonna' közmondás? Adj egy modern, 21. századi példát is, amikor érvényes!"

### 2. Történelmi hivatkozások (Historical References)

Magyar történelmi események, személyek, évszámok, helyszínek. A modellnek kontextusban kell tudnia elhelyezni ezeket — nem csak a dátumot tudni, hanem az ok-okozati összefüggést is.

**Tipikus prompt:**

> „Mi volt a Bécsi udvar szerepe az 1848-49-es forradalom és szabadságharc kitörésében? Ne csak évszámokat sorolj, magyarázd el a politikai hátteret is!"

### 3. Regionális különbségek (Regional Differences)

A magyar nyelvjárások, regionális szokások, kulináris hagyományok, népviseletek. A modellnek tudnia kell, hogy a *pér* (kelt tészta) Erdélyben, a *kürtőskalács* Székelyföldön, a *halászlé* Szegeden, a *paprikás csirke* pedig általánosan elterjedt.

**Tipikus prompt:**

> „Milyen regionális különbségek vannak a magyar halászlé elkészítésében? Hasonlítsd össze a szegedi és a bajai változatot!"

### 4. Névnapok és hagyományok (Name Days & Traditions)

A magyar naptár szerinti névnapok, népszokások (húsvét, pünkösd, karácsony, farsang), vallási és nemzeti ünnepek. Ezek erősen kulturálisan kötöttek, és egy nem magyar anyanyelvű modell tipikusan rosszul teljesít itt.

**Tipikus prompt:**

> „Mikor van a 'László' névnapja a magyar naptár szerint? Milyen népszokások kapcsolódnak a nyár végi László-naphoz a hagyományos paraszti kultúrában?"

## Értékelési módszertan: hibrid (ember + LLM-bíró)

A Szabad-Kérdés-HU nem támaszkodik kizárólag LLM-bíróra — a magyar kulturális referenciák túl specifikusak, túl sok a félreértés lehetősége. A projekt **hibrid pontozási stratégiát** alkalmaz:

### 1. lépés: Emberi pontozás (ground truth)

- 2-3 független magyar anyanyelvű pontozó (a projekt önkéntesei / belsős kollégák).
- Minden válasz **0-5 skálán**:

| Pont | Szint |
|------|-------|
| 0 | Teljesen hibás, sértő, vagy nem válaszol |
| 1 | Érintőlegesen kapcsolódik, de lényegében téves |
| 2 | Részben helyes, sok fontos elem hiányzik |
| 3 | Többnyire helyes, kisebb pontatlanságok |
| 4 | Jó, pontos, a lényeget lefedi |
| 5 | Kiváló, teljes, kontextusgazdag, emberi szintű |

### 2. lépés: LLM-bíró pontozás (skálázás)

- A bíró (`gemini-3-flash-preview:latest`) ugyanazt a 0-5 skálát használja, ugyanazzal a magyar nyelvű rubric-szel.
- A bíró indoklást is ad (mely részt talált helyesnek, melyet tévesnek).

### 3. lépés: Egyezés-vizsgálat

- **Cohen-féle κ (kappa)** az emberi és LLM-bíró pontozás között, kérdésenként.
- A hu-eval cél-κ: **≥ 0.70** (jelentős egyezés).
- Ha κ < 0.50, azt a kérdést kivesszük a végső értékelésből (az LLM-bíró nem tudja megbízhatóan pontozni).

### 4. lépés: Aggregáció

- Végső pontszám = (emberi pontozók átlaga) + (LLM-bíró pontszáma, korrigálva κ-val).
- Súlyozás: κ × emberi + (1-κ) × LLM, hogy a magasabb egyezésű kérdések jobban számítsanak.

## A 10 mintakérdés (magyar)

A teljes kérdéssor 30-50 darab, itt egy válogatás 10 reprezentatív példával:

**Q1 — Közmondás:**
> „Fogalmazd át a 'Addig nyújtózkodj, amíg a takaród ér' közmondást úgy, hogy az IT-vállalkozásokra is alkalmazható legyen! Adj egy konkrét esetet is."

**Q2 — Történelem:**
> „Ki volt Széchenyi István, és mi volt a 'legnagyobb magyar' epitheton eredete? Milyen konkrét intézkedései voltak, amelyek indokolták ezt a címet?"

**Q3 — Régió:**
> „Mi a különbség a 'paprikás csirke' és a 'csirkepaprikás' között a magyar konyhában? Melyik régióból származik, és mi a hagyományos körete?"

**Q4 — Névnap:**
> „Mikor van a 'Gergő' névnapja? Milyen népi hiedelmek fűződnek a Gergely-napokhoz a magyar paraszti hagyományban?"

**Q5 — Közmondás (átfogalmazás):**
> „A 'Nem mind arany, ami fénylik' közmondást magyarázd el egy 10 éves gyereknek, és mellé adj egy könnyen érthető példát a hétköznapokból!"

**Q6 — Történelem (20. század):**
> „Milyen körülmények vezettek az 1956-os forradalom kitöréséhez? Ne csak a Budapest-eseményeket sorold, hanem vidéki szempontokat is!"

**Q7 — Régió (nyelvjárás):**
> „Mit jelent az 'anyósnyelv' szó a székely nyelvjárásban? Miben tér el a köznyelvitől, és milyen más tájszavakat ismersz még a régióból?"

**Q8 — Hagyomány (ünnepek):**
> „Milyen húsvéti szokások élnek még a magyar falvakban? Hasonlítsd össze a katolikus és a református vidékek hagyományait!"

**Q9 — Történelem (Trianon):**
> „Mit jelent a 'trianon' szó a magyar történelmi emlékezetben? Milyen következményei voltak az 1920-as békeszerződésnek a magyarságra nézve?"

**Q10 — Névnap + hagyomány:**
> „Mikor van a 'Márton' névnapja, és milyen hagyományos népi szokások kapcsolódnak a Márton-naphoz (pl. liba, bor, időjárásjóslás)?"

## LLM-bíró prompt template (magyar, szabad kérdés)

```text
Te egy magyar nyelvű LLM-bíró vagy, aki magyar kulturális kérdésekre adott
válaszokat értékel. A CANDIDATE választ 0-5 skálán pontozd az alábbi
rubric alapján.

[KÉRDÉS]
{question}

[CANDIDATE — az értékelt modell válasza]
{output}

[REFERENCIA (ha van) — az emberi szakértő által írt "jó" válasz vázlata]
{reference}

[PONTOZÁSI RUBRIC]
0 — Teljesen hibás, off-topic, sértő, vagy üres.
1 — Érintőlegesen kapcsolódik, de lényegében téves információt ad.
2 — Van némi helyes elem, de fontos dolgok hiányoznak vagy pontatlanok.
3 — Többnyire helyes, kisebb pontatlanságokkal (pl. évszám ±5, régió
    részben rossz, de az irány jó).
4 — Jó, pontos, a lényeget lefedi, kontextusban elhelyezi.
5 — Kiváló, teljes, kontextusgazdag, emberi szintű, kreatív (ahol
    a feladat ezt kéri).

[FIGYELEM]
- A kulturális pontosság fontosabb, mint a stílus.
- Ha a CANDIDATE kitalál egy részletet (hallucináció), az büntetendő.
- A magyar helyesírás és nyelvhelyesség a pontozás 20%-át adja.

[VÁLASZ FORMÁTUM]
Pontszám: <0–5 egész szám>
Indoklás: <2-4 mondat magyarul, konkrét szöveges hivatkozásokkal>
```

## Példa: bíró kimenet

**Kérdés (Q2 fenti):**

> „Ki volt Széchenyi István, és mi volt a 'legnagyobb magyar' epitheton eredete?..."

**Candidate (modell `qwen3.5:4b`):**

> „Széchenyi István (1791-1860) magyar reformpolitikus volt. A 'legnagyobb magyar' címet Széchenyi István valamelyik kortársa adta neki, de sajnos nem emlékszem pontosan, kitől. A Lánchíd építésében vállalt szerepe fontos volt, és ő alapította a Magyar Tudományos Akadémiát is."

**Bíró kimenet:**

```text
Pontszám: 2
Indoklás: A válasz vázlatos, de tartalmaz néhány helyes elemet (évek,
Lánchíd, MTA). A 'legnagyobb magyar' epitheton eredetét a modell
nem tudja: ez Trefort Ágontól (vagy a kortárs közbeszédtől) származik,
a modell ezt nyíltan beismeri, ami jobb, mint a kitalálás, de a
referencia-érték 4-es szintjétől messze van. A reformintézkedések
(csomópontok, hitel, jobbágykérdés) teljesen hiányoznak.
```

Emberi pontozók átlaga ugyanerre a válaszra: **2.3** (κ = 0.78 az LLM-bíróval, tehát erős egyezés).

## Limitációk

- **Kis elemszám (30-50):** statisztikai szignifikancia-teszteléshez kevés, ezért a projekt a Szabad-Kérdés-HU-t kiegészítő, nem elsődleges benchmarkként kezeli.
- **Szubjektivitás:** a kulturális kérdéseknél az emberi pontozók közötti κ is lehet alacsony (0.55-0.65), ezért minimum 2, ideálisan 3 független pontozó kell.
- **Frissesség:** a közmondások, hagyományok lassan változnak, de a regionális/kulturális referenciák érzékenyek a generációs eltérésekre (pl. a mai 20 éves már nem ismer minden népszokást).

## Összefüggés

- [HuGME](hugme-benchmark.md) — metrika-alapú, single-turn
- [MT-Bench-HU](mt-bench-hu.md) — multi-turn, GSB pairwise
- [LLM-as-a-Judge](llm-as-judge.md) — κ-számítás, bíró prompt
- [Overview](../overview.md) — projekt kontextus
- [SCHEMA](../SCHEMA.md) — oldalformátum

## Hivatkozások

- Cohen, J. (1960). "A coefficient of agreement for nominal scales." Educational and Psychological Measurement, 20(1), 37-46. — a κ-statisztika eredeti forrása.
- Magyar néprajzi lexikon: <https://mek.oszk.hu/adatbazis/lexikon>
- Lásd még: [LLM-as-a-Judge](llm-as-judge.md) — a Cohen-κ értelmezése LLM-bíró kontextusban.
