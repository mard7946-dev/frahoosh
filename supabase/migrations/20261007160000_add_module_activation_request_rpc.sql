create or replace function public.request_module_activation(p_module_key text)
returns public.module_activations
language plpgsql
security definer
set search_path=public,private
as $$
declare
  v_role text := lower(coalesce(private.frahoosh_current_role(),''));
  v_row public.module_activations;
begin
  if v_role not in ('student','دانش‌آموز','parent','parents','ولی','اولیا') then
    raise exception 'فقط دانش‌آموز و اولیا می‌توانند درخواست فعال‌سازی ثبت کنند';
  end if;
  if coalesce(trim(p_module_key),'') = '' then
    raise exception 'شناسه قابلیت الزامی است';
  end if;
  select * into v_row from public.module_activations where module_key=trim(p_module_key) for update;
  if found and v_row.active then
    raise exception 'این قابلیت قبلاً فعال شده است';
  end if;
  if found then
    update public.module_activations
      set status='pending', requested_by=auth.uid(), requested_at=now(),
          decision_by=null, decision_at=null, decision_note=null, active=false,
          updated_at=now()
      where module_key=trim(p_module_key)
      returning * into v_row;
  else
    insert into public.module_activations(module_key,active,status,requested_by,requested_at,updated_at)
      values(trim(p_module_key),false,'pending',auth.uid(),now(),now())
      returning * into v_row;
  end if;
  return v_row;
end $$;
revoke all on function public.request_module_activation(text) from public;
revoke all on function public.request_module_activation(text) from anon;
grant execute on function public.request_module_activation(text) to authenticated;
