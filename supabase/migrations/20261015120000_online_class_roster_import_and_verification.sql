-- Frahoosh online-class roster import and student identity verification.
create or replace function public.import_online_class_roster(p_kind text, p_rows jsonb)
returns integer
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_school uuid := private.frahoosh_current_school_id();
  v_role text := lower(coalesce(private.frahoosh_current_role(), ''));
  r jsonb;
  v_count integer := 0;
  v_first text;
  v_last text;
  v_code text;
  v_class text;
  v_subject text;
  v_id integer;
begin
  if auth.uid() is null then raise exception 'برای ورود اطلاعات باید وارد حساب مدیریت شوید'; end if;
  if v_role not in ('manager','مدیر','مدیریت','principal','administrator','admin') then
    raise exception 'فقط مدیریت مدرسه مجاز به ورود گروهی اطلاعات است';
  end if;
  if v_school is null or not private.frahoosh_school_access_active(v_school) then
    raise exception 'اشتراک یا دسترسی این مدرسه فعال نیست';
  end if;
  if p_kind not in ('students','teachers') then raise exception 'نوع فهرست معتبر نیست'; end if;
  if jsonb_typeof(p_rows) <> 'array' or jsonb_array_length(p_rows) < 1 or jsonb_array_length(p_rows) > 1000 then
    raise exception 'فایل باید بین ۱ تا ۱۰۰۰ ردیف معتبر داشته باشد';
  end if;
  for r in select value from jsonb_array_elements(p_rows) loop
    v_first := btrim(coalesce(r->>'first_name',''));
    v_last := btrim(coalesce(r->>'last_name',''));
    if v_first = '' or v_last = '' then raise exception 'نام و نام خانوادگی در همه ردیف‌ها الزامی است'; end if;
    if p_kind = 'students' then
      v_code := btrim(coalesce(r->>'student_code',''));
      v_class := btrim(coalesce(r->>'class_name',''));
      if v_code = '' or v_class !~ '^[0-9۰-۹٠-٩]+/[0-9۰-۹٠-٩]+$' then
        raise exception 'کد دانش‌آموزی و کلاس معتبر برای همه ردیف‌ها الزامی است';
      end if;
      select id into v_id from public.students
        where tenant_school_id=v_school and student_code=v_code
        order by id limit 1;
      if v_id is null then
        insert into public.students(first_name,last_name,student_code,class_name,tenant_school_id)
        values(v_first,v_last,v_code,v_class,v_school);
      else
        update public.students set first_name=v_first,last_name=v_last,class_name=v_class
        where id=v_id and tenant_school_id=v_school;
      end if;
    else
      v_code := regexp_replace(btrim(coalesce(r->>'national_code','')), '[^0-9]', '', 'g');
      v_subject := nullif(btrim(coalesce(r->>'subject','')), '');
      if v_code !~ '^[0-9]{10}$' then raise exception 'کد ملی دبیر باید ۱۰ رقم باشد'; end if;
      select id into v_id from public.teachers
        where tenant_school_id=v_school and national_code=v_code
        order by id limit 1;
      if v_id is null then
        insert into public.teachers(first_name,last_name,national_code,subject,tenant_school_id)
        values(v_first,v_last,v_code,v_subject,v_school);
      else
        update public.teachers set first_name=v_first,last_name=v_last,subject=coalesce(v_subject,subject)
        where id=v_id and tenant_school_id=v_school;
      end if;
    end if;
    v_count := v_count + 1;
    v_id := null;
  end loop;
  return v_count;
end;
$$;

create or replace function public.register_online_class_student_guest_verified(
  p_class_id integer, p_session_id integer, p_display_name text, p_class_name text, p_student_code text
)
returns boolean
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_uid uuid := auth.uid();
  v_name text := btrim(coalesce(p_display_name,''));
  v_class text := btrim(coalesce(p_class_name,''));
  v_code text := btrim(coalesce(p_student_code,''));
  v_school uuid := private.frahoosh_current_school_id();
begin
  if v_uid is null then raise exception 'ورود مهمان معتبر نیست'; end if;
  if v_name = '' or v_class = '' or v_code = '' then raise exception 'نام، کلاس و کد دانش‌آموزی الزامی است'; end if;
  if not exists (
    select 1 from public.students st
    where st.tenant_school_id=v_school and st.student_code=v_code
      and replace(replace(regexp_replace(lower(btrim(coalesce(st.class_name,''))), '\s+', '', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(v_class), '\s+', '', 'g'),'ي','ی'),'ك','ک')
      and replace(replace(regexp_replace(lower(btrim(coalesce(st.first_name,'')||' '||coalesce(st.last_name,''))), '\s+', ' ', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(v_name), '\s+', ' ', 'g'),'ي','ی'),'ك','ک')
  ) then raise exception 'اطلاعات دانش‌آموز با فهرست رسمی همین مدرسه مطابقت ندارد؛ نام، کلاس و کد دانش‌آموزی را بررسی کنید'; end if;
  if not exists(select 1 from public.online_classes c where c.id=p_class_id and c.tenant_school_id=v_school) then
    raise exception 'کلاس متعلق به این مدرسه نیست';
  end if;
  if not exists(select 1 from public.online_class_sessions s where s.id=p_session_id and s.class_id=p_class_id and coalesce(s.ended_at,'')='') then
    raise exception 'جلسه کلاس فعال نیست';
  end if;
  if not exists(select 1 from public.weekly_schedule_entries w
    where w.tenant_school_id=v_school and w.online_class_id=p_class_id and w.activated_at is not null
      and replace(replace(regexp_replace(lower(btrim(w.class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(v_class), '\s+', '', 'g'),'ي','ی'),'ك','ک')) then
    raise exception 'این کلاس در برنامه هفتگی به جلسه فعال متصل نیست';
  end if;
  update public.guest_online_members set display_name=v_name,role='guest',left_at=null
    where class_id=p_class_id and user_id=v_uid;
  if not found then
    insert into public.guest_online_members(class_id,user_id,display_name,role)
    values(p_class_id,v_uid,v_name,'guest');
  end if;
  return true;
end;
$$;

grant execute on function public.import_online_class_roster(text,jsonb) to authenticated;
grant execute on function public.register_online_class_student_guest_verified(integer,integer,text,text,text) to anon, authenticated;
