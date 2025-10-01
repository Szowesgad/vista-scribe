#!/bin/zsh
# get_models.command
#
# Purpose: Download local models into ./models using the helper script. Useful after first install.
# Usage: double-click to download Whisper large-v3-turbo by default, or run with args.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

: "${WHISPER_VARIANT:=large-v3-turbo}"

cd "$REPO_DIR"

if [[ $# -gt 0 ]]; then
  echo "[i] Running: uv run python scripts/get_models.py $@"
  uv run python scripts/get_models.py "$@"
else
  echo "[i] Running: uv run python scripts/get_models.py --whisper ${WHISPER_VARIANT}"
  uv run python scripts/get_models.py --whisper "${WHISPER_VARIANT}"
fi

# Print next-steps hints are already in the helper output
