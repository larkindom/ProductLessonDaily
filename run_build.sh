#!/bin/zsh
# One-shot overnight job: build the Daily Product Lesson bank with Claude Code headless.
# Triggered by launchd (com.larkin.lessonbuild). Removes its own launchd job when done.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "/Users/larkindomench/Desktop/Larkin/daily-product-lesson" || exit 1

LOG="build_run.log"
{
  echo "================ build start $(date) ================"

  claude -p "Follow the instructions in BUILD_PROMPT.md in this directory exactly, and build the complete lesson bank now. Keep working book by book until validate_lessons.py passes with about 170 lessons across all 17 books." \
    --dangerously-skip-permissions \
    --add-dir "/Users/larkindomench/Desktop/Larkin/Product Books" \
    --append-system-prompt "You are running unattended overnight with no human present. Never ask questions or wait for input; make reasonable decisions and keep going until the task in BUILD_PROMPT.md is fully complete. Save lessons.json incrementally after each book."

  echo "================ build end $(date) exit=$? ================"
} >> "$LOG" 2>&1

# Self-remove the one-shot launchd job so it never runs again.
launchctl bootout "gui/$(id -u)/com.larkin.lessonbuild" 2>/dev/null
rm -f "$HOME/Library/LaunchAgents/com.larkin.lessonbuild.plist"
