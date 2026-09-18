from threading import Thread

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, PRIMARY, SECONDARY, SUCCESS, WHITE, CARD, SCHOOL_NAME, SCHOOL_YEAR
from mobile.ui import font_name, rtl_text


PANELS = {
    "management": ("مدیریت", [("اطلاعات مدرسه", "school_profile"), ("دانش‌آموزان", "students"), ("دبیران", "teachers"), ("کادر و کارکنان", "staff"), ("پایه و کلاس‌ها", "school_class_config"), ("حساب‌های سامانه", "users"), ("رویدادها", "school_events"), ("کارنامه‌ها", "report_cards"), ("برنامه هفتگی", "weekly_schedule"), ("آزمون آنلاین", "teacher_exams"), ("کلاس آنلاین", "online_classes"), ("مالی", "finance_accounts")]),
    "educational": ("معاون آموزشی", [("دانش‌آموزان", "students"), ("دبیران", "staff"), ("کلاس‌های دبیران", "teacher_classes"), ("حضور و غیاب", "attendance"), ("نمرات", "student_grades"), ("تکالیف", "assignments"), ("طرح درس", "lesson_plans"), ("برنامه هفتگی", "weekly_schedule"), ("برنامه امتحانات", "exam_schedule"), ("پیگیری آموزشی", "educational_followups")]),
    "executive": ("معاون اجرایی", [("دانش‌آموزان", "students"), ("کارکنان", "staff"), ("ارتباط اولیا و فرزند", "parent_children"), ("برنامه هفتگی", "weekly_schedule"), ("کارنامه ماهیانه", "monthly_report_cards"), ("انضباط", "discipline_records"), ("گواهی اشتغال", "certificate_requests"), ("رویدادها", "school_events")]),
    "cultural": ("معاون پرورشی", [("فعالیت‌ها", "educational_activities"), ("مسابقات", "activity_offers"), ("انتخابات شورای دانش‌آموزی", "student_council"), ("بسیج دانش‌آموزی", "basij_registration"), ("شهردار مدرسه", "school_mayor"), ("مراسمات", "morning_ceremony"), ("پیام‌ها", "messages")]),
    "advisor": ("مشاوره", [("سوابق مشاوره", "counseling_records"), ("پیگیری جلسات", "counseling_followups"), ("دانش‌آموزان", "students"), ("ملاقات اولیا", "parent_meetings"), ("گزارش‌ها", "report_cards")]),
    "teachers": ("دبیران", [("کلاس‌های من", "teacher_classes"), ("طرح درس", "lesson_plans"), ("برنامه هفتگی", "weekly_schedule"), ("حضور و غیاب", "attendance"), ("نمرات", "grades"), ("تکالیف", "assignments"), ("آزمون آنلاین", "teacher_exams")]),
    "students": ("دانش‌آموزان", [("اطلاعات شخصی", "students"), ("پایه و کلاس", "student_class_info"), ("نمرات", "student_grades"), ("حضور و غیاب", "attendance"), ("کلاس‌های آنلاین", "online_classes"), ("تکالیف", "assignment_submissions"), ("برنامه هفتگی", "weekly_schedule"), ("برنامه امتحانی", "exam_schedule")]),
    "parents": ("اولیا", [("فرزندان", "parent_children"), ("اطلاعات دانش‌آموز", "students"), ("نمرات", "student_grades"), ("حضور و غیاب", "attendance"), ("کارنامه", "report_cards"), ("ملاقات با دبیر", "teacher_parent_meetings"), ("پیام‌ها", "messages")]),
    "finance": ("مالی", [("حساب‌ها", "finance_accounts"), ("تراکنش‌ها", "finance_transactions"), ("کمک‌های داوطلبانه", "finance_donations"), ("گزینه‌های پرداخت", "payment_offers"), ("درخواست‌های پرداخت", "payment_attempts"), ("سوابق پرداخت", "payment_records")]),
    "payment": ("پرداخت آنلاین", [("گزینه‌های پرداخت", "payment_offers"), ("درخواست‌های پرداخت", "payment_attempts"), ("سوابق پرداخت", "payment_records")]),
    "online": ("کلاس‌های آنلاین", [("کلاس‌ها", "online_classes"), ("جلسات", "online_class_sessions"), ("دانش‌آموزان کلاس", "online_class_students"), ("دبیران کلاس", "online_class_teachers"), ("حضور آنلاین", "online_attendance")]),
    "teacher_exams": ("آزمون آنلاین", [("آزمون‌ها", "teacher_exams"), ("سؤالات", "quiz_questions")]),
    "smart_board": ("تابلو هوشمند", [("محتوای آموزشی", "smart_board_content"), ("فعالیت‌ها", "smart_board_activities"), ("آزمون‌های کوتاه", "smart_board_quizzes"), ("تخته‌ها", "smart_board_whiteboards")]),
    "ai": ("هوش مصنوعی", [("گزارش‌های هوشمند", "ai_smart_reports"), ("پرسش‌های هوشمند", "ai_questions"), ("جلسات دستیار", "ai_assistant_sessions")]),
    "reports": ("گزارش‌ها", [("کارنامه‌ها", "report_cards"), ("نمرات", "grades"), ("حضور و غیاب", "attendance"), ("ارزیابی دانش‌آموزان", "student_grades"), ("گزارش هوشمند", "ai_smart_reports")]),
    "schedule": ("برنامه هفتگی", [("برنامه هفتگی", "weekly_schedule"), ("برنامه تولیدشده", "generated_weekly_schedule"), ("برنامه امتحانات", "exam_schedule"), ("کلاس‌های دبیران", "teacher_classes")]),
    "messages": ("صندوق پیام‌ها", [("صندوق ورودی", "messages"), ("مخاطبان", "message_targets"), ("وضعیت خواندن", "message_reads")]),
    "settings": ("تنظیمات", [("تنظیمات حساب", "account_settings"), ("مشخصات مدرسه", "school_profile"), ("ساختار کلاس‌ها", "school_class_config"), ("حساب‌های سامانه", "users")]),
    "about": ("درباره برنامه", []),
}


