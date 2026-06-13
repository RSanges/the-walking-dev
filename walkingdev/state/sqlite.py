"""Zero-config local store: a single SQLite file. Default for clone-and-run."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from .base import StateStore


class SQLiteStore(StateStore):
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self):
        # A short busy timeout lets the bot and the nightly run share the file
        # without spurious "database is locked" errors.
        c = sqlite3.connect(self.path, timeout=30)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with closing(self._conn()) as c, c:
            c.executescript(
                "CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);"
                "CREATE TABLE IF NOT EXISTS evening (date TEXT PRIMARY KEY, answers TEXT);"
                "CREATE TABLE IF NOT EXISTS episodes (date TEXT PRIMARY KEY, url TEXT,"
                " script TEXT, created_at TEXT, duration REAL);"
                "CREATE TABLE IF NOT EXISTS tasks (date TEXT, idx INTEGER, text TEXT,"
                " done INTEGER DEFAULT 0, PRIMARY KEY(date, idx));"
            )
            # Migrate older DBs that predate the duration column.
            cols = {r["name"] for r in c.execute("PRAGMA table_info(episodes)")}
            if "duration" not in cols:
                c.execute("ALTER TABLE episodes ADD COLUMN duration REAL")

    def save_onboarding(self, answers: dict[str, Any]) -> None:
        with closing(self._conn()) as c, c:
            c.execute("INSERT OR REPLACE INTO kv(k, v) VALUES('onboarding', ?)",
                      (json.dumps(answers, ensure_ascii=False),))

    def get_onboarding(self) -> dict[str, Any]:
        with closing(self._conn()) as c:
            row = c.execute("SELECT v FROM kv WHERE k='onboarding'").fetchone()
            return json.loads(row["v"]) if row else {}

    def is_onboarded(self) -> bool:
        return bool(self.get_onboarding())

    def save_evening(self, date: str, answers: dict[str, Any]) -> None:
        with closing(self._conn()) as c, c:
            c.execute("INSERT OR REPLACE INTO evening(date, answers) VALUES(?, ?)",
                      (date, json.dumps(answers, ensure_ascii=False)))

    def get_evening(self, date: str) -> dict[str, Any]:
        with closing(self._conn()) as c:
            row = c.execute("SELECT answers FROM evening WHERE date=?",
                            (date,)).fetchone()
            return json.loads(row["answers"]) if row else {}

    def record_episode(self, date: str, url: str, script: str,
                       duration: float | None = None) -> None:
        with closing(self._conn()) as c, c:
            c.execute("INSERT OR REPLACE INTO episodes(date, url, script, created_at,"
                      " duration) VALUES(?, ?, ?, datetime('now'), ?)",
                      (date, url, script, duration))

    def list_episodes(self) -> list[dict]:
        with closing(self._conn()) as c:
            rows = c.execute(
                "SELECT date, url, duration FROM episodes ORDER BY date DESC"
            ).fetchall()
            return [{"date": r["date"], "url": r["url"], "duration": r["duration"]}
                    for r in rows]

    def save_tasks(self, date: str, texts: list[str]) -> None:
        with closing(self._conn()) as c, c:
            c.execute("DELETE FROM tasks WHERE date=?", (date,))
            c.executemany(
                "INSERT INTO tasks(date, idx, text, done) VALUES(?, ?, ?, 0)",
                [(date, i, t) for i, t in enumerate(texts)])

    def get_tasks(self, date: str) -> list[dict]:
        with closing(self._conn()) as c:
            rows = c.execute(
                "SELECT idx, text, done FROM tasks WHERE date=? ORDER BY idx",
                (date,)).fetchall()
            return [{"idx": r["idx"], "text": r["text"], "done": bool(r["done"])}
                    for r in rows]

    def toggle_task(self, date: str, idx: int) -> bool | None:
        """Flip a task's done flag atomically. Returns the new state, or None if
        the (date, idx) row does not exist (e.g. a stale checklist)."""
        with closing(self._conn()) as c, c:
            cur = c.execute(
                "UPDATE tasks SET done = 1 - done WHERE date=? AND idx=?",
                (date, idx))
            if cur.rowcount != 1:
                return None
            row = c.execute("SELECT done FROM tasks WHERE date=? AND idx=?",
                            (date, idx)).fetchone()
            return bool(row["done"])
