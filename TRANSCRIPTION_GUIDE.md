# Przewodnik transkrypcji dla vista-scribe

Ten przewodnik wyjaśnia jak uruchomić serwer vista-scribe i użyć go do transkrypcji plików audio lub nagrywania i transkrypcji bezpośrednio z mikrofonu. Dostępne są trzy sposoby transkrypcji: skrypt `run_transcription.sh` do plików audio, skrypt `record_and_transcribe.py` do bezpośredniego nagrywania i transkrypcji, oraz skrypt `transcribe_for_ai.sh` do automatycznego wykrywania i transkrypcji wiadomości głosowych dla asystentów AI.

## TL;DR (Szybki Start)

### Metoda 1: Transkrypcja istniejącego pliku audio

```bash
# 1. Daj uprawnienia do wykonania skryptu
chmod +x run_transcription.sh

# 2. Uruchom skrypt z ścieżką do pliku audio
./run_transcription.sh ścieżka/do/pliku.mp3    # transkrybuj konkretny plik

# Jeśli nie podasz pliku, skrypt zapyta czy chcesz nagrać z mikrofonu
./run_transcription.sh                         # interaktywny wybór opcji
```

### Metoda 2: Bezpośrednie nagrywanie i transkrypcja

```bash
# 1. Daj uprawnienia do wykonania skryptu
chmod +x record_and_transcribe.py

# 2a. Uruchom nagrywanie z mikrofonu i transkrypcję (przez uv)
uv run python record_and_transcribe.py                    # nagrywaj i transkrybuj

# 2b. Lub transkrybuj istniejący plik bez formatowania (opcjonalnie)
uv run python record_and_transcribe.py ścieżka/do/pliku.mp3 --no-format

# UWAGA: Zawsze używaj "uv run python" aby mieć dostęp do zależności
```

Nowy skrypt `record_and_transcribe.py` dodatkowo:
- Kopiuje transkrypcję do schowka
- Zapisuje wynik do pliku w katalogu `outputs/`
- Automatycznie uruchamia backend jeśli nie jest uruchomiony

## Szczegółowy opis procesu transkrypcji

### 1. Przygotowanie środowiska

Skrypt najpierw sprawdza czy masz zainstalowany `uv` (nowoczesny menadżer pakietów Python) i synchronizuje środowisko:

```bash
# Synchronizacja środowiska
uv sync
```

Ta komenda zapewnia, że wszystkie wymagane zależności z `pyproject.toml` są zainstalowane w środowisku `.venv`.

### 2. Wykrywanie modeli

vista-scribe używa dwóch typów modeli MLX:

1. **Whisper** (obowiązkowy) - model do rozpoznawania mowy, konwertuje audio na tekst
2. **LLM** (opcjonalny) - model językowy do formatowania transkrypcji (interpunkcja, wielkie litery)

Skrypt automatycznie wykrywa modele w katalogu `./models/`:

```bash
# Standardowe lokalizacje
./models/whisper-large-v3-turbo    # Whisper (domyślny)
./models/bielik-4.5b-mxfp4-mlx     # LLM (domyślny)
```

MLX ma znaną specyfikę na macOS, gdzie ścieżki z `/Users/` są konwertowane na `/users/` jeśli taka ścieżka istnieje.

### 3. Uruchamianie backendu

Backend vista-scribe to serwer FastAPI, który udostępnia API do transkrypcji. Skrypt uruchamia go w tle:

```bash
# Uruchomienie backendu z właściwymi zmiennymi środowiskowymi
WHISPER_DIR="./models/whisper-large-v3-turbo" FORMAT_ENABLED="1" \
  LLM_ID="./models/bielik-4.5b-mxfp4-mlx" HOST="127.0.0.1" PORT="8237" \
  uv run python backend.py
```

Zmienne środowiskowe:
- `WHISPER_DIR` - ścieżka do modelu Whisper
- `FORMAT_ENABLED` - włącza (1) lub wyłącza (0) formatowanie LLM
- `LLM_ID` - ścieżka lub identyfikator modelu MLX-LM
- `HOST`, `PORT` - adres, na którym nasłuchuje serwer (domyślnie 127.0.0.1:8237)

### 4. Weryfikacja działania serwera

Skrypt sprawdza, czy backend działa poprawnie, wysyłając zapytanie do endpointu `/healthz`:

```bash
curl -s http://127.0.0.1:8237/healthz
# Oczekiwana odpowiedź: {"ok":true,"state":"idle"}
```

### 5. Przygotowanie pliku audio

Aby przetestować transkrypcję, potrzebny jest plik audio. Możesz:
- Podać ścieżkę jako argument do skryptu: `./run_transcription.sh ścieżka/do/pliku.mp3`
- Pozwolić skryptowi znaleźć przykładowe pliki audio w katalogu `tests/audio/`
- Użyć pliku z Voice Memos (Dyktafon) macOS

