## 0. Wspólne tło techniczne

Trzy fakty z konfiguracji, które tłumaczą większość obserwowanych kształtów krzywych:

- **JVM**: `-Xms512m -Xmx8g` (`bench/config.toml`). Heap może urosnąć do 8 GB, ale startuje od 512 MB
- **GC**: domyślny w JDK 25 → G1GC (Garbage-First). Pauzy stop-the-world tylko dla fazy Young (dla Mixed/Full bardzo rzadko)
- **Pomiar RAM**: zewnętrzny sampling RSS co 10 ms (`resource_monitor.py`). RSS = pamięć wzięta od OS, nie koniecznie cała jest używana od wewnątrz JVM.
- **Logi GC**: `-Xlog:gc*` — parser (`bench/gc_parser.py`) wyciąga wszystkie typy pauz. Na wykresach są wyłącznie pauzy `Young` — czyli G1 ani razu nie musiał wykonać Mixed/Full GC.

---

## 1. Scenariusz 1 — CPU
- **Java**: niemal natychmiastowy skok do ~88 MB w pierwszej próbce → długi constant przez ~5 s → **nagły skok do ~138 MB** tuż przed końcem
    - Początkowe 88 MB = narzut startowy JVM: classloader, metaspace, JIT compiler thread, początkowe regiony G1, biblioteki natywne
    - Plateau przez czas obliczeń: Mandelbrot to czysta praca CPU na lokalnych `double`/`int`, alokacji obiektów heap praktycznie nie ma → GC nie ma co robić, RSS się nie rusza.
    - Skok na końcu = alokacja bufora bajtów obrazu PPM 4096×4096 (kilkadziesiąt MB) przed zapisem do pliku. To **nie** jest GC.
- **Rust**: start ~2 MB → liniowy, powolny wzrost do ~50 MB.
    - Brak bootstrap'u runtime'u; binarka mapuje minimalny zestaw stron.
    - Liniowy wzrost = bufor pikseli stopniowo rośnie (lub `Vec` jest realokowany w miarę zapisywania linii obrazu).

Różnica ~88 MB vs ~2 MB na starcie pokazuje **stały koszt obecności JVM** - nawet jeśli sam algorytm nic nie alokuje,
dla aplikacji długo działających ten koszt jest pomijalny, ale dla krótkich programów (np. workflowy, narzędzie CLI) jest dominujący.


## 2. Scenariusz 2 — I/O / CSV Filter

Krzywa Java przechodzi w wyraźnych skokach: **~500 MB → ~650 MB → ~1000 MB → ~1900 MB**, każdy poprzedzony prostą linią.

**Mechanizm krok po kroku:**

