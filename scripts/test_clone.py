"""Validate the pinned (cloned) voice on NEW text via the production engine."""
import numpy as np
import soundfile as sf

from walkingdev.config import Config
from walkingdev.tts import make_tts

cfg = Config.load("config.yaml")
NEW_TEXT = ("Aujourd'hui, gros point sur tes projets. Le premier avance bien, et "
            "il faut trancher sur le second. Cote veille, deux actus a ne pas "
            "rater. On garde le cap. Bonne marche.")
out = make_tts(cfg).synthesize(NEW_TEXT, "audio/clone_control.wav")
a, sr = sf.read(out)
print("OK ->", out, "| dur=%.2fs" % (len(a) / sr), "| rms=%.5f" % float(np.sqrt(np.mean(a ** 2))))
