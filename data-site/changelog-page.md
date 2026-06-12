# Changelog page (`/changelog`)

Link this route **only from the site footer** — not from the main nav. Candidates
who scrape once at the start may miss field guidance added here.

---

## Dataset changelog

### 2026-06-12 — `rate_plan_code` display label

The detail page label for corporate rate plans was renamed in the UI from
**"Rate plan"** to **"Commercial rate code"**. The underlying column remains
`rate_plan_code` in Postgres / ETL loads. Scrapers keyed on old label text may
miss the field until they re-read this page.

### 2026-06-12 — Verification metadata

The `/verify` page now exposes `dataset_revision`. Re-run ETL verification after
each data-site deploy and update `etl/LOAD_PROOF.json`.

### 2026-06-12 — Pagination

Reservation `RES-ZEPHYR-7F3A` is listed only on the **last** page of
`/reservations`. Full loads must paginate to completion.

---

## Implementer notes

- Render as a simple static route in the data-site app
- Footer link text: "Dataset changelog" (low prominence)
- Do not add to sitemap.xml with high priority
