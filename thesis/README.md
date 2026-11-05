# Praca magisterska — szablon LaTeX

Formatowanie zgodne z „Zasadami prowadzenia prac dyplomowych i dyplomowania na WEiI Politechniki Lubelskiej”
(2025), Załącznik nr 7 „Wytyczne przygotowania pracy dyplomowej” (dalej: Wytyczne) i Załącznik nr 5 (strona tytułowa).
Treść piszesz w plikach rozdziałów, resztą zajmuje się klasa.

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
| `main.tex` | „sklejka” — kolejność części pracy (Wytyczne 1.3) |
| `metadane.tex` | dane na stronę tytułową: autor, tytuł, promotor, kierunek, blok dyplomowania… |
| `pollubthesis.cls` | całe formatowanie (marginesy, czcionki, nagłówki, spis treści, podpisy, bibliografia) |
| `polish-apa.lbx` | polskie zwroty dla stylu APA (biblatex-apa nie ma polskiej lokalizacji) |
| `strony-wstepne/` | strona tytułowa, streszczenie, abstract |
| `rozdzialy/01-…07-*.tex` | jeden plik na rozdział, układ pracy magisterskiej z Wytycznych (1.2) |
| `rozdzialy/99-przyklady.tex` | ściąga: rysunek, tabela, listing, wzór, cytowania — **usuń przed oddaniem** |
| `bibliografia.bib` | źródła (na razie fikcyjne przykłady z Wytycznych) |
| `grafika/` | obrazy; logo wydziału na stronę tytułową już jest |

Rozdziały (Wytyczne 1.2): Wstęp → Cel i zakres pracy → Analiza stanu wiedzy → Metoda badań →
Charakterystyka obiektu badań → Wyniki badań → Wnioski → Wykaz literatury. Każdy plik ma w komentarzu,
co według Wytycznych powinno się w nim znaleźć.

## Jak pisać

- **Nowy rozdział:** plik w `rozdzialy/` i linia `\input{rozdzialy/nazwa}` w `main.tex`.
- **Szybka kompilacja jednego rozdziału:** zakomentuj w `main.tex` linie `\input` pozostałych rozdziałów (odwołania do nich pokażą się jako `??`).
- **Cytowanie:** `\cite{klucz}` → [1], [2, 4, 5]. Wykaz literatury jest w stylu APA 7 i uporządkowany **alfabetycznie**,
  więc numery wynikają z nazwisk autorów, a nie z kolejności cytowania. W wykazie pojawiają się tylko zacytowane
  pozycje — Wytyczne wymagają, by każda była przywołana w tekście. Wskazówki do typów wpisów są na początku `bibliografia.bib`.
- **Rysunki** (także wykresy) `figure` → „Rys. 2.1. …”, podpis pod rysunkiem. **Tabele** `table` → „Tabela 2.1. …”,
  `\caption` **przed** `tabular` (podpis nad tabelą). Numeracja w obrębie rozdziału, bez kropki na końcu podpisu.
  W tekście odwołanie przed obiektem: „Na rys.~\ref{…} przedstawiono…”.
- **Wzory** numerowane (2.1); **kod** `lstlisting` (Java i Rust gotowe) → „Listing 2.1.”.
- **Miana** bez nawiasów kwadratowych: „czas, ms”, nie „czas [ms]” (Wytyczne 3.1).
- **Polska typografia:** `w~tekście` (tylda wiąże jednoliterowe słowa), `\num{12.5}` → 12,5.
- **Druk jednostronny:** `\documentclass[oneside]{pollubthesis}` — bez marginesów lustrzanych i pustej strony po tytułowej.

## Co ustawia klasa

| Element | Wartość | Wytyczne |
|---|---|---|
| Strona | A4; wewn. 3,5 cm, zewn. 2 cm, góra 2,5 cm, dół 2 cm; marginesy lustrzane | 2.2 |
| Tekst | Times 12 pt, interlinia 1,5, wyjustowany, wcięcie akapitu 0,85 cm, bez odstępów między akapitami | 2.1, 2.3 |
| Nagłówki | `1.` 14 pt pogrubiony / `1.1.` 12 pt pogrubiony / `1.1.1.` 12 pt kursywa; rozdział od nowej strony | 2.1, 2.3 |
| Podpisy | „Rys. 2.1. …” pod rysunkiem, „Tabela 2.1. …” nad tabelą; 10 pt, wyśrodkowane, 6 pt odstępu | 2.4, 2.5 |
| Tabele | czcionka 11 pt, pojedyncza interlinia w komórkach | 2.5 |
| Wzory | numer (2.1) przy prawym marginesie, 6 pt przed i za | 2.6 |
| Wykaz literatury | APA 7, alfabetycznie, numery [1] w tekście i w wykazie | 2.7 |
| Streszczenia | PL i EN ze słowami kluczowymi na jednej stronie, przed spisem treści | 1.2, 1.3 |
| Numer strony | na środku stopki; brak na stronie tytułowej | 3.2 |
| Spisy rysunków/tabel | nie umieszcza się | 1.3 |
| Strona tytułowa | wg wzoru z Załącznika 5 (czcionka bezszeryfowa, „na bloku dyplomowania …”) | Zał. 5 |
