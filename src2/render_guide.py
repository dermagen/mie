from pathlib import Path
import re
import sys
import unicodedata
from bs4 import BeautifulSoup, NavigableString
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / 'MIE-sl.md'
HTML_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'MIE-sl.html'
HEAD_PATH = ROOT / 'src/head.inc'

md_source = MD_PATH.read_text(encoding='utf-8')
head = HEAD_PATH.read_text(encoding='utf-8')
css = re.search(r'<style>(.*?)</style>', head, re.S).group(1).strip()
font_links = re.search(r'(<link rel="preconnect".*?<link rel="stylesheet"[^>]+>)', head, re.S).group(1)
renderer = MarkdownIt('commonmark', {'html': True, 'typographer': False}).enable('table')
soup = BeautifulSoup(renderer.render(md_source), 'html.parser')

# The title-page title/strapline are supplied below; remove the Markdown title block.
for heading in list(soup.find_all(['h1', 'h2'], limit=2)):
    heading.decompose()
for p in list(soup.find_all('p', recursive=False)):
    if 'Грамматическая основа' in p.get_text(' ', strip=True):
        p.decompose()
        break
first_hr = soup.find('hr')
if first_hr:
    first_hr.decompose()

# Render the opening statement of stress notation as a course-style rule panel.
first_p = soup.find('p', recursive=False)
if first_p and 'Ударение в записи MIE-sl:' in first_p.get_text(' ', strip=True):
    panel = soup.new_tag('div', attrs={'class': 'rule'})
    label = soup.new_tag('span', attrs={'class': 'bt'})
    label.string = 'Как читать эту запись'
    panel.append(label)
    first_p.strong.unwrap() if first_p.strong else None
    first_p.wrap(panel)
    first_p.insert_before(label)

# Heading anchors and course-style chapter numbers.
headings = soup.find_all(['h2', 'h3'])
used = set()
for i, h in enumerate(headings, 1):
    text = h.get_text(' ', strip=True)
    slug = re.sub(r'[^\w-]+', '-', text.lower(), flags=re.UNICODE).strip('-')
    ident = f'sec-{i}-{slug or "section"}'
    while ident in used:
        ident += '-x'
    used.add(ident)
    h['id'] = ident
    if h.name == 'h2':
        m = re.match(r'^(\d+)\.\s*(.*)$', text)
        if m:
            h.clear()
            kicker = soup.new_tag('span', attrs={'class': 'ln'})
            kicker.string = 'Раздел ' + m.group(1)
            h.append(kicker)
            h.append(NavigableString(m.group(2)))

# Apply the language-example and Latin-form conventions used in MIE-kurs.html.
for strong in list(soup.find_all('strong')):
    text = strong.get_text('', strip=True)
    has_cyr = bool(re.search(r'[А-Яа-яЁёѢѣѤѥӘәӁӂ]', text))
    distinctive = bool(re.search(r'[ёЁәӘѥѤӂӁ]', text)) or any(m in text for m in ('\u0301', '\u0304', '\u0306', '\u0323'))
    if has_cyr and (distinctive or not re.search(r'\s', text)) and not text.startswith(('Ударение', 'Зачем')):
        strong.name = 'b'
        strong.wrap(soup.new_tag('span', attrs={'class': 'ie'}))
for em in list(soup.find_all('em')):
    letters = [c for c in em.get_text('', strip=True) if c.isalpha()]
    if letters and sum('LATIN' in unicodedata.name(c, '') for c in letters) >= max(1, len(letters) * .7):
        em['class'] = list(set(em.get('class', []) + ['lat']))
    elif letters and any('CYRILLIC' in unicodedata.name(c, '') for c in letters):
        em['class'] = list(set(em.get('class', []) + ['tr']))
for table in soup.find_all('table'):
    table['class'] = list(set(table.get('class', []) + ['wide']))
    table.wrap(soup.new_tag('div', attrs={'class': 'table-wrap'}))

