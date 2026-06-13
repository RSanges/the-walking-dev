"""Extract the day's concrete, actionable tasks from the generated brief script.

The morning brief is audio; these tasks become a tappable Telegram checklist so
the user can mark progress, which then feeds the evening questions and the next
brief (follow-through loop).
"""
import logging

from . import llm

log = logging.getLogger(__name__)


def extract_tasks(config, script: str) -> list[str]:
    n = int(config.get("tasks", "count", default=5))
    prompt = (
        "Voici le SCRIPT d'un brief audio quotidien personnel. Extrais-en la liste\n"
        f"des taches CONCRETES et ACTIONNABLES de la journee (max {n}),\n"
        "formulees a l'imperatif, courtes (max ~10 mots chacune), priorisees, sans\n"
        "redondance. Pas de generalites. Reponds UNIQUEMENT par un tableau JSON de\n"
        "chaines, rien d'autre.\n\n=== SCRIPT ===\n" + (script or "")
    )
    try:
        arr = llm.parse_json_array(llm.run_cli(config, prompt, timeout=180))
        tasks = [str(x).strip() for x in arr if str(x).strip()]
        return tasks[:n]
    except Exception:
        log.warning("task extraction failed; no checklist this run", exc_info=True)
        return []
