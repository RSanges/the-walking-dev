"""Shared prompt builder so both writer backends produce the same brief.

Anything personal (the challenge focus areas, extra grounding context) comes from
config via the profile dict, with neutral defaults, so the source stays generic
and each user shapes the brief from their own ``config.yaml``.
"""

from ..news import format_for_prompt

# Neutral rotating focus areas for the daily "challenge" segment (one per day).
# Override with podcast.challenge.domains in config.yaml.
DEFAULT_DOMAINS = [
    "work, projects and momentum",
    "discipline, body and health (sport, routines, sleep)",
    "money and finances",
    "relationships (close ones, partners, network, clients)",
    "life direction, meaning and long-term vision",
    "mindset and relationship to work (focus, habits, fears)",
]


def build_prompt(data) -> str:
    p = data.profile or {}
    tone = p.get("tone", "direct et cash")   # narration style, from podcast.tone
    themes = p.get("themes", "")
    depth = p.get("news_depth", "3 a 5 sujets, un court paragraphe chacun")
    today = str(getattr(data, "date", "") or "")
    name = (p.get("name") or "").strip()
    domains = p.get("challenge_domains") or DEFAULT_DOMAINS
    context = (p.get("challenge_context") or "").strip()
    domain = _domain_of_day(today, domains)
    news_block = format_for_prompt(getattr(data, "news", None) or [])
    parts = [
        "Tu rediges le SCRIPT PARLE d'un podcast quotidien personnel en francais,",
        "pour etre lu par une synthese vocale. Pas de markdown, pas de titres,",
        "uniquement le texte a dire. Ton: " + str(tone) + ".",
        "Duree cible 10 a 20 minutes. Tutoiement.",
        ("Tu t'adresses directement a " + name + ", par son prenom. N'invente"
         " jamais un autre nom.") if name else "Tu t'adresses directement a l'auditeur.",
        "DATE DU JOUR: " + today + " (format AAAA-MM-JJ). C'est aujourd'hui.",
        "",
        "Ordre des segments OBLIGATOIRE: intro courte, veille d'actualites,",
        "avancement projets/objectifs, DEFI DU JOUR (reflexion), resume des mails",
        "utiles, agenda du jour, puis une cloture qui met en mouvement.",
        "",
        "=== VEILLE D'ACTUALITES ===",
        "THEMES: " + str(themes),
        "Profondeur souhaitee: " + str(depth) + ".",
        "Voici les ACTUS RECENTES recuperees via flux RSS (datees, dernieres 48h).",
        "Base ta veille UNIQUEMENT sur ces items:",
        "",
        news_block,
        "",
        "REGLES DE LA VEILLE:",
        "- Traite SEULEMENT des sujets de cette liste. N'ajoute aucune actu de ta",
        "  memoire, n'invente rien, ne cite pas d'evenement ancien.",
        "- LIGNE EDITORIALE STRICTE: uniquement ce qui aide a avancer, comprendre,",
        "  reflechir. ECARTE faits divers, people/celebrites, sport, futilites, sauf",
        "  affaire vraiment majeure. Si un item releve de ca, ignore-le simplement.",
        "- Choisis les plus pertinents, regroupe par theme, et explique pourquoi ca",
        "  compte. Tu peux approfondir un item via recherche web, mais ne sors pas",
        "  de cette liste de sujets.",
        "- Rattache a la situation de l'auditeur (projets, objectifs) quand c'est",
        "  pertinent, sans plaquer artificiellement.",
        "",
        "=== MAILS ET AGENDA (tu as des connecteurs Gmail et Google Agenda) ===",
        "- Tu DOIS appeler l'outil Gmail pour chercher les mails non lus des 24h du",
        "  compte " + str(_mail(data)) + " (hors promotions et newsletters) AVANT",
        "  d'ecrire le segment mails. Resume les utiles; s'il n'y en a pas, dis-le.",
        "- Tu DOIS appeler l'outil Google Agenda pour lister les evenements",
        "  d'aujourd'hui (" + today + ") AVANT d'ecrire le segment agenda.",
        "- N'affirme jamais 'pas de donnees' ou 'rien recu' sans avoir reellement",
        "  appele l'outil correspondant. N'invente aucun mail ni evenement.",
        "",
        "=== PROJETS ET OBJECTIFS (source vault/local) ===",
        "Incite a l'action UNIQUEMENT pour les projets en statut 'actif'. Tout",
        "autre statut (production, termine, gele, en pause, planifie, archive,",
        "demo, support) = PAS d'action: ne dis pas de deployer/finir/relancer.",
        "Mentionne ces projets-la seulement si c'est reellement pertinent (ex.",
        "incident, suivi leger). Le champ 'prochaine etape' peut etre perime: s'il",
        "contredit le statut, fie-toi au statut.",
        _brief(data.brief),
        "",
        "PROFIL DE " + (name or "L'AUDITEUR").upper() + " (contexte pour",
        "personnaliser, ne pas lire tel quel a voix haute):",
        _about(data.brief),
        "",
        "=== DEFI DU JOUR (juste apres les projets/objectifs) ===",
        "Domaine a explorer aujourd'hui (rotation quotidienne): " + domain + ".",
        "Construis un court segment qui le challenge VRAIMENT:",
        "- D'ABORD une provocation cash et personnelle: pointe une contradiction",
        "  ou un angle mort REEL de sa situation (tire de ses projets, objectifs,",
        "  profil, reponses du soir). Zero generalite de coaching.",
        "- PUIS une question ouverte et puissante a ruminer pendant sa marche.",
        "- Ancre tout dans SA realite concrete (ses projets, objectifs, contraintes",
        "  et la situation du moment).",
        (("- Contexte personnel a exploiter pour viser juste: " + context)
         if context else ""),
        "- 4 a 6 phrases. Ca doit percuter, pas tartiner.",
        "",
        "REPONSES DU SOIR (a integrer dans projets/objectifs et le ton):",
        _kv(data.evening),
        "",
        "SUIVI DES TACHES D'HIER (coche = fait) :",
        _prev_tasks(getattr(data, "prev_tasks", None)),
        "Mentionne brievement ce suivi: felicite pour ce qui est fait, rappelle",
        "sans culpabiliser ce qui reste, propose de le reprendre si pertinent.",
        "",
        "=== TON CERVEAU COMPLET (toutes tes notes) ===",
        "Ci-dessous l'integralite de tes notes: corps des fiches projets,",
        "decisions, connaissances, relations, societes, index et journal recent.",
        "C'est ta matiere de fond pour TOUS les segments. Sers-t'en pour ancrer",
        "la veille, le suivi des projets et surtout le defi du jour dans ta vraie",
        "situation (qui sont tes associes/clients, quelles decisions tu as prises,",
        "tes societes, ce que tu as note recemment). Relie les sujets entre eux.",
        "Ne recite pas ces notes telles quelles: pioche ce qui est pertinent.",
        _vault(data.brief),
        "",
        "Ecris maintenant le script complet, pret a etre vocalise.",
    ]
    return "\n".join(part for part in parts if part != "")


