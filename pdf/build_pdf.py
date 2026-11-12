#!/usr/bin/env python3
"""Собрать PDF курса из актуальных исходников без обращения к сети."""
from __future__ import annotations
import argparse
import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MIE = ROOT / 'mie'
FONTS = HERE / 'fonts'


def face(family: str, file: Path, weight: int, style: str) -> str:
    return (f'@font-face {{ font-family: "{family}"; src: url("{file.resolve().as_uri()}"); '
            f'font-style: {style}; font-weight: {weight}; }}\n')


def font_css() -> str:
    css = ''
    styles = [('Regular', 400, 'normal'), ('Italic', 400, 'italic'),
              ('Bold', 700, 'normal'), ('BoldItalic', 700, 'italic')]
    for family in ('Tinos', 'Arimo'):
        for suffix, weight, style in styles:
            path = FONTS / 'fallback' / f'{family}-{suffix}.ttf'
            if not path.is_file():
                raise FileNotFoundError(f'Нет шрифта {path}')
            css += face(family, path, weight, style)
    # Не включаем проприетарные файлы в комплект: пользователь может положить
    # свои лицензионные файлы или установить шрифты в системе.
    microsoft = {
        'Cambria': [('cambria.ttc', 400, 'normal'), ('cambria.ttf', 400, 'normal'),
                    ('cambriai.ttf', 400, 'italic'), ('cambriab.ttf', 700, 'normal'),
                    ('cambriaz.ttf', 700, 'italic')],
        'Calibri': [('calibri.ttf', 400, 'normal'), ('calibrii.ttf', 400, 'italic'),
                    ('calibrib.ttf', 700, 'normal'), ('calibriz.ttf', 700, 'italic')],
    }
    for family, files in microsoft.items():
        regular_used = False
        for name, weight, style in files:
            p = FONTS / 'microsoft' / name
            if p.exists():
                if family == 'Cambria' and weight == 400 and style == 'normal':
                    if regular_used:
                        continue
                    regular_used = True
                css += face(family, p, weight, style)
    return css


def rebuild_html() -> None:
    print('Сборка HTML из mie/src…', flush=True)
    subprocess.run(['perl', 'src/build.pl'], cwd=MIE, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html-only', action='store_true',
                        help='не пересобирать HTML; использовать текущий готовый файл')
    parser.add_argument('--input', type=Path, help='использовать указанный HTML без пересборки')
    parser.add_argument('--output', type=Path, default=HERE / 'MIE-kurs.pdf',
                        help='путь к результату (по умолчанию pdf/MIE-kurs.pdf)')
    args = parser.parse_args()
    try:
        from weasyprint import HTML, CSS, default_url_fetcher
        from weasyprint.text.fonts import FontConfiguration
        from pypdf import PdfReader
    except ImportError as e:
        parser.exit(2, f'Не установлены зависимости: {e}. См. pdf/README.md.\n')
    if args.input:
        source = args.input.resolve()
    elif (MIE / 'src' / 'build.pl').is_file():
        if not args.html_only:
            rebuild_html()
        source = MIE / 'MIE-kurs.html'
    else:
        source = HERE / 'MIE-kurs.html'
        print('Исходники проекта не найдены: используется HTML из папки pdf.', flush=True)
    html = source.read_text(encoding='utf-8')
    # Шрифты подключаются только из локальных файлов/системы: внешние ссылки
    # Google Fonts убираем, внутренние ссылки документа не трогаем.
    html = re.sub(r'<link\b[^>]*href=["\']https://fonts\.(?:googleapis|gstatic)\.com[^"\']*["\'][^>]*>\s*', '', html, flags=re.I)
    def local_fetcher(url, *a, **kw):
        if urlparse(url).scheme not in ('file', 'data'):
            raise ValueError(f'Внешние ресурсы при PDF-сборке отключены: {url}')
        return default_url_fetcher(url, *a, **kw)
    # WeasyPrint не поддерживает margin-inline/max-content в CSS содержания.
    # Явные печатные размеры сохраняют две выровненные по верху колонки.
    print_css = """<style media="print">
      .course-toc .toc-columns { width: 150mm; margin: 0 auto; grid-template-columns: 1fr 1fr; }
      .ex li:nth-last-child(2) { break-after: avoid; page-break-after: avoid; }
    </style>"""
    html = html.replace('</head>', print_css + '</head>', 1)
    config = FontConfiguration()
    stylesheet = CSS(string=font_css(), font_config=config, url_fetcher=local_fetcher)
    target = args.output.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f'Формирование {target}…', flush=True)
    with tempfile.TemporaryDirectory(dir=target.parent, prefix='.pdf-build-') as tmp:
        intermediate = Path(tmp) / 'course.pdf'
        HTML(string=html, base_url=source.parent.as_uri() + '/', url_fetcher=local_fetcher).write_pdf(
            intermediate, stylesheets=[stylesheet], font_config=config)
        reader = PdfReader(str(intermediate))
        links = 0
        for page in reader.pages:
            for ref in page.get('/Annots', []):
                obj = ref.get_object()
                if obj.get('/Subtype') == '/Link':
                    action = obj.get('/A')
                    if obj.get('/Dest') or (action and action.get_object().get('/S') == '/GoTo'):
                        links += 1
        if not reader.pages or not links:
            raise RuntimeError('В PDF нет страниц или внутренних ссылок: готовый файл не заменён.')
        intermediate.replace(target)
    print(f'Готово: {len(reader.pages)} страниц, внутренних ссылок: {links}.', flush=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    main()
