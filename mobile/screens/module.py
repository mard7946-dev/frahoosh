from threading import Thread

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

from mobile.config import APP_NAME, CARD, PRIMARY, SCHOOL_NAME, SCHOOL_YEAR, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

# Every module is backed by real tables already used by the application API.
MODULES = {
    "management": ("مدیریت مدرسه", "school_profile", ["students", "teachers", "school_class_config", "staff", "school_events", "users"]),
    "educational": ("معاونت آموزشی", "teacher_classes", ["teacher_classes", "lesson_plans", "attendance", "grades", "assignments"]),
    "executive": ("معاونت اجرایی", "students", ["students", "parents", "staff", "attendance", "school_events"]),
    "cultural": ("معاونت پرورشی", "educational_activities", ["educational_activities", "school_events", "students", "messages"]),
    "advisor": ("مشاوره", "counseling_records", ["counseling_records", "counseling_followups", "students"]),
    "teachers": ("دبیران", "teachers", ["teachers", "teacher_classes", "staff"]),
    "students": ("دانش‌آموزان", "students", ["students", "student_grades", "attendance", "assignments"]),
    "parents": ("اولیا", "parents", ["parent_children", "parents", "parent_meetings", "students"]),
    "finance": ("مالی", "finance_accounts", ["finance_accounts", "finance_transactions", "finance_donations", "payment_records"]),
    "payment": ("پرداخت آنلاین", "payment_records", ["payment_offers", "payment_attempts", "payment_records"]),
    "online": ("کلاس‌های آنلاین", "online_classes", ["online_classes", "online_class_sessions", "online_class_students", "online_class_teachers"]),
    "smart_board": ("تابلو هوشمند", "smart_board_content", ["smart_board_content", "smart_board_activities", "smart_board_quizzes", "smart_board_whiteboards"]),
    "ai": ("دستیار هوش مصنوعی", "ai_questions", ["ai_assistant_sessions", "ai_questions", "ai_smart_reports"]),
    "messages": ("صندوق پیام‌ها", "messages", ["messages", "message_targets", "message_reads"]),
    "settings": ("تنظیمات", "account_settings", ["account_settings", "school_profile", "school_class_config"]),
    "reports": ("گزارش‌ها", "report_cards", ["report_cards", "report_card_snapshots", "grades", "attendance", "student_grades"]),
    "schedule": ("برنامه هفتگی", "weekly_schedule", ["weekly_schedule", "generated_weekly_schedule", "exam_schedule"]),
    "student_info": ("وضعیت تحصیلی", "students", ["students", "grades", "student_grades", "attendance", "assignments", "report_cards"]),
}

FRIENDLY = {
    "school_profile":"مشخصات مدرسه", "school_class_config":"ساختار کلاس‌ها", "users":"حساب‌های سامانه",
    "students":"دانش‌آموزان", "teachers":"دبیران", "staff":"کارکنان", "teacher_classes":"کلاس‌های دبیران",
    "lesson_plans":"طرح درس‌ها", "attendance":"حضور و غیاب", "grades":"نمرات", "student_grades":"ارزیابی دانش‌آموزان",
    "assignments":"تکالیف", "parents":"اولیا", "parent_children":"ارتباط ولی و فرزند", "parent_meetings":"جلسات اولیا",
    "finance_accounts":"حساب‌های مالی", "finance_transactions":"تراکنش‌های مالی", "finance_donations":"کمک‌های داوطلبانه",
    "payment_offers":"تعریف پرداخت", "payment_attempts":"درخواست‌های پرداخت", "payment_records":"سوابق پرداخت",
    "online_classes":"کلاس‌های آنلاین", "online_class_sessions":"جلسات آنلاین", "online_class_students":"دانش‌آموزان کلاس",
    "online_class_teachers":"دبیران کلاس", "educational_activities":"فعالیت‌های پرورشی", "school_events":"رویدادهای مدرسه",
    "counseling_records":"سوابق مشاوره", "counseling_followups":"پیگیری مشاوره", "smart_board_content":"محتوای تابلو",
    "smart_board_activities":"فعالیت‌های تابلو", "smart_board_quizzes":"آزمون‌های کوتاه", "smart_board_whiteboards":"تخته‌های آموزشی",
    "ai_assistant_sessions":"جلسات دستیار", "ai_questions":"پرسش‌های هوشمند", "ai_smart_reports":"گزارش‌های هوشمند",
    "messages":"پیام‌ها", "message_targets":"مخاطبان پیام", "message_reads":"وضعیت خواندن", "report_cards":"کارنامه‌ها",
    "report_card_snapshots":"نسخه‌های کارنامه", "weekly_schedule":"برنامه هفتگی", "generated_weekly_schedule":"برنامه تولیدشده",
    "exam_schedule":"برنامه امتحانات", "account_settings":"تنظیمات حساب",
}

