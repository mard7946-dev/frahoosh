-- Schedule metadata for standalone online classes.
-- Safe additive migration: existing class records and links remain unchanged.
alter table public.online_classes
  add column if not exists scheduled_date date,
  add column if not exists scheduled_time time without time zone,
  add column if not exists auto_activate boolean not null default true;

create index if not exists online_classes_schedule_idx
  on public.online_classes (scheduled_date, scheduled_time)
  where scheduled_date is not null;

comment on column public.online_classes.scheduled_date is 'Local school date for the online class';
comment on column public.online_classes.scheduled_time is 'Local school start time for the online class';
comment on column public.online_classes.auto_activate is 'Allow the dashboard to activate the class at its scheduled time';
