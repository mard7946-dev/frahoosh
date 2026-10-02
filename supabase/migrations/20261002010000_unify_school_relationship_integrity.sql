-- فراهوش: یکپارچه‌سازی هسته ارتباطات مدرسه
-- این migration اتصال رکوردهای دانش‌آموز/دبیر، دسترسی رابطه‌ای و پیام‌رسانی را
-- در سطح دیتابیس تثبیت می‌کند.

create or replace function private.frahoosh_current_parent_username()
returns text
language sql
stable
security definer
set search_path=''
as $$
  select coalesce(
    (select a.username
       from public.account_settings a
      where a.auth_user_id=auth.uid()
        and lower(coalesce(a.role,'')) in ('parent','parents','ولی','اولیا')
      limit 1),
    (select a.username
       from public.account_settings a
      where a.auth_user_id=auth.uid()
      limit 1)
  )
$$;

create or replace function private.frahoosh_current_parent_matches(p_parent_key text)
returns boolean
language sql
stable
security definer
set search_path=''
as $$
  select exists(
    select 1 from public.account_settings a
     where a.auth_user_id=auth.uid()
       and (
         lower(coalesce(a.username,''))=lower(coalesce(p_parent_key,''))
         or lower(coalesce(a.email,''))=lower(coalesce(p_parent_key,''))
         or lower(coalesce(a.national_code,''))=lower(coalesce(p_parent_key,''))
       )
  )
$$;

create or replace function private.frahoosh_teacher_can_access_student(p_student_id bigint)
returns boolean
language sql
stable
security definer
set search_path=''
as $$
  select exists (
    select 1
      from public.teacher_classes tc
      join public.students s
        on s.grade=tc.grade and s.class_name=tc.class_name
     where tc.teacher_id=private.frahoosh_current_teacher_id()
       and coalesce(tc.active,1)=1
       and s.id=p_student_id
  )
$$;

-- تمام ستون‌های student_id / teacher_id که قبلاً orphan نداشتند،
-- به موجودیت اصلی خود متصل می‌شوند.
do $$
declare r record; cname text;
begin
  for r in
    select c.table_name,c.column_name,
           case when c.column_name='student_id' then 'students' else 'teachers' end ref_table
    from information_schema.columns c
    where c.table_schema='public'
      and c.column_name in ('student_id','teacher_id')
      and c.data_type in ('integer','bigint')
      and not exists (
        select 1
        from information_schema.key_column_usage k
        join information_schema.table_constraints tc
          on tc.constraint_name=k.constraint_name and tc.table_schema=k.table_schema
        where tc.table_schema='public'
          and tc.constraint_type='FOREIGN KEY'
          and k.table_name=c.table_name
          and k.column_name=c.column_name
      )
  loop
    execute format(
      'select 1 from public.%I x left join public.%I y on y.id=x.%I where x.%I is not null and y.id is null limit 1',
      r.table_name,r.ref_table,r.column_name,r.column_name
    ) into cname;
    if cname is null then
      execute format(
        'alter table public.%I add constraint %I foreign key (%I) references public.%I(id)',
        r.table_name,
        left('fk_'||r.table_name||'_'||r.column_name||'_core',60),
        r.column_name,
        r.ref_table
      );
    end if;
  end loop;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname='parent_children_student_id_fkey'
  ) then
    alter table public.parent_children
      add constraint parent_children_student_id_fkey
      foreign key (student_id) references public.students(id);
  end if;
end $$;

create index if not exists idx_parent_children_student_id
  on public.parent_children(student_id);
drop index if exists public.idx_teacher_classes_teacher_id;

-- برای تمام FKهای تک‌ستونه شاخص پوششی بساز؛ FK بدون index در مقیاس مدرسه کند می‌شود.
do $
declare r record; idxname text;
begin
  for r in
    select n.nspname as schema_name,c.relname as table_name,a.attname as column_name
      from pg_constraint fk
      join pg_class c on c.oid=fk.conrelid
      join pg_namespace n on n.oid=c.relnamespace
      join pg_attribute a on a.attrelid=c.oid and a.attnum=fk.conkey[1]
     where fk.contype='f' and n.nspname='public'
       and array_length(fk.conkey,1)=1
       and not exists (
         select 1 from pg_index i
          where i.indrelid=c.oid and i.indisvalid and i.indisready
            and i.indnkeyatts=1 and i.indkey[0]=fk.conkey[1]
       )
  loop
    idxname := left('idx_'||r.table_name||'_'||r.column_name||'_fk',60);
    execute format('create index if not exists %I on public.%I(%I)',idxname,r.table_name,r.column_name);
  end loop;
