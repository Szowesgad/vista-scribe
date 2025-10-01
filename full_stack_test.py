#!/usr/bin/env python3
"""
full_stack_test.py

Run the full local pipeline on an audio file:
- Transcribe using MLX Whisper (local model already used by stt.py)
- Format using local MLX-LM (llm.py)

Usage:
  uv run python full_stack_test.py <audio_path> [--lang pl]

Notes:
- For WAV (16k mono) it uses stt.transcribe directly.
- For non-WAV (e.g., MP3), it decodes via mlx_audio.load and calls
  whisper.transcribe with the loaded samples.
- Saves outputs to outputs/full_stack/<basename>.raw.txt and .fmt.txt
- Respects env vars used by stt.py and llm.py (WHISPER_DIR, LLM_ID, etc.).

"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

# Reuse app modules
import stt as stt_mod
import llm as llm_mod

# For direct whisper call on non-WAV (via CLI fallback)
import subprocess
import sys

from path_utils import normalize_model_path

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("full_stack_test")


async def transcribe_any(audio_path: str, lang: str | None = None) -> str | None:
    """Transcribe WAV via stt.transcribe; other formats via mlx_audio + whisper."""
    audio_path = str(Path(audio_path).resolve())
    ext = Path(audio_path).suffix.lower()

    if stt_mod.whisper_model is None:
        logger.error("Whisper model not initialized in stt.py. Check WHISPER_DIR.")
        return None

    if ext == ".wav":
        return await stt_mod.transcribe(audio_path)

    try:
        logger.info(f"Transcribing non-WAV via mlx_whisper CLI: {audio_path}")
        out_dir = Path("outputs") / "full_stack"
        out_dir.mkdir(parents=True, exist_ok=True)
        base = Path(audio_path).stem
        cmd = [
            "mlx_whisper",
            "--model", stt_mod.WHISPER_DIR,
            "--language", (lang or os.environ.get("WHISPER_LANG", "pl")),
            "--output-dir", str(out_dir),
            "--output-format", "txt",
            audio_path,
        ]
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode != 0:
            logger.error(f"mlx_whisper CLI failed (code {proc.returncode}): {proc.stderr.decode('utf-8', 'ignore')}")
            return None
        txt_path = out_dir / f"{base}.txt"
        if not txt_path.exists():
            logger.error(f"Expected transcription output not found: {txt_path}")
            return None
        text = txt_path.read_text(encoding="utf-8").strip()
        logger.info(f"Transcription OK via CLI ({len(text)} chars)")
        return text
    except Exception as e:
        logger.error(f"Transcription failed for {audio_path}: {e}", exc_info=True)
        return None


async def run_full_stack(audio_path: str, lang: str | None = None) -> int:
    # 1) Transcribe
    raw = await transcribe_any(audio_path, lang=lang)
    if raw is None:
        logger.error("Transcription returned None.")
        return 2
    if not raw.strip():
        logger.warning("Empty transcription result.")

    # 2) Format
    fmt = await llm_mod.format_text(raw)
    if fmt is None:
        logger.warning("Formatting failed; falling back to raw text.")
        fmt = raw

    # 3) Save outputs
    out_dir = Path("outputs") / "full_stack"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = Path(audio_path).stem
    raw_p = out_dir / f"{base}.raw.txt"
    fmt_p = out_dir / f"{base}.fmt.txt"
    raw_p.write_text(raw, encoding="utf-8")
    fmt_p.write_text(fmt, encoding="utf-8")

    print("\n=== Full Stack Result ===")
    print(f"Audio: {audio_path}")
    print(f"Raw  -> {raw_p}")
    print(f"Fmt  -> {fmt_p}")
    print("\nPreview (first 200 chars):")
    print("RAW:", (raw[:200] + ("…" if len(raw) > 200 else "")))
    print("FMT:", (fmt[:200] + ("…" if len(fmt) > 200 else "")))

    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio_path", help="Path to audio file (wav/mp3/flac/aiff)")
    ap.add_argument("--lang", default=os.environ.get("WHISPER_LANG", "pl"), help="Language code hint (e.g., pl, en)")
    args = ap.parse_args()

    # Normalize WHISPER_DIR if present (workaround for MLX path case rules)
    if os.environ.get("WHISPER_DIR"):
        os.environ["WHISPER_DIR"] = normalize_model_path(os.environ["WHISPER_DIR"]) or os.environ["WHISPER_DIR"]

    return asyncio.run(run_full_stack(args.audio_path, lang=args.lang))


if __name__ == "__main__":
    raise SystemExit(main())
