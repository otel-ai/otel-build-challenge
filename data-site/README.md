# Data site canary package

Deploy these changes to **otel-hackathon-data-site** (Vercel). They support Phase 1
fingerprint checks and Tier A live-eval questions.

## Changes summary

| Feature | File / route | Purpose |
|---------|--------------|---------|
| Zephyr canary reservation | [canary-reservation.json](canary-reservation.json) | `company_name` only on detail page |
| `dataset_revision` on verify | [verify-page-snippet.tsx](verify-page-snippet.tsx) | Rotates per deploy |
| Changelog (footer link only) | [changelog-page.md](changelog-page.md) | Off-guard field rename notice |
| Pagination edge | [pagination-notes.md](pagination-notes.md) | Last-page-only reservation |

## Deploy checklist

1. Merge `canary-reservation.json` into your reservations seed / generator
2. Add `/changelog` route from `changelog-page.md` content; link in site footer only
3. Update `/verify` to render `dataset_revision` and aggregates matching
   `scripts/compute_load_fingerprint.py` in the brief repo
4. Ensure reservation `RES-ZEPHYR-7F3A` appears **only** on the last list page
5. Set `DATASET_REVISION` env var on Vercel (e.g. `2026.06.12.1`) — bump on redeploy

## Evaluator questions enabled

- Tier A: "What is Zephyr Dynamics Ltd contributing in Q3 stay revenue?"
- Scenario 7 in TOOL_TEST_SCENARIOS: company must exist after ETL
- Health check: `dataset_revision` must match candidate `LOAD_PROOF.json`
