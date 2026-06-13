"""Quick non-GPU smoke test: imports + (optional) knowledge + prompt build.

Uses config.yaml if present (so the knowledge section reflects your setup),
otherwise falls back to a minimal in-memory config. Skips the GPU TTS module.
"""
import importlib
import pkgutil
from pathlib import Path

import walkingdev

# 1) Import every submodule (catches syntax/import errors), skip GPU tts module.
bad = []
for m in pkgutil.walk_packages(walkingdev.__path__, "walkingdev."):
    if m.name.endswith("tts.omnivoice"):
        continue
    try:
        importlib.import_module(m.name)
    except Exception as e:  # noqa
        bad.append((m.name, repr(e)))
print("Modules imported OK" if not bad else "IMPORT FAILURES:")
for n, e in bad:
    print("  ", n, e)

# 2) Knowledge provider (Obsidian against your vault if configured, else local).
from walkingdev.config import Config
from walkingdev.knowledge import make_knowledge

try:
    cfg = Config.load("config.yaml")
except FileNotFoundError:
    cfg = Config({"knowledge": {"backend": "local"}, "state": {"backend": "sqlite",
                  "sqlite": {"path": "data/smoke.db"}}}, Path("."))
brief = make_knowledge(cfg).gather()
print("\nProjects read:", len(brief.projects))
for p in brief.projects[:5]:
    print("  -", p["name"], "| status:", p["status"], "| next:", (p["next"] or "")[:50])
print("Objectives read:", len(brief.objectives))

# 3) Prompt builder.
from walkingdev.writer.base import WriteInput
from walkingdev.writer.prompt import build_prompt

prompt = build_prompt(WriteInput(
    profile={"themes": "AI, web dev", "tone": "direct and frank", "name": "Alex"},
    evening={"tomorrow_priority": "Ship the next feature"},
    brief=brief, date="2026-06-13"))
print("\nPrompt built:", len(prompt), "chars (excerpt):")
print(prompt[:220])
