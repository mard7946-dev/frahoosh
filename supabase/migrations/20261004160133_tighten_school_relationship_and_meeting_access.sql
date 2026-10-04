drop policy if exists "staff_meeting_requests_insert" on public.meeting_requests;
create policy "school_staff_meeting_requests_insert"
on public.meeting_requests
for insert
to authenticated
with check (
  lower(coalesce(requester_username,'')) = lower(coalesce(public.current_account_username(),''))
  and lower(coalesce(requester_role,'')) = lower(coalesce(private.frahoosh_current_role(),''))
  and lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
    'manager','مدیر','مدیریت',
    'executive','معاون اجرایی','معاونت اجرایی',
    'educational','معاون آموزشی','معاونت آموزشی',
    'cultural','معاون پرورشی','معاونت پرورشی',
    'advisor','مشاور','counselor',
    'teacher','دبیر','staff'
  ])
);

drop policy if exists "staff parent_children insert" on public.parent_children;
drop policy if exists "staff parent_children update" on public.parent_children;
drop policy if exists "staff parent_children delete" on public.parent_children;
create policy "management parent_children insert"
on public.parent_children for insert to authenticated
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
    'manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'
  ])
);
create policy "management parent_children update"
on public.parent_children for update to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
    'manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'
  ])
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
    'manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'
  ])
);
create policy "management parent_children delete"
on public.parent_children for delete to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
    'manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'
  ])
);

drop policy if exists "school_relationships_staff_all" on public.school_relationships;
create policy "management school_relationships_all"
on public.school_relationships for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
    'manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'
  ])
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
    'manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'
  ])
);
