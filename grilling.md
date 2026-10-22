# Scenariusz 3 — Współbieżność: symulacja cząstek Lennard-Jones (Java vs Rust)

Dokument jest wynikiem sesji planowania („grilling”) i stanowi **kompletną specyfikację do implementacji** dla agenta.
Wszystkie decyzje poniżej zostały zatwierdzone przez autora pracy. Jeśli coś jest niejasne — pytaj, nie zgaduj.

---

## 0. Kontekst projektu

- Praca magisterska: porównanie Java 25 vs Rust (edition 2024) na metrykach maszynowych.
- **Wyłącznie biblioteki standardowe** obu języków (zero zależności w `Cargo.toml`, zero bibliotek w Javie).
  Skrypty Pythona w `bench/` mogą używać tylko tego, co jest w `bench/requirements.txt` (psutil, matplotlib, seaborn, numpy).
- Istniejące scenariusze: 1 `mandelbrot`, 2 `csv`, 4 `streaming` — **wszystkie jednowątkowe**. Scenariusz 3 jest jedynym wielowątkowym.
- Pipeline: `bench/run_benchmarks.py` (fazy: build, generate, timing [hyperfine], resources [RSS co 10 ms], gc [`-Xlog:gc*`]),
  `bench/visualize.py` (wykresy do `results/charts/<scenario>/`), konfiguracja `bench/config.toml`. Instrukcja: `bench/README.md`.
- Wzorzec do naśladowania: scenariusz 4 (`streaming`) — program sam zapisuje własny JSON z pomiarami do `output/`,
  pipeline go konsoliduje (`consolidate_latency`).
- Maszyna pomiarowa: **PC, AMD Ryzen 5 7500X3D** (Zen 4, 6 rdzeni / 12 wątków, jednorodne rdzenie, 1 CCD, 96 MB L3),
  **Windows 11 natywnie** (nie WSL). Implementacja może być rozwijana na Linuksie, ale musi działać na Windowsie
  (ścieżki, `.exe`, `java.exe` — pipeline już to obsługuje).

---

## 1. Cel badawczy i hipotezy

Badamy **wyłącznie** dwie hipotezy (JIT i RAM nie są przedmiotem tego scenariusza, choć pipeline je zmierzy):

- **H2 (stabilność czasu kroku):** w stanie ustalonym rozkład czasu kroku symulacji w Javie ma dłuższy ogon (p99, max)
  niż w Ruście, ponieważ pauza GC (stop-the-world) zatrzymuje wszystkie wątki, a bariera czeka na najwolniejszy.
  Rust ma wąski rozkład.
  → **Z analizy rozkładu odrzucamy pierwsze 10% kroków każdego przebiegu** (rozgrzewanie JIT + topnienie kryształu).
  Czas całkowity (hyperfine) obejmuje cały przebieg — spójnie z innymi scenariuszami.
- **H3 (skalowanie):** oba języki skalują się blisko liniowo do 6 wątków (rdzenie fizyczne); powyżej 6 (SMT) przyrost jest mały;
  efektywność ogranicza część szeregowa kroku (prawo Amdahla: `S(P) = 1 / (s + (1 − s)/P)`, gdzie `s` = udział
  szeregowej fazy budowy siatki w czasie kroku przy P = 1).

Dodatkowo (jakościowo, „fearless concurrency”): rozszerzony log implementacji — patrz §10.

---

## 2. Model fizyczny (parametry benchmarku LAMMPS „LJ”, `bench/in.lj`)

| Parametr | Wartość |
|---|---|
| Jednostki | zredukowane LJ: σ = ε = m = 1 |
| Potencjał | Lennard-Jones 12-6, odcięcie `r_c = 2.5` |
| Gęstość | ρ* = 0.8442 |
| Temperatura startowa | T* = 1.44 |
| Krok czasowy | dt = 0.005 |
| Zespół / integrator | NVE, velocity Verlet |
| Brzegi | **periodyczne (PBC)**, sześcienne pudełko o boku L, konwencja minimum image |
| Stan początkowy | sieć FCC, `n × n × n` komórek elementarnych, `N = 4·n³` |

