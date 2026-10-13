import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOM = ROOT / "app/src/main/assets/room_assets/online_class.html"
PATCH = ROOT / "app/src/main/assets/room_assets/classroom_patch.js"


class StudentPublishedQuizAccessTests(unittest.TestCase):
    def test_permission_gate_does_not_hide_quiz_toggle(self):
        source = ROOM.read_text(encoding="utf-8")
        start = source.index("function setStudentToolsPermission(value)")
        end = source.index("function applyClassroomRoleView()", start)
        gate = source[start:end]
        match = re.search(r'for\\s*\\(const id of \\[(.*?)\\]\\)', gate, re.S)
        self.assertIsNotNone(match, "student permission-gate control list must exist")
        self.assertNotIn('"quizToggle"', match.group(1),
                         "media/board permissions must not hide the quiz entry point")

    def test_student_restrictions_keep_quiz_entry_point_visible(self):
        source = PATCH.read_text(encoding="utf-8")
        start = source.index("function restrictStudentUI()")
        end = source.index("async function pollPermissions()", start)
        gate = source[start:end]
        match = re.search(r'for\\s*\\(const id of \\[(.*?)\\]\\)', gate, re.S)
        self.assertIsNotNone(match, "student UI restriction control list must exist")
        self.assertNotIn('"quizToggle"', match.group(1),
                         "student restrictions must preserve the published-quiz button")

    def test_quiz_button_opens_published_quizzes(self):
        source = ROOM.read_text(encoding="utf-8")
        self.assertIn('if(qt&&drawer)qt.onclick=()=>{drawer.open=true;const panel=$("quizPanel");if(panel){panel.style.display="block";', source)
        self.assertIn('smart_board_quizzes?class_id=eq.', source)
        self.assertIn('is_published=eq.true', source)


if __name__ == "__main__":
    unittest.main()
