from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, WHITE, CARD, BORDER
from mobile.ui import font_name, rtl_text

MODULE_TITLES={"management":"مدیریت","educational":"معاون آموزشی","executive":"معاون اجرایی","cultural":"معاون پرورشی","advisor":"مشاوره","teacher":"پنل دبیر","teachers":"دبیران","student":"پنل دانش‌آموز","students":"دانش‌آموزان","parent":"پنل اولیا","parents":"اولیا","finance":"مالی","payment":"پرداخت آنلاین","online":"کلاس‌های آنلاین","smart_board":"تابلو هوشمند","ai":"دستیار هوش مصنوعی","messages":"صندوق پیام‌ها","settings":"تنظیمات","reports":"گزارش‌ها","schedule":"برنامه هفتگی","student_info":"وضعیت تحصیلی"}
MODULE_TABLES={"management":["school_profile","school_class_config","users"],"educational":["teacher_classes","lesson_plans","grades","assignments"],"executive":["students","parent_children","executive_classes","executive_operations","executive_requests"],"cultural":["educational_activities","cultural_activity_registrations","cultural_reports"],"advisor":["counseling_records","counseling_followups","students"],"teacher":["teacher_classes","teacher_activities","teacher_attendance","assignments"],"teachers":["teachers","staff","teacher_classes"],"student":["students","student_grades","grades","assignments"],"students":["students","student_grades","attendance","assignments"],"parent":["parent_children","students","grades","attendance"],"parents":["parent_children","students","parent_meetings"],"finance":["finance_accounts","finance_transactions","finance_donations","finance_extra","payment_records"],"payment":["payment_offers","payment_attempts","payment_records"],"online":["online_classes","online_class_sessions","online_class_students","online_class_teachers"],"smart_board":["smart_board_content","smart_board_activities","smart_board_quizzes","smart_board_whiteboards"],"ai":["ai_assistant_sessions","ai_questions","ai_smart_reports"],"messages":["message_inbox","messages","message_targets"],"settings":["account_settings","school_profile","school_class_config"],"reports":["report_cards","report_card_snapshots","grades","student_grades"],"schedule":["weekly_schedule","generated_weekly_schedule","exam_schedule"],"student_info":["students","grades","student_grades","report_cards"]}
DISPLAY_COLUMNS={"students":["id","first_name","last_name","national_code","grade","class_name","phone"],"teachers":["id","first_name","last_name","national_code","subject","grades","employment_status"],"staff":["id","first_name","last_name","role","phone","employment_status"],"teacher_classes":["id","teacher_name","subject","grade","class_name","active"],"school_profile":["school_name","school_code","principal_name","phone","address","academic_year"],"school_class_config":["total_classes","grade7_classes","grade8_classes","grade9_classes"],"grades":["student_id","teacher_id","subject","exam_name","score","max_score","grade_type","term","grade_date"],"student_grades":["student_id","teacher_id","subject","class_name","assessment_type","assessment_title","score","coefficient","grade_date_shamsi"],"attendance":["student_id","teacher_id","subject","class_name","attendance_date","status"],"assignments":["student_id","teacher_id","title","subject","class_name","status","due_date"],"lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title","session_date"],"teacher_activities":["teacher_id","student_id","title","activity_type","subject","score","activity_date"],"teacher_attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],"parent_children":["parent_username","student_id"],"parent_meetings":["student_id","teacher_id","parent_phone","reason","meeting_date","status"],"payment_offers":["id","title","amount","payment_reason","target_type","target_value","active","gateway_enabled"],"payment_attempts":["id","offer_id","student_id","payer_username","amount","status","gateway_ref","created_at"],"payment_records":["id","student_id","parent_username","title","amount","payment_type","gateway","reference","status","payment_date_shamsi"],"online_classes":["id","title","subject","lesson","teacher","grade","class_name","duration","start_time_shamsi","end_time_shamsi","status"],"online_class_sessions":["id","class_id","started_at","ended_at"],"online_class_students":["id","class_id","student_id","student_name"],"online_class_teachers":["id","class_id","teacher_id","teacher_name"],"smart_board_content":["id","title","class_id","teacher_id","content_date_shamsi"],"smart_board_activities":["id","title","class_id","teacher_id","activity_date_shamsi"],"smart_board_quizzes":["id","title","question","class_id","teacher_id","quiz_date_shamsi"],"smart_board_whiteboards":["id","title","class_id","teacher_id","board_date"],"messages":["id","sender_name","title","body","audience_type","created_at"],"message_inbox":["id","sender_username","sender_role","title","body","is_read","created_at"],"message_targets":["id","message_id","target_type","target_value","target_role","target_id","read_at"],"executive_classes":["id","name","grade","teacher","created_at"],"executive_operations":["id","operation_type","title","student_id","class_name","status","operation_date"],"executive_requests":["id","title","requester","status","description","created_at"],"educational_activities":["id","title","subject","grade","class_name","teacher_id","student_id","activity_date","status"],"cultural_activity_registrations":["id","activity_title","activity_kind","student_id","student_name","fee","payment_status","status"],"cultural_reports":["id","title","report_type","activity_id","report_date"],"counseling_records":["id","student_name","visit_reason","recommendations","next_visit","created_at"],"counseling_followups":["id","student_id","subject","description","status","created_at"],"finance_accounts":["id","title","balance","created_at"],"finance_transactions":["id","transaction_type","title","amount","category","transaction_date"],"finance_donations":["id","donor_name","amount","description","donation_date"],"finance_extra":["id","title","student_name","amount","payment_date"],"ai_assistant_sessions":["id","username","role","title","created_at"],"ai_questions":["id","username","role","question","answer","created_at"],"ai_smart_reports":["id","title","report_type","target_type","target_id","created_at"],"report_cards":["id","student_id","term","average","grade_level","academic_year","report_date"],"report_card_snapshots":["id","student_id","term","academic_year","average","generated_date_shamsi"],"weekly_schedule":["id","teacher","subject","grade","class_count","class_names","weekdays"],"generated_weekly_schedule":["id","teacher","subject","grade","class_name","weekday","bell","week_index"],"exam_schedule":["id","subject","grade","exam_date","duration","exam_start_time","exam_end_time"],"account_settings":["username","display_name","phone","email","national_code","role"]}

