# Published tool test scenarios (Phase 2)

Implement these as **property tests** in your `tests/test_tools.py`. You do not
need to match exact floating-point totals in unit tests if you document tolerance;
structural properties below are mandatory.

Assume a **correct ETL load** of the hackathon dataset into Postgres.

---

## Scenario 1 — Grain inequality (July OTB)

**Tool:** `get_otb_summary("2025-07", exclude_cancelled=True)`

**Properties:**

- `reservation_count < row_count` (unless you prove equality is impossible for this month)
- `room_nights >= reservation_count`
- `room_revenue <= total_revenue` for the same month (total includes non-room components)

---

## Scenario 2 — Cancellation filter changes counts

**Tool:** `get_otb_summary` for any month with known cancellations

**Properties:**

- `exclude_cancelled=True` → `row_count` strictly less than `exclude_cancelled=False`
  when the month contains cancelled stay rows
- `reservation_count` with exclusions ≤ `reservation_count` without exclusions

---

## Scenario 3 — Segment shares sum to one

**Tool:** `get_segment_mix("2025-07", macro_group=None)`

**Properties:**

- `sum(share_of_room_nights) == 1.0` ± 1e-6
- `sum(share_of_revenue) == 1.0` ± 1e-6
- Every share is between 0 and 1 inclusive

---

## Scenario 4 — Macro group filter narrows universe

**Tool:** `get_segment_mix("2025-07", macro_group="Retail")` vs `macro_group=None`

**Properties:**

- Filtered total `room_nights` ≤ unfiltered total `room_nights`
- Every returned segment has `macro_group == "Retail"`

---

## Scenario 5 — Pickup uses booking date, not stay date

**Tool:** `get_pickup_delta(booking_window_days=365, future_stay_from="2025-07-01")`

**Properties:**

- Result only includes stays with `stay_date >= future_stay_from`
- Changing `booking_window_days` to a very small value (e.g. 1) produces
  `new_reservations` ≤ the 365-day window result
- Document in test comments that `create_datetime` defines the booking window

---

## Scenario 6 — OTA concentration signal

**Tool:** `get_segment_mix("2025-08", macro_group=None)`

**Properties:**

- At least one segment with `market_code == "OTA"` exists in hackathon data
- `share_of_revenue` for OTA is strictly between 0 and 1
- Test fails loudly if OTA segment missing (signals broken ETL or wrong month)

---

## Scenario 7 (bonus) — Detail-page completeness

**Tool:** ad hoc query or extended tool test

**Properties:**

- Every reservation on the data site list has been opened on its detail page during ETL
- `company_name` and `rate_plan_code` are populated where the site shows them
- Row count matches the `/verify` page after a full pagination pass

---

## Scenario 8 — Block shares sum to one

**Tool:** `get_block_vs_transient_mix("2025-07", exclude_cancelled=True)`

**Properties:**

- `share_of_room_nights_block + share_of_room_nights_transient == 1.0` ± 1e-6
- `share_of_revenue_block + share_of_revenue_transient == 1.0` ± 1e-6
- `block_room_nights + transient_room_nights == denominator_room_nights`

---

## Scenario 9 — OTB room nights match segment total

**Tools:** `get_otb_summary("2025-07")` and `get_segment_mix("2025-07")`

**Properties:**

- `get_otb_summary.room_nights == sum(segment.room_nights)` across all segments
  returned by `get_segment_mix` for the same month (same cancellation filter)

---

## Scenario 10 — `/verify` reconciliation

**Tool:** ad hoc check after ETL (not necessarily a named tool)

**Properties:**

- `total_stay_rows` in your DB equals `total_stay_rows` on `/verify` for your scrape anchor date
- `otb_room_nights` in your DB equals `/verify` → `otb_room_nights` (same anchor)
- Record `anchor_date` in `LOAD_PROOF.json` and health endpoint

Document how you scraped `/verify` (browser automation or manual cross-check).
