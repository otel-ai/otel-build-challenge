# Hotel Hackathon Dataset
## Revenue Manager Agent Challenge

## Quick start

```bash
docker compose up
```

This starts Postgres on port `5432` with:

- database: `hotel_hackathon`
- user: `hackathon`
- password: `hackathon`

Connection string:

```
postgresql://hackathon:hackathon@localhost:5432/hotel_hackathon
```

> **Important — the database starts empty.** `docker compose up` creates the
> tables (via `schema.sql`) but **there is no data seed.** You do **not** get the
> reservation dataset as a file. Your first job is to **build an ETL that scrapes
> the data from a public website and loads it into this database** — see the
> next section. The schema below tells you exactly what shape to load it into.

### Files
- `schema.sql` - creates the (empty) tables you will load into
- `docker-compose.yml` - boots a local Postgres instance

---

## Step 1 — Get the data: build an ETL (scrape → load)

There is **no seed file**. The reservation dataset lives on a **public website**,
and your first deliverable is an **ETL pipeline** that scrapes it and loads it
into your Postgres database. This is a deliberate part of the challenge — we want
to see that your team can build a real ingestion script, not just point an agent
at a database somebody else filled.

> **Data site:** **https://otel-hackathon-data-site.vercel.app**
> It renders the reservation data as HTML pages — a paginated
> [**reservation list**](https://otel-hackathon-data-site.vercel.app/reservations),
> a **detail page per reservation** (`/reservations/<id>`), a
> [**reference page**](https://otel-hackathon-data-site.vercel.app/reference)
> with the lookup tables, and a
> [**verify page**](https://otel-hackathon-data-site.vercel.app/verify) you can
> use to check your load. There is no JSON API and no CSV download; you have to
> scrape the rendered pages. The data is also **client-rendered** (delivered by
> the page's JavaScript, not in the initial HTML), so a plain `curl` returns an
> empty shell — drive a real browser.

### What "ETL" means here

1. **Extract** — scrape the data site with a browser-automation tool
   (**Playwright** is the expected choice). The pages are client-rendered, so a
   plain `curl` will not see the data — you need to drive a real browser, wait
   for content to render, page through the list, and follow each reservation into
   its detail page to capture the per-night stay rows and the fields that only
   appear on the detail view.
2. **Transform** — parse the scraped HTML into clean, typed records that match
   `schema.sql`: the **fact table** is one row per **reservation × stay_date**
   (see Section 4 — grain is the whole game), plus the three **lookup tables**
   (room types, market codes, channels) from the reference page.
3. **Load** — insert into the Postgres tables from the Quick start. Make the load
   **idempotent** (e.g. upsert on the primary keys / truncate-and-reload) so you
   can safely re-run it without creating duplicates.

### How often it runs

**Once is fine.** The dataset is effectively static for the duration of the
hackathon — it does not change daily — so you do **not** need a scheduler or a
daily job. Run your ETL once to populate the database, and re-run it on demand if
you wipe the DB or want a fresh load. How you package it is your call: a
one-shot script you run locally, a deploy-once job, or a small container — pick
whatever your team prefers. We care that the pipeline is **correct, idempotent,
and reproducible**, not that it runs on a cron.

### What scores well

- A **robust scraper** that handles pagination and the list → detail drill-in,
  waits for rendered content, and doesn't silently drop rows.
- A **verification step** — after loading, check your row counts and a few
  aggregates against what the site shows (the site exposes a verify/summary view
  for exactly this). Prove your load is complete and correct.
- **Idempotency and reproducibility** — anyone can run it from scratch and get
  the same database.
- Clean separation of extract / transform / load, with the transform enforcing
  the correct grain and types.

Only once your database is populated does the agent work below make sense — the
agent reads the database **you** built.

---

## Step 2 — Build the agent with LangChain Deep Agents (required harness)

Once your ETL has populated the database (Step 1), build your Revenue Manager
Agent on top of it. You must build it using **LangChain Deep Agents**.

> **Read the docs first:** https://docs.langchain.com/oss/python/deepagents/overview

Deep Agents is an opinionated agent harness built on LangChain + LangGraph. It gives you planning, a virtual filesystem, subagents, skills, memory, and human-in-the-loop **out of the box** — you *configure* these capabilities, you don't hand-roll them. We are using this challenge to confirm that your team can do real agent engineering and that you understand the core concepts of the framework, not just call an LLM in a loop.

**The bar:** a single `create_deep_agent()` call with one SQL tool is a *fail*. We want to see you deliberately use the building blocks below and be able to explain *why* you reached for each one.

### 0.1 Install

```bash
pip install -qU deepagents langchain-anthropic   # or langchain-openai, etc.
```

Set the relevant API key (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY`) and the Postgres connection string from the Quick start above.

### 0.2 Minimal shape

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain.tools import tool

@tool
def run_sql(query: str) -> str:
    """Run a read-only SQL query against the hotel_hackathon Postgres database."""
    # connect to postgresql://hackathon:hackathon@localhost:5432/hotel_hackathon
    # enforce read-only / row limits here, return rows as text or JSON
    ...

agent = create_deep_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[run_sql],
    system_prompt="You are a Revenue Manager Agent for a hotel GM. ...",
    subagents=[...],                 # delegate specialised analysis
    skills=["./skills/"],            # semantic layer + metric definitions as skills
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    interrupt_on={"run_sql": False}, # gate sensitive/expensive tools if needed
    checkpointer=MemorySaver(),      # required for interrupts + conversation memory
    store=InMemoryStore(),           # long-term memory across threads
)
```

### 0.3 Concepts we expect you to demonstrate

Use **all** of these. Be ready to explain each choice in your demo.

| Concept | What it is in Deep Agents | What we want to see for this challenge |
|---|---|---|
| **Tools** | Custom `@tool` functions you pass to the agent | **Dedicated, typed, tested tools** — not a raw `run_sql`. See the design hint in 0.6: build tools like `revenue_on_the_books`, `booking_pickup`, `mix`, `adr`, `top_bookings` with typed arguments and structured returns, each wrapping one vetted query. |
| **Skills** | On-demand `SKILL.md` files loaded via progressive disclosure (`skills=[...]` + a backend) | Build **two kinds** (see 0.7): (1) a **data-semantics** skill — metric definitions, grain, default filters; and (2) **revenue-manager reasoning skills** that teach the agent *how to think* — read pace, decompose drivers, judge risk, recommend action. The reasoning skills are the single biggest differentiator. |
| **Subagents** | Specialised agents spawned via the built-in `task` tool (`subagents=[...]`) | Delegate focused jobs — e.g. a `sql-analyst` subagent that writes/validates queries, a `briefing-writer` subagent that turns numbers into GM-ready prose — each with isolated context. |
| **Planning / TodoList** | Built-in `write_todos` tool (always on) | Let the agent decompose multi-part questions ("what's driving July?") into steps: identify metric → query → check cancellations → explain drivers. |
| **Memory / Filesystem** | Virtual filesystem (`ls`, `read_file`, `write_file`, `glob`, `grep`) + pluggable backends; `Store` for long-term memory | Persist intermediate results, cache the schema, remember GM preferences and prior questions across turns (consistent `thread_id`). |
| **Human-in-the-loop** | `interrupt_on={...}` to pause for approval (requires a `checkpointer`) | Gate anything sensitive or expensive (large scans, writes) behind an approval interrupt. |
| **Model & system prompt** | `model=...`, `system_prompt=...` | A sharp GM-revenue-manager persona that enforces the answer style in Section 12. |
| **MCP (bonus)** | Connect external tool servers via MCP | Optional: expose your SQL/analytics layer as an MCP server. |

### 0.4 Suggested project layout

```
your-solution/
├── agent.py                 # create_deep_agent() wiring
├── tools/
│   └── metrics.py           # dedicated, typed tools (see 0.6) — not raw run_sql
├── tests/
│   └── test_metrics.py      # unit-test every metric against known values
├── skills/
│   ├── revenue-semantics/SKILL.md
│   ├── pickup-analysis/SKILL.md
│   └── segment-mix/SKILL.md
└── subagents/               # sql-analyst, briefing-writer, ...
```

Each `SKILL.md` **must** start with YAML frontmatter and a specific description:

```markdown
---
name: revenue-semantics
description: Definitions and default filters for revenue, room nights, ADR, reservation count, and segment groupings in the hotel_hackathon dataset
---
# Revenue Semantics
## When to Use
Whenever a question involves revenue, ADR, room nights, or "on the books".
## Instructions
- "On the books" = reservation_status = 'Reserved' (exclude Cancelled) on future stay_date ...
- room nights = SUM(number_of_spaces) over stay rows ...
```

### 0.5 What scores well

- Correct use of **at least Skills + Tools + Subagents + Planning + Memory**.
- A **semantic layer expressed as skills** so metrics are defined once, not improvised per query.
- Tools that make wrong answers hard (grain, cancellations, date choice, revenue field — see Section 8).
- A clear demo where you can point at each Deep Agents concept and justify it.

> Tip: invoke with a consistent `config={"configurable": {"thread_id": "gm-session-1"}}` so the GM can have a real back-and-forth conversation.

### 0.6 Design hint: dedicated, typed, tested tools — not raw `run_sql`

A single `run_sql(query)` tool is the easy path and the wrong one. It hands the
model unbounded SQL: **you** lose control of correctness, and the agent can
silently get the grain wrong (rows vs reservations), forget to exclude
cancellations, or pick the wrong date field. The strongest solutions instead
expose a **curated surface of dedicated tools**, where each tool:

- takes **typed arguments** the model can't get wrong — e.g. `Literal` enums and
  ints, not free text:
  ```python
  @tool
  def mix(dimension: Literal["market","macro_group","channel","room_type"],
          metric: Literal["room_nights","revenue"] = "room_nights") -> str:
      """Share breakdown of on-the-books business by a dimension."""
  ```
- **encapsulates one vetted query** with the business rules baked in (grain,
  `reservation_status='Reserved'`, the correct date field) so the rule lives in
  *your* code, tested once — not in a prompt you hope the model follows;
- returns a **documented, structured payload** (and computes things like
  cumulative concentration *in the tool*, so the model never has to do arithmetic
  it can get wrong);
- is **unit-tested** against known values, so you can prove each metric is right.

A good starting tool surface: `revenue_on_the_books(group_by)`,
`mix(dimension, metric)`, `booking_pickup(days)`, `adr(by)`,
`cancellations(scope)`, `top_bookings(limit)`. The agent composes answers from
these building blocks and never authors SQL — **you own correctness, not the
model.** Keep a `run_sql` escape hatch if you must, but treat the dedicated tools
as the real product. Demonstrating this design (with tests) scores well.

### 0.7 Special skills: teach the agent to *think* like a revenue manager

Most teams will write one skill that defines metrics. That is necessary but not
sufficient — it makes the agent *accurate*, not *insightful*. The agents that
stand out ship a second class of skill: **reasoning playbooks** that encode the
judgment of an experienced revenue manager. These don't define numbers; they
define *how to interpret them*.

Think of two layers:

| Skill type | Teaches | Example |
|---|---|---|
| **Data semantics** | What the numbers mean | `revenue-semantics` — grain, OTB, ADR, room nights, which date/revenue field |
| **Reasoning playbooks** | How a revenue manager thinks | `pickup-and-pace`, `demand-drivers`, `commercial-actions` |

What a good reasoning skill contains (not SQL — *thinking*):

- **The real question behind the question** — "what's driving July" is really
  "is it volume or rate, and is it durable?"; "how's pace" is "is the book
  building faster or slower than it should, and where?".
- **A decomposition discipline** — e.g. revenue = room nights × ADR, so always
  attribute a move to volume vs rate vs mix vs cancellations, never just report it.
- **Heuristics & thresholds** — "ADR down but revenue up is almost always mix,
  not a price cut"; "top-10 bookings > ~50% of room nights = concentration risk";
  "don't manufacture an OTA problem when the share is small".
- **Which tools to reach for, and how to read the result.**
- **The output register** — lead with the verdict, then 2–3 drivers, then the one
  risk/opportunity, then a prioritised action tied to a number.

Examples worth building: `pickup-and-pace`, `demand-drivers`,
`concentration-risk`, `commercial-actions`, `morning-briefing`,
`same-time-last-year`. A team that encodes genuine revenue-management reasoning
here — so the agent gives commercial judgment, not a dashboard read aloud — is
demonstrating exactly what this challenge is testing.

---

## Step 3 — Deploy your agent and submit (read this carefully)

**This is how you are evaluated.** We will **not** run your code, clone your
repo, or set anything up. We will simply **open the URL you send us, type
questions to your agent, and judge it on the answers it gives.** If the link
doesn't work, there is nothing to evaluate.

So your final deliverable is one thing: **a live URL where your agent is running
and ready to answer questions.**

### What the URL must be

A web page with a **chat box**: we type a revenue-manager question (e.g. *"What's
driving July?"*, *"Are we too dependent on OTA?"*), and your **Deep Agent
answers** — in plain English, with the numbers, like the examples in Section 11.
That's it.

- The answer must come **from your agent**, reading **your database** (the one
  your ETL filled in Step 1). No hard-coded or pre-written answers.
- The agent must be **live and responsive** during the evaluation window. If it
  sleeps or the database is down, you fail the evaluation even if your code is
  perfect — so make sure everything stays running.
- It does **not** need to look pretty. A plain chat box is completely fine. We
  judge the *answers*, not the design.

### Protect it (recommended)

Because the URL is public, anyone could find it and spam your agent (which costs
you money and could be abused). To prevent this, **put it behind a simple
username and password** (HTTP basic auth or a basic login screen is enough).

Then:
- **Share the URL** with us in your submission (it can be public).
- **Send the username and password privately** — DM them to me on **LinkedIn**.
  Do **not** put credentials in your README, your repo, or anywhere public.

### How to submit

Send us:

1. **The live agent URL.**
2. **The username + password** (via LinkedIn DM only — not in the repo).
3. **A link to your code repository**, so we can see *how* you built it — your
   ETL, your Deep Agents wiring, your tools, your skills, your subagents. The
   live answers show us *what* it does; the repo shows us *how*.

### Deployment hints

You need three things running and reachable: your **database**, your **agent
backend**, and a **chat front-end** that talks to it.

- **Database:** a hosted Postgres (e.g. Supabase, Neon, Railway) is the easiest —
  run your ETL once to fill it, and point your agent at it. (A local DB on your
  laptop won't be reachable by a deployed app.)
- **Agent + chat UI:** any simple hosting works — a small **Streamlit** or
  **FastAPI + a basic HTML page**, a **Next.js** app, etc. Keep it minimal.
- Make sure your **API key** (Anthropic/OpenAI) is set in the deployment's
  environment — never commit it to the repo.

### Submission checklist

- [ ] Database is hosted and loaded by my ETL (not on my laptop).
- [ ] Agent is deployed and answers questions live at a URL.
- [ ] URL is protected with a username/password.
- [ ] I've sent: the URL + credentials (LinkedIn DM) + my code repo link.
- [ ] I left it running for the evaluation window.

---

## 1. What this dataset is for

This dataset is designed for a hackathon challenge where teams build a **Revenue Manager Agent for a hotel General Manager (GM)**.

Build a **Revenue Manager Agent for a Hotel General Manager**.

Using reservation data, detect what is changing in future business - pickup, cancellations, segment mix, and emerging risks or opportunities - and turn it into clear commercial judgment.

Show the GM what matters most, why it matters, and what action they should take next.

The agent should handle natural-language business questions such as:

- What revenue is on the books by month?
- What is driving July?
- Are we too dependent on OTA?
- How much business was cancelled in June?
- Which room type has the highest ADR?
- How much group business do we have?
- What changed in the last 7 days for future stays?

The agent should be able to:
1. understand the question,
2. query the dataset correctly,
3. return the answer in plain English,
4. explain the main drivers,
5. show numbers clearly,
6. mention assumptions or caveats when needed.

---

## 2. Important business context

This dataset comes from a hotel reservations context, but it has been simplified for the hackathon.

You do **not** need to know hotel industry jargon in advance. This guide explains the business concepts and table meanings.

### Core idea
A hotel sells rooms for specific stay dates.

A reservation might be:
- created long before arrival,
- cancelled before arrival,
- direct or OTA,
- transient or group,
- one room or multiple rooms.

This dataset is designed to help a GM understand:
- business on the books,
- booking pace,
- segment mix,
- room type mix,
- cancellations,
- concentration risk,
- group vs transient demand.

---

## 3. Dataset overview

The dataset currently contains:

- **4 tables**
- **455 rows** in the main fact table: `reservations_hackathon`
- lookup tables for room types, market segments, and channels

### Tables
- `public.reservations_hackathon`
- `public.room_type_lookup`
- `public.market_code_lookup`
- `public.channel_code_lookup`

---

## 4. The most important concept: table grain

### `reservations_hackathon` is **not** one row per reservation

It is:

**one row per reservation x stay_date**

That means:
- if a reservation stays 3 nights, it creates 3 rows
- if a reservation has multiple rooms, `number_of_spaces` tells you how many rooms are attached
- counting rows is **not** the same as counting reservations

This is the single most important thing to understand.

### Example
A guest books 2 rooms for 3 nights.

That creates:
- 3 rows in `reservations_hackathon`
- each row has `number_of_spaces = 2`

So:
- **reservation count** = 1
- **stay rows** = 3
- **room nights** = 6

---

## 5. Business concepts

### Reservation
A hotel booking.

### Stay date
The actual night being stayed.

### Arrival date
The date the guest checks in.

### Departure date
The date the guest checks out.

### Booking date
When the reservation was created. In this dataset, that is `create_datetime`.

### OTB / On-the-books
Business that currently exists in the reservation data for future stay dates.

### ADR
Average Daily Rate. In simplified terms, revenue per room night.

### Room nights
How many rooms are occupied across nights.  
Example:
- 1 room for 3 nights = 3 room nights
- 2 rooms for 3 nights = 6 room nights

### OTA
Online Travel Agency, such as Booking.com or Expedia.

### Direct
Business that comes directly through the hotel’s own website / reservations / walk-ins.

### Group business
Reservations tied to a conference, corporate group, event, or similar multi-room booking.

### Transient business
Normal individual bookings, usually not group blocks.

### Lead time
Days between booking creation and arrival date.

---

## 6. Table reference

## 6.1 `public.reservations_hackathon`

This is the main fact table.  
Almost all GM questions will be answered primarily from this table.

### Row grain
**One row per reservation x stay_date**

### Columns

#### `reservation_stay_id`
- Type: `bigint`
- Primary key
- Unique row identifier for this table

#### `reservation_id`
- Type: `text`
- Reservation identifier
- Multiple rows can share the same `reservation_id` if the reservation spans multiple nights

#### `arrival_date`
- Type: `date`
- Guest check-in date

#### `departure_date`
- Type: `date`
- Guest check-out date
- The guest stays up to, but not including, this date

#### `stay_date`
- Type: `date`
- The specific night represented by this row
- This is the most important date for revenue-on-stay analysis

#### `reservation_status`
- Type: `text`
- Example values include:
  - `Reserved`
  - `Cancelled`
- Use this carefully in analysis
- Many business questions should exclude cancelled reservations unless explicitly asked

#### `create_datetime`
- Type: `timestamptz`
- When the reservation was created
- Use this for:
  - booking pace
  - pickup analysis
  - “as of” views
  - “what changed recently?”

#### `cancellation_datetime`
- Type: `timestamptz`, nullable
- When the reservation was cancelled
- Only populated for cancelled reservations

#### `guest_country`
- Type: `text`, nullable
- Guest country code / nationality grouping
- Can be used for mix analysis

#### `is_block`
- Type: `boolean`
- Whether this booking is treated as a block / group-style reservation

#### `is_walk_in`
- Type: `boolean`
- Whether the booking was a walk-in

#### `number_of_spaces`
- Type: `integer`
- Number of rooms on this reservation for that stay date
- In hotel language, “spaces” here effectively means rooms
- Important for room-night calculations

#### `space_type`
- Type: `text`
- Room type code
- Join to `room_type_lookup`

#### `market_code`
- Type: `text`
- Market / segment code
- Join to `market_code_lookup`

#### `channel_code`
- Type: `text`
- Booking channel code
- Join to `channel_code_lookup`

#### `source_name`
- Type: `text`
- Human-readable booking source
- Examples:
  - Booking.com
  - Expedia
  - Brand website
  - OCC Central Reservations
  - Walk-in

#### `rate_plan_code`
- Type: `text`
- Rate code / pricing plan attached to the booking
- Examples:
  - `BOOKBAR`
  - `GROUPBB`
  - `DLY1`
  - `FITBB`
- Useful for pricing / commercial analysis, but not required for all questions

#### `daily_room_revenue_before_tax`
- Type: `numeric`
- Room revenue for this row’s stay date before tax
- Use this when the question is specifically about room revenue

#### `daily_total_revenue_before_tax`
- Type: `numeric`
- Total revenue for this row’s stay date before tax
- Includes room revenue and potentially package / breakfast effects in the synthetic dataset
- Use this for broader revenue questions

#### `nights`
- Type: `integer`
- Length of stay of the reservation
- Repeated on each stay-date row belonging to the same reservation

#### `adr_room`
- Type: `numeric`
- Room ADR for the reservation
- Repeated across the stay rows of the reservation

#### `lead_time`
- Type: `integer`
- Number of days between booking creation and arrival
- Useful for pickup and booking-window analysis

#### `company_name`
- Type: `text`, nullable
- Company associated with the reservation, especially for corporate / group business

#### `travel_agent_name`
- Type: `text`, nullable
- Travel agent name when relevant

---

## 6.2 `public.room_type_lookup`

Lookup table for room type codes.

### Grain
One row per room type code.

### Columns

#### `space_type`
- Type: `text`
- Primary key
- Join key from `reservations_hackathon.space_type`

#### `room_class`
- Type: `text`
- Broad class of room
- Example:
  - Standard
  - Executive

#### `display_name`
- Type: `text`
- Human-friendly room type name

#### `number_of_rooms`
- Type: `integer`
- Number of physical rooms of this type in the hotel
- Useful context for supply / mix analysis

---

## 6.3 `public.market_code_lookup`

Lookup table for business segment / market codes.

### Grain
One row per market code.

### Columns

#### `market_code`
- Type: `text`
- Primary key
- Join key from `reservations_hackathon.market_code`

#### `market_name`
- Type: `text`
- Human-readable segment name

#### `macro_group`
- Type: `text`
- Broader grouping of the segment
- Examples:
  - Retail
  - Corporate
  - MICE
  - Leisure
  - Leisure Group

#### `description`
- Type: `text`
- Plain-English description of the market code

### Included market codes
- `OTA` = Online Travel Agency
- `BAR` = Best Available Retail
- `PROM` = Promotional Retail
- `FIT` = Free Independent Traveller
- `CSR` = Corporate Negotiated
- `CNR` = Corporate Room Nights
- `CNI` = Conference / Incentive Group
- `CGR` = Corporate Group
- `EVEN` = Event Demand
- `SMERF` = SMERF Group

---

## 6.4 `public.channel_code_lookup`

Lookup table for booking channels.

### Grain
One row per channel code.

### Columns

#### `channel_code`
- Type: `text`
- Primary key
- Join key from `reservations_hackathon.channel_code`

#### `channel_name`
- Type: `text`
- Human-readable channel name

#### `channel_group`
- Type: `text`
- Broad grouping of the channel
- Examples:
  - Digital
  - Direct
  - Offline

### Included channel codes
- `WEB`
- `REC`
- `EMA`
- `WAL`

---

## 7. Relationship diagram

### Main joins

#### Room type
`reservations_hackathon.space_type = room_type_lookup.space_type`

#### Market segment
`reservations_hackathon.market_code = market_code_lookup.market_code`

#### Channel
`reservations_hackathon.channel_code = channel_code_lookup.channel_code`

---

## 8. Common pitfalls

## 8.1 Do not confuse rows with reservations
Counting rows is not the same as counting bookings. Think about what the correct approach is.

---

## 8.2 Do not confuse reservations with room nights

A reservation can cover multiple rooms. Make sure your room-night calculation accounts for this.

---

## 8.3 Be careful with cancelled bookings

Think about whether cancelled reservations should be included or excluded depending on the question being asked.

---

## 8.4 Know which date you are using

The dataset has multiple date fields. Make sure you use the right one for the question. Using the wrong date can produce a logically wrong answer even if the SQL runs.

---

## 8.5 Know which revenue field you need

There are two revenue columns in the dataset. Understand what each one represents and choose the right one for the question.

---

## 9. Business definitions and semantic clarity

A strong solution will define business metrics explicitly instead of improvising them every time. Your agent should have clear, consistent definitions for concepts like reservation count, room nights, revenue, ADR, and segment groupings.

How you define and group these is part of the challenge.

---

## 10. Why a semantic layer is a strong idea

Direct natural-language to SQL can be error-prone.

A strong team may create a semantic layer that defines:

* business metrics,
* default filters,
* dimension mappings,
* standard business rules.

This is powerful because it reduces common mistakes like:

* counting rows instead of reservations,
* mixing room revenue and total revenue,
* forgetting cancelled rows,
* confusing stay date and booking date.

A semantic layer is **not required**, but it is a strong differentiator and should score well if implemented clearly.

---

## 11. Example questions

These are the kinds of questions the Revenue Manager agent should handle.

### Examples

* What revenue is on the books by month?
* Which segments are driving July?
* How much of July is group business?
* Are we too dependent on OTA?
* What changed in the last 7 days for future stays?
* Which room type is generating the highest ADR?
* How much business was cancelled in June?
* What share of our future business is corporate?
* Which companies are contributing the most revenue?
* Is our business concentrated in a few large bookings?

---

## 12. Answer style

A good answer is not just raw SQL output. A weak answer names a single metric. A strong answer explains the drivers, quantifies the key numbers, highlights risks or opportunities, and speaks in language a GM would trust.

Think: what would a sharp revenue manager say in a morning briefing?

---

## 13. Final advice for teams

1. Decide whether the question is about stay date or booking date.
2. Be explicit about whether cancelled reservations are included.
3. Prefer clear business definitions for metrics like bookings, room nights, and revenue.
4. Return answers in plain English, not just raw query output.
5. When there is ambiguity, state your assumption.

---

## 14. Quick reference

### Main fact table

`reservations_hackathon`

### Lookup tables

* `room_type_lookup`
* `market_code_lookup`
* `channel_code_lookup`

---

## 15. Dataset shape

* `room_type_lookup`: 3 rows
* `market_code_lookup`: 10 rows
* `channel_code_lookup`: 4 rows
* `reservations_hackathon`: 455 rows

---

## 16. Challenge objective

Build a **Revenue Manager Agent for a Hotel General Manager** that uses reservation data to detect what is changing in future business, turn it into clear commercial judgment, and recommend what action to take next.
