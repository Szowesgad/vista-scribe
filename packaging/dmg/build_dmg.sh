#!/bin/bash
# build_dmg.sh
#
# Purpose: Build a simple DMG for vista-scribe distribution.
# - Includes (if present): packaging/dist/vista-scribe.app (tray app)
# - Always includes helper scripts: Install Backend, Get Models, Uninstall Backend
# - Creates vista-scribe.dmg in packaging/dmg/
#
# Requirements: hdiutil (macOS), optional: create-dmg (not required)

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$(cd -- "$(dirname "$0")" && pwd)"
STAGE_DIR="${OUT_DIR}/stage"
DMG_NAME="vista-scribe.dmg"

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

# Copy app if built
APP_SRC="${ROOT_DIR}/packaging/dist/vista-scribe.app"
if [[ -d "$APP_SRC" ]]; then
  echo "[i] Adding app bundle: $APP_SRC"
  cp -R "$APP_SRC" "$STAGE_DIR/Vista Scribe.app"
else
  echo "[!] App bundle not found at $APP_SRC — continuing without it."
  echo "    Build it first with: (cd packaging && python setup.py py2app)"
fi

# Copy helper scripts
mkdir -p "$STAGE_DIR/Helpers"
cp "${ROOT_DIR}/packaging/scripts/install_backend.command" "$STAGE_DIR/Helpers/Install Backend.command"
cp "${ROOT_DIR}/packaging/scripts/get_models.command" "$STAGE_DIR/Helpers/Get Models.command"
cp "${ROOT_DIR}/packaging/scripts/uninstall_backend.command" "$STAGE_DIR/Helpers/Uninstall Backend.command"
chmod +x "$STAGE_DIR/Helpers"/*.command

# Include the LaunchAgent template for reference
mkdir -p "$STAGE_DIR/Extras"
cp "${ROOT_DIR}/packaging/launchagents/com.vista-scribe.backend.plist" "$STAGE_DIR/Extras/"

# Minimal README inside DMG
cat >"$STAGE_DIR/README-INSTALL.txt" <<'TXT'
Vista Scribe — Installation
===========================

1) (Optional) Drag "Vista Scribe.app" into /Applications.
   - If the app is missing here, build it from source or run from the repo.
2) Double-click Helpers / Get Models.command — downloads Whisper locally.
3) Double-click Helpers / Install Backend.command — installs and starts the background server.
4) Grant macOS permissions on first run (Microphone, Accessibility, Input Monitoring).
5) Test: curl -s http://127.0.0.1:8237/healthz

To remove the backend later, run Helpers / Uninstall Backend.command.
TXT

# Create DMG
DMG_PATH="${OUT_DIR}/${DMG_NAME}"
rm -f "$DMG_PATH"
hdiutil create -volname "vista-scribe" -srcfolder "$STAGE_DIR" -ov -format UDZO "$DMG_PATH"

echo "[✓] Built DMG: $DMG_PATH"
