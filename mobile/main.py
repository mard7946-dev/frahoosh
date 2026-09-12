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

        try:
            Window.softinput_mode = "below_target"
        except Exception:
            pass

        self.sm = ScreenManager(
            transition=FadeTransition(duration=0.15)
        )

        try:
            from mobile.services.app_state import AppState
            self.app_state = AppState()
        except Exception as exc:
            print("APP STATE STARTUP ERROR:", repr(exc))
            self.app_state = None

        self.sm.add_widget(
            LoginScreen(
                name="login",
                app_state=self.app_state,
            )
        )

        self.sm.current = "login"
        Clock.schedule_once(self._startup_check, 0)
        return self.sm

    def _startup_check(self, *_):
        try:
            self.sm.current = "login"
        except Exception as exc:
            print("LOGIN SCREEN START ERROR:", repr(exc))

    def ensure_dashboard(self):
        if self.sm is None:
            return None

        try:
            return self.sm.get_screen("dashboard")
        except Exception:
            pass

        from mobile.screens.dashboard import DashboardScreen
        dashboard = DashboardScreen(
            name="dashboard",
            app_state=self.app_state,
        )
        self.sm.add_widget(dashboard)
        return dashboard

    def ensure_module(self):
        if self.sm is None:
            return None

        try:
            return self.sm.get_screen("module")
        except Exception:
            pass

        from mobile.screens.module import ModuleScreen
        module = ModuleScreen(
            name="module",
            app_state=self.app_state,
        )
        self.sm.add_widget(module)
        return module

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

    def open_dashboard(self):
        try:
            dashboard = self.ensure_dashboard()
            if dashboard is None:
                raise RuntimeError("مدیریت صفحات آماده نیست.")

            # ModuleScreen is required by the dashboard drawer. Create it
            # before switching so every menu item can actually open.
            self.ensure_module()

            if hasattr(dashboard, "refresh"):
                dashboard.refresh()

            self.sm.current = "dashboard"
            return True
        except Exception as exc:
            print("DASHBOARD OPEN ERROR:", repr(exc))
            return False


if __name__ == "__main__":
    FrahooshApp().run()
