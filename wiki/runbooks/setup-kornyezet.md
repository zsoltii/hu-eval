# Környezet beállítása (eval-hu conda env)

*Típus:* runbook
*Forrás(ok):* belső projekt, [Anaconda docs](https://docs.conda.io/), [Ollama Python client](https://github.com/ollama/ollama-python)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Cél

Létrehozni egy reprodukálható, izolált Python környezetet a magyar LLM értékelési projekthez (`eval-hu` conda env), amiben minden benchmark script, judge hívás és aggregáció fut. A env-nek tartalmaznia kell a `requests`, `pandas`, `matplotlib`, `deepeval` és `ollama` csomagokat.

## Előfeltételek

- **Anaconda / Miniconda** telepítve (`$HOME/anaconda3/` a default lokáció ezen a gépen)
- **Ollama szerver** fut a `http://localhost:11434` címen (vagy elérhető hálózaton)
- **Python 3.11** — a `eval-hu` env ezt a verziót használja (3.12-vel a `deepeval`-nak vannak kompatibilitási gondjai)
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
eval-hhu                 $HOME/anaconda3/envs/eval-hu
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

### 3. Csomagok telepítése

```bash
# Telepítsd az összes szükséges csomag egyetlen pip paranccsal
# (így a pip egyszerre oldja fel a függőségeket, nem lesz konfliktus)
pip install \
    requests \
    pandas \
    matplotlib \
    deepeval \
    ollama
```

A telepítés ~2-3 perc. Ha bármelyik csomag `ERROR` hibát dob, ne `pip install --upgrade --force-reinstall`-ozz — olvasd el a hibaüzenetet, és külön telepítsd a problémásat.

**Pip vs conda konfliktus elkerülése:**

```bash
# Ha egy csomag a conda repóból is elérhető (pl. pandas),
#conda úton is telepítheted — DE csak akkor, ha az env aktiválva van
conda install -n eval-hu -y pandas matplotlib requests

# A deepeval és ollama NINCS conda repóban, ezeket mindig pip-pel telepítsd
pip install deepeval ollama
```

### 4. Verifikáció (import check)

Futtasd ezt a Python scriptet, hogy minden csomag betölthető-e:

```python
# verify_env.py — futtasd: python verify_env.py
import sys

# Csomagok listája, amit ellenőrzünk
csomagok = [
    ("requests", "HTTP kérések (Ollama API, dataset letöltés)"),
    ("pandas", "JSON eredmények aggregációja"),
    ("matplotlib", "Heatmap és chart generálás"),
    ("deepeval", "LLM-as-a-Judge keretrendszer"),
    ("ollama", "Ollama Python kliens"),
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
    print("⚠️  Van hiányzó csomag — telepítsd a pip install paranccsal.")
    sys.exit(1)
```

```bash
# Futtatás
cd .
python verify_env.py
```

Elvárt kimenet (a verziószámok változhatnak):

```
Python: 3.11.x (...)
Interpreter: $HOME/anaconda3/envs/eval-hu/bin/python
---
✅ requests       2.32.x     — HTTP kérések (Ollama API, dataset letöltés)
✅ pandas         2.2.x      — JSON eredmények aggregációja
✅ matplotlib     3.9.x      — Heatmap és chart generálás
✅ deepeval       1.x.x      — LLM-as-a-Judge keretrendszer
✅ ollama         0.4.x      — Ollama Python kliens
---
🎉 Minden csomag OK, az eval-hu env használatra kész!
```

### 5. Ollama elérhetőség ellenőrzése

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

### D) `deepeval` telepítés deepeval[api] vs deepeval

**Tünet:** A `deepeval` települ, de `from deepeval.metrics import ...` nem működik.

**Ok:** A `deepeval` több extra opcionális függőséggel rendelkezik.

**Megoldás:**

```bash
# A teljes telepítés, beleértve az LLM judge-ot
pip install deepeval[all]

# Vagy ha csak az LLM judge kell
pip install deepeval
pip install langchain openai  # ha LLM judge-ot használsz
```

### E) Linux-on a `libstdc++` hiányzik a deepeval miatt

**Tünet:** `ImportError: libstdc++.so.6: cannot open shared object file`

**Megoldás (Ubuntu/Debian):**

```bash
sudo apt-get update
sudo apt-get install -y libstdc++6
```

## Ellenőrző lista

- [ ] `conda env list` mutatja az `eval-hu` env-et
- [ ] `python --version` 3.11.x-et mutat
- [ ] `which pip` az env-en belüli pip-et mutatja
- [ ] `python verify_env.py` minden csomagnál ✅-t ír
- [ ] `curl http://localhost:11434/api/tags` válaszol (Ollama szerver fut)
- [ ] Van legalább 1 modell letöltve (`ollama list`)

## Kapcsolódó

- [Runbook: HuLU futtatása](run-hulu-modell-x.md) — az env használata benchmark futtatáshoz
- [Runbook: LLM Judge prompt](llm-judge-prompt-template.md) — judge hívás deepeval-lal
- [Runbook: Aggregáció](aggregate-results.md) — pandas/matplotlib scriptek
- [Runbook: Debug](debug-modell-nem-valaszol.md) — mit tegyél, ha valami nem megy
- [Overview](../overview.md) — projekt cél és hatókör
- [SCHEMA](../SCHEMA.md) — oldalformátum
