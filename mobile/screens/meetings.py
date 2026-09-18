from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text


def role_of(state):
    raw = str(getattr(state, "role", "student") or "student").strip().lower()
    return {
        "admin": "manager", "administrator": "manager", "مدیر": "manager", "مدیریت": "manager",
        "معاون آموزشی": "educational", "educational": "educational",
        "دبیر": "teacher", "teacher": "teacher",
        "کادر": "staff", "staff": "staff",
        "مشاور": "counselor", "مشاوره": "counselor", "counselor": "counselor",
        "ولی": "parent", "اولیا": "parent", "parent": "parent",
    }.get(raw, raw)


class MeetingsScreen(Screen):
    """Real school meeting workflow: request -> manager approval -> educational deputy."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.target_role = "teacher"
        self._build()

    def _label(self, text, size="12sp", color=SECONDARY, height=42, bold=False):
        w = Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color,
                  bold=bold, halign="right", valign="middle", size_hint_y=None, height=dp(height))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _button(self, text, cb, color=PRIMARY, height=44):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="11sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(height))
        b.bind(on_release=cb)
        return b

    def _field(self, hint, height=46):
        return TextInput(hint_text=rtl_text(hint), font_name=font_name(), font_size="12sp",
                         halign="right", multiline=False, size_hint_y=None, height=dp(height),
                         padding=[dp(10), dp(8)])

    def _username(self):
        p = self.app_state.profile if self.app_state else {}
        u = self.app_state.user if self.app_state else {}
        return str(p.get("username") or u.get("email") or "").strip()

    def _role(self):
        return role_of(self.app_state)

    def on_pre_enter(self, *args):
        self.show_home()

    def show_home(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        head = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(7))
        back = self._button("‹ بازگشت", self._back, SECONDARY, 46)
        head.add_widget(back)
        head.add_widget(self._label("ملاقات و درخواست جلسه", "20sp", PRIMARY, 46, True))
        root.add_widget(head)
        root.add_widget(self._label("درخواست‌ها واقعی در سرور ذخیره می‌شوند. تأیید مدیر انجام می‌شود و سپس درخواست برای معاون آموزشی ارجاع می‌گردد.", "10sp", SECONDARY, 58))

        role = self._role()
        if role == "parent":
            self._parent_form(root)
        elif role in {"teacher", "staff", "counselor"}:
            self._staff_form(root, role)
        elif role in {"manager", "educational"}:
            self._review(root, role)
        else:
            root.add_widget(self._label("این بخش برای نقش فعلی فعال نشده است.", height=60))
        self.add_widget(root)

    def _scroll(self, widget):
        s = ScrollView(do_scroll_x=False)
        s.add_widget(widget)
        return s

    def _parent_form(self, root):
        root.add_widget(self._label("ثبت درخواست از طرف ولی", "15sp", PRIMARY, 36, True))
        form = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        student = self._field("انتخاب دانش‌آموز")
        target_name = self._field("نام دبیر / کادر / مشاور")
        date = self._field("تاریخ ملاقات")
        time = self._field("ساعت ملاقات")
        reason = self._field("علت ملاقات")
        desc = self._field("توضیحات تکمیلی", 72)
        desc.multiline = True
        for w in [student, target_name, date, time, reason, desc]:
            form.add_widget(w)
        chooser = GridLayout(cols=4, spacing=dp(5), size_hint_y=None, height=dp(46))
        for label, key in [("دبیر","teacher"),("کادر","staff"),("مشاور","counselor"),("مدیریت","manager")]:
            chooser.add_widget(self._button(label, lambda *_a, k=key, b=None: self._set_target(k), PRIMARY, 44))
        form.add_widget(chooser)
        submit = self._button("ثبت درخواست ملاقات", lambda *_: self._create(
            student.text, target_name.text, date.text, time.text, reason.text, desc.text, "parent",
            parent_username=self._username(), student_id=None), SUCCESS, 48)
        form.add_widget(submit)
        root.add_widget(self._scroll(form))
        self._load_people_for_parent(student)

    def _load_people_for_parent(self, student_field):
        # The visible field remains touch-friendly; target lists are loaded from the
        # same server tables so a later web client can use the identical identifiers.
        try:
            rows = self.app_state.api.table_select("students", {"order":"id.asc", "limit":"100"})
            names = [str(r.get("first_name",""))+" "+str(r.get("last_name","")) for r in rows]
            student_field.hint_text = rtl_text("انتخاب دانش‌آموز: " + (" / ".join(names[:5]) if names else "پرونده فرزند"))
        except Exception:
            pass

    def _staff_form(self, root, role):
        root.add_widget(self._label("ثبت درخواست ملاقات با ولی", "15sp", PRIMARY, 36, True))
        form = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        student = self._field("نام دانش‌آموز")
        parent = self._field("نام اولیا")
        date = self._field("تاریخ ملاقات")
        time = self._field("ساعت ملاقات")
        reason = self._field("علت ملاقات")
        desc = self._field("توضیحات تکمیلی", 72); desc.multiline = True
        for w in [student, parent, date, time, reason, desc]: form.add_widget(w)
        form.add_widget(self._button("ثبت درخواست ملاقات با اولیا", lambda *_: self._create(
            student.text, parent.text, date.text, time.text, reason.text, desc.text, role,
            parent_name=parent.text.strip()), SUCCESS, 48))
        root.add_widget(self._scroll(form))

    def _set_target(self, role):
        self.target_role = role
        self.status_text = getattr(self, "status_text", None)
        if self.status_text:
            self.status_text.text = rtl_text("مخاطب ملاقات: " + role)

    def _create(self, student_name, target_name, date, time, reason, description, requester_role, **extra):
        if not all(str(x or "").strip() for x in [student_name, target_name, date, time, reason]):
            return self._message("همه فیلدهای اصلی ملاقات را تکمیل کنید.", ERROR)
        payload = {
            "requester_username": self._username(),
            "requester_role": requester_role,
            "requester_name": getattr(self.app_state, "display_name", "کاربر"),
            "student_name": student_name.strip(),
            "target_role": self.target_role if requester_role == "parent" else "parent",
            "target_name": target_name.strip(),
            "requested_date": date.strip(),
            "requested_time": time.strip(),
            "reason": reason.strip(),
            "description": description.strip(),
            "status": "pending_manager",
            "manager_status": "pending",
            "educational_status": "pending",
        }
        payload.update(extra)
        try:
            self.app_state.api.table_insert("meeting_requests", payload)
            self._message("درخواست با موفقیت به مدیر ارسال شد.", SUCCESS)
            self.show_home()
        except Exception as exc:
            self._message("ثبت درخواست انجام نشد: " + str(exc), ERROR)

    def _review(self, root, role):
        title = "تأیید و ارجاع درخواست‌های ملاقات" if role == "manager" else "ملاقات‌های ارجاع‌شده برای معاون آموزشی"
        root.add_widget(self._label(title, "15sp", PRIMARY, 36, True))
        try:
            filters = {"order":"id.desc","limit":"100"}
            if role == "educational":
                filters["status"] = "eq.manager_approved"
            rows = self.app_state.api.table_select("meeting_requests", filters)
        except Exception as exc:
            root.add_widget(self._label("خواندن درخواست‌ها انجام نشد: " + str(exc), color=ERROR, height=60))
            return
        if not rows:
            root.add_widget(self._label("درخواستی برای نمایش وجود ندارد.", height=60))
            return
        scroll_box = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None)
        scroll_box.bind(minimum_height=scroll_box.setter("height"))
        for row in rows:
            card = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(4), size_hint_y=None, height=dp(166))
            card.add_widget(self._label(
                f"#{row.get('id')} | {row.get('requester_name') or row.get('requester_username')} → {row.get('target_name') or 'مخاطب'}\n"
                f"دانش‌آموز: {row.get('student_name') or '-'} | تاریخ: {row.get('requested_date')} | ساعت: {row.get('requested_time')}\n"
                f"علت: {row.get('reason')}\nوضعیت: {row.get('status')}", "10sp", SECONDARY, 92, True))
            actions = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
            if role == "manager" and row.get("status") == "pending_manager":
                actions.add_widget(self._button("تأیید مدیر و ارجاع", lambda *_a, rid=row["id"]: self._manager_approve(rid), SUCCESS, 44))
                actions.add_widget(self._button("رد درخواست", lambda *_a, rid=row["id"]: self._reject(rid), ERROR, 44))
            elif role == "educational" and row.get("status") == "manager_approved":
                actions.add_widget(self._button("تأیید نهایی / تعیین وقت", lambda *_a, rid=row["id"], d=row.get("requested_date"), t=row.get("requested_time"): self._educational_approve(rid,d,t), SUCCESS, 44))
            card.add_widget(actions); scroll_box.add_widget(card)
        root.add_widget(self._scroll(scroll_box))

    def _manager_approve(self, rid):
        try:
            self.app_state.api.table_update("meeting_requests", {"id": f"eq.{rid}"}, {
                "manager_status":"approved", "manager_approved_at":"now()", "status":"manager_approved"
            })
            self._message("درخواست تأیید و برای معاون آموزشی ارجاع شد.", SUCCESS)
            self.show_home()
        except Exception as exc: self._message(str(exc), ERROR)

    def _educational_approve(self, rid, date, time):
        try:
            self.app_state.api.table_update("meeting_requests", {"id": f"eq.{rid}"}, {
                "educational_status":"approved", "final_date":date, "final_time":time,
                "status":"confirmed"
            })
            self._message("ملاقات نهایی شد و برای طرفین قابل پیگیری است.", SUCCESS)
            self.show_home()
        except Exception as exc: self._message(str(exc), ERROR)

    def _reject(self, rid):
        try:
            self.app_state.api.table_update("meeting_requests", {"id": f"eq.{rid}"}, {"manager_status":"rejected","status":"rejected"})
            self._message("درخواست رد شد.", ERROR); self.show_home()
        except Exception as exc: self._message(str(exc), ERROR)

    def _message(self, text, color):
        # Keep feedback in a small modal-free banner to avoid Android popup crashes.
        try:
            self.clear_widgets()
            root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
            root.add_widget(self._label(text, "15sp", color, 90, True))
            root.add_widget(self._button("بازگشت", self.show_home, PRIMARY, 48))
            self.add_widget(root)
        except Exception:
            pass

    def _back(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
