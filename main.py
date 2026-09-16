__version__ = "1.5.6"

from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


# Keep the first frame completely independent from mobile/optional modules.
# This is intentional: the user must always see the login form even if a
# service, font, Supabase configuration, or another screen fails to import.
Window.clearcolor = (0.965, 0.975, 0.985, 1)


class AuthScreenManager(ScreenManager):
    PUBLIC_SCREENS = {"login"}

    def __init__(self, app_state=None, **kwargs):
        kwargs.setdefault("transition", NoTransition())
        super().__init__(**kwargs)
        self.app_state = app_state

    def on_current(self, _manager, screen_name):
        if screen_name in self.PUBLIC_SCREENS:
            return
        if self.app_state is None or not self.app_state.logged_in:
            Clock.schedule_once(lambda *_: setattr(self, "current", "login"), 0)


class EmergencyLoginScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(0.965, 0.975, 0.985, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        root = BoxLayout(orientation="vertical", padding=dp(28), spacing=dp(14))
        root.add_widget(Label(text="فراهوش", font_size="34sp", bold=True, color=(0.05, 0.45, 0.25, 1), size_hint_y=None, height=dp(60)))
        root.add_widget(Label(text="سامانه هوشمند آموزشی یکپارچه مدرسه", font_size="17sp", color=(0.15, 0.25, 0.35, 1), size_hint_y=None, height=dp(48)))
        root.add_widget(Label(text="دبیرستان سردار حاجی زاده ۲", font_size="14sp", color=(0.05, 0.45, 0.25, 1), size_hint_y=None, height=dp(40)))
        root.add_widget(Label(text="ورود کاربران", font_size="21sp", bold=True, color=(0.05, 0.45, 0.25, 1), size_hint_y=None, height=dp(48)))

        self.identifier = TextInput(
            hint_text="کد ملی",
            multiline=False,
            size_hint_y=None,
            height=dp(54),
            halign="right",
            padding=[dp(14), dp(14)],
        )
        self.password = TextInput(
            hint_text="رمز عبور",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(54),
            halign="right",
            padding=[dp(14), dp(14)],
        )
        self.status = Label(
            text="",
            font_size="13sp",
            color=(0.15, 0.25, 0.35, 1),
            size_hint_y=None,
            height=dp(55),
            halign="center",
            valign="middle",
        )
        self.status.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        self.button = Button(
            text="ورود به فراهوش",
            font_size="17sp",
            background_normal="",
            background_color=(0.05, 0.55, 0.30, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(56),
        )
        self.button.bind(on_release=self.login)

        root.add_widget(self.identifier)
        root.add_widget(self.password)
        root.add_widget(self.status)
        root.add_widget(self.button)
        root.add_widget(Label(text="نام کاربری: کد ملی\nرمز عبور پیش‌فرض: حرف اول نام + کد ملی", font_size="12sp", halign="center"))
        self.add_widget(root)

    def _sync_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    @staticmethod
    def _normalize_digits(value):
        return str(value or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))

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
        if self.app_state is None:
            self.status.text = "در حال آماده‌سازی سرویس..."
            return
        if self.app_state.api is None:
            self.status.text = "سرویس اتصال آماده نیست."
            return
        if not self.app_state.api.configured:
            self.status.text = "تنظیمات اتصال سرور در برنامه وجود ندارد."
            return

        self._busy = True
        self.button.disabled = True
        self.status.text = "در حال بررسی اطلاعات..."
        Thread(target=self._authenticate, args=(identifier, password), daemon=True).start()

    def _authenticate(self, identifier, password):
        try:
            session = self.app_state.api.sign_in(identifier, password)
            if not session or not self.app_state.set_session(session):
                raise RuntimeError("ورود انجام نشد.")
            Clock.schedule_once(lambda *_: self._success(), 0)
        except Exception as exc:
            print("LOGIN ERROR:", repr(exc))
            Clock.schedule_once(lambda *_: self._failed(str(exc)), 0)

    def _success(self):
        self._busy = False
        self.button.disabled = False
        self.status.text = "ورود موفق بود."
        app = App.get_running_app()
        if app is not None and not app.open_dashboard():
            self.status.text = "ورود موفق شد اما داشبورد باز نشد."

    def _failed(self, message):
        self._busy = False
        self.button.disabled = False
        self.status.text = message or "ورود انجام نشد."


class FrahooshApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_state = None
        self.sm = None

    def build(self):
        self.title = "Frahoosh"
        self.sm = AuthScreenManager(app_state=None)

        # Do NOT import LoginScreen here. The bootstrap login is deliberately
        # made only from Kivy primitives so an optional module cannot blank the UI.
        login = EmergencyLoginScreen(name="login", app_state=None)
        self.sm.add_widget(login)
        self.sm.current = "login"

        # AppState initialization happens off the UI thread. The login screen
        # is already visible and remains usable once the service is ready.
        Thread(target=self._initialize_app_state, daemon=True).start()
        return self.sm

    def _initialize_app_state(self):
        try:
            from mobile.services.app_state import AppState
            state = AppState()
            Clock.schedule_once(lambda *_: self._state_ready(state), 0)
        except Exception as exc:
            print("APP STATE STARTUP ERROR:", repr(exc))

    def _state_ready(self, state):
        self.app_state = state
        self.sm.app_state = state
        login = self.sm.get_screen("login")
        login.app_state = state
        print("APP STATE READY")

    def ensure_dashboard(self):
        try:
            return self.sm.get_screen("dashboard")
        except Exception:
            from mobile.screens.dashboard import DashboardScreen
            screen = DashboardScreen(name="dashboard", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def ensure_exam(self):
        try:
            return self.sm.get_screen("teacher_exams")
        except Exception:
            from mobile.screens.teacher_exams import TeacherExamsScreen
            screen = TeacherExamsScreen(name="teacher_exams", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def ensure_module(self):
        try:
            return self.sm.get_screen("module")
        except Exception:
            from mobile.screens.module import ModuleScreen
            screen = ModuleScreen(name="module", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def ensure_school(self):
        try:
            return self.sm.get_screen("school")
        except Exception:
            from mobile.screens.school import SchoolScreen
            screen = SchoolScreen(name="school", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def ensure_update(self):
        try:
            return self.sm.get_screen("update")
        except Exception:
            from mobile.screens.update import UpdateScreen
            screen = UpdateScreen(name="update", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def _set_screen_capture_policy(self):
        try:
            role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
            allowed = {"manager", "admin", "administrator", "مدیر", "مدیریت", "معاون آموزشی", "معاون اجرایی", "معاون پرورشی", "educational", "executive", "cultural"}
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            window_manager = autoclass("android.view.WindowManager")
            if role in allowed:
                activity.getWindow().clearFlags(window_manager.LayoutParams.FLAG_SECURE)
            else:
                activity.getWindow().addFlags(window_manager.LayoutParams.FLAG_SECURE)
        except Exception as exc:
            print("SCREEN SECURITY POLICY ERROR:", repr(exc))

    def open_dashboard(self):
        try:
            if self.app_state is None or not self.app_state.logged_in:
                self.sm.current = "login"
                return False
            dashboard = self.ensure_dashboard()
            if dashboard is None:
                return False
            self._set_screen_capture_policy()
            self.sm.current = "dashboard"
            try:
                dashboard.refresh()
            except Exception as exc:
                print("DASHBOARD REFRESH ERROR:", repr(exc)
            return True
        except Exception as exc:
            print("DASHBOARD OPEN ERROR:", repr(exc))
            return False


if __name__ == "__main__":
    FrahooshApp().run()
