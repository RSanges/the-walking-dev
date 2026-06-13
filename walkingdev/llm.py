"""Single entry point for asking the configured Claude Code CLI a question.

Used by the script writer, the adaptive evening questions and the daily task
extraction. Headless and covered by a Claude Max subscription (no API cost).

The prompt is fed on STDIN (not as a CLI argument): it can be large (the whole
vault is injected) and Windows caps a command line at ~32 KB. Passing it on argv
would also expose it in the process list.
"""
import logging
import shutil
import subprocess

log = logging.getLogger(__name__)


def run_cli(config, prompt: str, timeout: int = 300) -> str:
    """Run ``claude -p`` headless with the prompt on stdin; return stdout.

    Raises ``RuntimeError`` on a non-zero exit or if the CLI is not found.
    """
    cc = config.section("writer", "claude_code")
    command = cc.get("command", "claude")
    mode = cc.get("permission_mode", "bypassPermissions")
    # Resolve via PATH (honours PATHEXT, so npm's claude.cmd is found on Windows);
    # fall back to the bare name so an absolute path in config still works.
    exe = shutil.which(command) or command
    cmd = [exe, "-p"]
    if mode:
        cmd += ["--permission-mode", mode]
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,            # prompt on stdin, not argv (size- and privacy-safe)
            capture_output=True, text=True, encoding="utf-8",
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Claude Code CLI '{command}' not found on PATH. Install it, set "
            "writer.claude_code.command, or use writer.backend: api."
        ) from e
    if proc.returncode != 0:
        raise RuntimeError("claude -p failed: " + (proc.stderr or "")[:500])
    return proc.stdout


# Back-compat alias (older call sites used ``llm.ask``).
ask = run_cli


def parse_json_array(raw: str) -> list:
    """Extract the first top-level JSON array from a model reply."""
    import json
    s, e = raw.find("["), raw.rfind("]")
    if s == -1 or e == -1 or e < s:
        return []
    return json.loads(raw[s:e + 1])
