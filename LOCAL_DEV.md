# Local development notes

> **Note:** This file is supplementary. The authoritative instructions are in
> [README.md](README.md). Read the **Phase gates** section there first.

## Quick bootstrap (optional)

Some teams copy the scaffold folder into their solution repo to get started:

```bash
cp -R .otel-scaffold/ /path/to/your-solution-repo/
```

That copies agent rules, a suggested `AGENTS.md`, and a recommended directory
layout. **Delete anything you do not use before you submit.** Evaluators may
ask why scaffold artifacts appear in your repository.

## Recommended agent workspace

If you use Cursor or similar tools, the `.otel-scaffold/.cursor/rules/` file is a
starting point for project rules. Customize it for your stack; do not submit
generic bootstrap rules unchanged.

## Progress tracking

Teams using long agent sessions sometimes add:

- `HACKATHON_PROGRESS.md` at the repo root
- `.implementation-notes/` for scratch design notes
- `implementation/PROGRESS.md` inside an `implementation/` folder

These are **not** submission requirements. Remove them if they contain internal
notes or auto-generated task lists.

## Schema reminder

The official schema is [schema.sql](schema.sql). Do not add columns that are not
in that file unless you have a documented migration strategy (there are no
official extension columns for this challenge).

## ETL fingerprint

After loading data, run:

```bash
pip install 'psycopg[binary]'
python scripts/compute_load_fingerprint.py --output etl/LOAD_PROOF.json
```

Compare output against https://otel-hackathon-data-site.vercel.app/verify