Obsługiwane formaty: WAV, MP3, M4A i inne (dzięki mlx-audio).

### 6. Wysyłanie pliku do transkrypcji

Skrypt wysyła plik audio do backendu za pomocą `curl`:

```bash
# Transkrypcja bez formatowania
curl -s -F "audio=@plik.mp3" http://127.0.0.1:8237/transcribe

# Transkrypcja z formatowaniem
curl -s -F "audio=@plik.mp3" http://127.0.0.1:8237/stt_and_format
```

### 7. Otrzymywanie i przetwarzanie wyników

Backend zwraca wynik transkrypcji w formacie JSON:

```json
{"text": "Oto transkrypcja tekstu mówionego z pliku audio."}
```

Skrypt wyodrębnia tekst z JSON-a, wyświetla go i zapisuje do pliku `.transkrypcja.txt` obok oryginalnego pliku audio.

## Jak działa vista-scribe pod spodem

### Proces transkrypcji

1. **MLX Whisper** (rozpoznawanie mowy):
   - Dekoduje plik audio do tablicy próbek
   - Dzieli audio na segmenty
   - Przeprowadza rozpoznawanie mowy dla każdego segmentu
   - Łączy wyniki w pełną transkrypcję

2. **MLX-LM** (opcjonalne formatowanie):
   - Przyjmuje surową transkrypcję (bez interpunkcji, wielkich liter)
   - Używa instrukcji systemowej do formatowania tekstu
   - Generuje sformatowaną wersję z poprawną interpunkcją i wielkimi literami
   - Zachowuje oryginalną treść, poprawiając tylko formatowanie

### Endpointy API

Backend udostępnia kilka endpointów:

- `GET /healthz` - sprawdzenie statusu serwera
- `POST /transcribe` - transkrypcja audio (tylko STT)
- `POST /format` - formatowanie tekstu (tylko LLM)
- `POST /stt_and_format` - transkrypcja + formatowanie (połączony proces)
- `POST /action` - zmiana stanu serwera (listening/idle/muted)
- `GET /events` - strumień SSE ze stanem serwera (dla widgetów)

## Rozwiązywanie problemów

### 1. Problem z uv

```
[!] Nie znaleziono 'uv'. Zainstaluj i uruchom ponownie powłokę:
  curl -LsSf https://astral.sh/uv/install.sh | sh
  exec -l $SHELL
```

### 2. Brak modeli

```
[!] Nie znaleziono modelu Whisper. Zainstaluj go najpierw:
uv run python scripts/get_models.py --whisper large-v3-turbo
```

### 3. Backend nie startuje

Sprawdź logi błędów:
```bash
cat logs/backend.err.log
```

Typowe problemy:
- Niepoprawne ścieżki do modeli
- Port 8237 jest już zajęty (sprawdź `lsof -i:8237`)
- Brak uprawnienia do zapisu do katalogów logów

### 4. Problemy z formatowaniem

Jeśli formatowanie nie działa:
- Sprawdź czy `FORMAT_ENABLED=1`
- Sprawdź czy znaleziono model LLM
- Sprawdź logi błędów w `logs/backend.err.log`

## Bezpośrednie nagrywanie z mikrofonu

Skrypt `record_and_transcribe.py` umożliwia nagrywanie bezpośrednio z mikrofonu i natychmiastową transkrypcję bez potrzeby tworzenia plików pośrednich:

### Jak działa nagrywanie

1. **Uruchomienie nagrywania**:
   ```bash
   uv run python record_and_transcribe.py
   ```

2. **Proces nagrywania**:
   - Skrypt sprawdza czy backend jest uruchomiony, a jeśli nie, uruchamia go automatycznie
   - Następnie inicjuje nagrywanie z domyślnego mikrofonu
   - Wyświetla wskaźnik nagrywania z animacją i licznikiem czasu
   - Automatycznie wykrywa ciszę i kończy nagrywanie po wykryciu pauzy w mówieniu

3. **Przetwarzanie i wyniki**:
   - Po zakończeniu nagrywania, audio jest wysyłane do backendu do transkrypcji
   - Wynik transkrypcji jest wyświetlany w terminalu
   - Tekst jest automatycznie kopiowany do schowka (można wkleić ⌘V gdzie indziej)
   - Transkrypcja jest również zapisywana do pliku w katalogu `outputs/` z timestampem

### Wskazówki dotyczące nagrywania

- Mów wyraźnie i nie za szybko
- Skrypt automatycznie zakończy nagrywanie po wykryciu około 0,8 sekundy ciszy
- Możesz przerwać nagrywanie w dowolnym momencie naciskając Ctrl+C
- Jeśli nagrywanie nie działa, sprawdź czy masz przyznane uprawnienia do mikrofonu
- Skrypt obsługuje ustawienia formatowania zgodnie z zmiennymi środowiskowymi

### Dodatkowe opcje

