# LLM-as-a-Judge prompt template (magyar)

*Típus:* runbook
*Forrás(ok):* [Zheng et al. 2023 — Judging LLM-as-a-Judge](https://arxiv.org/abs/2306.05685), [MT-Bench paper](https://arxiv.org/abs/2306.05685), [DeepEval docs](https://docs.confident-ai.com/)
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Cél

Újrafelhasználható, magyar nyelvű LLM-as-a-Judge prompt template, amivel generatív benchmarkok válaszait (HuGME, MT-Bench-HU, szabad kérdéssor) tudjuk automatikusan értékelni. A judge 1-10 skálán ad pontszámot, strukturált JSON kimenettel.

## Mikor használd

- **Generatív benchmark kiértékelés:** amikor a modell szabad szöveges választ ad (nem 0-9 számot)
- **Párhuzamos összehasonlítás:** két modell válaszát egymás mellé téve
- **Minőségi kontroll:** release előtti sanity check, hogy a modell nem romlott-e

## Mikor NE használd

- **Statisztikai benchmarkok** (HuLU, MMLU-HU): ott egzakt match kell, nem judge
- **Faktográfiai kérdések:** "Mikor volt a mohácsi csata?" — itt string-match jobb
- **Valós idejű rendszerek:** a judge +999 költség/tokent hozzáad, csak batch-ben éri meg

## A prompt architektúrája

Három részből áll:

1. **System prompt** — a judge szerepe, instrukciók, korlátok
2. **User prompt (rubric)** — a konkrét feladat, a két válasz, és az értékelési szempontok
3. **Output format** — kötelező JSON séma

### 1. System prompt

```text
Te egy tapasztalt magyar nyelvű szövegértékelő bíró (LLM judge) vagy. 
A feladatod: két modell által generált választ értékelsz egy adott kérdésre 
vagy utasításra. A cél az, hogy kiderítsd, melyik válasz jobb minőségű, 
pontosabb, hasznosabb és stílusban megfelelőbb.

Szabályok:
- Mindig objektíven, a rubrikus kritériumok alapján értékelsz — ne a válasz 
  hossza alapján, hanem a tartalom és pontosság szerint.
- Ha egy válasz hibás, félrevezető vagy nem releváns, azt alacsony pontszámmal 
  jelezd, függetlenül attól, hogy a másik válasz sem jobb.
- A pontszámok EGÉSZ számok 1 és 10 között. Tizedesjegyet NE használj.
- A magyar nyelvi minőséget (helyesírás, nyelvtan, idiomatikusság) is vedd 
  figyelembe.
- A kulturális kontextust ismerd: magyar nevek, helyek, események.
- Ha mindkét válasz egyformán jó/rossz, a pontszámok legyenek azonosak.

Válaszod CSAK JSON formátumban add, semmi mást ne írj a JSON köré.
```

### 2. User prompt — értékelési feladat

```text
Feladat / Kérdés:
---
{QUESTION}
---

A válasz, amit értékelned kell:
---
{RESPONSE}
---

Értékeld az alábbi szempontok szerint, mindegyikre 1-10 pontot adva:

1. **Pontosság (accuracy)**: A válasz tartalmilag helyes? Van benne ténybeli hiba?
2. **Relevancia (relevance)**: A válasz a feltett kérdésre/utasításra válaszol?
3. **Teljesség (completeness)**: Minden fontos aspektust lefed?
4. **Magyar nyelvi minőség (fluency)**: Helyesírás, nyelvtan, idiomatikusság?
5. **Hasznosság (helpfulness)**: A válasz mennyire segíti a felhasználót?

A rubrikák részletes leírása:

- **9-10 pont (Kiemelkedő)**: Tökéletes, hibátlan, minden szempontból kifogástalan.
  Szakértői szintű, azonnal felhasználható.
- **7-8 pont (Jó)**: Kisebb hiányosságok lehetnek, de összességében magas 
  minőségű. A lényeget pontosan átadja.
- **5-6 pont (Átlagos)**: Használható, de vannak benne pontatlanságok vagy 
  hiányosságok. További szerkesztést igényelne.
- **3-4 pont (Gyenge)**: Jelentős hibák, hiányos, vagy félrevezető információ.
- **1-2 pont (Elfogadhatatlan)**: Teljesen hibás, irreleváns, vagy érthetetlen.

Válaszod formátuma (CSAK ez a JSON, semmi más):

{
  "scores": {
    "accuracy": <1-10>,
    "relevance": <1-10>,
    "completeness": <1-10>,
    "fluency": <1-10>,
    "helpfulness": <1-10>
  },
  "overall": <1-10>,           // súlyozott átlag: accuracy*0.3 + relevance*0.25 + completeness*0.2 + fluency*0.1 + helpfulness*0.15, kerekítve
  "winner": "A" | "B" | "tie", // ha két választ hasonlítasz össze
  "reasoning": "<2-3 mondat indoklás magyarul>",
  "issues": ["<probléma 1>", "<probléma 2>"]  // konkrét hibák listája, üres ha nincs
}
```

### 3. Output formátum — JSON séma

A judge **mindig** ezt a JSON-t adja vissza. Ha a modell más formátumban válaszol, parsolási hiba — újra kell futtatni erősebb system prompttal.

```json
{
  "scores": {
    "accuracy": 8,
    "relevance": 9,
    "completeness": 7,
    "fluency": 8,
    "helpfulness": 8
  },
  "overall": 8,
  "winner": "A",
  "reasoning": "Az A válasz pontosabb és konkrétabb példákat hoz, míg a B válasz általánosabb marad. A nyelvi minőség mindkettőnél megfelelő.",
  "issues": ["B: a második állítás történelmileg pontatlan"]
}
```

## Python hívás — teljes script

```python
#!/usr/bin/env python
# judge_score.py — LLM-as-a-Judge hívás (1-10 skála, JSON output)
# Használat: python judge_score.py --question "..." --response "..." --judge-model gemini-3-flash-preview:latest

import argparse, json, re, time
from pathlib import Path
import requests

OLLAMA_URL = "http://localhost:11434"
JUDGE_DEFAULT = "gemini-3-flash-preview:latest"
SYSTEM = ("Te egy tapasztalt magyar szövegértékelő bíró vagy. "
          "1-10 skálán pontozol, EGÉSZ számokkal, CSAK JSON-t adsz vissza.")


def build_user_prompt(question: str, response: str, response_b: str | None) -> str:
    user = (f"Feladat:\n---\n{question}\n---\n\n"
            f"A válasz (A):\n---\n{response}\n---\n")
    if response_b:
        user += f"\nB válasz (összehasonlítás):\n---\n{response_b}\n---\n"
    user += """
Értékeld 1-10 skálán: accuracy, relevance, completeness, fluency, helpfulness.
Pontszám-sávok: 9-10 kiemelkedő, 7-8 jó, 5-6 átlagos, 3-4 gyenge, 1-2 elfogadhatatlan.
Válasz CSAK JSON:
{"scores":{"accuracy":N,"relevance":N,"completeness":N,"fluency":N,"helpfulness":N},
 "overall":N,"winner":"A"|"B"|"tie","reasoning":"<2-3 mondat>","issues":["..."]}"""
    return user


def call_judge(question: str, response: str, response_b: str | None,
               judge_model: str, retries: int = 3) -> dict:
    payload = {"model": judge_model, "system": SYSTEM,
               "prompt": build_user_prompt(question, response, response_b),
               "stream": False, "format": "json",
               "options": {"temperature": 0.0, "num_predict": 800}}
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
            r.raise_for_status()
            text = r.json().get("response", "").strip()
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception as e:
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Judge {retries}x sikertelen: {last}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--question", required=True)
    p.add_argument("--response", required=True)
    p.add_argument("--response-b", default=None)
    p.add_argument("--judge-model", default=JUDGE_DEFAULT)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    result = call_judge(args.question, args.response, args.response_b, args.judge_model)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.out:
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

## Használati példák

### Egyetlen válasz értékelése

```bash
python judge_score.py \
  --question "Magyarázd el a mohácsi csata jelentőségét 3 mondatban." \
  --response "A mohácsi csata 1526-ban zajlott, ahol II. Lajos királyunk vereséget szenvedett a török haderőtől. A vereség a középkori Magyar Királyság bukásának kezdetét jelentette." \
  --judge-model gemini-3-flash-preview:latest
```

### Két válasz A/B összehasonlítása

```bash
python judge_score.py --question "Mit jelent a 'kézbe ad' kifejezés?" \
  --response "Azt jelenti, hogy valamit odaad valakinek a kezébe." \
  --response-b "Idiomatikus kifejezés: valamit formálisan vagy jelképesen átadunk, gyakran felelősséggel együtt." \
  --judge-model gemini-3-flash-preview:latest
```

### Batch feldolgozás (részlet)

```python
# batch_judge.py — JSONL-ből olvas, judge hív, kiír
import json
from pathlib import Path
from judge_score import call_judge

IN, OUT, JUDGE = Path("./results/qwen3.5-4b/hugme_results.jsonl"), \
                 Path("./results/qwen3.5-4b/hugme_judged.jsonl"), "gemini-3-flash-preview:latest"
with IN.open(encoding="utf-8") as fin, OUT.open("w", encoding="utf-8") as fout:
    for line in fin:
        item = json.loads(line)
        try:
            item["judge"] = call_judge(item["question"], item["response"], None, JUDGE)
        except Exception as e:
            item["judge"] = {"error": str(e)}
        fout.write(json.dumps(item, ensure_ascii=False) + "\n")
```

## Prompt engineering tippek (röviden)

1. **`format: "json"` (Ollama)** — kényszeríti a JSON kimenetet: `payload = {"model": ..., "format": "json"}`
2. **`temperature: 0.0`** — a bíró determinisztikus legyen
3. **Anchor-alapú rubrika** — 1-2, 3-4, 5-6, 7-8, 9-10 sávokhoz konkrét leírás
4. **Súlyozott `overall`** — accuracy×0.30 + relevance×0.25 + completeness×0.20 + helpfulness×0.15 + fluency×0.10
5. **Position bias** — A/B tesztnél az első választ preferálja; megoldás: futtasd (A,B) és (B,A) irányban, átlagold
6. **Self-judging tilos** — a bíró SOHA ne legyen ugyanaz a modell, mint az értékelt
7. **System prompt fallback** — régi Ollama: `full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{user_prompt}"`

## Gyakori hibák

| Tünet | Megoldás |
|-------|----------|
| Judge szöveget ad JSON helyett | `format: "json"` + "CSAK JSON" a promptban |
| Minden score 7 (lapos) | Adj 2-3 példát minden sávhoz |
| A mindig nyer B-vel szemben | Futtasd (A,B) és (B,A) irányban, átlagolj |
| Self-bias | Másik modellcsaládot bíróul |
| Timeout | `num_predict=500`, `timeout=120`, retry backoff |

## Ellenőrző lista (minden judge hívás előtt)

- [ ] Van-e konkrét, anchor-alapú rubrika (1-2, 3-4, ..., 9-10)
- [ ] A prompt tartalmazza-e a "CSAK JSON" utasítást
- [ ] `format: "json"` be van-e állítva az Ollama hívásban
- [ ] A `temperature=0.0` a judge-nál
- [ ] A bíró modell MÁS, mint az értékelt modell
- [ ] Van-e retry logika JSON parsolási hiba esetére
- [ ] A position bias ellen van-e swap-and-average stratégia

## Kapcsolódó

- [Runbook: Környezet](setup-kornyezet.md) — `deepeval` telepítés
- [Runbook: HuLU](run-hulu-modell-x.md) — statisztikai benchmark (itt nincs judge)
- [Runbook: Aggregáció](aggregate-results.md) — judge eredmények pandas-aggregációja
- [Overview](../overview.md)
- [SCHEMA](../SCHEMA.md)
