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

MODULE_TITLES={"management":"مدیریت","educational":"معاون آموزشی","executive":"معاون اجرایی","cultural":"معاون پرورشی","advisor":"مشاوره","teachers":"دبیران","students":"دانش‌آموزان","parents":"اولیا","finance":"مالی","payment":"پرداخت آنلاین","online":"کلاس‌های آنلاین","smart_board":"تابلو هوشمند","ai":"دستیار هوش مصنوعی","messages":"صندوق پیام‌ها","settings":"تنظیمات","reports":"گزارش‌ها","schedule":"برنامه هفتگی","student_info":"وضعیت تحصیلی"}

MODULE_TABLES={
"management":["school_profile","school_class_config","students","teachers","staff","users"],"educational":["teacher_classes","lesson_plans","attendance","grades","assignments"],"executive":["students","parents","staff","attendance","school_events"],"cultural":["educational_activities","school_events","students","messages"],"advisor":["counseling_records","counseling_followups","students"],"teachers":["teachers","staff","teacher_classes"],"students":["students","student_grades","attendance","assignments"],"parents":["parent_children","parents","parent_meetings","students"],"finance":["finance_accounts","finance_transactions","finance_donations","payment_records"],"payment":["payment_offers","payment_attempts","payment_records"],"online":["online_classes","online_class_sessions","online_class_students","online_class_teachers"],"smart_board":["smart_board_content","smart_board_activities","smart_board_quizzes","smart_board_whiteboards"],"ai":["ai_assistant_sessions","ai_questions","ai_smart_reports"],"messages":["messages","message_targets","message_reads"],"settings":["account_settings","school_profile","school_class_config"],"reports":["report_cards","report_card_snapshots","grades","attendance","student_grades"],"schedule":["weekly_schedule","generated_weekly_schedule","exam_schedule"],"student_info":["students","grades","student_grades","attendance","assignments","report_cards"]}

FRIENDLY={"school_profile":"مشخصات مدرسه","school_class_config":"ساختار کلاس‌ها","users":"حساب‌های سامانه","students":"دانش‌آموزان","teachers":"دبیران","staff":"کارکنان","teacher_classes":"کلاس‌های دبیر","lesson_plans":"طرح درس‌ها","grades":"نمرات","student_grades":"ارزیابی‌ها","attendance":"حضور و غیاب","assignments":"تکالیف","parent_children":"ارتباط ولی و فرزند","parent_meetings":"جلسات اولیا","parents":"اولیا","payment_offers":"گزینه‌های پرداخت","payment_attempts":"درخواست‌های پرداخت","payment_records":"سوابق پرداخت","online_classes":"کلاس‌های آنلاین","online_class_sessions":"جلسات کلاس آنلاین","online_class_students":"دانش‌آموزان کلاس آنلاین","online_class_teachers":"دبیران کلاس آنلاین","messages":"پیام‌ها","message_targets":"مخاطبان پیام","message_reads":"وضعیت خواندن پیام","report_cards":"کارنامه‌ها","report_card_snapshots":"نسخه‌های کارنامه","weekly_schedule":"برنامه هفتگی","generated_weekly_schedule":"برنامه تولیدشده","exam_schedule":"برنامه امتحانات","account_settings":"تنظیمات حساب","finance_accounts":"حساب‌های مالی","finance_transactions":"تراکنش‌های مالی","finance_donations":"کمک‌های داوطلبانه","educational_activities":"فعالیت‌های پرورشی","school_events":"رویدادهای مدرسه","counseling_records":"سوابق مشاوره","counseling_followups":"پیگیری مشاوره","smart_board_content":"محتوای تابلو","smart_board_activities":"فعالیت‌های تابلو","smart_board_quizzes":"آزمون‌های کوتاه","smart_board_whiteboards":"تخته‌های آموزشی","ai_assistant_sessions":"جلسات دستیار هوشمند","ai_questions":"پرسش‌های هوشمند","ai_smart_reports":"گزارش‌های هوشمند"}

