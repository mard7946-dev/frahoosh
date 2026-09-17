from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image

from mobile.screens.login import LoginScreen
from mobile.config import SCHOOL_YEAR

SCHOOL_LOGO = "mobile/assets/school_logo.jpg"


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
        self.sm = ScreenManager(transition=FadeTransition(duration=.15))
        try:
            from mobile.services.app_state import AppState
            self.app_state = AppState()
        except Exception as exc:
            print("APP STATE STARTUP ERROR:", repr(exc))
            self.app_state = None
        self.sm.add_widget(LoginScreen(name="login", app_state=self.app_state))
        self.sm.current = "login"

        # School logo is a non-interactive watermark/header mark visible above every screen.
        root = FloatLayout()
        root.add_widget(self.sm)
        try:
            logo = Image(source=SCHOOL_LOGO, size_hint=(None, None), size=(56, 56),
                         pos_hint={"right": 0.985, "top": 0.985}, opacity=0.82,
                         allow_stretch=True, keep_ratio=True)
            logo.disabled = True
            root.add_widget(logo)
            self.school_logo = logo
        except Exception as exc:
            print("SCHOOL LOGO ERROR:", repr(exc))
        Clock.schedule_once(self._startup_check, 0)
        return root

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
        try:
            from mobile.screens.dashboard3 import DashboardScreen
            dashboard = DashboardScreen(name="dashboard", app_state=self.app_state)
            self.sm.add_widget(dashboard)
            return dashboard
        except Exception as exc:
            print("DASHBOARD BUILD ERROR:", repr(exc))
            try:
                from mobile.screens.dashboard_fallback import DashboardFallbackScreen
                dashboard = DashboardFallbackScreen(name="dashboard", app_state=self.app_state)
                self.sm.add_widget(dashboard)
                return dashboard
            except Exception as fallback_exc:
                print("DASHBOARD FALLBACK BUILD ERROR:", repr(fallback_exc))
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
            if hasattr(dashboard, "refresh"):
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
        try:
            self._set_screen_capture_policy()
            self.sm.current = "dashboard"
            Clock.schedule_once(self._refresh_dashboard_safe, 0.05)
            return True
        except Exception as exc:
            print("DASHBOARD NAVIGATION ERROR:", repr(exc))
            return False


if __name__ == "__main__":
    FrahooshApp().run()
