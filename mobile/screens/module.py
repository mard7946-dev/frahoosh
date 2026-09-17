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

MODULE_TITLES = {
    "management":"مدیریت", "educational":"معاون آموزشی", "executive":"معاون اجرایی", "cultural":"معاون پرورشی",
    "advisor":"مشاوره", "teachers":"دبیران", "students":"دانش‌آموزان", "parents":"اولیا", "finance":"مالی",
    "payment":"پرداخت آنلاین", "online":"کلاس‌های آنلاین", "smart_board":"تابلو هوشمند", "ai":"دستیار هوش مصنوعی",
    "messages":"صندوق پیام‌ها", "settings":"تنظیمات", "reports":"گزارش‌ها", "schedule":"برنامه هفتگی", "student_info":"وضعیت تحصیلی",
}

MODULE_TABLES = {
    "management":["school_profile","school_class_config","students","teachers","staff","users"],
    "educational":["teacher_classes","lesson_plans","attendance","grades","assignments"],
    "executive":["students","parents","staff","attendance","school_events"],
    "cultural":["educational_activities","school_events","students","messages"],
    "advisor":["counseling_records","counseling_followups","students"],
    "teachers":["teachers","staff","teacher_classes"],
    "students":["students","student_grades","attendance","assignments"],
    "parents":["parent_children","parents","parent_meetings","students"],
    "finance":["finance_accounts","finance_transactions","finance_donations","payment_records"],
    "payment":["payment_offers","payment_attempts","payment_records"],
    "online":["online_classes","online_class_sessions","online_class_students","online_class_teachers"],
    "smart_board":["smart_board_content","smart_board_activities","smart_board_quizzes","smart_board_whiteboards"],
    "ai":["ai_assistant_sessions","ai_questions","ai_smart_reports"],
    "messages":["messages","message_targets","message_reads"],
    "settings":["account_settings","school_profile","school_class_config"],
    "reports":["report_cards","report_card_snapshots","grades","attendance","student_grades"],
    "schedule":["weekly_schedule","generated_weekly_schedule","exam_schedule"],
    "student_info":["students","grades","student_grades","attendance","assignments","report_cards"],
}

FRIENDLY = {
    "school_profile":"مشخصات مدرسه","school_class_config":"تنظیمات کلاس‌ها","users":"حساب‌های سامانه","students":"دانش‌آموزان",
    "teachers":"دبیران","staff":"کارکنان","teacher_classes":"کلاس‌های دبیر","lesson_plans":"طرح درس‌ها","grades":"نمرات",
    "student_grades":"ارزیابی‌های دانش‌آموز","attendance":"حضور و غیاب","assignments":"تکالیف","parent_children":"ارتباط ولی و فرزند",
    "parent_meetings":"جلسات اولیا","parents":"اولیا","payment_offers":"گزینه‌های پرداخت","payment_attempts":"درخواست‌های پرداخت",
    "payment_records":"سوابق پرداخت","online_classes":"کلاس‌های آنلاین","online_class_sessions":"جلسات کلاس آنلاین",
    "online_class_students":"دانش‌آموزان کلاس آنلاین","online_class_teachers":"دبیران کلاس آنلاین","messages":"پیام‌ها",
    "message_targets":"مخاطبان پیام","message_reads":"وضعیت خواندن پیام","report_cards":"کارنامه‌ها","report_card_snapshots":"نسخه‌های کارنامه",
    "weekly_schedule":"برنامه هفتگی","generated_weekly_schedule":"برنامه تولیدشده","exam_schedule":"برنامه امتحانات",
    "account_settings":"تنظیمات حساب","finance_accounts":"حساب‌های مالی","finance_transactions":"تراکنش‌های مالی",
    "finance_donations":"کمک‌های داوطلبانه","educational_activities":"فعالیت‌های پرورشی","school_events":"رویدادهای مدرسه",
    "counseling_records":"سوابق مشاوره","counseling_followups":"پیگیری‌های مشاوره","smart_board_content":"محتوای تابلو",
    "smart_board_activities":"فعالیت‌های تابلو","smart_board_quizzes":"آزمون‌های کوتاه","smart_board_whiteboards":"تخته‌های کلاس",
    "ai_assistant_sessions":"جلسات دستیار هوشمند","ai_questions":"پرسش‌های هوش مصنوعی","ai_smart_reports":"گزارش‌های هوشمند",
}

