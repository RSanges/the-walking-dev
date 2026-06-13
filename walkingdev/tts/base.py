"""TTSEngine: turn the script text into an audio file."""
from abc import ABC, abstractmethod


class TTSEngine(ABC):
    @abstractmethod
    def synthesize(self, text: str, out_path: str) -> str:
        """Render `text` to an audio file at out_path, return the path."""
