-- Keep student-owned shared exam attempts and guest class registration within the caller's tenant.
do $$
declare v_def text; v_pos integer; v_rel integer; v_end integer; v_guard text;
begin
 v_def:=pg_get_functiondef(to_regprocedure('public.get_shared_attempt_questions(bigint)'));
 v_def:=replace(v_def,'where a.id=p_attempt_id',
  'where a.id=p_attempt_id and a.tenant_school_id=private.frahoosh_current_school_id()');
 execute v_def;

 v_def:=pg_get_functiondef(to_regprocedure('public.start_shared_teacher_exam(text,integer,text)'));
 v_def:=replace(v_def,
  'from public.students s where lower(s.email)=lower(v_email) or lower(s.national_code)=',
  'from public.students s where s.tenant_school_id=private.frahoosh_current_school_id() and (lower(s.email)=lower(v_email) or lower(s.national_code)=');
 v_def:=replace(v_def,
  'or lower(s.student_code)=lower(coalesce(p_student_username,v_username)) order by s.id limit 1;',
  'or lower(s.student_code)=lower(coalesce(p_student_username,v_username))) order by s.id limit 1;');
 execute v_def;

 v_def:=pg_get_functiondef(to_regprocedure('public.submit_teacher_exam(bigint,jsonb)'));
 if position('FRAHOOSH_TENANT_SCOPE_GUARD' in v_def)=0 then
  v_pos:=strpos(v_def,'$function$'); v_rel:=strpos(lower(substr(v_def,v_pos+length('$function$'))),'begin');
  v_end:=v_pos+length('$function$')+v_rel+length('begin')-2;
  v_guard:='/* FRAHOOSH_TENANT_SCOPE_GUARD */ if not exists(select 1 from public.teacher_exam_attempts a where a.id=p_attempt_id and a.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''تلاش آزمون متعلق به این مدرسه نیست''; end if;';
  v_def:=substr(v_def,1,v_end)||E'\n  '||v_guard||E'\n  '||substr(v_def,v_end+1);
  execute v_def;
 end if;

 v_def:=pg_get_functiondef(to_regprocedure('public.register_online_class_student_guest(integer,integer,text,text)'));
 if position('FRAHOOSH_TENANT_SCOPE_GUARD' in v_def)=0 then
  v_pos:=strpos(v_def,'$function$'); v_rel:=strpos(lower(substr(v_def,v_pos+length('$function$'))),'begin');
  v_end:=v_pos+length('$function$')+v_rel+length('begin')-2;
  v_guard:='/* FRAHOOSH_TENANT_SCOPE_GUARD */ if not exists(select 1 from public.online_classes c where c.id=p_class_id and c.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''کلاس متعلق به این مدرسه نیست''; end if;';
  v_def:=substr(v_def,1,v_end)||E'\n  '||v_guard||E'\n  '||substr(v_def,v_end+1);
  execute v_def;
 end if;
end $$;
