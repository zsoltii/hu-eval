# Környezet beállítása (eval-hu conda env)

*Típus:* runbook
*Forrás(ok):* belső projekt, [Anaconda docs](https://docs.conda.io/), [Ollama Python client](https://github.com/ollama/ollama-python), projekt `requirements.txt` (2026-07-19)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-10-17

---

## Cél

Létrehozni egy reprodukálható, izolált Python környezetet a magyar LLM értékelési projekthez (`eval-hu` conda env, illetve conda nélküli gépeken `uv` venv), amiben minden benchmark script, judge hívás és aggregáció fut. A futtatáshoz szükséges csomagok a projekt gyökerében lévő `requirements.txt`-ben vannak deklarálva (2026-07-19 óta).

> **v1.7 (2026-10-17) változtatások:**
> - Új "2b. Alternatíva: uv venv" szakasz — conda nélküli gépeken a projekt `.venv/` mappája (Python 3.11)
> - A shell orchestratorok interpreter-feloldása: `PYTHON` env > conda `eval-hu` > projekt `.venv` (conda nélküli gépeken automatikusan a `.venv`-et használják)
> - A `datasets/` mappa a repo része (verziókövetett) — a `data/` feltöltése `cp -r datasets/* data/`, majd `python scripts/prepare_ud_v3.py` (UD v4 prompt-variáns)

> **v1.3.4 (2026-07-19) változtatások:**
> - `requirements.txt` fájl a projekt gyökerében — `pip install -r requirements.txt` a kanonikus telepítési mód
> - A `deepeval` opcionális (a `judge_hugme.py` / `judge_mt_bench.py` saját implementációt használ, `requests`-szel hívja a bírót); a kommentek frissítve
> - Az `ollama` Python kliens **nem** kell — a scriptek közvetlenül `requests.post`-tal hívják a `/api/generate` (ollama) és `/v1/chat/completions` (openai) végpontokat
> - Új "A) `requirements.txt` használata (ajánlott)" szakasz — az egylépéses telepítéshez
> - OpenAI-kompatibilis backend esetén a `2.6. Végpont ellenőrzése` szakasz is bekerült

## Előfeltételek

- **Anaconda / Miniconda** telepítve (`$HOME/anaconda3/` a default lokáció ezen a gépen)
- **Ollama szerver** fut a `http://localhost:11434` címen — VAGY más OpenAI-kompatibilis végpont (llama-server, vLLM, stb.) elérhető
- **Python 3.11** — a `eval-hu` env ezt a verziót használja
- **Linux / macOS** — a parancsok mindkettőn működnek, de a `~/.bashrc` vs `~/.zshrc` eltérő lehet

## Lépések

### 1. Conda env létrehozása

```bash
# Frissítsd a conda-t, hogy elkerüld a régi solver bugokat
conda update -n base -c defaults conda -y

# Hozd létre az eval-hu env-et Python 3.11-gyel
conda create -n eval-hu -y python=3.11

# Ellenőrizd, hogy létrejött-e
conda env list | grep eval-hu
```

A kimenetben ezt kell látnod:

```
eval-hu                  $HOME/anaconda3/envs/eval-hu
```

### 2. Aktiválás

```bash
# Aktiváld az env-et
conda activate eval-hu

# A prompt elején megjelenik: (eval-hu) $
# Ellenőrizd a Python verziót
python --version
# Elvárt: Python 3.11.x

# Ellenőrizd a pip-et (mindig az env-en belüli pip-et használd!)
which pip
# Elvárt: $HOME/anaconda3/envs/eval-hu/bin/pip
```

**FONTOS:** Ha a `which pip` a `/usr/bin/pip`-et mutatja, akkor a `conda activate` nem futott le rendesen. Ilyenkor a globális Pythonba telepítesz, ami **rossz** — töröld a telepítést és aktiválj újra.

### 2b. Alternatíva: uv venv (conda nélküli gépek, 2026-10-17 óta)

Ha a gépen nincs conda (pl. friss clone egy új gépen), a `uv` csomagkezelővel
ugyanaz a Python 3.11-es környezet felépíthető a projekt `.venv/` mappájába.
Ekkor az 1-2. lépés (conda létrehozás + aktiválás) kimarad, és a 3. lépés
`uv pip`-pel fut.

```bash
# A projekt gyökeréből (ahol a requirements.txt van)
uv venv --python 3.11 .venv          # legenerálja a .venv-et (a CPython 3.11.x-et letölti)
uv pip install --python .venv/bin/python -r requirements.txt

# Aktiválás (a további python hívásokhoz)
source .venv/bin/activate
which python   # <projekt>/.venv/bin/python kell legyen
```

A `.venv/` a `.gitignore`-ban van. A shell orchestratorok (`queue_runner.sh`,
`queue_all_benchmarks.sh`, `phase2_runner.sh`, `post_followup.sh`, `priority_judge.sh`,
`watchdog_priority.sh`) automatikusan felismerik a környezetet — a feloldási
sorrend: `PYTHON` env változó > conda `eval-hu` > projekt `.venv` > hiba.
Kézi felülíráshoz: `PYTHON=/útvonal/python bash scripts/queue_runner.sh`.

### 3. Csomagok telepítése

#### A) `requirements.txt` használata (ajánlott, 2026-07-19 óta)

A projekt gyökerében lévő `requirements.txt` tartalmazza az összes szükséges függőséget. A conda env aktiválása után:

```bash
# A projekt gyökeréből (ahol a requirements.txt van)
cd <projekt-gyökere>
pip install -r requirements.txt
```

uv venv esetén (2b. szakasz) ugyanez `uv pip`-pel:

```bash
# A projekt gyökeréből
uv pip install --python .venv/bin/python -r requirements.txt
# (ha a venv már aktiválva van: uv pip install -r requirements.txt)
```

A `requirements.txt` jelenlegi tartalma (a kommenteket leszámítva):

```
requests>=2.32
pandas>=2.0
matplotlib>=3.7
numpy>=1.24
datasets>=2.14
# deepeval>=0.21  # opcionális — a scriptek saját judge implementációt használnak
# ollama-python>=0.2  # opcionális — a scriptek requests-szel hívnak
```

> A `datasets` a HuggingFace dataset-ek letöltéséhez kell (`download_hulu.py`, `download_mmlu_hu.py`, `download_ud_hungarian.py`).

#### B) Manuális pip install (ha a `requirements.txt` nem elérhető)

```bash
pip install \
    requests \
    pandas \
    matplotlib \
    datasets
```

A `deepeval` és `ollama` Python kliens **opcionális** — a scriptek nem használják őket. Ha valamelyik importálás mégis szükséges, külön telepíthető.

A telepítés ~2-3 perc. Ha bármelyik csomag `ERROR` hibát dob, ne `pip install --upgrade --force-reinstall`-ozz — olvasd el a hibaüzenetet, és külön telepítsd a problémásat.

**Pip vs conda konfliktus elkerülése:**

```bash
# Ha egy csomag a conda repóból is elérhető (pl. pandas),
# conda úton is telepítheted — DE csak akkor, ha az env aktiválva van
conda install -n eval-hu -y pandas matplotlib requests

# A datasets NINCS conda repóban, mindig pip-pel telepítsd
pip install datasets
```

### 4. Verifikáció (import check)

Futtasd ezt a Python scriptet, hogy minden csomag betölthető-e:

```python
# verify_env.py — futtasd: python verify_env.py
import sys

# Csomagok listája, amit ellenőrzünk
csomagok = [
    ("requests", "HTTP kérések (Ollama API, OpenAI API, dataset letöltés)"),
    ("pandas", "JSON eredmények aggregációja"),
    ("matplotlib", "Heatmap és chart generálás"),
    ("numpy", "aggregátor és heatmap számítások"),
    ("datasets", "HuggingFace dataset-ek letöltése"),
]

print(f"Python: {sys.version}")
print(f"Interpreter: {sys.executable}")
print("---")

mind_ok = True
for nev, leiras in csomagok:
    try:
        mod = __import__(nev)
        verzio = getattr(mod, "__version__", "ismeretlen")
        print(f"✅ {nev:15s} {verzio:10s} — {leiras}")
    except ImportError as e:
        print(f"❌ {nev:15s} HIBA: {e}")
        mind_ok = False

print("---")
if mind_ok:
    print("🎉 Minden csomag OK, az eval-hu env használatra kész!")
    sys.exit(0)
else:
    print("⚠️  Van hiányzó csomag — telepítsd a pip install -r requirements.txt paranccsal.")
    sys.exit(1)
```

```bash
# Futtatás
cd <projekt-gyökere>
python verify_env.py
```

Elvárt kimenet (a verziószámok változhatnak):

```
Python: 3.11.x (...)
Interpreter: $HOME/anaconda3/envs/eval-hu/bin/python
---
✅ requests       2.32.x     — HTTP kérések (Ollama API, OpenAI API, dataset letöltés)
✅ pandas         2.2.x      — JSON eredmények aggregációja
✅ matplotlib     3.9.x      — Heatmap és chart generálás
✅ numpy          1.26.x     — aggregátor és heatmap számítások
✅ datasets       2.14.x     — HuggingFace dataset-ek letöltése
---
🎉 Minden csomag OK, az eval-hu env használatra kész!
```

### 5. Végpont(ok) elérhetősége

#### A) Ollama szerver (alapértelmezett backend)

```bash
# curl teszt — a legegyszerűbb módja, hogy kiderítsd, fut-e a szerver
curl -s http://localhost:11434/api/tags | python -m json.tool | head -20
```

Ha `Connection refused` hibát kapsz, az Ollama szerver nem fut. Indítsd el:

```bash
# Háttérben indítás (Linux)
ollama serve &

# Vagy systemd-vel (ha így van telepítve)
sudo systemctl start ollama
```

Ha `models` listát látsz (pl. `qwen3.5:4b`, `qwen3.5:0.8b`), akkor minden kész.

#### B) OpenAI-kompatibilis végpont (opcionális, 2026-07-19 óta)

Ha llama-server / vLLM / TGI / felhő OpenAI API-t használsz a `--backend openai` kapcsolóval:

```bash
# llama-server alapértelmezett port
curl -s http://localhost:8080/v1/models | python -m json.tool | head

# Helyi Ollama /v1 (cloud modellek proxyzva)
curl -s http://localhost:11434/v1/models | python -m json.tool | head

# Felhő OpenAI API
curl -s https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | python -m json.tool | head
```

A válasz `data[].id` (vagy `models[].name`) mezője a modell pontos neve, amit a `--model` kapcsolónak át kell adni.

### 6. Datasetek előkészítése

A benchmark-futtatáshoz 5 dataset kell. **2026-10-17 óta a `datasets/` mappa a git repo része** (verziókövetett, ~6.5 MB, 7 fájl — a korábbi, „git nem követi" leírás elavult), így friss clone után azonnal elérhető. A scriptek viszont a `./data/...` útvonalat várják, ezért a clone után másolni kell:

**A) Másolás a `data/` mappába (ajánlott, új gépeken ez az egyetlen lépés):**

A mappa szerkezete (a `data/` alatt ugyanez lesz):

```
datasets/
├── hulu/           hulu_std.jsonl, hulu_raw.jsonl
├── mmlu_hu/        mmlu_hu_std.jsonl
├── hugme/          prompts.jsonl
├── mt_bench_hu/    questions.jsonl
└── ud_hungarian/   hu_szeged-ud-test.conllu, ud_hungarian_std.jsonl
```

```bash
# A datasets/ tartalmát másoljuk a data/ alá (a scriptek által várt útvonal)
mkdir -p data
cp -r datasets/* data/

# UD Hungarian v4 prompt-variáns generálása (a run_ud_v3.py ezt használja)
python scripts/prepare_ud_v3.py
```

Vagy symlinkkel (helytakarékos, ha a datasets/ és a data/ külön fájlrendszeren van):

```bash
ln -s ../datasets/hulu data/hulu
ln -s ../datasets/mmlu_hu data/mmlu_hu
ln -s ../datasets/hugme data/hugme
ln -s ../datasets/mt_bench_hu data/mt_bench_hu
ln -s ../datasets/ud_hungarian data/ud_hungarian
# (a prepare_ud_v3.py symlink esetén a datasets/ud_hungarian/-ba ír)
```

**B) Online letöltés (fallback, ha a `datasets/` hiányozna):**

