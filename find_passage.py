#!/usr/bin/env python3
"""Helper: find a passage in a book's extracted text and print clean context.

Usage: python find_passage.py "<book filename substring>" "<regex>" [chars_before] [chars_after]
Prints the matched region as clean paragraphs so excerpts can be copied verbatim.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TXT_DIR = os.path.join(HERE, "book_text")


def main():
    book_sub = sys.argv[1].lower()
    pattern = sys.argv[2]
    before = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    after = int(sys.argv[4]) if len(sys.argv) > 4 else 1200

    matches = [p for p in glob.glob(os.path.join(TXT_DIR, "*.txt")) if book_sub in os.path.basename(p).lower()]
    if not matches:
        print("No book matched:", book_sub); return
    path = matches[0]
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for m in re.finditer(pattern, text, re.IGNORECASE):
        s = max(0, m.start() - before)
        e = min(len(text), m.end() + after)
        chunk = text[s:e].strip()
        print("=" * 70)
        print(f"[{os.path.basename(path)}]  @char {m.start()}")
        print("-" * 70)
        print(chunk)
        print()
        break  # first match only


if __name__ == "__main__":
    main()
