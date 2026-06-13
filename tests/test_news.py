import time
from types import SimpleNamespace

from walkingdev import news
from walkingdev.config import Config

NOW = time.time()


def _entry(title, ts, summary="", link="", tags=None):
    return {
        "title": title,
        "summary": summary,
        "link": link or ("http://x/" + title.replace(" ", "-")),
        "published_parsed": time.gmtime(ts),
        "tags": tags or [],
    }


def _feed(*entries):
    return SimpleNamespace(feed={"title": "Src"}, entries=list(entries), bozo=0)


def _cfg(feeds, **over):
    base = {"news": {"feeds": feeds, "window_hours": 48, "max_items_per_feed": 4,
                     "max_per_theme": 3, "max_total": 16}}
    base["news"].update(over)
    return Config(base, ".")


def test_drops_stale_and_undated(monkeypatch):
    feed = _feed(
        _entry("fresh", NOW - 3600),
        _entry("stale", NOW - 10 * 24 * 3600),
    )
    feed.entries.append({"title": "undated", "summary": "", "link": "u", "tags": []})
    monkeypatch.setattr(news, "_parse_feed", lambda url, t: feed)
    items = news.gather_news(_cfg({"T": ["u1"]}))
    titles = [i["title"] for i in items]
    assert "fresh" in titles and "stale" not in titles and "undated" not in titles


def test_excludes_keywords(monkeypatch):
    feed = _feed(
        _entry("Serious AI news", NOW - 3600),
        _entry("Celebrity horoscope buzz", NOW - 3600),
    )
    monkeypatch.setattr(news, "_parse_feed", lambda url, t: feed)
    items = news.gather_news(_cfg({"T": ["u1"]}))
    titles = [i["title"] for i in items]
    assert "Serious AI news" in titles
    assert "Celebrity horoscope buzz" not in titles


def test_dedup_cross_theme_keeps_first(monkeypatch):
    same = _entry("Shared story", NOW - 3600, link="http://x/shared")
    feeds = {"A": ["ua"], "B": ["ub"]}

    def fake(url, t):
        return _feed(dict(same))
    monkeypatch.setattr(news, "_parse_feed", fake)
    items = news.gather_news(_cfg(feeds))
    assert sum(1 for i in items if i["link"] == "http://x/shared") == 1
    assert items[0]["theme"] == "A"  # earlier theme wins


def test_per_feed_cap(monkeypatch):
    feed = _feed(*[_entry(f"n{i}", NOW - 60 * i) for i in range(10)])
    monkeypatch.setattr(news, "_parse_feed", lambda url, t: feed)
    items = news.gather_news(_cfg({"T": ["u1"]}, max_items_per_feed=2, max_per_theme=10))
    assert len(items) == 2


def test_unreachable_feed_is_skipped(monkeypatch):
    monkeypatch.setattr(news, "_parse_feed", lambda url, t: None)
    items = news.gather_news(_cfg({"T": ["u1"]}))
    assert items == []
    assert news.format_for_prompt([]).startswith("(aucune")
