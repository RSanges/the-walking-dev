"""WAV -> MP3 encoding via lameenc (no ffmpeg needed, works on Windows).

OmniVoice/soundfile produce WAV; podcast feeds want MP3. This keeps the TTS
engine format-agnostic and does the packaging here.
"""
from pathlib import Path


def wav_to_mp3(wav_path: str, mp3_path: str, bitrate: int = 128) -> str:
    import lameenc
    import numpy as np
    import soundfile as sf

    data, sr = sf.read(wav_path, dtype="int16")
    data = np.asarray(data)
    channels = 1 if data.ndim == 1 else data.shape[1]

    encoder = lameenc.Encoder()
    encoder.set_bit_rate(bitrate)
    encoder.set_in_sample_rate(sr)
    encoder.set_channels(channels)
    encoder.set_quality(2)  # 2 = high quality, reasonably fast
    mp3 = encoder.encode(data.tobytes()) + encoder.flush()

    Path(mp3_path).parent.mkdir(parents=True, exist_ok=True)
    with open(mp3_path, "wb") as f:
        f.write(mp3)
    return mp3_path
