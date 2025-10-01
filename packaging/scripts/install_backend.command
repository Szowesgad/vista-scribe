#!/bin/zsh
# install_backend.command
#
# Purpose: Install and start the vista-scribe backend (FastAPI) as a LaunchAgent.
# - Verifies uv tool and Python env
# - Optionally downloads models via scripts/get_models.py if missing
# - Writes ~/Library/LaunchAgents/com.vista-scribe.backend.plist with your paths
# - Loads and starts the agent; prints log locations
#
# Usage: double-click in Finder (Terminal will open) or run from shell.

set -euo pipefail

# Resolve repo root (this script lives in packaging/scripts)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

# MLX path quirk: prefer lowercase /users when available
lower_users() {
  local p="$1"
  if [[ "$p" == /Users/* ]]; then
    local fixed="/users/${p#*/Users/}"
    if [[ -e "$fixed" ]]; then
      echo "$fixed"
      return
    fi
  fi
  echo "$p"
}

# Check uv
if ! command -v uv >/dev/null 2>&1; then
  echo "[!] 'uv' not found. Install it with:"
  echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

# Ensure models exist (download if needed)
: "${WHISPER_VARIANT:=large-v3-turbo}"
: "${FORMAT_ENABLED:=1}"
: "${HOST:=127.0.0.1}"
: "${PORT:=8237}"
: "${LOG_LEVEL:=INFO}"

MODEL_DIR="${REPO_DIR}/models"
mkdir -p "$MODEL_DIR"

if [[ ! -d "${MODEL_DIR}/whisper-${WHISPER_VARIANT}" ]]; then
  echo "[i] Whisper model not found; downloading (${WHISPER_VARIANT})…"
  (cd "$REPO_DIR" && uv run python scripts/get_models.py --whisper "$WHISPER_VARIANT")
fi

# Decide WHISPER_DIR
if [[ -d "${MODEL_DIR}/whisper-${WHISPER_VARIANT}" ]]; then
  WHISPER_DIR="${MODEL_DIR}/whisper-${WHISPER_VARIANT}"
else
  # fallback: prefer large if present
  if [[ -d "${MODEL_DIR}/whisper-large-v3-turbo" ]]; then
    WHISPER_DIR="${MODEL_DIR}/whisper-large-v3-turbo"
  else
    WHISPER_DIR="${MODEL_DIR}/whisper-medium"
  fi
fi
WHISPER_DIR="$(lower_users "$WHISPER_DIR")"

# LLM is optional; use LLM_ID if provided, otherwise skip
if [[ "${FORMAT_ENABLED}" == "0" || "${FORMAT_ENABLED}" == "false" || "${FORMAT_ENABLED}" == "no" ]]; then
  USE_LLM=0
else
  USE_LLM=1
fi

PLIST="$HOME/Library/LaunchAgents/com.vista-scribe.backend.plist"
mkdir -p "$(dirname "$PLIST")"

# Write plist dynamically
cat >"$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.vista-scribe.backend</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/bin/env</string>
      <string>bash</string>
      <string>-lc</string>
      <string>cd $(lower_users "$REPO_DIR") && uv run python backend.py</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>EnvironmentVariables</key>
    <dict>
      <key>WHISPER_DIR</key><string>${WHISPER_DIR}</string>
      <key>FORMAT_ENABLED</key><string>${FORMAT_ENABLED}</string>
      <key>HOST</key><string>${HOST}</string>
      <key>PORT</key><string>${PORT}</string>
      <key>LOG_LEVEL</key><string>${LOG_LEVEL}</string>
PLIST

# If LLM_ID is set, include it
if [[ ${USE_LLM} -eq 1 && -n "${LLM_ID:-}" ]]; then
  LLM_PATH="$(lower_users "$LLM_ID")"
  echo "      <key>LLM_ID</key><string>${LLM_PATH}</string>" >>"$PLIST"
fi

# Close dicts
cat >>"$PLIST" <<'PLIST'
    </dict>
    <key>StandardOutPath</key><string>/tmp/vista-scribe.backend.out.log</string>
    <key>StandardErrorPath</key><string>/tmp/vista-scribe.backend.err.log</string>
  </dict>
</plist>
PLIST

echo "[i] LaunchAgent written to: $PLIST"

# Load (unload first if already loaded)
if launchctl list | grep -q "com.vista-scribe.backend"; then
  launchctl unload "$PLIST" || true
fi
launchctl load "$PLIST"
launchctl start com.vista-scribe.backend || true

echo "[✓] Backend started (com.vista-scribe.backend)"
echo "    Logs: /tmp/vista-scribe.backend.{out,err}.log"
echo "    Health: curl -s http://127.0.0.1:${PORT}/healthz | jq"
