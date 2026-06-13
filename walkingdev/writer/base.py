"""ScriptWriter: the 'brain' that turns gathered material into the spoken script.

Backends (selected by writer.backend):
  claude_code (default): local Claude Code CLI, headless, covered by a Max plan,
    with MCP connectors (Gmail/Calendar) and web search.
  local: any OpenAI-compatible local server (Ollama, LM Studio, llama.cpp, vLLM).
    Fully offline, no connectors.
  api: the Anthropic API (needs ANTHROPIC_API_KEY).

Each backend builds the same prompt and calls walkingdev.llm.ask; the only
difference is whether it has live mail/calendar connectors (``connectors``).
"""
from dataclasses import dataclass

from .. import llm
from .prompt import build_prompt, clean_script


@dataclass
class WriteInput:
    profile: dict          # onboarding answers (themes, tone, address...)
    evening: dict          # last evening answers
    brief: object          # knowledge.Brief
    date: str
    news: object = None        # list[dict] of fresh RSS items (walkingdev.news)
    prev_tasks: object = None   # yesterday's tasks [{text, done}] for follow-through


class ScriptWriter:
    """Base script writer: build the prompt, call the configured LLM backend,
    clean the result. Backends subclass this and only tweak ``connectors`` and
    ``_timeout``."""

    #: whether this backend can call live Gmail/Calendar tools.
    connectors: bool = False

    def __init__(self, config):
        self.config = config
        self.timeout = self._timeout()

    def _timeout(self) -> int:
        return 600

    def write_script(self, data: WriteInput) -> str:
        prompt = build_prompt(data, connectors=self.connectors)
        return clean_script(llm.ask(self.config, prompt, timeout=self.timeout))


# Backwards/explicit interface marker for type checkers; the concrete backends
# subclass ScriptWriter and only tweak `connectors` / `_timeout`.
__all__ = ["ScriptWriter", "WriteInput"]
