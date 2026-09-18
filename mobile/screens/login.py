from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from mobile.config import (
    APP_NAME, APP_VERSION, SYSTEM_TITLE, SCHOOL_NAME, APP_SLOGAN,
    LOGO_PATH, LOGIN_USERNAME_HINT, LOGIN_PASSWORD_HINT,
    PRIMARY, SECONDARY, SUCCESS, WHITE, ERROR,
)
from mobile.ui import font_name, rtl_text, PersianTextInput


NAVY = (0.025, 0.075, 0.20, 1)
BLUE = (0.05, 0.34, 0.78, 1)
CYAN = (0.03, 0.78, 0.92, 1)
ORANGE = (1.0, 0.48, 0.10, 1)
GLASS = (0.05, 0.16, 0.36, .92)
FIELD = (0.04, 0.13, 0.29, .98)


class GlassPanel(BoxLayout):
    def __init__(self, bg=GLASS, radius=22, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg)
            self.rect = RoundedRectangle(radius=[dp(radius)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size


class LoginScreen(Screen):
    """Production login screen: RTL, touch-first, branded and connected to the real auth service."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._build()

    def label(self, text, size="12sp", color=WHITE, bold=False, center=True):
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

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=[dp(18), dp(12), dp(18), dp(10)], spacing=dp(7))
        with root.canvas.before:
            Color(*NAVY)
            self._bg = RoundedRectangle(radius=[0])
            Color(*BLUE)
            self._orb1 = Ellipse()
            Color(*ORANGE)
            self._orb2 = Ellipse()

        def sync(*_):
            self._bg.pos = root.pos
            self._bg.size = root.size
            self._orb1.pos = (root.right - dp(135), root.top - dp(150))
            self._orb1.size = (dp(230), dp(230))
            self._orb2.pos = (root.x - dp(90), root.y + dp(55))
            self._orb2.size = (dp(150), dp(150))

        root.bind(pos=sync, size=sync)

        # Hero / brain-and-book branding. The existing repository logo is reused;
        # no new external asset is required.
        hero = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(188), spacing=dp(0))
        logo = Image(source=LOGO_PATH, allow_stretch=True, keep_ratio=True, size_hint_y=None, height=dp(118))
        hero.add_widget(logo)
        hero.add_widget(self.label(APP_NAME, "31sp", WHITE, True))
        hero.add_widget(self.label(SYSTEM_TITLE, "9sp", (0.78, 0.87, 1, 1), False))
        root.add_widget(hero)

        # The school name intentionally comes only from config/runtime_config.json,
        # so it can be changed without touching the login UI.
        school = GlassPanel(orientation="horizontal", padding=[dp(12), dp(4)], spacing=dp(6),
                            size_hint_y=None, height=dp(48), bg=(0.08, 0.30, 0.58, .72), radius=18)
        school.add_widget(self.label(SCHOOL_NAME or "نام مدرسه", "13sp", WHITE, True))
        root.add_widget(school)

        root.add_widget(self.label(APP_SLOGAN, "11sp", CYAN, True))

        card = GlassPanel(orientation="vertical", padding=[dp(16), dp(12)], spacing=dp(7),
                          size_hint_y=None, height=dp(285), bg=GLASS, radius=24)

        card.add_widget(self.label("به فراهوش خوش آمدید", "19sp", WHITE, True))
        card.add_widget(self.label("برای ورود، اطلاعات خود را وارد کنید.", "9sp", (0.75, 0.84, .95, 1), False))

        self.identifier = PersianTextInput(
            hint_text=rtl_text(LOGIN_USERNAME_HINT),
            font_name=font_name(), font_size="14sp", multiline=False,
            size_hint_y=None, height=dp(48), halign="right",
            padding=[dp(13), dp(10)], background_color=FIELD,
            foreground_color=WHITE, cursor_color=CYAN,
        )
        self.password = PersianTextInput(
            hint_text=rtl_text(LOGIN_PASSWORD_HINT),
            password=True, password_mask="*",
            font_name="Roboto", font_size="14sp", multiline=False,
            size_hint_y=None, height=dp(48), halign="right",
            padding=[dp(13), dp(10)], background_color=FIELD,
            foreground_color=WHITE, cursor_color=CYAN,
        )
        card.add_widget(self.identifier)
        card.add_widget(self.password)

        self.status = self.label("", "9sp", (0.78, 0.87, 1, 1), False)
        card.add_widget(self.status)

        self.login_button = Button(
            text=rtl_text("ورود   →"),
            font_name=font_name(), font_size="15sp", bold=True,
            background_normal="", background_down="",
            background_color=CYAN, color=NAVY,
            size_hint_y=None, height=dp(48),
        )
        self.login_button.bind(on_release=self.login)
        card.add_widget(self.login_button)
        root.add_widget(card)

        footer = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        bio = Button(text=rtl_text("◉  ورود با اثر انگشت"), font_name=font_name(), font_size="9sp",
                     background_normal="", background_color=(0.08, .22, .43, .9), color=WHITE)
        bio.bind(on_release=lambda *_: self._set_status("ورود با اثر انگشت در این نسخه فعال نشده است.", SECONDARY))
        recovery = Button(text=rtl_text("رمز عبور را فراموش کرده‌اید؟"), font_name=font_name(), font_size="9sp",
                          background_normal="", background_color=(0.08, .22, .43, .9), color=CYAN)
        recovery.bind(on_release=lambda *_: self._set_status("بازیابی رمز عبور از طریق مدیریت سامانه انجام می‌شود.", SECONDARY))
        footer.add_widget(bio)
        footer.add_widget(recovery)
        root.add_widget(footer)

        root.add_widget(self.label(f"نسخه {APP_VERSION}  |  اندروید 156", "8sp", (0.60, 0.72, .88, 1), False))
        self.add_widget(root)

    def _set_status(self, text, color=SECONDARY):
        self.status.text = rtl_text(text)
        self.status.color = color

    @staticmethod
    def _normalize_digits(value):
        value = str(value or "")
        return value.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))

    @staticmethod
    def _readable_error(exc):
        message = str(exc or "").strip()
        lower = message.lower()
        if "invalid login credentials" in lower:
            return "کد ملی یا رمز عبور صحیح نیست."
        if "email not confirmed" in lower:
            return "حساب کاربری هنوز تأیید نشده است."
        if "user not found" in lower:
            return "کاربری با این کد ملی پیدا نشد."
        if "too many requests" in lower:
            return "تعداد تلاش‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."
        if "timed out" in lower or "timeout" in lower:
            return "ارتباط با سرور زمان‌بر شد؛ دوباره تلاش کنید."
        if "urlopen error" in lower or "network" in lower:
            return "ارتباط با سرور برقرار نشد. اینترنت را بررسی کنید."
        if message.startswith(("ط§", "ط®", "ط§ط", "ظ")):
            return "خطا در ارتباط یا احراز هویت. لطفاً اطلاعات ورود را بررسی کنید."
        return message or "ورود انجام نشد."

    def login(self, *_):
        if self._busy:
            return
        identifier = self._normalize_digits(self.identifier.text).strip()
        password = self.password.text or ""
        if identifier != self.identifier.text:
            self.identifier.text = identifier
        if not identifier:
            self._set_status("نام کاربری یا کد ملی را وارد کنید.", ERROR)
            return
        if len(identifier) != 10 or not identifier.isdigit():
            self._set_status("نام کاربری باید کد ملی ۱۰ رقمی باشد.", ERROR)
            return
        if not password:
            self._set_status("رمز عبور را وارد کنید.", ERROR)
            return
        if self.app_state is None:
            self._set_status("وضعیت برنامه آماده نیست.", ERROR)
            return
        if self.app_state.api is None:
            self._set_status("سرویس اتصال آماده نیست.", ERROR)
            return
        if not self.app_state.api.configured:
            self._set_status("تنظیمات اتصال سرور در برنامه وجود ندارد.", ERROR)
            return

        self._busy = True
        self.login_button.disabled = True
        self._set_status("در حال بررسی اطلاعات...", (0.78, 0.87, 1, 1))
        Thread(target=self._authenticate, args=(identifier, password), daemon=True).start()

    def _authenticate(self, identifier, password):
        try:
            session = self.app_state.api.sign_in(identifier, password)
            if not session:
                raise RuntimeError("نشست ایجاد نشد.")
            if not self.app_state.set_session(session):
                raise RuntimeError("ذخیره نشست انجام نشد.")
            Clock.schedule_once(lambda dt: self._login_success(), 0)
        except Exception as exc:
            print("LOGIN ERROR:", repr(exc))
            message = self._readable_error(exc)
            Clock.schedule_once(lambda dt, msg=message: self._login_failed(msg), 0)

    def _login_success(self):
        self._busy = False
        self.login_button.disabled = False
        self._set_status("ورود موفق بود.", SUCCESS)
        try:
            app = App.get_running_app()
            if app is not None and hasattr(app, "open_dashboard"):
                if app.open_dashboard():
                    return
                raise RuntimeError("داشبورد باز نشد.")
            if self.manager:
                dashboard = self.manager.get_screen("dashboard")
                if hasattr(dashboard, "refresh"):
                    dashboard.refresh()
                self.manager.current = "dashboard"
        except Exception as exc:
            print("DASHBOARD ERROR:", repr(exc))
            self._set_status("ورود موفق شد اما داشبورد باز نشد.", ERROR)

    def _login_failed(self, message):
        self._busy = False
        self.login_button.disabled = False
        self._set_status(message, ERROR)

    def on_pre_enter(self, *args):
        self._busy = False
        try:
            self.login_button.disabled = False
        except Exception:
            pass
        return super().on_pre_enter(*args)
