# vista-scribe (project description)

Local-first speech-to-text for macOS with an always-on tray app and an optional background server. No API keys required. Uses MLX Whisper for transcription and, optionally, a small local MLX-LM for punctuation/capitalization.

This document replaces the older root-level PROJECT_DESCRIPTION.md and avoids any ANSI/emoji characters for maximum portability. The original file has been relocated under docs/.

## What it does (plain English)

- You press a global hotkey (double-tap Option by default) to start/stop recording.
- The app records audio from the microphone and stops on silence (or when you stop it).
- The audio is transcribed locally with MLX Whisper.
- Optional: a small local LLM "cleans up" the transcript (punctuation and capitalization).
- The result is copied to the clipboard and pasted into the active application.

## Why local-first

- Privacy: audio and text stay on your Mac.
- Speed: models are kept in memory, so there is no cold start when using the background server.
- Offline-friendly: works without network connectivity once models are downloaded.

## Components

- Menu-bar tray app (Python, rumps/Quartz): hotkeys, recording, paste, and status.
- Local backend (FastAPI, optional): preloads Whisper and the optional LLM; provides HTTP endpoints for scripts, Finder Quick Action, or other clients.
- Helper scripts: download models, quick start, Finder Quick Action client, LaunchAgent installer.

## Endpoints exposed by the local backend

- GET /healthz  -> health status
- POST /transcribe  (multipart: audio=@file) -> { text }
- POST /format      (json: { text })         -> { text }
- POST /stt_and_format (multipart: audio=@file) -> { text }
- POST /action      (json: { action: activate|idle|mute }) -> { state }
- GET /events       (SSE stream with { state })

These run by default at http://127.0.0.1:8237 .

## Models

- Whisper: choose one of
  - large-v3-turbo (recommended)
  - medium (smaller/faster)
- Optional LLM for formatting (e.g., Bielik 1.5B/4.5B/11B in MLX, or a small Llama/Qwen in MLX).

Paths tip for MLX on macOS: prefer lowercase /users/... when an uppercase /Users/... path causes issues.

## Directory structure (abridged)

```
vista-scribe/
  README.md
  main.py                  # tray app entry and state machine
  hotkeys.py               # global hotkeys (incl. double-Option)
  audio.py                 # recording with silence detection
  stt.py                   # local MLX Whisper integration
  llm.py                   # optional MLX-LM formatting adapter
  backend.py               # FastAPI server (Whisper + optional LLM)
  path_utils.py            # path normalization helpers (/Users -> /users)
  docs/
    PROJECT_DESCRIPTION.md # this file
    mlx-lm/                # CLI help snapshots
  scripts/
    get_models.py          # download models into ./models
    quick_action_backend.sh# Finder Quick Action client
  packaging/
    launchagents/com.vista-scribe.backend.plist
    dmg/build_dmg.sh
    setup.py               # optional py2app bundling (tray)
  quick_start.sh           # one-click setup/start helper
  models/                  # local models live here (not in VCS)
  outputs/                 # results and benchmarks (ignored by VCS)
```

## Quick start (no .env required)

1) Sync deps and activate venv

```
uv sync
source .venv/bin/activate
```

2) Download models (choose Whisper variant; LLM optional)

```
uv run python scripts/get_models.py --whisper large-v3-turbo
# or: --whisper medium
# optional LLM example:
# uv run python scripts/get_models.py --whisper large-v3-turbo --llm mlx-community/Llama-3.2-3B-Instruct-4bit
```

3) Start the backend (foreground)

```
uv run python backend.py
```

Health check (separate terminal):

```
curl -s http://127.0.0.1:8237/healthz
```

4) Start the tray app (global double-Option hotkey)

```
uv run python main.py
```

5) Finder Quick Action (optional)

Use scripts/quick_action_backend.sh to send a file to the backend and copy results to the clipboard.

## Configuration knobs

- WHISPER_VARIANT=large-v3-turbo|medium (preferred) or WHISPER_DIR to force a model path.
- FORMAT_ENABLED=0|1 controls whether LLM formatting runs.
- LLM_ID points to a local MLX model directory or an MLX model repo (will auto-download on first use).
- DOUBLE_OPTION_INTERVAL_MS controls double-tap detection window (default 350).

## Testing and linting

- Run tests: `uv run pytest -q`
- Ruff linting: `uvx ruff format .` and `uvx ruff check .`

## Notes

- Grant macOS permissions on first run: Microphone, Accessibility, Input Monitoring.
- If the backend should always run, install the LaunchAgent from packaging/launchagents.
- When providing absolute model paths for MLX, prefer lowercase /users/... .
