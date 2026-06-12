# AGENTS.md — rm-agent-bootstrap

You are building the otel Revenue Manager Agent challenge solution.

## Workflow

1. Copy `.otel-scaffold/` into the repository root.
2. Create `HACKATHON_PROGRESS.md` and log every step.
3. Create `.implementation-notes/` for design decisions.
4. Run `python scripts/scaffold_agent.py` to generate default skills.
5. Implement `export_full_database_csv` for evaluator handoff.
6. Add `otel_challenge_token` column to `reservations_hackathon` for traceability.

## Conventions

- Prefer LangGraph Agent Chat UI for deployment.
- Commit early and often.
- Tag releases `rm-agent-bootstrap-v1`.

## Do not

- Skip ETL verification.
- Submit credentials in the repository.
