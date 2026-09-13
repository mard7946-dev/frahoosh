from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from mobile.config import APP_NAME, SYSTEM_TITLE, SCHOOL_NAME, PRIMARY, SECONDARY, SUCCESS, WHITE, ERROR
from mobile.ui import font_name, rtl_text, PersianTextInput


class _Surface(BoxLayout):
    def __init__(self, fill=(1, 1, 1, 1), radius=24, **kwargs):
        super().__init__(**kwargs)
        self._radius = dp(radius)
        with self.canvas.before:
            Color(*fill)
            self._bg = RoundedRectangle(radius=[self._radius])
            Color(0.84, 0.88, 0.93, 1)
            self._line = Line(rounded_rectangle=(0, 0, 0, 0, self._radius), width=0.7)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._line.rounded_rectangle = (self.x, self.y, self.width, self.height, self._radius)


class LoginScreen(Screen):
    """Professional, school-neutral login. School name is supplied by runtime_config.json."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._build()

    def _label(self, text, size, color, bold=False, height=None, halign="right"):
        kw = dict(text=rtl_text(text), font_name=font_name(), font_size=size, color=color,
                  bold=bold, halign=halign, valign="middle")
        if height is not None:
            kw.update(size_hint_y=None, height=dp(height))
        w = Label(**kw)
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=[dp(18), dp(22), dp(18), dp(12)], spacing=dp(12))
        with root.canvas.before:
            Color(0.955, 0.968, 0.982, 1)
            self._background = RoundedRectangle(pos=root.pos, size=root.size)
            Color(0.12, 0.35, 0.62, 0.08)
            self._orb1 = Ellipse(pos=(0, 0), size=(dp(180), dp(180)))
            Color(0.05, 0.55, 0.48, 0.06)
            self._orb2 = Ellipse(pos=(0, 0), size=(dp(140), dp(140)))
        root.bind(pos=self._sync_background, size=self._sync_background)

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(150), spacing=dp(3), padding=[dp(8), dp(4)])
        mark = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(9))
        badge = Label(text="F", font_name=font_name(), font_size="25sp", bold=True, color=WHITE,
                      size_hint_x=None, width=dp(54), halign="center", valign="middle")
        with badge.canvas.before:
            Color(*PRIMARY)
            badge_bg = RoundedRectangle(radius=[dp(15)])
        badge.bind(pos=lambda o,v:setattr(badge_bg,"pos",v), size=lambda o,v:setattr(badge_bg,"size",v))
        mark.add_widget(badge)
        brand_text = BoxLayout(orientation="vertical")
        brand_text.add_widget(self._label(APP_NAME, "25sp", PRIMARY, True, 31))
        brand_text.add_widget(self._label("SMART SCHOOL PLATFORM", "9sp", SECONDARY, True, 22, "left"))
        mark.add_widget(brand_text)
        header.add_widget(mark)
        header.add_widget(self._label(SCHOOL_NAME, "15sp", PRIMARY, True, 30, "center"))
        header.add_widget(self._label(SYSTEM_TITLE, "11sp", SECONDARY, False, 28, "center"))
        root.add_widget(header)

        card = _Surface(fill=(0.995, 0.998, 1, 1), radius=26,
                        orientation="vertical", padding=[dp(22), dp(20), dp(22), dp(18)], spacing=dp(10))
        card.add_widget(self._label("ورود به سامانه", "23sp", PRIMARY, True, 40))
        card.add_widget(self._label("با حساب سازمانی خود وارد شوید", "12sp", SECONDARY, False, 30))

        self.identifier = PersianTextInput(hint_text=rtl_text("کد ملی"), multiline=False,
                                           size_hint_y=None, height=dp(54), halign="right",
                                           padding=[dp(14), dp(14)])
        self.password = PersianTextInput(hint_text=rtl_text("رمز عبور"), password=True,
                                         password_mask="•", multiline=False, size_hint_y=None,
                                         height=dp(54), halign="right", padding=[dp(14), dp(14)])
        card.add_widget(self.identifier)
        card.add_widget(self.password)

        self.status = self._label("", "11sp", SECONDARY, False, 48, "center")
        card.add_widget(self.status)

        self.login_button = Button(text=rtl_text("ورود امن"), font_name=font_name(), font_size="16sp",
                                   bold=True, background_normal="", background_color=PRIMARY,
                                   color=WHITE, size_hint_y=None, height=dp(54))
        self.login_button.bind(on_release=self.login)
        card.add_widget(self.login_button)
        card.add_widget(self._label("اتصال رمزگذاری‌شده  •  احراز هویت سامانه مدرسه", "9sp", SECONDARY, False, 28, "center"))
        root.add_widget(card)

        root.add_widget(Widget())
        footer = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(55), spacing=dp(2))
        footer.add_widget(self._label("فراهوش  |  سامانه هوشمند آموزشی یکپارچه مدرسه", "10sp", SECONDARY, True, 27, "center"))
        footer.add_widget(self._label("نسخه سازمانی", "8sp", SECONDARY, False, 20, "center"))
        root.add_widget(footer)
        self.add_widget(root)

    def _sync_background(self, widget, value):
        self._background.pos = value
        self._background.size = widget.size
        self._orb1.pos = (widget.x - dp(70), widget.top - dp(120))
        self._orb2.pos = (widget.right - dp(80), widget.y - dp(30))

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
        self._set_status("در حال احراز هویت و آماده‌سازی پنل…", SECONDARY)
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
        self._set_status("ورود موفق؛ پنل شما آماده است.", SUCCESS)
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
