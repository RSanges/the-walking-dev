from .base import TTSEngine


def make_tts(config) -> TTSEngine:
    backend = config.get("tts", "backend", default="omnivoice")
    if backend == "omnivoice":
        from .omnivoice import OmniVoiceEngine
        return OmniVoiceEngine(config)
    raise NotImplementedError("tts backend not implemented: " + str(backend))
