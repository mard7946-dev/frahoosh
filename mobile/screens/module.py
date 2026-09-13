from threading import Thread

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, CARD, PRIMARY, SCHOOL_NAME, SCHOOL_YEAR, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text


ROLE_ALIASES = {
    "admin": "manager", "administrator": "manager", "manager": "manager", "مدیر": "manager", "مدیریت": "manager",
    "executive": "executive", "معاون اجرایی": "executive", "educational": "educational", "training": "educational", "معاون آموزشی": "educational",
    "cultural": "cultural", "پرورشی": "cultural", "معاون پرورشی": "cultural", "advisor": "advisor", "counselor": "advisor", "مشاور": "advisor",
    "teacher": "teacher", "teacher_staff": "teacher", "دبیر": "teacher", "معلم": "teacher", "student": "student", "دانش‌آموز": "student",
    "دانش آموز": "student", "parent": "parent", "parent_guardian": "parent", "guardian": "parent", "ولی": "parent", "اولیا": "parent",
}
ROLE_FEATURES = {
    "manager": "مدیریت مدرسه، آمار، کاربران، امور مالی، گزارش‌ها و تنظیمات سامانه.",
    "educational": "کلاس‌ها، دروس، ارزشیابی، برنامه‌ریزی آموزشی و گزارش‌های آموزشی.",
    "executive": "پرونده‌ها، ثبت‌نام، کلاس‌ها، امور اجرایی و ارتباط با اولیا.",
    "cultural": "فعالیت‌های فرهنگی، پیگیری دانش‌آموزان، اولیا و گزارش‌های پرورشی.",
    "advisor": "پرونده دانش‌آموز، جلسات مشاوره، پیگیری و گزارش مشاوره.",
    "teacher": "کلاس‌ها، دانش‌آموزان کلاس، حضور و غیاب، نمرات، تکالیف و آزمون‌ها.",
    "student": "برنامه هفتگی، وضعیت تحصیلی، نمرات، تکالیف، کلاس آنلاین و پرداخت.",
    "parent": "وضعیت تحصیلی فرزند، حضور و غیاب، نمرات، تکالیف، پیام‌ها و پرداخت.",
}
MODULE_TITLES = {"management": "مدیریت", "educational": "معاون آموزشی", "executive": "معاون اجرایی", "cultural": "معاون پرورشی", "advisor": "مشاوره", "teacher": "پنل دبیر", "teachers": "دبیران", "student": "پنل دانش‌آموز", "students": "دانش‌آموزان", "parent": "پنل اولیا", "parents": "اولیا", "finance": "مالی", "payment": "پرداخت آنلاین", "online": "کلاس‌های آنلاین", "smart_board": "تابلو هوشمند", "ai": "دستیار هوش مصنوعی", "messages": "صندوق پیام‌ها", "settings": "تنظیمات", "reports": "گزارش‌ها", "schedule": "برنامه هفتگی", "student_info": "وضعیت تحصیلی"}
MODULE_TABLES = {"management": ["school_profile", "school_class_config", "users"], "educational": ["teacher_classes", "lesson_plans", "grades", "assignments"], "executive": ["students", "parent_children", "executive_classes", "executive_operations", "executive_requests"], "cultural": ["educational_activities", "cultural_activity_registrations", "cultural_reports"], "advisor": ["counseling_records", "counseling_followups", "students"], "teacher": ["teacher_classes", "teacher_activities", "teacher_attendance", "assignments"], "teachers": ["teachers", "staff", "teacher_classes"], "student": ["students", "student_grades", "grades", "assignments"], "students": ["students", "student_grades", "attendance", "assignments"], "parent": ["parent_children", "students", "grades", "attendance"], "parents": ["parent_children", "students", "parent_meetings"], "finance": ["finance_accounts", "finance_transactions", "finance_donations", "finance_extra", "payment_records"], "payment": ["payment_offers", "payment_attempts", "payment_records"], "online": ["online_classes", "online_class_sessions", "online_class_students", "online_class_teachers"], "smart_board": ["smart_board_content", "smart_board_activities", "smart_board_quizzes", "smart_board_whiteboards"], "ai": ["ai_assistant_sessions", "ai_questions", "ai_smart_reports"], "messages": ["message_inbox", "messages", "message_targets"], "settings": ["account_settings", "school_profile", "school_class_config"], "reports": ["report_cards", "report_card_snapshots", "grades", "student_grades"], "schedule": ["weekly_schedule", "generated_weekly_schedule", "exam_schedule"], "student_info": ["students", "grades", "student_grades", "report_cards"]}
DISPLAY_COLUMNS = {"students": ["id", "first_name", "last_name", "national_code", "grade", "class_name", "phone"], "teachers": ["id", "first_name", "last_name", "national_code", "subject", "grades", "employment_status"], "staff": ["id", "first_name", "last_name", "role", "phone", "employment_status"], "teacher_classes": ["id", "teacher_name", "subject", "grade", "class_name", "active"], "school_profile": ["school_name", "school_code", "principal_name", "phone", "address", "academic_year"], "school_class_config": ["total_classes", "grade7_classes", "grade8_classes", "grade9_classes"], "grades": ["student_id", "teacher_id", "subject", "exam_name", "score", "max_score", "grade_type", "term", "grade_date"], "student_grades": ["student_id", "teacher_id", "subject", "class_name", "assessment_type", "assessment_title", "score", "coefficient", "grade_date_shamsi"], "attendance": ["student_id", "teacher_id", "subject", "class_name", "attendance_date", "status"], "assignments": ["student_id", "teacher_id", "title", "subject", "class_name", "status", "due_date"], "lesson_plans": ["teacher_id", "teacher_name", "subject", "grade", "class_name", "title", "session_date"], "teacher_activities": ["teacher_id", "student_id", "title", "activity_type", "subject", "score", "activity_date"], "teacher_attendance": ["student_id", "teacher_id", "class_name", "subject", "attendance_date", "status"], "parent_children": ["parent_username", "student_id"], "parent_meetings": ["student_id", "teacher_id", "parent_phone", "reason", "meeting_date", "status"], "payment_offers": ["id", "title", "amount", "payment_reason", "target_type", "target_value", "active", "gateway_enabled"], "payment_attempts": ["id", "offer_id", "student_id", "payer_username", "amount", "status", "gateway_ref", "created_at"], "payment_records": ["id", "student_id", "parent_username", "title", "amount", "payment_type", "gateway", "reference", "status", "payment_date_shamsi"], "online_classes": ["id", "title", "subject", "lesson", "teacher", "grade", "class_name", "duration", "start_time_shamsi", "end_time_shamsi", "status"], "online_class_sessions": ["id", "class_id", "started_at", "ended_at"], "online_class_students": ["id", "class_id", "student_id", "student_name"], "online_class_teachers": ["id", "class_id", "teacher_id", "teacher_name"], "messages": ["id", "sender_name", "title", "body", "audience_type", "created_at"], "message_inbox": ["id", "sender_username", "sender_role", "title", "body", "is_read", "created_at"], "message_targets": ["id", "message_id", "target_type", "target_value", "target_role", "target_id", "read_at"], "report_cards": ["id", "student_id", "term", "average", "grade_level", "academic_year", "report_date"], "report_card_snapshots": ["id", "student_id", "term", "academic_year", "average", "generated_date_shamsi"], "weekly_schedule": ["id", "teacher", "subject", "grade", "class_count", "class_names", "weekdays"], "generated_weekly_schedule": ["id", "teacher", "subject", "grade", "class_name", "weekday", "bell", "week_index"], "exam_schedule": ["id", "subject", "grade", "exam_date", "duration", "exam_start_time", "exam_end_time"], "account_settings": ["username", "display_name", "phone", "email", "national_code", "role"]}


