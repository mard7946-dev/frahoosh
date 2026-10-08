from kivy.app import App
from kivy.clock import Clock

CLASSROOM_URL = "https://frahoosh.ir/online-class/"

class ClassroomApp(App):
    def build(self):
        # This APK is intentionally a classroom-only shell.
        # It never opens the main Frahoosh dashboard or any other module.
        Clock.schedule_once(self.open_classroom, 0.15)
        return None

    def open_classroom(self, *_):
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ClassroomLauncher = autoclass("ir.frahoosh.ClassroomLauncher")
        ClassroomLauncher.open(PythonActivity.mActivity, CLASSROOM_URL)

ClassroomApp().run()
