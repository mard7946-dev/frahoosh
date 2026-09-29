-- Normalize the official Frahoosh test identities to canonical national-code usernames.
-- This prevents stale email-based relationship rows from breaking recipient lists
-- and keeps معاون پرورشی (cultural) distinct from مشاور (advisor).

update public.account_settings
set preferences = jsonb_set(
  coalesce(preferences, '{}'::jsonb),
  '{role}',
  '"cultural"'::jsonb,
  true
)
where national_code = '1234567893';

update public.school_relationships
set source_username = case lower(source_username)
  when 'amirhossein.ejraei@frahoosh.test' then '1234567891'
  when 'mohammadreza.amoozeshi@frahoosh.test' then '1234567892'
  when 'adel.kalhor@frahoosh.test' then '1234567893'
  when 'reza.mardaneh@frahoosh.test' then '1234567894'
  when 'hassan.mohammadi@frahoosh.test' then '1234567895'
  when 'hassan.mardaneh@frahoosh.test' then '0053409531'
  else source_username
end,
target_username = case lower(target_username)
  when 'amirhossein.ejraei@frahoosh.test' then '1234567891'
  when 'mohammadreza.amoozeshi@frahoosh.test' then '1234567892'
  when 'adel.kalhor@frahoosh.test' then '1234567893'
  when 'reza.mardaneh@frahoosh.test' then '1234567894'
  when 'hassan.mohammadi@frahoosh.test' then '1234567895'
  when 'hassan.mardaneh@frahoosh.test' then '0053409531'
  else target_username
end;

update public.school_relationships
set source_role = case source_username
  when '1234567891' then 'executive'
  when '1234567892' then 'educational'
  when '1234567893' then 'cultural'
  when '1234567894' then 'teacher'
  when '1234567895' then 'student'
  when '0053409531' then 'manager'
  else source_role
end,
target_role = case target_username
  when '1234567891' then 'executive'
  when '1234567892' then 'educational'
  when '1234567893' then 'cultural'
  when '1234567894' then 'teacher'
  when '1234567895' then 'student'
  when '0053409531' then 'manager'
  else target_role
end
where source_username in ('1234567891','1234567892','1234567893','1234567894','1234567895','0053409531')
   or target_username in ('1234567891','1234567892','1234567893','1234567894','1234567895','0053409531');
