from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

class ClassroomApp(App):
    def build(self):
        box = BoxLayout(orientation="vertical", padding=40, spacing=24)
        box.add_widget(Label(
            text="فراهوش\nکلاس آنلاین",
            font_size="28sp",
            halign="center"
        ))
        button = Button(
            text="ورود به کلاس آنلاین",
            font_size="22sp",
            size_hint_y=None,
            height=80
        )
        button.bind(on_release=self.show_status)
        box.add_widget(button)
        self.status = Label(
            text="برنامه با موفقیت اجرا شد.",
            font_size="18sp"
        )
        box.add_widget(self.status)
        return box

    def show_status(self, *_):
        self.status.text = "محیط کلاس آماده است.\nبرای مرحله بعد، اتصال مرورگر/کلاس فعال می‌شود."

ClassroomApp().run()
