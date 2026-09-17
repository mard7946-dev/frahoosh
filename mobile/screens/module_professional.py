from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from mobile.config import CARD, PRIMARY, SECONDARY, SUCCESS, WHITE, APP_NAME, SCHOOL_NAME, SCHOOL_YEAR
from mobile.ui import font_name, rtl_text
from mobile.screens.module import ModuleScreen, MODULE_TABLES, MODULE_TITLES, FRIENDLY, ROLE_FEATURES


MODULE_DESCRIPTIONS = {
    "management": "مدیریت یکپارچه مدرسه، کاربران، کارکنان و اطلاعات پایه.",
    "educational": "مدیریت امور آموزشی، کلاس‌ها، حضور و غیاب، نمرات و تکالیف.",
    "executive": "مدیریت پرونده‌ها، اولیا، کارکنان و رویدادهای اجرایی.",
    "cultural": "مدیریت فعالیت‌های پرورشی، فرهنگی و رویدادهای مدرسه.",
    "advisor": "ثبت و پیگیری سوابق و جلسات مشاوره دانش‌آموزان.",
    "teacher": "ابزارهای کاری دبیر برای کلاس، حضور و غیاب، نمره و تکلیف.",
    "teachers": "فهرست دبیران، کارکنان و کلاس‌های آموزشی.",
    "student": "مشاهده وضعیت تحصیلی، نمرات، حضور و غیاب و تکالیف.",
    "students": "مدیریت و مشاهده اطلاعات و وضعیت تحصیلی دانش‌آموزان.",
    "parent": "مشاهده اطلاعات فرزند، نمرات، حضور و غیاب و تکالیف.",
    "parents": "مدیریت ارتباط اولیا و اطلاعات مرتبط با فرزندان.",
    "finance": "مدیریت حساب‌ها، تراکنش‌ها و کمک‌های داوطلبانه.",
    "payment": "مدیریت گزینه‌های پرداخت و سوابق تراکنش‌های سامانه.",
    "online": "مدیریت کلاس‌های آنلاین، جلسات و اعضای کلاس.",
    "smart_board": "مدیریت محتوای آموزشی، فعالیت‌ها، آزمونک و تخته کلاس.",
    "ai": "مدیریت پرسش‌ها، جلسات و گزارش‌های هوشمند.",
    "messages": "مدیریت پیام‌ها، مخاطبان و وضعیت خواندن پیام‌ها.",
    "settings": "تنظیمات حساب و اطلاعات پایه مدرسه.",
    "reports": "دسترسی منظم به کارنامه‌ها، نمرات و گزارش‌های آموزشی.",
    "schedule": "مدیریت برنامه هفتگی و برنامه امتحانات.",
    "student_info": "نمایش متمرکز وضعیت تحصیلی و سوابق دانش‌آموز.",
}


