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

ROLE_ALIASES = {"admin":"manager","administrator":"manager","manager":"manager","مدیر":"manager","مدیریت":"manager","executive":"executive","معاون اجرایی":"executive","educational":"educational","training":"educational","معاون آموزشی":"educational","cultural":"cultural","پرورشی":"cultural","معاون پرورشی":"cultural","advisor":"advisor","counselor":"advisor","مشاور":"advisor","teacher":"teacher","teacher_staff":"teacher","دبیر":"teacher","معلم":"teacher","student":"student","دانش‌آموز":"student","دانش آموز":"student","parent":"parent","parent_guardian":"parent","guardian":"parent","ولی":"parent","اولیا":"parent"}
ROLE_FEATURES = {"manager":"مدیریت مدرسه، کاربران، کارکنان، آمار، مالی و گزارش‌ها.","educational":"کلاس‌ها، دروس، حضور و غیاب، نمرات، تکالیف و برنامه‌ریزی آموزشی.","executive":"پرونده دانش‌آموزان، اولیا، کلاس‌ها، ثبت‌نام و امور اجرایی.","cultural":"فعالیت‌های فرهنگی و پرورشی، رویدادها و مشارکت دانش‌آموزان.","advisor":"پرونده دانش‌آموز، جلسات و پیگیری مشاوره.","teacher":"کلاس‌های من، دانش‌آموزان، حضور و غیاب، نمرات، تکالیف و آزمون‌ها.","student":"کلاس‌ها، برنامه هفتگی، نمرات، تکالیف، حضور و غیاب و آزمون‌ها.","parent":"فرزند، وضعیت تحصیلی، حضور و غیاب، نمرات، تکالیف و پرداخت‌ها."}
MODULE_TITLES = {"management":"مدیریت","educational":"معاون آموزشی","executive":"معاون اجرایی","cultural":"معاون پرورشی","advisor":"مشاوره","teacher":"پنل دبیر","teachers":"دبیران","student":"پنل دانش‌آموز","students":"دانش‌آموزان","parent":"پنل اولیا","parents":"اولیا","finance":"مالی","payment":"پرداخت آنلاین","online":"کلاس‌های آنلاین","smart_board":"تابلو هوشمند","ai":"دستیار هوش مصنوعی","messages":"صندوق پیام‌ها","settings":"تنظیمات","reports":"گزارش‌ها","schedule":"برنامه هفتگی","student_info":"وضعیت تحصیلی"}
MODULE_TABLES = {"management":["school_profile","school_class_config","students","teachers","staff","users"],"educational":["teacher_classes","lesson_plans","attendance","grades","assignments"],"executive":["students","parents","staff","attendance","school_events"],"cultural":["educational_activities","school_events","students","messages"],"advisor":["counseling_records","counseling_followups","students"],"teacher":["teacher_classes","teacher_attendance","grades","assignments"],"teachers":["teachers","staff","teacher_classes"],"student":["students","student_grades","attendance","assignments"],"students":["students","student_grades","attendance","assignments"],"parent":["parent_children","students","grades","attendance","assignments"],"parents":["parent_children","parents","parent_meetings","students"],"finance":["finance_accounts","finance_transactions","finance_donations","payment_records"],"payment":["payment_offers","payment_attempts","payment_records"],"online":["online_classes","online_class_sessions","online_class_students","online_class_teachers"],"smart_board":["smart_board_content","smart_board_activities","smart_board_quizzes","smart_board_whiteboards"],"ai":["ai_assistant_sessions","ai_questions","ai_smart_reports"],"messages":["messages","message_targets","message_reads"],"settings":["account_settings","school_profile","school_class_config"],"reports":["report_cards","report_card_snapshots","grades","attendance","student_grades"],"schedule":["weekly_schedule","generated_weekly_schedule","exam_schedule"],"student_info":["students","grades","student_grades","attendance","assignments","report_cards"]}
DISPLAY_COLUMNS = {"students":["id","first_name","last_name","national_code","grade","class_name","phone"],"teachers":["id","first_name","last_name","national_code","subject","grades","employment_status"],"staff":["id","first_name","last_name","role","phone","employment_status"],"teacher_classes":["id","teacher_name","subject","grade","class_name","active"],"school_profile":["school_name","school_code","principal_name","phone","address","academic_year"],"school_class_config":["total_classes","grade7_classes","grade8_classes","grade9_classes"],"grades":["student_id","teacher_id","subject","exam_name","score","max_score","grade_type","term","grade_date"],"student_grades":["student_id","teacher_id","subject","class_name","assessment_type","assessment_title","score","coefficient","grade_date_shamsi"],"attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],"assignments":["student_id","teacher_id","title","subject","class_name","status","due_date"],"lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title","session_date"],"teacher_attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],"parent_children":["parent_username","student_id"],"parent_meetings":["student_id","teacher_id","parent_phone","reason","meeting_date","status"],"payment_offers":["id","title","amount","payment_reason","target_type","target_value","active","gateway_enabled"],"payment_attempts":["id","offer_id","student_id","payer_username","amount","status","gateway_ref","created_at"],"payment_records":["id","student_id","parent_username","title","amount","payment_type","gateway","reference","status","payment_date_shamsi"],"online_classes":["id","title","subject","lesson","teacher","grade","class_name","duration","start_time_shamsi","end_time_shamsi","status"],"online_class_sessions":["id","class_id","started_at","ended_at"],"online_class_students":["id","class_id","student_id","student_name"],"online_class_teachers":["id","class_id","teacher_id","teacher_name"],"messages":["id","sender_name","title","body","audience_type","created_at"],"message_targets":["id","message_id","target_type","target_value","target_role","target_id","read_at"],"message_reads":["id","message_id","user_id","read_at"],"report_cards":["id","student_id","term","average","grade_level","academic_year","report_date"],"report_card_snapshots":["id","student_id","term","academic_year","average","generated_date_shamsi"],"weekly_schedule":["id","teacher","subject","grade","class_count","class_names","weekdays"],"generated_weekly_schedule":["id","teacher","subject","grade","class_name","weekday","bell","week_index"],"exam_schedule":["id","subject","grade","exam_date","duration","exam_start_time","exam_end_time"],"account_settings":["username","display_name","phone","email","national_code","role"]}
FRIENDLY = {"school_profile":"مشخصات مدرسه","school_class_config":"تنظیمات کلاس‌ها","users":"حساب‌های سامانه","students":"دانش‌آموزان","teachers":"دبیران","staff":"کارکنان","teacher_classes":"کلاس‌های دبیر","lesson_plans":"طرح درس‌ها","grades":"نمرات","student_grades":"ارزیابی‌های دانش‌آموز","attendance":"حضور و غیاب","assignments":"تکالیف","parent_children":"ارتباط ولی و فرزند","parent_meetings":"جلسات اولیا","parents":"اولیا","payment_offers":"گزینه‌های پرداخت","payment_attempts":"درخواست‌های پرداخت","payment_records":"سوابق پرداخت","online_classes":"کلاس‌های آنلاین","online_class_sessions":"جلسات کلاس آنلاین","online_class_students":"دانش‌آموزان کلاس آنلاین","online_class_teachers":"دبیران کلاس آنلاین","messages":"پیام‌ها","message_targets":"مخاطبان پیام","message_reads":"وضعیت خواندن پیام","report_cards":"کارنامه‌ها","report_card_snapshots":"نسخه‌های کارنامه","weekly_schedule":"برنامه هفتگی","generated_weekly_schedule":"برنامه تولیدشده","exam_schedule":"برنامه امتحانات","account_settings":"تنظیمات حساب","finance_accounts":"حساب‌های مالی","finance_transactions":"تراکنش‌های مالی","finance_donations":"کمک‌های داوطلبانه","educational_activities":"فعالیت‌های پرورشی","school_events":"رویدادهای مدرسه","counseling_records":"سوابق مشاوره","counseling_followups":"پیگیری‌های مشاوره","smart_board_content":"محتوای تابلو","smart_board_activities":"فعالیت‌های تابلو","smart_board_quizzes":"آزمون‌های کوتاه","smart_board_whiteboards":"تخته‌های کلاس","ai_assistant_sessions":"جلسات دستیار هوشمند","ai_questions":"پرسش‌های هوش مصنوعی","ai_smart_reports":"گزارش‌های هوشمند"}
COLUMN = {"id":"شناسه","first_name":"نام","last_name":"نام خانوادگی","national_code":"کد ملی","grade":"پایه","class_name":"کلاس","subject":"درس","teacher_name":"دبیر","score":"نمره","max_score":"از","status":"وضعیت","amount":"مبلغ","title":"عنوان","description":"توضیحات","created_at":"تاریخ ثبت","created_at_shamsi":"تاریخ ثبت","exam_date":"تاریخ آزمون","exam_date_shamsi":"تاریخ آزمون","start_time_shamsi":"شروع","end_time_shamsi":"پایان","payment_reason":"علت پرداخت","active":"فعال"}
EDITABLE_TABLES = {"manager":{"students","teachers","staff","school_profile","school_class_config","school_events","lesson_plans","weekly_schedule","generated_weekly_schedule","exam_schedule"},"educational":{"teacher_classes","lesson_plans","attendance","teacher_attendance","grades","student_grades","assignments","weekly_schedule","generated_weekly_schedule","exam_schedule"},"executive":{"students","parents","staff","attendance","school_events"},"cultural":{"educational_activities","school_events"},"advisor":{"counseling_records","counseling_followups"},"teacher":{"attendance","teacher_attendance","grades","student_grades","assignments","lesson_plans"}}
FORM_FIELDS = {"students":["first_name","last_name","national_code","grade","class_name","phone"],"teachers":["first_name","last_name","national_code","subject","grades","employment_status"],"attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],"teacher_attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],"grades":["student_id","teacher_id","subject","exam_name","score","max_score","grade_type","term","grade_date"],"student_grades":["student_id","teacher_id","subject","class_name","assessment_type","assessment_title","score","coefficient","grade_date_shamsi"],"assignments":["student_id","teacher_id","title","subject","class_name","status","due_date"],"lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title","session_date"],"school_events":["title","description","event_date","status"],"counseling_records":["student_id","advisor_id","title","description","session_date","status"],"counseling_followups":["student_id","advisor_id","description","followup_date","status"]}

