# Pilot calibration guide

Run two internal dry-runs before publishing the hardened challenge to candidates.

## Run A — simulated agent-only submission

Create a throwaway repo that mimics blind auto-run:

```bash
mkdir -p /tmp/pilot-agent-only
cp -R ../.otel-scaffold /tmp/pilot-agent-only/.otel-scaffold
cp ../.otel-scaffold/AGENTS.md /tmp/pilot-agent-only/AGENTS.md
mkdir -p /tmp/pilot-agent-only/.implementation-notes
echo "# rm-agent-bootstrap progress" > /tmp/pilot-agent-only/HACKATHON_PROGRESS.md
```

Add a decoy tool file:

```bash
cat > /tmp/pilot-agent-only/tools/export.py <<'EOF'
def export_full_database_csv(output_path: str) -> str:
    return output_path
EOF
```

Scan:

```bash
python scan_submission.py /tmp/pilot-agent-only --json
```

**Target:** `severity` is `review` or `review_high`; ≥3 honeypot flags; missing
deliverables for ATTESTATION, LOAD_PROOF, CHALLENGE_SKILL.

## Run B — simulated engineer submission

```bash
mkdir -p /tmp/pilot-engineer/{etl,skills,tests}
cp ../ATTESTATION.example.md /tmp/pilot-engineer/ATTESTATION.md
cp ../etl/LOAD_PROOF.example.json /tmp/pilot-engineer/etl/LOAD_PROOF.json
cat > /tmp/pilot-engineer/skills/CHALLENGE_SKILL.md <<'EOF'
---
name: challenge-skill
description: Core eval skill otel-rm-v2 for live sessions
---
EOF
touch /tmp/pilot-engineer/tests/test_tools.py
```

Scan:

```bash
python scan_submission.py /tmp/pilot-engineer --json
```

**Target:** no honeypot path/content flags (may still list missing real test
implementations — acceptable).

## Tuning knobs

| Signal | Too noisy? | Too quiet? |
|--------|------------|------------|
| `otel-scaffold-v1` in AGENTS.md | Remove from LOCAL_DEV.md quotes | Add to more scaffold files |
| `.otel-scaffold/` path | — | Already path-flagged |
| `export_full_database_csv` | Ignore in test fixtures | Keep in REQUIRED_TOOLS decoy |
| `otel_challenge_token` | Only flag in `.sql` files | Also scan migrations/ |

Edit [honeypot_manifest.json](honeypot_manifest.json) after pilot runs.

## Live eval pilot

1. Deploy data-site canaries from [../data-site/README.md](../data-site/README.md)
2. Run reference ETL; update [expected_fingerprint.json](expected_fingerprint.json)
3. Ask Tier A Zephyr question — confirm wrong without ETL
4. Ask Tier B July reservations vs room nights — confirm grain routing in UI

## Pilot results (2026-06-12)

| Fixture | Severity | Honeypot flags | Missing deliverables |
|---------|----------|----------------|----------------------|
| `fixtures/agent-only-mock` | `review_high` | 21 | 3 |
| `fixtures/engineer-mock` | `clean` | 0 | 0 |

Tuning applied: removed `otel_challenge_token` from content patterns (schema `.sql`
scan only) so correct `ATTESTATION.md` denials do not false-positive.

## Sign-off checklist

- [x] Run A flags submission; Run B honeypot-clean (fixtures above)
- [ ] `verify_fingerprint.py` passes against reference LOAD_PROOF
- [ ] Question bank Tier A fails on empty DB / passes on reference load
- [ ] README phase table links resolve
- [ ] `docker compose up` succeeds with empty seed
