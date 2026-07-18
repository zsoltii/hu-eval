# HuLU Benchmark

*Típus:* concept
*Forrás(ok):* [Nytud/HuLU](https://github.com/nytud/HuLU) — NYTK hivatalos meta-repo; LREC-COLING 2024 cikk (Yang et al.); 6 NYTK HuggingFace sub-task dataset
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-16 (v1.2.10 — nehézség-statisztikák is törölve, csak per-modell + per-sub-task maradt)

---

## Mi a HuLU?

A **HuLU** (Hungarian Language Understanding) a NYTK (Nyelvtudományi Kutatóközpont, Budapest) által 2022-ben kiadott, magyar nyelvű GLUE-szerű benchmark-csomag. Célja, hogy a magyar nyelvi modellek nyelvértését egységes, reprodukálható keretrendszerben mérje — hasonlóan az angol GLUE/SuperGLUE benchmarkokhoz.

A benchmark **6 NLU sub-taskból** áll, plusz egy 7., különböző formátumú olvasásértő (RC) datasetből (HuRC — lásd lentebb). Mind a 6 NLU sub-taskot ugyanaz a formátum (JSONL, tanító/dev/teszt split, magyar prompt, 0-1 label) és ugyanaz a kiértékelési protokoll (accuracy vagy MCC) jellemzi.

> ⚠️ Fontos: a HuLU kizárólag **statisztikai (determinisztikus) benchmark**. Nem igényel LLM-as-a-Judge bírót, így olcsó, gyors, és felhőfüggetlenül reprodukálható.

> 🛠️ **Implementációs státusz (2026-06-09):** a `hu-eval` projektben a **6 NLU sub-task van implementálva** a `scripts/download_hulu.py` + `scripts/run_hulu.py` pipeline-ban. HuRC külön formátumú (cloze-style), és nincs letöltve/futtatva.

## A 6 NLU sub-task — összefoglaló

| Task | Mit mér? | Bemenet | Kimenet | Metrika | N (val) |
|------|----------|---------|---------|---------|---------|
| **HuCOLA** | morfológiai/szintaktikai elfogadhatóság | 1 mondat | bináris (0/1) | Matthews korreláció (MCC) | 910 |
| **HuCoPA** | ok-okozati következtetés | premise + 2 choice | bináris (0/1) | pontosság | 100 |
| **HuRTE** | olvasásértő entailment | premise + hypothesis | bináris (0/1) | pontosság | 243 |
| **HuSST** | érzelem-polaritás (sentiment) | 1 szöveg | 3 osztály (0/1/2) | pontosság | 1165 |
| **HuWNLI** | névmás-referencia + NLI | 2 mondat (Winograd) | bináris (0/1) | pontosság | 60 |
| **HuCB** | természetes nyelvű inferencia (NLI) | premise + hypothesis | 3 osztály (0/1/2) | pontosság | 103 |
| **Összesen** | | | | | **2581** |

A 2581 validációs példa task-sorrendben van a `data/hulu/hulu_std.jsonl`-ben: HuCOLA (910) → HuCoPA (100) → HuRTE (243) → HuSST (1165) → HuWNLI (60) → HuCB (103).

---

## Sub-task részletek

### 1. HuCOLA — Magyar nyelvtani elfogadhatóság (Corpus of Linguistic Acceptability)

**Mit ellenőriz:** a modell anyanyelvi szintű morfológiai és szintaktikai tudását. Képes-e felismerni, hogy egy magyar mondat nyelvtanilag helyes-e vagy sem?

**Felépítés:** minden példa egyetlen magyar mondat. A mondatok fele helyes (label=1), fele pedig szándékosan helytelen (label=0). A helytelen mondatok jellemzően:
- morfológiai egyeztetési hibát tartalmaznak (pl. „A kutya ugatnak a kertben." — az alany és az ige nincs egyeztetve)
- igeragozási hibát (pl. „A gyerekek játszanakék.")
- névelőhiányt vagy -többletet
- értelmetlen szókapcsolatot (szemantikai anomália)

**Prompt formátum** (a `download_hulu.py` `build_prompt` függvényéből):
```
Döntsd el, hogy az alábbi magyar mondat nyelvtanilag helyes-e.
Válaszolj CSAK egy számmal: 0 (helytelen) vagy 1 (helyes).

Mondat: {sentence}

Válasz:
```

**Kiértékelés:** Matthews Correlation Coefficient (MCC), -1 és +1 között. Az MCC jobban kezeli a kiegyensúlyozatlan osztályokat, mint a sima pontosság. Referencia-emberi teljesítmény: ~0.78 MCC. Erős baseline (XLM-R large): ~0.65 MCC.

**Példa:**
- Helyes: „A macska alszik a kanapén." → label=1
- Helytelen: „A macska alszikék a kanapén." → label=0

**Nehézség:** a magyar nyelv agglutináló (sok toldalék), és a toldalékok gyakran szétszakadnak a SentencePiece/BPE tokenizálásban, ami rontja a modell teljesítményét. A magyar-specifikus tokenizer (pl. XLM-R, huBERT) előnyt jelent.

---

### 2. HuCoPA — Ok-okozati következtetés (Choice of Plausible Alternatives)

**Mit ellenőriz:** a modell kauzális reasoning képességét. Képes-e felismerni, hogy egy adott premissza melyik folytatása okszerűbb (ok-okozati viszony)?

**Felépítés:** minden példa egy premissza és két lehetséges folytatás. A modell feladata kiválasztani az okszerűbb folytatást. Az okszerűség lehet:
- **okozat** (effect): a premissza MIATT következik be a folytatás
- **ok** (cause): a premissza MIÉRT következett be

Példa: „A tűzjelző megszólalt." → „A dolgozók elhagyták az épületet." (okozat) vs. „A dolgozók folytatták a munkát." (nem okszerű)

**Prompt formátum:**
```
Az alábbi premisszához melyik folytatás illik jobban (az oksági viszony alapján)?
Válaszolj CSAK egy számmal: 0 (első) vagy 1 (második).

Premissza: {premise}
0) {choice1}
1) {choice2}

Válasz:
```

**Kiértékelés:** pontosság. Baseline (XLM-R large): ~65-70% accuracy.

**Példa:**
- Premissza: „A férfi elvesztette a hallását."
- 0: „Majdnem megfulladt az óceánban." (nem okszerű)
- 1: „Majdnem meghalt egy robbanásban." (okszerű — hangos robbanás → hallásvesztés)
- label=1

**Adatbázis megjegyzés:** a NYTK/HuCoPA HF datasetben a label **1-indexelt STRING** (`"1"` / `"2"`), nem 0-indexelt. A `download_hulu.py` `int(label) - 1` transzformációval javítja. A `nytud/HuCoPA` git submodule-ban 0-indexelt INT van — a `_g()` helper mindkettőt kezeli.

---

### 3. HuRTE — Olvasásértő entailment (Reading Textual Entailment)

**Mit ellenőriz:** a modell képes-e entailment viszonyt felismerni két mondat között. Ha a premissza igaz, a hipotézis is igaz-e (entailment), vagy nem feltétlenül (not_entailment)?

**Felépítés:** minden példa egy premissza és egy hipotézis. A modell feladata eldönteni, hogy a hipotézis **következik-e** a premisszából (label=1) vagy sem (label=0). Bináris osztályozás.

**Prompt formátum:**
```
Az alábbi hipotézis NEM következik-e a premisszából? (ellentmondás vagy semleges)
Válaszolj CSAK egy számmal: 0 (nem, a hipotézis ellentmond a premisszának) vagy 1 (igen, a hipotézis következik a premisszából).

Premissza: {premise}
Hipotézis: {hypothesis}

Válasz:
```

**Kiértékelés:** pontosság. Baseline: ~80-90% accuracy (a feladat viszonylag egyszerű a többi NLI-hez képest).

**Példa:**
- Premissza: „Dana Reeve, a színész Christopher Reeve özvegye 44 éves korában halt meg tüdőrákban."
- Hipotézis: „Christopher Reeve-nek balesete volt." (nem releváns a premisszából → label=0)
- Ellenpélda: Premissza: „A Caritas bejelentette, hogy Bagdad bombázása során több iraki vesztette életét." + Hipotézis: „Iraki emberek haltak meg." → label=1 (entailment)

**Fontos megjegyzés:** a prompt az „inverz" logikát használja — a modellnek a „NEM következik" kérdésre kell válaszolnia 0-val (ellentmondás) vagy 1-gyel (entailment). Ez a v1.2 smoke teszt során kiderült inverzió volt (az eredeti prompt „következik" volt, de a HF label 0=not_entailment, 1=entailment). A javított prompt konzisztens a label-ekkel.

---

### 4. HuSST — Magyar sentiment analysis

**Mit ellenőriz:** a modell képes-e felismerni egy magyar szöveg érzelmi polaritását (negatív, semleges, pozitív). Ez a klasszikus 3-osztályos sentiment feladat.

**Felépítés:** minden példa egy magyar szöveg (rövid, 1-3 mondat, gyakran filmkritikák, termékértékelések). A modell feladata a szöveg hangulatának 3 osztályba sorolása:
- **0 (negatív):** panasz, kritika, rossz tapasztalat
- **1 (semleges):** tényszerű leírás, vegyes érzések
- **2 (pozitív):** dicséret, elégedettség, pozitív élmény

**Prompt formátum:**
```
Az alábbi szöveg milyen hangulatú?
Válaszolj CSAK egy számmal: 0 (negatív), 1 (semleges), vagy 2 (pozitív).

Szöveg: {text}

Válasz:
```

**Kiértékelés:** pontosság. Baseline: ~65-75% accuracy. Osztály-eloszlás: negatív (kb. 35%), semleges (kb. 25%), pozitív (kb. 40%).

**Adatbázis megjegyzés:** a HF-ben a label **STRING** (`"negative"` / `"neutral"` / `"positive"`), nem int. A `download_hulu.py` `normalize_label` függvénye `{"negative": 0, "neutral": 1, "positive": 2}` mapping-gel konvertál.

**Példa:**
- „Nos, a Jason elment Manhattanbe és a Pokolba kapcsán, azt hiszem, az elkerülhetetlen folytatások ötletlistájáról kihúzhatunk egy űrállomást 2455-ben." → label=1 (semleges, vegyes)
- „Ez egy fantasztikus film, minden percét élveztem." → label=2 (pozitív)
- „Nagy csalódás, a színészek gyengén játszottak, a történet unalmas." → label=0 (negatív)

---

### 5. HuWNLI — Magyar Winograd NLI (referenciafeloldás)

**Mit ellenőriz:** a modell referenciális következtetési képességét. Képes-e egy névmás (általában „ő", „az", „ez") referenciáját feloldani egy előző mondatból, és eldönteni, hogy a behelyettesítés után a második mondat természetes marad-e?

**Felépítés:** minden példa két mondat, ahol az első mondat tartalmaz egy névmási antecedenst, a második mondatban pedig egy névmás van, amely erre utal. A modell feladata eldönteni, hogy a névmás behelyettesítése az antecedenssel természetes-e (label=0) vagy természetlen (label=1).

Ez a feladat a klasszikus **Winograd Schema Challenge** magyar változata: egyetlen szó megváltoztatása a második mondatban a referenciát is megváltoztatja, és a modellnek ezt a finom referenciaváltást kell felismernie.

**Prompt formátum:**
```
Az első mondatban lévő névmás a második mondatba behelyettesítve természetes marad-e?
Válaszolj CSAK egy számmal: 0 (igen, természetes, a második mondat igaz) vagy 1 (nem, természetlen, a második mondat nem igaz).

1) {sentence1}
2) {sentence2}

Válasz:
```

**Kiértékelés:** pontosság. Ez a **legnehezebb** sub-task: a legjobb modellek is 40-55% accuracy-t érnek el, ami közel van a 50%-os véletlen baseline-hoz. A referenciafeloldás nehézsége: a modellnek a világismeretére kell támaszkodnia, nem csak a felszíni szintaxisra.

**Példa:**
- 1: „A lefolyót eldugította a haj. Ki kell tisztítani."
- 2: „A hajat ki kell tisztítani." → label=0 (természetes, a haj okozta a dugulást)
- Ellenpélda: 1: „A lefolyó tele van vízzel." + 2: „A vizet ki kell önteni." → label=1 (természetlen, a lefolyót nem kell kiönteni)

---

### 6. HuCB — CommitmentBank (NLI fokozatok)

**Mit ellenőriz:** a modell NLI (Natural Language Inference) képessége 3 fokozatban. A modellnek nem binárisan kell dönteni, hanem 3 osztály közül választani: ellentmondás, semleges, vagy következmény (entailment).

**Felépítés:** minden példa egy premissza és egy hipotézis. A modell feladata a két mondat viszonyát 3 osztályba sorolni:
- **0 (ellentmondás / contradiction):** a hipotézis ELLENTMOND a premisszának
- **1 (semleges / neutral):** a hipotézis NEM KÖVETKEZIK a premisszából, de nem is mond ellent (kiegészítő információ)
- **2 (következmény / entailment):** a hipotézis KÖVETKEZIK a premisszából

Ez a standard **SNLI/MultiNLI** formátum magyar változata, 3 osztállyal (ellentétben a HuRTE bináris formátumával).

**Prompt formátum:**
```
Milyen viszony van az alábbi két mondat között?
Válaszolj CSAK egy számmal: 0 (ellentmondás), 1 (semleges), vagy 2 (következmény).

1) {premise}
2) {hypothesis}

Válasz:
```

**Kiértékelés:** pontosság. Osztály-eloszlás: entailment (40%), neutral (25%), contradiction (35%). Baseline: ~60-75% accuracy.

**Adatbázis megjegyzés:** a HF label STRING (`"entailment"` / `"neutral"` / `"contradiction"`). A `download_hulu.py` mapping: `{"contradiction": 0, "neutral": 1, "entailment": 2}` — a prompt sorrendjéhez igazítva (ellentmondás=0, semleges=1, entailment=2).

**Példa:**
- 1: „A Mikhál tudta már jól, hogy nem a kecskebak hozta." + 2: „A beszélő szerint vereséget szenvedtek." → label=0 (ellentmondás)
- 1: „Riporter: Kételkedtek vagy inkább csak legyintettetek." + 2: „Balázs Zoltán szerint válság lesz." → label=2 (entailment)
- 1: „Á.S.: Hát elsősorban a személyem ilyen, mindenen..." + 2: „Á.S. szerint az egész világ ellenük van." → label=0 (ellentmondás)

---

## Hogyan működik a benchmark — pipeline

A `hu-eval` projekt 4 lépcsős pipeline-t használ a HuLU futtatásához:

### 1. Letöltés (`scripts/download_hulu.py`)

A script két forrásból tud letölteni:
- **HuggingFace** (alapértelmezett, online): `NYTK/HuCOLA`, `NYTK/HuCoPA`, `NYTK/HuRTE`, `NYTK/HuSST`, `NYTK/HuWNLI`, `NYTK/HuCommitmentBank` — validation split
- **Git** (`--offline` flag): `git clone --recurse-submodules https://github.com/nytud/HuLU.git` — a NYTK meta-repo submoduljaiból

A letöltött rekordok mezőnevei a forrástól függően camelCase (HF: `Sent_id`, `Sent`, `Label`) vagy snake_case (git: `sent_id`, `sent`, `sent_label`). A `_g(rec, *nevek, default)` helper mindkettőt kezeli. A labelek normalizálva vannak:
- HuCOLA/HuWNLI/HuRTE/HuCoPA: int 0/1 (a HF HuCoPA label 1-indexelt, `int(label) - 1` javítja)
- HuSST: string `negative`/`neutral`/`positive` → int 0/1/2
- HuCB: string `entailment`/`neutral`/`contradiction` → int 0/1/2

### 2. Standardizálás (`data/hulu/hulu_std.jsonl`)

Minden rekord egységes formátumba kerül:
```json
{
  "id": "hulu_hucola_00000",
  "task": "hucola",
  "prompt": "<magyar prompt szöveg>",
  "choices": ["0", "1"],
  "answer_index": 0,
  "source": "NYTK/HuCOLA"
}
```

A `prompt` mező a `build_prompt(task, rec)` függvényből jön, ami task-specifikus magyar promptot generál. A `choices` a lehetséges label-értékek listája. Az `answer_index` a helyes label indexe a `choices` listában. A `source` a HF dataset neve.

A task-sorrend a standardizált fájlban: HuCOLA → HuCoPA → HuRTE → HuSST → HuWNLI → HuCB.

### 3. Futtatás (`scripts/run_hulu.py`)

A `run_hulu.py` a `hulu_std.jsonl`-t olvassa, és minden rekordot elküld az Ollama API-nak. A modell válaszából az `extract_choice(text, num_choices)` függvény kiemeli a label-t:

```python
def extract_choice(text: str, num_choices: int) -> int:
    if not text:
        return -1
    m = re.search(r"\b([0-9])\b", text)
    if m and 0 <= int(m.group(1)) < num_choices:
        return int(m.group(1))
    magyar = {
        "nulla": 0, "egy": 1, "kettő": 2, "három": 3, "négy": 4,
        "öt": 5, "hat": 6, "hét": 7, "nyolc": 8, "kilenc": 9,
    }
    for szo, n in magyar.items():
        if szo in text.lower() and n < num_choices:
            return n
    return -1
```

Az `extract_choice` először a regex-szel keres számjegyet (0-9), és ha talál, visszaadja. Ha nem talál, a magyar szavakat (nulla, egy, kettő, ...) próbálja. Ha egyik sem, -1 (üres válasz).

A futtatás két módban történhet:
- **`--mode nothink`** (alapértelmezett, num_predict=4096): a gondolkodás el van nyomva, a modell közvetlenül válaszol
- **`--mode think`** (num_predict=16384): a modell gondolkodhat, a gondolkodás a `response` mezőben megjelenik

A két mód eredményei külön mappákba kerülnek:
- `state/{model_safe}-nothink/hulu.json` és `state/{model_safe}-think/hulu.json`
- `results/{model_safe}-nothink/hulu_results.jsonl` és `results/{model_safe}-think/hulu_results.jsonl`

A `model_safe` a modellnévből képződik: `model.replace(":", "-").replace("/", "-") + f"-{mode}"`. Például `gpt-oss:120b-cloud` + `think` → `gpt-oss-120b-cloud-think`.

### 4. JSONL rekordok mezői (v1.2.5)

Minden futtatott rekord a JSONL fájlba íródik az alábbi mezőkkel:

```json
{
  "id": "hulu_hucola_00000",
  "task": "hucola",
  "prompt": "<prompt szöveg>",
  "choices": ["0", "1"],
  "gold": 0,
  "raw_response": "1",
  "prediction": 1,
  "correct": false,
  "mode": "nothink",
  "ollama_total_duration_ns": 1234567890,
  "ollama_load_duration_ns": 12345678,
  "ollama_prompt_eval_count": 246,
  "ollama_prompt_eval_duration_ns": 234567890,
  "ollama_eval_count": 5,
  "ollama_eval_duration_ns": 12345678,
  "ollama_done_reason": "stop"
}
```

- `gold` = `answer_index` (a helyes label)
- `prediction` = az `extract_choice` által kiemelt label (-1 ha üres)
- `correct` = `prediction == gold`
- `mode` = `"nothink"` vagy `"think"`
- `ollama_*` mezők = az Ollama API válaszából (teljesítmény-metrikák)

### 5. Checkpoint rendszer (stop-on-error + resume)

A futtatás **stop-on-error** szemantikát követ:
- HTTP 400/404/422 → azonnali stop (konfigurációs hiba)
- HTTP 429/5xx → max 3 retry, Retry-After header alapján
- Timeout → max 3 retry, exponenciális backoff
- ConnectionError → azonnali stop

A state a `state/{model_safe}-{mode}/hulu.json`-ban mentődik atomi write-tal (`tmp + os.replace`). A JSONL fájl append-only, minden rekord után `flush + fsync`. A futtatás bármikor RESUME-olható: `python scripts/run_hulu.py --model X --mode Y` (a `--reset` nélkül onnan folytat, ahol abbahagyta).

A `--limit N` flag task-szintű: `--limit 10` → 10 HuCOLA + 10 HuCoPA + 10 HuRTE + 10 HuSST + 10 HuWNLI + 10 HuCB = 60 prompt.

### 6. Aggregáció (`scripts/aggregate_results.py`)

Az aggregátor a `results/{model_safe}-{mode}/hulu_results.jsonl` és `hulu_summary.json` fájlokat olvassa. A summary az utolsó rekord után íródik:

```json
{
  "model": "minimax-m3:cloud",
  "benchmark": "hulu",
  "timestamp": "2026-06-08T18:03:29.756846+00:00",
  "run_id": "hulu-minimax-m3-cloud-1780834571",
  "num_examples": 2581,
  "num_correct": 1956,
  "accuracy": 0.7578,
  "results_file": "results/minimax-m3-cloud-nothink/hulu_results.jsonl"
}
```

A composite score számítása a 6 NLU task átlagából történik (MCC 0-1-re skálázva + accuracy-k), és a riportban modellenként jelenik meg.

---

## Gyakori buktatók (pitfalls) — bővített

1. **Label-formátum keveredés** — HuCB és HuSST 3 osztályos, a többi bináris. A `download_hulu.py` minden labelt egységes **0-indexelt int** formátumba normalizál, de ha saját loader-t írsz, figyelj erre.

2. **HuCoPA label-eltolás** — a NYTK/HuCoPA HF datasetben a label **1-indexelt STRING** (`"1"` / `"2"`), nem 0-indexelt. A `download_hulu.py` `int(label) - 1` transzformációval javítja. A `nytud/HuCoPA` git submodule-ban 0-indexelt INT van.

3. **A `test` split label-jei hiányoznak** — a teszt halmazt csak a NYTK szerverén tudod kiértékelni. A `hu-eval` emiatt a `validation` splitet használja lokális kiértékelésre (~1k példa/sub-task).

4. **Morfológia-érzékenység** — a HuCoLA-ban egyetlen rag vagy toldalék megváltoztatása érvénytelenné teszi a mondatot. A modell tokenizálója (SentencePiece/BPE) gyakran szétszabdalja a ragokat, ami rontja a teljesítményt. A magyar-specifikus tokenizer (XLM-R, huBERT) előnyt jelent.

5. **HuRTE prompt inverzió** — a 2026-06-07 smoke teszt során kiderült, hogy az eredeti prompt „következik-e" volt, de a HF label 0=not_entailment, 1=entailment. Az inverz prompt (`NEM következik-e?`) a label-ekkel konzisztens.

6. **HuCB prompt-mapping** — a prompt a 0=ellentmondás, 1=semleges, 2=következmény sorrendet használja, és a `download_hulu.py` mapping is ezt követi (`{"contradiction": 0, "neutral": 1, "entailment": 2}`). Az inverzió itt is egy smoke tesztben derült ki.

7. **HuWNLI nehézség** — a legnehezebb sub-task, a modellek 40-55% accuracy-t érnek el (közel a 50%-os véletlen baseline-hoz). A referenciafeloldás a világismeretre támaszkodik.

8. **`num_predict` limit** — a `stop_on_error.py` `num_predict: 4096` (nothink) vagy `16384` (think) értéket küld. A thinking modellek (gpt-oss, minimax, qwen3.5) 2048+ tokent generálhatnak, és a limitnél megállnak (`done: length`), ami üres válaszhoz vezet. A 16384-es think limit a v1.2.5-ös javítás eredménye.

9. **Think/nothink eltérő eredmények** — ugyanaz a modell más eredményt adhat think vs nothink módban. A `glm-5.1:cloud` pl. nothink 71.6%, think 75.8% (+4.2%). A `kimi-k2.6:cloud` nothink 75.9%, think 75.2% (-0.7%). A gondolkodás segíthet vagy ronthat is, modelltől függően.

10. **Cloud rate limit / timeout** — a cloud modellek néha 429 (rate limit) vagy timeout hibát adnak. A checkpoint rendszer RESUME-olja a futtatást, de a hiba gyakori (>10% a 120B modelleknél).

11. **Token offset off-by-one** — a `score_continuation` függvényben a logit- és target-indexek elcsúszhatnak 1-gyel (lásd fent). Mindig tesztelj egy ismert példával.

12. **Field-name eltérés HF vs. git között** — a HF rekordok camelCase-t (`Sent_id`, `Sent`, `Label`) és string label-eket használnak; a git submodule-ok snake_case-t (`sent_id`, `sent`, `sent_label`) és int label-eket. A `download_hulu.py` `_g(rec, *nevek, default)` helper-je mindkettőt kezeli.

---

## Tipikus prompt-formátum (generatív kiértékelés)

A HuLU sub-taskok magyar nyelvű promptokat használnak (lásd a fenti sub-task részleteket). A modell válaszából az `extract_choice` regex-szel `r"\b([0-9])\b"` kiemeli az első számot, és azt tekinti labelnek. Ha a modelltől 1-nél több számjegyet kapunk, az elsőt vesszük; ha egyet sem, a magyar szavakat (nulla, egy, kettő, ...) próbáljuk; ha az sem, -1 (üres) confidence-del eldobjuk.

A think módban a gondolkodás a `response` mezőben jelenik meg (az Ollama a `think: False` flag ellenére a gondolkodást a `response` végére írja). Az `extract_choice` a teljes `response`-t nézi, és a végén lévő számjegyet veszi.

---

## Aggregáció és riport

A 6 NLU task átlaga a **HuLU score** (0-100 skálán):

```python
def hulu_aggregate(scores: dict[str, float]) -> float:
    """scores: {"hucola": mcc, "hucb": acc, "hucopa": acc, "hurte": acc, "husst": acc, "huwnli": acc}
    — mind 0-1 közti érték. HuRC külön aggregate-elve, ha hozzáadódik."""
    # MCC-t skálázzuk 0-1 közé (HuCoLA), a többi accuracy már 0-1
    norm = {
        "hucola": (scores["hucola"] + 1) / 2,
        "hucb":   scores["hucb"],
        "hucopa": scores["hucopa"],
        "hurte":  scores["hurte"],
        "husst":  scores["husst"],
        "huwnli": scores["huwnli"],
    }
    return sum(norm.values()) / len(norm) * 100
```

A think/nothink módok külön composite score-t kapnak. A riportban a **task-szintű bontás** fontosabb, mint az aggregátum — mert két modell azonos HuLU score-t érhet el, de teljesen más erősségekkel (pl. egyik jobb NLI-ben, másik morfológiában).

### Per-sub-task riport (v1.2.10, 2026-06-16)

A fenti aggregátor formula (`hulu_aggregate`) csak egy kompozit számot ad. A részletesebb, **sub-task szintű** riport a `scripts/hulu_breakdown_report.py` script-tel készül, és a következőket mutatja:

- **6 NLU sub-task accuracy** modellenként és módonként (HuCOLA, HuCoPA, HuRTE, HuSST, HuWNLI, HuCB)
- **Composite** (per spec) = a 6 sub-task accuracy **egyenként súlyozatlan** átlaga
- **Overall** (kanonikus) = az összes promptra számított accuracy (`total_correct / total_examples`) — ez a `hulu_summary.json` `accuracy` mezője, és a kanonikus `aggregate_results.py` HuLU score-ja

> **v1.2.10 egyszerűsítés:** a riport **kizárólag az egyes modellek/sub-taskok pontosságát** tartalmazza. Minden más dimenzió törölve:
> - **Sebesség, idő, token-metrikák** (sec/pr, TS/pr) — a v1.2.9 óta
> - **Pool-szintű nehézségi statisztikák** (pool átlag, szórás, medián, legjobb modell) — a v1.2.10-ben törölve
>
> A riport célja: **melyik modell milyen sub-taskon hogyan teljesít** — egyetlen kérdés, hogy jól válaszolt-e vagy sem.

A két composite formula közti különbség: a **Composite** egyenlő súllyal veszi a 6 sub-taskot (így a kis HuWNLI 60 prompt ugyanannyit nyom, mint a nagy HuSST 1165). Az **Overall** a prompt-számmal súlyoz, így a HuSST dominál — és egy HuSST-n gyenge modell (pl. `qwen3-next-80b-cloud nothink` 58.5% HuSST) erősen lerontja az Overall-t, míg a Composite-ban kevésbé.

A teljes 19×6-os mátrix a [`reports/hulu-breakdown-2026-06-16.md`](../reports/hulu-breakdown-2026-06-16.md) oldalon. A nyers CSV: `reports/hulu_breakdown.csv`. Két PNG:

- [`hulu_breakdown_think_nothink.png`](../reports/hulu_breakdown_think_nothink.png) — **think és nothink külön oszlopokban**, ugyanazon modell két módja egymás mellett
- [`hulu_breakdown_accuracy.png`](../reports/hulu_breakdown_accuracy.png) — per-sub-task accuracy + Composite + Overall

### Tipikus modell-teljesítmények (v1.2.9, 2026-06-12, 19/19 benchmark kész)

| Modell | nothink | think | Δ | Megjegyzés |
|--------|---------|-------|---|------------|
| `qwen3.5:cloud` | 75.0% | **78.1%** | **+3.1** | 🏆 legjobb think |
| `minimax-m3:cloud` | 75.8% | 77.1% | +1.3 | 🥈 |
| `deepseek-v4-flash:cloud` | 73.3% | 76.7% | **+3.4** | 🥉 |
| `kimi-k2.6:cloud` | **75.9%** | 75.2% | -0.7 | 🥇 legjobb nothink |
| `deepseek-v4-pro:cloud` | 74.6% | 75.9% | +1.3 | |
| `glm-5.1:cloud` | 71.6% | 75.7% | **+4.1** | think SOKAT segít |
| `nemotron-3-ultra:cloud` | 70.5% | 71.8% | +1.3 | 550B |
| `gpt-oss:120b:cloud` | 71.8% | 71.6% | -0.2 | thinking mindkét módban azonos |
| `gpt-oss:20b:cloud` | 67.0% | – | – | régi kód, 125 üres pred |
| `qwen3-next:80b-cloud` | 61.5% | 63.2% | +1.7 | 🥇 leggyengébb acc mindkét módban |

**Megjegyzések (v1.2.10 — 2026-06-12 adatok):**
- **19/19 benchmark kész** (10 modell × 2 mód, kivéve `gpt-oss:20b` think = nem futott). Nincs részleges, nincs [RÉSZLEGES] jelölés.
- **Nothink átlag (10): 71.7% | Think átlag (9): 74.0% | Összesített átlag (19): 72.8%**
- **Top 5:** `qwen3.5 (think)` 78.1% → `minimax-m3 (think)` 77.1% → `deepseek-v4-flash (think)` 76.7% → `kimi-k2.6 (nothink)` 75.9% → `deepseek-v4-pro (think)` 75.9%
- **A think mód hatása modellenként változó:** `glm-5.1` (+4.1), `deepseek-v4-flash` (+3.4), `qwen3.5` (+3.1) — a thinking segít; `kimi-k2.6` (-0.7), `gpt-oss:120b` (-0.2) — a thinking nem segít
- **A `qwen3-next:80b` a leggyengébb modell** — Composite 60.5% (nothink) / 66.0% (think), mindkét esetben a pool utolsó helyezettje. A v1.2.10-es riport nem méri a sebességet, így a korábbi "leggyorsabb is" minősítés dokumentálatlan marad — csak az accuracy-alapú megítélés maradt.

---

## Kapcsolódó

- [Overview](../overview.md) — projekt cél, hatókör
- [SCHEMA](../SCHEMA.md) — wiki-oldalak formátuma
- [MMLU-HU](mmlu-hu.md) — 38 tantárgy (NYTK/hu-mmlu), 5-shot tudás-teszt
- [ARC + GSM8K-HU](arc-gsm8k-hu.md) — logikai és matematikai benchmarkok
- [Perplexitás](perplexity-hu.md) — nyelvmodell-minőség mérése
- [Ollama API kliens](ollama-api-client.md) — hogyan hívjuk a modelleket
- [Runbook: HuLU futtatás](../runbooks/run-hulu-modell-x.md) — lépésről lépésre pipeline
- [Entitás: HuLU dataset](../entities/dataset-hulu.md) — letöltési URL-ek, licenc, méret
- [Tervezési elv: checkpoint](../concepts/checkpoint-progress.md) — stop-on-error + resume
- [Tervezési elv: think/nothink módok](../log.md) — mode flag, num_predict 4096/16384 (v1.2.5 bejegyzés)