COLUMNS={"id":"شناسه","first_name":"نام","last_name":"نام خانوادگی","national_code":"کد ملی","grade":"پایه","class_name":"کلاس","phone":"تلفن","subject":"درس","teacher_name":"دبیر","score":"نمره","max_score":"از","status":"وضعیت","amount":"مبلغ","title":"عنوان","description":"توضیحات","created_at":"تاریخ ثبت","attendance_date":"تاریخ حضور","exam_date":"تاریخ آزمون","start_time_shamsi":"شروع","end_time_shamsi":"پایان","payment_reason":"علت پرداخت","active":"فعال","role":"نقش","email":"ایمیل","username":"نام کاربری","term":"نوبت","academic_year":"سال تحصیلی","event_date":"تاریخ رویداد"}

EDITABLE={"manager":{"students","teachers","staff","school_profile","school_class_config","school_events","lesson_plans","weekly_schedule","generated_weekly_schedule","exam_schedule"},"educational":{"teacher_classes","lesson_plans","attendance","grades","student_grades","assignments","weekly_schedule","generated_weekly_schedule","exam_schedule"},"executive":{"students","parents","staff","attendance","school_events"},"cultural":{"educational_activities","school_events"},"advisor":{"counseling_records","counseling_followups"},"teacher":{"attendance","grades","student_grades","assignments","lesson_plans"}}
FORM_FIELDS={"students":["first_name","last_name","national_code","grade","class_name","phone"],"teachers":["first_name","last_name","national_code","subject"],"attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],"grades":["student_id","teacher_id","subject","exam_name","score","max_score","grade_type","term"],"assignments":["student_id","teacher_id","title","subject","class_name","status"],"lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title"],"school_events":["title","description","event_date","status"]}

DESCRIPTIONS={"school_profile":"هویت و مشخصات رسمی مدرسه","school_class_config":"پایه‌ها، کلاس‌ها و ساختار آموزشی","students":"پرونده و اطلاعات دانش‌آموزان","teachers":"پرونده و اطلاعات دبیران","staff":"مدیریت کارکنان مدرسه","teacher_classes":"کلاس‌ها و مسئولیت‌های دبیران","lesson_plans":"ثبت و پیگیری طرح درس","attendance":"کنترل حضور و غیاب","grades":"ثبت و مشاهده نمرات","assignments":"مدیریت تکالیف","parents":"اطلاعات اولیا","parent_children":"ارتباط حساب ولی با فرزند","parent_meetings":"جلسات و ارتباط با خانواده","finance_accounts":"حساب‌های مالی","finance_transactions":"گردش تراکنش‌ها","finance_donations":"کمک‌های داوطلبانه","payment_offers":"تعریف گزینه‌های پرداخت","payment_attempts":"پیگیری درخواست‌ها","payment_records":"سوابق پرداخت","online_classes":"مدیریت کلاس‌های آنلاین","online_class_sessions":"جلسات کلاس","online_class_students":"اعضای کلاس آنلاین","online_class_teachers":"دبیران کلاس آنلاین","messages":"صندوق پیام‌ها","report_cards":"کارنامه‌ها","weekly_schedule":"برنامه هفتگی کلاس‌ها","generated_weekly_schedule":"برنامه تولیدشده","exam_schedule":"برنامه امتحانات","account_settings":"تنظیمات حساب","educational_activities":"فعالیت‌های پرورشی","school_events":"رویدادهای مدرسه","counseling_records":"سوابق جلسات مشاوره","counseling_followups":"پیگیری مشاوره","smart_board_content":"محتوای آموزشی تابلو","smart_board_activities":"فعالیت‌های تعاملی","smart_board_quizzes":"آزمون‌های کوتاه","smart_board_whiteboards":"تخته آموزشی","ai_assistant_sessions":"جلسات دستیار هوشمند","ai_questions":"پرسش‌های هوشمند","ai_smart_reports":"گزارش‌های تحلیلی"}

class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical",padding=[dp(14),dp(12)],spacing=dp(6),size_hint_y=None,**kwargs)
        with self.canvas.before:
            Color(*CARD); self.bg=RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self._sync,size=self._sync)
    def _sync(self,*_): self.bg.pos=self.pos; self.bg.size=self.size

