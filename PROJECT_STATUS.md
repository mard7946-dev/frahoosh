# Frahoosh Mobile — Project Status

## Current foundation (v1.1.0)
- Cleaned all Python syntax errors in the current repository.
- Added a real loading screen before Login/Dashboard.
- Added bundled Persian/Arabic Noto font (regular/bold).
- Added RTL text shaping support.
- Fixed session storage to use Android app-private storage when running on device.
- Kept Supabase Auth as the login backend; no service_role key is used in the client.
- Improved profile/role extraction from Supabase user metadata and account_settings.
- Added role-specific dashboard module menus for the supported Frahoosh roles.
- Added a real module navigation screen instead of routing every dashboard button to Update.
- Added packaged runtime configuration support for CI builds without committing credentials.
- Added explicit Python dependency versions.

## Important
The role dashboards and module navigation are now structurally ready, but each module's CRUD/data operations must be connected to the exact Web v16.12 Supabase schema and RLS policies. No fake tables or invented schema are used here.

## CI configuration
Set these GitHub repository Secrets/Variables before expecting online login inside the APK:
- Secret: `FRAHOOSH_SUPABASE_URL`
- Secret: `FRAHOOSH_SUPABASE_ANON_KEY`
- Variable: `FRAHOOSH_SCHOOL_ID`
- Variable: `FRAHOOSH_SCHOOL_NAME`
- Variable: `FRAHOOSH_SCHOOL_YEAR`


## Android CI fix — 2026-08-31
The Android workflow was corrected so SDK package installation does not use `yes | sdkmanager ...` under `set -o pipefail`. That pattern causes a false `Broken pipe` exit code after sdkmanager finishes normally. The workflow now installs SDK packages directly, installs NDK 28c explicitly, generates `mobile/runtime_config.json` from GitHub Secrets/Variables, and runs `python -m compileall -q mobile` before Buildozer.


## 2026-09-18 — professional workflow expansion
- Parent online-class access was removed from the role menu.
- Added real `meeting_requests` workflow: parent/teacher/staff/counselor can create meeting requests; manager approval moves them to the educational deputy; final confirmation stores the confirmed date/time.
- Added a manager-facing `نمونه کلاس هوشمند` screen that explains the classroom experience for teacher, parent, student and manager and reads the latest online-class/whiteboard/content/activity/quiz records from the shared backend.
- Added dedicated Android screens and navigation for meetings and the smart-class preview while preserving the existing generic module/table engine.
- Added Supabase RLS for meeting requester/target access and manager/educational-deputy review.
- Next validation step: run the Android CI build and apply the new Supabase migration in the project's database before production use.
