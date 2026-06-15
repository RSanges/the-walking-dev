"""Single text-generation primitive, shared by the script writer, the adaptive
evening questions and the daily task extraction.

``ask()`` dispatches on ``writer.backend`` so every LLM call in the project uses
the same engine you configured:

- ``claude_code`` (default): the local Claude Code CLI, headless (``claude -p``),
  covered by a Claude Max plan. Brings web search + connected MCP tools.
- ``local``: any OpenAI-compatible local server (Ollama, LM Studio, llama.cpp,
  vLLM, text-generation-webui...). Fully offline: the prompt never leaves the
  machine. No web/mail/calendar tools.
- ``api``: the Anthropic API (needs ANTHROPIC_API_KEY).

The prompt is always sent on stdin / in the request body, never on argv (it can
be large, and argv would expose it in the process list).
"""
import json
import logging
import shutil
import subprocess
import urllib.error
import urllib.request

from .config import Config

log = logging.getLogger(__name__)


def ask(config, prompt: str, timeout: int = 300) -> str:
    """Generate text for ``prompt`` using the configured writer backend."""
    backend = config.get("writer", "backend", default="claude_code")
    if backend == "local":
        return _complete_local(config, prompt, timeout)
    if backend == "api":
        return _complete_api(config, prompt, timeout)
    return _complete_claude_cli(config, prompt, timeout)


# Back-compat alias (older call sites used llm.run_cli for the Claude Code path).
def run_cli(config, prompt: str, timeout: int = 300) -> str:
    return _complete_claude_cli(config, prompt, timeout)


def _complete_claude_cli(config, prompt: str, timeout: int) -> str:
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
            "writer.claude_code.command, or switch writer.backend to 'local'/'api'."
        ) from e
    if proc.returncode != 0:
        # The Claude CLI prints some failures (e.g. "401 Invalid authentication
        # credentials") to stdout, not stderr. Fall back to stdout so the reason
        # actually surfaces in logs and alerts instead of an empty message.
        detail = (proc.stderr or "").strip() or (proc.stdout or "").strip()
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {detail[:500]}")
    return proc.stdout


def _complete_local(config, prompt: str, timeout: int) -> str:
    """Call an OpenAI-compatible local server's /chat/completions endpoint."""
    loc = config.section("writer", "local")
    base = (loc.get("base_url") or "http://localhost:11434/v1").rstrip("/")
    model = loc.get("model", "llama3.1")
    key = Config.env("LOCAL_LLM_API_KEY") or loc.get("api_key") or "not-needed"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": float(loc.get("temperature", 0.7)),
        "max_tokens": int(loc.get("max_tokens", 4000)),
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Local LLM request to {base} failed ({e}). Is the server running? "
            "(e.g. `ollama serve`, LM Studio, llama.cpp). Check writer.local.base_url."
        ) from e
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected local LLM response: {data!r}") from e


def _complete_api(config, prompt: str, timeout: int) -> str:
    model = config.get("writer", "api", "model", default="claude-opus-4-8")
    key = Config.env("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY missing (writer.backend = api)")
    import anthropic
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=model, max_tokens=int(config.get("writer", "api", "max_tokens", default=4000)),
        messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in msg.content if b.type == "text")


def parse_json_array(raw: str) -> list:
    """Extract the first top-level JSON array from a model reply."""
    s, e = raw.find("["), raw.rfind("]")
    if s == -1 or e == -1 or e < s:
        return []
    return json.loads(raw[s:e + 1])
