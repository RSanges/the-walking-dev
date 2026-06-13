"""Spike: validate OmniVoice French TTS on this machine.

OmniVoice 'voice design' uses a FIXED vocabulary (not free text), and has no
French accent tag. French TEXT is still rendered natively; we only pick speaker
attributes from the allowed set. For a truly native French voice, voice CLONING
with a French reference sample is the better route (see ref_audio in config).

Valid design tokens (English, comma+space):
  male, female | child, teenager, young adult, middle-aged, elderly
  very low pitch, low pitch, moderate pitch, high pitch, very high pitch, whisper
  american/british/australian/canadian/indian/... accent

    uv run python scripts/spike_omnivoice.py
Outputs: audio/spike_*.wav
"""
import time
from pathlib import Path

import soundfile as sf
import torch
from omnivoice import OmniVoice

OUT = Path(__file__).resolve().parent.parent / "audio"
OUT.mkdir(parents=True, exist_ok=True)

TEXT = (
    "Bonjour. Il est sept heures, voici ton brief du jour. "
    "On commence par la veille, puis tes projets, et on finit par l'agenda. "
    "Allez, on se met en mouvement."
)

SAMPLES = {
    "spike_male_mid_moderate": "male, middle-aged, moderate pitch",
    "spike_male_young_low": "male, young adult, low pitch",
    "spike_female_mid_moderate": "female, middle-aged, moderate pitch",
    "spike_auto": None,
}


def main():
    print("Chargement du modele OmniVoice sur GPU...")
    t0 = time.time()
    model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice", device_map="cuda:0", dtype=torch.float16)
    print("Modele charge en %.1fs" % (time.time() - t0))

    for name, instruct in SAMPLES.items():
        t0 = time.time()
        audio = model.generate(text=TEXT, instruct=instruct) if instruct \
            else model.generate(text=TEXT)
        path = OUT / (name + ".wav")
        sf.write(path, audio[0], 24000)
        print("Genere %s en %.1fs -> %s" % (name, time.time() - t0, path))

    print("\nTermine. Ecoute les fichiers dans:", OUT)


if __name__ == "__main__":
    main()