end $;

-- teacher_classes already has its canonical teacher_id index.
create index if not exists idx_assignments_student_teacher
  on public.assignments(student_id,teacher_id);
create index if not exists idx_attendance_student_teacher
  on public.attendance(student_id,teacher_id);
create index if not exists idx_grades_student_teacher
  on public.grades(student_id,teacher_id);
create index if not exists idx_student_grades_student_teacher
  on public.student_grades(student_id,teacher_id);
create index if not exists idx_meeting_requests_student_teacher
  on public.meeting_requests(student_id,teacher_id);
create index if not exists idx_teacher_parent_meetings_student_teacher
  on public.teacher_parent_meetings(student_id,teacher_id);

-- خواندن رکوردهای مرتبط برای دانش‌آموز، ولی و دبیر.
do $$
declare r record;
begin
  for r in
    select distinct c.table_name
      from information_schema.columns c
     where c.table_schema='public'
       and c.column_name='student_id'
       and c.data_type in ('integer','bigint')
       and c.table_name <> 'students'
  loop
    execute format('drop policy if exists "frahoosh_student_own_read" on public.%I',r.table_name);
    execute format(
      'create policy "frahoosh_student_own_read" on public.%I for select to authenticated using (student_id=private.frahoosh_current_student_id())',
      r.table_name
    );

    execute format('drop policy if exists "frahoosh_parent_child_read" on public.%I',r.table_name);
    execute format(
      'create policy "frahoosh_parent_child_read" on public.%I for select to authenticated using (exists (select 1 from public.parent_children pc where pc.student_id=public.%I.student_id and private.frahoosh_current_parent_matches(pc.parent_username)))',
      r.table_name,r.table_name
    );

    execute format('drop policy if exists "frahoosh_teacher_student_read" on public.%I',r.table_name);
    execute format(
      'create policy "frahoosh_teacher_student_read" on public.%I for select to authenticated using (private.frahoosh_teacher_can_access_student(student_id))',
      r.table_name
    );
  end loop;

  for r in
    select distinct c.table_name
      from information_schema.columns c
     where c.table_schema='public'
       and c.column_name='teacher_id'
       and c.data_type in ('integer','bigint')
       and c.table_name <> 'teachers'
  loop
    execute format('drop policy if exists "frahoosh_teacher_own_read" on public.%I',r.table_name);
    execute format(
      'create policy "frahoosh_teacher_own_read" on public.%I for select to authenticated using (teacher_id=private.frahoosh_current_teacher_id())',
      r.table_name
    );
  end loop;
end $$;

create or replace function private.frahoosh_can_message_target(p_target text)
returns boolean
language sql
stable
security definer
set search_path=''
as $$
  with me as (
    select a.username,a.email,a.national_code,a.role
      from public.account_settings a
     where a.auth_user_id=auth.uid()
     limit 1
  ), target as (
    select a.username,a.email,a.national_code
      from public.account_settings a
     where lower(coalesce(a.username,''))=lower(coalesce(p_target,''))
        or lower(coalesce(a.email,''))=lower(coalesce(p_target,''))
        or lower(coalesce(a.national_code,''))=lower(coalesce(p_target,''))
     limit 1
  )
  select exists(
    select 1 from me m, target t
    where lower(coalesce(m.role,'')) in (
      'manager','مدیر','مدیریت','educational','معاون آموزشی',
      'executive','معاون اجرایی','cultural','معاون پرورشی','advisor','مشاور'
    )
    or exists (
      select 1 from public.school_relationships sr
       where sr.active=true
         and lower(sr.source_username)=lower(m.username)
         and lower(sr.target_username)=lower(t.username)
    )
    or exists (
      select 1 from public.school_relationships sr
       where sr.active=true
         and lower(sr.target_username)=lower(m.username)
         and lower(sr.source_username)=lower(t.username)
    )
  )
$$;

drop policy if exists "messages authenticated send" on public.messages;
create policy "messages authenticated send"
on public.messages
for insert to authenticated
with check (
  lower(coalesce(sender,''))=lower(coalesce(auth.jwt()->>'email',''))
  and private.frahoosh_can_message_target(receiver)
);
