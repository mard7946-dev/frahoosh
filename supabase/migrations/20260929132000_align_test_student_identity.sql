-- Align the test student's personal identity with the agreed test account name.
begin;
update public.students
set first_name='محمد', last_name='', class_name='۸/۱'
where id=2;
commit;
