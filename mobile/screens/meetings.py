from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text, fa_display, PersianTextInput


def _is_legacy_management_account(state, profile):
    """Compatibility bridge for the existing production manager account.
    Its database row was historically stored with role=student and must not
    hide management-only workflows until the server-side role is corrected.
    """
    username = str((profile or {}).get("username") or "").strip().lower()
    email = str((profile or {}).get("email") or "").strip().lower()
    local = email.split("@", 1)[0] if "@" in email else ""
    return username in {"student", "student1"} or local in {"student", "student1"}

def role_of(state):
    profile = getattr(state, "profile", {}) or {}
    if _is_legacy_management_account(state, profile):
        return "manager"
    active_panel=str(getattr(state,"panel_role","") or "").strip().lower()
    aliases={"management":"manager","teachers":"teacher","teacher_panel":"teacher","teacher_dashboard":"teacher","دبیران":"teacher","کادر و دبیران":"teacher"}
    if active_panel:
        return aliases.get(active_panel,active_panel)
    profile = getattr(state, "profile", {}) or {}
    if _is_legacy_management_account(state, profile):
        return "manager"
    candidates = [
        profile.get("role"),
        profile.get("user_role"),
        profile.get("school_role"),
        getattr(state, "role", None),
        profile.get("user_role"),
        profile.get("school_role"),
        profile.get("user_type"),
        profile.get("account_type"),
    ]
    raw = next((str(v).strip().lower() for v in candidates if str(v or "").strip()), "student")
    return {
        "admin":"manager","administrator":"manager","principal":"manager","manager":"manager","management":"manager","school_management":"manager",
        "مدیر":"manager","مدیریت":"manager",
        "معاون آموزشی":"educational","educational":"educational","educational_deputy":"educational",
        "معاون اجرایی":"executive","اجرایی":"executive","executive":"executive","executive_deputy":"executive",
        "معاون پرورشی":"cultural","پرورشی":"cultural","cultural":"cultural","cultural_deputy":"cultural",
        "مشاور":"counselor","مشاوره":"counselor","counselor":"counselor","counseling":"counselor",
        "دبیر":"teacher","teacher":"teacher","کادر":"staff","staff":"staff",
        "ولی":"parent","اولیا":"parent","parent":"parent",
        "دانش‌آموز":"student","دانش آموز":"student","student":"student",
    }.get(raw, raw)


