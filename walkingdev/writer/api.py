"""Fallback ScriptWriter: Anthropic API key. For users without Claude Code.

Note: no MCP connectors here; mail/agenda must be passed in by the caller or
fetched separately. Web search via the API tool if enabled.
"""
from .base import ScriptWriter, WriteInput
from .prompt import build_prompt, clean_script


class ApiWriter(ScriptWriter):
    def __init__(self, config):
        from ..config import Config
        self.model = config.get("writer", "api", "model", default="claude-opus-4-8")
        self.key = Config.env("ANTHROPIC_API_KEY")
        if not self.key:
            raise RuntimeError("ANTHROPIC_API_KEY manquant (writer.backend = api)")

    def write_script(self, data: WriteInput) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": build_prompt(data)}],
        )
        return clean_script(
            "".join(b.text for b in msg.content if b.type == "text"))
