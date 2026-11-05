# Notatki na obronę: Java vs Rust (~5 min)

Deck: `presentation/obrona.html` → `presentation/obrona.pdf` (`presentation/scripts/build.sh obrona.html`).
Układ wg wytycznych prowadzącego (`wytyczne.pdf`), skrócony do 5 minut: metodyka, dyskusja i wnioski mają po 1 slajdzie, bez hipotez.
Liczby jak w pełnej prezentacji (`notatki.md`, `assets/numbers.json`).

| Slajd | Co                          | Czas | Narastająco |
|-------|-----------------------------|------|-------------|
| 1     | Tytuł                       | 0:10 | 0:10        |
| 2     | Motywacja: AWS Aurora DSQL  | 0:35 | 0:45        |
| 3     | Cel i zakres pracy          | 0:30 | 1:15        |
| 4     | Metodyka badań              | 0:35 | 1:50        |
| 5     | Aplikacja autorska          | 0:25 | 2:15        |
| 6     | Wyniki: czas i pamięć       | 0:35 | 2:50        |
| 7     | Wyniki: GC i latencja       | 0:35 | 3:25        |
| 8     | Dyskusja                    | 0:45 | 4:10        |
| 9     | Wnioski                     | 0:30 | 4:40        |
| 10    | Bibliografia                | 0:05 | 4:45        |
| 11    | Dziękuję za uwagę           | 0:05 | **4:50**    |

Slajdy zapasowe (po „Dziękuję”, na pytania): 12 skalowanie S3 z krzywą Amdahla, 13 wszystkie liczby.

---

**1. Tytuł (0:10)**
Dzień dobry, nazywam się Karol Mac. Moja praca porównuje Javę i Rusta na programach o identycznej funkcjonalności. Promotorem jest dr inż. Łukasz Gałka.

**2. Motywacja (0:35)**
Amazon w bazie Aurora DSQL miał komponent Adjudicator napisany w Kotlinie, czyli na JVM. Po latach strojenia robił 3 tysiące transakcji na sekundę.
Programiści Javy przepisali go w Ruście i pierwsza wersja robiła 30 tysięcy, dziesięć razy więcej. Zespół wskazywał pauzy GC jako problem.
To jeden komponent i jeden zespół. Ja sprawdziłem, ile wynosi różnica na zwykłych, identycznych programach.

**3. Cel i zakres (0:30)**
Celem było zmierzenie, jak Java 25 i Rust różnią się czasem, pamięcią, wpływem GC i skalowalnością.
Przygotowałem 4 scenariusze: obliczenia, I/O, wątki i strumień miliarda zdarzeń IoT. Każdy w obu językach, tylko na bibliotekach standardowych.

**4. Metodyka (0:35)**
Czas mierzy hyperfine, a porównuję medianę. Pamięć RSS próbkuję co 10 ms w 5 przebiegach. Pauzy GC biorę z logu JVM, a latencję mierzę dla każdego zdarzenia.
Wszystko na jednej maszynie: Ryzen z 6 rdzeniami, Windows 11, JDK 25 i Rust 1.98. Ten sam algorytm i dane, a skrypt sprawdza zgodność wyników.

**5. Aplikacja autorska (0:25)**
Pipeline w Pythonie prowadzi cały eksperyment, od generowania danych po wykresy. Na dole ta sama pętla pomiaru latencji w obu językach.

**6. Czas i pamięć (0:35)**
Rust był szybszy w każdym scenariuszu, od 6% do dwóch razy. W pamięci różnice są dużo większe: Java zajmuje od 2,7 do 54 razy więcej.

**7. GC i latencja (0:35)**
Percentyle od p50 do p99,9 są identyczne. GC widać dopiero w skrajnym ogonie: powyżej 0,4 ms Java ma 97 zdarzeń na miliard, a Rust 11.

**8. Dyskusja (0:45)**
Pamięć: JVM ma stały narzut, a G1 nie oddaje sterty systemowi. W S4 stan programu to 1 MB, więc widać prawie sam narzut.
W S1 JIT generuje kod prawie tak dobry jak LLVM. W S2 kosztują alokacje przy parsowaniu, nie same pauzy.
Skalowanie jest w obu językach takie samo, ogranicza je 6 rdzeni fizycznych. Spodziewałem się wpływu GC na wątki w S3, ale go nie było.

