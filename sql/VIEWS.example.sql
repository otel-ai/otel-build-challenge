-- Example views for Phase 2 tools. Apply after schema.sql:
--   psql "$DATABASE_URL" -f sql/VIEWS.example.sql
--
-- Required tools should query these views (or an internal layer with identical logic).

create or replace view public.vw_stay_night_active as
select *
from public.reservations_hackathon
where reservation_status <> 'Cancelled';

create or replace view public.vw_segment_stay_night as
select
  r.*,
  m.market_name,
  m.macro_group
from public.reservations_hackathon r
join public.market_code_lookup m
  on r.market_code = m.market_code;