class ModuleScreen(Screen):
    def __init__(self,app_state,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.module_key=""; self.return_to="dashboard"; self.active_table=None; self._counts={}; self._build()
    def label(self,text,size="13sp",color=SECONDARY,bold=False,align="right"):
        w=Label(text=rtl_text(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,halign=align,valign="middle"); w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w
    def button(self,text,action,color=PRIMARY,height=dp(44)):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="11sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=height); b.bind(on_release=action); return b
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(7))
        head=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(7)); head.add_widget(self.button("‹ بازگشت",self.go_back,PRIMARY,dp(78))); self.title=self.label(APP_NAME,"20sp",PRIMARY,True,"center"); head.add_widget(self.title); root.add_widget(head)
        self.sub=self.label(SCHOOL_NAME+"  |  "+(SCHOOL_YEAR or "۱۴۰۵-۱۴۰۶"),"9sp",SECONDARY,False,"center"); root.add_widget(self.sub)
        self.body=BoxLayout(orientation="vertical",spacing=dp(7)); root.add_widget(self.body); self.add_widget(root)
    def set_module(self,key,return_to="dashboard"): self.return_to=return_to or "dashboard"; self.show_module(key)
    def load_module(self,key,return_to="dashboard"): self.set_module(key,return_to)
    def show_module(self,key):
        self.module_key=key or "management"; self.active_table=None; self._counts={}; self.title.text=rtl_text(MODULE_TITLES.get(self.module_key,self.module_key)); self._render_workspace(); Thread(target=self._load_counts,daemon=True).start()
    def _clear(self): self.body.clear_widgets()
    def _load_counts(self):
        api=getattr(self.app_state,"api",None)
        if api is None: return
        for table in MODULE_TABLES.get(self.module_key,[])[:4]:
            try:
                rows=api.table_select(table,{"limit":"100"}); self._counts[table]=len(rows) if isinstance(rows,list) else 0
            except Exception: self._counts[table]=None
        Clock.schedule_once(lambda *_: self._refresh_counts(),0)
    def _refresh_counts(self):
        for table,widget in getattr(self,"_count_widgets",{}).items():
            n=self._counts.get(table)
            widget.text=rtl_text("—" if n is None else str(n))
    def _render_workspace(self):
        self._clear(); self._count_widgets={}; title=MODULE_TITLES.get(self.module_key,self.module_key); tables=MODULE_TABLES.get(self.module_key,[])
        hero=Card(height=dp(148),padding=[dp(16),dp(12)])
        hero.add_widget(self.label("FRAHOOSH  /  WORKSPACE","9sp",PRIMARY,True,"left")); hero.add_widget(self.label(title,"25sp",PRIMARY,True,"center")); hero.add_widget(self.label("میزکار تخصصی این پنل؛ دسترسی مستقیم به داده‌های واقعی مدرسه","10sp",SECONDARY,False,"center")); hero.add_widget(self.label("اتصال سامانه فعال  •  سال تحصیلی "+(SCHOOL_YEAR or "۱۴۰۵-۱۴۰۶"),"9sp",SUCCESS,True,"center")); self.body.add_widget(hero)
        kpi=GridLayout(cols=2,spacing=dp(7),size_hint_y=None,height=dp(122))
        for i,table in enumerate(tables[:4]):
            c=Card(height=dp(57),padding=[dp(10),dp(6)]); name=self.label(FRIENDLY.get(table,table),"9sp",SECONDARY,True,"center"); value=self.label("…","19sp",PRIMARY,True,"center"); self._count_widgets[table]=value; c.add_widget(name); c.add_widget(value); kpi.add_widget(c)
        self.body.add_widget(kpi)
        self.body.add_widget(self.label("دسترسی‌های کلیدی","14sp",PRIMARY,True,"right"))
        quick=ScrollView(do_scroll_x=False,size_hint_y=None,height=dp(74)); qgrid=GridLayout(cols=2,spacing=dp(7),padding=[dp(1),dp(1)],size_hint_y=None); qgrid.bind(minimum_height=qgrid.setter("height"))
        for table in tables[:6]:
            b=self.button((FRIENDLY.get(table,table))+"  ›",lambda *_a,t=table:self.open_table(t),PRIMARY,dp(52)); qgrid.add_widget(b)
        quick.add_widget(qgrid); self.body.add_widget(quick)
        self.body.add_widget(self.label("فضای عملیاتی پنل","14sp",PRIMARY,True,"right"))
        scroll=ScrollView(do_scroll_x=False); grid=GridLayout(cols=1,spacing=dp(7),padding=[dp(1),dp(1),dp(1),dp(10)],size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        for idx,table in enumerate(tables,1):
            c=Card(height=dp(92)); row=BoxLayout(spacing=dp(9)); badge=Card(width=dp(48),size_hint_x=None,padding=dp(3)); badge.add_widget(self.label("%02d"%idx,"11sp",PRIMARY,True,"center")); row.add_widget(badge); info=BoxLayout(orientation="vertical",spacing=dp(2)); info.add_widget(self.label(FRIENDLY.get(table,table),"14sp",PRIMARY,True)); info.add_widget(self.label(DESCRIPTIONS.get(table,"اطلاعات عملیاتی سامانه"),"9sp",SECONDARY)); row.add_widget(info); c.add_widget(row); c.add_widget(self.button("باز کردن محیط عملیاتی  ›",lambda *_a,t=table:self.open_table(t),PRIMARY,dp(34))); grid.add_widget(c)
        if not tables: grid.add_widget(self.label("برای این پنل زیرعملکردی ثبت نشده است.","13sp",SECONDARY,False,"center"))
        scroll.add_widget(grid); self.body.add_widget(scroll)
    def open_table(self,table): self.active_table=table; self._render_table_loading(); Thread(target=self._fetch_table,args=(table,),daemon=True).start()
    def _render_table_loading(self):
        self._clear(); c=Card(height=dp(190)); c.add_widget(self.label("در حال آماده‌سازی محیط عملیاتی","19sp",PRIMARY,True,"center")); c.add_widget(self.label("فراهوش در حال دریافت اطلاعات واقعی این بخش است…","10sp",SECONDARY,False,"center")); self.body.add_widget(c)
    def _fetch_table(self,table):
        try:
            rows=self.app_state.api.table_select(table,{"limit":"80"}); rows=rows if isinstance(rows,list) else []; Clock.schedule_once(lambda *_:self._render_table(table,rows),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._render_error(table,str(exc)),0)
    def _render_error(self,table,error):
        self._clear(); self.body.add_widget(self.label(FRIENDLY.get(table,table),"18sp",PRIMARY,True,"center")); self.body.add_widget(self.label("دریافت اطلاعات انجام نشد: "+str(error),"11sp",SECONDARY,False,"center")); self.body.add_widget(self.button("↻ تلاش دوباره",lambda *_:self.open_table(table),PRIMARY,dp(44))); self.body.add_widget(self.button("‹ بازگشت به میزکار",lambda *_:self._render_workspace(),SECONDARY,dp(44)))
    def _render_table(self,table,rows):
        self._clear(); h=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6)); h.add_widget(self.button("‹ میزکار",lambda *_:self._render_workspace(),PRIMARY,dp(78))); h.add_widget(self.label(FRIENDLY.get(table,table),"17sp",PRIMARY,True,"center")); h.add_widget(self.button("↻",lambda *_:self.open_table(table),PRIMARY,dp(45))); self.body.add_widget(h)
        self.body.add_widget(self.label("%d رکورد واقعی از سامانه متصل شد"%len(rows),"10sp",SUCCESS,True,"center"))
        scroll=ScrollView(do_scroll_x=False); grid=GridLayout(cols=1,spacing=dp(7),padding=[dp(1),dp(1)],size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        if not rows: grid.add_widget(self.label("اطلاعاتی ثبت نشده است.","13sp",SECONDARY,False,"center"))
        role=str(getattr(self.app_state,"role","student") or "student").lower(); editable=EDITABLE.get(role,set())
        for row in rows:
            if not isinstance(row,dict): continue
            c=Card(height=dp(96)); preferred=["first_name","last_name","title","subject","grade","class_name","status","score","amount","date","created_at"]; keys=[k for k in preferred if k in row][:5] or list(row.keys())[:5]; shown=[]
            for k in keys:
                v=row.get(k)
                if v not in (None,""): shown.append(f"{COLUMNS.get(k,k)}: {v}")
            c.add_widget(self.label("  |  ".join(shown) or "رکورد بدون اطلاعات نمایشی","10sp",PRIMARY,True));
            if table in editable and row.get("id") is not None: c.add_widget(self.button("حذف رکورد",lambda *_a,t=table,i=row.get("id"):self.delete_row(t,i),SECONDARY,dp(30)))
            grid.add_widget(c)
        scroll.add_widget(grid); self.body.add_widget(scroll)
        if table in editable and table in FORM_FIELDS: self.body.add_widget(self.button("＋ ثبت اطلاعات جدید",lambda *_:self._new_form(table),SUCCESS,dp(45)))
    def _new_form(self,table):
        self._clear(); self.body.add_widget(self.label("ثبت "+FRIENDLY.get(table,table),"18sp",PRIMARY,True,"center")); scroll=ScrollView(do_scroll_x=False); box=BoxLayout(orientation="vertical",spacing=dp(7),padding=dp(3),size_hint_y=None); box.bind(minimum_height=box.setter("height")); fields={}
        for key in FORM_FIELDS.get(table,[]):
            inp=TextInput(hint_text=rtl_text(COLUMNS.get(key,key)),font_name=font_name(),multiline=False,halign="right",size_hint_y=None,height=dp(43),padding=[dp(10),dp(8)]); fields[key]=inp; box.add_widget(inp)
        box.add_widget(self.button("ثبت اطلاعات",lambda *_:self._insert(table,fields),SUCCESS,dp(46))); box.add_widget(self.button("‹ بازگشت",lambda *_:self.open_table(table),PRIMARY,dp(44))); scroll.add_widget(box); self.body.add_widget(scroll)
    def _insert(self,table,fields):
        payload={k:v.text.strip() for k,v in fields.items() if v.text.strip()}
        if not payload:return
        self._render_table_loading(); Thread(target=self._do_insert,args=(table,payload),daemon=True).start()
    def _do_insert(self,table,payload):
        try:self.app_state.api.table_insert(table,payload); Clock.schedule_once(lambda *_:self.open_table(table),0)
        except Exception as exc:Clock.schedule_once(lambda *_:self._render_error(table,str(exc)),0)
    def delete_row(self,table,row_id): self._render_table_loading(); Thread(target=self._do_delete,args=(table,row_id),daemon=True).start()
    def _do_delete(self,table,row_id):
        try:self.app_state.api.table_delete(table,{"id":"eq."+str(row_id)}); Clock.schedule_once(lambda *_:self.open_table(table),0)
        except Exception as exc:Clock.schedule_once(lambda *_:self._render_error(table,str(exc)),0)
    def go_back(self,*_):
        if self.manager:self.manager.current=self.return_to if self.manager.has_screen(self.return_to) else "dashboard"
