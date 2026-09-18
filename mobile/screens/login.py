from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from mobile.config import (
    APP_VERSION, SYSTEM_TITLE, SCHOOL_NAME, APP_SLOGAN,
    LOGO_PATH, LOGIN_USERNAME_HINT, LOGIN_PASSWORD_HINT,
    PRIMARY, SECONDARY, SUCCESS, WHITE, ERROR,
)
from mobile.ui import font_name, rtl_text, PersianTextInput


NAVY = (0.035, 0.09, 0.20, 1)
BLUE = (0.07, 0.38, 0.76, 1)
CYAN = (0.04, 0.75, 0.90, 1)
GREEN = (0.10, 0.62, 0.34, 1)
CARD = (1, 1, 1, .97)


class LoginScreen(Screen):
    """Clean fixed-size branded login; one logo, one slogan, configurable school name."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._build()

    def label(self, value, size="11sp", color=SECONDARY, bold=False):
        w = Label(text=rtl_text(str(value)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="center", valign="middle")
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=[dp(18), dp(10), dp(18), dp(8)], spacing=dp(5))
        with root.canvas.before:
            Color(*NAVY)
            bg = RoundedRectangle(radius=[0])
            Color(*BLUE)
            orb1 = Ellipse()
            Color(*CYAN)
            orb2 = Ellipse()

        def sync(*_):
            bg.pos = root.pos
            bg.size = root.size
            orb1.pos = (root.right - dp(105), root.top - dp(105))
            orb1.size = (dp(155), dp(155))
            orb2.pos = (root.x - dp(65), root.y + dp(45))
            orb2.size = (dp(105), dp(105))

        root.bind(pos=sync, size=sync)

        root.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # Dedicated visual area keeps the logo centered and at a predictable size.
        hero = AnchorLayout(anchor_x="center", anchor_y="center",
                            size_hint_y=None, height=dp(176), padding=[dp(8), dp(6)])
        logo = Image(source=LOGO_PATH, size_hint=(None, None), size=(dp(148), dp(148)),
                     allow_stretch=True, keep_ratio=True)
        hero.add_widget(logo)
        root.add_widget(hero)

        # The product name appears only once: inside the logo asset.
        root.add_widget(self.label(SCHOOL_NAME or "نام مدرسه", "17sp", WHITE, True))
        root.add_widget(self.label(APP_SLOGAN, "11sp", CYAN, True))

        card = BoxLayout(orientation="vertical", padding=[dp(16), dp(12)], spacing=dp(7),
                         size_hint_y=None, height=dp(250))
        with card.canvas.before:
            Color(*CARD)
            panel = RoundedRectangle(radius=[dp(22)])
        card.bind(pos=lambda o, v: setattr(panel, "pos", v), size=lambda o, v: setattr(panel, "size", v))

        card.add_widget(self.label("ورود کاربران", "18sp", PRIMARY, True))
        self.identifier = PersianTextInput(
            hint_text=rtl_text(LOGIN_USERNAME_HINT), font_name=font_name(), font_size="14sp",
            multiline=False, size_hint_y=None, height=dp(46), halign="right",
            padding=[dp(13), dp(10)], background_color=(0.95, .97, 1, 1),
            foreground_color=NAVY, cursor_color=BLUE,
        )
        self.password = PersianTextInput(
            hint_text=rtl_text(LOGIN_PASSWORD_HINT), password=True, password_mask="*",
            font_name="Roboto", font_size="14sp", multiline=False, size_hint_y=None, height=dp(46),
            halign="right", padding=[dp(13), dp(10)], background_color=(0.95, .97, 1, 1),
            foreground_color=NAVY, cursor_color=BLUE,
        )
        card.add_widget(self.identifier)
        card.add_widget(self.password)
        self.status = self.label("", "8sp", SECONDARY, False)
        card.add_widget(self.status)
        self.login_button = Button(
            text=rtl_text("ورود به سامانه"),
            font_name=font_name(), font_size="14sp", bold=True,
            background_normal="", background_color=CYAN, color=NAVY,
            size_hint_y=None, height=dp(46),
        )
        self.login_button.bind(on_release=self.login)
        card.add_widget(self.login_button)
        root.add_widget(card)

        root.add_widget(Widget(size_hint_y=None, height=dp(2)))
        root.add_widget(self.label(f"نسخه {APP_VERSION}", "8sp", (0.64, .73, .88, 1), False))
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
        if self.app_state is None or self.app_state.api is None:
            self._set_status("سرویس اتصال آماده نیست.", ERROR)
            return
        if not self.app_state.api.configured:
            self._set_status("تنظیمات اتصال سرور در برنامه وجود ندارد.", ERROR)
            return
        self._busy = True
        self.login_button.disabled = True
        self._set_status("در حال بررسی اطلاعات...", SECONDARY)
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
