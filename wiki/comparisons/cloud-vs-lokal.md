# Cloud vs. Lokális — Üzemeltetési Tradeoff-k

*Típus:* comparison
*Forrás(ok):* Ollama dokumentáció, modell árlisták (Q1 2026), háztartási áramköltség HU (~40 HUF/kWh), projekt belső
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Cél

Mikor érdemes cloud (zárt API-n elérhető) modellt használni, és mikor lokális (saját gépen futó) modellt? Ez az oldal a költség, latency, privacy és minőség dimenziók mentén segít dönteni — táblázatos és döntési mátrix formátumban.

## A két üzemeltetési mód

### Cloud modellek

- API-n keresztül hívható, más üzemelteti (OpenAI, Anthropic, Google, Alibaba, DeepSeek, stb.)
- Általában a legnagyobb, legfrissebb modellek érhetők el itt
- Per-token fizetés, jellemzően USD / 1M token
- Internet-kapcsolat szükséges minden híváshoz

### Lokális modellek

- Saját hardveren fut (Ollama, llama.cpp, vLLM, stb.)
- Egyszeri hardver-befektetés + áramköltség
- Nincs internet-függőség, nincs per-hívás díj
- A modellméretet a rendelkezésre álló VRAM/RAM korlátozza

## Költség összehasonlítás (nagyságrend)

Az alábbi számok **nagyságrendi becslések**, nem pontos árak. A cél az összehasonlíthatóság, nem a könyvelés.

### Cloud költségek (USD / 1M token)

| Kategória | Tier | Hozzávetőleges ár (USD/1M tok) | Megjegyzés |
|-----------|------|-------------------------------:|------------|
| Pro / Flagship | `minimax-m3`, `deepseek-v4-pro` | 2-15 | Legjobb minőség, legdrágább |
| Flash / Mini | `gemini-3-flash-preview` | 0.1-0.5 | 5-10x olcsóbb, kisebb minőségveszteség |
| Ultra-large | `qwen3.5:cloud` | 5-30 | Csak nagyon nehéz feladatra éri meg |
| Bírószintű | `deepseek-v4-pro:cloud` (hivatalos bíró 2026-07-19 óta) | 1-5 | LLM-as-a-Judge hívásokra; a `gemini-3-flash-preview:latest` megszűnt 2026-07-14 |

### Lokális költségek

| Kompnens | Érték | Megjegyzés |
|----------|-------|------------|
| GPU beszerzés (egyszeri) | 800-3000 USD | RTX 4090 / A100 / hasonló |
| GPU élettartam | 4-5 év | Amortizáció: 200-750 USD/év |
| Fogyasztás (kontrollált) | 200-500 W | Modellmérettől és terheléstől függ |
| Fogyasztás (alapjárat) | 50-100 W | Mindig megy, ha a gép be van kapcsolva |
| Áramköltség (40 HUF/kWh) | ~50-150 USD/év | 8-24 óra/nap aktív használat |
| Memória (RAM) | 16-128 GB | Modellmérettől függően |

### Havidíra vetített költség-összehasonlítás (példa)

Tegyük fel, hogy **havi 50M tokent** dolgozunk fel (kb. 2500 oldal szöveg):

| Mód | Havidíj egyenérték |
|-----|---------------------|
| `minimax-m3:cloud` (10 USD/1M átlag) | ~500 USD/hó |
| `gemini-3-flash-preview` (0.3 USD/1M) | ~15 USD/hó |
| `qwen3.5:cloud` (20 USD/1M) | ~1000 USD/hó |
| **Lokális `qwen3.5:4b`** (amortizáció + áram) | ~50-100 USD/hó |
| **Lokális `qwen3.5:0.8b`** (kis modell, kisebb GPU) | ~30-60 USD/hó |

> Megjegyzés: a lokális költség nem függ a token-mennyiségtől (fix áram), míg a cloud lineárisan skálázódik.

## Latency összehasonlítás

### Tipikus latency értékek (nagyságrend)

| Mód | TTFT (ms) | TPOT (ms/tok) | Megjegyzés |
|-----|----------:|--------------:|------------|
| Cloud (közeli régió) | 200-800 | 20-60 | Hálózati RTT + queue + generálás |
| Cloud (távoli régió) | 500-2000 | 30-100 | Többszörös RTT |
| Lokális (GPU, kicsi modell) | 30-100 | 5-20 | Nincs hálózat, nincs queue |
| Lokális (GPU, nagy modell) | 100-500 | 20-80 | GPU compute-bound |
| Lokális (CPU only) | 500-5000 | 50-500 | Lassú, de működik |

### Mikor számít a latency?

- **Interaktív chat (1 válasz < 2 másodperc)** — lokális kicsi vagy cloud flash előnyös
- **Batch feldolgozás (1000+ prompt éjszaka)** — latency nem számít, cloud olcsóbb lehet
- **Realtime voice (TTFT < 300ms)** — lokális kicsi vagy nagyon gyors cloud szükséges

## Privacy és adatkezelés

### Cloud kockázatok

- Az adatok elhagyják a gépet → a szolgáltató látja a promptot és a választ
- Adatvédelmi szabályzatok változhatnak
- Egyes szolgáltatók (OpenAI, Anthropic) kínálnak "no-train" opciót, de ez nem garancia
- **Személyes adat, üzleti titok, orvosi/pénzügyi adat** — ne küldjük cloudba, hacsak nem muszáj

