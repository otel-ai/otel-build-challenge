# Evaluation rubric (internal)

Weighted scoring for Phase 4–5. Honeypot flags do not auto-fail; they trigger
manual review and Phase 5 probes.

| Dimension | Weight | Pass signals | Fail signals |
|-----------|--------|--------------|--------------|
| ETL correctness | 20% | `LOAD_PROOF.json` matches baseline; Zephyr canary present; `/health` fingerprint | Wrong row counts; missing last-page reservation; stale `dataset_revision` |
| Tool layer | 25% | Required tools; tests pass; no raw SQL tools | Single `run_sql`; grain bugs in Tier B |
| Skills / judgment | 30% | Tier D/E strong answers; `otel-rm-v2` in CHALLENGE_SKILL | Thin metrics-only skills; generic GM platitudes |
| Agent architecture | 15% | All Deep Agents blocks justified in ARCHITECTURE.md; streaming UI | Blocks unused; Streamlit-only black box |
| Engineering authenticity | 10% | Phase 5 explains code; no honeypot artifacts | Scaffold copy; `otel_challenge_token`; `export_full_database_csv` |

## Severity guide (honeypot scanner)

| Scanner severity | Action |
|------------------|--------|
| `clean` | Standard eval |
| `review` | Add honeypot probe in Phase 5; ask AI declaration in ATTESTATION |
| `review_high` | Multiple aggressive pattern matches; prioritize architecture interview |

## Phase gate minimums

| Phase | Minimum to proceed |
|-------|-------------------|
| 0 | Correct canary answer on `otel_challenge_token` |
| 1 | Fingerprint within tolerance of expected |
| 2 | ≥6 tests; three required tool names present |
| 3 | ≥4 skills; ARCHITECTURE.md; CHALLENGE_SKILL phrase |
| 4 | Live Tier A + one Tier B question answered correctly |
| 5 | Tool explanation + patch test passed |

## Notes

- Update [expected_fingerprint.json](expected_fingerprint.json) whenever the data
  site deploy bumps `dataset_revision` or adds canary rows (+3 stay rows for Zephyr → 458 total).
- Question bank: [question_bank.yaml](question_bank.yaml)
