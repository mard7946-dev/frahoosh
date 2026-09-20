from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.image import Image
from kivy.resources import resource_find
from kivy.uix.floatlayout import FloatLayout

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
        root = FloatLayout()

        # The agreed portrait Frahoosh artwork is the dashboard background too.
        bg_candidates = [
            "mobile/assets/frahoosh_login_mobile.jpg",
            "assets/frahoosh_login_mobile.jpg",
        ]
        bg_source = next((resource_find(x) for x in bg_candidates if resource_find(x)), None)
        if bg_source:
            background = Image(
                source=bg_source,
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0},
                allow_stretch=True,
                keep_ratio=False,
                opacity=1,
            )
            root.add_widget(background)

        # A dark translucent layer keeps the artwork visible while preserving
        # readability of the dashboard controls.
        with root.canvas.before:
            Color(0.01, 0.03, 0.09, 0.28)
            root._shade = RoundedRectangle(radius=[0])

        def sync_shade(*_):
            root._shade.pos = root.pos
            root._shade.size = root.size
        root.bind(pos=sync_shade, size=sync_shade)

        content = BoxLayout(
            orientation="vertical",
            padding=[dp(10), dp(8), dp(10), dp(8)],
            spacing=dp(6),
            size_hint=(0.94, 0.96),
            pos_hint={"center_x": 0.5, "center_y": 0.50},
        )

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(112), spacing=dp(2))
        header.add_widget(self.label(APP_NAME, "23sp", WHITE, True, True))
        header.add_widget(self.label(SCHOOL, "12sp", WHITE, True, True))
        header.add_widget(self.label("یادگیری هوشمند، مدرسه‌ای یکپارچه، آینده‌ای روشن", "8sp", WHITE, False, True))
        self.welcome = self.label("خوش آمدید", "15sp", WHITE, True, True)
        self.role_text = self.label("", "9sp", WHITE, False, True)
        header.add_widget(self.welcome)
        header.add_widget(self.role_text)
        content.add_widget(header)

        content.add_widget(self.label("پنل‌های سامانه", "14sp", WHITE, True, True))

        panel_frame = BoxLayout(
            orientation="vertical",
            padding=[dp(8), dp(8)],
            spacing=dp(6),
            size_hint_y=1,
        )
        with panel_frame.canvas.before:
            Color(0.02, 0.08, 0.18, 0.48)
            panel_frame._bg = RoundedRectangle(radius=[dp(18)])
        panel_frame.bind(
            pos=lambda o,v:setattr(panel_frame._bg, "pos", v),
            size=lambda o,v:setattr(panel_frame._bg, "size", v),
        )

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        self.panel_box = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            padding=[dp(2), dp(3)],
            size_hint_y=None,
        )
        self.panel_box.bind(minimum_height=self.panel_box.setter("height"))
        scroll.add_widget(self.panel_box)
        panel_frame.add_widget(scroll)
        content.add_widget(panel_frame)

        self.status = self.label("", "8sp", WHITE, True, True)
        content.add_widget(self.status)

        out = Button(
            text=rtl_text("خروج از حساب"),
            font_name=font_name(),
            font_script_name="Arab",
            text_language="fa",
            font_size="10sp",
            background_normal="",
            background_color=(.65, .12, .14, .92),
            color=WHITE,
            size_hint_y=None,
            height=dp(38),
        )
        out.bind(on_release=self.logout)
        content.add_widget(out)
        root.add_widget(content)
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

        # Keep the canonical 19-panel dashboard visible. Access control is
        # enforced inside each operational route; the dashboard itself remains
        # the stable mother navigation surface and is not reduced to one card.
        visible_panels = list(PANELS)

        grid = GridLayout(
            cols=2,
            spacing=dp(8),
            padding=[dp(2), dp(4)],
            size_hint_y=None,
        )
        grid.bind(minimum_height=grid.setter("height"))

        for i, (title, route) in enumerate(visible_panels, 1):
            btn = Button(
                text=rtl_text(f"{i:02d}  {title}"),
                font_name=font_name(),
                font_size="12sp",
                background_normal="",
                background_down="",
                background_color=PRIMARY,
                color=WHITE,
                font_script_name="Arab",
                text_language="fa",
                size_hint_y=None,
                height=dp(58),
            )
            btn.bind(on_release=lambda *_args, r=route: self.open(r))
            grid.add_widget(btn)

        self.panel_box.add_widget(grid)
        self.status.text = rtl_text(f"{len(visible_panels)} پنل عملیاتی • برای ورود، پنل موردنظر را لمس کنید.")
        return True

    def open(self, route):
        if route not in ACTIVE_ROUTES or not self.manager:
            return
        try:
            role=str(getattr(self.app_state,"role","student") or "student").strip().lower()
            needs_identity=role in ("student","دانش‌آموز","parent","parents","ولی","اولیا")
            confirmed=bool((getattr(self.app_state,"session",{}) or {}).get("identity_confirmed"))
            if needs_identity and not confirmed:
                # The identity-gate screen is optional in the Android build.
                # Never let a missing gate turn a normal panel tap into the
                # generic "internal panel error". If the gate exists, use it;
                # otherwise continue to the operational panel and let the
                # panel enforce its own access rules.
                gate = None
                try:
                    if hasattr(app, "ensure_identity_gate"):
                        gate = app.ensure_identity_gate()
                except Exception as gate_exc:
                    print("IDENTITY GATE ERROR:", repr(gate_exc))
                if gate is not None:
                    gate.pending_route = route
                    self.manager.current = "special_identity_gate"
                    return
            app=App.get_running_app()
            if app is None: raise RuntimeError("برنامه فراهوش آماده نیست.")
            if route=="teacher_exams" and hasattr(app,"ensure_exam"):
                screen=app.ensure_exam()
                if screen is None: raise RuntimeError("مرکز آزمون آماده نشد.")
                self.manager.current="teacher_exams"; return
            if not hasattr(app,"ensure_panel"): raise RuntimeError("سرویس پنل آماده نیست.")
            screen=app.ensure_panel()
            if screen is None: raise RuntimeError("پنل عملیاتی آماده نشد.")
            screen.set_route(route); self.manager.current="panel"
        except Exception as exc:
            # Do not put raw Python/Kivy exception text into the Persian UI.
            # It renders as squares on devices using the B Titr font and also
            # exposes implementation details to the user.
            self.status.text=rtl_text("پنل باز نشد؛ خطای فنی در گزارش برنامه ثبت شد.")
            self.status.color=(0.85,0.15,0.15,1)
            print("DASHBOARD PANEL OPEN ERROR:", repr(exc))
    def logout(self, *_):
        try:
            if self.app_state:
                self.app_state.logout()
        except Exception:
            pass
        if self.manager:
            self.manager.current = "login"
