"""Reset for a clean first run: clear state, local audio, and the published feed.

Keeps the SQLite schema (so a running bot keeps working) but empties the tables,
removes local audio, and publishes an empty feed. For the ftp backend it also
deletes the remote episodes; for other backends the remote cleanup is skipped.
"""
import glob
import os
import sqlite3

from walkingdev.config import Config
from walkingdev.hosting import make_hosting
from walkingdev.hosting.feed import build_feed
from walkingdev.state import make_state

cfg = Config.load("config.yaml")

# 1) Clear DB tables (keep schema)
dbp = str(make_state(cfg).path)
if os.path.exists(dbp):
    c = sqlite3.connect(dbp)
    for t in ("kv", "evening", "episodes", "tasks"):
        try:
            c.execute("DELETE FROM " + t)
        except sqlite3.OperationalError:
            pass
    c.commit()
    c.close()
    print("DB cleared:", dbp)

# 2) Remove local audio
for pat in ("audio/*.wav", "audio/*.mp3", "audio/feed.xml"):
    for f in glob.glob(str(cfg.root / pat)):
        os.remove(f)
        print("removed", f)

# 3) Clean remote episodes (ftp backend only)
if cfg.get("hosting", "backend") in ("ftp", "sftp", "ftps"):
    import paramiko
    ftp = cfg.section("hosting", "ftp")
    host = ftp.get("host") or Config.env("FTP_HOST")
    port = int(ftp.get("port") or 22)
    remote_dir = (ftp.get("remote_dir") or "www/podcast").strip("/")
    try:
        t = paramiko.Transport((host, port))
        t.connect(username=Config.env("FTP_USER"), password=Config.env("FTP_PASSWORD"))
        sftp = paramiko.SFTPClient.from_transport(t)
        epdir = remote_dir + "/episodes"
        try:
            for name in sftp.listdir(epdir):
                sftp.remove(epdir + "/" + name)
                print("remote removed", epdir + "/" + name)
        except OSError:
            pass
        sftp.close()
        t.close()
    except Exception as e:  # noqa
        print("SFTP cleanup skipped:", repr(e))

# 4) Publish an empty feed
hosting = make_hosting(cfg)
title = cfg.get("podcast", "title", default="The Walking Dev")
base = hosting.feed_url().rsplit("/", 1)[0]
hosting.put_feed(build_feed(title, base, hosting.feed_url(), []))
print("Empty feed published ->", hosting.feed_url())
print("RESET done. Send /start in Telegram for a clean onboarding.")
