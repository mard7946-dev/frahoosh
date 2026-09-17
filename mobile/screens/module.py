# Frahoosh final mobile module entry point.
# Accordion navigation only: no PageLayout and no swipe between subpanels.
from mobile.screens.professional_workspace import ProfessionalWorkspaceScreen
from mobile.screens.module_workspace import ModuleWorkspaceScreen, SUBMENUS, FRIENDLY
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

SUBMENUS.setdefault("participation", [
    ("فعالیت‌ها", "educational_activities"),
    ("رویدادها", "school_events"),
    ("مشارکت اولیا", "parent_meetings"),
])
FRIENDLY.setdefault("participation", "مشارکت و فعالیت‌ها")

ONLINE_CLASS_CREATORS = {"manager", "educational", "executive"}

class FinalModuleScreen(ProfessionalWorkspaceScreen):
    """Stable final entry point: accordion subpanels and touch-friendly forms."""

    def open_table(self, table, refresh_subbar=True):
        if table in ("teacher_exams", "online_classes", "messages", "payment_offers"):
            return super().open_table(table, refresh_subbar=False)
        return ModuleWorkspaceScreen.open_table(self, table, refresh_subbar=False)

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

    def editor(self, table, row):
        fields = [k for k in (self.FORMS.get(table) if hasattr(self, "FORMS") else None) or [] if k not in self.HIDDEN] if False else [k for k in (self._form_fields(table, row)) if k not in {"id", "created_at", "updated_at", "deleted_at"}]
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        from kivy.uix.scrollview import ScrollView
        sc = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        inputs = {}
        for f in fields:
            ti = TextInput(text="" if row is None else str(row.get(f, "")), hint_text=rtl_text(FRIENDLY.get(f, self._column_label(f))), font_name=font_name(), font_size="15sp", halign="right", multiline=f in {"description", "content", "body", "question"}, size_hint_y=None, height=dp(78 if f in {"description", "content", "body", "question"} else 52), padding=[dp(12), dp(12)])
            inputs[f] = ti
            form.add_widget(ti)
        sc.add_widget(form); root.add_widget(sc)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        popup = Popup(title=rtl_text(("ویرایش" if row else "ثبت جدید") + " • " + FRIENDLY.get(table, table)), content=root, size_hint=(.94, .90), auto_dismiss=False)
        actions.add_widget(self.btn("انصراف", lambda *_: popup.dismiss(), SECONDARY, dp(44)))
        actions.add_widget(self.btn("ذخیره", lambda *_: self.save(table, row, inputs, popup), SUCCESS, dp(44)))
        root.add_widget(actions); popup.open()

    def _form_fields(self, table, row):
        forms = {
            "students":["first_name","last_name","national_code","grade","class_name","phone"],
            "teachers":["first_name","last_name","national_code","phone","subject"],
            "staff":["first_name","last_name","phone","role"],
            "school_events":["title","description","event_date","status"],
            "lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title","description"],
            "assignments":["student_id","teacher_id","title","subject","class_name","description","status"],
            "attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],
            "grades":["student_id","teacher_id","subject","score","max_score","term"],
            "teacher_exams":["teacher_id","title","subject","grade","class_name","exam_type","duration","description","published","secure_mode","max_attempts","passing_score"],
            "online_classes":["title","subject","lesson","teacher","grade","class_name","duration","start_time_shamsi","end_time_shamsi","status","join_url","meeting_url"],
            "finance_donations":["title","description","amount","status"],
            "messages":["title","description","status"],
            "school_profile":["title","description"],
        }
        return forms.get(table) or [k for k in (row or {}) if k not in {"id","created_at","updated_at","deleted_at"}] or ["title","description","status"]

    def _column_label(self, key):
        return {
            "first_name":"نام", "last_name":"نام خانوادگی", "national_code":"کد ملی", "grade":"پایه", "class_name":"کلاس", "phone":"تلفن", "subject":"درس", "teacher_name":"نام دبیر", "teacher_id":"شناسه دبیر", "student_id":"شناسه دانش‌آموز", "score":"نمره", "max_score":"حداکثر نمره", "status":"وضعیت", "amount":"مبلغ", "title":"عنوان", "description":"توضیحات", "attendance_date":"تاریخ حضور", "event_date":"تاریخ رویداد", "exam_date":"تاریخ آزمون", "start_time_shamsi":"تاریخ و ساعت شروع", "end_time_shamsi":"تاریخ و ساعت پایان", "role":"نقش", "email":"ایمیل", "username":"نام کاربری", "term":"نوبت", "academic_year":"سال تحصیلی", "content":"محتوا", "question":"متن سؤال", "question_type":"نوع سؤال", "published":"انتشار", "duration":"مدت به دقیقه", "share_code":"کد اشتراک", "target_class_name":"کلاس مقصد", "start_at":"شروع", "end_at":"پایان", "lesson":"مبحث/جلسه", "exam_type":"نوع آزمون", "secure_mode":"حالت امن", "max_attempts":"حداکثر دفعات شرکت", "passing_score":"نمره قبولی", "join_url":"لینک ورود", "meeting_url":"لینک جلسه"
        }.get(key, FRIENDLY.get(key, key))

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
            head.add_widget(self.btn("＋ ایجاد کلاس", lambda *_: self._online_editor(), SUCCESS, dp(38)))
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
