You are building the lesson bank for a "Daily Product Lesson" email tool. Work entirely inside `/Users/larkindomench/Desktop/Larkin/daily-product-lesson`. Do NOT send any email. Your only job is to populate `lessons.json`.

## Goal
Produce about **10 lessons per book** for all 17 books listed in `books.json` — roughly **170 lessons total** — appended into `lessons.json` as one JSON array. Keep the lessons already in `lessons.json`.

## Inputs
- `books.json` — maps each canonical book name to its author and its extracted text file in `book_text/`.
- `book_text/*.txt` — the full extracted text of each book. Read these to find real content.
- `find_passage.py` — helper: `./.venv/bin/python find_passage.py "<book name substring>" "<regex>"` prints clean context around the first match.
- `validate_lessons.py` — checks schema and that every quote appears VERBATIM in its book.

## Lesson schema (each element of the JSON array)
```json
{
  "id": "kebab-case-unique-slug",
  "book": "<exact canonical name from books.json>",
  "author": "<from books.json>",
  "title": "Short, punchy lesson title (5-9 words)",
  "summary": "2-4 sentences in your own words: the impactful takeaway that makes the reader a better product manager. Concrete and actionable, not a book report.",
  "takeaway": "One imperative sentence the reader can act on today.",
  "quotes": [
    {"text": "<SHORT verbatim quote copied exactly from the book>", "chapter": "<chapter or section name/number if identifiable, else ''>"}
  ],
  "tags": ["1-3 PM themes, e.g. strategy, discovery, leadership, execution, writing"]
}
```

## Rules for quotes (critical)
- Quotes MUST be **verbatim** — copy the exact characters from the book text file. Do not paraphrase, merge separate lines with invented punctuation, or fix grammar.
- Keep each quote **short**: 1-3 sentences. Pull **a few key quotes per chapter** as you move through the book — not long passages.
- Each lesson should have **2-4 quotes** that support its summary.
- The validator normalizes whitespace and curly quotes/dashes, so don't worry about those — but the words and punctuation must match what's in the file.

## Method (do this book by book, all 17)
1. Pick the next book in `books.json` that does NOT already have >= 8 lessons in `lessons.json` (this makes the run resumable).
2. Read its `book_text/<file>` — skim it in sections to understand its chapters and main arguments. Use Grep/Read on the txt file, or `find_passage.py` to grab clean verbatim context for a quote you want.
3. Identify ~10 distinct, high-impact lessons spread across the book's chapters. For each, write the summary + takeaway in your own words and attach 2-4 verbatim key quotes (note the chapter).
4. Append these lessons to the array in `lessons.json` and SAVE the file before moving to the next book (incremental progress — never hold all work in memory).
5. After each book, run: `./.venv/bin/python validate_lessons.py` and FIX any "QUOTE NOT FOUND" errors (the quote text isn't verbatim — re-copy it exactly from the file) before continuing.

## Quality bar
- Lessons should be genuinely useful to a practicing product manager: strategy, discovery, execution, leadership, communication/writing, customer research, prioritization, org design.
- Vary the lessons within a book; don't repeat the same idea.
- Titles and summaries are original writing; only the `quotes` are verbatim.

## Finish
When all 17 books each have ~10 lessons:
- Run `./.venv/bin/python validate_lessons.py` one final time and ensure it prints "All checks passed." with ~170 lessons across all 17 books.
- Run `./.venv/bin/python daily_lesson.py --dry-run` to confirm a lesson renders.
- Write a one-line summary of the final lesson count to `build_result.txt`.

Be efficient and thorough. This is an unattended overnight run — keep going book by book until all 17 are done.
