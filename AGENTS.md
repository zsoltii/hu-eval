# AGENTS.md — hu-eval

Magyar LLM értékelési projekt. Két réteg:

- **`scripts/`** — futtatható Python (21 `.py` + 7 `.sh`), nincs build, nincs test framework
- **`wiki/`** — magyar nyelvű dokumentáció (Karpathy LLM Wiki módszer)

A gyökér `README.md` a részletes projekt-térkép — itt csak a nem nyilvánvaló dolgok. Aktuális állapot / változásnapló: `wiki/log.md` (append-only, mindig friss).

## Környezet (kötelező)

- **Conda env:** `eval-hu` Python 3.11-gyel (`$HOME/anaconda3/envs/eval-hu`). **Python 3.12 nem jó** (`deepeval` kompatibilitás). Ha `which pip` `/usr/bin/pip`, a `conda activate eval-hu` nem futott le.
- **Ollama szerver:** `http://localhost:11434` — futnia kell minden benchmark előtt. Ellenőrzés: `curl -s http://localhost:11434/api/tags`.
- **Függőségek:** nincs lockfile (`requirements.txt`/`pyproject.toml` nincs). Telepítés: `pip install requests pandas matplotlib deepeval ollama-python datasets`. Mac-en: `export MPLBACKEND=Agg`.
- **Git repo:** ez a mappa maga a git repo (remote `github.com/zsoltii/hu-eval.git`). NE inicializálj új git-et. A `results/`, `data/`, `logs/`, `state/` mappák `.gitignore`-olva vannak (futtatási adatok, nem verziókövetve) — ne töröld őket a `.gitignore`-ból.
- **Git munkafolyamat (kötelező):** minden módosítás után `git add` KÖTELEZŐ (a változtatott fájlok stagelése). A `git commit` és `git push` csak **konkrét kérésre** történjen — ilyenkor a commit message-et te írod meg, tömör és leíró formában. Ne commit-olj és ne push-olj önállóan.

## Parancsok

**Mindig a projekt gyökeréből futtasd** (ahol a `README.md` van), NEM a `scripts/`-ból — minden útvonal relatív (`./data/...`, `./results/...`, `./state/...`, `./logs/...`).

```bash
# Egyszeri letöltés (kötelező az első futás előtt)
python scripts/download_hulu.py                  # HuLU: 6 NLU sub-task NYTK HF-ről
python scripts/download_hulu.py --offline         # fallback: git clone nytud/HuLU
python scripts/download_mmlu_hu.py               # MMLU-HU: NYTK/hu-mmlu, 38 tantárgy
python scripts/download_ud_hungarian.py          # UD Hungarian (CoNLL-U) GitHub-ról

# Benchmark futtatás — ugyanaz a parancs RESUME-ol is
# 5 runner létezik: run_hulu, run_mmlu_hu, run_hugme, run_mt_bench_hu, run_ud_hungarian
python scripts/run_hulu.py --model qwen3.5:4b              # első ind. vagy folytatás (nothink)
python scripts/run_hulu.py --model qwen3.5:4b --mode think # thinking módban
python scripts/run_hulu.py --model qwen3.5:4b --limit 50   # smoke test
python scripts/run_hulu.py --model qwen3.5:4b --reset      # nulláról újra
python scripts/run_hulu.py --model qwen3.5:4b --status     # csak állapot (nem futtat)

# Generatív benchmarkok után LLM-judge (gemini-3-flash-preview bíró) KÖTELEZŐ
python scripts/judge_hugme.py --model qwen3.5:4b
python scripts/judge_mt_bench.py --model qwen3.5:4b --baseline deepseek-v4-flash:cloud

# OpenAI-kompatibilis backend (Ollama /v1, llama-server, stb.) — cloud modellek
# is futtathatók, mert az Ollama átproxizza őket. Ugyanaz a checkpoint/stop-on-error.
python scripts/run_hulu.py --model gpt-oss:20b-cloud --backend openai --base-url http://localhost:11434/v1

# Aggregáció + riport (csak az utolsó lépés)
python scripts/aggregate_results.py
```

Nincs `lint`, `test`, `typecheck`, `format`, `build` — ne találj ki ilyeneket. Nincs CI, nincs pre-commit, nincs pytest.

