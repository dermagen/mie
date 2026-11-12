#!/usr/bin/env python3
"""Убирает в уроках 4–26 только акуты, избыточные по правилу §3.3.

Действует на готовую кириллическую разметку .ie и отдельные латинские
подписи к ней; исходники не изменяет. Аффиксы и неоднозначности сохраняются.
"""
import re, sys, unicodedata
from pathlib import Path

MARKUP = re.compile(r'<[^>]*>')
SPAN = re.compile(r'(<span class="ie">)(.*?)(</span>)', re.S)
PAIR = re.compile(r'(<span class="ie">)((?:(?!</span>).)*)(</span>\s+<span class="lat">)((?:(?!</span>).)*)(</span>)', re.S)
LAT_WORD = re.compile(r'[A-Za-z\u00c0-\u024f\u02b0-\u02ff\u0300-\u036f\u1e00-\u1eff]+')
HEADING = re.compile(r'(<h([124])\b[^>]*>.*?</h\2>)', re.S)
WORD = re.compile(r'[А-Яа-яЁёѤѥӘәӁӂ\u0300-\u036f]+')
ACUTE = '\u0301'
VOWELS = set('аэиоуыяеюә')
SONORANTS = set('рлмн')


def simplify_span(content):
    # NFD makes every acute an independent character, including precomposed letters.
    text = unicodedata.normalize('NFD', content)
    plain, positions = [], []
    pos = 0
    for m in MARKUP.finditer(text):
        for i in range(pos, m.start()):
            plain.append(text[i]); positions.append(i)
        pos = m.end()
    for i in range(pos, len(text)):
        plain.append(text[i]); positions.append(i)
    plain = ''.join(plain)
    remove = []
    for match in WORD.finditer(plain):
        start, end = match.span()
        # Isolated morphemes carry their own accent, not a word-level prediction.
        if (start and plain[start - 1] in '-–—') or (end < len(plain) and plain[end] in '-–—'):
            continue
        clusters = []
        for i in range(start, end):
            char = plain[i]
            if unicodedata.combining(char) and clusters:
                clusters[-1][1].append((char, i))
            else:
                clusters.append([char.lower(), []])
        if sum(c == ACUTE for _, marks in clusters for c, _ in marks) != 1:
            continue
        nuclei, yo = [], []
        for j, (base, marks) in enumerate(clusters):
            diacritics = {c for c, _ in marks}
            is_yo = base == 'е' and '\u0308' in diacritics
            nextbase = clusters[j + 1][0] if j + 1 < len(clusters) else ''
            prevbase = clusters[j - 1][0] if j else ''
            if base in VOWELS:
                # NFD represents й as и + breve; it is not a syllable.
                if base == 'и' and '\u0306' in diacritics:
                    continue
                # Non-syllabic u as the second element of a written diphthong.
                prev_is_vowel = prevbase in VOWELS and not (prevbase == 'и' and any(c == '\u0306' for c, _ in clusters[j - 1][1]))
                if base == 'у' and prev_is_vowel and nextbase not in VOWELS and nextbase != 'и':
                    continue
                nuclei.append(j)
                if is_yo: yo.append(j)
            elif base in 'ъь' and nextbase in SONORANTS:
                nuclei.append(j)
            elif base == 'ѥ' and j == 0 and nextbase in SONORANTS:
                nuclei.append(j)
        if not nuclei or len(yo) > 1:
            continue
        predicted = yo[0] if yo else nuclei[-1] if len(nuclei) == 1 else nuclei[-2]
        marks = clusters[predicted][1]
        for char, i in marks:
            if char == ACUTE:
                remove.append(positions[i])
    if not remove:
        return content, 0
    for i in sorted(remove, reverse=True):
        text = text[:i] + text[i+1:]
    return unicodedata.normalize('NFC', text), len(remove)


def simplify_paired_latin(content):
    # Only a single parenthesised MIE word: source quotations and ambiguous
    # lists are untouched. ḱ/ǵ retain their acute: it denotes palatality.
    text = unicodedata.normalize('NFD', content)
    if not (text.startswith('(') and text.endswith(')') and LAT_WORD.fullmatch(text[1:-1])):
        return content, 0
    remove = []
    base, marks = '', []
    for i, char in enumerate(text):
        if not unicodedata.combining(char):
            base, marks = char.lower(), []
        else:
            if char == ACUTE and (base in 'aeiouə' or (base in 'rlmn' and any(x in marks for x in ('\u0323','\u0325')))):
                remove.append(i)
            marks.append(char)
    if len(remove) != 1:
        return content, 0
    i = remove[0]
    return unicodedata.normalize('NFC', text[:i] + text[i+1:]), 1


def apply(html):
    pieces = HEADING.split(html)
    active = False
    in_keys = False
    count = 0
    for i in range(0, len(pieces), 3):
        if active:
            def pair_replace(m):
                nonlocal count
                new_cyr, n = simplify_span(m.group(2))
                latin, ln = m.group(4), 0
                raw_cyr = unicodedata.normalize('NFD', MARKUP.sub('', m.group(2)))
                if n == 1 and WORD.fullmatch(raw_cyr):
                    latin, ln = simplify_paired_latin(latin)
                count += n + ln
                return m.group(1) + new_cyr + m.group(3) + latin + m.group(5)
            pieces[i] = PAIR.sub(pair_replace, pieces[i])
            def replace(m):
                nonlocal count
                new, n = simplify_span(m.group(2))
                count += n
                return m.group(1) + new + m.group(3)
            pieces[i] = SPAN.sub(replace, pieces[i])
        if i + 2 < len(pieces):
            heading, level = pieces[i+1], pieces[i+2]
            if level == '1':
                active = False
                in_keys = False
            elif level == '2':
                in_keys = 'Приложение Б' in heading
                lesson = re.search(r'Урок\s+(\d+)', heading)
                active = bool(lesson and 4 <= int(lesson.group(1)) <= 26)
            elif level == '4' and in_keys:
                lesson = re.search(r'Урок\s+(\d+)', heading)
                active = bool(lesson and 4 <= int(lesson.group(1)) <= 26)
    return ''.join(pieces[i] + (pieces[i+1] if i+1 < len(pieces) else '') for i in range(0,len(pieces),3)), count

if __name__ == '__main__':
    path = Path(sys.argv[1])
    content, count = apply(path.read_text(encoding='utf-8'))
    path.write_text(content, encoding='utf-8')
    print(f'Показ по §3.3: убрано {count} избыточных акутов в уроках 4–26 и их ключах.')
