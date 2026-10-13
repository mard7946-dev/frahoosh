import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOM = ROOT / "online_class_apk/app/src/main/assets/room_assets/online_class.html"
ACTIVITY = ROOT / "online_class_apk/app/src/main/java/ir/frahoosh/classroom/MainActivity.java"
PATCH = ROOT / "online_class_apk/app/src/main/assets/room_assets/classroom_patch.js"
MANIFEST = ROOT / "online_class_apk/app/src/main/AndroidManifest.xml"


class ClassroomRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.room = ROOM.read_text(encoding="utf-8")
        cls.activity = ACTIVITY.read_text(encoding="utf-8")
        cls.patch = PATCH.read_text(encoding="utf-8")
        cls.manifest = MANIFEST.read_text(encoding="utf-8")

    def test_student_tool_permissions_do_not_hide_published_quiz_entry(self):
        start = self.room.index("function setStudentToolsPermission(value)")
        end = self.room.index("async function ensureTeacherSession()", start)
        gate = self.room[start:end]
        self.assertIn('for(const id of ["screen"', gate)
        self.assertIn('for(const id of ["screen","prev","next","clear","clearAll","color","size","teacherToolPermission","qsave"]){', gate)
        self.assertIn('const toggle=$("quizToggle")', self.room)
        self.assertIn('is_published=eq.true', self.room)

    def test_student_quiz_toggle_is_not_hidden_by_patch_permission_gate(self):
        start = self.patch.index("function restrictStudentUI()")
        end = self.patch.index("async function pollPermissions()", start)
        gate = self.patch[start:end]
        self.assertIn('const quizToggle=$("quizToggle")', gate)
        self.assertIn('for(const id of ["screen","prev","next","clear","clearAll","color","size","teacherToolPermission"]){', gate)

    def test_webview_blocks_unsafe_navigation_and_limits_classroom_origin(self):
        self.assertIn('"https".equalsIgnoreCase(scheme)', self.activity)
        self.assertIn('"frahoosh.ir".equalsIgnoreCase(host)', self.activity)
        self.assertIn('return true;', self.activity)
        self.assertIn('Intent.ACTION_VIEW', self.activity)

    def test_main_frame_network_error_does_not_auto_reload_forever(self):
        start = self.activity.index("public void onReceivedError")
        end = self.activity.index("@Override", start + len("@Override"))
        handler = self.activity[start:end]
        self.assertIn("loadDataWithBaseURL", handler)
        self.assertNotIn("postDelayed", handler)
        self.assertNotIn('loadUrl(CLASSROOM_URL + "index.html")', handler)

    def test_camera_and_microphone_permissions_are_declared(self):
        self.assertIn('android.permission.CAMERA', self.manifest)
        self.assertIn('android.permission.RECORD_AUDIO', self.manifest)

    def test_room_has_whiteboard_and_published_quiz_features(self):
        self.assertIn('id="board"', self.room)
        self.assertIn('function loadQuizzes()', self.room)
        self.assertIn('async function answerQuiz(', self.room)


if __name__ == "__main__":
    unittest.main()
