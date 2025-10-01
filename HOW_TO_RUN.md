# Jak uruchomić vista-scribe (przewodnik uruchamiania)

## TL;DR - Szybki start

```bash
# Z repo root (najprostszy sposób):
chmod +x scripts/quickstart_mac.sh
./scripts/quickstart_mac.sh

# Lub uruchom backend i tray osobno (dla deweloperów):
# Terminal 1:
FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo uv run python backend.py

# Terminal 2:
FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo uv run python main.py
```

## Metoda 1: Skrypt quickstart_mac.sh

Zaktualizowany skrypt quickstart_mac.sh automatycznie:
1. Synchronizuje środowisko (uv sync)
2. Aktywuje środowisko (.venv)
3. Pobiera modele (jeśli nie istnieją)
4. Autodektuje ścieżki LLM (jeśli FORMAT_ENABLED=1)
5. Uruchamia aplikację w trybie tray lub backend

Opcje wywołania:

```bash
# Domyślnie (tray app, Whisper large-v3-turbo):
./scripts/quickstart_mac.sh

# Uruchom backend API:
MODE=backend ./scripts/quickstart_mac.sh

# Określony model Whisper:
WHISPER_VARIANT=medium ./scripts/quickstart_mac.sh

# Z formatowaniem wyłączonym (tylko STT):
FORMAT_ENABLED=0 ./scripts/quickstart_mac.sh

# Z konkretnym LLM:
LLM_ID=/users/you/models/bielik-4.5b-mxfp4-mlx ./scripts/quickstart_mac.sh
```

## Metoda 2: Konfiguracje IDE (JetBrains)

W projekcie skonfigurowano gotowe konfiguracje Run/Debug w katalogu `.run`:
1. `Vista Scribe — Backend (uv)` - uruchamia backend API na http://127.0.0.1:8237
2. `Vista Scribe — Tray (uv)` - uruchamia aplikację w zasobniku systemowym (menubar)
3. `Vista Scribe — Tests (uv)` - uruchamia testy
4. `Vista Scribe — Full stack test (uv)` - wykonuje test pełnego przetwarzania
5. `Ruff — check/format (uvx)` - linter/formatter

Aby użyć:
1. Otwórz projekt w PyCharm/IntelliJ
2. Przejdź do Run → Edit Configurations
3. Znajdź powyższe konfiguracje w sekcji "Shared"
4. Uruchom "Vista Scribe — Backend (uv)" i "Vista Scribe — Tray (uv)"

## Metoda 3: Ręczne uruchomienie w terminalu

```bash
# 1. Synchronizuj środowisko
uv sync

# 2. Aktywuj środowisko (opcjonalne)
source .venv/bin/activate

# 3. Uruchom backend (w jednym terminalu)
FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo uv run python backend.py

# 4. Uruchom tray (w drugim terminalu)
FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo uv run python main.py
```

## Zmienne środowiskowe (opcjonalne)

- `WHISPER_VARIANT=large-v3-turbo` - wariant modelu Whisper (large-v3-turbo lub medium)
- `WHISPER_DIR=/sciezka/do/whisper-modelu` - bezpośrednia ścieżka do modelu Whisper
- `FORMAT_ENABLED=1` - włącz (1) lub wyłącz (0) formatowanie transkrypcji
- `LLM_ID=/sciezka/lub/repo/id` - model MLX-LM do formatowania
- `HOST=127.0.0.1` - host dla backendu
- `PORT=8237` - port dla backendu
- `TRAY_ICON=/sciezka/do/icon.png` - opcjonalna ikona zasobnika

Domyślne ścieżki modeli:
- Whisper: `./models/whisper-large-v3-turbo`
- LLM: `./models/bielik-4.5b-mxfp4-mlx`

## Uruchamianie w trybie background (nohup)

Aby uruchomić aplikację w tle (odporną na zamknięcie terminala):

