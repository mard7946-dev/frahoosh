-- Frahoosh: connect the current demo school relationships.
-- Idempotent and role-driven; no account identifiers are hard-coded.

BEGIN;

WITH student AS (
  SELECT id
  FROM public.students
  ORDER BY id
  LIMIT 1
),
parent AS (
  SELECT username
  FROM public.account_settings
  WHERE role = 'parent'
  ORDER BY username
  LIMIT 1
)
INSERT INTO public.parent_children (parent_username, student_id)
SELECT parent.username, student.id
FROM parent CROSS JOIN student
WHERE NOT EXISTS (
  SELECT 1
  FROM public.parent_children pc
  WHERE pc.parent_username = parent.username
    AND pc.student_id = student.id
);

DELETE FROM public.parent_children pc
WHERE NOT EXISTS (
  SELECT 1
  FROM public.account_settings a
  WHERE a.role = 'parent'
    AND a.username = pc.parent_username
);

WITH student AS (
  SELECT id, class_name, grade
  FROM public.students
  ORDER BY id
  LIMIT 1
),
teacher AS (
  SELECT u.linked_teacher_id AS teacher_id, u.display_name AS teacher_name
  FROM public.users u
  WHERE u.role = 'teacher'
    AND u.linked_teacher_id IS NOT NULL
  ORDER BY u.id
  LIMIT 1
),
subject AS (
  SELECT COALESCE(t.subject, '') AS subject
  FROM public.teachers t
  WHERE t.id = (SELECT teacher_id FROM teacher)
  LIMIT 1
)
INSERT INTO public.teacher_classes
  (teacher_id, teacher_name, subject, grade, class_name, active)
SELECT
  teacher.teacher_id,
  teacher.teacher_name,
  subject.subject,
  student.grade,
  student.class_name,
  1
FROM student
CROSS JOIN teacher
CROSS JOIN subject
WHERE NOT EXISTS (
  SELECT 1
  FROM public.teacher_classes tc
  WHERE tc.teacher_id = teacher.teacher_id
    AND tc.class_name = student.class_name
    AND tc.grade = student.grade
);

WITH student AS (
  SELECT id
  FROM public.students
  ORDER BY id
  LIMIT 1
),
school_class AS (
  SELECT id
  FROM public.teacher_classes
  ORDER BY id
  LIMIT 1
)
INSERT INTO public.online_class_students
  (class_id, student_id, student_name)
SELECT school_class.id, student.id, ''
FROM school_class
CROSS JOIN student
WHERE NOT EXISTS (
  SELECT 1
  FROM public.online_class_students ocs
  WHERE ocs.class_id = school_class.id
    AND ocs.student_id = student.id
);

COMMIT;
