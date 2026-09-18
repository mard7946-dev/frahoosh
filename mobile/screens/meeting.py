from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from mobile.config import APP_NAME, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text


ROLE_MAP = {
    "admin": "manager", "administrator": "manager", "مدیر": "manager", "مدیریت": "manager",
    "معاون آموزشی": "educational", "educational": "educational",
    "معاون اجرایی": "executive", "executive": "executive",
    "معاون پرورشی": "cultural", "cultural": "cultural",
    "مشاور": "advisor", "مشاوره": "advisor", "advisor": "advisor", "counselor": "advisor",
    "دبیر": "teacher", "معلم": "teacher", "teacher": "teacher",
    "ولی": "parent", "اولیا": "parent", "parent": "parent",
    "دانش‌آموز": "student", "student": "student",
}


class MeetingScreen(Screen):
    """Real school meeting workflow backed by the unified meeting_requests API."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.people = []
        self.students = []
        self._build()

    def role(self):
        return ROLE_MAP.get(str(getattr(self.app_state, "role", "student") or "student").strip().lower(), "student")

    def label(self, text, size="11sp", color=SECONDARY, bold=False, center=False, height=None):
        w = Label(text=rtl_text(str(text)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="center" if center else "right", valign="middle",
                  size_hint_y=None, height=dp(height) if height else None)
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def button(self, text, cb, color=PRIMARY, height=44):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="11sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(height))
        b.bind(on_release=cb)
        return b

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        head.add_widget(self.button("‹ بازگشت", lambda *_: self._back(), PRIMARY, 40))
        head.add_widget(self.label("ملاقات و جلسات مدرسه", "18sp", PRIMARY, True, True))
        root.add_widget(head)
        self.status = self.label("در حال آماده‌سازی…", "9sp", SECONDARY, False, True, 34)
        root.add_widget(self.status)

        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(7), padding=[dp(2), dp(4)], size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.show()

    def show(self):
        self.body.clear_widgets()
        self.people = []
        self.students = []
        role = self.role()

        self.body.add_widget(self.label("سامانه ملاقات و جلسات", "20sp", PRIMARY, True, True, 48))
        self.body.add_widget(self.label(
            "درخواست‌ها ابتدا برای تأیید مدیر ثبت می‌شوند؛ پس از تأیید، به معاون آموزشی ارجاع و زمان نهایی اعلام می‌شود.",
            "10sp", SECONDARY, False, True, 62
        ))

        if role == "parent":
            self._parent_form()
        elif role == "teacher":
            self._teacher_form()
        elif role in ("advisor", "executive", "cultural"):
            self._staff_form()
        elif role == "manager":
            self._review_queue("manager")
        elif role == "educational":
            self._review_queue("educational")
        else:
            self.body.add_widget(self.label("این بخش برای نقش فعلی فعال نیست.", "13sp", PRIMARY, True, True, 50))

        if role not in ("manager", "educational"):
            self.body.add_widget(self.label("درخواست‌های من / مرتبط با من", "15sp", PRIMARY, True, True, 42))
            self._load_rows()

    def _field(self, hint, multiline=False, height=44):
        f = TextInput(hint_text=rtl_text(hint), font_name=font_name(), font_size="11sp",
                      multiline=multiline, halign="right", size_hint_y=None, height=dp(height),
                      padding=[dp(9), dp(8)])
        self.body.add_widget(f)
        return f

    def _spinner(self, values, default):
        vals = values or [default]
        s = Spinner(text=rtl_text(default), values=tuple(rtl_text(v) for v in vals),
                    font_name=font_name(), font_size="11sp", size_hint_y=None, height=dp(44))
        self.body.add_widget(s)
        return s

    def _parent_form(self):
        self.body.add_widget(self.label("ثبت درخواست ملاقات با دبیر، کادر، مشاور یا مدیریت", "14sp", PRIMARY, True, True, 40))
        self.student_spinner = self._spinner(["در حال دریافت دانش‌آموزان…"], "انتخاب دانش‌آموز")
        self.target_role = self._spinner(["دبیر", "کادر", "مشاور", "مدیریت"], "دبیر")
        self.target_spinner = self._spinner(["در حال دریافت افراد…"], "انتخاب فرد")
        self.target_role.bind(text=lambda *_: self._reload_targets())
        self.date = self._field("تاریخ ملاقات (مثلاً ۱۴۰۵/۰۷/۲۰)")
        self.time = self._field("ساعت ملاقات (مثلاً ۱۰:۳۰)")
        self.reason = self._field("علت ملاقات")
        self.description = self._field("توضیحات تکمیلی", True, 78)
        self.body.add_widget(self.button("ثبت درخواست ملاقات", self._create, SUCCESS))
        self._load_parent_students()

    def _teacher_form(self):
        self.body.add_widget(self.label("درخواست ملاقات با ولی دانش‌آموز", "14sp", PRIMARY, True, True, 40))
        self.student_spinner = self._spinner(["در حال دریافت دانش‌آموزان…"], "انتخاب دانش‌آموز")
        self.parent_spinner = self._spinner(["در حال دریافت اولیا…"], "انتخاب ولی")
        self.date = self._field("تاریخ ملاقات")
        self.time = self._field("ساعت ملاقات")
        self.reason = self._field("علت ملاقات")
        self.description = self._field("توضیحات تکمیلی", True, 78)
        self.body.add_widget(self.button("ثبت درخواست ملاقات با ولی", self._create, SUCCESS))
        self._load_teacher_students()

    def _staff_form(self):
        self.body.add_widget(self.label("درخواست ملاقات با ولی دانش‌آموز", "14sp", PRIMARY, True, True, 40))
        self.student_spinner = self._spinner(["در حال دریافت دانش‌آموزان…"], "انتخاب دانش‌آموز")
        self.parent_spinner = self._spinner(["در حال دریافت اولیا…"], "انتخاب ولی")
        self.date = self._field("تاریخ ملاقات")
        self.time = self._field("ساعت ملاقات")
        self.reason = self._field("علت ملاقات")
        self.description = self._field("توضیحات تکمیلی", True, 78)
        self.body.add_widget(self.button("ثبت درخواست ملاقات", self._create, SUCCESS))
        self._load_teacher_students()

    def _review_queue(self, stage):
        self.stage = stage
        self.body.add_widget(self.label(
            "درخواست‌های منتظر تأیید مدیر" if stage == "manager" else "درخواست‌های تأییدشده مدیر • آماده بررسی معاون آموزشی",
            "15sp", PRIMARY, True, True, 44
        ))
        self.queue = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.queue.bind(minimum_height=self.queue.setter("height"))
        self.body.add_widget(self.queue)
        self._load_queue()

    def _load_parent_students(self):
        def work():
            try:
                username = self._username()
                links = self.app_state.api.table_select("parent_children", {"parent_username": "eq." + username, "limit": "100"}) or []
                ids = [str(x.get("student_id")) for x in links if x.get("student_id") is not None]
                rows = self.app_state.api.table_select("students", {"limit": "200"}) or []
                selected = [r for r in rows if str(r.get("id")) in ids]
                Clock.schedule_once(lambda *_: self._set_students(selected), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _load_teacher_students(self):
        def work():
            try:
                rows = self.app_state.api.table_select("students", {"limit": "200"}) or []
                Clock.schedule_once(lambda *_: self._set_students(rows), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _set_students(self, rows):
        self.students = rows or []
        values = [self._student_label(r) for r in self.students]
        if not values:
            values = ["هیچ دانش‌آموزی پیدا نشد"]
        if hasattr(self, "student_spinner"):
            self.student_spinner.values = tuple(rtl_text(v) for v in values)
            self.student_spinner.text = rtl_text(values[0])

        if hasattr(self, "parent_spinner"):
            self._load_parents()

    def _load_parents(self):
        def work():
            try:
                links = self.app_state.api.table_select("parent_children", {"limit": "500"}) or []
                sid = self._selected_student_id()
                selected = [x for x in links if str(x.get("student_id")) == str(sid)]
                values = [str(x.get("parent_name") or x.get("parent_username") or "ولی ثبت‌شده") for x in selected]
                if not values:
                    values = ["ولی ثبت نشده است"]
                Clock.schedule_once(lambda *_: self._set_parents(values), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _set_parents(self, values):
        self.parent_spinner.values = tuple(rtl_text(v) for v in values)
        self.parent_spinner.text = rtl_text(values[0])

    def _reload_targets(self):
        role_text = str(self.target_role.text)
        target_role = {"دبیر": "teacher", "کادر": "staff", "مشاور": "advisor", "مدیریت": "manager"}.get(role_text, "teacher")
        def work():
            try:
                if target_role == "teacher":
                    rows = self.app_state.api.table_select("teachers", {"limit": "200"}) or []
                elif target_role == "staff":
                    rows = self.app_state.api.table_select("staff", {"limit": "200"}) or []
                else:
                    rows = self.app_state.api.table_select("users", {"limit": "200"}) or []
                values = []
                for r in rows:
                    name = r.get("display_name") or " ".join(x for x in [r.get("first_name"), r.get("last_name")] if x) or r.get("username")
                    if name: values.append(str(name))
                if not values:
                    values = ["فردی برای انتخاب پیدا نشد"]
                Clock.schedule_once(lambda *_: self._set_targets(values), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _set_targets(self, values):
        self.target_spinner.values = tuple(rtl_text(v) for v in values)
        self.target_spinner.text = rtl_text(values[0])

    def _selected_student_id(self):
        selected = str(getattr(self, "student_spinner", None).text or "")
        for r in self.students:
            if self._student_label(r) == selected:
                return r.get("id")
        return None

    def _selected_student_name(self):
        sid = self._selected_student_id()
        for r in self.students:
            if str(r.get("id")) == str(sid):
                return self._student_label(r)
        return ""

    @staticmethod
    def _student_label(row):
        return " ".join(x for x in [row.get("first_name"), row.get("last_name")] if x) or str(row.get("student_name") or row.get("id") or "")

    def _username(self):
        p = getattr(self.app_state, "profile", {}) or {}
        u = getattr(self.app_state, "user", {}) or {}
        return str(p.get("username") or p.get("email") or u.get("email") or "").strip()

    def _create(self, *_):
        role = self.role()
        student_id = self._selected_student_id()
        if role == "parent":
            target_role_text = str(self.target_role.text)
            target_role = {"دبیر": "teacher", "کادر": "staff", "مشاور": "advisor", "مدیریت": "manager"}.get(target_role_text, "teacher")
            target_name = str(self.target_spinner.text)
            parent_username = self._username()
            parent_name = getattr(self.app_state, "display_name", "") or parent_username
        else:
            target_role = "parent"
            target_name = str(getattr(self, "parent_spinner", None).text or "")
            parent_username = target_name
            parent_name = target_name
        date = str(self.date.text).strip()
        time = str(self.time.text).strip()
        reason = str(self.reason.text).strip()
        if not student_id or not date or not time or not reason or not target_name or "یافت نشد" in target_name:
            return self._error("دانش‌آموز، فرد ملاقات، تاریخ، ساعت و علت ملاقات الزامی است.")
        payload = {
            "p_requester_role": role,
            "p_requester_username": self._username(),
            "p_student_id": student_id,
            "p_student_name": self._selected_student_name(),
            "p_parent_username": parent_username,
            "p_parent_name": parent_name,
            "p_target_user_id": "",
            "p_target_role": target_role,
            "p_target_name": target_name,
            "p_requested_date_shamsi": date,
            "p_requested_time": time,
            "p_reason": reason,
            "p_description": str(self.description.text).strip(),
        }
        self.status.text = rtl_text("در حال ثبت درخواست در سرور…")
        def work():
            try:
                meeting_id = self.app_state.api.rpc("frahoosh_meeting_create", payload)
                Clock.schedule_once(lambda *_: self._created(meeting_id), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _created(self, meeting_id):
        self.status.text = rtl_text(f"درخواست ملاقات با شناسه {meeting_id} ثبت شد و در انتظار تأیید مدیر است.")
        self.status.color = SUCCESS
        self.show()

    def _load_queue(self):
        def work():
            try:
                rows = self.app_state.api.table_select("meeting_requests", {"limit": "200", "order": "created_at.desc"}) or []
                if self.stage == "manager":
                    rows = [r for r in rows if str(r.get("manager_status")) == "pending"]
                else:
                    rows = [r for r in rows if str(r.get("manager_status")) == "approved" and str(r.get("educational_status")) == "pending"]
                Clock.schedule_once(lambda *_: self._render_queue(rows), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _render_queue(self, rows):
        self.queue.clear_widgets()
        if not rows:
            self.queue.add_widget(self.label("درخواستی برای بررسی وجود ندارد.", "12sp", SECONDARY, False, True, 52))
            return
        for row in rows:
            box = BoxLayout(orientation="vertical", spacing=dp(3), padding=dp(7), size_hint_y=None, height=dp(150))
            box.add_widget(self.label(
                f"#{row.get('id')} • {row.get('student_name','')}\n"
                f"درخواست‌دهنده: {row.get('requester_role','')} • ملاقات با: {row.get('target_name','')}\n"
                f"تاریخ: {row.get('requested_date_shamsi','')} • ساعت: {row.get('requested_time','')}\n"
                f"علت: {row.get('reason','')}",
                "10sp", SECONDARY, False, True, 92
            ))
            actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
            if self.stage == "manager":
                actions.add_widget(self.button("تأیید و ارجاع به معاون آموزشی", lambda *_a, i=row.get("id"): self._review_manager(i, True), SUCCESS, 40))
                actions.add_widget(self.button("رد درخواست", lambda *_a, i=row.get("id"): self._review_manager(i, False), (0.72, .16, .18, 1), 40))
            else:
                actions.add_widget(self.button("تأیید نهایی", lambda *_a, i=row.get("id"): self._review_educational(i, True), SUCCESS, 40))
                actions.add_widget(self.button("رد", lambda *_a, i=row.get("id"): self._review_educational(i, False), (0.72, .16, .18, 1), 40))
            box.add_widget(actions)
            self.queue.add_widget(box)

    def _review_manager(self, meeting_id, approve):
        self._review("frahoosh_meeting_manager_review", {"p_meeting_id": meeting_id, "p_approve": approve, "p_note": ""})

    def _review_educational(self, meeting_id, approve):
        self._review("frahoosh_meeting_educational_review", {
            "p_meeting_id": meeting_id, "p_approve": approve,
            "p_final_date_shamsi": "", "p_final_time": "", "p_note": ""
        })

    def _review(self, fn, payload):
        def work():
            try:
                self.app_state.api.rpc(fn, payload)
                Clock.schedule_once(lambda *_: self.show(), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _load_rows(self):
        def work():
            try:
                rows = self.app_state.api.table_select("meeting_requests", {"limit": "100", "order": "created_at.desc"}) or []
                Clock.schedule_once(lambda *_: self._render_rows(rows), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _render_rows(self, rows):
        for row in rows[:30]:
            box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(112), padding=dp(7), spacing=dp(2))
            box.add_widget(self.label(
                f"#{row.get('id')} • {row.get('target_name','')} • {row.get('status','')}\n"
                f"تاریخ درخواست: {row.get('requested_date_shamsi','')} • ساعت: {row.get('requested_time','')}\n"
                f"وضعیت مدیر: {row.get('manager_status','')} • معاون آموزشی: {row.get('educational_status','')}",
                "9sp", SECONDARY, False, True, 88
            ))
            self.body.add_widget(box)

    def _error(self, message):
        self.status.text = rtl_text("خطا: " + str(message))
        self.status.color = (0.8, 0.15, 0.15, 1)

    def _back(self):
        if self.manager:
            self.manager.current = "dashboard"