```bash
# Backend w tle z przekierowaniem logów
nohup FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo uv run python backend.py > logs/backend.out.log 2> logs/backend.err.log &

# Tray app w tle z przekierowaniem logów (i ustawieniem NOHUP_MODE)
nohup NOHUP_MODE=1 FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo uv run python main.py > logs/tray.out.log 2> logs/tray.err.log &

# Sprawdź czy procesy działają
ps aux | grep "python" | grep -E "backend|main"

# Sprawdź logi:
tail -f logs/backend.err.log
tail -f logs/tray.err.log
```

**Uwaga o trybie nohup**: W trybie background, aplikacja:
- Nie wyświetla okien dialogowych wymagających interakcji
- Automatycznie wykrywa brak uprawnień Accessibility i kontynuuje działanie
- Loguje wszystkie komunikaty do plików
- Uwalnia zasoby poprawnie przy błędach inicjalizacji

## Uprawnienia dostępu do klawiatury (Accessibility)

Aplikacja wymaga uprawnień dostępu do klawiatury, aby monitorować skróty klawiszowe:

1. **Przy pierwszym uruchomieniu**:
   - macOS wyświetli prośbę o dostęp do monitorowania wejścia
   - Wybierz "Otwórz ustawienia prywatności" lub przejdź do Ustawień systemowych

2. **Ręczne włączenie uprawnień**:
   - System Settings → Privacy & Security → Accessibility
   - Włącz przełącznik obok "python" lub nazwy aplikacji
   - Po włączeniu, uruchom ponownie aplikację lub wybierz "Enable Hotkeys" z menu

3. **Gdy uprawnienia nie są przyznane**:
   - Aplikacja nadal działa, ale bez skrótów klawiszowych
   - W menu zasobnika pojawi się status "Hotkeys Disabled" z ikoną 🚫
   - Możesz włączyć skróty później przez menu "Enable Hotkeys"

**Najważniejsze skróty (gdy włączone)**:
- Podwójny Option (⌥⌥) – start/stop nagrywania
- Shift+Command+/ (⇧⌘/) – start/stop nagrywania
- Przytrzymaj Control – mów podczas trzymania, zwolnij aby zakończyć

## Rozwiązywanie problemów

1. **Aplikacja się nie uruchamia:**
   - Sprawdź czy `uv` jest zainstalowane: `which uv`
   - Wykonaj `uv sync` aby zaktualizować środowisko

2. **Modele nie są wykrywane:**
   - Sprawdź katalog `models/` czy zawiera podfoldery z modelami
   - Wykonaj `uv run python scripts/get_models.py --whisper large-v3-turbo`

3. **Backend nie odpowiada:**
   - Sprawdź healthcheck: `curl -s http://127.0.0.1:8237/healthz`
   - Zobacz logi: `cat logs/backend.err.log`

4. **Problemy z nagrywaniem/wklejaniem:**
   - Sprawdź uprawnienia macOS: System Settings → Privacy & Security
     • Microphone (Terminal/Python)
     • Accessibility (Terminal/Python)
     • Input Monitoring (Terminal/Python)

5. **Skróty klawiszowe nie działają:**
   - Sprawdź logi: `tail -f logs/tray.err.log`
   - Zobacz komunikat "Failed to create event tap" lub "Event tap stopped"
   - Nadaj uprawnienia Accessibility jak opisano powyżej
   - Uruchom ponownie lub użyj "Enable Hotkeys" z menu

6. **Ścieżki modeli z /Users:**
   - MLX może mieć problem z ścieżkami zawierającymi /Users
   - Użyj wersji /users/ jeśli dostępna, np.: 
     `/users/twojlogin/...` zamiast `/Users/twojlogin/...`

## Healthcheck i diagnostyka

```bash
# Sprawdź czy backend działa
curl -s http://127.0.0.1:8237/healthz | jq

# Sprawdź logi
cat logs/backend.err.log

# Test pełnego przetwarzania:
uv run python full_stack_test.py sciezka/do/pliku.mp3 --lang pl
```