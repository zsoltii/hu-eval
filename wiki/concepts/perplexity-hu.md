# Perplexity (PPL) magyar nyelven

*Típus:* concept
*Forrás(ok):* https://huggingface.co/docs/transformers/perplexity — HF Transformers PPL doksi; https://huggingface.co/datasets/wikipedia — Wikipedia dump; https://en.wikipedia.org/wiki/Perplexity — elméleti háttér; https://github.com/huggingface/evaluate — evaluate könyvtár
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Mi a perplexity (PPL)?

A **perplexity** (zavarodás, röviden PPL) egy nyelvmodell minőségének alapvető mérőszáma. Formálisan egy token-szekvencia valószínűségének exponenciálisa: ha egy modell egy N hosszú szekvenciát ír le, akkor

$$PPL = \exp\left(-\frac{1}{N} \sum_{i=1}^{N} \log p(x_i | x_{<i})\right)$$

Azaz a **negatív átlagos log-likelihood exponenciálisa**. Értelmezése: a PPL azt mondja meg, hogy a modell minden egyes tokennél „hány egyenlő esélyű opció között habozik". PPL=10 azt jelenti, hogy a modell minden lépésnél nagyjából 10 egyformán valószínű lehetőség közül választ.

> 📚 Például egy modell, ami jól leírja a magyar nyelvet, PPL≈15-25 közötti értéket ér el tiszta magyar Wikipédián. Egy gyengébb vagy nem magyarra specializált modell PPL-je 50-100+ is lehet.

A PPL **kisebb = jobb**. A logaritmikus természet miatt a különbség sokszor inkább nagyságrendekben mérhető, mint abszolút számokban: PPL=20 → PPL=40 ugyanakkora „ugrás", mint PPL=40 → PPL=80.

## Miért fontos a perplexity?

1. **Nyílt végű, nem benchmark-függő** — a PPL nem igényel címkézett adathalmazt, bármilyen magyar szövegen mérhető (Wikipedia, hírportálok, könyvek).
2. **Modell-összehasonlításra** — ha két modell PPL-je 25 vs. 50 egy adott magyar szövegen, akkor az első **várhatóan jobb lesz** bármilyen downstream feladaton.
3. **Pre-training monitorozás** — pre-training során a PPL a célveszteség, így közvetlenül jelzi a tanulás előrehaladását.
4. **Out-of-domain detekció** — ha egy modell PPL-je hirtelen megugrik egy szövegen, az azt jelenti, hogy a szöveg távol áll a modell pre-training adatától.
5. **Olcsó és gyors** — nincs szükség LLM-as-a-Judge bíróra, GPU-n másodpercek alatt kiszámolható.

### Korlátok

A PPL **nem mér mindent**:
- Egy modell lehet alacsony PPL-ű, de „buta" (pl. csak gyakori szókapcsolatokat ismételget).
- A PPL **nyelv- és szövegfüggő** — egy angol Wikipédián mért PPL nem hasonlítható össze közvetlenül egy magyar Wikipédián mérttel.
- A PPL **tokenizáló-függő** — két modell eltérő tokenizálóval más PPL-t ad ugyanarra a szövegre, még akkor is, ha a mögöttes „tudásuk" azonos.

> ⚠️ A PPL-t mindig **ugyanazzal a szöveggel és ugyanazzal a tokenizálóval** kell mérni, ha modelleket akarunk összehasonlítani.

## Magyar Wikipedia — az alapértelmezett PPL-korpusz

A magyar PPL-méréshez a **magyar Wikipédia** a de facto standard korpusz. Előnyei:

- **Nagy, tiszta, jól strukturált** — kb. 600 millió token, csaknem kizárólag helyes magyar nyelven.
- **Public domain** — szabadon letölthető és felhasználható.
- **Sokféle témát fed le** — általános tudás, kultúra, tudomány, technika, földrajz, stb.
- **A nemzetközi PPL-kutatások referenciakorpusza** — szinte minden nyelvmodell-kiértékelés Wikipedia-alapú, így a magyar modell is közvetlenül összehasonlítható.

### Letöltés

```bash
# Közvetlenül a HF datasets-ről
python -c "
from datasets import load_dataset
ds = load_dataset('wikipedia', 'hu', split='train', trust_remote_code=True)
print(f'Sorok száma: {len(ds)}')
print(f'Első cikk címe: {ds[0][\"title\"]}')
"
```

A dump mérete tömörítve kb. 1.2 GB, kicsomagolva ~5 GB. A teljes feldolgozáshoz általában egy **mintát** veszünk (pl. 10 000 cikk, vagy 50 millió token).

### Alternatív korpuszok

A magyar PPL-t más korpuszokon is érdemes mérni, mert a modell profilját jobban feltárja:

- **OSCAR magyar** — Common Crawl-ből származó hétköznapi webes szöveg (zajosabb, valóságosabb).
- **HuggingFaceFW/fineweb-edu-hu** — oktatási célú, szűrt webes szöveg.
- **Újsághírek** (pl. Telex, Index) — aktuális, modern nyelvhasználat.
- **Könyvek** (pl. Project Gutenberg) — irodalmi, formális nyelv.