class PanelScreen(Screen):
    """Standalone panel shell. It does not depend on the old module wrapper."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.route = "management"
        self.table = None
        self.rows = []
        self._build()

    def label(self, value, size="10sp", color=SECONDARY, bold=False):
        w = Label(text=rtl_text(str(value)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="center", valign="middle")
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def button(self, value, callback, color=PRIMARY, height=dp(44)):
        b = Button(text=rtl_text(value), font_name=font_name(), font_size="11sp",
                   background_normal="", background_down="", background_color=color,
                   color=WHITE, size_hint_y=None, height=height)
        b.bind(on_release=callback)
        return b

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        top.add_widget(self.button("‹ داشبورد", self.go_dashboard, PRIMARY))
        self.title = self.label(APP_NAME, "18sp", PRIMARY, True)
        top.add_widget(self.title)
        root.add_widget(top)
        root.add_widget(self.label(f"{SCHOOL_NAME} • سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}", "8sp"))
        self.status = self.label("محیط پنل آماده است", "9sp", SUCCESS, True)
        root.add_widget(self.status)
        self.body = BoxLayout(orientation="vertical", spacing=dp(7))
        root.add_widget(self.body)
        self.add_widget(root)

    def set_route(self, route):
        self.route = route if route in PANELS else "management"
        self.table = None
        self.show_home()

    def show_home(self):
        title, items = PANELS[self.route]
        self.title.text = rtl_text(title)
        self.body.clear_widgets()
        if self.route == "about":
            box = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(10))
            box.add_widget(self.label(APP_NAME, "28sp", PRIMARY, True))
            box.add_widget(self.label("سامانه هوشمند آموزشی یکپارچه مدرسه", "12sp", SECONDARY, True))
            box.add_widget(self.label("یادگیری هوشمند، مدرسه‌ای یکپارچه، دانش آموز خلاق", "11sp", SUCCESS, True))
            self.body.add_widget(box)
            return

        head = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(92), padding=dp(10))
        head.add_widget(self.label(title, "20sp", PRIMARY, True))
        head.add_widget(self.label("یک زیرپنل را انتخاب کنید تا اطلاعات واقعی همان بخش از سرور خوانده شود.", "9sp"))
        self.body.add_widget(head)
        scroll = ScrollView(do_scroll_x=False)
        box = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None, padding=[dp(2), dp(2)])
        box.bind(minimum_height=box.setter("height"))
        for i, (caption, table) in enumerate(items, 1):
            box.add_widget(self.button(f"{i:02d}  {caption}", lambda *_a, t=table, c=caption: self.open_table(t, c), PRIMARY, dp(50)))
        scroll.add_widget(box)
        self.body.add_widget(scroll)
        self.status.text = rtl_text(f"{len(items)} زیرپنل آماده • داده‌ها از سرور خوانده می‌شوند")
        self.status.color = SUCCESS

    def open_table(self, table, caption):
        self.table = table
        self.body.clear_widgets()
        self.title.text = rtl_text(caption)
        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        top.add_widget(self.button("‹ بازگشت", lambda *_: self.show_home(), PRIMARY))
        top.add_widget(self.label(caption, "16sp", PRIMARY, True))
        self.body.add_widget(top)
        self.area = BoxLayout(orientation="vertical")
        self.body.add_widget(self.area)
        self.status.text = rtl_text("در حال دریافت اطلاعات واقعی…")
        self.status.color = SECONDARY
        Thread(target=self._load_table, args=(table,), daemon=True).start()

    def _load_table(self, table):
        try:
            api = getattr(self.app_state, "api", None)
            if api is None:
                raise RuntimeError("سرویس اتصال آماده نیست")
            rows = api.table_select(table, {"limit": "100"}) or []
            Clock.schedule_once(lambda *_: self._show_rows(rows), 0)
        except Exception as exc:
            Clock.schedule_once(lambda *_: self._show_error(str(exc)), 0)

    def _show_rows(self, rows):
        self.rows = rows if isinstance(rows, list) else []
        self.area.clear_widgets()
        self.status.text = rtl_text(f"{len(self.rows)} رکورد واقعی")
        self.status.color = SUCCESS
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, padding=dp(3))
        box.bind(minimum_height=box.setter("height"))
        if not self.rows:
            box.add_widget(self.label("برای این بخش هنوز رکوردی ثبت نشده است.", "13sp", PRIMARY, True))
        else:
            for i, row in enumerate(self.rows[:100], 1):
                if not isinstance(row, dict):
                    continue
                text = "  |  ".join(f"{k}: {str(v)[:40]}" for k, v in list(row.items())[:6])
                item = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(6))
                with item.canvas.before:
                    Color(*CARD)
                    bg = RoundedRectangle(radius=[dp(8)])
                item.bind(pos=lambda o, v, bg=bg: setattr(bg, "pos", v),
                          size=lambda o, v, bg=bg: setattr(bg, "size", v))
                item.add_widget(self.label(f"{i}. {text}", "8sp", SECONDARY, False))
                box.add_widget(item)
        scroll.add_widget(box)
        self.area.add_widget(scroll)

    def _show_error(self, message):
        self.area.clear_widgets()
        self.status.text = rtl_text("خطا در دریافت اطلاعات")
        self.status.color = (0.85, 0.15, 0.15, 1)
        self.area.add_widget(self.label("اتصال به پنل برقرار شد، اما دریافت داده انجام نشد.", "12sp", PRIMARY, True))
        self.area.add_widget(self.label(message, "8sp", SECONDARY, False))

    def go_dashboard(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
