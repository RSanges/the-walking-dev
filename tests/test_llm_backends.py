import io
import json

from walkingdev import llm
from walkingdev.config import Config


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def test_ask_dispatches_to_local(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode())
        captured["auth"] = req.headers.get("Authorization")
        payload = {"choices": [{"message": {"content": "LOCAL SCRIPT"}}]}
        return _FakeResp(json.dumps(payload).encode())

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    cfg = Config({"writer": {"backend": "local", "local": {
        "base_url": "http://localhost:11434/v1", "model": "llama3.1"}}}, ".")
    out = llm.ask(cfg, "hello")
    assert out == "LOCAL SCRIPT"
    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["body"]["model"] == "llama3.1"
    assert captured["body"]["messages"][0]["content"] == "hello"
    assert captured["auth"].startswith("Bearer ")


def test_local_backend_surfaces_connection_error(monkeypatch):
    import urllib.error

    def boom(req, timeout=None):
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(llm.urllib.request, "urlopen", boom)
    cfg = Config({"writer": {"backend": "local"}}, ".")
    try:
        llm.ask(cfg, "x")
    except RuntimeError as e:
        assert "server running" in str(e).lower()
    else:
        raise AssertionError("expected RuntimeError")


def test_local_writer_builds_local_prompt(monkeypatch):
    from walkingdev.knowledge.base import Brief
    from walkingdev.writer import make_writer
    from walkingdev.writer.base import WriteInput

    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["prompt"] = json.loads(req.data.decode())["messages"][0]["content"]
        payload = {"choices": [{"message": {"content": "x" * 400}}]}
        return _FakeResp(json.dumps(payload).encode())

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    cfg = Config({"writer": {"backend": "local"}}, ".")
    w = make_writer(cfg)
    assert w.connectors is False
    out = w.write_script(WriteInput({"name": "Alex"}, {}, Brief(), "2026-06-13"))
    assert out  # cleaned, non-empty
    # The local prompt must not ask the model to call Gmail/Calendar tools.
    assert "connecteurs Gmail" not in seen["prompt"]


def test_ask_dispatches_to_claude_cli_by_default(monkeypatch):
    calls = {}

    def fake_run_cli(config, prompt, timeout):
        calls["hit"] = True
        return "CLI OUT"

    monkeypatch.setattr(llm, "_complete_claude_cli", fake_run_cli)
    cfg = Config({}, ".")  # default backend = claude_code
    assert llm.ask(cfg, "p") == "CLI OUT"
    assert calls["hit"]
