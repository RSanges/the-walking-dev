import re

from walkingdev.hosting.feed import _hms, build_feed

EPISODES = [
    {"url": "http://x/episodes/2026-06-13.mp3", "title": "P - 2026-06-13",
     "date": "2026-06-13", "length": 10, "duration": 125},
    {"url": "http://x/episodes/2026-06-12.mp3", "title": "P - 2026-06-12",
     "date": "2026-06-12", "length": 20, "duration": 3700},
]


def _titles(xml):
    return re.findall(r"<title>(P - 2026[^<]+)</title>", xml)


def test_feed_lists_newest_first():
    xml = build_feed("P", "http://x", "http://x/feed.xml", EPISODES).decode()
    assert _titles(xml) == ["P - 2026-06-13", "P - 2026-06-12"]


def test_feed_emits_itunes_duration():
    xml = build_feed("P", "http://x", "http://x/feed.xml", EPISODES).decode()
    durations = re.findall(r"<itunes:duration>([^<]+)</itunes:duration>", xml)
    assert durations == ["2:05", "1:01:40"]


def test_owner_email_omitted_when_empty():
    xml = build_feed("P", "http://x", "http://x/feed.xml", EPISODES,
                     owner_email="").decode()
    assert "<itunes:owner>" not in xml


def test_owner_email_present_when_set():
    xml = build_feed("P", "http://x", "http://x/feed.xml", EPISODES,
                     owner_email="me@example.com").decode()
    assert "me@example.com" in xml


def test_cover_image_included():
    xml = build_feed("P", "http://x", "http://x/feed.xml", EPISODES,
                     cover_url="http://x/cover.jpg").decode()
    assert "http://x/cover.jpg" in xml


def test_empty_feed_is_valid_xml():
    xml = build_feed("P", "http://x", "http://x/feed.xml", []).decode()
    assert "<rss" in xml and "</rss>" in xml


def test_hms_formatting():
    assert _hms(5) == "0:05"
    assert _hms(125) == "2:05"
    assert _hms(3700) == "1:01:40"
