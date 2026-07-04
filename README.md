# Daily Product Lesson

[![Tests](https://github.com/larkindom/ProductLessonDaily/actions/workflows/tests.yml/badge.svg)](https://github.com/larkindom/ProductLessonDaily/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/github/license/larkindom/ProductLessonDaily)](LICENSE)

> A small automation that emails me one product-management lesson every morning —
> a written takeaway plus a few verbatim key quotes — drawn at random from my
> shelf of product books. Built to turn books I'd already read (but rarely
> revisited) into a daily, low-effort learning habit.

*Built by Larkin Domench as a hands-on product exercise: scoping a real problem,
making explicit build-vs-quality tradeoffs, and shipping a working system.*

---

## The problem
I own several great product/strategy books. I read them once and the ideas faded. I
didn't want another app to check or a course to finish — I wanted the good parts
to **come to me**, in small daily doses, with enough of the original text to
actually land. Spaced, passive, zero-effort review.

## Who it's for
Me, first — but the pattern fits any knowledge worker who wants to compound what
they read instead of letting it decay.

## Key product decisions (and the tradeoffs)
| Decision | Options I weighed | What I chose & why |
|---|---|---|
| **How lessons are generated** | Live LLM each morning vs. a pre-curated bank | **Pre-curated bank.** Higher quality, $0 and reliable at send time, no runtime dependency. The "intelligence" is front-loaded once. |
| **How much book text to include** | Long verbatim excerpts vs. a few short key quotes | Started with long excerpts; **switched to 2–4 short key quotes** after they felt too heavy to read daily. (Real feedback → real iteration.) |
| **Delivery** | In-app/draft vs. real email | **Real email via Gmail**, so it lands in my inbox with no extra step. Auto-detects SSL/465 when the network blocks 587. |
| **Quote integrity** | Trust the generator vs. verify | Built a **validator** that fails the build if any quote isn't verbatim in its source book — guards against paraphrase/hallucination. |
| **Scheduling** | Cloud cron vs. local | **Local `launchd`** — the job needs the book files on my machine and no server to pay for. |

## How it works
```
Books (PDF/EPUB/MOBI)
   │  extract_books.py            → clean text per book
   ▼
book_text/*.txt
   │  curated once into …         → summary + takeaway + verbatim key quotes
   ▼
lessons.json  ──validate_lessons.py──►  every quote must appear verbatim in its book
   │
   │  launchd @ 7:00 AM daily
   ▼
daily_lesson.py  → random lesson (no repeats until the bank cycles) → Gmail SMTP → inbox
```

## What I learned
- **Front-loading quality beats clever runtime.** A boring, deterministic daily
  job + a well-curated dataset is more reliable than a smart job that can fail.
- **Verbatim integrity needs a test, not trust.** The validator caught real
  paraphrase errors I'd have shipped.
- **Small feedback loops matter.** The excerpt-length change came from one round
  of "this feels heavy" — exactly how a product should evolve.

## Run it yourself
> Note: this repo intentionally does **not** include the books or their extracted
> text (copyrighted). It ships the code, architecture, and sample data so you can
> point it at your own library.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pymupdf ebooklib beautifulsoup4 lxml mobi

cp config.example.json config.json     # set your to/from + SMTP
cp lessons.sample.json lessons.json     # or generate your own bank

# add books to a folder, then:
python extract_books.py                 # books → book_text/*.txt
python validate_lessons.py              # verify quotes are verbatim
python daily_lesson.py --dry-run        # preview, no send
python daily_lesson.py                  # send today's lesson
```
Email auth uses a Gmail **app password** read from `$GMAIL_APP_PASSWORD` or
`~/.product_lesson_secret`. Schedule it with `launchd` (macOS) or cron.

## Files
| File | Purpose |
|------|---------|
| `daily_lesson.py` | Picks a lesson (no repeats) and emails it |
| `extract_books.py` | Book files → clean text |
| `validate_lessons.py` | Schema + verbatim-quote check |
| `find_passage.py` | Helper to locate exact quotes in a book |
| `books.json` | Canonical book names → author + text file |
| `config.example.json` / `lessons.sample.json` | Templates (real versions git-ignored) |

## Tech
Python · PyMuPDF / EbookLib / mobi (multi-format extraction) · Gmail SMTP (SSL) ·
macOS `launchd` scheduling.

## Testing
`validate_lessons.py` and `find_passage.py` have a pytest suite covering the
verbatim-quote gate (valid lesson, paraphrase, missing fields, duplicate id,
unknown book, too many quotes) and passage lookup. CI runs it on every push.
```bash
pip install -r requirements-dev.txt
pytest -v
```
