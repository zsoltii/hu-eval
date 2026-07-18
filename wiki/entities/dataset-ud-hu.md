# UD Hungarian Treebank (Szeged)

*Típus:* entity
*Forrás(ok):* Universal Dependencies Project, Szeged Treebank 2.0
*Létrehozva:* 2026-06-06
*Frissítve:* 2026-06-06

---

## Azonosítás

- **Teljes név:** UD Hungarian (Szeged) Treebank
- **Rövidítés:** hu_szeged (UD kód), UD-HU (a projektünkben)
- **Verzió:** UD v2.13 (2024-es release)
- **Megjelenés:** 2017-től folyamatosan karbantartva, 2.13 a legfrissebb stabil verzió
- **Karbantartó:** Szegedi Tudományegyetem + Universal Dependencies Consortium

## Cél és tartalom

A UD Hungarian Treebank egy **nyelvészeti, morfológiai és szintaktikai annotált korpusz**, ami a magyar nyelv mondatszerkezeti tulajdonságait dokumentálja. A projektünkben a **nyelvészeti mélytesztek** (lásd: [Nyelvészeti benchmark](../concepts/nyelveszeti-osszefoglalo.md)) alapjául szolgál.

### Mit mér a UD Hungarian?

- **Mondattani elemzés (parsing):** szintaktikai fa építése magyar szövegből
- **Morfológiai egyértelműsítés:** a magyar agglutináló nyelv rengeteg ragozási formát produkál; a modell helyesen azonosítja-e a szóalakokat
- **Dependency parsing:** szavak közötti függőségi kapcsolatok azonosítása
- **Szórend:** a magyar szórend viszonylag szabad, de nem tetszőleges
- **POS-tagging:** egyes magyar szavak több szófaji kategóriába is tartozhatnak

### Korpusz forrása

A Szeged Treebank az alábbi szövegtípusokat tartalmazza:

- **Sajtószövegek** (legnagyobb rész)
- **Irodalmi szövegek** (magyar szépirodalom, publicisztika)
- **Hivatalos szövegek** (jogszabályok, szerződések)
- **Tudományos szövegek** (absztraktok, tanulmányok)
- **Beszélt nyelvi átiratok** (kisebb rész)

## Méret és felosztás

- **Train split:** ~10 800 mondat, ~204 000 token
- **Dev split:** ~1 250 mondat, ~24 000 token
- **Test split:** ~1 150 mondat, ~22 000 token
- **Összesen:** ~13 200 mondat, ~250 000 token

A UD-formátumra konvertált rész kisebb, mint a teljes Szeged Treebank (~70 000 mondat) — csak az emberileg újraannotált, UD-kompatibilis rész kerül bele.

## Formátum

A UD Hungarian **CoNLL-U** formátumban érhető el:

```
# sent_id = hu_szeged-00001
# text = A kutya ugat a kertben.
1	A	a	DET	_	Definite=Def|PronType=Art	2	det	_	_
2	kutya	kutya	NOUN	_	Case=Nom|Number=Sing	3	nsubj	_	_
3	ugat	ugat	VERB	_	Definite=Ind|Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	0	root	_	_
4	a	a	DET	_	Definite=Def|PronType=Art	5	det	_	_
5	kertben	kert	NOUN	_	Case=Ine|Number=Sing	3	obl	_	_
6	.	.	PUNCT	_	_	3	punct	_	_
```

### CoNLL-U mezők (10 tab-szeparált oszlop)

1. **ID** — token sorszám a mondatban
2. **FORM** — szóalak (felszíni forma)
3. **LEMMA** — lemma (töalak)
4. **UPOS** — univerzális szófaji kód
5. **XPOS** — magyar specifikus szófaji kód
6. **FEATS** — morfológiai jegyek (eset, szám, személy, stb.)
7. **HEAD** — a fej token ID-ja
8. **DEPREL** — függőségi reláció
9. **DEPS** — másodlagos függőségek
10. **MISC** — egyéb megjegyzések

## Licenc

- **Licenc típusa:** Creative Commons BY-NC-SA 4.0
- **Korlátozás:** a treebankkel fine-tune-olt modellek nem publikálhatók kereskedelmi célra
- **Kutatási használat:** szabad, a forrás megjelölésével

## Letöltés

- **Hivatalos URL:** https://universaldependencies.org/treebanks/hu_szeged/
- **GitHub tükör:** https://github.com/UniversalDependencies/UD_Hungarian-Szeged
- **Méret:** ~6.5 MB (CoNLL-U, tömörítés nélkül)

## Hivatkozás (citation)

```bibtex
@inproceedings{udhungarian,
  title={Universal Dependencies for Hungarian (Szeged Treebank)},
  author={Vincze, Veronika and {Szeged Treebank Team}},
  booktitle={Proceedings of the CoNLL Shared Task on Universal Dependencies},
  year={2017}
}

@misc{ud2024,
  title={Universal Dependencies v2.13},
  author={{Universal Dependencies Consortium}},
  year={2024},
  howpublished={\url{https://universaldependencies.org/}}
}
```

