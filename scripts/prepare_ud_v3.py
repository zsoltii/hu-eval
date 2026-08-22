#!/usr/bin/env python
"""v4 prompt: teljes CoNLL-U formátumleírás + példa + "CSAK táblázat" utasítás."""
import json
from pathlib import Path

SRC = Path("data/ud_hungarian/ud_hungarian_std.jsonl")
DST = Path("data/ud_hungarian/ud_hungarian_v4.jsonl")

TEMPLATE = """Elemezd a következő magyar mondatot Universal Dependencies (UD) szerint.

CoNLL-U formátum: minden token egy sor, 10 tabulátorral tagolt oszlop:
ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC

Oszlopok:
- ID: tokenszám (1,2,3,…)
- FORM: szóalak a mondatban
- LEMMA: szótári alak
- UPOS: egyetemes szófaj (NOUN,VERB,ADJ,DET,ADP,ADV,PROPN,PRON,AUX,SCONJ,CCONJ,NUM,PUNCT,INTJ,PART,X)
- XPOS: nyelvspecifikus szófaj (magyarra _)
- FEATS: morfológiai jegyek (pl. Case=Nom|Number=Sing) vagy _
- HEAD: szülő token ID-je, 0 = gyökér
- DEPREL: dependencia reláció (nsubj,obj,det,amod:att,obl,advmod,root,conj,cc,punct stb.)
- DEPS: _ 
- MISC: _ 

Példa — "A macska az asztalon alszik.":
1\tA\ta\tDET\t_\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tmacska\tmacska\tNOUN\t_\tCase=Nom|Number=Sing\t5\tnsubj\t_\t_
3\taz\taz\tDET\t_\tDefinite=Def|PronType=Art\t4\tdet\t_\t_
4\tasztalon\tasztal\tNOUN\t_\tCase=Sup|Number=Sing\t5\tobl\t_\t_
5\talszik\talszik\tVERB\t_\tDefinite=Ind|Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin\t0\troot\t_\t_
6\t.\t.\tPUNCT\t_\t_\t5\tpunct\t_\t_

Mondat: {mondat}

Válasz: CSAK a CoNLL-U táblázatot add meg, semmi mást."""

items = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines()]
out = []
for item in items:
    tokens = item["tokens"]
    sentence = " ".join(t["form"] for t in tokens)
    new_item = dict(item)
    new_item["prompt"] = TEMPLATE.format(mondat=sentence)
    new_item["dataset_version"] = "v4-format-description"
    out.append(new_item)

DST.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out), encoding="utf-8")
print(f"✅ Kész: {DST} ({len(out)} mondat)")
