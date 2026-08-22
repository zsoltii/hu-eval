# UD Hungarian — Javasolt prompt CoNLL-U formátumleírással

*Típus:* prompt-terv
*Forrás:* hu-eval projekt, 64K kontextus teszt tapasztalatai
*Létrehozva:* 2026-07-25

## Kontextus

A Qwen3-Next-80B IQ3_XXS 16K kontextus + 4096 max_tokens mellett nem produkált valid
CoNLL-U kimenetet. 64K kontextus + max_tokens limit nélkül már működött, de a kimenet
gyakran 7 oszlopos (a jelenlegi prompt kérése) a 10 oszlopos CoNLL-U szabvány helyett,
és néha hiányos. Az alábbi prompt **formátumleírást + példamondatot** tartalmaz,
amivel a modell megbízhatóbban ad 10 oszlopos CoNLL-U kimenetet.

## Prompt

```
Elemezd a következő magyar mondatot a Universal Dependencies (UD) szerint.

FIGYELEM: Lehet, hogy nem ismered a CoNLL-U formátumot. Olvasd el figyelmesen az alábbi leírást.

A CoNLL-U formátum 10 tabulátorral tagolt oszlopot jelent soronként.
Minden token egy sort kap. Az oszlopok:

  1. ID     — Tokenszám (1, 2, 3, ...)
  2. FORM   — A token szóalakja (eredeti, ahogy a mondatban szerepel)
  3. LEMMA  — A token szótári alakja (szótő)
  4. UPOS   — Egyetemes szófaji kód (pl. NOUN, VERB, ADJ, DET, ADP, ADV, PROPN,
              PRON, AUX, SCONJ, CCONJ, NUM, PUNCT, INTJ, PART, X)
  5. XPOS   — Nyelvspecifikus szófaj (magyarra gyakran _ vagy üres)
  6. FEATS  — Morfológiai jegyek, vesszővel elválasztva, pl.:
              Case=Nom|Number=Plur | Degree=Pos | Tense=Past|Person=3
              Ha nincs ilyen, _ (aláhúzás).
  7. HEAD   — A fej token ID-ja (a szintaktikai szülő). 0 ha a mondat gyökere.
  8. DEPREL — A dependencia reláció típusa (pl. nsubj, obj, det, amod:att,
              obl, advmod, root, conj, cc, punct, stb.)
  9. DEPS   — Enhanced dependencia (magyarra általában _ )
 10. MISC   — Egyéb megjegyzések (magyarra általában _ )

PÉLDA — egy egyszerű magyar mondat helyes CoNLL-U elemzése:

Mondat: A macska az asztalon alszik.

Helyes CoNLL-U:
1	A	a	DET	_	Definite=Def|PronType=Art	2	det	_	_
2	macska	macska	NOUN	_	Case=Nom|Number=Sing	5	nsubj	_	_
3	az	az	DET	_	Definite=Def|PronType=Art	4	det	_	_
4	asztalon	asztal	NOUN	_	Case=Sup|Number=Sing	5	obl	_	_
5	alszik	alszik	VERB	_	Definite=Ind|Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	0	root	_	_
6	.	.	PUNCT	_	_	5	punct	_	_

MOST ELEMEZD AZ ALÁBBI MONDATOT:

Mondat: {mondat}

Válasz CSAK a CoNLL-U táblázatot add meg, minden token egy sorban,
10 oszlop, tabulátorral tagolva. Ne írj semmit a táblázat elé vagy után.
```

## Megjegyzések

- A példamondat (`A macska az asztalon alszik.`) szándékosan egyszerű és egyértelmű.
- A FEATS oszlopban a magyar specifikus jegyeket (Number, Case, Person, stb.) a példából
  is tanulhatja a modell.
- A DEPREL oszlopban a legfontosabb relációk: `nsubj`, `obj`, `det`, `amod:att`, `obl`,
  `advmod`, `root`, `conj`, `cc`, `punct`, `advmod:mode`, `nmod:att`, stb.
- A `FIGYELEM` rész segít, hogy a modell ne ugorja át a formátumleírást.
- A `CSA a CoNLL-U táblázatot add meg` kérés a CoT zaj kiszűrésére szolgál.
