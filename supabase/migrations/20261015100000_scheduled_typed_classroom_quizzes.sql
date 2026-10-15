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
