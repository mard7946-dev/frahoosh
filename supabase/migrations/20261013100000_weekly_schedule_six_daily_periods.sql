-- Allow the school-wide timetable to represent up to six daily periods.
alter table public.weekly_schedule_entries
  drop constraint if exists weekly_schedule_entries_period_check;
alter table public.weekly_schedule_entries
  add constraint weekly_schedule_entries_period_check
  check (period between 1 and 6);
