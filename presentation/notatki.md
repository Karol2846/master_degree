# Notatki prelegenta: Java vs Rust

Czas docelowy ok. 25 min plus pytania (slot 30 min). Czasy są orientacyjne.
Liczby pochodzą z `results/parsed/*.json` i przelicza je `presentation/scripts/key_numbers.py`.
RSS podaję w MB = 1024² B, tak jak na wykresach.

| Sekcja | Slajdy | Czas | Narastająco |
|---|---|---|---|
| Wstęp | 1–4 | 3:05 | 3:05 |
| Cel, pytania badawcze, zakres | 5–7 | 2:15 | 5:20 |
| Metoda | 8–13 | 5:00 | 10:20 |
| S1 CPU | 14–16 | 1:50 | 12:10 |
| S2 I/O | 17–20 | 3:05 | 15:15 |
| S3 współbieżność | 21–25 | 4:10 | 19:25 |
| S4 pamięć | 26–29 | 3:05 | 22:30 |
| Synteza | 30–34 | 3:00 | **25:30** |

Slajd 35 (wszystkie liczby) jest po „Dziękuję” i służy do pytań.

---

## Wstęp (3:05)

**1. Tytuł (0:20)**
Dzień dobry, nazywam się Karol Mac. Przedstawię projekt, w którym porównałem Javę i Rusta na programach o identycznej funkcjonalności.
Opiekunem projektu jest dr inż. Łukasz Gałka.

**2. Pytanie do sali (0:40)**
Na początek proszę o podniesienie ręki: kto uważa, że program w Ruście jest *zawsze* szybszy od tego samego programu w Javie?
Policz ręce na głos („około połowa sali”). Wrócimy do tego na końcu.

**3. Discord (1:15)**
W 2020 roku Discord przepisał serwis „Read States” z Go na Rust. Go wymuszał garbage collection co najmniej co 2 minuty.
Ponieważ GC skanował wtedy cały duży cache, co 2 minuty pojawiały się skoki latencji i CPU. Wersja w Ruście ich nie miała.
Wykres jest schematem, nie danymi. Ważne zastrzeżenie: to był Go, nie Java. Stąd pytanie, czy to samo dotyczy Javy z nowoczesnym G1.

**4. Warunki idealne vs rzeczywistość (0:50)**
Typowy benchmark podaje średni czas, a użytkownik odczuwa ogon latencji, czyli te nieliczne wolne odpowiedzi.
Benchmark mierzy czas CPU, a firma płaci w chmurze za RAM przydzielony kontenerom.
Dlatego mierzyłem nie tylko czas, ale też pamięć w czasie, pauzy GC i rozkład latencji.

## Cel, pytania badawcze, zakres (2:15)

**5. Cel pracy (0:45)**
Problem: wybór języka często opiera się na przekonaniach, a brakuje porównań identycznych programów w różnych typach obciążeń.
Cel: zmierzyć, jak Java 25 i Rust różnią się czasem, pamięcią, wpływem GC i skalowalnością w czterech scenariuszach.

**6. Pytania badawcze (1:00)**
Problem rozkładam na cztery pytania; pod każdym szarym napisem jest miara, którą na nie odpowiadam.
1, czas: jak duża jest różnica czasu wykonania i od czego zależy? Porównuję stosunek T_Java / T_Rust w S1–S4.
2, pamięć: ile pamięci zajmuje każdy język i jak zmienia się ona w czasie? Szczytowy RSS i przebieg RSS w czasie.
3, GC: czy pauzy GC są widoczne w latencji, a jeśli tak, to w której części rozkładu? Percentyle latencji zdarzenia w S4 i liczba zdarzeń w ogonie.
4, współbieżność: jak oba języki skalują się wraz z liczbą wątków? Przyspieszenie S(P) i efektywność E(P) w S3 dla 1–12 wątków.

**7. Zakres pracy (0:30)**
Najpierw problem i pytania badawcze, potem implementacja 4 scenariuszy w obu językach (tylko biblioteki standardowe).
Następnie pipeline pomiarowy w Pythonie, pomiary oraz analiza.

## Metoda (5:00)

**8. Dwa modele wykonania (1:00)**
Java kompiluje się do bytecode'u, który wykonuje środowisko uruchomieniowe, czyli JVM: najpierw interpretuje, a gorące fragmenty kompiluje JIT-em (C1, potem C2). Pamięć zwalnia G1 GC.
Rust kompiluje się przez LLVM do natywnego pliku wykonywalnego. Pamięć zwalnia się deterministycznie, gdy właściciel wychodzi ze scope'u (`Drop`).
To dwa skrajne modele zarządzania pamięcią, oba używane w backendzie, i dlatego wybrałem tę parę.

