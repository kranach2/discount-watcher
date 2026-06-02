# Rule: data/price_history.json format

`data/price_history.json` is your long-term memory. It must stay machine-parseable so future runs of you (and future versions of this agent) can read it without surprises.

## Schema (never change without bumping `schema_version`)

```json
{
  "schema_version": 1,
  "products": {
    "<product_key>": {
      "observations": [
        {
          "date": "2026-05-24",
          "store": "woolworths",
          "price": 3.50,
          "was_price": 5.50,
          "is_on_special": true,
          "in_stock": true
        }
      ]
    }
  }
}
```

`<product_key>` is the `key` field from `products.json` (lowercase snake_case, never the display name).

## Rules

1. **Append-only.** Never delete observations. If the file grows past 5MB, an out-of-band cleanup task will prune; that's not your job.
2. **One observation per product per store per run.** If a fetch failed, write an observation with `"in_stock": null, "price": null, "error": "<short reason>"`. Missing data is data.
3. **Dates are ISO format** (`YYYY-MM-DD`), in the agent's local timezone (Perth, Australia / AWST).
4. **Never overwrite the file in place.** Write to `data/price_history.json.tmp`, verify it parses, then `mv` it over the original. The `send_email.py` and `fetch_*.py` scripts are not running concurrently, but this protects against an interrupted write corrupting your memory.
5. **If the file doesn't exist or fails to parse**, log the issue, send the email anyway with today's data only, and create a fresh file with `schema_version: 1` and just today's observations. Do not panic — one day of missing history is fine.

## What this enables

The 30-day median check in CLAUDE.md's "what counts as a discount" rule relies on having at least ~15 prior observations for a product. New products take time to accumulate history; until then, fall back to the store's own `is_on_special` flag and `max_price`.
