# HuLU Per-Sub-Task Bontás

*Generálva:* 2026-06-16T06:46:00.962882+00:00

*19 benchmark (egyedi rekord: utolsó előfordulás alapján).*

## Módszer

A `results/{model}-{mode}/hulu_results.jsonl` fájlokból csoportosítunk a `task` mező szerint. Duplikátumok (RESUME-ból): az utolsó előfordulás számít. A sub-task accuracy egyszerű átlag (`correct / total`); a HuCOLA-t is így kezeljük (a kanonikus specifikáció MCC-t ír elő, de a JSONL `correct: bool` mezőt tartalmaz, így a kompatibilitás kedvéért itt is accuracy-t jelentetünk).

- **Composite** (per spec): a 6 sub-task accuracy egyszerű (egyenként súlyozatlan) átlaga — megfelel a `wiki/concepts/hulu-benchmark.md` Aggregáció szekciójának.
- **Overall** (kanonikus): az összes promptra számított accuracy (`total_correct / total_examples`) — ez a `hulu_summary.json` `accuracy` mezője, és a kanonikus `aggregate_results.py` HuLU score-ja. A HuSST (1165 prompt) dominálja, így a nehezebb HuSST-s modellek alacsonyabb overall score-t kapnak.

## Táblázat — think vs nothink (accuracy %, külön oszlopok)

![Think vs nothink accuracy](hulu_breakdown_think_nothink.png)

| Modell | HuCOLA nt | HuCoPA nt | HuRTE nt | HuSST nt | HuWNLI nt | HuCB nt | HuCOLA th | HuCoPA th | HuRTE th | HuSST th | HuWNLI th | HuCB th | Composite nt | Composite th | Overall nt | Overall th |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **deepseek-v4-flash-cloud** | 88.1% | 91.0% | 81.5% | 62.0% | 46.7% | 50.5% | 85.9% | 93.0% | 95.1% | 67.8% | 25.0% | 67.0% | 70.0% | 72.3% | 73.3% | 76.7% |
| **deepseek-v4-pro-cloud** | 85.4% | 86.0% | 58.0% | 72.5% | 28.3% | 57.3% | 85.9% | 96.0% | 91.8% | 66.2% | 21.7% | 71.8% | 64.6% | 72.2% | 74.6% | 75.9% |
| **glm-5.1-cloud** | 75.1% | 97.0% | 90.1% | 65.5% | 31.7% | 65.0% | 83.3% | 95.0% | 94.2% | 67.5% | 6.7% | 80.6% | 70.7% | 71.2% | 71.6% | 75.7% |
| **gpt-oss-120b-cloud** | 72.7% | 92.0% | 90.5% | 66.7% | 41.7% | 74.8% | 71.5% | 90.0% | 91.4% | 66.6% | 55.0% | 74.8% | 73.1% | 74.9% | 71.8% | 71.6% |
| **gpt-oss-20b-cloud** | 61.1% | 84.0% | 93.0% | 65.9% | 41.7% | 68.0% | — | — | — | — | — | — | 68.9% | — | 67.0% | — |
| **kimi-k2.6-cloud** | 79.7% | 91.0% | 89.7% | 70.0% | 55.0% | 75.7% | 78.7% | 97.0% | 94.7% | 69.4% | 11.7% | 81.6% | 76.8% | 72.2% | 75.9% | 75.2% |
| **minimax-m3-cloud** | 83.3% | 98.0% | 81.5% | 69.9% | 13.3% | 77.7% | 83.7% | 96.0% | 88.5% | 70.3% | 35.0% | 75.7% | 70.6% | 74.9% | 75.8% | 77.1% |
| **nemotron-3-ultra-cloud** | 72.4% | 89.0% | 86.8% | 65.7% | 41.7% | 68.9% | 75.3% | 93.0% | 91.8% | 65.8% | 11.7% | 75.7% | 70.8% | 68.9% | 70.5% | 71.8% |
| **qwen3-next-80b-cloud** | 57.6% | 92.0% | 93.8% | 58.5% | 5.0% | 56.3% | 58.1% | 91.0% | 93.0% | 60.5% | 35.0% | 58.3% | 60.5% | 66.0% | 61.4% | 63.2% |
| **qwen3.5-cloud** | 81.6% | 97.0% | 78.6% | 70.0% | 26.7% | 71.8% | 87.6% | 96.0% | 94.2% | 69.6% | 1.7% | 80.6% | 71.0% | 71.6% | 75.0% | 78.1% |

## Táblázat — per sub-task (accuracy %)

![Per-sub-task accuracy](hulu_breakdown_accuracy.png)

