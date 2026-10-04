create or replace function public.create_meeting_request(
  p_title text,
  p_target_role text,
  p_target_username text,
  p_target_name text,
  p_student_id bigint default null,
  p_requested_day text default null,
  p_requested_date text default null,
  p_requested_time text default null,
  p_reason text default null,
  p_description text default null,
  p_requester_name text default null
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_role text;
  v_username text;
  v_id bigint;
  v_student_ok boolean := true;
begin
  if auth.uid() is null then
    raise exception 'نشست کاربر معتبر نیست';
  end if;

  v_role := lower(trim(coalesce(private.frahoosh_current_role(),'')));
  v_username := trim(coalesce(public.current_account_username(),''));

  if v_role not in (
    'parent','parents','ولی','اولیا',
    'teacher','دبیر','staff','کادر',
    'advisor','counselor','مشاور',
    'educational','معاون آموزشی','معاونت آموزشی',
    'executive','معاون اجرایی','معاونت اجرایی',
    'cultural','معاون پرورشی','معاونت پرورشی',
    'manager','مدیر','مدیریت',
    'student','دانش‌آموز'
  ) then
    raise exception 'این نقش اجازه ثبت درخواست ملاقات ندارد';
  end if;

  if v_username = '' then raise exception 'شناسه حساب کاربر پیدا نشد'; end if;
  if coalesce(trim(p_title),'') = '' then raise exception 'عنوان ملاقات الزامی است'; end if;
  if coalesce(trim(p_target_username),'') = '' then raise exception 'نام کاربر مخاطب الزامی است'; end if;
  if coalesce(trim(p_requested_date),'') = '' then raise exception 'تاریخ ملاقات الزامی است'; end if;
  if coalesce(trim(p_requested_time),'') = '' then raise exception 'ساعت ملاقات الزامی است'; end if;
  if coalesce(trim(p_reason),'') = '' then raise exception 'موضوع ملاقات الزامی است'; end if;

  if v_role in ('parent','parents','ولی','اولیا') and p_student_id is not null then
    select exists(
      select 1
      from public.parent_children pc
      left join public.account_settings a on a.auth_user_id = auth.uid()
      where pc.student_id = p_student_id
        and lower(coalesce(pc.parent_username,'')) in (
          lower(coalesce(a.username,'')),
          lower(coalesce(a.national_code,''))
        )
    ) into v_student_ok;
    if not v_student_ok then raise exception 'این دانش‌آموز به حساب ولی متصل نیست'; end if;
  end if;

  insert into public.meeting_requests(
    title, requester_username, requester_name, requester_role,
    target_username, target_name, target_role, student_id,
    requested_day, requested_date, requested_time,
    reason, description, status, manager_status
  ) values (
    trim(p_title), v_username, coalesce(nullif(trim(p_requester_name),''), v_username), v_role,
    trim(p_target_username), coalesce(nullif(trim(p_target_name),''), trim(p_target_username)), lower(trim(coalesce(p_target_role,''))), p_student_id,
    nullif(trim(coalesce(p_requested_day,'')),''), trim(p_requested_date), trim(p_requested_time),
    trim(p_reason), nullif(trim(coalesce(p_description,'')),''),
    'pending_manager', 'pending'
  )
  returning id into v_id;

  if trim(coalesce(p_target_username,'')) <> '' then
    insert into public.messages(
      sender, sender_name, receiver, title, body, audience_type, audience_value
    ) values (
      v_username, coalesce(nullif(trim(p_requester_name),''), v_username),
      trim(p_target_username), 'درخواست جدید ملاقات',
      'درخواست ملاقات «' || trim(p_title) || '» برای ' ||
      trim(p_requested_date) || ' ساعت ' || trim(p_requested_time) || ' ثبت شد.',
      'user', trim(p_target_username)
    );
  end if;

  return v_id;
end;
$function$;

revoke all on function public.create_meeting_request(text,text,text,text,bigint,text,text,text,text,text,text) from public;
revoke all on function public.create_meeting_request(text,text,text,text,bigint,text,text,text,text,text,text) from anon;
grant execute on function public.create_meeting_request(text,text,text,text,bigint,text,text,text,text,text,text) to authenticated;
