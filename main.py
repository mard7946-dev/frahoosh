__version__ = "1.5.1"

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.label import Label

from mobile.screens.login import LoginScreen


class StartupFallback(Label):
    pass


class FrahooshApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_state = None
        self.sm = None

    def build(self):
        self.title = "Frahoosh"
        self.sm = ScreenManager()
        try:
            from mobile.services.app_state import AppState
            self.app_state = AppState()
        except Exception as exc:
            print("APP STATE STARTUP ERROR:", repr(exc))
        self.sm.add_widget(LoginScreen(name="login", app_state=self.app_state))
        self.sm.current = "login"
        Clock.schedule_once(self._startup, 0)
        return self.sm

    def _startup(self, *_):
        try:
            self.sm.current = "login"
        except Exception as exc:
            print("LOGIN START ERROR:", repr(exc))

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
