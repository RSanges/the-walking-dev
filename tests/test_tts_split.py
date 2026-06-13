from walkingdev.tts.omnivoice import _split


def test_splits_on_sentence_punctuation():
    chunks = _split("Une phrase. Une question ? Une exclamation !", max_chars=20)
    assert len(chunks) >= 2
    assert all(len(c) <= 20 for c in chunks)


def test_hard_wraps_oversized_sentence():
    chunks = _split("x" * 1300, max_chars=600)
    assert all(len(c) <= 600 for c in chunks)
    assert sum(len(c) for c in chunks) == 1300


def test_keeps_short_text_in_one_chunk():
    chunks = _split("Court et simple.", max_chars=600)
    assert chunks == ["Court et simple."]


def test_empty_text_yields_no_chunks():
    assert _split("", max_chars=600) == []
