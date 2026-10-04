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


    def _build(self):
        """Premium Frahoosh login: school identity, clean RTL typography and touch-friendly controls."""
        from kivy.uix.floatlayout import FloatLayout

        root = FloatLayout()

        # Deep navy + Frahoosh red/gold accents keep the login visually distinct.
        with root.canvas.before:
            Color(0.025, 0.045, 0.085, 1)
            self._background = Rectangle(pos=root.pos, size=root.size)
            Color(0.70, 0.08, 0.12, 0.18)
            self._red_glow = RoundedRectangle(radius=[dp(180)])
            Color(0.95, 0.68, 0.16, 0.10)
            self._gold_glow = RoundedRectangle(radius=[dp(150)])

        def background_sync(*_):
            self._background.pos = root.pos
            self._background.size = root.size
            self._red_glow.pos = (root.x - dp(120), root.top - dp(260))
            self._red_glow.size = (dp(360), dp(260))
            self._gold_glow.pos = (root.right - dp(190), root.y - dp(80))
            self._gold_glow.size = (dp(330), dp(250))
        root.bind(pos=background_sync, size=background_sync)
        Clock.schedule_once(background_sync, 0)

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            size_hint=(0.88, 0.96),
            pos_hint={"center_x": .5, "center_y": .5},
            padding=[0, dp(4), 0, dp(4)],
        )

        logo_path = resource_find("mobile/assets/frahoosh_logo.png") or resource_find("assets/frahoosh_logo.png")
        if logo_path:
            logo_box = BoxLayout(size_hint_y=None, height=dp(74), padding=[0, dp(2)])
            logo_box.add_widget(Image(source=logo_path, allow_stretch=True, keep_ratio=True))
            content.add_widget(logo_box)

        title = Label(
            text=fa_display("فراهوش"),
            font_name=title_font_name(),
            font_size="30sp",
            bold=True,
            color=(1, 0.82, 0.32, 1),
            halign="center", valign="middle",
            size_hint_y=None, height=dp(39),
        )
        title.bind(size=lambda o, v: setattr(o, "text_size", v))
        content.add_widget(title)

        subtitle = Label(
            text=fa_display("سامانه مدیریت هوشمند یکپارچه مدرسه"),
            font_name=font_name(), font_size="10.5sp",
            color=(0.94, 0.96, 1, 1),
            halign="center", valign="middle",
            size_hint_y=None, height=dp(24),
        )
        subtitle.bind(size=lambda o, v: setattr(o, "text_size", v))
        content.add_widget(subtitle)

        school = Label(
            text=fa_display(SCHOOL_NAME),
            font_name=font_name(), font_size="8.5sp",
            color=(0.72, 0.77, 0.86, 1),
            halign="center", valign="middle",
            size_hint_y=None, height=dp(19),
        )
        school.bind(size=lambda o, v: setattr(o, "text_size", v))
        content.add_widget(school)

        # Glass-like login card with a warm top accent.
        form = BoxLayout(
            orientation="vertical",
            padding=[dp(18), dp(16), dp(18), dp(14)],
            spacing=dp(6),
            size_hint_y=None,
            height=dp(362),
        )
        with form.canvas.before:
            Color(0.98, 0.99, 1, 0.985)
            form._card = RoundedRectangle(radius=[dp(26)])
            Color(0.88, 0.64, 0.18, 0.95)
            form._accent = RoundedRectangle(radius=[dp(4)])
            Color(0.84, 0.87, 0.92, 0.8)
            form._line = Line(rounded_rectangle=(0, 0, 0, 0, dp(26)), width=0.8)

        def form_sync(*_):
            form._card.pos = form.pos
            form._card.size = form.size
            form._accent.pos = (form.x + dp(25), form.top - dp(4))
            form._accent.size = (form.width - dp(50), dp(3))
            form._line.rounded_rectangle = (form.x, form.y, form.width, form.height, dp(26))
        form.bind(pos=form_sync, size=form_sync)

        heading = Label(
            text=fa_display("خوش آمدید"),
            font_name=title_font_name(), font_size="19sp",
            color=INK, bold=True,
            halign="right", valign="middle",
            size_hint_y=None, height=dp(28),
        )
        heading.bind(size=lambda o, v: setattr(o, "text_size", v))
        form.add_widget(heading)

        desc = Label(
            text=fa_display("برای ورود به حساب فراهوش، اطلاعات خود را وارد کنید"),
            font_name=font_name(), font_size="8.5sp",
            color=MUTED, halign="right", valign="middle",
            size_hint_y=None, height=dp(20),
        )
        desc.bind(size=lambda o, v: setattr(o, "text_size", v))
        form.add_widget(desc)

        user_label = self.label("نام کاربری / کد ملی / رایانامه", "8.2sp", MUTED, True, "right")
        user_label.size_hint_y = None
        user_label.height = dp(17)
        form.add_widget(user_label)
        self.identifier = self._field(LOGIN_USERNAME_HINT or "نام کاربری یا کد ملی", False)
        form.add_widget(self.identifier)

        pass_label = self.label("رمز عبور", "8.2sp", MUTED, True, "right")
        pass_label.size_hint_y = None
        pass_label.height = dp(17)
        form.add_widget(pass_label)
        self.password = self._field(LOGIN_PASSWORD_HINT or "رمز عبور", True)
        # Keep the real password in CredentialTextInput.logical_text and render
        # an explicit ASCII asterisk mask. This avoids Android square-glyph
        # rendering while preserving the exact credential sent to Supabase.
        self.password.masked = True
        self.password.password = False
        self.password.foreground_color = INK
        form.add_widget(self.password)

        row = BoxLayout(size_hint_y=None, height=dp(27), spacing=dp(2))
        self.remember_checkbox = CheckBox(
            active=False, size_hint=(None, None), size=(dp(25), dp(25)),
            color=(0.72, 0.08, 0.12, 1),
        )
        self.remember_checkbox.bind(active=self._remember_changed)
        row.add_widget(self.remember_checkbox)
        remember = Button(
            text=fa_display("مرا به خاطر بسپار"), font_name=font_name(),
            font_size="8.2sp", color=MUTED,
            background_normal="", background_color=(0, 0, 0, 0),
        )
        remember.bind(on_press=self._toggle_remember)
        row.add_widget(remember)
        forgot = Button(
            text=fa_display("بازیابی رمز"), font_name=font_name(),
            font_size="8.2sp", color=(0.68, 0.07, 0.12, 1),
            background_normal="", background_color=(0, 0, 0, 0),
        )
        forgot.bind(on_press=self.forgot_password)
        row.add_widget(forgot)
        form.add_widget(row)

        self.login_button = Button(
            text=fa_display("ورود به فراهوش"),
            font_name=title_font_name(), font_size="13.5sp", bold=True,
            background_normal="", background_down="",
            background_color=(0.70, 0.07, 0.12, 1),
            color=WHITE, size_hint_y=None, height=dp(48),
        )
        self.login_button.bind(on_press=self.login)
        form.add_widget(self.login_button)

        self.status = self.label("", "8.2sp", MUTED, False, "center")
        self.status.size_hint_y = None
        self.status.height = dp(22)
        form.add_widget(self.status)
        content.add_widget(form)

        slogan = Label(
            text=fa_display("یادگیری هوشمند • مدرسه یکپارچه • دانش‌آموز خلاق"),
            font_name=font_name(), font_size="8.5sp",
            color=(0.93, 0.75, 0.38, 1), bold=True,
            halign="center", valign="middle",
            size_hint_y=None, height=dp(22),
        )
        slogan.bind(size=lambda o, v: setattr(o, "text_size", v))
        content.add_widget(slogan)

        footer = Label(
            text=fa_display("دبیرستان سردار شهید حاجی‌زاده ۲  •  سال تحصیلی ۱۴۰۵–۱۴۰۶"),
            font_name=font_name(), font_size="7sp",
            color=(0.58, 0.64, 0.73, 1),
            halign="center", valign="middle",
            size_hint_y=None, height=dp(18),
        )
        footer.bind(size=lambda o, v: setattr(o, "text_size", v))
        content.add_widget(footer)

        root.add_widget(content)
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
