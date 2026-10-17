-- Reduce database write amplification from the minute-by-minute classroom schedule refresh.
-- The prior function rewrote every schedule row and several class rows on every run,
-- even when no values changed. These indexes support username resolution, active-session
-- lookup, schedule matching, and due-class closing.
create index if not exists idx_account_settings_username_login
  on public.account_settings (username);
create index if not exists idx_account_settings_national_code_login
  on public.account_settings (national_code);
create index if not exists idx_teachers_phone_login
  on public.teachers (phone);
create index if not exists idx_teachers_mobile_login
  on public.teachers (mobile);
create index if not exists idx_teachers_national_code_login
  on public.teachers (national_code);
create index if not exists idx_weekly_schedule_online_class_weekday
  on public.weekly_schedule_entries (online_class_id, weekday);
create index if not exists idx_weekly_schedule_weekday_times
  on public.weekly_schedule_entries (weekday, start_time, end_time);
create index if not exists idx_online_class_sessions_class_id_id
  on public.online_class_sessions (class_id, id desc);
create index if not exists idx_online_classes_due_to_close
  on public.online_classes (end_at)
  where auto_close = true and end_at is not null and status <> 'closed';

create or replace function public.refresh_online_class_statuses()
returns void
language plpgsql
security definer
set search_path = public
as $function$
declare
  v_now timestamptz := now();
  v_today date := (now() at time zone 'Asia/Tehran')::date;
  v_weekday text := extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text;
begin
  -- Only write class rows whose computed schedule/status actually changed.
  update public.online_classes c
  set start_at = ((v_today + w.start_time) at time zone 'Asia/Tehran'),
      end_at = ((v_today + w.end_time) at time zone 'Asia/Tehran'),
      auto_activate = true,
      auto_close = true,
      status = case
        when v_now < ((v_today + w.start_time) at time zone 'Asia/Tehran') then 'pending'
        when v_now >= ((v_today + w.end_time) at time zone 'Asia/Tehran') then c.status
        else 'active'
      end
  from public.weekly_schedule_entries w
  where w.online_class_id = c.id
    and w.weekday = v_weekday
    and w.day_enabled
    and w.start_time is not null
    and w.end_time is not null
    and (
      c.start_at is distinct from ((v_today + w.start_time) at time zone 'Asia/Tehran')
      or c.end_at is distinct from ((v_today + w.end_time) at time zone 'Asia/Tehran')
      or c.auto_activate is distinct from true
      or c.auto_close is distinct from true
      or c.status is distinct from case
        when v_now < ((v_today + w.start_time) at time zone 'Asia/Tehran') then 'pending'
        when v_now >= ((v_today + w.end_time) at time zone 'Asia/Tehran') then c.status
        else 'active'
      end
    );

  -- Preserve existing activation timestamps and avoid rewriting unchanged rows.
  update public.weekly_schedule_entries w
  set activated_at = case
    when w.weekday = v_weekday
      and w.day_enabled
      and v_now >= ((v_today + w.start_time) at time zone 'Asia/Tehran')
      and v_now < ((v_today + w.end_time) at time zone 'Asia/Tehran')
    then coalesce(w.activated_at, v_now)
    else null
  end
  where w.start_time is not null
    and w.end_time is not null
    and w.activated_at is distinct from case
      when w.weekday = v_weekday
        and w.day_enabled
        and v_now >= ((v_today + w.start_time) at time zone 'Asia/Tehran')
        and v_now < ((v_today + w.end_time) at time zone 'Asia/Tehran')
      then coalesce(w.activated_at, v_now)
      else null
    end;

  -- Clear stale schedule windows for classes with no enabled entry today.
  update public.online_classes c
  set start_at = null,
      end_at = null,
      status = case when exists (
        select 1 from public.online_class_sessions s
        where s.class_id = c.id
          and nullif(btrim(coalesce(s.ended_at, '')), '') is null
      ) then 'active' else 'pending' end
  where (c.start_at is not null or c.end_at is not null
      or c.status is distinct from case when exists (
        select 1 from public.online_class_sessions s
        where s.class_id = c.id
          and nullif(btrim(coalesce(s.ended_at, '')), '') is null
      ) then 'active' else 'pending' end)
    and exists (
      select 1 from public.weekly_schedule_entries w
      where w.online_class_id = c.id
        and w.start_time is not null and w.end_time is not null
        and w.day_enabled
    )
    and not exists (
      select 1 from public.weekly_schedule_entries w
      where w.online_class_id = c.id
        and w.weekday = v_weekday
        and w.start_time is not null and w.end_time is not null
        and w.day_enabled
    );

  -- Close overdue sessions even if a class status was already marked closed.
  update public.online_class_sessions s
  set ended_at = v_now::text
  from public.online_classes c
  where c.id = s.class_id
    and c.auto_close
    and c.end_at is not null
    and c.end_at <= v_now
    and nullif(btrim(coalesce(s.ended_at, '')), '') is null;

  update public.online_classes c
  set status = 'closed'
  where c.auto_close
    and c.end_at is not null
    and c.end_at <= v_now
    and c.status is distinct from 'closed';

  update public.online_classes c
  set status = 'active'
  where c.auto_activate
    and c.start_at is not null
    and c.start_at <= v_now
    and (c.end_at is null or c.end_at > v_now)
    and c.status is distinct from 'active'
    and c.status is distinct from 'closed';
end;
$function$;

revoke execute on function public.refresh_online_class_statuses() from public, anon, authenticated;
