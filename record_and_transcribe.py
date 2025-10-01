#!/usr/bin/env python3
"""
record_and_transcribe.py - Script to record audio and transcribe it using vista-scribe backend

This script provides a simple way to record audio from the microphone and send it
to the vista-scribe backend for transcription. It works with an existing backend
or can start one if needed.

Usage:
  python record_and_transcribe.py                # Record and transcribe
  python record_and_transcribe.py file.mp3       # Transcribe existing file

Features:
- Records audio from the default microphone until silence is detected
- Sends audio to the vista-scribe backend for transcription
- Copies the transcription result to the clipboard
- Can start the backend if it's not already running
- Provides clear feedback during the process
"""

import sys
import os
import json
import time
import asyncio
import subprocess
import logging
import argparse
import tempfile
from pathlib import Path
import requests
from audio import Recorder

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
BACKEND_URL = "http://127.0.0.1:8237"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 300  # seconds

# ANSI colors for better readability
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
YELLOW = '\033[0;33m'
NC = '\033[0m'  # No Color

def color_print(color, message):
    """Print a message with color"""
    print(f"{color}{message}{NC}")

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
        color_print(GREEN, "[✓] Backend is already running.")
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
        color_print(RED, "[!] No Whisper model found. Please run scripts/get_models.py first.")
        return False
    
    # Find LLM model (optional)
    llm_path = None
    llm_candidates = [
        os.path.join(model_dir, "bielik-4.5b-mxfp4-mlx"),
        os.path.join(model_dir, "bielik-1.5b-mxfp4-mlx"),
        os.path.join(model_dir, "bielik-11b-mxfp4-mlx")
    ]
    
    for candidate in llm_candidates:
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
    color_print(BLUE, "[*] Starting vista-scribe backend...")
    
    backend_log = os.path.join(log_dir, "backend.err.log")
    backend_out = os.path.join(log_dir, "backend.out.log")
    
    try:
        process = subprocess.Popen(
            ["python", os.path.join(REPO_DIR, "backend.py")],
            env=env,
            stdout=open(backend_out, "a"),
            stderr=open(backend_log, "a")
        )
        
        # Wait for backend to start
        color_print(YELLOW, "[*] Waiting for backend to start...")
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 seconds timeout
            if check_backend_running():
                color_print(GREEN, f"[✓] Backend started successfully (PID: {process.pid}).")
                return True
            time.sleep(1)
        
        color_print(RED, f"[!] Backend failed to start. Check logs: {backend_log}")
        return False
        
    except Exception as e:
        color_print(RED, f"[!] Failed to start backend: {e}")
        return False

async def record_audio():
    """Record audio from the microphone and save it to a temporary file"""
    color_print(BLUE, "=== Recording Audio ===")
    color_print(YELLOW, "[*] Recording will start in 1 second. Speak after the beep.")
    color_print(YELLOW, "[*] Recording will automatically stop after silence is detected.")
    time.sleep(1)
    
    # Make a beep sound to indicate recording start
    print("\a")  # ASCII bell
    color_print(GREEN, "[*] Recording started... (speak now)")
    
    # Create a recorder instance and start recording
    recorder = Recorder()
    try:
        await recorder.start()
        
        # Show a simple "recording" animation
        animation = "|/-\\"
        idx = 0
        start_time = time.time()
        
        while recorder._stream and recorder._stream.active:
            # Check if recording is still active
            if not recorder._collect_task or recorder._collect_task.done():
                break
                
            # Print animation frame
            sys.stdout.write(f"\r{RED}● Recording {animation[idx % len(animation)]} {time.time() - start_time:.1f}s{NC}")
            sys.stdout.flush()
            idx += 1
            
            # Sleep briefly
            await asyncio.sleep(0.1)
            
            # Timeout after TIMEOUT seconds
            if time.time() - start_time > TIMEOUT:
                color_print(YELLOW, "\n[!] Recording timeout reached. Stopping.")
                break
        
        # Stop recording and get the temporary file path
        audio_path = await recorder.stop()
        color_print(GREEN, f"\n[✓] Recording finished. Audio saved temporarily.")
        return audio_path
        
    except Exception as e:
        color_print(RED, f"\n[!] Error during recording: {e}")
        if recorder._stream and recorder._stream.active:
            await recorder.stop()
        return None

def transcribe_file(file_path, with_formatting=True):
    """Send an audio file to the backend for transcription"""
    if not check_backend_running():
        color_print(RED, "[!] Backend is not running. Starting it...")
        if not start_backend():
            return None
    
    color_print(BLUE, f"=== Transcribing Audio ===")
    color_print(YELLOW, "[*] Sending audio to the backend for processing...")
    
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
                color_print(RED, f"[!] Backend response missing 'text' field: {result}")
                return None
        else:
            color_print(RED, f"[!] Backend returned error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        color_print(RED, f"[!] Error during transcription: {e}")
        return None

def copy_to_clipboard(text):
    """Copy text to clipboard"""
    if not text:
        return False
        
    try:
        # For macOS
        process = subprocess.Popen(
            ["pbcopy"],
            stdin=subprocess.PIPE,
            text=True
        )
        process.communicate(input=text)
        return process.returncode == 0
    except Exception as e:
        color_print(RED, f"[!] Failed to copy to clipboard: {e}")
        return False

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Record or transcribe audio using vista-scribe backend")
    parser.add_argument("file", nargs="?", help="Optional audio file to transcribe (if not provided, will record from microphone)")
    parser.add_argument("--no-format", action="store_true", help="Disable LLM formatting (use raw Whisper output)")
    args = parser.parse_args()
    
    # Handle file transcription or recording
    if args.file:
        # Transcribe existing file
        if not os.path.exists(args.file):
            color_print(RED, f"[!] File not found: {args.file}")
            return 1
            
        color_print(BLUE, f"=== Transcribing file: {args.file} ===")
        text = transcribe_file(args.file, with_formatting=not args.no_format)
        
    else:
        # Record audio and transcribe
        audio_path = await record_audio()
        if not audio_path or not os.path.exists(audio_path):
            color_print(RED, "[!] Recording failed or didn't produce a file.")
            return 1
            
        text = transcribe_file(audio_path, with_formatting=not args.no_format)
        
        # Clean up temporary file
        try:
            os.unlink(audio_path)
        except Exception as e:
            color_print(YELLOW, f"[!] Warning: Could not delete temporary file {audio_path}: {e}")
    
    # Handle transcription result
    if text:
        color_print(GREEN, "=== Transcription Result ===")
        print(f"{BLUE}{text}{NC}")
        
        # Save to a file
        output_dir = os.path.join(REPO_DIR, "outputs")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_file = os.path.join(output_dir, f"transcription-{timestamp}.txt")
        
        with open(output_file, "w") as f:
            f.write(text)
        color_print(GREEN, f"[✓] Transcription saved to: {output_file}")
        
        # Copy to clipboard
        if copy_to_clipboard(text):
            color_print(GREEN, "[✓] Transcription copied to clipboard.")
        
        return 0
    else:
        color_print(RED, "[!] Transcription failed.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        color_print(YELLOW, "\n[*] Interrupted by user. Exiting.")
        sys.exit(0)