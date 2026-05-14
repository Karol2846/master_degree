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
3. Współbierzność: równoległe przetwarzanie obliczeń.
   Symulacja w której równolegle jest liczone kilka rzeczy dla jednego wyniku - np. symulacja 5000 cząstek, które muszę ze sobą reagować.
4. **Zarządzanie pamięcią**: Działający w pamięci silnik przetwarzania strumieniowego (symulacja IoT).
   Odbiór milionów zdarzeń, filtrowanie anomalii i agregacja (średnia krocząca).
   Głównym celem jest zbadanie przepustowości oraz zestawienie wahań opóźnień (latency spikes)
   powodowanych przez Garbage Collector w Javie z determinizmem modelu Ownership w Rust-cie.
