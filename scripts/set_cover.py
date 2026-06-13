"""Prepare the podcast cover, upload it, and republish the feed with it.

Usage: python scripts/set_cover.py [SOURCE_IMAGE]
Default source: podcast.cover from config.yaml, else pictures/cover-source.png.
"""
import sys

from PIL import Image

from walkingdev.config import Config
from walkingdev.hosting import make_hosting
from walkingdev.pipeline.nightly import _publish_feed
from walkingdev.state import make_state

cfg = Config.load("config.yaml")
src = (sys.argv[1] if len(sys.argv) > 1
       else cfg.get("podcast", "cover") or "pictures/cover-source.png")

# 1) Apple-compliant cover: square, 1400-3000px, RGB JPEG.
im = Image.open(src).convert("RGB").resize((1500, 1500), Image.LANCZOS)
out = cfg.resolve("cover.jpg")
im.save(out, "JPEG", quality=90)
print("cover.jpg created (1500x1500 RGB)")

# 2) Upload next to the feed via the public hosting API.
hosting = make_hosting(cfg)
hosting.put_asset("cover.jpg", out.read_bytes(), "image/jpeg")
print("cover uploaded")

# 3) Republish the feed (now references the cover).
title = cfg.get("podcast", "title", default="The Walking Dev")
_publish_feed(cfg, make_state(cfg), hosting, title)
print("feed republished with cover ->", hosting.feed_url())
