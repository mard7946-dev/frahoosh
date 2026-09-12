from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition

from mobile.services.app_state import AppState
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

        try:
            self.app_state = AppState()
        except Exception as exc:
            print("APP STATE INIT ERROR:", repr(exc))
            self.app_state = None

        self.sm = ScreenManager(
            transition=FadeTransition(duration=0.15)
        )

        # IMPORTANT: build only the login screen at startup.
        # Other screens are loaded lazily after successful login so a
        # dashboard/module import error can never prevent the login page.
        self.sm.add_widget(
            LoginScreen(
                name="login",
                app_state=self.app_state,
            )
        )

        self.sm.current = "login"
        return self.sm

    def ensure_dashboard(self):
        if self.sm is None:
            return None

        try:
            dashboard = self.sm.get_screen("dashboard")
            return dashboard
        except Exception:
            pass

        from mobile.screens.dashboard import DashboardScreen

        dashboard = DashboardScreen(
            name="dashboard",
            app_state=self.app_state,
        )
        self.sm.add_widget(dashboard)
        return dashboard

    def ensure_school(self):
        if self.sm is None:
            return None

        try:
            return self.sm.get_screen("school")
        except Exception:
            pass

        from mobile.screens.school import SchoolScreen

        screen = SchoolScreen(
            name="school",
            app_state=self.app_state,
        )
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

        screen = UpdateScreen(
            name="update",
            app_state=self.app_state,
        )
        self.sm.add_widget(screen)
        return screen

    def open_dashboard(self):
        try:
            dashboard = self.ensure_dashboard()
            if dashboard is None:
                raise RuntimeError("مدیریت صفحات آماده نیست.")

            if hasattr(dashboard, "refresh"):
                dashboard.refresh()

            self.sm.current = "dashboard"
            return True
        except Exception as exc:
            print("DASHBOARD OPEN ERROR:", repr(exc))
            return False


if __name__ == "__main__":
    FrahooshApp().run()