Stałe pochodne:
- stała sieci `a = (4 / ρ)^(1/3) ≈ 1.6796`, bok pudełka `L = n · a`
- liczba komórek siatki na wymiar `M = floor(L / r_c)`, bok komórki `cell = L / M` (≥ r_c)
  - n = 30 → N = 108 000, L ≈ 50.39, M = 20
  - n = 10 → N = 4 000,   L ≈ 16.80, M = 6
- `r_c2 = r_c · r_c = 6.25`
- `E_shift = 4 · (r_c^-12 − r_c^-6)` (≈ −0.016317) — przesunięcie energii potencjalnej **tylko do raportowania energii**;
  siły są identyczne jak w LAMMPS (`lj/cut`).

---

## 3. Algorytm (identyczny w obu językach — wymóg walidacji Java ↔ Rust)

### 3.1 Struktury danych (styl idiomatyczny — świadoma decyzja)
- **Java:** `final class Particle { double x, y, z, vx, vy, vz, fx, fy, fz; }`, tablica `Particle[]`;
  komórki siatki: `ArrayList<Integer>[]` (rozmiar M³), **czyszczone `.clear()` i używane ponownie** co krok
  (boxing indeksów > 127 to świadomy, idiomatyczny koszt Javy — źródło alokacji dla GC, materiał do H2).
- **Rust:** `struct Particle { x, y, z, vx, vy, vz, fx, fy, fz: f64 }`, `Vec<Particle>`;
  komórki: `Vec<Vec<u32>>` czyszczone `.clear()` i używane ponownie.
- **Nie** robimy wersji „zoptymalizowanej” (SoA, `int[] head/next`) — jedna, idiomatyczna wersja na język.

### 3.2 Współbieżność
- **Java:** P stałych wątków platformowych (`new Thread(...)`) + `java.util.concurrent.CyclicBarrier(P)`.
- **Rust:** `std::thread::scope` tworzący P stałych wątków + `std::sync::Barrier::new(P)`.
- Wątki żyją przez całą symulację (nie są tworzone co krok). Wątek główny tylko startuje wątki i robi `join`.
- **Dokładnie P wątków roboczych** (także dla P = 1). Wątek roboczy 0 dodatkowo wykonuje fazę szeregową i mierzy czasy.
- Statyczny podział cząstek: wątek `t` dostaje ciągły blok indeksów `[t·N/P, (t+1)·N/P)` (dzielenie całkowite, ten sam wzór w obu językach).
- **Żadnych ręcznie pisanych prymitywów** (spin-bariery, atomiki do synchronizacji) — tylko powyższe.
- Brak wyścigów danych z konstrukcji: każdy wątek zapisuje wyłącznie do swoich cząstek; pozycje innych tylko czyta
  (w fazie sił, gdy nikt ich nie modyfikuje). W Ruście wymaga to podziału danych (np. `split_at_mut`/chunki dla zapisu
  + współdzielony odczyt pozycji — np. osobna kopia/snapshot pozycji lub `UnsafeCell`-free projekt; agent wybiera
  bezpieczne, idiomatyczne rozwiązanie bez `unsafe`, jeśli to możliwe — **zanotuj w logu z §10, jeśli `unsafe` okazał się konieczny**).

### 3.3 Inicjalizacja (poza pętlą mierzoną)
1. Wczytaj plik wejściowy (§5).
2. Zbuduj siatkę, policz siły początkowe (jak faza C poniżej), policz energię dla kroku 0.

### 3.4 Pętla kroku (S kroków), 4 fazy, bariera po każdej fazie
- **Faza A — pozycje (równolegle, własny blok):**
  `vx += 0.5*dt*fx; (y, z analogicznie)` → `x += dt*vx; ...` → zawinięcie PBC:
  `if (x >= L) x -= L; else if (x < 0) x += L;` (analogicznie y, z).
- **Faza B — siatka (szeregowo, tylko wątek 0):** wyczyść wszystkie komórki; dla `i = 0..N-1` rosnąco:
  `cx = (int)(x / cell); if (cx >= M) cx = M - 1;` (analogicznie cy, cz),
  `c = (cz*M + cy)*M + cx`, dodaj `i` do komórki `c`. (Cząstki w komórce są więc w rosnącej kolejności indeksów.)
