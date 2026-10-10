# Praca magisterska — szablon LaTeX

Formatowanie odwzorowane z dokumentu Word wydziału (Politechnika Lubelska, WEiI): strona tytułowa,
spis treści, nagłówki, podpisy, bibliografia. Treść piszesz w plikach rozdziałów, resztą zajmuje się klasa.

## Budowanie

```bash
make          # build/main.pdf  (latexmk → pdflatex + biber)
make watch    # przebudowa po każdym zapisie pliku
make clean    # usuwa build/
```

Bez `make`: `latexmk` w katalogu `` (konfiguracja w `.latexmkrc`).

## Struktura

| Plik / katalog | Zawartość |
|---|---|
| `main.tex` | „sklejka” — kolejność części pracy |
| `metadane.tex` | dane na stronę tytułową: autor, tytuł, promotor, kierunek… |
| `pollubthesis.cls` | całe formatowanie (marginesy, czcionki, nagłówki, spis treści, podpisy, bibliografia) |
| `strony-wstepne/` | strona tytułowa, streszczenie, abstract |
| `rozdzialy/01-…06-*.tex` | jeden plik na rozdział, szkielet jak w oryginale |
| `rozdzialy/99-przyklady.tex` | ściąga: rysunek, wykres, tabela, listing, wzór, cytowania — **usuń przed oddaniem** |
| `bibliografia.bib` | źródła (na razie fikcyjne przykłady) |
| `grafika/` | obrazy; logo wydziału na stronę tytułową już jest |

## Jak pisać

- **Nowy rozdział:** plik w `rozdzialy/` i linia `\input{rozdzialy/nazwa}` w `main.tex`.
- **Szybka kompilacja jednego rozdziału:** zakomentuj w `main.tex` linie `\input` pozostałych rozdziałów (odwołania do nich pokażą się jako `??`).
- **Cytowanie:** `\cite{klucz}` → [1], [2–4]. Numeracja w kolejności cytowania; w bibliografii pojawiają się tylko
  zacytowane pozycje (dopóki nic nie cytujesz, rozdziału „Bibliografia” nie ma).
- **Rysunki** `figure`, **wykresy** `wykres` (osobna numeracja, jak w oryginale), **tabele** `table`,
  **kod** `lstlisting` (Java i Rust gotowe). Podpisy pod obiektami, numeracja ciągła.
- **Polska typografia:** `w~tekście` (tylda wiąże jednoliterowe słowa), `\num{12.5}` → 12,5.
- **Druk jednostronny:** `\documentclass[oneside]{pollubthesis}` — bez marginesów lustrzanych i pustej strony po tytułowej.

## Co odwzorowano z Worda

| Element | Wartość |
|---|---|
| Strona | A4; góra 2,5 cm, wewnętrzny 3,5 cm, zewnętrzny 2 cm; marginesy lustrzane (druk dwustronny) |
| Tekst | Times 12 pt, interlinia 1,5 (20,7 pt — 34 wiersze na stronę), wyjustowany, wcięcie 1,27 cm |
| Nagłówki | `1.` 16 pt / `1.1.` 14 pt / `1.1.1.` 12 pt, pogrubione; rozdział od nowej strony |
| Spis treści | 3 poziomy, kropki prowadzące, bez numerów stron w stopce; zawiera wpis „Spis treści” |
| Numer strony | na środku stopki; liczony od strony tytułowej, widoczny od streszczenia |
| Podpisy | „Rysunek 1 …”, „Tabela 1 …”, „Wykres 1 …” — 9 pt, pogrubione, wyśrodkowane, tuż pod obiektem |
| Tabele | pełna siatka, szary wiersz nagłówka (`\rowcolor{tabnaglowek}`), interlinia 1,5 w komórkach |
| Bibliografia | numeryczna [1], kolejność cytowania, wpisy wyrównane do lewej, wcięte 0,635 cm (bez wysunięcia) |
| Dzielenie wyrazów | wyłączone, jak w oryginale (włączenie: komentarz w `pollubthesis.cls`) |

Odstępy pionowe wymierzono na wydruku oryginału — różnice poniżej 2 pt.