## A checkpoint / stop-on-error rendszer SZENT

A scriptek **`stop-on-error + resume`** szemantikát követnek — a projekt alapvető tervezési elve:

- Bármilyen Ollama/backend hiba (429, 5xx, timeout, connection error, modell nem található) → `OllamaFatalError` (ős: `FatalBackendError`) → futás AZONNAL megáll.
- State atomi write (`tmp` + `os.replace`) `state/{model_safe}-{mode}/hulu.json`-ba (`scripts/checkpoint.py`).
- `results/{model}/hulu_results.jsonl` append-only, minden item után `flush` + `fsync`.
- `python scripts/run_hulu.py --model X` bármikor újraindítható — onnan folytat, ahol abbahagyta (`--reset` nélkül).
- Ha egy futás `failed_stopped`, az aggregátor riportján `⚠️ Részleges eredmények` figyelmeztetés + `[RÉSZLEGES]` composite score jelenik meg.

Részletek: `wiki/concepts/checkpoint-progress.md`. Bármilyen retry/logging/sleep-loop ötlet előtt OLVASD EL ezt az oldalt.

## Konvenciók (nem nyilvánvaló a kódból)

- **Modellnév → mappa:** `model.replace(":", "-").replace("/", "-") + f"-{mode}"` (`scripts/run_hulu.py:97`). Pl. `qwen3.5:4b` + `nothink` → `qwen3.5-4b-nothink`. Mindig ezt alkalmazd fájlútvonalnál.
- **Cloud modell-pool:** a forrása a `scripts/queue_all_benchmarks.sh` `MODELS` tömb (nem a wiki) — ott van az aktuális lista és a `:cloud` suffix konvenció. Ha egy korábban RETIRED-nek írt modell még szerepel a scriptben, a script az igazság — ne távolítsd el anélkül, hogy ellenőriznéd.
- **Cloud modell rákérdezés:** ha a modell nincs helyben és nem `:cloud` suffix-szel végződik, a script megkérdezi, cloud-ként akarod-e.
- **Ollama kliens beállítások** (`scripts/stop_on_error.py`): `temperature: 0.0`, `stream: False`, `num_predict` alapértelmezetten `4096` (nothink), think módban `16384` (`scripts/run_hulu.py:195`). Ne változtasd meg — az eredmények reprodukálhatósága függ tőle.
- **Composite score súlyok:** 40% statisztikai + 40% generatív + 20% nyelvészeti, hardcoded `scripts/aggregate_results.py:30` (`W_STAT, W_GEN, W_LING`). STAT=`[hulu, mmlu_hu]`, GEN=`[hugme, mt_bench_hu]`, LING=`[ud_hungarian]`. Ha egy dimenzió hiányzik, a súlyok újraosztódnak — NE változtasd meg.
- **HuLU riportolási konvenció (KÖTELEZŐ):** a riportban a HuLU **összesített** pontosság mellett a 6 NLU sub-task (HuCOLA, HuCoPA, HuRTE, HuSST, HuWNLI, HuCB) eredményeit **külön táblázatban, külön-külön is** fel KELL tüntetni minden modellre (nothink ÉS think módban). Az összesített HuLU score önmagában nem elég — a per-sub-task bontás kötelező, nem opcionális. Sub-task hiány esetén a sort tilos "—" helyettesítővel kitölteni; a futást el kell végezni. (Részletes forma: `wiki/reports/riport-template.md` HuLU szekciója.)
- **Benchmark-leírás konvenció (KÖTELEZŐ):** minden riportban, **minden benchmark-szekció elejére** be KELL tenni egy rövid (2-4 soros) leírást arról, hogy az adott benchmark **mit tesztel** (milyen képességet mér, milyen formátumban, milyen kimenettel). Ez a kötelező fejléc a HuLU, MMLU-HU, HuGME, MT-Bench-HU és UD Hungarian szekciókban is — nem opcionális. (Minta: `wiki/reports/report-2026-07-14.md`.)
- **Kvantálás konvenció (KÖTELEZŐ):** minden riportban a modellek **kvantálási szintjét** kötelezően szerepeltetni kell (külön "Modell-kvantálás" szakasz a fejléc után, vagy oszlop a modell-táblázatban). **Új modell futtatása előtt mindig rá kell kérdezni a felhasználóra: milyen kvantálással fut (pl. q4_K_M, fp16, awq, stb.), vagy cloud-e.** Ha a modell Ollama Cloud alatt fut (így a lokális kvantálás nem ismert), akkor `ollama-cloud` értéket kell beírni — nem lehet üresen hagyni.
- **Több kvantálás ugyanarra a modellre:** előfordulhat, hogy egy modellt több kvantálással is futtatunk benchmarkra. Ilyenkor minden (modell × kvantálás) kombináció **külön sor** a riportban, és a mappa-útvonalban is különválik (a modell-bélyegző tartalmazza a kvantálást). Ellenőrizd a scriptet, ha szükséges. A "Modell-kvantálás" szakaszban is külön sor minden kombinációnak.
- **Backend konvenció (KÖTELEZŐ a riportban):** a benchmarkok futtathatók közvetlen Ollama backenden (`--backend ollama`, default) vagy OpenAI-kompatibilis backenden (`--backend openai --base-url ...`). Ha a futtatás **nem** közvetlen Ollama volt, a riportban a modellnél fel kell tüntetni a backendet. A `results/*.jsonl` sorai tartalmazzák a `"backend"` mezőt — ebből visszakereshető. A checkpoint/stop-on-error rendszer backend-független (közös `FatalBackendError`).
- **Nyelv:** magyar a wikiben, angol a kódban. Docstring/comment/user-facing üzenet **magyarul**. Új scriptnél tartsd ezt a kevert stílust.
- **Wiki írás — KÖTELEZŐ módszer:** a `wiki/` mappában bármilyen oldal létrehozásakor/szerkesztésekor a **Karpathy LLM Wiki módszert** kell használni (lásd `wiki/SCHEMA.md` és a `wiki-karpathy-method` projekt-skillt `.opencode/skills/`-ban). Szabályok röviden: kötelező oldal-fejléc-blokk (típus/forrás/létrehozva/frissítve, NEM YAML frontmatter), oldal-univerzum szerinti mappa (`concepts/`, `entities/`, `comparisons/`, `runbooks/`, `reports/`), standard relatív markdown linkek (Obsidian `*wikilink*` tilos), preserve & extend elv, új oldalnál `index.md` + `log.md` frissítése.

