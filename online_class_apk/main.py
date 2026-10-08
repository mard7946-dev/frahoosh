from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

CLASS_URL = "https://frahoosh.ir/online-class/"

class AppMain(App):
    def build(self):
        box = BoxLayout(orientation="vertical", padding=40, spacing=20)
        box.add_widget(Label(text="فراهوش\nکلاس آنلاین", font_size="28sp"))
        b = Button(text="ورود به کلاس آنلاین", font_size="22sp", size_hint_y=None, height=70)
        b.bind(on_release=self.open_class)
        box.add_widget(b)
        Clock.schedule_once(self.open_class, 0.5)
        return box

    def open_class(self, *_):
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(CLASS_URL))
            PythonActivity.mActivity.startActivity(intent)
        except Exception as exc:
            self.root.children[0].text = "باز کردن کلاس انجام نشد.\nلطفاً مرورگر Chrome را نصب/فعال کنید."

AppMain().run()
