"""Generate adaptive evening questions from the user's current context.

Each evening, instead of a fixed list, the model proposes a few short questions
tailored to active projects, objectives, the user profile and recent answers, so
the check-in stays relevant and feeds a better next-morning brief. Two fixed
anchors (energy, workout) are always kept for trend tracking. Falls back to the
static EVENING list if generation fails (robust by design), and logs why.
"""
import json
import logging

from . import llm
from .questions import EVENING, Question

log = logging.getLogger(__name__)

ANCHORS = [
    Question("energy", "Energie / forme ce soir, de 1 a 5 ?", kind="scale"),
    Question("workout", "Seance de sport faite aujourd'hui ?", kind="bool"),
]


def generate(config, day: str) -> list[Question]:
    count = int(config.get("evening", "dynamic_count", default=8))
    try:
        from .knowledge import make_knowledge
        from .state import make_state
        brief = make_knowledge(config).gather()
        state = make_state(config)
        recent = _recent_evenings(state)
        tasks = state.get_tasks(day)
        prompt = _prompt(brief, recent, day, count, tasks)
        texts = llm.parse_json_array(llm.run_cli(config, prompt))
        dynamic = [Question(f"q{i}", str(t), kind="text")
                   for i, t in enumerate(texts[:count]) if str(t).strip()]
        if dynamic:
            return dynamic + ANCHORS
        log.warning("evening question generation returned nothing; using static list")
    except Exception:
        log.warning("evening question generation failed; using static list", exc_info=True)
    return list(EVENING)


def _recent_evenings(state, n: int = 2) -> list[dict]:
    out = []
    try:
        for ep in state.list_episodes():  # newest first; reuse dates
            ev = state.get_evening(ep["date"])
            if ev:
                out.append({"date": ep["date"], "answers": ev})
            if len(out) >= n:
                break
    except Exception:
        log.warning("could not read recent evening answers", exc_info=True)
    return out


def _prompt(brief, recent, day: str, count: int = 8, tasks=None) -> str:
    tasks_txt = "\n".join(
        ("- [x] " if t.get("done") else "- [ ] ") + t.get("text", "")
        for t in (tasks or [])) or "(aucune)"
    projects = "\n".join(
        f"- {p.get('name', '')} [{p.get('status', '')}] {p.get('next', '') or ''}"
        for p in getattr(brief, "projects", []) if p.get("status") == "actif")
    objectives = "\n".join(f"- {o}" for o in getattr(brief, "objectives", [])[:8])
    about = (getattr(brief, "about", "") or "")[:1500]
    rec = json.dumps(recent, ensure_ascii=False)[:800]
    return (
        f"Tu prepares le point du soir d'un assistant personnel pour {day}.\n"
        f"Genere EXACTEMENT {count} QUESTIONS courtes, concretes, a faible\n"
        "friction, en francais, qui aideront a rediger le brief de demain\n"
        "matin. Couvre un eventail: avancement du jour, projets actifs et leurs\n"
        "prochaines etapes, revenus/finances, blocages, priorite de demain, corps,\n"
        "et une question de recul/reflexion. Elles doivent etre ADAPTEES au contexte\n"
        "ci-dessous. Reference des elements concrets (noms de projets, echeances,\n"
        "rendez-vous) quand c'est pertinent. Varie, ne sois pas redondant.\n"
        "Si des taches du jour ci-dessous ne sont PAS cochees, inclus une question\n"
        "sur leur suivi.\n"
        "N'inclus PAS de question sur l'energie ni le sport (gerees a part).\n"
        "Reponds UNIQUEMENT par un tableau JSON de chaines, rien d'autre.\n\n"
        "PROJETS ACTIFS:\n" + (projects or "(aucun)") + "\n\n"
        "OBJECTIFS:\n" + (objectives or "(aucun)") + "\n\n"
        "PROFIL:\n" + about + "\n\n"
        "TACHES DU JOUR (coche = fait):\n" + tasks_txt + "\n\n"
        "REPONSES RECENTES DU SOIR:\n" + rec + "\n"
    )