```bash
python scripts/download_hulu.py            # HuLU (NYTK HF-ről, 2581 példa)
python scripts/download_mmlu_hu.py         # MMLU-HU (NYTK/hu-mmlu, 38 tantárgy)
python scripts/download_ud_hungarian.py    # UD Hungarian (CoNLL-U GitHub-ról)
# HuGME (prompts.jsonl) és MT-Bench-HU (questions.jsonl) jelenleg nincs
# download script — ezeket kézzel kell előállítani vagy a datasets/-ből másolni.
```

Az így letöltött fájlok a `data/<benchmark>/` mappába kerülnek. Az UD v4 variánst
online letöltés esetén is `python scripts/prepare_ud_v3.py`-vel kell generálni.

## Gyakori buktatók

### A) A `conda` parancs nem található

**Tünet:** `conda: command not found`

**Ok:** A conda nincs a PATH-ban.

**Megoldás:**

```bash
# Linux: add hozzá a ~/.bashrc-hez
echo 'export PATH="$HOME/anaconda3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# macOS (zsh): add hozzá a ~/.zshrc-hez
echo 'export PATH="$HOME/anaconda3/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### B) Rossz Python env-be telepít a pip

**Tünet:** `which pip` a `/usr/bin/pip`-et mutatja, vagy a `python` nem a `3.11.x` verziót mutatja.

**Ok:** A `conda activate` nem futott le, vagy a shell nem inicializálta a conda init szkriptet.

**Megoldás:**

```bash
# 1. Ellenőrizd a conda init-et
conda init bash  # vagy `conda init zsh` macOS-en

