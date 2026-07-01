#!/bin/zsh
# One-shot scheduled wrapper: run the resumable per-book bank build, then remove
# its own launchd timer so it never fires again.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
PROJ="/Users/larkindomench/daily-product-lesson"
/bin/zsh "$PROJ/build_bank.sh" >> "$PROJ/bank_build.log" 2>&1
launchctl bootout "gui/$(id -u)/com.larkin.bankbuild" 2>/dev/null
rm -f "$HOME/Library/LaunchAgents/com.larkin.bankbuild.plist"
