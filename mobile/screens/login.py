from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

from mobile.config import APP_NAME, SYSTEM_TITLE, SCHOOL_NAME, APP_SLOGAN, BACKGROUND_PATH, LOGIN_USERNAME_HINT, LOGIN_PASSWORD_HINT, PRIMARY, SECONDARY, SUCCESS, WHITE, ERROR
from mobile.ui import font_name, rtl_text, PersianTextInput


class LoginScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._build()

    def _build(self):
        Window.clearcolor = (0.95, 0.97, 0.99, 1)
        root = BoxLayout(orientation="vertical", padding=[dp(22), dp(18), dp(22), dp(18)], spacing=dp(9))
        with root.canvas.before:
            Color(0.95, 0.97, 0.99, 1); self._background = Rectangle()
            Color(0.12, 0.35, 0.62, 1); self._top_band = Rectangle()
        def sync_background(*_):
            self._background.pos = root.pos; self._background.size = root.size
            self._top_band.pos = (root.x, root.top - dp(7)); self._top_band.size = (root.width, dp(7))
        root.bind(pos=sync_background, size=sync_background)
        if BACKGROUND_PATH:
            try:
                bg = Image(source=BACKGROUND_PATH, allow_stretch=True, keep_ratio=False, opacity=0.16)
                bg.size_hint = (1, 1)
                root.add_widget(bg, index=0)
            except Exception as exc:
                print("LOGIN BACKGROUND ERROR:", repr(exc))
        root.add_widget(Label(text=rtl_text(APP_NAME), font_name=font_name(), font_size="38sp", bold=True, color=PRIMARY, size_hint_y=None, height=dp(62)))
        root.add_widget(Label(text=rtl_text(SYSTEM_TITLE), font_name=font_name(), font_size="16sp", color=SECONDARY, halign="center", valign="middle", size_hint_y=None, height=dp(38)))
        root.add_widget(Label(text=rtl_text(SCHOOL_NAME or "دبیرستان سردار حاجی زاده ۲"), font_name=font_name(), font_size="18sp", bold=True, color=PRIMARY, halign="center", valign="middle", size_hint_y=None, height=dp(48)))
        root.add_widget(Label(text=rtl_text(APP_SLOGAN), font_name=font_name(), font_size="12sp", color=SECONDARY, halign="center", valign="middle", size_hint_y=None, height=dp(30)))
        root.add_widget(Label(text=rtl_text("ورود کاربران"), font_name=font_name(), font_size="21sp", color=PRIMARY, bold=True, halign="center", valign="middle", size_hint_y=None, height=dp(42)))
        self.identifier = PersianTextInput(hint_text=rtl_text(LOGIN_USERNAME_HINT), font_size="17sp", multiline=False, size_hint_y=None, height=dp(64), halign="right", padding=[dp(16), dp(15)], background_color=(1,1,1,1), foreground_color=(0.12,0.14,0.18,1))
        self.password = PersianTextInput(hint_text=rtl_text(LOGIN_PASSWORD_HINT), password=True, password_mask="*", font_name="Roboto", font_size="17sp", multiline=False, size_hint_y=None, height=dp(64), halign="right", padding=[dp(16), dp(15)], background_color=(1,1,1,1), foreground_color=(0.12,0.14,0.18,1))
        root.add_widget(self.identifier); root.add_widget(self.password)
        self.status = Label(text="", font_name=font_name(), font_size="13sp", color=SECONDARY, halign="center", valign="middle", size_hint_y=None, height=dp(48))
        self.status.bind(size=lambda obj, value: setattr(obj, "text_size", value)); root.add_widget(self.status)
        self.login_button = Button(text=rtl_text("ورود به فراهوش"), font_name=font_name(), font_size="17sp", background_normal="", background_color=SUCCESS, color=WHITE, size_hint_y=None, height=dp(56))
        self.login_button.bind(on_release=self.login); root.add_widget(self.login_button)
        root.add_widget(Label(text=rtl_text("کد ملی ۱۰ رقمی را به‌عنوان نام کاربری وارد کنید."), font_name=font_name(), font_size="11sp", color=SECONDARY, halign="center", valign="middle"))
        self.add_widget(root)

    def _set_status(self, text, color=SECONDARY): self.status.text = rtl_text(text); self.status.color = color
    @staticmethod
    def _normalize_digits(value):
        value = str(value or ""); return value.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    @staticmethod
    def _readable_error(exc):
        message = str(exc or "").strip(); lower = message.lower()
        if "invalid login credentials" in lower: return "کد ملی یا رمز عبور صحیح نیست."
        if "email not confirmed" in lower: return "حساب کاربری هنوز تأیید نشده است."
        if "user not found" in lower: return "کاربری با این کد ملی پیدا نشد."
        if "too many requests" in lower: return "تعداد تلاش‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."
        if "timed out" in lower or "timeout" in lower: return "ارتباط با سرور زمان‌بر شد؛ دوباره تلاش کنید."
        if "urlopen error" in lower or "network" in lower: return "ارتباط با سرور برقرار نشد. اینترنت را بررسی کنید."
        if message.startswith(("ط§", "ط®", "ط§ط", "ظ")): return "خطا در ارتباط یا احراز هویت. لطفاً اطلاعات ورود را بررسی کنید."
        return message or "ورود انجام نشد."
    def login(self, *_):
        if self._busy: return
        identifier = self._normalize_digits(self.identifier.text).strip(); password = self.password.text or ""
        if identifier != self.identifier.text: self.identifier.text = identifier
        if not identifier: self._set_status("نام کاربری یا کد ملی را وارد کنید.", ERROR); return
        if len(identifier) != 10 or not identifier.isdigit(): self._set_status("نام کاربری باید کد ملی ۱۰ رقمی باشد.", ERROR); return
        if not password: self._set_status("رمز عبور را وارد کنید.", ERROR); return
        if self.app_state is None: self._set_status("وضعیت برنامه آماده نیست.", ERROR); return
        if self.app_state.api is None: self._set_status("سرویس اتصال آماده نیست.", ERROR); return
        if not self.app_state.api.configured: self._set_status("تنظیمات اتصال سرور در برنامه وجود ندارد.", ERROR); return
        self._busy = True; self.login_button.disabled = True; self._set_status("در حال بررسی اطلاعات...", SECONDARY)
        Thread(target=self._authenticate, args=(identifier, password), daemon=True).start()
    def _authenticate(self, identifier, password):
        try:
            session = self.app_state.api.sign_in(identifier, password)
            if not session: raise RuntimeError("نشست ایجاد نشد.")
            if not self.app_state.set_session(session): raise RuntimeError("ذخیره نشست انجام نشد.")
            Clock.schedule_once(lambda dt: self._login_success(), 0)
        except Exception as exc:
            print("LOGIN ERROR:", repr(exc)); message = self._readable_error(exc); Clock.schedule_once(lambda dt, msg=message: self._login_failed(msg), 0)
    def _login_success(self):
        self._busy = False; self.login_button.disabled = False; self._set_status("ورود موفق بود.", SUCCESS)
        try:
            app = App.get_running_app()
            if app is not None and hasattr(app, "open_dashboard"):
                if app.open_dashboard(): return
                raise RuntimeError("داشبورد باز نشد.")
            if self.manager:
                dashboard = self.manager.get_screen("dashboard")
                if hasattr(dashboard, "refresh"): dashboard.refresh()
                self.manager.current = "dashboard"
        except Exception as exc:
            print("DASHBOARD ERROR:", repr(exc)); self._set_status("ورود موفق شد اما داشبورد باز نشد.", ERROR)
    def _login_failed(self, message): self._busy = False; self.login_button.disabled = False; self._set_status(message, ERROR)
    def on_pre_enter(self, *args):
        self._busy = False
        try: self.login_button.disabled = False
        except Exception: pass
        return super().on_pre_enter(*args)
