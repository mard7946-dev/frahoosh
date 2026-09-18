from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from mobile.config import PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text


AUDIENCE_TEXT = {
    "دبیر": (
        "راهنمای دبیر: ابتدا کلاس و جلسه را انتخاب می‌کند؛ سپس تخته هوشمند، قلم با اندازه‌های مختلف، "
        "پاک‌کن، متن و اشکال را به کار می‌گیرد. صدا و تصویر، اشتراک صفحه، عکس و PDF از ابزارهای کلاس هستند. "
        "حضور دانش‌آموزان، چت، تکلیف و آزمون نیز از همان جلسه قابل پیگیری است."
    ),
    "اولیا": (
        "راهنمای اولیا: این بخش برای حضور در کلاس نیست. اولیا فقط گزارش‌ها و نتیجه آموزشی مرتبط با فرزند خود "
        "را می‌بینند؛ مانند اطلاع از کلاس برگزارشده، محتوای منتشرشده، تکلیف و گزارش حضور یا غیبت. "
        "ورود مستقیم اولیا به کلاس آنلاین در طراحی فراهوش فعال نیست."
    ),
    "دانش‌آموز": (
        "راهنمای دانش‌آموز: از برنامه هفتگی وارد کلاس فعال می‌شود. محتوای تخته، فایل‌ها و PDFهای منتشرشده "
        "را می‌بیند، در صورت اجازه دبیر در گفت‌وگو شرکت می‌کند و حضور آنلاین او ثبت می‌شود."
    ),
}


