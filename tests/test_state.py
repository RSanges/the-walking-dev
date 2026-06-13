import sqlite3

from walkingdev.state.sqlite import SQLiteStore


def test_episode_roundtrip_with_duration(tmp_path):
    s = SQLiteStore(str(tmp_path / "s.db"))
    s.record_episode("2026-06-13", "http://x/e.mp3", "script", 123.4)
    eps = s.list_episodes()
    assert eps == [{"date": "2026-06-13", "url": "http://x/e.mp3", "duration": 123.4}]


def test_onboarding_and_evening(tmp_path):
    s = SQLiteStore(str(tmp_path / "s.db"))
    assert s.is_onboarded() is False
    s.save_onboarding({"name": "Alex"})
    assert s.is_onboarded() is True
    assert s.get_onboarding()["name"] == "Alex"
    s.save_evening("2026-06-13", {"energy": "4"})
    assert s.get_evening("2026-06-13") == {"energy": "4"}
    assert s.get_evening("1999-01-01") == {}


def test_tasks_and_toggle(tmp_path):
    s = SQLiteStore(str(tmp_path / "s.db"))
    s.save_tasks("2026-06-13", ["a", "b"])
    assert [t["text"] for t in s.get_tasks("2026-06-13")] == ["a", "b"]
    assert s.toggle_task("2026-06-13", 0) is True
    assert s.toggle_task("2026-06-13", 0) is False
    # Missing row returns None, never a fabricated True.
    assert s.toggle_task("2026-06-13", 99) is None
    assert s.toggle_task("1999-01-01", 0) is None


def test_migrates_legacy_schema_without_duration(tmp_path):
    p = tmp_path / "old.db"
    c = sqlite3.connect(p)
    c.executescript(
        "CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT);"
        "CREATE TABLE evening (date TEXT PRIMARY KEY, answers TEXT);"
        "CREATE TABLE episodes (date TEXT PRIMARY KEY, url TEXT, script TEXT, created_at TEXT);"
        "CREATE TABLE tasks (date TEXT, idx INTEGER, text TEXT, done INTEGER DEFAULT 0,"
        " PRIMARY KEY(date, idx));"
    )
    c.execute("INSERT INTO episodes(date, url, script) VALUES('2026-06-12','u','old')")
    c.commit()
    c.close()

    s = SQLiteStore(str(p))  # should ALTER TABLE ADD COLUMN duration, keep data
    eps = s.list_episodes()
    assert eps[0]["date"] == "2026-06-12"
    assert eps[0]["duration"] is None
    s.record_episode("2026-06-13", "u2", "new", 9.0)
    assert s.list_episodes()[0]["duration"] == 9.0
