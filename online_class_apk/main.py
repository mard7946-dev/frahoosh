from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from android.permissions import request_permissions, Permission

CLASS_URL = "https://frahoosh.ir/online-class/"

class Root(Widget):
    pass

class AppMain(App):
    def build(self):
        return Root()

    def _open_classroom(self, *_):
        try:
            from jnius import autoclass
            Activity = autoclass("org.kivy.android.PythonActivity")
            Launcher = autoclass("ir.frahoosh.ClassroomLauncher")
            Launcher.open(Activity.mActivity, CLASS_URL)
        except Exception as exc:
            self.root.clear_widgets()
            self.root.add_widget(Label(
                text="خطا در باز کردن کلاس آنلاین\n\nلطفاً اتصال اینترنت و WebView اندروید را بررسی کنید.",
                halign="center",
                valign="middle",
            ))

    def on_start(self):
        try:
            request_permissions(
                [Permission.INTERNET, Permission.CAMERA, Permission.RECORD_AUDIO],
                lambda *_: Clock.schedule_once(self._open_classroom, 0.8),
            )
        except Exception:
            Clock.schedule_once(self._open_classroom, 1.0)

AppMain().run()
