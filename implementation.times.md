# Czasy implementacji

## Scenariusz 1

- planowanie: 48 minut
- implementacja Rust: 9 minut (sprawdzanie kompilacji)
- implementacja Java: 7 minut

## Scenariusz 2

- planowanie: 31 minuty
- implementacja Rust: 3 minuty
- implementacja Java: 1 minuty

## Scenariusz 4

- planowanie: 56 minuty
- implementacja Rust: 16 minut
- implementacja Java: 7 minut

## Scenariusz 3

- planowanie: 2h 43min
- implementacja Rust: 10 min
- implementacja Java: 11 min


---

# Instrukcja uruchamiania benchmarków

## Wymagania wstępne

Przed uruchomieniem upewnij się, że masz zainstalowane:

| Narzędzie    | Minimalna wersja         | Jak sprawdzić         |
|--------------|--------------------------|-----------------------|
| Python       | 3.11+ (wymaga `tomllib`) | `python --version`    |
| Java JDK     | Open JDK 25              | `java --version`      |
| Rust + Cargo | dowolna stabilna         | `cargo --version`     |
| hyperfine    | dowolna                  | `hyperfine --version` |

Instalacja hyperfine (jeśli brak):
```powershell
cargo install hyperfine
```

---

## Krok 1 — Instalacja zależności Pythona

Uruchom z **katalogu głównego projektu** (`master_degree/`):

```powershell
pip install -r bench/requirements.txt
```

Instaluje: `psutil`, `matplotlib`, `seaborn`, `numpy`.

---

## Krok 2 — Konfiguracja (`bench/config.toml`)

Przed pierwszym uruchomieniem sprawdź ścieżkę do JDK:

```toml
[java]
java_home = "C:\\Users\\karol\\.jdks\\openjdk-25.0.2"   # <-- dostosuj do swojej ścieżki
```

Pozostałe ustawienia domyślne:

```toml
[general]
warmup_runs = 3          # liczba przebiegów rozgrzewkowych (hyperfine)
benchmark_runs = 10      # liczba mierzonych przebiegów (hyperfine)
resource_monitor_runs = 5  # liczba przebiegów monitorowania RAM/CPU
resource_sample_interval_ms = 10  # częstotliwość próbkowania zasobów
```

---

## Krok 3 — Uruchamianie benchmarków

Wszystkie polecenia uruchamiaj z **katalogu głównego projektu**.

### Pełny pipeline (zalecane)

Buduje projekty, mierzy czas, monitoruje zasoby, zbiera logi GC:

```powershell
python bench/run_benchmarks.py --phases all
```

### Wybrane fazy

Możesz uruchomić tylko wybrane fazy:

```powershell
# Tylko budowanie (javac + jar + cargo build --release)
python bench/run_benchmarks.py --phases build

# Tylko pomiar czasu wykonania (wymaga wcześniejszego buildu)
python bench/run_benchmarks.py --phases timing

# Tylko monitoring pamięci RAM i CPU (wymaga wcześniejszego buildu)
python bench/run_benchmarks.py --phases resources

# Tylko logi GC (Java Garbage Collector, wymaga wcześniejszego buildu)
python bench/run_benchmarks.py --phases gc

# Kilka faz naraz
python bench/run_benchmarks.py --phases build timing
```

### Nadpisywanie parametrów

```powershell
# Szybki test: 1 warmup, 5 przebiegów
python bench/run_benchmarks.py --phases timing --warmup 1 --runs 5

# Tylko wybrany scenariusz
python bench/run_benchmarks.py --phases all --scenarios scenario1

# Własna ścieżka do configu
python bench/run_benchmarks.py --config path/to/config.toml
```

---

## Krok 4 — Generowanie wykresów

Po zakończeniu benchmarków uruchom wizualizację:

```powershell
# Wszystkie wykresy (format PDF)
python bench/visualize.py

# Wybrane wykresy
python bench/visualize.py --charts timing ram

# Inny format wyjściowy
python bench/visualize.py --format png
python bench/visualize.py --format pdf png svg
```

Dostępne typy wykresów:

| Nazwa         | Opis                                                 |
|---------------|------------------------------------------------------|
| `timing`      | Czas wykonania Java vs Rust (słupkowy z odchyleniem) |
| `ram`         | Szczytowe zużycie pamięci RAM                        |
| `ram_time`    | Zużycie RAM w czasie (przebiegi mediany)             |
| `gc_hist`     | Histogram przerw GC (Java)                           |
| `gc_timeline` | Zdarzenia GC w czasie (Java)                         |
| `binary`      | Rozmiar skompilowanych plików                        |

---

## Struktura wyników

Po uruchomieniu benchmarków pliki wynikowe trafiają do `results/`:

```
results/
├── raw/
│   ├── hyperfine/              # surowe wyniki hyperfine (.json)
│   │   └── scenario1_java.json
│   │   └── scenario1_rust.json
│   ├── resource_monitor/       # próbki RAM/CPU per przebieg (.json)
│   │   └── scenario1_java_aggregated.json
│   │   └── scenario1_rust_aggregated.json
│   ├── gc_logs/                # surowe logi GC Java (.log)
│   │   └── scenario1_gc.log
│   └── binary_sizes.json       # rozmiary skompilowanych plików
├── parsed/
│   ├── timing.json             # zestawienie czasów wszystkich scenariuszy
│   ├── resources.json          # zestawienie zasobów wszystkich scenariuszy
│   └── gc_pauses_scenario1.json
└── charts/                     # wykresy (.pdf/.png/.svg)
    ├── execution_time.pdf
    ├── peak_ram.pdf
    └── ...
```

---

## Rozwiązywanie problemów

**`hyperfine not found`**
```powershell
cargo install hyperfine
```

**`ModuleNotFoundError: psutil`**
```powershell
pip install -r bench/requirements.txt
```

**`javac FAILED` / `cargo build FAILED`**
- Sprawdź `java_home` w `bench/config.toml`
- Upewnij się, że `cargo` jest w `PATH`

**Wyniki `timing` bez wcześniejszego `build`**
- Faza `timing` wymaga gotowych binarek. Uruchom najpierw `--phases build`.
