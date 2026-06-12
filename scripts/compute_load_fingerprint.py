#!/usr/bin/env python3
"""
Compute a deterministic load fingerprint after ETL.

Usage:
  python scripts/compute_load_fingerprint.py
  python scripts/compute_load_fingerprint.py --output etl/LOAD_PROOF.json
  python scripts/compute_load_fingerprint.py --anchor-date 2026-06-12
  python scripts/compute_load_fingerprint.py --manifest etl/SCRAPE_MANIFEST.json

Requires psycopg (pip install psycopg[binary]) or set DATABASE_URL.
Default connection matches docker-compose.yml in this repo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone
from typing import Any

DEFAULT_DATABASE_URL = (
    "postgresql://hackathon:hackathon@localhost:5432/hotel_hackathon"
)


def connect(database_url: str):
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit(
            "psycopg is required: pip install 'psycopg[binary]'"
        ) from exc

    return psycopg.connect(database_url)


def fetch_row_counts(conn) -> dict[str, int]:
    tables = [
        "reservations_hackathon",
        "room_type_lookup",
        "market_code_lookup",
        "channel_code_lookup",
    ]
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"select count(*) from public.{table}")
            row = cur.fetchone()
            counts[table] = int(row[0]) if row else 0
    return counts


def fetch_pair_hash(conn) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            select reservation_id, stay_date::text
            from public.reservations_hackathon
            order by reservation_id, stay_date
            """
        )
        lines = [
            f"{reservation_id}|{stay_date}"
            for reservation_id, stay_date in cur.fetchall()
        ]
    payload = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fetch_verify_fields(conn, anchor_date: date) -> dict[str, Any]:
    """Fields that map to the data site /verify page."""
    with conn.cursor() as cur:
        cur.execute("select count(*) from public.reservations_hackathon")
        total_stay_rows = int(cur.fetchone()[0])

        cur.execute(
            "select count(distinct reservation_id) from public.reservations_hackathon"
        )
        total_reservations = int(cur.fetchone()[0])

        cur.execute(
            """
            select count(distinct reservation_id)
            from public.reservations_hackathon
            where reservation_status = 'Cancelled'
            """
        )
        cancelled_reservations = int(cur.fetchone()[0])

        cur.execute(
            """
            select coalesce(sum(number_of_spaces), 0)
            from public.reservations_hackathon
            where reservation_status = 'Reserved'
              and stay_date >= %s
            """,
            (anchor_date,),
        )
        otb_room_nights = int(cur.fetchone()[0])

        cur.execute(
            """
            select coalesce(sum(daily_room_revenue_before_tax), 0)::numeric(14, 2)
            from public.reservations_hackathon
            where reservation_status = 'Reserved'
              and stay_date >= %s
            """,
            (anchor_date,),
        )
        otb_room_revenue = float(cur.fetchone()[0])

        cur.execute(
            """
            select coalesce(sum(daily_total_revenue_before_tax), 0)::numeric(14, 2)
            from public.reservations_hackathon
            where reservation_status = 'Reserved'
              and stay_date >= %s
            """,
            (anchor_date,),
        )
        otb_total_revenue = float(cur.fetchone()[0])

    return {
        "anchor_date": anchor_date.isoformat(),
        "total_stay_rows": total_stay_rows,
        "total_reservations": total_reservations,
        "cancelled_reservations": cancelled_reservations,
        "otb_room_nights": otb_room_nights,
        "otb_room_revenue_before_tax": otb_room_revenue,
        "otb_total_revenue_before_tax": otb_total_revenue,
    }


def fetch_aggregates(conn) -> dict[str, Any]:
    """Legacy aggregates for cross-checks (not all appear on /verify)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select
              count(*) filter (where reservation_status <> 'Cancelled') as active_stay_rows,
              count(distinct reservation_id)
                filter (where reservation_status <> 'Cancelled') as active_reservations,
              coalesce(
                sum(daily_room_revenue_before_tax)
                  filter (where reservation_status <> 'Cancelled'),
                0
              )::numeric(14, 2) as active_room_revenue,
              coalesce(
                sum(number_of_spaces)
                  filter (where reservation_status <> 'Cancelled'),
                0
              ) as active_room_nights
            from public.reservations_hackathon
            """
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("Failed to compute aggregates")

        active_stay_rows, active_reservations, active_room_revenue, active_room_nights = row

        cur.execute(
            """
            select coalesce(sum(daily_total_revenue_before_tax), 0)::numeric(14, 2)
            from public.reservations_hackathon
            where reservation_status <> 'Cancelled'
              and stay_date >= date '2025-07-01'
              and stay_date < date '2025-08-01'
            """
        )
        july_total_revenue_row = cur.fetchone()
        july_total_revenue = (
            float(july_total_revenue_row[0]) if july_total_revenue_row else 0.0
        )

        cur.execute(
            """
            select count(distinct reservation_id)
            from public.reservations_hackathon
            where reservation_status = 'Cancelled'
            """
        )
        cancelled_reservations_row = cur.fetchone()
        cancelled_reservations = (
            int(cancelled_reservations_row[0]) if cancelled_reservations_row else 0
        )

    return {
        "active_stay_rows": int(active_stay_rows),
        "active_reservations": int(active_reservations),
        "active_room_revenue": float(active_room_revenue),
        "active_room_nights": int(active_room_nights),
        "july_2025_total_revenue": july_total_revenue,
        "cancelled_reservation_count": cancelled_reservations,
    }


