"""Run only the ScriptWriter (no TTS/publish) to inspect the news freshness."""
import sys

from walkingdev.config import Config
from walkingdev.knowledge import make_knowledge
from walkingdev.news import gather_news
from walkingdev.state import make_state
from walkingdev.writer import make_writer
from walkingdev.writer.base import WriteInput

day = sys.argv[1] if len(sys.argv) > 1 else "2026-06-04"
cfg = Config.load("config.yaml")
state = make_state(cfg)
knowledge = make_knowledge(cfg)

profile = state.get_onboarding()
profile.setdefault("themes", "IA, dev web, impression 3D, finance, actu generale")
profile.setdefault("mail_account", cfg.get("mail", "account"))
profile.setdefault("tone", cfg.get("podcast", "tone", default="direct et cash"))
evening = state.get_evening(day) or state.get_evening("2026-06-03")
brief = knowledge.gather()
news = gather_news(cfg)
print("Actus RSS:", len(news))

script = make_writer(cfg).write_script(WriteInput(profile, evening, brief, day, news))
print("=== SCRIPT (", len(script), "car.) ===")
print(script)
