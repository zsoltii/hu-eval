# HuLU Per-Sub-Task Bontás

*Generálva:* 2026-07-25T08:21:30.388249+00:00

*1 benchmark (egyedi rekord: utolsó előfordulás alapján).*

## Módszer

A `results/{model}-{mode}/hulu_results.jsonl` fájlokból csoportosítunk a `task` mező szerint. Duplikátumok (RESUME-ból): az utolsó előfordulás számít. A sub-task accuracy egyszerű átlag (`correct / total`); a HuCOLA-t is így kezeljük (a kanonikus specifikáció MCC-t ír elő, de a JSONL `correct: bool` mezőt tartalmaz, így a kompatibilitás kedvéért itt is accuracy-t jelentetünk).

- **Composite** (per spec): a 6 sub-task accuracy egyszerű (egyenként súlyozatlan) átlaga — megfelel a `wiki/concepts/hulu-benchmark.md` Aggregáció szekciójának.
- **Overall** (kanonikus): az összes promptra számított accuracy (`total_correct / total_examples`) — ez a `hulu_summary.json` `accuracy` mezője, és a kanonikus `aggregate_results.py` HuLU score-ja. A HuSST (1165 prompt) dominálja, így a nehezebb HuSST-s modellek alacsonyabb overall score-t kapnak.

## Táblázat — think vs nothink (accuracy %, külön oszlopok)

![Think vs nothink accuracy](hulu_breakdown_think_nothink.png)

| Modell | HuCOLA nt | HuCoPA nt | HuRTE nt | HuSST nt | HuWNLI nt | HuCB nt | HuCOLA th | HuCoPA th | HuRTE th | HuSST th | HuWNLI th | HuCB th | Composite nt | Composite th | Overall nt | Overall th |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS** | 51.5% | 90.0% | 72.8% | 57.0% | 13.3% | 49.5% | — | — | — | — | — | — | 55.7% | — | 56.5% | — |

## Táblázat — per sub-task (accuracy %)

![Per-sub-task accuracy](hulu_breakdown_accuracy.png)

| Modell (mód) | HuCOLA | HuCoPA | HuRTE | HuSST | HuWNLI | HuCB | Composite | Overall |
|---|---|---|---|---|---|---|---|---|
| **unsloth-Qwen3-Next-80B-A3B-Thinking-GGUF-UD-IQ3_XXS (nothink)** | 51.5% (n=910) | 90.0% (n=100) | 72.8% (n=243) | 57.0% (n=1165) | 13.3% (n=60) | 49.5% (n=103) | **55.7%** | 56.5% |