__version__ = "1.5.2"

from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button


class EmergencyLoginScreen(Screen):
    """Last-resort visible login. It prevents a startup/import problem from becoming a blank screen."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False

        root = BoxLayout(
            orientation="vertical",
            padding=dp(28),
            spacing=dp(14),
        )
        root.add_widget(BoxLayout(size_hint_y=0.16))
        root.add_widget(Label(text="فراهوش", font_size="34sp", bold=True, size_hint_y=None, height=dp(58)))
        root.add_widget(Label(text="سامانه هوشمند مدیریت مدرسه", font_size="18sp", size_hint_y=None, height=dp(42)))
        root.add_widget(Label(text="ورود کاربران", font_size="20sp", bold=True, size_hint_y=None, height=dp(42)))

        self.identifier = TextInput(
            hint_text="کد ملی",
            multiline=False,
            size_hint_y=None,
            height=dp(54),
            halign="right",
        )
        self.password = TextInput(
            hint_text="رمز عبور",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(54),
            halign="right",
        )
        self.status = Label(text="", size_hint_y=None, height=dp(54), halign="center", valign="middle")
        self.status.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        self.button = Button(text="ورود به فراهوش", size_hint_y=None, height=dp(56))
        self.button.bind(on_release=self.login)

        root.add_widget(self.identifier)
        root.add_widget(self.password)
        root.add_widget(self.status)
        root.add_widget(self.button)
        root.add_widget(Label(text="نام کاربری: کد ملی\nرمز عبور پیش‌فرض: حرف اول نام + کد ملی"))
        root.add_widget(BoxLayout(size_hint_y=0.16))
        self.add_widget(root)

    @staticmethod
    def _digits(value):
        return str(value or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))

    def login(self, *_):
        if self._busy:
            return
        identifier = self._digits(self.identifier.text).strip()
        password = self.password.text or ""
        self.identifier.text = identifier
        if len(identifier) != 10 or not identifier.isdigit():
            self.status.text = "کد ملی باید ۱۰ رقم باشد."
            return
        if not password:
            self.status.text = "رمز عبور را وارد کنید."
            return
        if self.app_state is None or self.app_state.api is None:
            self.status.text = "سرویس اتصال آماده نیست."
            return
        if not self.app_state.api.configured:
            self.status.text = "تنظیمات اتصال سرور وجود ندارد."
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
            Clock.schedule_once(lambda dt: self._success(), 0)
        except Exception as exc:
            print("EMERGENCY LOGIN ERROR:", repr(exc))
            Clock.schedule_once(lambda dt, msg=str(exc): self._failed(msg), 0)

    def _success(self):
        self._busy = False
        self.button.disabled = False
        self.status.text = "ورود موفق بود."
        app = App.get_running_app()
        if app is not None and app.open_dashboard():
            return
        self.status.text = "ورود موفق شد اما داشبورد باز نشد."

    def _failed(self, message):
        self._busy = False
        self.button.disabled = False
        self.status.text = message or "ورود انجام نشد."


class AuthScreenManager(ScreenManager):
    """Only loading/login are public until a valid session exists."""

    PUBLIC_SCREENS = {"loading", "login", "emergency_login"}

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._redirecting = False

    def on_current(self, _manager, screen_name):
        if self._redirecting or screen_name in self.PUBLIC_SCREENS:
            return
        state = self.app_state
        if state is None or not state.logged_in:
            self._redirecting = True
            Clock.schedule_once(self._redirect_to_login, 0)

    def _redirect_to_login(self, *_):
        try:
            self.current = "login"
        finally:
            self._redirecting = False


class FrahooshApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_state = None
        self.sm = None

    def build(self):
        self.title = "Frahoosh"
        try:
            from kivy.core.window import Window
            Window.clearcolor = (0.965, 0.975, 0.985, 1)
        except Exception as exc:
            print("WINDOW INIT ERROR:", repr(exc))

        try:
            from mobile.services.app_state import AppState
            self.app_state = AppState()
        except Exception as exc:
            print("APP STATE STARTUP ERROR:", repr(exc))
            self.app_state = None

        self.sm = AuthScreenManager(app_state=self.app_state)

        # Login is the first visible screen. Loading is no longer allowed to
        # hide the login UI during startup or network/session checks.
        try:
            from mobile.screens.login import LoginScreen
            self.sm.add_widget(LoginScreen(name="login", app_state=self.app_state))
        except Exception as exc:
            print("LOGIN SCREEN STARTUP ERROR:", repr(exc))
            self.sm.add_widget(EmergencyLoginScreen(name="emergency_login", app_state=self.app_state))
            self.sm.current = "emergency_login"
            return self.sm

        self.sm.current = "login"
        Clock.schedule_once(self._startup, 0.15)
        return self.sm

    def _startup(self, *_):
        """Restore a saved Supabase session, refreshing it when necessary."""
        try:
            if self.app_state is None or not self.app_state.logged_in:
                self.sm.current = "login"
                return

            valid = False
            try:
                valid = self.app_state.api.validate_session()
            except Exception as exc:
                print("SESSION VALIDATION ERROR:", repr(exc))

            if not valid:
                try:
                    valid = self.app_state.refresh_session()
                except Exception as exc:
                    print("SESSION REFRESH ERROR:", repr(exc))

            if valid:
                self.open_dashboard()
            else:
                self.app_state.logout()
                self.sm.current = "login"
        except Exception as exc:
            print("AUTH START ERROR:", repr(exc))
            try:
                self.sm.current = "login"
            except Exception:
                pass

    def ensure_dashboard(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("dashboard")
        except Exception:
            from mobile.screens.dashboard import DashboardScreen
            screen = DashboardScreen(name="dashboard", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def ensure_exam(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("teacher_exams")
        except Exception:
            from mobile.screens.teacher_exams import TeacherExamsScreen
            screen = TeacherExamsScreen(name="teacher_exams", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def ensure_module(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("module")
        except Exception:
            from mobile.screens.module import ModuleScreen
            screen = ModuleScreen(name="module", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def ensure_school(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("school")
        except Exception:
            from mobile.screens.school import SchoolScreen
            screen = SchoolScreen(name="school", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def ensure_update(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("update")
        except Exception:
            from mobile.screens.update import UpdateScreen
            screen = UpdateScreen(name="update", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen

    def _set_screen_capture_policy(self):
        """Allow screen capture only for management/deputy roles."""
        try:
            role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
            allowed = {
                "manager", "admin", "administrator", "مدیر", "مدیریت",
                "معاون آموزشی", "معاون اجرایی", "معاون پرورشی",
                "educational", "executive", "cultural",
            }
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
                if self.sm is not None:
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
                print("DASHBOARD REFRESH ERROR:", repr(exc))
            return True
        except Exception as exc:
            print("DASHBOARD OPEN ERROR:", repr(exc))
            return False


if __name__ == "__main__":
    FrahooshApp().run()
