#!/usr/bin/env python3
"""shopify-low-stock: list Shopify product variants that are low on stock.

Uses the Shopify Admin GraphQL API. Only the Python standard library is needed.

Credentials are read from environment variables (never hard-code them):
  SHOPIFY_STORE         your-store.myshopify.com
  SHOPIFY_ACCESS_TOKEN  Admin API access token with the read_products and
                        read_inventory scopes
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

__version__ = "0.1.0"
DEFAULT_API_VERSION = "2025-07"

QUERY = """
query LowStock($cursor: String) {
  productVariants(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      title
      sku
      inventoryQuantity
      inventoryItem { tracked }
      product { title status }
    }
  }
}
"""


def graphql(store: str, token: str, query: str, variables: dict, api_version: str) -> dict:
    url = f"https://{store}/admin/api/{api_version}/graphql.json"
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"Shopify API error {e.code}: {e.read().decode(errors='replace')}")
        errors = data.get("errors")
        if errors:
            throttled = any(
                (err.get("extensions") or {}).get("code") == "THROTTLED" for err in errors
            ) if isinstance(errors, list) else False
            if throttled and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"Shopify GraphQL error: {errors}")
        return data["data"]
    raise SystemExit("Gave up after repeated rate limiting.")


def fetch_variants(store: str, token: str, api_version: str):
    cursor = None
    while True:
        data = graphql(store, token, QUERY, {"cursor": cursor}, api_version)
        page = data["productVariants"]
        yield from page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]


def filter_low_stock(variants, threshold: int, include_drafts: bool = False,
                     include_untracked: bool = False):
    """Return rows for variants at or below `threshold`, lowest stock first."""
    rows = []
    for v in variants:
        qty = v.get("inventoryQuantity")
        if qty is None:
            continue
        tracked = (v.get("inventoryItem") or {}).get("tracked", True)
        if not tracked and not include_untracked:
            continue
        product = v.get("product") or {}
        if product.get("status") != "ACTIVE" and not include_drafts:
            continue
        if qty <= threshold:
            rows.append({
                "product": product.get("title", ""),
                "variant": v.get("title", ""),
                "sku": v.get("sku") or "",
                "quantity": qty,
                "status": product.get("status", ""),
            })
    rows.sort(key=lambda r: (r["quantity"], r["product"].lower()))
    return rows


def print_table(rows) -> None:
    if not rows:
        print("No low-stock variants found.")
        return
    headers = ["product", "variant", "sku", "quantity"]
    widths = {h: max(len(h), *(len(str(r[h])) for r in rows)) for h in headers}
    print("  ".join(h.upper().ljust(widths[h]) for h in headers))
    for r in rows:
        print("  ".join(str(r[h]).ljust(widths[h]) for h in headers))
    print(f"\n{len(rows)} variant(s) at or below threshold.")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="List Shopify variants that are low on stock.")
    p.add_argument("-t", "--threshold", type=int, default=5,
                   help="report variants with quantity <= this (default: 5)")
    p.add_argument("--csv", metavar="FILE", help="also write results to a CSV file")
    p.add_argument("--include-drafts", action="store_true",
                   help="include draft and archived products")
    p.add_argument("--include-untracked", action="store_true",
                   help="include variants whose inventory is not tracked")
    p.add_argument("--api-version", default=os.environ.get("SHOPIFY_API_VERSION", DEFAULT_API_VERSION))
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)

    store = os.environ.get("SHOPIFY_STORE")
    token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    if not store or not token:
        p.error("set SHOPIFY_STORE and SHOPIFY_ACCESS_TOKEN environment variables")

    rows = filter_low_stock(fetch_variants(store, token, args.api_version), args.threshold,
                            args.include_drafts, args.include_untracked)
    print_table(rows)
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["product", "variant", "sku", "quantity", "status"])
            w.writeheader()
            w.writerows(rows)
        print(f"Saved to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
