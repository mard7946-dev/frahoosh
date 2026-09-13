from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from mobile.config import APP_NAME, SYSTEM_TITLE, SCHOOL_NAME, PRIMARY, SECONDARY, SUCCESS, WHITE, ERROR
from mobile.ui import font_name, rtl_text, PersianTextInput


class _Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.985, 0.99, 1, 1)
            self.bg = RoundedRectangle(radius=[dp(22)])
            Color(0.84, 0.88, 0.94, 1)
            self.border = Line(rounded_rectangle=(0, 0, 0, 0, dp(22)), width=0.8)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(22))


class LoginScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._build()

    def _label(self, text, size, color, bold=False, height=None):
        kw = dict(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, bold=bold,
                  halign="right", valign="middle")
        if height is not None:
            kw.update(size_hint_y=None, height=dp(height))
        w = Label(**kw)
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=[dp(18), dp(18), dp(18), dp(12)], spacing=dp(12))
        with root.canvas.before:
            Color(0.965, 0.975, 0.99, 1)
            self.bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[dp(0)])
        root.bind(pos=lambda o, v: setattr(self.bg, "pos", v), size=lambda o, v: setattr(self.bg, "size", v))

        brand = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(128), spacing=dp(2), padding=[dp(8), 0])
        brand.add_widget(self._label(APP_NAME, "34sp", PRIMARY, True, 48))
        brand.add_widget(self._label("سامانه هوشمند آموزشی یکپارچه مدرسه", "15sp", SECONDARY, True, 34))
        brand.add_widget(self._label(SCHOOL_NAME, "12sp", PRIMARY, False, 32))
        root.add_widget(brand)

        card = _Card(orientation="vertical", padding=[dp(22), dp(20), dp(22), dp(18)], spacing=dp(10))
        card.add_widget(self._label("ورود به حساب کاربری", "22sp", PRIMARY, True, 42))
        card.add_widget(self._label("برای ورود، کد ملی و رمز عبور خود را وارد کنید.", "12sp", SECONDARY, False, 34))

        self.identifier = PersianTextInput(hint_text=rtl_text("کد ملی"), multiline=False, size_hint_y=None,
                                           height=dp(54), halign="right", padding=[dp(14), dp(14)])
        self.password = PersianTextInput(hint_text=rtl_text("رمز عبور"), password=True, password_mask="•", multiline=False,
                                         size_hint_y=None, height=dp(54), halign="right", padding=[dp(14), dp(14)])
        card.add_widget(self.identifier)
        card.add_widget(self.password)

        self.status = self._label("", "12sp", SECONDARY, False, 52)
        self.status.halign = "center"
        card.add_widget(self.status)

        self.login_button = Button(text=rtl_text("ورود امن"), font_name=font_name(), font_size="16sp", bold=True,
                                   background_normal="", background_color=PRIMARY, color=WHITE,
                                   size_hint_y=None, height=dp(54))
        self.login_button.bind(on_release=self.login)
        card.add_widget(self.login_button)
        card.add_widget(self._label("اطلاعات ورود شما فقط برای احراز هویت استفاده می‌شود.", "10sp", SECONDARY, False, 30))
        root.add_widget(card)

        root.add_widget(Widget())
        footer = self._label("FRAHOOSH  •  SCHOOL MANAGEMENT", "9sp", SECONDARY, True, 26)
        footer.halign = "center"
        root.add_widget(footer)
        self.add_widget(root)

    def _set_status(self, text, color=SECONDARY):
        self.status.text = rtl_text(text)
        self.status.color = color

    @staticmethod
    def _normalize_digits(value):
        table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        return str(value or "").translate(table)

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
        if "timeout" in lower:
            return "ارتباط با سرور زمان‌بر شد؛ دوباره تلاش کنید."
        if "network" in lower or "urlopen error" in lower:
            return "ارتباط با سرور برقرار نشد؛ اینترنت را بررسی کنید."
        return message or "ورود انجام نشد."

    def login(self, *_):
        if self._busy:
            return
        identifier = self._normalize_digits(self.identifier.text).strip()
        password = self.password.text or ""
        self.identifier.text = identifier
        if len(identifier) != 10 or not identifier.isdigit():
            self._set_status("کد ملی باید ۱۰ رقم باشد.", ERROR)
            return
        if not password:
            self._set_status("رمز عبور را وارد کنید.", ERROR)
            return
        if self.app_state is None or self.app_state.api is None:
            self._set_status("سرویس برنامه آماده نیست.", ERROR)
            return
        if not self.app_state.api.configured:
            self._set_status("تنظیمات اتصال سرور در برنامه وجود ندارد.", ERROR)
            return
        self._busy = True
        self.login_button.disabled = True
        self._set_status("در حال احراز هویت و آماده‌سازی پنل...", SECONDARY)
        Thread(target=self._authenticate, args=(identifier, password), daemon=True).start()

    def _authenticate(self, identifier, password):
        try:
            session = self.app_state.api.sign_in(identifier, password)
            if not session:
                raise RuntimeError("نشست ایجاد نشد.")
            if not self.app_state.set_session(session):
                raise RuntimeError("ذخیره نشست انجام نشد.")
            Clock.schedule_once(lambda *_: self._login_success(), 0)
        except Exception as exc:
            print("LOGIN ERROR:", repr(exc))
            msg = self._readable_error(exc)
            Clock.schedule_once(lambda *_: self._login_failed(msg), 0)

    def _login_success(self):
        self._busy = False
        self.login_button.disabled = False
        self._set_status("ورود موفق؛ پنل شما در حال آماده‌سازی است.", SUCCESS)
        try:
            app = App.get_running_app()
            if app is not None and hasattr(app, "open_dashboard") and app.open_dashboard():
                return
            if self.manager is None:
                raise RuntimeError("مدیر صفحات برنامه وجود ندارد.")
            dashboard = self.manager.get_screen("dashboard")
            if hasattr(dashboard, "refresh"):
                dashboard.refresh()
            self.manager.current = "dashboard"
        except Exception as exc:
            print("DASHBOARD ERROR:", repr(exc))
            self._set_status("ورود موفق شد، اما پنل باز نشد. دوباره تلاش کنید.", ERROR)

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
