#!/usr/bin/env python3
"""Static smoke checks for the challenge brief repo (no database required)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_tracked_files_exist() -> list[str]:
    errors: list[str] = []
    for rel in subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True
    ).strip().splitlines():
        if rel and not (ROOT / rel).is_file():
            errors.append(f"missing tracked file: {rel}")
    return errors


def check_json_examples() -> list[str]:
    errors: list[str] = []
    load_proof = json.loads((ROOT / "etl/LOAD_PROOF.example.json").read_text())
    manifest = json.loads((ROOT / "etl/SCRAPE_MANIFEST.example.json").read_text())

    for key in (
        "version",
        "reservation_stay_pair_sha256",
        "anchor_date",
        "total_stay_rows",
        "verify_field_map",
    ):
        if key not in load_proof:
            errors.append(f"LOAD_PROOF.example.json missing key: {key}")

    for key in (
        "anchor_date",
        "pages_scraped",
        "reservation_ids_count",
        "reservation_ids_sha256",
    ):
        if key not in manifest:
            errors.append(f"SCRAPE_MANIFEST.example.json missing key: {key}")

    for table, count in load_proof.get("row_counts", {}).items():
        if count != 0:
            errors.append(
                f"LOAD_PROOF.example row_counts.{table} should be 0 in template (got {count})"
            )

    return errors


def check_tools_and_schema() -> list[str]:
    errors: list[str] = []
    required_tools = (ROOT / "REQUIRED_TOOLS.md").read_text()
    schema = (ROOT / "schema.sql").read_text()

    for tool in (
        "get_otb_summary",
        "get_segment_mix",
        "get_pickup_delta",
        "get_block_vs_transient_mix",
    ):
        if tool not in required_tools:
            errors.append(f"REQUIRED_TOOLS.md missing {tool}")

    if "is_block" not in schema:
        errors.append("schema.sql missing is_block")
    if "METRIC_DEFINITIONS.md" not in required_tools:
        errors.append("REQUIRED_TOOLS.md missing METRIC_DEFINITIONS.md requirement")

    views = (ROOT / "sql/VIEWS.example.sql").read_text()
    if "vw_stay_night_active" not in views or "vw_segment_stay_night" not in views:
        errors.append("sql/VIEWS.example.sql missing required views")

    return errors


def check_markdown_links() -> list[str]:
    errors: list[str] = []
    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts or "evaluator" in md.parts or "data-site" in md.parts:
            continue
        rel_md = md.relative_to(ROOT)
        text = md.read_text()
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "#")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = (md.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{rel_md}: link escapes repo: {target}")
                continue
            if not resolved.is_file() and not resolved.is_dir():
                errors.append(f"{rel_md}: broken link: {target}")
    return errors


def main() -> int:
    checks = [
        ("tracked files", check_tracked_files_exist),
        ("json examples", check_json_examples),
        ("tools and schema", check_tools_and_schema),
        ("markdown links", check_markdown_links),
    ]

    failed = False
    for name, fn in checks:
        errors = fn()
        if errors:
            failed = True
            print(f"FAIL {name}:")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"OK   {name}")

    if failed:
        print("\nBrief smoke checks failed.")
        return 1

    print("\nBrief smoke checks passed (database / docker not exercised).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
