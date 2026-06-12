# Pagination edge case

## Requirement

Reservation **`RES-ZEPHYR-7F3A`** (Zephyr Dynamics Ltd canary) must appear **only
on the last page** of `/reservations`.

## Why

Scrapers that:

- stop when `rows.length < pageSize` on a full page,
- assume fixed total pages without walking to the end, or
- cache only the first page

…will miss the canary. Evaluators use Tier A questions and Scenario 7 tests that
fail without this reservation.

## Suggested implementation

If you use page size `20` and total reservations `N`:

1. Place `RES-ZEPHYR-7F3A` as the **only** row on page `ceil(N/20)` when that
   page would otherwise be short, OR
2. Append it as the last item in the dataset sort order so it naturally lands on
   the final page.

## Verification

Manual: paginate until the last page — confirm Zephyr reservation appears.

Automated: Playwright test in data-site CI clicks "Next" until disabled, asserts
`RES-ZEPHYR-7F3A` visible.
