#!/usr/bin/env python3
"""
Fetch products from Woolworths' public search API.

Usage:
    python tools/fetch_woolworths.py "tim tam original"

Returns a JSON array of up to 10 normalised product records to stdout.

NOTE: This calls an unofficial endpoint that powers woolworths.com.au's own
search. It works today, but it is not contractually stable — if the schema
changes, this script will need an update. The CLAUDE.md instructions tell
the agent how to behave if this script errors out (skip the item, note it
in the email, move on).
"""

import json
import sys
import time
from typing import Any

import requests

SEARCH_URL = "https://www.woolworths.com.au/apis/ui/Search/products"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.woolworths.com.au",
    "Referer": "https://www.woolworths.com.au/",
}


def search(term: str, page_size: int = 10) -> list[dict[str, Any]]:
    payload = {
        "SearchTerm": term,
        "PageSize": page_size,
        "PageNumber": 1,
        "SortType": "TraderRelevance",
        "Filters": [],
        "Location": "/shop/search/products",
    }

    # Woolies' API sometimes sets cookies on a warm-up GET; do that first.
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get("https://www.woolworths.com.au/", timeout=10)

    resp = session.post(SEARCH_URL, json=payload, timeout=15)
    resp.raise_for_status()
    raw = resp.json()

    products: list[dict[str, Any]] = []
    for bundle in raw.get("Products", []):
        # Each "bundle" can contain multiple variants; take the first.
        for p in bundle.get("Products", [])[:1]:
            products.append(normalise(p))
    return products


def normalise(p: dict[str, Any]) -> dict[str, Any]:
    """Convert Woolies' verbose schema into our agent's flat format."""
    price = p.get("Price")
    was_price = p.get("WasPrice")
    is_on_special = bool(p.get("IsOnSpecial")) or (
        was_price is not None and price is not None and price < was_price
    )

    stockcode = p.get("Stockcode")
    url = (
        f"https://www.woolworths.com.au/shop/productdetails/{stockcode}"
        if stockcode
        else None
    )

    return {
        "name": p.get("Name", "").strip(),
        "price": price,
        "was_price": was_price if was_price and was_price != price else None,
        "is_on_special": is_on_special,
        "unit_price": p.get("CupString") or p.get("CupPrice"),
        "in_stock": p.get("IsAvailable", True) and not p.get("IsOutOfStock", False),
        "url": url,
        "store": "woolworths",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "no search term given", "store": "woolworths"}))
        return 2

    term = " ".join(sys.argv[1:]).strip()

    # Two tries with backoff. The agent's instructions say not to retry more
    # than twice; we burn one of those retries here so the agent doesn't have to.
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

    print(json.dumps({"error": str(last_err), "store": "woolworths"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
