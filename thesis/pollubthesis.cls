%% pollubthesis.cls — praca dyplomowa, Politechnika Lubelska, Wydział Elektrotechniki i Informatyki
%%
%% Formatowanie zgodne z „Zasadami prowadzenia prac dyplomowych i dyplomowania na WEiI” (2025),
%% Załącznik nr 7 „Wytyczne przygotowania pracy dyplomowej” (dalej: Wytyczne):
%%   A4, Times 12 pt, interlinia 1,5, tekst wyjustowany, wcięcie akapitu 0,85 cm (Wytyczne 2.1–2.3),
%%   marginesy lustrzane: wewn. 3,5 cm, zewn. 2 cm, góra 2,5 cm, dół 2 cm (2.2),
%%   nagłówki „1.” 14 pt pogrubiony / „1.1.” 12 pt pogrubiony / „1.1.1.” 12 pt kursywa (2.3),
%%   rysunki, tabele i wzory numerowane w obrębie rozdziału: „Rys. 2.1.”, „Tabela 2.1.”, „(2.1)” (2.4–2.6),
%%   podpis rysunku pod nim, podpis tabeli nad nią, 10 pt; tabele 11 pt (2.4–2.5),
%%   bibliografia APA 7 uporządkowana alfabetycznie, w tekście odwołania numeryczne [2, 4, 5] (2.7),
%%   numer strony na środku stopki, bez numeru na stronie tytułowej (3.2).
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
% Wytyczne 2.2: wewnętrzny (z oprawą) 3,5 cm, zewnętrzny 2 cm, górny 2,5 cm, dolny 2 cm.
% Numer strony w stopce, 1 cm nad dolną krawędzią tekstu.
\RequirePackage[a4paper,
  top=2.5cm, bottom=2cm,
  inner=3.5cm, outer=2cm,        % przy opcji oneside: inner = lewy, outer = prawy
  footskip=1cm]{geometry}
\RequirePackage{emptypage}       % strony wstawiane przez \cleardoublepage bez numeru
\raggedbottom
\RequirePackage[bottom]{footmisc} % przypisy zawsze na dole strony (mimo \raggedbottom)

% ---------------------------------------------------------------------------
% Akapit i interlinia
% ---------------------------------------------------------------------------
% Wytyczne 2.1 i 2.3: interlinia 1,5, akapit sygnalizowany tylko wcięciem (np. 0,85 cm), bez odstępów.
% Word „1,5 wiersza” dla Times 12 pt = 20,7 pt między liniami (12 × 1,15 × 1,5).
% Uwaga: punkt Worda to 1/72 cala (w LaTeX-u „bp”), a „pt” LaTeX-a to 1/72,27 cala.
% 20,7 bp = 20,778 pt; LaTeX dla 12 pt ma 14,5 pt, stąd współczynnik 20,778 / 14,5 = 1,4329.
\RequirePackage{setspace}
\newcommand*{\pollub@stretch}{1.4329}
\setstretch{\pollub@stretch}
\setlength{\parindent}{0.85cm}
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
% Nagłówki rozdziałów (Wytyczne 2.1, 2.3)
% ---------------------------------------------------------------------------
% Rozdział 14 pt pogrubiony, podrozdział 12 pt pogrubiony, punkt 12 pt kursywa; kropka po numerze,
% bez kropki po tytule; rozdział od nowej strony. Dalszy podział Wytyczne uznają za niewskazany.
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

% Rozdział: 14 pt, pogrubiony, zawsze od nowej strony.
\titleformat{\chapter}[hang]
  {\normalfont\fontsize{14}{17}\selectfont\bfseries}
  {\pollub@numer{0.75cm}{\thechapter.}}{0pt}{}[\global\pollub@ostatniepo=18pt]
\titleformat{name=\chapter,numberless}[hang]
  {\normalfont\fontsize{14}{17}\selectfont\bfseries}{}{0pt}{}[\global\pollub@ostatniepo=18pt]
\titlespacing{\chapter}{0pt}{-24pt}{18pt}  % ujemne „przed”: tytuł przy górnym marginesie

% Podrozdział: 12 pt, pogrubiony.
\titleformat{\section}[hang]
  {\normalfont\normalsize\bfseries}
  {\pollub@numer{1cm}{\thesection.}}{0pt}{}[\global\pollub@ostatniepo=6pt]
\titlespacing{\section}{0pt}{18pt}{6pt}

