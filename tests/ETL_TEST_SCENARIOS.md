# Published ETL test scenarios (Phase 1)

Implement these as **property tests** in your `tests/test_etl.py`. You need
**at least three** cases covering the scenarios below.

Assume a **correct scrape → load** of the hackathon dataset into Postgres.

---

## Scenario 1 — Lookup row counts

**Properties:**

- `room_type_lookup`: 3 rows
- `market_code_lookup`: 10 rows
- `channel_code_lookup`: 4 rows

---

## Scenario 2 — Fact-table grain uniqueness

**Properties:**

- No duplicate `(reservation_id, stay_date)` pairs in `reservations_hackathon`
- Matches the unique constraint in [schema.sql](../schema.sql)

---

## Scenario 3 — Manifest and verify reconciliation

**Properties:**

- `etl/SCRAPE_MANIFEST.json` → `reservation_ids_count` equals
  `count(distinct reservation_id)` in the fact table
- `total_stay_rows` in your DB equals `total_stay_rows` on `/verify` for the
  manifest `anchor_date`
- Optional: recompute `reservation_ids_sha256` from DB and assert it matches the manifest

---

## Scenario 4 (bonus) — Stay row expansion

**Properties:**

- For at least one multi-night reservation, `count(*)` of stay rows equals `nights`
  from the detail page (grain sanity check)
