-- The current school rollout is in full operational test mode.
-- Keep all consumer workflows enabled so their real CRUD paths are testable.
update public.module_activations
set active = true,
    activated_at = coalesce(activated_at, now())
where module_key in (
  'activity_registrations',
  'basij_registration',
  'online_classes',
  'parent_activities',
  'school_ally',
  'school_mayor',
  'student_council',
  'survey_responses',
  'teacher_exams',
  'transport_requests'
);