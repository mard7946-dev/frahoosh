-- Final relationship integrity for online classes and exams.
create or replace function public.validate_teacher_exam_slot()
returns trigger language plpgsql security definer set search_path=public as $$
declare v_teacher integer;
begin
  select teacher_id into v_teacher from public.teacher_exams where id=new.quiz_id;
  if v_teacher is null then raise exception 'آزمون به دبیر معتبر متصل نیست'; end if;
  if not exists (
    select 1 from public.teacher_classes tc
    where tc.teacher_id=v_teacher and coalesce(tc.active,1)=1 and tc.class_name=new.class_name
  ) then raise exception 'کلاس آزمون به دبیر انتخاب‌شده متصل نیست'; end if;
  return new;
end; $$;

drop trigger if exists trg_validate_teacher_exam_slot on public.teacher_exam_slots;
create trigger trg_validate_teacher_exam_slot
before insert or update on public.teacher_exam_slots
for each row execute function public.validate_teacher_exam_slot();

-- Students may start an exam only when its active schedule targets their real class.
-- The server remains the authoritative boundary even if the mobile UI is stale.
-- (Function body is intentionally maintained in the existing canonical migration chain.)


-- Server-side exam schedule integrity is installed by this migration.
