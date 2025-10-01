# stt.py (speech-to-text)
#
# Local transcription using MLX Whisper (no API key required).
# Loads the Whisper model once and transcribes audio files produced by audio.py.
#
# Key env vars:
# - WHISPER_DIR: absolute or relative path to whisper model directory.
#                If omitted, defaults to './models/whisper-large-v3-turbo' if present,
#                otherwise './whisper-large-v3-turbo' in repo root.
#                NOTE: mlx_whisper may be sensitive to uppercase in absolute
#                paths on macOS; we normalize '/Users' → '/users'.

import asyncio
import os
import logging
from dotenv import load_dotenv

# MLX Whisper
import mlx_whisper as whisper
from mlx_whisper.load_models import load_model
import wave
import numpy as np

from path_utils import normalize_model_path

# --- setup ---
load_dotenv()
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s - %(levelname)s - %(message)s")

# --- model load (once) ---
_repo_root = os.path.dirname(os.path.abspath(__file__))
# Allow choosing between large-v3-turbo and medium via env; fallback to what's present
_variant = os.environ.get("WHISPER_VARIANT", "").strip().lower()  # 'large-v3-turbo' | 'medium'

# If WHISPER_DIR provided, use it directly (normalized) below; otherwise compute default
if not os.environ.get("WHISPER_DIR"):
    candidates = []
    if _variant in {"large-v3-turbo", "medium"}:
        candidates.append(os.path.join(_repo_root, "models", f"whisper-{_variant}"))
        candidates.append(os.path.join(_repo_root, f"whisper-{_variant}"))
    else:
        # No explicit variant: prefer large-v3-turbo if present, else medium
        for v in ("large-v3-turbo", "medium"):
            candidates.append(os.path.join(_repo_root, "models", f"whisper-{v}"))
            candidates.append(os.path.join(_repo_root, f"whisper-{v}"))
    # pick first existing, else default to models/whisper-large-v3-turbo path
    _default_whisper_path = next((c for c in candidates if os.path.isdir(c)), os.path.join(_repo_root, "models", "whisper-large-v3-turbo"))
else:
    _default_whisper_path = os.environ.get("WHISPER_DIR")

WHISPER_DIR = normalize_model_path(_default_whisper_path)

try:
    whisper_model = load_model(WHISPER_DIR)
    logging.info(f"MLX Whisper model loaded from: {WHISPER_DIR}")
except Exception as e:
    logging.error(f"Failed to load MLX Whisper model at '{WHISPER_DIR}': {e}")
    whisper_model = None

# Language preference (None = auto). Read from env on startup if provided.
LANGUAGE_CODE = (os.environ.get("WHISPER_LANGUAGE") or os.environ.get("LANGUAGE") or "").strip().lower() or None


def set_language(code: str | None):
    """Set preferred language code ('pl', 'en', or None for auto)."""
    global LANGUAGE_CODE
    if code:
        code = code.strip().lower()
        if code not in ("pl", "en"):
            logging.warning(f"Unsupported language code '{code}', falling back to auto")
            code = None
    LANGUAGE_CODE = code
    logging.info(f"Whisper language set to: {LANGUAGE_CODE or 'auto'}")


def get_language() -> str | None:
    """Get current preferred language code or None for auto."""
    return LANGUAGE_CODE


async def transcribe(path: str) -> str | None:
    """Transcribe the audio file at the given path using local MLX Whisper.

    Args:
        path: Path to the audio file (wav/mp3/flac/aiff). audio.py saves .wav.
    Returns:
        The transcribed text or None on failure.
    """
    if whisper_model is None:
        logging.error("Whisper model not initialized. Set WHISPER_DIR correctly.")
        return None
    if not os.path.exists(path):
        logging.error(f"Audio file not found at path: {path}")
        return None

    logging.info(f"Starting transcription for audio file: {path}")
    try:
        # Load WAV (audio.py saves 16kHz mono int16). For other formats, rely on CLI for now.
        with wave.open(path, 'rb') as wf:
            sr = wf.getframerate()
            ch = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n = wf.getnframes()
            raw = wf.readframes(n)
        if sampwidth == 2:
            arr = np.frombuffer(raw, dtype=np.int16)
            scale = 32768.0
        elif sampwidth == 4:
            arr = np.frombuffer(raw, dtype=np.int32)
            scale = 2147483648.0
        else:
            arr = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)
            scale = 128.0
        if ch > 1:
            arr = arr.reshape(-1, ch).mean(axis=1)
        samples = (arr.astype(np.float32) / scale).astype(np.float32)

        # Run in thread pool to avoid blocking if heavy
        loop = asyncio.get_event_loop()
        # Pass language if explicitly set; otherwise let Whisper auto-detect
        lang = LANGUAGE_CODE
        if lang:
            func = lambda: whisper.transcribe(path, language=lang)
        else:
            func = lambda: whisper.transcribe(path)
        result = await loop.run_in_executor(None, func)
        text = (result.get("text") or "").strip()
        logging.info(f"Transcription successful. Length: {len(text)} chars.")
        return text
    except Exception as e:
        logging.error(f"Error during local transcription: {e}", exc_info=True)
        return None
