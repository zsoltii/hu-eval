# Nem-HuLU benchmarkok — módszertani összefoglaló

*Típus:* concept
*Forrás(ok):*
- [MMLU-HU](mmlu-hu.md) — 38 tantárgy, 5-shot tudás-teszt (NYTK/hu-mmlu)
- [ARC + GSM8K-HU](arc-gsm8k-hu.md) — logikai és matematikai benchmarkok
- [Perplexitás](perplexity-hu.md) — nyelvmodell-minőség mérése
- [HuGME](hugme-benchmark.md) — generatív, LLM-as-a-Judge pontozás
- [MT-Bench-HU](mt-bench-hu.md) — multi-turn, LLM-as-a-Judge pontozás
- [UD Hungarian](ud-hungarian.md) — Universal Dependencies függőségi elemzés
- [Magyar morfológia](morfologia-hu.md) — toldalékolási szabályok
- [Nyelvészeti összefoglaló](nyelveszeti-osszefoglalo.md) — nyelvészeti dimenzió áttekintése
- [Karpathy LLM Wiki módszer](../../../llm-wiki/karpathy-llm-wiki-method.md) — elméleti háttér

*Létrehozva:* 2026-06-09
*Frissítve:* 2026-06-16 (v1.2.11 — 4 benchmark implementálva, scope szűkítve 5 benchmarkra)

---

## Áttekintés

A `hu-eval` projekt **5 benchmarkot** definiál az `scripts/aggregate_results.py` `STAT/GEN/LING` listáiban (v1.2.11):

| Kategória | Benchmark | Implementáció | Méret (val) | Metrika |
|-----------|-----------|---------------|-------------|---------|
| **STAT** | [HuLU](hulu-benchmark.md) | ✅ `run_hulu.py` | 2581 | accuracy |
| **STAT** | MMLU-HU | ✅ `run_mmlu_hu.py` (5-shot) | 1880 | accuracy per subject |
| **GEN** | HuGME | ✅ `run_hugme.py` + `judge_hugme.py` | 300 prompt × 6 metrika | judge score (0-1) |
| **GEN** | MT-Bench-HU | ✅ `run_mt_bench_hu.py` + `judge_mt_bench.py` | 24 kérdés × 2 forduló | GSB win rate (0-1) |
| **LING** | UD Hungarian | ✅ `run_ud_hungarian.py` | 137 mondat | (UPOS+UAS+LAS)/3 |

A következő benchmarkok **kimaradtak** (nincs magyar dataset vagy nem támogatott az Ollama API-n):
- ARC-HU (nincs magyar forrás)
- GSM8K-HU (nincs magyar forrás)
- Perplexitás (Ollama API nem ad logprobs-t)
- Magyar morfológia (nincs standard magyar teszt)
- Magyar szórend (nincs standard magyar teszt)

> 🛠️ **Implementációs státusz (2026-06-16):** a HuLU (kész, 19/19 benchmark) + MMLU-HU + HuGME + MT-Bench-HU + UD Hungarian mind implementálva, checkpoint-aware runnerekkel és judge scriptekkel. Az orchestrator (`queue_all_benchmarks.sh`) egyszerre futtatja az összes benchmarkot az összes modellre.

---

## Statisztikai benchmarkok (40% súly)

### 1. MMLU-HU (Massive Multitask Language Understanding — magyar)

**Mit mér:** a modell általános tudását 38 tantárgyban (természettudomány, társadalomtudomány, bölcsészet, jog, orvostudomány, stb.). A modell képes-e többszintű, iskolai/egyetemi szintű kérdésekre helyesen válaszolni.

