from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "web" / "online-class" / "index.html"
ROOM = ROOT / "web" / "online-class" / "room.html"
PATCH = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room_assets" / "classroom_patch.js"


class OnlineClassContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry = ENTRY.read_text(encoding="utf-8")
        cls.room = ROOM.read_text(encoding="utf-8")
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


    def test_shared_room_loader_uses_paths_supported_by_web_and_android(self):
        self.assertIn('getText("/mobile/assets/online_class.html"', self.room)
        self.assertIn('getText("/online_class_apk/classroom_patch.js"', self.room)
        self.assertNotIn("../../online_class_apk/app/src/main/assets", self.room)


if __name__ == "__main__":
    unittest.main()
