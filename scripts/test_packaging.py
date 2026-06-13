"""Test MP3 packaging + RSS feed on the already-generated episode (no Claude)."""
import os

from walkingdev.audio_encode import wav_to_mp3
from walkingdev.config import Config
from walkingdev.hosting import make_hosting
from walkingdev.pipeline.nightly import _publish_feed
from walkingdev.state import make_state

cfg = Config.load("config.yaml")
state = make_state(cfg)
hosting = make_hosting(cfg)
title = cfg.get("podcast", "title", default="The Walking Dev")

# Convert existing WAVs to MP3 so the feed has real sizes.
for e in state.list_episodes():
    wav = "audio/%s.wav" % e["date"]
    mp3 = "audio/%s.mp3" % e["date"]
    if os.path.exists(wav):
        wav_to_mp3(wav, mp3)
        print("MP3:", mp3, "%.2f Mo" % (os.path.getsize(mp3) / 1e6))

_publish_feed(cfg, state, hosting, title)
feed = "audio/feed.xml"
print("feed.xml ecrit:", os.path.exists(feed), "(%d octets)" % os.path.getsize(feed))
print("\n--- debut feed.xml ---")
print(open(feed, encoding="utf-8").read()[:900])
