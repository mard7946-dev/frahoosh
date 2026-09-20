from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from mobile.ui import font_name, rtl_text

NAVY = (0.02, 0.08, 0.20, 1)
BLUE = (0.05, 0.30, 0.65, 1)
CYAN = (0.03, 0.75, 0.92, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.75, 0.82, 0.92, 1)
BG = (0.95, 0.97, 0.99, 1)
GREEN = (0.10, 0.55, 0.30, 1)

PANELS = [
    ("مدیریت", "management"), ("معاون آموزشی", "educational"),
    ("معاون اجرایی", "executive"), ("معاون پرورشی", "cultural"),
    ("مشاوره", "advisor"), ("دبیران", "teachers"),
    ("دانش‌آموزان", "students"), ("اولیا", "parents"),
    ("مالی", "finance"), ("پرداخت آنلاین", "payment"),
    ("کلاس‌های آنلاین", "online"), ("آزمون آنلاین", "teacher_exams"),
    ("تابلو هوشمند", "smart_board"), ("هوش مصنوعی", "ai"),
    ("گزارش‌ها", "reports"), ("برنامه هفتگی", "schedule"),
    ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"),
    ("درباره برنامه", "about"),
]

ROLE_MENUS = {
    "management": [
        ("مدیریت کاربران و کارکنان", "staff"), ("دانش‌آموزان", "students"),
        ("دبیران", "teachers"), ("کلاس‌ها", "executive_classes"),
        ("اطلاعیه‌ها", "school_events"), ("گزارش‌ها", "executive_reports"),
        ("برنامه هفتگی", "weekly_schedule"), ("برنامه امتحانات", "exam_schedule"),
    ],
    "educational": [
        ("تأیید حضور و غیاب", "attendance"), ("ارجاعات دانش‌آموزی", "referrals"),
        ("درخواست جلسات", "teacher_meetings"), ("گزارش آموزشی", "reports"),
        ("کلاس‌های مجازی", "online"), ("اطلاع‌رسانی", "school_events"),
        ("برنامه امتحانات", "exam_schedule"), ("بانک سوال", "question_bank"),
    ],
    "executive": [
        ("دانش‌آموزان", "students"), ("مدیریت کلاس‌ها", "executive_classes"),
        ("امور اجرایی", "executive_operations"), ("گزارش‌های اجرایی", "executive_reports"),
        ("برنامه هفتگی", "weekly_schedule"), ("برنامه امتحانات", "exam_schedule"),
        ("کلاس آنلاین", "online"),
    ],
    "cultural": [
        ("فعالیت‌های فرهنگی", "cultural_activity_registrations"),
        ("مسابقات", "competitions"), ("گزارش‌های فرهنگی", "cultural_reports"),
        ("انضباطی", "discipline_records"), ("پیام‌ها", "school_events"),
    ],
    "advisor": [
        ("تابلو اعلانات مشاور", "counselor_board"), ("پرونده مشاوره", "counseling_file"),
        ("پیگیری وضعیت دانش‌آموز", "student_follow"), ("ارجاع به مدیریت", "refer_management"),
        ("جلسه اولیا", "parent_meeting"), ("کلاس‌های آموزشی", "counseling_classes"),
        ("آموزش خانواده", "family_training"), ("هدایت تحصیلی", "career_guidance"),
        ("گزارشات", "reports"), ("موارد انضباطی", "discipline_records"),
        ("پیام‌ها", "school_events"),
    ],
    "teachers": [
        ("کلاس‌های من", "executive_classes"), ("حضور و غیاب", "teacher_attendance"),
        ("ثبت نمرات", "grade_items"), ("تکالیف", "assignments"),
        ("آزمون آنلاین", "teacher_exams"), ("کلاس مجازی", "online"),
        ("طرح درس", "lesson_plans"), ("جلسات اولیا", "teacher_meetings"),
        ("گزارش‌ها", "reports"), ("بانک سوال", "question_bank"),
        ("پیام‌ها", "school_events"),
    ],
    "students": [
        ("پروفایل من", "students"), ("حضور و غیاب", "attendance"),
        ("نمرات", "grades"), ("تکالیف", "assignments"),
        ("فعالیت‌های آموزشی", "educational_activities"), ("کلاس‌های آنلاین", "online"),
        ("برنامه هفتگی", "weekly_schedule"), ("اطلاعیه‌ها", "school_events"),
        ("آزمون‌ها", "teacher_exams"),
    ],
    "parents": [
        ("فرزندان من", "parent_children"), ("نمرات", "grades"),
        ("حضور و غیاب", "attendance"), ("تکالیف", "assignments"),
        ("فعالیت‌های آموزشی", "educational_activities"), ("برنامه هفتگی", "weekly_schedule"),
        ("آزمون‌ها", "exam_schedule"), ("پرداخت‌ها", "payment_records"),
        ("درخواست ملاقات", "parent_meeting_requests"), ("اطلاعیه‌ها", "school_events"),
    ],
}

