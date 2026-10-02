-- Frahoosh: close anonymous execution paths for security-definer operational functions.
-- Login lookup remains anonymously callable because national-code login resolves the
-- Auth email before a session exists. Operational writes must never be callable by anon.

revoke all on function public.create_online_class_with_members(
  integer,text,text,text,text,text,text
) from anon;

revoke all on function public.validate_teacher_exam_slot() from public;
revoke all on function public.validate_teacher_exam_slot() from anon;
revoke all on function public.validate_teacher_exam_slot() from authenticated;

grant execute on function public.create_online_class_with_members(
  integer,text,text,text,text,text,text
) to authenticated;

-- Keep trigger execution owned by PostgreSQL; it is not an RPC endpoint.
