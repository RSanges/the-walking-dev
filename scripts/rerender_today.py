"""Re-clean + re-synthesize + re-publish an episode (no Claude re-run).

Usage: python scripts/rerender_today.py [YYYY-MM-DD]   (default: today)
"""
import sqlite3
import sys
from datetime import date

from walkingdev.audio_encode import wav_to_mp3
from walkingdev.config import Config
from walkingdev.hosting import make_hosting
from walkingdev.pipeline.nightly import _publish_feed, _wav_seconds
from walkingdev.state import make_state
from walkingdev.tts import make_tts
from walkingdev.writer.prompt import clean_script

DAY = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
cfg = Config.load("config.yaml")
state = make_state(cfg)

row = sqlite3.connect(state.path).execute(
    "SELECT script FROM episodes WHERE date=?", (DAY,)).fetchone()
if not row:
    raise SystemExit(f"No stored episode for {DAY}.")
script = clean_script(row[0])
print("Cleaned script, start:", repr(script[:70]))

wav = str(cfg.root / "audio" / (DAY + ".wav"))
mp3 = str(cfg.root / "audio" / (DAY + ".mp3"))
make_tts(cfg).synthesize(script, wav)
wav_to_mp3(wav, mp3, bitrate=int(cfg.get("podcast", "mp3_bitrate", default=128)))

title = cfg.get("podcast", "title", default="The Walking Dev")
hosting = make_hosting(cfg)
url = hosting.publish(mp3, DAY)
state.record_episode(DAY, url, script, _wav_seconds(wav))
_publish_feed(cfg, state, hosting, title)
print("Republished ->", url)
