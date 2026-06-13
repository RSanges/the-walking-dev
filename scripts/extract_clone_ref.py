"""Extract a clean reference segment from an audio file and transcribe it.

Produces voices/<name>.wav (mono 24kHz) + voices/<name>.txt (Whisper FR
transcription) for OmniVoice voice cloning.

Usage:
    python scripts/extract_clone_ref.py SOURCE [START_SEC] [DURATION_SEC] [NAME]

You must own the rights to SOURCE (record yourself, or use audio you are licensed
to use). A 20-40s clean mono clip of a single speaker works best for cloning.
"""
import sys

import librosa
import soundfile as sf

SRC = sys.argv[1] if len(sys.argv) > 1 else "voices/source.mp3"
START = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
NAME = sys.argv[4] if len(sys.argv) > 4 else "narrator"
SR = 24000
OUT_WAV = f"voices/{NAME}.wav"
OUT_TXT = f"voices/{NAME}.txt"

# 1) Extract the segment, mono, 24kHz
y, _ = librosa.load(SRC, sr=SR, mono=True, offset=START, duration=DUR)
sf.write(OUT_WAV, y, SR)
print("Segment extracted:", OUT_WAV, "(%.1fs, %dHz mono)" % (len(y) / SR, SR))

# 2) Transcribe (French) with Whisper
import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
asr = pipeline("automatic-speech-recognition",
               model="openai/whisper-small", device=device)
res = asr(OUT_WAV, chunk_length_s=30,
          generate_kwargs={"language": "french", "task": "transcribe"})
text = (res.get("text") or "").strip()
with open(OUT_TXT, "w", encoding="utf-8") as f:
    f.write(text)
print("=== TRANSCRIPTION ===")
print(text)
