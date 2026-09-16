from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition

from mobile.screens.login import LoginScreen


class FrahooshApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_state = None
        self.sm = None

    def build(self):
        self.title = "Frahoosh"
        # Never expose the default black Kivy window while the first screen is loading.
        Window.clearcolor = (0.94, 0.97, 0.985, 1)
        try:
            Window.softinput_mode = "below_target"
        except Exception:
            pass
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        try:
            from mobile.services.app_state import AppState
            self.app_state = AppState()
        except Exception as exc:
            print("APP STATE STARTUP ERROR:", repr(exc))
            self.app_state = None
        self.sm.add_widget(LoginScreen(name="login", app_state=self.app_state))
        self.sm.current = "login"
        Clock.schedule_once(self._startup_check, 0)
        return self.sm

    def _startup_check(self, *_):
        try:
            self.sm.current = "login"
        except Exception as exc:
            print("LOGIN SCREEN START ERROR:", repr(exc))

    def _set_screen_capture_policy(self):
        try:
            role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
            allowed = {"manager", "admin", "administrator", "مدیر", "مدیریت", "معاون آموزشی", "معاون اجرایی", "معاون پرورشی", "educational", "executive", "cultural"}
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

    def ensure_dashboard(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("dashboard")
        except Exception:
            pass
        from mobile.screens.dashboard import DashboardScreen
        d = DashboardScreen(name="dashboard", app_state=self.app_state)
        self.sm.add_widget(d)
        return d

    def ensure_exam(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("teacher_exams")
        except Exception:
            pass
        from mobile.screens.teacher_exams import TeacherExamsScreen
        s = TeacherExamsScreen(name="teacher_exams", app_state=self.app_state)
        self.sm.add_widget(s)
        return s

    def ensure_module(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("module")
        except Exception:
            pass
        from mobile.screens.module import ModuleScreen
        s = ModuleScreen(name="module", app_state=self.app_state)
        self.sm.add_widget(s)
        return s

    def ensure_school(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("school")
        except Exception:
            pass
        from mobile.screens.school import SchoolScreen
        s = SchoolScreen(name="school", app_state=self.app_state)
        self.sm.add_widget(s)
        return s

    def ensure_update(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("update")
        except Exception:
            pass
        from mobile.screens.update import UpdateScreen
        s = UpdateScreen(name="update", app_state=self.app_state)
        self.sm.add_widget(s)
        return s

    def open_dashboard(self):
        try:
            dashboard = self.ensure_dashboard()
            if dashboard is None:
                raise RuntimeError("مدیریت صفحات آماده نیست.")
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
