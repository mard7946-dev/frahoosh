-- Backend defaults for operational CRUD forms.
-- Prevents valid user forms from failing solely because audit/routing columns
-- were NOT NULL without a database default.

alter table public.discipline_records alter column created_at set default now();
alter table public.message_targets alter column created_at set default now();
alter table public.message_targets alter column target_type set default 'role';
alter table public.finance_accounts alter column title set default 'حساب مدرسه';
alter table public.payment_offers alter column target_type set default 'school';
alter table public.survey_responses alter column submitted_at set default now();
alter table public.discipline_items alter column created_at set default now();
alter table public.discipline_settings alter column updated_at set default now();
