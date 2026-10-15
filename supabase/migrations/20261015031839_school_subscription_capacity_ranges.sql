alter table public.subscription_plans add column if not exists student_min integer not null default 1;
alter table public.school_subscriptions add column if not exists student_min integer not null default 1;

update public.subscription_plans
set student_min=case student_limit when 100 then 1 when 200 then 101 when 300 then 201 when 500 then 301 when 700 then 501 when 1000 then 701 else 1 end,
    name=split_part(name,' / ',1)||' / '||
      case student_limit
       when 100 then '۱ تا ۱۰۰'
       when 200 then '۱۰۱ تا ۲۰۰'
       when 300 then '۲۰۱ تا ۳۰۰'
       when 500 then '۳۰۱ تا ۵۰۰'
       when 700 then '۵۰۱ تا ۷۰۰'
       when 1000 then '۷۰۱ تا ۱۰۰۰'
       else '۱ تا '||student_limit::text
      end||' دانش‌آموز';

update public.school_subscriptions ss
set student_min=coalesce((select p.student_min from public.subscription_plans p where p.id=ss.plan_id),1);

do $$
begin
 if not exists(select 1 from pg_constraint where conname='subscription_plan_capacity_range_check' and conrelid='public.subscription_plans'::regclass) then
  alter table public.subscription_plans add constraint subscription_plan_capacity_range_check check(student_limit>=student_min);
 end if;
 if not exists(select 1 from pg_constraint where conname='school_subscription_capacity_range_check' and conrelid='public.school_subscriptions'::regclass) then
  alter table public.school_subscriptions add constraint school_subscription_capacity_range_check check(student_limit>=student_min);
 end if;
end $$;

create or replace function private.frahoosh_fill_subscription_from_plan()
returns trigger language plpgsql set search_path=''
as $$
declare p public.subscription_plans%rowtype;
begin
 if new.plan_id is not null then
  select * into p from public.subscription_plans where id=new.plan_id;
  if not found then raise exception 'طرح اشتراک انتخاب‌شده معتبر نیست.' using errcode='23503'; end if;
  if not p.is_active and (tg_op='INSERT' or new.plan_id is distinct from old.plan_id) then
   raise exception 'طرح اشتراک غیرفعال است.' using errcode='23514';
  end if;
  if p.price_irr<=0 and new.status in ('active','past_due') then
   raise exception 'قیمت طرح اشتراک هنوز تعیین نشده است؛ ابتدا قیمت را در مدیریت طرح‌ها ثبت کنید.' using errcode='23514';
  end if;
  new.duration_months:=p.duration_months;
  new.student_min:=p.student_min;
  new.student_limit:=p.student_limit;
  new.price_irr:=p.price_irr;
 end if;
 if new.starts_at is null then new.starts_at:=now(); end if;
 if new.ends_at is null then new.ends_at:=new.starts_at+make_interval(months=>new.duration_months); end if;
 new.updated_at:=now();
 return new;
end; $$;
drop trigger if exists frahoosh_subscription_plan_defaults on public.school_subscriptions;
create trigger frahoosh_subscription_plan_defaults before insert or update of plan_id,starts_at,ends_at,duration_months,student_min,student_limit,price_irr
on public.school_subscriptions for each row execute function private.frahoosh_fill_subscription_from_plan();

create or replace function private.frahoosh_validate_subscription_capacity()
returns trigger language plpgsql security definer set search_path=''
as $$
declare v_count bigint;
begin
 if new.status in ('active','past_due') then
  select count(*) into v_count from public.students s where s.tenant_school_id=new.school_id;
  if v_count>new.student_limit then
   raise exception 'تعداد دانش‌آموزان فعلی (%) از ظرفیت طرح انتخابی (%) بیشتر است.',v_count,new.student_limit using errcode='23514';
  end if;
 end if;
 return new;
end; $$;
drop trigger if exists frahoosh_subscription_capacity_check on public.school_subscriptions;
drop trigger if exists zz_frahoosh_subscription_capacity_check on public.school_subscriptions;
create trigger zz_frahoosh_subscription_capacity_check before insert or update on public.school_subscriptions
for each row execute function private.frahoosh_validate_subscription_capacity();
