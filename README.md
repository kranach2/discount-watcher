# Woolies Watcher — a Claude Code agent that watches Woolworths/Coles for discounts

A simple but real agent project. It runs once a day, checks the prices of products on your watchlist at Woolworths and Coles, and emails you a digest. If something is out of stock or genuinely unavailable, a sub-agent goes off and finds reasonable alternatives.

## Mental model (read this first)

There is a lot of jargon around "agents." Strip it back and an agent is just **a loop that does three things**:

1. **Observe** — read the world (here: fetch prices, read your watchlist).
2. **Decide** — reason about what to do (here: is this a discount worth telling the user about? Is this item missing? Should I find substitutes?).
3. **Act** — change the world (here: send an email, update price history).

The "intelligence" lives in step 2. The "tools" are the things that let the agent observe and act in steps 1 and 3.

Claude Code organises this with a few file conventions:

| File | What it is | Analogy |
|---|---|---|
| `CLAUDE.md` | Project-level briefing read every run | The job description |
| `.claude/skills/<name>/SKILL.md` | A how-to Claude pulls in when relevant | A specific procedure manual |
| `.claude/agents/<name>.md` | A sub-agent — a specialist Claude can delegate to | A coworker you can hand work to |
| `.claude/rules/<name>.md` | Strict rules / invariants | The compliance handbook |
| `.claude/settings.json` | Permissions, hooks, which model | The IT policy |
| `tools/*.py` | Plain Python scripts Claude calls via Bash | The hardware |
| `data/*.json` | Persistent state Claude reads/writes | Memory |

Everything else is just glue.

## What this project does today (Phase 1)

- Reads `data/products.json` (your watchlist)
- For each product, calls `tools/fetch_woolworths.py` and `tools/fetch_coles.py`
- Decides whether each result is a meaningful discount (using both the store's "Special" flag and your historical price floor in `data/price_history.json`)
- If a product appears unavailable, spawns the `alternative-finder` sub-agent
- Emails you a digest via `tools/send_email.py`
- Updates `data/price_history.json` so tomorrow's run is smarter

## Phase 2 (later — the cart/checkout flow)

Stubbed for now. The pattern will be: Claude proposes a cart → emails you for approval with a one-time link → after you click approve, Claude (via Playwright) logs in and checks out. **Important honest note**: Woolworths and Coles both have bot detection on the checkout path. We will build it, but expect it to be the most fragile part and we may need to fall back to "open the pre-filled cart in your browser, you click pay."

## Setup

Detailed steps are in `docs/SETUP.md` but the short version:

```bash
# 1. Clone, install deps
pip install -r requirements.txt

# 2. Copy env template, fill in values
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY, GMAIL_USER, GMAIL_APP_PASSWORD, EMAIL_TO

# 3. Edit your watchlist
nano data/products.json

# 4. Test once manually
bash run_daily.sh

# 5. Schedule it (pick one):
#    - GitHub Actions: push to GitHub, set secrets, the workflow runs at 4pm AWST daily
#    - Local cron:     crontab -e   →   0 16 * * * cd /path/to/woolies-watcher && bash run_daily.sh
```

## Adding / removing products

Edit `data/products.json`. The format is documented in that file. No code change needed — Claude reads this fresh every run.
