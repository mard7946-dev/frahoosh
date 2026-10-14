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
        self.assertIn("هیچ رکوردی به Supabase ارسال نشد", self.entry)
        self.assertIn('api("/rest/v1/teachers"', self.entry)
        # Student import must return before the teacher-table insert loop.
        student_branch = self.entry.index('if(kind==="students"){')
        teacher_insert = self.entry.index('api("/rest/v1/teachers"', student_branch)
        student_return = self.entry.index("return}", student_branch)
        self.assertLess(student_return, teacher_insert)

    def test_weekly_schedule_is_local_and_role_entry_uses_same_page(self):
        self.assertIn('localStorage.setItem("frahoosh_weekly_schedule"', self.entry)
        self.assertIn('id="scheduleDay"', self.entry)
        self.assertIn('id="studentSchedule"', self.entry)
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


if __name__ == "__main__":
    unittest.main()
