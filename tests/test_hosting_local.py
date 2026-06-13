from walkingdev.config import Config
from walkingdev.hosting.local import LocalHosting


def _cfg(tmp_path):
    return Config({"hosting": {"local": {
        "output_dir": str(tmp_path / "public"),
        "public_base_url": "http://localhost:8000",
    }}}, tmp_path)


def test_publish_layout_matches_feed_urls(tmp_path):
    h = LocalHosting(_cfg(tmp_path))
    mp3 = tmp_path / "audio" / "2026-06-13.mp3"
    mp3.parent.mkdir(parents=True)
    mp3.write_bytes(b"ID3data")
    url = h.publish(str(mp3), "2026-06-13")
    assert url == "http://localhost:8000/episodes/2026-06-13.mp3"
    assert (tmp_path / "public" / "episodes" / "2026-06-13.mp3").read_bytes() == b"ID3data"


def test_publish_same_source_is_idempotent(tmp_path):
    """Publishing a file that already lives at the destination must not raise
    SameFileError (the regression that crashed the default nightly)."""
    h = LocalHosting(_cfg(tmp_path))
    dest = tmp_path / "public" / "episodes" / "2026-06-13.mp3"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"data")
    url = h.publish(str(dest), "2026-06-13")
    assert url.endswith("/episodes/2026-06-13.mp3")


def test_put_feed_and_asset(tmp_path):
    h = LocalHosting(_cfg(tmp_path))
    h.put_feed(b"<rss/>")
    assert (tmp_path / "public" / "feed.xml").read_bytes() == b"<rss/>"
    url = h.put_asset("cover.jpg", b"img", "image/jpeg")
    assert url == "http://localhost:8000/cover.jpg"
    assert (tmp_path / "public" / "cover.jpg").read_bytes() == b"img"
    assert h.feed_url() == "http://localhost:8000/feed.xml"
