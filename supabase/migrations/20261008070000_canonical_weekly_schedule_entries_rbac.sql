-- Frahoosh: normalize weekly schedule entry CRUD to the canonical day/period table.
drop policy if exists "weekly_schedule_entries_staff_all" on public.weekly_schedule_entries;

create policy "weekly_schedule_entries_management_crud"
on public.weekly_schedule_entries
for all
to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(), '')) = any (
    array[
      'manager','مدیر','مدیریت',
      'educational','معاون آموزشی','معاونت آموزشی',
      'executive','معاون اجرایی','معاونت اجرایی'
    ]
  )
)
with check (
  lower(coalesce(private.frahoosh_current_role(), '')) = any (
    array[
      'manager','مدیر','مدیریت',
      'educational','معاون آموزشی','معاونت آموزشی',
      'executive','معاون اجرایی','معاونت اجرایی'
    ]
  )
);

create policy "weekly_schedule_entries_teacher_own_read"
on public.weekly_schedule_entries
for select
to authenticated
using (
  teacher_id = private.frahoosh_current_teacher_id()
);

alter table public.weekly_schedule_entries
  drop constraint if exists weekly_schedule_entries_period_check;

alter table public.weekly_schedule_entries
  add constraint weekly_schedule_entries_period_check
  check (period between 1 and 3);

create index if not exists idx_weekly_schedule_entries_class_day_period
  on public.weekly_schedule_entries (class_name, weekday, period);
