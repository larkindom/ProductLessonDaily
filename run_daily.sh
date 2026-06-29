#!/bin/zsh
# Daily 7 AM job: send one product lesson via Gmail SMTP.
# Reads the app password from ~/.product_lesson_secret (or $GMAIL_APP_PASSWORD).
export PATH="$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "/Users/larkindomench/Desktop/Larkin/daily-product-lesson" || exit 1
exec ./.venv/bin/python daily_lesson.py >> send.log 2>&1