> 📊 A magyar Wikipédián mért PPL és a webes/újságos PPL között gyakran 2-3x szorzó a különbség, mert a Wikipédia „letisztultabb" nyelvezetű, mint a web.

## Sliding window — hogyan mérjünk hosszú szövegeken?

A PPL képlete „teljes szekvenciára" vonatkozik, de a modellek **kontextablak-mérete** korlátos (pl. 2048, 4096, 8192 token). Hosszabb szövegek esetén a **sliding window** (csúszóablak) technikát használjuk.

### Az alapelv

A szöveget fix hosszúságú ablakokra bontjuk (pl. 512 token), és minden ablakra külön-külön kiszámoljuk a PPL-t. Az ablakok **stridével** (eltolással) csúsznak egymáson — ez a `stride` paraméter.

```
stride=512, max_length=512:
ablak 1:  [0..511]
ablak 2:    [512..1023]      <- stride=512, nincs átfedés
ablak 3:      [1024..1535]
```

```
stride=256, max_length=512:
ablak 1:  [0..511]
ablak 2:    [256..767]      <- stride=256, 50% átfedés
ablak 3:      [512..1023]
```

### Miért fontos a stride?

- **Nagy stride** (pl. 512, nincs átfedés): gyors, de a PPL-változásokat a szövegen belül „elkeni". A kezdő-pozíciókban a modell kontextje üres, és az első néhány token PPL-je magasabb.
- **Kis stride** (pl. 64, sok átfedés): lassú, de pontosabb, mert minden tokent többször is kiértékelünk, különböző kontextussal. A standard `stride = max_length` (nincs átfedés) és a `stride = max_length / 2` (50% átfedés) a két leggyakoribb.

> 🔧 Ajánlott alapbeállítás: `max_length=512, stride=512` (nincs átfedés) a leggyorsabb; `stride=256` (50% átfedés) a pontosabb, de 2x lassabb.

## Transformers PPL calculator — Python kód

A HuggingFace `transformers` könyvtár beépített PPL-számoló függvényt kínál. A legegyszerűbb használat:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "qwen3.5:4b"   # vagy bármelyik magyarul is tudó modell
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")

# Magyar szöveg
text = """A magyar nyelv az uráli nyelvcsalád finnugor ágába tartozik.
Beszélőinek száma világszerte körülbelül 13 millió fő."""

# Egyszerű PPL (rövid szövegre)
encodings = tok(text, return_tensors="pt").to(model.device)
with torch.no_grad():
    outputs = model(**encodings, labels=encodings.input_ids)
    ppl = torch.exp(outputs.loss).item()

print(f"PPL: {ppl:.2f}")
```

### Sliding window PPL — teljes implementáció

```python
import torch
import math
from typing import Iterator

def sliding_window_ppl(
    model,
    tok,
    text: str,
    max_length: int = 512,
    stride: int = 256,
    device: str = "cuda",
) -> float:
    """Sliding window PPL hosszú szövegre.

    Visszatérési érték: float, a teljes szöveg perplexitása.
    """
    encodings = tok(text, return_tensors="pt").input_ids.to(device)
    n_tokens = encodings.size(1)

    if n_tokens <= max_length:
        # Rövid szöveg: egyszerű számítás
        with torch.no_grad():
            out = model(encodings, labels=encodings)
        return torch.exp(out.loss).item()

    log_likelihoods = []
    nlls = []
    prev_end = 0

    for begin_loc in range(0, n_tokens, stride):
        end_loc = min(begin_loc + max_length, n_tokens)
        target_len = end_loc - prev_end   # csak az új tokeneket pontozzuk

        input_ids = encodings[:, begin_loc:end_loc]
        target_ids = input_ids.clone()
        # Az átfedő részt maszkoljuk a loss-ból
        target_ids[:, :-target_len] = -100

        with torch.no_grad():
            out = model(input_ids, labels=target_ids)
            # out.loss az átlagos NLL a nem-maszkolt tokenekre
            nll = out.loss.float() * target_len
        nlls.append(nll)
        prev_end = end_loc

        if end_loc == n_tokens:
            break

    avg_nll = torch.stack(nlls).sum() / n_tokens
    return torch.exp(avg_nll).item()
```

### Használat magyar Wikipédián

```python
from datasets import load_dataset

ds = load_dataset("wikipedia", "hu", split="train", streaming=True)

# Első 5 cikk összefűzött szövege
texts = []
for i, ex in enumerate(ds):
    if i >= 5:
        break
    texts.append(ex["text"])
corpus = "\n\n".join(texts)[:200_000]   # kb. 50k token

ppl = sliding_window_ppl(model, tok, corpus, max_length=512, stride=256)
print(f"Magyar Wikipedia PPL: {ppl:.2f}")
```

## PPL kiértékelés az `evaluate` könyvtárral

A HuggingFace `evaluate` csomagja kínál egy egyszerűbb PPL-metrikát, de a sliding window-os verziót kézzel kell implementálni (lásd fent). Az `evaluate` használata:

```python
import evaluate

