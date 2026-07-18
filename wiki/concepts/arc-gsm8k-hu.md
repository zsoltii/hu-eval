# ARC-HU és GSM8K-HU

*Típus:* concept
*Forrás(ok):* https://huggingface.co/datasets/ai2_arc — ARC eredeti; https://huggingface.co/datasets/gsm8k — GSM8K eredeti; https://github.com/EleutherAI/lm-evaluation-harness — lm-eval keretrendszer; https://github.com/nytud/mlmm-evaluation — magyar benchmarkok
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Bevezetés — két benchmark, két feladattípus

Ez az oldal két, gyakran együtt futtatott magyar benchmarkot tárgyal:

- **ARC-HU** — az AI2 Reasoning Challenge magyar fordítása, **tudásalapú logikai következtetés**, multiple-choice formátumban.
- **GSM8K-HU** — a Grade School Math 8K magyar fordítása, **matematikai szöveges feladatok**, szabad szöveges válasszal (exact match).

Mindkettő az **mlmm-evaluation** GitHub repóban érhető el magyarul, és ugyanazt a `lm-evaluation-harness` keretrendszert használja futtatásra, de a kiértékelés módja gyökeresen eltérő (multiple-choice vs. exact match).

---

## ARC-HU — tudásalapú logikai következtetés

### Mi az ARC?

Az **ARC** (AI2 Reasoning Challenge, Clark et al. 2018) az Allen AI Institute által készített, **7-9. osztályos amerikai természettudományi vizsgák** kérdéseiből álló benchmark. 7787 kérdést tartalmaz, és a modell feladata a 4 válaszlehetőség közül kiválasztani a helyeset.

Két nehézségi szintje van:
- **ARC-Easy (ARC-E)**: 5197 kérdés, egyszerűbb, általában 1-2 lépéses következtetéssel megoldható.
- **ARC-Challenge (ARC-C)**: 2590 kérdés, nehezebb, gyakran 3+ lépéses gondolkodást igényel, és sok kérdés a modell „csapdáját" hivatott feltárni.

### ARC-HU — a magyar változat

A **NYTK** az mlmm-evaluation repóban publikálta az ARC magyar fordítását. A fordítás hasonló az MMLU-HU-hoz: gépi fordítás + humán ellenőrzés. A természettudományos kontextus (biológia, kémia, fizika, földrajz) jellemzően jól fordítható, de a kultúraspecifikus utalások (pl. amerikai államok, helyi fajok) néha értelmetlenné válnak.

### Példa kérdés (ARC-Challenge, magyar)

```
Kérdés: Egy növény leveleit permetezzük egy kísérletben. Az egyik levelet
       az alsó oldalán, a másikat a felső oldalán, a harmadikat mindkét
       oldalán. Ezután a növényt erős fénybe helyezzük. Melyik levelek
       maradnak zöldek legtovább?

A) Csak a felső oldalán permetezett
B) Csak az alsó oldalán permetezett
C) Mindkét oldalán permetezett
D) Mindhárom egyformán

Helyes válasz: B
```

A helyes válasz (B) a sztóma-elméleten alapul: a gázcsere az alsó oldalon történik, és ha eltömítjük, a fotoszintézis leáll.

### Formátum és prompt-protokoll

```python
ARC_PROMPT = """Az alábbi kérdés egy természettudományos vizsgakérdés.
Válaszolj egyetlen betűvel: A, B, C vagy D.

Kérdés: {question}

A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Válasz:"""
```

Alapértelmezetten **0-shot** (nincs példa), de a `lm-evaluation-harness` támogatja a few-shot módot is. A magyar modell-értékeléseknél általában 0-shot-ot használunk, mert a magyar nyelvű few-shot példák ritkák és a modell könnyen „elcsúszik" a formátumtól.

### Kiértékelés — multiple-choice scoring

```python
def arc_score(preds: list[str], labels: list[str]) -> float:
    """preds és labels: 'A'/'B'/'C'/'D' listák, azonos hosszúságú."""
    assert len(preds) == len(labels)
    correct = sum(p == l for p, l in zip(preds, labels))
    return correct / len(labels)
```

