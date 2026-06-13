import asyncio

from walkingdev.channels import make_channel
from walkingdev.channels.cli import CLIChannel
from walkingdev.config import Config


def _cfg(tmp_path):
    return Config({"channel": {"backend": "cli"},
                   "knowledge": {"backend": "local"},
                   "state": {"backend": "sqlite",
                             "sqlite": {"path": str(tmp_path / "s.db")}}}, tmp_path)


def test_make_channel_returns_cli(tmp_path):
    assert isinstance(make_channel(_cfg(tmp_path)), CLIChannel)


def test_onboarding_collects_and_saves(tmp_path, monkeypatch):
    ch = CLIChannel(_cfg(tmp_path))
    answers = iter(["AI, web dev", "3 topics", "", "", "", "all", "", "", "18 min", ""])
    monkeypatch.setattr("builtins.input", lambda *_: next(answers))
    assert ch.state.is_onboarded() is False
    ch.run()  # not onboarded -> onboarding flow
    assert ch.state.is_onboarded() is True
    assert ch.state.get_onboarding()["themes"] == "AI, web dev"


def test_send_tasks_prints(tmp_path, capsys):
    ch = CLIChannel(_cfg(tmp_path))
    asyncio.run(ch.send_tasks("2026-06-13", [
        {"idx": 0, "text": "do a thing", "done": False},
        {"idx": 1, "text": "done thing", "done": True},
    ]))
    out = capsys.readouterr().out
    assert "do a thing" in out and "[x] 2. done thing" in out
