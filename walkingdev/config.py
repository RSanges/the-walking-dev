"""Load config.yaml + .env into one object.

The project root (the folder holding config.yaml, .env, audio/ and data/) is
resolved once and exposed as ``Config.root`` so every relative path in the code
anchors to the same place regardless of the current working directory (the bot
and the nightly run can be launched from different CWDs by a scheduler).
"""
import os
from pathlib import Path

import yaml


def _resolve_root() -> Path:
    """Locate the project root.

    Order: an explicit ``WALKINGDEV_HOME`` env var, else the current directory
    if it already holds a config file (the normal clone-and-run case), else the
    package parent (a source checkout run from elsewhere).
    """
    env = os.environ.get("WALKINGDEV_HOME")
    if env:
        return Path(env).expanduser().resolve()
    cwd = Path.cwd()
    if (cwd / "config.yaml").exists() or (cwd / "config.example.yaml").exists():
        return cwd
    return Path(__file__).resolve().parent.parent


class Config:
    def __init__(self, data: dict, root: Path):
        self._d = data or {}
        self.root = root

    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        root = _resolve_root()
        p = Path(path)
        if not p.is_absolute():
            p = root / p
        if not p.exists():
            raise FileNotFoundError(
                f"{p} not found. Copy config.example.yaml to config.yaml and "
                "edit it (see the README), then try again."
            )
        _load_dotenv(root / ".env")
        with open(p, encoding="utf-8") as f:
            return cls(yaml.safe_load(f) or {}, root)

    def get(self, *keys, default=None):
        cur = self._d
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def section(self, *keys) -> dict:
        """Return a config sub-dict, normalising a missing/empty (``None``)
        YAML section to ``{}`` so callers can always ``.get(...)`` on it."""
        val = self.get(*keys)
        return val if isinstance(val, dict) else {}

    def resolve(self, path: str) -> Path:
        """Resolve a possibly-relative path against the project root."""
        p = Path(path)
        return p if p.is_absolute() else (self.root / p)

    @staticmethod
    def env(name: str, default: str = "") -> str:
        return os.environ.get(name, default)


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        k, v = line.split("=", 1)
        v = v.strip()
        # Strip a single pair of matching surrounding quotes, the usual way to
        # protect a value containing spaces or '#'.
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        os.environ.setdefault(k.strip(), v)
