-- Complete role-aware visibility for the remaining student/teacher/class domain tables.
-- Uses relationship columns rather than login strings.

do $$
declare r record; p text;
begin
  for r in
    select distinct c.table_name, bool_or(c.column_name='teacher_id') as has_teacher
    from information_schema.columns c
    where c.table_schema='public' and c.column_name='student_id'
      and c.table_name not in (
        'students','account_settings','parent_children',
        'ai_educational_analysis','ai_questions','archive_items',
        'parent_dashboard_events','student_dashboard_events',
        'payment_records','payment_transactions'
      )
    group by c.table_name
  loop
    p := 'staff domain access '||r.table_name;
    execute format('drop policy if exists %I on public.%I',p,r.table_name);
    execute format('create policy %I on public.%I for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()))',p,r.table_name);
    p := 'student linked read '||r.table_name;
    execute format('drop policy if exists %I on public.%I',p,r.table_name);
    execute format('create policy %I on public.%I for select to authenticated using (student_id=(select private.frahoosh_current_student_id()))',p,r.table_name);
    p := 'parent linked read '||r.table_name;
    execute format('drop policy if exists %I on public.%I',p,r.table_name);
    execute format('create policy %I on public.%I for select to authenticated using (exists (select 1 from public.parent_children pc join public.account_settings a on lower(a.username)=lower(pc.parent_username) where pc.student_id=public.%I.student_id and a.auth_user_id=(select auth.uid())))',p,r.table_name,r.table_name);
    if r.has_teacher then
      p := 'teacher linked read '||r.table_name;
      execute format('drop policy if exists %I on public.%I',p,r.table_name);
      execute format('create policy %I on public.%I for select to authenticated using (teacher_id=(select private.frahoosh_current_teacher_id()))',p,r.table_name);
    end if;
  end loop;

  for r in
    select distinct table_name from information_schema.columns
    where table_schema='public' and column_name='teacher_id'
      and table_name not in ('teachers','assignments','attendance','grades','student_grades','teacher_exams','teacher_parent_meetings','teacher_classes','online_class_teachers','payment_records')
  loop
    p := 'staff teacher domain access '||r.table_name;
    execute format('drop policy if exists %I on public.%I',p,r.table_name);
    execute format('create policy %I on public.%I for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()))',p,r.table_name);
    p := 'teacher own read '||r.table_name;
    execute format('drop policy if exists %I on public.%I',p,r.table_name);
    execute format('create policy %I on public.%I for select to authenticated using (teacher_id=(select private.frahoosh_current_teacher_id()))',p,r.table_name);
  end loop;

  for r in
    select distinct table_name from information_schema.columns
    where table_schema='public' and column_name='class_id'
      and table_name not in ('online_class_students','online_class_teachers')
  loop
    p := 'staff class domain access '||r.table_name;
    execute format('drop policy if exists %I on public.%I',p,r.table_name);
    execute format('create policy %I on public.%I for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()))',p,r.table_name);
    p := 'student class member read '||r.table_name;
    execute format('drop policy if exists %I on public.%I',p,r.table_name);
    execute format('create policy %I on public.%I for select to authenticated using (exists (select 1 from public.online_class_students m where m.class_id::text=public.%I.class_id::text and m.student_id::text=(select private.frahoosh_current_student_id())::text))',p,r.table_name,r.table_name);
    p := 'teacher class member read '||r.table_name;
    execute format('drop policy if exists %I on public.%I',p,r.table_name);
    execute format('create policy %I on public.%I for select to authenticated using (exists (select 1 from public.online_class_teachers m where m.class_id::text=public.%I.class_id::text and m.teacher_id::text=(select private.frahoosh_current_teacher_id())::text))',p,r.table_name,r.table_name);
  end loop;
end $$;