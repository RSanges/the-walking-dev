"""Send a throwaway clickable task checklist to verify the Telegram buttons."""
import asyncio

from walkingdev.channels import make_channel
from walkingdev.config import Config
from walkingdev.state import make_state

DAY = "2026-06-04"
PREVIEW = [
    "[Test] Tape-moi pour me cocher",
    "[Test] Et decoche-moi ensuite",
    "[Test] Verifie que le check tient",
]

cfg = Config.load("config.yaml")
state = make_state(cfg)
state.save_tasks(DAY, PREVIEW)
asyncio.run(make_channel(cfg).send_tasks(DAY, state.get_tasks(DAY)))
print("Apercu envoye:", len(PREVIEW), "taches")
