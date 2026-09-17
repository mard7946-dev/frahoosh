from threading import Thread

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from mobile.config import APP_NAME, CARD, PRIMARY, SCHOOL_NAME, SCHOOL_YEAR, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

MODULES = {
    "management": ("مدیریت مدرسه", ["students", "teachers", "school_class_config", "staff", "school_events", "users"]),
    "educational": ("معاونت آموزشی", ["teacher_classes", "lesson_plans", "attendance", "grades", "assignments"]),
    "executive": ("معاونت اجرایی", ["students", "parents", "staff", "attendance", "school_events"]),
    "cultural": ("معاونت پرورشی", ["educational_activities", "school_events", "students", "messages"]),
    "advisor": ("مشاوره", ["counseling_records", "counseling_followups", "students"]),
    "teachers": ("دبیران", ["teachers", "teacher_classes", "staff"]),
    "students": ("دانش‌آموزان", ["students", "student_grades", "attendance", "assignments"]),
    "parents": ("اولیا", ["parent_children", "parents", "parent_meetings", "students"]),
    "finance": ("مالی", ["finance_accounts", "finance_transactions", "finance_donations", "payment_records"]),
    "payment": ("پرداخت آنلاین", ["payment_offers", "payment_attempts", "payment_records"]),
    "online": ("کلاس‌های آنلاین", ["online_classes", "online_class_sessions", "online_class_students", "online_class_teachers"]),
    "smart_board": ("تابلو هوشمند", ["smart_board_content", "smart_board_activities", "smart_board_quizzes", "smart_board_whiteboards"]),
    "ai": ("دستیار هوش مصنوعی", ["ai_assistant_sessions", "ai_questions", "ai_smart_reports"]),
    "messages": ("صندوق پیام‌ها", ["messages", "message_targets", "message_reads"]),
    "settings": ("تنظیمات", ["account_settings", "school_profile", "school_class_config"]),
    "reports": ("گزارش‌ها", ["report_cards", "report_card_snapshots", "grades", "attendance", "student_grades"]),
    "schedule": ("برنامه هفتگی", ["weekly_schedule", "generated_weekly_schedule", "exam_schedule"]),
    "student_info": ("وضعیت تحصیلی", ["students", "grades", "student_grades", "attendance", "assignments", "report_cards"]),
}

FRIENDLY = {
    "school_profile": "مشخصات مدرسه", "school_class_config": "ساختار کلاس‌ها", "users": "حساب‌های سامانه",
    "students": "دانش‌آموزان", "teachers": "دبیران", "staff": "کارکنان", "teacher_classes": "کلاس‌های دبیران",
    "lesson_plans": "طرح درس‌ها", "attendance": "حضور و غیاب", "grades": "نمرات", "student_grades": "ارزیابی دانش‌آموزان",
    "assignments": "تکالیف", "parents": "اولیا", "parent_children": "ارتباط ولی و فرزند", "parent_meetings": "جلسات اولیا",
    "finance_accounts": "حساب‌های مالی", "finance_transactions": "تراکنش‌های مالی", "finance_donations": "کمک‌های داوطلبانه",
    "payment_offers": "تعریف پرداخت", "payment_attempts": "درخواست‌های پرداخت", "payment_records": "سوابق پرداخت",
    "online_classes": "کلاس‌های آنلاین", "online_class_sessions": "جلسات آنلاین", "online_class_students": "دانش‌آموزان کلاس",
    "online_class_teachers": "دبیران کلاس", "educational_activities": "فعالیت‌های پرورشی", "school_events": "رویدادهای مدرسه",
    "counseling_records": "سوابق مشاوره", "counseling_followups": "پیگیری مشاوره", "smart_board_content": "محتوای تابلو",
    "smart_board_activities": "فعالیت‌های تابلو", "smart_board_quizzes": "آزمون‌های کوتاه", "smart_board_whiteboards": "تخته‌های آموزشی",
    "ai_assistant_sessions": "جلسات دستیار", "ai_questions": "پرسش‌های هوشمند", "ai_smart_reports": "گزارش‌های هوشمند",
    "messages": "پیام‌ها", "message_targets": "مخاطبان پیام", "message_reads": "وضعیت خواندن", "report_cards": "کارنامه‌ها",
    "report_card_snapshots": "نسخه‌های کارنامه", "weekly_schedule": "برنامه هفتگی", "generated_weekly_schedule": "برنامه تولیدشده",
    "exam_schedule": "برنامه امتحانات", "account_settings": "تنظیمات حساب",
}

