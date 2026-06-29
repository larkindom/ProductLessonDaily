#!/bin/zsh
# Securely store your Gmail app password for the Daily Product Lesson tool.
# Usage:  ./set_password.sh
# It prompts (hidden input), writes ~/.product_lesson_secret with 600 perms,
# then sends a test lesson so you can confirm delivery.

SECRET="$HOME/.product_lesson_secret"
echo -n "Paste your 16-character Gmail app password (input hidden): "
read -s PW
echo
PW="${PW// /}"   # strip spaces Google shows in the app-password display
if [ ${#PW} -lt 16 ]; then
  echo "That doesn't look like a 16-char app password. Aborting."
  exit 1
fi
printf "%s" "$PW" > "$SECRET"
chmod 600 "$SECRET"
echo "Saved to $SECRET (permissions 600)."
echo "Note: the from_email in config.json sends; lessons arrive at to_email."
echo "Sending a test lesson to confirm delivery..."
cd "$(dirname "$0")" || exit 1
./.venv/bin/python daily_lesson.py --id mom-test-talk-about-their-life