class _Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(12), dp(9)], spacing=dp(3), size_hint_y=None, **kwargs)
        with self.canvas.before:
            Color(*CARD)
            self.bg = RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class ModuleScreen(Screen):
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.module_key = ""
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(13), spacing=dp(8))
        head = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        back = Button(text=rtl_text("‹ داشبورد"), font_name=font_name(), font_size="13sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(105))
        back.bind(on_release=self.go_back)
        head.add_widget(back)
        self.title = Label(text=rtl_text(APP_NAME), font_name=font_name(), font_size="21sp", bold=True, color=PRIMARY, halign="right", valign="middle")
        self.title.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        head.add_widget(self.title)
        root.add_widget(head)
        self.status = Label(text="", font_name=font_name(), font_size="11sp", color=SECONDARY, halign="center", valign="middle", size_hint_y=None, height=dp(42))
        self.status.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        root.add_widget(self.status)
        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(8), padding=[dp(3), dp(3)], size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def go_back(self, *_):
        if self.manager:
            self.manager.current = "dashboard"

    def set_module(self, key):
        self.show_module(key)

    def load_module(self, key):
        self.show_module(key)

    def _role(self):
        try:
            raw = getattr(self.app_state, "role", "student")
        except Exception:
            raw = "student"
        raw = str(raw or "student").strip().lower()
        return ROLE_ALIASES.get(raw, raw)

    def show_module(self, key):
        self.module_key = str(key or "").strip().lower()
        title = MODULE_TITLES.get(self.module_key, self.module_key or APP_NAME)
        role = self._role()
        self.title.text = rtl_text(title)
        self.body.clear_widgets()
        self.status.text = rtl_text("در حال دریافت اطلاعات سامانه…")
        self.status.color = SECONDARY
        self._add_label(f"{title}  |  {SCHOOL_NAME}", "19sp", PRIMARY, 50, True)
        self._add_notice("امکانات نقش شما", ROLE_FEATURES.get(role, "امکانات در دسترس بر اساس نقش ثبت‌شده در حساب کاربری نمایش داده می‌شوند."), SUCCESS)
        self._add_label(f"سال تحصیلی: {SCHOOL_YEAR or '—'}  •  اطلاعات زنده از سامانه مرکزی", "10sp", SECONDARY, 38)
        tables = MODULE_TABLES.get(self.module_key, [])
        if not tables:
            self.status.text = rtl_text("برای این بخش منبع داده‌ای تعریف نشده است؛ امکانات پنل همچنان در دسترس‌اند.")
            self.status.color = SECONDARY
            self._add_notice("وضعیت داده", "این بخش هنوز جدول داده‌ای مستقلی ندارد. از گزینه‌های پنل برای ادامه استفاده کنید.", SECONDARY)
            return
        Thread(target=self._load_tables, args=(tables,), daemon=True).start()

    def _load_tables(self, tables):
        results = []
        for table in tables:
            try:
                rows = self.app_state.api.table_select(table, {"limit": "25"}) or []
                results.append((table, rows, "data", ""))
            except Exception as exc:
                kind = self._error_kind(exc)
                results.append((table, [], kind, str(exc)))
        Clock.schedule_once(lambda *_: self._render_tables(results), 0)

    @staticmethod
    def _error_kind(exc):
        message = str(exc).lower()
        if any(marker in message for marker in ("permission", "forbidden", "unauthorized", "not authorized", "row-level", "rls", " 401", " 403", "jwt")):
            return "access"
        if any(marker in message for marker in ("timeout", "connection", "network", "dns", "unreachable", "failed to establish")):
            return "network"
        return "api"

    def _render_tables(self, results):
        total = no_data = denied = failed = 0
        for table, rows, kind, detail in results:
            if kind == "data" and rows:
                total += len(rows)
                self._add_label(self._friendly(table), "15sp", PRIMARY, 38, True)
                for row in rows[:25]:
                    self._add_record(table, row)
            elif kind == "data":
                no_data += 1
                self._add_notice(self._friendly(table), "داده‌ای برای نمایش وجود ندارد. امکانات این بخش فعال هستند و با ثبت داده در سامانه نمایش داده می‌شوند.", SECONDARY)
            elif kind == "access":
                denied += 1
                self._add_notice(self._friendly(table), "دسترسی به این داده برای نقش فعلی توسط سامانه مجاز نیست. برای تغییر دسترسی با مدیریت مدرسه تماس بگیرید.", (0.75, 0.25, 0.16, 1))
            else:
                failed += 1
                label = "خطای ارتباط با سامانه" if kind == "network" else "خطای API یا تنظیمات داده"
                self._add_notice(self._friendly(table), f"{label}. لطفاً اتصال و تنظیمات سامانه را بررسی و دوباره تلاش کنید.\n{detail}", (0.70, 0.18, 0.20, 1))
        summary = f"{total} رکورد بارگذاری شد"
        if no_data:
            summary += f" • {no_data} بخش بدون داده"
        if denied:
            summary += f" • {denied} بخش بدون مجوز"
        if failed:
            summary += f" • {failed} خطای دریافت"
        self.status.text = rtl_text(summary)
        self.status.color = SUCCESS if not (denied or failed) else SECONDARY
        self._button("↻ تازه‌سازی اطلاعات", lambda *_: self.show_module(self.module_key), SUCCESS)

    def _add_notice(self, title, text, color=SECONDARY):
        card = _Card(height=dp(82))
        heading = Label(text=rtl_text(title), font_name=font_name(), font_size="14sp", bold=True, color=color, halign="right", valign="middle", size_hint_y=None, height=dp(27))
        heading.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        body = Label(text=rtl_text(text), font_name=font_name(), font_size="10sp", color=SECONDARY, halign="right", valign="top")
        body.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        card.add_widget(heading)
        card.add_widget(body)
        self.body.add_widget(card)

    def _add_record(self, table, row):
        cols = DISPLAY_COLUMNS.get(table) or [key for key in row.keys() if key != "password"][:8]
        parts = [f"{self._column(column)}: {row.get(column)}" for column in cols if column in row and row.get(column) not in (None, "")]
        text = "\n".join(parts) or "رکورد ثبت شده"
        card = _Card(height=max(dp(62), dp(25 * min(8, len(parts)) + 12)))
        label = Label(text=rtl_text(text), font_name=font_name(), font_size="10sp", color=SECONDARY, halign="right", valign="middle")
        label.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        card.add_widget(label)
        self.body.add_widget(card)

    def _add_label(self, text, size="14sp", color=SECONDARY, height=50, bold=False):
        label = Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, bold=bold, halign="right", valign="middle", size_hint_y=None, height=dp(height))
        label.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        self.body.add_widget(label)
        return label

    def _button(self, text, callback, color=PRIMARY):
        button = Button(text=rtl_text(text), font_name=font_name(), font_size="13sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=dp(48))
        button.bind(on_release=callback)
        self.body.add_widget(button)
        return button

    @staticmethod
    def _friendly(table):
        return {"school_profile": "مشخصات مدرسه", "school_class_config": "تنظیمات کلاس‌ها", "users": "حساب‌های سامانه", "students": "دانش‌آموزان", "teachers": "دبیران", "staff": "کارکنان", "teacher_classes": "کلاس‌های دبیر", "lesson_plans": "طرح درس‌ها", "grades": "نمرات", "student_grades": "ارزیابی‌های دانش‌آموز", "attendance": "حضور و غیاب", "assignments": "تکالیف", "parent_children": "ارتباط ولی و فرزند", "parent_meetings": "جلسات اولیا", "payment_offers": "گزینه‌های پرداخت", "payment_attempts": "درخواست‌های پرداخت", "payment_records": "سوابق پرداخت", "online_classes": "کلاس‌های آنلاین", "online_class_sessions": "جلسات کلاس آنلاین", "online_class_students": "دانش‌آموزان کلاس آنلاین", "online_class_teachers": "دبیران کلاس آنلاین", "messages": "پیام‌ها", "message_inbox": "صندوق ورودی", "message_targets": "مخاطبان پیام", "report_cards": "کارنامه‌ها", "report_card_snapshots": "نسخه‌های کارنامه", "weekly_schedule": "برنامه هفتگی", "generated_weekly_schedule": "برنامه تولیدشده", "exam_schedule": "برنامه امتحانات", "account_settings": "تنظیمات حساب"}.get(table, table.replace("_", " "))

    @staticmethod
    def _column(column):
        return {"id": "شناسه", "first_name": "نام", "last_name": "نام خانوادگی", "national_code": "کد ملی", "grade": "پایه", "class_name": "کلاس", "subject": "درس", "teacher_name": "دبیر", "score": "نمره", "max_score": "از", "status": "وضعیت", "amount": "مبلغ", "title": "عنوان", "description": "توضیحات", "created_at": "تاریخ ثبت", "created_at_shamsi": "تاریخ ثبت", "exam_date": "تاریخ آزمون", "exam_date_shamsi": "تاریخ آزمون", "start_time_shamsi": "شروع", "end_time_shamsi": "پایان", "payment_reason": "علت پرداخت", "is_read": "خوانده شده", "active": "فعال"}.get(column, column.replace("_", " "))
