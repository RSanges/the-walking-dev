"""Publish the already-generated episodes to the configured hosting.

Uploads audio/<date>.mp3 + feed.xml, prints the public URLs. No Claude, no TTS.
Run after filling .env (e.g. FTP_USER / FTP_PASSWORD for the ftp backend).
"""
import os

from walkingdev.config import Config
from walkingdev.hosting import make_hosting
from walkingdev.pipeline.nightly import _publish_feed
from walkingdev.state import make_state

cfg = Config.load("config.yaml")
state = make_state(cfg)
hosting = make_hosting(cfg)
title = cfg.get("podcast", "title", default="The Walking Dev")

eps = state.list_episodes()
if not eps:
    raise SystemExit("No episode in the local state.")

for e in eps:
    mp3 = str(cfg.root / "audio" / (e["date"] + ".mp3"))
    if os.path.exists(mp3):
        print("Uploaded MP3 ->", hosting.publish(mp3, e["date"]))

_publish_feed(cfg, state, hosting, title)
print("RSS feed published ->", hosting.feed_url())
