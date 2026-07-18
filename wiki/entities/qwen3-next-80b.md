# Qwen3-Next 80B (Cloud)

*Típus:* entity
*Forrás(ok):* Alibaba Cloud Qwen team hivatalos model card, Ollama `/api/show` válasz, belső benchmark mérések (2026-06-10/11)
*Létrehozva:* 2026-06-10
*Frissítve:* 2026-06-11 (v1.2.7 — első benchmark eredmények)

---

## Azonosítás

- **Teljes név:** Qwen3-Next 80B (Ollama alias: `qwen3-next:80b-cloud`)
- **Szolgáltató:** Alibaba Cloud / Qwen Team (kínai, Hangzhou)
- **Paraméterszám:** 80 milliárd
- **Kvantizálás:** FP8 (8-bit floating point) — az Ollama cloud provider FP8-ban tárolja
- **Elérhetőség:** cloud-only az Ollama registry-n keresztül
- **Státusz a projektben:** aktív benchmark modell (2026-06-10 óta, a `queue_runner.sh` és `phase2_runner.sh` `MODELS` tömbjében a 2. pozícióban)
- **Szerep:** benchmark (mind nothink, mind think módban fut)

## Képességek

### Kontextus ablak
- **Névleges:** 262 144 token (a Qwen3-Next sorozat legnagyobb kontextusa, jóval meghaladja a korábbi Qwen 3.5 256K-t)
- **Effektív:** gyakorlatban a 262K kontextusvégi romlás egyelőre nem mért a projektben (a HuLU átlagos promptja ~300-2000 token, az MMLU-HU 5-shot promptja ~500-1500 token)

### Architektúra
- **Típus:** Qwen3-Next — a Qwen 3.5 utódja, hatékonyabb architektúrával
- **Paraméter: 80B**, ami a Qwen 3.5 dense sorozat (397B) és a Qwen 3.5 MoE (30B-A3B, 235B-A22B) között helyezkedik el
- **FP8 kvantizálás:** az Ollama cloud provider FP8-ban tárolja a modellt, ami kisebb memóriahasználatot és gyorsabb inferenciát eredményez a normál FP16/BF16-hoz képest

### Modalitások
- **Bemenet:** szöveg (text-only)
- **Kimenet:** szöveg
- **Multimodalitás:** a Qwen3-Next dense verziók nem multimodálisak (a Qwen-VL a külön sorozat)

### Nyelvek
- **Elsődleges:** kínai (mandarin), angol
- **Támogatott:** magyar, japán, koreai, francia, német, orosz, spanyol, arab, hindi — a Qwen család széles multilingual lefedettséget örökölte
- **Magyar:** erős — a Qwen család magyar nyelvű teljesítménye következetesen jó, de a 80B paraméter + FP8 kvantálás a Qwen 3.5 397B-nél gyengébb pontszámot valószínűsít

### Speciális tokenek / formátum
- Saját chat template, "thinking" mód támogatással (capabilities: `["completion", "thinking", "tools"]`)
- System prompt: igen
- Function calling: igen (tools capability)
- JSON mode: igen
- **Qwen-specifikus:** "enable_thinking" / `think` flag — boolean paraméterként kapcsolható

### Ollama API részletek (`/api/show`)

```json
{
  "details": {
    "parent_model": "qwen3-next:80b",
    "family": "qwen3next",
    "parameter_size": "80000000000",
    "quantization_level": "FP8"
  },
  "model_info": {
    "general.architecture": "qwen3next",
    "general.parameter_count": 80000000000,
    "qwen3next.context_length": 262144,
    "qwen3next.embedding_length": 2048
  },
  "capabilities": ["completion", "thinking", "tools"]
}
```

## Várható magyar minőség

### Elméleti pozícionálás
- **A Qwen 3.5 397B "kistesója"** — 80B paraméter vs 397B, de FP8 kvantálás és hatékonyabb architektúra miatt a teljesítménykülönbség várhatóan kisebb, mint a paraméterszám-különbség sugallná
- **A pool középmezőnye** — a 80B + FP8 + hatékony architektúra a `kimi-k2.6:cloud` (1T, int4) és a `qwen3.5:cloud` (397B) közé helyezi

