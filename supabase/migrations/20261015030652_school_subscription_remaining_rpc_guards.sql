-- Extend school isolation to the remaining exposed operational RPCs and honor subscription state.
do $$
declare r record; v_def text; v_guard text; v_pos integer; v_rel integer; v_end integer;
begin
 for r in select * from (values
  ('public.delete_meeting_request(bigint)','meeting_requests','p_id'),
  ('public.update_meeting_request(bigint,text,text,text,text,text,text,text,text)','meeting_requests','p_id'),
  ('public.get_teacher_exam_questions(bigint)','teacher_exam_attempts','p_attempt_id'),
  ('public.create_teacher_exam_share(integer,text,text,timestamp with time zone,timestamp with time zone,integer)','teacher_exams','p_quiz_id'),
  ('public.update_teacher_exam_share(bigint,text,text,timestamp with time zone,timestamp with time zone,integer,boolean)','teacher_exam_shares','p_share_id')
 ) as x(signature,table_name,id_arg)
 loop
  v_def:=pg_get_functiondef(to_regprocedure(r.signature));
  if position('FRAHOOSH_TENANT_SCOPE_GUARD' in v_def)=0 then
   v_guard:=format('/* FRAHOOSH_TENANT_SCOPE_GUARD */ if not exists(select 1 from public.%I t where t.id=%I and t.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''رکورد متعلق به این مدرسه نیست یا پیدا نشد''; end if;',r.table_name,r.id_arg);
   v_pos:=strpos(v_def,'$function$'); v_rel:=strpos(lower(substr(v_def,v_pos+length('$function$'))),'begin');
   if v_pos=0 or v_rel=0 then raise exception 'Could not find function body in %',r.signature; end if;
   v_end:=v_pos+length('$function$')+v_rel+length('begin')-2;
   v_def:=substr(v_def,1,v_end)||E'\n  '||v_guard||E'\n  '||substr(v_def,v_end+1);
   execute v_def;
  end if;
 end loop;

 for r in select * from (values
  ('public.record_online_class_checkpoint(integer,bigint,integer,integer)','p_class_id','p_student_id'),
  ('public.record_online_class_checkpoint_failure(integer,bigint,integer,integer)','p_class_id','p_student_id'),
  ('public.record_online_class_entry(integer,bigint,integer)','p_class_id','p_student_id'),
  ('public.is_online_class_student_blocked(integer,bigint,integer)','p_class_id','p_student_id')
 ) as x(signature,class_arg,student_arg)
 loop
  v_def:=pg_get_functiondef(to_regprocedure(r.signature));
  if position('FRAHOOSH_TENANT_SCOPE_GUARD' in v_def)=0 then
   v_pos:=strpos(v_def,'$function$'); v_rel:=strpos(lower(substr(v_def,v_pos+length('$function$'))),'begin');
   if v_pos=0 or v_rel=0 then raise exception 'Could not find function body in %',r.signature; end if;
   v_end:=v_pos+length('$function$')+v_rel+length('begin')-2;
   v_guard:=format('/* FRAHOOSH_TENANT_SCOPE_GUARD */ if not exists(select 1 from public.online_classes c where c.id=%I and c.tenant_school_id=private.frahoosh_current_school_id()) or not exists(select 1 from public.students s where s.id=%I and s.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''کلاس یا دانش‌آموز متعلق به این مدرسه نیست''; end if;',r.class_arg,r.student_arg);
   v_def:=substr(v_def,1,v_end)||E'\n  '||v_guard||E'\n  '||substr(v_def,v_end+1);
   execute v_def;
  end if;
 end loop;

 v_def:=pg_get_functiondef(to_regprocedure('public.list_teacher_exam_shares(integer)'));
 v_def:=replace(v_def,'where s.quiz_id=p_quiz_id and (a.national_code=t.national_code or a.username=t.national_code)',
  'where s.quiz_id=p_quiz_id and e.tenant_school_id=private.frahoosh_current_school_id() and (a.national_code=t.national_code or a.username=t.national_code)');
 execute v_def;

 v_def:=pg_get_functiondef(to_regprocedure('public.frahoosh_can_activate_modules()'));
 v_def:=replace(v_def,'select lower(coalesce((select role from public.account_settings where auth_user_id=auth.uid() limit 1),'''')) in',
  'select private.frahoosh_school_access_active(private.frahoosh_current_school_id()) and lower(coalesce((select role from public.account_settings where auth_user_id=auth.uid() limit 1),'''')) in');
 execute v_def;

 v_def:=pg_get_functiondef(to_regprocedure('public.is_module_active(text)'));
 v_def:=replace(v_def,'select coalesce((select active from public.module_activations where module_key=p_module_key), true);',
  'select private.frahoosh_school_access_active(private.frahoosh_current_school_id()) and coalesce((select active from public.module_activations where module_key=p_module_key and tenant_school_id=private.frahoosh_current_school_id()), true);');
 execute v_def;

 v_def:=pg_get_functiondef(to_regprocedure('public.request_module_activation(text)'));
 if position('FRAHOOSH_SUBSCRIPTION_ACTIVE_GUARD' in v_def)=0 then
  v_pos:=strpos(v_def,'$function$'); v_rel:=strpos(lower(substr(v_def,v_pos+length('$function$'))),'begin');
  v_end:=v_pos+length('$function$')+v_rel+length('begin')-2;
  v_guard:='/* FRAHOOSH_SUBSCRIPTION_ACTIVE_GUARD */ if not private.frahoosh_school_access_active(private.frahoosh_current_school_id()) then raise exception ''اشتراک مدرسه منقضی شده یا فعال نیست''; end if;';
  v_def:=substr(v_def,1,v_end)||E'\n  '||v_guard||E'\n  '||substr(v_def,v_end+1);
  execute v_def;
 end if;
end $$;
