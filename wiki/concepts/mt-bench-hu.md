# MT-Bench Magyar Verzió (MT-Bench-HU)

*Típus:* concept
*Forrás(ok):*
- Zheng, L., Chiang, W., Sheng, Y., et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." arXiv:2306.05685. <https://arxiv.org/abs/2306.05685>
- Eredeti MT-Bench repo: <https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge>
- Belső projekt: hu-eval overview — lásd [Overview](../overview.md)

*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-16 (v1.2.11 — runner + judge implementálva, 24 kérdés × 2 turn, GSB pairwise)

---

> 🛠️ **Implementációs státusz (2026-06-16):** ✅ `run_mt_bench_hu.py` + `judge_mt_bench.py` kész. 24 kérdés (8 kategória × 3), 2 forduló. Baseline modell: `deepseek-v4-flash:cloud`. GSB pairwise, counterbalanced (swap). Win rate 0-1. A `data/mt_bench_hu/questions.jsonl` tartalmazza a kérdéseket.

## Mi az MT-Bench-HU?

Az **MT-Bench** (Multi-Turn Benchmark) a LMSYS csapat (Zheng et al., 2023) által kifejlesztett benchmark, amely a modellek **többfordulós, nyílt párbeszédes** képességeit méri. Az eredeti benchmark 80 (későbbi bővítésben 100) multi-turn promptból áll, 8 kategóriában.

A **MT-Bench-HU** a hu-eval projekt saját, **magyar nyelvű adaptációja**: a promptok magyar nyelvűek, a kategóriák a magyar nyelvhasználatra jellemző feladattípusokkal bővülnek (pl. magyar nyelvű kód-komment, hivatalos levél, irónia-felismerés), és a bíró prompt is magyar.

## A 8 kategória

Az eredeti MT-Bench 8 kategóriát használ; a magyar verzió ugyanazt a vázt követi, de a kategóriák tartalma új, magyar specifikus promptokból áll:

| # | Kategória | Példa-feladattípus |
|---|-----------|-------------------|
| 1 | **Creative Writing (kreatív írás)** | magyar novella, vers, dalszöveg folytatása |
| 2 | **Code (kód, magyar kommenttel)** | Python függvény, de `# magyar megjegyzésekkel` és `docstring` magyarul |
| 3 | **Formal Letter (hivatalos levél)** | önéletrajz, panaszlevél, munkahelyi kérelem |
| 4 | **Irony / Sarcasm (irónia, szarkazmus)** | felismerni vagy írni iróniát, szarkasztikus választ |
| 5 | **Reasoning (logikai érvelés)** | lépésről lépésre gondolkodtató magyar feladat |
| 6 | **Translation (fordítás)** | HU↔EN, HU↔DE, HU↔FR magas minőségű fordítás |
| 7 | **Math (matematika)** | magyar nyelvű szöveges matek feladat (árak, távolságok) |
| 8 | **History (magyar történelem)** | 1848, 1956, rendszerváltás, magyar tudósok, stb. |

A kategóriánkénti prompt-szám: 10 (egyszerűsített verzió) vagy 12-13 (teljes, 100-as verzió). A hu-eval projekt a **80 promptos** verziót használja a költség-hatékony iterációhoz.

## Multi-turn struktúra

Minden prompt **két fordulóból** áll:

1. **1. forduló:** az eredeti felhasználói kérdés
2. **2. forduló:** egy kontextuális follow-up, ami a modell első válaszára épül

**Példa — Irony kategória, 2. forduló:**

> 1. forduló: „Írj egy vicces Facebook-posztot arról, hogy a szomszéd megint 6-kor füvet nyír."
>
> 2. forduló: „Most írd át úgy, hogy a szomszéd legyen a főhős, aki büszke a felszerelésére — de az irónia maradjon meg."

A második forduló a modell **kontextus-megtartó** és **stílus-konzisztens** képességét teszteli.

## Értékelés: 1-10 skála + indoklás

Minden fordulót **1-10** közötti egész számmal pontozunk, és a bíró **kötelező** indoklást ad. A pontozási rubrika (magyarra fordítva, az eredeti MT-Bench alapján):

| Pont | Szint | Leírás |
|------|-------|--------|
| 1-2 | **Súlyosan hibás** | érthetetlen, teljesen off-topic, vagy káros |
| 3-4 | **Gyenge** | van némi értelmes tartalom, de sok hiba |
| 5-6 | **Átlagos** | megfelelő válasz, de nem kiemelkedő |
| 7-8 | **Jó** | jól strukturált, pontos, csak apróbb hiányosságok |
| 9-10 | **Kiváló** | emberi szintű vagy afeletti, kreatív, pontos |

Az aggregálás: **két forduló átlaga** (vagy súlyozott átlaga, ha a 2. forduló nehezebb).

## Pairwise (GSB) összehasonlítás

Az MT-Bench két értékelési módot támogat:

### 1. Single grading (abszolút)

- A bíró 1-10 skálán pontozza a választ önmagában.
- Előny: gyors, olcsó (1× inference).
- Hátrány: kalibráció nehéz, modell-összehasonlításnál a bíró referencia-eltolódása torzít.

### 2. Pairwise GSB (Good / Same / Bad)

A **GSB** a projekt által preferált módszer:

- A bíró **két választ** kap (A és B, véletlenül rendezve, hogy ne legyen pozíció-bias).
- Három lehetőség egyike:
  - **G** (Good): A jobb, mint B
  - **S** (Same): nagyjából egyforma
  - **B** (Bad): A rosszabb, mint B
