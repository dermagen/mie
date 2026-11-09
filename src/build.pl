#!/usr/bin/perl
# Сборка курса MIE: src/*.html (+ dict.txt) -> MIE-kurs.html
#
# Разметка в исходниках (латинская «рабочая» запись MIE):
#   [[...]]   -> кириллица MIE           <span class="ie">...</span>
#   [=...=]   -> кириллица + латиница    <span class="ie">...</span> <span class="lat">(...)</span>
#   [%...%]   -> только латиница MIE     <span class="lat">...</span>
#   внутри:  {...} — жирное (флексия), ^ — заглавная буква следующего звука
#
# Рабочая запись: a e i o u; долгота — удвоение (aa, ee ...); ударение — апостроф
# после гласной (bhe'roo, pate'er); R L M N — слоговые ṛ ḷ ṃ ṇ; K G Gh — ḱ ǵ ǵʰ;
# kw gw gwh — лабиовелярные; bh dh gh — придыхательные; y — [j]; w — [w]; h — гортанный.
# Неслоговое i после гласной (oi, ei, ai) пишется как й автоматически.
#
# Макросы таблиц:  @@noun|o|stem|подпись@@  (o, on, a, i, u)
#                  @@verb|pres|stem|подпись@@ (pres, mood, mid)

use strict; use warnings; use utf8;
use open qw(:std :encoding(UTF-8));
use Unicode::Normalize qw(NFC);
use File::Basename qw(dirname);

my $ACC = "\x{301}";
my %CV  = (a=>'а', e=>'э', i=>'и', o=>'о', u=>'у');
my %YV  = (a=>'я', e=>'е', o=>'ё', u=>'ю', i=>'йи');
my %LMAC= (a=>'ā', e=>'ē', i=>'ī', o=>'ō', u=>'ū');
my %SON = (R=>['ъ','р','ṛ'], L=>['ъ','л','ḷ'], M=>['ъ','м','ṃ'], N=>['ь','н','ṇ']);
my @CONS = (
  ['gwh','гвх','gʷh'], ['kw','кв','kʷ'], ['gw','гв','gʷ'],
  ['bh','бх','bh'], ['dh','дх','dh'], ['gh','гх','gh'], ['Gh','ж','ǵh'],
  ['K','ц','ḱ'], ['G','з','ǵ'],
  ['p','п','p'], ['b','б','b'], ['t','т','t'], ['d','д','d'], ['k','к','k'], ['g','г','g'],
  ['s','с','s'], ['h','х','h'], ['m','м','m'], ['n','н','n'], ['r','р','r'], ['l','л','l'],
  ['w','в','w'], ['f','ф','f'],
);

