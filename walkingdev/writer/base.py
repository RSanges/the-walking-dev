"""ScriptWriter: the 'brain' that turns gathered material into the spoken script.

claude_code (default): runs the local Claude Code CLI headless, covered by a Max
subscription, with access to MCP connectors (Gmail/Calendar) and web search.
api: fallback using an Anthropic API key for users without Claude Code.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WriteInput:
    profile: dict          # onboarding answers (themes, tone, address...)
    evening: dict          # last evening answers
    brief: object          # knowledge.Brief
    date: str
    news: object = None        # list[dict] of fresh RSS items (walkingdev.news)
    prev_tasks: object = None   # yesterday's tasks [{text, done}] for follow-through


class ScriptWriter(ABC):
    @abstractmethod
    def write_script(self, data: WriteInput) -> str:
        """Return the final narration text (segments already ordered)."""
