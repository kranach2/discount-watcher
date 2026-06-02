---
name: email-digest
description: Use this skill when composing and sending the daily price-watch email digest. Covers the email structure, subject line conventions, what to include and exclude, how to format prices and discounts, and how to invoke the send_email tool.
---

# Email digest composition

## Subject line

Pick one of these patterns based on what you found:

- `Woolies Watcher · 3 discounts today` (when you have ≥1 discount)
- `Woolies Watcher · nothing on special today` (when nothing meaningful)
- `Woolies Watcher · 2 items unavailable, alternatives inside` (when stock issues dominate)
- `Woolies Watcher · run failed for <store>` (when a fetcher consistently errored)

Lead with the most useful piece of information. Don't write "Your daily digest 🛒✨" — concise and honest.

## Body structure

Use HTML (the send_email tool accepts an `--html-file`). Structure:

```
<h2>Discounts today</h2>
<ul>
  <li>
    <b>Tim Tam Original 200g</b> —
    <b>$3.50 at Woolworths</b> (was $5.50, -36%).
    Cheapest in your 30-day history.
    <a href="...">view</a>
  </li>
  ...
</ul>

<h2>Heads up</h2>
<ul>
  <li>
    <b>Vegemite 380g</b> — out of stock at both stores for 3 days running.
    <br>Alternatives the agent found: Vegemite 220g at Woolworths ($6.50, $2.95/100g —
    slightly worse value but in stock), or Promite 250g at Coles ($5.50, similar taste profile per reviews).
  </li>
</ul>

<h2>No change</h2>
<p>5 other items watched, none on special. (Milk, bread, eggs, butter, oats.)</p>
```

## Discount line conventions

For each discount, in one line: **name** — **price at store** (was-price, percent off). Then a half-line of context (why it's worth telling them: "below your max", "cheapest in 30 days", "matches typical sale floor").

If you have store-marked specials AND a historical-low discount, show the better framing (historical-low is more interesting).

## Sending

Write the HTML body to `/tmp/digest.html`, then:

```bash
python tools/send_email.py \
  --subject "Woolies Watcher · 3 discounts today" \
  --html-file /tmp/digest.html
```

The tool reads sender, recipient, and Gmail app password from env vars (`GMAIL_USER`, `GMAIL_APP_PASSWORD`, `EMAIL_TO`).

## What to omit

- Don't show items that are at their normal price unless the user has 5 or fewer items watched (in which case a "no change" footer is fine for completeness).
- Don't include the agent's reasoning. The user wants the answer, not the working.
- Don't apologise or hedge. If a store failed, one sentence: "Coles fetch failed today — will retry tomorrow."
