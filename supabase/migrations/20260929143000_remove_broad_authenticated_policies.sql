-- Do not let a generic authenticated policy bypass the role/ownership
-- rules in private.frahoosh_can_access(). PostgreSQL combines permissive
-- policies with OR, so these broad policies made several modules writable
-- by every authenticated account.
do $$
declare
  r record;
begin
  for r in
    select schemaname, tablename, policyname
    from pg_policies
    where schemaname='public'
      and policyname in (
        'frahoosh_authenticated_all',
        'frahoosh_authenticated_operational'
      )
  loop
    execute format('drop policy if exists %I on %I.%I',
                   r.policyname, r.schemaname, r.tablename);
  end loop;
end $$;
