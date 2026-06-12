-- Optional bootstrap if you exported a CSV from the list view.
-- Truncate and load without per-night detail expansion.

truncate public.reservations_hackathon;

-- Example: copy from a one-row-per-reservation CSV (grain shortcut).
-- \copy public.reservations_hackathon (...) from 'export.csv' csv header;

-- Lookup tables can be seeded from /reference HTML snapshots.