1. Aplikacja Java alokuje intensywnie w pass 1 (`Csv.run()` w `java/.../csv/Csv.java:18-26` ładuje wszystkie kwoty do `double[]` przez Stream API — `mapToDouble().sorted().toArray()`, plus boxing/parsowanie generuje masę krótkożyjących obiektów `String` i `Double`).
2. Eden Space się zapełnia → G1 odpala **Young GC** (pauza STW, widoczna na timeline).
3. Po Young GC G1 oblicza heuristycznie: czy bieżący *committed heap size* wystarczy do utrzymania `GCTimeRatio`. Jeśli alokacja nadal jest szybsza niż reclaiming → **commit dodatkowych regionów z OS**.
4. Każdy taki commit = nowe strony pamięci wirtualnej zostają zmapowane do procesu → **RSS skacze w górę** (to obserwujemy jako „stopień").
5. Plateau między stopniami = na tym poziomie heap'u G1 nadąża, nie ma potrzeby commitowania więcej.

**Dlaczego po pass 1 RSS NIE spada?**
- `double[] amounts` (po sortowaniu) staje się śmieciem, gdy zaczyna się pass 2 → w teorii ~400 MB zwalniane.
- Ale **G1 domyślnie nie zwraca pamięci do OS** po niesynchronizowanym uncommit. W JDK 12+ istnieje `G1PeriodicGCInvokesConcurrent` + `G1PeriodicGCInterval` które pozwalają na okresowy uncommit, ale **nie są domyślnie włączone**.
- Skoro `-Xmx=8g`, JVM uważa, że ma „bilet" do trzymania tego co już zacommitował.
- Stąd RSS pozostaje na 1.9 GB do końca programu, mimo że *heap used* w tym czasie spadłby diametralnie.

**Końcowy gwałtowny zjazd** = process `exit()`, OS odbiera strony.

### 2.2 `ram_over_time.pdf` — kształt trójkąta w Ruście

- Rust: liniowy wzrost do ~400 MB w pass 1, **gwałtowny zjazd przy ~6 s**, potem płaska linia ~20 MB przez resztę pass 2.
- Zjazd to nie GC i nie sweep — to **deterministyczna dealokacja**: `Vec<f64>` zawierający kwoty wychodzi ze scope'u po obliczeniu thresholdu i jego `Drop` zwraca pamięć przez `free()` natychmiast.
- W pass 2 Rust streamuje plik linijka po linijce z buforem — stąd niski, stały poziom.

**To jest najmocniejszy wizualny argument dla tezy pracy** o ownership vs GC: **ten sam algorytm w obu językach kończy z różnym poziomem zaalokowanej pamięci, choć logicznie potrzeba tej pamięci spadła do zera.**

### 2.3 `gc_pause_timeline.pdf` — unikalne elementy

- Około **150 pauz Young** rozsianych głównie w przedziale 0–9 s i 12–21 s.
- Większość pauz: **0.4–0.7 ms** (typowy G1 Young dla średniego heap'u).
- **Dwa outlier'y ~3 ms** (przy ~1.3 s i ~6.7 s) — najprawdopodobniej Young GC, który wystąpił tuż po commit'cie nowego, dużego stopnia heap'u: zestaw survivor + rescanning Remembered Sets staje się większy, pauza dłuższa.
- **Widoczna przerwa ~9–12 s w aktywności GC** — to nie błąd pomiaru, tylko cisza alokacyjna:
    - Pass 1 się kończy (`br.lines()...toArray()` zwrócił tablicę).
    - Następuje `Arrays.sort()` na prymitywach `double[]` — sortowanie *in-place*, **bez alokacji obiektów**.
    - Plus `Files.size()` i obliczenie indeksu — operacje skalarne.
    - GC nie ma co robić, brak pauz.
    - Po otwarciu pass 2 (nowe `BufferedReader`, nowy `FileWriter`, kolejny Stream API z boxowaniem) → alokacje wracają, GC wznawia.

### 2.4 `gc_pause_histogram.pdf`

- Rozkład wyraźnie skupiony przy 0.5–0.7 ms (Eden ma stałą pojemność, każda kolekcja ewakuuje podobną ilość obiektów).
- Mean ~0.6 ms, P99 ~1 ms, ogon do 3 ms.
- **Brak pauz typu Mixed/Full** — G1 ani razu nie musiał zająć się old generation, bo working set był krótkożyjący (klasyczny weak generational hypothesis).

### 2.5 Pozostałe wykresy w 1 zdaniu

- `peak_ram.pdf` — pokazuje przepaść: Java ~1.9 GB peak vs Rust ~400 MB peak.
- `execution_time.pdf` — Java wolniejsza głównie przez koszt boxing/Stream API w pass 1.
- `binary_size.pdf` — patrz scenario 1.

---

## 3. Scenariusz 4 — Memory / IoT Streaming (`results/charts/scenario4/`)

Wykresy: `execution_time.pdf`, `peak_ram.pdf`, `ram_over_time.pdf`, `gc_pause_timeline.pdf`, `gc_pause_histogram.pdf`, `latency_distribution.pdf`, `latency_percentiles.pdf`, `binary_size.pdf`.

**Scenariusz zaprojektowany pod tezę pracy** — porównanie ogonów rozkładu latencji GC vs ownership.

### 3.1 `ram_over_time.pdf`

- **Java**: schodki ~30 MB → ~90 MB → ~270 MB → ~350 MB, plateau ~350 MB od ~2 s do końca.
    - Każdy stopień = commit kolejnej porcji regionów G1 w miarę zapełniania `HashMap<Integer, SensorState>` (`java/.../streaming/Streaming.java:15`).
    - Plateau = wszystkie ID czujników już widziane (working set się ustabilizował), nowych wpisów do mapy nie ma → G1 ma stały rozmiar i nie commituje więcej.
- **Rust**: ~6 MB płasko od początku do końca.
    - `HashMap` w Ruście trzyma struktury bez boxing'u (klucz `i32`, wartość `SensorState` inline w bucket'cie), brak nagłówków obiektów (8–16 B per obiekt w Javie), brak overheadu GC bookkeeping.
    - Praktycznie **~60× mniej pamięci** na tym samym zadaniu.

### 3.2 `gc_pause_timeline.pdf` + `gc_pause_histogram.pdf`

- **Tylko 15 pauz Young** przez 8 s — bardzo niska częstotliwość, bo working set jest stabilny (mało survivorów do ewakuacji).
- Pierwsza pauza najdłuższa (~1.12 ms) — heap przechodzi z initial state do steady-state, Remembered Sets dopiero się ustawiają, więcej regionów do zeskanowania.
- Kolejne pauzy malejąco: ~0.88 → ~0.77 → ... → ustabilizowane przy ~0.55–0.7 ms.
- Histogram: wąski rozkład 0.55–1.12 ms, Mean = 0.71 ms, P99 = 1.12 ms (P99 = max przy małej próbce 15).
- **Brak Mixed/Full GC** — long-lived obiekty (mapa sensorów) siedzą w old gen i G1 ich nie rusza, bo nie ma pressure.

### 3.3 `latency_percentiles.pdf` — KLUCZOWY wykres dla pracy

Oś Y log, pomiar **per-event** (czas przetworzenia pojedynczego eventu):

| Percentyl | Java 25 | Rust    | Komentarz                     |
|-----------|---------|---------|-------------------------------|
| p50       | ~0.2 µs | ~0.2 µs | identyczne — fast path bez GC |
| p95       | ~0.2 µs | ~0.2 µs | jw.                           |
| p99       | ~0.2 µs | ~0.2 µs | jw.                           |
| p99.9     | ~0.4 µs | ~0.2 µs | Java zaczyna pokazywać braki  |
| max       | ~3 ms   | ~0.5 ms | różnica ~6x                   |

- p50–p99 identyczne dowodzą, że JIT'owany kod Javy jest **w trybie ustalonym tak samo szybki** jak Rust — to ważne, żeby uniknąć narracji „Rust zawsze szybszy".
- p99.9 i max odsłaniają **różnicę architektoniczną**: Java ma kilka eventów, które trafiły w pauzę GC (1.12 ms z timeline + szum schedulera OS daje ~3 ms max), Rust ma stały deterministyczny czas + tylko OS scheduler / page fault.
- To **bezpośredni dowód tezy**: GC powoduje deterministyczne pogorszenie ogonów rozkładu latencji, nawet jeśli średnie są identyczne.

### 3.4 `latency_distribution.pdf`

- Oba histogramy mają tę samą lewą stronę (tryb ~0.2 µs), różnica tylko w ogonie:
    - Java: ogon sięga ~10⁴ µs (kilka eventów w przedziale milisekund).
    - Rust: urywa się przy ~10³ µs.
- Bardziej szczegółowa wersja informacji z `latency_percentiles.pdf` — przydatna jako uzupełniający wykres, ale `latency_percentiles.pdf` lepiej komunikuje main finding.

### 3.5 Pozostałe wykresy w 1 zdaniu

- `peak_ram.pdf` — ~350 MB vs ~6 MB (rzędu wielkości).
- `execution_time.pdf` — Java w tym scenariuszu jest często **wolniejsza** głównie przez koszt hashowania `Integer` boxed key + GC overhead.

---

## 4. Podsumowanie metodologiczne (do akapitu w pracy)

- **Pomiar RSS, nie heap used**: świadoma decyzja — RSS to to, co widzi administrator/OS, i to ten wymiar zasobowy ma znaczenie ekonomiczne (instancja chmurowa, kontener, embedded). Heap used byłby bardziej „przychylny" Javie, ale fałszywie sugerowałby, że pamięć jest „dostępna" dla innych procesów.
- **Sampling 10 ms**: krótsze spike'i mogą zostać niezauważone — wzmianka w pracy o granicach metody. Dla pauz GC mamy precyzyjny pomiar z logów (mikrosekundy), więc tail latency jest mierzony rzetelnie niezależnie od samplingu RSS.
- **Brak Full GC w żadnym scenariuszu** = G1 wypadł poprawnie skonfigurowany dla naszego obciążenia. To istotne stwierdzenie: porównujemy „dobry przypadek" Javy z Rustem, nie ustawiony pod tezę przypadek patologiczny.
- **Schodki w RAM ≠ wyciek pamięci**: to świadomy projekt G1 (commit nowych regionów + brak natychmiastowego uncommit). Można to zmienić flagami (np. `-XX:G1PeriodicGCInterval`, `-XX:+UseShenandoahGC` lub `-XX:+UseZGC` ze `-XX:+ZUncommit`), ale za cenę wyższego narzutu CPU lub innych trade-offów — to dobry materiał na rozdział „możliwe optymalizacje".

---

## 5. Mapowanie wykres → unikalny element (cheatsheet)

| Wykres                               | Co opisać unikalnego                                                |
|--------------------------------------|---------------------------------------------------------------------|
| `scenario1/ram_over_time.pdf`        | Stały narzut startowy JVM (~88 MB) + spike PPM na końcu             |
| `scenario2/ram_over_time.pdf`        | **Schodki Javy 500→650→1000→1900 MB**; trójkąt Rusta z dropem ~6 s  |
| `scenario2/gc_pause_timeline.pdf`    | Dwa outlier'y ~3 ms; przerwa w GC ~9–12 s (sortowanie `double[]`)   |
| `scenario2/gc_pause_histogram.pdf`   | Rozkład skupiony 0.5–0.7 ms, P99 ~1 ms, brak Mixed/Full             |
| `scenario4/ram_over_time.pdf`        | Schodki 30→90→270→350 MB → plateau; ~60× mniej RAM w Ruście         |
| `scenario4/gc_pause_timeline.pdf`    | Tylko 15 pauz; pierwsza najdłuższa, dalej malejąco do steady-state  |
| `scenario4/gc_pause_histogram.pdf`   | Wąski rozkład 0.55–1.12 ms                                          |
| `scenario4/latency_percentiles.pdf`  | **Główny dowód tezy**: p50–p99 równe, p99.9 i max rozjeżdżają się   |
| `scenario4/latency_distribution.pdf` | Identyczna lewa strona, ogon Javy o rząd wielkości dłuższy          |