% Punkt: 12 pt, kursywa.
\titleformat{\subsection}[hang]
  {\normalfont\normalsize\itshape}
  {\pollub@numer{1.25cm}{\thesubsection.}}{0pt}{}[\global\pollub@ostatniepo=6pt]
\titlespacing{\subsection}{0pt}{12pt}{6pt}

% Czwarty poziom (\subsubsection): nienumerowany, poza spisem treści — Wytyczne go odradzają.
\titleformat{\subsubsection}[hang]
  {\normalfont\normalsize\itshape}{}{0pt}{}[\global\pollub@ostatniepo=6pt]
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
% Podpisy i numeracja rysunków, tabel, wzorów i listingów (Wytyczne 2.4–2.6)
% ---------------------------------------------------------------------------
% „Rys. 2.1. Tytuł” pod rysunkiem, „Tabela 2.1. Tytuł” nad tabelą; czcionka tekstu, 10 pt (o 2 pt
% mniejsza od tekstu), wyśrodkowane, bez kropki na końcu (nie stawiaj jej w \caption{…}).
% Wykresy to też rysunki — wstawiaj je w figure.
\RequirePackage{caption}
\DeclareCaptionFont{pollubpodpis}{\fontsize{10}{12}\selectfont}
% singlespacing musi być przed rozmiarem — inaczej przywraca 12 pt
\captionsetup{font={singlespacing,pollubpodpis}, labelsep=period,
  justification=centering, skip=6pt}
\captionsetup[table]{position=top}   % \caption{…} wpisuj PRZED tabular
\addto\captionspolish{%
  \renewcommand{\figurename}{Rys.}%
  \renewcommand{\tablename}{Tabela}}
% Numeracja w obrębie rozdziału (2.1, 2.2, …) — domyślna w klasie report, tu tylko dla jasności.
\counterwithin{figure}{chapter}
\counterwithin{table}{chapter}
\counterwithin{equation}{chapter}

% Tabele: zalecana czcionka 11 pt, pojedyncza interlinia w komórkach (jak w przykładzie z Wytycznych).
% (Ustawiane po \@floatboxreset, bo ten wywołuje \normalsize.)
\def\pollub@table{table}
\g@addto@macro\@floatboxreset{%
  \ifx\@captype\pollub@table
    \fontsize{11}{13.2}\selectfont
  \fi}

% Odstępy: 6 pt przed i za podpisem (Wytyczne 2.4), obiekt oddzielony od tekstu jednym wierszem.
\setlength{\intextsep}{6pt}
\setlength{\textfloatsep}{12pt}
\setlength{\floatsep}{12pt}

