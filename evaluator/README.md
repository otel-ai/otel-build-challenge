# Evaluator tooling (internal)

**Not for candidates.** Do not link this folder from the public challenge README.

## Setup

```bash
cd evaluator
python -m venv .venv && source .venv/bin/activate
pip install pyyaml
```

## Tools

| Script | Purpose |
|--------|---------|
| `scan_submission.py` | Flag honeypot paths and canary strings in a candidate repo |
| `verify_fingerprint.py` | Compare `LOAD_PROOF.json` to expected baseline |
| `question_bank.yaml` | Live eval questions by tier |
| `rubric.md` | Weighted scoring |
| `honeypot_manifest.json` | Patterns maintained by evaluators |

## Usage

```bash
# Scan a cloned candidate repository
python scan_submission.py /path/to/candidate-repo --json

# Verify load proof (update expected_fingerprint.json after data-site deploy)
python verify_fingerprint.py /path/to/candidate-repo/etl/LOAD_PROOF.json
```

See [PILOT_GUIDE.md](PILOT_GUIDE.md) for calibration runs.