COLUMNS = {
    "id": "شناسه", "first_name": "نام", "last_name": "نام خانوادگی", "national_code": "کد ملی", "grade": "پایه",
    "class_name": "کلاس", "phone": "تلفن", "subject": "درس", "teacher_name": "دبیر", "score": "نمره",
    "max_score": "حداکثر نمره", "status": "وضعیت", "amount": "مبلغ", "title": "عنوان", "description": "توضیحات",
    "created_at": "تاریخ ثبت", "attendance_date": "تاریخ حضور", "exam_date": "تاریخ آزمون", "event_date": "تاریخ رویداد",
    "start_time_shamsi": "شروع", "end_time_shamsi": "پایان", "role": "نقش", "email": "ایمیل", "username": "نام کاربری",
    "term": "نوبت", "academic_year": "سال تحصیلی", "active": "فعال", "teacher_id": "شناسه دبیر", "student_id": "شناسه دانش‌آموز",
}

# Tables intentionally exposed for write operations. Other tables remain safely view-only.
EDITABLE = {
    "manager": {t for _, tables in MODULES.values() for t in tables},
    "educational": {"teacher_classes", "lesson_plans", "attendance", "grades", "student_grades", "assignments", "weekly_schedule", "generated_weekly_schedule", "exam_schedule"},
    "executive": {"students", "parents", "staff", "attendance", "school_events"},
    "cultural": {"educational_activities", "school_events"},
    "advisor": {"counseling_records", "counseling_followups"},
    "teacher": {"attendance", "grades", "student_grades", "assignments", "lesson_plans"},
}

FORM_FIELDS = {
    "students": ["first_name", "last_name", "national_code", "grade", "class_name", "phone"],
    "teachers": ["first_name", "last_name", "national_code", "phone", "subject"],
    "staff": ["first_name", "last_name", "phone", "role"],
    "school_events": ["title", "description", "event_date", "status"],
    "lesson_plans": ["teacher_id", "teacher_name", "subject", "grade", "class_name", "title"],
    "assignments": ["student_id", "teacher_id", "title", "subject", "class_name", "status"],
    "attendance": ["student_id", "teacher_id", "class_name", "subject", "attendance_date", "status"],
    "grades": ["student_id", "teacher_id", "subject", "score", "max_score", "term"],
}

HIDDEN = {"id", "created_at", "updated_at", "deleted_at"}


