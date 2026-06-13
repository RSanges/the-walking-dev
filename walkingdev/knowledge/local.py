"""LocalKnowledge: projects/objectives live in the StateStore, fed by onboarding
and the evening follow-up. Default provider, works without any external tool.
"""
from .base import Brief, KnowledgeProvider


class LocalKnowledge(KnowledgeProvider):
    def __init__(self, config):
        from ..state import make_state
        self.state = make_state(config)

    def gather(self) -> Brief:
        ob = self.state.get_onboarding()
        return Brief(
            projects=ob.get("projects", []),
            objectives=[o for o in (ob.get("objectives") or [])],
            notes=ob.get("projects_focus", ""),
        )

    def write_journal(self, date: str, summary: str) -> None:
        # Local provider keeps the trace inside the episode record (no files).
        return None
