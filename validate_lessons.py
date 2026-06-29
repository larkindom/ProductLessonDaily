#!/usr/bin/env python3
"""Validate lessons.json: schema + every quote must appear verbatim in its book.

Whitespace and curly/straight quotes/dashes are normalized before matching, so
formatting differences don't cause false failures. Exits non-zero on any problem.

Usage: python validate_lessons.py [path/to/lessons.json]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TXT_DIR = os.path.join(HERE, "book_text")


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-").replace("…", "...")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "lessons.json")
    books = json.load(open(os.path.join(HERE, "books.json"), encoding="utf-8"))
    lessons = json.load(open(path, encoding="utf-8"))

    # cache normalized book texts
    cache = {}
    for name, meta in books.items():
        p = os.path.join(TXT_DIR, meta["file"])
        cache[name] = norm(open(p, encoding="utf-8").read()) if os.path.exists(p) else None

    errors = []
    ids = set()
    per_book = {}
    quote_count = 0

    for i, l in enumerate(lessons):
        where = f"lesson #{i} ({l.get('id', '?')})"
        for field in ("id", "book", "title", "summary", "quotes"):
            if not l.get(field):
                errors.append(f"{where}: missing '{field}'")
        lid = l.get("id")
        if lid in ids:
            errors.append(f"{where}: duplicate id")
        ids.add(lid)
        book = l.get("book")
        per_book[book] = per_book.get(book, 0) + 1
        if book not in books:
            errors.append(f"{where}: unknown book '{book}'")
            continue
        body = cache.get(book)
        if body is None:
            errors.append(f"{where}: no text for book '{book}'")
            continue
        quotes = l.get("quotes") or []
        if not (1 <= len(quotes) <= 6):
            errors.append(f"{where}: expected 1-6 quotes, got {len(quotes)}")
        for q in quotes:
            quote_count += 1
            text = q["text"] if isinstance(q, dict) else q
            if norm(text) not in body:
                errors.append(f"{where}: QUOTE NOT FOUND in book -> \"{text[:70]}...\"")

    print(f"Lessons: {len(lessons)} | quotes: {quote_count} | books covered: {len(per_book)}")
    for b in sorted(per_book):
        print(f"  {per_book[b]:>3}  {b}")
    if errors:
        print(f"\n{len(errors)} PROBLEM(S):")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
