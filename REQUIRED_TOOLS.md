# Required tool layer (Phase 2)

Your Revenue Manager Agent must expose a **deliberate tool surface**. Handing the
model a single `run_sql(query)` tool is an automatic fail.

Implement the four tools below with these **exact names** and semantics. How you
structure modules, types, and database access is your choice.

## General rules

- Tools must **not** accept arbitrary SQL strings from the model.
- Each tool docstring must state the **grain** of every count and sum it returns.
- Default behaviour for OTB-style questions: **exclude** `reservation_status = 'Cancelled'`
  unless the tool argument explicitly includes them.
- Room nights = `sum(number_of_spaces)` at stay-date grain unless documented otherwise.
- Reservation count = `count(distinct reservation_id)` at the filtered grain.
- **Query through views:** implement tools against
  [sql/VIEWS.example.sql](sql/VIEWS.example.sql) (`vw_stay_night_active`,
  `vw_segment_stay_night`) or an internal query layer with the same filters and
  joins. Do not expose raw table scans to the model.

Apply the views after `schema.sql`:

```bash
psql "$DATABASE_URL" -f sql/VIEWS.example.sql
```

---

## 1. `get_otb_summary`

```python
def get_otb_summary(stay_month: str, exclude_cancelled: bool = True) -> dict:
    """
    On-the-books summary for a calendar month of stay dates (YYYY-MM).

    Returns:
      - stay_month
      - row_count (stay-date rows)
      - reservation_count (distinct reservation_id)
      - room_nights (sum of number_of_spaces)
      - room_revenue (sum daily_room_revenue_before_tax)
      - total_revenue (sum daily_total_revenue_before_tax)
      - exclude_cancelled (echo input)
    """
```

**Grain note:** `row_count` is **not** reservation count. Document that in the docstring.

---

## 2. `get_segment_mix`

```python
def get_segment_mix(
    stay_month: str,
    macro_group: str | None = None,
) -> dict:
    """
  Segment mix for a stay month.

  Returns a list of segments with:
    - market_code, market_name, macro_group
    - room_nights, total_revenue
    - share_of_room_nights (0–1, denominator = all segments in scope)
    - share_of_revenue (0–1, same denominator)

  If macro_group is set, filter to that macro_group only.
  """
```

**Denominator:** shares must use the **same filtered population** for every segment
in the result set. State the denominator in the return payload.

---

## 3. `get_pickup_delta`

```python
def get_pickup_delta(
    booking_window_days: int,
    future_stay_from: str,
) -> dict:
    """
  Booking pace / pickup for future stays.

  booking_window_days: include reservations whose create_datetime falls in
    [now - booking_window_days, now] (UTC).
  future_stay_from: ISO date; only stay_date >= this date.

  Uses create_datetime for the booking window — not stay_date.

  Returns:
    - booking_window_days, future_stay_from
    - new_reservations (distinct reservation_id created in window)
    - new_room_nights (sum number_of_spaces for those stays)
    - new_total_revenue
    - by_segment (top segments by revenue with same definitions)
    """
```

---

## 4. `get_block_vs_transient_mix`

```python
def get_block_vs_transient_mix(
    stay_month: str,
    exclude_cancelled: bool = True,
) -> dict:
    """
  Block vs transient room-night and revenue mix for a stay month (YYYY-MM).

  Uses is_block on the fact table:
    - block: is_block = true
    - transient: is_block = false

  Returns:
    - stay_month, exclude_cancelled
    - block_room_nights, transient_room_nights
    - block_total_revenue, transient_total_revenue
    - share_of_room_nights_block (0–1)
    - share_of_room_nights_transient (0–1)
    - share_of_revenue_block (0–1)
    - share_of_revenue_transient (0–1)
    - denominator_room_nights, denominator_revenue (state explicitly)
    """
```

**Grain note:** room nights = `sum(number_of_spaces)` at stay-date grain within the month.

---

## Tests you must ship

Add `tests/test_tools.py` in your solution repo with **at least eight** test cases.
We publish property-based scenarios in [tests/TOOL_TEST_SCENARIOS.md](tests/TOOL_TEST_SCENARIOS.md).
Your tests should encode those properties against your loaded database (or fixtures
derived from a correct ETL load).

---

## Submission checklist (Phase 2)

- [ ] Four required tools implemented with exact names
- [ ] Tools query through `vw_stay_night_active` / `vw_segment_stay_night` (or equivalent)
- [ ] No raw SQL string parameter on any agent-facing tool
- [ ] `tests/test_tools.py` with ≥ 8 cases covering published scenarios
- [ ] Tool module(s) importable without starting the agent server
