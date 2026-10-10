# Konfiguracja latexmk: `latexmk` (lub `make`) w katalogu master/ buduje build/main.pdf
$pdf_mode = 1;                 # pdflatex
$bibtex_use = 2;               # biber uruchamiany automatycznie, gdy trzeba
$out_dir = 'build';
@default_files = ('main.tex');
$pdflatex = 'pdflatex -interaction=nonstopmode -file-line-error -synctex=1 %O %S';
