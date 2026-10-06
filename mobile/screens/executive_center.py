from datetime import datetime

from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Line, Rectangle

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME, SCHOOL_YEAR
from mobile.ui import font_name, fa_display


class ExecutiveCenterScreen(Screen):
    """پنل عملیاتی معاون اجرایی؛ تمام عملیات این صفحه از Supabase واقعی استفاده می‌کند."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.students = []
        self.exams = []
        self._build()

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None or not getattr(api, "configured", False):
            raise RuntimeError("اتصال واقعی Supabase آماده نیست.")
        if not getattr(api, "access_token", ""):
            raise RuntimeError("نشست معتبر برای کار با اطلاعات وجود ندارد.")
        # پنل اجرایی نباید به LocalStore/دمو برود.
        if getattr(api, "local_mode", False):
            raise RuntimeError("این پنل فقط با داده واقعی Supabase کار می‌کند.")
        return api

    def _label(self, text, size="11sp", color=SECONDARY, height=38, bold=False):
        w = Label(
            text=fa_display(str(text)),
            font_name=font_name(),
            font_size=size,
            color=color,
            bold=bold,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(height),
        )
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _button(self, text, callback, color=PRIMARY, height=44):
        b = Button(
            text=fa_display(text),
            font_name=font_name(),
            font_size="11sp",
            background_normal="",
            background_color=color,
            color=WHITE,
            size_hint_y=None,
            height=dp(height),
        )
        b.bind(on_release=callback)
        return b

    def _field(self, hint, height=44):
        return TextInput(
            hint_text=fa_display(hint),
            font_name=font_name(),
            font_size="11sp",
            multiline=False,
            size_hint_y=None,
            height=dp(height),
            halign="right",
        )

    def _spinner(self, text, values, height=44):
        return Spinner(
            text=fa_display(text),
            values=[fa_display(v) for v in values],
            font_name=font_name(),
            font_size="11sp",
            size_hint_y=None,
            height=dp(height),
        )

    def _table(self, headers, rows, min_col_width=120):
        """جدول واقعی با اسکرول افقی؛ مناسب نمایش منظم در موبایل."""
        cols = len(headers)
        grid = GridLayout(
            cols=cols,
            spacing=dp(1),
            padding=dp(1),
            size_hint_y=None,
            size_hint_x=None,
        )
        grid.width = dp(max(cols * min_col_width, 360))
        grid.bind(minimum_height=grid.setter("height"))

        for h in headers:
            cell = self._label(h, "10sp", WHITE, 42, True)
            cell.width = dp(min_col_width)
            cell.size_hint_x = None
            grid.add_widget(cell)

        for row in rows:
            for value in row:
                cell = self._label(value, "10sp", SECONDARY, 46)
                cell.width = dp(min_col_width)
                cell.size_hint_x = None
                grid.add_widget(cell)

        scroll = ScrollView(
            do_scroll_x=True,
            do_scroll_y=True,
            size_hint_y=None,
            height=dp(360),
            bar_width=dp(5),
        )
        scroll.add_widget(grid)
        return scroll

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        head.add_widget(self._button("بازگشت", self._back, SECONDARY, 42))
        head.add_widget(self._label("مرکز عملیاتی معاون اجرایی", "17sp", PRIMARY, 42, True))
        root.add_widget(head)

        self.status = self._label(
            "اتصال این بخش به داده واقعی Supabase است؛ هیچ داده ساختگی برای عملیات اجرایی نمایش داده نمی‌شود.",
            "10sp",
            SECONDARY,
            42,
        )
        root.add_widget(self.status)

        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            padding=[dp(3), dp(4)],
            size_hint_y=None,
        )
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.show_home()

    def _clear(self):
        self.body.clear_widgets()

    def _start(self, worker, success):
        def run():
            try:
                data = worker()
                Clock.schedule_once(lambda *_: success(data), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=run, daemon=True).start()

    def _load(self, table, params=None):
        return self._api().table_select(table, params or {}) or []

    def show_home(self):
        self._clear()
        self.body.add_widget(self._label("امور اجرایی", "18sp", PRIMARY, 44, True))
        actions = (
            ("پرونده هویتی دانش‌آموزان", self.identity),
            ("کارنامه", self.report_cards),
            ("کارت‌های دانش‌آموزی", self.cards),
            ("برنامه امتحانی", self.exam_schedule),
            ("صندلی کلاسی", self.class_seats),
            ("صندلی امتحانی", self.exam_seats),
            ("گواهی اشتغال به تحصیل", self.certificates),
            ("درخواست‌های اجرایی", self.requests),
        )
        for title, callback in actions:
            self.body.add_widget(self._button(title, callback, PRIMARY, 48))

    # ------------------------------------------------------------------
    # 1) پرونده هویتی: جدول واقعی
    # ------------------------------------------------------------------
    def identity(self, *_):
        self._clear()
        self.body.add_widget(self._label("پرونده هویتی دانش‌آموزان", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._button(
            "بارگذاری پرونده‌های واقعی از Supabase",
            lambda *_: self._start(
                lambda: self._load(
                    "students",
                    {
                        "select": "id,first_name,last_name,national_code,student_code,father_name,mother_name,birth_certificate_no,birth_date,grade,class_name,phone,parent_phone,address",
                        "order": "id.asc",
                        "limit": "200",
                    },
                ),
                self._render_identity,
            ),
            SUCCESS,
            48,
        ))

    def _render_identity(self, rows):
        self._clear()
        self.body.add_widget(self._label("پرونده هویتی — جدول اطلاعات واقعی", "16sp", PRIMARY, 42, True))
        if not rows:
            self.body.add_widget(self._label("دانش‌آموزی برای نمایش ثبت نشده است.", color=ERROR, height=44))
            return

        headers = (
            "ردیف", "نام", "نام خانوادگی", "کد ملی", "کد دانش‌آموزی",
            "نام پدر", "شماره شناسنامه", "تاریخ تولد", "پایه", "کلاس", "تلفن"
        )
        data = []
        for i, r in enumerate(rows, 1):
            data.append((
                str(i),
                r.get("first_name", ""),
                r.get("last_name", ""),
                r.get("national_code", ""),
                r.get("student_code", ""),
                r.get("father_name", ""),
                r.get("birth_certificate_no", ""),
                r.get("birth_date", ""),
                r.get("grade", ""),
                r.get("class_name", ""),
                r.get("phone", ""),
            ))
        self.body.add_widget(self._table(headers, data, 125))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    # ------------------------------------------------------------------
    # 2) کارنامه: ردیف | نام درس | نمره | وضعیت
    # ------------------------------------------------------------------
    def report_cards(self, *_):
        self._clear()
        self.body.add_widget(self._label("کارنامه دانش‌آموزان", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "کارنامه به صورت جدول درسی نمایش داده می‌شود؛ هر ردیف یک درس و نمره همان درس است.",
            height=44,
        ))
        self._load_students_for_module(self._prepare_report_cards)

    def _load_students_for_module(self, callback):
        self._start(
            lambda: self._load(
                "students",
                {
                    "select": "id,first_name,last_name,national_code,student_code,grade,class_name",
                    "order": "last_name.asc,first_name.asc",
                    "limit": "200",
                },
            ),
            callback,
        )

    def _prepare_report_cards(self, rows):
        self.students = rows or []
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی در Supabase ثبت نشده است.", color=ERROR, height=44))
            return
        self.body.add_widget(self._label("ابتدا دانش‌آموز را انتخاب کنید.", "14sp", PRIMARY, 38, True))
        names = [f"{r.get('first_name','')} {r.get('last_name','')} — {r.get('student_code','')}" for r in self.students]
        picker = self._spinner(names[0], names, 48)
        self.body.add_widget(picker)
        self.body.add_widget(self._button(
            "نمایش کارنامه همین دانش‌آموز",
            lambda *_: self._start(
                lambda: self._load(
                    "student_grades",
                    {
                        "select": "id,subject,score,term,assessment_type,assessment_title,grade_date_shamsi",
                        "student_id": f"eq.{self.students[picker.values.index(picker.text)]['id']}",
                        "order": "subject.asc,id.asc",
                        "limit": "500",
                    },
                ),
                lambda grades: self._render_report_card_table(
                    self.students[picker.values.index(picker.text)], grades
                ),
            ),
            PRIMARY,
            48,
        ))

    def _render_report_card_table(self, student, rows):
        self._clear()
        full_name = f"{student.get('first_name','')} {student.get('last_name','')}".strip()
        self.body.add_widget(self._label(
            f"کارنامه: {full_name} | پایه {student.get('grade','')} | کلاس {student.get('class_name','')}",
            "15sp", PRIMARY, 44, True,
        ))
        data = []
        for i, r in enumerate(rows or [], 1):
            score = r.get("score", "")
            try:
                status = "قبول" if float(score) >= 10 else "نیازمند پیگیری"
            except Exception:
                status = "ثبت نشده"
            data.append((
                str(i),
                r.get("subject", ""),
                score,
                status,
            ))
        # جدول همیشه با ساختار واقعی کارنامه نمایش داده می‌شود، حتی اگر هنوز نمره‌ای ثبت نشده باشد.
        if not data:
            self.body.add_widget(self._table(
                ("ردیف", "نام درس", "نمره", "وضعیت"),
                [("—", "هنوز نمره‌ای ثبت نشده", "—", "ثبت نشده")],
                145,
            ))
        else:
            self.body.add_widget(self._table(("ردیف", "نام درس", "نمره", "وضعیت"), data, 145))
        self.body.add_widget(self._button("انتخاب دانش‌آموز دیگر", self.report_cards, SECONDARY))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    # ------------------------------------------------------------------
    # 3) کارت‌ها: دانش‌آموز | نوع کارت | کد کارت | تاریخ
    # ------------------------------------------------------------------
    def cards(self, *_):
        self._clear()
        self.body.add_widget(self._label("کارت‌های دانش‌آموزی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "کارت‌ها از جدول student_cards خوانده می‌شوند و ثبت کارت نیز با فرم مخصوص همین موضوع انجام می‌شود.",
            height=44,
        ))
        self._start(
            lambda: self._load(
                "student_cards",
                {
                    "select": "id,student_id,card_type,code,created_at",
                    "order": "id.desc",
                    "limit": "500",
                },
            ),
            self._render_cards,
        )

    def _render_cards(self, rows):
        rows = rows or []
        self._start(
            lambda: self._load(
                "students",
                {"select": "id,first_name,last_name,student_code", "order": "last_name.asc,first_name.asc", "limit": "200"},
            ),
            lambda students: self._render_cards_with_students(rows, students),
        )

    def _render_cards_with_students(self, rows, students):
        self._clear()
        self.body.add_widget(self._label("فهرست کارت‌های دانش‌آموزی", "16sp", PRIMARY, 42, True))
        lookup = {str(s.get("id")): s for s in (students or [])}
        data = []
        for i, r in enumerate(rows, 1):
            s = lookup.get(str(r.get("student_id")), {})
            data.append((
                str(i),
                f"{s.get('first_name','')} {s.get('last_name','')}".strip() or "—",
                r.get("card_type", ""),
                r.get("code", ""),
                r.get("created_at", ""),
            ))
        self.body.add_widget(self._table(
            ("ردیف", "دانش‌آموز", "نوع کارت", "کد کارت", "تاریخ ثبت"),
            data or [("—", "کارتی ثبت نشده", "—", "—", "—")],
            145,
        ))
        self.body.add_widget(self._button("صدور/ثبت کارت دانش‌آموز", lambda *_: self._card_form(students), SUCCESS, 48))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    def _card_form(self, students):
        self.students = students or []
        self._clear()
        self.body.add_widget(self._label("ثبت کارت دانش‌آموز", "16sp", PRIMARY, 42, True))
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی ثبت نشده است.", color=ERROR, height=44))
            return
        names = [f"{s.get('first_name','')} {s.get('last_name','')}" for s in self.students]
        picker = self._spinner(names[0], names, 48)
        card_type = self._spinner("کارت دانش‌آموزی", ["کارت دانش‌آموزی", "کارت ورود", "کارت کتابخانه", "سایر"], 48)
        code = self._field("کد کارت", 48)
        self.body.add_widget(picker)
        self.body.add_widget(card_type)
        self.body.add_widget(code)
        self.body.add_widget(self._button(
            "ثبت کارت",
            lambda *_: self._start(
                lambda: self._save_card(
                    self.students[picker.values.index(picker.text)],
                    card_type.text,
                    code.text,
                ),
                lambda _: self._cards_saved(),
            ),
            SUCCESS,
            48,
        ))
        self.body.add_widget(self._button("انصراف", lambda *_: self.cards(), SECONDARY))

    def _save_card(self, student, card_type, code):
        code = str(code or "").strip()
        if not code:
            raise ValueError("کد کارت الزامی است.")
        self._api().table_insert("student_cards", {
            "student_id": int(student["id"]),
            "card_type": str(card_type).strip(),
            "code": code,
        })
        return True

    def _cards_saved(self):
        self._ok("کارت دانش‌آموز با موفقیت ثبت شد.")
        self.cards()

    # ------------------------------------------------------------------
    # 4) برنامه امتحانی: ردیف | درس | پایه | تاریخ | ساعت | مدت
    # ------------------------------------------------------------------
    def exam_schedule(self, *_):
        self._clear()
        self.body.add_widget(self._label("برنامه امتحانی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "برنامه از جدول exam_schedule خوانده می‌شود و هر ردیف یک امتحان واقعی است.",
            height=42,
        ))
        self._start(
            lambda: self._load(
                "exam_schedule",
                {
                    "select": "id,subject,grade,exam_date,exam_start_time,exam_end_time,duration",
                    "order": "exam_date.asc,id.asc",
                    "limit": "500",
                },
            ),
            self._render_exam_schedule,
        )

    def _render_exam_schedule(self, rows):
        self._clear()
        self.body.add_widget(self._label("جدول برنامه امتحانی", "16sp", PRIMARY, 42, True))
        data = []
        for i, r in enumerate(rows or [], 1):
            data.append((
                str(i),
                r.get("subject", ""),
                r.get("grade", ""),
                r.get("exam_date", ""),
                f"{r.get('exam_start_time','')} تا {r.get('exam_end_time','')}".strip(),
                r.get("duration", ""),
            ))
        self.body.add_widget(self._table(
            ("ردیف", "نام درس", "پایه", "تاریخ", "ساعت", "مدت"),
            data or [("—", "امتحانی ثبت نشده", "—", "—", "—", "—")],
            135,
        ))
        self.body.add_widget(self._button("ثبت امتحان جدید", lambda *_: self._exam_schedule_form(), SUCCESS, 48))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    def _exam_schedule_form(self):
        self._clear()
        self.body.add_widget(self._label("ثبت برنامه امتحانی", "16sp", PRIMARY, 42, True))
        subject = self._field("نام درس")
        grade = self._field("پایه")
        date = self._field("تاریخ امتحان")
        start = self._field("ساعت شروع")
        end = self._field("ساعت پایان")
        duration = self._field("مدت (دقیقه)")
        for w in (subject, grade, date, start, end, duration):
            self.body.add_widget(w)
        self.body.add_widget(self._button(
            "ثبت برنامه امتحان",
            lambda *_: self._start(
                lambda: self._save_exam_schedule(subject.text, grade.text, date.text, start.text, end.text, duration.text),
                lambda _: self._exam_schedule_saved(),
            ),
            SUCCESS,
            48,
        ))
        self.body.add_widget(self._button("انصراف", self.exam_schedule, SECONDARY))

    def _save_exam_schedule(self, subject, grade, date, start, end, duration):
        if not str(subject).strip() or not str(date).strip():
            raise ValueError("نام درس و تاریخ امتحان الزامی است.")
        try:
            dur = int(str(duration or "0").strip() or "0")
        except Exception:
            raise ValueError("مدت امتحان باید عدد باشد.")
        self._api().table_insert("exam_schedule", {
            "subject": str(subject).strip(),
            "grade": str(grade).strip(),
            "exam_date": str(date).strip(),
            "exam_start_time": str(start).strip(),
            "exam_end_time": str(end).strip(),
            "duration": dur,
        })
        return True

    def _exam_schedule_saved(self):
        self._ok("برنامه امتحانی در Supabase ثبت شد.")
        self.exam_schedule()

    # ------------------------------------------------------------------
    # 5) گواهی اشتغال: دانش‌آموز + تاریخ تقاضا + مقصد + پیش‌نمایش نمونه
    # ------------------------------------------------------------------
    def certificates(self, *_):
        self._clear()
        self.body.add_widget(self._label("گواهی اشتغال به تحصیل", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "دانش‌آموز، تاریخ تقاضا و مقصد گواهی را مشخص کنید؛ سپس همان گواهی با اطلاعات واقعی دانش‌آموز نمایش داده می‌شود.",
            height=48,
        ))
        self._load_students_for_module(self._prepare_certificate)

    def _prepare_certificate(self, rows):
        self.students = rows or []
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی ثبت نشده است.", color=ERROR, height=44))
            return
        self.body.add_widget(self._label("اطلاعات درخواست گواهی", "14sp", PRIMARY, 38, True))
        names = [f"{r.get('first_name','')} {r.get('last_name','')} — {r.get('national_code','')}" for r in self.students]
        picker = self._spinner(names[0], names, 48)
        request_date = self._field("تاریخ تقاضا", 48)
        recipient = self._field("فقط به منظور ارائه به", 48)
        self.body.add_widget(picker)
        self.body.add_widget(request_date)
        self.body.add_widget(recipient)
        self.body.add_widget(self._button(
            "نمایش گواهی",
            lambda *_: self._render_certificate(
                self.students[picker.values.index(picker.text)],
                request_date.text.strip() or self._today(),
                recipient.text.strip(),
            ),
            PRIMARY,
            48,
        ))

    def _school_info(self):
        rows = self._load("school_profile", {"select": "*", "limit": "1"})
        return rows[0] if rows else {}

    @staticmethod
    def _education_period(grade):
        g = str(grade or "").strip()
        if any(x in g for x in ("7", "هفتم", "8", "هشتم", "9", "نهم")):
            return "دوره متوسطه اول"
        if any(x in g for x in ("10", "دهم", "11", "یازدهم", "12", "دوازدهم")):
            return "دوره متوسطه دوم"
        return "دوره تحصیلی"

    @staticmethod
    def _today():
        import calendar
        gy, gm, gd = datetime.now().year, datetime.now().month, datetime.now().day
        g_d_m = [0,31,59,90,120,151,181,212,243,273,304,334]
        gy2 = gy + 1 if gm > 2 else gy
        days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
        jy = -1595 + 33 * (days // 12053)
        days %= 12053
        jy += 4 * (days // 1461)
        days %= 1461
        if days > 365:
            jy += (days - 1) // 365
            days = (days - 1) % 365
        jm = 1 + (days // 31) if days < 186 else 7 + ((days - 186) // 30)
        jd = 1 + (days % 31) if days < 186 else 1 + ((days - 186) % 30)
        return f"{jy:04d}/{jm:02d}/{jd:02d}"

    def _render_certificate(self, student, request_date=None, recipient=""):
        import os

        school = self._school_info()
        school_name = school.get("school_name") or SCHOOL_NAME
        school_code = school.get("school_code") or ""
        academic_year = school.get("academic_year") or SCHOOL_YEAR
        grade = student.get("grade") or ""
        period = self._education_period(grade)
        request_date = request_date or school.get("request_date_shamsi") or self._today()
        full_name = f"{student.get('first_name','')} {student.get('last_name','')}".strip()
        father_name = student.get("father_name") or ""
        birth_no = student.get("birth_certificate_no") or ""
        birth_date = student.get("birth_date") or ""
        national_code = student.get("national_code") or ""
        principal = school.get("principal_name") or ""

        self._clear()
        self.body.add_widget(self._label("گواهی اشتغال به تحصیل — پیش‌نمایش نمونه", "16sp", PRIMARY, 42, True))
        page = FloatLayout(size_hint=(None, None), size=(dp(842), dp(595)))
        with page.canvas.before:
            Color(0.10, 0.10, 0.10, 1)
            Line(rectangle=(0, 0, dp(842), dp(555)), width=1.0)

        def txt(value, x, y, w, h, size="11sp", bold=False, color=SECONDARY, halign="right"):
            lab = Label(
                text=fa_display(str(value)),
                font_name=font_name(),
                font_size=size,
                color=color,
                bold=bold,
                size_hint=(None, None),
                size=(dp(w), dp(h)),
                pos=(dp(x), dp(y)),
                halign=halign,
                valign="middle",
            )
            lab.text_size = (dp(w), dp(h))
            page.add_widget(lab)
            return lab

        txt("جمهوری اسلامی ایران", 330, 540, 190, 22, "11sp", True, SECONDARY, "center")
        txt("وزارت آموزش و پرورش", 320, 518, 210, 22, "11sp", True, SECONDARY, "center")
        txt(f"دوره تحصیلی: {period}", 295, 496, 260, 22, "10sp", False, SECONDARY, "center")
        txt("گواهی اشتغال به تحصیل", 285, 458, 280, 38, "18sp", True, SECONDARY, "center")

        photo = str(student.get("photo") or "").strip()
        if photo and os.path.exists(photo):
            page.add_widget(Image(source=photo, allow_stretch=True, keep_ratio=True, size_hint=(None, None), size=(dp(92), dp(105)), pos=(dp(24), dp(430))))
        else:
            with page.canvas:
                Color(0.92, 0.92, 0.92, 1)
                Rectangle(pos=(dp(24), dp(430)), size=(dp(92), dp(105)))
            txt("عکس", 24, 468, 92, 25, "10sp", False, SECONDARY, "center")

        txt("شماره: ................................", 70, 404, 130, 24, "10sp", False, SECONDARY, "left")
        txt(f"بدین وسیله گواهی میشود: {full_name}", 535, 404, 280, 24, "10sp", True)
        txt(f"کد ملی: {national_code}", 360, 404, 160, 24, "10sp")
        txt(f"فرزند: {father_name}", 175, 372, 160, 24, "10sp", True)
        txt(f"شماره شناسنامه: {birth_no}", 350, 372, 190, 24, "10sp")
        txt(f"تاریخ تولد: {birth_date}", 560, 372, 170, 24, "10sp")
        txt(f"سال تحصیلی: {academic_year}", 330, 340, 200, 24, "10sp")
        txt(f"در مدرسه: {school_name} ({school_code})", 515, 308, 300, 24, "10sp")
        txt(f"در پایه: {grade}", 400, 308, 105, 24, "10sp")
        txt("مشغول به تحصیل میباشد", 575, 275, 240, 25, "10sp")
        txt(f"این گواهی طبق تقاضای مورخ: {request_date}", 500, 225, 315, 25, "10sp")
        txt(f"فقط به منظور ارائه به: {recipient or '................................................'}", 485, 170, 330, 25, "10sp")
        txt("صادر گردیده و فاقد هرگونه ارزش دیگری می باشد.", 440, 105, 375, 25, "10sp")
        txt("تاریخ", 560, 68, 110, 25, "10sp", False, SECONDARY, "center")
        txt("مهر و امضا مدیر مدرسه", 315, 68, 190, 25, "10sp", True, SECONDARY, "center")
        txt(principal, 300, 42, 220, 22, "10sp", False, SECONDARY, "center")
        warning = txt("این گواهی بدون تایید (مهر و امضای زنده مدیر) فاقد اعتبار میباشد", 2, 145, 25, 300, "9sp", True, ERROR, "center")
        warning.rotation = 90
        with page.canvas:
            Color(0.15, 0.15, 0.15, 1)
            Line(rectangle=(dp(700), dp(25), dp(90), dp(90)), width=1)
        txt("تأیید", 700, 58, 90, 24, "9sp", True, SECONDARY, "center")

        sv = ScrollView(do_scroll_x=True, do_scroll_y=True, size_hint_y=None, height=dp(600))
        sv.add_widget(page)
        self.body.add_widget(sv)
        self.body.add_widget(self._button("بازگشت به گواهی‌ها", self.certificates, SECONDARY))

    # ------------------------------------------------------------------
    # 6) صندلی کلاس: جدول | دانش‌آموز | کلاس | شماره صندلی
    # ------------------------------------------------------------------
    def class_seats(self, *_):
        self._clear()
        self.body.add_widget(self._label("صندلی کلاسی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "جدول واقعی صندلی‌های ثبت‌شده؛ برای ثبت فقط دانش‌آموز و شماره صندلی انتخاب می‌شود.",
            height=44,
        ))
        self._start(
            lambda: self._load(
                "class_seats",
                {"select": "id,student_id,class_name,seat_no,created_at", "order": "id.asc", "limit": "500"},
            ),
            self._render_class_seats,
        )

    def _render_class_seats(self, rows):
        rows = rows or []
        self._start(
            lambda: self._load(
                "students",
                {"select": "id,first_name,last_name,student_code", "order": "last_name.asc,first_name.asc", "limit": "200"},
            ),
            lambda students: self._render_class_seats_with_students(rows, students),
        )

    def _render_class_seats_with_students(self, rows, students):
        self._clear()
        lookup = {str(s.get("id")): s for s in (students or [])}
        data = []
        for i, r in enumerate(rows, 1):
            s = lookup.get(str(r.get("student_id")), {})
            data.append((
                str(i),
                f"{s.get('first_name','')} {s.get('last_name','')}".strip() or "—",
                r.get("class_name", ""),
                r.get("seat_no", ""),
            ))
        self.body.add_widget(self._table(
            ("ردیف", "دانش‌آموز", "کلاس", "شماره صندلی"),
            data or [("—", "صندلی ثبت نشده", "—", "—")],
            145,
        ))
        self.body.add_widget(self._button("تخصیص/ویرایش صندلی", lambda *_: self._start(
            lambda: self._load("students", {"select": "id,first_name,last_name,class_name", "order": "last_name.asc,first_name.asc", "limit": "200"}),
            self._prepare_class_seat,
        ), SUCCESS, 48))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    def _prepare_class_seat(self, rows):
        self.students = rows or []
        self._clear()
        self.body.add_widget(self._label("تخصیص صندلی کلاس", "16sp", PRIMARY, 42, True))
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی ثبت نشده است.", color=ERROR, height=44))
            return
        names = [f"{r.get('first_name','')} {r.get('last_name','')}" for r in self.students]
        picker = self._spinner(names[0], names, 48)
        seat = self._field("فقط شماره صندلی", 48)
        self.body.add_widget(picker)
        self.body.add_widget(seat)
        self.body.add_widget(self._button(
            "ثبت شماره صندلی",
            lambda *_: self._start(
                lambda: self._save_class_seat(self.students[picker.values.index(picker.text)], seat.text),
                lambda _: self._class_seat_saved(),
            ),
            SUCCESS, 48,
        ))
        self.body.add_widget(self._button("انصراف", self.class_seats, SECONDARY))

    def _save_class_seat(self, student, seat_text):
        number = str(seat_text or "").strip()
        if not number.isdigit() or int(number) < 1:
            raise ValueError("شماره صندلی باید یک عدد مثبت باشد.")
        sid = int(student["id"])
        rows = self._load("class_seats", {"student_id": f"eq.{sid}", "limit": "1"})
        payload = {"student_id": sid, "class_name": student.get("class_name", ""), "seat_no": number}
        if rows:
            self._api().table_update("class_seats", {"id": f"eq.{rows[0]['id']}"}, payload)
        else:
            self._api().table_insert("class_seats", payload)
        return True

    def _class_seat_saved(self):
        self._ok("صندلی کلاس برای دانش‌آموز ثبت شد.")
        self.class_seats()

    # ------------------------------------------------------------------
    # 7) صندلی امتحانی: آزمون -> دانش‌آموز -> فقط شماره صندلی
    # ------------------------------------------------------------------
    def exam_seats(self, *_):
        self._clear()
        self.body.add_widget(self._label("صندلی امتحانی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "جدول هر ردیف را به یک آزمون، دانش‌آموز و شماره صندلی همان آزمون اختصاص می‌دهد.",
            height=44,
        ))
        self._start(
            lambda: self._load("exam_seat_assignments", {
                "select": "id,exam_id,student_id,subject,exam_date,seat_number",
                "order": "exam_date.asc,id.asc",
                "limit": "500",
            }),
            self._render_exam_seat_table,
        )

    def _render_exam_seat_table(self, rows):
        rows = rows or []
        self._start(
            lambda: self._load("students", {"select": "id,first_name,last_name", "order": "last_name.asc,first_name.asc", "limit": "200"}),
            lambda students: self._render_exam_seat_table_with_students(rows, students),
        )

    def _render_exam_seat_table_with_students(self, rows, students):
        self._clear()
        lookup = {str(s.get("id")): s for s in (students or [])}
        data = []
        for i, r in enumerate(rows, 1):
            s = lookup.get(str(r.get("student_id")), {})
            data.append((
                str(i),
                r.get("subject", ""),
                r.get("exam_date", ""),
                f"{s.get('first_name','')} {s.get('last_name','')}".strip() or "—",
                r.get("seat_number", ""),
            ))
        self.body.add_widget(self._table(
            ("ردیف", "آزمون/درس", "تاریخ", "دانش‌آموز", "شماره صندلی"),
            data or [("—", "تخصیصی ثبت نشده", "—", "—", "—")],
            135,
        ))
        self.body.add_widget(self._button("تخصیص صندلی برای آزمون", lambda *_: self._load_exam_picker(), SUCCESS, 48))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    def _load_exam_picker(self):
        self._start(
            lambda: self._load("exam_schedule", {
                "select": "id,subject,grade,exam_date,exam_start_time,exam_end_time",
                "order": "exam_date.asc,id.asc",
                "limit": "200",
            }),
            self._prepare_exam_seats,
        )

    def _prepare_exam_seats(self, exams):
        self.exams = exams or []
        self._clear()
        self.body.add_widget(self._label("مرحله ۱: انتخاب درس/آزمون", "16sp", PRIMARY, 42, True))
        if not self.exams:
            self.body.add_widget(self._label("برنامه امتحانی در Supabase ثبت نشده است؛ ابتدا برنامه امتحانی را ثبت کنید.", color=ERROR, height=52))
            self.body.add_widget(self._button("رفتن به برنامه امتحانی", self.exam_schedule, SECONDARY))
            return
        exam_names = [f"{e.get('subject','')} — {e.get('grade','')} — {e.get('exam_date','')}" for e in self.exams]
        epicker = self._spinner(exam_names[0], exam_names, 48)
        self.body.add_widget(epicker)
        self.body.add_widget(self._button(
            "ادامه و انتخاب دانش‌آموز",
            lambda *_: self._load_exam_students(self.exams[epicker.values.index(epicker.text)]),
            PRIMARY, 46,
        ))
        self.body.add_widget(self._button("انصراف", self.exam_seats, SECONDARY))

    def _load_exam_students(self, exam):
        self._start(
            lambda: self._load("students", {
                "select": "id,first_name,last_name,student_code,national_code,class_name,grade",
                "order": "last_name.asc,first_name.asc",
                "limit": "200",
            }),
            lambda rows: self._show_exam_student_form(exam, rows),
        )

    def _show_exam_student_form(self, exam, students):
        self.students = students or []
        self._clear()
        self.body.add_widget(self._label(
            f"مرحله ۲: دانش‌آموز | {exam.get('subject','')} | {exam.get('exam_date','')}",
            "15sp", PRIMARY, 42, True,
        ))
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی ثبت نشده است.", color=ERROR, height=44))
            return
        names = [f"{r.get('first_name','')} {r.get('last_name','')}" for r in self.students]
        spicker = self._spinner(names[0], names, 48)
        seat = self._field("مرحله ۳: فقط شماره صندلی این درس", 48)
        self.body.add_widget(spicker)
        self.body.add_widget(seat)
        self.body.add_widget(self._button(
            "ثبت صندلی همین آزمون",
            lambda *_: self._start(
                lambda: self._save_exam_seat(exam, self.students[spicker.values.index(spicker.text)], seat.text),
                lambda _: self._exam_seat_saved(),
            ),
            SUCCESS, 48,
        ))
        self.body.add_widget(self._button("انصراف", self.exam_seats, SECONDARY))

    def _save_exam_seat(self, exam, student, seat_text):
        value = str(seat_text or "").strip()
        if not value.isdigit() or int(value) < 1:
            raise ValueError("شماره صندلی باید یک عدد مثبت باشد.")
        sid = int(student["id"])
        eid = str(exam["id"])
        existing = self._load("exam_seat_assignments", {"exam_id": f"eq.{eid}", "student_id": f"eq.{sid}", "limit": "1"})
        payload = {
            "exam_id": eid,
            "student_id": sid,
            "subject": exam.get("subject", ""),
            "exam_date": exam.get("exam_date", ""),
            "seat_number": int(value),
        }
        if existing:
            self._api().table_update("exam_seat_assignments", {"id": f"eq.{existing[0]['id']}"}, payload)
        else:
            self._api().table_insert("exam_seat_assignments", payload)
        return True

    def _exam_seat_saved(self):
        self._ok("صندلی این آزمون برای دانش‌آموز ثبت شد.")
        self.exam_seats()

    # ------------------------------------------------------------------
    # 6) درخواست‌ها: فرم کامل + ثبت واقعی
    # ------------------------------------------------------------------
    def requests(self, *_):
        self._clear()
        self.body.add_widget(self._label("درخواست‌های اجرایی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._button(
            "نمایش درخواست‌های واقعی",
            lambda *_: self._start(
                lambda: self._load(
                    "executive_requests",
                    {
                        "select": "id,title,requester,status,description,created_at,role,target_person,request_date,followup,notification_status",
                        "order": "id.desc",
                        "limit": "200",
                    },
                ),
                self._render_requests,
            ),
            SUCCESS,
            48,
        ))
        self.body.add_widget(self._button("ثبت درخواست جدید", lambda *_: self._request_form(), PRIMARY, 48))

    def _render_requests(self, rows):
        self._clear()
        self.body.add_widget(self._label(
            "درخواست‌ها — موضوع | مخاطب | تاریخ | پیگیری | وضعیت | اطلاع‌رسانی وضعیت",
            "15sp",
            PRIMARY,
            46,
            True,
        ))
        if not rows:
            self.body.add_widget(self._label("درخواستی در Supabase ثبت نشده است.", color=ERROR, height=44))
            self.body.add_widget(self._button("بازگشت", lambda *_: self.requests(), SECONDARY))
            return
        data = []
        for r in rows:
            data.append((
                r.get("title", ""),
                r.get("target_person") or r.get("role", ""),
                r.get("request_date") or r.get("created_at", ""),
                r.get("followup") or "",
                r.get("status", ""),
                r.get("notification_status", ""),
            ))
        self.body.add_widget(self._table(
            ("موضوع", "مخاطب", "تاریخ", "پیگیری", "وضعیت", "اطلاع‌رسانی وضعیت"),
            data,
            145,
        ))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    def _request_form(self):
        self._clear()
        self.body.add_widget(self._label("ثبت درخواست اجرایی", "16sp", PRIMARY, 42, True))
        subject = self._field("موضوع")
        target = self._field("مخاطب")
        date = self._field("تاریخ (خالی = تاریخ امروز)")
        follow = self._field("پیگیری")
        status = self._spinner(
            "در انتظار بررسی",
            ["در انتظار بررسی", "در حال بررسی", "انجام شد", "رد شد"],
            46,
        )
        notification = self._spinner(
            "ثبت شد",
            ["ثبت شد", "در انتظار اطلاع‌رسانی", "اطلاع‌رسانی شد"],
            46,
        )
        for w in (subject, target, date, follow, status, notification):
            self.body.add_widget(w)

        self.body.add_widget(self._button(
            "ثبت درخواست در Supabase",
            lambda *_: self._start(
                lambda: self._save_request(
                    subject.text,
                    target.text,
                    date.text,
                    follow.text,
                    status.text,
                    notification.text,
                ),
                lambda _: self._requests_saved(),
            ),
            SUCCESS,
            48,
        ))
        self.body.add_widget(self._button("انصراف", lambda *_: self.requests(), SECONDARY))

    def _save_request(self, subject, target, date, follow, status, notification):
        subject = str(subject or "").strip()
        target = str(target or "").strip()
        if not subject or not target:
            raise ValueError("موضوع و مخاطب الزامی است.")

        request_date = str(date or "").strip() or self._today()
        requester = str(getattr(self.app_state, "display_name", "") or "معاون اجرایی").strip()

        payload = {
            "title": subject,
            "requester": requester,
            "status": str(status or "در انتظار بررسی").strip(),
            "description": str(follow or "").strip(),
            "role": "executive",
            "target_person": target,
            "request_date": request_date,
            "followup": str(follow or "").strip(),
            "notification_status": str(notification or "ثبت شد").strip(),
        }
        self._api().table_insert("executive_requests", payload)
        return True

    def _requests_saved(self):
        self._ok("درخواست با موفقیت در Supabase ثبت شد.")
        self.requests()

    def _ok(self, text):
        self.status.text = fa_display(text)
        self.status.color = SUCCESS

    def _error(self, text):
        self.status.text = fa_display("خطا: " + str(text))
        self.status.color = ERROR

    def _back(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
