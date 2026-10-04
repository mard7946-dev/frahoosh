from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
from kivy.metrics import dp
from kivy.resources import resource_find
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from mobile.config import (
    APP_NAME, SCHOOL_NAME, APP_SLOGAN, SYSTEM_TITLE, LOGIN_USERNAME_HINT, LOGIN_PASSWORD_HINT,
    SUCCESS, WHITE, ERROR,
)
from mobile.ui import font_name, title_font_name, fa_display, PersianTextInput, CredentialTextInput



INK = (0.055, 0.10, 0.18, 1)
MUTED = (0.39, 0.46, 0.56, 1)
BLUE = (0.06, 0.43, 0.86, 1)
BLUE_DARK = (0.035, 0.24, 0.58, 1)
FIELD_BG = (0.965, 0.978, 0.995, 1)
BORDER = (0.84, 0.88, 0.94, 1)
WHITE = (1, 1, 1, 1)

class LoginScreen(Screen):
    # Credential fields use LTR direction for account identifiers.
    """Responsive Android login. Authentication and remember-me use the real app services."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._auto_login_checked = False
        self._build()

    def label(self, value, size="11sp", color=WHITE, bold=False, halign="right"):
        w = Label(
            text=fa_display(str(value)),
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
        common = dict(
            hint_text=str(hint), font_name=font_name(), font_size="13sp", multiline=False,
            size_hint_y=None, height=dp(46), halign="right", padding=[dp(13), dp(9)],
            background_normal="", background_active="", background_color=(0, 0, 0, 0),
            foreground_color=INK, hint_text_color=(0.56, 0.62, 0.70, 1),
            cursor_color=BLUE, selection_color=(0.10, 0.43, 0.86, 0.18),
        )
        if password:
            field = CredentialTextInput(masked=True, **common)
        else:
            field = PersianTextInput(password=False, **common)
        with field.canvas.before:
            Color(*FIELD_BG)
            field._bg = RoundedRectangle(radius=[dp(13)])
            Color(*BORDER)
            field._border = Line(rounded_rectangle=(0, 0, 0, 0, dp(13)), width=0.8)
        def sync(*_):
            field._bg.pos = field.pos; field._bg.size = field.size
            field._border.rounded_rectangle = (field.x, field.y, field.width, field.height, dp(13))
        field.bind(pos=sync, size=sync)
        return field

    def _remember_changed(self, *_args):
        pass

    def _toggle_remember(self, *_):
        self.remember_checkbox.active = not self.remember_checkbox.active

    def _set_status(self, text, color=WHITE):
        self.status.text = fa_display(text)
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
            return "کاربری با این مشخصات پیدا نشد."
        if "pgrst202" in lower or "could not find the function" in lower:
            return "سرویس ورود با کد ملی روی سرور فعال نشده است."
        if "permission denied" in lower or "not allowed" in lower:
            return "دسترسی سرویس ورود از سرور مجاز نیست."
        if "too many requests" in lower:
            return "تعداد تلاش‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."
        if "timed out" in lower or "timeout" in lower:
            return "ارتباط با سرور زمان‌بر شد؛ دوباره تلاش کنید."
        if "urlopen error" in lower or "network" in lower or "certificate" in lower or "dns" in lower:
            return "ارتباط با سرور برقرار نشد. اینترنت و دسترسی شبکه را بررسی کنید."
        if message and any("\u0600" <= ch <= "\u06ff" for ch in message):
            return message
        return "خطای ورود: " + message if message else "خطای ورود؛ دوباره تلاش کنید."

    def login(self, *_):
        if self._busy:
            return
        identifier = self._normalize_digits(self.identifier.text).strip()
        password = self.password.get_logical_text() if hasattr(self.password, "get_logical_text") else (self.password.text or "")
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
        self._set_status("در حال بررسی اطلاعات...", MUTED)
        Thread(target=self._authenticate, args=(identifier, password, remember), daemon=True).start()

    def _authenticate(self, identifier, password, remember):
        try:
            session = self.app_state.api.sign_in(identifier, password)
            if not session:
                raise RuntimeError("نشست ایجاد نشد.")
            session["login_identifier"] = self._normalize_digits(identifier).strip()
            self.app_state.set_session(session, remember=remember)
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
        self._set_status(message if message and len(str(message)) < 120 else "ارتباط با سرور برقرار نشد. دوباره تلاش کنید.", ERROR)

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
        self._set_status("در حال ارسال لینک بازیابی رمز...", MUTED)
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
        self._auto_login_checked = True
        try:
            if self.app_state is not None and getattr(self.app_state, "logged_in", False):
                self.app_state.logout()
        except Exception:
            pass
        return super().on_pre_enter(*args)

    def _open_saved_session(self):
        try:
            app = App.get_running_app()
            if app is not None and hasattr(app, "open_dashboard"):
                if app.open_dashboard():
                    return
            self._set_status("نشست ذخیره‌شده دیگر معتبر نیست.", ERROR)
            if self.app_state:
                self.app_state.logout()
        except Exception as exc:
            print("AUTO LOGIN ERROR:", repr(exc))
            self._set_status("ورود خودکار انجام نشد.", ERROR)
