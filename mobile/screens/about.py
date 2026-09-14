from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_ID, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

APP_VERSION = "1.5.2"
PRODUCER = "حسن مردانه جهان تیغ"
SUPPORT = "۰۹۳۷۷۳۲۹۹۱۲"


class AboutScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build()

    def _label(self, text, size="15sp", color=SECONDARY, height=52, bold=False):
        w = Label(
            text=rtl_text(text), font_name=font_name(), font_size=size,
            color=color, bold=bold, halign="right", valign="middle",
            size_hint_y=None, height=dp(height), padding=(dp(8), dp(4)),
        )
        w.bind(size=lambda o, v: setattr(o, "text_size", (v[0] - dp(16), None)))
        return w

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        head = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(54), spacing=dp(8))
        back = Button(
            text=rtl_text("‹ بازگشت"), font_name=font_name(), font_size="14sp",
            background_normal="", background_color=PRIMARY, color=WHITE,
            size_hint_x=None, width=dp(105),
        )
        back.bind(on_release=self.go_back)
        head.add_widget(back)
        title = self._label("درباره برنامه", "21sp", PRIMARY, 54, True)
        head.add_widget(title)
        root.add_widget(head)

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(6), size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        school = SCHOOL_NAME or "نام مدرسه"
        school_code = f"کد مدرسه: {SCHOOL_ID}" if SCHOOL_ID else "کد مدرسه: در تنظیمات مدرسه تعیین نشده است"
        year = SCHOOL_YEAR or "۱۴۰۵-۱۴۰۶"
        rows = [
            ("نام برنامه", APP_NAME),
            ("سازنده", PRODUCER),
            ("ورژن برنامه", APP_VERSION),
            ("سازگاری", "Android 7.0 و بالاتر (API 24+)، نسخه بهینه‌شده برای گوشی و تبلت"),
            ("سال تولید", year),
            ("مدرسه فعال", school),
            ("شناسه / کد مدرسه", school_code),
            ("پشتیبانی و خرید اشتراک", SUPPORT),
        ]
        for key, value in rows:
            card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(76), padding=dp(6), spacing=dp(2))
            card.add_widget(self._label(key, "12sp", SECONDARY, 26, True))
            card.add_widget(self._label(value, "15sp", PRIMARY if key in ("نام برنامه", "ورژن برنامه") else SECONDARY, 44))
            body.add_widget(card)

        note = self._label(
            "این نسخه برای استقرار در مدارس مختلف طراحی شده است. نام و کد مدرسه از تنظیمات امن هر مدرسه خوانده می‌شود و نیازی به تغییر کد اصلی برنامه نیست.",
            "13sp", SUCCESS, 82,
        )
        body.add_widget(note)
        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    def go_back(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