class MeetingsScreen(Screen):
    """Real meeting workflow: request -> manager approval -> educational deputy -> confirmation."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.target_role = "teacher"
        self._student_rows = []
        self._target_rows = []
        self._parent_rows = []
        self._build()

    def _label(self, text, size="12sp", color=SECONDARY, height=42, bold=False, center=False):
        w = Label(text=fa_display(text), font_name=font_name(), font_size=size, color=color,
                  bold=bold, halign="center" if center else "right", valign="middle",
                  size_hint_y=None, height=dp(height))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _button(self, text, cb, color=PRIMARY, height=44):
        b = Button(text=fa_display(text), font_name=font_name(), font_size="11sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(height))
        b.bind(on_press=cb)
        return b

    def _field(self, hint, height=46):
        return PersianTextInput(hint_text=fa_display(hint), font_name=font_name(), font_size="12sp",
                         halign="right", multiline=False, size_hint_y=None, height=dp(height),
                         padding=[dp(10), dp(8)])

    def _username(self):
        p = self.app_state.profile if self.app_state else {}
        u = self.app_state.user if self.app_state else {}
        # All school messaging uses public.users.username, not the Supabase Auth email.
        return str(p.get("username") or u.get("username") or p.get("email") or u.get("email") or "").strip()

    def _role(self):
        return role_of(self.app_state)

    def _spinner(self, text, values, height=48):
        s = Spinner(
            text=fa_display(text),
            values=[fa_display(v) for v in values],
            font_name=font_name(), font_size="12sp",
            size_hint_y=None, height=dp(height),
            background_normal="", background_color=(0.05, 0.18, 0.34, 1),
            color=WHITE,
        )
        return s

    def on_pre_enter(self, *args):
        self.show_home()

    def show_home(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        head = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(7))
        head.add_widget(self._button("‹ بازگشت", self._back, SECONDARY, 46))
        head.add_widget(self._label("ملاقات و درخواست جلسه", "20sp", PRIMARY, 46, True, True))
        root.add_widget(head)
        root.add_widget(self._label(
            "درخواست در سرور ثبت می‌شود؛ ابتدا مدیر بررسی می‌کند، سپس برای معاون آموزشی ارجاع می‌شود و نتیجه برای طرف‌های مجاز قابل پیگیری است.",
            "10sp", SECONDARY, 58, True, True))

        role = self._role()
        if role == "parent":
            self._parent_form(root)
        elif role in {"teacher", "staff", "counselor"}:
            self._staff_form(root, role)
        elif role in {"manager", "educational"}:
            self._review(root, role)
        else:
            root.add_widget(self._label("این بخش برای نقش فعلی فعال نشده است.", height=60, center=True))
        self.add_widget(root)

    def _scroll(self, widget):
        s = ScrollView(do_scroll_x=False)
        s.add_widget(widget)
        return s

    def _load_parent_children(self):
        api = getattr(self.app_state, "api", None)
        if api is None:
            return []
        username = self._username()
        try:
            links = api.table_select("parent_children", {"parent_username": f"eq.{username}", "limit": "100"})
            rows = []
            for link in links or []:
                sid = link.get("student_id")
                if sid is None:
                    continue
                try:
                    students = api.table_select("students", {"id": f"eq.{sid}", "limit": "1"})
                    if students:
                        rows.append(students[0])
                except Exception:
                    pass
            # Never fall back to the whole student table: a parent must only
            # see children explicitly linked to the authenticated account.
            self._student_rows = rows
            return rows
        except Exception as exc:
            print("PARENT CHILDREN LOAD ERROR:", repr(exc))
            return []

    def _load_targets(self, role):
        api = getattr(self.app_state, "api", None)
        if api is None:
            return []
        try:
            role_map = {
                "teacher": {"teacher","teachers"},
                "staff": {"staff"},
                "counselor": {"counselor","advisor","مشاور"},
                "manager": {"manager","admin","administrator","management"},
            }
            allowed = role_map.get(role, {role})
            rows = api.table_select("users", {"limit":"500"}) or []
            result=[]
            for row in rows:
                r=str(row.get("role") or "").strip().lower()
                if r not in {str(x).lower() for x in allowed}: continue
                if not row.get("username"): continue
                result.append({
                    "username":row.get("username"),
                    "display_name":row.get("display_name") or row.get("username"),
                    "first_name":row.get("display_name") or "",
                    "last_name":"",
                    "role":row.get("role"),
                    "id":row.get("id"),
                })
            self._target_rows=result
            return result
        except Exception as exc:
            print("MEETING TARGET LOAD ERROR:", repr(exc))
            return []

    def _parent_form(self, root):
        root.add_widget(self._label("ثبت درخواست ملاقات از طرف ولی", "15sp", PRIMARY, 36, True, True))
        form = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        children = self._load_parent_children()
        child_names = [
            f"{r.get('first_name','')} {r.get('last_name','')}".strip() + (f" • {r.get('class_name')}" if r.get("class_name") else "")
            for r in children
        ]
        if not child_names:
            child_names = ["فرزند متصل به حساب پیدا نشد"]
        student = self._spinner("انتخاب دانش‌آموز", child_names)

        self.target_role = "teacher"
        target_type = self._spinner("نوع فرد مورد ملاقات", ["دبیر", "کادر", "مشاور", "مدیریت"])
        target_map = {"دبیر": "teacher", "کادر": "staff", "مشاور": "counselor", "مدیریت": "manager"}
        target_map_visual = {fa_display(k): v for k, v in target_map.items()}
        target_name = self._spinner("نام فرد مورد ملاقات", ["ابتدا نوع فرد را انتخاب کنید"])

        def refresh_targets(spinner, value):
            logical_value = str(value).replace("ي", "ی").replace("ك", "ک")
            role = target_map.get(logical_value) or target_map_visual.get(str(value)) or "teacher"
            self.target_role = role
            rows = self._load_targets(role)
            names = [self._person_name(r) for r in rows if self._person_name(r)]
            target_name.values = [fa_display(n) for n in (names or ["فردی برای این نقش پیدا نشد"])]
            target_name.text = target_name.values[0]
        target_type.bind(text=refresh_targets)
        target_type.text = fa_display("دبیر")
        refresh_targets(target_type, "دبیر")

        day = self._spinner("روز هفته", ["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه"])
        title = self._field("عنوان ملاقات")
        date = self._field("تاریخ ملاقات")
        time = self._field("ساعت ملاقات")
        reason = self._field("علت ملاقات")
        desc = self._field("توضیحات تکمیلی", 72)
        desc.multiline = True
        for w in [student, target_type, target_name, title, day, date, time, reason, desc]:
            form.add_widget(w)

        submit = self._button("ثبت درخواست ملاقات", lambda *_: self._create_parent(
            student, target_name, title, day, date, time, reason, desc), SUCCESS, 48)
        form.add_widget(submit)
        root.add_widget(self._scroll(form))
        self._my_requests(root)

    def _my_requests(self, root):
        api=getattr(self.app_state,"api",None)
        if api is None:return
        try:
            rows=api.table_select("meeting_requests",{"requester_username":"eq."+self._username(),"order":"id.desc","limit":"50"}) or []
        except Exception as exc:
            root.add_widget(self._label("خواندن درخواست‌های قبلی انجام نشد: "+str(exc),color=ERROR,height=50)); return
        root.add_widget(self._label("درخواست‌های ثبت‌شده من","15sp",PRIMARY,38,True,True))
        if not rows:
            root.add_widget(self._label("هنوز درخواست ملاقاتی ثبت نشده است.",height=45,center=True)); return
        for row in rows:
            box=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(145),spacing=dp(3))
            summary="#"+str(row.get("id"))+" | "+str(row.get("title") or "ملاقات")+" | "+str(row.get("target_name") or "-")+"\n"+str(row.get("requested_day") or "-")+" | "+str(row.get("requested_date") or "-")+" | "+str(row.get("requested_time") or "-")+"\nموضوع: "+str(row.get("reason") or "-")+" | وضعیت: "+self._status_text(row.get("status"))
            box.add_widget(self._label(summary,"10sp",SECONDARY,82,True))
            actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5))
            if row.get("status") in {"pending_manager","manager_approved"}:
                actions.add_widget(self._button("ویرایش",lambda *_a,r=dict(row):self._edit_request(r),PRIMARY,40))
            if row.get("status") in {"pending_manager","rejected"}:
                actions.add_widget(self._button("حذف",lambda *_a,r=dict(row):self._delete_request(r),ERROR,40))
            box.add_widget(actions); root.add_widget(box)

    def _edit_request(self,row):
        self.clear_widgets()
        root=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(7))
        root.add_widget(self._label("ویرایش درخواست ملاقات","20sp",PRIMARY,48,True,True))
        form=BoxLayout(orientation="vertical",spacing=dp(6),size_hint_y=None); form.bind(minimum_height=form.setter("height"))
        title=self._field("عنوان ملاقات"); title.text=str(row.get("title") or "")
        day=self._spinner("روز هفته",["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه"]); day.text=fa_display(str(row.get("requested_day") or "شنبه"))
        date=self._field("تاریخ ملاقات"); date.text=str(row.get("requested_date") or "")
        time=self._field("ساعت ملاقات"); time.text=str(row.get("requested_time") or "")
        reason=self._field("علت ملاقات"); reason.text=str(row.get("reason") or "")
        desc=self._field("توضیحات تکمیلی",72); desc.multiline=True; desc.text=str(row.get("description") or "")
        for w in [title,day,date,time,reason,desc]: form.add_widget(w)
        form.add_widget(self._button("ذخیره ویرایش",lambda *_:self._save_edit(row.get("id"),title,day,date,time,reason,desc),SUCCESS,48))
        form.add_widget(self._button("حذف درخواست",lambda *_:self._delete_request(row),ERROR,44))
        form.add_widget(self._button("بازگشت",self.show_home,SECONDARY,44))
        root.add_widget(self._scroll(form)); self.add_widget(root)

    def _save_edit(self,rid,title,day,date,time,reason,desc):
        if not all(str(x.text or "").strip() for x in [title,date,time,reason]):
            return self._message("عنوان، تاریخ، ساعت و موضوع الزامی است.",ERROR)
        try:
            self.app_state.api.table_update("meeting_requests",{"id":"eq."+str(rid),"requester_username":"eq."+self._username()},{"title":title.text.strip(),"requested_day":str(day.text).strip(),"requested_date":date.text.strip(),"requested_time":time.text.strip(),"reason":reason.text.strip(),"description":desc.text.strip(),"status":"pending_manager","manager_status":"pending"})
            self._message("درخواست ویرایش و دوباره برای بررسی مدیر ارسال شد.",SUCCESS)
        except Exception as exc:self._message("ویرایش انجام نشد: "+str(exc),ERROR)

    def _delete_request(self,row):
        try:
            self.app_state.api.table_delete("meeting_requests",{"id":"eq."+str(row.get("id")),"requester_username":"eq."+self._username()})
            self._message("درخواست ملاقات حذف شد.",SUCCESS)
        except Exception as exc:self._message("حذف انجام نشد: "+str(exc),ERROR)

    def _person_name(self, row):
        display = row.get("display_name") or row.get("full_name")
        if display:
            return str(display).strip()
        name = f"{row.get('first_name','')} {row.get('last_name','')}".strip()
        if name:
            return name
        return str(row.get("username") or row.get("email") or "").strip()

    def _selected_student(self, spinner):
        text = str(spinner.text or "").strip()
        for row in self._student_rows:
            label = self._person_name(row)
            if row.get("class_name"):
                label += f" • {row.get('class_name')}"
            if text == label or text == fa_display(label):
                return row
        return self._student_rows[0] if self._student_rows else None

    def _selected_target(self, spinner):
        text = str(spinner.text or "").strip()
        for row in self._target_rows:
            if text == self._person_name(row) or text == fa_display(self._person_name(row)):
                return row
        return self._target_rows[0] if self._target_rows else None

    def _create_parent(self, student, target, title, day, date, time, reason, desc):
        srow = self._selected_student(student)
        trow = self._selected_target(target)
        if not srow or not trow:
            return self._message("دانش‌آموز و فرد مورد ملاقات را از فهرست انتخاب کنید.", ERROR)
        teacher_id=None
        if self.target_role in {"teacher","teachers"} and trow.get("username"):
            try:
                trs=self.app_state.api.table_select("teachers",{"email":f"eq.{trow.get('username')}","select":"id","limit":"1"}) or []
                teacher_id=trs[0].get("id") if trs else None
            except Exception:
                teacher_id=None
        self._create(
            student_name=self._person_name(srow),
            target_name=self._person_name(trow),
            title=title.text, day=day.text, date=date.text, time=time.text,
            reason=reason.text, description=desc.text, requester_role="parent",
            student_id=srow.get("id"), target_username=trow.get("username"),
            teacher_id=teacher_id,
        )

    def _load_parents_for_student(self, student_id):
        api = getattr(self.app_state, "api", None)
        if api is None or student_id is None:
            return []
        try:
            links = api.table_select("parent_children", {"student_id":f"eq.{student_id}","limit":"100"}) or []
            result=[]
            for link in links:
                username=str(link.get("parent_username") or "").strip()
                if not username: continue
                users=api.table_select("users", {"username":f"eq.{username}","limit":"1"}) or []
                u=users[0] if users else {}
                result.append({
                    "username":username,
                    "display_name":u.get("display_name") or username,
                    "role":"parent",
                    "student_id":student_id,
                })
            self._parent_rows=result
            return result
        except Exception as exc:
            print("MEETING PARENT LOAD ERROR:", repr(exc))
            return []

    def _staff_form(self, root, role):
        root.add_widget(self._label("ثبت درخواست ملاقات با اولیا", "15sp", PRIMARY, 36, True, True))
        form = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        students = []
        try:
            students = self.app_state.api.table_select("students", {"order": "id.asc", "limit": "100"}) or []
        except Exception:
            pass
        self._student_rows = students
        student_labels = [self._person_name(r) + (f" • {r.get('class_name')}" if r.get("class_name") else "") for r in students]
        student = self._spinner("انتخاب دانش‌آموز", student_labels or ["دانش‌آموز پیدا نشد"])
        parent = self._spinner("انتخاب ولی دانش‌آموز", ["ابتدا دانش‌آموز را انتخاب کنید"])

        def refresh_parents(spinner, value):
            row = self._selected_student(spinner)
            rows = self._load_parents_for_student(row.get("id") if row else None)
            names = [self._person_name(r) for r in rows]
            parent.values = [fa_display(n) for n in (names or ["نام ولی در پرونده ثبت نشده است"])]
            parent.text = parent.values[0]
        student.bind(text=refresh_parents)
        if students:
            student.text = fa_display(student_labels[0])
            refresh_parents(student, student_labels[0])

        day = self._spinner("روز هفته", ["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه"])
        title = self._field("عنوان ملاقات")
        date = self._field("تاریخ ملاقات")
        time = self._field("ساعت ملاقات")
        reason = self._field("علت ملاقات")
        desc = self._field("توضیحات تکمیلی", 72)
        desc.multiline = True
        for w in [student, parent, title, day, date, time, reason, desc]:
            form.add_widget(w)

        form.add_widget(self._button("ثبت درخواست ملاقات با اولیا", lambda *_: self._create_staff(
            student, parent, title, day, date, time, reason, desc, role), SUCCESS, 48))
        root.add_widget(self._scroll(form))
        self._my_requests(root)

    def _create_staff(self, student, parent, title, day, date, time, reason, desc, role):
        srow = self._selected_student(student)
        ptext = str(parent.text or "").strip()
        prow = next((p for p in self._parent_rows if ptext in (self._person_name(p), fa_display(self._person_name(p)))), None)
        prow = prow or (self._parent_rows[0] if self._parent_rows else None)
        if not srow or not prow:
            return self._message("دانش‌آموز و ولی او را از فهرست انتخاب کنید.", ERROR)
        self._create(
            student_name=self._person_name(srow), target_name=self._person_name(prow),
            title=title.text, day=day.text, date=date.text, time=time.text,
            reason=reason.text, description=desc.text, requester_role=role,
            student_id=srow.get("id"), target_username=prow.get("username"),
            parent_id=prow.get("id"),
        )

    def _create(self, student_name, target_name, title, day, date, time, reason, description, requester_role, **extra):
        if not all(str(x or "").strip() for x in [student_name, target_name, title, day, date, time, reason]):
            return self._message("عنوان، مخاطب، روز، تاریخ، ساعت و علت ملاقات الزامی است.", ERROR)
        payload = {
            "requester_username": self._username(),
            "requester_role": requester_role,
            "requester_name": getattr(self.app_state, "display_name", None) or ((getattr(self.app_state,"profile",{}) or {}).get("display_name") or self._username() or "کاربر"),
            "target_username": str(extra.get("target_username") or "").strip() or None,
            "target_role": self.target_role if requester_role == "parent" else "parent",
            "target_name": str(target_name).strip(),
            "title": str(title).strip(),
            "requested_day": str(day).strip(),
            "requested_date": str(date).strip(),
            "requested_time": str(time).strip(),
            "reason": str(reason).strip(),
            "description": str(description or "").strip(),
            "status": "pending_manager",
            "manager_status": "pending",
        }
        payload.update(extra)
        try:
            self.app_state.api.table_insert("meeting_requests", payload)
            self._message("درخواست با موفقیت ثبت شد و برای تأیید مدیر ارسال گردید.", SUCCESS)
        except Exception as exc:
            self._message("ثبت درخواست انجام نشد: " + str(exc), ERROR)

    def _review(self, root, role):
        title = "مدیریت درخواست‌های ملاقات" if role == "manager" else "ملاقات‌های ارجاع‌شده برای معاون آموزشی"
        root.add_widget(self._label(title, "15sp", PRIMARY, 36, True, True))
        if role == "manager":
            root.add_widget(self._button("＋ ایجاد درخواست ملاقات جدید", lambda *_: self._manager_create_form(), SUCCESS, 48))
        try:
            filters = {"order": "id.desc", "limit": "100"}
            if role == "educational":
                filters["status"] = "eq.manager_approved"
            rows = self.app_state.api.table_select("meeting_requests", filters) or []
        except Exception as exc:
            root.add_widget(self._label("خواندن درخواست‌ها انجام نشد: " + str(exc), color=ERROR, height=60))
            return
        if not rows:
            root.add_widget(self._label("درخواستی برای نمایش وجود ندارد.", height=60, center=True))
            return

        scroll_box = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None)
        scroll_box.bind(minimum_height=scroll_box.setter("height"))
        for row in rows:
            status = self._status_text(row.get("status"))
            card = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(4),
                             size_hint_y=None, height=dp(190))
            card.add_widget(self._label(
                f"#{row.get('id')} | {row.get('title') or 'ملاقات'} | {row.get('requester_name') or row.get('requester_username')} → {row.get('target_name') or 'مخاطب'}\n"
                f"دانش‌آموز: {row.get('student_name') or '-'} | روز: {row.get('requested_day') or '-'} | تاریخ: {row.get('requested_date')} | ساعت: {row.get('requested_time')}\n"
                f"علت: {row.get('reason') or '-'}\nوضعیت: {status}",
                "10sp", SECONDARY, 108, True))
            actions = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
            if role == "manager" and row.get("status") == "pending_manager":
                actions.add_widget(self._button("تأیید مدیر و ارجاع", lambda *_a, rid=row["id"]: self._manager_approve(rid), SUCCESS, 44))
                actions.add_widget(self._button("رد درخواست", lambda *_a, rid=row["id"]: self._reject(rid), ERROR, 44))
            elif role == "educational" and row.get("status") == "manager_approved":
                actions.add_widget(self._button("تأیید نهایی / تعیین وقت", lambda *_a, rid=row["id"], d=row.get("requested_date"), t=row.get("requested_time"): self._educational_approve(rid, d, t), SUCCESS, 44))
            card.add_widget(actions)
            scroll_box.add_widget(card)
        root.add_widget(self._scroll(scroll_box))

    def _status_text(self, status):
        return {
            "pending_manager": "در انتظار تأیید مدیر",
            "manager_approved": "تأیید مدیر؛ ارجاع‌شده به معاون آموزشی",
            "confirmed": "تأیید نهایی و زمان‌بندی‌شده",
            "rejected": "رد شده",
        }.get(str(status), str(status or "-"))

    def _manager_create_form(self):
        self._clear()
        self._label("ایجاد درخواست ملاقات", "21sp", PRIMARY, 52, True, True)
        # Never let a backend read failure make the meeting button appear dead.
        try:
            students = self.app_state.api.table_select("students", {"order":"id.asc","limit":"200"}) or []
        except Exception as exc:
            print("MANAGER MEETING STUDENT LOAD ERROR:", repr(exc))
            students = []
        self._student_rows = students
        labels = [self._person_name(r) for r in students]
        student = self._spinner("انتخاب دانش‌آموز", labels or ["دانش‌آموزی برای انتخاب ثبت نشده است"])
        parent = self._spinner("انتخاب ولی دانش‌آموز", ["ابتدا دانش‌آموز را انتخاب کنید"])
        def refresh(sp, value):
            row = self._selected_student(sp)
            rows = self._load_parents_for_student(row.get("id") if row else None)
            names = [self._person_name(r) for r in rows]
            parent.values = [fa_display(n) for n in (names or ["ولی برای این دانش‌آموز ثبت نشده است"])]
            parent.text = parent.values[0]
        student.bind(text=refresh)
        if students:
            student.text = fa_display(labels[0])
            refresh(student, labels[0])
        day=self._spinner("روز هفته", ["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه"])
        title=self._field("عنوان ملاقات")
        date=self._field("تاریخ ملاقات")
        time=self._field("ساعت ملاقات")
        reason=self._field("علت ملاقات")
        desc=self._field("توضیحات تکمیلی",72); desc.multiline=True
        for w in [student,parent,day,title,date,time,reason,desc]:
            self.body.add_widget(w)
        self.body.add_widget(self._button("ثبت درخواست ملاقات",lambda *_:self._create_manager_meeting(student,parent,title,day,date,time,reason,desc),SUCCESS,48))
        self.body.add_widget(self._button("بازگشت",lambda *_:self.show_home(),SECONDARY,44))

    def _create_manager_meeting(self, student,parent,title,day,date,time,reason,desc):
        srow=self._selected_student(student)
        ptext=str(parent.text or "").strip()
        prow=next((p for p in getattr(self,"_parent_rows",[]) if ptext in (self._person_name(p),fa_display(self._person_name(p)))),None)
        if not srow or not prow:
            return self._message("دانش‌آموز و ولی او را انتخاب کنید.",ERROR)
        self._create(
            student_name=self._person_name(srow), target_name=self._person_name(prow),
            title=title.text,day=day.text,date=date.text,time=time.text,reason=reason.text,
            description=desc.text,requester_role="manager",student_id=srow.get("id"),
            target_username=prow.get("username"),parent_id=prow.get("id")
        )

    def _manager_approve(self, rid):
        try:
            self.app_state.api.table_update("meeting_requests", {"id": f"eq.{rid}"}, {
                "manager_status": "approved",
                    "status": "manager_approved",
            })
            self._message("درخواست تأیید و برای معاون آموزشی ارجاع شد.", SUCCESS)
        except Exception as exc:
            self._message(str(exc), ERROR)

    def _educational_approve(self, rid, date, time):
        try:
            self.app_state.api.table_update("meeting_requests", {"id": f"eq.{rid}"}, {
                "status": "confirmed",
            })
            self._message("ملاقات نهایی شد و برای طرفین قابل پیگیری است.", SUCCESS)
        except Exception as exc:
            self._message(str(exc), ERROR)

    def _reject(self, rid):
        try:
            self.app_state.api.table_update("meeting_requests", {"id": f"eq.{rid}"}, {
                "manager_status": "rejected", "status": "rejected"
            })
            self._message("درخواست رد شد.", ERROR)
        except Exception as exc:
            self._message(str(exc), ERROR)

    def _message(self, text, color):
        try:
            self.clear_widgets()
            root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
            root.add_widget(self._label(text, "15sp", color, 90, True, True))
            root.add_widget(self._button("بازگشت", self.show_home, PRIMARY, 48))
            self.add_widget(root)
        except Exception:
            pass

    def _back(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