**9. 4 scenariusze (0:50)**
S1 to czyste obliczenia CPU (Mandelbrot), S2 to masowe I/O z parsowaniem (CSV 50 mln wierszy).
S3 to współbieżność (symulacja dynamiki molekularnej na P wątkach z barierą), a S4 to strumień miliarda zdarzeń IoT, gdzie patrzymy na RAM i ogon latencji.

**10. Dane wejściowe (0:40)**
Dane generują skrypty w Pythonie ze stałym seedem 42, więc oba języki dostają identyczne wejście.
S3 używa parametrów benchmarku Lennarda-Jonesa z LAMMPS: gęstość 0,8442, temperatura 1,44, cutoff 2,5.

**11. Projekt eksperymentu (1:10)**
Dla każdej pary scenariusz × język: hyperfine z 3 rozgrzewkami i 10 pomiarami, monitor RSS co 10 ms w 5 przebiegach oraz log GC Javy.
S3 mierzyłem dla 7 liczb wątków i 2 rozmiarów układu. Oba języki mają ten sam algorytm, idiomatyczny kod i domyślne flagi.
Poprawność: w S3 automatyczna walidacja (zgodność pozycji Java–Rust, dryf energii, niezależność od P); w S2 oba programy dały identyczne pliki wynikowe.

**12. Metryki (0:50)**
Czas to mediana z hyperfine. Szczytowy RSS mówi, ile RAM-u proces zabrał systemowi. Mierzę RSS, a nie heap, bo to widzi system i za to się płaci.
p99 oznacza, że 99% zdarzeń jest szybszych niż ta wartość. S(P) to przyspieszenie na P wątkach, a E(P) to efektywność, idealnie 1.

**13. Środowisko (0:30)**
Ryzen 5 7500X3D (6 rdzeni, 12 wątków), 32 GB RAM, Windows 11. OpenJDK 25.0.2 z G1 i Rust 1.98 w trybie release.

## S1: CPU (1:50)

**14. Mandelbrot (0:30)**
4096 na 4096 pikseli, do 1000 iteracji na piksel, czyste obliczenia zmiennoprzecinkowe. Tutaj spotykają się JIT Javy i LLVM.

**15. Pytanie (0:20)**
O ile szybszy jest Rust? A: 2×, B: 30%, C: 6%. Ręce w górę przy A, potem B, potem C.

**16. Wynik (1:00)**
Odpowiedź C: około 6%, czyli 5,69 vs 5,38 s. W czystych obliczeniach JIT jest prawie tak dobry jak kod natywny.
Za to pamięć: JVM od startu zajmuje około 88 MB, a Rust rośnie razem z buforem obrazu. Szczyt to 138 vs 52 MB.

## S2: I/O (3:05)

**17. Filtrowanie CSV (0:40)**
Plik ma 50 mln transakcji, około 5 GB (dokładnie 4,7 GB). Pierwszy przebieg wczytuje wszystkie kwoty, sortuje je i wyznacza próg górnego 1%.
Drugi przebieg filtruje i zapisuje wiersze powyżej progu.

**18. Pytanie (0:20)**
Ile razy szybciej Rust przefiltruje ten plik? A: 1,1×, B: 2×, C: 10×. Ręce.

**19. Wynik (1:15)**
Odpowiedź B: dwa razy szybciej, 21,8 vs 10,8 s. Parsowanie tworzy w Javie masę krótkożyjących obiektów.
Najlepiej widać tu różnicę modeli pamięci. Java rośnie schodkami: G1 dokłada regiony sterty i nie oddaje ich systemowi.
Rust rysuje trójkąt: wektor kwot rośnie, a po wyznaczeniu progu `Drop` zwalnia go natychmiast. Szczyt to 2068 vs 485 MB, czyli ×4,3.

**20. Pauzy GC (0:50)**
W całym przebiegu jest 134 pauzy, wszystkie typu Young, z medianą 0,58 ms i maksimum 1,4 ms. Łącznie 81 ms, czyli około 0,4% czasu.
Widoczna przerwa około 3,5 s to sortowanie tablicy `double[]`: działa w miejscu i nic nie alokuje, więc GC nie ma czego sprzątać.
Czyli w S2 GC nie jest wąskim gardłem. Różnica czasu wynika z parsowania i alokacji, a nie z samych pauz.

## S3: współbieżność (4:10)

