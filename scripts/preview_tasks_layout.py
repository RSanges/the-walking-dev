"""Send a checklist with the new layout (body text wraps, compact buttons)."""
import asyncio
from datetime import date

from walkingdev.channels import make_channel
from walkingdev.config import Config
from walkingdev.state import make_state

DAY = date.today().isoformat()
SAMPLE = [
    "Avancer la prochaine etape du projet principal",
    "Repondre aux deux mails importants en attente",
    "Preparer la reunion de demain matin",
    "Prendre une decision sur le point bloquant",
    "Caler une seance de sport, meme courte",
]

cfg = Config.load("config.yaml")
state = make_state(cfg)
tasks = state.get_tasks(DAY)
if not tasks:  # don't overwrite real tasks if a morning run already created them
    state.save_tasks(DAY, SAMPLE)
    tasks = state.get_tasks(DAY)
asyncio.run(make_channel(cfg).send_tasks(DAY, tasks))
print("apercu envoye pour", DAY, "-", len(tasks), "taches")
