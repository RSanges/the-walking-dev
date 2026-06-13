"""End-to-end test of the production TTS engine (not the spike script)."""
from pathlib import Path

import numpy as np
import soundfile as sf

from walkingdev.config import Config
from walkingdev.tts import make_tts

cfg = Config({"tts": {"backend": "omnivoice", "omnivoice": {
    "instruct": "male, young adult, low pitch",
    "device": "cuda:0", "sample_rate": 24000,
}}}, Path("."))

TEXT = ("Bonjour. Il est sept heures, voici ton brief du jour. "
        "On commence par la veille, puis tes projets, et on finit par l'agenda. "
        "Allez, on se met en mouvement.")

out = make_tts(cfg).synthesize(TEXT, "audio/narrator_final.wav")
a, sr = sf.read(out)
print("OK ->", out, "| dur=%.2fs" % (len(a) / sr), "| rms=%.5f" % float(np.sqrt(np.mean(a ** 2))))
