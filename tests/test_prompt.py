from walkingdev.knowledge.base import Brief
from walkingdev.writer.base import WriteInput
from walkingdev.writer.prompt import DEFAULT_DOMAINS, build_prompt, clean_script


def _build(profile, date="2026-06-13", connectors=False):
    return build_prompt(WriteInput(profile=profile, evening={}, brief=Brief(), date=date),
                        connectors=connectors)


def test_default_prompt_has_no_personal_data():
    p = _build({"name": "Alex"})
    for leak in ("TDAH", "creanciers", "Cervobsidian", "Romain", "rsanges"):
        assert leak not in p
    assert any(d in p for d in DEFAULT_DOMAINS)


def test_challenge_domains_and_context_injected():
    p = _build({"name": "Alex", "challenge_domains": ["mon focus"],
                "challenge_context": "mes details perso"})
    assert "mon focus" in p
    assert "mes details perso" in p


def test_mail_account_none_does_not_render_none():
    p = _build({"name": "Alex", "mail_account": None}, connectors=True)
    assert "compte None" not in p
    assert "le compte configure" in p


def test_connectors_false_skips_mail_and_agenda():
    p = _build({"name": "Alex"}, connectors=False)
    assert "connecteurs Gmail" not in p
    assert "Pas de segment mails ni agenda" in p


def test_connectors_true_includes_mail_and_agenda():
    p = _build({"name": "Alex", "mail_account": "me@example.com"}, connectors=True)
    assert "outil Gmail" in p
    assert "me@example.com" in p


def test_addresses_user_by_name():
    assert "Alex" in _build({"name": "Alex"})


def test_clean_script_keeps_legit_opening():
    s = clean_script("Bonjour Alex, on attaque la journee.\nLigne deux.")
    assert s.splitlines()[0] == "Bonjour Alex, on attaque la journee."


def test_clean_script_strips_meta_prefix_and_fences():
    s = clean_script("Voici le script pret a vocaliser :\n```\nBonjour.\n```")
    assert s == "Bonjour."
