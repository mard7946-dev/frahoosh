-- Scheduled classroom quizzes with up to four typed questions.
alter table public.smart_board_quizzes
  add column if not exists publish_at timestamptz,
  add column if not exists ends_at timestamptz,
  add column if not exists questions jsonb;

-- Existing one-question quizzes remain readable through the legacy columns.
alter table public.smart_board_quizzes
  drop constraint if exists smart_board_quizzes_schedule_order_check;
alter table public.smart_board_quizzes
  add constraint smart_board_quizzes_schedule_order_check
  check (publish_at is null or ends_at is null or ends_at > publish_at);

create index if not exists smart_board_quizzes_class_schedule_idx
  on public.smart_board_quizzes(class_id, publish_at, ends_at)
  where is_published = true;

comment on column public.smart_board_quizzes.questions is
  'Optional JSON array of up to four classroom quiz questions; legacy question/option columns remain supported.';

alter table public.smart_board_quizzes
  drop constraint if exists smart_board_quizzes_questions_count_check;
alter table public.smart_board_quizzes
  add constraint smart_board_quizzes_questions_count_check
  check (
    case
      when questions is null then true
      when jsonb_typeof(questions) = 'array'
        then jsonb_array_length(questions) between 1 and 4
      else false
    end
  );

-- Enforce the publication window at the database boundary for student/guest reads.
drop policy if exists smart_board_quizzes_guest_class_read on public.smart_board_quizzes;
create policy smart_board_quizzes_guest_class_read
on public.smart_board_quizzes for select to authenticated
using (
  is_published = true
  and (publish_at is null or publish_at <= now())
  and (ends_at is null or ends_at > now())
  and exists (
    select 1 from public.guest_online_members g
    where g.class_id = smart_board_quizzes.class_id
      and g.user_id = (select auth.uid())
      and g.role = 'guest'
      and g.left_at is null
  )
  and exists (
    select 1 from public.online_class_sessions s
    where s.class_id = smart_board_quizzes.class_id and s.ended_at is null
  )
);

drop policy if exists smart_board_quizzes_student_roster_read on public.smart_board_quizzes;
create policy smart_board_quizzes_student_roster_read
on public.smart_board_quizzes for select to authenticated
using (
  is_published = true
  and (publish_at is null or publish_at <= now())
  and (ends_at is null or ends_at > now())
  and exists (
    select 1
    from public.students st
    join public.online_classes c on c.id = smart_board_quizzes.class_id
    where st.id = (select private.frahoosh_current_student_id())
      and replace(replace(regexp_replace(lower(btrim(st.class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(btrim(c.class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
  )
  and exists (
    select 1 from public.online_class_sessions s
    where s.class_id = smart_board_quizzes.class_id and s.ended_at is null
  )
);
