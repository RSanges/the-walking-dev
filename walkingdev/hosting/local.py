"""LocalHosting: copy the MP3 into a public folder, regenerate feed.xml there.

Default backend; pair with a tunnel (e.g. cloudflared) to expose it on the go.
Files are laid out exactly like the remote backends (``episodes/<date>.mp3`` +
``feed.xml`` + ``cover.jpg`` under the output dir) so the feed URLs always match.
"""
import shutil
from pathlib import Path

from .base import AudioHosting


class LocalHosting(AudioHosting):
    def __init__(self, config):
        c = config.section("hosting", "local")
        self.out = config.resolve(c.get("output_dir", "public"))
        self.base = c.get("public_base_url", "http://localhost:8000").rstrip("/")
        self.out.mkdir(parents=True, exist_ok=True)

    def publish(self, mp3_path: str, date: str) -> str:
        dest = self.out / "episodes" / (date + ".mp3")
        dest.parent.mkdir(parents=True, exist_ok=True)
        src = Path(mp3_path).resolve()
        if src != dest.resolve():     # the nightly may already write here
            shutil.copy(src, dest)
        return self.base + "/episodes/" + dest.name

    def feed_url(self) -> str:
        return self.base + "/feed.xml"

    def put_feed(self, xml: bytes) -> None:
        (self.out / "feed.xml").write_bytes(xml)

    def put_asset(self, name: str, data: bytes, content_type: str) -> str:
        (self.out / name).write_bytes(data)
        return self.base + "/" + name
