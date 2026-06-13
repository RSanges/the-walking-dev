from .base import ScriptWriter


def make_writer(config) -> ScriptWriter:
    backend = config.get("writer", "backend", default="claude_code")
    if backend == "claude_code":
        from .claude_code import ClaudeCodeWriter
        return ClaudeCodeWriter(config)
    if backend == "api":
        from .api import ApiWriter
        return ApiWriter(config)
    raise NotImplementedError("writer backend non implemente: " + str(backend))
