from .base import ScriptWriter, WriteInput

__all__ = ["ScriptWriter", "WriteInput", "make_writer"]


def make_writer(config) -> ScriptWriter:
    backend = config.get("writer", "backend", default="claude_code")
    if backend == "claude_code":
        from .claude_code import ClaudeCodeWriter
        return ClaudeCodeWriter(config)
    if backend == "local":
        from .local import LocalWriter
        return LocalWriter(config)
    if backend == "api":
        from .api import ApiWriter
        return ApiWriter(config)
    raise NotImplementedError("writer backend not implemented: " + str(backend))