## Hova NE nyúlj

- `scripts/stop_on_error.py` retry-táblái (`NO_RETRY_CODES={400,404,422}`, `RETRYABLE_CODES={429,500,502,503,504}`) szándékosan szűkek. Ne bővítsd a retry-t anélkül, hogy érted a stop-policy-t.
- `state/` atomi write mintája (`tmp` + `os.replace`) kritikus a részleges állapot ellen. Ne cseréld `open()+write()`-ra.
- `results/*.jsonl` append-only + `fsync` a hosszú futás alatti adatvesztés ellen. Ne írj egyetlen `json.dump`-pal az egészet.
- Ha bármit változtatsz a checkpoint rendszeren, FRISSÍTSD a `wiki/concepts/checkpoint-progress.md`-t is.

## Gyors referencia

| Keresed | Hol |
|---------|-----|
| Projekt-térkép, gyors indulás | `README.md` (gyökér) |
| Checkpoint tervezési elv | `wiki/concepts/checkpoint-progress.md` |
| HuLU futtatás lépésről lépésre | `wiki/runbooks/run-hulu-modell-x.md` |
| Környezet beállítás | `wiki/runbooks/setup-kornyezet.md` |
| Aggregáció + riport | `wiki/runbooks/aggregate-results.md` |
| Debug: modell nem válaszol | `wiki/runbooks/debug-modell-nem-valaszol.md` |
| LLM judge prompt template | `wiki/runbooks/llm-judge-prompt-template.md` |
| Wiki katalógus | `wiki/index.md` |
| Wiki formátum/szabályok | `wiki/SCHEMA.md` |
| Aktuális állapot, változásnapló | `wiki/log.md` |

Ha a wikiben valamit nem találsz, nézd előbb a `wiki/index.md` kategóriáit — valószínűleg csak rossz útvonalat tippeltél.
