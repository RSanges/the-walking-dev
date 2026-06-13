"""Default ScriptWriter: invoke Claude Code headless (claude -p).

Covered by a Claude Max subscription (no API cost). Claude Code brings web
search and the connected MCP servers (Gmail, Calendar) into the run. For an
unattended nightly run, tools must be usable without interactive approval, so a
permission mode (default: bypassPermissions) is passed through.

The actual subprocess call lives in walkingdev.llm.run_cli (shared with the
evening-questions and task-extraction call sites).
"""
from .. import llm
from .base import ScriptWriter, WriteInput
from .prompt import build_prompt, clean_script


class ClaudeCodeWriter(ScriptWriter):
    def __init__(self, config):
        self.config = config
        self.timeout = int(config.section("writer", "claude_code").get("timeout_s", 600))

    def write_script(self, data: WriteInput) -> str:
        out = llm.run_cli(self.config, build_prompt(data), timeout=self.timeout)
        return clean_script(out)
