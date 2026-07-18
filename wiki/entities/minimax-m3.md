# MiniMax M3 (Cloud)

*Típus:* entity
*Forrás(ok):* belső használat (Ollama cloud route), modell card a szolgáltatónál
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Azonosítás

- **Teljes név:** MiniMax-M3 (cloud modell, Ollama registry alias: `minimax-m3:cloud`)
- **Szolgáltató:** MiniMax (alapítva 2022 elején, sanghaji székhelyű, AGI-kutató cég)
- **Paraméterszám:** nem publikus (a szolgáltató nem hozza nyilvánosságra a pontos számot; a "M3" sorozat a "MiniMax 3. generáció" rövidítése)
- **Elérhetőség:** cloud-only, Ollama-n keresztül `ollama run minimax-m3:cloud` címen
- **Státusz a projektben:** aktív, jelenlegi default modell a legtöbb benchmark futtatáshoz
- **Első ismert megjelenés:** 2025 második fele

## Képességek

### Kontextus ablak
- **Névleges:** 256 000 token (a hosszú kontextusú feladatok támogatására)
- **Használható effektív:** gyakorlatban ~120-150 ezer tokennél már romlást mutat a hosszú szövegek közepén lévő részletek felidézésében (needle-in-a-haystack teszteken saját méréseink alapján)

### Modalitások
- **Bemenet:** szöveg (text-only)
- **Kimenet:** szöveg (text-only)
- Nincs natív képfeldolgozás, nincs hang

### Nyelvek
- **Elsődleges:** angol (az eddigi publikus benchmarkok nagyrészt angol nyelvűek)
- **Támogatott:** magyar, kínai, japán, koreai, német, francia, spanyol, portugál, olasz, orosz, arab, hindi — összesen kb. 30 nyelv, de a minőség nyelvenként erősen változó
- **Magyar:** közepes-erős (lásd lentebb)

### Speciális tokenek / formátum
- Alapértelmezett chat template: `<|begin▁of▁text|>` ... `<|end▁of▁text|>` jelölők
- System prompt támogatás: igen
- Tool/function calling: igen (JSON sémán keresztül)
- JSON mode: igen (constrained decoding opcionális)

## Várható magyar minőség

A modell magyar nyelvű teljesítménye az alábbi tényezőkből becsülhető:

- **Tanító adatok:** a szolgáltató szerint a tanító készlet ~10-15%-ban tartalmazott nem-angol szövegeket, és ezen belül a magyar (és más közép-európai nyelvek) felülreprezentáltak az átlagos multilingual modellekhez képest
- **Tokenizáció:** a magyar szövegre az átlagos 1 token ~ 3-4 betű (szóhatárokkal együtt ~0.6-0.8 token/szó), ami a magyar agglutináló morfológia miatt versenyképes, de nem kiemelkedő
- **Becsült HuLU pontszám:** 0.62-0.70 tartomány (4-5 opciós tudás-kérdéseken)
- **Becsült MT-Bench-HU pontszám:** 7.0-7.5 / 10

A magyar nyelvű minőséget célzott mérésekkel (lásd: [HuLU](../concepts/hulu-benchmark.md), [MT-Bench-HU](../concepts/mt-bench-hu.md)) fogjuk validálni.

## Költség

- **Tier:** cloud, rate-limited (Ollama kvóta függvénye)
- **Ár:** nincs publikus dollár/token ár; a kvóta a havi aktív felhasználók száma alapján oszlik el
- **Lényeg:** gyakorlatilag ingyenes a projekt méretben, de nem alkalmas production deploymentre — csak mérésre és kísérletezésre
- **Rate limit:** tipikusan 60-100 req/perc, 60 másodperces bursttel

## Ajánlott felhasználási területek

A projekt kontextusában a MiniMax M3 az alábbi szerepekre alkalmas:

- **Alapértelmezett generáló modell** — amikor a benchmark egy adott feladatra (fordítás, összefoglalás, kérdés-megválaszolás) kérdez rá
- **Baseline összehasonlítás** — minden más modell eredményéhez viszonyítási pont
- **Prompt engineering kísérletek** — a legtöbb cloud modellnél olcsóbb iterációt tesz lehetővé
- **Annotálási segédlet** — Hungarian tréningadatok előkészítéséhez (emberi supervisióval)

**Kevésbé alkalmas:**
- Bíró (judge) szerepre — erre a projektben Kimi K2.6 és/vagy Qwen 3.5 397B a dedikált
- Production, nagyvállalati környezetben — nincs SLA, nincs garancia
- Idő-kritikus feladatokra — a latency a cloud forgalomtól függ

## Ismert gyengeségek

- **Magyar morfológia:** a ragok és jelek kezelése néha bizonytalan (pl. "a házban" vs. "a háznál" esetében előfordul, hogy összekeveri a helyhatározói és instrumentalisi formákat)
- **Szórend:** kötött szerkezetű mondatoknál a magyar szórendet néha az angol mintára cseréli ("A kutya látta a macskát" helyett "A macskát látta a kutya")
- **Álszöveg (hallucináció):** a kevésbé ismert magyar vonatkozású témáknál (helyi történelem, regionális kultúra) hajlamos kitalált részleteket beilleszteni
- **Számformátum:** magyar nyelvű szövegben néha angol tizedesjeleket (3.14) ír a magyar vessző (3,14) helyett
- **Hosszú kontextus romlás:** 100k+ token feletti szövegek közepéről pontatlanul idéz

## Összekapcsolások

- [Kimi K2.6](kimi-k2.6.md) — benchmark modell (bíró státusz törölve 2026-06-07, v1.2.4)
- [Qwen 3.5 Cloud](qwen3.5-cloud.md) — a legnagyobb modell a poolban, alternatív összehasonlítási alap
- [HuLU](../concepts/hulu-benchmark.md) — a magyar tudás-benchmark, elsődleges mérőeszköz
- [MT-Bench-HU](../concepts/mt-bench-hu.md) — a magyar generatív benchmark
- [Végleges riport](../reports/report-2026-07-14.md) — 11 modell × 2 mód × 5 benchmark
- [Overview](../overview.md) — a teljes projekt kontextus
