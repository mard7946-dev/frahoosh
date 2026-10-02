-- Remove five confirmed legacy tables that have zero rows, no code/RPC/view/trigger usage,
-- and no foreign-key dependents. Active equivalents remain:
-- payment_offers/payment_config? payment_config is legacy and unused; payment_offers is canonical.
drop table if exists public.frahoosh_events;
drop table if exists public.teacher_messages;
drop table if exists public.app_roles;
drop table if exists public.message_inbox;
drop table if exists public.payment_config;

update public.students
set email='amirkiyanori.student@frahoosh.test'
where national_code='1234567895';

update public.teachers
set email='reza.teacher@frahoosh.test'
where national_code='1234567894';
