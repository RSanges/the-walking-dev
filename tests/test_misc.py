from walkingdev import llm
from walkingdev.config import Config
from walkingdev.knowledge import make_knowledge
from walkingdev.questions import EVENING, ONBOARDING, Question


def test_parse_json_array_extracts_array():
    assert llm.parse_json_array('blah ["a", "b"] trailing') == ["a", "b"]
    assert llm.parse_json_array("no array here") == []
    assert llm.parse_json_array('prefix [1, 2, 3]') == [1, 2, 3]


def test_local_knowledge_reads_onboarding(tmp_path):
    cfg = Config({"knowledge": {"backend": "local"},
                  "state": {"backend": "sqlite",
                            "sqlite": {"path": str(tmp_path / "s.db")}}}, tmp_path)
    from walkingdev.state import make_state
    make_state(cfg).save_onboarding({"projects": [{"name": "P", "status": "actif"}],
                                     "objectives": ["ship it"]})
    brief = make_knowledge(cfg).gather()
    assert brief.projects[0]["name"] == "P"
    assert brief.objectives == ["ship it"]


def test_question_sets_have_stable_keys():
    keys = [q.key for q in ONBOARDING] + [q.key for q in EVENING]
    assert len(keys) == len(set(keys))  # no duplicate keys within a set is enough
    assert all(isinstance(q, Question) for q in ONBOARDING + EVENING)


def test_make_knowledge_unknown_backend_raises(tmp_path):
    cfg = Config({"knowledge": {"backend": "nope"}}, tmp_path)
    try:
        make_knowledge(cfg)
    except NotImplementedError as e:
        assert "not implemented" in str(e)
    else:
        raise AssertionError("expected NotImplementedError")
