#!/usr/bin/env bash
# transcribe_for_ai.sh - Wrapper script to run ai_transcriber.py with proper uv environment
# 
# This script helps AI assistants transcribe user voice messages by using
# vista-scribe's infrastructure. It looks for voice message files in standard
# locations and transcribes them using the local MLX Whisper model.
#
# Usage:
#   ./transcribe_for_ai.sh               # Find and transcribe latest voice message
#   ./transcribe_for_ai.sh --path FILE   # Transcribe a specific audio file
#   ./transcribe_for_ai.sh --no-format   # Transcribe without LLM formatting

set -euo pipefail

# Colorful output for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Set repo directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Check if uv is installed
if ! command -v uv >/dev/null 2>&1; then
  echo -e "${RED}[!] Error: 'uv' not found. Please install it:${NC}"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

echo -e "${BLUE}=== Vista Scribe AI Transcription Tool ===${NC}"
echo -e "${YELLOW}[*] This tool helps AI assistants transcribe user voice messages${NC}"

# Sync dependencies first
echo -e "${BLUE}[*] Syncing dependencies...${NC}"
uv sync

# Forward all arguments to the Python script
echo -e "${BLUE}[*] Running AI transcriber...${NC}"
uv run python ai_transcriber.py "$@"

# Check exit status
if [ $? -eq 0 ]; then
  echo -e "${GREEN}[✓] Transcription completed successfully${NC}"
  
  # Instructions for the user
  echo
  echo -e "${BLUE}=== Instructions for Users ===${NC}"
  echo -e "To share a voice message with the AI assistant:"
  echo -e "1. Use Voice Memos app on your Mac to record a message"
  echo -e "2. Share or save the recording to the project directory"
  echo -e "3. Run this script again to transcribe your message"
  echo -e "4. The AI will be able to read and respond to your voice message"
  echo
  echo -e "${GREEN}AI assistant can now respond to your voice message${NC}"
  
  exit 0
else
  echo -e "${RED}[!] Transcription failed${NC}"
  
  echo
  echo -e "${YELLOW}=== Troubleshooting ===${NC}"
  echo -e "1. Make sure you have recorded a voice message"
  echo -e "2. Check that the vista-scribe backend is running"
  echo -e "3. Verify that the Whisper model is installed in the models directory"
  echo -e "4. Try specifying a file path directly: ./transcribe_for_ai.sh --path /path/to/audio.m4a"
  
  exit 1
fi