sub tokenize {
  my ($s) = @_;
  my @t; my $i = 0; my $n = length $s;
  while ($i < $n) {
    my $c = substr($s, $i, 1);
    if ($c eq '{') { push @t, {t=>'M', v=>'<b>'};  $i++; next }
    if ($c eq '}') { push @t, {t=>'M', v=>'</b>'}; $i++; next }
    if ($c eq '^') { push @t, {t=>'CAP'}; $i++; next }
    if ($c =~ /[aeiou]/) {
      my $k = {t=>'V', v=>$c, long=>0, st=>0}; $i++;
      if ($i < $n && substr($s,$i,1) eq "'") { $k->{st} = 1; $i++ }
      if ($i < $n && substr($s,$i,1) eq $c) {
        $k->{long} = 1; $i++;
        if ($i < $n && substr($s,$i,1) eq "'") { $k->{st} = 1; $i++ }
      }
      push @t, $k; next;
    }
    if ($c =~ /[RLMN]/) {
      my $k = {t=>'S', v=>$c, st=>0}; $i++;
      if ($i < $n && substr($s,$i,1) eq "'") { $k->{st} = 1; $i++ }
      push @t, $k; next;
    }
    if ($c eq 'y') { push @t, {t=>'Y'}; $i++; next }
    my $hit = 0;
    for my $cc (@CONS) {
      my $L = length $cc->[0];
      if (substr($s, $i, $L) eq $cc->[0]) {
        push @t, {t=>'C', v=>$cc->[0], c=>$cc->[1], l=>$cc->[2]}; $i += $L; $hit = 1; last;
      }
    }
    next if $hit;
    push @t, {t=>'O', v=>$c}; $i++;
  }
  # неслоговые i, u (второй элемент дифтонга); ударение, поставленное после
  # дифтонга (oi', au'), переносится на его первый элемент
  for my $k (0..$#t) {
    my $x = $t[$k];
    next unless $x->{t} eq 'V' && ($x->{v} eq 'i' || $x->{v} eq 'u') && !$x->{long};
    my $p = nb(\@t, $k, -1); my $q = nb(\@t, $k, 1);
    next unless defined $p && $t[$p]{t} eq 'V' && !$t[$p]{glide} && $t[$p]{v} ne $x->{v}
             && !(defined $q && ($t[$q]{t} eq 'V' || $t[$q]{t} eq 'Y'));
    $x->{glide} = 1 if $x->{v} eq 'i';
    if ($x->{st}) { $x->{st} = 0; $t[$p]{st} = 1 }
  }
  return @t;
}
# ближайший соседний токен, пропуская разметку
sub nb {
  my ($t, $k, $d) = @_;
  my $j = $k + $d;
  while ($j >= 0 && $j <= $#$t) { return $j unless $t->[$j]{t} eq 'M'; $j += $d }
  return undef;
}

sub cyr {
  my @t = tokenize($_[0]);
  my $out = ''; my $cap = 0; my %used;
  my $emit = sub { my $s = shift; if ($cap) { $s = ucfirst $s; $cap = 0 } $out .= $s };
  my $marks = sub { my ($a, $b) = @_; for my $m ($a+1 .. $b-1) { if ($t[$m]{t} eq 'M') { $out .= $t[$m]{v}; $used{$m} = 1 } } };
  for my $k (0..$#t) {
    next if $used{$k};
    my $x = $t[$k];
    if    ($x->{t} eq 'M')   { $out .= $x->{v} }
    elsif ($x->{t} eq 'CAP') { $cap = 1 }
    elsif ($x->{t} eq 'O')   { $out .= $x->{v} }
    elsif ($x->{t} eq 'C') {
      my $j = nb(\@t, $k, 1);
      if ($x->{v} eq 's' && defined $j && $t[$j]{t} eq 'C' && $t[$j]{v} eq 't') {
        my $j2 = nb(\@t, $j, 1);
        if (defined $j2 && $t[$j2]{t} eq 'Y') { $marks->($k, $j2); $emit->('щ'); $used{$j} = $used{$j2} = 1; next }
      }
      if (($x->{v} eq 't' || $x->{v} eq 'k') && defined $j && $t[$j]{t} eq 'Y') {
        $marks->($k, $j); $emit->($x->{v} eq 't' ? 'ч' : 'ш'); $used{$j} = 1; next;
      }
      $emit->($x->{c});
    }
    elsif ($x->{t} eq 'Y') {
      my $j = nb(\@t, $k, 1);
      if (defined $j && $t[$j]{t} eq 'V' && !$t[$j]{glide}) {
        my $v = $t[$j];
        $marks->($k, $j);
        my $s = $YV{$v->{v}};
        $s .= $ACC if $v->{st};
        $s .= ($v->{v} eq 'e' ? 'е' : $CV{$v->{v}}) if $v->{long};   # yē = ее (по введению)
        $emit->($s); $used{$j} = 1;
      } else { $emit->('й') }
    }
    elsif ($x->{t} eq 'V') {
      if ($x->{glide}) { $emit->('й'); next }
      my $s = $CV{$x->{v}};
      $s .= $ACC if $x->{st};
      $s .= $CV{$x->{v}} if $x->{long};
      $emit->($s);
    }
    elsif ($x->{t} eq 'S') {
      my $m = $SON{$x->{v}};
      $emit->($m->[0] . ($x->{st} ? $ACC : '') . $m->[1]);
    }
  }
  return NFC($out);
}

sub lat {
  my @t = tokenize($_[0]);
  my $out = ''; my $cap = 0;
  my $emit = sub { my $s = shift; if ($cap) { $s = ucfirst $s; $cap = 0 } $out .= $s };
  for my $x (@t) {
    if    ($x->{t} eq 'M')   { $out .= $x->{v} }
    elsif ($x->{t} eq 'CAP') { $cap = 1 }
    elsif ($x->{t} eq 'O')   { $out .= $x->{v} }
    elsif ($x->{t} eq 'C')   { $emit->($x->{l}) }
    elsif ($x->{t} eq 'Y')   { $emit->('y') }
    elsif ($x->{t} eq 'V')   { $emit->(($x->{long} ? $LMAC{$x->{v}} : $x->{v}) . ($x->{st} ? $ACC : '')) }
    elsif ($x->{t} eq 'S')   { $emit->($SON{$x->{v}}[2] . ($x->{st} ? $ACC : '')) }
  }
  return NFC($out);
}

sub ie   { '<span class="ie">' . cyr($_[0]) . '</span>' }
sub iel  { '<span class="ie">' . cyr($_[0]) . '</span> <span class="lat">(' . lat($_[0]) . ')</span>' }
sub lato { '<span class="lat">' . lat($_[0]) . '</span>' }

# ---------- макросы таблиц ----------
my @CASES = ('Именительный', 'Родительный', 'Дательный', 'Винительный',
             'Творительный', 'Местный', 'Отложительный', 'Звательный');
# окончания: [ед.], [мн.] в порядке @CASES
my %NOUN = (
  o  => [[qw(os osyo ooi om oo oi ood e)],      [qw(oos oom obhos ons oois oisu obhos oos)]],
  on => [[qw(om osyo ooi om oo oi ood om)],     [qw(a oom obhos a oois oisu obhos a)]],
  a  => [[qw(aa aas aai aam aa aai aad a)],     [qw(aas aam aabhos aans aabhis aasu aabhos aas)]],
  i  => [[qw(is eis eyei im ii eei eis ei)],     [qw(eyes eyom ibhos ins ibhis isu ibhos eyes)]],
  u  => [[qw(us ous ewei um uu eeu ous ou)],    [qw(ewes ewom ubhos uns ubhis usu ubhos ewes)]],
);
sub accend { # если основа без ударения — ударение на первую гласную окончания
  my ($stem, $end) = @_;
  return $stem . '{' . $end . '}' if $stem =~ /'/;
  $end =~ s/^([^aeiou]*[aeiou])/$1'/;
  return $stem . '{' . $end . '}';
}
sub noun_table {
  my ($type, $stem, $cap) = @_;
  my $e = $NOUN{$type} or die "noun type $type";
  my $h = qq{<table class="par">\n<caption>$cap</caption>\n<thead><tr><th>Падеж</th><th>Ед. число</th><th>Мн. число</th></tr></thead>\n<tbody>\n};
  for my $i (0..7) {
    $h .= '<tr><th>' . $CASES[$i] . '</th><td>' . ie(accend($stem, $e->[0][$i])) . '</td><td>' . ie(accend($stem, $e->[1][$i])) . "</td></tr>\n";
  }
  return $h . "</tbody>\n</table>\n";
}
my @PERS = ('1 л. ед.', '2 л. ед.', '3 л. ед.', '1 л. мн.', '2 л. мн.', '3 л. мн.');
my %VERB = (
  pres => [['Настоящее', '', [qw(oo esi eti omos ete onti)]],
           ['Имперфект', 'AUG', [qw(om es et omo ete ont)]],
           ['Будущее', '', [qw(syoo syesi syeti syomos syete syonti)]]],
  mood => [['Сослагательное', '', [qw(oo eesi eeti oomos eete oonti)]],
           ['Желательное', '', [qw(oim ois oit oime oite oint)]],
           ['Повелительное', '', ['', 'e', 'etood', '', 'ete', 'ontood']]],
  mid  => [['Медиальное наст.', '', [qw(ar esor etor omesdha edhwe ontor)]],
           ['Медиальный имперф.', '', [qw(a eso eto omedha edhwe onto)]]],
);
sub verb_table {
  my ($type, $stem, $cap) = @_;
  my $cols = $VERB{$type} or die "verb type $type";
  my $h = qq{<table class="par verb">\n<caption>$cap</caption>\n<thead><tr><th>Лицо</th>};
  $h .= '<th>' . $_->[0] . '</th>' for @$cols;
  $h .= "</tr></thead>\n<tbody>\n";
  for my $p (0..5) {
    $h .= '<tr><th>' . $PERS[$p] . '</th>';
    for my $c (@$cols) {
      my $end = $c->[2][$p];
      if ($end eq '') { $h .= '<td>—</td>'; next }
      my $st = $stem;
      if ($c->[1] eq 'AUG') { (my $u = $stem) =~ s/'//g; $st = "e'$u" }
      $h .= '<td>' . ie($st . '{' . $end . '}') . '</td>';
    }
    $h .= "</tr>\n";
  }
  return $h . "</tbody>\n</table>\n";
}

# ---------- словарь ----------
my @ORDER = split //, 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя';
my %ORD; @ORD{@ORDER} = (1..@ORDER);
sub sortkey {
  my $s = lc NFC($_[0]); $s =~ s/[\x{301}\x{300}]//g; $s =~ s/^[^а-яё]+//;
  return join '', map { exists $ORD{$_} ? sprintf('%02d', $ORD{$_}) : '99' } split //, $s;
}
sub dictionary {
  my ($file) = @_;
  open my $f, '<', $file or die "$file: $!";
  my @e;
  while (<$f>) {
    chomp; s/\r//; next if /^\s*(#|$)/;
    my ($w, $g, $ru, $par) = map { s/^\s+|\s+$//gr } split /;/, $_, 4;
    push @e, {w=>$w, g=>$g, ru=>$ru, par=>$par // '', c=>cyr($w =~ s/[{}]//gr)};
  }
  my $n = @e;
  my $h = qq{<p class="small">Всего слов: $n. Порядок — по русскому алфавиту кириллической записи MIE (буква <span class="ie">э</span> стоит после <span class="ie">ь</span>). В скобках — латинская запись. Справа — родственные слова в славянских языках и латыни.</p>\n<div class="dict">\n};
  my $letter = '';
  for my $x (sort { sortkey($a->{c}) cmp sortkey($b->{c}) } @e) {
    my $l = uc substr(NFC($x->{c} =~ s/\x{301}//gr), 0, 1);
    if ($l ne $letter) { $letter = $l; $h .= qq{<p class="dl">$l</p>\n} }
    my $par = $x->{par} ne '' ? qq{ <span class="par">◊ $x->{par}</span>} : '';
    $h .= '<p class="de">' . iel($x->{w}) . qq{ <span class="gr">$x->{g}</span> $x->{ru}$par</p>\n};
  }
  $h .= "</div>\n";
  # обратный указатель
  my @r;
  for my $x (@e) {
    for my $g (split /\s*,\s*/, $x->{ru} =~ s/\([^)]*\)//gr) {
      $g =~ s/^\s+|\s+$//g; next if $g eq '' || $g =~ /^[-—]/;
      push @r, [$g, $x->{w}];
    }
  }
  my $ix = qq{<div class="dict">\n};
  $letter = '';
  my %seen;
  for my $p (sort { sortkey($a->[0]) cmp sortkey($b->[0]) or $a->[0] cmp $b->[0] } @r) {
    next if $seen{"$p->[0]|$p->[1]"}++;
    my $l = uc substr($p->[0], 0, 1);
    if ($l ne $letter && $l =~ /[А-ЯЁ]/) { $letter = $l; $ix .= qq{<p class="dl">$l</p>\n} }
    $ix .= qq{<p class="de">$p->[0] — } . ie($p->[1]) . "</p>\n";
  }
  $ix .= "</div>\n";
  return ($h, $ix);
}

# ---------- сборка ----------
if (@ARGV && $ARGV[0] eq '--test') {
  shift @ARGV; binmode STDIN, ':encoding(UTF-8)';
  my @w = @ARGV ? @ARGV : map { chomp; $_ } <STDIN>;
  printf "%-22s %-24s %s\n", $_, cyr($_), lat($_) for @w;
  exit;
}
# режим Markdown: perl build.pl --md вход.md выход.md
# ([[...]] -> кириллица, [=...=] -> кириллица (латиница), [%...%] -> латиница; {...} -> **...**)
if (@ARGV && $ARGV[0] eq '--md') {
  my ($in, $out) = @ARGV[1, 2];
  open my $f, '<', $in or die "$in: $!"; my $t = do { local $/; <$f> }; close $f;
  my $plain = sub { (my $s = shift) =~ s/[{}]//g; $s };
  $t =~ s/\[=(.+?)=\]/cyr($1) . ' (*' . lat($plain->($1)) . '*)'/ge;
  $t =~ s/\[%(.+?)%\]/'*' . lat($plain->($1)) . '*'/ge;
  $t =~ s/\[\[(.+?)\]\]/cyr($1)/ge;
  $t =~ s{</?b>}{**}g;
  die "Неразобранная разметка: $1\n" if $t =~ /(\[\[.{0,30}|\[=.{0,30}|\[%.{0,30})/;
  open my $o, '>', $out or die "$out: $!"; print $o $t; close $o;
  print "OK: $out\n"; exit;
}
my $dir = dirname(__FILE__);
my $outfile = $ARGV[0] // "$dir/../MIE-kurs.html";
opendir my $dh, $dir or die; my @parts = sort grep { /^\d\d.*\.html$/ } readdir $dh; closedir $dh;
my $body = '';
for my $p (@parts) { open my $f, '<', "$dir/$p" or die; local $/; $body .= <$f> . "\n" }

# ключи к упражнениям: <aside class="key" title="Урок N">...</aside> переносятся в приложение
my $keys = '';
$body =~ s{<aside class="key" title="([^"]*)">(.*?)</aside>}{ $keys .= qq{<h4>$1</h4>\n$2\n}; '' }gse;
$body =~ s/<!--KEYS-->/$keys/;

my ($dict, $index) = dictionary("$dir/dict.txt");
$body =~ s/<!--DICT-->/$dict/;
$body =~ s/<!--INDEX-->/$index/;

$body =~ s/\@\@noun\|(\w+)\|([^|]+)\|(.*?)\@\@/noun_table($1,$2,$3)/ge;
$body =~ s/\@\@verb\|(\w+)\|([^|]+)\|(.*?)\@\@/verb_table($1,$2,$3)/ge;
$body =~ s/\[=(.+?)=\]/iel($1)/ge;
$body =~ s/\[%(.+?)%\]/lato($1)/ge;
$body =~ s/\[\[(.+?)\]\]/ie($1)/ge;

# оглавление из заголовков
my $toc = qq{<ul class="toc">\n}; my $n = 0;
$body =~ s{<(h1|h2)( class="[^"]*")?>(.*?)</\1>}{
  my ($tag, $cls, $txt) = ($1, $2 // '', $3); $n++;
  (my $plain = $txt) =~ s{</span>}{. }g; $plain =~ s/<[^>]+>//g;
  $toc .= $tag eq 'h1' ? qq{<li class="tp"><a href="#s$n">$plain</a></li>\n} : qq{<li><a href="#s$n">$plain</a></li>\n};
  qq{<$tag$cls id="s$n">$txt</$tag>}
}ge;
$toc .= "</ul>\n";
$body =~ s/<!--TOC-->/$toc/;

die "Неразобранная разметка: $1\n" if $body =~ /(\[\[.{0,30}|\[=.{0,30}|\@\@.{0,30})/;

open my $tf, '<', "$dir/head.inc" or die; my $head = do { local $/; <$tf> };
open my $o, '>', $outfile or die;
print $o $head, $body, "</body>\n</html>\n";
print "OK: $outfile, частей: ", scalar(@parts), ", символов: ", length($head . $body), "\n";

# режим проверки: perl build.pl --test "строка"