TABLE_FIELDS = {
    "students": ["id","first_name","last_name","national_code","student_code","grade","class_name","phone","parent_phone","email","address"],
    "teachers": ["id","first_name","last_name","national_code","phone","email","subject","grades"],
    "staff": ["id","first_name","last_name","role","phone","employee_code","national_code","employment_status"],
    "attendance": ["id","student_id","date","status","description"],
    "teacher_attendance": ["id","student_id","teacher_id","class_name","subject","attendance_date","status","description"],
    "grades": ["id","student_id","subject","exam_name","score","grade_type","term","grade_date"],
    "grade_items": ["id","student_id","teacher_id","subject","grade_type","term","score","grade_date","description"],
    "assignments": ["id","student_id","teacher","subject","title","due_date","status"],
    "teacher_exams": ["id","teacher_id","title","subject","grade","class_name","exam_type","exam_date","duration"],
    "lesson_plans": ["id","teacher_id","teacher_name","subject","grade","class_name","title","content","session_date","created_at"],
    "teacher_meetings": ["id","teacher_id","student_id","student_name","parent_name","meeting_at","subject","status","report"],
    "executive_classes": ["id","name","grade","teacher","created_at"],
    "executive_operations": ["id","operation_type","title","student_id","class_name","status","operation_date","description"],
    "executive_reports": ["id","title","report_type","student_id","class_name","report_date","created_by"],
    "weekly_schedule": ["id","teacher","hours","grade","class_count","subject","bell_pattern","class_names"],
    "exam_schedule": ["id","subject","grade","exam_date","duration","weight"],
    "cultural_activity_registrations": ["id","student_id","activity_id","activity_title","activity_kind","fee","payment_status","registration_date"],
    "competitions": ["id","title","category","start_date","end_date","status"],
    "cultural_reports": ["id","title","report_type","activity_id","report_date"],
    "payment_records": ["id","student_id","parent_username","title","amount","status","payment_date"],
    "school_events": ["id","event_type","title","actor_username","created_at"],
    "smart_board_content": ["id","title","content","class_id","teacher_id","content_date_shamsi"],
    "ai_questions": ["id","username","role","question","answer","answer_date_shamsi"],
    "ai_educational_analysis": ["id","student_id","teacher_id","subject","period","score","risk_level","analysis_date_shamsi"],
    "parent_children": ["id","first_name","last_name","student_code","grade","class_name","parent_phone"],
    "parent_meeting_requests": ["id","student_id","teacher_id","parent_phone","reason","meeting_date","status"],
}

LABELS = {
    "id":"شناسه","first_name":"نام","last_name":"نام خانوادگی","national_code":"کد ملی",
    "student_code":"کد دانش‌آموزی","grade":"پایه","class_name":"کلاس","phone":"تلفن",
    "parent_phone":"تلفن ولی","subject":"درس","status":"وضعیت","description":"توضیحات",
    "score":"نمره","exam_name":"عنوان ارزشیابی","date":"تاریخ","title":"عنوان",
    "teacher":"دبیر","student_id":"دانش‌آموز","teacher_id":"دبیر","attendance_date":"تاریخ حضور",
    "payment_status":"وضعیت پرداخت","amount":"مبلغ","operation_type":"نوع عملیات",
}

def title_label(text, size="20sp"):
    w = Label(text=rtl_text(text), font_name=font_name(), font_size=size,
              color=WHITE, bold=True, halign="center", valign="middle")
    w.bind(size=lambda o, v: setattr(o, "text_size", v))
    return w

def make_button(text, callback, height=dp(48), color=BLUE):
    b = Button(text=rtl_text(text), font_name=font_name(), font_size="13sp",
               color=WHITE, size_hint_y=None, height=height,
               background_normal="", background_color=color)
    b.bind(on_release=callback)
    return b

class CleanDashboardScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        header = BoxLayout(size_hint_y=None, height=dp(68), padding=dp(8))
        with header.canvas.before:
            Color(*NAVY); header.bg = RoundedRectangle(pos=header.pos, size=header.size, radius=[dp(14)])
        header.bind(pos=lambda o,v:setattr(header.bg,"pos",v), size=lambda o,v:setattr(header.bg,"size",v))
        header.add_widget(title_label("فراهوش | داشبورد", "20sp"))
        root.add_widget(header)
        root.add_widget(Label(text=rtl_text("پنل موردنظر را انتخاب کنید"), font_name=font_name(),
                              font_size="12sp", color=NAVY, size_hint_y=None, height=dp(32)))
        sc = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=2, spacing=dp(8), padding=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for text, route in PANELS:
            grid.add_widget(make_button(text, lambda *_a, r=route: self.open_panel(r), dp(56)))
        sc.add_widget(grid); root.add_widget(sc)
        self.add_widget(root)

    def open_panel(self, route):
        app = App.get_running_app()
        if app and app.open_clean_panel(route):
            return
        print("CLEAN DASHBOARD ROUTE ERROR:", route)

