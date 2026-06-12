#!/usr/bin/env python3
"""Compare candidate LOAD_PROOF.json against evaluator baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def compare_proofs(
    candidate: dict[str, Any],
    expected: dict[str, Any],
    tolerance: float = 0.01,
) -> list[str]:
    issues: list[str] = []

    for table, expected_count in expected.get("row_counts", {}).items():
        actual = candidate.get("row_counts", {}).get(table)
        if actual != expected_count:
            issues.append(
                f"row_counts.{table}: expected {expected_count}, got {actual}"
            )

    expected_hash = expected.get("reservation_stay_pair_sha256")
    actual_hash = candidate.get("reservation_stay_pair_sha256")
    if expected_hash and actual_hash != expected_hash:
        issues.append("reservation_stay_pair_sha256 mismatch")

    expected_revision = expected.get("dataset_revision")
    actual_revision = candidate.get("dataset_revision")
    if expected_revision and actual_revision != expected_revision:
        issues.append(
            f"dataset_revision: expected {expected_revision}, got {actual_revision}"
        )

    for key, expected_value in expected.get("aggregates", {}).items():
        actual_value = candidate.get("aggregates", {}).get(key)
        if actual_value is None:
            issues.append(f"aggregates.{key}: missing")
            continue
        if isinstance(expected_value, (int, float)) and isinstance(
            actual_value, (int, float)
        ):
            if abs(float(actual_value) - float(expected_value)) > tolerance:
                issues.append(
                    f"aggregates.{key}: expected {expected_value}, got {actual_value}"
                )
        elif actual_value != expected_value:
            issues.append(
                f"aggregates.{key}: expected {expected_value}, got {actual_value}"
            )

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("load_proof", type=Path, help="Candidate etl/LOAD_PROOF.json")
    parser.add_argument(
        "--expected",
        type=Path,
        default=Path(__file__).with_name("expected_fingerprint.json"),
        help="Evaluator baseline JSON",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.load_proof.is_file():
        raise SystemExit(f"File not found: {args.load_proof}")

    candidate = load_json(args.load_proof)
    if not args.expected.is_file():
        report = {
            "status": "skipped",
            "message": (
                f"Baseline not found at {args.expected}. "
                "Update expected_fingerprint.json after data-site deploy."
            ),
            "candidate_row_counts": candidate.get("row_counts"),
        }
        print(json.dumps(report, indent=2))
        sys.exit(0)

    expected = load_json(args.expected)
    issues = compare_proofs(candidate, expected)
    report = {
        "status": "pass" if not issues else "fail",
        "issues": issues,
        "candidate_generated_at": candidate.get("generated_at"),
        "expected_dataset_revision": expected.get("dataset_revision"),
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Status: {report['status']}")
        for issue in issues:
            print(f"  - {issue}")

    sys.exit(0 if not issues else 2)


if __name__ == "__main__":
    main()
