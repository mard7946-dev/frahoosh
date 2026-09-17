from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.carousel import Carousel
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

MANAGER = [
    ("مدیریت", "management"), ("معاون آموزشی", "educational"),
    ("معاون اجرایی", "executive"), ("معاون پرورشی", "cultural"),
    ("مشاوره", "advisor"), ("دبیران", "teachers"),
    ("اولیا", "parents"), ("دانش‌آموزان", "students"),
    ("مالی", "finance"), ("پرداخت آنلاین", "payment"),
    ("کلاس‌های آنلاین", "online"), ("آزمون آنلاین", "teacher_exams"),
    ("تابلو هوشمند", "smart_board"), ("دستیار هوش مصنوعی", "ai"),
    ("گزارش‌ها", "reports"), ("برنامه هفتگی", "schedule"),
    ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"),
    ("درباره برنامه", "about"),
]

SCHOOL_LOGO = "mobile/assets/school_logo.jpg"


class PanelFrame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(8), **kwargs)
        with self.canvas.before:
            Color(0.97, 0.98, 1.0, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class DashboardFallbackScreen(Screen):
    """Safe dashboard: fixed school header + compact lower panel frame + vertical swipe."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8)], spacing=dp(7))

        # Fixed header: logo + school name + welcome, never part of the swipe area.
        header = BoxLayout(size_hint_y=None, height=dp(96), spacing=dp(9))
        logo = Image(source=SCHOOL_LOGO, size_hint=(None, 1), width=dp(82), allow_stretch=True, keep_ratio=True)
        header.add_widget(logo)
        info = BoxLayout(orientation="vertical", spacing=dp(1))
        info.add_widget(Label(text=rtl_text(SCHOOL_NAME), font_name=font_name(), font_size="18sp",
                              color=PRIMARY, bold=True, halign="right", valign="middle"))
        info.add_widget(Label(text=rtl_text("سامانه هوشمند مدیریت مدرسه"), font_name=font_name(), font_size="11sp",
                              color=SECONDARY, halign="right", valign="middle"))
        name = str(getattr(self.app_state, "display_name", "کاربر فراهوش") or "کاربر فراهوش")
        info.add_widget(Label(text=rtl_text(f"خوش آمدید، {name}"), font_name=font_name(), font_size="13sp",
                              color=SUCCESS, bold=True, halign="right", valign="middle"))
        info.add_widget(Label(text=rtl_text(f"سال تحصیلی {SCHOOL_YEAR}"), font_name=font_name(), font_size="10sp",
                              color=SECONDARY, halign="right", valign="middle"))
        header.add_widget(info)
        root.add_widget(header)

        self.counter = Label(text=rtl_text("پنل ۱ از ۱۹"), font_name=font_name(), font_size="12sp",
                             color=SUCCESS, bold=True, size_hint_y=None, height=dp(24),
                             halign="center", valign="middle")
        root.add_widget(self.counter)

        # Only this lower frame moves. The rest of the page stays fixed.
        self.frame = PanelFrame(size_hint_y=1)
        self.carousel = Carousel(direction="top", loop=False, size_hint=(1, 1), scroll_timeout=120,
                                 scroll_distance=dp(12))
        self.carousel.bind(index=self._changed)
        for i, (title, route) in enumerate(MANAGER, 1):
            card = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(9))
            card.add_widget(Label(text=rtl_text(title), font_name=font_name(), font_size="23sp",
                                  color=PRIMARY, bold=True, halign="center", valign="middle", size_hint_y=None, height=dp(55)))
            card.add_widget(Label(text=rtl_text(f"پنل {i} از {len(MANAGER)}"), font_name=font_name(), font_size="11sp",
                                  color=SECONDARY, halign="center", valign="middle", size_hint_y=None, height=dp(28)))
            card.add_widget(Label(text=rtl_text(self.desc(route)), font_name=font_name(), font_size="13sp",
                                  color=SECONDARY, halign="center", valign="middle"))
            go = Button(text=rtl_text("ورود به پنل و اجرای عملیات"), font_name=font_name(), font_size="13sp",
                        background_normal="", background_color=PRIMARY, color=WHITE,
                        size_hint_y=None, height=dp(48))
            go.bind(on_release=lambda *_a, r=route: self.open_route(r))
            card.add_widget(go)
            self.carousel.add_widget(card)
        self.frame.add_widget(self.carousel)
        root.add_widget(self.frame)

        hint = Label(text=rtl_text("پنل‌ها را با حرکت انگشت بالا و پایین جابه‌جا کنید"), font_name=font_name(),
                     font_size="10sp", color=SECONDARY, size_hint_y=None, height=dp(22),
                     halign="center", valign="middle")
        root.add_widget(hint)
        out = Button(text=rtl_text("خروج از حساب"), font_name=font_name(), background_normal="",
                     background_color=(.65, .12, .14, 1), color=WHITE, size_hint_y=None, height=dp(40))
        out.bind(on_release=self.logout)
        root.add_widget(out)
        self.add_widget(root)

    def _changed(self, carousel, index):
        self.counter.text = rtl_text(f"پنل {int(index) + 1} از {len(MANAGER)}")

    def desc(self, route):
        return {
            "management":"مدیریت دانش‌آموزان، دبیران، کارکنان، کلاس‌ها و اطلاعات مدرسه.",
            "educational":"کلاس‌ها، حضور و غیاب، نمرات، تکالیف و برنامه آموزشی.",
            "executive":"پرونده دانش‌آموزان، اولیا، ثبت‌نام و امور اجرایی.",
            "cultural":"فعالیت‌های فرهنگی و پرورشی و رویدادها.",
            "advisor":"پرونده و پیگیری جلسات مشاوره.",
            "teachers":"فهرست دبیران و کلاس‌های آنان.",
            "students":"پرونده، نمرات و حضور و غیاب دانش‌آموزان.",
            "parents":"اولیا و وضعیت تحصیلی فرزندان.",
            "finance":"حساب‌ها، تراکنش‌ها و کمک‌های داوطلبانه.",
            "payment":"گزینه‌های پرداخت و سوابق تراکنش.",
            "online":"کلاس، جلسه، حضور و غیاب، گفت‌وگو، تخته و اطلاع غیبت.",
            "teacher_exams":"پنج نوع سؤال، تصحیح خودکار، زمان‌بندی و آزمون واقعی.",
            "smart_board":"محتوای آموزشی و ابزارهای تعاملی.",
            "ai":"پرسش و تحلیل آموزشی.",
            "reports":"گزارش‌های مدرسه و آموزشی.",
            "schedule":"برنامه هفتگی کلاس‌ها و دبیران.",
            "messages":"صندوق پیام‌ها و ارسال پیام.",
            "settings":"تنظیمات حساب و مدرسه.",
            "about":"اطلاعات برنامه و مدرسه.",
        }.get(route, "امکانات اجرایی این بخش بر اساس نقش کاربر.")

    def open_route(self, route):
        app = self.get_root_app()
        if app is None or app.sm is None:
            return
        try:
            module = app.ensure_module()
            if module is not None:
                module.set_module(route, "dashboard")
                app.sm.current = "module"
        except Exception as exc:
            print("FALLBACK DASHBOARD ROUTE ERROR:", repr(exc))

    def get_root_app(self):
        from kivy.app import App
        return App.get_running_app()

    def logout(self, *_):
        try:
            self.app_state.logout()
        except Exception:
            pass
        if self.manager:
            self.manager.current = "login"
