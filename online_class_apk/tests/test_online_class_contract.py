from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "web" / "online-class" / "index.html"
ROOM = ROOT / "web" / "online-class" / "room.html"
CLASSROOM = ROOT / "mobile" / "assets" / "online_class.html"
PATCH = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room_assets" / "classroom_patch.js"


class OnlineClassContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry = ENTRY.read_text(encoding="utf-8")
        cls.room = ROOM.read_text(encoding="utf-8")
        cls.classroom = CLASSROOM.read_text(encoding="utf-8")
        cls.patch = PATCH.read_text(encoding="utf-8")

    def test_entry_offers_three_distinct_roles(self):
        for role in ("manager", "teacher", "student"):
            self.assertIn(f"chooseRole('{role}')", self.entry)
        self.assertNotIn("chooseRole('staff')", self.entry)

    def test_student_roster_is_local_not_posted_to_supabase(self):
        self.assertIn('localStorage.setItem("frahoosh_local_students"', self.entry)
        self.assertIn('if(kind==="students")', self.entry)
        self.assertIn("هیچ اطلاعات دانش‌آموزی به پایگاه داده مرکزی ارسال نشد", self.entry)
        self.assertIn('api("/rest/v1/teachers"', self.entry)
        # Student import must return before the teacher-table insert loop.
        student_branch = self.entry.index('if(kind==="students"){')
        teacher_insert = self.entry.index('api("/rest/v1/teachers"', student_branch)
        student_return = self.entry.index("return}", student_branch)
        self.assertLess(student_return, teacher_insert)

    def test_weekly_schedule_uses_existing_supabase_contract(self):
        self.assertIn("weekly_schedule_entries", self.entry)
        self.assertIn("get_student_class_schedule", self.entry)
        self.assertIn('id="scheduleDay"', self.entry)
        self.assertIn('id="studentSchedule"', self.entry)
        self.assertIn('register_online_class_student_guest', self.entry)
        self.assertIn('location.href="room.html"', self.entry)

    def test_weekly_bell_times_are_editable_and_shared_with_apk(self):
        for field in ('scheduleStartTime', 'scheduleEndTime'):
            self.assertIn(f'id="{field}"', self.entry)
        self.assertIn('data-edit-schedule=', self.entry)
        self.assertIn('start_time,end_time', self.entry)
        self.assertIn('if(start_time>=end_time)', self.entry)
        self.assertIn('weekly_schedule_entries', self.entry)
        self.assertIn('ساعت پایان باید بعد از ساعت شروع باشد.', self.entry)
        migration = (ROOT / "supabase" / "migrations" /
                     "20261014070000_weekly_schedule_bell_time_automation.sql").read_text(encoding="utf-8")
        self.assertIn("trg_validate_weekly_schedule_bell_times", migration)
        self.assertIn("refresh_online_class_statuses", migration)
        self.assertIn("Asia/Tehran", migration)
        self.assertIn("ورود دبیر به این کلاس فقط در بازه زمانی", migration)

    def test_room_requires_a_complete_authenticated_session(self):
        self.assertIn('!config.token', self.room)
        self.assertIn('!config.userId', self.room)
        self.assertIn('frahoosh_online_class_config', self.room)

    def test_student_tools_remain_teacher_permission_gated(self):
        self.assertIn('const student=', self.patch)
        self.assertIn('const controller=', self.patch)
        self.assertIn('tools_permission', self.patch)
        self.assertIn('pollPermissions', self.patch)


    def test_apk_bundles_exact_same_entry_and_classroom_sources(self):
        apk_entry = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "index.html"
        apk_room = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room.html"
        apk_classroom = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room_assets" / "online_class.html"
        apk_patch = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room_assets" / "classroom_patch.js"
        web_classroom = ROOT / "mobile" / "assets" / "online_class.html"
        source_patch = ROOT / "online_class_apk" / "classroom_patch.js"
        self.assertEqual(self.entry, apk_entry.read_text(encoding="utf-8"))
        self.assertEqual(self.room, apk_room.read_text(encoding="utf-8"))
        self.assertEqual(web_classroom.read_text(encoding="utf-8"), apk_classroom.read_text(encoding="utf-8"))
        self.assertEqual(source_patch.read_text(encoding="utf-8"), apk_patch.read_text(encoding="utf-8"))


    def test_class_creation_persists_valid_jalali_date_and_24_hour_time(self):
        self.assertIn('classWizardStep===4?$("cdateDisplay")', self.entry)
        self.assertIn('if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(selectedDate))', self.entry)
        self.assertIn('if(!/^(?:[01]\\d|2[0-3]):[0-5]\\d$/.test(selectedTime))', self.entry)
        for field in ("start_time_shamsi", "end_time_shamsi", "start_at", "end_at"):
            self.assertIn(field, self.entry)
        self.assertIn('unicode-bidi:isolate-override!important', self.entry)
        self.assertIn('timeZone:"Asia/Tehran"', self.entry)
        self.assertIn('function todayJalali(){const p=Object.fromEntries', self.entry)


    def test_student_schedule_auto_refreshes_and_uses_server_bell_times(self):
        self.assertIn("function getTehranBellState(row)", self.entry)
        self.assertIn("showStudentSchedule(true)", self.entry)
        self.assertIn("startTeacherSchedulePolling()", self.entry)
        self.assertIn("sessionId:s[0]?.id||null", self.entry)
        migration = (ROOT / "supabase" / "migrations" /
                     "20261014072000_weekly_schedule_runtime_times_and_session_close.sql").read_text(encoding="utf-8")
        self.assertIn("start_time time without time zone", migration)
        self.assertIn("end_time time without time zone", migration)
        self.assertIn("drop function if exists public.get_student_class_schedule(text)", migration)

    def test_classroom_leaves_when_server_ends_or_replaces_its_session(self):
        self.assertIn("missingSessionPolls", self.classroom)
        self.assertIn("closeClassAfterServerEnd", self.classroom)
        self.assertIn("String(latest.id)!==String(C.sessionId)", self.classroom)
        self.assertIn('location.replace("/online-class/")', self.classroom)

    def test_android_grants_microphone_independently_of_camera(self):
        activity = (ROOT / "online_class_apk" / "app" / "src" / "main" / "java" /
                    "ir" / "frahoosh" / "classroom" / "MainActivity.java").read_text(encoding="utf-8")
        self.assertIn("missingPermissionsFor(PermissionRequest request)", activity)
        self.assertIn("needsAudio && checkSelfPermission(Manifest.permission.RECORD_AUDIO)", activity)
        self.assertIn("needsCamera && checkSelfPermission(Manifest.permission.CAMERA)", activity)
        self.assertIn("grantWebMediaPermission(request);", activity)
        self.assertIn("denying camera must not mute the microphone", activity)
        self.assertNotIn("requestMediaPermissions();", activity)
        self.assertNotIn("hasMediaPermissions()", activity)
        # A combined camera+microphone permission check must not gate a microphone-only request.
        permission_handler = activity.split("public void onPermissionRequest", 1)[1].split("public boolean onShowFileChooser", 1)[0]
        self.assertNotIn("hasMediaPermissions()", permission_handler)

    def test_shared_room_loader_falls_back_to_deployed_classroom_assets(self):
        self.assertIn('getTextFallback(["/mobile/assets/online_class.html","/online_class_apk/app/src/main/assets/room_assets/online_class.html"]', self.room)
        self.assertIn('getTextFallback(["/online_class_apk/classroom_patch.js","/online_class_apk/app/src/main/assets/room_assets/classroom_patch.js"]', self.room)
        self.assertNotIn("../../online_class_apk/app/src/main/assets", self.room)

    def test_whiteboard_fills_remaining_viewport_when_header_wraps(self):
        self.assertIn(".layout{flex:1 1 0;height:auto;min-height:0", self.classroom)
        self.assertIn(".boardwrap{flex:1 1 0;height:auto;min-height:0", self.classroom)


if __name__ == "__main__":
    unittest.main()