A `preds` listát a modell kimenetéből regex-pel nyerjük ki: `r"\b([ABCD])\b"` az első egyedi betű. Ha a modell nem ad betűt, `null`-t rögzítünk, és az ilyen példákat a riportban külön számláljuk („format failure rate").

### ARC-E és ARC-C külön riportálása

Mivel a két nehézségi szint nagyon más, mindig **külön riportoljuk** őket:

```python
ARC_RESULTS = {
    "arc_easy_hu": 0.78,        # 78% a könnyű halmazon
    "arc_challenge_hu": 0.51,   # 51% a nehéz halmazon
    "arc_overall_hu": 0.68,     # 68% együttesen (mikro-átlag)
}
```

Az **arc_overall** az Easy + Challenge egyesített pontossága (mikro-átlag, N=7787). Egyes riportok a kettő átlagát (makro) használják, de a mikro-átlag a gyakoribb, mert így a könnyű halmaz nagyobb súlyt kap (ami a valós felhasználáshoz közelebb áll).

### Gyakori buktatók — ARC-HU

1. **„Melyik a helyes" vs. „melyik a legjobb"** — egyes kérdéseknél a modell több opciót is helyesnek tart. A teszt a „legjobb" opciót várja, és csak azt fogadja el.
2. **Számok a szövegben** — ha a kérdés számokat tartalmaz (pl. „3 percig forraljuk"), a modell gyakran „elveszti" a számot a szövegben. A magyar nyelvű tokenizálók a számjegyeket néha több tokenre bontják.
3. **Nagybetűs opciók** — egyes modellek az opciókat kisbetűsnek írják vissza („a" helyett „A"), és ez a pontos match-et elrontja. A parser normalizáljon nagybetűsre.
4. **Több betűs válasz** — előfordul, hogy a modell „A és B" választ ad. Ilyenkor érdemes az első betűt venni (ebben az esetben „A"), de ezt a riportban jelöljük.

---

## GSM8K-HU — általános iskolai matematika

### Mi a GSM8K?

A **GSM8K** (Grade School Math 8K, Cobbe et al. 2021) 8500 **szöveges matematikai feladatot** tartalmaz, amelyek jellemzően 2-8 lépéses aritmetikai következtetést igényelnek. A feladatokat humán szerzők írták, és a megoldáshoz vezető gondolatmenetet is tartalmazzák (`solution` mező).

Példa (angol eredeti, magyar fordítás):

```
Kérdés: Józsefnek 3-szor annyi pénze van, mint Annának. Ha József ad
       2000 Ft-ot Annának, akkor Annának 2-szer annyi pénze lesz, mint
       Józsefnek. Mennyi pénzük volt eredetileg külön-külön?

Megoldás (gondolatmenet):
  Legyen Anna pénze x forint, Józsefé 3x.
  Átadás után: Anna = x + 2000, József = 3x - 2000.
  Feltétel: x + 2000 = 2 * (3x - 2000)
  x + 2000 = 6x - 4000
  6000 = 5x
  x = 1200
  Tehát Anna 1200 Ft, József 3600 Ft.

Válasz: 1200 és 3600
```

A helyes válasz az **numerikus eredmény** (vagy eredmények), nem a gondolatmenet.

### GSM8K-HU — a magyar változat

A **NYTK** a GSM8K magyar fordítását is közzétette az mlmm-evaluation repóban. A matematikai feladatok jellemzően könnyebben lokalizálhatók (pénznem, nevek, kontextus), mint a tudásalapú kérdések, de a magyar nyelvű matematikai szövegértés továbbra is kihívás a modelleknek.

### Formátum és prompt-protokoll — CoT (chain-of-thought)

A GSM8K-HU-nál alapértelmezetten **chain-of-thought (CoT) promptinget** használunk, azaz a modellnek lépésről lépésre kell levezetnie a megoldást, mielőtt kiadja a végső számot.

```python
GSM8K_COT_PROMPT = """Az alábbi feladatot lépésről lépésre oldd meg.
Az utolsó sorban CSAK a végső numerikus választ add meg, a
"#### SZÁM" formátumban (pl. "#### 42").

Példa:
Kérdés: Ha 3 alma van nálam, és adok 1-et, hány marad?
Megoldás: 3 - 1 = 2 alma marad.
#### 2

Kérdés: {question}
Megoldás:"""
```

A modell kimenete így néz ki egy jó válasznál:

```
Kérdés: Józsefnek 3-szor annyi pénze van, mint Annának...
Megoldás: Legyen Anna pénze x, Józsefé 3x. Átadás után Anna = x+2000,
József = 3x-2000. A feltétel: x+2000 = 2(3x-2000). Ebből x = 1200.
Tehát Anna 1200, József 3600.
#### 1200, 3600
```

A „####" marker fontos: a parser ebből olvassa ki a végső számot.

### Kiértékelés — exact match scoring

A GSM8K-HU kiértékelése **exact match**: a modell végső numerikus válaszát hasonlítjuk a referencia-értékhez. A szöveges gondolatmenetet nem pontozzuk.

```python
import re

def extract_gsm8k_answer(text: str) -> str | None:
    """Kiemeli a '#### SZÁM' sort, vagy az utolsó számot a szövegből."""
    m = re.search(r"####\s*([\d\.,]+)", text)
    if m:
        return m.group(1).strip()
    # Fallback: utolsó szám a szövegben
    nums = re.findall(r"[\d\.,]+", text)
    return nums[-1] if nums else None

def normalize_number(s: str) -> float:
    """Magyar/angol számformátum normalizálása float-ra."""
    return float(s.replace(" ", "").replace(",", "."))

def gsm8k_exact_match(pred_text: str, gold_text: str) -> bool:
    pred = extract_gsm8k_answer(pred_text)
    gold = extract_gsm8k_answer(gold_text)
    if pred is None or gold is None:
        return False
    try:
        return abs(normalize_number(pred) - normalize_number(gold)) < 1e-6
    except ValueError:
        return pred.strip() == gold.strip()
```

A pontosság így:

```python
def gsm8k_score(preds: list[str], golds: list[str]) -> float:
    return sum(gsm8k_exact_match(p, g) for p, g in zip(preds, golds)) / len(golds)
```

### Miért fontos a „####" marker?

Ha a modell szabad szöveges választ ad a végén (pl. „A válasz 1200 és 3600 forint"), akkor a `re.findall(r"[\d\.,]+", text)` az utolsó számot adná vissza (ami „3600"), de a helyes válasz két szám. A „####" marker explicit megoldásra kényszeríti a modellt, és a parser egyértelműen meg tudja találni a végső választ.

### CoT prompting — be/ki kapcsolás

A `lm-evaluation-harness` támogatja a CoT-ot a `--apply-chat-template` és a `--cot` flag-ekkel. A magyar nyelvű értékelésnél két lehetőségünk van:

1. **CoT magyarul**: a prompt magyar, a modell magyarul lépésenként vezet le. A magyar CoT erősebb nyelvészeti kötést ad, de egyes modelleknél rontja a pontosságot (mert a gondolkodási lánc „elcsúszik").

2. **CoT angolul**: a prompt és a gondolatmenet angol, csak a kérdés magyar. Ez meglepő módon **gyakran jobb eredményt ad**, mert a legtöbb modell CoT-példái angolok voltak a pre-training során.

```bash
# Magyar CoT (alapértelmezett)
python -m mlmm_eval.main --task gsm8k_hu --cot --cot-language hu

# Angol CoT (kísérleti)
python -m mlmm_eval.main --task gsm8k_hu --cot --cot-language en
```

### Gyakori buktatók — GSM8K-HU

1. **A modell kihagyja a „####" markert** — a fallback regex ilyenkor az utolsó számot veszi, ami lehet, hogy nem a végső válasz. Érdemes a „format failure" rátát külön riportálni.
2. **Magyar/angol tizedesvessző** — a magyarban `3,14` az angolban `3.14`. A `normalize_number` függvény mindkettőt kezeli, de a modell néha a másikat írja vissza.
3. **Pénznemek és mértékegységek** — a magyar verzió „Ft"-et használ, de a modell néha „$"-t ír vissza. Ez a parse-ot általában nem zavarja, mert a számot keressük.
4. **Több szám a válaszban** — ha a kérdés két számot kérdez (pl. „József és Anna pénze"), a modell gyakran csak az egyiket adja. Ilyenkor a `extract_gsm8k_answer` csak az utolsót veszi, és ez a „félig helyes" válasz elvész.
5. **Aritmetikai hibák** — a modell gyakran eljut a helyes gondolatmenetig, de az utolsó osztásban/szorzásban elszámolja magát. A CoT nem garantálja a helyes numerikus végeredményt.
6. **Kontextuális pénznem** — ha a magyar verzióban „Ft" szerepel, de a modell pre-trainingje amerikai dollárra volt tanítva, néha „dollárban" válaszol. Ez általában nem okoz parse-hibát, de a gold answer-vel való egyezéshez figyelni kell.

## Összehasonlítás — ARC-HU vs. GSM8K-HU

| Szempont | ARC-HU | GSM8K-HU |
|----------|--------|----------|
| Feladat típusa | tudás + logika | matematikai szöveges feladat |
| Kérdések száma | ~7787 (Easy + Challenge) | ~8500 |
| Válasz formátum | A/B/C/D betű | numerikus |
| Metrika | accuracy (multiple-choice) | exact match |
| CoT ajánlott? | nem (0-shot általában jobb) | igen (szinte kötelező) |
| Nehézség | közepes | közepes–nehéz |
| Kulturelfüggőség | magas (tudás) | alacsony (matematika) |

## Kombinált futtatás és riport

A két benchmarkot érdemes **egyetlen riportban** megjeleníteni, mert együttesen jól jellemzik a modell **„tanult tudás + gondolkodás"** profilját:

```python
COMBINED_RESULTS = {
    "arc_easy_hu":         0.78,
    "arc_challenge_hu":    0.51,
    "arc_overall_hu":      0.68,   # mikro-átlag
    "gsm8k_hu":            0.42,   # exact match, CoT-tal
    "gsm8k_hu_no_cot":     0.18,   # CoT nélkül jellemzően sokkal rosszabb
    "reasoning_composite": 0.55,   # = (arc_overall + gsm8k_hu) / 2
}
```

A `gsm8k_hu_no_cot` érték fontos kontroll: ha a CoT-s és CoT nélküli érték között hatalmas a rés (pl. 0.42 vs. 0.18), az azt mutatja, hogy a modell „tud lépésenként gondolkodni, de az eredményt nem tudja fejben tartani" — ez egy fontos modell-jellemző.

## Kapcsolódó

- [Overview](../overview.md) — projekt cél
- [SCHEMA](../SCHEMA.md) — wiki-formátum
- [HuLU Benchmark](hulu-benchmark.md) — magyar nyelvértés
- [MMLU-HU](mmlu-hu.md) — 38 tantárgy, tudás-teszt
- [Perplexitás](perplexity-hu.md) — nyelvmodell-minőség
- [Ollama API kliens](ollama-api-client.md) — modellek hívása
