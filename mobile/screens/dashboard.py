from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from mobile.config import (
    APP_NAME,
    SCHOOL_NAME,
    PRIMARY,
    SECONDARY,
    SUCCESS,
    WHITE,
)

from mobile.ui import font_name, rtl_text

ROLE_ALIASES = {
    "admin": "manager", "administrator": "manager", "manager": "manager",
    "مدیر": "manager", "مدیریت": "manager", "executive": "executive",
    "معاون اجرایی": "executive", "educational": "educational", "training": "educational",
    "معاون آموزشی": "educational", "cultural": "cultural", "پرورشی": "cultural",
    "معاون پرورشی": "cultural", "advisor": "advisor", "counselor": "advisor",
    "مشاور": "advisor", "مشاوره": "advisor", "teacher": "teacher",
    "teacher_staff": "teacher", "دبیر": "teacher", "معلم": "teacher",
    "student": "student", "دانش‌آموز": "student", "دانش آموز": "student",
    "parent": "parent", "parent_guardian": "parent", "guardian": "parent",
    "ولی": "parent", "اولیا": "parent",
}

ROLE_TITLES = {
    "manager": "مدیریت", "executive": "معاون اجرایی", "educational": "معاون آموزشی",
    "cultural": "معاون پرورشی", "advisor": "مشاوره", "teacher": "دبیر",
    "student": "دانش‌آموز", "parent": "ولی",
}

MANAGER_MENU = [
    ("مدیریت", "management"), ("معاون آموزشی", "educational"),
    ("معاون اجرایی", "executive"), ("معاون پرورشی", "cultural"),
    ("مشاوره", "advisor"), ("دبیران", "teachers"), ("اولیا", "parents"),
    ("دانش‌آموزان", "students"), ("مالی", "finance"), ("پرداخت آنلاین", "payment"),
    ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"),
    ("دستیار هوش مصنوعی", "ai"), ("گزارش‌ها", "reports"),
    ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about"),
]

ROLE_MENU = {
    "executive": [("معاون اجرایی", "executive"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "educational": [("معاون آموزشی", "educational"), ("دانش‌آموزان", "students"), ("دبیران", "teachers"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("گزارش‌ها", "reports"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "cultural": [("معاون پرورشی", "cultural"), ("دانش‌آموزان", "students"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "advisor": [("مشاوره", "advisor"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "teacher": [("پنل دبیر", "teacher"), ("دانش‌آموزان", "students"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "student": [("پنل دانش‌آموز", "student"), ("برنامه هفتگی", "schedule"), ("وضعیت تحصیلی", "student_info"), ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "parent": [("پنل اولیا", "parent"), ("وضعیت تحصیلی فرزند", "student_info"), ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
}

LIVE_ROUTES = {
    "management", "educational", "executive", "teachers", "students", "parents",
    "teacher", "student", "parent", "online", "messages", "reports", "schedule", "student_info",
}


class DashboardScreen(Screen):
    """Role dashboard with live routing for the core school workflows."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build_ui()

    def _make_label(self, text, size, color=SECONDARY, bold=False):
        label = Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, bold=bold, halign="center", valign="middle")
        label.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        return label

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[dp(18)] * 4, spacing=dp(10))
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(105), spacing=dp(4))
        header.add_widget(self._make_label(APP_NAME, "30sp", PRIMARY, True))
        header.add_widget(self._make_label("سامانه هوشمند مدیریت مدرسه", "18sp", PRIMARY, True))
        header.add_widget(self._make_label(SCHOOL_NAME, "13sp", SECONDARY))
        root.add_widget(header)

        self.welcome_label = self._make_label("خوش آمدید", "22sp", PRIMARY, True)
        self.role_label = self._make_label("", "15sp", SECONDARY)
        self.status_label = self._make_label("سامانه آماده استفاده است", "13sp", SUCCESS)
        root.add_widget(self.welcome_label)
        root.add_widget(self.role_label)
        root.add_widget(self.status_label)

        scroll = ScrollView(do_scroll_x=False)
        self.menu_box = GridLayout(cols=1, spacing=dp(9), padding=[dp(2), dp(8), dp(2), dp(8)], size_hint_y=None)
        self.menu_box.bind(minimum_height=self.menu_box.setter("height"))
        scroll.add_widget(self.menu_box)
        root.add_widget(scroll)

        logout_button = Button(text=rtl_text("خروج از حساب"), font_name=font_name(), font_size="15sp", background_normal="", background_color=(0.65, 0.12, 0.14, 1), color=WHITE, size_hint_y=None, height=dp(48))
        logout_button.bind(on_release=self.logout)
        root.add_widget(logout_button)
        self.add_widget(root)

    def _get_role(self):
        try:
            raw = self.app_state.role
        except Exception as exc:
            print("DASHBOARD ROLE ERROR:", repr(exc))
            raw = "student"
        raw = str(raw or "student").strip().lower()
        return ROLE_ALIASES.get(raw, raw)

    def _get_display_name(self):
        try:
            return str(self.app_state.display_name or "کاربر فراهوش")
        except Exception as exc:
            print("DASHBOARD NAME ERROR:", repr(exc))
            return "کاربر فراهوش"

    def refresh(self):
        role = self._get_role()
        self.welcome_label.text = rtl_text(f"خوش آمدید، {self._get_display_name()}")
        self.role_label.text = rtl_text(f"نقش کاربری: {ROLE_TITLES.get(role, 'کاربر')}")
        self.status_label.text = rtl_text("سامانه آماده استفاده است")
        self._populate_menu(role)
        return True

    def _populate_menu(self, role):
        self.menu_box.clear_widgets()
        items = MANAGER_MENU if role == "manager" else ROLE_MENU.get(role, [("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")])
        for title, route in items:
            button = Button(text=rtl_text(title), font_name=font_name(), font_size="15sp", background_normal="", background_color=(0.08, 0.30, 0.48, 1), color=WHITE, size_hint_y=None, height=dp(50))
            button.bind(on_release=lambda btn, r=route: self._menu_selected(r))
            self.menu_box.add_widget(button)

    def _menu_selected(self, route):
        if route == "about":
            self.status_label.text = rtl_text("سامانه هوشمند آموزشی یکپارچه مدرسه")
            return
        if not self.manager:
            return
        try:
            if route in LIVE_ROUTES:
                if not self.manager.has_screen("live_panel"):
                    from mobile.screens.live_panel import LivePanelScreen
                    self.manager.add_widget(LivePanelScreen(name="live_panel", app_state=self.app_state))
                panel = self.manager.get_screen("live_panel")
                panel.set_panel(route)
                self.manager.current = "live_panel"
                return

            if not self.manager.has_screen("module"):
                from mobile.screens.module import ModuleScreen
                self.manager.add_widget(ModuleScreen(name="module", app_state=self.app_state))
            module = self.manager.get_screen("module")
            if hasattr(module, "set_module"):
                module.set_module(route)
            elif hasattr(module, "load_module"):
                module.load_module(route)
            self.manager.current = "module"
        except Exception as exc:
            print("DASHBOARD NAV ERROR:", repr(exc))
            self.status_label.text = rtl_text("خطا در باز کردن بخش موردنظر.")

    def logout(self, *_):
        try:
            if self.app_state is not None:
                self.app_state.logout()
        except Exception as exc:
            print("LOGOUT ERROR:", repr(exc))
        if self.manager:
            self.manager.current = "login"
