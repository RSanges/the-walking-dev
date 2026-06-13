"""StateStore interface: onboarding answers, evening answers, episodes."""
from abc import ABC, abstractmethod
from typing import Any


class StateStore(ABC):
    @abstractmethod
    def save_onboarding(self, answers: dict[str, Any]) -> None: ...
    @abstractmethod
    def get_onboarding(self) -> dict[str, Any]: ...
    @abstractmethod
    def is_onboarded(self) -> bool: ...
    @abstractmethod
    def save_evening(self, date: str, answers: dict[str, Any]) -> None: ...
    @abstractmethod
    def get_evening(self, date: str) -> dict[str, Any]: ...
    @abstractmethod
    def record_episode(self, date: str, url: str, script: str,
                       duration: float | None = None) -> None: ...
    @abstractmethod
    def list_episodes(self) -> list[dict]: ...  # [{date, url, duration}], newest first
    @abstractmethod
    def save_tasks(self, date: str, texts: list[str]) -> None: ...
    @abstractmethod
    def get_tasks(self, date: str) -> list[dict]: ...  # [{idx, text, done}]
    @abstractmethod
    def toggle_task(self, date: str, idx: int) -> bool | None: ...  # new state, or None if missing
