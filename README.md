# shopify-low-stock

A small, dependency-free Python command-line tool that lists the product variants in a Shopify store that are running low on stock, so you can reorder before you sell out.

## Features

- Uses the Shopify Admin GraphQL API, with pagination and retry on rate limits
- Set your own low-stock threshold
- Skips draft/archived products and untracked inventory by default
- Prints a table and can export a CSV
- Needs only the Python standard library (Python 3.8+)

## Setup

1. In Shopify admin, go to **Settings → Apps and sales channels → Develop apps** and create a custom app.
2. Give it the Admin API scopes `read_products` and `read_inventory`, then install it and copy the Admin API access token.
3. Set the environment variables:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="shpat_..."
```

Never commit your token to Git.

## Usage

```bash
python low_stock.py                  # variants with 5 or fewer in stock
python low_stock.py -t 10            # custom threshold
python low_stock.py --csv low.csv    # also save to CSV
python low_stock.py --include-drafts --include-untracked
```

Example output:

```
PRODUCT         VARIANT       SKU      QUANTITY
Ottoman Bed     Double/Grey   OTT-DG   0
Ottoman Bed     King/Grey     OTT-KG   2

2 variant(s) at or below threshold.
```

## Running tests

```bash
python -m unittest test_low_stock
```

## Contributing

Issues and pull requests are welcome. Ideas: per-location stock, email/Slack alerts, a GitHub Action to run on a schedule.

## License

MIT, see [LICENSE](LICENSE).