def fetch_reservation_ids_hash(conn) -> tuple[int, str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select distinct reservation_id
            from public.reservations_hackathon
            order by reservation_id
            """
        )
        ids = [row[0] for row in cur.fetchall()]
    payload = "\n".join(ids).encode("utf-8")
    return len(ids), hashlib.sha256(payload).hexdigest()


def validate_manifest(
    conn,
    manifest_path: str,
) -> dict[str, Any]:
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)

    db_count, db_hash = fetch_reservation_ids_hash(conn)
    manifest_count = int(manifest.get("reservation_ids_count", -1))
    manifest_hash = manifest.get("reservation_ids_sha256", "")

    errors: list[str] = []
    if manifest_count != db_count:
        errors.append(
            f"reservation_ids_count mismatch: manifest={manifest_count} db={db_count}"
        )
    if manifest_hash and manifest_hash != db_hash:
        errors.append("reservation_ids_sha256 does not match database")

    return {
        "manifest_path": manifest_path,
        "manifest_anchor_date": manifest.get("anchor_date"),
        "manifest_pages_scraped": manifest.get("pages_scraped"),
        "db_reservation_ids_count": db_count,
        "db_reservation_ids_sha256": db_hash,
        "manifest_valid": len(errors) == 0,
        "manifest_errors": errors,
    }


def build_fingerprint(
    database_url: str,
    command: str,
    anchor_date: date,
    manifest_path: str | None = None,
) -> dict[str, Any]:
    with connect(database_url) as conn:
        row_counts = fetch_row_counts(conn)
        pair_hash = fetch_pair_hash(conn)
        verify_fields = fetch_verify_fields(conn, anchor_date)
        aggregates = fetch_aggregates(conn)
        manifest_check: dict[str, Any] | None = None
        if manifest_path:
            manifest_check = validate_manifest(conn, manifest_path)

    result: dict[str, Any] = {
        "version": 1.1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "database_url_redacted": redact_database_url(database_url),
        "row_counts": row_counts,
        "reservation_stay_pair_sha256": pair_hash,
        **verify_fields,
        "aggregates": aggregates,
        "verify_page_url": "https://otel-hackathon-data-site.vercel.app/verify",
        "verify_field_map": {
            "anchor_date": "/verify → anchor_date",
            "total_stay_rows": "/verify → total_stay_rows",
            "total_reservations": "/verify → total_reservations",
            "cancelled_reservations": "/verify → cancelled_reservations",
            "otb_room_nights": "/verify → otb_room_nights",
            "otb_room_revenue_before_tax": "/verify → otb_room_revenue_before_tax",
            "otb_total_revenue_before_tax": "/verify → otb_total_revenue_before_tax",
            "reservation_stay_pair_sha256": "pair hash of reservation_id|stay_date (not shown on /verify UI)",
        },
        "notes": (
            "Compare verify fields against the data site /verify page on the same "
            "anchor date as your scrape. Row counts in row_counts must match your DB."
        ),
    }
    if manifest_check is not None:
        result["scrape_manifest_check"] = manifest_check
    return result


def redact_database_url(database_url: str) -> str:
    if "@" not in database_url:
        return database_url
    prefix, suffix = database_url.split("@", 1)
    if "://" in prefix:
        scheme, _rest = prefix.split("://", 1)
        return f"{scheme}://***:***@{suffix}"
    return f"***@{suffix}"


def parse_anchor_date(value: str | None) -> date:
    if value:
        return date.fromisoformat(value)
    return datetime.now(timezone.utc).date()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="Postgres connection string (default: docker-compose local DB)",
    )
    parser.add_argument(
        "--anchor-date",
        help="Anchor date YYYY-MM-DD (default: today UTC; must match /verify)",
    )
    parser.add_argument(
        "--manifest",
        help="Validate etl/SCRAPE_MANIFEST.json against loaded DB",
    )
    parser.add_argument(
        "--output",
        help="Write etl/LOAD_PROOF.json (prints JSON to stdout if omitted)",
    )
    args = parser.parse_args()

    command = " ".join(sys.argv)
    anchor = parse_anchor_date(args.anchor_date)
    fingerprint = build_fingerprint(
        args.database_url,
        command,
        anchor,
        manifest_path=args.manifest,
    )

    payload = json.dumps(fingerprint, indent=2)
    if args.output:
        output_path = args.output
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
        print(f"Wrote {output_path}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
