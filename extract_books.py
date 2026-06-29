#!/usr/bin/env python3
"""Extract clean plain text from every book in the Product Books folder.

Outputs one .txt file per book into ./book_text/ . Handles PDF, EPUB, MOBI.
Skips the Russian FB2 (The Goal) and the duplicate Build Trap file.
"""
import os
import re
import sys
import glob

BOOKS_DIR = "/Users/larkindomench/Desktop/Larkin/Product Books"
OUT_DIR = os.path.join(os.path.dirname(__file__), "book_text")
os.makedirs(OUT_DIR, exist_ok=True)

# Skip these (duplicate / non-English)
SKIP = {
    "Melissa Perri - Escaping the Build Trap_ How Effective Product Management Creates Real Value (2018, O’Reilly Media) - libgen.li (1).pdf",
    "[The Goal №1] Голдратт, Элиягу М._ - libgen.li.fb2",
}


def clean(text: str) -> str:
    # normalize whitespace, drop control chars, collapse blank lines
    text = text.replace("\x00", " ")
    # de-hyphenate words split across line breaks
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def from_pdf(path: str) -> str:
    import fitz
    doc = fitz.open(path)
    parts = []
    for page in doc:
        parts.append(page.get_text("text"))
    doc.close()
    return clean("\n".join(parts))


def from_epub(path: str) -> str:
    from ebooklib import epub
    import ebooklib
    from bs4 import BeautifulSoup
    book = epub.read_epub(path)
    parts = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "lxml")
        for tag in soup(["script", "style"]):
            tag.decompose()
        parts.append(soup.get_text("\n"))
    return clean("\n".join(parts))


def from_mobi(path: str) -> str:
    import mobi
    from bs4 import BeautifulSoup
    tmpdir, filepath = mobi.extract(path)
    # mobi.extract returns path to an html/epub file
    if filepath.lower().endswith((".html", ".htm", ".xhtml")):
        with open(filepath, "rb") as f:
            soup = BeautifulSoup(f.read(), "lxml")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return clean(soup.get_text("\n"))
    elif filepath.lower().endswith(".epub"):
        return from_epub(filepath)
    else:
        with open(filepath, "rb") as f:
            return clean(f.read().decode("utf-8", "ignore"))


def main():
    files = sorted(glob.glob(os.path.join(BOOKS_DIR, "*")))
    for path in files:
        name = os.path.basename(path)
        if name in SKIP or name.startswith("."):
            print(f"SKIP   {name}")
            continue
        ext = os.path.splitext(name)[1].lower()
        out = os.path.join(OUT_DIR, os.path.splitext(name)[0] + ".txt")
        try:
            if ext == ".pdf":
                text = from_pdf(path)
            elif ext == ".epub":
                text = from_epub(path)
            elif ext == ".mobi":
                text = from_mobi(path)
            else:
                print(f"SKIP   {name} (unsupported {ext})")
                continue
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"OK     {name}  ->  {len(text):,} chars")
        except Exception as e:
            print(f"FAIL   {name}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