class Surface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(12), dp(10)], spacing=dp(7), size_hint_y=None, **kwargs)
        with self.canvas.before:
            Color(*CARD)
            self.bg = RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class ModuleScreen(Screen):
    """Professional real-data workspace. Every record shown here is read from the configured API."""
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.module_key = "management"
        self.return_to = "dashboard"
        self.active_table = None
        self.rows = []
        self.columns = []
        self.search_text = ""
        self._build()

    def lbl(self, text, size="12sp", color=SECONDARY, bold=False, align="right"):
        w = Label(text=rtl_text(str(text)), font_name=font_name(), font_size=size, color=color, bold=bold,
                  halign=align, valign="middle")
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def btn(self, text, callback, color=PRIMARY, h=dp(42), width=None):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="11sp", background_normal="",
                   background_color=color, color=WHITE, size_hint_y=None, height=h)
        if width is not None:
            b.size_hint_x = None
            b.width = width
        b.bind(on_release=callback)
        return b

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        head.add_widget(self.btn("‹ بازگشت", self.go_back, PRIMARY, dp(42), dp(82)))
        self.title = self.lbl(APP_NAME, "19sp", PRIMARY, True, "center")
        head.add_widget(self.title)
        head.add_widget(self.btn("⌂", self.go_dashboard, PRIMARY, dp(42), dp(48)))
        root.add_widget(head)
        root.add_widget(self.lbl(f"{SCHOOL_NAME}  |  {SCHOOL_YEAR}", "9sp", SECONDARY, False, "center"))
        self.status = self.lbl("", "9sp", SUCCESS, True, "center")
        root.add_widget(self.status)
        self.body = BoxLayout(orientation="vertical", spacing=dp(6))
        root.add_widget(self.body)
        self.add_widget(root)

    def set_module(self, key, return_to="dashboard"):
        self.module_key = key if key in MODULES else "management"
        self.return_to = return_to or "dashboard"
        self.active_table = None
        self.rows = []
        self.render_workspace()

    load_module = set_module

    def clear(self):
        self.body.clear_widgets()

    def _role(self):
        role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
        aliases = {"admin": "manager", "administrator": "manager", "مدیر": "manager", "مدیریت": "manager",
                   "معاون آموزشی": "educational", "معاون اجرایی": "executive", "معاون پرورشی": "cultural",
                   "مشاور": "advisor", "دبیر": "teacher", "معلم": "teacher", "دانش‌آموز": "student", "ولی": "parent", "اولیا": "parent"}
        return aliases.get(role, role)

    def can_write(self, table):
        return table in EDITABLE.get(self._role(), set())

    def render_workspace(self):
        self.clear()
        title, tables = MODULES[self.module_key]
        self.title.text = rtl_text(title)
        self.status.text = rtl_text("اتصال فعال • اطلاعات واقعی سامانه")
        self.status.color = SUCCESS

        hero = Surface(height=dp(106))
        hero.add_widget(self.lbl(title, "22sp", PRIMARY, True, "center"))
        hero.add_widget(self.lbl("محیط عملیاتی حرفه‌ای • مشاهده، ثبت، ویرایش و حذف با دسترسی نقش کاربر", "10sp", SECONDARY, False, "center"))
        hero.add_widget(self.lbl(str(getattr(self.app_state, "display_name", "کاربر فراهوش")), "9sp", PRIMARY, True, "center"))
        self.body.add_widget(hero)

        quick = Surface(height=dp(70))
        row = BoxLayout(spacing=dp(6))
        for table in tables[:4]:
            row.add_widget(self.btn(FRIENDLY.get(table, table), lambda *_a, t=table: self.open_table(t), PRIMARY, dp(38)))
        quick.add_widget(self.lbl("دسترسی سریع", "11sp", PRIMARY, True))
        quick.add_widget(row)
        self.body.add_widget(quick)

        scroll = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=1, spacing=dp(7), size_hint_y=None, padding=[dp(2), dp(2)])
        grid.bind(minimum_height=grid.setter("height"))
        for index, table in enumerate(tables, 1):
            card = Surface(height=dp(94))
            top = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(5))
            top.add_widget(self.lbl(f"{index:02d}", "10sp", WHITE, True, "center"))
            top.add_widget(self.lbl(FRIENDLY.get(table, table), "14sp", PRIMARY, True))
            card.add_widget(top)
            card.add_widget(self.lbl("داده واقعی • عملیات کامل" if self.can_write(table) else "داده واقعی • فقط مشاهده بر اساس سطح دسترسی", "9sp", SECONDARY))
            actions = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(5))
            actions.add_widget(self.btn("مشاهده و مدیریت", lambda *_a, t=table: self.open_table(t), PRIMARY, dp(34)))
            if self.can_write(table):
                actions.add_widget(self.btn("＋ ثبت جدید", lambda *_a, t=table: self.open_editor(t, None), SUCCESS, dp(34)))
            card.add_widget(actions)
            grid.add_widget(card)
        scroll.add_widget(grid)
        self.body.add_widget(scroll)

    def open_table(self, table):
        self.active_table = table
        self.rows = []
        self.clear()
        head = Surface(height=dp(74))
        line = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        line.add_widget(self.btn("‹ پنل", lambda *_: self.render_workspace(), PRIMARY, dp(38), dp(64)))
        line.add_widget(self.lbl(FRIENDLY.get(table, table), "17sp", PRIMARY, True, "center"))
        line.add_widget(self.btn("↻", lambda *_: self.load_table(table), PRIMARY, dp(38), dp(48)))
        head.add_widget(line)
        search = TextInput(hint_text=rtl_text("جستجو در رکوردهای همین جدول"), font_name=font_name(), font_size="11sp",
                           halign="right", multiline=False, size_hint_y=None, height=dp(32), padding=[dp(8), dp(6)])
        self.search_input = search
        head.add_widget(search)
        self.body.add_widget(head)
        toolbar = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        if self.can_write(table):
            toolbar.add_widget(self.btn("＋ ثبت رکورد جدید", lambda *_: self.open_editor(table, None), SUCCESS, dp(40)))
        toolbar.add_widget(self.btn("اعمال جستجو", lambda *_: self.render_rows(self._filtered_rows()), PRIMARY, dp(40)))
        toolbar.add_widget(self.btn("پاک کردن جستجو", lambda *_: self._clear_search(), SECONDARY, dp(40)))
        self.body.add_widget(toolbar)
        self.table_area = BoxLayout(orientation="vertical")
        self.body.add_widget(self.table_area)
        self.load_table(table)

    def _clear_search(self):
        if hasattr(self, "search_input"):
            self.search_input.text = ""
        self.render_rows(self.rows)

    def load_table(self, table):
        self.status.text = rtl_text("در حال دریافت اطلاعات واقعی…")
        self.status.color = SECONDARY
        def work():
            try:
                rows = self.app_state.api.table_select(table, {"limit": "100"}) or []
                if not isinstance(rows, list):
                    rows = []
                Clock.schedule_once(lambda *_: self._loaded(table, rows, None), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._loaded(table, [], str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _loaded(self, table, rows, error):
        if table != self.active_table:
            return
        self.rows = rows
        if error:
            self.status.text = rtl_text("خطا: " + error)
            self.status.color = (0.8, 0.15, 0.15, 1)
        else:
            self.status.text = rtl_text(f"{len(rows)} رکورد واقعی دریافت شد")
            self.status.color = SUCCESS
        self.render_rows(rows)

    def _filtered_rows(self):
        q = str(getattr(self, "search_input", None).text if hasattr(self, "search_input") else "").strip().lower()
        if not q:
            return self.rows
        return [r for r in self.rows if q in " ".join(str(v) for v in r.values()).lower()]

    def render_rows(self, rows):
        if not hasattr(self, "table_area"):
            return
        self.table_area.clear_widgets()
        if not rows:
            empty = Surface(height=dp(120))
            empty.add_widget(self.lbl("رکوردی برای نمایش وجود ندارد", "16sp", PRIMARY, True, "center"))
            empty.add_widget(self.lbl("در صورت داشتن دسترسی، از «ثبت رکورد جدید» استفاده کنید.", "10sp", SECONDARY, False, "center"))
            self.table_area.add_widget(empty)
            return
        keys = []
        for row in rows:
            if isinstance(row, dict):
                for key in row:
                    if key not in HIDDEN and key not in keys:
                        keys.append(key)
        self.columns = keys
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        content = BoxLayout(orientation="vertical", size_hint=(None, None), spacing=dp(3), padding=dp(2))
        width = max(dp(430), dp(145) * max(2, len(keys)) + dp(160))
        content.width = width
        content.bind(minimum_height=content.setter("height"))
        header = BoxLayout(size_hint=(None, None), width=width, height=dp(42), spacing=dp(2))
        for key in keys:
            header.add_widget(self.lbl(COLUMNS.get(key, key), "9sp", WHITE, True, "center"))
        if self.can_write(self.active_table):
            header.add_widget(self.lbl("عملیات", "9sp", WHITE, True, "center"))
        self._paint_header(header)
        content.add_widget(header)
        for index, row in enumerate(rows, 1):
            content.add_widget(self._row_widget(row, index, keys, width))
        scroll.add_widget(content)
        self.table_area.add_widget(scroll)

    def _paint_header(self, widget):
        with widget.canvas.before:
            Color(*PRIMARY)
            bg = RoundedRectangle(radius=[dp(8)])
        widget.bind(pos=lambda o, v: setattr(bg, "pos", v), size=lambda o, v: setattr(bg, "size", v))

    def _row_widget(self, row, index, keys, width):
        box = BoxLayout(size_hint=(None, None), width=width, height=dp(52), spacing=dp(2), padding=[dp(2), dp(2)])
        for key in keys:
            value = row.get(key, "")
            text = str(value)
            if len(text) > 26:
                text = text[:25] + "…"
            box.add_widget(self.lbl(text, "8sp", SECONDARY, False, "center"))
        if self.can_write(self.active_table):
            actions = BoxLayout(size_hint_x=None, width=dp(145), spacing=dp(3))
            actions.add_widget(self.btn("ویرایش", lambda *_a, r=dict(row): self.open_editor(self.active_table, r), PRIMARY, dp(46)))
            actions.add_widget(self.btn("حذف", lambda *_a, r=dict(row): self.confirm_delete(self.active_table, r), (0.72, 0.16, 0.18, 1), dp(46)))
            box.add_widget(actions)
        if index % 2 == 0:
            with box.canvas.before:
                Color(0.94, 0.97, 0.985, 1)
                bg = RoundedRectangle(radius=[dp(6)])
            box.bind(pos=lambda o, v: setattr(bg, "pos", v), size=lambda o, v: setattr(bg, "size", v))
        return box

    def open_editor(self, table, row):
        fields = [k for k in (FORM_FIELDS.get(table) or self._infer_fields(row)) if k not in HIDDEN]
        if not fields:
            self.show_message("فرم این جدول", "ساختار جدول از داده واقعی مشخص نشد. ابتدا حداقل یک رکورد ثبت‌شده در جدول وجود داشته باشد.")
            return
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(7))
        scroll = ScrollView(do_scroll_x=False)
        form = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, padding=[dp(3), dp(3)])
        form.bind(minimum_height=form.setter("height"))
        inputs = {}
        for field in fields:
            form.add_widget(self.lbl(COLUMNS.get(field, field), "10sp", PRIMARY, True))
            value = "" if row is None else str(row.get(field, ""))
            ti = TextInput(text=value, font_name=font_name(), font_size="11sp", halign="right", multiline=False,
                           size_hint_y=None, height=dp(42), padding=[dp(9), dp(8)])
            inputs[field] = ti
            form.add_widget(ti)
        scroll.add_widget(form)
        root.add_widget(scroll)
        actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        popup = Popup(title=rtl_text(("ویرایش" if row else "ثبت جدید") + " • " + FRIENDLY.get(table, table)),
                      content=root, size_hint=(0.94, 0.86), auto_dismiss=False)
        actions.add_widget(self.btn("انصراف", lambda *_: popup.dismiss(), SECONDARY, dp(42)))
        actions.add_widget(self.btn("ذخیره اطلاعات", lambda *_: self.save_record(table, row, inputs, popup), SUCCESS, dp(42)))
        root.add_widget(actions)
        popup.open()

    def _infer_fields(self, row):
        if row:
            return [k for k in row.keys() if k not in HIDDEN]
        return ["title", "description", "status"]

    def save_record(self, table, row, inputs, popup):
        payload = {key: widget.text.strip() for key, widget in inputs.items() if widget.text.strip() != ""}
        if not payload:
            self.show_message("ثبت اطلاعات", "حداقل یک فیلد را وارد کنید.")
            return
        popup.dismiss()
        self.status.text = rtl_text("در حال ذخیره اطلاعات واقعی…")
        def work():
            try:
                if row is None:
                    self.app_state.api.table_insert(table, payload)
                    msg = "رکورد جدید با موفقیت ثبت شد."
                else:
                    row_id = row.get("id")
                    if row_id is None:
                        raise RuntimeError("شناسه رکورد برای ویرایش پیدا نشد.")
                    self.app_state.api.table_update(table, {"id": "eq." + str(row_id)}, payload)
                    msg = "رکورد با موفقیت ویرایش شد."
                Clock.schedule_once(lambda *_: self._after_write(table, msg), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._write_error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _after_write(self, table, message):
        self.status.text = rtl_text(message)
        self.status.color = SUCCESS
        self.load_table(table)

    def _write_error(self, message):
        self.status.text = rtl_text("ذخیره انجام نشد: " + message)
        self.status.color = (0.8, 0.15, 0.15, 1)

    def confirm_delete(self, table, row):
        rid = row.get("id")
        if rid is None:
            self.show_message("حذف رکورد", "این رکورد شناسه قابل حذف ندارد.")
            return
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        root.add_widget(self.lbl("آیا از حذف این رکورد مطمئن هستید؟", "15sp", PRIMARY, True, "center"))
        root.add_widget(self.lbl("این عملیات روی اطلاعات واقعی سامانه انجام می‌شود.", "10sp", SECONDARY, False, "center"))
        actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(7))
        popup = Popup(title=rtl_text("تأیید حذف"), content=root, size_hint=(0.88, 0.38), auto_dismiss=False)
        actions.add_widget(self.btn("انصراف", lambda *_: popup.dismiss(), SECONDARY, dp(42)))
        actions.add_widget(self.btn("حذف قطعی", lambda *_: self.delete_record(table, rid, popup), (0.72, 0.16, 0.18, 1), dp(42)))
        root.add_widget(actions)
        popup.open()

    def delete_record(self, table, rid, popup):
        popup.dismiss()
        self.status.text = rtl_text("در حال حذف رکورد واقعی…")
        def work():
            try:
                self.app_state.api.table_delete(table, {"id": "eq." + str(rid)})
                Clock.schedule_once(lambda *_: self._after_write(table, "رکورد با موفقیت حذف شد."), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._write_error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def show_message(self, title, message):
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        root.add_widget(self.lbl(message, "11sp", SECONDARY, False, "center"))
        p = Popup(title=rtl_text(title), content=root, size_hint=(0.88, 0.34))
        root.add_widget(self.btn("متوجه شدم", lambda *_: p.dismiss(), PRIMARY, dp(42)))
        p.open()

    def go_dashboard(self, *_):
        try:
            self.manager.current = self.return_to or "dashboard"
        except Exception:
            pass

    def go_back(self, *_):
        self.go_dashboard()
