-- Tenant-scope existing SECURITY DEFINER RPCs. These checks complement direct-table RLS.
create or replace function private.frahoosh_set_tenant_school()
returns trigger language plpgsql set search_path=''
as $$
declare v_school_id uuid; v_class_id text;
begin
 if coalesce(current_setting('request.jwt.claim.role',true),'')='service_role' or private.frahoosh_is_platform_admin() then
  if new.tenant_school_id is null and tg_op='UPDATE' then new.tenant_school_id:=old.tenant_school_id; end if;
  return new;
 end if;
 v_school_id:=private.frahoosh_current_school_id();
 if v_school_id is null and tg_op='INSERT' and tg_table_name='account_settings' then
  select id into v_school_id from public.schools where slug='frahoosh-default' limit 1;
 end if;
 if v_school_id is null and tg_op='INSERT' and tg_table_name='online_classes'
    and coalesce((auth.jwt()->>'is_anonymous')::boolean,false) then
  select id into v_school_id from public.schools where slug='frahoosh-default' limit 1;
 end if;
 if v_school_id is null and tg_op='INSERT' and to_jsonb(new)?'class_id' then
  v_class_id:=to_jsonb(new)->>'class_id';
  if v_class_id is not null then select oc.tenant_school_id into v_school_id from public.online_classes oc where oc.id::text=v_class_id limit 1; end if;
 end if;
 if v_school_id is not null then new.tenant_school_id:=v_school_id;
 elsif tg_op='UPDATE' then new.tenant_school_id:=old.tenant_school_id;
 elsif new.tenant_school_id is null then raise exception 'مدرسهٔ کاربر مشخص نیست؛ ثبت اطلاعات انجام نشد.' using errcode='42501';
 end if;
 return new;
end; $$;

