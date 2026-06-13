import os
from pathlib import Path

from walkingdev.config import Config, _load_dotenv


def test_section_normalises_none():
    c = Config({"tts": {"omnivoice": None}}, Path("."))
    assert c.section("tts", "omnivoice") == {}
    assert c.section("missing", "key") == {}


def test_get_nested_and_default():
    c = Config({"a": {"b": {"c": 1}}}, Path("."))
    assert c.get("a", "b", "c") == 1
    assert c.get("a", "x", default="d") == "d"


def test_resolve_relative_vs_absolute(tmp_path):
    c = Config({}, tmp_path)
    assert c.resolve("data/x.db") == tmp_path / "data" / "x.db"
    abs_path = tmp_path / "abs"
    assert c.resolve(str(abs_path)) == abs_path


def test_dotenv_strips_quotes_and_export(tmp_path, monkeypatch):
    for k in ("TOK", "PW", "PLAIN", "EXP"):
        monkeypatch.delenv(k, raising=False)
    env = tmp_path / ".env"
    env.write_text(
        'TOK="123:abc"\n'
        "PW='p#ss word'\n"
        "PLAIN=value\n"
        "export EXP=exported\n"
        "# comment\n"
        "\n",
        encoding="utf-8",
    )
    _load_dotenv(env)
    assert os.environ["TOK"] == "123:abc"
    assert os.environ["PW"] == "p#ss word"
    assert os.environ["PLAIN"] == "value"
    assert os.environ["EXP"] == "exported"


def test_dotenv_does_not_override_real_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ALREADY", "real")
    env = tmp_path / ".env"
    env.write_text("ALREADY=fromfile\n", encoding="utf-8")
    _load_dotenv(env)
    assert os.environ["ALREADY"] == "real"