def clean_script(text: str) -> str:
    """Strip wrappers a model may add around the spoken text: a leading meta
    sentence ('Voici le script...'), markdown horizontal rules, and code fences.
    Only the first couple of lines are considered for meta-stripping so a real
    opening line is never silently dropped.
    """
    import re
    out = (text or "").strip()
    lines = out.splitlines()
    fences = ("---", "***", "```", "~~~")
    # A model sometimes prefixes a meta line (even after calling tools), e.g.
    # "J'ai interroge Gmail (...). Voici le script pret a vocaliser." Drop at most
    # the first two leading empty/fence/meta lines before the real spoken text.
    meta = re.compile(
        r"(voici le script|here'?s the script|pr[eê]t[ae]? [àa] (vocalis|lire)|"
        r"script (pret|pr[eê]t) a (vocalis|etre))",
        re.I)
    for _ in range(2):
        if lines and (not lines[0].strip() or lines[0].strip() in fences
                      or meta.search(lines[0])):
            lines.pop(0)
        else:
            break
    # Remove horizontal-rule and fence lines anywhere.
    lines = [ln for ln in lines if ln.strip() not in fences]
    return "\n".join(lines).strip()


def _domain_of_day(date_str: str, domains: list[str]) -> str:
    domains = domains or DEFAULT_DOMAINS
    try:
        from datetime import date
        idx = date.fromisoformat(date_str).toordinal() % len(domains)
    except Exception:
        idx = 0
    return domains[idx]


def _about(brief) -> str:
    return (getattr(brief, "about", "") or "").strip() or "(profil non disponible)"


def _vault(brief) -> str:
    return (getattr(brief, "vault", "") or "").strip() or "(vault non disponible)"


def _prev_tasks(tasks) -> str:
    if not tasks:
        return "(pas de taches hier)"
    return "\n".join(
        ("- [x] " if t.get("done") else "- [ ] ") + t.get("text", "")
        for t in tasks)


def _mail(data):
    return (data.profile or {}).get("mail_account") or "le compte configure"


def _brief(brief) -> str:
    if brief is None:
        return "(aucun)"
    lines = []
    for pr in getattr(brief, "projects", []) or []:
        lines.append("- " + pr.get("name", "") + " [" + pr.get("status", "")
                     + "] prochaine etape: " + pr.get("next", ""))
    for ob in getattr(brief, "objectives", []) or []:
        lines.append("- objectif: " + ob)
    return "\n".join(lines) or "(aucun)"


def _kv(d) -> str:
    if not d:
        return "(pas de reponses ce soir, genere quand meme)"
    return "\n".join("- " + k + ": " + str(v) for k, v in d.items())
