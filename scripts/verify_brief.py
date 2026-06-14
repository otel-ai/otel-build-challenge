#!/usr/bin/env python3
"""Smoke checks for the challenge brief (public repository only)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_SITE_URL = "https://otel-hackathon-data-site.vercel.app"
DATA_SITE_ROUTES = ("/", "/reservations", "/verify", "/reference", "/changelog")
DEFAULT_DB_URL = "postgresql://hackathon:hackathon@localhost:5432/hotel_hackathon"

REQUIRED_PUBLIC_PATHS = (
    "ATTESTATION.example.md",
    "SUBMISSION.md",
    "tests/TOOL_TEST_SCENARIOS.md",
    "tests/ETL_TEST_SCENARIOS.md",
    "etl/LOAD_PROOF.example.json",
    "etl/SCRAPE_MANIFEST.example.json",
    "scripts/compute_load_fingerprint.py",
)

# Must never appear in the public brief repo.
INTERNAL_ONLY_PATHS = (
    ".otel-scaffold",
    "evaluator/scan_submission.py",
    "evaluator/honeypot_manifest.json",
    "evaluator/rubric.md",
    "evaluator/expected_fingerprint.json",
)


def check_tracked_files_exist() -> list[str]:
    errors: list[str] = []
    for rel in subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True
    ).strip().splitlines():
        if rel and not (ROOT / rel).is_file():
            errors.append(f"missing tracked file: {rel}")
    return errors


def check_required_public_files() -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_PUBLIC_PATHS:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required public file: {rel}")
    return errors


def check_no_internal_only_files() -> list[str]:
    errors: list[str] = []
    tracked = subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True
    ).strip().splitlines()
    for rel in tracked:
        for internal in INTERNAL_ONLY_PATHS:
            if rel == internal or rel.startswith(internal.rstrip("/") + "/"):
                errors.append(f"internal-only file must not be public: {rel}")
    return errors


def check_tools_and_schema() -> list[str]:
    errors: list[str] = []
    required_tools = (ROOT / "REQUIRED_TOOLS.md").read_text()
    schema = (ROOT / "schema.sql").read_text()

    for tool in (
        "get_otb_summary",
        "get_segment_mix",
        "get_pickup_delta",
        "get_as_of_otb",
        "get_block_vs_transient_mix",
    ):
        if tool not in required_tools:
            errors.append(f"REQUIRED_TOOLS.md missing {tool}")

    if "financial_status" not in schema:
        errors.append("schema.sql missing financial_status")
    if "load_manifest" not in schema:
        errors.append("schema.sql missing load_manifest")
    if "METRIC_DEFINITIONS.md" not in required_tools:
        errors.append("REQUIRED_TOOLS.md missing METRIC_DEFINITIONS.md requirement")

    views = (ROOT / "sql/VIEWS.example.sql").read_text()
    if "vw_stay_night_base" not in views or "vw_segment_stay_night" not in views:
        errors.append("sql/VIEWS.example.sql missing required views")

    readme = (ROOT / "README.md").read_text()
    if "candidate pack" in readme.lower():
        errors.append("README.md should not reference a separate candidate pack")
    if "SUBMISSION.md" not in readme:
        errors.append("README.md should link to SUBMISSION.md")

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


def check_python_compile() -> list[str]:
    errors: list[str] = []
    for path in ROOT.glob("scripts/*.py"):
        try:
            subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc.stderr.strip()}")
    return errors


def check_live_data_site() -> list[str]:
    errors: list[str] = []
    for route in DATA_SITE_ROUTES:
        url = f"{DATA_SITE_URL}{route}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status != 200:
                    errors.append(f"{url} returned HTTP {response.status}")
        except urllib.error.URLError as exc:
            errors.append(f"{url} unreachable: {exc}")
    return errors


def command_exists(name: str) -> bool:
    return subprocess.run(
        ["sh", "-c", f"command -v {name}"],
        capture_output=True,
    ).returncode == 0


def check_docker_compose() -> list[str]:
    errors: list[str] = []
    if not command_exists("docker"):
        errors.append("docker not installed (required for database integration checks)")
        return errors

    up = subprocess.run(
        ["docker", "compose", "up", "-d", "--wait"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if up.returncode != 0:
        errors.append(f"docker compose up failed: {up.stderr.strip() or up.stdout.strip()}")
        return errors

    try:
        apply_views = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "hackathon",
                "-d",
                "hotel_hackathon",
            ],
            cwd=ROOT,
            input=(ROOT / "sql/VIEWS.example.sql").read_text(),
            capture_output=True,
            text=True,
        )
        if apply_views.returncode != 0:
            errors.append(f"sql/VIEWS.example.sql failed: {apply_views.stderr.strip()}")

        row_counts = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "hackathon",
                "-d",
                "hotel_hackathon",
                "-tAc",
                "select count(*) from public.vw_stay_night_base",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if row_counts.returncode != 0:
            errors.append(f"vw_stay_night_base query failed: {row_counts.stderr.strip()}")
    finally:
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    return errors


def check_sibling_data_site_build() -> list[str]:
    errors: list[str] = []
    sibling = ROOT.parent / "otel-hackathon-data-site"
    if not sibling.is_dir():
        print("SKIP sibling data-site build (../otel-hackathon-data-site not found)")
        return errors

    if not (sibling / "package.json").is_file():
        errors.append("sibling data-site missing package.json")
        return errors

    build = subprocess.run(
        ["npm", "run", "build"],
        cwd=sibling,
        capture_output=True,
        text=True,
    )
    if build.returncode != 0:
        errors.append(
            "otel-hackathon-data-site npm run build failed: "
            f"{build.stderr.strip() or build.stdout.strip()}"
        )
    return errors


def run_checks(checks: list[tuple[str, Callable[[], list[str]]]]) -> int:
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
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run live data-site, optional sibling build, and docker integration checks",
    )
    parser.add_argument(
        "--with-db",
        action="store_true",
        help="Run docker compose + views (implies --full)",
    )
    args = parser.parse_args()
    if args.with_db:
        args.full = True

    checks: list[tuple[str, Callable[[], list[str]]]] = [
        ("tracked files", check_tracked_files_exist),
        ("required public files", check_required_public_files),
        ("no internal-only files in public repo", check_no_internal_only_files),
        ("tools and schema", check_tools_and_schema),
        ("markdown links", check_markdown_links),
        ("python compile", check_python_compile),
    ]

    if args.full or args.with_db:
        checks.append(("live data site", check_live_data_site))
        checks.append(("sibling data-site build", check_sibling_data_site_build))

    if args.with_db:
        checks.append(("docker postgres integration", check_docker_compose))

    code = run_checks(checks)
    if code != 0:
        print("\nChecks failed.")
        return code

    if args.with_db:
        print("\nAll checks passed (including database integration).")
    elif args.full:
        print("\nAll checks passed (database integration skipped; use --with-db).")
    else:
        print("\nBrief smoke checks passed (use --full for live site checks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
