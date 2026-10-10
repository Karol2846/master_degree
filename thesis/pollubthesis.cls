%% pollubthesis.cls — praca dyplomowa, Politechnika Lubelska, Wydział Elektrotechniki i Informatyki
%%
%% Formatowanie odwzorowane z szablonu Word (Magisterka.docx):
%%   A4, Times 12 pt, interlinia „1,5 wiersza”, tekst wyjustowany, wcięcie akapitu 1,27 cm,
%%   marginesy lustrzane (wewn. 3,5 cm, zewn. 2 cm, góra 2,5 cm), numer strony na środku stopki,
%%   numeracja rozdziałów „1.”, „1.1.”, „1.1.1.”, podpisy „Rysunek 1 …” / „Tabela 1 …” pod obiektem,
%%   bibliografia numeryczna [1], [2], … w kolejności cytowania.
%%
%% Opcje klasy:
%%   twoside (domyślnie) — druk dwustronny: marginesy lustrzane + pusta strona za stroną tytułową
%%   oneside             — druk jednostronny: lewy margines 3,5 cm na każdej stronie
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{pollubthesis}[2026/10/10 Praca dyplomowa PL WEiI]

\newif\if@pollub@twoside \@pollub@twosidetrue
\DeclareOption{oneside}{\@pollub@twosidefalse}
\DeclareOption{twoside}{\@pollub@twosidetrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessOptions\relax

\if@pollub@twoside
  \LoadClass[12pt,a4paper,twoside,openany]{report}
\else
  \LoadClass[12pt,a4paper,oneside,openany]{report}
\fi

% ---------------------------------------------------------------------------
% Język i czcionki
% ---------------------------------------------------------------------------
\RequirePackage[T1]{fontenc}
\RequirePackage[english,polish]{babel}   % ostatni język = główny
\RequirePackage{mathptmx}                % matematyka w stylu Times
\RequirePackage{tgtermes}                % tekst: TeX Gyre Termes (klon Times New Roman)
\RequirePackage{tgheros}                 % bezszeryfowa: TeX Gyre Heros (klon Arial) — strona tytułowa
\renewcommand*\ttdefault{lmtt}           % maszynowa: Latin Modern Mono — listingi kodu
\RequirePackage{microtype}
\RequirePackage{etoolbox}

% ---------------------------------------------------------------------------
% Strona
% ---------------------------------------------------------------------------
% W Wordzie: góra 2,5 cm, dół 2 cm, stopka 1,25 cm od krawędzi. Stopka ma jednak dwa akapity
% (numer strony + pusty), więc „wypycha” tekst w górę — efektywny dolny margines to ok. 2,3 cm.
% Poniższe wartości odtwarzają ten efekt: 34 wiersze na stronie i numer strony 1,83 cm nad krawędzią.
\RequirePackage[a4paper,
  top=2.5cm, bottom=2.3cm,
  inner=3.5cm, outer=2cm,        % przy opcji oneside: inner = lewy, outer = prawy
  footskip=13.4pt]{geometry}
\RequirePackage{emptypage}       % strony wstawiane przez \cleardoublepage bez numeru
\raggedbottom
\RequirePackage[bottom]{footmisc} % przypisy zawsze na dole strony (mimo \raggedbottom)

% ---------------------------------------------------------------------------
% Akapit i interlinia
% ---------------------------------------------------------------------------
% Word „1,5 wiersza” dla Times 12 pt = 20,7 pt między liniami (12 × 1,15 × 1,5).
% Uwaga: punkt Worda to 1/72 cala (w LaTeX-u „bp”), a „pt” LaTeX-a to 1/72,27 cala.
% 20,7 bp = 20,778 pt; LaTeX dla 12 pt ma 14,5 pt, stąd współczynnik 20,778 / 14,5 = 1,4329.
\RequirePackage{setspace}
\newcommand*{\pollub@stretch}{1.4329}
\setstretch{\pollub@stretch}
\setlength{\parindent}{1.27cm}
\setlength{\parskip}{0pt}
\RequirePackage{indentfirst}     % wcięcie także w pierwszym akapicie po nagłówku
\clubpenalty=10000
\widowpenalty=10000
% Bez dzielenia wyrazów — jak w oryginale (Word nie dzieli, tylko rozciąga odstępy między słowami).
% Aby włączyć dzielenie, usuń \hyphenpenalty=10000 poniżej.
\AtBeginDocument{\hyphenpenalty=10000 \emergencystretch=3em \hbadness=10000} % hbadness: bez ostrzeżeń „Underfull” o rozciągniętych odstępach

% ---------------------------------------------------------------------------
% Kolory, grafika, tabele, matematyka
% ---------------------------------------------------------------------------
\RequirePackage[table]{xcolor}
\definecolor{pollubtekst}{HTML}{231F20}   % kolor tekstu ze strony tytułowej szablonu
\definecolor{tabnaglowek}{HTML}{BFBFBF}   % tło wiersza nagłówkowego tabel
\RequirePackage{graphicx}
\graphicspath{{grafika/}}
\RequirePackage{array}
\RequirePackage{tabularx}
\RequirePackage{multirow}
\RequirePackage{float}                    % umożliwia [H] — „dokładnie tutaj”
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{siunitx}
\sisetup{output-decimal-marker={,}, group-separator={\,},  % polski przecinek dziesiętny
  mode=text}                                               % liczby czcionką tekstu (Times)

% ---------------------------------------------------------------------------
% Nagłówki rozdziałów (Nagłówek 1–3 w Wordzie)
% ---------------------------------------------------------------------------
% Odstępy wymierzone na wydruku oryginału.
\RequirePackage{titlesec}
\setcounter{secnumdepth}{2}   % numerowane: rozdział, podrozdział, punkt (1., 1.1., 1.1.1.)
\setcounter{tocdepth}{2}      % w spisie treści te same trzy poziomy

% Numer w polu o stałej szerokości (jak tabulator w Wordzie); dłuższy numer po prostu się rozsuwa.
\newsavebox{\pollub@numerbox}
\newcommand{\pollub@numer}[2]{%
  \sbox{\pollub@numerbox}{#2}%
  \ifdim\wd\pollub@numerbox<#1\relax
    \makebox[#1][l]{\usebox{\pollub@numerbox}}%
  \else
    \usebox{\pollub@numerbox}\hspace{0.5em}%
  \fi}

% Dwa nagłówki pod rząd (np. rozdział → podrozdział): jak w oryginale obowiązuje większy z odstępów
% „po” poprzednim i „przed” następnym. Każdy nagłówek zapamiętuje swój odstęp „po”, a następny
% dokłada tylko brakującą różnicę (titlesec domyślnie pomija wtedy odstęp „przed”).
\newskip\pollub@ostatniepo
\newskip\pollub@roznica
\renewcommand{\ttl@titlespace}[1]{%
  \pollub@roznica=#1\relax
  \advance\pollub@roznica-\pollub@ostatniepo
  \ifdim\pollub@roznica>\z@ \vspace{\pollub@roznica}\fi}

% Rozdział: 16 pt, pogrubiony, zawsze od nowej strony.
\titleformat{\chapter}[hang]
  {\normalfont\fontsize{16}{19}\selectfont\bfseries}
  {\pollub@numer{0.87cm}{\thechapter.}}{0pt}{}[\global\pollub@ostatniepo=15.3pt]
\titleformat{name=\chapter,numberless}[hang]
  {\normalfont\fontsize{16}{19}\selectfont\bfseries}{}{0pt}{}[\global\pollub@ostatniepo=15.3pt]
\titlespacing{\chapter}{0pt}{-24pt}{15.3pt}  % ujemne „przed”: tytuł przy górnym marginesie, jak w Wordzie

% Podrozdział: 14 pt, pogrubiony, wcięty o 0,635 cm.
\titleformat{\section}[hang]
  {\normalfont\fontsize{14}{17}\selectfont\bfseries}
  {\pollub@numer{1.27cm}{\thesection.}}{0pt}{}[\global\pollub@ostatniepo=13.8pt]
\titlespacing{\section}{0.635cm}{28.2pt}{13.8pt}

% Punkt: 12 pt, pogrubiony, wcięty o 1,27 cm.
\titleformat{\subsection}[hang]
  {\normalfont\normalsize\bfseries}
  {\pollub@numer{1.27cm}{\thesubsection.}}{0pt}{}[\global\pollub@ostatniepo=12pt]
\titlespacing{\subsection}{1.27cm}{24pt}{12pt}

% Czwarty poziom (\subsubsection): nienumerowany, poza spisem treści.
\titleformat{\subsubsection}[hang]
  {\normalfont\normalsize\bfseries\itshape}{}{0pt}{}[\global\pollub@ostatniepo=6pt]
\titlespacing{\subsubsection}{0pt}{12pt}{6pt}

% ---------------------------------------------------------------------------
% Spis treści
% ---------------------------------------------------------------------------
\RequirePackage{tocloft}
\renewcommand{\cfttoctitlefont}{\normalfont\fontsize{14}{17}\selectfont\bfseries}
\renewcommand{\cftaftertoctitle}{}
\setlength{\cftbeforetoctitleskip}{-17.7pt}  % ujemne wartości: pozycje jak w oryginale
\setlength{\cftaftertoctitleskip}{-8.6pt}
\tocloftpagestyle{empty}
% wszystkie poziomy zwykłą czcionką, z kropkami prowadzącymi i kropką po numerze
\renewcommand{\cftchapfont}{\normalfont}
\renewcommand{\cftchappagefont}{\normalfont}
\renewcommand{\cftchapleader}{\normalfont\cftdotfill{\cftdotsep}}
\renewcommand{\cftchapaftersnum}{.}
\renewcommand{\cftsecaftersnum}{.}
\renewcommand{\cftsubsecaftersnum}{.}
\renewcommand{\cftdotsep}{0.6}
\setlength{\cftchapindent}{0pt}      \setlength{\cftchapnumwidth}{24pt}
\setlength{\cftsecindent}{12pt}      \setlength{\cftsecnumwidth}{36pt}
\setlength{\cftsubsecindent}{24pt}   \setlength{\cftsubsecnumwidth}{48pt}
\setlength{\cftbeforechapskip}{6.25bp}
\setlength{\cftbeforesecskip}{6.25bp}
\setlength{\cftbeforesubsecskip}{6.25bp}

% \spistresci — spis treści bez numerów stron w stopce (jak w oryginale).
% Oryginał zawierał wpis „Spis treści” w samym spisie; usuń linię z \addcontentsline, jeśli zbędny.
\newcommand{\spistresci}{%
  \clearpage
  \pagestyle{empty}%
  \phantomsection
  \addcontentsline{toc}{chapter}{\contentsname}%
  \tableofcontents
  \clearpage
  \pagestyle{plain}}

% ---------------------------------------------------------------------------
% Podpisy rysunków, tabel, wykresów i listingów (styl „Legenda” w Wordzie)
% ---------------------------------------------------------------------------
\RequirePackage{caption}
\DeclareCaptionFont{pollubpodpis}{\fontsize{9}{11}\selectfont}
% singlespacing musi być przed rozmiarem — inaczej przywraca 12 pt
\captionsetup{font={singlespacing,pollubpodpis,bf}, labelfont=bf,
  labelsep=space,                % „Rysunek 1 Tytuł” — zmień na period, by mieć „Rysunek 1. Tytuł”
  justification=centering, skip=0.8bp}  % podpis tuż pod obiektem, jak w oryginale
% numeracja ciągła w całej pracy (Rysunek 1, 2, …), a nie 1.1, 1.2, …
\counterwithout{figure}{chapter}
\counterwithout{table}{chapter}
\counterwithout{equation}{chapter}

% Tabele: w oryginale komórki mają interlinię 1,5 jak tekst (setspace domyślnie daje 1,0 w obiektach
% pływających). Podpis i tak ma pojedynczą interlinię (singlespacing w \captionsetup).
% Wiersz tabeli ma wysokość wiersza tekstu (20,7 pt), a tekst siedzi wyżej niż w LaTeX-u (11,6 pt od
% górnej linii zamiast 14,5 pt) — jak w Wordzie.
% (Ustawiane po \@floatboxreset, bo ten wywołuje \normalsize i nadpisałby \strutbox.)
\def\pollub@table{table}
\g@addto@macro\@floatboxreset{%
  \ifx\@captype\pollub@table
    \setstretch{\pollub@stretch}%
    \setbox\strutbox\hbox{\vrule\@height 11.6bp\@depth 9.1bp\@width\z@}%
  \fi}

% Odstępy wokół rysunków/tabel/wykresów zmierzone na oryginale: tekst → obiekt 9,8 pt (od linii bazowej),
% obiekt → podpis 8,5 pt, podpis → następny wiersz tekstu 23,1 pt (od linii bazowych).
\setlength{\intextsep}{\z@}
\setlength{\textfloatsep}{7.8bp}   % obiekt na górze strony → tekst jak w akapicie (23 pt)
\setlength{\floatsep}{1bp}
\newcommand*{\pollub@nadobiektem}{\vspace*{5.8bp}}
\AtBeginEnvironment{figure}{\pollub@nadobiektem}
\AtBeginEnvironment{table}{\pollub@nadobiektem}

% Osobna numeracja wykresów („Wykres 1 …”), jak w oryginale.
\RequirePackage{newfloat}
\DeclareFloatingEnvironment[fileext=low, listname={Spis wykresów}, name=Wykres,
  placement=htbp, within=none]{wykres}
\AtBeginEnvironment{wykres}{\pollub@nadobiektem}

% ---------------------------------------------------------------------------
% Listy (punktory jak w Wordzie: • / o / ▪, punktor 0,635 cm, tekst 1,27 cm)
% ---------------------------------------------------------------------------
\RequirePackage{enumitem}
\setlist{nosep}
\setlist[itemize]{labelindent=0.635cm, labelwidth=0.635cm, labelsep=0pt, leftmargin=!, align=left}
\setlist[enumerate]{labelindent=0.635cm, labelwidth=0.635cm, labelsep=0pt, leftmargin=!, align=left}
\setlist[itemize,1]{label=\textbullet}
\setlist[itemize,2]{label=\texttt{o}}
\setlist[itemize,3]{label=\tiny$\blacksquare$}
\setlist[enumerate,1]{label=\arabic*.}
\setlist[enumerate,2]{label=\alph*)}

% ---------------------------------------------------------------------------
% Listingi kodu
% ---------------------------------------------------------------------------
\RequirePackage{listings}
\renewcommand{\lstlistingname}{Listing}
\renewcommand{\lstlistlistingname}{Spis listingów}
\lstdefinelanguage{Rust}{
  morekeywords={as,async,await,break,const,continue,crate,dyn,else,enum,extern,false,fn,for,
    if,impl,in,let,loop,match,mod,move,mut,pub,ref,return,self,Self,static,struct,super,
    trait,true,type,unsafe,use,where,while},
  morekeywords=[2]{bool,char,f32,f64,i8,i16,i32,i64,i128,isize,str,u8,u16,u32,u64,u128,
    usize,String,Vec,Option,Result,Box,Some,None,Ok,Err},
  sensitive=true,
  morecomment=[l]{//},
  morecomment=[s]{/*}{*/},
  morestring=[b]",
}
\lstset{
  basicstyle=\ttfamily\footnotesize\setstretch{1},
  keywordstyle=\bfseries,
  keywordstyle=[2]\bfseries,
  commentstyle=\itshape\color{black!60},
  numbers=left, numberstyle=\tiny\color{black!50}, numbersep=6pt,
  frame=single, rulecolor=\color{black!40},
  columns=fullflexible, keepspaces=true,
  breaklines=true, showstringspaces=false, tabsize=4,
  captionpos=b, numberbychapter=false,
  literate={ą}{{\k{a}}}1 {ć}{{\'c}}1 {ę}{{\k{e}}}1 {ł}{{\l{}}}1 {ń}{{\'n}}1 {ó}{{\'o}}1
           {ś}{{\'s}}1 {ź}{{\'z}}1 {ż}{{\.z}}1 {Ą}{{\k{A}}}1 {Ć}{{\'C}}1 {Ę}{{\k{E}}}1
           {Ł}{{\L{}}}1 {Ń}{{\'N}}1 {Ó}{{\'O}}1 {Ś}{{\'S}}1 {Ź}{{\'Z}}1 {Ż}{{\.Z}}1,
}

% ---------------------------------------------------------------------------
% Bibliografia: numeryczna [1], kolejność cytowania, wpisy do lewej, wcięte o 0,635 cm.
% Jak w oryginale: numer „[1]” w tym samym wierszu co tekst, kolejne wiersze bez wysunięcia
% (zaczynają się pod numerem, 0,635 cm od marginesu).
% ---------------------------------------------------------------------------
\RequirePackage{csquotes}
\RequirePackage[backend=biber, style=numeric-comp, sorting=none,
  giveninits=true, maxbibnames=99]{biblatex}
\renewcommand*{\bibfont}{\normalfont\raggedright}
\setlength{\bibitemsep}{0pt}
\defbibenvironment{bibliography}
  {\list
     {\printtext[labelnumberwidth]{%
        \printfield{labelprefix}%
        \printfield{labelnumber}}}
     {\setlength{\leftmargin}{0.635cm}%
      \setlength{\labelwidth}{\z@}%
      \setlength{\labelsep}{0.25em}%     % zwykła spacja po „[1]”
      \setlength{\itemindent}{\labelsep}%
      \setlength{\itemsep}{\bibitemsep}%
      \setlength{\parsep}{\bibparsep}}%
      \renewcommand*{\makelabel}[1]{##1}}
  {\endlist}
  {\item}

% ---------------------------------------------------------------------------
% Dane pracy (ustawiane w metadane.tex)
% ---------------------------------------------------------------------------
\newcommand*{\autor}[1]{\gdef\PracaAutor{#1}}
\newcommand*{\nralbumu}[1]{\gdef\PracaNrAlbumu{#1}}
\newcommand*{\rodzajpracy}[1]{\gdef\PracaRodzaj{#1}}
\newcommand*{\kierunek}[1]{\gdef\PracaKierunek{#1}}
\newcommand*{\specjalnosc}[1]{\gdef\PracaSpecjalnosc{#1}}
\newcommand*{\tytul}[1]{\gdef\PracaTytul{#1}}
\newcommand*{\tytulang}[1]{\gdef\PracaTytulAng{#1}}
\newcommand*{\promotor}[1]{\gdef\PracaPromotor{#1}}
\newcommand*{\miejscowosc}[1]{\gdef\PracaMiejscowosc{#1}}
\newcommand*{\rok}[1]{\gdef\PracaRok{#1}}
\autor{Imię Nazwisko}
\nralbumu{00000}
\rodzajpracy{magisterska}
\kierunek{Informatyka}
\specjalnosc{}
\tytul{Tytuł pracy po polsku}
\tytulang{Thesis title in English}
\promotor{tytuł Imię Nazwisko}
\miejscowosc{Lublin}
\rok{\the\year}

% ---------------------------------------------------------------------------
% Streszczenie / Abstract — każde na osobnej stronie, poza spisem treści
% ---------------------------------------------------------------------------
\newenvironment{streszczenie}[1][Streszczenie]
  {\clearpage
   \pdfbookmark[0]{#1}{streszczenie.#1}%
   {\centering\normalfont\fontsize{16}{19}\selectfont\bfseries\rule{0pt}{14.9pt}#1\par}%
   \vspace{3pt}}
  {\clearpage}
% \slowakluczowe{…} lub \slowakluczowe[Key words]{…}
\newcommand{\slowakluczowe}[2][Słowa kluczowe]{%
  \par\vspace{\baselineskip}\noindent #1: #2\par}

% ---------------------------------------------------------------------------
% Hiperłącza (ładowane na końcu)
% ---------------------------------------------------------------------------
\RequirePackage[hidelinks, bookmarksnumbered, unicode]{hyperref}
\RequirePackage{bookmark}
\urlstyle{same}
\AtBeginDocument{\hypersetup{pdftitle={\PracaTytul}, pdfauthor={\PracaAutor}}}
