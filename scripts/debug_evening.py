"""Debug: show Claude's raw output + parse result for evening questions."""
from walkingdev import evening_questions as eq
from walkingdev.config import Config
from walkingdev.knowledge import make_knowledge
from walkingdev.state import make_state

cfg = Config.load("config.yaml")
brief = make_knowledge(cfg).gather()
recent = eq._recent_evenings(make_state(cfg))
prompt = eq._prompt(brief, recent, "2026-06-04")
print("PROMPT len:", len(prompt))
try:
    raw = eq._ask_claude_json(cfg, prompt)
    print("RAW len:", len(raw))
    print("----- RAW START -----")
    print(raw[:2000])
    print("----- RAW END -----")
    print("PARSED:", eq._parse(raw))
except Exception as e:  # noqa
    print("EXCEPTION:", repr(e))
