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
