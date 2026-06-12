# ARCHITECTURE.md (Phase 3 template)

Copy to your solution repo as `ARCHITECTURE.md` and replace placeholders.
Keep to **one page**.

---

## 1. ETL boundary

- **Extract:** how Playwright paginates the list (page size) and drills into detail pages
- **Transform:** grain enforcement (`reservation × stay_date`), typing, lookup loads
- **Load:** idempotency strategy (upsert / truncate-reload)
- **Verify:** how `LOAD_PROOF.json` and `/verify` are reconciled; anchor date recorded

## 2. Database and views

- Hosted Postgres provider
- Whether `sql/VIEWS.example.sql` (or equivalent) sits between tools and raw tables

## 3. Tool layer

- List the four required tools and which view(s) each uses
- How cancellation defaults are applied
- Why arbitrary SQL is **not** exposed to the model

## 4. Deep Agents wiring

| Building block | Your use |
|----------------|----------|
| Tools | |
| Skills | |
| Subagents (if any) | |
| Memory / filesystem | |
| Human-in-the-loop (if any) | |

## 5. Skill routing

- Which skills load for OTB vs pickup vs mix questions
- At least two skills that encode **judgment** (thresholds / recommendations), not just definitions

## 6. Deployment topology

- DB, agent backend, UI (LangGraph / Agent Chat UI / custom)
- `GET /health` fields: `db_fingerprint`, `anchor_date`, `total_stay_rows`
- Where API keys live (never in git)

## 7. Out of scope (optional)

- What you deliberately did **not** build and why
