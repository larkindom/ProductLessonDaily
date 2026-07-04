"""Tests for validate_lessons.py: text normalization and the verbatim-quote gate.

Uses tmp_path fixtures to stand in for books.json / lessons.json / book_text
so tests don't depend on the (git-ignored, copyrighted) real library.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_lessons as vl


def test_norm_collapses_whitespace():
    assert vl.norm("Hello   \n  world") == "hello world"


def test_norm_normalizes_curly_quotes_and_dashes():
    assert vl.norm("“Don’t stop—ever…”") == '"don\'t stop-ever..."'


def test_norm_is_case_insensitive():
    assert vl.norm("HELLO") == vl.norm("hello")


@pytest.fixture
def library(tmp_path, monkeypatch):
    """A minimal fake book library: one book, one lesson bank."""
    txt_dir = tmp_path / "book_text"
    txt_dir.mkdir()
    (txt_dir / "sample.txt").write_text(
        "The only way to win is to ship something people actually want.",
        encoding="utf-8",
    )
    books = {"Sample Book": {"file": "sample.txt"}}
    (tmp_path / "books.json").write_text(json.dumps(books), encoding="utf-8")

    monkeypatch.setattr(vl, "HERE", str(tmp_path))
    monkeypatch.setattr(vl, "TXT_DIR", str(txt_dir))
    return tmp_path


def _run(lessons, library, monkeypatch, capsys):
    path = library / "lessons.json"
    path.write_text(json.dumps(lessons), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["validate_lessons.py", str(path)])
    try:
        vl.main()
        code = 0
    except SystemExit as e:
        code = e.code or 0
    return code, capsys.readouterr().out


def test_valid_lesson_passes(library, monkeypatch, capsys):
    lessons = [{
        "id": "sample-1",
        "book": "Sample Book",
        "title": "Ship it",
        "summary": "Bias toward shipping.",
        "quotes": ["The only way to win is to ship something people actually want."],
    }]
    code, out = _run(lessons, library, monkeypatch, capsys)
    assert code == 0
    assert "All checks passed." in out


def test_paraphrased_quote_fails_build(library, monkeypatch, capsys):
    lessons = [{
        "id": "sample-1",
        "book": "Sample Book",
        "title": "Ship it",
        "summary": "Bias toward shipping.",
        "quotes": ["The only way to win is to ship what people really want."],  # paraphrased
    }]
    code, out = _run(lessons, library, monkeypatch, capsys)
    assert code != 0
    assert "QUOTE NOT FOUND" in out


def test_missing_required_field_fails_build(library, monkeypatch, capsys):
    lessons = [{
        "id": "sample-1",
        "book": "Sample Book",
        "quotes": ["The only way to win is to ship something people actually want."],
        # missing "title" and "summary"
    }]
    code, out = _run(lessons, library, monkeypatch, capsys)
    assert code != 0
    assert "missing 'title'" in out
    assert "missing 'summary'" in out


def test_duplicate_id_fails_build(library, monkeypatch, capsys):
    lesson = {
        "id": "sample-1",
        "book": "Sample Book",
        "title": "Ship it",
        "summary": "Bias toward shipping.",
        "quotes": ["The only way to win is to ship something people actually want."],
    }
    code, out = _run([lesson, dict(lesson)], library, monkeypatch, capsys)
    assert code != 0
    assert "duplicate id" in out


def test_unknown_book_fails_build(library, monkeypatch, capsys):
    lessons = [{
        "id": "sample-1",
        "book": "A Book Not In The Library",
        "title": "Ship it",
        "summary": "Bias toward shipping.",
        "quotes": ["Anything."],
    }]
    code, out = _run(lessons, library, monkeypatch, capsys)
    assert code != 0
    assert "unknown book" in out


def test_too_many_quotes_fails_build(library, monkeypatch, capsys):
    lessons = [{
        "id": "sample-1",
        "book": "Sample Book",
        "title": "Ship it",
        "summary": "Bias toward shipping.",
        "quotes": ["The only way to win is to ship something people actually want."] * 7,
    }]
    code, out = _run(lessons, library, monkeypatch, capsys)
    assert code != 0
    assert "expected 1-6 quotes" in out
