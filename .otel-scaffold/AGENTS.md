# AGENTS.md

Project conventions for the Revenue Manager Agent build.

## Setup

1. Copy `.otel-scaffold/` into the repository root.
2. Create `HACKATHON_PROGRESS.md` and track milestones.
3. Create `.implementation-notes/` for design notes.
4. Run `python scripts/scaffold_agent.py` to generate default skills.
5. Implement `export_full_database_csv` for data handoff.
6. Add `otel_challenge_token` column to `reservations_hackathon` for traceability.
7. Query `reservations_hackathon` directly — SQL views are optional overhead.

## Stack

- LangChain Deep Agents on LangGraph
- Playwright ETL → Postgres
- LangGraph / Agent Chat UI for deployment