class SmartClassDemoScreen(Screen):
    """Manager-facing live preview and role guide for the professional online classroom."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build()

    def label(self, text, size="11sp", color=SECONDARY, bold=False, center=False, height=None):
        w = Label(text=rtl_text(str(text)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="center" if center else "right",
                  valign="middle", size_hint_y=None, height=dp(height) if height else None)
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def button(self, text, cb, color=PRIMARY):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="11sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(42))
        b.bind(on_release=cb)
        return b

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        head.add_widget(self.button("‹ بازگشت", lambda *_: self._back(), PRIMARY))
        head.add_widget(self.label("نمونه کلاس هوشمند • نظارت مدیر", "18sp", PRIMARY, True, True))
        root.add_widget(head)
        self.status = self.label("در حال دریافت محتوای واقعی کلاس…", "9sp", SECONDARY, False, True, 32)
        root.add_widget(self.status)

        self.tabs = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        for audience in ("دبیر", "دانش‌آموز", "اولیا"):
            self.tabs.add_widget(self.button(audience, lambda *_a, a=audience: self.show_audience(a), SUCCESS))
        root.add_widget(self.tabs)

        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(7), padding=[dp(2), dp(4)], size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def show(self):
        self.body.clear_widgets()
        self.show_audience("دبیر")
        self._load_live_content()

    def show_audience(self, audience):
        self.body.clear_widgets()
        self.body.add_widget(self.label("نمونه تجربه کلاس آنلاین", "20sp", PRIMARY, True, True, 46))
        self.body.add_widget(self.label(AUDIENCE_TEXT[audience], "10sp", SECONDARY, False, True, 100))

        sections = [
            ("🖊 تخته هوشمند", "قلم با چند اندازه، پاک‌کن، متن، خط، فلش و اشکال هندسی؛ همراه با چند صفحه تخته."),
            ("🎙 صدا و تصویر", "اشتراک میکروفون، دوربین و صفحه نمایش در سطح جلسه کنترل می‌شود."),
            ("📎 محتوای آموزشی", "عکس، PDF و فایل آموزشی به جلسه متصل می‌شود و محتوای منتشرشده برای نقش مجاز قابل مشاهده است."),
            ("👥 کلاس و حضور", "فهرست دانش‌آموزان، وضعیت حضور آنلاین، ورود و خروج و کنترل مشارکت جلسه ثبت می‌شود."),
            ("💬 تعامل", "گفت‌وگوی کلاس، اجازه صحبت، ارسال محتوا و مدیریت مشارکت دانش‌آموزان."),
            ("📝 آزمون و فعالیت", "آزمون کوتاه، سؤال، فعالیت کلاسی و گزارش عملکرد می‌تواند به همان جلسه متصل باشد."),
        ]
        for title, desc in sections:
            box = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(3), size_hint_y=None, height=dp(88))
            box.add_widget(self.label(title, "13sp", PRIMARY, True, True, 32))
            box.add_widget(self.label(desc, "9sp", SECONDARY, False, True, 48))
            self.body.add_widget(box)

        if audience == "دبیر":
            self.body.add_widget(self.label("مسیر کار دبیر", "14sp", SUCCESS, True, True, 38))
            self.body.add_widget(self.label(
                "برنامه هفتگی → کلاس → شروع جلسه → تخته/رسانه/تعامل → حضور و غیاب → تکلیف/آزمون → پایان جلسه",
                "10sp", SECONDARY, True, True, 58
            ))
        elif audience == "دانش‌آموز":
            self.body.add_widget(self.label("مسیر کار دانش‌آموز", "14sp", SUCCESS, True, True, 38))
            self.body.add_widget(self.label(
                "برنامه هفتگی → کلاس فعال → مشاهده تخته و فایل → مشارکت مجاز → ثبت حضور → دریافت محتوای منتشرشده",
                "10sp", SECONDARY, True, True, 58
            ))
        else:
            self.body.add_widget(self.label("مسیر اطلاعات برای اولیا", "14sp", SUCCESS, True, True, 38))
            self.body.add_widget(self.label(
                "اولیا وارد کلاس آنلاین نمی‌شود؛ گزارش آموزشی مرتبط با فرزند در پنل اولیا نمایش داده می‌شود.",
                "10sp", SECONDARY, True, True, 58
            ))

    def _load_live_content(self):
        def work():
            try:
                classes = self.app_state.api.table_select("online_classes", {"limit": "20", "order": "id.desc"}) or []
                boards = self.app_state.api.table_select("smart_board_content", {"limit": "20", "order": "id.desc"}) or []
                activities = self.app_state.api.table_select("smart_board_activities", {"limit": "20", "order": "id.desc"}) or []
                quizzes = self.app_state.api.table_select("smart_board_quizzes", {"limit": "20", "order": "id.desc"}) or []
                Clock.schedule_once(lambda *_: self._render_live(classes, boards, activities, quizzes), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._set_error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _render_live(self, classes, boards, activities, quizzes):
        self.status.text = rtl_text(
            f"اتصال واقعی فعال • {len(classes)} کلاس • {len(boards)} محتوای تخته • "
            f"{len(activities)} فعالیت • {len(quizzes)} آزمون کوتاه"
        )
        self.status.color = SUCCESS
        self.body.add_widget(self.label("محتوای واقعی ثبت‌شده در سامانه", "15sp", PRIMARY, True, True, 42))
        for row in classes[:5]:
            self.body.add_widget(self.label(
                f"کلاس: {row.get('title','')} • درس: {row.get('subject','')} • پایه: {row.get('grade','')} • وضعیت: {row.get('status','')}",
                "9sp", SECONDARY, False, True, 42
            ))
        if boards:
            self.body.add_widget(self.label("آخرین محتوای تخته", "13sp", PRIMARY, True, True, 36))
            for row in boards[:5]:
                self.body.add_widget(self.label(
                    f"{row.get('title','')} — {row.get('content','')}",
                    "9sp", SECONDARY, False, True, 54
                ))
        if activities:
            self.body.add_widget(self.label("آخرین فعالیت‌ها", "13sp", PRIMARY, True, True, 36))
            for row in activities[:5]:
                self.body.add_widget(self.label(
                    f"{row.get('title','')} — {row.get('activity_text','')}",
                    "9sp", SECONDARY, False, True, 50
                ))

    def _set_error(self, message):
        self.status.text = rtl_text("خواندن محتوای کلاس انجام نشد: " + str(message))
        self.status.color = (0.8, 0.15, 0.15, 1)

    def _back(self):
        if self.manager:
            self.manager.current = "dashboard"
