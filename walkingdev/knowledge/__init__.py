from .base import Brief, KnowledgeProvider

__all__ = ["Brief", "KnowledgeProvider", "make_knowledge"]


def make_knowledge(config) -> KnowledgeProvider:
    backend = config.get("knowledge", "backend", default="local")
    if backend == "local":
        from .local import LocalKnowledge
        return LocalKnowledge(config)
    if backend == "obsidian":
        from .obsidian import ObsidianKnowledge
        return ObsidianKnowledge(config)
    raise NotImplementedError("knowledge backend not implemented: " + str(backend))
