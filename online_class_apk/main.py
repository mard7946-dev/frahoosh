from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

CLASSROOM_URL = "https://frahoosh.ir/online-class/"

class ClassroomApp(App):
    def build(self):
        box = BoxLayout(orientation="vertical", padding=28, spacing=18)
        box.add_widget(Label(
            text="فراهوش\nکلاس آنلاین",
            font_size="28sp",
            halign="center",
            valign="middle",
        ))
        self.status = Label(
            text="مسیر واقعی کلاس آنلاین فراهوش آماده است.",
            font_size="17sp",
            halign="center",
        )
        box.add_widget(self.status)
        button = Button(
            text="ورود به کلاس آنلاین",
            font_size="21sp",
            size_hint_y=None,
            height=78,
        )
        button.bind(on_release=self.open_classroom)
        box.add_widget(button)
        Clock.schedule_once(lambda *_: self.open_classroom(), 0.8)
        return box

    def open_classroom(self, *_):
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            ClassroomLauncher = autoclass("ir.frahoosh.ClassroomLauncher")
            activity = PythonActivity.mActivity
            ClassroomLauncher.open(activity, CLASSROOM_URL)
            self.status.text = "در حال باز کردن کلاس آنلاین فراهوش..."
        except Exception as exc:
            self.status.text = "باز کردن کلاس انجام نشد.\n" + str(exc)

ClassroomApp().run()