COLUMNS = {
    "id":"شناسه","first_name":"نام","last_name":"نام خانوادگی","national_code":"کد ملی","grade":"پایه","class_name":"کلاس",
    "phone":"تلفن","subject":"درس","teacher_name":"دبیر","score":"نمره","max_score":"از","status":"وضعیت","amount":"مبلغ",
    "title":"عنوان","description":"توضیحات","created_at":"تاریخ ثبت","attendance_date":"تاریخ حضور","exam_date":"تاریخ آزمون",
    "start_time_shamsi":"شروع","end_time_shamsi":"پایان","payment_reason":"علت پرداخت","active":"فعال","role":"نقش",
    "email":"ایمیل","username":"نام کاربری","term":"نوبت","academic_year":"سال تحصیلی","event_date":"تاریخ رویداد",
}

EDITABLE = {
    "manager":{"students","teachers","staff","school_profile","school_class_config","school_events","lesson_plans","weekly_schedule","generated_weekly_schedule","exam_schedule"},
    "educational":{"teacher_classes","lesson_plans","attendance","teacher_attendance","grades","student_grades","assignments","weekly_schedule","generated_weekly_schedule","exam_schedule"},
    "executive":{"students","parents","staff","attendance","school_events"},
    "cultural":{"educational_activities","school_events"}, "advisor":{"counseling_records","counseling_followups"},
    "teacher":{"attendance","teacher_attendance","grades","student_grades","assignments","lesson_plans"},
}

FORM_FIELDS = {
    "students":["first_name","last_name","national_code","grade","class_name","phone"],
    "teachers":["first_name","last_name","national_code","subject","grades","employment_status"],
    "attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],
    "grades":["student_id","teacher_id","subject","exam_name","score","max_score","grade_type","term","grade_date"],
    "assignments":["student_id","teacher_id","title","subject","class_name","status","due_date"],
    "lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title","session_date"],
    "school_events":["title","description","event_date","status"],
}

ICONS = {"school_profile":"مدرسه","school_class_config":"کلاس‌ها","students":"دانش‌آموزان","teachers":"دبیران","staff":"کارکنان",
         "grades":"نمرات","student_grades":"ارزیابی","attendance":"حضور","assignments":"تکالیف","lesson_plans":"طرح درس",
         "parents":"اولیا","parent_children":"فرزندان","parent_meetings":"جلسات","payment_records":"سوابق پرداخت","payment_offers":"تعریف پرداخت",
         "finance_accounts":"حساب‌ها","finance_transactions":"تراکنش‌ها","finance_donations":"کمک‌ها","online_classes":"کلاس‌ها",
         "online_class_sessions":"جلسات","online_class_students":"دانش‌آموزان","online_class_teachers":"دبیران","messages":"پیام‌ها",
         "report_cards":"کارنامه","report_card_snapshots":"نسخه‌ها","weekly_schedule":"برنامه","generated_weekly_schedule":"برنامه تولیدشده",
         "exam_schedule":"امتحانات","smart_board_content":"محتوا","smart_board_activities":"فعالیت‌ها","smart_board_quizzes":"آزمون کوتاه",
         "smart_board_whiteboards":"تخته","ai_assistant_sessions":"جلسات","ai_questions":"پرسش‌ها","ai_smart_reports":"گزارش‌ها"}

class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(15),dp(12)], spacing=dp(7), size_hint_y=None, **kwargs)
        with self.canvas.before:
            Color(*CARD); self.bg = RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self._sync, size=self._sync)
    def _sync(self, *_): self.bg.pos=self.pos; self.bg.size=self.size

