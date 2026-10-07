drop policy if exists module_activations_consumer_active_read on public.module_activations;
create policy module_activations_consumer_active_read on public.module_activations
for select to authenticated
using (
  active = true
  and lower(coalesce(private.frahoosh_current_role(),'')) in
    ('student','دانش‌آموز','parent','parents','ولی','اولیا')
);