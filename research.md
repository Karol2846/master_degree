Zdecydowałem się na implementację wyłącznie w oparciu o biblioteki standardowe obu języków (brak zewnętrznych zależności).
Dodatkowo, aby przyspieszyć proces tworzenia kodu - chciałbym użyć narzędzi Ai.
W związku z tym pominę metryki związane z czasem programowania i złożonością kodu.
W samych badaniach skupię się stricte na metrykach maszynowych
(czas wykonania, szczytowe zużycie RAM, rozmiar pliku wykonywalnego, linie kodu, złożoność kodu (SonarQube), czas wykonania pracy - generowanie, prompty itd)

Wybrałem 4 następujące scenariusze badawcze:
1. **Obciążenie CPU**: Generowanie zbioru Mandelbrota z zapisem do surowego formatu PPM
   (ze względu na brak wbudowanej obsługi kompresji obrazów w standardowej bibliotece Rusta).
2. Obciążenie I/O: Sekwencyjne przetwarzanie pliku CSV (np. 5 GB danych transakcyjnych).
   Parsowanie wierszy, nałożenie prostego filtru (szukanie największych transakcji) i zapis pasujących rekordów do nowego pliku.
3. **Współbieżność**: równoległa symulacja dynamiki molekularnej 3D (potencjał Lennard-Jonesa, parametry benchmarku LAMMPS LJ,
   108 000 i 4 000 cząstek, periodyczne warunki brzegowe, listy komórek przebudowywane co krok).
   P stałych wątków synchronizowanych barierą (Java: `Thread` + `CyclicBarrier`, Rust: `thread::scope` + `std::sync::Barrier`),
   P ∈ {1, 2, 3, 4, 6, 8, 12}. Hipotezy: skalowanie zgodne z prawem Amdahla (nasycenie powyżej 6 rdzeni fizycznych)
   oraz dłuższy ogon rozkładu czasu kroku w Javie przez pauzy GC zatrzymujące wszystkie wątki.
   Szczegółowy plan: `grilling.md`.
4. **Zarządzanie pamięcią**: Działający w pamięci silnik przetwarzania strumieniowego (symulacja IoT).
   Odbiór milionów zdarzeń, filtrowanie anomalii i agregacja (średnia krocząca).
   Głównym celem jest zbadanie przepustowości oraz zestawienie wahań opóźnień (latency spikes)
   powodowanych przez Garbage Collector w Javie z determinizmem modelu Ownership w Rust-cie.