**21. Dynamika molekularna (0:50)**
Symuluję 108 tysięcy cząstek Lennarda-Jonesa. Na obrazkach mały przebieg z 4 tysiącami: kryształ topi się i przechodzi w ciecz.
Każdy krok ma 4 fazy z barierą po każdej. Budowa siatki komórek jest szeregowa, a reszta działa na P wątkach.

**22. Pytanie (0:20)**
Który język lepiej skaluje się na 12 wątkach? A: Java, B: Rust, C: remis. Ręce.

**23. Wynik (1:20)**
Remis: przyspieszenie na 12 wątkach to 6,8 vs 6,9. Do 6 wątków jest prawie liniowo, z efektywnością 84–88%.
P=8 jest gorsze niż P=6 w obu językach: 8 wątków na 6 rdzeniach dzieli się nierówno, a bariera czeka na najwolniejszy.
Powyżej 6 wątków ogranicza sprzęt: 6 rdzeni fizycznych, SMT dokłada mało (szczegóły z Amdahlem: pytanie 6).

**24. Gdzie idzie czas kroku? (0:40)**
Rozbicie kroku na 4 fazy, mediana na krok, z czekaniem na barierze. Prawie cały czas to faza sił C: 190 vs 139 ms przy jednym wątku.
Część szeregowa B to 0,3–0,5%, na wykresie jej nie widać. Słupki Javy są przy każdym P około 1,4× wyższe.
Wniosek: język nie zmienia skalowania, tylko punkt startu.

**25. Czas kroku (1:00)**
Spodziewałem się, że pauza GC w jednym wątku przez barierę zatrzyma wszystkie i wydłuży ogon czasu kroku. Tak się nie stało.
W pętli są tylko 2 pauzy po około 1,4 ms na 200 kroków po około 39 ms, a skoki czasu kroku Javy nie pokrywają się z pauzami.
Java jest wolniejsza równomiernie (mediana 39 vs 27,5 ms). Najprawdopodobniej wynika to z układu danych: tablica referencji do obiektów i boxing w listach komórek oznaczają skoki po pamięci.
Uczciwie: nie używałem profilera, więc to interpretacja wsparta tym, że różnica siedzi w fazie liczenia sił.

## S4: pamięć / IoT (3:05)

**26. Strumień IoT (0:40)**
Każde zdarzenie to 20-bajtowy rekord: znacznik czasu, id sensora i wartość. Mamy miliard zdarzeń z 1000 sensorów, 2% to anomalie.
Dla każdego zdarzenia: (1) czytam rekord, (2) znajduję stan sensora w mapie, czyli okno ostatnich 128 wartości,
(3) aktualizuję kroczącą średnią i odchylenie okna, (4) jeśli wartość odbiega od średniej o więcej niż 3σ, to anomalia.
Latencja zdarzenia to czas kroków 1–4, mierzony dla każdego z miliarda zdarzeń. Cały stan to ok. 1000 × 128 liczb, czyli ~1 MB.

**27. Pytanie (0:20)**
Ile razy więcej RAM zużyje Java? A: 1,5×, B: 5×, C: 50×. Ręce.

**28. Wynik (0:50)**
Odpowiedź C, a nawet więcej: ×54. Java zajmuje 351 MB, Rust 6,5 MB. Stan programu jest malutki, więc w Javie widać prawie sam narzut JVM i sterty.
Java rośnie schodkami do plateau i tam zostaje, a Rust ma płaską linię. Czas różni się niewiele: Java ×1,09.

**29. Latencja (1:15)**
Tu szukam efektu Discorda. Percentyle od p50 do p99.9 są identyczne w obu językach (0,2 i 0,4 µs).
Max nie jest dowodem: to pojedyncze zdarzenie i w Ruście jest nawet wyższe. To szum schedulera systemu.
Prawy wykres liczy zdarzenia w ogonie: ile z miliarda trwało co najmniej 0,1, 0,4 i 0,8 ms. Powyżej 0,4 ms Java ma 97, a Rust 11.
Kiedy G1 robi pauzę, zdarzenie, które akurat jest przetwarzane, czeka razem z nią, więc jego latencja to ~czas pauzy.
Pauz było 146 po średnio 0,52 ms (linia przerywana), a nadwyżka Javy w ogonie to podobny rząd: ponad 0,1 ms 129 zdarzeń więcej, ponad 0,4 ms 86 więcej.
Rust też ma kilkadziesiąt wolnych zdarzeń: to tło systemu (wywłaszczenia, przerwania), obecne w obu językach.
GC kosztuje, ale w naszych warunkach to nie Discord.

