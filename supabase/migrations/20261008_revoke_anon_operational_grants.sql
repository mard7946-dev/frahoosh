-- Frahoosh operational API hardening
-- The Android client authenticates before touching school data.
-- RLS remains the authorization boundary; anon must not have table privileges.
do $$
declare
  t text;
begin
  foreach t in array array[
    'grades',
    'weekly_schedule_entries',
    'students',
    'attendance',
    'attendance_batches',
    'discipline_records',
    'messages',
    'counseling_records',
    'executive_operations',
    'certificate_requests',
    'finance_transactions',
    'module_activations'
  ] loop
    execute format('revoke all on table public.%I from anon', t);
    execute format('grant select, insert, update, delete on table public.%I to authenticated', t);
  end loop;
end $$;