class _Card(BoxLayout):
    def __init__(self,**kwargs):
        super().__init__(orientation="vertical",padding=[dp(12),dp(9)],spacing=dp(3),size_hint_y=None,**kwargs)
        with self.canvas.before:
            Color(*CARD); self.bg=RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._sync,size=self._sync)
    def _sync(self,*_):self.bg.pos=self.pos;self.bg.size=self.size

class ModuleScreen(Screen):
    def __init__(self,app_state,**kwargs):super().__init__(**kwargs);self.app_state=app_state;self.module_key="";self._build()
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(13),spacing=dp(8));head=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(8))
        b=Button(text=rtl_text("‹ داشبورد"),font_name=font_name(),font_size="13sp",background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(105));b.bind(on_release=self.go_back);head.add_widget(b)
        self.title=Label(text=rtl_text(APP_NAME),font_name=font_name(),font_size="21sp",bold=True,color=PRIMARY,halign="right",valign="middle");self.title.bind(size=lambda o,v:setattr(o,"text_size",v));head.add_widget(self.title);root.add_widget(head)
        self.status=Label(text="",font_name=font_name(),font_size="11sp",color=SECONDARY,halign="center",valign="middle",size_hint_y=None,height=dp(38));self.status.bind(size=lambda o,v:setattr(o,"text_size",v));root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False);self.body=BoxLayout(orientation="vertical",spacing=dp(8),padding=[dp(3),dp(3)],size_hint_y=None);self.body.bind(minimum_height=self.body.setter("height"));scroll.add_widget(self.body);root.add_widget(scroll);self.add_widget(root)
    def go_back(self,*_):
        if self.manager:self.manager.current="dashboard"
    def set_module(self,key):self.show_module(key)
    def load_module(self,key):self.show_module(key)
    def show_module(self,key):
        self.module_key=str(key or "").strip().lower();self.title.text=rtl_text(MODULE_TITLES.get(self.module_key,self.module_key or APP_NAME));self.body.clear_widgets();self.status.text=rtl_text("در حال دریافت اطلاعات سامانه…");self.status.color=SECONDARY
        self._add_label(f"{MODULE_TITLES.get(self.module_key,self.module_key)}  |  {SCHOOL_NAME}","19sp",PRIMARY,50,True)
        self._add_label(f"سال تحصیلی: {SCHOOL_YEAR or '—'}  •  اطلاعات زنده از سامانه مرکزی","10sp",SECONDARY,38)
        Thread(target=self._load_tables,args=(MODULE_TABLES.get(self.module_key,[]),),daemon=True).start()
    def _load_tables(self,tables):
        results=[]
        for table in tables:
            try:results.append((table,self.app_state.api.table_select(table,{"limit":"25"}) or [],None))
            except Exception as exc:results.append((table,[],str(exc)))
        Clock.schedule_once(lambda *_:self._render_tables(results),0)
    def _render_tables(self,results):
        total=0
        for table,rows,error in results:
            if rows:
                total+=len(rows);self._add_label(self._friendly(table),"15sp",PRIMARY,38,True)
                for row in rows[:25]:self._add_record(table,row)
            else:self._add_label(f"{self._friendly(table)}\nهنوز اطلاعاتی برای نمایش در این بخش ثبت نشده است.","11sp",SECONDARY,54)
        self.status.text=rtl_text(f"{total} رکورد برای این پنل بارگذاری شد. برای دریافت آخرین اطلاعات، تازه‌سازی کنید.");self.status.color=SUCCESS
        self._button("↻ تازه‌سازی اطلاعات",lambda *_:self.show_module(self.module_key),SUCCESS)
    def _add_record(self,table,row):
        cols=DISPLAY_COLUMNS.get(table) or [k for k in row.keys() if k!="password"][:8];parts=[]
        for c in cols:
            if c in row and row.get(c) not in (None,""):parts.append(f"{self._column(c)}: {row.get(c)}")
        text="\n".join(parts) or "رکورد ثبت شده";card=_Card(height=max(dp(62),dp(25*min(8,len(parts))+12)));lab=Label(text=rtl_text(text),font_name=font_name(),font_size="10sp",color=SECONDARY,halign="right",valign="middle");lab.bind(size=lambda o,v:setattr(o,"text_size",v));card.add_widget(lab);self.body.add_widget(card)
    def _add_label(self,text,size="14sp",color=SECONDARY,height=50,bold=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="right",valign="middle",size_hint_y=None,height=dp(height));w.bind(size=lambda o,v:setattr(o,"text_size",v));self.body.add_widget(w);return w
    def _button(self,text,cb,color=PRIMARY):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="13sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(48));b.bind(on_release=cb);self.body.add_widget(b);return b
    @staticmethod
    def _friendly(t):return {"school_profile":"مشخصات مدرسه","school_class_config":"تنظیمات کلاس‌ها","users":"حساب‌های سامانه","students":"دانش‌آموزان","teachers":"دبیران","staff":"کارکنان","teacher_classes":"کلاس‌های دبیر","lesson_plans":"طرح درس‌ها","grades":"نمرات","student_grades":"ارزیابی‌های دانش‌آموز","attendance":"حضور و غیاب","assignments":"تکالیف","parent_children":"ارتباط ولی و فرزند","parent_meetings":"جلسات اولیا","payment_offers":"گزینه‌های پرداخت","payment_attempts":"درخواست‌های پرداخت","payment_records":"سوابق پرداخت","online_classes":"کلاس‌های آنلاین","online_class_sessions":"جلسات کلاس آنلاین","online_class_students":"دانش‌آموزان کلاس آنلاین","online_class_teachers":"دبیران کلاس آنلاین","messages":"پیام‌ها","message_inbox":"صندوق ورودی","message_targets":"مخاطبان پیام","report_cards":"کارنامه‌ها","report_card_snapshots":"نسخه‌های کارنامه","weekly_schedule":"برنامه هفتگی","generated_weekly_schedule":"برنامه تولیدشده","exam_schedule":"برنامه امتحانات","account_settings":"تنظیمات حساب"}.get(t,t.replace("_"," "))
    @staticmethod
    def _column(c):return {"id":"شناسه","first_name":"نام","last_name":"نام خانوادگی","national_code":"کد ملی","grade":"پایه","class_name":"کلاس","subject":"درس","teacher_name":"دبیر","score":"نمره","max_score":"از","status":"وضعیت","amount":"مبلغ","title":"عنوان","description":"توضیحات","created_at":"تاریخ ثبت","created_at_shamsi":"تاریخ ثبت","exam_date":"تاریخ آزمون","exam_date_shamsi":"تاریخ آزمون","start_time_shamsi":"شروع","end_time_shamsi":"پایان","payment_reason":"علت پرداخت","is_read":"خوانده شده","active":"فعال"}.get(c,c.replace("_"," "))
