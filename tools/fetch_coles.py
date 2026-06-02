#!/usr/bin/env python3
"""
Fetch products from Coles' public search.

Usage:
    python tools/fetch_coles.py "tim tam original"

Returns a JSON array of up to 10 normalised product records to stdout.

NOTE: Coles' site is more aggressive about bot detection than Woolworths.
If you start getting 403s, the most likely causes (in order) are:
  1. Akamai bot protection flagged the User-Agent / no-cookies pattern.
     A real browser session works fine; a bare requests.get does not.
  2. The endpoint moved. Inspect coles.com.au in dev tools to find the
     current bff/search endpoint.
  3. They've added a required header (x-api-key, etc.).

For a small daily run (~10 products) this usually works. For higher
volumes you'll want a real headless-browser fetch (Playwright) or a
paid scraping service.
"""

import json
import sys
import time
from typing import Any
from urllib.parse import quote_plus

import requests

# This is the BFF (backend-for-frontend) endpoint coles.com.au uses for its
# own search UI. Schema and path may shift; treat as best-effort.
SEARCH_URL_TEMPLATE = (
    "https://www.coles.com.au/api/bff/products/search?q={query}&start=0&limit=10"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-AU,en;q=0.9",
    "Referer": "https://www.coles.com.au/",
}


def search(term: str) -> list[dict[str, Any]]:
    session = requests.Session()
    session.headers.update(HEADERS)
    # Warm up cookies.
    session.get("https://www.coles.com.au/", timeout=10)

    url = SEARCH_URL_TEMPLATE.format(query=quote_plus(term))
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    raw = resp.json()

    products: list[dict[str, Any]] = []
    for p in raw.get("results", [])[:10]:
        products.append(normalise(p))
    return products


def normalise(p: dict[str, Any]) -> dict[str, Any]:
    pricing = p.get("pricing", {}) or {}
    price = pricing.get("now")
    was = pricing.get("was")
    is_special = bool(pricing.get("promotionType")) or (
        was is not None and price is not None and price < was
    )

    product_id = p.get("id") or p.get("productId")
    slug = p.get("name", "").lower().replace(" ", "-")
    url = (
        f"https://www.coles.com.au/product/{slug}-{product_id}"
        if product_id
        else None
    )

    return {
        "name": p.get("name", "").strip(),
        "price": price,
        "was_price": was if was and was != price else None,
        "is_on_special": is_special,
        "unit_price": pricing.get("comparable"),
        "in_stock": p.get("availability", {}).get("available", True),
        "url": url,
        "store": "coles",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "no search term given", "store": "coles"}))
        return 2

    term = " ".join(sys.argv[1:]).strip()

    last_err: Exception | None = None
    for attempt in range(2):
        try:
            products = search(term)
            print(json.dumps(products, indent=2))
            return 0
        except requests.HTTPError as e:
            last_err = e
            if e.response.status_code == 429:
                time.sleep(3)
                continue
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            break

    print(json.dumps({"error": str(last_err), "store": "coles"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
