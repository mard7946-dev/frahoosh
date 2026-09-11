from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import (
    ScreenManager,
    FadeTransition,
)

from mobile.ui import register_fonts


class FrahooshMobileApp(App):

    title = "فراهوش"

    def build(self):

        Window.clearcolor = (
            0.965,
            0.975,
            0.985,
            1
        )

        try:
            register_fonts()
        except Exception as exc:
            print(
                "FONT ERROR:",
                repr(exc)
            )

        try:

            from mobile.services.app_state import (
                AppState
            )

            self.state = AppState()

        except Exception as exc:

            print(
                "APP STATE ERROR:",
                repr(exc)
            )

            self.state = None

        manager = ScreenManager(
            transition=FadeTransition(
                duration=0.12
            )
        )

        try:

            from mobile.screens.login import (
                LoginScreen
            )

            manager.add_widget(
                LoginScreen(
                    self.state,
                    name="login"
                )
            )

        except Exception as exc:

            print(
                "LOGIN SCREEN ERROR:",
                repr(exc)
            )

        try:

            from mobile.screens.dashboard import (
                DashboardScreen
            )

            manager.add_widget(
                DashboardScreen(
                    self.state,
                    name="dashboard"
                )
            )

        except Exception as exc:

            print(
                "DASHBOARD SCREEN ERROR:",
                repr(exc)
            )

        try:

            from mobile.screens.module import (
                ModuleScreen
            )

            manager.add_widget(
                ModuleScreen(
                    self.state,
                    name="module"
                )
            )

        except Exception as exc:

            print(
                "MODULE SCREEN ERROR:",
                repr(exc)
            )

        try:

            from mobile.screens.update import (
                UpdateScreen
            )

            manager.add_widget(
                UpdateScreen(
                    self.state,
                    name="update"
                )
            )

        except Exception as exc:

            print(
                "UPDATE SCREEN ERROR:",
                repr(exc)
            )

        if manager.has_screen(
            "login"
        ):

            manager.current = "login"

        elif manager.screen_names:

            manager.current = (
                manager.screen_names[0]
            )

        return manager


if __name__ == "__main__":
    FrahooshMobileApp().run()
