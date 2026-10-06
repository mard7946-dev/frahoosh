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

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME, SCHOOL_YEAR
from mobile.ui import font_name, fa_display


class ExecutiveCenterScreen(Screen):
    """Operational executive-deputy center backed by the real Supabase tables."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.students = []
        self.exams = []
        self._build()

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None or not getattr(api, "configured", False):
            raise RuntimeError("اتصال واقعی سامانه آماده نیست.")
        if not getattr(api, "access_token", ""):
            raise RuntimeError("نشست معتبر برای کار با اطلاعات وجود ندارد.")
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
        s = Spinner(
            text=fa_display(text),
            values=[fa_display(v) for v in values],
            font_name=font_name(),
            font_size="11sp",
            size_hint_y=None,
            height=dp(height),
        )
        return s

    def _table(self, headers, rows, widths=None):
        cols = len(headers)
        grid = GridLayout(cols=cols, spacing=dp(1), padding=dp(1), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        if widths:
            grid.size_hint_x = None
            grid.width = dp(sum(widths))
        for h in headers:
            grid.add_widget(self._label(h, "10sp", WHITE, 40, True))
        for row in rows:
            for value in row:
                grid.add_widget(self._label(value, "10sp", SECONDARY, 44))
        return grid

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        head.add_widget(self._button("بازگشت", self._back, SECONDARY, 42))
        head.add_widget(self._label("مرکز عملیاتی معاون اجرایی", "17sp", PRIMARY, 42, True))
        root.add_widget(head)
        self.status = self._label("داده‌ها مستقیماً از Supabase خوانده و در همان‌جا ثبت می‌شوند.", "10sp", SECONDARY, 34)
        root.add_widget(self.status)

        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(7), padding=[dp(3), dp(4)], size_hint_y=None)
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
        for title, callback in (
            ("پرونده هویتی دانش‌آموزان", self.identity),
            ("گواهی اشتغال به تحصیل", self.certificates),
            ("کارنامه‌ها", self.report_cards),
            ("صندلی کلاس", self.class_seats),
            ("صندلی امتحانی", self.exam_seats),
            ("درخواست‌های اجرایی", self.requests),
        ):
            self.body.add_widget(self._button(title, callback, PRIMARY, 48))

    # ------------------------------------------------------------------
    # Identity file: real table, not a multiline text block.
    # ------------------------------------------------------------------
    def identity(self, *_):
        self._clear()
        self.body.add_widget(self._label("پرونده هویتی دانش‌آموزان", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("اطلاعات زیر از جدول واقعی students خوانده می‌شود.", height=36))
        self.body.add_widget(self._button("بارگذاری پرونده‌های واقعی", lambda *_: self._start(
            lambda: self._load("students", {"select": "*", "order": "id.asc", "limit": "200"}),
            self._render_identity
        ), SUCCESS))

    def _render_identity(self, rows):
        self._clear()
        self.body.add_widget(self._label("پرونده هویتی — جدول اطلاعات", "16sp", PRIMARY, 42, True))
        if not rows:
            self.body.add_widget(self._label("دانش‌آموزی برای نمایش ثبت نشده است.", color=ERROR, height=44))
            return
        headers = ("نام", "نام خانوادگی", "کد ملی", "کد دانش‌آموزی", "نام پدر", "تولد", "پایه", "کلاس", "تلفن")
        data = []
        for r in rows:
            data.append((
                r.get("first_name", ""),
                r.get("last_name", ""),
                r.get("national_code", ""),
                r.get("student_code", ""),
                r.get("father_name", ""),
                r.get("birth_date", ""),
                r.get("grade", ""),
                r.get("class_name", ""),
                r.get("phone", ""),
            ))
        self.body.add_widget(self._table(headers, data))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    # ------------------------------------------------------------------
    # Certificate: official preview structure, generated from selected student.
    # ------------------------------------------------------------------
    def certificates(self, *_):
        self._clear()
        self.body.add_widget(self._label("گواهی اشتغال به تحصیل", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "پیش‌نمایش رسمی بر مبنای فایل نمونه «سامانه.pdf»؛ اطلاعات دانش‌آموز از سامانه واقعی خوانده می‌شود.",
            height=46
        ))
        self.body.add_widget(self._button("بارگذاری دانش‌آموزان", lambda *_: self._start(
            lambda: self._load("students", {"select": "*", "order": "last_name.asc,first_name.asc", "limit": "200"}),
            self._prepare_certificate
        ), SUCCESS))

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
        self.body.add_widget(self._button("نمایش گواهی رسمی", lambda *_: self._render_certificate(
            self.students[picker.values.index(picker.text)]
        ), PRIMARY, 48))

    def _school_info(self):
        try:
            rows = self._load("school_profile", {"select": "*", "limit": "1"})
            return rows[0] if rows else {}
        except Exception:
            return {}

    @staticmethod
    def _education_period(grade):
        g = str(grade or "").strip()
        if any(x in g for x in ("7", "هفتم", "8", "هشتم", "9", "نهم")):
            return "دوره متوسطه اول"
        if any(x in g for x in ("10", "دهم", "11", "یازدهم", "12", "دوازدهم")):
            return "دوره متوسطه دوم"
        return "دوره تحصیلی"

    def _render_certificate(self, student):
        school = self._school_info()
        school_name = school.get("school_name") or SCHOOL_NAME
        school_code = school.get("school_code") or ""
        academic_year = school.get("academic_year") or SCHOOL_YEAR
        grade = student.get("grade") or ""
        request_date = datetime.now().strftime("%Y/%m/%d")

        self._clear()
        self.body.add_widget(self._label("پیش‌نمایش گواهی اشتغال به تحصیل", "16sp", PRIMARY, 42, True))

        # Header exactly follows the supplied certificate hierarchy.
        self.body.add_widget(self._label("جمهوری اسلامی ایران", "13sp", SECONDARY, 30, True))
        self.body.add_widget(self._label("وزارت آموزش و پرورش", "12sp", SECONDARY, 28, True))
        self.body.add_widget(self._label(self._education_period(grade), "10sp", SECONDARY, 26))
        self.body.add_widget(self._label("گواهی اشتغال به تحصیل", "18sp", PRIMARY, 44, True))

        info = GridLayout(cols=2, spacing=dp(1), padding=dp(2), size_hint_y=None)
        info.bind(minimum_height=info.setter("height"))
        fields = [
            ("نام و نام خانوادگی دانش‌آموز", f"{student.get('first_name','')} {student.get('last_name','')}"),
            ("کد ملی", student.get("national_code", "")),
            ("نام پدر", student.get("father_name", "")),
            ("شماره شناسنامه", student.get("birth_certificate_no", "")),
            ("تاریخ تولد", student.get("birth_date", "")),
            ("سال تحصیلی", academic_year),
            ("نام و کد مدرسه", f"{school_name} ({school_code})" if school_code else school_name),
            ("پایه", grade),
            ("دوره تحصیلی", self._education_period(grade)),
            ("تاریخ تقاضا", request_date),
        ]
        for title, value in fields:
            info.add_widget(self._label(title, "10sp", WHITE, 42, True))
            info.add_widget(self._label(value or "—", "10sp", SECONDARY, 42))
        self.body.add_widget(info)

        self.body.add_widget(self._label("مشغول به تحصیل می‌باشد.", "11sp", SECONDARY, 38))
        self.body.add_widget(self._label("این گواهی طبق تقاضای مورخ:", "11sp", SECONDARY, 38))
        self.body.add_widget(self._label("فقط به منظور ارائه به:  ................................................", "11sp", SECONDARY, 42))
        self.body.add_widget(self._label("صادر گردید و فاقد هرگونه ارزش دیگری می‌باشد.", "10sp", SECONDARY, 40))

        footer = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(92))
        footer.add_widget(self._label("تاریخ:  ........................", "11sp", SECONDARY, 70))
        footer.add_widget(self._label("مهر و امضای مدیر مدرسه\n........................", "11sp", SECONDARY, 70, True))
        self.body.add_widget(footer)
        self.body.add_widget(self._label("تذکر: در صورت خالی بودن شماره شناسنامه، این فیلد از اطلاعات واقعی دانش‌آموز در سامانه تکمیل می‌شود؛ مقدار ساختگی تولید نمی‌شود.", "9sp", ERROR, 52))
        self.body.add_widget(self._button("بازگشت به امور اجرایی", lambda *_: self.show_home(), SECONDARY))

    # ------------------------------------------------------------------
    # Report cards: fixed four-column structure.
    # ------------------------------------------------------------------
    def report_cards(self, *_):
        self._clear()
        self.body.add_widget(self._label("کارنامه‌ها", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("ساختار اجباری: ردیف | درس | نمره | وضعیت", height=38, bold=True))
        self.body.add_widget(self._button("بارگذاری کارنامه‌های واقعی", lambda *_: self._start(
            lambda: self._load("student_grades", {"select": "*", "order": "student_id.asc,subject.asc,id.asc", "limit": "500"}),
            self._render_report_cards
        ), SUCCESS))

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
            self.body.add_widget(self._label("نمره‌ای ثبت نشده است.", color=ERROR, height=44))
            return
        self.body.add_widget(self._table(("ردیف", "درس", "نمره", "وضعیت"), data))

    # ------------------------------------------------------------------
    # Class seating: choose student, enter only seat number.
    # ------------------------------------------------------------------
    def class_seats(self, *_):
        self._clear()
        self.body.add_widget(self._label("صندلی کلاس", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("ابتدا دانش‌آموز انتخاب می‌شود؛ کاربر فقط شماره صندلی را وارد می‌کند.", height=44))
        self.body.add_widget(self._button("بارگذاری دانش‌آموزان", lambda *_: self._start(
            lambda: self._load("students", {"select": "*", "order": "last_name.asc,first_name.asc", "limit": "200"}),
            self._prepare_class_seat
        ), SUCCESS))

    def _prepare_class_seat(self, rows):
        self.students = rows or []
        self._clear()
        self.body.add_widget(self._label("اختصاص صندلی کلاس", "16sp", PRIMARY, 42, True))
        if not self.students:
            self.body.add_widget(self._label("دانش‌آموزی ثبت نشده است.", color=ERROR, height=44))
            return
        names = [f"{r.get('first_name','')} {r.get('last_name','')} — {r.get('student_code') or r.get('national_code','')}" for r in self.students]
        picker = self._spinner(names[0], names, 48)
        seat = self._field("فقط شماره صندلی", 48)
        self.body.add_widget(picker)
        self.body.add_widget(seat)
        self.body.add_widget(self._button("ثبت شماره صندلی", lambda *_: self._save_class_seat(
            self.students[picker.values.index(picker.text)], seat
        ), SUCCESS))

    def _save_class_seat(self, student, seat):
        number = seat.text.strip()
        if not number or not number.isdigit() or int(number) < 1:
            raise ValueError("شماره صندلی باید یک عدد مثبت باشد.")
        sid = int(student["id"])
        rows = self._load("class_seats", {"student_id": f"eq.{sid}", "limit": "1"})
        payload = {"student_id": sid, "class_name": student.get("class_name", ""), "seat_no": number}
        if rows:
            self._api().table_update("class_seats", {"id": f"eq.{rows[0]['id']}"}, payload)
        else:
            self._api().table_insert("class_seats", payload)
        # Keep the existing student_class_info record synchronized for screens
        # that consume the historical classroom_seat field.
        info = self._load("student_class_info", {"student_id": f"eq.{sid}", "limit": "1"})
        if info:
            self._api().table_update("student_class_info", {"id": f"eq.{info[0]['id']}"}, {"classroom_seat": number})
        self._ok("شماره صندلی کلاس در سامانه ثبت شد.")

    # ------------------------------------------------------------------
    # Exam seating: choose exam first, then student, then only seat number.
    # ------------------------------------------------------------------
    def exam_seats(self, *_):
        self._clear()
        self.body.add_widget(self._label("صندلی امتحانی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("ابتدا درس/آزمون مشخص می‌شود؛ سپس دانش‌آموز انتخاب و فقط شماره صندلی همان درس ثبت می‌شود.", height=48))
        self.body.add_widget(self._button("بارگذاری برنامه امتحانات", lambda *_: self._start(
            lambda: self._load("exam_schedule", {"select": "*", "order": "exam_date.asc,id.asc", "limit": "200"}),
            self._prepare_exam_seats
        ), SUCCESS))

    def _prepare_exam_seats(self, exams):
        self.exams = exams or []
        self._clear()
        self.body.add_widget(self._label("اختصاص صندلی بر اساس درس/آزمون", "16sp", PRIMARY, 42, True))
        if not self.exams:
            self.body.add_widget(self._label("برنامه امتحانی ثبت نشده است.", color=ERROR, height=44))
            return
        exam_names = [f"{e.get('subject','')} — {e.get('grade','')} — {e.get('exam_date','')}" for e in self.exams]
        epicker = self._spinner(exam_names[0], exam_names, 48)
        self.body.add_widget(epicker)
        self.body.add_widget(self._button("انتخاب آزمون", lambda *_: self._show_exam_student_form(
            self.exams[epicker.values.index(epicker.text)]
        ), PRIMARY, 46))

    def _show_exam_student_form(self, exam):
        self._clear()
        self.body.add_widget(self._label(f"آزمون: {exam.get('subject','')} | تاریخ: {exam.get('exam_date','')}", "15sp", PRIMARY, 42, True))
        names = [f"{r.get('first_name','')} {r.get('last_name','')} — {r.get('student_code') or r.get('national_code','')}" for r in self.students]
        if not names:
            self.students = self._load("students", {"select": "*", "order": "last_name.asc,first_name.asc", "limit": "200"})
            names = [f"{r.get('first_name','')} {r.get('last_name','')} — {r.get('student_code') or r.get('national_code','')}" for r in self.students]
        if not names:
            self.body.add_widget(self._label("دانش‌آموزی ثبت نشده است.", color=ERROR, height=44))
            return
        spicker = self._spinner(names[0], names, 48)
        seat = self._field("فقط شماره صندلی این درس", 48)
        self.body.add_widget(spicker)
        self.body.add_widget(seat)
        self.body.add_widget(self._button("ثبت صندلی این درس", lambda *_: self._save_exam_seat(
            exam, self.students[spicker.values.index(spicker.text)], seat
        ), SUCCESS))

    def _save_exam_seat(self, exam, student, seat):
        value = seat.text.strip()
        if not value.isdigit() or int(value) < 1:
            raise ValueError("شماره صندلی باید یک عدد مثبت باشد.")
        sid = int(student["id"])
        eid = str(exam["id"])
        existing = self._load("exam_seat_assignments", {
            "exam_id": f"eq.{eid}", "student_id": f"eq.{sid}", "limit": "1"
        })
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
        self._ok("صندلی همین درس برای دانش‌آموز ثبت شد.")

    # ------------------------------------------------------------------
    # Requests: complete operational form and real persistence.
    # ------------------------------------------------------------------
    def requests(self, *_):
        self._clear()
        self.body.add_widget(self._label("درخواست‌های اجرایی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._button("نمایش درخواست‌های واقعی", lambda *_: self._start(
            lambda: self._load("executive_requests", {"select": "*", "order": "id.desc", "limit": "200"}),
            self._render_requests
        ), SUCCESS))
        self.body.add_widget(self._button("ثبت درخواست جدید", lambda *_: self._request_form(), PRIMARY, 48))

    def _render_requests(self, rows):
        self._clear()
        self.body.add_widget(self._label("درخواست‌ها — موضوع | مخاطب | تاریخ | پیگیری | وضعیت | اطلاع‌رسانی", "15sp", PRIMARY, 46, True))
        if not rows:
            self.body.add_widget(self._label("درخواستی ثبت نشده است.", color=ERROR, height=44))
            return
        data = []
        for r in rows:
            data.append((
                r.get("title") or r.get("request_type", ""),
                r.get("target_person") or r.get("role", ""),
                r.get("request_date") or r.get("created_at", ""),
                r.get("followup") or r.get("description", ""),
                r.get("status", ""),
                r.get("notification_status", ""),
            ))
        self.body.add_widget(self._table(("موضوع", "مخاطب", "تاریخ", "پیگیری", "وضعیت", "اطلاع‌رسانی وضعیت"), data))

    def _request_form(self):
        self._clear()
        self.body.add_widget(self._label("ثبت درخواست اجرایی", "16sp", PRIMARY, 42, True))
        subject = self._field("موضوع")
        target = self._field("مخاطب")
        date = self._field("تاریخ")
        follow = self._field("پیگیری", 64)
        status = self._spinner("pending", ["pending", "در حال بررسی", "انجام شد", "رد شد"], 46)
        notification = self._spinner("ثبت شد", ["ثبت شد", "در انتظار اطلاع‌رسانی", "اطلاع‌رسانی شد"], 46)
        for w in (subject, target, date, follow, status, notification):
            self.body.add_widget(w)
        self.body.add_widget(self._button("ثبت در Supabase", lambda *_: self._save_request(
            subject, target, date, follow, status, notification
        ), SUCCESS))
        self.body.add_widget(self._button("انصراف", lambda *_: self.requests(), SECONDARY))

    def _save_request(self, subject, target, date, follow, status, notification):
        if not subject.text.strip() or not target.text.strip():
            raise ValueError("موضوع و مخاطب الزامی است.")
        request_date = date.text.strip() or datetime.now().strftime("%Y-%m-%d")
        payload = {
            "title": subject.text.strip(),
            "requester": str(getattr(self.app_state, "display_name", "معاون اجرایی")),
            "status": status.text.strip(),
            "description": follow.text.strip(),
            "role": "executive",
            "target_person": target.text.strip(),
            "request_date": request_date,
            "followup": follow.text.strip(),
            "notification_status": notification.text.strip(),
        }
        self._api().table_insert("executive_requests", payload)
        self._ok("درخواست در Supabase ثبت شد.")
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
