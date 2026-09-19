from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

# IMPORTANT: LoginScreen is intentionally NOT imported at module import time.
# A failure in login.py (or one of its optional dependencies) must never kill
# the Android process before the first frame is displayed.
LoginScreen = None


class EmergencyLoginScreen(Screen):
    """Minimal startup-safe screen used only if the normal login module fails."""
    def __init__(self, app_state=None, import_error=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.import_error = import_error
        root = BoxLayout(orientation="vertical", padding=32, spacing=16)
        root.add_widget(Label(text="فراهوش", font_size="28sp"))
        root.add_widget(Label(text="ورود", font_size="22sp"))
        self.username = TextInput(hint_text="نام کاربری / کد ملی", multiline=False)
        self.password = TextInput(hint_text="رمز عبور", password=True, multiline=False)
        root.add_widget(self.username)
        root.add_widget(self.password)
        self.status = Label(text="در حال آماده‌سازی صفحه ورود...", font_size="14sp")
        root.add_widget(self.status)
        button = Button(text="ورود", size_hint_y=None, height=52)
        button.bind(on_release=self.retry_login)
        root.add_widget(button)
        self.add_widget(root)
        if import_error:
            print("LOGIN MODULE STARTUP ERROR:", repr(import_error))

    def retry_login(self, *_):
        global LoginScreen
        try:
            if LoginScreen is None:
                from mobile.screens.login import LoginScreen as _LoginScreen
                LoginScreen = _LoginScreen
            app = App.get_running_app()
            real = LoginScreen(name="login", app_state=getattr(app, "app_state", None))
            self.manager.add_widget(real)
            self.manager.current = "login"
        except Exception as exc:
            print("LOGIN RETRY ERROR:", repr(exc))
            self.status.text = "صفحه ورود اصلی بارگذاری نشد. خطای داخلی ثبت شد."



class FrahooshApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_state = None
        self.sm = None

    def build(self):
        self.title = "Frahoosh"
        Window.clearcolor = (0.94, 0.97, 0.985, 1)
        try:
            Window.softinput_mode = "below_target"
        except Exception:
            pass

        # Android startup must contain no project-service initialization.
        # First render a login-capable screen; only then initialize AppState.
        # This isolates the first frame from Supabase/network/storage/native
        # dependencies and from every non-login module.
        self.sm = ScreenManager()

        global LoginScreen
        try:
            from mobile.screens.login import LoginScreen as _LoginScreen
            LoginScreen = _LoginScreen
            self.sm.add_widget(LoginScreen(name="login", app_state=None))
        except Exception as exc:
            print("LOGIN CONSTRUCTION ERROR:", repr(exc))
            self.sm.add_widget(
                EmergencyLoginScreen(name="login", app_state=None, import_error=exc)
            )
        self.sm.current = "login"

        # AppState is intentionally initialized after the first frame.
        Clock.schedule_once(self._load_app_state, 0.10)
        Clock.schedule_once(self._startup_check, 0)
        return self.sm

    def _load_app_state(self, *_):
        try:
            from mobile.services.app_state import AppState
            self.app_state = AppState()
            screen = self.sm.get_screen("login")
            screen.app_state = self.app_state
            print("APP STATE READY")
        except Exception as exc:
            print("APP STATE LAZY STARTUP ERROR:", repr(exc))

    def _startup_check(self, *_):
        try:
            self.sm.current = "login"
        except Exception as exc:
            print("LOGIN SCREEN START ERROR:", repr(exc))

    def _set_screen_capture_policy(self):
        try:
            # Dashboard is the authenticated landing page for every role.
        # Do not block it on heavy panel construction or a role-specific gate.
        try:
            self._set_screen_capture_policy()
            role_routes = {
                "manager": "management",
                "admin": "management",
                "administrator": "management",
                "مدیر": "management",
                "مدیریت": "management",
                "educational": "educational",
                "معاون آموزشی": "educational",
                "executive": "executive",
                "معاون اجرایی": "executive",
                "cultural": "cultural",
                "معاون پرورشی": "cultural",
                "advisor": "advisor",
                "مشاور": "advisor",
                "teacher": "teachers",
                "دبیر": "teachers",
                "student": "students",
                "دانش‌آموز": "students",
                "parent": "parents",
                "ولی": "parents",
                "اولیا": "parents",
            }
            raw_role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
            target_route = role_routes.get(raw_role, "management")
            # Keep dashboard visible first; role panel is opened from there.
            # This also makes panel construction fully lazy and isolates the
            # authenticated dashboard from heavy module imports.
            self.sm.current = "dashboard"
            return True
        except Exception as exc:
            print("DASHBOARD NAVIGATION ERROR:", repr(exc))
            return False


if __name__ == "__main__":
    FrahooshApp().run()
