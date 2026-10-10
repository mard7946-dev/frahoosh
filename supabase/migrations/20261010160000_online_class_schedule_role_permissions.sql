-- Allow the approved management roles to create scheduled classes and assign members.
-- Keep all access restricted to authenticated school staff with explicit role checks.
drop policy if exists manager_educational_crud_online_classes on public.online_classes;
create policy manager_educational_crud_online_classes
on public.online_classes for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(), '')) = any(array[
    'manager','مدیر','مدیریت',
    'educational','معاون آموزشی','معاونت آموزشی',
    'executive','معاون اجرایی','معاونت اجرایی'
  ])
)
with check (
  lower(coalesce(private.frahoosh_current_role(), '')) = any(array[
    'manager','مدیر','مدیریت',
    'educational','معاون آموزشی','معاونت آموزشی',
    'executive','معاون اجرایی','معاونت اجرایی'
  ])
);

drop policy if exists manager_educational_crud_online_class_students on public.online_class_students;
create policy manager_educational_crud_online_class_students
on public.online_class_students for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(), '')) = any(array[
    'manager','مدیر','مدیریت',
    'educational','معاون آموزشی','معاونت آموزشی',
    'executive','معاون اجرایی','معاونت اجرایی'
  ])
)
with check (
  lower(coalesce(private.frahoosh_current_role(), '')) = any(array[
    'manager','مدیر','مدیریت',
    'educational','معاون آموزشی','معاونت آموزشی',
    'executive','معاون اجرایی','معاونت اجرایی'
  ])
);

drop policy if exists manager_educational_crud_online_class_teachers on public.online_class_teachers;
create policy manager_educational_crud_online_class_teachers
on public.online_class_teachers for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(), '')) = any(array[
    'manager','مدیر','مدیریت',
    'educational','معاون آموزشی','معاونت آموزشی',
    'executive','معاون اجرایی','معاونت اجرایی'
  ])
)
with check (
  lower(coalesce(private.frahoosh_current_role(), '')) = any(array[
    'manager','مدیر','مدیریت',
    'educational','معاون آموزشی','معاونت آموزشی',
    'executive','معاون اجرایی','معاونت اجرایی'
  ])
);