ppl_metric = evaluate.load("perplexity", module_type="metric")
results = ppl_metric.compute(
    model_id="qwen3.5:4b",
    add_start_token=True,
    predictions=["A magyar nyelv az uráli nyelvcsaládba tartozik."]
)
print(results)  # {'perplexities': [...], 'mean_perplexity': ...}
```

Ez a kisebb szövegekre kényelmes, de **nem támogatja a sliding window-t** out-of-the-box.

## Tipikus PPL-értékek magyar modelleken (tájékoztató)

| Modell | PPL (hu Wikipedia) | Megjegyzés |
|--------|-------------------|------------|
| `qwen3.5:0.8b` | ~35–45 | kicsi, gyenge |
| `qwen3.5:2b` | ~22–28 | kicsi, meglepően jó |
| `qwen3.5:4b` | ~16–20 | közepes, ajánlott baseline |
| `qwen3.5:cloud` | ~10–14 | nagy, kiváló |
| `minimax-m3:cloud` | ~11–15 | cloud, magyarra specializált |
| `gemini-3-flash` | ~12–16 | cloud, kisebb modell |
| `deepseek-v4-pro` | ~9–13 | cloud, legjobb |

> ⚠️ Ezek az értékek erősen függenek a tokenizálótól, a korpusz-vágástól, és a sliding window paraméterektől. A fenti értékek csak nagyságrendi tájékoztatásnak tekinthetők.

## PPL és downstream teljesítmény kapcsolata

A PPL erős prediktora a downstream benchmarkoknak, de **nem lineáris** az összefüggés. Például:

- Egy modell PPL-je 25-ről 20-ra javul (20% relatív javulás) → HuLU score jellemzően 5-10 százalékpontot javul.
- Egy modell PPL-je 20-ról 15-re javul (25% relatív javulás) → HuLU score már csak 3-5 százalékpontot javul.
- A telítési pont általában PPL=10-12 körül van — ez alatt a PPL-javulás alig hat a downstream-ra.

> 📈 A PPL tehát **jobb monitorozó eszköz, mint cél-mérőszám**: a cél a downstream benchmarkokon való javulás, de a PPL-t olcsó, gyors proxyként használjuk a pre-training során.

## Gyakori buktatók

1. **Összehasonlíthatatlan korpuszok** — ne hasonlítsd össze egy modell angol Wikipedia PPL-jét egy másik modell magyar Wikipedia PPL-jével.
2. **Összehasonlíthatatlan tokenizálók** — két modell eltérő tokenizálóval más PPL-t ad. Ha a modell BPE-tokenizálója 1 magyar szót 2 tokenre bont, míg egy másiké 1-re, akkor a PPL-értékek nem közvetlenül összehasonlíthatók (bár a PPL „per-token" értelemben van definiálva, a gyakorlatban ez a hatás érezhető).
3. **Túl rövid ablak** — ha a `max_length` túl kicsi (pl. 64), a modell nem lát elég kontextust, és a PPL felfelé torzul.
4. **Ablak-pontatlanság** — a sliding window implementációban gyakori hiba, hogy a `target_ids` maszkolása rossz. Mindig tesztelj egy ismert toy-példával.
5. **A cikk címe és a törzs** — a magyar Wikipédia cikkei gyakran „( település)" típusú diszambiguáló suffix-eket tartalmaznak a címben. Ha ezt is belevesszük a korpuszba, a PPL kissé torzul. Érdemes kiszűrni vagy normalizálni.
6. **A teszt-szivárgás** — ha a modell pre-training korpusza tartalmazta a magyar Wikipédiát, akkor a PPL-mérés „emlékezik" a szövegre, és a PPL alulbecsüli a modell valódi általános képességét. Ezt a hatást nehéz detektálni, de létezik: friss (2024+) magyar szövegeken érdemes kontroll-PPL-t is mérni.

## PPL mint drift-monitor

A PPL kiválóan alkalmas **modell-degradáció monitorozására** is. Ha egy modell viselkedése hirtelen megváltozik (pl. finomhangolás, kvantálás, vagy akár egy upstream frissítés miatt), a PPL ezt azonnal jelzi, míg a benchmark-eredmények lassabban reagálnak.

```python
# Heti PPL-monitorozás egy rögzített 10k token magyar mintán
def weekly_ppl_check(model, tok, reference_text: str) -> dict:
    ppl = sliding_window_ppl(model, tok, reference_text, max_length=512, stride=256)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "ppl": ppl,
        "delta_from_last": ...,   # előző heti értékhez képest
    }
```

## Kapcsolódó

- [Overview](../overview.md) — projekt cél
- [SCHEMA](../SCHEMA.md) — wiki-formátum
- [HuLU Benchmark](hulu-benchmark.md) — magyar nyelvértési benchmark
- [MMLU-HU](mmlu-hu.md) — 38 tantárgy, tudás-teszt
- [ARC + GSM8K-HU](arc-gsm8k-hu.md) — logika és matematika
- [Ollama API kliens](ollama-api-client.md) — modellek hívása
