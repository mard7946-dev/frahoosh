__version__ = "1.5.9"

from threading import Thread

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

Window.clearcolor = (0.96, 0.97, 0.98, 1)


class EmergencyLoginScreen(Screen):
    """Self-contained first screen. No optional Frahoosh module is imported here."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._busy = False
        self._build_login()

    def _build_login(self):
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        card = BoxLayout(
            orientation="vertical",
            size_hint=(0.90, None),
            height=dp(500),
            padding=[dp(22), dp(22), dp(22), dp(18)],
            spacing=dp(10),
        )

        card.add_widget(Label(
            text="فراهوش",
            font_size="32sp",
            bold=True,
            color=(0.03, 0.42, 0.22, 1),
            size_hint_y=None,
            height=dp(52),
        ))
        card.add_widget(Label(
            text="سامانه هوشمند آموزشی یکپارچه مدرسه",
            font_size="16sp",
            color=(0.12, 0.18, 0.25, 1),
            size_hint_y=None,
            height=dp(38),
        ))
        card.add_widget(Label(
            text="دبیرستان سردار حاجی زاده ۲",
            font_size="14sp",
            color=(0.03, 0.42, 0.22, 1),
            size_hint_y=None,
            height=dp(34),
        ))
        card.add_widget(Label(
            text="ورود کاربران",
            font_size="21sp",
            bold=True,
            color=(0.08, 0.12, 0.18, 1),
            size_hint_y=None,
            height=dp(42),
        ))

        self.identifier = TextInput(
            hint_text="کد ملی",
            multiline=False,
            size_hint_y=None,
            height=dp(54),
            font_size="18sp",
            halign="right",
            padding=[dp(14), dp(12)],
        )
        self.password = TextInput(
            hint_text="رمز عبور",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(54),
            font_size="18sp",
            halign="right",
            padding=[dp(14), dp(12)],
        )
        card.add_widget(self.identifier)
        card.add_widget(self.password)

        self.status = Label(
            text="",
            font_size="13sp",
            color=(0.55, 0.10, 0.10, 1),
            size_hint_y=None,
            height=dp(44),
        )
        card.add_widget(self.status)

        self.button = Button(
            text="ورود به فراهوش",
            font_size="17sp",
            size_hint_y=None,
            height=dp(56),
            background_normal="",
            background_color=(0.04, 0.52, 0.28, 1),
            color=(1, 1, 1, 1),
        )
        self.button.bind(on_release=self.login)
        card.add_widget(self.button)

        card.add_widget(Label(
            text="نام کاربری: کد ملی\nرمز عبور پیش‌فرض: حرف اول نام + کد ملی",
            font_size="12sp",
            color=(0.25, 0.28, 0.32, 1),
            halign="center",
            size_hint_y=None,
            height=dp(48),
        ))
        outer.add_widget(card)
        self.add_widget(outer)

    @staticmethod
    def _normalize_digits(value):
        return str(value or "").translate(str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789",
        ))

    def login(self, *_):
        if self._busy:
            return
        identifier = self._normalize_digits(self.identifier.text).strip()
        password = self.password.text or ""
        self.identifier.text = identifier
        if not identifier:
            self.status.text = "کد ملی را وارد کنید."
            return
        if len(identifier) != 10 or not identifier.isdigit():
            self.status.text = "کد ملی باید ۱۰ رقم باشد."
            return
        if not password:
            self.status.text = "رمز عبور را وارد کنید."
            return

        self._busy = True
        self.button.disabled = True
        self.status.text = "در حال ورود..."
        Thread(target=self._authenticate, args=(identifier, password), daemon=True).start()

    def _authenticate(self, identifier, password):
        try:
            app = App.get_running_app()
            from mobile.services.app_state import AppState
            state = app.app_state
            if state is None:
                state = AppState()
                app.app_state = state
            if state.api is None or not state.api.configured:
                raise RuntimeError("تنظیمات اتصال سرور در برنامه وجود ندارد.")
            session = state.api.sign_in(identifier, password)
            if not session or not state.set_session(session):
                raise RuntimeError("نام کاربری یا رمز عبور صحیح نیست.")
            app.open_dashboard()
        except Exception as exc:
            print("LOGIN ERROR:", repr(exc))
            from kivy.clock import Clock
            Clock.schedule_once(lambda *_: self._failed(str(exc)), 0)

    def _failed(self, message):
        self._busy = False
        self.button.disabled = False
        self.status.text = message or "ورود انجام نشد."


class AuthScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        kwargs["transition"] = NoTransition()
        super().__init__(**kwargs)


class FrahooshApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_state = None
        self.sm = None

    def build(self):
        self.title = "Frahoosh"
        self.sm = AuthScreenManager()
        self.sm.add_widget(EmergencyLoginScreen(name="login"))
        self.sm.current = "login"
        return self.sm

    def ensure_dashboard(self):
        try:
            return self.sm.get_screen("dashboard")
        except Exception:
            from mobile.screens.dashboard import DashboardScreen
            screen = DashboardScreen(name="dashboard", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def open_dashboard(self):
        try:
            if self.app_state is None or not self.app_state.logged_in:
                self.sm.current = "login"
                return False
            dashboard = self.ensure_dashboard()
            self.sm.current = "dashboard"
            try:
                dashboard.refresh()
            except Exception as exc:
                print("DASHBOARD REFRESH ERROR:", repr(exc))
            return True
        except Exception as exc:
            print("DASHBOARD OPEN ERROR:", repr(exc))
            return False


if __name__ == "__main__":
    FrahooshApp().run()
