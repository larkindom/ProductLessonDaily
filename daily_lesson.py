#!/usr/bin/env python3
"""Daily Product Lesson emailer.

Picks one lesson at random (no repeats until the whole bank is exhausted) from
lessons.json and emails it to you via Gmail SMTP. Designed to be run once each
morning by a launchd timer.

Setup:
  - lessons.json   : the curated lesson bank (list of lesson objects)
  - config.json    : recipient + SMTP settings
  - GMAIL_APP_PASSWORD : 16-char Gmail app password, read from env or
                         ~/.product_lesson_secret

State:
  - state.json     : tracks which lesson ids have been sent, so we cycle through
                     the whole bank before repeating.

Run manually:        python daily_lesson.py
Preview only (no send): python daily_lesson.py --dry-run
Send a specific id:  python daily_lesson.py --id <lesson-id>
"""
import argparse
import datetime as dt
import html
import json
import os
import random
import smtplib
import ssl
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

HERE = os.path.dirname(os.path.abspath(__file__))
LESSONS_PATH = os.path.join(HERE, "lessons.json")
CONFIG_PATH = os.path.join(HERE, "config.json")
STATE_PATH = os.path.join(HERE, "state.json")
LOG_PATH = os.path.join(HERE, "send.log")
SECRET_FILE = os.path.expanduser("~/.product_lesson_secret")


def log(msg: str) -> None:
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_app_password(cfg) -> str:
    env_name = cfg.get("app_password_env", "GMAIL_APP_PASSWORD")
    pw = os.environ.get(env_name)
    if pw:
        return pw.strip()
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, encoding="utf-8") as f:
            return f.read().strip()
    raise SystemExit(
        f"No Gmail app password found. Set ${env_name} or write it to {SECRET_FILE}"
    )


def pick_lesson(lessons, state, forced_id=None):
    by_id = {l["id"]: l for l in lessons}
    if forced_id:
        if forced_id not in by_id:
            raise SystemExit(f"No lesson with id '{forced_id}'")
        return by_id[forced_id]
    sent = set(state.get("sent_ids", []))
    remaining = [l for l in lessons if l["id"] not in sent]
    if not remaining:  # cycled through everything -> reset
        log("All lessons sent; resetting cycle.")
        state["sent_ids"] = []
        remaining = list(lessons)
    return random.choice(remaining)


def normalize_quotes(lesson):
    """Return list of (text, chapter) tuples, tolerating several shapes."""
    out = []
    raw = lesson.get("quotes")
    if raw is None and lesson.get("excerpt"):  # backward compat
        raw = [lesson["excerpt"]]
    for q in raw or []:
        if isinstance(q, str):
            out.append((q.strip(), ""))
        elif isinstance(q, dict):
            out.append((str(q.get("text", "")).strip(), str(q.get("chapter", "")).strip()))
    return [(t, c) for (t, c) in out if t]


def render_html(lesson, day_number) -> str:
    book = html.escape(lesson["book"])
    author = html.escape(lesson.get("author", ""))
    title = html.escape(lesson["title"])
    summary = html.escape(lesson["summary"]).replace("\n", "<br>")
    takeaway = html.escape(lesson.get("takeaway", ""))
    # key quotes: a few short verbatim pull-quotes
    quote_blocks = []
    for text, chapter in normalize_quotes(lesson):
        cite = f"<div style='font-size:12px;color:#9a9a93;font-family:Arial,sans-serif;margin-top:6px;'>{html.escape(chapter)}</div>" if chapter else ""
        quote_blocks.append(
            "<blockquote style='margin:0 0 16px;padding:2px 0 2px 16px;border-left:3px solid #d8c08a;'>"
            f"<div style='font-size:15px;line-height:1.6;color:#2a2a2a;'>&ldquo;{html.escape(text)}&rdquo;</div>"
            f"{cite}</blockquote>"
        )
    excerpt_html = "".join(quote_blocks)
    tags = " · ".join(html.escape(t) for t in lesson.get("tags", []))

    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f2;">