**9. Wnioski (0:30)**
Na zwykłych programach różnica czasu to od 6% do 2×, a nie 10×. Języki różnią się przede wszystkim pamięcią.
Rust, gdy liczy się RAM i przy masowym I/O. Java w obliczeniach i tam, gdzie ważniejszy jest ekosystem. Ograniczenia: jedna maszyna, domyślny G1, kod idiomatyczny.

**10. Bibliografia (0:05)**
Najważniejsze źródła są na slajdzie.

**11. Koniec (0:05)**
Dziękuję za uwagę.

---

## Przewidywane pytania (skrót; pełne odpowiedzi w `notatki.md`)

- **Dlaczego G1, a nie ZGC/Shenandoah?**
  - G1 jest domyślny, czyli to, co dostaje większość aplikacji. Nie było żadnego Full GC.
  - ZGC daje krótsze pauzy kosztem CPU i RAM-u. To temat na dalsze badania.
- **Czy kod Javy nie był celowo gorszy?**
  - Ten sam algorytm i dane, kod idiomatyczny, domyślne flagi.
  - S3: pozycje Java ↔ Rust zgodne do 10⁻⁶; S2: identyczne pliki wynikowe.
- **Dlaczego RSS, a nie heap?**
  - RSS to pamięć, którą widzi system. Na jej podstawie działa limit kontenera i rachunek w chmurze.
- **Skąd tylko ×6,9 na 12 wątkach, skoro część szeregowa to ~0,4%?**
  - Amdahl daje ~11,5×. Limit jest sprzętowy: 6 rdzeni fizycznych, SMT dokłada mało.
- **Dlaczego P = 8 jest gorsze niż P = 6?**
  - 8 wątków na 6 rdzeniach. Bariera czeka na najwolniejszy wątek.
- **Dlaczego w S4 Rust ma wyższe max?**
  - Max to jedno zdarzenie z miliarda, czyli szum schedulera. Dlatego porównuję liczbę zdarzeń w ogonie.
- **Czy GC w Javie to realny problem na produkcji?**
  - Discord (2023): w Cassandrze (Java) pauzy GC powodowały skoki latencji, węzły trzeba było ręcznie restartować. Po przejściu na ScyllaDB (C++) p99 odczytu spadło z 40–125 ms do 15 ms.
  - Źródło: B. Ingram, „How Discord Stores Trillions of Messages”, Discord Blog, 6.03.2023.
  - W moich pomiarach sterta miała ~350 MB, a pauzy G1 ~0,5 ms. Baza z bilionami wiadomości to inna skala.
- **Skąd u AWS 10×, a u mnie najwyżej 2×?**
  - Na Lobsters członek zespołu DSQL tłumaczył dużą część różnicy innym wzorcem alokacji i kopiowania w idiomatycznej Javie i idiomatycznym Ruście. Twierdził też, że ekspert od JVM zmniejszyłby ją kodem mniej idiomatycznym.
  - Adjudicator to rozproszony system pod dużą współbieżnością, gdzie pauza na jednym hoście opóźnia całą transakcję. Moje scenariusze działają na jednej maszynie.
  - Sam Vogels pisze, że JDK 21 wystarcza dla wielu serwisów, a Rust ma sens tam, gdzie tail latency jest krytyczne.
- **Inne przepisania z Javy na Rusta?**
  - Datadog (2024): analizator statyczny kodu, 3× szybciej i 10× mniej pamięci. Przy okazji wymienili parser i silnik reguł, więc to też nie jest czysty efekt języka.
  - Źródło: J. Delange, K. Qian, R. Trieu, „How we migrated our static analyzer from Java to Rust”, Datadog Engineering Blog, 23.05.2024.
- **Czy korzystałeś z narzędzi AI?** (`research.md`, `implementation.times.md`)
  - Przygotuj odpowiedź: co generowało AI (kod implementacji), a co jest Twoje (projekt scenariuszy i eksperymentu, metryki, pipeline, walidacja, analiza, interpretacja).
