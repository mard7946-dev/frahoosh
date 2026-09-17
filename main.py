from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, FadeTransition, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image

from mobile.screens.login import LoginScreen
from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, LOGO_PATH, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

SCHOOL_LOGO = "mobile/assets/school_logo.jpg"


class BootstrapDashboard(Screen):
    """Last-resort dashboard used when the feature dashboard cannot be constructed.
    It deliberately uses only native Kivy widgets so a dashboard is always reachable
    after successful authentication. The normal dashboard remains the first choice.
    """
    MENU = [
        ("مدیریت", "management"), ("معاون آموزشی", "educational"),
        ("معاون اجرایی", "executive"), ("معاون پرورشی", "cultural"),
        ("مشاوره", "advisor"), ("دبیران", "teachers"), ("اولیا", "parents"),
        ("دانش‌آموزان", "students"), ("مالی", "finance"), ("پرداخت آنلاین", "payment"),
        ("کلاس‌های آنلاین", "online"), ("آزمون آنلاین", "teacher_exams"),
        ("تابلو هوشمند", "smart_board"), ("دستیار هوش مصنوعی", "ai"),
        ("گزارش‌ها", "reports"), ("برنامه هفتگی", "schedule"),
        ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about"),
    ]

    def __init__(self, app_state=None, error_text="", **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.error_text = error_text
        self._build()

    def _label(self, text, size="13sp", color=SECONDARY, bold=False):
        label = Label(
            text=rtl_text(text), font_name=font_name(), font_size=size,
            color=color, bold=bold, halign="center", valign="middle"
        )
        label.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        return label

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(self._label(APP_NAME, "25sp", PRIMARY, True))
        root.add_widget(self._label(SCHOOL_NAME, "15sp", PRIMARY, True))
        root.add_widget(self._label("سامانه هوشمند آموزشی یکپارچه مدرسه", "10sp"))
        self.welcome = self._label("خوش آمدید", "18sp", SUCCESS, True)
        root.add_widget(self.welcome)
        root.add_widget(self._label("پنل‌های سامانه", "14sp", PRIMARY, True))

        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView(do_scroll_x=False)
        grid = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for title, route in self.MENU:
            btn = Button(
                text=rtl_text(title), font_name=font_name(), font_size="13sp",
                background_normal="", background_color=PRIMARY, color=WHITE,
                size_hint_y=None, height=dp(44)
            )
            btn.bind(on_release=lambda *_args, r=route: self.open_route(r))
            grid.add_widget(btn)
        scroll.add_widget(grid)
        root.add_widget(scroll)

        if self.error_text:
            root.add_widget(self._label("داشبورد اصلی بارگذاری نشد؛ نسخه ایمن فعال شد.", "10sp", SECONDARY))

        logout = Button(
            text=rtl_text("خروج از حساب"), font_name=font_name(), font_size="11sp",
            background_normal="", background_color=(.65, .12, .14, 1), color=WHITE,
            size_hint_y=None, height=dp(38)
        )
        logout.bind(on_release=self.logout)
        root.add_widget(logout)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        try:
            name = str(getattr(self.app_state, "display_name", "کاربر فراهوش") or "کاربر فراهوش")
            self.welcome.text = rtl_text(f"خوش آمدید، {name}")
        except Exception:
            pass

    def open_route(self, route):
        app = App.get_running_app()
        if app is None:
            return
        try:
            if route == "about":
                screen = app.ensure_screen("about", "mobile.screens.about", "AboutScreen")
                app.sm.current = screen.name
            elif route == "teacher_exams":
                screen = app.ensure_screen("teacher_exams", "mobile.screens.teacher_exams_v4", "TeacherExamsV4Screen")
                app.sm.current = screen.name
            elif route in {"payment", "online", "messages"}:
                screen = app.ensure_screen("operations", "mobile.screens.operations", "OperationsScreen")
                if hasattr(screen, "set_route"):
                    screen.set_route(route)
                app.sm.current = screen.name
            else:
                screen = app.ensure_screen("module", "mobile.screens.module", "ModuleScreen")
                if hasattr(screen, "set_module"):
                    screen.set_module(route, "dashboard")
                app.sm.current = screen.name
        except Exception as exc:
            print("BOOTSTRAP ROUTE ERROR:", repr(exc))

    def logout(self, *_):
        try:
            if self.app_state:
                self.app_state.logout()
        except Exception:
            pass
        if self.manager:
            self.manager.current = "login"


class FrahooshApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_state = None
        self.sm = None
        self.dashboard_error = ""

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
        root = FloatLayout()
        root.add_widget(self.sm)
        try:
            logo = Image(source=SCHOOL_LOGO, size_hint=(None, None), size=(52, 52),
                         pos_hint={"right": .985, "top": .985}, opacity=.86,
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

    def ensure_screen(self, name, module_path, class_name):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen(name)
        except Exception:
            pass
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        screen = cls(name=name, app_state=self.app_state)
        self.sm.add_widget(screen)
        return screen

    def ensure_dashboard(self):
        if self.sm is None:
            return None
        try:
            return self.sm.get_screen("dashboard")
        except Exception:
            pass
        try:
            from mobile.screens.dashboard_safe import DashboardScreen
            dashboard = DashboardScreen(name="dashboard", app_state=self.app_state)
            self.sm.add_widget(dashboard)
            self.dashboard_error = ""
            return dashboard
        except Exception as exc:
            self.dashboard_error = repr(exc)
            print("DASHBOARD BUILD ERROR:", self.dashboard_error)
            try:
                dashboard = BootstrapDashboard(name="dashboard", app_state=self.app_state, error_text=self.dashboard_error)
                self.sm.add_widget(dashboard)
                return dashboard
            except Exception as fallback_exc:
                print("DASHBOARD FALLBACK ERROR:", repr(fallback_exc))
                self.dashboard_error = repr(fallback_exc)
                return None

    def ensure_exam(self):
        return self.ensure_screen("teacher_exams", "mobile.screens.teacher_exams_v4", "TeacherExamsV4Screen")

    def ensure_module(self):
        return self.ensure_screen("module", "mobile.screens.module", "ModuleScreen")

    def ensure_school(self):
        return self.ensure_screen("school", "mobile.screens.school", "SchoolScreen")

    def ensure_update(self):
        return self.ensure_screen("update", "mobile.screens.update", "UpdateScreen")

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