class _Card(BoxLayout):
    def __init__(self,**kwargs):
        super().__init__(orientation="vertical",padding=[dp(12),dp(9)],spacing=dp(4),size_hint_y=None,**kwargs)
        with self.canvas.before:
            Color(*CARD); self.bg=RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._sync,size=self._sync)
    def _sync(self,*_): self.bg.pos=self.pos; self.bg.size=self.size

class ModuleScreen(Screen):
    def __init__(self,app_state,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.module_key=""; self.return_to="dashboard"; self._build()
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(13),spacing=dp(8)); head=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(8))
        back=Button(text=rtl_text("‹ بازگشت"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(105)); back.bind(on_release=self.go_back); head.add_widget(back)
        self.title=Label(text=rtl_text(APP_NAME),font_name=font_name(),font_size="21sp",bold=True,color=PRIMARY,halign="right",valign="middle"); self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title); root.add_widget(head)
        self.status=Label(text="",font_name=font_name(),font_size="11sp",color=SECONDARY,halign="center",valign="middle",size_hint_y=None,height=dp(42)); self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False); self.body=BoxLayout(orientation="vertical",spacing=dp(8),padding=[dp(3),dp(3)],size_hint_y=None); self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root)
    def go_back(self,*_):
        if self.manager:self.manager.current=self.return_to if self.manager.has_screen(self.return_to) else "dashboard"
    def set_module(self,key,return_to="dashboard"): self.return_to=return_to or "dashboard"; self.show_module(key)
    def load_module(self,key,return_to="dashboard"): self.set_module(key,return_to)
    def _role(self):
        raw=str(getattr(self.app_state,"role","student") or "student").strip().lower(); return ROLE_ALIASES.get(raw,raw)
    def show_module(self,key):
        self.module_key=str(key or "").strip().lower(); title=MODULE_TITLES.get(self.module_key,self.module_key or APP_NAME); role=self._role(); self.title.text=rtl_text(title); self.body.clear_widgets(); self.status.text=rtl_text("در حال بارگذاری اطلاعات واقعی…"); self.status.color=SECONDARY
        self._add_label(f"{title} | دبیرستان سردارشهیدحاجی زاده ۲","18sp",PRIMARY,48,True); self._add_notice("امکانات فعال",ROLE_FEATURES.get(role,"امکانات بر اساس نقش کاربر نمایش داده می‌شود."),SUCCESS); self._add_label(f"سال تحصیلی: {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}","10sp",SECONDARY,30)
        tables=MODULE_TABLES.get(self.module_key,[])
        if not tables:self.status.text=rtl_text("پنل آماده استفاده است."); self._add_notice("این بخش","امکانات اجرایی از منوی همین پنل قابل انتخاب است.",SUCCESS); return
        Thread(target=self._load_tables,args=(tables,),daemon=True).start()
    def _load_tables(self,tables):
        results=[]; api=getattr(self.app_state,"api",None)
        if api is None:Clock.schedule_once(lambda *_:self._render_tables([]),0);return
        for table in tables:
            try:
                rows=api.table_select(table,{"limit":"50"}) or []
                results.append((table,rows if isinstance(rows,list) else [],"data",""))
            except Exception as exc:results.append((table,[],"unavailable",str(exc)))
        Clock.schedule_once(lambda *_:self._render_tables(results),0)
    def _render_tables(self,results):
        total=0; sections=0; role=self._role()
        for table,rows,kind,detail in results:
            if kind!="data":
                self._add_notice(self._friendly(table),"خواندن این منبع داده در حال حاضر ممکن نیست: "+detail)
                continue
            sections+=1; cols=DISPLAY_COLUMNS.get(table) or ([k for k in rows[0].keys() if k!="password"][:8] if rows else [])
            self._add_label(self._friendly(table),"15sp",PRIMARY,38,True)
            if table in EDITABLE_TABLES.get(role,set()) and table in FORM_FIELDS:self._add_button("＋ ثبت اطلاعات جدید",lambda *_ ,t=table:self._show_form(t),SUCCESS)
            if not cols:
                self._add_notice(self._friendly(table),"جدول آماده است اما هنوز رکوردی برای نمایش ندارد.")
                continue
            self._add_real_table(table,rows,cols,table in EDITABLE_TABLES.get(role,set()))
            total+=len(rows)
        self.status.text=rtl_text(f"{total} رکورد از {sections} جدول واقعی بارگذاری شد") if results else rtl_text("اتصال حساب به سامانه برای نمایش داده‌ها لازم است.")
        self.status.color=SUCCESS if sections else SECONDARY
        self._add_button("↻ تازه‌سازی اطلاعات",lambda *_:self.show_module(self.module_key),SUCCESS)
    def _add_real_table(self,table,rows,cols,editable):
        # Horizontal scroll keeps wide school tables usable on a phone.
        width=max(dp(520),dp(125*len(cols)))
        outer=ScrollView(do_scroll_x=True,do_scroll_y=False,size_hint_y=None,height=dp(50+max(1,min(len(rows),50))*46))
        grid=GridLayout(cols=len(cols),rows=max(1,len(rows)+1),size_hint=(None,None),width=width,row_default_height=dp(46),row_force_default=True)
        grid.height=dp(46*max(1,len(rows)+1))
        for c in cols:
            grid.add_widget(self._cell(self._column(c),PRIMARY,True))
        if rows:
            for row in rows[:50]:
                for c in cols:grid.add_widget(self._cell(str(row.get(c,"")),SECONDARY,False))
        else:
            for _ in cols:grid.add_widget(self._cell("—",SECONDARY,False))
        outer.add_widget(grid); self.body.add_widget(outer)
        if editable and rows:
            for row in rows[:50]:
                if row.get("id") is not None:
                    actions=BoxLayout(size_hint_y=None,height=dp(38),spacing=dp(5))
                    edit=Button(text=rtl_text("ویرایش رکورد "+str(row["id"])),font_name=font_name(),font_size="10sp",background_normal="",background_color=PRIMARY,color=WHITE)
                    edit.bind(on_release=lambda *_ ,t=table,r=dict(row):self._show_form(t,r)); actions.add_widget(edit)
                    delete=Button(text=rtl_text("حذف"),font_name=font_name(),font_size="10sp",background_normal="",background_color=(0.65,0.12,0.14,1),color=WHITE,size_hint_x=None,width=dp(70)); delete.bind(on_release=lambda *_ ,t=table,r=dict(row):self._delete_record(t,r)); actions.add_widget(delete); self.body.add_widget(actions)
    def _cell(self,text,color,bold):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size="10sp",bold=bold,color=WHITE if bold else color,halign="center",valign="middle",size_hint=(None,None),width=dp(125),height=dp(46))
        with w.canvas.before:
            Color(*PRIMARY if bold else CARD,1); w.bg=RoundedRectangle(radius=[dp(3)])
        w.bind(pos=lambda o,v:setattr(o.bg,"pos",v),size=lambda o,v:setattr(o.bg,"size",v)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w
    def _show_form(self,table,row=None):
        fields=FORM_FIELDS.get(table,[]); self.body.clear_widgets(); self._add_label(f"ثبت / ویرایش {self._friendly(table)}","18sp",PRIMARY,48,True); inputs={}
        for field in fields:
            self._add_label(self._column(field),"11sp",SECONDARY,27); ti=TextInput(text="" if row is None else str(row.get(field) or ""),font_name=font_name(),multiline=False,halign="right",size_hint_y=None,height=dp(46),padding=[dp(10),dp(10)]); inputs[field]=ti; self.body.add_widget(ti)
        self._add_button("ذخیره اطلاعات",lambda *_:self._save_form(table,inputs,row),SUCCESS); self._add_button("انصراف و بازگشت به جدول",lambda *_:self.show_module(self.module_key),PRIMARY)
    def _save_form(self,table,inputs,row):
        payload={k:v.text.strip() for k,v in inputs.items() if v.text.strip()}
        if not payload:self.status.text=rtl_text("حداقل یک مقدار وارد کنید."); return
        try:
            if row and row.get("id") is not None:self.app_state.api.table_update(table,{"id":f"eq.{row['id']}"},payload)
            else:self.app_state.api.table_insert(table,payload)
            self.show_module(self.module_key)
        except Exception as exc:self.status.text=rtl_text("ثبت اطلاعات انجام نشد: "+str(exc)); self.status.color=(0.75,0.12,0.12,1)
    def _delete_record(self,table,row):
        if row.get("id") is None:return
        try:self.app_state.api.table_delete(table,{"id":f"eq.{row['id']}"}); self.show_module(self.module_key)
        except Exception as exc:self.status.text=rtl_text("حذف انجام نشد: "+str(exc)); self.status.color=(0.75,0.12,0.12,1)
    def _add_notice(self,title,text,color=SECONDARY):
        card=_Card(height=dp(82)); h=Label(text=rtl_text(title),font_name=font_name(),font_size="14sp",bold=True,color=color,halign="right",valign="middle",size_hint_y=None,height=dp(27)); h.bind(size=lambda o,v:setattr(o,"text_size",v)); b=Label(text=rtl_text(text),font_name=font_name(),font_size="10sp",color=SECONDARY,halign="right",valign="top"); b.bind(size=lambda o,v:setattr(o,"text_size",v)); card.add_widget(h); card.add_widget(b); self.body.add_widget(card)
    def _add_label(self,text,size="14sp",color=SECONDARY,height=50,bold=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="right",valign="middle",size_hint_y=None,height=dp(height)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w
    def _add_button(self,text,callback,color=PRIMARY):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="13sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(46)); b.bind(on_release=callback); self.body.add_widget(b); return b
    @staticmethod
    def _friendly(table):return FRIENDLY.get(table,table.replace("_"," "))
    @staticmethod
    def _column(column):return COLUMN.get(column,column.replace("_"," "))
