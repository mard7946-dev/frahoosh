from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from mobile.config import (
    SCHOOL_NAME, BACKGROUND_PATH, LOGIN_USERNAME_HINT, LOGIN_PASSWORD_HINT,
    SUCCESS, WHITE, ERROR,
)
from mobile.ui import font_name, rtl_text, PersianTextInput


NAVY = (0.025, 0.08, 0.20, 1)
FIELD = (0.025, 0.16, 0.36, 0.82)
CYAN = (0.03, 0.78, 0.94, 1)
GOLD = (0.92, 0.68, 0.20, 1)
CARD = (0.015, 0.09, 0.22, 0.90)


class LoginScreen(Screen):
    """Full-screen branded Android login with real authentication and remember-me persistence."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._build()

    def label(self, value, size="11sp", color=WHITE, bold=False, halign="right"):
        w = Label(
            text=rtl_text(str(value)),
            font_name=font_name(),
            font_size=size,
            color=color,
            bold=bold,
            halign=halign,
            valign="middle",
        )
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _field(self, hint, password=False):
        return PersianTextInput(
            hint_text=rtl_text(hint),
            password=password,
            password_mask="*",
            font_name=font_name(),
            font_size="14sp",
            multiline=False,
            size_hint_y=None,
            height=dp(43),
            halign="right",
            padding=[dp(13), dp(8)],
            background_normal="",
            background_active="",
            background_color=FIELD,
            foreground_color=WHITE,
            hint_text_color=(0.75, 0.84, 0.96, 1),
            cursor_color=CYAN,
            selection_color=(0.10, 0.50, 0.90, 0.55),
        )

    def _build(self):
        from kivy.uix.floatlayout import FloatLayout

        root = FloatLayout()

        background = Image(
            source=BACKGROUND_PATH,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        root.add_widget(background)

        card = BoxLayout(
            orientation="vertical",
            padding=[dp(17), dp(13), dp(17), dp(13)],
            spacing=dp(5),
            size_hint=(0.90, None),
            height=dp(348),
            pos_hint={"center_x": 0.5, "y": 0.16},
        )
        with card.canvas.before:
            Color(*CARD)
            panel = RoundedRectangle(radius=[dp(24)])
        card.bind(
            pos=lambda o, v: setattr(panel, "pos", v),
            size=lambda o, v: setattr(panel, "size", v),
        )

        card.add_widget(self.label("نام دبیرستان", "10sp", (0.68, 0.82, 1, 1), True))

        school_value = self.label(SCHOOL_NAME or "نام مدرسه", "13sp", WHITE, True)
        school_value.size_hint_y = None
        school_value.height = dp(31)
        with school_value.canvas.before:
            Color(0.04, 0.19, 0.39, 0.78)
            school_panel = RoundedRectangle(radius=[dp(12)])
        school_value.bind(
            pos=lambda o, v: setattr(school_panel, "pos", v),
            size=lambda o, v: setattr(school_panel, "size", v),
        )
        card.add_widget(school_value)

        card.add_widget(self.label("نام کاربری", "10sp", (0.68, 0.82, 1, 1), True))
        self.identifier = self._field(LOGIN_USERNAME_HINT)
        card.add_widget(self.identifier)

        card.add_widget(self.label("رمز عبور", "10sp", (0.68, 0.82, 1, 1), True))
        self.password = self._field(LOGIN_PASSWORD_HINT, password=True)
        card.add_widget(self.password)

        options = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(4))

        self.remember_checkbox = CheckBox(
            active=False,
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            color=CYAN,
        )
        remember_label = Button(
            text=rtl_text("مرا بخاطر بسپار"),
            font_name=font_name(),
            font_size="10sp",
            color=WHITE,
            background_normal="",
            background_color=(0, 0, 0, 0),
            size_hint=(None, 1),
            width=dp(105),
            halign="right",
            valign="middle",
        )
        remember_label.bind(on_release=self._toggle_remember)

        forgot = Button(
            text=rtl_text("فراموشی رمز"),
            font_name=font_name(),
            font_size="10sp",
            color=GOLD,
            background_normal="",
            background_color=(0, 0, 0, 0),
            halign="right",
            valign="middle",
        )
        forgot.bind(on_release=self.forgot_password)

        options.add_widget(self.remember_checkbox)
        options.add_widget(remember_label)
        options.add_widget(Widget())
        options.add_widget(forgot)
        card.add_widget(options)

        self.status = self.label("", "9sp", (0.75, 0.86, 1, 1), False, "center")
        self.status.size_hint_y = None
        self.status.height = dp(20)
        card.add_widget(self.status)

        self.login_button = Button(
            text=rtl_text("ورود"),
            font_name=font_name(),
            font_size="15sp",
            bold=True,
            background_normal="",
            background_color=CYAN,
            color=NAVY,
            size_hint_y=None,
            height=dp(45),
        )
        self.login_button.bind(on_release=self.login)
        card.add_widget(self.login_button)

        root.add_widget(card)
        self.add_widget(root)

    def _toggle_remember(self, *_):
        self.remember_checkbox.active = not self.remember_checkbox.active

    def _set_status(self, text, color=WHITE):
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
            return "نام کاربری یا رمز عبور صحیح نیست."
        if "email not confirmed" in lower:
            return "حساب کاربری هنوز تأیید نشده است."
        if "user not found" in lower:
            return "کاربری با این نام کاربری پیدا نشد."
        if "too many requests" in lower:
            return "تعداد تلاش‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."
        if "timed out" in lower or "timeout" in lower:
            return "ارتباط با سرور زمان‌بر شد؛ دوباره تلاش کنید."
        if "urlopen error" in lower or "network" in lower:
            return "ارتباط با سرور برقرار نشد. اینترنت را بررسی کنید."
        return message or "ورود انجام نشد."

    def login(self, *_):
        if self._busy:
            return
        identifier = self._normalize_digits(self.identifier.text).strip()
        password = self.password.text or ""
        remember = bool(self.remember_checkbox.active)

        if identifier != self.identifier.text:
            self.identifier.text = identifier
        if not identifier:
            self._set_status("نام کاربری یا کد ملی را وارد کنید.", ERROR)
            return
        if "@" not in identifier and (len(identifier) != 10 or not identifier.isdigit()):
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
        self._set_status("در حال بررسی اطلاعات...", (0.75, 0.86, 1, 1))
        Thread(target=self._authenticate, args=(identifier, password, remember), daemon=True).start()

    def _authenticate(self, identifier, password, remember):
        try:
            session = self.app_state.api.sign_in(identifier, password)
            if not session:
                raise RuntimeError("نشست ایجاد نشد.")
            if not self.app_state.set_session(session, remember=remember):
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

    def forgot_password(self, *_):
        if self._busy:
            return
        identifier = self._normalize_digits(self.identifier.text).strip()
        if not identifier:
            self._set_status("ابتدا نام کاربری یا کد ملی را وارد کنید.", ERROR)
            return
        if "@" not in identifier and (len(identifier) != 10 or not identifier.isdigit()):
            self._set_status("برای بازیابی رمز، کد ملی ۱۰ رقمی را وارد کنید.", ERROR)
            return
        if self.app_state is None or self.app_state.api is None or not self.app_state.api.configured:
            self._set_status("سرویس اتصال آماده نیست.", ERROR)
            return

        self._busy = True
        self.login_button.disabled = True
        self._set_status("در حال ارسال لینک بازیابی رمز...", (0.75, 0.86, 1, 1))
        Thread(target=self._send_recovery, args=(identifier,), daemon=True).start()

    def _send_recovery(self, identifier):
        try:
            self.app_state.api.send_password_recovery(identifier)
            Clock.schedule_once(lambda dt: self._recovery_success(), 0)
        except Exception as exc:
            print("PASSWORD RECOVERY ERROR:", repr(exc))
            message = self._readable_error(exc)
            Clock.schedule_once(lambda dt, msg=message: self._recovery_failed(msg), 0)

    def _recovery_success(self):
        self._busy = False
        self.login_button.disabled = False
        self._set_status("لینک بازیابی رمز به ایمیل ثبت‌شده ارسال شد.", SUCCESS)

    def _recovery_failed(self, message):
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
