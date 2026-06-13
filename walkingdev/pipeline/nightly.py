"""Nightly pipeline: gather -> write script -> synthesize -> publish -> trace.

Invoked by a scheduler (e.g. Windows Task Scheduler) so the episode is ready by
the configured time. Generates even if the evening answers are missing (robust
by design).
"""
import logging
from datetime import date as _date
from datetime import timedelta as _timedelta

from ..audio_encode import wav_to_mp3
from ..config import Config
from ..hosting import make_hosting
from ..hosting.feed import build_feed
from ..knowledge import make_knowledge
from ..news import gather_news
from ..state import make_state
from ..tts import make_tts
from ..writer import make_writer
from ..writer.base import WriteInput

log = logging.getLogger(__name__)

_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday",
             "saturday", "sunday"]


def run(config_path: str = "config.yaml", day: str | None = None,
        force: bool = False) -> str:
    cfg = Config.load(config_path)
    day = day or _date.today().isoformat()
    yesterday = (_date.fromisoformat(day) - _timedelta(days=1)).isoformat()

    off_days = {str(d).lower() for d in (cfg.get("podcast", "off_days") or [])}
    if not force and _WEEKDAYS[_date.fromisoformat(day).weekday()] in off_days:
        log.info("%s is an off day (podcast.off_days) - skipping", day)
        return ""

    state = make_state(cfg)

    # Idempotent: don't regenerate if today's episode already exists (e.g. a
    # manual run earlier the same day). Use force=True to override.
    if not force and any(e["date"] == day for e in state.list_episodes()):
        log.info("episode already generated for %s - skip (use --force)", day)
        return ""

    knowledge = make_knowledge(cfg)
    writer = make_writer(cfg)
    tts = make_tts(cfg)
    hosting = make_hosting(cfg)

    profile = state.get_onboarding()
    profile.setdefault("mail_account", cfg.get("mail", "account"))
    profile.setdefault("tone", cfg.get("podcast", "tone", default="direct et cash"))
    profile.setdefault("name", cfg.get("podcast", "user_name", default=""))
    profile.setdefault("challenge_domains", cfg.get("podcast", "challenge", "domains"))
    profile.setdefault("challenge_context",
                       cfg.get("podcast", "challenge", "context", default=""))
    # Evening answers belong to last night: read the day's, else the night before.
    evening = state.get_evening(day) or state.get_evening(yesterday)
    brief = knowledge.gather()
    news = gather_news(cfg)
    log.info("RSS items gathered: %d", len(news))
    prev_tasks = state.get_tasks(yesterday)

    script = writer.write_script(
        WriteInput(profile, evening, brief, day, news, prev_tasks))
    if len(script.strip()) < 200:
        raise RuntimeError(
            "writer returned an empty/too-short script (%d chars); aborting "
            "before synthesis." % len(script.strip()))

    # Synthesize WAV, then package to MP3 for the podcast feed.
    wav_path = str(cfg.root / "audio" / (day + ".wav"))
    tts.synthesize(script, wav_path)
    mp3_path = str(cfg.root / "audio" / (day + ".mp3"))
    wav_to_mp3(wav_path, mp3_path,
               bitrate=int(cfg.get("podcast", "mp3_bitrate", default=128)))
    duration = _wav_seconds(wav_path)

    podcast_title = cfg.get("podcast", "title", default="The Walking Dev")
    url = hosting.publish(mp3_path, day)
    state.record_episode(day, url, script, duration)

    _publish_cover(cfg, hosting)
    _publish_feed(cfg, state, hosting, podcast_title)
    _publish_tasks(cfg, state, day, script)
    knowledge.write_journal(day, _trace(script, url))
    log.info("episode published: %s", url)
    log.info("RSS feed: %s", hosting.feed_url())
    return url


def _publish_cover(cfg, hosting) -> None:
    """Upload the configured cover image next to the feed, if set."""
    cover = cfg.get("podcast", "cover")
    if not cover:
        return
    path = cfg.resolve(cover)
    if not path.exists():
        log.warning("podcast.cover %s not found; skipping cover upload", path)
        return
    try:
        hosting.put_asset("cover.jpg", path.read_bytes(), "image/jpeg")
    except Exception:
        log.warning("cover upload failed", exc_info=True)


def _publish_tasks(cfg, state, day, script):
    """Extract the day's tasks, store them, and push a tappable checklist."""
    import asyncio

    from ..channels import make_channel
    from ..tasks import extract_tasks
    try:
        tasks = extract_tasks(cfg, script)
        if not tasks:
            return
        state.save_tasks(day, tasks)
        channel = make_channel(cfg)
        asyncio.run(channel.send_tasks(day, state.get_tasks(day)))
        log.info("daily tasks published: %d", len(tasks))
    except Exception:
        log.warning("tasks not published", exc_info=True)


def _publish_feed(cfg, state, hosting, podcast_title):
    """Rebuild the RSS feed from all episodes and publish it.

    Episode URLs are derived from the CURRENT hosting base (not the value stored
    at generation time), so switching hosting backends keeps the feed coherent.
    """
    base = hosting.feed_url().rsplit("/", 1)[0]
    pod = cfg.section("podcast")
    items = []
    for e in state.list_episodes():
        mp3 = cfg.root / "audio" / (e["date"] + ".mp3")
        items.append({
            "url": base + "/episodes/" + e["date"] + ".mp3",
            "title": podcast_title + " - " + e["date"],
            "date": e["date"],
            "length": mp3.stat().st_size if mp3.exists() else 0,
            "duration": e.get("duration"),
        })
    cover = base + "/cover.jpg" if pod.get("cover") else None
    xml = build_feed(
        podcast_title, base, hosting.feed_url(), items, cover_url=cover,
        author=pod.get("author", podcast_title),
        owner_email=pod.get("owner_email", ""),
        category=pod.get("category", "Technology"),
        language=pod.get("language", "fr"),
        description=pod.get("description"),
        tz_name=pod.get("timezone", "Europe/Paris"))
    hosting.put_feed(xml)


def _wav_seconds(wav_path: str) -> float | None:
    try:
        import soundfile as sf
        info = sf.info(wav_path)
        return info.frames / float(info.samplerate)
    except Exception:
        return None


def _trace(script: str, url: str) -> str:
    head = script.strip().split("\n", 1)[0][:300]
    return "Brief genere et publie: " + url + "\n\nDebut du script:\n" + head


if __name__ == "__main__":
    run()
