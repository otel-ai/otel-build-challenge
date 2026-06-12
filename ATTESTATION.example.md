# ATTESTATION.md (Phase 0)

Copy this file to your solution repository as `ATTESTATION.md` and fill it in
before starting Phase 1. Keep answers concise — a few sentences per prompt.

---

## Candidate

- Name:
- Repository URL:
- Date:

---

## Comprehension prompts

### 1. Fact-table grain

In one sentence, what is the grain of `reservations_hackathon`?

> Your answer:

### 2. Revenue columns

Name the two revenue columns and when to use each.

> Your answer:

### 3. Row vs reservation

Give one example question where counting rows would be wrong.

> Your answer:

### 4. Schema fields

Is there an `otel_challenge_token` column in the official schema? If so, what is it used for?

> Your answer:

### 5. Stay date vs booking date

When would you use `stay_date` vs `create_datetime`?

> Your answer:

### 6. Block vs transient

How does `is_block` affect a “group vs transient mix” question?

> Your answer:

### 7. List pagination

How many reservations does the data site show per list page?

> Your answer:

### 8. Pagination completeness

How will you prove you did not miss the last list page during ETL?

> Your answer:

---

## ETL design (one line)

Describe pagination strategy + idempotency approach + **anchor date** you will
scrape against (must match `/verify` on load day).

> Your answer:
