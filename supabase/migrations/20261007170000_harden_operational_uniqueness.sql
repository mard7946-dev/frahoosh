-- Production hardening for operational school workflows.
-- Online Class, Online Exam, and Meetings are intentionally untouched.

create unique index if not exists attendance_batches_one_submission_per_slot
on public.attendance_batches (teacher_id, class_name, subject, period, attendance_date)
where status <> 'rejected';

create unique index if not exists attendance_one_student_per_batch
on public.attendance (batch_id, student_id);

create unique index if not exists activity_registrations_one_student_per_activity
on public.activity_registrations (activity_id, student_id);

create unique index if not exists student_council_one_registration_per_year
on public.student_council (student_id, election_year);

create unique index if not exists basij_one_registration_per_student
on public.basij_registration (student_id);

create unique index if not exists school_ally_one_registration_per_student
on public.school_ally (student_id);

create unique index if not exists school_mayor_one_registration_per_student
on public.school_mayor (student_id);

revoke all on function public.frahoosh_assign_certificate_registration() from anon, authenticated;