**Forrás:** [NYTK/hu-mmlu](https://huggingface.co/datasets/NYTK/hu-mmlu) — a NYTK hivatalos fordítása az eredeti [hendrycks_test](https://huggingface.co/datasets/hendrycks_test) (MMLU) benchmarknak. **38 tantárgy**, 1880 validációs példa (a NYTK kihagyott néhányat a fordításból az eredeti 57-ből).

**Formátum:** standard 4-választásos MCQ (A/B/C/D):
- `prompt`: a kérdés szövege (magyarul)
- `choices`: 4 lehetséges válasz (A, B, C, D)
- `answer`: a helyes válasz indexe (0-3 INT, nem A/B/C/D string!)

**5-shot prompting:** a modell 5 példát lát kérdésenként (kérdés + helyes válasz), és a 6. kérdésre kell válaszolnia. A 5-shot kontextus javítja a pontosságot, mert a modell megtanulja a formátumot.

**Pipeline:**
1. `scripts/download_mmlu_hu.py` — letölti a NYTK/hu-mmlu "all" config validation + dev splitjét (38 tantárgy egyesítve), és egységes `data/mmlu_hu/mmlu_hu_std.jsonl` + `mmlu_hu_dev.jsonl` formátumba konvertálja
2. `scripts/run_mmlu_hu.py` — 5-shot promptot generál a dev splitből, a modellnek küldi, `extract_choice` 0-3 int-et keres
3. `scripts/aggregate_results.py` — a 38 tantárgy átlagából composite score-t számol

**Prompt formátum** (5-shot):
```
Kérdés: Melyik a Föld legnagyobb óceánja?
A) Atlanti-óceán
B) Indiai-óceán
C) Csendes-óceán
D) Jeges-tenger

Válasz: C

Kérdés: Ki írta a "Tüskevár" című regényt?
A) Móricz Zsigmond
B) Wass Albert
C) Jókai Mór
D) Karinthy Frigyes

Válasz: A

(... 3 további példa ...)

Kérdés: Melyik évben volt a mohácsi vész?
A) 1526
B) 1458
C) 1492
D) 1541

Válasz:
```

**Kiértékelés:** accuracy (helyes válaszok aránya). Tantárgyankénti bontás is megjelenik. Baseline (Qwen2-7B): ~40-50%, GPT-4: ~70%.

**Implementációs státusz:** ✅ runner kész (`run_mmlu_hu.py`). Letöltő + runner + aggregátor. 5-shot prompting, 38 subject breakdown.

---

### 2. ARC-HU (AI2 Reasoning Challenge — magyar)

**Mit mér:** a modell természettudományos (fizika, kémia, biológia) következtetési képességét általános iskolai szintű kérdéseken. A kérdések nehezek, mert a modell nem tudja "kitalálni" a választ — valódi tudásra van szükség.

**Forrás:** [ai2_arc](https://huggingface.co/datasets/allenai/ai2_arc) — AI2 eredeti benchmarkja, magyar fordítás (a NYTK vagy más fordító). Két nehézségi szint: **ARC-Easy** (~80% baseline acc) és **ARC-Challenge** (~25-40% baseline acc, nehéz).

**Formátum:** 4-választásos MCQ (A/B/C/D), természettudományos kérdések (pl. "Miért tűnik a Holdnak mindig ugyanaz az oldala?"). A kérdés lehet szöveges vagy tartalmazhat diagrammot (a magyar verzió általában szöveges).

**Pipeline:**
1. `scripts/download_arc_hu.py` (tervezett) — letölti az ARC Easy + Challenge validációs splitjét, és egységes JSONL-be konvertálja
2. `scripts/run_arc_hu.py` (tervezett) — few-shot prompt (0-shot vagy 3-shot), `extract_choice` 0-3 int
3. Aggregátor — Easy és Challenge átlag külön, vagy együtt

**Kiértékelés:** accuracy. ARC-Challenge a fontosabb (ott vannak a nehéz kérdések).

**Implementációs státusz:** ❌ kimaradt (v1.2.11 scope döntés: nincs magyar dataset az Ollama stacken).

---

### 3. GSM8K-HU (Grade School Math — magyar)

**Mit mér:** a modell általános iskolai szintű matematikai szöveges feladatok megoldási képességét. A modellnek lépésről lépésre kell gondolkodnia, és a végén egy numerikus választ adnia.

**Forrás:** [gsm8k](https://huggingface.co/datasets/gsm8k) — OpenAI eredeti benchmarkja, magyar fordítás. 1319 training + 250 test (validation) példa.

**Formátum:** nyílt szöveges matematikai feladat, ahol a modellnek lépésről lépésre kell levezetnie a megoldást, és a végén a `#### {szám}` formátumban megadnia a választ. Pl.:
```
Kérdés: Egy dobozban 12 ceruza van. Pistának 5-tel több, mint a dobozban lévő kétharmada. Hány ceruzája van Pistának?

Válasz (lépésről lépésre, végén a számmal):
12 ceruza van a dobozban. 12 × 2/3 = 8 ceruza a dobozban lévő kétharmad. Pistának 5-tel több = 8 + 5 = 13.
#### 13
```

**Pipeline:**
1. `scripts/download_gsm8k_hu.py` (tervezett) — letölti a validation splitet, és egységes JSONL-be konvertálja
2. `scripts/run_gsm8k_hu.py` (tervezett) — 0-shot vagy 8-shot chain-of-thought prompt. A modell válaszából regex `r"#### (-?\d+)"` kiemeli a végső számot
3. Aggregátor — accuracy (pontos egyezés a helyes számmal)

**Kiértékelés:** accuracy (a kiemelt szám pontosan megegyezik a gold értékkel). A lépésenkénti gondolkodás nem pontozódik, csak a végső szám.

**Nehézség:** a magyar nyelvű matematikai szöveges feladatok ritkák, és a fordítás során a számok/névmások cserélődhetnek. A modell gyakran rossz számra jut, ha nem érti a magyar szöveget.

**Implementációs státusz:** ❌ kimaradt (v1.2.11 scope döntés: nincs magyar dataset az Ollama stacken).

---

### 4. Perplexitás (PPL) magyar nyelven

**Mit mér:** a modell nyelvmodell-minőségét — mennyire "jól" generálja a természetes magyar szöveget. Az alacsony PPL jobb. A PPL a modell választási bizonytalanságát méri: `PPL = exp(-1/N * sum(log P(token_i | context)))`.

**Forrás:** a projekt egy magyar nyelvű szövegtestet használ (pl. a NYTK webcorpusából vagy magyar Wikipédiából kivágott ~1000 mondat). A standard az [NYTK](https://github.com/nytud) szövegek.

**Formátum:** nem kérdés-válasz, hanem a modell kap egy hosszú magyar szöveget, és a tokenenkénti log-likelihood-ból számoljuk a PPL-t:
- `PPL = exp(-1/N * sum(log P(token_i | token_1, ..., token_{i-1})))`
- Alacsonyabb PPL = a modell jobban "meglepi" a szöveget (várhatóbbnak találja) = jobb nyelvmodell

**Pipeline:**
1. `scripts/download_perplexity_hu.py` (tervezett) — letölti a magyar szövegtestet (pl. ~1000 mondat a Wikipédiáról)
2. `scripts/perplexity_hu.py` (tervezett) — a `stop_on_error.py`-ban lévő `call_ollama_strict` függvénnyel lekéri az Ollama API-tól a prompt_eval_count és prompt_eval_duration értékeket. A PPL kiszámítása: `ollama_eval_count / ollama_eval_duration` (token/sec), vagy a teljes szövegre aggregálva
3. Aggregátor — modellenkénti PPL, alacsonyabb jobb

**Kiértékelés:** PPL érték (folytonos). A `scripts/perplexity_hu.py` a `concepts/perplexity-hu.md` oldalon van dokumentálva, de még nincs implementálva.

**Tipikus értékek:**
- Erős magyar modell (XLM-R, huBERT): PPL ~30-50
- Közepes modell: PPL ~50-100
- Gyenge modell: PPL > 100

**Fontos megjegyzés:** a PPL-t a tokenizáló is befolyásolja. A magyar-specifikus tokenizáló alacsonyabb PPL-t ad, mert a magyar szavakat kevesebb tokenre bontja.

**Implementációs státusz:** ❌ kimaradt (v1.2.11 scope döntés: Ollama API nem ad logprobs-t, ezért PPL nem számolható).

---

## Generatív benchmarkok (40% súly)

### 5. HuGME (Hungarian Generative Model Evaluation)

**Mit mér:** a modell generatív képességét magyar nyelven — a modell szöveget generál, és egy **LLM-as-a-Judge** modell (jelenleg `gemini-3-flash-preview`) pontozza 1-5 skálán. A HuGME a magyar nyelvű szabad generálás minőségét méri.

**Forrás:** a projekt saját, kézzel összeállított 300 kérdésből áll (magyar nyelvű, különböző témák: kreativitás, összefoglalás, fordítás, stb.). A promptok magyar nyelvűek, és a modell 1-3 bekezdéses választ generál.

**Formátum:** nyílt szöveges generálás:
- `prompt`: magyar nyelvű kérdés vagy utasítás
- `response`: a modell által generált szöveg (1-3 bekezdés)
- `score`: 1-5 (a bíró modell pontozása)
- `rubric`: a pontozási szempontok (pl. "fluencia, relevancia, kreativitás")

**Pipeline:**
1. `scripts/download_hugme.py` (tervezett) — a 300 kézzel összeállított promptot JSONL-be írja
2. `scripts/run_hugme.py` (tervezett) — a modellnek küldi a promptokat, és a válaszokat elmenti
3. `scripts/judge_score.py` (tervezett) — a bíró modell (`gemini-3-flash-preview`) pontozza a válaszokat 1-5 skálán
4. Aggregátor — átlagos score modellenként, és a bíró modell konzisztenciája (Cohen-κ)

**Bíró prompt formátum:**
```
Kérdés: {prompt}
Modell válasza: {response}

Értékeld a választ 1-5 skálán az alábbi szempontok alapján:
1 = súlyos hibák (értelmetlen, nem releváns)
2 = sok hiba, érthető de rossz
3 = elfogadható, de nem kiemelkedő
4 = jó, jól megválaszolt
5 = kiváló, kreatív, pontos

Csak egy számot adj válaszul.
```

**Kiértékelés:** átlagos bíró score (1-5). A bíró modell pontosságát emberi spot-check-kel validáljuk (Cohen-κ a magyar referenciákon ~0.71).

**Implementációs státusz:** ✅ `run_hugme.py` + `judge_hugme.py`. 300 prompt (6 metrika × 50). A bíró `gemini-3-flash-preview`. Nincs DeepEval wrapper — a judge_hugme.py saját promptokkal hívja az LLM-et. `judge.overall` = 6 metrika átlaga (0-1).

---

### 6. MT-Bench-HU (Multi-Turn Benchmark — magyar)

**Mit mér:** a modell multi-turn (többfordulós) beszélgetési képességét. A modell 80 kérdésből álló, 2 fordulós beszélgetést folytat, és egy LLM-as-a-Judge pontozza a válaszokat GSB (Good/Same/Bad) pairwise összehasonlítással.

**Forrás:** [MT-Bench](https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge) (LMSYS) magyar fordítása. 80 kérdés 8 kategóriában (writing, roleplay, reasoning, math, extraction, stem, humanities, coding).

**Formátum:** 2 fordulós beszélgetés:
- 1. forduló: a modell válaszol az eredeti kérdésre
- 2. forduló: a modell válaszol egy follow-up kérdésre (az 1. forduló alapján)
- A bíró modell **páronként** hasonlítja össze két modell válaszait, és GSB-t ad (Good/Same/Bad)

**Pipeline:**
1. `scripts/download_mt_bench_hu.py` (tervezett) — a 80 kérdést JSONL-be írja
2. `scripts/run_mt_bench_hu.py` (tervezett) — a modellnek küldi a kérdéseket (2 forduló), és a válaszokat elmenti
3. `scripts/judge_mt_bench.py` (tervezett) — a bíró modell (`gemini-3-flash-preview`) GSB-t ad minden modellpárra
4. Aggregátor — win rate modellenként, kategóriánkénti bontás

**Bíró prompt formátum** (GSB):
```
Kérdés: {question}
Modell A válasza: {response_A}
Modell B válasza: {response_B}

Melyik válasz jobb? Válaszolj A, B, vagy S (egyenlő) betűvel.
```

**Kiértékelés:** win rate (hányszor nyer A vs B). A bíró modell pozíció-bias elkerülése érdekében a bíró felváltva látja A-t és B-t először (counterbalanced).

**Implementációs státusz:** ✅ `run_mt_bench_hu.py` + `judge_mt_bench.py`. 24 kérdés (8 kategória × 3), 2 forduló. Baseline modell: `deepseek-v4-flash:cloud`. GSB pairwise, counterbalanced (swap). Win rate 0-1.

---

## Nyelvészeti mélytesztek (20% súly)

### 7. UD Hungarian (Universal Dependencies — magyar)

**Mit mér:** a modell szintaktikai elemzési képességét — képes-e egy magyar mondat szófaj-címkéit (POS tagging), morfológiai jellemzőit, és függőségi viszonyait (dependency parsing) helyesen azonosítani.

**Forrás:** [Universal Dependencies](https://universaldependencies.org/treebanks/hu_szeged.html) — a `hu_szeged` treebank (~1000 mondat, manuálisan annotálva). A CoNLL-U formátum a standard.

**Formátum:** CoNLL-U (tab-szeparált, 10 oszlop):
```
# sent_id = 1
# text = A macska alszik a kanapén.
1   A       a       DET     _       Definite=Def|PronType=Art   2   det     _   _
2   macska  macska  NOUN    _       Case=Nom|Number=Sing         3   nsubj   _   _
3   alszik  alszik  VERB    _       Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin   0   root    _   _
4   a       a       DET     _       Definite=Def|PronType=Art   5   det     _   _
5   kanapén kanapé NOUN    _       Case=Sup|Number=Sing          3   obl     _   SpaceAfter=No
6   .       .       PUNCT   _       _                            3   punct   _   _
```

**Pipeline:**
1. `scripts/download_ud_hungarian.py` (tervezett) — a hu_szeged treebank CoNLL-U fájlját JSONL-be konvertálja
2. `scripts/run_ud_hungarian.py` (tervezett) — a modellnek küldi a mondatot, és a válaszból parse-olja a POS/DEP címkéket
3. Aggregátor — UAS (Unlabeled Attachment Score), LAS (Labeled Attachment Score), POS accuracy

**Kiértékelés:**
- **UAS** (Unlabeled Attachment Score): a függőségi viszonyok helyes aránya (fej szó indexe)
- **LAS** (Labeled Attachment Score): UAS + a függőség típusának helyessége
- **POS accuracy**: a szófaji címkék helyes aránya
- **Morfológiai accuracy**: az eset, szám, személy, stb. címkék helyes aránya

**Baseline:** UDPipe magyar modell: UAS ~85%, LAS ~80%, POS ~95%. A magyar LLM-ek általában gyengébbek, mert a szintaktikai elemzés nem a fő erősségük.

**Implementációs státusz:** ✅ `download_ud_hungarian.py` + `run_ud_hungarian.py`. 137 mondat a GitHub raw `hu_szeged-ud-test.conllu` fájlból. A modell válaszából regex kinyerés (TOKEN/UPOS/HEAD/DEPREL). Composite = (UPOS + UAS + LAS) / 3.

---

### 8. Magyar morfológia (Deep Test)

**Mit mér:** a modell toldalékolási szabályok ismeretét. Képes-e helyesen toldalékolni egy szót (pl. "ház" → "házban", "házak", "házhoz") a kontextus alapján.

**Forrás:** kézzel összeállított 200 mondatos teszt (NYTK vagy a projekt sajátja), amely különböző toldalékolási eseteket fed le:
- Esetragok (nominativus, accusativus, dativus, stb.)
- Birtokos személyragok (-m, -d, -a, -ja, -nk, -tok, -juk, stb.)
- Többes szám (-k, -ok, -ek, -ak)
- Igeragozás (személy, szám, idő, mód)
- Melléknévfokozás (-bb, -leg, -bbnél, stb.)
- Képzők (-ság, -ség, -zat, -zet, stb.)

**Formátum:** cloze-teszt (kitöltős):
```
Kérdés: A macska a (ház___) alszik.
A) ház
B) házban
C) házból
D) házra

Válasz: B
```

VAGY: szabad szöveges kiegészítés, ahol a modell beírja a helyes toldalékot:
```
Kérdés: Töltsd ki az üres helyet: A macska a ház___ alszik.
Válasz: házban
```

**Pipeline:**
1. `scripts/download_morfologia_hu.py` (tervezett) — a 200 mondatos teszt JSONL-be írása
2. `scripts/run_morfologia_hu.py` (tervezett) — 0-shot vagy 3-shot prompt, `extract_choice` 0-3 int (MCQ) VAGY regex a szöveges kitöltésre
3. Aggregátor — accuracy kategóriánként (eset, szám, ige, melléknév, képző)

**Kiértékelés:** accuracy (MCQ-nál) vagy exact match (szöveges kitöltésnél). Kategóriánkénti bontás fontos, mert a modell lehet jó esetben, de gyenge igében.

**Nehézség:** a magyar toldalékolás rendkívül szabályos, de a mély agglutináció miatt egy szó 5-6 toldalékot is viselhet (-házaikban = -ház + -a + -i + -k + -ban). A modell tokenizálója gyakran szétszabdalja a toldalékokat, ami rontja a teljesítményt.

**Implementációs státusz:** ❌ kimaradt (v1.2.11 scope döntés: nincs standard magyar teszt).

---

## Aggregáció és composite score

A `scripts/aggregate_results.py` az 5 benchmark eredményeit a három dimenzióba aggregálja (v1.2.11):

- **STAT (40%):** HuLU + MMLU-HU
- **GEN (40%):** HuGME + MT-Bench-HU
- **LING (20%):** UD Hungarian

A composite score:
```python
def composite_score(stat_scores, gen_scores, ling_scores):
    """stat/gen/ling: list[float] 0-1 közti értékek."""
    w_stat, w_gen, w_ling = 0.40, 0.40, 0.20
    stat = sum(stat_scores) / len(stat_scores)
    gen = sum(gen_scores) / len(gen_scores)
    ling = sum(ling_scores) / len(ling_scores)
    return (w_stat * stat + w_gen * gen + w_ling * ling) * 100
```

Ha egy dimenzióból hiányoznak eredmények, a súlyok újraosztódnak a jelenlévőkre (a kód ezt kezeli).

---

## Implementációs státusz (v1.2.11)

A HuLU-n kívüli 4 benchmark implementálva van. Az alábbi benchmarkok **kimaradtak** (nincs magyar dataset / Ollama limitáció):

| Benchmark | Kimaradás oka |
|-----------|---------------|
| ARC-HU | nincs magyar forrás |
| GSM8K-HU | nincs magyar forrás |
| Perplexitás | Ollama API nem ad logprobs-t |
| Magyar morfológia | nincs standard magyar teszt |
| Magyar szórend | nincs standard magyar teszt |

A meglévő 5 benchmark mindegyike checkpoint-aware, timeout-specifikus, és a `queue_all_benchmarks.sh` segítségével egyszerre futtatható.

**A sorrend (implementálva):**

1. **HuLU** — kész (19/19 modell × mód)
2. **MMLU-HU** — 5-shot, 38 subject
3. **HuGME** — 300 prompt, 6 metrika, LLM judge
4. **MT-Bench-HU** — 24 kérdés, 2 turn, GSB pairwise
5. **UD Hungarian** — 137 mondat, CoNLL-U parse

---

## Kapcsolódó

- [HuLU Benchmark](hulu-benchmark.md) — részletes HuLU leírás (v1.2.6)
- [Overview](../overview.md) — projekt cél, hatókör, három dimenzió
- [SCHEMA](../SCHEMA.md) — wiki-oldalak formátuma
- [Tervezési elv: checkpoint](../concepts/checkpoint-progress.md) — stop-on-error + resume
- [LLM-as-Judge](llm-as-judge.md) — bíró modell használata generatív benchmarkoknál
- [Runbook: HuLU futtatás](../runbooks/run-hulu-modell-x.md) — lépésről lépésre pipeline
- [Runbook: bíró prompt template](../runbooks/llm-judge-prompt-template.md) — bíró promptok
- [Aggregáció](../runbooks/aggregate-results.md) — composite score számítás
- [Nyelvészeti összefoglaló](nyelveszeti-osszefoglalo.md) — LING dimenzió áttekintése
