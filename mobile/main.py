from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition

from mobile.services.app_state import AppState
from mobile.screens.login import LoginScreen
from mobile.screens.dashboard import DashboardScreen
from mobile.screens.school import SchoolScreen
from mobile.screens.update import UpdateScreen


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

        self.app_state = AppState()

        self.sm = ScreenManager(
            transition=FadeTransition(duration=0.15)
        )

        self.sm.add_widget(
            LoginScreen(
                name="login",
                app_state=self.app_state,
            )
        )

        self.sm.add_widget(
            DashboardScreen(
                name="dashboard",
                app_state=self.app_state,
            )
        )

        self.sm.add_widget(
            SchoolScreen(
                name="school",
                app_state=self.app_state,
            )
        )

        self.sm.add_widget(
            UpdateScreen(
                name="update",
                app_state=self.app_state,
            )
        )

        if self.app_state.logged_in:
            self.sm.current = "dashboard"
        else:
            self.sm.current = "login"

        return self.sm

    def on_start(self):
        if self.app_state is not None and self.app_state.logged_in:
            try:
                dashboard = self.sm.get_screen("dashboard")
                if hasattr(dashboard, "refresh"):
                    dashboard.refresh()
            except Exception as exc:
                print("DASHBOARD START ERROR:", repr(exc))


if __name__ == "__main__":
    FrahooshApp().run()