class CleanPanelScreen(Screen):
    def __init__(self, app_state=None, route="management", **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.route = route
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        header = BoxLayout(size_hint_y=None, height=dp(64), padding=dp(6))
        with header.canvas.before:
            Color(*NAVY); header.bg = RoundedRectangle(pos=header.pos, size=header.size, radius=[dp(14)])
        header.bind(pos=lambda o,v:setattr(header.bg,"pos",v), size=lambda o,v:setattr(header.bg,"size",v))
        back = make_button("‹ بازگشت", lambda *_: self.go_back(), dp(46), BLUE)
        header.add_widget(back); header.add_widget(title_label("پنل " + next((x for x,y in PANELS if y==self.route), self.route), "18sp"))
        root.add_widget(header)
        self.area = BoxLayout(orientation="vertical", spacing=dp(8))
        root.add_widget(self.area)
        self.add_widget(root)
        self.show_menu()

    def show_menu(self):
        self.area.clear_widgets()
        items = ROLE_MENUS.get(self.route, [(x,x) for x in PANELS])
        sc = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=2, spacing=dp(8), padding=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for text, key in items:
            grid.add_widget(make_button(text, lambda *_a,k=key: self.open_module(k), dp(58), GREEN))
        sc.add_widget(grid); self.area.add_widget(sc)

    def open_module(self, table):
        self.area.clear_widgets()
        self.area.add_widget(CleanModuleScreen(self.app_state, table=table, on_back=self.show_menu))

    def go_back(self):
        app = App.get_running_app()
        if app and app.sm: app.sm.current = "clean_dashboard"

class CleanModuleScreen(BoxLayout):
    def __init__(self, app_state, table, on_back=None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(7), **kwargs)
        self.app_state = app_state
        self.table = table
        self.on_back = on_back
        self.status = Label(text=rtl_text("در حال بارگذاری اطلاعات واقعی..."), font_name=font_name(),
                            font_size="11sp", color=NAVY, size_hint_y=None, height=dp(30))
        self.add_widget(self.status)
        bar = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        bar.add_widget(make_button("بازگشت", lambda *_: self.on_back() if self.on_back else None, dp(42), BLUE))
        bar.add_widget(make_button("تازه‌سازی", lambda *_: self.load(), dp(42), GREEN))
        self.add_widget(bar)
        self.scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        self.rows = BoxLayout(orientation="vertical", size_hint=(None,None), spacing=dp(4), padding=dp(4))
        self.rows.bind(minimum_height=self.rows.setter("height"))
        self.scroll.add_widget(self.rows); self.add_widget(self.scroll)
        Clock.schedule_once(lambda *_: self.load(), 0)

    def load(self):
        self.status.text = rtl_text("در حال خواندن " + LABELS.get(self.table, self.table) + " ...")
        if not self.app_state or not getattr(self.app_state, "api", None):
            self.status.text = rtl_text("اتصال داده هنوز آماده نیست.")
            return
        def work():
            try:
                data = self.app_state.api.table_select(self.table, {"limit":"100"}) or []
                Clock.schedule_once(lambda *_: self.render(data), 0)
            except Exception as exc:
                print("CLEAN MODULE LOAD ERROR:", repr(exc))
                Clock.schedule_once(lambda *_: self.fail(), 0)
        Thread(target=work, daemon=True).start()

    def render(self, data):
        self.rows.clear_widgets()
        fields = TABLE_FIELDS.get(self.table) or (list(data[0].keys()) if data else ["id","title","status"])
        header = BoxLayout(size_hint=(None,None), width=max(dp(920), dp(155)*len(fields)), height=dp(46), spacing=dp(2))
        for f in fields:
            header.add_widget(Label(text=rtl_text(LABELS.get(f,f)), font_name=font_name(), font_size="12sp",
                                    color=WHITE, bold=True, size_hint=(None,1), width=dp(150)))
        self.rows.add_widget(header)
        for row in data:
            line = BoxLayout(size_hint=(None,None), width=header.width, height=dp(62), spacing=dp(2))
            for f in fields:
                value = str(row.get(f, "") or "—")
                line.add_widget(Label(text=rtl_text(value), font_name=font_name(), font_size="12sp",
                                      color=NAVY, halign="center", valign="middle",
                                      size_hint=(None,1), width=dp(150)))
            self.rows.add_widget(line)
        self.status.text = rtl_text("تعداد رکوردها: " + str(len(data)))

    def fail(self):
        self.rows.clear_widgets()
        self.status.text = rtl_text("خطا در دریافت اطلاعات؛ جزئیات در گزارش برنامه ثبت شد.")

