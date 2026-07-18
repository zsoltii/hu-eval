# Universal Dependencies — Hungarian (UD Hungarian)

*Típus:* concept
*Forrás(ok):*
- [Universal Dependencies — Hungarian treebank](https://universaldependencies.org/treebanks/hu/index.html) — hivatalos UD oldal, letöltés és statisztikák
- [UD Hungarian (Szeged Treebank)](https://github.com/UniversalDependencies/UD_Hungarian-Szeged) — GitHub repo, CoNLL-U fájlok
- [Nivre, J. et al. (2016). Universal Dependencies v1](https://aclanthology.org/L16-1002/) — az UD keretrendszer leírása (LREC 2016)
- [Universal Dependencies v2](https://universaldependencies.org/v2/) — aktuális specifikáció
- [Szeged Treebank honlap (NYTK)](https://rgai.inf.u-szeged.hu/node/78) — eredeti magyar treebank
- [Universal POS tags](https://universaldependencies.org/u/pos/) — POS tagkészlet

*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-16 (v1.2.11 — runner implementálva: CoNLL-U parse, 137 mondat, UPOS/UAS/LAS composite)

---

> 🛠️ **Implementációs státusz (2026-06-16):** ✅ `download_ud_hungarian.py` + `run_ud_hungarian.py` kész. Forrás: GitHub raw `hu_szeged-ud-test.conllu` (nem HF). 137 mondat, a modell CoNLL-U formátumban válaszol, a runner regex-szel nyeri ki a TOKEN/UPOS/HEAD/DEPREL mezőket. Composite score = (UPOS + UAS + LAS) / 3. A `data/ud_hungarian/sentences.jsonl` tartalmazza a mondatokat referenciával.

## 1. Mi az UD Hungarian?

A **Universal Dependencies (UD)** egy nyelvészeti keretrendszer, amely egységes, nyelvfüggetlen annotációs szabványt definiál mondattani elemzésre (POS taggelés + dependency parsing). Az UD projekt 2014-ben indult (Google, Stanford, Charles University, ÚFAL), mára 200+ nyelvet fed le. Minden nyelvhez ún. **treebank** tartozik, amely manuálisan annotált, CoNLL-U formátumú mondatok gyűjteménye.

A **magyar UD treebank** a Szeged Treebankre épül (NYTK, Szegedi Tudományegyetem), és `UD_Hungarian-Szeged` néven érhető el. Jelenleg (UD v2.16, 2026) ~25 000 tokent tartalmaz, kézzel annotálva, "news" és "wiki" doménekből. Kisebb kiegészítések más forrásokból is kerültek bele.

### 1.1. Miért fontos ez LLM-értékeléshez?

Egy LLM akkor „beszéli jól a magyart", ha a mondattani struktúrát is helyesen kezeli — nem csak a szógyakoriságokat. Az UD Hungarian három dolgot mér:

1. **POS (part-of-speech) tagging** — a modell helyesen azonosítja-e a szófajokat (ige, főnév, melléknév, névelő, stb.)
2. **Dependency parsing** — a modell felismeri-e a szavak közötti nyelvtani függőségeket (alany, tárgy, határozó, stb.)
3. **Lemmatizálás** — a modell visszafejti-e a szótövet (pl. „házban" → „ház")

Mindháromra van metrika, és mind a három specifikusan magyar nyelvi kihívás, mert a magyar **agglutináló** nyelv: egy szó akár 4-5 toldalékot is viselhet, és a toldalékolás szabályai (magánhangzó-harmónia, mássalhangzó-illeszkedés) rendkívül bonyolulttá teszik a tokenizálást és a címkézést.

## 2. Letöltés és formátum

### 2.1. Honnan töltsd le?

- **Hivatalos UD oldal (treebanks/hu):** https://universaldependencies.org/treebanks/hu/index.html
- **Közvetlen GitHub:** https://github.com/UniversalDependencies/UD_Hungarian-Szeged
- **Két fő fájl:** `hu_szeged-ud-train.conllu`, `hu_szeged-ud-test.conllu`, valamint `hu_szeged-ud-dev.conllu`

A CoNLL-U formátum tabulátorral tagolt, minden sor egy tokent ír le, üres sor választja el a mondatokat. Egy tipikus sor:

```
# sent_id = dev-1234
# text = A macska az asztalon ül.
1   A       a       DET    Definite=Def|PronType=Art  2   det   _   _
2   macska  macska  NOUN   Case=Nom|Number=Sing         4   nsubj _   _
3   az      az      DET    Definite=Def|PronType=Art   4   det   _   _
4   asztalon asztal NOUN   Case=Sup|Number=Sing         5   obl   _   _
5   ül      ül      VERB   Number=Sing|Person=3|Tense=Pres 0 root   _   _
6   .       .       PUNCT  _                            5   punct _   _
```

Az oszlopok: `ID`, `FORM` (a szóalak), `LEMMA` (tő), `UPOS` (egyetemes POS), `XPOS` (nyelv-specifikus POS), `FEATS` (morfológiai jegyek), `HEAD` (fej ID), `DEPREL` (függőségi reláció), `DEPS` (alternatív fejek), `MISC`.

### 2.2. Tokenizálási sajátosság

A magyar agglutináló volta miatt a tokenizálás önmagában is vitatott: a „házban" szó egy token, de a „legszebbekké" szó szintén egy token. Az UD treebank ezt az elvet követi — **szó = token** (szóköz által határolt egység). Ez azt jelenti, hogy a modellnek az ilyen hosszú, toldalékolt alakokat egészben kell kezelnie, és nem szabad szétszednie toldalékokra tokenizáláskor. Ez nehezíti a subword-tokenizáló modelleket (BPE, WordPiece): ha a tokenizer felaprítja a szót, elveszhetnek a morfológiai információk.

## 3. Metrikák: UAS, LAS

### 3.1. UAS (Unlabeled Attachment Score)

Az UAS azt méri, hogy a modell **helyesen azonosítja-e, melyik szó a feje egy adott szónak**, függetlenül a reláció típusától. Példa:

Helyes elemzés: „A macska az asztalon ül." → az „ül" (ID=5) a root, az „asztalon" (ID=4) feje az „ül" (HEAD=5).

Ha a modell azt mondja, hogy az „asztalon" feje a „macska" (HEAD=2), akkor UAS szempontból hibázik, akkor is, ha a DEPREL mezőt jól tippeli.

UAS számítása: `helyes_head_következtetések / összes_függőségi_él × 100%`. A felső határ modern rendszereknek ~92-95% angolra, magyarra ~88-92%.

### 3.2. LAS (Labeled Attachment Score)

A LAS szigorúbb: a HEAD-en kívül a DEPREL-t is nézi. Tehát ha a modell kitalálja a helyes fejet, de a rossz relációt írja (pl. `nsubj` helyett `obj`), az LAS-ban hibának számít. Ez a fő riport-metrika dependency parsingra.

LAS = (helyes_head ÉS helyes_deprel) / összes_függőségi_él × 100%. Magyarra a legjobb rendszerek LAS ~85-90%-ot érnek el.

### 3.3. POS accuracy (UPOS)

A POS accuracy egyszerű: a modell által adott UPOS címkék egyeznek-e az aranystandarddal. Számítása: `helyes_UPOS / összes_token × 100%`. A felső határ magyarra ~97-98%.

### 3.4. Lemma accuracy (opcionális)

A lemma accuracy a tő-visszaállítás pontosságát méri. Magyarra különösen nehéz, mert a toldalékolás visszafordítása nem triviális (pl. „házakban" → „ház", „legszebbekké" → „szép").

## 4. Miért nehéz ez magyarra?

### 4.1. Esetragok (case suffixes)

A magyar nyelv **18+ esetet** különböztet meg (alanyi, tárgyas, részes, birtokos, elöljárós, stb.). Mindegyik más-más toldalék, és a toldalék alakja függ a szó végződésétől (magánhangzó-harmónia) és a mássalhangzó-illeszkedéstől. Példa „ház":

| Eset | Toldalék | Teljes alak |
|------|----------|-------------|
| Alanyi (Nom) | — | ház |
| Tárgyas (Acc) | -at/-et | házat |
| Birtokos (Gen) | -nak/-nek | háznak |
| Elöljárós (Sup) | -on/-en/-ön | házon |
| Határozói (Ins) | -szal/-szel | házzal |

Egy LLM-nek ezeket helyesen kell előállítania generáláskor, és helyesen kell azonosítania parsingkor. A nem-magyar modellek tipikus hibája: angolos túláltalánosítás („házat" helyett „házzal" a tárgyas esetbe).

### 4.2. Magánhangzó-harmónia (vowel harmony)

A magyar toldalékok illeszkednek a szó utolsó magánhangzójához:
- Ha a szó utolsó magánhangzója **első harmóniájú** (a, á, o, ó, u, ú — „mély" vagy „alsó"), akkor a toldalék is első harmóniájú: `-ban`, `-nak`, `-val`.
- Ha **második harmóniájú** (e, é, i, í, ö, ő, ü, ű — „magas"), akkor a toldalék is második: `-ben`, `-nek`, `-vel`.

Példa: „kert" (e → magas) → „kertben" (e), „kertnek" (e). „asztal" (a → mély) → „asztalban" (a), „asztalnak" (a). A hiba tipikus formája: „kertban" vagy „asztalben" — ilyenkor a modell nem vette figyelembe a tő utolsó magánhangzóját.

### 4.3. Többes szám és birtokos együtt

A magyarban a birtokos személyét és számát is jelölni kell a birtokon. Példa: „a macskám" (1. sz. egyes, enyém), „a macskád" (2. sz. egyes, tiéd), „a macskája" (3. sz. egyes, övé). Többes szám birtokossal: „a macskáim" (több macska, több enyém), „a macskái" (több macska, egyes 3. személy birtokos).

A birtokos személyjelet ismét **magánhangzó-harmónia és mássalhangzó-illeszkedés** befolyásolja, és a birtokos számát is jelölni kell („macskátok" — többes szám 2. személy). Ez egy 4×3×2 = 24-es rácsozat, ahol minden rácspontnak van egyedi alakja.

## 5. Minta: 10 mondat várható POS taggel és dependency-vel

Az alábbiakban 10 magyar mondatot mutatunk be, a várt UPOS tagekkel és a fő dependency-élekkel. A teljes annotáció a Szeged Treebankben található.

### Mondat 1: „A kutya ugat."
- `A` → DET (névelő)
- `kutya` → NOUN (főnév, alanyeset)
- `ugat` → VERB (ige, jelen idő, 3. személy)
- `.` → PUNCT
- Főbb élek: `kutya` ← nsubj ← `ugat`; `A` ← det ← `kutya`

### Mondat 2: „A gyerekek az iskolában tanulnak."
- `A` → DET
- `gyerekek` → NOUN (többes szám, alanyeset)
- `az` → DET
- `iskolában` → NOUN (birtokos esetű volna, de elöljárós, Case=Sup)
- `tanulnak` → VERB (többes szám, 3. személy, jelen idő)
- Fő élek: `gyerekek` ← nsubj ← `tanulnak`; `iskolában` ← obl ← `tanulnak`

### Mondat 3: „Esik az eső."
- `Esik` → VERB (3. személy, jelen)
- `az` → DET
- `eső` → NOUN (alanyeset)
- Fő élek: `eső` ← nsubj ← `Esik`. Érdekesség: az alany a mondat végén van, mert a mondat topik-fókusz szerkezetet tükröz.

### Mondat 4: „Szeretem a csokoládét."
- `Szeretem` → VERB (1. személy egyes, tárgyas ragozás)
- `a` → DET
- `csokoládét` → NOUN (tárgyeset, Case=Acc)
- Fő élek: `csokoládét` ← obj ← `Szeretem`

### Mondat 5: „Péter és Mari elmentek a boltba."
- `Péter` → PROPN (tulajdonnév, alanyeset)
- `és` → CCONJ (kapcsos kötőszó)
- `Mari` → PROPN
- `elmentek` → VERB (többes szám, 3. személy, múlt idő, perfective)
- `a` → DET
- `boltba` → NOUN (birtokos esetbe kerül az irányjelölővel: Case=Ill+Number=Sing)
- Fő élek: alany = `Péter` + `Mari` (conj), `elmentek` ← nsubj

### Mondat 6: „A szép piros virágok az asztalon vannak."
- `A` → DET
- `szép` → ADJ (melléknév)
- `piros` → ADJ
- `virágok` → NOUN (többes szám, alanyeset)
- `az` → DET
- `asztalon` → NOUN (elöljárós eset, Case=Sup)
- `vannak` → VERB (létezik, többes szám, 3. személy)
- Fő élek: `virágok` ← nsubj ← `vannak`; `asztalon` ← obl

### Mondat 7: „Kérlek, add ide a könyvet!"
- `Kérlek` → VERB (1. személy, kér tárgyatlan, kérsz formaszerű felszólítás)
- `add` → VERB (2. személy, felszólító mód)
- `ide` → ADV (távolra mutató határozószó)
- `a` → DET
- `könyvet` → NOUN (tárgyeset, Case=Acc)
- Fő élek: `könyvet` ← obj ← `add`

### Mondat 8: „Ma szép idő van."
- `Ma` → ADV (időhatározó)
- `szép` → ADJ
- `idő` → NOUN (alanyeset)
- `van` → VERB (3. személy, jelen, létezik)
- Fő élek: `idő` ← nsubj ← `van`; `Ma` ← advmod ← `van`

### Mondat 9: „Azt hiszem, hogy holnap esni fog."
- `Azt` → PRON (hivatkozó névmás, tárgyeset)
- `hiszem` → VERB (1. személy, jelen, tárgyas)
- `hogy` → SCONJ (alárendelő kötőszó)
- `holnap` → ADV
- `esni` → VERB (főnévi igenév)
- `fog` → AUX (segédige, jövő idő)
- Fő élek: `Azt` ← obj ← `hiszem`; `esni` ← ccomp (kiejtés) ← `hiszem`; `fog` ← aux ← `esni`

### Mondat 10: „Sokkal többet dolgozott, mint gondoltam."
- `Sokkal` → ADV
- `többet` → ADV (közelítőleges számnévi)
- `dolgozott` → VERB (3. személy, múlt, perfective)
- `mint` → SCONJ
- `gondoltam` → VERB (1. személy, múlt)
- Fő élek: `többet` ← advmod ← `dolgozott`; `gondoltam` ← advcl ← `dolgozott`

## 6. Értékelési módszertan

### 6.1. Pipeline (implementálva v1.2.11)

1. **Letöltés:** `scripts/download_ud_hungarian.py` — a GitHub raw `hu_szeged-ud-test.conllu` fájlból (~137 mondat) standard JSONL-be konvertálja `data/ud_hungarian/sentences.jsonl` néven.
2. **Futtatás:** `scripts/run_ud_hungarian.py` — minden mondatra elküldi a modellnek a CoNLL-U formátumú elemzési kérést. A modell válaszából regex-szel (TOKEN/UPOS/HEAD/DEPREL) parse-olja ki a mezőket.
3. **Metrikák:** UPOS accuracy (szófaji címkék), UAS (fej-mutató helyessége), LAS (fej + reláció helyessége). Minden mondatra külön számolva.
4. **Composite score:** `(UPOS + UAS + LAS) / 3` — a summary JSON-ban `score` néven.

### 6.2. Konkrét prompt-sablon

```
Feladat: Elemezd az alábbi magyar mondatot szófaj és nyelvtani függőség szerint!
Minden szóhoz add meg:
- ID (sorszám, 1-től)
- FORM (a szóalak)
- LEMMA (a szótő)
- UPOS (egyetemes szófaj: NOUN, VERB, ADJ, ADV, DET, PRON, AUX, CCONJ, SCONJ, ADP, NUM, PROPN, PUNCT, X)
- HEAD (a fej szó sorszáma, 0 ha root)
- DEPREL (függőségi reláció: nsubj, obj, iobj, obl, advmod, amod, det, case, mark, cc, conj, root, punct, aux, cop, ...)

Mondat: "{sentence}"
Válasz: táblázatban, TSV vagy Markdown táblázat.
```

### 6.3. Értékelő script vázlat (Python)

A projektben használható egy `eval_ud.py` script, amely:
- beolvassa a CoNLL-U referenciát
- meghívja a modellt minden mondatra
- parse-olja a modell kimenetét (elvárt: táblázat)
- összehasonlítja a token-szintű UPOS-t és a fej-él-párokat
- riportolja az UAS/LAS/UPOS accuracy-t

A script az `entity/ud-hungarian-tooling.md` oldalon részletezett (amennyiben létezik, lásd [Index](../index.md)).

### 6.4. Elfogadható küszöbértékek

| Szint | UPOS acc | UAS | LAS | Értelmezés |
|-------|----------|-----|-----|------------|
| Kiváló | ≥97% | ≥90% | ≥85% | Professzionális NLP-szint |
| Jó | 93-97% | 85-90% | 78-85% | Erős, használható |
| Elfogadható | 85-93% | 75-85% | 65-78% | Korlátozottan megbízható |
| Gyenge | <85% | <75% | <65% | Csak tájékoztató |

## 7. Gyakori hibák és buktatók

### 7.1. Tokenizálási eltérések

Ha a modell a „legszebbekké" szót három subwordre bontja (`leg`, `##szebb`, `##ekké`), de az UD tokenként egy egység, akkor az összehasonlítás fals negatív. Megoldás: a modell kimenetében minden tokent összefűzünk és normalizálunk (ékezetek, kis/nagy betű), mielőtt összehasonlítanánk.

### 7.2. Többértelműségek

A magyarban a POS-tagek néha egyértelműsítésre szorulnak. Példa: „észre" → ADV (főnévvé alakult határozószó) vagy NOUN? Az UD a szövegkörnyezet alapján dönt. A modell, ha nincs kontextus, gyakran rosszul dönt.

### 7.3. Token-határ a toldalékoknál

Egyes modellek (különösen a kisebb lokális LLM-ek) megpróbálják szétszedni a toldalékokat (pl. „házban" → „ház" + „ban"). Ez szintaktikailag érhető, de az UD-vel ellentétes, és azonnal nullázza az UPOS accuracy-t. Megoldás: utasítás a promptban: „A szót NEM szabad toldalékokra bontani, kezeld egyetlen tokenként."

## 8. Miért releváns ez a projekt számára?

Az UD Hungarian a magyar nyelvű LLM-értékelés egyik **legrégibb, legjobban dokumentált** benchmarkja. Előnyei:
- **Standard, peer-reviewed** — nemzetközileg elfogadott
- **Automatizálható** — gyors, olcsó, reprodukálható
- **Diagnosztikus** — konkrétan megmutatja, hol hibázik a modell (POS? függőség? lemma?)
- **Összehasonlítható** — több modell eredménye azonos metrikákon mérhető

A [Nyelvészeti összefoglaló](nyelveszeti-osszefoglalo.md) oldalon az UD Hungarian a kompozit nyelvészeti score egyik fő komponense (20% súly a teljes nyelvészeti dimenzión belül).

## 9. Kapcsolódó

- [Overview](../overview.md) — projekt cél és hatókör
- [SCHEMA](../SCHEMA.md) — wiki-formátum
- [Magyar morfológia teszt](morfologia-hu.md) — kiegészítő teszt a toldalékolási szabályokra
- [Szórend teszt](szorend-hu.md) — magyar szórend és fókusz
- [Nyelvészeti összefoglaló](nyelveszeti-osszefoglalo.md) — az összes nyelvészeti teszt együtt
- [Karpathy LLM Wiki módszer](../../../llm-wiki/karpathy-llm-wiki-method.md) — elméleti háttér
- [Universal Dependencies honlap](https://universaldependencies.org/) — nemzetközi projekt
