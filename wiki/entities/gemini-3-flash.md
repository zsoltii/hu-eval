# Gemini 3 Flash Preview (Cloud)

*Típus:* entity
*Forrás(ok):* Google DeepMind hivatalos model card, belső használat
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-07-15 (v1.3 — bíró modellként, megszűnt 2026-07-14)

---

## Azonosítás

- **Teljes név:** Gemini 3 Flash Preview (Ollama alias: `gemini-3-flash-preview:latest`)
- **Szolgáltató:** Google DeepMind (Mountain View, CA, USA)
- **Paraméterszám:** nem publikus (a "Flash" sorozat a "kisebb, gyorsabb" verziót jelöli a Pro és Ultra mellett)
- **Elérhetőség:** cloud-only, Ollama-n keresztül `ollama run gemini-3-flash-preview:latest`
- **Státusz a projektben:** 🔴 **megszűnt** — bíró (LLM-as-a-Judge) modell volt, 2026-07-14. 09:00 CEST óta nem elérhető (Ollama megszűnés)
- **Megjelenés:** 2025 Q4 — a Gemini 2.5 Flash utódja, "preview" státuszban

> ⚠️ **Bíró modell volt:** a Gemini 3 Flash Preview kizárólag a HuGME és MT-Bench-HU kiértékelésére szolgált (v1.2.1 óta a judge pool egyetlen tagja). Mivel 2026-07-14-én megszűnt, **ezek az eredmények nem reprodukálhatóak** — új bíró modell (pl. `gemini-3-pro-preview` vagy más) szükséges a jövőbeli rejudge-hez. Benchmark modellként SOHA nem futott.

## Képességek

### Kontextus ablak
- **Névleges:** 1 000 000 token
- **Effektív:** a Google saját tesztjei szerint 1M-ig megbízható, kiemelkedő needle-in-a-haystack teljesítménnyel (~99% a teljes tartományban)
- **A projektben:** nem használjuk ki a teljes 1M-ot, de a hosszú MT-Bench konverzációk és a teljes HuLU kérdéssor egyszerre feldolgozható

### Modalitások
- **Bemenet:** szöveg + kép + hang + videó
- **Kimenet:** szöveg
- **A projektben:** CSAK szöveges módban használjuk (a multimodal képességeket nem benchmarkoljuk — lásd: [Overview](../overview.md), "kizárások" szakasz)
- **Megjegyzés:** a Flash verzió a multimodalitásban gyengébb, mint a Pro/Ultra testvérei

### Nyelvek
- **Elsődleges:** angol (a Google modellek az egyik legjobb multilingual coverage-szel rendelkeznek)
- **Támogatott:** magyar és további ~100 nyelv, kiemelkedő lefedettséggel az EU nyelvekben
- **Magyar:** erős-közepes — a Gemini 3 Flash a magyar nyelvű feladatokon rendre az MMLU-HU-n és hasonlókon a top 5-ben van a cloud modellek között

### Speciális tokenek / formátum
- Saját chat template, multimodalitásra optimalizált pozicionális enkódolás
- System prompt: igen, támogatja a hosszú, részletes rendszerüzeneteket
- Function calling: igen, "tools" néven
- JSON mode: igen, schema-constrained generation támogatással
- **"Thinking" mód:** a Gemini 3 sorozatban dedikált "thinking budget" paraméter — beállítható, hogy mennyi "gondolkodási" tokent használjon válaszadás előtt

## Várható magyar minőség

- **Tanító adatok:** a Google nyilvános adatai szerint a Gemini 3 sorozatot ~3T tokenen tanították, a magyar lefedettség az EU-s nyelvek között kiemelt
- **Tokenizáció:** SentencePiece-alapú, a magyar szöveget hatékonyan kezeli (1 token ~ 4-5 betű)
- **Becsült HuLU:** 0.68-0.74 tartomány (a Flash verziónál jellemzően 2-3 pontszám százalékkal alacsonyabb, mint a Pro-nál, de a magyar minőségben a különbség kisebb, mint az angolban)
- **Becsült MT-Bench-HU:** 7.3-7.8 / 10 — erős, de a stílus néha "Google-translate ízű" (túl sima, kevésbé természetes)
- **Erősség:** strukturált, tényszerű válaszok; matematikai és logikai feladatok magyarul
- **Gyengeség:** kreatív, irodalmi szöveg; regionális magyar kifejezések

## Költség

- **Tier:** cloud, rate-limited (a Google AI Studio kvóta függvénye)
- **Ár:** a Gemini 3 Flash preview API-n $0.075 / 1M input token, $0.30 / 1M output token — ez az egyik legolcsóbb cloud modell jelenleg
- **Ollama cloud route:** ingyenes, kvóta-korlátos (napi 1000-2000 kérés, burst 60/perc)
- **Lényeg:** a Gemini 3 Flash a legköltséghatékonyabb cloud modell a poolban

## Ajánlott felhasználási területek (eredetileg tervezett)

A projekt eredeti tervében a Gemini 3 Flash a következőkért felelt volna:

- **Gyors baseline** — a Flash a leggyorsabb a cloud modellek közül
- **Magyar tudás-mérés** — HuLU, MMLU-HU (de ezekhez végül nem ezt használtuk bírónak)
- **Bíró (LLM-as-a-Judge)** — ténylegesen ezt a szerepet töltötte be a HuGME és MT-Bench-HU kiértékelésében

> 🔴 **Jelenleg:** a modell megszűnt, így a fenti szerepek egyike sem elérhető. Új bíró modell szükséges a generatív benchmarkok rejudge-éhez.

## Ismert gyengeségek (mint bíró)

- **Pozíció-bias:** a judge script counterbalanced (swap) technikával kezelte
- **Self-overrefusal:** ártalmatlan magyar kérdéseknél is túlzott safety aktiválás
- **Preview instabilitás:** silent update-ek miatt a hash rögzítése kötelező lett volna

## Összekapcsolások

- [LLM-as-a-Judge](../concepts/llm-as-judge.md) — a bíró keretrendszer (a gemini volt az egyetlen judge)
- [HuGME](../concepts/hugme-benchmark.md) — 6 metrika, gemini bíróval pontozva
- [MT-Bench-HU](../concepts/mt-bench-hu.md) — GSB pairwise, gemini bíróval
- [Végleges riport](../reports/report-2026-07-14.md) — a gemini-bíró eredmények (nem reprodukálhatóak)
