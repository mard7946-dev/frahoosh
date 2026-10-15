create or replace function public.verify_online_class_student(
  p_first_name text, p_last_name text, p_class_name text, p_student_code text
)
returns boolean
language plpgsql
stable
security definer
set search_path = public, pg_temp
as $$
declare
  v_school uuid := private.frahoosh_current_school_id();
begin
  if nullif(btrim(coalesce(p_first_name,'')),'') is null
    or nullif(btrim(coalesce(p_last_name,'')),'') is null
    or nullif(btrim(coalesce(p_class_name,'')),'') is null
    or nullif(btrim(coalesce(p_student_code,'')),'') is null then
    raise exception 'نام، نام خانوادگی، کد دانش‌آموزی و کلاس الزامی است';
  end if;
  return exists (
    select 1 from public.students st
    where st.tenant_school_id = v_school
      and st.student_code = btrim(p_student_code)
      and replace(replace(regexp_replace(lower(btrim(coalesce(st.class_name,''))), '\s+', '', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(btrim(p_class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
      and replace(replace(regexp_replace(lower(btrim(coalesce(st.first_name,'')||' '||coalesce(st.last_name,''))), '\s+', ' ', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(btrim(p_first_name||' '||p_last_name)), '\s+', ' ', 'g'),'ي','ی'),'ك','ک')
  );
end;
$$;
grant execute on function public.verify_online_class_student(text,text,text,text) to anon, authenticated;