### Lokális előnyök

- Adatok soha nem hagyják el a gépet
- Nincs külső függőség, offline is működik
- Compliance (GDPR, HIPAA, stb.) egyszerűbb
- Auditálható, reprodukálható

### Döntési szempont

| Adatérzékenység | Ajánlott mód |
|------------------|--------------|
| Publikus, nem érzékeny | Cloud bármelyik |
| Belső céges, nem titkos | Cloud (no-train) vagy lokális |
| Személyes adat (PII) | Lokális vagy saját privát cloud |
| Orvosi/pénzügyi/jogi | Csak lokális, auditált környezetben |
| Államtitok, üzleti kritikus | Teljesen offline lokális |

## Minőség várakozások

### Általános szabály (2026 eleji állapot)

- **Cloud flagship** (`minimax-m3`, `deepseek-v4-pro`, `kimi-k2.6`) — a legjobb magyar minőség, de költséges
- **Cloud flash/mid** (`gemini-3-flash-preview`) — meglepően jó magyar minőség, olcsón
- **Lokális kis (0.8-2B)** — elfogadható egyszerű feladatokra, magyar morfológia gyenge
- **Lokális közepes (4-8B)** — meglepően jó magyar nyelven, sok feladatra elég
- **Lokális nagy (70B+)** — cloud szintű, ha van elég GPU

### Feladattípus szerinti várakozás

| Feladat | Lokális 0.8-4B | Cloud flash | Cloud flagship |
|---------|:--------------:|:-----------:|:--------------:|
| Egyszerű Q&A | ✅ jó | ✅ kiváló | ✅ kiváló |
| Magyar morfológia (ritka rag) | ⚠️ gyenge | ✅ jó | ✅ kiváló |
| Esszé, kreatív írás | ❌ gyenge | ✅ jó | ✅ kiváló |
| Kódolás (Python/JS) | ✅ jó (egyszerű) | ✅ jó | ✅ kiváló |
| Matematikai érvelés | ⚠️ közepes | ✅ jó | ✅ kiváló |
| Többnyelvű, ritka nyelvek | ❌ gyenge | ⚠️ közepes | ✅ jó |

## Döntési mátrix

### Mikor válassz cloud-ot?

- ✅ Magas minőség kell, és a költség nem számít
- ✅ Alkalmi, bursty terhelés (nem érdemes saját GPU-t venni)
- ✅ A feladat nem érzékeny (publikus tartalom)
- ✅ Legnagyobb kontextus kell (200k+ token)
- ✅ Nincs elég hardver a lokális futtatáshoz
- ✅ Szeretnéd a legújabb modellt kipróbálni gyorsan

### Mikor válassz lokálist?

- ✅ Privacy kritikus (személyes, orvosi, jogi adat)
- ✅ Nagy volumen, fix költségvetés (havi 50M+ token)
- ✅ Internet-hozzáférés nem megbízható
- ✅ Alacsony latency kell (real-time voice, interaktív UI)
- ✅ Van felesleges GPU-kapacitás (pl. meglévő szerver)
- ✅ Compliance / audit követelmények

### Mikor mindkettő (hybrid)?

- ✅ Egyszerű feladatok → lokális kicsi (`qwen3.5:0.8b`)
- ✅ Nehéz feladatok → cloud flagship (`minimax-m3`)
- ✅ Privacy filter előtte → ha érzékeny, lokális; ha nem, cloud

## Hybrid tervezési minta

```
Bejövő prompt
    │
    ▼
┌─────────────────┐
│ Privacy / cost  │
│   classifier    │  ← lokális `qwen3.5:0.8b` (gyors, olcsó)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
  alacsony  magas
  költség   érzékeny
    │         │
    ▼         ▼
  Cloud    Lokális
  API     nagy modell
  (best)  (qwen3.5:4b+)
```

A legtöbb production deployment így működik: 80% lokális olcsó, 20% cloud drága, ahol kell a minőség.

## Konkrét ajánlás a hu-eval projekthez

A projekt kontextusában (értékelés, riportkészítés):

- **Alapértelmezett versenyző modellek** — `minimax-m3:cloud` (kiindulási pont)
- **Lokális baseline** — `qwen3.5:4b` (a legjobb ár/teljesítmény arány lokálisan)
- **Bíró modell — `deepseek-v4-pro:cloud` (hivatalos bíró 2026-07-19 óta; a `gemini-3-flash-preview:latest` megszűnt 2026-07-14, a kimi bíró státusza törölve 2026-06-07, v1.2.4)
- **Gyors smoke test** — `deepseek-v4-pro:cloud` (olcsó, gyors, "elég jó"; a gemini-3-flash-preview megszűnt)

## Kapcsolódó

- [Modell vs. Modell](modell-vs-modell.md) — páronkénti benchmark összehasonlítás
- [Benchmark vs. Benchmark](benchmark-vs-benchmark.md) — milyen benchmarkot használjunk
- [Overview](../overview.md) — fő modellkészlet és értékelési keretrendszer
- [SCHEMA](../SCHEMA.md) — formátum
