from datetime import datetime
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, fa_display


class ExecutiveCenterScreen(Screen):
    """Role-specific operational center for the executive deputy.

    Uses the existing canonical school tables. No mock records are created.
    """

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.section = "home"
        self._build()

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None or not getattr(api, "configured", False):
            raise RuntimeError("اتصال واقعی سامانه آماده نیست.")
        return api

    def _label(self, text, size="11sp", color=SECONDARY, height=38, bold=False):
        w = Label(text=fa_display(str(text)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="right", valign="middle",
                  size_hint_y=None, height=dp(height))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _button(self, text, callback, color=PRIMARY, height=44):
        b = Button(text=fa_display(text), font_name=font_name(), font_size="11sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(height))
        b.bind(on_release=callback)
        return b

    def _field(self, hint, height=44):
        w = TextInput(hint_text=fa_display(hint), font_name=font_name(), font_size="11sp",
                      multiline=False, size_hint_y=None, height=dp(height),
                      halign="right")
        return w

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        head.add_widget(self._button("بازگشت", self._back, SECONDARY, 42))
        head.add_widget(self._label("مرکز عملیاتی معاون اجرایی", "17sp", PRIMARY, 42, True))
        root.add_widget(head)
        self.status = self._label("اطلاعات از سامانه واقعی خوانده می‌شود.", "10sp", SECONDARY, 34)
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

    def show_home(self):
        self.section = "home"
        self._clear()
        self.body.add_widget(self._label("امور اجرایی", "18sp", PRIMARY, 44, True))
        items = [
            ("پرونده هویتی دانش‌آموزان", self.identity),
            ("گواهی اشتغال به تحصیل", self.certificates),
            ("کارنامه‌ها", self.report_cards),
            ("صندلی کلاس", self.class_seats),
            ("صندلی امتحانی", self.exam_seats),
            ("درخواست‌های اجرایی", self.requests),
        ]
        for title, cb in items:
            self.body.add_widget(self._button(title, cb, PRIMARY, 48))

    def _load(self, table, params=None):
        return self._api().table_select(table, params or {}) or []

    def identity(self):
        self.section = "identity"; self._clear()
        self.body.add_widget(self._label("پرونده هویتی دانش‌آموز", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("جدول هویتی شامل نام، نام خانوادگی، کد ملی، کد دانش‌آموزی، نام پدر، نام مادر، تاریخ تولد، تماس و نشانی است.", height=48))
        self.body.add_widget(self._button("بارگذاری پرونده‌ها", lambda *_: self._load_identity(), SUCCESS))
        self.status.text = fa_display("آماده دریافت اطلاعات واقعی.")
    def _load_identity(self):
        def work():
            try:
                rows = self._load("students", {"order":"id.asc", "limit":"100"})
                Clock.schedule_once(lambda *_: self._render_identity(rows), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()
    def _render_identity(self, rows):
        self._clear()
        self.body.add_widget(self._label("پرونده‌های هویتی", "16sp", PRIMARY, 42, True))
        if not rows:
            self.body.add_widget(self._label("پرونده‌ای ثبت نشده است.", color=ERROR, height=42)); return
        for r in rows:
            text = ("نام: %s %s\nکد ملی: %s | کد دانش‌آموزی: %s\nپدر: %s | مادر: %s\nتولد: %s | تلفن: %s\nنشانی: %s" %
                    (r.get("first_name",""), r.get("last_name",""), r.get("national_code",""), r.get("student_code",""),
                     r.get("father_name",""), r.get("mother_name",""), r.get("birth_date",""), r.get("phone",""), r.get("address","")))
            self.body.add_widget(self._label(text, height=108))

    def certificates(self):
        self.section = "certificates"; self._clear()
        self.body.add_widget(self._label("گواهی اشتغال به تحصیل", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label(
            "قالب گواهی مطابق نمونه مرجع: جمهوری اسلامی ایران، وزارت آموزش و پرورش، "
            "گواهی اشتغال به تحصیل، مشخصات دانش‌آموز، مدرسه، پایه، سال تحصیلی، علت ارائه، "
            "تاریخ و محل مهر و امضای مدیر.",
            height=72
        ))
        self.body.add_widget(self._button("نمایش درخواست‌های گواهی", lambda *_: self._load_certificates(), SUCCESS))

    def _load_certificates(self):
        def work():
            try:
                rows = self._load("certificate_requests", {"order":"created_at.desc", "limit":"100"})
                Clock.schedule_once(lambda *_: self._render_certificates(rows), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _render_certificates(self, rows):
        self._clear()
        self.body.add_widget(self._label("گواهی اشتغال به تحصیل — مطابق فرم مرجع", "16sp", PRIMARY, 44, True))
        if not rows:
            self.body.add_widget(self._label("درخواستی ثبت نشده است.", color=ERROR, height=44))
            self.body.add_widget(self._label(
                "فرم مرجع شامل این اطلاعات است: شماره، نام و نام خانوادگی، کد ملی، نام پدر، "
                "شماره شناسنامه، تاریخ تولد، سال تحصیلی، نام مدرسه، کد مدرسه، پایه، دوره تحصیلی، "
                "تاریخ تقاضا و مقصد ارائه گواهی.",
                height=86
            ))
            return
        for r in rows:
            student = str(r.get("student_name") or r.get("full_name") or "")
            national = str(r.get("national_code") or "")
            father = str(r.get("father_name") or "")
            birth = str(r.get("birth_date") or "")
            school = str(r.get("school_name") or "")
            school_code = str(r.get("school_code") or "")
            grade = str(r.get("grade") or r.get("base") or "")
            year = str(r.get("school_year") or "1404-1405")
            purpose = str(r.get("destination") or r.get("purpose") or "")
            request_date = str(r.get("request_date") or "")
            preview = (
                "جمهوری اسلامی ایران\n"
                "وزارت آموزش و پرورش\n"
                "گواهی اشتغال به تحصیل\n\n"
                "بدین وسیله گواهی می‌شود:\n"
                "نام: %s\nکد ملی: %s | فرزند: %s\n"
                "تاریخ تولد: %s | سال تحصیلی: %s\n"
                "در مدرسه: %s (%s) | در پایه: %s\n"
                "مشغول به تحصیل می‌باشد.\n\n"
                "این گواهی طبق تقاضای مورخ: %s\n"
                "فقط به منظور ارائه به: %s\n"
                "صادر گردید و فاقد هرگونه ارزش دیگری می‌باشد.\n\n"
                "تاریخ: ................    مهر و امضای مدیر مدرسه"
            ) % (student, national, father, birth, year, school, school_code, grade, request_date, purpose)
            self.body.add_widget(self._label(preview, "11sp", SECONDARY, 260, False))

    def report_cards(self):
        self.section = "report_cards"; self._clear()
        self.body.add_widget(self._label("کارنامه‌ها", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("نمایش استاندارد: ردیف | درس | نمره | وضعیت", height=40, bold=True))
        self.body.add_widget(self._button("بارگذاری ریز نمرات", lambda *_: self._load_report_cards(), SUCCESS))
    def _load_report_cards(self):
        def work():
            try:
                rows = self._load("student_grades", {"order":"student_id.asc,subject.asc,id.asc", "limit":"300"})
                Clock.schedule_once(lambda *_: self._render_report_cards(rows), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()
    def _render_report_cards(self, rows):
        self._clear()
        self.body.add_widget(self._label("کارنامه", "16sp", PRIMARY, 42, True))
        header = BoxLayout(size_hint_y=None, height=dp(38))
        for t in ("ردیف", "درس", "نمره", "وضعیت"):
            header.add_widget(self._label(t, "10sp", WHITE, 38, True))
        self.body.add_widget(header)
        for i, r in enumerate(rows, 1):
            score = r.get("score","")
            try: status = "قبول" if float(score) >= 10 else "نیازمند پیگیری"
            except Exception: status = "ثبت نشده"
            row = BoxLayout(size_hint_y=None, height=dp(42))
            for t in (str(i), str(r.get("subject","")), str(score), status):
                row.add_widget(self._label(t, "10sp", SECONDARY, 42))
            self.body.add_widget(row)

    def class_seats(self):
        self.section = "class_seats"; self._clear()
        self.body.add_widget(self._label("صندلی کلاس", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("در این بخش فقط شماره صندلی وارد می‌شود؛ اطلاعات اضافه از کاربر گرفته نمی‌شود.", height=44))
        sid = self._field("شناسه دانش‌آموز")
        seat = self._field("شماره صندلی")
        self.body.add_widget(sid); self.body.add_widget(seat)
        self.body.add_widget(self._button("ثبت شماره صندلی", lambda *_: self._save_class_seat(sid, seat), SUCCESS))
    def _save_class_seat(self, sid, seat):
        try:
            student_id = int(sid.text.strip()); number = seat.text.strip()
            if not number: raise ValueError("شماره صندلی را وارد کنید.")
            rows = self._load("student_class_info", {"student_id":f"eq.{student_id}", "limit":"1"})
            if rows:
                self._api().table_update("student_class_info", {"id":f"eq.{rows[0]['id']}"}, {"classroom_seat":number})
            else:
                self._api().table_insert("student_class_info", {"student_id":student_id, "classroom_seat":number})
            self._ok("شماره صندلی کلاس ثبت شد.")
        except Exception as exc: self._error(str(exc))

    def exam_seats(self):
        self.section = "exam_seats"; self._clear()
        self.body.add_widget(self._label("صندلی امتحانی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("صندلی هر دانش‌آموز باید داخل برنامه امتحانی همان درس اختصاص داده شود.", height=48))
        self._load_exam_schedule()

    def _load_exam_schedule(self):
        def work():
            try:
                exams = self._load("exam_schedule", {"order":"exam_date.asc,id.asc", "limit":"100"})
                Clock.schedule_once(lambda *_: self._render_exam_seats(exams), 0)
            except Exception as exc: Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()
    def _render_exam_seats(self, exams):
        self._clear()
        self.body.add_widget(self._label("اختصاص صندلی بر اساس درس", "16sp", PRIMARY, 42, True))
        if not exams:
            self.body.add_widget(self._label("برنامه امتحانی ثبت نشده است.", color=ERROR, height=44)); return
        for exam in exams:
            subject = str(exam.get("subject",""))
            eid = str(exam.get("id",""))
            date = str(exam.get("exam_date",""))
            self.body.add_widget(self._label("%s | تاریخ: %s" % (subject, date), "12sp", PRIMARY, 34, True))
            sid = self._field("شناسه دانش‌آموز")
            seat = self._field("شماره صندلی این درس")
            self.body.add_widget(sid); self.body.add_widget(seat)
            self.body.add_widget(self._button("ثبت صندلی برای این درس", lambda *_a, eid=eid, subject=subject, date=date, sid=sid, seat=seat: self._save_exam_seat(eid, subject, date, sid, seat), SUCCESS, 42))
    def _save_exam_seat(self, eid, subject, date, sid, seat):
        try:
            student_id = int(sid.text.strip()); number = int(seat.text.strip())
            if number < 1: raise ValueError("شماره صندلی باید مثبت باشد.")
            existing = self._load("exam_seat_assignments", {"exam_id":f"eq.{eid}", "student_id":f"eq.{student_id}", "limit":"1"})
            payload={"exam_id":eid,"student_id":student_id,"subject":subject,"exam_date":date,"seat_number":number}
            if existing:
                self._api().table_update("exam_seat_assignments", {"id":f"eq.{existing[0]['id']}"}, payload)
            else:
                self._api().table_insert("exam_seat_assignments", payload)
            self._ok("صندلی اختصاصی این درس ثبت شد.")
        except Exception as exc: self._error(str(exc))

    def requests(self):
        self.section = "requests"; self._clear()
        self.body.add_widget(self._label("درخواست‌های اجرایی", "17sp", PRIMARY, 44, True))
        self.body.add_widget(self._label("هر درخواست شامل موضوع، مخاطب، تاریخ، پیگیری و اطلاع‌رسانی وضعیت است.", height=44))
        self.body.add_widget(self._button("نمایش درخواست‌ها", lambda *_: self._load_requests(), SUCCESS))
        self.body.add_widget(self._button("ثبت درخواست جدید", lambda *_: self._request_form(), PRIMARY))
    def _load_requests(self):
        def work():
            try:
                rows=self._load("executive_requests", {"order":"id.desc","limit":"100"})
                Clock.schedule_once(lambda *_: self._render_requests(rows), 0)
            except Exception as exc: Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()
    def _render_requests(self, rows):
        self._clear(); self.body.add_widget(self._label("پیگیری درخواست‌ها", "16sp", PRIMARY, 42, True))
        for r in rows:
            self.body.add_widget(self._label(
                "موضوع: %s\nمخاطب: %s | تاریخ: %s\nپیگیری: %s | اطلاع‌رسانی وضعیت: %s\nوضعیت: %s" %
                (r.get("request_type") or r.get("title",""), r.get("target_person") or r.get("target") or r.get("role",""),
                 r.get("request_date") or r.get("created_at",""), r.get("followup") or r.get("description",""),
                 r.get("notification_status") or r.get("status",""), r.get("status","")), height=96))

    def _request_form(self):
        self._clear(); self.body.add_widget(self._label("ثبت درخواست اجرایی", "16sp", PRIMARY, 42, True))
        subject=self._field("موضوع درخواست"); target=self._field("مخاطب درخواست"); date=self._field("تاریخ درخواست"); follow=self._field("پیگیری درخواست", 70)
        for w in (subject,target,date,follow): self.body.add_widget(w)
        self.body.add_widget(self._button("ثبت درخواست", lambda *_: self._save_request(subject,target,date,follow), SUCCESS))
    def _save_request(self, subject,target,date,follow):
        try:
            if not subject.text.strip() or not target.text.strip(): raise ValueError("موضوع و مخاطب الزامی است.")
            payload={"title":subject.text.strip(),"requester":str(getattr(self.app_state,'display_name','معاون اجرایی')),"request_type":subject.text.strip(),"target_person":target.text.strip(),"request_date":date.text.strip() or datetime.now().strftime("%Y-%m-%d"),"followup":follow.text.strip(),"description":follow.text.strip(),"status":"pending","notification_status":"ثبت شد"}
            self._api().table_insert("executive_requests",payload)
            self._ok("درخواست ثبت شد و وضعیت آن قابل پیگیری است.")
            self.requests()
        except Exception as exc: self._error(str(exc))

    def _ok(self, text):
        self.status.text=fa_display(text); self.status.color=SUCCESS
    def _error(self, text):
        self.status.text=fa_display("خطا: "+str(text)); self.status.color=ERROR
    def _back(self,*_):
        if self.manager: self.manager.current="dashboard"
