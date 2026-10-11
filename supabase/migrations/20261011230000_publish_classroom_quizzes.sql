alter table public.smart_board_quizzes
  add column if not exists is_published boolean not null default true;

alter table public.smart_board_quizzes
  add column if not exists published_at timestamptz not null default now();

update public.smart_board_quizzes
set is_published = true
where is_published is null;
