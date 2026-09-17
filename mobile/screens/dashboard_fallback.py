from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

MANAGER = [
    ("مدیریت", "management"), ("معاون آموزشی", "educational"),
    ("معاون اجرایی", "executive"), ("معاون پرورشی", "cultural"),
    ("مشاوره", "advisor"), ("دبیران", "teachers"),
    ("اولیا", "parents"), ("دانش‌آموزان", "students"),
    ("مالی", "finance"), ("پرداخت آنلاین", "payment"),
    ("کلاس‌های آنلاین", "online"), ("آزمون آنلاین", "teacher_exams"),
    ("تابلو هوشمند", "smart_board"), ("دستیار هوش مصنوعی", "ai"),
    ("گزارش‌ها", "reports"), ("برنامه هفتگی", "schedule"),
    ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"),
    ("درباره برنامه", "about"),
]


class DashboardFallbackScreen(Screen):
    """Build-safe dashboard used only if the rich dashboard cannot be constructed."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text=rtl_text(APP_NAME), font_name=font_name(), font_size="24sp",
                              color=PRIMARY, bold=True, size_hint_y=None, height=dp(45)))
        root.add_widget(Label(text=rtl_text("سامانه هوشمند مدیریت مدرسه"), font_name=font_name(),
                              font_size="13sp", color=SECONDARY, size_hint_y=None, height=dp(32)))
        self.counter = Label(text=rtl_text("۱۹ پنل مدیریت"), font_name=font_name(), font_size="14sp",
                             color=SUCCESS, bold=True, size_hint_y=None, height=dp(32))
        root.add_widget(self.counter)
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        box = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, padding=[0, dp(4)])
        box.bind(minimum_height=box.setter("height"))
        for i, (title, route) in enumerate(MANAGER, 1):
            btn = Button(text=rtl_text(f"{i}. {title}"), font_name=font_name(), font_size="16sp",
                         background_normal="", background_color=PRIMARY, color=WHITE,
                         size_hint_y=None, height=dp(52))
            btn.bind(on_release=lambda *_a, r=route: self.open_route(r))
            box.add_widget(btn)
        scroll.add_widget(box)
        root.add_widget(scroll)
        out = Button(text=rtl_text("خروج از حساب"), font_name=font_name(), background_normal="",
                     background_color=(.65, .12, .14, 1), color=WHITE,
                     size_hint_y=None, height=dp(42))
        out.bind(on_release=self.logout)
        root.add_widget(out)
        self.add_widget(root)

    def open_route(self, route):
        app = self.get_root_app()
        if app is None or app.sm is None:
            return
        try:
            module = app.ensure_module()
            if module is not None:
                module.set_module(route, "dashboard")
                app.sm.current = "module"
        except Exception as exc:
            print("FALLBACK DASHBOARD ROUTE ERROR:", repr(exc))

    def get_root_app(self):
        from kivy.app import App
        return App.get_running_app()

    def logout(self, *_):
        try:
            self.app_state.logout()
        except Exception:
            pass
        if self.manager:
            self.manager.current = "login"