- **Faza C — siły (równolegle, własny blok):** dla każdej własnej cząstki `i`: zeruj `f`;
  iteruj po 27 sąsiednich komórkach w **ustalonej kolejności**: `for dz in -1..=1 { for dy in -1..=1 { for dx in -1..=1 {` 
  komórka `((cz+dz+M)%M, (cy+dy+M)%M, (cx+dx+M)%M)`; dla każdego `j` w komórce (kolejność z listy), `j != i`:
  ```
  ddx = x_i - x_j;  if (ddx >  0.5*L) ddx -= L; else if (ddx < -0.5*L) ddx += L;   (ddy, ddz analogicznie)
  r2 = ddx*ddx + ddy*ddy + ddz*ddz
  if (r2 < r_c2) {
      inv_r2 = 1.0 / r2
      inv_r6 = inv_r2 * inv_r2 * inv_r2
      f_over_r = 24.0 * inv_r2 * inv_r6 * (2.0 * inv_r6 - 1.0)
      fx_i += f_over_r * ddx;  fy_i += f_over_r * ddy;  fz_i += f_over_r * ddz
      pe_local += 0.5 * (4.0 * inv_r6 * (inv_r6 - 1.0) - E_shift)
  }
  ```
  Każda para liczona dwukrotnie (bez III zasady Newtona) — celowo, brak zapisów do cudzych cząstek.
  **Kolejność i postać działań dokładnie jak wyżej** (bez FMA, bez `mul_add`, bez przestawiania) — od tego zależy
  kryterium zgodności Java ↔ Rust. `pe_local` — suma cząstkowa per wątek.
- **Faza D — prędkości (równolegle, własny blok):** `vx += 0.5*dt*fx; ...`; `ke_local += 0.5*(vx*vx + vy*vy + vz*vz)`.
- Energia: co 10 kroków (gdy `step % 10 == 0`, numeracja kroków od 1; oraz po ostatnim kroku) wątek 0 sumuje `pe_local`
  i `ke_local` wszystkich wątków **w kolejności indeksów wątków** i zapisuje `{step, ke, pe, total}`.
  Sumy cząstkowe mogą być liczone zawsze (koszt pomijalny), zapisywane tylko co 10 kroków.

### 3.5 Pomiar czasu (wewnątrz programu)
- Wątek 0 bierze znacznik czasu na początku kroku i **po wyjściu z każdej z 4 barier** → czasy 4 faz (z czekaniem na barierze)
  oraz czas całego kroku. Java: `System.nanoTime()`, Rust: `std::time::Instant`.
- Wyniki do **prealokowanych tablic**; zapis JSON dopiero po zakończeniu symulacji.
- Java dodatkowo zapisuje `t0_uptime_ms` = `ManagementFactory.getRuntimeMXBean().getUptime()` w chwili startu pętli
  (moduł `java.management` — część JDK) oraz offset startu każdego kroku względem startu pętli, aby nałożyć pauzy GC
  z logu (`uptime`) na oś czasu kroków.

---

## 4. Interfejs CLI (oba języki identycznie)

```
particles --input <plik.bin> --steps <S> --threads <P> [--snapshot-every <k>] [--dump-final <plik.bin>]
```
- Parsowanie ręczne (Java: `args[]`, Rust: `std::env::args()`), bez bibliotek. Brak wymaganego argumentu → błąd i kod ≠ 0.
- Zawsze na końcu: JSON z pomiarami → `output/scenario3_steps_{lang}_n{N}_p{P}.json` (`lang` ∈ `java`, `rust`).
- `--snapshot-every k`: co k kroków dopisuje klatkę w formacie **XYZ** do `output/scenario3_snapshots_{lang}.xyz`
  (linia z N, linia komentarza z numerem kroku, potem `Ar x y z` per cząstka). **Nigdy w przebiegach pomiarowych.**
- `--dump-final plik`: po ostatnim kroku zapisuje pozycje końcowe: `u32 N`, potem `N × (x, y, z)` jako `f64` LE.
  Używane tylko w fazie `validate`.

