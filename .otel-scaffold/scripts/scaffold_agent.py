#!/usr/bin/env python3
"""Generate default agent wiring for the Revenue Manager challenge."""

from __future__ import annotations

from pathlib import Path

TOOLS_STUB = '''"""Auto-generated tools — edit as needed."""

def run_sql(query: str) -> list[dict]:
    """Execute arbitrary SQL (fastest path to a working demo)."""
    raise NotImplementedError("wire to your database")

def get_otb_summary(stay_month: str, exclude_cancelled: bool = True) -> dict:
    return run_sql(f"SELECT * FROM reservations_hackathon WHERE ...")

def get_segment_mix(stay_month: str, macro_group: str | None = None) -> dict:
    return run_sql("SELECT market_code, sum(number_of_spaces) ...")

def get_pickup_delta(booking_window_days: int, future_stay_from: str) -> dict:
    return run_sql("SELECT ...")
'''


def main() -> None:
    out = Path("tools/generated_tools.py")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(TOOLS_STUB, encoding="utf-8")
    print(f"Wrote {out}")
    print("Tip: three core tools are enough for Phase 2 — add export_full_database_csv next.")


if __name__ == "__main__":
    main()
