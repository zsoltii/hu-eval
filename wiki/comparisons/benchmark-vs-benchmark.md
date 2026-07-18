# Benchmark vs. Benchmark — Mit Mér Melyik?

*Típus:* comparison
*Forrás(ok):* HuLU paper, MMLU-HU, HuGME (HuggingFace), Universal Dependencies Hungarian, MT-Bench
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Cél

A magyar LLM-ek értékelésére használt benchmarkok **nem mérik ugyanazt** — van, ami lexikális tudást, van, ami nyelvészeti mélységet, van, ami generatív minőséget. Ez az oldal segít eldönteni, **melyik benchmarkot mikor futtassuk**, és mit tudunk (nem) megállapítani az eredményeikből.

## A négy fő benchmark-család

A projekt négy, jól elkülöníthető benchmark-családot használ. Ezek kiegészítik egymást, de egyik sem helyettesíti a másikat.

### 1. HuLU — Hungarian Language Understanding

- **Mit mér:** zártvégű, magyar nyelvű, olvasott-szövegértésen alapuló multiple-choice kérdések
- **Formátum:** 4-5 opció közül kell kiválasztani a helyeset, hasonlóan az angol MMLU-hoz
- **Területek:** magyar történelem, irodalom, nyelvtan, általános tudás, logika magyar nyelven
- **Skála:** 0-100% pontosság
- **Erősség:** jól skálázódik, gyors, olcsó, magyar specifikus
- **Gyengeség:** nem mér generatív minőséget, nem mér nyelvészeti mélységet

### 2. MMLU-HU — Massive Multitask Language Understanding (Hungarian)

- **Mit mér:** az eredeti MMLU 57 tudományterületének magyar fordítása
- **Formátum:** 4 opciós MCQ, "correct answer" típusú
- **Területek:** matematika, fizika, jog, orvosl, filozófia, stb. — magyarul
- **Skála:** 0-100% pontosság
- **Erősség:** nemzetközileg összehasonlítható, mivel az eredeti MMLU-val azonos struktúra
- **Gyengeség:** fordítási zaj, kulturális eltérések (US-centrikus kérdések)

### 3. HuGME — Hungarian Generative Model Evaluation

- **Mit mér:** nyíltvégű generatív feladatok, LLM-as-a-Judge értékeléssel
- **Formátum:** szabad szöveges válasz, bíró modell 1-5 skálán pontozza
- **Területek:** kreativitás, érvelés, összefoglalás, fordítás magyarról/angolra
- **Skála:** 1-5 Likert, aztán 0-100-ra normálva
- **Erősség:** a valós használathoz legközelebb, a "minőség" fogalmát közvetlenül méri
- **Gyengeség:** drága (bíró modell hívás), lassú, bíró elfogultság (bias) kockázata

### 4. UD Hungarian — Universal Dependencies (nyelvészeti)

- **Mit mér:** morfológiai elemzés (POS-tagging), szintaktikai elemzés (dependency parsing), lemmatizálás
- **Formátum:** token-szintű CoNLL-U annotáció, F1 pontszám
- **Területek:** ragok, egyeztetés, szórend, igeragozás
- **Skála:** 0-100% F1 score (pontosság × fedés harmonikus közepe)
- **Erősség:** a magyar nyelv mély, strukturális tudását méri — ezt más benchmark nem teszi
- **Gyengeség:** technikai, nem "felhasználóbarát" — nehéz értelmezni a F1-t laikusoknak

## Átfedés és komplementaritás

### Átfedési mátrix

Az alábbi mátrix megmutatja, hogy az egyes képességeket melyik benchmark méri (1 = közvetlenül, 0.5 = részben, 0 = nem méri).

| Képesség | HuLU | MMLU-HU | HuGME | UD-HU |
|----------|:----:|:-------:|:-----:|:-----:|
| Lexikális tudás (magyar) | 1.0 | 0.7 | 0.3 | 0.0 |
| Tényismeret (angol MMLU tükrözés) | 0.3 | 1.0 | 0.2 | 0.0 |
| Olvasott szövegértés (magyar) | 1.0 | 0.8 | 0.4 | 0.0 |
| Matematikai/logikai érvelés | 0.5 | 1.0 | 0.6 | 0.0 |
| Generatív minőség (folyékonyság) | 0.0 | 0.0 | 1.0 | 0.2 |
| Érvelés, esszé, kreativitás | 0.0 | 0.0 | 1.0 | 0.0 |
| Magyar morfológia (ragok) | 0.2 | 0.0 | 0.3 | 1.0 |
| Magyar szórend (szabad) | 0.0 | 0.0 | 0.4 | 0.9 |
| Lexikális pontosság (false info) | 0.3 | 0.3 | 0.8 | 0.0 |
| Következetesség, koherencia | 0.0 | 0.0 | 0.9 | 0.0 |

