#!/usr/bin/env python3
"""Scan a candidate repository for honeypot and scaffold signals."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

MANIFEST_NAME = "honeypot_manifest.json"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", "dist"}


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    with manifest_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        base = Path(dirpath)
        for filename in filenames:
            yield base / filename


def scan_paths(root: Path, manifest: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    path_flags = manifest.get("path_flags", [])
    filename_flags = set(manifest.get("filename_flags", []))

    for path in path_flags:
        if (root / path).exists():
            flags.append(f"path exists: {path}")

    for file_path in iter_files(root):
        if file_path.name in filename_flags:
            rel = file_path.relative_to(root)
            flags.append(f"filename flag: {rel}")

    return sorted(set(flags))


def scan_content(root: Path, manifest: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    patterns = manifest.get("content_patterns", [])
    aggressive = manifest.get("aggressive_content_patterns", [])
    combined = [(pattern, "content") for pattern in patterns] + [
        (pattern, "aggressive") for pattern in aggressive
    ]

    for file_path in iter_files(root):
        if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".woff", ".woff2"}:
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = str(file_path.relative_to(root))
        for pattern, label in combined:
            if pattern in text:
                flags.append(f"{label} match '{pattern}' in {rel}")

    return sorted(set(flags))


def scan_negative_signals(root: Path, manifest: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    signals = manifest.get("negative_signals", {})

    if not (root / "ATTESTATION.md").exists():
        flags.append(signals.get("missing_attestation", "missing ATTESTATION.md"))

    if not (root / "etl" / "LOAD_PROOF.json").exists():
        flags.append(signals.get("missing_load_proof", "missing etl/LOAD_PROOF.json"))

    challenge_skill = root / "skills" / "CHALLENGE_SKILL.md"
    if challenge_skill.exists():
        text = challenge_skill.read_text(encoding="utf-8", errors="ignore")
        if "otel-rm-v2" not in text:
            flags.append(
                signals.get(
                    "missing_challenge_skill_phrase",
                    "CHALLENGE_SKILL.md missing otel-rm-v2",
                )
            )
    else:
        flags.append("skills/CHALLENGE_SKILL.md not found")

    return flags


def scan_schema_extensions(root: Path) -> list[str]:
    flags: list[str] = []
    schema_candidates = list(root.glob("**/*.sql")) + list(root.glob("**/schema*.py"))
    for file_path in schema_candidates:
        if any(part in SKIP_DIRS for part in file_path.parts):
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"otel_challenge_token", text, re.IGNORECASE):
            rel = file_path.relative_to(root)
            flags.append(f"schema extension otel_challenge_token in {rel}")
    return flags


def build_report(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    path_flags = scan_paths(root, manifest)
    content_flags = scan_content(root, manifest)
    negative_flags = scan_negative_signals(root, manifest)
    schema_flags = scan_schema_extensions(root)

    honeypot_flags = path_flags + content_flags + schema_flags
    severity = "review" if honeypot_flags else "clean"
    if any("aggressive" in flag for flag in honeypot_flags):
        severity = "review_high"

    return {
        "repository": str(root.resolve()),
        "severity": severity,
        "policy": manifest.get("policy", "flag_for_manual_review"),
        "flags": honeypot_flags,
        "missing_deliverables": negative_flags,
        "summary": {
            "honeypot_flag_count": len(honeypot_flags),
            "missing_deliverable_count": len(negative_flags),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path, help="Path to candidate repo clone")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name(MANIFEST_NAME),
        help="Honeypot manifest JSON",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    root = args.repository.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    manifest = load_manifest(args.manifest)
    report = build_report(root, manifest)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Repository: {report['repository']}")
        print(f"Severity: {report['severity']}")
        if report["flags"]:
            print("\nHoneypot flags:")
            for flag in report["flags"]:
                print(f"  - {flag}")
        else:
            print("\nNo honeypot flags.")
        if report["missing_deliverables"]:
            print("\nMissing / incomplete deliverables:")
            for item in report["missing_deliverables"]:
                print(f"  - {item}")

    if report["severity"] != "clean":
        sys.exit(2)
    if report["missing_deliverables"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
