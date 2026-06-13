"""Shared test fixtures. All tests are offline: no network, no GPU, no Telegram."""
from pathlib import Path

import pytest

from walkingdev.config import Config


@pytest.fixture
def cfg(tmp_path: Path):
    """A Config rooted at a temp dir, so file paths never touch the real repo."""
    def _make(data: dict | None = None) -> Config:
        return Config(data or {}, tmp_path)
    return _make
