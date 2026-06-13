"""OmniVoiceEngine: local, GPU, open-source TTS (k2-fsa/OmniVoice).

API per the official repo (validated in scripts/spike_omnivoice.py):
    from omnivoice import OmniVoice
    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cuda:0",
                                      dtype=torch.float16)
    audio = model.generate(text=..., instruct="male, young adult, low pitch")  # design
    audio = model.generate(text=..., ref_audio="ref.wav", ref_text="...")       # clone
    sf.write("out.wav", audio[0], 24000)

Voice design uses a FIXED vocabulary (no French accent tag); French text is still
rendered natively. Diffusion is stochastic, so a chunk can occasionally come out
silent/garbled: we re-roll any take whose RMS falls below ``min_rms``, which keeps
the unattended nightly run robust.
"""
import logging
from pathlib import Path

from .base import TTSEngine

log = logging.getLogger(__name__)


class OmniVoiceEngine(TTSEngine):
    def __init__(self, config):
        c = config.section("tts", "omnivoice")
        # Designed voice (default): an instruct string describing the narrator.
        self.instruct = c.get("instruct", "male, young adult, low pitch")
        # Optional voice cloning instead of design:
        self.ref_audio = c.get("ref_audio")
        if self.ref_audio:
            self.ref_audio = str(config.resolve(self.ref_audio))
        # ref_text: inline, else a sidecar <ref_audio>.txt (transcription).
        self.ref_text = c.get("ref_text") or _sidecar_text(self.ref_audio)
        self.device = c.get("device", "cuda:0")
        self.sample_rate = int(c.get("sample_rate", 24000))
        self.num_step = c.get("num_step")
        self.speed = c.get("speed")
        self.max_chars = int(c.get("max_chars", 600))
        # Fixed seed => reproducible designed voice (same timbre every run).
        self.seed = c.get("seed")
        # Anti-silence guard (re-roll degenerate diffusion takes).
        self.min_rms = float(c.get("min_rms", 0.02))
        self.max_retries = int(c.get("max_retries", 3))
        self._model = None

    def _load(self):
        if self._model is None:
            import torch
            from omnivoice import OmniVoice
            if self.device.startswith("cuda") and not torch.cuda.is_available():
                raise RuntimeError(
                    f"tts.omnivoice.device is '{self.device}' but no CUDA GPU is "
                    "available. Install the CUDA PyTorch build (see "
                    "scripts/install_omnivoice.ps1) or set device to 'cpu'.")
            self._model = OmniVoice.from_pretrained(
                "k2-fsa/OmniVoice", device_map=self.device, dtype=torch.float16)
        return self._model

    def _gen_kwargs(self, text: str) -> dict:
        kw = {"text": text}
        if self.ref_audio:
            kw["ref_audio"] = self.ref_audio
            kw["ref_text"] = self.ref_text or ""
        else:
            kw["instruct"] = self.instruct
        if self.num_step:
            kw["num_step"] = self.num_step
        if self.speed:
            kw["speed"] = self.speed
        return kw

    def _generate_chunk(self, text: str):
        """Generate one chunk, re-rolling silent/degenerate takes. Returns the
        best take (highest RMS) seen across attempts."""
        import numpy as np
        model = self._load()
        kw = self._gen_kwargs(text)
        best, best_rms = None, -1.0
        for attempt in range(self.max_retries + 1):
            if self.seed is not None:
                # Reseed per attempt so a re-roll yields a *different* take while
                # staying reproducible run-to-run.
                import torch
                s = int(self.seed) + attempt
                torch.manual_seed(s)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed_all(s)
            a = np.asarray(model.generate(**kw)[0], dtype="float32")
            rms = float(np.sqrt(np.mean(a ** 2))) if a.size else 0.0
            if rms > best_rms:
                best, best_rms = a, rms
            if best_rms >= self.min_rms:
                break
        if best_rms < self.min_rms:
            log.warning("chunk stayed below min_rms (%.4f) after %d tries",
                        best_rms, self.max_retries + 1)
        return best

    def synthesize(self, text: str, out_path: str) -> str:
        import numpy as np
        import soundfile as sf
        pieces = [self._generate_chunk(ch) for ch in _split(text, self.max_chars)]
        full = np.concatenate(pieces) if pieces else np.zeros(1, dtype="float32")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_path, full, self.sample_rate)
        return out_path


def _sidecar_text(ref_audio):
    """Read <ref_audio>.txt if present (transcription of the reference clip)."""
    if not ref_audio:
        return None
    p = Path(ref_audio).with_suffix(".txt")
    return p.read_text(encoding="utf-8").strip() if p.exists() else None


def _split(text: str, max_chars: int = 600) -> list[str]:
    """Split into chunks <= max_chars, breaking on sentence boundaries (. ? !)
    and hard-wrapping any single sentence longer than max_chars."""
    import re
    sentences = re.split(r"(?<=[.?!])\s+", text.replace("\n", " ").strip())
    out, cur = [], ""
    for sent in sentences:
        if not sent:
            continue
        while len(sent) > max_chars:           # hard-wrap an oversized sentence
            if cur:
                out.append(cur.strip())
                cur = ""
            out.append(sent[:max_chars].strip())
            sent = sent[max_chars:]
        if len(cur) + len(sent) + 1 > max_chars and cur:
            out.append(cur.strip())
            cur = ""
        cur += sent + " "
    if cur.strip():
        out.append(cur.strip())
    return out
