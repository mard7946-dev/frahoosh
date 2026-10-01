-- Keep every authenticated school account on the same canonical
-- profile path used by the manager account.
--
-- The mobile client authenticates against auth.users, then resolves the
-- school identity through account_settings/public.users.  A newly created
-- Auth account must therefore never be left without its canonical users row.

create or replace function public.sync_account_settings_to_user(
    p_username text,
    p_email text default null,
    p_role text default 'student',
    p_display_name text default null,
    p_national_code text default null,
    p_linked_student_id integer default null,
    p_linked_teacher_id integer default null,
    p_linked_staff_id integer default null
)
returns public.users
language plpgsql
security definer
set search_path = public
as $$
declare
    v_row public.users;
    v_id integer;
    v_username text;
    v_role text;
begin
    v_username := nullif(trim(coalesce(p_username, '')), '');
    if v_username is null then
        v_username := nullif(trim(coalesce(p_national_code, '')), '');
    end if;
    if v_username is null then
        v_username := lower(nullif(trim(coalesce(p_email, '')), ''));
    end if;
    if v_username is null then
        raise exception 'canonical school username is required';
    end if;

    v_role := lower(trim(coalesce(p_role, 'student')));

    select id into v_id
    from public.users
    where username = v_username
    limit 1;

    if v_id is null and p_email is not null then
        select id into v_id
        from public.users
        where lower(display_name) = lower(trim(coalesce(p_display_name, '')))
        limit 1;
    end if;

    if v_id is null then
        select coalesce(max(id), 0) + 1 into v_id from public.users;
    end if;

    insert into public.users (
        id, username, password, role, permissions,
        linked_student_id, linked_teacher_id, linked_staff_id, display_name
    )
    values (
        v_id, v_username, null, v_role, '{"*":true}',
        p_linked_student_id, p_linked_teacher_id, p_linked_staff_id,
        coalesce(nullif(trim(p_display_name), ''), v_username)
    )
    on conflict (id) do update set
        username = excluded.username,
        role = excluded.role,
        permissions = excluded.permissions,
        linked_student_id = excluded.linked_student_id,
        linked_teacher_id = excluded.linked_teacher_id,
        linked_staff_id = excluded.linked_staff_id,
        display_name = excluded.display_name
    returning * into v_row;

    return v_row;
end;
$$;

create or replace function public.sync_auth_account_to_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    v_settings record;
    v_national_code text;
    v_role text;
    v_username text;
begin
    select *
    into v_settings
    from public.account_settings
    where lower(coalesce(email, '')) = lower(coalesce(new.email, ''))
    order by updated_at desc nulls last
    limit 1;

    v_national_code := nullif(trim(coalesce(v_settings.national_code, '')), '');
    v_role := lower(trim(coalesce(v_settings.role, 'student')));
    v_username := coalesce(
        nullif(trim(coalesce(v_settings.username, '')), ''),
        v_national_code,
        lower(nullif(trim(coalesce(new.email, '')), ''))
    );

    if v_username is null then
        return new;
    end if;

    perform public.sync_account_settings_to_user(
        v_username,
        new.email,
        v_role,
        coalesce(v_settings.display_name, new.raw_user_meta_data ->> 'full_name', new.email),
        v_national_code,
        nullif(v_settings.preferences::jsonb ->> 'linked_student_id', '')::integer,
        nullif(v_settings.preferences::jsonb ->> 'linked_teacher_id', '')::integer,
        nullif(v_settings.preferences::jsonb ->> 'linked_staff_id', '')::integer
    );

    update public.account_settings
    set auth_user_id = new.id,
        updated_at = current_timestamp::text
    where lower(coalesce(email, '')) = lower(coalesce(new.email, ''));

    return new;
exception
    when others then
        -- Authentication must not fail because optional school-profile
        -- enrichment failed. The profile is repaired on the next login.
        raise notice 'Frahoosh auth profile sync skipped: %', sqlerrm;
        return new;
end;
$$;

