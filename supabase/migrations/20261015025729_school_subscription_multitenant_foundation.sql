-- SaaS foundation for Frahoosh: tenant scoping, subscriptions and school-local memberships.
-- Applied to project gtmmllcxhdejwjjnyzrh as migration 20261015025729.
create schema if not exists private;

create table if not exists public.schools (
 id uuid primary key default gen_random_uuid(), slug text not null unique, name text not null,
 school_code text, owner_auth_user_id uuid references auth.users(id) on delete set null,
 status text not null default 'active' check(status in ('active','suspended','archived')),
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create unique index if not exists schools_school_code_unique on public.schools(school_code)
 where school_code is not null and school_code<>'';

create table if not exists public.subscription_plans (
 id uuid primary key default gen_random_uuid(), plan_code text not null unique, name text not null,
 duration_months integer not null check(duration_months>0), student_limit integer not null check(student_limit>0),
 price_irr bigint not null default 0 check(price_irr>=0), is_active boolean not null default true,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.school_subscriptions (
 id uuid primary key default gen_random_uuid(), school_id uuid not null references public.schools(id) on delete restrict,
 plan_id uuid references public.subscription_plans(id) on delete restrict,
 duration_months integer not null default 1 check(duration_months>0),
 student_limit integer not null default 100 check(student_limit>0), price_irr bigint not null default 0 check(price_irr>=0),
 starts_at timestamptz not null default now(), ends_at timestamptz not null,
 grace_days integer not null default 0 check(grace_days between 0 and 30),
 status text not null default 'active' check(status in ('active','past_due','expired','suspended','cancelled')),
 payment_reference text, notes text, created_by uuid references auth.users(id) on delete set null,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 constraint school_subscription_dates_valid check(ends_at>starts_at)
);
create index if not exists school_subscriptions_school_end_idx on public.school_subscriptions(school_id,status,ends_at desc);
create table if not exists public.school_memberships (
 id uuid primary key default gen_random_uuid(), school_id uuid not null references public.schools(id) on delete cascade,
 auth_user_id uuid not null references auth.users(id) on delete cascade,
 role text not null check(role in ('manager','educational','executive','cultural','advisor','teacher','student','parent')),
 is_active boolean not null default true, created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(), unique(school_id,auth_user_id,role)
);
create index if not exists school_memberships_user_idx on public.school_memberships(auth_user_id,is_active);
create table if not exists public.platform_admins (
 auth_user_id uuid primary key references auth.users(id) on delete cascade, created_at timestamptz not null default now()
);

insert into public.schools(slug,name,school_code,status)
select 'frahoosh-default',
 coalesce(nullif((select school_name from public.school_profile order by id limit 1),''),'مدرسهٔ فراهوش'),
 nullif((select school_code from public.school_profile order by id limit 1),''),'active'
on conflict(slug) do nothing;
insert into public.subscription_plans(plan_code,name,duration_months,student_limit,price_irr,is_active)
select 'm'||d.months::text||'_s'||c.capacity::text,d.label||' / حداکثر '||c.capacity::text||' دانش‌آموز',
 d.months,c.capacity,0,true
from (values (1,'یک‌ماهه'),(2,'دوماهه'),(3,'سه‌ماهه'),(6,'شش‌ماهه'),(9,'نه‌ماهه'),(12,'یک‌ساله'),(24,'دوساله')) d(months,label)
cross join (values(100),(200),(300),(500),(700),(1000)) c(capacity)
on conflict(plan_code) do nothing;

alter table public.account_settings add column if not exists tenant_school_id uuid references public.schools(id) on delete restrict;
update public.account_settings set tenant_school_id=(select id from public.schools where slug='frahoosh-default') where tenant_school_id is null;

create or replace function private.frahoosh_is_platform_admin()
returns boolean language sql stable security definer set search_path=''
as $$ select exists(select 1 from public.platform_admins where auth_user_id=auth.uid()); $$;
create or replace function private.frahoosh_current_school_id()
returns uuid language sql stable security definer set search_path=''
as $$ select a.tenant_school_id from public.account_settings a where a.auth_user_id=auth.uid() order by a.updated_at desc nulls last limit 1; $$;
create or replace function private.frahoosh_school_access_active(p_school_id uuid)
returns boolean language sql stable security definer set search_path=''
as $$
 select exists(select 1 from public.school_subscriptions ss join public.schools s on s.id=ss.school_id
 where ss.school_id=p_school_id and s.status='active' and ss.status in ('active','past_due')
 and now()<=ss.ends_at+make_interval(days=>ss.grace_days));
$$;
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
create or replace function private.frahoosh_normalize_school_role(p_role text)
returns text language sql immutable set search_path=''
as $$
 select case lower(trim(coalesce(p_role,'')))
 when 'manager' then 'manager' when 'مدیر' then 'manager' when 'مدیریت' then 'manager'
 when 'educational' then 'educational' when 'معاون آموزشی' then 'educational' when 'معاونت آموزشی' then 'educational'
 when 'executive' then 'executive' when 'معاون اجرایی' then 'executive' when 'معاونت اجرایی' then 'executive'
 when 'cultural' then 'cultural' when 'معاون پرورشی' then 'cultural' when 'معاونت پرورشی' then 'cultural'
 when 'advisor' then 'advisor' when 'مشاور' then 'advisor' when 'مشاوره' then 'advisor'
 when 'teacher' then 'teacher' when 'دبیر' then 'teacher' when 'معلم' then 'teacher'
 when 'student' then 'student' when 'دانش‌آموز' then 'student' when 'دانش آموز' then 'student'
 when 'parent' then 'parent' when 'ولی' then 'parent' when 'اولیا' then 'parent' else 'student' end;
$$;

do $$
declare v_school_id uuid; r record; v_constraint text; v_index text; v_predicate text;
begin
 select id into v_school_id from public.schools where slug='frahoosh-default';
 for r in select c.relname table_name,c.relrowsecurity rls_enabled from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='public' and c.relkind in ('r','p')
   and c.relname not in ('schools','subscription_plans','school_subscriptions','school_memberships','platform_admins')
 loop
  execute format('alter table public.%I add column if not exists tenant_school_id uuid',r.table_name);
  execute format('update public.%I set tenant_school_id=$1 where tenant_school_id is null',r.table_name) using v_school_id;
  v_constraint:=left('fk_'||r.table_name||'_tenant_school_id',63);
  if not exists(select 1 from pg_constraint where conrelid=format('public.%I',r.table_name)::regclass and conname=v_constraint) then
   execute format('alter table public.%I add constraint %I foreign key(tenant_school_id) references public.schools(id) on delete restrict not valid',r.table_name,v_constraint);
  end if;
  v_index:=left('ix_'||r.table_name||'_tenant_school_id',63);
  execute format('create index if not exists %I on public.%I(tenant_school_id)',v_index,r.table_name);
  if r.rls_enabled then
   execute format('drop policy if exists frahoosh_tenant_scope on public.%I',r.table_name);
   if r.table_name in ('account_settings','school_profile') then
    v_predicate:='(tenant_school_id=private.frahoosh_current_school_id() OR private.frahoosh_is_platform_admin())';
   else
    v_predicate:='(tenant_school_id=private.frahoosh_current_school_id() AND private.frahoosh_school_access_active(tenant_school_id))';
   end if;
   execute format('create policy frahoosh_tenant_scope on public.%I as restrictive for all to authenticated using (%s) with check (%s)',r.table_name,v_predicate,v_predicate);
  end if;
  execute format('drop trigger if exists frahoosh_set_tenant_school on public.%I',r.table_name);
  execute format('create trigger frahoosh_set_tenant_school before insert or update on public.%I for each row execute function private.frahoosh_set_tenant_school()',r.table_name);
 end loop;
end; $$;

create or replace function private.frahoosh_current_school_id()
returns uuid language plpgsql stable security definer set search_path=''
as $$
declare v_school_id uuid;
begin
 select a.tenant_school_id into v_school_id from public.account_settings a where a.auth_user_id=auth.uid() order by a.updated_at desc nulls last limit 1;
 if v_school_id is null then
  select oc.tenant_school_id into v_school_id from public.guest_online_members gm join public.online_classes oc on oc.id::text=gm.class_id::text
  where gm.user_id=auth.uid() and gm.left_at is null order by gm.joined_at desc limit 1;
 end if;
 return v_school_id;
end; $$;

create or replace function private.frahoosh_sync_school_membership()
returns trigger language plpgsql security definer set search_path=''
as $$
declare v_role text;
begin
 if tg_op='UPDATE' and old.auth_user_id is not null and old.tenant_school_id is not null then
  update public.school_memberships set is_active=false,updated_at=now() where auth_user_id=old.auth_user_id and school_id=old.tenant_school_id;
 end if;
 if new.auth_user_id is not null and new.tenant_school_id is not null then
  v_role:=private.frahoosh_normalize_school_role(new.role);
  insert into public.school_memberships(school_id,auth_user_id,role,is_active,updated_at)
  values(new.tenant_school_id,new.auth_user_id,v_role,true,now())
  on conflict(school_id,auth_user_id,role) do update set is_active=true,updated_at=now();
 end if;
 return new;
end; $$;
drop trigger if exists frahoosh_sync_school_membership on public.account_settings;
create trigger frahoosh_sync_school_membership after insert or update of auth_user_id,role,tenant_school_id
on public.account_settings for each row execute function private.frahoosh_sync_school_membership();

create or replace function private.frahoosh_fill_subscription_from_plan()
returns trigger language plpgsql set search_path=''
as $$
declare p public.subscription_plans%rowtype;
begin
 if new.plan_id is not null then
  select * into p from public.subscription_plans where id=new.plan_id;
  if not found then raise exception 'طرح اشتراک انتخاب‌شده معتبر نیست.' using errcode='23503'; end if;
  if not p.is_active and (tg_op='INSERT' or new.plan_id is distinct from old.plan_id) then raise exception 'طرح اشتراک غیرفعال است.' using errcode='23514'; end if;
  new.duration_months:=p.duration_months; new.student_limit:=p.student_limit; new.price_irr:=p.price_irr;
 end if;
 if new.starts_at is null then new.starts_at:=now(); end if;
 if new.ends_at is null then new.ends_at:=new.starts_at+make_interval(months=>new.duration_months); end if;
 new.updated_at:=now(); return new;
end; $$;
drop trigger if exists frahoosh_subscription_plan_defaults on public.school_subscriptions;
create trigger frahoosh_subscription_plan_defaults before insert or update of plan_id,starts_at,ends_at,duration_months,student_limit,price_irr
on public.school_subscriptions for each row execute function private.frahoosh_fill_subscription_from_plan();

create or replace function private.frahoosh_enforce_student_limit()
returns trigger language plpgsql security definer set search_path=''
as $$
declare v_limit integer; v_count bigint;
begin
 if new.tenant_school_id is null then raise exception 'مدرسهٔ دانش‌آموز مشخص نیست.' using errcode='42501'; end if;
 select ss.student_limit into v_limit from public.school_subscriptions ss
 where ss.school_id=new.tenant_school_id and ss.status in ('active','past_due') and now()<=ss.ends_at+make_interval(days=>ss.grace_days)
 order by ss.ends_at desc limit 1;
 if v_limit is null then raise exception 'اشتراک فعال مدرسه وجود ندارد یا منقضی شده است.' using errcode='42501'; end if;
 select count(*) into v_count from public.students s where s.tenant_school_id=new.tenant_school_id and (tg_op='INSERT' or s.id is distinct from new.id);
 if v_count>=v_limit then raise exception 'ظرفیت اشتراک مدرسه تکمیل شده است (حداکثر % دانش‌آموز).',v_limit using errcode='23514'; end if;
 return new;
end; $$;
drop trigger if exists frahoosh_z_enforce_student_limit on public.students;
create trigger frahoosh_z_enforce_student_limit before insert or update on public.students for each row execute function private.frahoosh_enforce_student_limit();

insert into public.school_subscriptions(school_id,plan_id,duration_months,student_limit,price_irr,starts_at,ends_at,grace_days,status,notes)
select s.id,null,120,300,0,now(),now()+interval '10 years',0,'active','Legacy school entitlement; replace with a paid plan when onboarding billing is configured.'
from public.schools s where s.slug='frahoosh-default'
and not exists(select 1 from public.school_subscriptions ss where ss.school_id=s.id);
insert into public.platform_admins(auth_user_id)
select a.auth_user_id from public.account_settings a where lower(coalesce(a.role,'')) in ('manager','مدیر','مدیریت') and a.auth_user_id is not null
on conflict(auth_user_id) do nothing;
insert into public.school_memberships(school_id,auth_user_id,role,is_active)
select a.tenant_school_id,a.auth_user_id,private.frahoosh_normalize_school_role(a.role),true
from public.account_settings a where a.tenant_school_id is not null and a.auth_user_id is not null
on conflict(school_id,auth_user_id,role) do update set is_active=true,updated_at=now();

alter table public.schools enable row level security;
alter table public.subscription_plans enable row level security;
alter table public.school_subscriptions enable row level security;
alter table public.school_memberships enable row level security;
alter table public.platform_admins enable row level security;
grant select,insert,update,delete on public.schools,public.subscription_plans,public.school_subscriptions,public.school_memberships,public.platform_admins to authenticated;

drop policy if exists schools_platform_admin_all on public.schools;
create policy schools_platform_admin_all on public.schools for all to authenticated using(private.frahoosh_is_platform_admin()) with check(private.frahoosh_is_platform_admin());
drop policy if exists schools_member_read on public.schools;
create policy schools_member_read on public.schools for select to authenticated using(id=private.frahoosh_current_school_id());

drop policy if exists subscription_plans_platform_admin_all on public.subscription_plans;
create policy subscription_plans_platform_admin_all on public.subscription_plans for all to authenticated using(private.frahoosh_is_platform_admin()) with check(private.frahoosh_is_platform_admin());
drop policy if exists subscription_plans_active_read on public.subscription_plans;
create policy subscription_plans_active_read on public.subscription_plans for select to authenticated using(is_active=true);

drop policy if exists school_subscriptions_platform_admin_all on public.school_subscriptions;
create policy school_subscriptions_platform_admin_all on public.school_subscriptions for all to authenticated using(private.frahoosh_is_platform_admin()) with check(private.frahoosh_is_platform_admin());
drop policy if exists school_subscriptions_member_read on public.school_subscriptions;
create policy school_subscriptions_member_read on public.school_subscriptions for select to authenticated using(school_id=private.frahoosh_current_school_id());

drop policy if exists school_memberships_platform_admin_all on public.school_memberships;
create policy school_memberships_platform_admin_all on public.school_memberships for all to authenticated using(private.frahoosh_is_platform_admin()) with check(private.frahoosh_is_platform_admin());
drop policy if exists school_memberships_manager_all on public.school_memberships;
create policy school_memberships_manager_all on public.school_memberships for all to authenticated
using(school_id=private.frahoosh_current_school_id() and private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check(school_id=private.frahoosh_current_school_id() and private.frahoosh_current_role() in ('manager','مدیر','مدیریت')
 and exists(select 1 from public.account_settings a where a.auth_user_id=school_memberships.auth_user_id and a.tenant_school_id=school_memberships.school_id));
drop policy if exists school_memberships_member_read on public.school_memberships;
create policy school_memberships_member_read on public.school_memberships for select to authenticated using(school_id=private.frahoosh_current_school_id());

drop policy if exists platform_admins_self_read on public.platform_admins;
create policy platform_admins_self_read on public.platform_admins for select to authenticated using(auth_user_id=auth.uid() or private.frahoosh_is_platform_admin());
drop policy if exists platform_admins_admin_write on public.platform_admins;
create policy platform_admins_admin_write on public.platform_admins for all to authenticated using(private.frahoosh_is_platform_admin()) with check(private.frahoosh_is_platform_admin());

revoke all on function private.frahoosh_is_platform_admin() from public,anon;
revoke all on function private.frahoosh_current_school_id() from public,anon;
revoke all on function private.frahoosh_school_access_active(uuid) from public,anon;
grant execute on function private.frahoosh_is_platform_admin() to authenticated;
grant execute on function private.frahoosh_current_school_id() to authenticated;
grant execute on function private.frahoosh_school_access_active(uuid) to authenticated;
