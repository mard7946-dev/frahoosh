# Frahoosh — Static Audit (2026-10-09)

STATUS: NOT COMPLETE. This is an audited snapshot with one CI fix. No build, no Supabase access, no device test was possible in the environment that produced it.

## Active Android path
buildozer.spec (v1.6.8) -> main.py -> mobile/main.py (FrahooshApp, lazy imports, EmergencyLoginScreen fallback)
-> screens/login.py -> screens/dashboard.py (DashboardScreen, PanelHubScreen)
-> screens/module_workspace.py (ModuleWorkspaceScreen) + specialised screens:
executive_center, finance, message_compose, assignment_submission, module_activation,
school_workflows, school_actions, operational_centers, teacher_exams_v4,
meetings / online_class / smart_class_preview (DO NOT TOUCH).

## Legacy / not imported anywhere (do not edit as a fix)
dashboard2, dashboard3, dashboard_fallback, dashboard_safe, live_panel, loading,
manager_exams, panel_screen, special_modules, teacher_exams, teacher_exams_v3.
To verify separately: mobile/mobile/*, mobile/rebuild*.

## Checks done
- python -m compileall mobile : OK
- build-android.yml parses as YAML : OK

## Change made
- .github/workflows/build-android.yml: FRAHOOSH_SCHOOL_ID/NAME/YEAR now read `secrets.X || vars.X`
  (PROJECT_STATUS.md documents them as Variables, workflow read only Secrets).

## Open items (need live Supabase / CI / device)
1. Dump pg_policies, grants, FKs, indexes from project gtmmllcxhdejwjjnyzrh; confirm no `using (true)` write policies remain
   (blanket policies from early migrations are dropped by later ones, final state unverified).
2. Confirm 20261008070000_canonical_weekly_schedule_entries_rbac supersedes the open SELECT policy on weekly_schedule.
3. Review anon-executable lookup_auth_email(s)_by_national_code for data leakage.
4. Fix "پیگیری آموزشی" table-access error from live grants/RLS/role mapping.
5. Module x role matrix + real E2E (create/update/delete/approve/role-reject) with supabase/test_data/test_accounts.sql.
6. Push, run Actions, verify artifact belongs to final commit SHA, install APK on device/emulator.

## UI changes applied (2026-10-09, second pass) — compile-checked only, NOT run on device
- Fonts: root cause of "□" = NotoSansArabic and BTitrBd have NO Latin letters and lack ( ) / % + = @ " ' etc.
  Added mobile/assets/FrahooshUI-{Regular,Bold}.ttf (Noto Arabic + DejaVu Latin, merged, 0 missing glyphs for
  Latin/Persian/digits/punctuation, verified by cmap + a raster test). ui.py/config.py and the PDF writers now prefer it.
  BTitrBd.ttf untouched and still used as title font.
- Tables (module_workspace.py): real bordered grid, RTL column order (first field at right), row-number column ("ردیف"),
  zebra rows, single-line cells with ellipsis, selected-row highlight, scrolls to the right edge on open.
- Login: larger type (was 7–8.5sp), larger fields/button, short-screen layout; auth logic untouched.
- Dashboard panels: larger headers/module buttons (height math unchanged).
- Version 1.6.8 -> 1.7.0 (numeric 170).

## NOT done
People-links ("اتصال افراد"), all module back-end/RLS work, Excel/PDF role gating, E2E tests, APK build.

## Third pass (v1.7.1) — compile + unit-logic checked only, NOT run on device
- Smart board (operational_centers.smart_board): newest->oldest by created_at (server order + defensive re-sort), grouped by Jalali day,
  time (Tehran, UTC+3:30) / author shown. Jalali converter in mobile/services/jalali.py verified against known dates.
- BUG FIX: operational_centers._edit_record required `fields`, but _record_card called it with 2 args -> TypeError on every "ویرایش". Now optional.
- Per-module tables (module_workspace.TABLE_PROFILES): distinct colour + column priority for grades, attendance, payments, weekly/exam schedule,
  assignments, students, finance; status badges (Persian + colour), money with separators, Jalali dates, scores. Formatter unit-tested.
- Finance ledger (finance.transactions): real grid with debit / credit / running balance / totals row / attachment count
  (one query instead of one per row). Maths in services/ledger.py, unit-tested.
- Online payment: supabase/functions/payment-gateway/index.ts (ZarinPal v4 start + server-side verify + payment_records insert),
  client operations._start_payment now calls it with the user's JWT. NOT deployed, NOT tested (needs ZARINPAL_MERCHANT_ID; no Deno here to type-check).
  Assumptions to confirm: ZarinPal is the chosen gateway; amounts are Toman (PAYMENT_AMOUNT_UNIT=IRT).
- Contract gap found: `grades` has only `score`; the required report-card column "نمره کل" (max score) does not exist yet.

## Still NOT done
Professional login redesign beyond type scale, deputies' real workflows, full counseling module, accountant extras (invoices/aging/year-end),
people-links, RLS/E2E on live Supabase, APK build.
