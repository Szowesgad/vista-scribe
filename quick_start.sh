#!/bin/zsh
# quick_start.sh — One‑click local setup & run for vista-scribe
#
# What it does (idempotent):
#  1) uv sync  -> ensure env
#  2) source .venv/bin/activate
#  3) Download models (Whisper variant you choose; optional LLM)
#  4) Start backend (foreground or as LaunchAgent) and healthcheck it
#  5) (Optional) Run full-stack tests on sample audio
#
# Usage examples:
#   zsh ./quick_start.sh                                      # defaults: Whisper large-v3-turbo, no LLM, backend foreground
#   zsh ./quick_start.sh --whisper medium                     # use Whisper medium
#   zsh ./quick_start.sh --llm \
#     /users/maciejgad/hosted/vistas/vista-scribe/models/bielik-4.5b-mxfp4-mlx
#   zsh ./quick_start.sh --install-backend --llm mlx-community/Llama-3.2-3B-Instruct-4bit
#   zsh ./quick_start.sh --no-test                            # skip sample tests
#
# Flags:
#   --whisper {large-v3-turbo|medium}  Whisper variant to download/use (default: large-v3-turbo)
#   --llm <repo_or_path>               Optional LLM for formatting (MLX local path or HF repo id)
#   --no-llm                           Disable formatting (FORMAT_ENABLED=0)
#   --install-backend                  Install & start LaunchAgent instead of foreground
#   --foreground                       Run backend in foreground (default)
#   --host <host>                      Backend host (default: 127.0.0.1)
#   --port <port>                      Backend port (default: 8237)
#   --no-test                          Don’t run sample audio tests
#
set -euo pipefail

# Resolve repo root robustly (works if script is in repo root or in scripts/)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" && pwd)"
if [[ -f "${SCRIPT_DIR}/pyproject.toml" || -f "${SCRIPT_DIR}/backend.py" ]]; then
  REPO_DIR="$SCRIPT_DIR"
else
  REPO_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
fi
cd "$REPO_DIR"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"

# Defaults
WHISPER_VARIANT="${WHISPER_VARIANT:-large-v3-turbo}"
LLM_REPO_OR_PATH="${LLM_ID:-}"
FORMAT_ENABLED="${FORMAT_ENABLED:-1}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8237}"
DO_INSTALL=0
RUN_FOREGROUND=1
RUN_TESTS=1

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --whisper)
      WHISPER_VARIANT="$2"; shift 2;;
    --llm)
      LLM_REPO_OR_PATH="$2"; FORMAT_ENABLED=1; shift 2;;
    --no-llm)
      LLM_REPO_OR_PATH=""; FORMAT_ENABLED=0; shift;;
    --install-backend)
      DO_INSTALL=1; RUN_FOREGROUND=0; shift;;
    --foreground)
      DO_INSTALL=0; RUN_FOREGROUND=1; shift;;
    --host)
      HOST="$2"; shift 2;;
    --port)
      PORT="$2"; shift 2;;
    --no-test)
      RUN_TESTS=0; shift;;
    *)
      echo "[!] Unknown flag: $1"; exit 2;;
  esac
done