# Two top-aligned columns, read top to bottom. Short labels affect only the TOC;
# section headings and their anchors remain unchanged.
short_labels = [
    'Принципы транскрипции', '1.1. Гласные и долгота', '1.2. Слоговые сонанты',
    '1.3. Взрывные и придыхательные', '1.4. Лабиовелярные',
    '1.5. Перед j', '1.6. Остальные согласные', '1.7. Сжатие сочетаний',
    '1.8. Ударение', '1.9. Набор знаков',
    'Существительные и падежи', 'Волк: o-основа', 'Женщина: ā-основа',
    'Иго: средний род', 'Двойственное число', 'Местоимения',
    'Указательные местоимения', 'Вопросительные и относительные',
    'Глаголы и наклонения', '4.1. Система времён',
    '4.2. Атематические глаголы', '4.3. Глагол «нести»', '4.4. Глагол «видеть»',
    'Прилагательные', 'Новый: склонение', 'Союзы и предлоги',
    'Словообразование', '7.1. Условный корень glew-', '7.2. Глагол «светить»',
    '7.3. Нулевая ступень и суффиксы', 'Примеры текста', 'Словарик',
    'Существительные', 'Прилагательные', 'Неизменяемое слово', 'Глаголы',
    'Числительные', 'Практические упражнения', 'Обратное чтение'
]
assert len(short_labels) == len(headings)
# Balance the line counts while keeping the verbs heading with its first subsection.
split = (len(headings) + 1) // 2
toc_soup = BeautifulSoup('', 'html.parser')
toc = toc_soup.new_tag('div', attrs={'class': 'tocpage guide-toc'})
title = toc_soup.new_tag('p', attrs={'class': 't1 center'})
b = toc_soup.new_tag('b'); b.string = 'Содержание'; title.append(b); toc.append(title)
columns = toc_soup.new_tag('div', attrs={'class': 'toc-columns'})
for group in (list(zip(headings, short_labels))[:split], list(zip(headings, short_labels))[split:]):
    ul = toc_soup.new_tag('ul', attrs={'class': 'toc'})
    for h, label in group:
        li = toc_soup.new_tag('li')
        if h.name == 'h2': li['class'] = ['tp']
        a = toc_soup.new_tag('a', href='#' + h['id'])
        a.string = label
        li.append(a); ul.append(li)
    columns.append(ul)
toc.append(columns)

title_page = '''<div class="title">
<p class="t1">Современный индоевропейский язык</p>
<p class="t2">Краткое руководство по транскрипции и грамматическим формам</p>
<p class="t3"><span class="ie">MIE-sl</span></p>
<p class="t4">Славянизированная кириллическая орфография<br>лексическая основа — Большой словарь MIE; грамматический справочник — третье издание грамматики</p>
</div>'''
extra_css = '''
.guide-toc .toc-columns { display: grid; grid-template-columns: max-content max-content; width: max-content; margin-inline: auto; gap: 8mm; align-items: start; }
.guide-toc .toc { columns: auto; margin: 0; padding: 0; font-size: 9.5pt; }
.guide-toc .toc li:first-child { margin-top: 0; }
.guide-toc .toc a { white-space: nowrap; }
@media screen { .guide-toc { margin-bottom: 14mm; } }
@media screen and (max-width: 620px) { .guide-toc .toc-columns { grid-template-columns: max-content; gap: 0.5em; max-width: 100%; } }
'''
content = soup.decode_contents()
html = f'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Краткое руководство по славянизированной кириллической орфографии MIE-sl.">
<title>Краткое руководство MIE-sl — кириллическая орфография</title>
{font_links}<style>{css}\n{extra_css}</style></head><body>
{title_page}{toc}{content}</body></html>'''
HTML_PATH.write_text(html, encoding='utf-8')
check = BeautifulSoup(html, 'html.parser')
assert len(check.select('h2[id]')) == 11
assert all(check.find(id=a['href'][1:]) for a in check.select('.toc a'))
assert 'не предполагается' in check.get_text()
print(f'{HTML_PATH}: {HTML_PATH.stat().st_size} bytes; {len(check.select(".toc a"))} TOC links')