## Használat — Python loader snippet

```python
def parse_conllu(path: str):
    """CoNLL-U fájl feldolgozása: mondatok listája dict-ekben."""
    sentences = []
    current_sent = None
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# sent_id"):
                if current_sent is not None:
                    sentences.append(current_sent)
                current_sent = {"sent_id": line.split("=", 1)[1].strip(), "tokens": []}
            elif line.startswith("# text"):
                if current_sent is not None:
                    current_sent["text"] = line.split("=", 1)[1].strip()
            elif line.startswith("#"):
                continue
            elif line.strip() == "":
                if current_sent is not None and current_sent["tokens"]:
                    sentences.append(current_sent)
                    current_sent = None
            else:
                fields = line.split("\t")
                if len(fields) >= 10 and current_sent is not None:
                    current_sent["tokens"].append({
                        "id": fields[0], "form": fields[1], "lemma": fields[2],
                        "upos": fields[3], "xpos": fields[4], "feats": fields[5],
                        "head": fields[6], "deprel": fields[7],
                        "deps": fields[8], "misc": fields[9],
                    })
    if current_sent is not None and current_sent["tokens"]:
        sentences.append(current_sent)
    return sentences


if __name__ == "__main__":
    sents = parse_conllu("./hu_szeged-ud-train.conllu")
    print(f"Összesen {len(sents)} mondat betöltve.")
    if sents:
        first = sents[0]
        print(f"\n--- Első mondat (sent_id: {first['sent_id']}) ---")
        print(f"Szöveg: {first.get('text', '')}")
        for tok in first["tokens"]:
            print(f"  {tok['id']}. {tok['form']} ({tok['upos']}, lemma={tok['lemma']})")
```

## Használat a projektben — nyelvészeti mélytesztek

Három konkrét teszt alapjául szolgál (részletek: [Nyelvészeti benchmark módszertan](../concepts/nyelveszeti-osszefoglalo.md)):

1. **Morfológiai egyértelműsítés** — a modell megmondja egy szó esetét/számát/személyét
2. **Dependency parsing** (egyszerűsített) — a modell megjelöli a függőségi relációkat
3. **Szórend anomália detekció** — a modell megmondja, melyik szórend helyes

Példa prompt az (1) teszthez: "Milyen esetben van a 'kertben' szó a 'A macska a kertben játszik' mondatban? A) Alanyeset B) Beleset C) Inessivus D) Adessivus" — helyes: C.

## Kiértékelés

### Fő metrikák

- **POS-tagging accuracy** — szófaji címkék helyes aránya
- **Morphological feature accuracy (MFA)** — morfológiai jegyek helyes aránya
- **LAS (Labeled Attachment Score)** — függőségi kapcsolatok + relációk helyes aránya
- **UAS (Unlabeled Attachment Score)** — csak a kapcsolatok helyes aránya

### Baseline eredmények (magyar NLP irodalom)

| Modell | POS | MFA | UAS | LAS |
|--------|-----|-----|-----|-----|
| UDPipe (magyar spec.) | 0.97 | 0.94 | 0.88 | 0.84 |
| spaCy hu_core_news_lg | 0.96 | 0.92 | 0.85 | 0.81 |
| Magyar BERT-large (FT) | 0.97 | 0.93 | 0.86 | 0.82 |
| GPT-4 (zero-shot) | 0.82 | 0.65 | 0.55 | 0.45 |

A GPT-4 zero-shot a referencia-érték — a cél, hogy a magyar LLM-ek ezt fine-tune nélkül is megközelítsék.

## Ismert korlátok

- **NC licenc** — treebankkel fine-tune-olt modellek kereskedelmi célra nem publikálhatók
- **Sajtónyelvi dominancia** — főként sajtószövegek, nem reprezentálja a beszélt nyelvet vagy közösségi médiát
- **Korpuszméret** — ~250k token viszonylag kicsi
- **Aktuális nyelvi állapot** — 2010-es évekbeli szövegeket is tartalmaz
- **Nyelvészeti ≠ funkcionális** — a UD a nyelvészeti pontosságot méri, nem a felhasználói élményt

## Összekapcsolások

- [Nyelvészeti benchmark módszertan](../concepts/nyelveszeti-osszefoglalo.md), [Morfológiai tesztek](../concepts/morfologia-hu.md)
- [UD parser beállítás](../runbooks/setup-kornyezet.md) — a parser konfigurálása
- [HuLU](dataset-hulu.md), [MMLU-HU](dataset-mmlu-hu.md) — statisztikai benchmarkok
- [Modell entity-k](minimax-m3.md), [Qwen 3.5 397B](qwen3.5-397b.md)
