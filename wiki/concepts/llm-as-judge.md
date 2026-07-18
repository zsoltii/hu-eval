# LLM-as-a-Judge — Módszertan

*Típus:* concept
*Forrás(ok):*
- Zheng, L., Chiang, W., Sheng, Y., et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." arXiv:2306.05685
- DeepEval dokumentáció: <https://docs.confident-ai.com/>
- Cohen, J. (1960). "A coefficient of agreement for nominal scales."
- Belső projekt: hu-eval overview — lásd [Overview](../overview.md)

*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Mi az LLM-as-a-Judge?

Az **LLM-as-a-Judge** (röviden: LLM-bíró) egy olyan értékelési módszer, ahol egy **erős, megbízható LLM** (a „bíró") pontozza vagy hasonlítja össze egy másik modell (a „jelölt") válaszait. A módszer elterjedése az MT-Bench (Zheng et al., 2023) óta robbanásszerű, mert:

- **Olcsóbb**, mint az emberi pontozás (1-2 nagyságrenddel).
- **Skálázható** — percek alatt több ezer választ lehet bíróval pontozni.
- **Konzisztens** — nem fárad el, nem változik a kedve.
- **Korlátai** is vannak: bias, hallucináció, pontatlanság — ezeket kezelni kell.

## Mikor használjuk, és mikor nem?

### Használjuk, ha

- Sok szabad szöveges választ kell pontozni (100+).
- A pontozási skála jól definiálható (1-5, 1-10, 0-1).
- A bíró modell erősebb, mint a jelölt.
- Van emberi spot-check a validációhoz.

### NE használjuk, ha

