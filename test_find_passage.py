"""Tests for find_passage.py: locating a verbatim passage for excerpting."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import find_passage as fp


def _run(monkeypatch, capsys, tmp_path, book_sub, pattern, before="30", after="40"):
    txt_dir = tmp_path / "book_text"
    txt_dir.mkdir()
    (txt_dir / "sample-book.txt").write_text(
        "Before context here. The only way to win is to ship. After context here.",
        encoding="utf-8",
    )
    monkeypatch.setattr(fp, "HERE", str(tmp_path))
    monkeypatch.setattr(fp, "TXT_DIR", str(txt_dir))
    monkeypatch.setattr(sys, "argv", ["find_passage.py", book_sub, pattern, before, after])
    fp.main()
    return capsys.readouterr().out


def test_finds_matching_passage_with_context(monkeypatch, capsys, tmp_path):
    out = _run(monkeypatch, capsys, tmp_path, "sample", r"only way to win")
    assert "sample-book.txt" in out
    assert "The only way to win is to ship" in out
    assert "Before context here" in out


def test_match_is_case_insensitive(monkeypatch, capsys, tmp_path):
    out = _run(monkeypatch, capsys, tmp_path, "sample", r"THE ONLY WAY")
    assert "The only way to win" in out


def test_no_matching_book_reports_cleanly(monkeypatch, capsys, tmp_path):
    out = _run(monkeypatch, capsys, tmp_path, "no-such-book", r"anything")
    assert "No book matched" in out
