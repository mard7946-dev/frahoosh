update public.students s
set email=a.email
from public.account_settings a
where a.role='student' and a.national_code=s.national_code
  and coalesce(a.email,'')<>'' and s.email is distinct from a.email;

update public.teachers t
set email=a.email
from public.account_settings a
where a.role='teacher' and a.national_code=t.national_code
  and coalesce(a.email,'')<>'' and t.email is distinct from a.email;

insert into public.staff(first_name,last_name,role,employee_code,national_code,employment_status,work_experience)
select 'حسن','مردانه جهان تیغ','مدیر','TEST-001','0053409531','فعال','حساب مدیریت فراهوش'
where not exists (select 1 from public.staff where national_code='0053409531');

update public.users u
set linked_staff_id=s.id
from public.staff s
where u.username='0053409531' and s.national_code='0053409531';