### Mit jelent ez a gyakorlatban?

- **HuLU önmagában** — "mennyit tud a modell magyarról" kérdésre ad választ, de nem mondja meg, hogyan ír
- **MMLU-HU önmagában** — "mennyit tud a modell általában" kérdésre ad választ, de a magyar minőségről nem sokat mond
- **HuGME önmagában** — "milyen a modell írása" kérdésre ad választ, de a ténysmereti pontosságról keveset
- **UD-HU önmagában** — "mennyire ismeri a modell a magyar nyelvtant" kérdésre ad választ, de a használhatóságról semmit

A négy benchmark **együttesen** ad reális képet — önmagukban egyik sem elég.

## Mikor melyiket használjuk?

### Döntési fa

```
Szeretném tesztelni egy modell magyar képességeit.
│
├── Gyors, olcsó áttekintést akarok (~1 óra)
│   └── Futtass HuLU-t (és MMLU-HU-t, ha van rá idő)
│
├── A modell ténysmereti tudása érdekel
│   ├── Általános tudás → MMLU-HU
│   └── Magyar specifikus tudás → HuLU
│
├── A modell írásminősége érdekel (esszé, összefoglaló, stb.)
│   └── Futtass HuGME-t
│
├── A modell magyar nyelv mély ismerete érdekel (grammatika)
│   └── Futtass UD-HU-t
│
├── Production deployment előtt állok
│   └── Futtasd mind a négyet — a composite score csak így értelmes
│
└── Csak egyet futtathatok, és gyorsan kell dönteni
    └── HuLU + UD-HU kombináció (magyar specifikus, gyors)
```

### Ajánlott kombinációk

| Cél | Benchmarkok | Becsült idő/modell |
|-----|-------------|---------------------|
| Smoke test (gyors) | HuLU (100 kérdés) | 5-10 perc |
| Standard assessment | HuLU + MMLU-HU + UD-HU | 2-3 óra |
| Teljes kiértékelés | HuLU + MMLU-HU + HuGME + UD-HU | 4-6 óra |
| Deep-dive riport | Teljes + saját szabad kérdéssor | 1-2 nap |

## Korlátok és buktatók

### HuLU korlátai

- MCQ formátum → a modellnek "csak" a jó opciót kell kiválasztania, nem kell írnia
- Zártvégű → a modell nem tud "tudatosan hazudni" vagy "kreatívan kitérni"
- Coverage: a HuLU kérdésbank nem feltétlenül reprezentálja a teljes magyar nyelvet

### MMLU-HU korlátai

- Fordítási zaj — egyes kérdések furán hangzanak magyarul
- Kulturális elfogultság — az eredeti MMLU US-centrikus, a fordítás nem változtatja meg a tartalmat
- Nem magyar specifikus tudást mér, csak magyarul mér tudást

### HuGME korlátai

- **Bíró elfogultság** — ha a bíró modell ugyanabból a családból való, mint a vizsgált modell, torzíthat
- Költséges — minden válasz bíró hívás, ami 5-10x annyi token, mint maga a válasz
- Szubjektivitás — az 1-5 skála interpretációja bíró modellenként változhat
- Prompt érzékenység — ugyanaz a feladat más prompttal más eredményt hoz

### UD-HU korlátai

- Technikai — a F1 score nehezen kommunikálható laikusok felé
- Coverage — a Universal Dependencies treebank nem feltétlenül reprezentatív (főleg irodalmi szövegek)
- Generatív modelleknél az UD inkább downstream — a modell nem direkt dependency parse-t csinál

## Ajánlott mintasúlyok a composite score-hoz

Az [Overview](../overview.md) alapján:

- **Statisztikai benchmarkok** (HuLU + MMLU-HU) → **40%**
- **Generatív benchmarkok** (HuGME) → **40%**
- **Nyelvészeti mélytesztek** (UD-HU) → **20%**

Ha csak HuLU és UD-HU fut (gyors assessment):

- HuLU → 70%, UD-HU → 30%

## Kapcsolódó

- [Modell vs. Modell](modell-vs-modell.md) — páronkénti összehasonlítási keretrendszer
- [Cloud vs. Lokális](cloud-vs-lokal.md) — üzemeltetési döntés
- [Eredmény Aggregáció](../reports/eredmeny-aggregacio.md) — hogyan kombináljuk a benchmark pontszámokat
- [Overview](../overview.md) — fő keretrendszer
- [SCHEMA](../SCHEMA.md) — formátum
