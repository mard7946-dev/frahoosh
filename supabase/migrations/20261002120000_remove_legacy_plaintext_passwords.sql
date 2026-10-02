-- Legacy users table must never retain authentication passwords.
-- Supabase Auth is the sole password store.
update public.users
set password = null
where password is not null;

comment on column public.users.password is
'Deprecated legacy field. Must remain NULL; authentication passwords are stored only by Supabase Auth.';
