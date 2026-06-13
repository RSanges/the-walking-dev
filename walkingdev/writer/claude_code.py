"""Default ScriptWriter: Claude Code headless (claude -p).

Covered by a Claude Max subscription (no API cost). Claude Code brings web search
and the connected MCP servers (Gmail, Calendar) into the run, so by default it
fills the mail/agenda segments live. Set writer.claude_code.connectors: false if
you have no Gmail/Calendar MCP connected.
"""
from .base import ScriptWriter


class ClaudeCodeWriter(ScriptWriter):
    def __init__(self, config):
        super().__init__(config)
        cc = config.section("writer", "claude_code")
        self.connectors = bool(cc.get("connectors", True))

    def _timeout(self) -> int:
        return int(self.config.section("writer", "claude_code").get("timeout_s", 600))
