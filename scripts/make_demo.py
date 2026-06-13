"""Generate the neutral-voice demo clip shown in the README.

Uses OmniVoice in DESIGN mode (a generic voice from the instruct vocabulary, no
cloning), on fixed generic English text, so the clip exposes nothing personal.
Output: demo/sample.mp3. Requires the GPU TTS stack (scripts/install_omnivoice.ps1).

    uv run python scripts/make_demo.py
"""
from pathlib import Path

from walkingdev.audio_encode import wav_to_mp3
from walkingdev.config import Config
from walkingdev.tts import make_tts

TEXT = (
    "Good morning. Here's your brief for the day. A new open model dropped this "
    "week, worth a look. Your top priority: ship the auth endpoint first. "
    "One thing at a time. Enjoy the walk."
)

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
DEMO.mkdir(exist_ok=True)

# Design voice (the documented default) — explicitly NOT a clone.
cfg = Config({"tts": {"backend": "omnivoice", "omnivoice": {
    "instruct": "male, young adult, low pitch",
    "device": "cuda:0",
    "sample_rate": 24000,
}}}, ROOT)

wav = str(DEMO / "sample.wav")
make_tts(cfg).synthesize(TEXT, wav)
mp3 = str(DEMO / "sample.mp3")
wav_to_mp3(wav, mp3, bitrate=128)
print("wrote", mp3)