drop trigger if exists trg_sync_auth_account_to_user on auth.users;
create trigger trg_sync_auth_account_to_user
after insert or update of email, raw_user_meta_data on auth.users
for each row execute function public.sync_auth_account_to_user();

-- When account_settings is created/updated after Auth (the common onboarding
-- order), synchronize it immediately as well.
create or replace function public.sync_account_settings_row_to_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    perform public.sync_account_settings_to_user(
        new.username,
        new.email,
        new.role,
        new.display_name,
        new.national_code,
        nullif(new.preferences::jsonb ->> 'linked_student_id', '')::integer,
        nullif(new.preferences::jsonb ->> 'linked_teacher_id', '')::integer,
        nullif(new.preferences::jsonb ->> 'linked_staff_id', '')::integer
    );
    return new;
exception
    when others then
        raise notice 'Frahoosh account_settings sync skipped: %', sqlerrm;
        return new;
end;
$$;

drop trigger if exists trg_sync_account_settings_row_to_user on public.account_settings;
create trigger trg_sync_account_settings_row_to_user
after insert or update of username, email, role, display_name, national_code, preferences
on public.account_settings
for each row execute function public.sync_account_settings_row_to_user();

revoke all on function public.sync_account_settings_to_user(text,text,text,text,text,integer,integer,integer) from public;
revoke all on function public.sync_auth_account_to_user() from public;
revoke all on function public.sync_account_settings_row_to_user() from public;
grant execute on function public.sync_auth_account_to_user() to service_role;

-- Repair every already-existing account_settings row immediately.
do $$
declare
    r record;
begin
    for r in
        select username, email, role, display_name, national_code, preferences
        from public.account_settings
    loop
        perform public.sync_account_settings_to_user(
            r.username,
            r.email,
            r.role,
            r.display_name,
            r.national_code,
            nullif(r.preferences::jsonb ->> 'linked_student_id', '')::integer,
            nullif(r.preferences::jsonb ->> 'linked_teacher_id', '')::integer,
            nullif(r.preferences::jsonb ->> 'linked_staff_id', '')::integer
        );
    end loop;
end $$;


-- Canonical profile RPCs used by the mobile client after Auth succeeds.
-- They deliberately read the same account_settings -> users path as the
-- manager account, so role resolution cannot silently fall back to student.
create or replace function public.lookup_login_profile_by_email(p_email text)
returns table(
    username text,
    role text,
    display_name text,
    national_code text,
    linked_student_id integer,
    linked_teacher_id integer,
    linked_staff_id integer
)
language sql
security definer
set search_path = public
stable
as $$
    select
        u.username,
        u.role,
        u.display_name,
        a.national_code,
        u.linked_student_id,
        u.linked_teacher_id,
        u.linked_staff_id
    from public.account_settings a
    join public.users u
      on lower(trim(u.username)) =
         lower(trim(coalesce(nullif(a.national_code,''), a.username)))
    where lower(trim(coalesce(a.email,''))) = lower(trim(coalesce(p_email,'')))
    limit 1;
$$;

create or replace function public.lookup_login_profile_by_national_code(p_national_code text)
returns table(
    username text,
    role text,
    display_name text,
    national_code text,
    linked_student_id integer,
    linked_teacher_id integer,
    linked_staff_id integer
)
language sql
security definer
set search_path = public
stable
as $$
    select
        u.username,
        u.role,
        u.display_name,
        a.national_code,
        u.linked_student_id,
        u.linked_teacher_id,
        u.linked_staff_id
    from public.account_settings a
    join public.users u
      on lower(trim(u.username)) =
         lower(trim(coalesce(nullif(a.national_code,''), a.username)))
    where regexp_replace(coalesce(a.national_code,''),'[^0-9]','','g')
        = regexp_replace(coalesce(p_national_code,''),'[^0-9]','','g')
    limit 1;
$$;

revoke all on function public.lookup_login_profile_by_email(text) from public;
revoke all on function public.lookup_login_profile_by_national_code(text) from public;
grant execute on function public.lookup_login_profile_by_email(text) to authenticated;
grant execute on function public.lookup_login_profile_by_national_code(text) to authenticated;
