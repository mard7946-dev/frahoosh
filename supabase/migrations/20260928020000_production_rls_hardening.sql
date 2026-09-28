-- Frahoosh production RLS hardening
-- Enables RLS on every public table and centralizes role/ownership checks.

create schema if not exists private;
revoke all on schema private from public;

create or replace function private.frahoosh_context()
returns jsonb
language sql
stable
security definer
set search_path = pg_catalog, public, auth, private
as $$
  select coalesce((
    select jsonb_build_object(
      'username', u.username,
      'role', lower(coalesce(u.role, '')),
      'student_id', u.linked_student_id,
      'teacher_id', u.linked_teacher_id,
      'staff_id', u.linked_staff_id,
      'auth_user_id', au.id
    )
    from auth.users au
    left join public.account_settings a
      on lower(coalesce(a.email,'')) = lower(coalesce(au.email,''))
    left join public.users u
      on u.username = coalesce(a.username, au.email)
    where au.id = (select auth.uid())
    limit 1
  ), '{}'::jsonb);
$$;

create or replace function private.frahoosh_can_access(p_table text, p_row jsonb, p_operation text)
returns boolean
language plpgsql
stable
security definer
set search_path = pg_catalog, public, auth, private
as $$
declare
  c jsonb := private.frahoosh_context();
  v_user text := nullif(c->>'username','');
  v_role text := lower(coalesce(c->>'role',''));
  v_student text := nullif(c->>'student_id','');
  v_teacher text := nullif(c->>'teacher_id','');
  v_owner text;
  v_owned boolean := false;
  v_operation text := lower(coalesce(p_operation,'select'));
  v_staff_role boolean := v_role in (
    'manager','educational','executive','cultural','advisor','teacher','staff',
    'مدیر','معاون آموزشی','معاون اجرایی','معاون پرورشی','مشاور','دبیر','کارمند'
  );
begin
  if v_user is null or v_role = '' then return false; end if;
  if v_staff_role then return true; end if;

  if p_table = 'staff' then return false;
  elsif p_table = 'users' then
    return v_operation = 'select' and p_row->>'username' = v_user;
  elsif p_table = 'account_settings' then
    return v_operation in ('select','update') and p_row->>'username' = v_user;
  elsif p_table = 'students' then
    if v_role = 'student' then
      return p_row->>'id' = v_student;
    elsif v_role in ('parent','parents','ولی','اولیا') then
      return exists (
        select 1 from public.parent_children pc
        where pc.parent_username = v_user and pc.student_id::text = p_row->>'id'
      );
    end if;
    return false;
  elsif p_table = 'parent_children' then
    return p_row->>'parent_username' = v_user or p_row->>'student_id' = v_student;
  elsif p_table in ('finance_accounts','finance_transactions') then
    return false;
  elsif p_table = 'school_relationships' then
    return p_row->>'source_username' = v_user or p_row->>'target_username' = v_user;
  end if;

  if v_operation in ('insert','update','delete') then
    if v_role = 'student' then
      if p_table not in (
        'assignment_submissions','school_ally','basij_registration',
        'school_mayor','student_council','certificate_requests',
        'messages','message_reads'
      ) then return false; end if;
    elsif v_role in ('parent','parents','ولی','اولیا') then
      if p_table not in (
        'meeting_requests','parent_meetings','transport_requests',
        'parent_activities','messages','message_reads'
      ) then return false; end if;
    else
      return false;
    end if;
  end if;

  foreach v_owner in array array[
    nullif(p_row->>'username',''),
    nullif(p_row->>'parent_username',''),
    nullif(p_row->>'student_username',''),
    nullif(p_row->>'sender',''),
    nullif(p_row->>'receiver',''),
    nullif(p_row->>'requester_username',''),
    nullif(p_row->>'target_username',''),
    nullif(p_row->>'actor_username',''),
    nullif(p_row->>'created_by','')
  ] loop
    if v_owner = v_user then v_owned := true; exit; end if;
  end loop;
  if v_owned then return true; end if;

  if v_student is not null and nullif(p_row->>'student_id','') = v_student then
    return true;
  end if;

  if v_role in ('parent','parents','ولی','اولیا')
     and nullif(p_row->>'student_id','') is not null
     and exists (
       select 1 from public.parent_children pc
       where pc.parent_username = v_user
         and pc.student_id::text = p_row->>'student_id'
     ) then
    return true;
  end if;

  if v_teacher is not null and nullif(p_row->>'teacher_id','') = v_teacher then
    return true;
  end if;

  if p_table = 'teachers' then
    return v_role = 'teacher' and p_row->>'id' = v_teacher
       or v_operation = 'select';
  end if;

  if p_table = 'online_class_teachers' then
    return v_role = 'teacher' and p_row->>'teacher_id' = v_teacher;
  end if;

  if v_operation = 'select' then
    if p_table in (
      'school_profile','school_events','exam_schedule','generated_weekly_schedule',
      'weekly_schedule','online_classes','online_class_sessions','smart_class_preview',
      'cultural_competitions','art_competitions','sport_competitions','qari_registration',
      'payment_offers','counseling_classes','counselor_board'
    ) then return true; end if;

    if p_table = 'teachers' then return true; end if;

    if p_row->>'student_id' is null
       and p_row->>'teacher_id' is null
       and p_row->>'parent_username' is null
       and p_row->>'username' is null
       and p_row->>'sender' is null
       and p_row->>'receiver' is null
       and p_row->>'student_username' is null
       and p_row->>'requester_username' is null
       and p_row->>'target_username' is null
       and p_row->>'actor_username' is null
       and p_row->>'created_by' is null
       and p_table not in (
         'messages','message_targets','message_reads','payment_records',
         'payment_attempts','report_cards','report_card_snapshots','grades',
         'student_grades','attendance','online_attendance','assignments',
         'assignment_submissions','discipline_records','counseling_records',
         'counseling_followups','counseling_guidance','ai_educational_analysis',
         'archive_items','parent_meetings','meeting_requests','teacher_meetings',
         'finance_accounts','finance_transactions'
       ) then return true; end if;
  end if;

  return false;
