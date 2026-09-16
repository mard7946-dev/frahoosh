__version__ = "1.5.5"

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.label import Label

from mobile.screens.login import LoginScreen


class StartupFallback(Label):
    pass


class AuthScreenManager(ScreenManager):
    """Prevent unauthenticated navigation away from the login screen."""

    PUBLIC_SCREENS = {"login"}

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
            from mobile.services.app_state import AppState
            self.app_state = AppState()
        except Exception as exc:
            print("APP STATE STARTUP ERROR:", repr(exc))

        self.sm = AuthScreenManager(app_state=self.app_state)

        # Login is deliberately the first and only startup screen.
        # The old LoadingScreen performed background/session work before
        # the login UI was shown and could leave the app stuck on loading.
        self.sm.add_widget(
            LoginScreen(name="login", app_state=self.app_state)
        )
        self.sm.current = "login"
        return self.sm

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
