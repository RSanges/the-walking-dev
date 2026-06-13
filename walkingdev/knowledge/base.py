"""KnowledgeProvider: where projects/objectives come from, and where the daily
trace is written. LocalKnowledge works for everyone; ObsidianKnowledge reads a
structured vault. Add a provider by implementing this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Brief:
    projects: list[dict] = field(default_factory=list)   # [{name, status, next}]
    objectives: list[str] = field(default_factory=list)
    notes: str = ""
    about: str = ""   # user profile ("À propos de moi"), for personalisation
    vault: str = ""   # full vault dump (decisions, knowledge, people, etc.)


class KnowledgeProvider(ABC):
    @abstractmethod
    def gather(self) -> Brief:
        """Read projects + objectives to feed the projects/objectives segment."""

    @abstractmethod
    def write_journal(self, date: str, summary: str) -> None:
        """Leave a dated trace of the episode (optional for some providers)."""
