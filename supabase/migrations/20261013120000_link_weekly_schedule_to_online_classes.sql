-- Link each weekly timetable entry to its single activated online-class record.
alter table public.weekly_schedule_entries
  add column if not exists online_class_id integer references public.online_classes(id) on delete set null,
  add column if not exists activated_at timestamptz,
  add column if not exists activated_by text;

create index if not exists idx_weekly_schedule_entries_online_class_id
  on public.weekly_schedule_entries (online_class_id);
