"""Environment and configuration check, surfaced via `walkingdev doctor`."""
import importlib.util
import os
import shutil
from pathlib import Path

from .config import Config


def check(config_path: str = "config.yaml") -> int:
    ok = True

    def line(label, good, hint=""):
        nonlocal ok
        ok = ok and good
        mark = "OK " if good else "XX "
        print(mark + label + ("" if good else "  -> " + hint))

    root = Path.cwd()
    cfg = None
    try:
        cfg = Config.load(config_path)
        root = cfg.root
    except FileNotFoundError:
        pass
    except Exception as e:  # malformed YAML, etc.
        line("config.yaml loads", False, repr(e))

    line("config.yaml present", cfg is not None,
         "copy config.example.yaml to config.yaml")
    line(".env present", (root / ".env").exists(),
         "copy .env.example to .env and fill in the secrets")

    # Backend-aware checks (only when config loaded; .env is now in the environ).
    if cfg is not None:
        writer = cfg.get("writer", "backend", default="claude_code")
        if writer == "claude_code":
            command = cfg.get("writer", "claude_code", "command", default="claude")
            line(f"writer '{command}' on PATH", shutil.which(command) is not None,
                 "install Claude Code, or set writer.backend: api")
        else:
            line("ANTHROPIC_API_KEY set", bool(os.environ.get("ANTHROPIC_API_KEY")),
                 "writer.backend is 'api' but no key in .env")

        if cfg.get("channel", "backend", default="telegram") == "telegram":
            line("TELEGRAM_BOT_TOKEN set", bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
                 "create a bot via @BotFather and put the token in .env")

        if cfg.get("knowledge", "backend", default="local") == "obsidian":
            vault = cfg.get("knowledge", "obsidian", "vault_path", default="")
            line("Obsidian vault_path exists", bool(vault) and Path(vault).is_dir(),
                 "set knowledge.obsidian.vault_path to your vault folder")

        if cfg.get("hosting", "backend", default="local") in ("ftp", "sftp", "ftps"):
            line("FTP_USER / FTP_PASSWORD set",
                 bool(os.environ.get("FTP_USER") and os.environ.get("FTP_PASSWORD")),
                 "set FTP_USER and FTP_PASSWORD in .env")

        if cfg.get("tts", "backend", default="omnivoice") == "omnivoice":
            _check_gpu(cfg, line)

    # Encoder for the MP3 packaging step.
    line("lameenc importable", importlib.util.find_spec("lameenc") is not None,
         "pip install lameenc")

    print("\nDoctor:", "all green" if ok else "some items need attention")
    return 0 if ok else 1


def _check_gpu(cfg, line):
    device = cfg.get("tts", "omnivoice", "device", default="cuda:0")
    if not str(device).startswith("cuda"):
        return
    if importlib.util.find_spec("torch") is None:
        line("torch (CUDA) installed", False,
             "run scripts/install_omnivoice.ps1 (GPU TTS)")
        return
    try:
        import torch
        line("CUDA GPU available", torch.cuda.is_available(),
             "no CUDA GPU detected; set tts.omnivoice.device: cpu")
    except Exception as e:  # noqa
        line("torch imports", False, repr(e))