class FeatureCard(BoxLayout):
    def __init__(self, title, subtitle, callback, number, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(15), dp(11)], spacing=dp(5), size_hint_y=None, height=dp(122), **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, .985)
            self.bg = RoundedRectangle(radius=[dp(17)])
        self.bind(pos=self._sync, size=self._sync)
        top = BoxLayout(size_hint_y=None, height=dp(27), spacing=dp(8))
        badge = Label(text=rtl_text(str(number)), font_name=font_name(), font_size="10sp", bold=True, color=WHITE,
                      size_hint_x=None, width=dp(28), halign="center", valign="middle")
        with badge.canvas.before:
            Color(*PRIMARY)
            badge_bg = RoundedRectangle(radius=[dp(10)])
        badge.bind(pos=lambda o, v: setattr(badge_bg, "pos", v), size=lambda o, v: setattr(badge_bg, "size", v))
        top.add_widget(badge)
        title_w = Label(text=rtl_text(title), font_name=font_name(), font_size="14sp", bold=True, color=PRIMARY,
                        halign="right", valign="middle")
        title_w.bind(size=lambda o, v: setattr(o, "text_size", v))
        top.add_widget(title_w)
        self.add_widget(top)
        desc = Label(text=rtl_text(subtitle), font_name=font_name(), font_size="9sp", color=SECONDARY,
                     halign="right", valign="middle", size_hint_y=None, height=dp(27))
        desc.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.add_widget(desc)
        btn = Button(text=rtl_text("مشاهده و مدیریت"), font_name=font_name(), font_size="10sp",
                     background_normal="", background_color=PRIMARY, color=WHITE, size_hint_y=None, height=dp(38))
        btn.bind(on_release=callback)
        self.add_widget(btn)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class ProfessionalModuleScreen(ModuleScreen):
    """Professional landing page for every module; existing CRUD/table engine is preserved."""

    def show_module(self, key):
        self.module_key = str(key or "").strip().lower()
        title = MODULE_TITLES.get(self.module_key, self.module_key or APP_NAME)
        role = self._role()
        self.title.text = rtl_text(title)
        self.body.clear_widgets()
        self.status.text = rtl_text("اتصال به اطلاعات سامانه…")
        self.status.color = SECONDARY

        hero = BoxLayout(orientation="vertical", padding=[dp(18), dp(14)], spacing=dp(4), size_hint_y=None, height=dp(126))
        with hero.canvas.before:
            Color(1, 1, 1, .985)
            hero_bg = RoundedRectangle(radius=[dp(20)])
        hero.bind(pos=lambda o, v: setattr(hero_bg, "pos", v), size=lambda o, v: setattr(hero_bg, "size", v))
        h = Label(text=rtl_text(title), font_name=font_name(), font_size="21sp", bold=True, color=PRIMARY,
                  halign="right", valign="middle", size_hint_y=None, height=dp(38))
        h.bind(size=lambda o, v: setattr(o, "text_size", v))
        hero.add_widget(h)
        d = Label(text=rtl_text(MODULE_DESCRIPTIONS.get(self.module_key, ROLE_FEATURES.get(role, "امکانات این بخش بر اساس دسترسی کاربر نمایش داده می‌شود."))),
                  font_name=font_name(), font_size="10sp", color=SECONDARY, halign="right", valign="middle")
        d.bind(size=lambda o, v: setattr(o, "text_size", v))
        hero.add_widget(d)
        school = Label(text=rtl_text(f"{SCHOOL_NAME}  |  سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}"), font_name=font_name(),
                       font_size="9sp", color=PRIMARY, halign="right", valign="middle", size_hint_y=None, height=dp(25))
        school.bind(size=lambda o, v: setattr(o, "text_size", v))
        hero.add_widget(school)
        self.body.add_widget(hero)

        self._add_label("امکانات این پنل", "15sp", PRIMARY, 40, True)
        tables = MODULE_TABLES.get(self.module_key, [])
        if not tables:
            self._add_notice("این بخش آماده است", "امکانات اجرایی این قسمت از منوی مربوطه در دسترس است.", SUCCESS)
            self.status.text = rtl_text("پنل آماده استفاده است")
            return

        for index, table in enumerate(tables, 1):
            subtitle = f"داده‌های واقعی سامانه • {self._table_hint(table)}"
            card = FeatureCard(self._friendly(table), subtitle,
                               lambda *_args, t=table: self._open_table(t), index)
            self.body.add_widget(card)

        self._add_notice("اتصال سامانه", "هر کارت به منبع داده واقعی همین پنل متصل است؛ برای مشاهده، ثبت یا ویرایش اطلاعات وارد همان بخش شوید.", SUCCESS)
        self.status.text = rtl_text(f"{len(tables)} امکان اجرایی برای این پنل")
        self.status.color = SUCCESS

    def _table_hint(self, table):
        hints = {
            "students": "پرونده و مشخصات دانش‌آموزان", "teachers": "اطلاعات دبیران", "staff": "اطلاعات کارکنان",
            "attendance": "حضور و غیاب", "teacher_attendance": "حضور و غیاب کلاس", "grades": "نمرات و ارزشیابی",
            "student_grades": "ارزیابی‌های دانش‌آموز", "assignments": "تکالیف", "lesson_plans": "طرح درس",
            "school_profile": "اطلاعات پایه مدرسه", "school_class_config": "ساختار کلاس‌ها", "users": "حساب‌های سامانه",
            "parent_children": "ارتباط ولی و فرزند", "parents": "اطلاعات اولیا", "parent_meetings": "جلسات اولیا",
            "finance_accounts": "حساب‌های مالی", "finance_transactions": "تراکنش‌های مالی", "finance_donations": "کمک‌های داوطلبانه",
            "payment_offers": "گزینه‌های پرداخت", "payment_attempts": "درخواست‌های پرداخت", "payment_records": "سوابق پرداخت",
            "online_classes": "کلاس‌های آنلاین", "online_class_sessions": "جلسات کلاس", "online_class_students": "اعضای دانش‌آموز",
            "online_class_teachers": "دبیران کلاس", "smart_board_content": "محتوای آموزشی", "smart_board_activities": "فعالیت‌ها",
            "smart_board_quizzes": "آزمونک‌ها", "smart_board_whiteboards": "تخته‌ها", "messages": "پیام‌ها",
            "message_targets": "مخاطبان پیام", "message_reads": "وضعیت خواندن", "report_cards": "کارنامه‌ها",
            "report_card_snapshots": "نسخه‌های کارنامه", "weekly_schedule": "برنامه هفتگی", "generated_weekly_schedule": "برنامه تولیدشده",
            "exam_schedule": "برنامه امتحانات", "account_settings": "تنظیمات حساب", "educational_activities": "فعالیت‌های پرورشی",
            "school_events": "رویدادهای مدرسه", "counseling_records": "سوابق مشاوره", "counseling_followups": "پیگیری مشاوره",
            "ai_assistant_sessions": "جلسات دستیار", "ai_questions": "پرسش‌های هوش مصنوعی", "ai_smart_reports": "گزارش‌های هوشمند",
        }
        return hints.get(table, "مدیریت اطلاعات")

    def _open_table(self, table):
        self.body.clear_widgets()
        self._add_label(self._friendly(table), "18sp", PRIMARY, 44, True)
        self._add_button("‹ بازگشت به امکانات پنل", lambda *_: self.show_module(self.module_key), PRIMARY)
        self.status.text = rtl_text("در حال بارگذاری اطلاعات واقعی…")
        self.status.color = SECONDARY
        Thread = __import__("threading", fromlist=["Thread"]).Thread
        Thread(target=self._load_single_table, args=(table,), daemon=True).start()

    def _load_single_table(self, table):
        api = getattr(self.app_state, "api", None)
        if api is None:
            Clock = __import__("kivy.clock", fromlist=["Clock"]).Clock
            Clock.schedule_once(lambda *_: self._render_tables([]), 0)
            return
        try:
            rows = api.table_select(table, {"limit": "50"}) or []
            result = [(table, rows if isinstance(rows, list) else [], "data", "")]
        except Exception as exc:
            result = [(table, [], "unavailable", str(exc))]
        Clock = __import__("kivy.clock", fromlist=["Clock"]).Clock
        Clock.schedule_once(lambda *_: self._render_tables(result), 0)
