from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.app import App

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

SCHOOL = SCHOOL_NAME or "دبیرستان سردار شهید حاجی زاده ۲"

# The dashboard is deliberately built only from core Kivy widgets.
# Navigation must never depend on optional/complex UI widgets.
PANELS = [
    ("مدیریت", "management"),
    ("معاون آموزشی", "educational"),
    ("معاون اجرایی", "executive"),
    ("معاون پرورشی", "cultural"),
    ("مشاوره", "advisor"),
    ("دبیران", "teachers"),
    ("دانش‌آموزان", "students"),
    ("اولیا", "parents"),
    ("مالی", "finance"),
    ("پرداخت آنلاین", "payment"),
    ("کلاس‌های آنلاین", "online"),
    ("آزمون آنلاین", "teacher_exams"),
    ("تابلو هوشمند", "smart_board"),
    ("هوش مصنوعی", "ai"),
    ("گزارش‌ها", "reports"),
    ("برنامه هفتگی", "schedule"),
    ("صندوق پیام‌ها", "messages"),
    ("تنظیمات", "settings"),
    ("درباره برنامه", "about"),
]

ACTIVE_ROUTES = {route for _, route in PANELS}

ROLE_TITLES = {
    "manager": "مدیریت", "educational": "معاون آموزشی",
    "executive": "معاون اجرایی", "cultural": "معاون پرورشی",
    "advisor": "مشاوره", "teacher": "دبیر", "student": "دانش‌آموز",
    "parent": "ولی",
}

ALIASES = {
    "admin": "manager", "administrator": "manager", "مدیر": "manager", "مدیریت": "manager",
    "executive": "executive", "معاون اجرایی": "executive",
    "educational": "educational", "معاون آموزشی": "educational",
    "cultural": "cultural", "معاون پرورشی": "cultural",
    "advisor": "advisor", "مشاور": "advisor",
    "teacher": "teacher", "دبیر": "teacher", "معلم": "teacher",
    "student": "student", "دانش‌آموز": "student", "دانش آموز": "student",
    "parent": "parent", "ولی": "parent", "اولیا": "parent",
}


class DashboardScreen(Screen):
    """Stable production dashboard. Every visible panel has a direct navigation action."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build()

    def label(self, text, size="13sp", color=SECONDARY, bold=False, center=False):
        w = Label(
            text=rtl_text(str(text)),
            font_name=font_name(),
            font_size=size,
            color=color,
            bold=bold,
            halign="center" if center else "right",
            valign="middle",
        )
        w.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        return w

    def role(self):
        raw = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
        return ALIASES.get(raw, raw)

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(112), spacing=dp(3))
        header.add_widget(self.label(APP_NAME, "23sp", PRIMARY, True, True))
        header.add_widget(self.label(SCHOOL, "13sp", PRIMARY, True, True))
        header.add_widget(self.label("یادگیری هوشمند، مدرسه‌ای یکپارچه، آینده‌ای روشن", "9sp", SECONDARY, False, True))
        self.welcome = self.label("خوش آمدید", "16sp", SUCCESS, True, True)
        self.role_text = self.label("", "10sp", SECONDARY, False, True)
        header.add_widget(self.welcome)
        header.add_widget(self.role_text)
        root.add_widget(header)

        root.add_widget(self.label("پنل‌های سامانه", "15sp", PRIMARY, True, True))

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        self.panel_box = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            padding=[dp(2), dp(3)],
            size_hint_y=None,
        )
        self.panel_box.bind(minimum_height=self.panel_box.setter("height"))
        scroll.add_widget(self.panel_box)
        root.add_widget(scroll)

        self.status = self.label("", "9sp", SUCCESS, True, True)
        root.add_widget(self.status)

        out = Button(
            text=rtl_text("خروج از حساب"),
            font_name=font_name(),
            font_size="11sp",
            background_normal="",
            background_color=(.65, .12, .14, 1),
            color=WHITE,
            size_hint_y=None,
            height=dp(40),
        )
        out.bind(on_release=self.logout)
        root.add_widget(out)

        self.add_widget(root)

    def on_pre_enter(self, *_):
        if not self.app_state or not getattr(self.app_state, "logged_in", False):
            if self.manager:
                self.manager.current = "login"
            return
        self.refresh()

    def refresh(self):
        name = str(getattr(self.app_state, "display_name", "کاربر فراهوش") or "کاربر فراهوش")
        role = self.role()
        self.welcome.text = rtl_text(f"خوش آمدید، {name}")
        self.role_text.text = rtl_text(f"پنل {ROLE_TITLES.get(role, 'کاربر')} | دسترسی فعال")
        self.panel_box.clear_widgets()

        role_routes = {
            "manager": ("مدیریت", "management"),
            "educational": ("معاون آموزشی", "educational"),
            "executive": ("معاون اجرایی", "executive"),
            "cultural": ("معاون پرورشی", "cultural"),
            "advisor": ("مشاوره", "advisor"),
            "teacher": ("دبیران", "teachers"),
            "student": ("دانش‌آموزان", "students"),
            "parent": ("اولیا", "parents"),
        }
        visible_panels = [role_routes[role]] if role in role_routes else [("مدیریت", "management")]

        for i, (title, route) in enumerate(visible_panels, 1):
            btn = Button(
                text=rtl_text(f"{i:02d}  {title}"),
                font_name=font_name(),
                font_size="14sp",
                background_normal="",
                background_down="",
                background_color=PRIMARY,
                color=WHITE,
                size_hint_y=None,
                height=dp(52),
            )
            btn.bind(on_release=lambda *_args, r=route: self.open(r))
            self.panel_box.add_widget(btn)

        self.status.text = rtl_text(f"{len(visible_panels)} پنل عملیاتی • برای ورود، پنل موردنظر را لمس کنید.")
        return True

    def open(self, route):
        if route not in ACTIVE_ROUTES or not self.manager:
            return
        try:
            # Students and parents must first review and explicitly confirm the
            # student record. A discrepancy goes only through the school inbox.
            role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
            needs_identity = role in ("student", "دانش‌آموز", "parent", "parents", "ولی", "اولیا")
            confirmed = bool((getattr(self.app_state, "session", {}) or {}).get("identity_confirmed"))
            if needs_identity and not confirmed:
                gate = self.manager.get_screen("special_identity_gate")
                gate.pending_route = route
                self.manager.current = "special_identity_gate"
                return

            app = App.get_running_app()
            if app is None or not hasattr(app, "ensure_panel"):
                raise RuntimeError("سرویس پنل آماده نیست.")
            screen = app.ensure_panel()
            if screen is None:
                raise RuntimeError("پنل عملیاتی هنوز آماده نشده است.")
            screen.set_route(route)
            self.manager.current = "panel"
        except Exception as exc:
            self.status.text = rtl_text("خطای داخلی پنل: " + str(exc))
            self.status.color = (0.85, 0.15, 0.15, 1)
            print("DASHBOARD PANEL OPEN ERROR:", repr(exc))
    def logout(self, *_):
        try:
            if self.app_state:
                self.app_state.logout()
        except Exception:
            pass
        if self.manager:
            self.manager.current = "login"