- Eredmény: **win-rate** (A győzelmek aránya).

A GSB előnye: a bíró könnyebben dönt relatív összehasonlításban, mint abszolút pontozásban. Az LMSYS ChatbotArena is ezt használja.

## Bíró prompt template (magyar, GSB mód)

```text
Te egy magyar nyelvű LLM-bíró vagy. A feladatod: hasonlítsd össze a VÁLASZ_A
és VÁLASZ_B szöveget az alábbi szempontok szerint:

[INPUT — a felhasználó multi-turn kérdésének 2. fordulója]
{input_turn2}

[VÁLASZ_A — modell A válasza]
{response_a}

[VÁLASZ_B — modell B válasza]
{response_b}

[ÉRTÉKELÉSI SZEMPONTOK]
- Pontosság (fact-check, ha van referenciális tartalom)
- Stílus-konzisztencia az 1. fordulóval (kontextus-megtartás)
- Olvashatóság, magyar nyelvhelyesség
- Utasítás-követés (a 2. forduló kérésének teljesítése)
- Kreativitás / elegancia (kreatív feladatoknál)

[POZÍCIÓ-BIAS KIKÜSZÖBÖLÉSE]
A és B véletlenszerűen van rendezve; ne feltételezd, hogy bármelyik pozíció
eleve jobb. Döntésed kizárólag a szöveges tartalmon alapuljon.

[VÁLASZ FORMÁTUM]
{
  "gyoztes": "A" | "B" | "SAME",
  "bizalom": 0.0–1.0,        # mennyire vagy biztos a döntésben
  "indoklas": "2-4 mondat magyarul, konkrét szöveges hivatkozásokkal"
}
```

A `bizalom` mező fontos: a < 0.6 bizalmi döntéseket a projekt külön kezeli, és emberi felülvizsgálatra jelöli.

## Példa: teljes MT-Bench-HU futás

**1. forduló (Code kategória):**

> „Írj egy Python függvényt, ami kiszámítja egy lista mediánját! A függvény legyen type-hinted, a docstring és a megjegyzések magyar nyelvűek."

**Modell A (`minimax-m3:cloud`) válasz — 1. forduló:**

```python
from typing import List, Union

def median(lista: List[Union[int, float]]) -> float:
    """
    Kiszámítja egy számlista mediánját.

    Args:
        lista: A bemeneti számok listája.

    Returns:
        A medián értéke.
    """
    if not lista:
        raise ValueError("A lista nem lehet üres.")
    rendezett = sorted(lista)
    n = len(rendezett)
    if n % 2 == 1:
        return float(rendezett[n // 2])
    return (rendezett[n // 2 - 1] + rendezett[n // 2]) / 2
```

**2. forduló:**

> „Most add hozzá a függvényhez azt is, hogy a hibás típusú bemeneteket (pl. stringek a listában) kezelje: dobjon TypeError-t, és a hibaüzenet legyen magyar."

**Modell A válasz — 2. forduló:**

```python
from typing import List, Union

def median(lista: List[Union[int, float]]) -> float:
    # ... előző kód ...
    if not lista:
        raise ValueError("A lista nem lehet üres.")
    for elem in lista:
        if not isinstance(elem, (int, float)):
            raise TypeError(f"Csak számok lehetnek a listában, de '{elem}' típusa: {type(elem).__name__}")
    # ...
```

**Bíró (GSB) értékelés modell A vs. modell B (`qwen3.5:4b`):**

```json
{
  "gyoztes": "A",
  "bizalom": 0.82,
  "indoklas": "A válasz_A pontosabban kezeli a típus-ellenőrzést: a TypeError
  magyar nyelvű, konkrétan megnevezi a hibás elemet. A válasz_B csak egy
  generikus 'rossz típus' hibát dob, és a docstring frissítését is
  elmulasztja. Mindkét kód fut, de A részletesebb és jobban követi a
  2. forduló kérését."
}
```

## Limitációk

- **Magyar specifikus kategóriák (Irony, Formal Letter, History)** nehezebben skálázódnak, mint az általános kategóriák — magas az emberi spot-check szükséglet.
- **Bíró költség:** a 80 prompt × 2 forduló × bíró = 160 bíró hívás modellenként, ami `deepseek-v4-pro:cloud` (jelenlegi hivatalos bíró, 2026-07-19 óta) mellett is lassú (~30-45 perc). A `gemini-3-flash-preview:latest` megszűnt 2026-07-14.
- **Párosítás-kombinatorika:** 6 modell pairwise összehasonlítása = 15 pár, ami 1200 bíró hívás. Érdemes először abszolút pontozással szűrni, és csak a top 3-4 modellt pairwise futtatni.

## Összefüggés

- [HuGME](hugme-benchmark.md) — single-turn, metrika-alapú értékelés
- [Szabad kérdés HU](szabad-kerdes-hu.md) — kulturálisan specifikus, lazább
- [LLM-as-a-Judge](llm-as-judge.md) — bíró módszertan, GSB stratégia részletesen
- [Overview](../overview.md) — projekt kontextus
- [SCHEMA](../SCHEMA.md) — oldalformátum

## Hivatkozások

- Zheng et al. 2023, arXiv:2306.05685 — az eredeti MT-Bench paper
- FastChat repo: <https://github.com/lm-sys/FastChat> — `fastchat/llm_judge` könyvtár
- LMSYS ChatbotArena: <https://chat.lmsys.org/>
