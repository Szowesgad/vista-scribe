#!/usr/bin/env python3
"""
Simple script to directly transcribe an audio file using mlx_whisper
as requested by the user.
"""

import sys
import mlx_whisper
from mlx_whisper.load_models import load_model
from mlx_audio import load as load_audio

def main():
    # Define paths
    model_path = "models/whisper-large-v3-turbo"
    audio_path = "user-messages/przepis-co-dalej-z-vista-scribe-musisz-przetranskrybowac-junie.m4a"
    
    print(f"Loading model from: {model_path}")
    model = load_model(model_path)
    
    print(f"Transcribing audio file: {audio_path}")
    # Load audio
    audio, sr = load_audio(open(audio_path, "rb").read())
    
    # Transcribe directly using mlx_whisper.transcribe as requested
    result = mlx_whisper.transcribe(model, audio, sr)
    
    # Print the transcription
    print("\n--- TRANSCRIPTION RESULT ---")
    print(result["text"])
    print("---------------------------\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())