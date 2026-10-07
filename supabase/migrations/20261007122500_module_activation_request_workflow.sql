alter table public.module_activations
  add column if not exists status text not null default 'approved',
  add column if not exists requested_by uuid,
  add column if not exists requested_at timestamptz,
  add column if not exists decision_by uuid,
  add column if not exists decision_at timestamptz,
  add column if not exists decision_note text;

update public.module_activations
set status = case when active then 'approved' else 'rejected' end
where status is null or status = '';

alter table public.module_activations enable row level security;

drop policy if exists module_activations_consumer_request on public.module_activations;
create policy module_activations_consumer_request on public.module_activations
for insert to authenticated
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) in
    ('student','دانش‌آموز','parent','parents','ولی','اولیا')
  and requested_by = auth.uid()
  and status = 'pending'
  and active = false
);

drop policy if exists module_activations_consumer_read_own on public.module_activations;
create policy module_activations_consumer_read_own on public.module_activations
for select to authenticated
using (
  requested_by = auth.uid()
  or lower(coalesce(private.frahoosh_current_role(),'')) in
    ('manager','مدیر','مدیریت','educational','معاون آموزشی','executive','معاون اجرایی')
);

drop policy if exists module_activations_staff_decide on public.module_activations;
create policy module_activations_staff_decide on public.module_activations
for update to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','educational','معاون آموزشی','executive','معاون اجرایی'))
with check (lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','educational','معاون آموزشی','executive','معاون اجرایی'));

drop policy if exists module_activations_authenticated_read on public.module_activations;
drop policy if exists module_activations_staff_all on public.module_activations;
drop policy if exists manager_crud_module_activations on public.module_activations;

create policy module_activations_staff_read on public.module_activations
for select to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','educational','معاون آموزشی','executive','معاون اجرایی'));

grant select, insert, update on public.module_activations to authenticated;