# MLX path quirk: prefer lowercase /users when available
lower_users() {
  local p="$1"
  if [[ "$p" == /Users/* ]]; then
    local fixed="/users/${p#*/Users/}"
    if [[ -e "$fixed" ]]; then
      echo "$fixed"; return
    fi
  fi
  echo "$p"
}

# Ensure uv
if ! command -v uv >/dev/null 2>&1; then
  echo "[!] 'uv' not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

# 1) uv sync (create/update venv)
echo "[i] Syncing env (uv sync)…"
uv sync

# 2) Activate venv for this script’s process
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# 3) Download models
if [[ -z "$WHISPER_VARIANT" ]]; then
  WHISPER_VARIANT="large-v3-turbo"
fi

echo "[i] Ensuring Whisper model: $WHISPER_VARIANT"
uv run python scripts/get_models.py --whisper "$WHISPER_VARIANT" ${LLM_REPO_OR_PATH:+--llm "$LLM_REPO_OR_PATH"}

# Resolve WHISPER_DIR
MODEL_DIR="$REPO_DIR/models"
if [[ -d "$MODEL_DIR/whisper-$WHISPER_VARIANT" ]]; then
  WHISPER_DIR="$MODEL_DIR/whisper-$WHISPER_VARIANT"
else
  # fallback to large then medium
  if [[ -d "$MODEL_DIR/whisper-large-v3-turbo" ]]; then
    WHISPER_DIR="$MODEL_DIR/whisper-large-v3-turbo"
  else
    WHISPER_DIR="$MODEL_DIR/whisper-medium"
  fi
fi
WHISPER_DIR="$(lower_users "$WHISPER_DIR")"

# LLM optional
if [[ -n "$LLM_REPO_OR_PATH" ]]; then
  LLM_ID="$(lower_users "$LLM_REPO_OR_PATH")"
else
  LLM_ID=""
fi

# 4) Start backend
if [[ $DO_INSTALL -eq 1 ]]; then
  echo "[i] Installing backend LaunchAgent…"
  WHISPER_DIR="$WHISPER_DIR" \
  FORMAT_ENABLED="$FORMAT_ENABLED" \
  HOST="$HOST" PORT="$PORT" \
  LLM_ID="$LLM_ID" \
  sh "$REPO_DIR/packaging/scripts/install_backend.command"
else
  echo "[i] Starting backend in background (nohup)…"
  # Stop any existing on same port (best-effort)
  : > "$LOG_DIR/backend.out.log"
  : > "$LOG_DIR/backend.err.log"
  # Start
  ( \
    export WHISPER_DIR="$WHISPER_DIR" FORMAT_ENABLED="$FORMAT_ENABLED" HOST="$HOST" PORT="$PORT"; \
    if [[ -n "$LLM_ID" ]]; then export LLM_ID="$LLM_ID"; fi; \
    nohup uv run python backend.py >>"$LOG_DIR/backend.out.log" 2>>"$LOG_DIR/backend.err.log" & \
  )
  sleep 0.5
fi

# Healthcheck (wait up to ~60s)
echo "[i] Healthchecking backend at http://$HOST:$PORT/healthz …"
ATTEMPTS=120
ok=0
for i in $(seq 1 $ATTEMPTS); do
  if curl -s "http://$HOST:$PORT/healthz" | grep -q '"ok": true'; then
    ok=1; break
  fi
  sleep 0.5
done
if [[ $ok -ne 1 ]]; then
  echo "[!] Backend healthcheck failed. See logs in $LOG_DIR/backend.err.log"
  echo "[i] Tip: model loading can take longer on first run. Recheck: curl -s http://$HOST:$PORT/healthz"
  exit 1
fi

echo "[✓] Backend is healthy."

# 5) Optional sample tests
if [[ $RUN_TESTS -eq 1 ]]; then
  samples=(
    "$REPO_DIR/assets/test_files/dialog_full_mia_CKD_final.mp3"
    "$REPO_DIR/assets/test_files/dialog_shadow_FINAL_LOUD_v2.mp3"
  )
  for f in "${samples[@]}"; do
    if [[ -f "$f" ]]; then
      echo "[i] Full-stack test on: $f"
      LLM_ID="$LLM_ID" FORMAT_ENABLED="$FORMAT_ENABLED" \
      uv run python full_stack_test.py "$f" --lang "${WHISPER_LANG:-pl}" || true
    fi
  done
fi

echo "\n=== Done ==="
echo "Backend:   http://$HOST:$PORT  (health: /healthz)"
echo "Whisper:   $WHISPER_DIR"
echo "LLM_ID:    ${LLM_ID:-<disabled>}  (FORMAT_ENABLED=$FORMAT_ENABLED)"
echo "Logs:      $LOG_DIR/backend.{out,err}.log"
echo "Examples:  curl -s http://$HOST:$PORT/healthz | jq"