- A feladat **referencia nélküli** és erősen **szubjektív** (pl. „melyik vers szebb").
- A jelölt modell **erősebb**, mint a bíró (fordított esetben a bíró limitál).
- A válasz **tényszerű pontossága** kritikus (orvosi, jogi tanács) — ilyenkor dedikált fact-check modell + emberi reviewer kell.
- A feladat **túl rövid** (egy-egy szavas válasz) — a bíró prompt-overhead-je miatt nem éri meg.

## A négy fő buktató (bias)

A LLM-bírók ismert torzításai (lásd Zheng et al. 2023):

### 1. Pozíció-bias (Position Bias)

A bíró hajlamos az **A** pozícióban lévő választ favorizálni, vagy fordítva, attól függően, hogy melyiket olvassa először. Megoldás:

- **Véletlen csere:** a bíró minden kérdésnél 50% eséllyel kapja az A-t és B-t fordítva.
- **Kétmenetes bírás:** ha a bíró az első menetben A-t választja, a másodikban (felcserélt pozíciókban) ismét pontozzon. Csak akkor tekintsd döntésnek, ha mindkét menet ugyanazt a győztest mondja.

### 2. Hossz-bias (Length Bias)

A hosszabb válaszokat a bíró hajlamos jobbnak ítélni, tartalomtól függetlenül. Megoldás:

- A promptban **explicit korlát:** „a rövidebb, de pontosabb választ preferáld, ha a tartalom megegyezik".
- A bíró promptban **hossz-normalizálás:** „1.0-szor hosszabb válasz ≠ 2× jobb, ha nincs tartalmi többlet".
- A mérésben **külön riporter** a hossz-statisztika (átlag, medián, percentilisek), hogy a bíró ne díjazza a feleslegesen hosszú válaszokat.

### 3. Hízelgés-bias (Sycophancy Bias)

A bíró hajlamos a „bókoló", a felhasználó véleményével egyetértő válaszokat jobbnak ítélni, még ha azok tartalmilag pontatlanok is. Megoldás:

- A promptban explicit **anti-sycophancy** utasítás: „Ha a kérdés tartalmilag téves, a válasz nem az egyetértést, hanem a korrekciót díjazza."
- A rubric-ok **szétválasztása:** a stílus-pontszám és a tartalom-pontszám legyen külön mező.

### 4. Self-bias (Saját modell favorizálása)

A bíró hajlamos a **saját maga stílusában** írt válaszokat jobbnak ítélni. Megoldás:

- **Mindig más modell legyen a bíró**, mint a jelölt.
- Ha mindenki mást bíróként használunk, periodikusan rotáljuk: `gemini-3-flash` → `deepseek-v4-pro` (a `kimi` bíró státusz törölve).

## Bíró modell kiválasztása

A bíró modell kiválasztásának szempontjai (súlyozott lista):

| Szempont | Súly | Megjegyzés |
|----------|------|------------|
| **Magyar nyelvi minőség** | 30% | A bíró legalább középszinten kezelje a magyart, lehetőleg ne legyenek mondatszerkezeti furcsaságok. |
| **Erő** (általános képességek) | 25% | A bíró legyen a jelöltnél legalább olyan erős. |
| **Konzervatív pontozás** | 20% | A bíró ne legyen „bókezű" — inkább szigorú, mint elnéző. |
| **Költség / sebesség** | 15% | 1000+ hívásnál a költség domináns. |
| **Bias-mentesség** | 10% | A 4 fő biai típusra ismert mitigációs technikákat ismerjen. |

A hu-eval projekt konkrét sorrendje: `gemini-3-flash-preview:latest` > `deepseek-v4-pro:cloud` (a kimi bíró státusz törölve 2026-06-07, v1.2.4). Lásd [HuGME](hugme-benchmark.md).

## Inter-rater reliability: Cohen-féle κ

Az **ember ↔ LLM-bíró egyezés** mérésére a Cohen-féle **kappa (κ)** statisztikát használjuk. Értelmezése (Landis & Koch, 1977):

| κ érték | Egyezés szintje |
|---------|-----------------|
| < 0.00 | Rosszabb, mint a véletlen |
| 0.00–0.20 | Elhanyagolható |
| 0.21–0.40 | Csekély |
| 0.41–0.60 | Közepes |
| 0.61–0.80 | Jelentős (a hu-eval cél-κ) |
| 0.81–1.00 | Majdnem tökéletes |

### Számítás Pythonban (illeszkedési példa)

```python
from sklearn.metrics import cohen_kappa_score

# Emberi pontozók (3 független), 0-5 skála
human_scores = [4, 3, 5, 2, 4, 3, 1, 5, 4, 2]

# Ugyanazokra a válaszokra az LLM-bíró pontszámai
llm_scores   = [4, 3, 4, 2, 5, 3, 1, 4, 4, 2]

# Cohen-féle κ (lineárisan súlyozott, mert ordinális skála)
kappa = cohen_kappa_score(human_scores, llm_scores, weights='linear')
print(f"Cohen-féle κ (lineáris): {kappa:.3f}")
# 0.85 — majdnem tökéletes egyezés
```

Több mint 2 pontozó esetén **Fleiss-féle κ** használata javasolt.

## Magyar nyelvű bíró promptolás — tippek

A magyar promptolás sajátosságai, amiket a hu-eval projekt a bíró promptoknál alkalmaz:

1. **Használj magyar utasítást a prompt elején.** Az angol nyelvű utasítás + magyar szöveg keveredése rontja a pontosságot. Pl. „Te egy magyar nyelvű bíró vagy" — ezt mindig tedd az első mondatba.

2. **A magyar nyelvhelyességi hibák kezelése.** A bíró ne büntesse a kisebb helyesírási hibákat, ha a tartalom helyes. A promptban explicit: „A nyelvhelyesség a pontszám max. 20%-a, a tartalom 80%."

3. **Magyar nevek, helyek, évszámok precizitása.** A bíró promptban mindig add át az esetleges referenciát: „Ha a válaszban konkrét évszám, név, vagy helyszín van, ellenőrizd a magyar forrásokkal való egyezést."

4. **A „Te" vs. „magázó" kérdése.** A magyar promptokban explicitté kell tenni a regisztert: „A választ légy tegező vagy magázó formában értékeld, ahogy a kérdés kéri." A bíró ne büntesse a tegező választ, ha a kérdés tegező, és fordítva.

5. **A magyar modalitás, bizonytalanság.** A magyarban gyakori a „talán", „valószínűleg", „úgy tűnik" — ezek nem bizonytalanság-jelek a modellnél, hanem természetes stílus. A bíró ne büntesse ezeket automatikusan.

## Általános bíró prompt template (magyar, univerzális)

```text
Te egy magyar nyelvű LLM-bíró vagy. A feladatod: pontozd a CANDIDATE
választ 0.0–1.0 között a {METRIC} metrika szerint.

[INPUT — felhasználói kérdés]
{input}

[CANDIDATE — értékelt modell válasza]
{output}

[REFERENCE — arany válasz, ha van]
{reference}

[RUBRIC — metrika-specifikus]
{rubric}

[ÁLTALÁNOS SZABÁLYOK]
- Csak a CANDIDATE szövegét értékeld, ne a kontextust.
- Ha a CANDIDATE üres vagy „Nem tudom" típusú, adj 0.0-t.
- Légy konzervatív: 0.7+ pontszámot csak valóban kiváló válaszra adj.
- A magyar nyelvhelyesség max. 20%-ban számít a tartalomhoz képest.
- A hosszabb válasz nem automatikusan jobb — csak ha tartalmi többlet van.
- Ha a CANDIDATE kitalál egy tényt (hallucináció), büntetőpont.

[VÁLASZ]
Pontszám: <0.00–1.00, két tizedesjeggyel>
Indoklás: <1-3 mondat magyarul>
```

## Melyik bíró modellt mikor?

| Feladat | Ajánlott bíró | Megjegyzés |
|---------|---------------|------------|
| Egyszerű single-turn pontozás (HuGME) | `gemini-3-flash-preview:latest` | Erős, konzervatív; a kimi bíró státusz törölve 2026-06-07 (v1.2.4) |
| Multi-turn, GSB pairwise (MT-Bench-HU) | `deepseek-v4-pro:cloud` | Olcsóbb, elég a 6-8 modell összehasonlításhoz |
| Kulturális, szabad kérdés (Szabad-Kérdés-HU) | `gemini-3-flash-preview:latest` | Magyar specifikum, κ-validációval; a kimi bíró státusz törölve 2026-06-07 (v1.2.4) |
| Gyors smoke-test (ciklus elején) | `gemini-3-flash-preview:latest` | Olcsó, „durva" szűrő |
| Végső riport-validáció (emberi review) | emberi szakértő | Minimum 2 emberi pontozó, κ-számítás |

## Limitációk és nyílt kérdések

- **Lánc-gondolkodás (CoT) hatása:** egyes kutatások szerint a bíró promptban a CoT („gondolkodj lépésről lépésre") javítja a pontosságot, mások szerint rontja (mert a bíró is hallucinálhat a gondolatmenetben). A hu-eval projekt **mindkét módot** kipróbálja, és a κ-val validálja, melyik a jobb magyar szövegen.
- **Több-bíró konszenzus:** nagy értékeléseknél érdemes 2-3 különböző bíró modellt futtatni, és a konszenzust venni (vagy a „legbizonytalanabb" kérdéseket emberi review-ra jelölni).
- **A bíró modell frissítése:** ha a bíró modellt frissítjük (pl. `gemini-3-flash-preview` → újabb verzió), a korábbi eredményeket újra kell futtatni — a bíró verziója meta-adat, és a riportban mindig jelölni kell.

## Összefüggés

- [HuGME](hugme-benchmark.md) — ahol a bíró promptot konkrétan használjuk
- [MT-Bench-HU](mt-bench-hu.md) — GSB pairwise stratégia
- [Szabad kérdés HU](szabad-kerdes-hu.md) — κ-validáció, emberi-LLM egyezés
- [Overview](../overview.md) — projekt kontextus
- [SCHEMA](../SCHEMA.md) — oldalformátum

## Hivatkozások

- Zheng, L. et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." arXiv:2306.05685. <https://arxiv.org/abs/2306.05685> — a LLM-as-a-Judge módszertan alapreferenciája, a 4 fő bias azonosítása.
- Cohen, J. (1960). "A coefficient of agreement for nominal scales." — a κ-statisztika.
- Landis, J. R., & Koch, G. G. (1977). "The measurement of observer agreement for categorical data." — a κ-értelmezési sávok.
- DeepEval: <https://docs.confident-ai.com/> — `GEval`, `LLMTestCase` — implementációs referencia.
- FastChat LLM Judge: <https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge> — az LMSYS bíró-prompt template-jeinek forrása.