do $$
declare r record; v_def text; v_guard text; v_pos integer; v_rel integer; v_end integer;
begin
 for r in select * from (values
  ('public.activate_online_class(integer)','online_classes'),
  ('public.delete_online_class_admin(integer)','online_classes'),
  ('public.start_online_class_session(integer)','online_classes'),
  ('public.end_online_class_session(integer)','online_classes'),
  ('public.get_online_class_guest_invite(integer)','online_classes'),
  ('public.guest_close_online_class(integer)','online_classes')
 ) as x(signature,table_name)
 loop
  v_def:=pg_get_functiondef(to_regprocedure(r.signature));
  if position('FRAHOOSH_TENANT_SCOPE_GUARD' in v_def)=0 then
   v_guard:=format('/* FRAHOOSH_TENANT_SCOPE_GUARD */ if not exists(select 1 from public.%I c where c.id=p_class_id and c.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''کلاس متعلق به این مدرسه نیست یا پیدا نشد''; end if;',r.table_name);
   v_pos:=strpos(v_def,'$function$');
   if v_pos=0 then raise exception 'Could not find function body delimiter in %',r.signature; end if;
   v_rel:=strpos(lower(substr(v_def,v_pos+length('$function$'))),'begin');
   if v_rel=0 then raise exception 'Could not find PL/pgSQL body in %',r.signature; end if;
   v_end:=v_pos+length('$function$')+v_rel+length('begin')-2;
   v_def:=substr(v_def,1,v_end)||E'\n  '||v_guard||E'\n  '||substr(v_def,v_end+1);
   execute v_def;
  end if;
 end loop;

 v_def:=pg_get_functiondef(to_regprocedure('public.set_weekly_schedule_day_enabled(text,boolean)'));
 v_def:=replace(v_def,'where weekday = p_weekday;','where weekday = p_weekday and tenant_school_id = private.frahoosh_current_school_id();');
 v_def:=replace(v_def,'where w.online_class_id=s.class_id and w.weekday=p_weekday and not w.day_enabled',
  'where w.online_class_id=s.class_id and w.weekday=p_weekday and w.tenant_school_id=private.frahoosh_current_school_id() and not w.day_enabled');
 v_def:=replace(v_def,'where w.online_class_id=c.id and w.weekday=p_weekday and not w.day_enabled',
  'where w.online_class_id=c.id and w.weekday=p_weekday and w.tenant_school_id=private.frahoosh_current_school_id() and not w.day_enabled');
 execute v_def;

 v_def:=pg_get_functiondef(to_regprocedure('public.get_student_class_schedule(text)'));
 v_def:=replace(v_def,'where p_weekday is null or w.weekday=p_weekday',
  'where w.tenant_school_id=private.frahoosh_current_school_id() and (p_weekday is null or w.weekday=p_weekday)');
 execute v_def;

 v_def:=pg_get_functiondef(to_regprocedure('public.create_payment_attempt(integer,integer)'));
 v_def:=replace(v_def,'where id=p_offer_id and active=1;','where id=p_offer_id and active=1 and tenant_school_id=private.frahoosh_current_school_id();');
 v_def:=replace(v_def,'insert into public.payment_attempts',
  'if not exists(select 1 from public.students s where s.id=v_sid and s.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''پرونده دانش‌آموز متعلق به این مدرسه نیست''; end if;'||E'\n  insert into public.payment_attempts');
 execute v_def;

 v_def:=pg_get_functiondef(to_regprocedure('public.start_teacher_exam(integer,integer,text)'));
 if position('FRAHOOSH_EXAM_SCOPE_GUARD' in v_def)=0 then
  v_pos:=strpos(v_def,'$function$'); v_rel:=strpos(lower(substr(v_def,v_pos+length('$function$'))),'begin');
  v_end:=v_pos+length('$function$')+v_rel+length('begin')-2;
  v_guard:='/* FRAHOOSH_EXAM_SCOPE_GUARD */ if not exists(select 1 from public.teacher_exams e where e.id=p_quiz_id and e.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''آزمون متعلق به این مدرسه نیست یا منتشر نشده است''; end if;';
  v_def:=substr(v_def,1,v_end)||E'\n  '||v_guard||E'\n  '||substr(v_def,v_end+1);
  v_def:=replace(v_def,'from public.students s where lower(s.email)=lower(v_email) or lower(s.national_code)=',
   'from public.students s where s.tenant_school_id=private.frahoosh_current_school_id() and (lower(s.email)=lower(v_email) or lower(s.national_code)=');
  v_def:=replace(v_def,'or lower(s.student_code)=lower(p_student_username) order by s.id limit 1;',
   'or lower(s.student_code)=lower(p_student_username)) order by s.id limit 1;');
  execute v_def;
 end if;

 v_def:=pg_get_functiondef(to_regprocedure('public.create_meeting_request(text,text,text,text,bigint,text,text,text,text,text,text)'));
 if position('FRAHOOSH_MEETING_STUDENT_SCOPE_GUARD' in v_def)=0 then
  v_pos:=strpos(v_def,'$function$'); v_rel:=strpos(lower(substr(v_def,v_pos+length('$function$'))),'begin');
  v_end:=v_pos+length('$function$')+v_rel+length('begin')-2;
  v_guard:='/* FRAHOOSH_MEETING_STUDENT_SCOPE_GUARD */ if p_student_id is not null and not exists(select 1 from public.students s where s.id=p_student_id and s.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''دانش‌آموز متعلق به این مدرسه نیست''; end if;';
  v_def:=substr(v_def,1,v_end)||E'\n  '||v_guard||E'\n  '||substr(v_def,v_end+1);
  execute v_def;
 end if;

 v_def:=pg_get_functiondef(to_regprocedure('public.send_school_message(text,text,text,text,text)'));
 if position('FRAHOOSH_MESSAGE_RECIPIENT_SCOPE_GUARD' in v_def)=0 then
  v_def:=replace(v_def,'if v_receiver is null then raise exception ''receiver required''; end if;',
   'if v_receiver is null then raise exception ''receiver required''; end if; /* FRAHOOSH_MESSAGE_RECIPIENT_SCOPE_GUARD */ if lower(coalesce(p_audience_type,''user''))=''user'' and not exists(select 1 from public.account_settings a where a.username=v_receiver and a.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''مخاطب متعلق به این مدرسه نیست''; end if;');
  execute v_def;
 end if;
end $$;
