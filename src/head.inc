<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Современный индоевропейский язык. Вводный курс</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=PT+Sans:wght@400;700&amp;family=PT+Serif:ital,wght@0,400;0,700;1,400&amp;display=swap">
<style>
@page { size: A4; margin: 20mm 18mm 20mm 20mm; }
:root {
  --ink: #1b1b1b; --soft: #555; --rule: #9a9a9a; --ie: #13325e; --tint: #f1f3f6; --tint2: #f7f4ec;
}
html { font-size: 11pt; }
body {
  font-family: "PT Serif", "Cambria", "Times New Roman", serif;
  color: var(--ink); background: #fff; line-height: 1.45;
  max-width: 172mm; margin: 0 auto; padding: 0 4mm;
  hyphens: auto; -webkit-hyphens: auto;
}
p { margin: 0 0 0.55em 0; text-align: justify; }
h1, h2, h3, h4 { font-family: "PT Sans", "Noto Sans", "Segoe UI", Arial, sans-serif; line-height: 1.2; break-after: avoid; page-break-after: avoid; }
h1 { font-size: 22pt; margin: 0 0 0.8em 0; text-align: center; break-before: page; page-break-before: always; padding-top: 30mm; }
h1 .pn { display: block; font-size: 12pt; letter-spacing: 0.25em; text-transform: uppercase; color: var(--soft); margin-bottom: 0.6em; }
h2 { font-size: 16pt; margin: 0 0 0.6em 0; padding-bottom: 0.2em; border-bottom: 1.5px solid var(--ink); break-before: page; page-break-before: always; }
h2 .ln { display: block; font-size: 10pt; letter-spacing: 0.15em; text-transform: uppercase; color: var(--soft); font-weight: normal; }
h3 { font-size: 12.5pt; margin: 1.1em 0 0.45em 0; }
h4 { font-size: 11pt; margin: 0.9em 0 0.35em 0; }
.ie { color: var(--ie); font-family: "PT Serif", "Cambria", "Times New Roman", serif; hyphens: manual; -webkit-hyphens: manual; }
.ie b { color: #8a1c1c; font-weight: bold; }
.lat { font-style: italic; color: var(--soft); font-size: 0.92em; }
.tr { font-style: italic; }
.small { font-size: 9.5pt; color: var(--soft); }
.center { text-align: center; }

/* Титул */
.title { text-align: center; padding-top: 45mm; break-after: page; page-break-after: always; }
.title .t1 { font-family: "PT Sans", Arial, sans-serif; font-size: 28pt; font-weight: bold; margin: 0 0 0.3em 0; text-align: center; }
.title .t2 { font-size: 15pt; margin: 0 0 2.5em 0; text-align: center; }
.title .t3 { font-size: 20pt; color: var(--ie); margin: 0 0 2.5em 0; text-align: center; }
.title .t4 { font-size: 11pt; color: var(--soft); text-align: center; }

/* Оглавление */
.tocpage { break-after: page; page-break-after: always; }
.tocpage .t1 { font-family: "PT Sans", Arial, sans-serif; font-size: 18pt; margin-bottom: 1em; }
.toc { list-style: none; padding: 0; margin: 0; columns: 2; column-gap: 8mm; font-size: 10pt; }
.toc li { margin: 0 0 0.2em 0; break-inside: avoid; }
.toc li.tp { font-weight: bold; margin-top: 0.6em; }
.toc a { color: var(--ink); text-decoration: none; }

/* Таблицы */
table { border-collapse: collapse; margin: 0.6em 0 0.9em 0; font-size: 10pt; break-inside: avoid; page-break-inside: avoid; }
caption { caption-side: top; text-align: left; font-weight: bold; padding: 0 0 0.25em 0; font-size: 10.5pt; }
th, td { border: 0.6pt solid var(--rule); padding: 2.5pt 6pt; vertical-align: top; text-align: left; }
thead th { background: var(--tint); font-family: "PT Sans", Arial, sans-serif; font-size: 9.5pt; }
tbody th { font-weight: normal; font-family: "PT Sans", Arial, sans-serif; font-size: 9.5pt; background: #fafafa; white-space: nowrap; }
table.wide { width: 100%; }
table.par td { min-width: 28mm; }
table.verb td { min-width: 22mm; }
table.vocab { width: 100%; }
table.vocab td:first-child { width: 34%; }
table.vocab td:last-child { width: 30%; color: var(--soft); font-size: 9.5pt; }
table.letters td, table.letters th { text-align: center; }

/* Блоки */
.rule, .note, .culture, .ex {
  padding: 0.5em 0.8em; margin: 0.8em 0; break-inside: avoid; page-break-inside: avoid;
}
.rule { border-left: 3pt solid var(--ie); background: var(--tint); }
.note { border-left: 3pt solid var(--rule); background: #fafafa; font-size: 10pt; }
.culture { border: 0.6pt solid var(--rule); background: var(--tint2); font-size: 10pt; }
.rule > :last-child, .note > :last-child, .culture > :last-child, .ex > :last-child { margin-bottom: 0; }
.bt { font-family: "PT Sans", Arial, sans-serif; font-weight: bold; font-size: 9.5pt; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.3em; display: block; }
.ex { border-top: 1pt solid var(--ink); border-bottom: 1pt solid var(--ink); padding-left: 0; padding-right: 0; break-inside: auto; page-break-inside: auto; }
.ex ol { margin: 0.2em 0 0.2em 1.4em; padding: 0; }
.ex li { margin-bottom: 0.25em; }

/* Тексты для чтения */
.text { margin: 0.5em 0 0.8em 0; }
.text p { text-align: left; margin-bottom: 0.35em; }
.text p.ru { font-style: italic; color: var(--soft); margin-left: 1.2em; }
.pair { width: 100%; }
.pair td { width: 50%; font-size: 10.5pt; }
.dialog p { text-align: left; margin-bottom: 0.25em; }
ul.plain { list-style: none; padding-left: 0.6em; }
ul, ol { margin-top: 0.2em; }

/* Словарь */
.dict { font-size: 9.5pt; }
@media print { .dict { columns: 2; column-gap: 7mm; } }
.dict p { text-align: left; margin: 0 0 0.18em 0; padding-left: 1em; text-indent: -1em; break-inside: avoid; }
.dict p.dl { font-family: "PT Sans", Arial, sans-serif; font-weight: bold; font-size: 12pt; margin-top: 0.5em; text-indent: 0; padding-left: 0; break-after: avoid; }
.dict .gr { font-style: italic; color: var(--soft); }
.dict .par { color: var(--soft); font-size: 9pt; }

.keys ol { columns: 1; }
.keys p { text-align: left; }
@media screen {
  body { padding-top: 10mm; padding-bottom: 20mm; }
  h1, h2 { margin-top: 18mm; }
  h1 { padding-top: 10mm; }
}
</style>
</head>
<body>
