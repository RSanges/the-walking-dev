"""ScriptWriter backed by the Anthropic API (writer.backend = api).

For users without Claude Code. No MCP connectors here, so mail/agenda segments
are skipped (the model is not asked to call tools it does not have). Needs
ANTHROPIC_API_KEY in .env. The request itself is made in walkingdev.llm.
"""
from .base import ScriptWriter


class ApiWriter(ScriptWriter):
    connectors = False

    def _timeout(self) -> int:
        return int(self.config.section("writer", "api").get("timeout_s", 600))
