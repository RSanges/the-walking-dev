"""Verify the published feed + latest episode are served correctly over HTTP.

Derives the base URL and the latest episode from config.yaml + the local state,
so it works for any deployment.
"""
import urllib.request

from walkingdev.config import Config
from walkingdev.hosting import make_hosting
from walkingdev.state import make_state

cfg = Config.load("config.yaml")
hosting = make_hosting(cfg)
feed = hosting.feed_url()
base = feed.rsplit("/", 1)[0]


def check(url, head=False):
    req = urllib.request.Request(url, method="HEAD" if head else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            ct = r.headers.get("Content-Type")
            cl = r.headers.get("Content-Length")
            body = b"" if head else r.read(120)
            print("OK  %s  [%s]  type=%s  len=%s" % (r.status, url, ct, cl))
            if body:
                print("    start:", body[:80])
    except Exception as e:  # noqa
        print("ERR", url, "->", repr(e))


check(feed)
episodes = make_state(cfg).list_episodes()
if episodes:
    check(base + "/episodes/" + episodes[0]["date"] + ".mp3", head=True)
else:
    print("(no episode in the local state yet)")