<div style="max-width:620px;margin:0 auto;padding:28px 22px;font-family:Georgia,'Times New Roman',serif;color:#1d1d1f;">
  <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#9a9a93;font-family:Arial,sans-serif;">
    Daily Product Lesson · {dt.date.today().strftime('%A, %B %-d, %Y')}
  </div>
  <h1 style="font-size:24px;line-height:1.25;margin:10px 0 4px;color:#111;">{title}</h1>
  <div style="font-size:14px;color:#6a6a63;font-family:Arial,sans-serif;margin-bottom:22px;">
    from <em>{book}</em>{' — ' + author if author else ''}
  </div>

  <div style="background:#fff;border-left:4px solid #c9962f;padding:16px 18px;border-radius:4px;margin-bottom:8px;">
    <div style="font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#c9962f;font-family:Arial,sans-serif;margin-bottom:8px;">The Lesson</div>
    <div style="font-size:16px;line-height:1.55;">{summary}</div>
  </div>

  {"<div style='background:#1d1d1f;color:#fff;padding:12px 18px;border-radius:4px;font-family:Arial,sans-serif;font-size:15px;margin-bottom:24px;'>→ " + takeaway + "</div>" if takeaway else ""}

  <div style="font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#9a9a93;font-family:Arial,sans-serif;margin-bottom:10px;">Key quotes</div>
  <div style="border-top:1px solid #e3e3df;padding-top:16px;">
    {excerpt_html}
  </div>

  <div style="margin-top:26px;padding-top:14px;border-top:1px solid #e3e3df;font-size:12px;color:#9a9a93;font-family:Arial,sans-serif;">
    {tags if tags else ''}<br>
    A lesson a day from your Product Books shelf.
  </div>
</div>
</body>
</html>"""


def render_text(lesson, day_number) -> str:
    lines = [
        f"DAILY PRODUCT LESSON — {dt.date.today():%A, %B %d, %Y}",
        "",
        lesson["title"].upper(),
        f"from {lesson['book']}" + (f" — {lesson.get('author')}" if lesson.get("author") else ""),
        "",
        "THE LESSON",
        lesson["summary"],
        "",
    ]
    if lesson.get("takeaway"):
        lines += [f"-> {lesson['takeaway']}", ""]
    lines += ["KEY QUOTES"]
    for text, chapter in normalize_quotes(lesson):
        lines.append(f'  "{text}"' + (f"  — {chapter}" if chapter else ""))
        lines.append("")
    if lesson.get("tags"):
        lines.append(" · ".join(lesson["tags"]))
    return "\n".join(lines)


def send(cfg, subject, text_body, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["from_email"]
    msg["To"] = cfg["to_email"]
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    password = get_app_password(cfg)
    context = ssl.create_default_context()
    port = int(cfg["smtp_port"])
    if port == 465:  # implicit SSL
        with smtplib.SMTP_SSL(cfg["smtp_host"], port, context=context) as server:
            server.login(cfg["from_email"], password)
            server.sendmail(cfg["from_email"], [cfg["to_email"]], msg.as_string())
    else:  # STARTTLS (587)
        with smtplib.SMTP(cfg["smtp_host"], port) as server:
            server.starttls(context=context)
            server.login(cfg["from_email"], password)
            server.sendmail(cfg["from_email"], [cfg["to_email"]], msg.as_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="render but do not send")
    ap.add_argument("--id", help="send a specific lesson id")
    ap.add_argument("--out", help="write rendered HTML to this path (for preview)")
    args = ap.parse_args()

    cfg = load_json(CONFIG_PATH)
    lessons = load_json(LESSONS_PATH, [])
    if not lessons:
        raise SystemExit("lessons.json is empty or missing.")
    state = load_json(STATE_PATH, {"sent_ids": [], "count": 0})

    lesson = pick_lesson(lessons, state, args.id)
    day_number = state.get("count", 0) + 1

    subject = f"Product Daily Lesson {dt.date.today():%m/%d/%y}: {lesson['title']}"
    html_body = render_html(lesson, day_number)
    text_body = render_text(lesson, day_number)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(html_body)
        log(f"Wrote preview to {args.out}")

    if args.dry_run:
        log(f"[DRY RUN] Would send '{lesson['id']}' — {lesson['title']} ({lesson['book']})")
        print("\n----- TEXT PREVIEW -----\n")
        print(text_body)
        return

    send(cfg, subject, text_body, html_body)

    if not args.id:  # only advance the cycle for normal scheduled sends
        state.setdefault("sent_ids", []).append(lesson["id"])
        state["count"] = day_number
        state["last_sent"] = dt.date.today().isoformat()
        save_json(STATE_PATH, state)
    log(f"SENT '{lesson['id']}' — {lesson['title']} ({lesson['book']}) to {cfg['to_email']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # ensure failures land in the log for the cron job
        log(f"ERROR: {e}")
        raise
