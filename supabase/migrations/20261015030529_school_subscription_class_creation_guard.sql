-- Enforce that an online class creator can only attach teachers and students from the same school.
do $$
declare v_def text; v_pos integer;
begin
 v_def:=pg_get_functiondef(to_regprocedure('public.create_online_class_with_members(integer,text,text,text,text,text,text)'));
 if position('FRAHOOSH_TEACHER_SCOPE_GUARD' in v_def)=0 then
  v_pos:=strpos(v_def,'select trim(coalesce(t.first_name');
  if v_pos=0 then raise exception 'Teacher lookup anchor not found in create_online_class_with_members'; end if;
  v_def:=substr(v_def,1,v_pos-1)
   || '/* FRAHOOSH_TEACHER_SCOPE_GUARD */ if not exists(select 1 from public.teachers t where t.id=p_teacher_id and t.tenant_school_id=private.frahoosh_current_school_id()) then raise exception ''دبیر انتخاب‌شده متعلق به این مدرسه نیست''; end if;' || E'\n    '
   || substr(v_def,v_pos);
  v_def:=replace(v_def,'where tc.teacher_id=p_teacher_id and coalesce(tc.active,1)=1',
    'where tc.teacher_id=p_teacher_id and tc.tenant_school_id=private.frahoosh_current_school_id() and coalesce(tc.active,1)=1');
  execute v_def;
 end if;
end $$;