class ModuleScreen(Screen):
    """Professional module landing page + live Supabase/SQLite table viewer.
    Login/dashboard are intentionally untouched. Every function card opens the real
    data table already connected through AppState.api.
    """
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.module_key=""; self.return_to="dashboard"; self.active_table=None; self._build()

    def label(self, text, size="13sp", color=SECONDARY, bold=False, align="right"):
        w=Label(text=rtl_text(str(text)), font_name=font_name(), font_size=size, color=color, bold=bold, halign=align, valign="middle")
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def button(self, text, action, color=PRIMARY, height=dp(46)):
        b=Button(text=rtl_text(text), font_name=font_name(), font_size="12sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=height)
        b.bind(on_release=action); return b

    def _build(self):
        root=BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(9))
        head=BoxLayout(size_hint_y=None,height=dp(55),spacing=dp(8))
        head.add_widget(self.button("‹ بازگشت", self.go_back, PRIMARY, dp(46)))
        self.title=self.label(APP_NAME,"20sp",PRIMARY,True); head.add_widget(self.title); root.add_widget(head)
        self.sub=self.label(SCHOOL_NAME+"  |  "+SCHOOL_YEAR,"10sp",SECONDARY,False,"center"); root.add_widget(self.sub)
        self.body=BoxLayout(orientation="vertical",spacing=dp(8)); root.add_widget(self.body); self.add_widget(root)

    def set_module(self,key,return_to="dashboard"):
        self.return_to=return_to or "dashboard"; self.show_module(key)
    def load_module(self,key,return_to="dashboard"): self.set_module(key,return_to)

    def show_module(self,key):
        self.module_key=key or "management"; self.active_table=None; self.title.text=rtl_text(MODULE_TITLES.get(self.module_key,self.module_key)); self._render_landing()

    def _clear(self): self.body.clear_widgets()

    def _render_landing(self):
        self._clear(); tables=MODULE_TABLES.get(self.module_key,[])
        hero=Card(height=dp(105)); hero.add_widget(self.label("محیط عملیاتی "+MODULE_TITLES.get(self.module_key,self.module_key),"18sp",PRIMARY,True,"center"))
        hero.add_widget(self.label("زیرعملکرد موردنظر را انتخاب کنید؛ اطلاعات مستقیماً از اتصال سامانه نمایش داده می‌شود.","11sp",SECONDARY,False,"center")); self.body.add_widget(hero)
        scroll=ScrollView(do_scroll_x=False); grid=GridLayout(cols=1, spacing=dp(9), padding=[dp(2),dp(2)], size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        role=str(getattr(self.app_state,"role","student") or "student").lower(); editable=EDITABLE.get(role,set())
        for table in tables:
            card=Card(height=dp(88)); row=BoxLayout(spacing=dp(10))
            info=BoxLayout(orientation="vertical",spacing=dp(2)); info.add_widget(self.label(ICONS.get(table,"اطلاعات"),"16sp",PRIMARY,True)); info.add_widget(self.label(FRIENDLY.get(table,table),"10sp",SECONDARY)); row.add_widget(info)
            if table in editable:
                row.add_widget(self.label("قابل ویرایش","10sp",SUCCESS,True,"center"))
            card.add_widget(row); card.add_widget(self.button("مشاهده و مدیریت اطلاعات  ›", lambda *_a,t=table:self.open_table(t), PRIMARY, dp(36))); grid.add_widget(card)
        if not tables: grid.add_widget(self.label("برای این پنل هنوز زیرعملکردی تعریف نشده است.","13sp",SECONDARY,False,"center"))
        scroll.add_widget(grid); self.body.add_widget(scroll)

    def open_table(self,table):
        self.active_table=table; self._render_table_loading(); Thread(target=self._fetch_table,args=(table,),daemon=True).start()
    def _render_table_loading(self):
        self._clear(); self.body.add_widget(self.label("در حال دریافت اطلاعات…","14sp",SECONDARY,True,"center"))
    def _fetch_table(self,table):
        try:
            rows=self.app_state.api.table_select(table,{"limit":"80"})
            if not isinstance(rows,list): rows=[]
            Clock.schedule_once(lambda *_:self._render_table(table,rows),0)
        except Exception as exc:
            Clock.schedule_once(lambda *_:self._render_error(table,str(exc)),0)

    def _render_error(self,table,error):
        self._clear(); self.body.add_widget(self.label(FRIENDLY.get(table,table),"18sp",PRIMARY,True,"center")); self.body.add_widget(self.label("دریافت اطلاعات انجام نشد: "+error,"12sp",SECONDARY,False,"center")); self.body.add_widget(self.button("↻ تلاش دوباره",lambda *_:self.open_table(table),PRIMARY,dp(44))); self.body.add_widget(self.button("‹ بازگشت به زیرعملکردها",lambda *_:self._render_landing(),SECONDARY,dp(44)))

    def _render_table(self,table,rows):
        self._clear(); head=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(7)); head.add_widget(self.button("‹ پنل",lambda *_:self._render_landing(),PRIMARY,dp(82))); head.add_widget(self.label(FRIENDLY.get(table,table),"17sp",PRIMARY,True)); head.add_widget(self.button("↻",lambda *_:self.open_table(table),PRIMARY,dp(45))); self.body.add_widget(head)
        self.body.add_widget(self.label(f"{len(rows)} مورد نمایش داده شد","10sp",SECONDARY,False,"center"))
        scroll=ScrollView(do_scroll_x=False); grid=GridLayout(cols=1,spacing=dp(8),padding=[dp(2),dp(2)],size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        if not rows: grid.add_widget(self.label("اطلاعاتی ثبت نشده است.","13sp",SECONDARY,False,"center"))
        for row in rows:
            if not isinstance(row,dict): continue
            card=Card(height=dp(105)); shown=[]
            preferred=["first_name","last_name","title","subject","grade","class_name","status","score","amount","date","created_at"]
            keys=[k for k in preferred if k in row][:5] or list(row.keys())[:5]
            for k in keys:
                value=row.get(k)
                if value in (None,""): continue
                shown.append(f"{COLUMNS.get(k,k)}: {value}")
            card.add_widget(self.label("  |  ".join(shown) or "رکورد بدون اطلاعات نمایشی","11sp",PRIMARY,True,"right"))
            role=str(getattr(self.app_state,"role","student") or "student").lower()
            if table in EDITABLE.get(role,set()) and row.get("id") is not None:
                card.add_widget(self.button("حذف این رکورد",lambda *_r,t=table,i=row.get("id"):self.delete_row(t,i),SECONDARY,dp(32)))
            grid.add_widget(card)
        scroll.add_widget(grid); self.body.add_widget(scroll)
        role=str(getattr(self.app_state,"role","student") or "student").lower()
        if table in EDITABLE.get(role,set()) and table in FORM_FIELDS:
            self.body.add_widget(self.button("＋ ثبت اطلاعات جدید",lambda *_:self._new_form(table),SUCCESS,dp(45)))

    def _new_form(self,table):
        self._clear(); self.body.add_widget(self.label("ثبت "+FRIENDLY.get(table,table),"18sp",PRIMARY,True,"center")); fields={}
        scroll=ScrollView(do_scroll_x=False); box=BoxLayout(orientation="vertical",spacing=dp(7),padding=[dp(3),dp(3)],size_hint_y=None); box.bind(minimum_height=box.setter("height"))
        for key in FORM_FIELDS.get(table,[]):
            inp=TextInput(hint_text=rtl_text(COLUMNS.get(key,key)),font_name=font_name(),multiline=False,halign="right",size_hint_y=None,height=dp(43),padding=[dp(10),dp(8)]); fields[key]=inp; box.add_widget(inp)
        box.add_widget(self.button("ثبت اطلاعات",lambda *_:self._insert(table,fields),SUCCESS,dp(46))); box.add_widget(self.button("‹ بازگشت",lambda *_:self.open_table(table),PRIMARY,dp(44))); scroll.add_widget(box); self.body.add_widget(scroll)

    def _insert(self,table,fields):
        payload={k:v.text.strip() for k,v in fields.items() if v.text.strip()}
        if not payload: return
        self._render_table_loading(); Thread(target=self._do_insert,args=(table,payload),daemon=True).start()
    def _do_insert(self,table,payload):
        try:
            self.app_state.api.table_insert(table,payload); Clock.schedule_once(lambda *_:self.open_table(table),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._render_error(table,str(exc)),0)

    def delete_row(self,table,row_id):
        self._render_table_loading(); Thread(target=self._do_delete,args=(table,row_id),daemon=True).start()
    def _do_delete(self,table,row_id):
        try:
            self.app_state.api.table_delete(table,{"id":"eq."+str(row_id)}); Clock.schedule_once(lambda *_:self.open_table(table),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._render_error(table,str(exc)),0)

    def go_back(self,*_):
        if self.manager: self.manager.current=self.return_to if self.manager.has_screen(self.return_to) else "dashboard"
