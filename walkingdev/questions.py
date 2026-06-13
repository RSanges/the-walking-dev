"""Question sets used by the messaging bot.

ONBOARDING runs once on first /start to calibrate everything.
EVENING runs each night to feed the next morning's episode.
Channel-agnostic so any MessagingChannel can render them.
"""
from dataclasses import dataclass, field
from typing import Literal

Kind = Literal["text", "voice", "scale", "list", "choice", "bool"]


@dataclass
class Question:
    key: str
    text: str
    kind: Kind = "text"
    choices: list[str] = field(default_factory=list)
    optional: bool = False
    hint: str = ""


# Asked ONCE on first run to build the user profile.
ONBOARDING: list[Question] = [
    Question("themes", "Quels themes veux-tu suivre en veille ? (ex. IA, dev web, "
             "impression 3D, finance) Separe par des virgules.", kind="list"),
    Question("news_depth", "Combien de sujets d'actu par jour, et plutot 1 phrase "
             "ou 1 paragraphe par sujet ?"),
    Question("sources_pref", "Des sources a privilegier ou a bannir ?", optional=True),
    Question("mail_priority", "Des expediteurs ou labels toujours prioritaires "
             "dans le resume mail ?", optional=True),
    Question("mail_ignore", "Des expediteurs a ignorer meme non lus ?", optional=True),
    Question("projects_focus", "Tous tes projets dans le brief, ou un focus ?"),
    Question("recurring_reminders", "Des rappels recurrents chaque jour ? "
             "(deadlines, habitudes, seance du jour...)", optional=True),
    # Note: the narrator VOICE is not asked here. It is configured in config.yaml
    # (tts: design by tags, or cloning of a sample), since a free-text answer
    # cannot drive the TTS engine.
    Question("address", "Je te tutoie ? Un surnom ou une formule d'ouverture ?",
             optional=True),
    Question("hard_limit", "Une longueur maximale stricte ? (ex. couper a 18 min)"),
    Question("off_days", "Des jours sans podcast ? (ex. dimanche)", kind="list",
             optional=True),
]

# Asked EVERY EVENING (~21:30). Short, low-friction, text or voice.
EVENING: list[Question] = [
    Question("day_recap", "Comment s'est passee ta journee ?", kind="voice"),
    Question("done_today", "Qu'as-tu avance ou termine aujourd'hui ?", kind="voice"),
    Question("tomorrow_priority", "LA priorite de demain ?"),
    Question("blocker", "Un blocage ou une decision en attente ?", optional=True),
    Question("energy", "Energie / forme ce soir, de 1 a 5 ?", kind="scale"),
    Question("workout", "Seance de sport faite aujourd'hui ?", kind="bool"),
]
