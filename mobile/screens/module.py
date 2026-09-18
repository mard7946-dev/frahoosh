# Frahoosh final mobile module entry point.
# Professional operational navigation: two-column subpanel cards with real table workspaces.
from mobile.screens.professional_workspace import ProfessionalWorkspaceScreen
from mobile.screens.module_workspace import ModuleWorkspaceScreen, SUBMENUS, FRIENDLY, TABLE_FIELDS, HIDDEN
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from mobile.ui import font_name, rtl_text
from mobile.config import PRIMARY, SECONDARY, SUCCESS, WHITE

SUBMENUS.setdefault("participation", [
    ("فعالیت‌ها", "educational_activities"),
    ("رویدادها", "school_events"),
    ("مشارکت اولیا", "parent_meetings"),
])
FRIENDLY.setdefault("participation", "مشارکت و فعالیت‌ها")

ONLINE_CLASS_CREATORS = {"manager", "educational", "executive"}

class FinalModuleScreen(ProfessionalWorkspaceScreen):
    """Stable final entry point: two-column subpanels and touch-friendly forms."""

    def render(self):
        # Spacious operational home: every subpanel is a real touch card.
        self.body.clear_widgets()
        items = SUBMENUS.get(self.route, [])
        self.title.text = rtl_text(FRIENDLY.get(self.route, self.route))
        intro = self._surface(dp(104))
        intro.add_widget(self.label(FRIENDLY.get(self.route, self.route), "21sp", PRIMARY, True, "center"))
        intro.add_widget(self.label("محیط اختصاصی این پنل • هر کارت یک زیرپنل مستقل و متصل به اطلاعات واقعی سامانه است.", "10sp", SECONDARY, False, "center"))
        intro.add_widget(self.label(f"{len(items)} زیرپنل فعال", "9sp", SUCCESS, True, "center"))
        self.body.add_widget(intro)
        # The module area is intentionally large: at least half of the screen,
        # so the two-column cards have a comfortable professional workspace.
        module_height = max(dp(420), Window.height * 0.50)
        module_surface = self._surface(module_height)
        scroll = ScrollView(do_scroll_x=False, size_hint_y=None, height=module_height - dp(14))
        grid = GridLayout(cols=2, spacing=dp(10), padding=[dp(4), dp(4)], size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for i, (text, table) in enumerate(items, 1):
            card = self._surface(dp(154))
            card.add_widget(self.label(f"{i:02d}", "10sp", WHITE, True, "center"))
            # Give the number its own visible header strip without changing the actual data model.
            card.add_widget(self.label(text, "14sp", PRIMARY, True, "center"))
            card.add_widget(self.label(FRIENDLY.get(table, table), "8sp", SECONDARY, False, "center"))
            card.add_widget(self.btn("ورود به محیط این بخش", lambda *_a, t=table: self.open_table(t), SUCCESS if self.can_write(table) else PRIMARY, dp(40)))
            grid.add_widget(card)
        scroll.add_widget(grid)
        module_surface.add_widget(scroll)
        self.body.add_widget(module_surface)

    def editor(self, table, row):
        # Never allow a form-construction exception to terminate the Android process.
        try:
            fields = [k for k in self._form_fields(table, row)
                      if k not in {"id", "created_at", "updated_at", "deleted_at"}]
            if not fields:
                self.message("ثبت اطلاعات", "برای این زیرپنل فیلد قابل ثبت تعریف نشده است.")
                return
            root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
            sc = ScrollView(do_scroll_x=False)
            form = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
            form.bind(minimum_height=form.setter("height"))
            inputs = {}
            for field in fields:
                label_text = self._column_label(field)
                form.add_widget(self.label(label_text, "9sp", PRIMARY, True))
                ti = TextInput(
                    text="" if row is None else str(row.get(field, "")),
                    hint_text=rtl_text(label_text),
                    font_name=font_name(), font_size="12sp", halign="right",
                    multiline=field in {"description", "content", "body", "question", "note", "decision"},
                    size_hint_y=None,
                    height=dp(76 if field in {"description", "content", "body", "question", "note", "decision"} else 44),
                    padding=[dp(9), dp(7)],
                )
                inputs[field] = ti
                form.add_widget(ti)
            sc.add_widget(form)
            root.add_widget(sc)
            actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
            popup = Popup(
                title=rtl_text(("ویرایش" if row else "ثبت جدید") + " • " + FRIENDLY.get(table, table)),
                content=root, size_hint=(.95, .90), auto_dismiss=False
            )
            actions.add_widget(self.btn("انصراف", lambda *_: popup.dismiss(), SECONDARY, dp(44)))
            actions.add_widget(self.btn("ذخیره", lambda *_: self.save(table, row, inputs, popup), SUCCESS, dp(44)))
            root.add_widget(actions)
            popup.open()
        except Exception as exc:
            print("NEW RECORD EDITOR ERROR:", repr(exc))
            self.message("ثبت اطلاعات", "باز کردن فرم این زیرپنل با خطا روبه‌رو شد. اطلاعات سامانه محفوظ است.")

    def open_table(self, table, refresh_subbar=True):
        if table == "meeting_requests":
            return self._meeting_workspace()
        if table == "smart_class_monitor":
            return self._smart_class_monitor()
        if table in ("teacher_exams", "online_classes", "messages", "payment_offers"):
            return super().open_table(table, refresh_subbar=False)
        return ModuleWorkspaceScreen.open_table(self, table, refresh_subbar=False)



    def _meeting_workspace(self):
        """Real parent/teacher/staff/counselor meeting workflow backed by Supabase."""
        self.table = "meeting_requests"
        self.body.clear_widgets()
        role = self.role()
        title = "ملاقات و درخواست جلسه"
        head = self._surface(dp(92))
        head.add_widget(self.label(title, "18sp", PRIMARY, True, "center"))
        if role in {"parent", "اولیا"}:
            head.add_widget(self.label("درخواست ملاقات با دبیر، کادر، مشاور یا مدیریت", "10sp", SECONDARY, False, "center"))
            self._meeting_parent_form()
        else:
            head.add_widget(self.label("ثبت درخواست ملاقات با اولیای دانش‌آموز؛ درخواست پس از تایید مدیر به معاون آموزشی ارجاع می‌شود.", "9sp", SECONDARY, False, "center"))
            self._meeting_staff_form()
        self.body.add_widget(head)
        self._meeting_list()

    def _spinner(self, values, default=None, height=48):
        vals = list(values) or ["—"]
        return Spinner(text=default or vals[0], values=vals, font_name=font_name(), font_size="13sp",
                       size_hint_y=None, height=dp(height), background_normal="", background_color=CARD)

    def _meeting_parent_form(self):
        role_names = [("teacher","دبیر"),("staff","کادر"),("advisor","مشاور"),("manager","مدیریت")]
        target = self._spinner([x[1] for x in role_names], "دبیر")
        self.body.add_widget(self.label("ملاقات با", "10sp", PRIMARY, True, "right"))
        self.body.add_widget(target)
        person = TextInput(hint_text=rtl_text("نام دبیر / کادر / مشاور / مدیر"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(48))
        student = TextInput(hint_text=rtl_text("شناسه دانش‌آموز"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(48), text=str(self.app_state.profile.get("linked_student_id") or ""))
        date = TextInput(hint_text=rtl_text("تاریخ ملاقات"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(48))
        time = TextInput(hint_text=rtl_text("ساعت ملاقات"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(48))
        reason = TextInput(hint_text=rtl_text("علت ملاقات"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(52))
        description = TextInput(hint_text=rtl_text("توضیحات تکمیلی"), font_name=font_name(), font_size="13sp", halign="right", multiline=True, size_hint_y=None, height=dp(80))
        for w in (person, student, date, time, reason, description): self.body.add_widget(w)
        self.body.add_widget(self.btn("ثبت درخواست ملاقات", lambda *_: self._save_meeting(
            requester_role="parent", target_role=dict(role_names).get(target.text,"teacher"), target_name=person.text,
            student_id=student.text, requested_date=date.text, requested_time=time.text,
            reason=reason.text, description=description.text
        ), SUCCESS, dp(46)))

    def _meeting_staff_form(self):
        role = self.role()
        requester_role = "teacher" if role in {"teacher","دبیر","teachers"} else ("advisor" if role in {"advisor","counselor","مشاوره"} else "staff")
        student = TextInput(hint_text=rtl_text("شناسه دانش‌آموز"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(48))
        parent = TextInput(hint_text=rtl_text("نام ولی دانش‌آموز"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(48))
        date = TextInput(hint_text=rtl_text("تاریخ ملاقات"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(48))
        time = TextInput(hint_text=rtl_text("ساعت ملاقات"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(48))
        reason = TextInput(hint_text=rtl_text("علت ملاقات"), font_name=font_name(), font_size="13sp", halign="right", size_hint_y=None, height=dp(52))
        description = TextInput(hint_text=rtl_text("توضیحات تکمیلی"), font_name=font_name(), font_size="13sp", halign="right", multiline=True, size_hint_y=None, height=dp(80))
        for w in (student,parent,date,time,reason,description): self.body.add_widget(w)
        self.body.add_widget(self.btn("ثبت درخواست ملاقات با ولی", lambda *_: self._save_meeting(
            requester_role=requester_role, target_role="parent", target_name=parent.text,
            student_id=student.text, requested_date=date.text, requested_time=time.text,
            reason=reason.text, description=description.text, parent_name=parent.text
        ), SUCCESS, dp(46)))

    def _save_meeting(self, requester_role, target_role, target_name, student_id, requested_date, requested_time, reason, description, parent_name=""):
        if not all(str(x or "").strip() for x in (target_name, student_id, requested_date, requested_time, reason)):
            self.message("درخواست ملاقات", "نام طرف ملاقات، دانش‌آموز، تاریخ، ساعت و علت الزامی است.")
            return
        profile = self.app_state.profile
        payload = {
            "requester_user_id": str(profile.get("username") or profile.get("email") or self.app_state.user.get("email") or ""),
            "requester_role": requester_role,
            "requester_name": self.app_state.display_name,
            "parent_id": profile.get("linked_parent_id"),
            "parent_name": parent_name or (self.app_state.display_name if requester_role == "parent" else ""),
            "student_id": int(student_id) if str(student_id).isdigit() else None,
            "student_name": "",
            "target_role": target_role,
            "target_name": str(target_name).strip(),
            "requested_date_shamsi": str(requested_date).strip(),
            "requested_time": str(requested_time).strip(),
            "reason": str(reason).strip(),
            "description": str(description or "").strip(),
        }
        try:
            self.app_state.api.table_insert("meeting_requests", payload)
            self.message("درخواست ملاقات", "درخواست ثبت شد و برای تایید مدیر ارسال شد.")
            self._meeting_workspace()
        except Exception as exc:
            self.message("خطا", str(exc))

    def _meeting_list(self):
        try:
            rows = self.app_state.api.table_select("meeting_requests", {"order":"id.desc", "limit":"30"})
        except Exception as exc:
            self.body.add_widget(self.label("خواندن درخواست‌های ملاقات انجام نشد: "+str(exc), "9sp", SECONDARY, False, "center"))
            return
        if not rows:
            self.body.add_widget(self.label("هنوز درخواست ملاقاتی ثبت نشده است.", "10sp", SECONDARY, False, "center"))
            return
        for row in rows:
            text = (
                f"#{row.get('id')}  {row.get('requester_name') or 'کاربر'} → {row.get('target_name') or 'مخاطب'}\n"
                f"دانش‌آموز: {row.get('student_name') or row.get('student_id') or '—'} | "
                f"{row.get('requested_date_shamsi') or '—'} | {row.get('requested_time') or '—'}\n"
                f"علت: {row.get('reason') or '—'}\n"
                f"مدیر: {row.get('manager_status') or '—'} | معاون آموزشی: {row.get('educational_status') or '—'} | وضعیت: {row.get('final_status') or '—'}"
            )
            self.body.add_widget(self.label(text, "10sp", PRIMARY, True, "right", 112))
            if self.role() in {"manager","admin","administrator","مدیر","مدیریت"} and row.get("manager_status") == "در انتظار تایید مدیر":
                self.body.add_widget(self.btn("✓ تایید مدیر و ارجاع به معاون آموزشی", lambda *_ ,x=row.get("id"): self._meeting_action(x,"approve"), SUCCESS, dp(42)))
                self.body.add_widget(self.btn("✕ رد درخواست", lambda *_ ,x=row.get("id"): self._meeting_action(x,"reject"), ERROR, dp(42)))
            if self.role() in {"educational","معاون آموزشی"} and row.get("manager_status") == "تایید مدیر":
                self.body.add_widget(self.btn("تایید نهایی / تعیین وقت", lambda *_ ,x=row.get("id"): self._meeting_schedule(x), SUCCESS, dp(42)))

    def _meeting_action(self, meeting_id, action):
        try:
            self.app_state.api.rpc("frahoosh_update_meeting_request", {"p_id":meeting_id,"p_action":action})
            self._meeting_workspace()
        except Exception as exc: self.message("عملیات ملاقات", str(exc))

    def _meeting_schedule(self, meeting_id):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        date = TextInput(hint_text=rtl_text("تاریخ نهایی"), font_name=font_name(), halign="right", size_hint_y=None, height=dp(48))
        time = TextInput(hint_text=rtl_text("ساعت نهایی"), font_name=font_name(), halign="right", size_hint_y=None, height=dp(48))
        note = TextInput(hint_text=rtl_text("یادداشت معاون آموزشی"), font_name=font_name(), halign="right", multiline=True, size_hint_y=None, height=dp(80))
        for w in (date,time,note): root.add_widget(w)
        pop = Popup(title=rtl_text("تعیین زمان ملاقات"), content=root, size_hint=(.92,.48), auto_dismiss=False)
        actions=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6))
        actions.add_widget(self.btn("انصراف",lambda *_:pop.dismiss(),SECONDARY,dp(44)))
        actions.add_widget(self.btn("تایید نهایی",lambda *_: self._finish_meeting(pop,meeting_id,date,time,note),SUCCESS,dp(44)))
        root.add_widget(actions); pop.open()

    def _finish_meeting(self,pop,meeting_id,date,time,note):
        try:
            self.app_state.api.rpc("frahoosh_update_meeting_request", {"p_id":meeting_id,"p_action":"schedule","p_note":note.text,"p_final_date":date.text,"p_final_time":time.text})
            pop.dismiss(); self._meeting_workspace()
        except Exception as exc: self.message("تعیین وقت", str(exc))

    def _smart_class_monitor(self):
        """Manager-only live content view: board, files, chat, quizzes and session data."""
        self.table = "smart_class_monitor"
        self.body.clear_widgets()
        if self.role() not in {"manager","admin","administrator","مدیر","مدیریت"}:
            self.body.add_widget(self.label("این بخش فقط برای مدیریت فعال است.", "14sp", SECONDARY, True, "center", 90))
            return
        head=self._surface(dp(96))
        head.add_widget(self.label("نمونه کلاس هوشمند — مشاهده محتوای کلاس", "18sp", PRIMARY, True, "center"))
        head.add_widget(self.label("مدیریت می‌تواند محتوای ثبت‌شده کلاس را بررسی کند و بخش‌های مختلف آن را برای دبیر، دانش‌آموز و اولیا توضیح دهد.", "9sp", SECONDARY, False, "center"))
        self.body.add_widget(head)
        try: classes=self.app_state.api.table_select("online_classes", {"order":"id.desc","limit":"20"})
        except Exception: classes=[]
        if not classes:
            self.body.add_widget(self.label("هنوز کلاس آنلاینی ثبت نشده است؛ بعد از ساخت کلاس، محتوای واقعی آن در اینجا نمایش داده می‌شود.", "10sp", SECONDARY, False, "center", 80))
            return
        for c in classes:
            cid=c.get("id")
            self.body.add_widget(self.label(f"کلاس #{cid} | {c.get('title') or 'کلاس آنلاین'}\nدرس: {c.get('subject') or '—'} | پایه: {c.get('grade') or '—'} | کلاس: {c.get('class_name') or '—'}", "11sp", PRIMARY, True, "right", 82))
            for table,title in [
                ("smart_board_content","📚 محتوای آموزشی"),
                ("smart_board_whiteboards","🖊 تخته و نوشته‌ها"),
                ("smart_board_media","🖼 عکس و رسانه"),
                ("smart_board_files","📎 فایل و PDF"),
                ("smart_board_quizzes","❓ آزمون کوتاه"),
                ("online_class_chat","💬 گفت‌وگو"),
                ("online_class_activity","📋 فعالیت کلاس"),
                ("online_class_sessions","⏱ جلسات"),
            ]:
                try:
                    params={"class_id":f"eq.{cid}","order":"id.desc","limit":"20"}
                    rows=self.app_state.api.table_select(table,params)
                except Exception:
                    rows=[]
                if rows:
                    self.body.add_widget(self.label(title, "11sp", SUCCESS, True, "right", 34))
                    for row in rows:
                        content=row.get("content") or row.get("text") or row.get("title") or row.get("body") or row.get("file_name") or row.get("file_url") or row.get("question") or "مورد ثبت‌شده"
                        self.body.add_widget(self.label(str(content), "9sp", SECONDARY, False, "right", 58))

    def _start_session(self, class_id):
        if not class_id:
            return
        self._write_async("online_class_sessions", {"class_id": class_id}, "جلسه آنلاین ثبت شد.")

    def _popup_form(self, title, fields, save_cb, size=(.94, .88)):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        from kivy.uix.scrollview import ScrollView
        form_scroll = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(7))
        form.bind(minimum_height=form.setter("height"))
        inputs = {}
        for key, hint in fields:
            ti = TextInput(
                hint_text=rtl_text(hint), text="", font_name=font_name(), font_size="15sp",
                halign="right", multiline=True if key in {"description", "body", "question", "accepted_answers"} else False,
                size_hint_y=None, height=dp(76 if key in {"description", "body", "question"} else 52),
                padding=[dp(12), dp(12)],
            )
            inputs[key] = ti
            form.add_widget(ti)
        form_scroll.add_widget(form)
        root.add_widget(form_scroll)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        popup = Popup(title=rtl_text(title), content=root, size_hint=size, auto_dismiss=False)
        actions.add_widget(self.btn("انصراف", lambda *_: popup.dismiss(), SECONDARY, dp(44)))
        actions.add_widget(self.btn("ذخیره", lambda *_: save_cb(inputs, popup), SUCCESS, dp(44)))
        root.add_widget(actions)
        popup.open()

    def _form_fields(self, table, row):
        # Only render fields that really exist in Supabase.
        forms = {
            "students":["first_name","last_name","father_name","mother_name","national_code","student_code","birth_date","religion","sect","nationality","phone","parent_phone","grade","class_name","email","address"],
            "teachers":["first_name","last_name","national_code","employee_code","phone","email","subject","grades","employment_status"],
            "staff":["first_name","last_name","role","phone","work_experience","employee_code","national_code","religion","sect","employment_status","teaching_hours"],
            "teacher_classes":["teacher_id","teacher_name","subject","grade","class_name","active"],
            "lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title","content","session_date","lesson_title","description","plan_date"],
            "assignments":["student_id","teacher_id","title","description","status","due_date","subject","class_name"],
            "attendance":["student_id","teacher_id","class_name","subject","attendance_date","status","description"],
            "grades":["student_id","teacher_id","subject","exam_name","score","max_score","description","grade_type","term","grade_date","title"],
            "student_grades":["student_id","teacher_id","subject","class_name","assessment_type","assessment_title","score","coefficient","grade_date","description","term","manager_released"],
            "discipline_records":["student_id","teacher_id","title","description","priority","status","item_id","deduction","actor_username","actor_role","note"],
            "educational_followups":["student_id","followup_date","followup_items","decision","status"],
            "academic_followups":["student_id","followup_date","followup_items","decision","status"],
            "teacher_exams":["teacher_id","title","subject","grade","class_name","exam_type","exam_date","duration","description","published","secure_mode","share_enabled","share_code","standard_mode","max_attempts","passing_score"],
            "online_classes":["title","subject","lesson","teacher","grade","class_name","duration","pages","record","smart_board","quiz","camera","microphone","start_time","end_time","status","activated_by","join_url","meeting_url"],
            "certificate_requests":["student_id","student_name","destination","request_date","status","executive_note"],
            "parent_meetings":["student_id","teacher_id","parent_phone","reason","meeting_date","status"],
            "teacher_parent_meetings":["teacher_id","student_id","parent_id","requested_date","status","manager_status","reason"],
            "student_referrals":["student_id","teacher_id","referral_to","reason","referral_date","status"],
            "khwarizmi_registrations":["title","category","grade","class_name","student_id","status"],
            "activity_offers":["title","category","event_date","active","amount","settings"],
            "activity_registrations":["activity_id","student_id","participation_type","team_members","competition_type","payment_status","status"],
            "school_events":["title","description","event_date","status"],
            "finance_donations":["donor_name","amount","description","donation_date"],
            "messages":["sender","receiver","text","sender_user_id","sender_name","title","body","audience_type","audience_value"],
            "school_profile":["school_name","school_code","principal_name","phone","address","academic_year","logo_path","request_date_shamsi"],
            "monthly_report_cards":["student_id","month_name","active"],
            "class_seat_assignments":["class_id","student_id","seat_number","academic_year"],
            "exam_seat_assignments":["exam_id","student_id","subject","exam_date","seat_number"],
            "assignment_submissions":["assignment_id","student_id","file_url","answer_text","submitted_at","status"],
        }
        requested = forms.get(table)
        real = set(TABLE_FIELDS.get(table, []))
        fields = [f for f in requested if not real or f in real] if requested else list(real)
        fields = [f for f in fields if f not in {"id","created_at","updated_at","deleted_at"}]
        if not fields:
            fields = [k for k in (row or {}) if k not in {"id","created_at","updated_at","deleted_at"}]
        return fields or ["title","description","status"]
    def _column_label(self, key):
        return {
            "first_name":"نام","last_name":"نام خانوادگی","father_name":"نام پدر","mother_name":"نام مادر",
            "national_code":"کد ملی / شناسه یکتا","personnel_code":"کد پرسنلی","birth_certificate_place":"محل صدور",
            "birth_place":"محل تولد","religion":"دین","sect":"مذهب","nationality":"ملیت","student_phone":"شماره تماس دانش‌آموز",
            "father_phone":"شماره تماس پدر","mother_phone":"شماره تماس مادر","phone":"شماره تماس","service_years":"سابقه خدمت",
            "grade":"پایه","class_name":"کلاس","subject":"درس","teacher_name":"نام دبیر","teacher_id":"شناسه دبیر",
            "student_id":"شناسه دانش‌آموز","score":"نمره","max_score":"حداکثر نمره","status":"وضعیت","amount":"مبلغ",
            "title":"عنوان","description":"توضیحات","attendance_date":"تاریخ حضور","event_date":"تاریخ رویداد",
            "exam_date":"تاریخ آزمون","start_time_shamsi":"تاریخ و ساعت شروع","end_time_shamsi":"تاریخ و ساعت پایان",
            "role":"نقش","email":"ایمیل","username":"نام کاربری","term":"نوبت","academic_year":"سال تحصیلی","content":"محتوا",
            "question":"متن سؤال","question_type":"نوع سؤال","published":"انتشار","duration":"مدت به دقیقه","share_code":"کد اشتراک",
            "target_class_name":"کلاس مقصد","start_at":"شروع","end_at":"پایان","lesson":"مبحث / جلسه","exam_type":"نوع آزمون",
            "secure_mode":"حالت امن","max_attempts":"حداکثر دفعات شرکت","passing_score":"نمره قبولی","join_url":"لینک ورود",
            "meeting_url":"لینک جلسه","weekly_sessions":"تعداد جلسات در هفته","teaching_amount_1":"میزان تدریس جلسه ۱",
            "teaching_date_1":"تاریخ جلسه ۱","teaching_title_1":"عنوان تدریس جلسه ۱","activity_type_1":"نوع فعالیت جلسه ۱",
            "teaching_amount_2":"میزان تدریس جلسه ۲","teaching_date_2":"تاریخ جلسه ۲","teaching_title_2":"عنوان تدریس جلسه ۲",
            "activity_type_2":"نوع فعالیت جلسه ۲","assignment_type":"نوع تکلیف","due_at":"زمان تحویل","period":"زنگ",
            "discipline_type":"نوع مورد انضباطی","record_date":"تاریخ ثبت","decision_type":"نوع تصمیم","deduct_score":"میزان کسر نمره",
            "referral_to":"ارجاع به","followup_date":"تاریخ پیگیری","followup_items":"موارد پیگیری شده","decision":"تصمیم‌گیری",
            "destination":"برای کجا صادر شود","request_date":"تاریخ درخواست","executive_note":"یادداشت معاون اجرایی",
            "target_type":"نوع مخاطب","target_person":"شخص مورد ملاقات","requested_date":"تاریخ ملاقات","reason":"علت درخواست",
            "category":"دسته‌بندی","activity_key":"نوع فعالیت","sport_mode":"نوع شرکت (تیمی / انفرادی)","team_name":"نام تیم / همگروه‌ها",
            "team_members":"همگروه‌ها","offer_id":"گزینه پرداخت","payment_status":"وضعیت پرداخت","audience_type":"نوع مخاطب",
            "audience_value":"مخاطب انتخاب‌شده"
        }.get(key, (f"میزان تدریس جلسه {key.split('_')[-1]}" if key.startswith("teaching_amount_") else f"تاریخ جلسه {key.split('_')[-1]}" if key.startswith("teaching_date_") else f"عنوان تدریس جلسه {key.split('_')[-1]}" if key.startswith("teaching_title_") else f"نوع فعالیت جلسه {key.split('_')[-1]}" if key.startswith("activity_type_") else FRIENDLY.get(key, key)))
    def _special_content(self, content, table):
        if table in ("online_classes", "online_class_sessions"):
            if self.role() not in ONLINE_CLASS_CREATORS:
                content.add_widget(self.btn("مشاهده کلاس‌های فعال", lambda *_: self._online_list(), PRIMARY, dp(42)))
                content.add_widget(self.label("ایجاد کلاس فقط توسط مدیر، معاون اجرایی و معاون آموزشی انجام می‌شود.", "9sp", SECONDARY, False, "center"))
                return
        return super()._special_content(content, table)

    def _online_list(self):
        self.table = "online_classes"
        self.body.clear_widgets()
        head = self._surface(dp(74))
        head.add_widget(self.label("کلاس‌های آنلاین", "17sp", PRIMARY, True, "center"))
        if self.role() in ONLINE_CLASS_CREATORS:
            head.add_widget(self.btn(" ایجاد کلاس", lambda *_: self._online_editor(), SUCCESS, dp(38)))
        else:
            head.add_widget(self.label("کلاس‌های فعال برای دبیر و دانش‌آموز از اینجا قابل مشاهده هستند.", "9sp", SECONDARY, False, "center"))
        self.body.add_widget(head)
        area = BoxLayout(orientation="vertical"); self.body.add_widget(area); self._load_to(area, "online_classes", self._online_card)

    def _online_editor(self):
        if self.role() not in ONLINE_CLASS_CREATORS:
            self.message("دسترسی کلاس آنلاین", "ایجاد کلاس فقط توسط مدیر، معاون اجرایی و معاون آموزشی مجاز است."); return
        return super()._online_editor()

    def _save_online(self, inputs, popup):
        if self.role() not in ONLINE_CLASS_CREATORS:
            self.message("دسترسی کلاس آنلاین", "ایجاد کلاس فقط توسط مدیر، معاون اجرایی و معاون آموزشی مجاز است."); return
        return super()._save_online(inputs, popup)

ModuleScreen = FinalModuleScreen
ProfessionalModuleScreen = FinalModuleScreen

__all__ = ["ModuleScreen", "ProfessionalModuleScreen", "FinalModuleScreen"]
