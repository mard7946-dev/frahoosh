from datetime import datetime

from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
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
            ("گواهی اشتغال به تحصیل", self.certificates),
            ("کارنامه‌ها", self.report_cards),
            ("صندلی کلاس", self.class_seats),
            ("صندلی امتحانی", self.exam_seats),
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
    # 2) گواهی اشتغال: پیش‌نمایش رسمی با اطلاعات همان دانش‌آموز
    # ------------------------------------------------------------------
    def certificates(self, *_):
        self._clear()
        self.body.add_widget(self._label("گواهی اشتغال به تحصیل", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "پیش‌نمایش رسمی بر اساس ساختار فایل نمونه «سامانه.pdf»؛ اطلاعات فقط از دانش‌آموز انتخاب‌شده و مشخصات مدرسه خوانده می‌شود.",
            height=48,
        ))
        self.body.add_widget(self._button(
            "بارگذاری دانش‌آموزان واقعی",
            lambda *_: self._start(
                lambda: self._load(
                    "students",
                    {
                        "select": "id,first_name,last_name,national_code,father_name,birth_certificate_no,birth_date,grade,class_name,photo",
                        "order": "last_name.asc,first_name.asc",
                        "limit": "200",
                    },
                ),
                self._prepare_certificate,
            ),
            SUCCESS,
            48,
        ))

    def _prepare_certificate(self, rows):
        self.students = rows or []
        self._clear()
        self.body.add_widget(self._label("انتخاب دانش‌آموز برای پیش‌نمایش گواهی", "16sp", PRIMARY, 42, True))
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی ثبت نشده است.", color=ERROR, height=44))
            return

        names = [
            f"{r.get('first_name','')} {r.get('last_name','')} — {r.get('national_code','')}"
            for r in self.students
        ]
        picker = self._spinner(names[0], names, 48)
        self.body.add_widget(picker)
        self.body.add_widget(self._button(
            "نمایش پیش‌نمایش رسمی",
            lambda *_: self._render_certificate(
                self.students[picker.values.index(picker.text)]
            ),
            PRIMARY,
            48,
        ))

    def _school_info(self):
        # school_profile باید برای معاون اجرایی قابل خواندن باشد.
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
        # گواهی نمونه با تاریخ شمسی است. تبدیل ساده تاریخ میلادی به شمسی
        # برای نمایش تاریخ روز؛ در صورت وجود تاریخ مدرسه همان مقدار حفظ می‌شود.
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

    def _certificate_cell(self, title, value, title_width=150):
        cell = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(42), spacing=dp(2))
        cell.add_widget(self._label(title, "9sp", SECONDARY, 42, True))
        cell.add_widget(self._label(value or "—", "10sp", SECONDARY, 42))
        return cell

    def _render_certificate(self, student):
        school = self._school_info()
        school_name = school.get("school_name") or SCHOOL_NAME
        school_code = school.get("school_code") or ""
        academic_year = school.get("academic_year") or SCHOOL_YEAR
        grade = student.get("grade") or ""
        period = self._education_period(grade)
        request_date = school.get("request_date_shamsi") or self._today()
        full_name = f"{student.get('first_name','')} {student.get('last_name','')}".strip()
        father_name = student.get("father_name") or ""
        birth_no = student.get("birth_certificate_no") or ""
        birth_date = student.get("birth_date") or ""
        national_code = student.get("national_code") or ""

        self._clear()
        self.body.add_widget(self._label("پیش‌نمایش گواهی اشتغال به تحصیل", "16sp", PRIMARY, 42, True))

        certificate = BoxLayout(orientation="vertical", padding=[dp(18), dp(14)],
                                spacing=dp(3), size_hint_y=None)
        certificate.bind(minimum_height=certificate.setter("height"))

        certificate.add_widget(self._label("جمهوری اسلامی ایران", "13sp", SECONDARY, 28, True))
        certificate.add_widget(self._label("وزارت آموزش وپرورش", "12sp", SECONDARY, 26, True))
        certificate.add_widget(self._label(f"دوره تحصیلی: {period}", "11sp", SECONDARY, 28))
        certificate.add_widget(self._label("گواهی اشتغال به تحصیل", "18sp", PRIMARY, 44, True))

        certificate.add_widget(self._label(
            f"شماره: ................................    بدین وسیله گواهی میشود: {full_name} کد ملی {national_code}",
            "10sp", SECONDARY, 38
        ))
        certificate.add_widget(self._label(
            f"فرزند: {father_name}    شماره شناسنامه: {birth_no}    تاریخ تولد: {birth_date}",
            "10sp", SECONDARY, 36
        ))
        certificate.add_widget(self._label(
            f"سال تحصیلی: {academic_year}", "10sp", SECONDARY, 34
        ))
        certificate.add_widget(self._label(
            f"در مدرسه: {school_name} ({school_code})    در پایه: {grade}",
            "10sp", SECONDARY, 38
        ))
        certificate.add_widget(self._label(
            "مشغول به تحصیل میباشد", "10sp", SECONDARY, 34, True
        ))
        certificate.add_widget(self._label(
            f"این گواهی طبق تقاضای مورخ: {request_date}", "10sp", SECONDARY, 38
        ))
        certificate.add_widget(self._label(
            "فقط به منظور ارائه به: ........................................................",
            "10sp", SECONDARY, 38
        ))
        certificate.add_widget(self._label(
            "صادر گردیده و فاقد هرگونه ارزش دیگری می باشد.", "10sp", SECONDARY, 36
        ))

        footer = GridLayout(cols=2, spacing=dp(12), size_hint_y=None, height=dp(100))
        footer.add_widget(self._label("تاریخ\n" + request_date, "10sp", SECONDARY, 88))
        footer.add_widget(self._label(
            "مهر و امضا مدیر مدرسه\n................................\n"
            f"{school.get('principal_name') or ''}",
            "10sp", SECONDARY, 88, True
        ))
        certificate.add_widget(footer)

        self.body.add_widget(certificate)
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))
    # ------------------------------------------------------------------
    # 3) کارنامه: ردیف | درس | نمره | وضعیت
    # ------------------------------------------------------------------
    def report_cards(self, *_):
        self._clear()
        self.body.add_widget(self._label("کارنامه‌ها", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._button(
            "بارگذاری کارنامه‌های واقعی",
            lambda *_: self._start(
                lambda: self._load(
                    "student_grades",
                    {
                        "select": "student_id,subject,score,term,grade_date_shamsi",
                        "order": "student_id.asc,subject.asc,id.asc",
                        "limit": "500",
                    },
                ),
                self._render_report_cards,
            ),
            SUCCESS,
            48,
        ))

    def _render_report_cards(self, rows):
        self._clear()
        self.body.add_widget(self._label("کارنامه — ردیف | درس | نمره | وضعیت", "16sp", PRIMARY, 42, True))
        data = []
        for i, r in enumerate(rows or [], 1):
            score = r.get("score", "")
            try:
                status = "قبول" if float(score) >= 10 else "نیازمند پیگیری"
            except Exception:
                status = "ثبت نشده"
            data.append((str(i), r.get("subject", ""), score, status))
        if not data:
            self.body.add_widget(self._label("نمره‌ای در Supabase ثبت نشده است.", color=ERROR, height=44))
            return
        self.body.add_widget(self._table(("ردیف", "درس", "نمره", "وضعیت"), data, 135))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    # ------------------------------------------------------------------
    # 4) صندلی کلاس: انتخاب دانش‌آموز + فقط شماره صندلی
    # ------------------------------------------------------------------
    def class_seats(self, *_):
        self._clear()
        self.body.add_widget(self._label("صندلی کلاس", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("دانش‌آموز را از فهرست انتخاب کنید؛ در فرم فقط شماره صندلی وارد می‌شود.", height=44))
        self.body.add_widget(self._button(
            "بارگذاری دانش‌آموزان",
            lambda *_: self._start(
                lambda: self._load(
                    "students",
                    {"select": "id,first_name,last_name,student_code,national_code,class_name", "order": "last_name.asc,first_name.asc", "limit": "200"},
                ),
                self._prepare_class_seat,
            ),
            SUCCESS,
            48,
        ))

    def _prepare_class_seat(self, rows):
        self.students = rows or []
        self._clear()
        self.body.add_widget(self._label("اختصاص صندلی کلاس", "16sp", PRIMARY, 42, True))
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی ثبت نشده است.", color=ERROR, height=44))
            return
        names = [
            f"{r.get('first_name','')} {r.get('last_name','')}"
            for r in self.students
        ]
        picker = self._spinner(names[0], names, 48)
        seat = self._field("فقط شماره صندلی", 48)
        self.body.add_widget(picker)
        self.body.add_widget(seat)
        self.body.add_widget(self._button(
            "ثبت شماره صندلی",
            lambda *_: self._start(
                lambda: self._save_class_seat(
                    self.students[picker.values.index(picker.text)], seat.text
                ),
                lambda _: self._ok("شماره صندلی کلاس در Supabase ثبت شد."),
            ),
            SUCCESS,
            48,
        ))

    def _save_class_seat(self, student, seat_text):
        number = str(seat_text or "").strip()
        if not number.isdigit() or int(number) < 1:
            raise ValueError("شماره صندلی باید یک عدد مثبت باشد.")
        sid = int(student["id"])
        rows = self._load("class_seats", {"student_id": f"eq.{sid}", "limit": "1"})
        payload = {
            "student_id": sid,
            "class_name": student.get("class_name", ""),
            "seat_no": number,
        }
        if rows:
            self._api().table_update("class_seats", {"id": f"eq.{rows[0]['id']}"}, payload)
        else:
            self._api().table_insert("class_seats", payload)
        return True

    # ------------------------------------------------------------------
    # 5) صندلی امتحانی: آزمون -> دانش‌آموز -> فقط شماره صندلی
    # ------------------------------------------------------------------
    def exam_seats(self, *_):
        self._clear()
        self.body.add_widget(self._label("صندلی امتحانی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "ترتیب اجباری: ابتدا درس/آزمون، سپس دانش‌آموز، سپس فقط شماره صندلی همان درس.",
            height=48,
        ))
        self.body.add_widget(self._button(
            "بارگذاری برنامه امتحانات واقعی",
            lambda *_: self._start(
                lambda: self._load(
                    "exam_schedule",
                    {
                        "select": "id,subject,grade,exam_date,exam_start_time,exam_end_time",
                        "order": "exam_date.asc,id.asc",
                        "limit": "200",
                    },
                ),
                self._prepare_exam_seats,
            ),
            SUCCESS,
            48,
        ))

    def _prepare_exam_seats(self, exams):
        self.exams = exams or []
        self._clear()
        self.body.add_widget(self._label("اختصاص صندلی بر اساس درس/آزمون", "16sp", PRIMARY, 42, True))
        if not self.exams:
            self.body.add_widget(self._label("برنامه امتحانی در Supabase ثبت نشده است.", color=ERROR, height=44))
            return
        exam_names = [
            f"{e.get('subject','')} — {e.get('grade','')} — {e.get('exam_date','')}"
            for e in self.exams
        ]
        epicker = self._spinner(exam_names[0], exam_names, 48)
        self.body.add_widget(epicker)
        self.body.add_widget(self._button(
            "انتخاب آزمون و ادامه",
            lambda *_: self._load_exam_students(
                self.exams[epicker.values.index(epicker.text)]
            ),
            PRIMARY,
            46,
        ))

    def _load_exam_students(self, exam):
        self._start(
            lambda: self._load(
                "students",
                {
                    "select": "id,first_name,last_name,student_code,national_code,class_name,grade",
                    "order": "last_name.asc,first_name.asc",
                    "limit": "200",
                },
            ),
            lambda rows: self._show_exam_student_form(exam, rows),
        )

    def _show_exam_student_form(self, exam, students):
        self.students = students or []
        self._clear()
        self.body.add_widget(self._label(
            f"آزمون: {exam.get('subject','')} | تاریخ: {exam.get('exam_date','')}",
            "15sp",
            PRIMARY,
            42,
            True,
        ))
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی در Supabase ثبت نشده است.", color=ERROR, height=44))
            return
        names = [f"{r.get('first_name','')} {r.get('last_name','')}" for r in self.students]
        spicker = self._spinner(names[0], names, 48)
        seat = self._field("فقط شماره صندلی این درس", 48)
        self.body.add_widget(spicker)
        self.body.add_widget(seat)
        self.body.add_widget(self._button(
            "ثبت صندلی این درس",
            lambda *_: self._start(
                lambda: self._save_exam_seat(
                    exam,
                    self.students[spicker.values.index(spicker.text)],
                    seat.text,
                ),
                lambda _: self._ok("صندلی همین درس برای دانش‌آموز در Supabase ثبت شد."),
            ),
            SUCCESS,
            48,
        ))

    def _save_exam_seat(self, exam, student, seat_text):
        value = str(seat_text or "").strip()
        if not value.isdigit() or int(value) < 1:
            raise ValueError("شماره صندلی باید یک عدد مثبت باشد.")
        sid = int(student["id"])
        eid = str(exam["id"])
        existing = self._load(
            "exam_seat_assignments",
            {"exam_id": f"eq.{eid}", "student_id": f"eq.{sid}", "limit": "1"},
        )
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