```bash
# Transkrypcja bez formatowania LLM (tylko Whisper)
uv run python record_and_transcribe.py --no-format

# Transkrypcja istniejącego pliku
uv run python record_and_transcribe.py ścieżka/do/pliku.mp3

# Połączenie obu opcji
uv run python record_and_transcribe.py ścieżka/do/pliku.mp3 --no-format
```

## Metoda 3: Transkrypcja wiadomości głosowych dla asystentów AI

Nowy skrypt `transcribe_for_ai.sh` został stworzony specjalnie do ułatwienia komunikacji głosowej między użytkownikami a asystentami AI:

```bash
# 1. Daj uprawnienia do wykonania skryptu (jednorazowo)
chmod +x transcribe_for_ai.sh

# 2a. Znajdź i transkrybuj najnowszą wiadomość głosową
./transcribe_for_ai.sh

# 2b. Transkrybuj konkretny plik audio
./transcribe_for_ai.sh --path /ścieżka/do/wiadomości.m4a

# 2c. Transkrybuj bez formatowania LLM
./transcribe_for_ai.sh --no-format
```

### Jak działa transkrypcja dla asystentów AI

1. **Nagrywanie wiadomości głosowej**:
   - Użyj aplikacji Voice Memos (Dyktafon) na swoim Macu
   - Nagraj wiadomość, którą chcesz przekazać asystentowi AI
   - Zapisz nagranie na pulpicie lub w katalogu projektu

2. **Uruchomienie transkrypcji**:
   - Uruchom skrypt `./transcribe_for_ai.sh`
   - Skrypt automatycznie wyszuka najnowsze nagrania głosowe w standardowych lokalizacjach
   - Jeśli nagranie nie zostanie znalezione, możesz podać jego ścieżkę ręcznie

3. **Proces transkrypcji**:
   - Skrypt uruchomi backend vista-scribe, jeśli nie jest uruchomiony
   - Wiadomość głosowa zostanie przetworzona przez lokalny model Whisper
   - Opcjonalnie, transkrypcja zostanie sformatowana przez lokalny model LLM
   - Wynik zostanie zapisany do pliku w katalogu `outputs/`

4. **Interakcja z asystentem AI**:
   - Asystent AI odczyta transkrypcję z pliku wynikowego
   - Asystent odpowie na treść twojej wiadomości głosowej
   - Cały proces odbywa się lokalnie, bez wysyłania danych do chmury

### Lokalizacje wiadomości głosowych

Skrypt szuka wiadomości głosowych w następujących lokalizacjach:

1. Pliki tymczasowe Voice Memos: `/Users/*/Library/Containers/com.apple.VoiceMemos/Data/tmp/**/message-from-user.m4a`
2. Standardowe lokalizacje Voice Memos: `~/Library/Containers/com.apple.VoiceMemos/Data/Library/Voicememos/*.m4a`
3. Popularne lokalizacje użytkownika:
   - `~/Desktop/*.m4a`
   - `~/Downloads/*.m4a`
   - Katalog projektu `*.m4a`, `*.mp3`, `*.wav`

Skrypt wybiera zawsze najnowszy (ostatnio zmodyfikowany) plik audio, chyba że podasz konkretną ścieżkę.

## Zatrzymanie backendu

Po zakończeniu transkrypcji backend nadal działa w tle. Możesz go zatrzymać:

```bash
# Zabij proces po PID
kill <PID>

# Lub znajdź procesy Python i zabij pasujący
ps aux | grep "python backend.py" | grep -v grep
kill <PID>
```

## Zaawansowane opcje

Możesz dostosować działanie skryptu przez zmienne środowiskowe:

```bash
# Wybierz model Whisper
WHISPER_VARIANT=medium ./run_transcription.sh

# Wyłącz formatowanie LLM
FORMAT_ENABLED=0 ./run_transcription.sh

# Ustaw konkretny model LLM
LLM_ID=./models/bielik-11b-mxfp4-mlx ./run_transcription.sh

# Dostosuj parametry generowania LLM
TEMPERATURE=0.1 MAX_NEW_TOKENS=256 ./run_transcription.sh
```

## Wnioski

Skrypt `run_transcription.sh` umożliwia łatwe uruchomienie backendu vista-scribe i przetestowanie transkrypcji audio. Skrypt `record_and_transcribe.py` pozwala na bezpośrednie nagrywanie z mikrofonu. Nowy skrypt `transcribe_for_ai.sh` umożliwia komunikację głosową z asystentami AI.

Dzięki użyciu modeli MLX cały proces odbywa się lokalnie, bez wysyłania danych do chmury i bez potrzeby kluczy API.

Warto zauważyć, że vista-scribe ma również aplikację w zasobniku systemowym (`main.py`), która używa tego samego silnika transkrypcji, ale dodatkowo oferuje wygodny interfejs i skróty klawiszowe.