### Schemat JSON z pomiarami
```json
{
  "lang": "java", "n": 108000, "threads": 6, "steps": 200, "dt": 0.005,
  "t0_uptime_ms": 412,                 // tylko Java
  "step_start_ns": [0, 191234567, ...], // offset startu kroku od startu pętli
  "step_ns":       [...],               // czas całego kroku
  "phase_ns": { "positions": [...], "cells": [...], "forces": [...], "velocities": [...] },
  "energy": [ {"step": 0, "ke": ..., "pe": ..., "total": ...}, {"step": 10, ...}, ... ]
}
```
JSON pisany ręcznie (jak w scenariuszu 4), bez bibliotek.

---

## 5. Dane wejściowe — `bench/gen_scenario3.py`

- CLI: `--cells n` (liczba komórek FCC na wymiar) i `--output <ścieżka>`; seed zapisany na stałe w skrypcie.
- Pozycje: sieć FCC (4 atomy na komórkę: (0,0,0), (½,½,0), (½,0,½), (0,½,½) × a).
- Prędkości: rozkład Maxwella-Boltzmanna (`random.Random(SEED).gauss`), odjęty pęd całkowity (średnia prędkość = 0),
  przeskalowane tak, by T = 1.44, gdzie `T = Σ v² / (3(N−1))`.
- Format (little-endian): `u32 N`, `f64 L`, następnie `N × (x, y, z, vx, vy, vz)` jako `f64`.
  Java: `ByteBuffer` + `ByteOrder.LITTLE_ENDIAN`; Rust: `f64::from_le_bytes`.
- Pliki: `output/scenario3_n108000.bin` (`--cells 30`), `output/scenario3_n4000.bin` (`--cells 10`).
- Przyspieszenia/siły startowe liczy program, nie generator.

---

## 6. Macierz eksperymentów

| ID | Wpis w config | N | Kroki | Wątki P | Zasoby (RSS) + GC |
|---|---|---|---|---|---|
| E1 | `scenario3` | 108 000 | 200 | 1, 2, 3, 4, 6, 8, 12 | P = 6 i P = 12 |
| E2 | `scenario3_small` | 4 000 | 2 000 | 1, 2, 3, 4, 6, 8, 12 | brak |
| Wizualizacja | ręcznie, poza pipeline | 4 000 | np. 1000 | 6 | — (Rust, `--snapshot-every 10`) |

- hyperfine: warmup/runs z `[general]` (3 / 10).
- Szacunek (do weryfikacji przy pierwszym uruchomieniu): ~0.2 s/krok przy P = 1 dla E1; cały pipeline ~1–1.5 h.
  Jeśli wyjdzie znacznie więcej — **zapytaj autora** przed zmianą liczby kroków.
- Konfiguracja JVM bez zmian: `-Xms512m -Xmx8g`, G1 (domyślny). Rust: domyślny `cargo build --release`
  (bez `target-cpu=native`, bez LTO). Brak rozgrzewania wewnątrz procesu.

---

## 7. Integracja z pipeline'em (rozszerzenie generyczne)

Istniejące scenariusze 1, 2, 4 muszą działać **bez zmian** (brak nowych kluczy = dotychczasowe zachowanie).

### 7.1 `bench/config.toml`
```toml
[scenarios.scenario3]
name = "Concurrency - LJ particles (E1)"
description = "3D Lennard-Jones MD, 108k particles, 200 steps, cell list, P worker threads + barrier"
java_package = "particles"
java_jar = "java/target/particles.jar"
rust_binary = "rust/target/release/particles.exe"
generator_script = "bench/gen_scenario3.py"
generator_args = ["--cells", "30", "--output", "output/scenario3_n108000.bin"]
generator_output = "output/scenario3_n108000.bin"
args = ["--input", "{input}", "--steps", "200", "--threads", "{threads}"]
threads = [1, 2, 3, 4, 6, 8, 12]
resource_threads = [6, 12]

[scenarios.scenario3_small]
name = "Concurrency - LJ particles (E2)"
description = "3D Lennard-Jones MD, 4k particles, 2000 steps"
java_package = "particles"
java_jar = "java/target/particles.jar"
rust_binary = "rust/target/release/particles.exe"
generator_script = "bench/gen_scenario3.py"
generator_args = ["--cells", "10", "--output", "output/scenario3_n4000.bin"]
generator_output = "output/scenario3_n4000.bin"
args = ["--input", "{input}", "--steps", "2000", "--threads", "{threads}"]
threads = [1, 2, 3, 4, 6, 8, 12]
resource_threads = []
```
Dodać też `[[bin]] name = "particles", path = "src/particles/main.rs"` w `rust/Cargo.toml`.

