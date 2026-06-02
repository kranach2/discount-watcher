---
name: price-checking
description: Use this skill whenever you need to fetch and interpret prices from Woolworths or Coles. Covers calling the fetcher scripts, picking the right product match from search results, interpreting the "IsOnSpecial" / "WasPrice" fields, detecting stock status, and what to do when the search returns nothing or the fetcher errors out.
---

# Price checking — Woolworths & Coles

## Calling the fetchers

```bash
python tools/fetch_woolworths.py "tim tam original 200g"
python tools/fetch_coles.py "tim tam original 200g"
```

Each prints a JSON array of up to 10 matches:

```json
[
  {
    "name": "Arnott's Tim Tam Original 200g",
    "price": 3.50,
    "was_price": 5.50,
    "is_on_special": true,
    "unit_price": "$1.75 per 100g",
    "in_stock": true,
    "url": "https://www.woolworths.com.au/shop/productdetails/123456",
    "store": "woolworths"
  }
]
```

If the fetcher errors (HTTP 429, network failure, schema changed), it exits non-zero and prints an error JSON: `{"error": "...", "store": "woolworths"}`. Do **not** retry more than twice — if a store is blocking, note it in the email and move on. The user would rather get a partial email at 4pm than no email at all.

## Picking the right match

Search results can include similar products (Tim Tam Original vs Tim Tam Chewy Caramel). Match against the user's `name` field in `products.json` first, then their `search_terms`. If you genuinely can't tell which is the right one (e.g. two products both seem to match), pick the cheapest and flag the ambiguity in the email body.

## Classifying the result

For each product in the watchlist, after fetching from both stores, classify as one of:

- **`discount`** — see the rule in CLAUDE.md (≥10% off Was, or ≥10% below 30-day median, or at/below user's max_price)
- **`regular_price`** — found and in stock, no meaningful discount
- **`out_of_stock`** — found but `in_stock: false`
- **`not_found`** — no plausible match in either store's results

For `out_of_stock` and `not_found`, hand off to the `alternative-finder` sub-agent.

## Gotchas

- **Unit price matters.** Sometimes Item A is $4 for 200g and Item B is $5 for 400g — B is cheaper per gram. Use `unit_price` to sanity-check.
- **Multi-buy specials.** "2 for $6" deals show up as a separate flag; the fetcher returns these in a `multi_buy` field if present. Treat them as discounts only if the user's typical buy quantity matches.
- **Out of stock ≠ discontinued.** A product missing for one day may be back tomorrow. Only flag as "consider an alternative" if it's been unavailable for 3+ consecutive runs (check `price_history.json`).
