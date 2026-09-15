__version__ = "1.5.5"

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.label import Label


class StartupFallback(Label):
    """Visible fallback instead of leaving the Android window black on startup errors."""

    def __init__(self, message="خطا در راه‌اندازی فراهوش", **kwargs):
        kwargs.setdefault("text", message)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("font_size", "18sp")
        super().__init__(**kwargs)
        self.bind(size=lambda obj, value: setattr(obj, "text_size", value))


class AuthScreenManager(ScreenManager):
    """ScreenManager guard: only loading and login are available without a session."""

    PUBLIC_SCREENS = {"loading", "login", "startup_error"}

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

    def _show_startup_error(self, title, exc=None):
        """Never leave the Android surface black when Python startup fails."""
        detail = ""
        if exc is not None:
            detail = f"\n\n{type(exc).__name__}: {exc}"
        message = f"{title}{detail}"
        print("STARTUP ERROR:", message)
        if self.sm is None:
            self.sm = ScreenManager()
        try:
            if self.sm.has_screen("startup_error"):
                screen = self.sm.get_screen("startup_error")
                screen.clear_widgets()
            else:
                from kivy.uix.screenmanager import Screen
                screen = Screen(name="startup_error")
                self.sm.add_widget(screen)
            screen.add_widget(StartupFallback(message=message))
            self.sm.current = "startup_error"
        except Exception as fallback_exc:
            print("STARTUP FALLBACK ERROR:", repr(fallback_exc))
            return False
        return True

    def build(self):
        self.title = "Frahoosh"
        Window.clearcolor = (0.965, 0.975, 0.985, 1)

        try:
            from mobile.services.app_state import AppState
            self.app_state = AppState()
        except Exception as exc:
            print("APP STATE STARTUP ERROR:", repr(exc))
            self.app_state = None

        self.sm = AuthScreenManager(app_state=self.app_state)

        # Build the public startup screens independently so one bad screen
        # cannot result in a completely black Android window.
        try:
            from mobile.screens.loading import LoadingScreen
            self.sm.add_widget(LoadingScreen(name="loading", app_state=self.app_state))
        except Exception as exc:
            return self._show_startup_error("خطا در ساخت صفحه آغازین برنامه", exc)

        try:
            from mobile.screens.login import LoginScreen
            self.sm.add_widget(LoginScreen(name="login", app_state=self.app_state))
        except Exception as exc:
            return self._show_startup_error("خطا در ساخت صفحه ورود", exc)

        self.sm.current = "loading"
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
                self._show_startup_error("خطا در شروع احراز هویت", exc)

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