## Synteza (3:00)

**30. Zbiorczo (0:40)**
Czas różni się od 6% do dwóch razy, a pamięć od ×2,7 do ×54, na skali logarytmicznej. Pamięć różnicuje języki dużo mocniej niż czas.

**31. Odpowiedzi (0:50)**
Czas: Rust był szybszy w każdym scenariuszu, ale skala zależy od obciążenia: od 6% w obliczeniach do 2× przy masowym I/O.
Pamięć: tu różnica jest największa, od ×2,7 do ×54.
GC: typowa latencja jest identyczna, pauzy widać tylko w skrajnym ogonie i ilościowo to mały efekt.
Współbieżność: oba języki skalują się praktycznie tak samo, różnica przyspieszeń nie przekracza 4%.

**32. Wnioski (1:10)**
Wracając do pytania z początku: Rust był szybszy zawsze, ale od 6% do 2×. Pamięć to od ×2,7 do ×54.
Rusta wybrałbym tam, gdzie liczy się pamięć i gęstość (kontenery, embedded, krótkie narzędzia CLI), przy masowym I/O i gdy ogon latencji musi być przewidywalny.
Javę tam, gdzie dominują obliczenia (w S1 JIT tracił tylko 6%), a liczy się ekosystem i koszt zespołu. Ogony GC są realne, ale małe.
Ograniczenia: jedna maszyna z Windowsem, domyślne flagi GC, kod idiomatyczny bez ręcznych optymalizacji.

**33. Źródła (0:10)**
Źródła są na slajdzie.

**34. Dziękuję (0:10)**
Dziękuję za uwagę, chętnie odpowiem na pytania.

---

## Przewidywane pytania

**1. Dlaczego nie ZGC lub Shenandoah?**
Domyślny G1 to „dobry przypadek” Javy, czyli to, co dostaje większość aplikacji bez strojenia. W żadnym scenariuszu nie było Full GC, tylko pauzy Young.
Inne kolektory to inne kompromisy: ZGC ma krótsze pauzy kosztem CPU i pamięci, a zwrot pamięci do systemu dają `ZUncommit` czy `G1PeriodicGCInterval`. To dobry kierunek dalszej pracy.

**2. Dlaczego P=8 jest gorsze niż P=6?**
8 wątków na 6 rdzeniach fizycznych: dwa rdzenie obsługują po dwa wątki przez SMT i liczą wolniej. Bariera czeka na najwolniejszy wątek, więc cały krok zwalnia (S(8) ≈ 5,0 vs S(6) ≈ 5,1–5,3).

**3. Czy kod Javy nie był celowo gorszy?**
Nie: ten sam algorytm i te same dane, idiomatyczny kod w obu językach, tylko biblioteki standardowe, domyślne flagi.
S3 przechodzi automatyczną walidację zgodności wyników Java–Rust (pozycje < 10⁻⁶), a w S2 pliki wynikowe były identyczne.

**4. Dlaczego RSS, a nie heap used?**
RSS to pamięć fizyczna, którą system przydzielił procesowi, czyli to, co liczy limit kontenera i rachunek w chmurze.
Heap used pomija narzut JVM (metaspace, kod JIT, wątki) i regiony zajęte, ale niezwolnione do systemu.

**5. Dlaczego w S4 Rust ma wyższy max niż Java?**
Max to pojedyncze zdarzenie z miliarda, które zależy od schedulera Windowsa (np. wywłaszczenie wątku), a nie od języka.
Dlatego porównuję liczbę zdarzeń w ogonie: > 0,4 ms Java 97 vs Rust 11.

**6. Skoro część szeregowa jest znikoma, dlaczego tylko ~6,9×?**
Amdahl uwzględnia tylko część szeregową (s ≈ 0,003–0,005) i przewiduje ~11,5×. Ograniczenie jest sprzętowe:
6 rdzeni fizycznych, SMT współdzieli jednostki wykonawcze i cache, więc wątki 7–12 dokładają mało. Do tego dochodzi przepustowość pamięci.

**7. Skąd wiadomo, że różnica w S3 to układ danych, a nie GC?**
W pętli są tylko 2 pauzy po ~1,4 ms, a skoki czasu kroku się z nimi nie pokrywają. Java jest wolniejsza równomiernie w każdym kroku.
Różnica siedzi w fazie liczenia sił (190 vs 139 ms przy P=1). Uczciwie: nie było profilera, więc mówię „najprawdopodobniej”.