### 7.2 `bench/run_benchmarks.py` / `bench/utils.py`
- `get_java_command` / `get_rust_command` / `get_java_command_with_gc`: dopinają `args` scenariusza; `{input}` → `generator_output`;
  `{threads}` → zostaje dla hyperfine (timing) lub podstawiane konkretną wartością (resources, gc, validate).
- **generate:** przekazuje `generator_args` do skryptu, jeśli są.
- **timing:** gdy scenariusz ma `threads` → `hyperfine --parameter-list threads 1,2,3,4,6,8,12 ...` (jeden JSON per język).
  Po zakończeniu kopiuje `output/scenario3_steps_{lang}_n{N}_p{P}.json` (ostatni przebieg każdego P) do
  `results/raw/steps/{scenario}_{lang}_p{P}.json`. `consolidate_timing` obsługuje wiele wyników (per P).
- **resources:** dla P z `resource_threads`; po **każdym** przebiegu kopiuje JSON kroków do
  `results/raw/steps/{scenario}_{lang}_p{P}_run{k}.json` (to źródło danych dla H2 — 5 przebiegów zbiorczo).
  Nazwy plików RSS z sufiksem `_p{P}`.
- **gc:** dla P z `resource_threads`; log `results/raw/gc_logs/{scenario}_p{P}_gc.log` + kopia JSON kroków z tego samego
  przebiegu (`..._p{P}_gc.json`) do nałożenia pauz na oś czasu.
- **validate (nowa faza):** tylko dla `scenario3`: uruchamia Javę i Rusta dla P = 1 i P = 12 z
  `--dump-final output/scenario3_final_{lang}_p{P}.bin`, potem `bench/validate_scenario3.py`. Niezdany test → kod ≠ 0.
- Konsolidacja kroków → `results/parsed/steps_scenario3.json` i `results/parsed/steps_scenario3_small.json`.
- Zaktualizować `bench/README.md` (nowa faza, nowe klucze configu, nowe wykresy).

### 7.3 `bench/validate_scenario3.py` — kryteria (wszystkie muszą przejść)
1. **Energia:** dla każdego z 4 przebiegów `max_t |E(t) − E(0)| / |E(0)| < 1e-3`.
2. **Determinizm względem P:** plik `final_{lang}_p1.bin` **bajtowo identyczny** z `final_{lang}_p12.bin` (dla obu języków).
3. **Java ↔ Rust:** maksymalna różnica pozycji (z konwencją minimum image) `< 1e-6`.
Wypisuje czytelny raport (wartości liczbowe + PASS/FAIL).

---

## 8. Wykresy — `bench/visualize.py`, katalog `results/charts/scenario3/` (i `scenario3_small/`)

Styl jak istniejące wykresy (`setup_style`, PDF + PNG). Java i Rust zawsze na jednym wykresie.

Standardowe (istniejące funkcje, dostosowane do scenariuszy z `threads`):
- `execution_time` — dla P = 6; `peak_ram`, `ram_over_time` — dla P = 6 i 12; `binary_size`;
  `gc_pause_timeline`, `gc_pause_histogram` — z logów P = 6 i 12.

Nowe:
- `speedup` — S(P) = T(1)/T(P) (mediany hyperfine) vs P; linia idealna y = P; krzywa Amdahla dla `s` wyznaczonego
  z fazy `cells` przy P = 1 (osobno per język). E1 i E2 osobno.
- `efficiency` — S(P)/P vs P.
- `phase_breakdown` — skumulowane słupki: mediana czasu faz positions / cells / forces / velocities per P (per język).
- `step_time_percentiles` — p50, p95, p99, max czasu kroku dla P = 6 i 12, oś Y log; dane: przebiegi z fazy resources,
  **po odrzuceniu pierwszych 10% kroków**; analogicznie do `latency_percentiles` ze scenariusza 4. (Główny wykres H2.)