COLUMNS = {
    "id":"شناسه", "first_name":"نام", "last_name":"نام خانوادگی", "national_code":"کد ملی", "grade":"پایه", "class_name":"کلاس",
    "phone":"تلفن", "subject":"درس", "teacher_name":"دبیر", "score":"نمره", "max_score":"حداکثر", "status":"وضعیت",
    "amount":"مبلغ", "title":"عنوان", "description":"توضیحات", "created_at":"تاریخ ثبت", "attendance_date":"تاریخ حضور",
    "exam_date":"تاریخ آزمون", "event_date":"تاریخ رویداد", "start_time_shamsi":"شروع", "end_time_shamsi":"پایان",
    "role":"نقش", "email":"ایمیل", "username":"نام کاربری", "term":"نوبت", "academic_year":"سال تحصیلی", "active":"فعال",
}

EDITABLE = {
    "manager":{"students","teachers","staff","school_profile","school_class_config","school_events","lesson_plans","weekly_schedule","generated_weekly_schedule","exam_schedule"},
    "educational":{"teacher_classes","lesson_plans","attendance","grades","student_grades","assignments","weekly_schedule","generated_weekly_schedule","exam_schedule"},
    "executive":{"students","parents","staff","attendance","school_events"},
    "cultural":{"educational_activities","school_events"},
    "advisor":{"counseling_records","counseling_followups"},
    "teacher":{"attendance","grades","student_grades","assignments","lesson_plans"},
}

FORMS = {
    "students":["first_name","last_name","national_code","grade","class_name","phone"],
    "school_events":["title","description","event_date","status"],
    "lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title","session_date"],
    "assignments":["student_id","teacher_id","title","subject","class_name","status","due_date"],
    "attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],
    "grades":["student_id","teacher_id","subject","exam_name","score","max_score","grade_type","term","grade_date"],
}

DESCRIPTIONS = {
    "students":"پرونده زنده دانش‌آموزان و اطلاعات پایه آن‌ها", "teachers":"اطلاعات و پرونده دبیران مدرسه", "attendance":"ثبت و پایش حضور و غیاب",
    "grades":"ثبت و مشاهده نمرات واقعی", "assignments":"مدیریت تکالیف و وضعیت انجام آن‌ها", "lesson_plans":"طرح درس و برنامه آموزشی",
    "school_events":"رویدادها و مناسبت‌های مدرسه", "parents":"اطلاعات خانواده و اولیا", "finance_transactions":"گردش واقعی حساب‌های مالی",
    "payment_records":"سوابق واقعی پرداخت‌های ثبت‌شده", "online_classes":"کلاس‌ها و جلسات آنلاین", "messages":"صندوق ارتباطات سامانه",
    "report_cards":"کارنامه‌ها و سوابق ارزیابی", "weekly_schedule":"برنامه هفتگی مدرسه", "exam_schedule":"برنامه امتحانات",
}

class Surface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(14), dp(12)], spacing=dp(7), size_hint_y=None, **kwargs)
        with self.canvas.before:
            Color(*CARD)
            self.bg = RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self.sync, size=self.sync)
    def sync(self, *_):
        self.bg.pos, self.bg.size = self.pos, self.size

