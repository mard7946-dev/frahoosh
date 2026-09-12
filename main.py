from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, FadeTransition, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button


class StartupFallbackScreen(Screen):
    """Never-crash startup screen used only if the normal login module fails."""

    def __init__(self, error_text="", **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(
            orientation="vertical",
            padding=dp(24),
            spacing=dp(12),
        )

        root.add_widget(Label(
            text="فراهوش",
            font_size="34sp",
            bold=True,
            size_hint_y=None,
            height=dp(60),
        ))
        root.add_widget(Label(
            text="ورود کاربران",
            font_size="20sp",
            size_hint_y=None,
            height=dp(42),
        ))

        self.identifier = TextInput(
            hint_text="کد ملی",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=dp(54),
        )
        self.password = TextInput(
            hint_text="رمز عبور",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(54),
        )
        self.status = Label(
            text=error_text or "",
            size_hint_y=None,
            height=dp(70),
        )

        root.add_widget(self.identifier)
        root.add_widget(self.password)
        root.add_widget(self.status)
        root.add_widget(Button(
            text="ورود به فراهوش",
            size_hint_y=None,
            height=dp(56),
        ))
        self.add_widget(root)


class FrahooshMobileApp(App):

    title = "فراهوش"

    def build(self):
        # Keep the very first startup path deliberately small. No Supabase,
        # dashboard, school or update module is imported before the login page
        # has a chance to render.
        try:
            Window.clearcolor = (0.965, 0.975, 0.985, 1)
            Window.softinput_mode = "below_target"
        except Exception:
            pass

        manager = ScreenManager(
            transition=FadeTransition(duration=0.12)
        )

        try:
            from mobile.screens.login import LoginScreen

            state = None
            try:
                from mobile.services.app_state import AppState
                state = AppState()
            except Exception as exc:
                print("APP STATE STARTUP ERROR:", repr(exc))

            login = LoginScreen(
                state,
                name="login",
            )
            manager.add_widget(login)

        except Exception as exc:
            print("LOGIN IMPORT/BUILD ERROR:", repr(exc))
            manager.add_widget(
                StartupFallbackScreen(
                    name="login",
                    error_text="صفحه ورود اصلی آماده نشد.\n" + repr(exc),
                )
            )

        manager.current = "login"
        return manager


if __name__ == "__main__":
    FrahooshMobileApp().run()
