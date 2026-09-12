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
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(12))
        root.add_widget(Label(text="فراهوش", font_size="34sp", bold=True, size_hint_y=None, height=dp(60)))
        root.add_widget(Label(text="ورود کاربران", font_size="20sp", size_hint_y=None, height=dp(42)))
        self.identifier = TextInput(hint_text="کد ملی", multiline=False, input_filter="int", size_hint_y=None, height=dp(54))
        self.password = TextInput(hint_text="رمز عبور", password=True, multiline=False, size_hint_y=None, height=dp(54))
        self.status = Label(text=error_text or "", size_hint_y=None, height=dp(70))
        root.add_widget(self.identifier)
        root.add_widget(self.password)
        root.add_widget(self.status)
        root.add_widget(Button(text="ورود به فراهوش", size_hint_y=None, height=dp(56)))
        self.add_widget(root)


class FrahooshMobileApp(App):
    title = "فراهوش"

    def build(self):
        try:
            Window.clearcolor = (0.965, 0.975, 0.985, 1)
            Window.softinput_mode = "below_target"
        except Exception:
            pass

        self.manager = ScreenManager(transition=FadeTransition(duration=0.12))

        try:
            from mobile.screens.login import LoginScreen
            state = None
            try:
                from mobile.services.app_state import AppState
                state = AppState()
            except Exception as exc:
                print("APP STATE STARTUP ERROR:", repr(exc))
            self.app_state = state
            self.manager.add_widget(LoginScreen(name="login", app_state=state))
        except Exception as exc:
            print("LOGIN IMPORT/BUILD ERROR:", repr(exc))
            self.app_state = None
            self.manager.add_widget(StartupFallbackScreen(name="login", error_text="صفحه ورود اصلی آماده نشد."))

        self.manager.current = "login"
        return self.manager

    def ensure_dashboard(self):
        """Create the real dashboard on demand. This is the actual Android entrypoint."""
        try:
            return self.manager.get_screen("dashboard")
        except Exception:
            pass

        from mobile.screens.dashboard import DashboardScreen
        dashboard = DashboardScreen(name="dashboard", app_state=self.app_state)
        self.manager.add_widget(dashboard)
        return dashboard

    def open_dashboard(self):
        """Open dashboard after successful authentication."""
        try:
            dashboard = self.ensure_dashboard()
            if dashboard is None:
                raise RuntimeError("داشبورد ساخته نشد.")
            self.manager.current = "dashboard"
            try:
                dashboard.refresh()
            except Exception as exc:
                print("DASHBOARD REFRESH ERROR:", repr(exc))
            return True
        except Exception as exc:
            print("DASHBOARD OPEN ERROR:", repr(exc))
            return False

    def ensure_module(self):
        try:
            return self.manager.get_screen("module")
        except Exception:
            pass
        from mobile.screens.module import ModuleScreen
        module = ModuleScreen(name="module", app_state=self.app_state)
        self.manager.add_widget(module)
        return module


if __name__ == "__main__":
    FrahooshMobileApp().run()
