-- Frahoosh: make every real public module table usable by the manager.
-- Only adds manager access where RLS is already enabled; it never changes
-- access rules for students, parents, teachers or other roles.
do $$
declare
  r record;
begin
  for r in
    select n.nspname as schema_name, c.relname as table_name
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relkind = 'r'
      and c.relrowsecurity = true
  loop
    execute format(
      'drop policy if exists frahoosh_manager_full_crud on %I.%I',
      r.schema_name, r.table_name
    );
    execute format(
      'create policy frahoosh_manager_full_crud on %I.%I
       for all to authenticated
       using (
         lower(coalesce((select private.frahoosh_current_role()), '''')) = any(
           array[''manager'',''admin'',''principal'',''مدیر'',''مدیریت'',''مدیر مدرسه'',''مدیریت مدرسه'']
         )
       )
       with check (
         lower(coalesce((select private.frahoosh_current_role()), '''')) = any(
           array[''manager'',''admin'',''principal'',''مدیر'',''مدیریت'',''مدیر مدرسه'',''مدیریت مدرسه'']
         )
       )',
      r.schema_name, r.table_name
    );
  end loop;
end $$;

grant usage on schema public to authenticated;
