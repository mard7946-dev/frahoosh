from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME
from mobile.ui import font_name, rtl_text


class SmartClassPreviewScreen(Screen):
    """Manager-facing live preview of the smart classroom and role-specific teaching guides."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build()

    def _label(self, text, size="11sp", color=SECONDARY, height=48, bold=False):
        w = Label(text=rtl_text(text), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="right", valign="middle",
                  size_hint_y=None, height=dp(height))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _button(self, text, cb, color=PRIMARY):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="11sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(45))
        b.bind(on_release=cb)
        return b

    def on_pre_enter(self, *args):
        self.show_home()

    def show_home(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        head = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(7))
        head.add_widget(self._button("‹ بازگشت", self._back, SECONDARY))
        head.add_widget(self._label("نمونه کلاس هوشمند", "20sp", PRIMARY, 46, True))
        root.add_widget(head)

        root.add_widget(self._label(
            f"{SCHOOL_NAME}\nنمای مدیر برای مشاهده محتوای کلاس و توضیح امکانات به دبیر، اولیا و دانش‌آموز",
            "11sp", SECONDARY, 68, True))

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", spacing=dp(7), padding=dp(3), size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        sections = [
            ("👨‍🏫 بخش دبیر",
             "ساخت جلسه، برنامه هفتگی، ورود به کلاس، تخته هوشمند، قلم در چند اندازه، پاک‌کن، شکل‌ها، متن، عکس، PDF، اشتراک صدا/تصویر، آزمونک، چت، حضور و غیاب و گزارش کلاس."),
            ("👨‍👩‍👦 بخش اولیا",
             "مشاهده اطلاعیه‌های آموزشی، وضعیت حضور فرزند، تکالیف، نمرات و گزارش‌های منتشرشده؛ کلاس آنلاین در پنل اولیا قرار نمی‌گیرد."),
            ("👨‍🎓 بخش دانش‌آموز",
             "ورود به جلسه آنلاین، مشاهده تخته و فایل‌های آموزشی، مشارکت در چت و آزمونک، مشاهده برنامه و وضعیت آموزشی."),
            ("🧑‍💼 بخش مدیر",
             "مشاهده کلاس‌های فعال، محتوای تخته، فایل‌ها، فعالیت‌ها، آزمونک‌ها و گزارش جلسه؛ کنترل دسترسی و نظارت بر روند کلاس."),
        ]
        for title, desc in sections:
            card = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(3),
                             size_hint_y=None, height=dp(112))
            card.add_widget(self._label(title, "14sp", PRIMARY, 34, True))
            card.add_widget(self._label(desc, "10sp", SECONDARY, 70))
            body.add_widget(card)

        body.add_widget(self._label("محتوای آخرین کلاس ثبت‌شده در سرور", "15sp", PRIMARY, 40, True))
        self._load_live_content(body)
        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    def _load_live_content(self, body):
        api = getattr(self.app_state, "api", None)
        if api is None:
            body.add_widget(self._label("اتصال API آماده نیست.", color=ERROR, height=50))
            return
        try:
            classes = api.table_select("online_classes", {"order":"id.desc","limit":"1"})
            if not classes:
                body.add_widget(self._label("هنوز کلاسی در سرور ثبت نشده است.", height=55))
                return
            cls = classes[0]
            cid = cls.get("id")
            body.add_widget(self._label(
                f"کلاس: {cls.get('title') or '-'} | درس: {cls.get('subject') or '-'}\n"
                f"پایه: {cls.get('grade') or '-'} | کلاس: {cls.get('class_name') or '-'} | دبیر: {cls.get('teacher') or '-'}",
                "11sp", SUCCESS, 68, True))
            sources = [
                ("تخته آموزشی", "smart_board_whiteboards", {"class_id":f"eq.{cid}"}),
                ("محتوای آموزشی", "smart_board_content", {"class_id":f"eq.{cid}"}),
                ("فعالیت‌های کلاس", "smart_board_activities", {"class_id":f"eq.{cid}"}),
                ("آزمونک‌ها", "smart_board_quizzes", {"class_id":f"eq.{cid}"}),
            ]
            for title, table, params in sources:
                try:
                    rows = api.table_select(table, dict(params, **{"order":"id.asc","limit":"20"}))
                except Exception:
                    rows = []
                body.add_widget(self._label(f"{title}: {len(rows)} مورد ثبت‌شده", "11sp", PRIMARY, 34, True))
                for row in rows[-5:]:
                    text = row.get("content") or row.get("activity_text") or row.get("question") or row.get("title") or "محتوا"
                    body.add_widget(self._label("• " + str(text), "10sp", SECONDARY, 46))

            body.add_widget(self._label(
                "نکته مدیریتی: این صفحه برای نمایش نمونه و نظارت است؛ عملیات اصلی کلاس از پنل دبیر انجام می‌شود و داده‌ها از همان Backend مشترک خوانده می‌شوند.",
                "10sp", SUCCESS, 72, True))
        except Exception as exc:
            body.add_widget(self._label("خواندن محتوای کلاس انجام نشد: " + str(exc), color=ERROR, height=70))

    def _back(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
