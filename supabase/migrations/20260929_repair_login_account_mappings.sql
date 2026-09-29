-- Repair the national-code -> Auth-email bridge used by the mobile login.
-- This migration is intentionally idempotent.
INSERT INTO public.account_settings (username, display_name, email, national_code, preferences)
VALUES
('1234567891','امیرحسین زارعی','amirhossein.ejraei@frahoosh.test','1234567891','{"role":"executive","national_code":"1234567891"}'::jsonb),
('1234567892','محمدرضا صفی','mohammadreza.amoozeshi@frahoosh.test','1234567892','{"role":"educational","national_code":"1234567892"}'::jsonb),
('1234567893','عادل کلهر','adel.kalhor@frahoosh.test','1234567893','{"role":"cultural","national_code":"1234567893"}'::jsonb),
('1234567894','رضا مردانه جهان تیغ','reza.mardane@frahoosh.test','1234567894','{"role":"teacher","national_code":"1234567894"}'::jsonb),
('1234567895','محمد','hassan.mohammadi@frahoosh.test','1234567895','{"role":"student","national_code":"1234567895"}'::jsonb),
('0053409531','حسن مردانه جهان تیغ','hassan.mardaneh@frahoosh.test','0053409531','{"role":"manager","national_code":"0053409531"}'::jsonb)
ON CONFLICT DO NOTHING;

UPDATE public.account_settings a
SET display_name = v.display_name,
    email = v.email,
    national_code = v.national_code,
    preferences = COALESCE(a.preferences,'{}'::jsonb) || v.preferences
FROM (VALUES
('1234567891','امیرحسین زارعی','amirhossein.ejraei@frahoosh.test','1234567891','{"role":"executive","national_code":"1234567891"}'::jsonb),
('1234567892','محمدرضا صفی','mohammadreza.amoozeshi@frahoosh.test','1234567892','{"role":"educational","national_code":"1234567892"}'::jsonb),
('1234567893','عادل کلهر','adel.kalhor@frahoosh.test','1234567893','{"role":"cultural","national_code":"1234567893"}'::jsonb),
('1234567894','رضا مردانه جهان تیغ','reza.mardane@frahoosh.test','1234567894','{"role":"teacher","national_code":"1234567894"}'::jsonb),
('1234567895','محمد','hassan.mohammadi@frahoosh.test','1234567895','{"role":"student","national_code":"1234567895"}'::jsonb),
('0053409531','حسن مردانه جهان تیغ','hassan.mardaneh@frahoosh.test','0053409531','{"role":"manager","national_code":"0053409531"}'::jsonb)
) AS v(username,display_name,email,national_code,preferences)
WHERE a.username=v.username OR a.national_code=v.national_code;