% Wzory: 6 pt przed i za równaniem (Wytyczne 2.6). \normalsize ustawia te odstępy od nowa, więc
% dopisujemy je do niego.
\g@addto@macro\normalsize{%
  \setlength{\abovedisplayskip}{6pt}%
  \setlength{\belowdisplayskip}{6pt}%
  \setlength{\abovedisplayshortskip}{6pt}%
  \setlength{\belowdisplayshortskip}{6pt}}

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
  captionpos=b, numberbychapter=true,     % „Listing 2.1.” — jak rysunki
  literate={ą}{{\k{a}}}1 {ć}{{\'c}}1 {ę}{{\k{e}}}1 {ł}{{\l{}}}1 {ń}{{\'n}}1 {ó}{{\'o}}1
           {ś}{{\'s}}1 {ź}{{\'z}}1 {ż}{{\.z}}1 {Ą}{{\k{A}}}1 {Ć}{{\'C}}1 {Ę}{{\k{E}}}1
           {Ł}{{\L{}}}1 {Ń}{{\'N}}1 {Ó}{{\'O}}1 {Ś}{{\'S}}1 {Ź}{{\'Z}}1 {Ż}{{\.Z}}1,
}

% ---------------------------------------------------------------------------
% Bibliografia (Wytyczne 2.7): wpisy w stylu APA 7, uporządkowane alfabetycznie według nazwisk
% pierwszych autorów, ponumerowane; w tekście odwołania numeryczne w nawiasach kwadratowych:
% [2] lub [2, 4, 5]. Wpisy formatuje biblatex-apa, polskie zwroty (W:, red., s., b.d., Pobrane … z:)
% są w polish-apa.lbx.
% ---------------------------------------------------------------------------
\RequirePackage{csquotes}
\RequirePackage[backend=biber, bibstyle=apa, citestyle=numeric, labelnumber,
  sortcites]{biblatex}
\renewcommand*{\bibfont}{\normalfont\raggedright}
\setlength{\bibitemsep}{0pt}
% Polskie odstępstwa od APA 7 przyjęte w Wytycznych (2.7):
% autorzy rozdzielani przecinkami („Kowalski, J., Nowak, A. B.”), redaktorzy „i” („W: J. Kowalski
% i A. B. Nowak (red.), …”); skrót „(red.)” małą literą; wydanie „wyd. 2”.
\DeclareDelimFormat[bib,biblist]{finalnamedelim}{%
  \ifcurrentname{editor}
    {\addspace\bibstring{and}\space}
    {\addcomma\addspace}}
\renewbibmacro*{apaeditorstrg}[1]{%
  \iffieldundef{#1type}
    {\ifthenelse{\value{#1}>1\OR\ifandothers{#1}}
       {\bibstring{editors}}
       {\bibstring{editor}}}
    {\ifthenelse{\value{#1}>1\OR\ifandothers{#1}}
       {\bibstring{\thefield{#1type}s}}
       {\bibstring{\thefield{#1type}}}}}
\DeclareFieldFormat{edition}{%
  \ifinteger{#1}
    {\bibstring{edition}\addnbspace#1}
    {#1\isdot}}
\DeclareFieldFormat{labelnumberwidth}{\mkbibbrackets{#1}}
% Numer „[1]” wysunięty na lewy margines listy, tekst wpisu wyrównany za numerami (jak w Wytycznych).
\defbibenvironment{bibliography}
  {\list
     {\printtext[labelnumberwidth]{%
        \printfield{labelprefix}%
        \printfield{labelnumber}}}
     {\setlength{\labelwidth}{\labelnumberwidth}%
      \setlength{\labelsep}{1em}%
      \setlength{\leftmargin}{\labelwidth}%
      \addtolength{\leftmargin}{\labelsep}%
      \setlength{\itemindent}{\z@}%
      \setlength{\itemsep}{\bibitemsep}%
      \setlength{\parsep}{\bibparsep}}%
      \renewcommand*{\makelabel}[1]{##1\hss}}
  {\endlist}
  {\item}

% ---------------------------------------------------------------------------
% Dane pracy (ustawiane w metadane.tex)
% ---------------------------------------------------------------------------
\newcommand*{\autor}[1]{\gdef\PracaAutor{#1}}
\newcommand*{\nralbumu}[1]{\gdef\PracaNrAlbumu{#1}}
\newcommand*{\rodzajpracy}[1]{\gdef\PracaRodzaj{#1}}
\newcommand*{\kierunek}[1]{\gdef\PracaKierunek{#1}}
\newcommand*{\blokdyplomowania}[1]{\gdef\PracaBlokDyplomowania{#1}}
\newcommand*{\tytul}[1]{\gdef\PracaTytul{#1}}
\newcommand*{\tytulang}[1]{\gdef\PracaTytulAng{#1}}
\newcommand*{\promotor}[1]{\gdef\PracaPromotor{#1}}
\newcommand*{\miejscowosc}[1]{\gdef\PracaMiejscowosc{#1}}
\newcommand*{\rok}[1]{\gdef\PracaRok{#1}}
\autor{Imię Nazwisko}
\nralbumu{00000}
\rodzajpracy{magisterska}
\kierunek{Informatyka}
\blokdyplomowania{}
\tytul{Tytuł pracy po polsku}
\tytulang{Thesis title in English}
\promotor{tytuł Imię Nazwisko}
\miejscowosc{Lublin}
\rok{\the\year}

% ---------------------------------------------------------------------------
% Streszczenie / Abstract — razem ze słowami kluczowymi na jednej stronie (Wytyczne 1.2 p. 1),
% poza spisem treści. Pierwsze otwiera nową stronę, kolejne dopisuje się pod poprzednim.
% ---------------------------------------------------------------------------
\newif\if@pollub@pierwszestreszczenie \@pollub@pierwszestreszczenietrue
\newenvironment{streszczenie}[1][Streszczenie]
  {\if@pollub@pierwszestreszczenie
     \clearpage\global\@pollub@pierwszestreszczeniefalse
   \else
     \par\vspace{2\baselineskip}%
   \fi
   \pdfbookmark[0]{#1}{streszczenie.#1}%
   {\centering\normalfont\fontsize{14}{17}\selectfont\bfseries#1\par}%
   \vspace{6pt}}
  {\par}
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
