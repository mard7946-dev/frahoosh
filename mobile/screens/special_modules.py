from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, CARD, SCHOOL_NAME
from mobile.ui import font_name, rtl_text, PersianTextInput


class _Card(BoxLayout):
    def __init__(self, fill=CARD, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(7), **kwargs)
        with self.canvas.before:
            Color(*fill)
            self.bg = RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class SpecialModuleScreen(Screen):
    """Real operational screens for workflows that must not be represented as generic tables."""
    def __init__(self, app_state=None, mode="attendance", **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.mode = mode
        self.students = []
        self.children = []
        self.pending_route = "panel"
        self._build_shell()

    def label(self, text, size="11sp", color=SECONDARY, bold=False, center=False, height=None):
        w = Label(text=rtl_text(str(text)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="center" if center else "right",
                  valign="middle", size_hint_y=None, height=dp(height or 34))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def btn(self, text, cb, color=PRIMARY, h=42):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="10sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(h))
        b.bind(on_release=cb)
        return b

    def _build_shell(self):
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        top.add_widget(self.btn("بازگشت", self.back, PRIMARY, 40))
        self.title = self.label("محیط عملیاتی", "18sp", PRIMARY, True, True, 42)
        top.add_widget(self.title)
        top.add_widget(self.btn("داشبورد", self.dashboard, PRIMARY, 40))
        root.add_widget(top)
        root.add_widget(self.label(f"{SCHOOL_NAME} • محیط اختصاصی و واقعی سامانه", "9sp", SECONDARY, False, True, 25))
        self.status = self.label("در حال آماده‌سازی…", "9sp", SUCCESS, True, True, 28)
        root.add_widget(self.status)
        self.body = BoxLayout(orientation="vertical", spacing=dp(6))
        root.add_widget(self.body)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        Clock.schedule_once(lambda *_: self.load(), 0.03)

    def load(self):
        self.body.clear_widgets()
        if self.mode == "attendance":
            self._attendance()
        elif self.mode == "discipline":
            self._discipline()
        elif self.mode == "report_cards":
            self._report_cards()
        elif self.mode == "finance":
            self._finance()
        elif self.mode == "parent_children":
            self._parent_children()
        elif self.mode == "identity_gate":
            self._identity_gate()
        elif self.mode == "smart_class":
            self._smart_class_hint()
        else:
            self._generic_special()

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None:
            raise RuntimeError("سرویس داده آماده نیست.")
        return api

    def _async(self, work, done):
        def run():
            try:
                result = work()
                Clock.schedule_once(lambda *_: done(result, None), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: done(None, str(exc)), 0)
        Thread(target=run, daemon=True).start()

    def _set_status(self, text, color=SUCCESS):
        self.status.text = rtl_text(text)
        self.status.color = color

    def back(self, *_):
        if self.manager:
            self.manager.current = "panel"

    def dashboard(self, *_):
        if self.manager:
            self.manager.current = "dashboard"

    def _attendance(self):
        role = str(getattr(self.app_state, "role", "") or "").strip().lower()
        if role in ("student","دانش‌آموز","parent","parents","ولی","اولیا"):
            self._student_attendance()
            return
        self.title.text = rtl_text("حضور و غیاب دبیر")
        self._set_status("کلاس‌های دبیر از اطلاعات واقعی سامانه خوانده می‌شود.")
        top = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        self.class_spinner = Spinner(text=rtl_text("در حال دریافت کلاس‌ها…"), values=(),
                                     font_name=font_name(), size_hint_x=0.72)
        top.add_widget(self.class_spinner)
        top.add_widget(self.btn("بارگذاری دانش‌آموزان", self._load_class_students, PRIMARY, 42))
        self.body.add_widget(top)
        self.attendance_area = BoxLayout(orientation="vertical")
        self.body.add_widget(self.attendance_area)
        self._async(self._teacher_classes, self._classes_loaded)

    def _student_attendance(self):
        self.title.text = rtl_text("حضور و غیاب دانش‌آموز")
        self._set_status("حضور و غیاب از جدول واقعی مدرسه برای پرونده تأییدشده خوانده می‌شود.")
        self.body.clear_widgets()
        role = str(getattr(self.app_state, "role", "") or "").strip().lower()
        if role in ("parent","parents","ولی","اولیا"):
            username = self.app_state.profile.get("username") or self.app_state.profile.get("email") or self.app_state.national_code
            self._async(lambda: self._parent_children_with_attendance(username), self._student_attendance_loaded)
            return
        sid = self.app_state.profile.get("linked_student_id") or self.app_state.profile.get("student_id")
        if not sid and isinstance(self.app_state.session, dict):
            sid = self.app_state.session.get("selected_student_id")
        self._async(lambda: self._student_attendance_bundle(sid), self._student_attendance_loaded)

    def _student_attendance_bundle(self, sid):
        if not sid:
            return ({}, [])
        api = self._api()
        students = api.table_select("students", {"id":"eq."+str(sid), "limit":"1"}) or []
        rows = api.table_select("attendance", {"student_id":"eq."+str(sid), "order":"attendance_date.desc", "limit":"100"}) or []
        return (students[0] if students else {}, rows)

    def _parent_children_with_attendance(self, username):
        api = self._api()
        links = api.table_select("parent_children", {"parent_username":"eq."+str(username), "limit":"20"}) or []
        result = []
        for link in links:
            sid = link.get("student_id")
            rows = api.table_select("students", {"id":"eq."+str(sid), "limit":"1"}) or []
            if rows:
                att = api.table_select("attendance", {"student_id":"eq."+str(sid), "order":"attendance_date.desc", "limit":"50"}) or []
                result.append((rows[0], att))
        return result

    def _student_attendance_loaded(self, data, error):
        if error:
            self._set_status("حضور و غیاب دریافت نشد: " + error, ERROR)
            return
        self.body.clear_widgets()
        if not data:
            self.body.add_widget(self.label("برای این پرونده هنوز رکورد حضور و غیاب ثبت نشده است.", "12sp", SECONDARY, True, True, 60))
            return
        if isinstance(data, list) and data and isinstance(data[0], tuple):
            for student, rows in data:
                self._attendance_card(student, rows)
        else:
            student, rows = data if isinstance(data, tuple) else ({}, data or [])
            self._attendance_card(student, rows)
        self._set_status("اطلاعات حضور و غیاب واقعی نمایش داده شد.", SUCCESS)

    def _attendance_card(self, student, rows):
        name = f"{student.get('first_name','')} {student.get('last_name','')}".strip() or "دانش‌آموز"
        card = _Card(size_hint_y=None, height=dp(150))
        card.add_widget(self.label(name + " • پایه " + str(student.get("grade") or "-") + " • کلاس " + str(student.get("class_name") or "-"), "12sp", PRIMARY, True, False, 32))
        grid = GridLayout(cols=3, size_hint_y=None, height=dp(70), spacing=dp(3))
        for caption in ("تاریخ","وضعیت","درس"):
            grid.add_widget(self.label(caption, "10sp", WHITE, True, True, 28))
        for row in rows[:4]:
            grid.add_widget(self.label(str(row.get("attendance_date") or row.get("date") or "-"), "9sp", SECONDARY, False, True, 28))
            grid.add_widget(self.label(str(row.get("status") or "-"), "9sp", SUCCESS if str(row.get("status")) == "حاضر" else ERROR, True, True, 28))
            grid.add_widget(self.label(str(row.get("subject") or "-"), "9sp", SECONDARY, False, True, 28))
        card.add_widget(grid)
        self.body.add_widget(card)

    def _teacher_classes(self):
        p = self.app_state.profile
        tid = p.get("linked_teacher_id") or p.get("teacher_id") or ""
        rows = self._api().table_select("teacher_classes", {"teacher_id": "eq." + str(tid), "limit": "50"})
        return rows or []

    def _classes_loaded(self, rows, error):
        if error:
            self._set_status("کلاس‌های دبیر دریافت نشد: " + error, ERROR)
            return
        self.teacher_classes = rows or []
        labels = [str(r.get("class_name") or r.get("name") or "کلاس بدون نام") + (" • " + str(r.get("subject")) if r.get("subject") else "") for r in self.teacher_classes]
        self.class_spinner.values = [rtl_text(x) for x in labels]
        self.class_spinner.text = self.class_spinner.values[0] if self.class_spinner.values else rtl_text("کلاسی برای دبیر ثبت نشده است.")
        self._set_status("کلاس دبیر انتخاب شد؛ فهرست دانش‌آموزان را بارگذاری کنید.", SUCCESS)

    def _selected_class(self):
        value = str(self.class_spinner.text or "")
        for r in getattr(self, "teacher_classes", []):
            candidate = str(r.get("class_name") or r.get("name") or "")
            subject = str(r.get("subject") or "")
            if value == candidate or value == candidate + (" • " + subject if subject else ""):
                return r
        return (getattr(self, "teacher_classes", []) or [None])[0]

    def _load_class_students(self, *_):
        selected = self._selected_class()
        if not selected:
            self._set_status("ابتدا یک کلاس دبیر را انتخاب کنید.", ERROR)
            return
        class_name = selected.get("class_name") or selected.get("name")
        self._set_status("در حال دریافت فهرست دانش‌آموزان کلاس…", SECONDARY)
        self._async(lambda: self._api().table_select("students", {"class_name": "eq." + str(class_name), "order": "last_name.asc", "limit": "100"}), self._students_loaded)

    def _students_loaded(self, rows, error):
        if error:
            self._set_status("فهرست دانش‌آموزان دریافت نشد: " + error, ERROR)
            return
        self.students = rows or []
        # A new class load starts a fresh attendance sheet. Do not carry
        # selections from a previously opened class into the next roster.
        self.attendance_state = {}
        self._render_attendance_rows()
        self._set_status(f"{len(self.students)} دانش‌آموز کلاس آماده ثبت حضور و غیاب است.", SUCCESS)

    def _render_attendance_rows(self):
        self.attendance_area.clear_widgets()
        head = GridLayout(cols=3, size_hint_y=None, height=dp(48), spacing=dp(4))
        for t in ("دانش‌آموز", "حاضر", "غایب"):
            head.add_widget(self.label(t, "12sp", WHITE, True, True, 44))
        self.attendance_area.add_widget(head)
        scroll = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=3, spacing=dp(4), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        self.attendance_buttons = {}
        for row in self.students:
            sid = row.get("id")
            name = f"{row.get('first_name','')} {row.get('last_name','')}".strip() or "دانش‌آموز بدون نام"
            grid.add_widget(self.label(name, "12sp", PRIMARY, True, False, 48))
            present = self.btn("حاضر", lambda *_a, s=sid: self._mark_attendance(s, "حاضر"), SUCCESS, 44)
            absent = self.btn("غایب", lambda *_a, s=sid: self._mark_attendance(s, "غایب"), ERROR, 44)
            self.attendance_buttons[sid] = (present, absent)
            grid.add_widget(present)
            grid.add_widget(absent)
        scroll.add_widget(grid)
        self.attendance_area.add_widget(scroll)
        self.attendance_area.add_widget(self.btn("ثبت نهایی حضور و غیاب", self._save_attendance, PRIMARY, 46))

    def _mark_attendance(self, sid, status):
        buttons = self.attendance_buttons.get(sid)
        if not buttons:
            return
        for b in buttons:
            b.background_color = SECONDARY
        buttons[0 if status == "حاضر" else 1].background_color = SUCCESS if status == "حاضر" else ERROR
        self.attendance_state = getattr(self, "attendance_state", {})
        self.attendance_state[sid] = status

    def _save_attendance(self, *_):
        selected = self._selected_class() or {}
        state = getattr(self, "attendance_state", {})
        if not state:
            self._set_status("حداقل وضعیت یک دانش‌آموز را انتخاب کنید.", ERROR)
            return
        teacher_id = self.app_state.profile.get("linked_teacher_id") or self.app_state.profile.get("teacher_id")
        subject = selected.get("subject") or ""
        class_name = selected.get("class_name") or selected.get("name") or ""
        date = __import__("datetime").date.today().isoformat()
        def work():
            api = self._api()
            saved = 0
            for sid, status in state.items():
                student = next((r for r in self.students if r.get("id") == sid), {})
                student_name = f"{student.get('first_name','')} {student.get('last_name','')}".strip()
                payload = {
                    "class_id": selected.get("id"),
                    "student_id": sid,
                    "student_name": student_name,
                    "teacher_id": teacher_id,
                    "class_name": class_name,
                    "subject": subject,
                    "attendance_date": date,
                    "status": status,
                    "date": date,
                    "description": "",
                }

                # One student/date/class/subject is one attendance record.
                # Re-saving the sheet updates the existing record instead of
                # creating duplicate attendance rows.
                filters = {
                    "student_id": "eq." + str(sid),
                    "attendance_date": "eq." + str(date),
                    "class_name": "eq." + str(class_name),
                }
                if subject:
                    filters["subject"] = "eq." + str(subject)

                existing_teacher = api.table_select(
                    "teacher_attendance",
                    {**filters, "limit": "1"},
                ) or []
                if existing_teacher and existing_teacher[0].get("id"):
                    api.table_update(
                        "teacher_attendance",
                        {"id": "eq." + str(existing_teacher[0]["id"])},
                        payload,
                    )
                else:
                    api.table_insert("teacher_attendance", payload)

                existing_shared = api.table_select(
                    "attendance",
                    {**filters, "limit": "1"},
                ) or []
                if existing_shared and existing_shared[0].get("id"):
                    api.table_update(
                        "attendance",
                        {"id": "eq." + str(existing_shared[0]["id"])},
                        payload,
                    )
                else:
                    api.table_insert("attendance", payload)
                saved += 1
            return saved
        self._set_status("در حال ثبت حضور و غیاب واقعی…", SECONDARY)
        self._async(work, lambda n,e: self._set_status((f"{n} وضعیت با موفقیت ثبت شد." if not e else "ثبت حضور و غیاب ناموفق بود: " + e), SUCCESS if not e else ERROR))

    def _discipline(self):
        self.title.text = rtl_text("ثبت مورد انضباطی")
        self._set_status("ثبت انضباطی بر اساس فهرست همان کلاس دبیر انجام می‌شود.")
        self._discipline_class_top()
        self.discipline_area = BoxLayout(orientation="vertical", spacing=dp(6))
        self.body.add_widget(self.discipline_area)
        self._async(self._teacher_classes, self._discipline_classes_loaded)

    def _discipline_class_top(self):
        top = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        self.disc_class = Spinner(text=rtl_text("انتخاب کلاس"), values=(), font_name=font_name(), size_hint_x=.72)
        top.add_widget(self.disc_class)
        top.add_widget(self.btn("بارگذاری", self._load_discipline_students, PRIMARY, 42))
        self.body.add_widget(top)

    def _discipline_classes_loaded(self, rows, error):
        self.teacher_classes = rows or []
        labels = [str(r.get("class_name") or r.get("name") or "") + (" • " + str(r.get("subject")) if r.get("subject") else "") for r in self.teacher_classes]
        self.disc_class.values = [rtl_text(x) for x in labels]
        if labels: self.disc_class.text = rtl_text(labels[0])

    def _load_discipline_students(self, *_):
        selected = self._selected_disc_class()
        if not selected:
            self._set_status("کلاس را انتخاب کنید.", ERROR); return
        class_name = selected.get("class_name") or selected.get("name")
        self._set_status("در حال دریافت فهرست دانش‌آموزان…", SECONDARY)
        self._async(lambda: self._api().table_select("students", {"class_name": "eq."+str(class_name), "order":"last_name.asc","limit":"100"}), self._discipline_students_loaded)

    def _selected_disc_class(self):
        value = str(self.disc_class.text or "")
        for r in getattr(self, "teacher_classes", []):
            base = str(r.get("class_name") or r.get("name") or "")
            full = base + (" • " + str(r.get("subject")) if r.get("subject") else "")
            if value == full or value == base:
                return r
        return (getattr(self, "teacher_classes", []) or [None])[0]

    def _discipline_students_loaded(self, rows, error):
        if error:
            self._set_status("فهرست دانش‌آموزان دریافت نشد: " + error, ERROR)
            return
        self.students = rows or []
        self.discipline_area.clear_widgets()
        self.discipline_widgets = {}

        # Same class roster layout as attendance: one student per row, with
        # the disciplinary type selected from a dropdown and one final save.
        head = GridLayout(cols=2, size_hint_y=None, height=dp(46), spacing=dp(4))
        head.add_widget(self.label("دانش‌آموز", "12sp", WHITE, True, True, 42))
        head.add_widget(self.label("نوع مشکل انضباطی", "12sp", WHITE, True, True, 42))
        self.discipline_area.add_widget(head)

        scroll = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=2, spacing=dp(4), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        kinds = ("تأخیر", "بی‌انضباطی", "بی‌احترامی", "عدم انجام تکلیف",
                 "ترک کلاس", "استفاده از تلفن همراه", "سایر")
        for row in self.students:
            sid = row.get("id")
            name = f"{row.get('first_name','')} {row.get('last_name','')}".strip() or "دانش‌آموز"
            grid.add_widget(self.label(name, "12sp", PRIMARY, True, False, 50))
            spinner = Spinner(
                text=rtl_text("نوع مشکل را انتخاب کنید"),
                values=tuple(rtl_text(x) for x in kinds),
                font_name=font_name(),
                size_hint_y=None,
                height=dp(46),
            )
            self.discipline_widgets[sid] = spinner
            grid.add_widget(spinner)
        scroll.add_widget(grid)
        self.discipline_area.add_widget(scroll)
        self.discipline_area.add_widget(
            self.btn("ثبت موارد انتخاب‌شده", self._save_discipline, SUCCESS, 46)
        )

    def _save_discipline(self, *_):
        placeholder = rtl_text("نوع مشکل را انتخاب کنید")
        selected = [
            (sid, sp.text)
            for sid, sp in getattr(self, "discipline_widgets", {}).items()
            if sp.text and sp.text != placeholder
        ]
        if not selected:
            self._set_status("برای ثبت، نوع مشکل انضباطی را از کشو انتخاب کنید.", ERROR)
            return
        teacher_id = self.app_state.profile.get("linked_teacher_id") or self.app_state.profile.get("teacher_id")
        actor = self.app_state.profile.get("username") or self.app_state.display_name
        record_date = __import__("datetime").date.today().isoformat()

        def work():
            api = self._api()
            saved = 0
            failures = []
            for sid, kind in selected:
                # These are the real columns of the canonical ZIP/Supabase
                # discipline_records table. Do not send decorative fields.
                payload = {
                    "student_id": sid,
                    "teacher_id": teacher_id,
                    "title": kind,
                    "description": "ثبت مورد انضباطی: " + kind,
                    "priority": "normal",
                    "status": "pending",
                    "item_id": None,
                    "deduction": 0,
                    "actor_username": actor,
                    "actor_role": str(getattr(self.app_state, "role", "teacher") or "teacher"),
                    "record_date": record_date,
                    "note": "ثبت از محیط انضباط دبیر در تاریخ " + record_date,
                }
                try:
                    api.table_insert("discipline_records", payload)
                    saved += 1
                except Exception as exc:
                    failures.append(str(exc))
            if failures:
                raise RuntimeError(f"{saved} مورد ثبت شد؛ {len(failures)} مورد ثبت نشد. " + failures[0])
            return saved

        self._set_status("در حال ثبت موارد انضباطی…", SECONDARY)
        self._async(
            work,
            lambda n, e: self._set_status(
                (f"{n} مورد انضباطی ثبت شد." if not e else "ثبت انضباطی ناموفق بود: " + e),
                SUCCESS if not e else ERROR,
            ),
        )

    def _report_cards(self):
        self.title.text = rtl_text("کارنامه دانش‌آموز")
        self._set_status("نمایش کارنامه به شکل کارنامه واقعی، نه جدول.")
        role = str(getattr(self.app_state, "role", "") or "").strip().lower()
        sid = self.app_state.profile.get("linked_student_id") or self.app_state.profile.get("student_id")
        if role in ("parent","parents","ولی","اولیا") and isinstance(self.app_state.session, dict):
            sid = self.app_state.session.get("selected_student_id") or sid
        if sid:
            self._async(self._report_data, self._report_loaded)
        elif role in ("parent","parents","ولی","اولیا"):
            username = self.app_state.profile.get("username") or self.app_state.profile.get("email") or self.app_state.national_code
            self._async(lambda: self._parent_report_children(username), self._report_students_loaded)
        else:
            self._async(lambda: self._api().table_select("students", {"order":"last_name.asc","limit":"100"}), self._report_students_loaded)

    def _parent_report_children(self, username):
        api = self._api()
        links = api.table_select("parent_children", {"parent_username":"eq."+str(username), "limit":"20"}) or []
        result = []
        for link in links:
            sid = link.get("student_id")
            rows = api.table_select("students", {"id":"eq."+str(sid), "limit":"1"}) or []
            result.extend(rows)
        return result

    def _report_students_loaded(self, rows, error):
        if error:
            self._set_status("فهرست دانش‌آموزان برای کارنامه دریافت نشد: " + error, ERROR)
            return
        self.body.clear_widgets()
        self.body.add_widget(self.label("ابتدا دانش‌آموز موردنظر را برای مشاهده کارنامه انتخاب کنید.", "12sp", PRIMARY, True, True, 40))
        scroll = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for row in rows or []:
            name = f"{row.get('first_name','')} {row.get('last_name','')}".strip() or "دانش‌آموز"
            grid.add_widget(self.btn(name + " • " + str(row.get("grade") or "-") + " / " + str(row.get("class_name") or "-"),
                                      lambda *_a, sid=row.get("id"): self._show_report_for_student(sid), PRIMARY, 42))
        scroll.add_widget(grid)
        self.body.add_widget(scroll)

    def _show_report_for_student(self, sid):
        if not sid:
            return
        self.app_state.profile["linked_student_id"] = sid
        self._async(self._report_data, self._report_loaded)

    def _report_data(self):
        profile = self.app_state.profile
        sid = (
            self.app_state.session.get("selected_student_id")
            if isinstance(self.app_state.session, dict) else None
        ) or profile.get("linked_student_id") or profile.get("student_id")
        if not sid:
            rows = self._api().table_select(
                "students",
                {"national_code": "eq." + str(self.app_state.national_code), "limit": "1"},
            )
            sid = (rows or [{}])[0].get("id")

        api = self._api()
        role = str(getattr(self.app_state, "role", "") or "").strip().lower()
        detailed = api.table_select(
            "student_grades",
            {"student_id": "eq." + str(sid), "order": "grade_date.desc", "limit": "100"},
        ) or []
        # The ZIP grade workflow exposes a manager_released flag. Students and
        # parents must only see released detailed grades.
        if role in ("student", "دانش‌آموز", "parent", "parents", "ولی", "اولیا"):
            detailed = [g for g in detailed if bool(g.get("manager_released"))]
        legacy = api.table_select(
            "grades",
            {"student_id": "eq." + str(sid), "order": "grade_date.desc", "limit": "100"},
        ) or []
        cards = api.table_select(
            "report_cards",
            {"student_id": "eq." + str(sid), "order": "id.desc", "limit": "1"},
        ) or []
        student = api.table_select("students", {"id": "eq." + str(sid), "limit": "1"})
        grades = detailed or legacy
        return (student[0] if student else {}, grades, cards[0] if cards else {})

    def _report_editor(self, row=None):
        sid = (
            self.app_state.session.get("selected_student_id")
            if isinstance(self.app_state.session, dict) else None
        ) or self.app_state.profile.get("linked_student_id") or self.app_state.profile.get("student_id")
        if not sid:
            self._set_status("ابتدا دانش‌آموز را برای کارنامه انتخاب کنید.", ERROR)
            return

        fields = [
            ("term", "نوبت"),
            ("average", "معدل"),
            ("grade_level", "پایه"),
            ("academic_year", "سال تحصیلی"),
            ("report_date", "تاریخ کارنامه"),
            ("description", "توضیحات"),
        ]
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        scroll = ScrollView(do_scroll_x=False)
        form = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        inputs = {}
        for key, hint in fields:
            form.add_widget(self.label(hint, "9sp", PRIMARY, True, False, 26))
            ti = PersianTextInput(
                text="" if row is None else str(row.get(key) or ""),
                hint_text=rtl_text(hint),
                font_size="12sp",
                size_hint_y=None,
                height=dp(44 if key != "description" else 76),
                multiline=key == "description",
            )
            inputs[key] = ti
            form.add_widget(ti)
        scroll.add_widget(form)
        root.add_widget(scroll)
        actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        popup = Popup(
            title=rtl_text(("ویرایش" if row else "ثبت جدید") + " • کارنامه"),
            content=root,
            size_hint=(.95, .88),
            auto_dismiss=False,
        )
        actions.add_widget(self.btn("انصراف", lambda *_: popup.dismiss(), SECONDARY, 40))
        actions.add_widget(self.btn("ذخیره", lambda *_: self._save_report(sid, row, inputs, popup), SUCCESS, 40))
        root.add_widget(actions)
        popup.open()

    def _save_report(self, sid, row, inputs, popup):
        payload = {k: v.text.strip() for k, v in inputs.items() if v.text.strip()}
        payload["student_id"] = sid
        if not payload.get("term"):
            self._set_status("نوبت کارنامه الزامی است.", ERROR)
            return
        popup.dismiss()
        def work():
            api = self._api()
            if row and row.get("id"):
                return api.table_update("report_cards", {"id": "eq." + str(row["id"])}, payload)
            return api.table_insert("report_cards", payload)
        self._async(
            work,
            lambda _, e: self._report_write_done(
                "کارنامه با موفقیت " + ("ویرایش شد." if row else "ثبت شد."), e
            ),
        )

    def _report_write_done(self, msg, error):
        self._set_status(("خطا: " + error) if error else msg, ERROR if error else SUCCESS)
        if not error:
            self._async(self._report_data, self._report_loaded)

    def _delete_report(self, *_):
        row = getattr(self, "report_official", None)
        if not row or not row.get("id"):
            self._set_status("ابتدا یک کارنامه را برای حذف انتخاب کنید.", ERROR)
            return
        def work():
            return self._api().table_delete("report_cards", {"id": "eq." + str(row["id"])})
        self._async(work, lambda _, e: self._report_write_done("کارنامه حذف شد.", e))

    def _report_loaded(self, data, error):
        if error:
            self._set_status("کارنامه دریافت نشد: " + error, ERROR)
            return
        student, grades, official = data
        self.report_official = dict(official or {})
        self.body.clear_widgets()

        role = str(getattr(self.app_state, "role", "") or "").strip().lower()
        writable_roles = {"manager", "admin", "administrator", "مدیر", "مدیریت", "executive", "معاون اجرایی"}
        if role in writable_roles:
            actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
            actions.add_widget(self.btn("ثبت جدید", lambda *_: self._report_editor(None), SUCCESS, 40))
            actions.add_widget(self.btn(
                "ویرایش",
                lambda *_: self._report_editor(self.report_official) if self.report_official
                else self._set_status("کارنامه‌ای برای ویرایش ثبت نشده است.", ERROR),
                PRIMARY, 40,
            ))
            actions.add_widget(self.btn("حذف", self._delete_report, ERROR, 40))
            self.body.add_widget(actions)

        report = _Card(fill=(0.98, 0.99, 1.0, 1))
        report.add_widget(self.label("کارنامه تحصیلی", "22sp", PRIMARY, True, True, 46))
        report.add_widget(self.label(SCHOOL_NAME, "12sp", SECONDARY, True, True, 30))
        report.add_widget(self.label(
            "سال تحصیلی " + str(official.get("academic_year") or SCHOOL_YEAR),
            "10sp", SECONDARY, False, True, 27,
        ))

        name = f"{student.get('first_name','')} {student.get('last_name','')}".strip() or "ثبت نشده"
        report.add_widget(self.label("نام دانش‌آموز: " + name, "12sp", PRIMARY, True, False, 32))
        report.add_widget(self.label(
            "پایه: " + str(student.get("grade") or "-") +
            "    کلاس: " + str(student.get("class_name") or "-") +
            "    کد ملی: " + str(student.get("national_code") or "-"),
            "10sp", SECONDARY, False, False, 30,
        ))

        weighted_sum = 0.0
        weight_total = 0.0
        scores = []
        for g in grades or []:
            try:
                score = float(g.get("score"))
                coefficient = float(g.get("coefficient") or 1)
                scores.append(score)
                weighted_sum += score * coefficient
                weight_total += coefficient
            except (TypeError, ValueError):
                pass
        calculated = (weighted_sum / weight_total) if weight_total else ((sum(scores) / len(scores)) if scores else None)
        avg = str(official.get("average")) if official.get("average") is not None else (f"{calculated:.2f}" if calculated is not None else "-")
        avg_card = _Card(fill=(0.90, 0.96, 1.0, 1), size_hint_y=None, height=dp(58))
        avg_card.add_widget(self.label("معدل کارنامه: " + avg + " از 20", "16sp", SUCCESS, True, True, 50))
        report.add_widget(avg_card)

        if not grades:
            report.add_widget(self.label(
                "برای این دانش‌آموز هنوز نمره قابل نمایش برای کارنامه ثبت نشده است.",
                "11sp", ERROR, True, True, 70,
            ))
        else:
            report.add_widget(self.label("ریز نمرات", "13sp", PRIMARY, True, True, 34))
            subject_grid = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, padding=[dp(2), dp(2)])
            subject_grid.bind(minimum_height=subject_grid.setter("height"))
            for g in grades:
                subject = str(g.get("subject") or "درس")
                score = str(g.get("score") if g.get("score") is not None else "-")
                kind = str(g.get("assessment_type") or g.get("grade_type") or "مستمر")
                term = str(g.get("term") or "-")
                title = str(g.get("assessment_title") or g.get("title") or "")
                teacher = str(g.get("teacher_name") or g.get("teacher_id") or "-")
                released = bool(g.get("manager_released")) if "manager_released" in g else True
                item = _Card(fill=(1, 1, 1, 1), size_hint_y=None, height=dp(118), padding=dp(8))
                item.add_widget(self.label(subject, "13sp", PRIMARY, True, True, 30))
                item.add_widget(self.label(
                    "نمره: " + score + " • " + kind + " • نوبت: " + term,
                    "10sp", SECONDARY, True, True, 27,
                ))
                item.add_widget(self.label(
                    ("عنوان: " + title + " • " if title else "") + "دبیر: " + teacher,
                    "9sp", SECONDARY, False, True, 25,
                ))
                item.add_widget(self.label(
                    "وضعیت نمایش: " + ("قابل مشاهده" if released else "منتظر تأیید مدیریت"),
                    "8sp", SUCCESS if released else SECONDARY, True, True, 22,
                ))
                subject_grid.add_widget(item)
            report.add_widget(subject_grid)

        report.add_widget(self.label("مهر و تأیید مدرسه / مدیریت", "9sp", SECONDARY, False, True, 38))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(report)
        self.body.add_widget(scroll)
        self._set_status("کارنامه واقعی از نمرات و رکورد کارنامه سامانه نمایش داده شد.", SUCCESS)

    def _finance(self):
        self.title.text = rtl_text("حسابداری و امور مالی")
        self._set_status("دفتر حسابداری: بدهکار، بستانکار، شماره فاکتور و مبلغ فاکتور.")
        top=GridLayout(cols=2, size_hint_y=None, height=dp(100), spacing=dp(5))
        self.fin_balance= self.label("موجودی: …","12sp",PRIMARY,True,True,45)
        self.fin_receivable=self.label("بستانکاری: …","12sp",SUCCESS,True,True,45)
        self.fin_payable=self.label("بدهکاری: …","12sp",ERROR,True,True,45)
        self.fin_invoices=self.label("فاکتورها: …","12sp",SECONDARY,True,True,45)
        for w in (self.fin_balance,self.fin_receivable,self.fin_payable,self.fin_invoices): top.add_widget(w)
        self.body.add_widget(top)
        role = str(getattr(self.app_state, "role", "") or "").strip().lower()
        writable_roles = {"manager", "admin", "administrator", "مدیر", "مدیریت", "finance", "مالی"}
        if role in writable_roles:
            actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5))
            actions.add_widget(self.btn("ثبت جدید", self._finance_editor, SUCCESS, 40))
            actions.add_widget(self.btn("ویرایش", self._finance_edit_selected, PRIMARY, 40))
            actions.add_widget(self.btn("حذف", self._finance_delete_selected, ERROR, 40))
            self.body.add_widget(actions)
        self.finance_area=BoxLayout(orientation="vertical")
        self.finance_selected=None
        self.body.add_widget(self.finance_area)
        self._async(self._finance_data,self._finance_loaded)

    def _finance_data(self):
        api=self._api()
        accounts=api.table_select("finance_accounts", {"limit":"50"}) or []
        tx=api.table_select("finance_transactions", {"order":"id.desc","limit":"50"}) or []
        inv=api.table_select("payment_records", {"order":"id.desc","limit":"50"}) or []
        return accounts,tx,inv

    def _finance_loaded(self,data,error):
        if error:
            self._set_status("اطلاعات مالی دریافت نشد: " + error, ERROR)
            return
        accounts, tx, inv = data
        balance = sum(float(a.get("balance") or 0) for a in accounts)
        debit_total = sum(float(x.get("debit") or 0) for x in tx)
        credit_total = sum(float(x.get("credit") or 0) for x in tx)
        self.fin_balance.text = rtl_text("مانده حساب‌ها: " + f"{balance:,.0f}")
        self.fin_receivable.text = rtl_text("بستانکار: " + f"{credit_total:,.0f}")
        self.fin_payable.text = rtl_text("بدهکار: " + f"{debit_total:,.0f}")
        self.fin_invoices.text = rtl_text("اسناد مالی: " + str(len(tx)))
        self.finance_area.clear_widgets()
        for row in tx[:20]:
            c = _Card(size_hint_y=None, height=dp(128))
            c.add_widget(self.label(
                "فاکتور: " + str(row.get("invoice_number") or row.get("id") or "-"),
                "11sp", PRIMARY, True, False, 28,
            ))
            c.add_widget(self.label(
                "عنوان: " + str(row.get("title") or "-") +
                " • طرف حساب: " + str(row.get("counterparty") or "-"),
                "10sp", SECONDARY, False, False, 27,
            ))
            c.add_widget(self.label(
                "مبلغ فاکتور: " + str(row.get("amount") or 0) +
                " • بدهکار: " + str(row.get("debit") or 0) +
                " • بستانکار: " + str(row.get("credit") or 0),
                "9sp", SECONDARY, False, False, 27,
            ))
            c.add_widget(self.label(
                "تاریخ: " + str(row.get("transaction_date") or "-") +
                " • دسته‌بندی: " + str(row.get("category") or "-"),
                "8sp", SECONDARY, False, False, 22,
            ))
            c.add_widget(self.btn(
                "انتخاب این سند",
                lambda *_a, x=row: self._finance_select(x),
                PRIMARY, 30,
            ))
            self.finance_area.add_widget(c)

    def _finance_select(self,row):
        self.finance_selected=dict(row or {})
        self._set_status("سند مالی انتخاب شد؛ برای ویرایش یا حذف اقدام کنید.", SUCCESS)

    def _finance_edit_selected(self,*_):
        row=getattr(self,"finance_selected",None)
        if not row:
            self._set_status("ابتدا یک سند مالی را انتخاب کنید.", ERROR)
            return
        self._finance_editor(row)

    def _finance_delete_selected(self,*_):
        row=getattr(self,"finance_selected",None)
        if not row or not row.get("id"):
            self._set_status("ابتدا یک سند مالی را انتخاب کنید.", ERROR)
            return
        rid=row.get("id")
        self._async(lambda:self._api().table_delete("finance_transactions",{"id":"eq."+str(rid)}),
                    lambda r,e:self._set_status(("سند مالی حذف شد." if not e else "حذف سند ناموفق بود: "+e),SUCCESS if not e else ERROR))

    def _finance_editor(self,row=None):
        self.body.clear_widgets()
        self.title.text = rtl_text("ویرایش سند مالی" if row else "ثبت سند مالی")
        fields = [
            ("شماره فاکتور", "invoice_number"),
            ("عنوان سند", "title"),
            ("طرف حساب", "counterparty"),
            ("مبلغ فاکتور", "amount"),
            ("بدهکار", "debit"),
            ("بستانکار", "credit"),
            ("دسته‌بندی", "category"),
            ("تاریخ سند", "transaction_date"),
            ("شرح", "description"),
        ]
        self.finance_inputs = {}
        self.finance_editing = row
        for hint, key in fields:
            ti = PersianTextInput(
                text="" if row is None else str(row.get(key) or ""),
                hint_text=rtl_text(hint),
                font_size="12sp",
                size_hint_y=None,
                height=dp(48 if key != "description" else 78),
                multiline=key == "description",
            )
            self.finance_inputs[key] = ti
            self.body.add_widget(self.label(hint, "9sp", PRIMARY, True, False, 24))
            self.body.add_widget(ti)

        type_box = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        self.finance_type = Spinner(
            text=rtl_text(str((row or {}).get("transaction_type") or "بدهکار")),
            values=(rtl_text("بدهکار"), rtl_text("بستانکار")),
            font_name=font_name(),
            size_hint_y=None,
            height=dp(42),
        )
        type_box.add_widget(self.label("نوع سند", "10sp", PRIMARY, True, False, 38))
        type_box.add_widget(self.finance_type)
        self.body.add_widget(type_box)

        actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        actions.add_widget(self.btn("ذخیره سند", self._save_finance, SUCCESS, 42))
        actions.add_widget(self.btn("بازگشت", lambda *_: self.load(), SECONDARY, 42))
        self.body.add_widget(actions)

    def _save_finance(self,*_):
        vals = {k: v.text.strip() for k, v in self.finance_inputs.items()}
        if not vals.get("amount") or not vals.get("title"):
            self._set_status("عنوان و مبلغ فاکتور الزامی است.", ERROR)
            return
        try:
            amount = float(vals.get("amount") or 0)
            debit = float(vals.get("debit") or 0)
            credit = float(vals.get("credit") or 0)
        except ValueError:
            self._set_status("مبلغ، بدهکار و بستانکار باید عددی باشند.", ERROR)
            return

        kind = str(self.finance_type.text or "بدهکار")
        if debit == 0 and credit == 0:
            if kind == "بستانکار":
                credit = amount
            else:
                debit = amount
        if debit > 0 and credit > 0:
            self._set_status("یک سند همزمان نباید بدهکار و بستانکار باشد.", ERROR)
            return

        payload = {
            "transaction_type": kind,
            "title": vals["title"],
            "amount": amount,
            "invoice_number": vals.get("invoice_number") or "",
            "debit": debit,
            "credit": credit,
            "counterparty": vals.get("counterparty") or "",
            "category": vals.get("category") or "",
            "description": vals.get("description") or "",
            "transaction_date": vals.get("transaction_date") or __import__("datetime").date.today().isoformat(),
        }
        row = getattr(self, "finance_editing", None)
        if row and row.get("id"):
            work = lambda: self._api().table_update(
                "finance_transactions", {"id": "eq." + str(row["id"])}, payload
            )
            msg = "سند مالی ویرایش شد."
        else:
            work = lambda: self._api().table_insert("finance_transactions", payload)
            msg = "سند مالی ثبت شد."

        self._set_status("در حال ذخیره سند واقعی…", SECONDARY)
        self._async(work, lambda _, e: self._finance_write_done(msg, e))

    def _finance_write_done(self,msg,error):
        self._set_status((msg if not error else "ذخیره سند ناموفق بود: " + error),
                         SUCCESS if not error else ERROR)
        if not error:
            self._finance()

    def _parent_children(self):
        self.title.text=rtl_text("اطلاعات فرزندان")
        username=self.app_state.profile.get("username") or self.app_state.profile.get("email") or self.app_state.national_code
        def work():
            api=self._api()
            rows=api.table_select("parent_children",{"parent_username":"eq."+str(username),"limit":"20"})
            children=[]
            for r in rows or []:
                sid=r.get("student_id")
                got=api.table_select("students",{"id":"eq."+str(sid),"limit":"1"})
                if got: children.append(got[0])
            return children
        self._async(work,self._children_loaded)

    def _children_loaded(self,children,error):
        if error:
            self._set_status("اطلاعات فرزندان دریافت نشد: "+error,ERROR); return
        self.children=children or []
        self.body.clear_widgets()
        self.body.add_widget(self.label("یک، دو یا چند فرزند را می‌توانید در این پنل ببینید.","11sp",PRIMARY,True,True,36))
        for child in self.children:
            c=_Card(size_hint_y=None,height=dp(120))
            name=f"{child.get('first_name','')} {child.get('last_name','')}".strip()
            c.add_widget(self.label(name or "نام ثبت نشده","14sp",PRIMARY,True,False,34))
            c.add_widget(self.label("پایه: "+str(child.get("grade") or "-")+" • کلاس: "+str(child.get("class_name") or "-"),"10sp",SECONDARY,False,False,28))
            c.add_widget(self.btn("مشاهده پرونده این فرزند",lambda *_a,s=child.get("id"):self._child_profile(s),SUCCESS,38))
            self.body.add_widget(c)
        if not self.children:
            self.body.add_widget(self.label("فرزندی برای این حساب متصل نشده است.","12sp",ERROR,True,True,60))

    def _child_profile(self,sid):
        if isinstance(self.app_state.session, dict) and sid:
            self.app_state.session["selected_student_id"] = sid
            try:
                from mobile.services.session import save_session
                save_session(self.app_state.session)
            except Exception:
                pass
        self._async(lambda:self._api().table_select("students",{"id":"eq."+str(sid),"limit":"1"}),self._show_child)

    def _show_child(self,row,error):
        if error or not row:
            self._set_status("پرونده فرزند قابل دریافت نیست.",ERROR); return
        self.body.clear_widgets()
        r=row[0] if isinstance(row,list) else row
        self.body.add_widget(self.label("پرونده دانش‌آموز","18sp",PRIMARY,True,True,40))
        for k,v in (("نام","first_name"),("نام خانوادگی","last_name"),("نام پدر","father_name"),("پایه","grade"),("کلاس","class_name"),("کد ملی","national_code"),("شماره تماس","phone")):
            self.body.add_widget(self.label(k+": "+str(r.get(v) or "ثبت نشده"),"11sp",SECONDARY,False,False,36))
        self.body.add_widget(self.btn("بازگشت به فهرست فرزندان",lambda *_:self.load(),SECONDARY,42))

    def _identity_gate(self):
        role=str(getattr(self.app_state,"role","student") or "student").lower()
        self.title.text=rtl_text("تأیید اطلاعات دانش‌آموز" if role in ("student","دانش‌آموز") else "تأیید اطلاعات فرزند")
        self._set_status("قبل از ورود به پنل، اطلاعات زیر را دقیق بررسی کنید.")
        self.gate_box=BoxLayout(orientation="vertical",spacing=dp(7))
        self.body.add_widget(self.gate_box)
        self._async(self._gate_data,self._gate_loaded)

    def _gate_data(self):
        role=str(getattr(self.app_state,"role","student") or "student").lower()
        api=self._api()
        if role in ("student","دانش‌آموز"):
            sid=self.app_state.profile.get("linked_student_id") or self.app_state.profile.get("student_id")
            rows=api.table_select("students",{"id":"eq."+str(sid),"limit":"1"}) if sid else api.table_select("students",{"national_code":"eq."+self.app_state.national_code,"limit":"1"})
            return rows[0] if rows else None
        username=self.app_state.profile.get("username") or self.app_state.profile.get("email") or self.app_state.national_code
        links=api.table_select("parent_children",{"parent_username":"eq."+str(username),"limit":"20"})
        result=[]
        for link in links or []:
            rows=api.table_select("students",{"id":"eq."+str(link.get("student_id")),"limit":"1"})
            if rows: result.append(rows[0])
        return result

    def _gate_loaded(self,data,error):
        if error:
            self._set_status("اطلاعات برای تأیید دریافت نشد: "+error,ERROR); return
        self.gate_data=data
        self.gate_box.clear_widgets()
        if isinstance(data,list):
            self.gate_box.add_widget(self.label("اطلاعات همه فرزندان متصل به حساب را بررسی کنید.","11sp",PRIMARY,True,True,38))
            for r in data:
                self._identity_card(r)
        elif data:
            self._identity_card(data)
        else:
            self.gate_box.add_widget(self.label("پرونده دانش‌آموز برای این حساب پیدا نشد.","12sp",ERROR,True,True,70))
            return
        self.gate_box.add_widget(self.btn("اطلاعات صحیح است؛ ورود به پنل",self._confirm_identity,SUCCESS,48))
        self.gate_box.add_widget(self.btn("مغایرت دارد؛ ارسال پیام به مدرسه",self._report_discrepancy,SECONDARY,48))

    def _identity_card(self,r):
        c=_Card(size_hint_y=None,height=dp(145))
        name=f"{r.get('first_name','')} {r.get('last_name','')}".strip()
        c.add_widget(self.label("نام و نام خانوادگی: "+(name or "-"),"13sp",PRIMARY,True,False,30))
        c.add_widget(self.label("کد ملی: "+str(r.get("national_code") or "-"),"10sp",SECONDARY,False,False,25))
        c.add_widget(self.label("پایه / کلاس: "+str(r.get("grade") or "-")+" / "+str(r.get("class_name") or "-"),"10sp",SECONDARY,False,False,25))
        c.add_widget(self.label("نام پدر: "+str(r.get("father_name") or "-"),"10sp",SECONDARY,False,False,25))
        c.add_widget(self.label("شماره تماس: "+str(r.get("phone") or "-"),"10sp",SECONDARY,False,False,25))
        self.gate_box.add_widget(c)

    def _confirm_identity(self,*_):
        if not self.app_state.session.get("identity_confirmed"):
            self.app_state.session["identity_confirmed"]=True
            try:
                from mobile.services.session import save_session
                save_session(self.app_state.session)
            except Exception:
                pass
        data = self.gate_data if isinstance(self.gate_data, list) else [self.gate_data]
        username = self.app_state.profile.get("username") or self.app_state.profile.get("email") or self.app_state.national_code
        role = str(getattr(self.app_state, "role", "student") or "student")
        try:
            for student in data:
                if student and student.get("id"):
                    payload = {
                        "auth_user_id": (self.app_state.user or {}).get("id"),
                        "username": username,
                        "role": role,
                        "student_id": student.get("id"),
                        "confirmation_status": "confirmed",
                    }
                    self._api().table_insert("identity_confirmations", payload)
        except Exception as exc:
            print("IDENTITY CONFIRMATION PERSIST ERROR:", repr(exc))
        if self.manager:
            target = getattr(self, "pending_route", "panel") or "panel"
            if target == "role_panel":
                role = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
                route = "parents" if role in ("parent", "parents", "ولی", "اولیا") else "students"
                try:
                    panel = self.manager.get_screen("panel")
                    panel.set_route(route)
                    self.manager.current = "panel"
                except Exception as exc:
                    print("ROLE PANEL OPEN AFTER IDENTITY ERROR:", repr(exc))
                    self.manager.current = "panel"
            else:
                self.manager.current = target if target in ("panel", "dashboard") else "panel"

    def _report_discrepancy(self,*_):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(7))
        ti=PersianTextInput(hint_text=rtl_text("شرح مغایرت را بنویسید"),font_size="12sp",multiline=True,size_hint_y=None,height=dp(150))
        root.add_widget(ti)
        popup=__import__("kivy.uix.popup",fromlist=["Popup"]).Popup(title=rtl_text("صندوق پیام مدرسه"),content=root,size_hint=(.94,.60),auto_dismiss=False)
        root.add_widget(self.btn("ارسال به صندوق پیام",lambda *_:self._send_discrepancy(ti,popup),SUCCESS,44))
        root.add_widget(self.btn("انصراف",lambda *_:popup.dismiss(),SECONDARY,44))
        popup.open()

    def _send_discrepancy(self,ti,popup):
        text=ti.text.strip()
        if not text:
            return
        popup.dismiss()
        sender=self.app_state.profile.get("username") or self.app_state.national_code
        payload={"sender":sender,"receiver":"manager","text":"مغایرت اطلاعات دانش‌آموز: "+text}
        def work():
            api=self._api()
            row=api.table_insert("messages",payload)
            if isinstance(row,list) and row and row[0].get("id"):
                api.table_insert("message_targets",{"message_id":row[0]["id"],"target_type":"role","target_value":"manager"})
            return True
        self._async(work,lambda r,e:self._set_status(("مغایرت از طریق صندوق پیام به مدرسه ارسال شد." if not e else "ارسال پیام ناموفق بود: "+e),SUCCESS if not e else ERROR))

    def _smart_class_hint(self):
        self.title.text=rtl_text("کلاس هوشمند")
        self._set_status("این بخش به محیط کلاس هوشمند متصل است.", SUCCESS)

    def _generic_special(self):
        self.body.add_widget(self.label("این زیرپنل محیط اختصاصی خود را دارد و به‌زودی تکمیل می‌شود.","12sp",PRIMARY,True,True,70))
