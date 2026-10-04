from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle, Ellipse
from kivy.metrics import dp
from kivy.resources import resource_find
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from mobile.config import (
    APP_NAME, SCHOOL_NAME, APP_SLOGAN, SYSTEM_TITLE, LOGIN_USERNAME_HINT, LOGIN_PASSWORD_HINT,
    SUCCESS, WHITE, ERROR,
)
from mobile.ui import font_name, title_font_name, rtl_text, fa_display, bundled_login_background, PersianTextInput, CredentialTextInput


NAVY = (0.015, 0.07, 0.18, 1)
FIELD = (0.02, 0.12, 0.30, 0.78)
CYAN = (0.03, 0.78, 0.94, 1)
GOLD = (0.95, 0.68, 0.16, 1)
RED = (0.96, 0.08, 0.12, 1)
MUTED = (0.72, 0.83, 0.96, 1)
GLASS = (0.01, 0.07, 0.20, 0.84)


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
        if password:
            field = CredentialTextInput(
                hint_text=str(hint),
                masked=True,
                font_name=font_name(),
                font_size="14sp",
                multiline=False,
                size_hint_y=None,
                height=dp(47),
                halign="right",
                padding=[dp(14), dp(9)],
                background_normal="",
                background_active="",
                background_color=(0, 0, 0, 0),
                foreground_color=WHITE,
                hint_text_color=MUTED,
                cursor_color=CYAN,
                selection_color=(0.10, 0.50, 0.90, 0.55),
            )
        else:
            field = PersianTextInput(
                hint_text=str(hint),
                password=False,
                font_name=font_name(),
                font_size="14sp",
                multiline=False,
                size_hint_y=None,
                height=dp(47),
                halign="right",
                padding=[dp(14), dp(9)],
                background_normal="",
                background_active="",
                background_color=(0, 0, 0, 0),
                foreground_color=WHITE,
                hint_text_color=MUTED,
                cursor_color=CYAN,
                selection_color=(0.10, 0.50, 0.90, 0.55),
            )
        with field.canvas.before:
            Color(*FIELD)
            field._bg = RoundedRectangle(radius=[dp(16)])
            Color(0.15, 0.58, 0.95, 0.75)
            field._border = Line(rounded_rectangle=(0, 0, 0, 0, dp(16)), width=0.9)
        def sync(*_):
            field._bg.pos = field.pos
            field._bg.size = field.size
            field._border.rounded_rectangle = (
                field.x, field.y, field.width, field.height, dp(16)
            )
        field.bind(pos=sync, size=sync)
        return field

    def _build(self):
        from kivy.uix.floatlayout import FloatLayout

        root = FloatLayout()

        # Professional entry artwork: use the bundled Frahoosh portrait with
        # a controlled dark overlay so Persian text stays crisp and readable.
        background = bundled_login_background()
        if background:
            bg = Image(source=background, allow_stretch=True, keep_ratio=False,
                       size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
            root.add_widget(bg)

        with root.canvas.before:
            Color(0.01, 0.035, 0.10, 0.72)
            self._overlay = Rectangle(pos=root.pos, size=root.size)
            Color(0.02, 0.65, 0.90, 0.10)
            self._glow1 = Ellipse()
            Color(0.95, 0.68, 0.16, 0.08)
            self._glow2 = Ellipse()

        def overlay_sync(*_):
            self._overlay.pos = root.pos
            self._overlay.size = root.size
            self._glow1.pos = (root.x - dp(80), root.top - dp(260))
            self._glow1.size = (dp(360), dp(360))
            self._glow2.pos = (root.right - dp(220), root.y + dp(80))
            self._glow2.size = (dp(300), dp(300))
        root.bind(pos=overlay_sync, size=overlay_sync)
        Clock.schedule_once(overlay_sync, 0)

        brand = BoxLayout(orientation="vertical", spacing=dp(2),
                          size_hint=(.88, .28), pos_hint={"center_x": .5, "top": .97},
                          padding=[dp(8), dp(2)])
        logo_path = resource_find("mobile/assets/frahoosh_logo.png") or resource_find("assets/frahoosh_logo.png")
        if logo_path:
            brand.add_widget(Image(source=logo_path, size_hint_y=None, height=dp(66),
                                   allow_stretch=True, keep_ratio=True))
        title = Label(text=fa_display("فراهوش"), font_name=title_font_name(),
                      font_size="28sp", bold=True, color=WHITE,
                      halign="center", valign="middle", size_hint_y=None, height=dp(42))
        title.bind(size=lambda o, v: setattr(o, "text_size", v))
        brand.add_widget(title)

        subtitle = Label(text=fa_display("سامانه هوشمند آموزشی یکپارچه مدرسه"),
                         font_name=font_name(), font_size="11sp", bold=True,
                         color=(0.80, 0.95, 1, 1), halign="center", valign="middle",
                         size_hint_y=None, height=dp(30))
        subtitle.bind(size=lambda o, v: setattr(o, "text_size", v))
        brand.add_widget(subtitle)

        school = Label(text=fa_display(SCHOOL_NAME), font_name=font_name(), font_size="10sp",
                       bold=True, color=GOLD, halign="center", valign="middle",
                       size_hint_y=None, height=dp(28))
        school.bind(size=lambda o, v: setattr(o, "text_size", v))
        brand.add_widget(school)
        root.add_widget(brand)

        card = BoxLayout(orientation="vertical", padding=[dp(20), dp(18)], spacing=dp(8),
                         size_hint=(.88, .50), pos_hint={"center_x": .5, "center_y": .39})
        with card.canvas.before:
            Color(0.018, 0.09, 0.20, 0.96)
            card._card = RoundedRectangle(radius=[dp(24)])
            Color(0.18, 0.78, 0.98, 0.78)
            card._line = Line(rounded_rectangle=(0, 0, 0, 0, dp(24)), width=1.0)

        def card_sync(*_):
            card._card.pos = card.pos
            card._card.size = card.size
            card._line.rounded_rectangle = (card.x, card.y, card.width, card.height, dp(24))
        card.bind(pos=card_sync, size=card_sync)

        welcome = Label(text=fa_display("ورود به سامانه"), font_name=title_font_name(),
                        font_size="20sp", color=WHITE, bold=True,
                        halign="center", valign="middle", size_hint_y=None, height=dp(36))
        welcome.bind(size=lambda o, v: setattr(o, "text_size", v))
        card.add_widget(welcome)

        hint = Label(text=fa_display("اطلاعات حساب کاربری خود را وارد کنید"),
                     font_name=font_name(), font_size="10sp",
                     color=(0.70, 0.82, 0.94, 1), halign="center", valign="middle",
                     size_hint_y=None, height=dp(25))
        hint.bind(size=lambda o, v: setattr(o, "text_size", v))
        card.add_widget(hint)

        self.identifier = self._field(LOGIN_USERNAME_HINT or "نام کاربری / کد ملی / رایانامه", False)
        self.password = self._field(LOGIN_PASSWORD_HINT or "رمز عبور", True)
        card.add_widget(self.identifier)
        card.add_widget(self.password)

        row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(5))
        self.remember_checkbox = CheckBox(active=False, size_hint=(None, None), size=(dp(30), dp(30)), color=CYAN)
        self.remember_checkbox.bind(active=self._remember_changed)
        row.add_widget(self.remember_checkbox)

        remember = Button(text=fa_display("مرا به خاطر بسپار"), font_name=font_name(), font_size="10.5sp",
                          color=WHITE, background_normal="", background_color=(0, 0, 0, 0))
        remember.bind(on_press=self._toggle_remember)
        row.add_widget(remember)

        forgot = Button(text=fa_display("بازیابی رمز"), font_name=font_name(), font_size="10.5sp",
                        color=GOLD, background_normal="", background_color=(0, 0, 0, 0))
        forgot.bind(on_press=self.forgot_password)
        row.add_widget(forgot)
        card.add_widget(row)

        self.login_button = Button(text=fa_display("ورود به فراهوش"), font_name=title_font_name(),
                                   font_size="15sp", bold=True,
                                   background_normal="", background_down=(0.02, 0.58, 0.78, 1), background_color=CYAN,
                                   color=(0.01, 0.06, 0.12, 1),
                                   size_hint_y=None, height=dp(54))
        self.login_button.bind(on_press=self.login)
        card.add_widget(self.login_button)

        self.status = self.label("", "9sp", MUTED, False, "center")
        self.status.size_hint_y = None
        self.status.height = dp(25)
        card.add_widget(self.status)
        root.add_widget(card)

        footer = Label(text=fa_display(f"{SCHOOL_NAME} - سال تحصیلی ۱۴۰۵–۱۴۰۶"),
                       font_name=font_name(), font_size="8sp",
                       color=(.78, .90, .98, 1), size_hint=(.92, None), height=dp(28),
                       pos_hint={"center_x": .5, "y": .025}, halign="center", valign="middle")
        footer.bind(size=lambda o, v: setattr(o, "text_size", v))
        root.add_widget(footer)
        self.add_widget(root)

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
