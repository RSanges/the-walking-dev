from pathlib import Path

import numpy as np
import soundfile as sf

for p in sorted(Path("audio").glob("spike_*.wav")):
    a, sr = sf.read(p)
    a = np.asarray(a, dtype=float)
    if a.ndim > 1:
        a = a.mean(axis=1)
    dur = len(a) / sr
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    rms = float(np.sqrt(np.mean(a**2))) if a.size else 0.0
    print(f"{p.name:34s} sr={sr} dur={dur:5.2f}s peak={peak:.4f} rms={rms:.5f}")
