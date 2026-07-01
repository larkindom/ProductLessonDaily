#!/bin/zsh
# Robust lesson-bank builder: one bounded claude call PER BOOK (not one giant call).
# Each call appends ~10 lessons for a single book, then we verify & validate.
# Resumable (skips books that already have >=8 lessons) and safe (restores a backup
# if a call corrupts lessons.json or drops entries).
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "/Users/larkindomench/daily-product-lesson" || exit 1

PY=./.venv/bin/python
count_all() { $PY -c 'import json;print(len(json.load(open("lessons.json"))))' 2>/dev/null || echo -1; }
count_book() { $PY -c "import json,sys;b=sys.argv[1];print(sum(1 for l in json.load(open('lessons.json')) if l.get('book')==b))" "$1" 2>/dev/null || echo 0; }

echo "############ bank build start $(date) ############"

$PY -c 'import json;[print(k) for k in json.load(open("books.json"))]' | while IFS= read -r book; do
  have=$(count_book "$book")
  if [ "$have" -ge 8 ]; then
    echo ">>> SKIP  '$book' (already has $have)"
    continue
  fi
  before=$(count_all)
  cp lessons.json lessons.bak
  echo ">>> BUILD '$book'  (have $have, total $before)  $(date +%H:%M:%S)"

  claude -p "You are adding lessons to the Daily Product Lesson bank. Read BUILD_PROMPT.md for the exact schema and rules. Author about 10 high-quality, distinct lessons for ONLY this one book: \"$book\". Its text file is listed in books.json under that exact name, inside book_text/. Append your lessons to the existing JSON array in lessons.json WITHOUT removing or changing any existing entries. Every quote must be copied VERBATIM from the book's text file (1-3 sentences each, 2-4 per lesson). When done, run ./.venv/bin/python validate_lessons.py and fix any QUOTE NOT FOUND errors for this book. Do NOT touch any other book's lessons." \
    --dangerously-skip-permissions \
    --append-system-prompt "Unattended run. Never ask questions; just do the work and save lessons.json." \
    < /dev/null > /dev/null 2>&1
  rc=$?

  after=$(count_all)
  if [ "$after" -lt 0 ]; then
    echo "    !! invalid JSON after '$book' (rc=$rc) — restoring backup"
    cp lessons.bak lessons.json
  elif [ "$after" -le "$before" ]; then
    echo "    !! no net new lessons for '$book' (rc=$rc, $before->$after) — restoring backup"
    cp lessons.bak lessons.json
  else
    echo "    ok '$book': $before -> $after (rc=$rc)"
  fi
done

echo "############ validating final bank ############"
$PY validate_lessons.py
echo "FINAL TOTAL: $(count_all) lessons  $(date)"
$PY -c 'import json;print("FINAL TOTAL: "+str(len(json.load(open("lessons.json"))))+" lessons")' > build_result.txt 2>/dev/null
echo "############ bank build end $(date) ############"
