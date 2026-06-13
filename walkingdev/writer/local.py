"""Fully-local ScriptWriter (writer.backend = local).

Talks to any OpenAI-compatible local server, so nothing leaves your machine:

  - Ollama          base_url: http://localhost:11434/v1   (model e.g. "llama3.1")
  - LM Studio       base_url: http://localhost:1234/v1
  - llama.cpp server, vLLM, text-generation-webui, ...

No web/mail/calendar connectors: the mail and agenda segments are skipped. The
HTTP call is made in walkingdev.llm (stdlib only, no extra dependency).
"""
from .base import ScriptWriter


class LocalWriter(ScriptWriter):
    connectors = False

    def _timeout(self) -> int:
        return int(self.config.section("writer", "local").get("timeout_s", 600))
