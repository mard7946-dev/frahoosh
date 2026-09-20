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
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from pathlib import Path

from mobile.config import (
    APP_NAME, SCHOOL_NAME, APP_SLOGAN, SYSTEM_TITLE, LOGIN_USERNAME_HINT, LOGIN_PASSWORD_HINT,
    SUCCESS, WHITE, ERROR,
)
from mobile.ui import font_name, rtl_text, PersianTextInput


NAVY = (0.015, 0.07, 0.18, 1)
FIELD = (0.02, 0.12, 0.30, 0.78)
CYAN = (0.03, 0.78, 0.94, 1)
GOLD = (0.95, 0.68, 0.16, 1)
RED = (0.96, 0.08, 0.12, 1)
MUTED = (0.72, 0.83, 0.96, 1)
GLASS = (0.01, 0.07, 0.20, 0.84)


class LoginScreen(Screen):
    """Responsive Android login. Authentication and remember-me use the real app services."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._auto_login_checked = False
        self._build()

    def label(self, value, size="11sp", color=WHITE, bold=False, halign="right"):
        w = Label(
            text=rtl_text(str(value)),
            font_name=font_name(),
            font_script_name="Arab",
            text_language="fa",
            font_size=size,
            color=color,
            bold=bold,
            halign=halign,
            valign="middle",
        )
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _field(self, hint, password=False):
        field = PersianTextInput(
            hint_text=rtl_text(hint),
            password=password,
            password_mask="*",
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

        root=FloatLayout()
        with root.canvas.before:
            Color(0.015,0.06,0.16,1); self._bg=Rectangle(pos=root.pos,size=root.size)
            Color(0.03,0.30,0.58,0.30); self._glow1=RoundedRectangle(radius=[dp(180)])
            Color(0.00,0.78,0.94,0.16); self._glow2=RoundedRectangle(radius=[dp(150)])
        def sync(*_):
            self._bg.pos=root.pos; self._bg.size=root.size
            self._glow1.pos=(root.width*.48,root.height*.67); self._glow1.size=(root.width*.62,root.width*.62)
            self._glow2.pos=(-root.width*.28,root.height*.15); self._glow2.size=(root.width*.56,root.width*.56)
        root.bind(pos=sync,size=sync); Clock.schedule_once(sync,0)

        title=Label(text=rtl_text("فراهوش"),font_name=font_name(),font_size="30sp",bold=True,color=WHITE,
                    size_hint=(.94,None),height=dp(48),pos_hint={"center_x":.5,"center_y":.86},halign="center")
        title.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(title)
        subtitle=Label(text=rtl_text("سامانه هوشمند آموزشی یکپارچه مدرسه"),font_name=font_name(),font_size="12sp",bold=True,
                      color=CYAN,size_hint=(.94,None),height=dp(34),pos_hint={"center_x":.5,"center_y":.815},halign="center")
        subtitle.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(subtitle)
        slogan=Label(text=rtl_text("یادگیری هوشمند، مدرسه یکپارچه، دانش آموز خلاق"),font_name=font_name(),font_size="10sp",
                     color=MUTED,size_hint=(.94,None),height=dp(30),pos_hint={"center_x":.5,"center_y":.775},halign="center")
        slogan.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(slogan)
        school=Label(text=rtl_text("دبیرستان سردار شهید حاجی زاده ۲"),font_name=font_name(),font_size="10sp",bold=True,
                     color=GOLD,size_hint=(.94,None),height=dp(30),pos_hint={"center_x":.5,"center_y":.735},halign="center")
        school.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(school)

        card=BoxLayout(orientation="vertical",padding=[dp(22),dp(20)],spacing=dp(9),
                       size_hint=(.88,.48),pos_hint={"center_x":.5,"center_y":.47})
        with card.canvas.before:
            Color(0.01,0.09,0.22,0.93); card._card=RoundedRectangle(radius=[dp(28)])
            Color(0.04,0.66,0.92,0.65); card._line=Line(rounded_rectangle=(0,0,0,0,dp(28)),width=1.2)
        def card_sync(*_):
            card._card.pos=card.pos; card._card.size=card.size
            card._line.rounded_rectangle=(card.x,card.y,card.width,card.height,dp(28))
        card.bind(pos=card_sync,size=card_sync)

        welcome=Label(text=rtl_text("ورود به حساب کاربری"),font_name=font_name(),font_size="18sp",
                      color=WHITE,bold=True,size_hint_y=None,height=dp(38),halign="center")
        welcome.bind(size=lambda o,v:setattr(o,"text_size",v)); card.add_widget(welcome)
        self.identifier=self._field(LOGIN_USERNAME_HINT or "نام کاربری / کد ملی / ایمیل",False)
        self.password=self._field(LOGIN_PASSWORD_HINT or "رمز عبور",True)
        card.add_widget(self.identifier); card.add_widget(self.password)

        row=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(5))
        self.remember_checkbox=CheckBox(active=False,size_hint=(None,None),size=(dp(30),dp(30)),color=CYAN)
        self.remember_checkbox.bind(active=self._remember_changed); row.add_widget(self.remember_checkbox)
        remember=Button(text=rtl_text("مرا به خاطر بسپار"),font_name=font_name(),font_size="10sp",color=WHITE,background_normal="",background_color=(0,0,0,0))
        remember.bind(on_release=self._toggle_remember); row.add_widget(remember)
        forgot=Button(text=rtl_text("فراموشی رمز"),font_name=font_name(),font_size="10sp",color=GOLD,background_normal="",background_color=(0,0,0,0))
        forgot.bind(on_release=self.forgot_password); row.add_widget(forgot)
        card.add_widget(row)

        self.login_button=Button(text=rtl_text("ورود به فراهوش"),font_name=font_name(),font_size="16sp",bold=True,
                                 background_normal="",background_color=CYAN,color=(0.01,0.06,0.12,1),
                                 size_hint_y=None,height=dp(52))
        self.login_button.bind(on_release=self.login); card.add_widget(self.login_button)
        self.status=self.label("", "9sp", MUTED, False, "center")
        self.status.size_hint_y=None; self.status.height=dp(26); card.add_widget(self.status)
        root.add_widget(card)

        footer=Label(text=rtl_text(f"{SCHOOL_NAME} • سال تحصیلی ۱۴۰۵–۱۴۰۶"),font_name=font_name(),font_size="8sp",
                     color=(.60,.78,.92,1),size_hint=(.92,None),height=dp(28),pos_hint={"center_x":.5,"y":.035},halign="center")
        footer.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(footer)
        self.add_widget(root)

    def _remember_changed(self, *_args):
        # The checkbox is the source of truth. AppState persists the session
        # only when this value is true.
        pass

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
            return "کاربری با این مشخصات پیدا نشد."
        if "pgrst202" in lower or "could not find the function" in lower:
            return "سرویس ورود با کد ملی روی سرور فعال نشده است."
        if "permission denied" in lower or "not allowed" in lower:
            return "دسترسی سرویس ورود از سرور مجاز نیست."
        if "too many requests" in lower:
            return "تعداد تلاش‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."
        if "timed out" in lower or "timeout" in lower:
            return "ارتباط با سرور زمان‌بر شد؛ دوباره تلاش کنید."
        if "urlopen error" in lower or "network" in lower:
            return "ارتباط با سرور برقرار نشد. اینترنت را بررسی کنید."
        # Never render raw exception payloads on the Persian login screen.
        # They can contain URLs, ASCII diagnostics, or unsupported glyphs.
        return "ارتباط با سرور برقرار نشد. دوباره تلاش کنید."

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
        self._set_status("در حال بررسی اطلاعات...", MUTED)
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

        # Real remember-me behavior: a previously persisted session is reused.
        if not self._auto_login_checked:
            self._auto_login_checked = True
            try:
                session = self.app_state.session if self.app_state else {}
                if (
                    isinstance(session, dict)
                    and session.get("remember_me") is True
                    and self.app_state.logged_in
                ):
                    self._set_status("در حال ورود خودکار...", MUTED)
                    Clock.schedule_once(lambda dt: self._open_saved_session(), 0.15)
            except Exception as exc:
                print("AUTO LOGIN CHECK ERROR:", repr(exc))

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