### Végleges HuLU benchmark eredmények (v1.2.9, 2026-06-12, teljes 2581 prompt)

| Mód | Composite | Overall | HuCOLA | HuCoPA | HuRTE | HuSST | HuWNLI | HuCB |
|-----|-----------|---------|--------|--------|-------|-------|--------|------|
| **nothink** | 60.5% | 61.4% | 57.6% | 92.0% | 93.8% | 58.5% | 5.0% | 56.3% |
| **think** | 66.0% | 63.2% | 58.1% | 91.0% | 93.0% | 60.5% | 35.0% | 58.3% |

- **Nothink:** Composite 60.5% (pool 19-ből a **19. — utolsó hely**), Overall 61.4%. A legerősebb sub-task: HuRTE 93.8%; a leggyengébb: HuWNLI 5.0% (közel a 0%-os szélső esethez)
- **Think:** Composite 66.0% (17. hely), Overall 63.2% (19. hely). A think mód itt **+5.5%-ot javít** a Composite-on és +1.8%-ot az Overall-ön
- **A korábbi részleges adat (66.6% think, 67.2% nothink) félrevezető volt** — a teljes benchmark futás 60.5%/66.0%-ot hozott, és a think MÓD VALÓJÁBAN JAVÍT a nothink-en (a részminta kiegyensúlyozatlan volt HuWNLI-ből)
- **Pool-pontszám (Composite szerinti):** nothink 19/19, think 17/19. A `qwen3-next-80b-cloud` a **leggyengébb modell** a poolban mindkét módban

### Sub-task szintű megfigyelések

- **Erős:** HuRTE 93.8% (nothink) — az olvasásértő entailment a legerősebb sub-task
- **Gyenge:** HuWNLI 5.0% (nothink), 35.0% (think) — a magyar nyelvű természetes nyelvű inferencia nehéz, de a think MÓD SOKAT JAVÍT (+30%)
- **Meglepetés:** a think mód **javít** a Qwen3-Next 80B-nél, de a Composite még mindig a legalacsonyabb a poolban. A Qwen3-Next 80B inkább "kompakt, gyors modell" trade-off, nem minőségi mennyezet

### Stílus
- A Qwen3-Next magyar szövege általában pontos, de a 80B-s modell néha "túl konzervatív" válaszokat ad
- A thinking trace-ek gyakran rövidek, mint a Qwen 3.5 397B-nél (kevesebb gondolkodási kapacitás)

## Implementációs státusz (2026-06-10/11)

- ✅ `scripts/queue_runner.sh` — `MODELS` tömbben a 2. pozícióban
- ✅ `scripts/phase2_runner.sh` — `MODELS` tömbben a 2. pozícióban
- ✅ `wiki/overview.md` — modell táblázatban szerepel
- ✅ `wiki/log.md` — v1.2.7 bejegyzés dokumentálja a hozzáadást
- ✅ Benchmark futás kész (v1.2.9, 2026-06-12, 2581/2581 prompt mindkét módban)
- ⏳ MMLU-HU, HuGME, MT-Bench-HU — ezekhez még nincs runner script

## Korábbi verziók / architektúra evolúció

- **Qwen 3.5 397B (dense)** — 397B paraméter, FP16 — a Qwen3-Next elődje, a poolban `qwen3.5:cloud` néven
- **Qwen 3.5 235B-A22B (MoE)** — 235B összes, 22B aktív — a Qwen team MoE kísérlete
- **Qwen3-Next 80B (dense, FP8)** — 80B, FP8, hatékonyabb architektúra — a Qwen 3.5 utódja, **ez az aktuális**

## Kapcsolódó

- [Qwen 3.5 397B (Cloud)](qwen3.5-397b.md) — az előd, 397B paraméter
- [Qwen 3.5 Local](qwen3.5-local.md) — helyi Qwen 3.5 modellek (0.8B-4B)
- [Overview](../overview.md) — projekt cél, modell pool
- [Log: qwen3-next:80b-cloud hozzáadása](../log.md) — v1.2.7 bejegyzés
- [HuLU Benchmark](../concepts/hulu-benchmark.md) — első benchmark, ahol fut
- [Runbook: HuLU futtatás](../runbooks/run-hulu-modell-x.md) — lépésről lépésre
