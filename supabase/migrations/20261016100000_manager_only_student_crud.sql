-- Keep the canonical student directory editable only by the school manager.
-- Staff may continue reading student records through the existing SELECT policies.
-- The separate approved roster/source used for student validation is not changed.
drop policy if exists "staff students insert" on public.students;
drop policy if exists "staff students update" on public.students;
drop policy if exists "staff students delete" on public.students;
