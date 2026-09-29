-- Finalize the agreed test identities shown in the Supabase/Auth screenshot.
begin;

update public.users
set display_name='محمد'
where username='1234567895';

update public.account_settings
set display_name='محمد',
    preferences=coalesce(preferences,'{}'::jsonb)||jsonb_build_object('role','student','test_user',true)
where username='1234567895';

update public.account_settings
set display_name='عادل کلهر',
    preferences=coalesce(preferences,'{}'::jsonb)||jsonb_build_object('role','cultural','test_user',true)
where username='1234567893';

commit;