class ModuleScreen(Screen):
    """Real module workspace. No mock KPI/data is generated; all displayed records come from ApiClient."""
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.module_key = "management"
        self.return_to = "dashboard"
        self.cache = {}
        self.active_table = None
        self._build()

    def lbl(self, text, size="12sp", color=SECONDARY, bold=False, align="right"):
        w = Label(text=rtl_text(str(text)), font_name=font_name(), font_size=size, color=color, bold=bold, halign=align, valign="middle")
        w.bind(size=lambda o,v:setattr(o,"text_size",v))
        return w

    def btn(self, text, callback, color=PRIMARY, h=dp(44)):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="12sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=h)
        b.bind(on_release=callback)
        return b

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(7))
        head=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(7))
        head.add_widget(self.btn("‹ بازگشت",self.go_back,PRIMARY,dp(78)))
        self.title=self.lbl(APP_NAME,"20sp",PRIMARY,True,"center"); head.add_widget(self.title)
        head.add_widget(self.btn("⌂",self.go_dashboard,PRIMARY,dp(48)))
        root.add_widget(head)
        self.sub=self.lbl(SCHOOL_NAME+"  |  "+SCHOOL_YEAR,"9sp",SECONDARY,False,"center"); root.add_widget(self.sub)
        self.body=BoxLayout(orientation="vertical",spacing=dp(7)); root.add_widget(self.body); self.add_widget(root)

    def set_module(self,key,return_to="dashboard"):
        self.module_key=key if key in MODULES else "management"; self.return_to=return_to or "dashboard"; self.cache={}; self.active_table=None; self.render_workspace()
    load_module=set_module

    def clear(self): self.body.clear_widgets()

    def render_workspace(self):
        self.clear(); title, primary, tables=MODULES[self.module_key]; self.title.text=rtl_text(title)
        role=str(getattr(self.app_state,"role","student") or "student").lower()
        user=str(getattr(self.app_state,"display_name","کاربر فراهوش") or "کاربر فراهوش")
        hero=Surface(height=dp(128))
        line=BoxLayout(size_hint_y=None,height=dp(25)); line.add_widget(self.lbl("FRAHOOSH  /  WORKSPACE","9sp",PRIMARY,True)); line.add_widget(self.lbl("● اتصال فعال","9sp",SUCCESS,True,"center")); hero.add_widget(line)
        hero.add_widget(self.lbl(title,"23sp",PRIMARY,True,"center")); hero.add_widget(self.lbl("محیط عملیاتی اختصاصی  |  "+user+"  |  نقش: "+role,"9sp",SECONDARY,False,"center")); self.body.add_widget(hero)
        self.render_kpis(tables)
        actions=Surface(height=dp(84)); actions.add_widget(self.lbl("دسترسی سریع","13sp",PRIMARY,True))
        row=BoxLayout(spacing=dp(7));
        for t in tables[:3]: row.add_widget(self.btn(FRIENDLY.get(t,t),lambda *_a,x=t:self.open_table(x),PRIMARY,dp(38)))
        actions.add_widget(row); self.body.add_widget(actions)
        self.render_tables(tables)

    def render_kpis(self,tables):
        box=BoxLayout(size_hint_y=None,height=dp(88),spacing=dp(7))
        for t in tables[:4]:
            c=Surface(height=dp(82),padding=[dp(8),dp(6)],spacing=dp(2)); c.add_widget(self.lbl(FRIENDLY.get(t,t),"9sp",SECONDARY,False,"center")); val=self.lbl("…","22sp",PRIMARY,True,"center"); c.add_widget(val); c.add_widget(self.lbl("رکورد واقعی دریافت‌شده","8sp",SECONDARY,False,"center")); box.add_widget(c); self._load_kpi(t,val)
        self.body.add_widget(box)

    def _load_kpi(self,table,label):
        def work():
            try:
                rows=self.app_state.api.table_select(table,{"limit":"80"}); self.cache[table]=rows if isinstance(rows,list) else []
                n=len(self.cache[table]); Clock.schedule_once(lambda *_:setattr(label,"text",rtl_text(str(n))),0)
            except Exception:
                Clock.schedule_once(lambda *_:setattr(label,"text",rtl_text("—")),0)
        Thread(target=work,daemon=True).start()

    def render_tables(self,tables):
        box=BoxLayout(orientation="vertical",spacing=dp(5))
        top=BoxLayout(size_hint_y=None,height=dp(32)); top.add_widget(self.lbl("داده‌های زنده این پنل","13sp",PRIMARY,True)); top.add_widget(self.lbl("برای مشاهده جزئیات، بخش را انتخاب کنید","8sp",SECONDARY,False,"center")); box.add_widget(top)
        scroll=ScrollView(do_scroll_x=False); grid=GridLayout(cols=1,spacing=dp(7),padding=[dp(2),dp(2),dp(2),dp(10)],size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        for i,t in enumerate(tables,1):
            c=Surface(height=dp(72),padding=[dp(10),dp(8)],spacing=dp(4)); r=BoxLayout(spacing=dp(7)); r.add_widget(self.lbl("%02d"%i,"11sp",PRIMARY,True,"center")); r.add_widget(self.lbl(FRIENDLY.get(t,t),"12sp",PRIMARY,True)); r.add_widget(self.lbl(DESCRIPTIONS.get(t,"اطلاعات عملیاتی متصل به سامانه"),"8sp",SECONDARY,False,"center")); r.add_widget(self.btn("مشاهده ›",lambda *_a,x=t:self.open_table(x),PRIMARY,dp(75))); c.add_widget(r); grid.add_widget(c)
        scroll.add_widget(grid); box.add_widget(scroll); self.body.add_widget(box)

    def open_table(self,table):
        self.active_table=table; self.clear();
        top=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(7)); top.add_widget(self.btn("‹ پنل",lambda *_:self.render_workspace(),PRIMARY,dp(72))); top.add_widget(self.lbl(FRIENDLY.get(table,table),"18sp",PRIMARY,True)); top.add_widget(self.btn("↻",lambda *_:self.open_table(table),PRIMARY,dp(45))); self.body.add_widget(top)
        wait=Surface(height=dp(120)); wait.add_widget(self.lbl("در حال دریافت اطلاعات واقعی...","16sp",PRIMARY,True,"center")); wait.add_widget(self.lbl("اتصال مستقیم به سرویس داده فراهوش","9sp",SECONDARY,False,"center")); self.body.add_widget(wait)
        Thread(target=self.fetch,args=(table,),daemon=True).start()

    def fetch(self,table):
        try:
            rows=self.app_state.api.table_select(table,{"limit":"80"}); rows=rows if isinstance(rows,list) else []
            Clock.schedule_once(lambda *_:self.show_table(table,rows),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self.show_error(table,str(exc)),0)

    def show_error(self,table,error):
        self.clear(); self.body.add_widget(self.lbl(FRIENDLY.get(table,table),"18sp",PRIMARY,True,"center")); self.body.add_widget(self.lbl("اتصال به این جدول برقرار نشد:\n"+error,"11sp",SECONDARY,False,"center")); self.body.add_widget(self.btn("↻ تلاش دوباره",lambda *_:self.open_table(table),PRIMARY,dp(44))); self.body.add_widget(self.btn("‹ بازگشت",lambda *_:self.render_workspace(),SECONDARY,dp(44)))

    def show_table(self,table,rows):
        self.clear(); head=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(7)); head.add_widget(self.btn("‹ پنل",lambda *_:self.render_workspace(),PRIMARY,dp(72))); head.add_widget(self.lbl(FRIENDLY.get(table,table),"17sp",PRIMARY,True)); head.add_widget(self.lbl(str(len(rows))+" رکورد دریافت شد","9sp",SUCCESS,True,"center")); head.add_widget(self.btn("↻",lambda *_:self.open_table(table),PRIMARY,dp(45))); self.body.add_widget(head)
        search=TextInput(hint_text=rtl_text("جستجو در داده‌های این بخش..."),font_name=font_name(),halign="right",multiline=False,size_hint_y=None,height=dp(40),padding=[dp(10),dp(8)]); self.body.add_widget(search)
        scroll=ScrollView(do_scroll_x=False); grid=GridLayout(cols=1,spacing=dp(7),size_hint_y=None,padding=[dp(2),dp(2)]); grid.bind(minimum_height=grid.setter("height"))
        def redraw(*_):
            grid.clear_widgets(); q=search.text.strip().lower()
            shown=0
            for row in rows:
                if not isinstance(row,dict): continue
                text=" | ".join(str(v) for v in row.values() if v not in (None,""))
                if q and q not in text.lower(): continue
                c=Surface(height=dp(92)); keys=[k for k in ["first_name","last_name","title","subject","grade","class_name","status","score","amount","created_at","event_date"] if k in row]
                keys=keys[:6] or list(row.keys())[:6]
                c.add_widget(self.lbl("  •  ".join(COLUMNS.get(k,k)+": "+str(row.get(k)) for k in keys),"10sp",PRIMARY,True))
                role=str(getattr(self.app_state,"role","student") or "student").lower()
                if table in EDITABLE.get(role,set()) and row.get("id") is not None: c.add_widget(self.btn("حذف رکورد","",SECONDARY,dp(28)))
                grid.add_widget(c); shown+=1
            if shown==0: grid.add_widget(self.lbl("رکوردی مطابق جستجو پیدا نشد.","11sp",SECONDARY,False,"center"))
        # Bind search without requiring a KV file; all rendering stays in Kivy Python.
        search.bind(text=redraw); scroll.add_widget(grid); self.body.add_widget(scroll); redraw()
        role=str(getattr(self.app_state,"role","student") or "student").lower()
        if table in EDITABLE.get(role,set()) and table in FORMS: self.body.add_widget(self.btn("＋ ثبت اطلاعات جدید",lambda *_:self.new_form(table),SUCCESS,dp(45)))

    def new_form(self,table):
        self.clear(); self.body.add_widget(self.lbl("ثبت اطلاعات | "+FRIENDLY.get(table,table),"18sp",PRIMARY,True,"center")); scroll=ScrollView(do_scroll_x=False); box=BoxLayout(orientation="vertical",spacing=dp(7),padding=dp(3),size_hint_y=None); box.bind(minimum_height=box.setter("height")); fields={}
        for key in FORMS.get(table,[]):
            inp=TextInput(hint_text=rtl_text(COLUMNS.get(key,key)),font_name=font_name(),halign="right",multiline=False,size_hint_y=None,height=dp(42),padding=[dp(10),dp(8)]); fields[key]=inp; box.add_widget(inp)
        box.add_widget(self.btn("ثبت در سامانه",lambda *_:self.insert(table,fields),SUCCESS,dp(46))); box.add_widget(self.btn("‹ بازگشت",lambda *_:self.open_table(table),PRIMARY,dp(44))); scroll.add_widget(box); self.body.add_widget(scroll)

    def insert(self,table,fields):
        payload={k:v.text.strip() for k,v in fields.items() if v.text.strip()}
        if not payload:return
        self.clear(); self.body.add_widget(self.lbl("در حال ثبت اطلاعات در سامانه...","15sp",PRIMARY,True,"center"));
        def work():
            try:self.app_state.api.table_insert(table,payload); Clock.schedule_once(lambda *_:self.open_table(table),0)
            except Exception as exc:Clock.schedule_once(lambda *_:self.show_error(table,str(exc)),0)
        Thread(target=work,daemon=True).start()

    def go_dashboard(self,*_):
        if self.manager:self.manager.current="dashboard"
    def go_back(self,*_):
        if self.manager:self.manager.current=self.return_to if self.manager.has_screen(self.return_to) else "dashboard"
