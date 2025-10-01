# Checklist uruchomienia i debugowania — vista-scribe

Ostatnia aktualizacja: 2025-10-01

TL;DR
- uv sync && source .venv/bin/activate
- [opcjonalnie] Pobierz modele: uv run python scripts/get_models.py --whisper large-v3-turbo
- Backend (szybki start): uruchom Run/Debug „Vista Scribe — Backend (FastAPI)”
- Tray (menubar): uruchom Run/Debug „Vista Scribe — Tray App (main.py)”
- Testy: Run/Debug „Vista Scribe — Tests (pytest)” lub: uv run pytest -q
- Healthcheck: curl -s http://127.0.0.1:8237/healthz | jq

1. Przygotowanie środowiska
- Wymagany Python 3.12. 
- Zainstaluj zależności: 
  - uv sync && source .venv/bin/activate
- Modele (lokalnie, MLX):
  - Whisper (domyślnie): uv run python scripts/get_models.py --whisper large-v3-turbo
  - Alternatywnie: uv run python scripts/get_models.py --whisper medium
  - Opcjonalny LLM do formatowania: uv run python scripts/get_models.py --llm mlx-community/Llama-3.2-3B-Instruct-4bit

2. Run/Debug (JetBrains)
- Nowe, uniwersalne konfiguracje są w katalogu .run/ i uruchamiają wszystko przez uv/uvx (zero „dziwnego” Pythona).
- W IDE znajdziesz je jako Shared (Run → Edit Configurations). Najpierw: `uv sync`.
- Dołączone konfiguracje (.run):
  - „Vista Scribe — Backend (uv)” — `uv run python backend.py` (HOST=127.0.0.1, PORT=8237, LOG_LEVEL=INFO, FORMAT_ENABLED=1, WHISPER_VARIANT=large-v3-turbo)
  - „Vista Scribe — Tray (uv)” — `uv run python main.py`
  - „Vista Scribe — Tests (uv)” — `uv run pytest -q`
  - „Vista Scribe — Full stack test (uv)” — `uv run python full_stack_test.py assets/test_files/... --lang pl`
  - „Ruff — check (uvx)” i „Ruff — format (uvx)” — `uvx ruff check .` / `uvx ruff format .`
- Stare konfiguracje w .idea/runConfigurations/ zostawiamy jako fallback (też działają na .venv).

3. Szybkie komendy (terminal)
- Lint + format:
  - uv run ruff format .
  - uv run ruff check .
- Testy:
  - uv run pytest -q
- Backend w foreground (ręcznie):
  - export HOST=127.0.0.1 PORT=8237 LOG_LEVEL=INFO
  - export FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo
  - uv run python backend.py
  - lub w jednej linii (tylko dla tej komendy):
    - FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo uv run python backend.py
- Tray (menubar):
  - uv run python main.py
  - lub w jednej linii (tylko dla tej komendy):
    - FORMAT_ENABLED=1 WHISPER_VARIANT=large-v3-turbo uv run python main.py

4. Integracje (Finder Quick Action / LaunchAgent)
- Quick Action: w Automator → „Run Shell Script” → /users/.../vista-scribe/scripts/quick_action_backend.sh "$@"
- LaunchAgent backend: sh packaging/scripts/install_backend.command
- Logi backend (LaunchAgent): /tmp/vista-scribe.backend.{out,err}.log

5. Healthcheck i logi
- Health: curl -s http://127.0.0.1:8237/healthz | jq
- Logi lokalne: konsola (run configs) lub logs/backend.{out,err}.log przy quick_start

6. Zmienne środowiskowe (ważne)
- Whisper: WHISPER_VARIANT=large-v3-turbo (albo medium) lub WHISPER_DIR=/users/.../models/whisper-large-v3-turbo
- Formatowanie: FORMAT_ENABLED=1, LLM_ID=/users/.../models/bielik-4.5b-mxfp4-mlx (lub id z HF MLX)
- Dodatkowe: DOUBLE_OPTION_INTERVAL_MS=350, TRAY_ICON opcjonalne (domyślnie assets/icon.png; ścieżki /Users→/users normalizujemy gdy to możliwe)

7. Rozwiązywanie problemów
- Brak dźwięku/nagrania: sprawdź uprawnienia macOS (Microphone, Accessibility, Input Monitoring).
- Ścieżki MLX: preferuj /users/... (niektóre narzędzia MLX nie lubią wielkiej litery „U”).
- Gdy coś „szaleje” w edytorze: odpal Run/Debug jeszcze raz, sprawdź zmienne ENV w konfiguracji i logi.

8. Następne kroki (aktualizacje zależności)
- Mamy raport: dependency-audit-2025-10-01.md.
- Opcja A (zalecana): podbić wszystkie patch/minor i uruchomić testy.
- Opcja B: wskaż konkretne paczki do aktualizacji.
- Po akceptacji: zaktualizujemy pyproject/requirements, odświeżymy uv.lock, uruchomimy testy i lint.

9. Pełna ścieżka diagnostyczna
1) curl -s http://127.0.0.1:8237/healthz | jq
2) launchctl list | grep vista-scribe (jeśli LaunchAgent)
3) ENV: WHISPER_DIR/WHISPER_VARIANT, FORMAT_ENABLED, LLM_ID
4) Uprawnienia macOS
5) Logi: /tmp/vista-scribe.backend.err.log
6) Wyłącz formatowanie (FORMAT_ENABLED=0) aby odizolować STT

Uwagi
- Zobacz także .junie/guideliness.md (styl pracy, domyślne modele, prompt, hotkeys).