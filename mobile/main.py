from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition

from mobile.screens.login import LoginScreen
from mobile.screens.panel_screen import PanelScreen


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

        # Preload the real operational panel workspace. Dashboard navigation
        # now switches to an already-created screen instead of dynamically
        # importing/constructing a panel at touch time.
        self.sm.add_widget(PanelScreen(name="panel", app_state=self.app_state))
        # Preload specialty operational screens so touch navigation never depends on
        # importing/building a screen inside the Android touch callback.
        try:
            from mobile.screens.smart_class_preview import SmartClassPreviewScreen
            self.sm.add_widget(SmartClassPreviewScreen(name="smart_class_preview", app_state=self.app_state))
        except Exception as exc:
            print("SMART CLASS PRELOAD ERROR:", repr(exc))
        try:
            from mobile.screens.special_modules import SpecialModuleScreen
            for _mode in ("attendance","discipline","report_cards","finance","parent_children","identity_gate"):
                self.sm.add_widget(SpecialModuleScreen(name="special_" + _mode, app_state=self.app_state, mode=_mode))
        except Exception as exc:
            print("SPECIAL MODULE PRELOAD ERROR:", repr(exc))

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

        # Students and parents must verify the real student record before
        # entering any role panel. A confirmed session can proceed normally.
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
            self.sm.current = "dashboard"
            Clock.schedule_once(self._refresh_dashboard_safe, 0.05)
            return True
        except Exception as exc:
            print("DASHBOARD NAVIGATION ERROR:", repr(exc))
            return False


if __name__ == "__main__":
    FrahooshApp().run()
