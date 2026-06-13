"""Generate the neutral-voice demo clip shown in the README.

Uses OmniVoice in DESIGN mode (a generic voice from the instruct vocabulary, no
cloning), on fixed generic English text, so the clip exposes nothing personal.
Outputs demo/sample.mp3 and, if ffmpeg + a cover image are available, a
demo/sample.mp4 (cover still + audio) you can drag into a GitHub issue to get an
inline player URL (GitHub embeds video, not audio). Requires the GPU TTS stack
(scripts/install_omnivoice.ps1).

    uv run python scripts/make_demo.py
"""
import shutil
import subprocess
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

# Optional: a small MP4 (cover still + audio) for an inline player on GitHub.
cover = ROOT / "cover.jpg"
if shutil.which("ffmpeg") and cover.exists():
    mp4 = str(DEMO / "sample.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", str(cover), "-i", mp3,
         "-c:v", "libx264", "-tune", "stillimage", "-vf", "scale=720:720",
         "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p", "-shortest", mp4],
        check=True, capture_output=True)
    print("wrote", mp4)
else:
    print("(ffmpeg or cover.jpg missing -> skipped mp4)")