| Modell (mód) | HuCOLA | HuCoPA | HuRTE | HuSST | HuWNLI | HuCB | Composite | Overall |
|---|---|---|---|---|---|---|---|---|
| **kimi-k2.6-cloud (nothink)** | 79.7% (n=910) | 91.0% (n=100) | 89.7% (n=243) | 70.0% (n=1165) | 55.0% (n=60) | 75.7% (n=103) | **76.8%** | 75.9% |
| **gpt-oss-120b-cloud (think)** | 71.5% (n=910) | 90.0% (n=100) | 91.4% (n=243) | 66.6% (n=1165) | 55.0% (n=60) | 74.8% (n=103) | **74.9%** | 71.6% |
| **minimax-m3-cloud (think)** | 83.7% (n=910) | 96.0% (n=100) | 88.5% (n=243) | 70.3% (n=1165) | 35.0% (n=60) | 75.7% (n=103) | **74.9%** | 77.1% |
| **gpt-oss-120b-cloud (nothink)** | 72.7% (n=910) | 92.0% (n=100) | 90.5% (n=243) | 66.7% (n=1165) | 41.7% (n=60) | 74.8% (n=103) | **73.1%** | 71.8% |
| **deepseek-v4-flash-cloud (think)** | 85.9% (n=910) | 93.0% (n=100) | 95.1% (n=243) | 67.8% (n=1165) | 25.0% (n=60) | 67.0% (n=103) | **72.3%** | 76.7% |
| **deepseek-v4-pro-cloud (think)** | 85.9% (n=910) | 96.0% (n=100) | 91.8% (n=243) | 66.2% (n=1165) | 21.7% (n=60) | 71.8% (n=103) | **72.2%** | 75.9% |
| **kimi-k2.6-cloud (think)** | 78.7% (n=910) | 97.0% (n=100) | 94.7% (n=243) | 69.4% (n=1165) | 11.7% (n=60) | 81.6% (n=103) | **72.2%** | 75.2% |
| **qwen3.5-cloud (think)** | 87.6% (n=910) | 96.0% (n=100) | 94.2% (n=243) | 69.6% (n=1165) | 1.7% (n=60) | 80.6% (n=103) | **71.6%** | 78.1% |
| **glm-5.1-cloud (think)** | 83.3% (n=910) | 95.0% (n=100) | 94.2% (n=243) | 67.5% (n=1165) | 6.7% (n=60) | 80.6% (n=103) | **71.2%** | 75.7% |
| **qwen3.5-cloud (nothink)** | 81.6% (n=910) | 97.0% (n=100) | 78.6% (n=243) | 70.0% (n=1165) | 26.7% (n=60) | 71.8% (n=103) | **71.0%** | 75.0% |
| **nemotron-3-ultra-cloud (nothink)** | 72.4% (n=910) | 89.0% (n=100) | 86.8% (n=243) | 65.7% (n=1165) | 41.7% (n=60) | 68.9% (n=103) | **70.8%** | 70.5% |
| **glm-5.1-cloud (nothink)** | 75.1% (n=910) | 97.0% (n=100) | 90.1% (n=243) | 65.5% (n=1165) | 31.7% (n=60) | 65.0% (n=103) | **70.7%** | 71.6% |
| **minimax-m3-cloud (nothink)** | 83.3% (n=910) | 98.0% (n=100) | 81.5% (n=243) | 69.9% (n=1165) | 13.3% (n=60) | 77.7% (n=103) | **70.6%** | 75.8% |
| **deepseek-v4-flash-cloud (nothink)** | 88.1% (n=910) | 91.0% (n=100) | 81.5% (n=243) | 62.0% (n=1165) | 46.7% (n=60) | 50.5% (n=103) | **70.0%** | 73.3% |
| **gpt-oss-20b-cloud (nothink)** | 61.1% (n=910) | 84.0% (n=100) | 93.0% (n=243) | 65.9% (n=1165) | 41.7% (n=60) | 68.0% (n=103) | **68.9%** | 67.0% |
| **nemotron-3-ultra-cloud (think)** | 75.3% (n=910) | 93.0% (n=100) | 91.8% (n=243) | 65.8% (n=1165) | 11.7% (n=60) | 75.7% (n=103) | **68.9%** | 71.8% |
| **qwen3-next-80b-cloud (think)** | 58.1% (n=910) | 91.0% (n=100) | 93.0% (n=243) | 60.5% (n=1165) | 35.0% (n=60) | 58.3% (n=103) | **66.0%** | 63.2% |
| **deepseek-v4-pro-cloud (nothink)** | 85.4% (n=910) | 86.0% (n=100) | 58.0% (n=243) | 72.5% (n=1165) | 28.3% (n=60) | 57.3% (n=103) | **64.6%** | 74.6% |
| **qwen3-next-80b-cloud (nothink)** | 57.6% (n=910) | 92.0% (n=100) | 93.8% (n=243) | 58.5% (n=1165) | 5.0% (n=60) | 56.3% (n=103) | **60.5%** | 61.4% |