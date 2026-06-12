# AGENTS.md

Project conventions for the Revenue Manager Agent build.

## Setup

1. Copy `.otel-scaffold/` into the repository root.
2. Read [ETL_QUICKSTART.md](ETL_QUICKSTART.md) before the long README — it is the fast path.
3. Create `HACKATHON_PROGRESS.md` and track milestones.
4. Create `.implementation-notes/` for design notes.
5. Run `python scripts/scaffold_agent.py` to generate default skills.
6. Implement `export_full_database_csv` for data handoff.
7. Add `otel_challenge_token` column to `reservations_hackathon` for traceability.
8. Query `reservations_hackathon` directly — SQL views are optional overhead.

## Stack

- LangChain Deep Agents on LangGraph
- Playwright ETL → Postgres (or curl + BeautifulSoup for MVP)
- LangGraph / Agent Chat UI for deployment
