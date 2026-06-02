#!/usr/bin/env bash
# run_daily.sh — the single entrypoint cron (or GitHub Actions) calls.
#
# It loads env vars from .env if present, then runs Claude Code in
# headless mode (-p / --print) with a short kickoff prompt. Claude reads
# CLAUDE.md, skills, agents, and the data/ files on its own.
#
# Exit code propagates: non-zero if Claude errored or send_email failed.

set -euo pipefail

cd "$(dirname "$0")"

# Load .env if it exists (GitHub Actions uses repo secrets instead)
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Sanity check the must-haves.
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY is required}"
: "${GMAIL_USER:?GMAIL_USER is required}"
: "${GMAIL_APP_PASSWORD:?GMAIL_APP_PASSWORD is required}"
: "${EMAIL_TO:?EMAIL_TO is required}"

# A short, deliberate kickoff. CLAUDE.md does the heavy lifting; we just
# tell Claude it's time to run.
PROMPT="It is time for today's price-watch run. Follow the daily flow in CLAUDE.md. When you're done, your last action should be sending exactly one email."

# --print runs non-interactively. --permission-mode=acceptEdits lets Claude
# write to data/price_history.json without prompting (settings.json restricts
# what it can touch).
claude \
  --print \
  --permission-mode=acceptEdits \
  --model=claude-sonnet-4-5 \
  "$PROMPT"
