-- Executive deputy needs read-only access to school profile
-- for the official certificate preview.

drop policy if exists "executive read school_profile" on public.school_profile;

create policy "executive read school_profile"
on public.school_profile
for select
to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(), '')) = any (
    array['executive','معاون اجرایی','معاونت اجرایی']
  )
);
