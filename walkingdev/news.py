"""RSS news gathering: fetch recent, substantive items from curated feeds.

Instead of asking the model to "search the web" (which mixes in stale,
training-data events), the pipeline pulls dated items from reliable RSS feeds,
filters by recency, drops low-value noise (faits divers, people, futilites), and
hands the model a fresh, dated list to summarize. This guarantees freshness and
keeps the editorial line: only news that helps understand and move forward.
"""
import calendar
import html
import logging
import re
import time
import urllib.request

log = logging.getLogger(__name__)

DEFAULT_EXCLUDE = [
    "people", "celebrite", "célébrité", "star", "stars", "tele-realite",
    "télé-réalité", "faits divers", "fait divers", "insolite", "horoscope",
    "buzz", "scandale people",
]

_FETCH_TIMEOUT = 15  # seconds per feed; a hung feed must not stall the nightly


def gather_news(config) -> list[dict]:
    n = config.section("news")
    if n.get("enabled") is False:
        return []  # privacy: no outbound RSS fetch (fully-local profile)
    feeds = n.get("feeds", {}) or {}
    window = int(n.get("window_hours", 48))
    per_feed = int(n.get("max_items_per_feed", 4))
    per_theme = int(n.get("max_per_theme", 3))
    total = int(n.get("max_total", 16))
    timeout = int(n.get("fetch_timeout", _FETCH_TIMEOUT))
    exclude = [w.lower() for w in (n.get("exclude_keywords") or DEFAULT_EXCLUDE)]
    cutoff = time.time() - window * 3600

    items: list[dict] = []
    for theme, urls in feeds.items():
        for url in (urls or []):
            d = _parse_feed(url, timeout)
            if d is None:
                continue
            source = (d.feed.get("title") if getattr(d, "feed", None) else "") or url
            kept = 0
            for e in d.entries:
                ts = _entry_ts(e)
                if ts is None or ts < cutoff:
                    continue  # undated or too old -> drop (freshness first)
                title = (e.get("title") or "").strip()
                summary = _clean(e.get("summary") or e.get("description") or "")
                blob = (title + " " + summary + " " + _cats(e)).lower()
                if any(w in blob for w in exclude):
                    continue
                items.append({
                    "theme": theme,
                    "source": source,
                    "title": title,
                    "summary": summary[:300],
                    "published": _iso(ts),
                    "ts": ts,
                    "link": e.get("link", ""),
                })
                kept += 1
                if kept >= per_feed:
                    break
    # Dedup the same story cross-posted across themes (keep first occurrence,
    # i.e. the earlier theme in config order).
    seen, deduped = set(), []
    for it in items:
        k = it["link"] or (it["title"].lower())
        if k in seen:
            continue
        seen.add(k)
        deduped.append(it)
    items = deduped

    # Balance per theme so no theme (e.g. AI) gets crowded out by another's
    # fresher-but-weaker items, then apply a global safety cap.
    by_theme: dict[str, list[dict]] = {}
    for it in items:
        by_theme.setdefault(it["theme"], []).append(it)
    selected: list[dict] = []
    for its in by_theme.values():
        its.sort(key=lambda x: x["ts"], reverse=True)
        selected.extend(its[:per_theme])
    selected.sort(key=lambda x: x["ts"], reverse=True)
    return selected[:total]


def _parse_feed(url: str, timeout: int):
    """Fetch a feed with a hard timeout, then parse the bytes. feedparser.parse
    on a URL uses urllib with no timeout, so we fetch ourselves first."""
    import feedparser
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "the-walking-dev/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except Exception as e:  # network error, timeout, bad status
        log.warning("feed fetch failed: %s (%s)", url, e)
        return None
    d = feedparser.parse(raw)
    if getattr(d, "bozo", 0) and not d.entries:
        log.warning("feed unparseable: %s (%r)", url, getattr(d, "bozo_exception", None))
        return None
    return d


def format_for_prompt(items: list[dict]) -> str:
    if not items:
        return "(aucune actu RSS recente recuperee)"
    by_theme: dict[str, list[dict]] = {}
    for it in items:
        by_theme.setdefault(it["theme"], []).append(it)
    out = []
    for theme, its in by_theme.items():
        out.append("# " + theme)
        for it in its:
            out.append("- [%s | %s] %s" % (it["published"][:10], it["source"], it["title"]))
            if it["summary"]:
                out.append("  " + it["summary"])
    return "\n".join(out)


def _entry_ts(e):
    for key in ("published_parsed", "updated_parsed"):
        st = e.get(key)
        if st:
            try:
                return calendar.timegm(st)  # struct_time is UTC
            except Exception:
                pass
    return None


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _cats(e) -> str:
    tags = e.get("tags") or []
    return " ".join(t.get("term", "") for t in tags if isinstance(t, dict))
