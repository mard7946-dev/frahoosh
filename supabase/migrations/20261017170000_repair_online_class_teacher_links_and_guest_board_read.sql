-- Repair class-to-teacher links required by classroom signaling RLS.
-- Match within each school only, and only update rows with a single unambiguous teacher match.
WITH aliases(alias_name, canonical_last_name) AS (
  VALUES
    ('فهیمراد', 'فهیم راد'),
    ('قاسمی', 'قاسمی'),
    ('کریمی', 'کریمی'),
    ('موسوی', 'عنایت اله موسوی'),
    ('فرضی', 'فرضی'),
    ('ایازیان', 'ایازیان'),
    ('قنبرپور', 'قنبرپور'),
    ('بابایی', 'بابایی'),
    ('حاجیزاده', 'حاجی زاده')
),
candidates AS (
  SELECT
    oct.id AS class_teacher_row_id,
    t.id AS matched_teacher_id,
    COUNT(*) OVER (PARTITION BY oct.id) AS match_count
  FROM public.online_class_teachers AS oct
  JOIN aliases AS a
    ON regexp_replace(replace(translate(lower(oct.teacher_name), 'يك', 'یک'), chr(8204), ''), '[[:space:]]', '', 'g') = a.alias_name
  JOIN public.teachers AS t
    ON t.tenant_school_id = oct.tenant_school_id
   AND regexp_replace(replace(translate(lower(t.last_name), 'يك', 'یک'), chr(8204), ''), '[[:space:]]', '', 'g')
       = regexp_replace(replace(translate(lower(a.canonical_last_name), 'يك', 'یک'), chr(8204), ''), '[[:space:]]', '', 'g')
  WHERE oct.teacher_id IS NULL
),
unique_matches AS (
  SELECT class_teacher_row_id, MAX(matched_teacher_id) AS teacher_id
  FROM candidates
  GROUP BY class_teacher_row_id
  HAVING MAX(match_count) = 1
)
UPDATE public.online_class_teachers AS oct
SET teacher_id = u.teacher_id
FROM unique_matches AS u
WHERE oct.id = u.class_teacher_row_id
  AND oct.teacher_id IS NULL;

-- Guest students may read saved board strokes only while they are active members
-- of the same class and school. Existing restrictive tenant-boundary policies remain in force.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'smart_board_whiteboards'
      AND policyname = 'guest class member read smart_board_whiteboards'
  ) THEN
    CREATE POLICY "guest class member read smart_board_whiteboards"
      ON public.smart_board_whiteboards
      FOR SELECT
      TO authenticated
      USING (
        EXISTS (
          SELECT 1
          FROM public.guest_online_members AS m
          WHERE m.class_id = smart_board_whiteboards.class_id
            AND m.user_id = (SELECT auth.uid())
            AND m.left_at IS NULL
            AND m.tenant_school_id = smart_board_whiteboards.tenant_school_id
        )
      );
  END IF;
END
$$;
