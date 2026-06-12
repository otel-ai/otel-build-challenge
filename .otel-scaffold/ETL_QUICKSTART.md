# ETL quick start

Faster path than reading the full README.

## Extract

1. Fetch `https://otel-hackathon-data-site.vercel.app/reservations` with `curl` or
   `requests` + BeautifulSoup.
2. The list shows **25 reservations per page** — increment `?page=` until empty.
3. Detail pages are optional for v1; list fields are enough for a first agent demo.

## Transform

Map HTML tables to `reservations_hackathon`. One row per reservation is fine for
early testing (expand to stay-date grain later).

## Load

See `sql/seed_from_csv.sql` if you exported a CSV locally.

## Verify

Spot-check a few rows manually; full `/verify` reconciliation can wait until Phase 4.
