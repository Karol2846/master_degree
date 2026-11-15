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

% Język i czcionki
\RequirePackage[T1]{fontenc}
\RequirePackage[english,polish]{babel}
\RequirePackage{mathptmx}
\RequirePackage{tgtermes}
\RequirePackage{tgheros}
\renewcommand*\ttdefault{lmtt}
\RequirePackage{microtype}
\RequirePackage{etoolbox}


% Strona
\RequirePackage[a4paper,
  top=2.5cm, bottom=2cm,
  inner=3.5cm, outer=2cm,
  footskip=1cm]{geometry}
\RequirePackage{emptypage}
\raggedbottom
\RequirePackage[bottom]{footmisc}


% Akapit i interlinia
\RequirePackage{setspace}
\newcommand*{\pollub@stretch}{1.4329}
\setstretch{\pollub@stretch}
\setlength{\parindent}{0.85cm}
\setlength{\parskip}{0pt}
\RequirePackage{indentfirst}
\clubpenalty=10000
\widowpenalty=10000
\AtBeginDocument{\hyphenpenalty=10000 \emergencystretch=3em \hbadness=10000}


% Kolory, grafika, tabele, matematyka-
\RequirePackage[table]{xcolor}
\definecolor{pollubtekst}{HTML}{231F20}
\definecolor{tabnaglowek}{HTML}{BFBFBF}
\RequirePackage{graphicx}
\graphicspath{{grafika/}}
\RequirePackage{array}
\RequirePackage{tabularx}
\RequirePackage{multirow}
\RequirePackage{float}                    % umożliwia [H] — „dokładnie tutaj”
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{siunitx}
\sisetup{output-decimal-marker={,}, group-separator={\,},
  mode=text}


% Nagłówki rozdziałów
\RequirePackage{titlesec}
\setcounter{secnumdepth}{2}
\setcounter{tocdepth}{2}

\newsavebox{\pollub@numerbox}
\newcommand{\pollub@numer}[2]{%
  \sbox{\pollub@numerbox}{#2}%
  \ifdim\wd\pollub@numerbox<#1\relax
    \makebox[#1][l]{\usebox{\pollub@numerbox}}%
  \else
    \usebox{\pollub@numerbox}\hspace{0.5em}%
  \fi}

\newskip\pollub@ostatniepo
\newskip\pollub@roznica
\renewcommand{\ttl@titlespace}[1]{%
  \pollub@roznica=#1\relax
  \advance\pollub@roznica-\pollub@ostatniepo
  \ifdim\pollub@roznica>\z@ \vspace{\pollub@roznica}\fi}

\titleformat{\chapter}[hang]
  {\normalfont\fontsize{14}{17}\selectfont\bfseries}
  {\pollub@numer{0.75cm}{\thechapter.}}{0pt}{}[\global\pollub@ostatniepo=18pt]
\titleformat{name=\chapter,numberless}[hang]
  {\normalfont\fontsize{14}{17}\selectfont\bfseries}{}{0pt}{}[\global\pollub@ostatniepo=18pt]
\titlespacing{\chapter}{0pt}{-24pt}{18pt}

\titleformat{\section}[hang]
  {\normalfont\normalsize\bfseries}
  {\pollub@numer{1cm}{\thesection.}}{0pt}{}[\global\pollub@ostatniepo=6pt]
\titlespacing{\section}{0pt}{18pt}{6pt}

\titleformat{\subsection}[hang]
  {\normalfont\normalsize\itshape}
  {\pollub@numer{1.25cm}{\thesubsection.}}{0pt}{}[\global\pollub@ostatniepo=6pt]
\titlespacing{\subsection}{0pt}{12pt}{6pt}

\titleformat{\subsubsection}[hang]
  {\normalfont\normalsize\itshape}{}{0pt}{}[\global\pollub@ostatniepo=6pt]
\titlespacing{\subsubsection}{0pt}{12pt}{6pt}

% Spis treści
\RequirePackage{tocloft}
\renewcommand{\cfttoctitlefont}{\normalfont\fontsize{14}{17}\selectfont\bfseries}
\renewcommand{\cftaftertoctitle}{}
\setlength{\cftbeforetoctitleskip}{-17.7pt}
\setlength{\cftaftertoctitleskip}{-8.6pt}
\tocloftpagestyle{empty}
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
\newcommand{\spistresci}{%
  \clearpage
  \pagestyle{empty}%
  \phantomsection
  \addcontentsline{toc}{chapter}{\contentsname}%
  \tableofcontents
  \clearpage
  \pagestyle{plain}}


% Podpisy i numeracja rysunków, tabel, wzorów i listingów
\RequirePackage{caption}
\DeclareCaptionFont{pollubpodpis}{\fontsize{10}{12}\selectfont}
\captionsetup{font={singlespacing,pollubpodpis}, labelsep=period,
  justification=centering, skip=6pt}
\captionsetup[table]{position=top}
\addto\captionspolish{%
  \renewcommand{\figurename}{Rys.}%
  \renewcommand{\tablename}{Tabela}}
\counterwithin{figure}{chapter}
\counterwithin{table}{chapter}
\counterwithin{equation}{chapter}

\def\pollub@table{table}
\g@addto@macro\@floatboxreset{%
  \ifx\@captype\pollub@table
    \fontsize{11}{13.2}\selectfont
  \fi}

\setlength{\intextsep}{6pt}
\setlength{\textfloatsep}{12pt}
\setlength{\floatsep}{12pt}

\g@addto@macro\normalsize{%
  \setlength{\abovedisplayskip}{6pt}%
  \setlength{\belowdisplayskip}{6pt}%
  \setlength{\abovedisplayshortskip}{6pt}%
  \setlength{\belowdisplayshortskip}{6pt}}


% Listy
\RequirePackage{enumitem}
\setlist{nosep}
\setlist[itemize]{labelindent=0.635cm, labelwidth=0.635cm, labelsep=0pt, leftmargin=!, align=left}
\setlist[enumerate]{labelindent=0.635cm, labelwidth=0.635cm, labelsep=0pt, leftmargin=!, align=left}
\setlist[itemize,1]{label=\textbullet}
\setlist[itemize,2]{label=\texttt{o}}
\setlist[itemize,3]{label=\tiny$\blacksquare$}
\setlist[enumerate,1]{label=\arabic*.}
\setlist[enumerate,2]{label=\alph*)}


% Listingi kodu
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


% Bibliografia
\RequirePackage{csquotes}
\RequirePackage[backend=biber, bibstyle=apa, citestyle=numeric, labelnumber,
  sortcites]{biblatex}
\renewcommand*{\bibfont}{\normalfont\raggedright}
\setlength{\bibitemsep}{0pt}
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

% Dane pracy
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

% Streszczenie / Abstract
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
\newcommand{\slowakluczowe}[2][Słowa kluczowe]{%
  \par\vspace{\baselineskip}\noindent #1: #2\par}


% Hiperłącza (ładowane na końcu)
\RequirePackage[hidelinks, bookmarksnumbered, unicode]{hyperref}
\RequirePackage{bookmark}
\urlstyle{same}
\AtBeginDocument{\hypersetup{pdftitle={\PracaTytul}, pdfauthor={\PracaAutor}}}
