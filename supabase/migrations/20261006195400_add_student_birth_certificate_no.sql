-- Store the student's official birth-certificate number for executive certificates.
alter table public.students
  add column if not exists birth_certificate_no text;