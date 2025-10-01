#!/usr/bin/env python3
"""
ai_transcriber.py - Script to help AI assistants transcribe user voice messages

This script is designed to help AI assistants like Junie transcribe voice messages
from users. It searches for voice message files in standard locations on macOS,
such as Voice Memos exports, and uses the vista-scribe backend to transcribe them.

Usage:
  python ai_transcriber.py                # Search and transcribe latest voice message
  python ai_transcriber.py --path /path/to/voice_message.m4a  # Transcribe specific file

Features:
- Automatically searches for voice messages in standard locations
- Starts the vista-scribe backend if needed
- Transcribes voice messages using local MLX Whisper model
- Optionally formats transcriptions using local MLX-LM model
- Saves results to a file that can be read by the AI assistant
"""

import os
import sys
import glob
import json
import time
import requests
import subprocess
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
BACKEND_URL = "http://127.0.0.1:8237"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(REPO_DIR, "outputs")
RESULTS_FILE = os.path.join(OUTPUT_DIR, "ai_transcription_result.txt")

def check_backend_running():
    """Check if the vista-scribe backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/healthz", timeout=2)
        return response.status_code == 200 and response.json().get("ok")
    except requests.RequestException:
        return False

def start_backend():
    """Start the vista-scribe backend if it's not already running"""
    if check_backend_running():
        logger.info("Backend is already running.")
        return True
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(REPO_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Determine model paths
    model_dir = os.path.join(REPO_DIR, "models")
    
    # Find Whisper model
    whisper_path = None
    for variant in ["whisper-large-v3-turbo", "whisper-medium"]:
        candidate = os.path.join(model_dir, variant)
        if os.path.isdir(candidate):
            whisper_path = candidate
            break
    
    if not whisper_path:
        logger.error("No Whisper model found. Please run scripts/get_models.py first.")
        return False
    
    # Find LLM model (optional)
    llm_path = None
    for candidate_name in ["bielik-4.5b-mxfp4-mlx", "bielik-1.5b-mxfp4-mlx", "bielik-11b-mxfp4-mlx"]:
        candidate = os.path.join(model_dir, candidate_name)
        if os.path.isdir(candidate):
            llm_path = candidate
            break
    
    # Normalize paths for MLX (lowercase /users on macOS)
    def lower_users(p):
        if p.startswith("/Users/"):
            fixed = "/users/" + p[7:]
            if os.path.exists(fixed):
                return fixed
        return p
    
    whisper_path = lower_users(whisper_path)
    if llm_path:
        llm_path = lower_users(llm_path)
    
    # Build environment variables
    env = os.environ.copy()
    env["WHISPER_DIR"] = whisper_path
    env["FORMAT_ENABLED"] = "1" if llm_path else "0"
    env["HOST"] = "127.0.0.1"
    env["PORT"] = "8237"
    
    if llm_path:
        env["LLM_ID"] = llm_path
    
    # Start the backend
    logger.info("Starting vista-scribe backend...")
    
    backend_log = os.path.join(log_dir, "backend.err.log")
    backend_out = os.path.join(log_dir, "backend.out.log")
    
    try:
        # Use 'python' with full path to ensure proper environment
        process = subprocess.Popen(
            ["python", os.path.join(REPO_DIR, "backend.py")],
            env=env,
            stdout=open(backend_out, "a"),
            stderr=open(backend_log, "a")
        )
        
        # Wait for backend to start
        logger.info("Waiting for backend to start...")
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 seconds timeout
            if check_backend_running():
                logger.info(f"Backend started successfully (PID: {process.pid}).")
                return True
            time.sleep(1)
        
        logger.error(f"Backend failed to start. Check logs: {backend_log}")
        return False
        
    except Exception as e:
        logger.error(f"Failed to start backend: {e}")
        return False

def find_voice_message_files():
    """Search for voice message files in standard locations"""
    logger.info("Searching for voice message files...")
    
    potential_files = []
    
    # Check common locations for Voice Memos on macOS
    home_dir = os.path.expanduser("~")
    
    # Pattern 1: Voice Memos app temporary files
    voice_memo_patterns = [
        # Global pattern that works across users
        "/Users/*/Library/Containers/com.apple.VoiceMemos/Data/tmp/**/message-from-user.m4a",
        # Current user pattern
        f"{home_dir}/Library/Containers/com.apple.VoiceMemos/Data/tmp/**/message-from-user.m4a",
        # Additional common pattern
        f"{home_dir}/Library/Containers/com.apple.VoiceMemos/Data/Library/Voicememos/*.m4a"
    ]
    
    # Additional locations to check
    additional_locations = [
        os.path.join(home_dir, "Desktop", "*.m4a"),
        os.path.join(home_dir, "Downloads", "*.m4a"),
        os.path.join(REPO_DIR, "*.m4a"),
        os.path.join(REPO_DIR, "*.mp3"),
        os.path.join(REPO_DIR, "*.wav")
    ]
    
    # Gather all potential voice message files
    for pattern in voice_memo_patterns + additional_locations:
        matches = glob.glob(pattern, recursive=True)
        for file_path in matches:
            # Only add if it exists and has been modified in the last hour
            if os.path.exists(file_path) and os.path.getmtime(file_path) > time.time() - 3600:
                potential_files.append((file_path, os.path.getmtime(file_path)))
    
    # Sort by modification time (newest first)
    potential_files.sort(key=lambda x: x[1], reverse=True)
    
    # Return just the file paths, newest first
    return [file_path for file_path, _ in potential_files]

def transcribe_file(file_path, with_formatting=True):
    """Send an audio file to the backend for transcription"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    if not check_backend_running():
        logger.info("Backend is not running. Starting it...")
        if not start_backend():
            return None
    
    logger.info(f"Transcribing audio file: {file_path}")
    
    try:
        # Determine which endpoint to use based on formatting preference
        endpoint = "/stt_and_format" if with_formatting else "/transcribe"
        
        # Send the file to the backend
        with open(file_path, "rb") as f:
            files = {"audio": f}
            response = requests.post(f"{BACKEND_URL}{endpoint}", files=files)
        
        if response.status_code == 200:
            result = response.json()
            if "text" in result:
                return result["text"]
            else:
                logger.error(f"Backend response missing 'text' field: {result}")
                return None
        else:
            logger.error(f"Backend returned error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        return None

def save_result(text, input_file=None):
    """Save the transcription result to a file for the AI to access"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create a result object with metadata
    result = {
        "transcription": text,
        "source_file": input_file,
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "backend": BACKEND_URL
    }
    
    # Save as formatted JSON
    with open(RESULTS_FILE, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Transcription result saved to: {RESULTS_FILE}")
    
    # Also save as plain text for easier reading
    text_file = os.path.join(OUTPUT_DIR, "latest_transcription.txt")
    with open(text_file, "w") as f:
        f.write(text)
    
    return RESULTS_FILE

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI assistant voice message transcriber")
    parser.add_argument("--path", help="Path to specific voice message file to transcribe")
    parser.add_argument("--no-format", action="store_true", help="Disable LLM formatting (use raw Whisper output)")
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Handle transcription
    if args.path:
        # Transcribe specific file
        logger.info(f"Transcribing specified file: {args.path}")
        file_to_transcribe = args.path
    else:
        # Find voice message files
        voice_files = find_voice_message_files()
        
        if not voice_files:
            logger.error("No voice message files found.")
            sys.exit(1)
        
        # Use the most recent file
        file_to_transcribe = voice_files[0]
        logger.info(f"Found {len(voice_files)} voice message files. Using most recent: {file_to_transcribe}")
    
    # Transcribe the file
    transcription = transcribe_file(file_to_transcribe, with_formatting=not args.no_format)
    
    if transcription:
        logger.info("Transcription successful:")
        print(f"\n--- Transcription Result ---\n{transcription}\n")
        
        # Save the result for the AI to access
        result_file = save_result(transcription, file_to_transcribe)
        logger.info(f"AI can access the result at: {result_file}")
        
        # Print instructions for the AI
        print("\n--- FOR AI ASSISTANT ---")
        print(f"Voice message transcription complete. Result saved to {result_file}")
        print(f"You can now respond to the user's transcribed message: '{transcription}'")
        
        return 0
    else:
        logger.error("Transcription failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())