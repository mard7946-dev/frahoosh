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
            role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
            allowed = {
                "manager", "admin", "administrator", "مدیر", "مدیریت",
                "معاون آموزشی", "معاون اجرایی", "معاون پرورشی",
                "educational", "executive", "cultural"
            }
            secure = role not in allowed
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            WindowManager = autoclass("android.view.WindowManager")
            if secure:
                activity.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE)
            else:
                activity.getWindow().clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
        except Exception as exc:
            print("SCREEN SECURITY POLICY ERROR:", repr(exc))

    def ensure_panel(self):
        """Lazy-load the operational panel only after the login/dashboard boundary."""
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("panel")
        except Exception:
            pass
        try:
            from mobile.screens.panel_screen import PanelScreen
            screen = PanelScreen(name="panel", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen
        except Exception as exc:
            print("PANEL BUILD ERROR:", repr(exc))
            return None

    def ensure_dashboard(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("dashboard")
        except Exception:
            pass
        try:
            from mobile.screens.dashboard3 import DashboardScreen
            dashboard = DashboardScreen(name="dashboard", app_state=self.app_state)
            self.sm.add_widget(dashboard)
            return dashboard
        except Exception as exc:
            print("DASHBOARD BUILD ERROR:", repr(exc))
            return None

    def ensure_exam(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("teacher_exams")
        except Exception:
            pass
        from mobile.screens.teacher_exams_v4 import TeacherExamsV4Screen
        screen = TeacherExamsV4Screen(name="teacher_exams", app_state=self.app_state)
        self.sm.add_widget(screen)
        return screen

    def ensure_module(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("module")
        except Exception:
            pass
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
            pass
        from mobile.screens.school import SchoolScreen
        screen = SchoolScreen(name="school", app_state=self.app_state)
        self.sm.add_widget(screen)
        return screen

    def ensure_meetings(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("meetings")
        except Exception:
            pass
        try:
            from mobile.screens.meetings import MeetingsScreen
            screen = MeetingsScreen(name="meetings", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen
        except Exception as exc:
            print("MEETINGS BUILD ERROR:", repr(exc))
            return None

    def ensure_smart_class_preview(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("smart_class_preview")
        except Exception:
            pass
        try:
            from mobile.screens.smart_class_preview import SmartClassPreviewScreen
            screen = SmartClassPreviewScreen(name="smart_class_preview", app_state=self.app_state)
            self.sm.add_widget(screen)
            return screen
        except Exception as exc:
            print("SMART CLASS PREVIEW BUILD ERROR:", repr(exc))
            return None

    def ensure_special_module(self, mode):
        name = "special_" + str(mode)
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen(name)
        except Exception as exc:
            print("SPECIAL MODULE LOOKUP ERROR:", repr(exc))
            return None

    def ensure_identity_gate(self):
        if self.sm is None:
            return None
        try:
            screen = self.sm.get_screen("special_identity_gate")
        except Exception as exc:
            print("IDENTITY GATE LOOKUP ERROR:", repr(exc))
            return None
        return screen

    def ensure_update(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("update")
        except Exception:
            pass
        from mobile.screens.update import UpdateScreen
        screen = UpdateScreen(name="update", app_state=self.app_state)
        self.sm.add_widget(screen)
        return screen

    def _refresh_dashboard_safe(self, *_):
        try:
            dashboard = self.sm.get_screen("dashboard")
            dashboard.refresh()
        except Exception as exc:
            print("DASHBOARD REFRESH ERROR:", repr(exc))

    def open_dashboard(self):
        if self.sm is None:
            print("DASHBOARD OPEN ERROR: ScreenManager is not ready")
            return False

        dashboard = self.ensure_dashboard()
        if dashboard is None:
            print("DASHBOARD OPEN ERROR: dashboard screen could not be created")
            return False

        # The dashboard is the post-login boundary. Do NOT require the
        # heavy operational panel to be constructed before showing it.
        # A panel failure must never make a successful login look like a
        # failed login. The panel is created only when the user opens it.
        # Students and parents still go through the identity gate from the
        # dashboard/panel navigation layer.
        role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
        needs_gate = role in ("student", "دانش‌آموز", "parent", "parents", "ولی", "اولیا")
        confirmed = bool(
            isinstance(getattr(self.app_state, "session", None), dict)
            and self.app_state.session.get("identity_confirmed")
        )
        try:
            self._set_screen_capture_policy()
            if needs_gate and not confirmed:
                gate = self.ensure_identity_gate()
                if gate is None:
                    print("IDENTITY GATE ERROR: screen could not be created")
                    return False
                gate.pending_route = "role_panel"
                self.sm.current = "special_identity_gate"
                Clock.schedule_once(lambda *_: gate.load(), 0.05)
                return True
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