- `step_time_timeline` — czas kroku vs numer kroku (Java i Rust, P = 6), z naniesionymi pauzami GC Javy
  (wyrównanie przez `t0_uptime_ms` + `step_start_ns` vs `uptime` z logu GC).

---

## 9. Wizualizacja symulacji — `bench/render_scenario3.py`

- Uruchamiana ręcznie **po** eksperymencie; nie jest częścią pomiarów.
- Wejście: `output/scenario3_snapshots_rust.xyz` z przebiegu: `particles --input output/scenario3_n4000.bin --steps 1000 --threads 6 --snapshot-every 10`.
- Wyjście: kilka klatek PNG (wykres 3D scatter, matplotlib) + GIF przez `matplotlib.animation.PillowWriter`
  (Pillow jest zależnością matplotlib — bez nowych pakietów) do `results/charts/scenario3/`.
- Plik XYZ można też otworzyć w OVITO (wzmianka w pracy).

---

## 10. Log implementacji — `implementation.times.md`

Sekcja „Scenariusz 3” w tym samym formacie co pozostałe (planowanie / implementacja Rust / implementacja Java),
**rozszerzona** o:
- liczbę iteracji z AI do pierwszej udanej kompilacji i do pierwszego poprawnego wyniku (przejście `validate`),
- błędy kompilacji związane ze współbieżnością w Ruście (borrow checker, `Send`/`Sync`, lifetimes w `thread::scope`),
- błędy wykonania w Javie (wyścigi danych, deadlock na barierze, niepoprawne wyniki),
- czy było potrzebne `unsafe` w Ruście (i dlaczego).

To jedyny kanał, którym teza „fearless concurrency” wchodzi do pracy — jako dane, nie opinia. Agent implementujący
powinien te zdarzenia notować na bieżąco (autor uzupełni czasy).

---

## 11. Kolejność prac (sugerowana)

1. `gen_scenario3.py` + wygenerowanie obu plików.
2. Rust `particles` (lepiej najpierw — kompilator wymusi bezpieczny podział danych).
3. Java `org.master.particles` (te same klasy/odpowiedzialności co w innych scenariuszach: `Main`, logika, I/O, JSON).
4. `validate_scenario3.py` + faza `validate` — **wyniki dopiero po przejściu walidacji**.
5. Rozszerzenia `run_benchmarks.py` / `utils.py` / `config.toml` (sprawdzić, że scenariusze 1, 2, 4 działają jak wcześniej).
6. Nowe wykresy w `visualize.py`, `render_scenario3.py`, aktualizacja `bench/README.md`.

Struktura kodu: wzoruj się na `mandelbrot` / `streaming` (podział na kilka plików wg odpowiedzialności, stałe na górze,
podobna gęstość komentarzy). Nazewnictwo: Java `java/src/main/java/org/master/particles/`, Rust `rust/src/particles/`.

---

## 12. Otwarte — świadomie odłożone

- **Procedura pomiarowa na Windowsie** (plan zasilania, Precision Boost — wstępnie: zostaje włączony i opisany jako
  zagrożenie trafności, bo 1 wątek taktuje wyżej niż 12 → speedup lekko zaniżony; przypinanie wątków — wstępnie brak;
  kolejność serii / przeplatanie języków; zamknięcie aplikacji w tle). Do ustalenia z autorem przez agenta, który
  będzie uruchamiał eksperyment na PC.
- Ścieżki w `config.toml` (`java_home`, `.exe`) są windowsowe — przy testach na Linuksie nie commitować zmian tych ścieżek.

## 13. Poza zakresem

- Pilotaż „który mechanizm współbieżności jest najszybszy” (odrzucony — temat na osobną pracę).
- Dodatkowy pomiar Rusta z `-C target-cpu=native` (odrzucony; w pracy wzmianka jako zagrożenie trafności:
  JIT Javy sam używa AVX-512 na Zen 4, Rust kompiluje pod bazowe x86-64).
- Listy Verleta, III zasada Newtona, wersje SoA, ściany/grawitacja, hipotezy o JIT i RAM.
