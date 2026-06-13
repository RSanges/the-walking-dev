"""ObsidianKnowledge: read a structured Obsidian vault.

Parses project notes' frontmatter (statut, next) and the objectives file, dumps
the ENTIRE vault (decisions, knowledge, people, companies, index, project
bodies, recent journal) as background context, and writes a dated journal entry.
Paths are configured in config.yaml.
"""
import logging
import re
from pathlib import Path

from .base import Brief, KnowledgeProvider

log = logging.getLogger(__name__)


class ObsidianKnowledge(KnowledgeProvider):
    def __init__(self, config):
        c = config.section("knowledge", "obsidian")
        self.vault = Path(c.get("vault_path", ""))
        if not self.vault.is_dir():
            log.warning("Obsidian vault_path %r is not a directory; the brief "
                        "will have no vault context", str(self.vault))
        self.projects_dir = self.vault / c.get("projects_dir", "01 - Projets")
        self.objectives_file = self.vault / c.get(
            "objectives_file", "02 - Objectifs/Objectifs.md")
        self.about_file = self.vault / c.get("about_file", "À propos de moi.md")
        self.journal_dir = self.vault / c.get("journal_dir", "05 - Journal")
        self.templates_dir = c.get("templates_dir", "99 - Templates")
        # Journal grows one entry per day (the bot writes to it) — bound it so
        # the dump can't balloon over time. Keep the most recent N entries.
        self.journal_recent = int(c.get("journal_recent", 14))
        # Hard ceiling on the whole dump, as a final guard against runaway size.
        self.max_chars = int(c.get("max_chars", 200000))

    def gather(self) -> Brief:
        projects = []
        if self.projects_dir.exists():
            for md in self.projects_dir.glob("*.md"):
                fm = _frontmatter(md.read_text(encoding="utf-8", errors="replace"))
                if fm.get("statut") in ("archive", "archivé"):
                    continue
                projects.append({
                    "name": md.stem,
                    "status": fm.get("statut", ""),
                    "next": fm.get("next", ""),
                })
        objectives = []
        if self.objectives_file.exists():
            text = self.objectives_file.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                m = re.match(r"\s*-\s+(.*)", line)
                if m:
                    objectives.append(re.sub(r"[*\[\]]", "", m.group(1)).strip())
        about = ""
        if self.about_file.exists():
            about = _strip_md(self.about_file.read_text(
                encoding="utf-8", errors="replace"))[:2500]
        return Brief(projects=projects, objectives=objectives, about=about,
                     vault=self._dump_vault())

    def _dump_vault(self) -> str:
        """Concatenate every note in the vault as one background-context blob.

        Includes all folders (decisions, knowledge, relations, companies, index,
        project bodies, root notes). Excludes hidden dirs (.obsidian, .trash) and
        the templates folder, plus the objectives/about files already surfaced
        in structured form. The journal is bounded to the most recent entries.
        """
        if not self.vault.exists():
            return ""
        already = {self.objectives_file.resolve(), self.about_file.resolve()}
        journal_dir = self.journal_dir.resolve()
        blocks, journals = [], []
        for md in sorted(self.vault.rglob("*.md")):
            rel = md.relative_to(self.vault)
            if any(p.startswith(".") for p in rel.parts):
                continue
            if rel.parts and rel.parts[0] == self.templates_dir:
                continue
            if md.resolve() in already:
                continue
            try:
                body = _strip_md(md.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if not body:
                continue
            block = "### " + rel.as_posix() + "\n" + body
            if journal_dir in md.resolve().parents:
                journals.append((md.name, block))  # name starts with the date
            else:
                blocks.append(block)
        journals.sort(reverse=True)               # most recent dates first
        blocks.extend(b for _, b in journals[: self.journal_recent])
        out = "\n\n".join(blocks)
        if self.max_chars and len(out) > self.max_chars:
            out = out[: self.max_chars] + "\n[...vault tronque (max_chars)...]"
        return out

    def write_journal(self, date: str, summary: str) -> None:
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        path = self.journal_dir / (date + " The Walking Dev.md")
        path.write_text(
            "---\ntags: [journal]\n---\n# " + date + " - Brief audio\n\n" + summary
            + "\n\n[[The Walking Dev]]\n",
            encoding="utf-8",
        )


def _strip_md(text: str) -> str:
    """Drop YAML frontmatter and collapse whitespace for a compact context blob."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    text = re.sub(r"[#>*`]", "", text)
    return re.sub(r"\n{2,}", "\n", text).strip()


def _frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out
