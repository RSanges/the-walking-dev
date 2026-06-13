from .base import StateStore
from .sqlite import SQLiteStore


def make_state(config) -> StateStore:
    backend = config.get("state", "backend", default="sqlite")
    if backend == "sqlite":
        path = config.get("state", "sqlite", "path", default="data/walkingdev.db")
        return SQLiteStore(str(config.resolve(path)))
    raise NotImplementedError("state backend not implemented: " + str(backend))
