#!/usr/bin/env python3
"""Потоковый преобразователь рабочей записи курса в черновую орфографию MIE-sl.
Исходные ударения сохранены явно, без автоматического добавления. { } — жирный шрифт.
"""
import json, re, sys, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lexicon'/'course_audit')]
from working_to_miesl import parse
from explicit_stress_renderer import to_new

# Разделители остаются вне слов; буквальные знаки пунктуации сохраняются.
WORD=re.compile(r"[A-Za-zə'{}^~]+")
def word(s):
    toks,cap,notes=parse(s, preserve_boundaries=True)
    text=to_new(toks,affix=True,src=s)
    if cap and text:
        # Перед заглавной могут быть открывающие маркеры выделения.
        i=next((i for i,c in enumerate(text) if c!='|'),None)
        if i is not None:text=text[:i]+text[i].upper()+text[i+1:]
    marks=['<b>' if c=='{' else '</b>' for c in s if c in '{}']
    if text.count('|') != len(marks):raise ValueError(f'границы выделения потеряны: {s!r}')
    for mark in marks:text=text.replace('|',mark,1)
    return unicodedata.normalize('NFC',text)
def convert(s):
    return WORD.sub(lambda m:word(m.group()),s)

if __name__=='__main__':
    for line in sys.stdin:
        try: print(json.dumps({'ok':convert(json.loads(line))},ensure_ascii=True),flush=True)
        except Exception as exc: print(json.dumps({'error':str(exc)},ensure_ascii=True),flush=True)