# 2. Nyiss új terminált (a source ~/.bashrc önmagában nem elég!)

# 3. Aktiválj újra
conda activate eval-hu

# 4. Ellenőrizd újra
which python  # $HOME/anaconda3/envs/eval-hu/bin/python kell legyen
which pip     # $HOME/anaconda3/envs/eval-hu/bin/pip kell legyen
```

### C) Mac-en a matplotlib nem tudja renderelni a headless ábrákat

**Tünet:** `RuntimeError: Invalid DISPLAY variable` vagy `cannot connect to X server`.

**Ok:** A matplotlib alapértelmezetten X11-et keres, Mac-en viszont nincs X szerver.

**Megoldás:**

```python
# A script elejére, a matplotlib importja ELŐTT
import matplotlib
matplotlib.use("Agg")  # Headless, fájlba mentés

import matplotlib.pyplot as plt
# ... további kód
```

Vagy állítsd be környezeti változóként:

```bash
echo 'export MPLBACKEND=Agg' >> ~/.bashrc
```

### D) `deepeval` telepítés — mostantól opcionális (2026-07-19)

**Régi konvenció (2026-06-06 – 2026-07-18):** a `pip install deepeval` kötelező volt a LLM-as-a-Judge hívásokhoz.

**2026-07-19 óta:** a `judge_hugme.py` és a `judge_mt_bench.py` **saját implementációt** használnak — `requests`-szel hívják a bíró modellt, és nincs szükség a `deepeval` Python csomagra. A `requirements.txt` ezért **nem tartalmazza** a `deepeval`-t (kommentben van, opcionális).

Ha mégis szükséges (pl. külső judge-pool integrációhoz):

```bash
# Csak akkor, ha valamelyik script deepeval-t igényel
pip install deepeval
```

### E) Linux-on a `libstdc++` hiányzik — mostantól nem kell (2026-07-19)

**Régi tünet:** `ImportError: libstdc++.so.6: cannot open shared object object file`.

**2026-07-19 óta:** a `deepeval` nem kötelező, így ez a hiba sem jellemző. Ha mégis előfordul (pl. egy másik projekt importálja):

```bash
sudo apt-get update
sudo apt-get install -y libstdc++6
```

## Ellenőrző lista

- [ ] `conda env list` mutatja az `eval-hu` env-et **vagy** létezik a projekt `.venv/` mappa (uv alternatíva)
- [ ] `python --version` 3.11.x-et mutat (conda) / `.venv/bin/python --version` 3.11.x-et mutat (uv)
- [ ] `which pip` az env-en belüli pip-et mutatja, vagy `uv pip list --python .venv/bin/python` működik
- [ ] `python verify_env.py` minden csomagnál ✅-t ír
- [ ] `curl http://localhost:11434/api/tags` válaszol (Ollama szerver fut)
- [ ] Van legalább 1 modell letöltve (`ollama list`)
- [ ] A `data/` mappa feltöltve (`cp -r datasets/* data/`), és létezik a `data/ud_hungarian/ud_hungarian_v4.jsonl`

## Kapcsolódó

- [Runbook: HuLU futtatása](run-hulu-modell-x.md) — az env használata benchmark futtatáshoz
- [Runbook: Benchmark futtatás OpenAI backenden](run-modell-x-openai-backend.md) — llama-server / vLLM / felhő OpenAI esetén
- [Runbook: LLM Judge prompt](llm-judge-prompt-template.md) — judge hívás deepeval-lal
- [Runbook: Aggregáció](aggregate-results.md) — pandas/matplotlib scriptek
- [Runbook: Debug](debug-modell-nem-valaszol.md) — mit tegyél, ha valami nem megy
- [Concept: OpenAI-kompatibilis backend](../concepts/openai-backend-support.md) — a két backend részletes leírása
- [Overview](../overview.md) — projekt cél és hatókör
- [SCHEMA](../SCHEMA.md) — oldalformátum
