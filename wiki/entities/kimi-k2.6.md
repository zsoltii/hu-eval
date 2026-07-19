# Kimi K2.6 (Cloud)

*Típus:* entity
*Forrás(ok):* Moonshot AI official model card, belső benchmark eredmények
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15 (v1.3 — benchmark modellként, végleges baseline eredményekkel)

---

## Azonosítás

- **Teljes név:** Kimi-K2.6 (Ollama alias: `kimi-k2.6:cloud`)
- **Szolgáltató:** Moonshot AI (kínai, 2023-ban alapított, hosszú kontextus specialistái)
- **Paraméterszám:** 1.04T összesen, aktív ~32B (MoE, "sparse activated" — 384 expert, ebből tokenenként 8 aktív)
- **Elérhetőség:** cloud-only, Ollama-n keresztül `ollama run kimi-k2.6:cloud`
- **Státusz a projektben:** aktív, **benchmark modell** (v1.2.4 óta a bíró státusz törölve — a HuLU/MMLE/HuGME/MT-Bench/UD fut rajta)
- **Megjelenés:** 2025 Q4 — a K2.5 utódmodellje

> 📝 **Szerep-változás:** eredetileg (v1.2.1–v1.2.3) judge + benchmark volt, majd v1.2.4-ben a bíró státusz véglegesen törölve — a kimi KIZÁRÓLAG benchmark modellként szerepel. A bíró pool jelenleg a `deepseek-v4-pro:cloud`-ból áll (2026-07-19 óta; a `gemini-3-flash-preview:latest` megszűnt 2026-07-14).

## Képességek

### Kontextus ablak
- **Névleges:** 2 000 000 token (!) — a Moonshot Kimi sorozat fő USP-je a hosszú kontextus
- **Effektív:** a Moonshot saját needle-in-a-haystack tesztjei szerint 1.5M-ig megbízható, felette lassú, de működik
- **A projektben:** a 2M ablak azért kritikus, mert az MT-Bench-HU és a HuGME konverzációk mellett a bíró modellnek gyakran az EGÉSZ válasz-sorozatot egyszerre kell látnia

### Modalitások
- **Bemenet:** szöveg (akár 2M token)
- **Kimenet:** szöveg (rövid, strukturált — pontozásra van optimalizálva)
- **Különleges:** a Kimi K2.6-t a Moonshot kifejezetten "értékelő" (evaluator) use-case-re is fine-tune-olta, nem csak általános chat-re

### Nyelvek
- **Elsődleges:** kínai (mandarin), angol
- **Támogatott:** magyar, japán, koreai, francia, német, orosz, spanyol — kb. 20 nyelv
- **Magyar:** közepes — önmagában a modell magyar generálásban nem kiemelkedő, de a magyar szöveg ÉRTELMEZÉSE és ÉRTÉKELÉSE az, amiben erős

### Speciális tokenek / formátum
- Saját chat template, hosszú kontextushoz optimalizált pozicionális enkódolással
- System prompt: igen, kifejezetten hosszú system prompt-ot támogat (akár 50k token)
- Function calling: igen
- JSON mode: igen, **constrained decoding** támogatással (a pontozási séma strict betartatására)

## Várható magyar minőség (mint bíró)

- **Erősségek:**
  - Strukturált pontozási feladatokban (1-10 skála, Likert, pairwise comparison) a magyar utasításokat is jól követi
  - A magyar és angol szövegek kereszt-értékelésében (mixed-language scoring) jobb, mint a kisebb modellek
  - A hosszú kontextus miatt a teljes beszélgetést egyszerre tudja értékelni, nem veszít kontextust
- **Gyengeségek:**
  - Magyar-specifikus stíluskonvenciók pontozásánál (pl. irodalmi hivatkozások, regionális kifejezések) néha túl liberális
  - Hajlamos a felszínes, de "helyesnek tűnő" válaszokat jobbra értékelni, mint a ténylegesen pontosakat (megfontolandó: a bíró elfogultság csökkentéséhez lásd: [Position bias](../concepts/llm-as-judge.md))

- **Becsült bíró-pontosság (agreement with human):** ~0.78-0.82 Cohen-kappa a magyar MT-Bench válaszokra
- **Bias:** enyhe pozíció-bias (a második helyen lévő választ hajlamos kicsit jobbra értékelni) — lásd a megfelelő concept oldalt

## Költség

- **Tier:** cloud, rate-limited
- **Ár:** a Moonshot API-n $0.15 / 1M input token, $0.60 / 1M output token (a K2.5 alapján; K2.6-ra várhatóan hasonló)
- **Ollama cloud route:** ingyenes, de erősen rate-limited (napi 50-100 hívás, burst 5/perc — a modell mérete miatt)
- **Lényeg:** a bíró szerep miatt KEVÉS hívás kell (tipikusan 1-2 hívás / MT-Bench item), tehát a kvóta elég

## Eredmények (v1.3 baseline, 2026-07-14)

| Mód | HuLU | MMLU-HU | HuGME | UD | Composite (40/40/20) |
|-----|------|---------|-------|-----|----------------------|
| nothink | 75.9% | 73.7% | 9.4% | 61.8% | **54.2%** (2. hely) |
| think | 75.2% | 92.7% | 9.4% | 0.0% | **45.5%** |

- 🥈 **2. hely composite** (nothink): 54.2% — nagyon közel a győztes deepseek-v4-pro (54.3%)-hoz
- 🥇 **Legjobb MMLU-HU** (think): 92.7% (egyenlő glm-5.1/glm-5.2/qwen3.5-think-kel)
- **Tradeoff:** a think mód javítja a statisztikait (MMLU 73.7% → 92.7%), de az UD-t 61.8% → 0.0%-ra rontja (CoT-zavar)

## Ajánlott felhasználási területek

A projekt kontextusában a Kimi K2.6 benchmark modellként szerepel:

- **HuLU / MMLU-HU** — statisztikai benchmarkok futtatása
- **HuGME / MT-Bench-HU** — generatív benchmarkok (jelenlegi bíró: deepseek-v4-pro:cloud, 2026-07-19 óta; a gemini-3-flash-preview megszűnt 2026-07-14)
- **UD Hungarian** — szintaktikai elemzés (nothink módban erős: 61.8%)

**NEM használjuk:**
- Bíróként (v1.2.4 óta törölve a judge szerep)
- Production deployment (nincs SLA, a Moonshot startup)

## Összekapcsolások

- [LLM-as-a-Judge](../concepts/llm-as-judge.md) — a bíró keretrendszer (a kimi már nincs benne)
- [MT-Bench-HU](../concepts/mt-bench-hu.md) — generatív benchmark
- [HuGME](../concepts/hugme-benchmark.md) — generatív LLM-judge
- [HuLU](../concepts/hulu-benchmark.md) — magyar NLU benchmark
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Qwen 3.5 Cloud](qwen3.5-cloud.md) — a pool legnagyobb modellje
