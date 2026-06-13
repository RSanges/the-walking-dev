"""Diagnose RSS feeds + show what gather_news() would feed the model."""
import time

import feedparser

from walkingdev.config import Config
from walkingdev.news import format_for_prompt, gather_news

cfg = Config.load("config.yaml")
feeds = cfg.get("news", "feeds", default={})

print("=== Diagnostic par flux ===")
for theme, urls in feeds.items():
    print("\n#", theme)
    for url in urls:
        d = feedparser.parse(url)
        n = len(d.entries)
        latest = "?"
        for e in d.entries[:1]:
            st = e.get("published_parsed") or e.get("updated_parsed")
            if st:
                latest = time.strftime("%Y-%m-%d", st)
        status = "OK" if n and not d.bozo else ("VIDE/ERR" if not n else "bozo")
        print("  [%s] entries=%d latest=%s  %s" % (status, n, latest, url))

print("\n=== Apres filtre (recence 48h + exclusions) ===")
items = gather_news(cfg)
print("Total retenu:", len(items))
print(format_for_prompt(items))