end;
$$;

revoke all on function private.frahoosh_context() from public;
revoke all on function private.frahoosh_can_access(text,jsonb,text) from public;
grant execute on function private.frahoosh_context() to authenticated;
grant execute on function private.frahoosh_can_access(text,jsonb,text) to authenticated;

do $$
declare t record;
begin
  for t in select tablename from pg_tables where schemaname='public' loop
    execute format('alter table public.%I enable row level security',t.tablename);
    execute format('drop policy if exists frahoosh_select on public.%I',t.tablename);
    execute format('drop policy if exists frahoosh_insert on public.%I',t.tablename);
    execute format('drop policy if exists frahoosh_update on public.%I',t.tablename);
    execute format('drop policy if exists frahoosh_delete on public.%I',t.tablename);
    execute format('create policy frahoosh_select on public.%I for select to authenticated using (private.frahoosh_can_access(%L,to_jsonb(%I),%L))',t.tablename,t.tablename,t.tablename,'select');
    execute format('create policy frahoosh_insert on public.%I for insert to authenticated with check (private.frahoosh_can_access(%L,to_jsonb(%I),%L))',t.tablename,t.tablename,t.tablename,'insert');
    execute format('create policy frahoosh_update on public.%I for update to authenticated using (private.frahoosh_can_access(%L,to_jsonb(%I),%L)) with check (private.frahoosh_can_access(%L,to_jsonb(%I),%L))',t.tablename,t.tablename,t.tablename,'update',t.tablename,t.tablename,'update');
    execute format('create policy frahoosh_delete on public.%I for delete to authenticated using (private.frahoosh_can_access(%L,to_jsonb(%I),%L))',t.tablename,t.tablename,t.tablename,'delete');
  end loop;
end $$;

revoke all on all tables in schema public from anon;
grant select,insert,update,delete on all tables in schema public to authenticated;
grant usage,select on all sequences in schema public to authenticated;

alter function public.sync_school_relationships_for_user() set search_path=pg_catalog,public;
alter function public.sync_parent_student_relationship() set search_path=pg_catalog,public;

revoke execute on function public.create_teacher_exam_share(bigint,text,text,timestamptz,timestamptz,integer) from public;
revoke execute on function public.get_shared_attempt_questions(bigint) from public;
revoke execute on function public.get_shared_exam(text) from public;
revoke execute on function public.notify_school_student_change() from public;
revoke execute on function public.start_shared_teacher_exam(text,bigint,text) from public;
revoke execute on function public.submit_teacher_exam(bigint,jsonb) from public;

grant execute on function public.create_teacher_exam_share(bigint,text,text,timestamptz,timestamptz,integer) to authenticated;
grant execute on function public.get_shared_attempt_questions(bigint) to authenticated;
grant execute on function public.get_shared_exam(text) to authenticated;
grant execute on function public.start_shared_teacher_exam(text,bigint,text) to authenticated;
grant execute on function public.submit_teacher_exam(bigint,jsonb) to authenticated;
