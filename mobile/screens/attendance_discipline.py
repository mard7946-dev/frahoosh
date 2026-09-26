from datetime import datetime
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, fa_display, PersianTextInput


def role_of(state):
    profile = getattr(state, "profile", {}) or {}
    active = str(getattr(state, "panel_role", "") or "").strip().lower()
    aliases = {
        "management": "manager", "مدیریت": "manager", "مدیر": "manager",
        "معاون آموزشی": "educational", "معاون اجرایی": "executive",
        "معاون پرورشی": "cultural", "مشاور": "advisor", "مشاوره": "advisor",
        "دبیران": "teacher", "دبیر": "teacher", "معلم": "teacher",
        "دانش‌آموز": "student", "اولیا": "parent",
    }
    if active:
        return aliases.get(active, active)
    raw = str(profile.get("role") or getattr(state, "role", "") or "student").strip().lower()
    return aliases.get(raw, raw)


class AttendanceDisciplineScreen(Screen):
    """Real class attendance and discipline workflow shared by teacher, deputies,
    manager and counselor. Writes use the existing canonical attendance and
    discipline tables so parents can read approved results from their child view.
    """

    def __init__(self, app_state=None, mode="attendance", **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.mode = mode
        self.class_rows = []
        self.students = []
        self.class_name = ""
        self.teacher_id = None
        self._build()

    def _label(self, text, size="12sp", color=SECONDARY, height=42, bold=False, center=False):
        w = Label(text=fa_display(text), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="center" if center else "right",
                  valign="middle", size_hint_y=None, height=dp(height))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _button(self, text, cb, color=PRIMARY, height=42):
        b = Button(text=fa_display(text), font_name=font_name(), font_size="10sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(height))
        b.bind(on_release=cb)
        return b

    def _spinner(self, text, values, height=46):
        return Spinner(text=fa_display(text),
                       values=tuple(fa_display(x) for x in values),
                       font_name=font_name(), font_size="11sp",
                       size_hint_y=None, height=dp(height))

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None:
            raise RuntimeError("سرویس اتصال به پایگاه داده آماده نیست.")
        return api

    def on_pre_enter(self, *_):
        self.show_home()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        head.add_widget(self._button("بازگشت", self._back, SECONDARY, 44))
        self.title = self._label("حضور و غیاب کلاس", "18sp", PRIMARY, 44, True, True)
        head.add_widget(self.title)
        root.add_widget(head)
        self.status = self._label("", "9sp", SECONDARY, 34, True, True)
        root.add_widget(self.status)
        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(3),
                              size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def _clear(self):
        self.body.clear_widgets()

    def _set_status(self, text, color=SUCCESS):
        self.status.text = fa_display(text)
        self.status.color = color

    def show_home(self):
        self._clear()
        role = role_of(self.app_state)
        self.title.text = fa_display("حضور و غیاب کلاس" if self.mode == "attendance" else "ثبت و پیگیری انضباط")
        allowed = {"teacher", "manager", "educational", "executive", "cultural", "advisor"}
        if role not in allowed:
            self._set_status("این بخش برای نقش فعلی فعال نیست.", ERROR)
            return
        self._load_classes(role)

    def _load_classes(self, role):
        self._clear()
        self._label("انتخاب کلاس", "16sp", PRIMARY, 42, True, True)
        try:
            api = self._api()
            if role == "teacher":
                p = getattr(self.app_state, "profile", {}) or {}
                self.teacher_id = p.get("linked_teacher_id") or p.get("teacher_id")
                params = {"limit": "200"}
                if self.teacher_id:
                    params["teacher_id"] = "eq." + str(self.teacher_id)
                rows = api.table_select("teacher_classes", params) or []
            else:
                rows = api.table_select("teacher_classes", {"limit": "500"}) or []
            students = api.table_select("students", {"limit": "1000"}) or []
        except Exception as exc:
            self._set_status("فهرست کلاس‌ها دریافت نشد: " + str(exc), ERROR)
            return

        classes = []
        for r in rows:
            name = str(r.get("class_name") or r.get("name") or "").strip()
            if name and name not in classes:
                classes.append(name)
        for r in students:
            name = str(r.get("class_name") or "").strip()
            if name and name not in classes:
                classes.append(name)
        classes.sort()
        self.class_rows = rows
        if not classes:
            self._label("کلاسی برای نمایش پیدا نشد.", height=55, center=True)
            return
        self.class_spinner = self._spinner("کلاس را انتخاب کنید", classes)
        self.body.add_widget(self.class_spinner)
        self.class_spinner.bind(text=lambda *_: self._open_class(self.class_spinner.text))
        self._open_class(classes[0])

    def _open_class(self, class_name):
        logical = str(class_name or "").replace("ي", "ی").replace("ك", "ک").strip()
        if not logical or logical == "کلاس را انتخاب کنید":
            return
        self.class_name = logical
        self._clear()
        self._label(("حضور و غیاب " if self.mode == "attendance" else "انضباط ") + logical,
                    "17sp", PRIMARY, 44, True, True)
        self.class_spinner = self._spinner(logical, [str(r.get("class_name") or r.get("name") or "").strip()
                                                      for r in self.class_rows
                                                      if str(r.get("class_name") or r.get("name") or "").strip()])
        if not self.class_spinner.values:
            self.class_spinner = self._spinner(logical, [logical])
        self.body.add_widget(self.class_spinner)
        self.class_spinner.bind(text=lambda *_: self._reload_selected_class(self.class_spinner.text))
        self._load_students(logical)

    def _reload_selected_class(self, value):
        if str(value).strip() and str(value).strip() != self.class_name:
            self.class_name = str(value).strip()
            self._load_students(self.class_name)

    def _load_students(self, class_name):
        try:
            rows = self._api().table_select("students", {
                "class_name": "eq." + class_name, "order": "last_name.asc", "limit": "500"
            }) or []
        except Exception as exc:
            self._set_status("فهرست دانش‌آموزان دریافت نشد: " + str(exc), ERROR)
            return
        self.students = rows
        if not rows:
            self._label("دانش‌آموزی برای این کلاس ثبت نشده است.", height=55, center=True)
            return
        self._label("فهرست دانش‌آموزان کلاس", "14sp", PRIMARY, 38, True, True)
        for student in rows:
            self._student_row(student)

        if self.mode == "discipline" and role_of(self.app_state) == "educational":
            self._label("موارد در انتظار تأیید معاون آموزشی", "14sp", PRIMARY, 42, True, True)
            self._load_pending()

    def _student_name(self, row):
        return (str(row.get("first_name") or "") + " " + str(row.get("last_name") or "")).strip() or str(row.get("display_name") or row.get("id") or "دانش‌آموز")

    def _student_row(self, student):
        sid = student.get("id")
        name = self._student_name(student)
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(82), spacing=dp(4))
        box.add_widget(self._label(name, "13sp", PRIMARY, 34, True, True))
        actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        if self.mode == "attendance":
            actions.add_widget(self._button("حاضر", lambda *_a, s=sid: self._save_attendance(s, "present"), SUCCESS, 38))
            actions.add_widget(self._button("غایب", lambda *_a, s=sid: self._save_attendance(s, "absent"), ERROR, 38))
        else:
            spinner = self._spinner("انتخاب مورد انضباطی", [
                "تأخیر", "غیبت غیرموجه", "بی‌نظمی", "تخلف آموزشی", "تخلف رفتاری", "سایر"
            ], 38)
            actions.add_widget(spinner)
            actions.add_widget(self._button("ثبت مورد", lambda *_a, s=sid, w=spinner: self._save_discipline(s, w), PRIMARY, 38))
        box.add_widget(actions)
        self.body.add_widget(box)

    def _save_attendance(self, student_id, status):
        try:
            api = self._api()
            today = datetime.now().strftime("%Y-%m-%d")
            p = getattr(self.app_state, "profile", {}) or {}
            teacher_id = p.get("linked_teacher_id") or p.get("teacher_id")
            subject = ""
            for row in self.class_rows:
                if str(row.get("class_name") or row.get("name") or "").strip() == self.class_name:
                    subject = str(row.get("subject") or "")
                    if not teacher_id:
                        teacher_id = row.get("teacher_id")
                    break
            filters = {
                "student_id": "eq." + str(student_id),
                "class_name": "eq." + self.class_name,
                "attendance_date": "eq." + today,
            }
            existing = api.table_select("attendance", {**filters, "limit": "1"}) or []
            payload = {"student_id": student_id, "teacher_id": teacher_id,
                       "class_name": self.class_name, "subject": subject,
                       "attendance_date": today, "status": status}
            if existing and existing[0].get("id"):
                api.table_update("attendance", {"id": "eq." + str(existing[0]["id"])}, payload,
                                 return_representation=False)
            else:
                api.table_insert("attendance", payload, return_representation=False)
            self._set_status("حضور و غیاب «" + self._student_name(next((x for x in self.students if x.get("id") == student_id), {})) + "» بلافاصله ثبت شد.", SUCCESS)
        except Exception as exc:
            self._set_status("ثبت حضور و غیاب انجام نشد: " + str(exc), ERROR)

    def _save_discipline(self, student_id, spinner):
        item = str(spinner.text or "").strip()
        if not item or item == "انتخاب مورد انضباطی":
            self._set_status("ابتدا مورد انضباطی را انتخاب کنید.", ERROR)
            return
        try:
            p = getattr(self.app_state, "profile", {}) or {}
            username = str(p.get("username") or p.get("email") or "").strip()
            role = role_of(self.app_state)
            payload = {
                "student_id": student_id, "teacher_id": p.get("linked_teacher_id") or p.get("teacher_id"),
                "title": item, "description": item, "priority": "عادی",
                "status": "pending", "item_id": item, "actor_username": username,
                "actor_role": role, "note": "در انتظار تأیید معاون آموزشی"
            }
            self._api().table_insert("discipline_records", payload, return_representation=False)
            self._set_status("مورد انضباطی ثبت شد و برای تأیید معاون آموزشی ارسال شد.", SUCCESS)
        except Exception as exc:
            self._set_status("ثبت مورد انضباطی انجام نشد: " + str(exc), ERROR)

    def _load_pending(self):
        try:
            rows = self._api().table_select("discipline_records", {
                "class_name": "eq." + self.class_name, "status": "eq.pending", "limit": "200"
            }) or []
        except Exception:
            rows = []
        for row in rows:
            self._label("دانش‌آموز: " + str(row.get("student_id")) + " • " + str(row.get("title") or "مورد انضباطی"),
                        height=42)
            self._button("تأیید و ارسال به ولی", lambda *_a, r=dict(row): self._approve_discipline(r), SUCCESS, 40)

    def _approve_discipline(self, row):
        if role_of(self.app_state) != "educational":
            return self._set_status("فقط معاون آموزشی می‌تواند مورد انضباطی را تأیید کند.", ERROR)
        try:
            api = self._api()
            rid = row.get("id")
            api.table_update("discipline_records", {"id": "eq." + str(rid)},
                             {"status": "approved", "note": "تأیید معاون آموزشی"},
                             return_representation=False)
            # Best-effort direct parent notification. The approved discipline record
            # remains the source of truth even if a legacy messages policy rejects it.
            try:
                links = api.table_select("parent_children", {"student_id": "eq." + str(row.get("student_id")), "limit": "20"}) or []
                for link in links:
                    parent = str(link.get("parent_username") or "").strip()
                    if parent:
                        api.table_insert("messages", {
                            "sender": str((getattr(self.app_state, "profile", {}) or {}).get("username") or "معاون آموزشی"),
                            "receiver": parent,
                            "text": "مورد انضباطی دانش‌آموز پس از تأیید معاون آموزشی ثبت شد.",
                            "sender_name": "معاون آموزشی",
                            "title": "اعلان انضباطی",
                            "body": "مورد انضباطی ثبت‌شده برای دانش‌آموز شما پس از تأیید معاون آموزشی در سامانه قرار گرفت.",
                            "audience_type": "direct", "audience_value": parent,
                        }, return_representation=False)
            except Exception as notify_exc:
                print("DISCIPLINE PARENT NOTIFY ERROR:", repr(notify_exc))
            self._set_status("مورد انضباطی تأیید شد و برای ولی ارسال شد.", SUCCESS)
            self._load_students(self.class_name)
        except Exception as exc:
            self._set_status("تأیید مورد انضباطی انجام نشد: " + str(exc), ERROR)

    def _back(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
