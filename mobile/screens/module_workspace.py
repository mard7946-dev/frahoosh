from threading import Thread

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from mobile.config import APP_NAME, CARD, PRIMARY, SCHOOL_NAME, SCHOOL_YEAR, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

# One shared operational vocabulary for Android and the future web client.
# Both clients must bind these keys to the same Supabase tables and field names.
SUBMENUS = {
"management":[("اطلاعات مدرسه","school_profile"),("دانش‌آموزان","students"),("دبیران","teachers"),("کادر و کارکنان","staff"),("پایه و کلاس‌ها","school_class_config"),("حساب‌های سامانه","users"),("رویدادها","school_events"),("صندوق پیام","messages"),("کارنامه‌ها","report_cards"),("برنامه هفتگی","weekly_schedule"),("آزمون آنلاین","teacher_exams"),("کلاس آنلاین","online_classes"),("مالی","finance_accounts"),("پرداخت آنلاین","payment_offers"),("تابلو هوشمند","smart_board_content"),("گزارش‌های مدیریتی","report_cards")],
"educational":[("پرونده اطلاعاتی دانش‌آموز","students"),("پرونده پرسنلی همکاران","staff"),("کلاس‌های دبیران","teacher_classes"),("فعال‌سازی کلاس آنلاین","online_classes"),("برنامه هفتگی","weekly_schedule"),("برنامه امتحانی","exam_schedule"),("پیگیری آموزشی","educational_followups"),("پیگیری درسی","academic_followups"),("پیگیری انضباطی","discipline_records"),("ثبت انضباطی","discipline_records"),("نمرات و کارنامه‌ها","student_grades"),("گزارش آموزشی هوشمند","ai_smart_reports"),("جشنواره خوارزمی","khwarizmi_registrations"),("آزمون آنلاین","teacher_exams"),("صندوق پیام","messages")],
"executive":[("پرونده دانش‌آموزی","students"),("پرونده پرسنلی کارکنان","staff"),("اولیا و ارتباط فرزند","parent_children"),("فعال‌سازی برنامه هفتگی","weekly_schedule"),("فعال‌سازی کارنامه ماهیانه","monthly_report_cards"),("فعال‌سازی کارنامه مستمر و پایان ترم","report_cards"),("ثبت انضباطی","discipline_records"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("کلاس‌های آنلاین","online_classes"),("رویدادها و مراسمات","school_events"),("صندوق پیام","messages")],
"cultural":[("پیام‌های پرورشی","messages"),("ایجاد مسابقات","activity_offers"),("مسابقات فرهنگی","cultural_competitions"),("مسابقات هنری","art_competitions"),("مسابقات ورزشی","sport_competitions"),("فعالیت‌ها و مراسمات","educational_activities"),("انتخابات شورای دانش‌آموزی","student_council"),("بسیج دانش‌آموزی","basij_registration"),("شهردار مدرسه","school_mayor"),("مکبر","morning_leaders"),("قاری برنامه ظهرگاهی","qari_registration"),("جدول مراسم ظهرگاهی","morning_ceremony"),("ثبت انضباطی","discipline_records"),("صندوق پیام","messages")],
"advisor":[("پرونده‌های مشاوره","counseling_records"),("پیگیری جلسات","counseling_followups"),("دانش‌آموزان","students"),("اولیا","parents"),("درخواست ملاقات","parent_meeting_requests"),("گزارش‌های مشاوره","report_cards"),("صندوق پیام","messages")],
"teachers":[("کلاس‌های من","teacher_classes"),("طرح درس","lesson_plans"),("برنامه هفتگی","weekly_schedule"),("کلاس‌های آنلاین فعال","online_classes"),("آزمون آنلاین","teacher_exams"),("حضور و غیاب","attendance"),("نمرات درسی","grades"),("تکالیف","assignments"),("موارد انضباطی","discipline_records"),("ارجاع دانش‌آموز","student_referrals"),("درخواست ملاقات اولیا","teacher_parent_meetings"),("صندوق پیام","messages")],
"students":[("اطلاعات شخصی","students"),("پایه و کلاس","student_class_info"),("نمرات","student_grades"),("وضعیت حضور و غیاب","attendance"),("کلاس‌های آنلاین فعال","online_classes"),("شرکت در فعالیت‌ها","activity_registrations"),("انتخابات شورای دانش‌آموزی","student_council"),("بسیج دانش‌آموزی","basij_registration"),("همیار مدرسه","school_ally"),("شهردار مدرسه","school_mayor"),("ارسال تکالیف","assignment_submissions"),("برنامه هفتگی","weekly_schedule"),("برنامه امتحانی","exam_schedule"),("شماره صندلی کلاسی","class_seat_assignments"),("شماره صندلی امتحانی","exam_seat_assignments"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("صندوق پیام","messages"),("کمک‌های داوطلبانه / پرداخت آنلاین","payment")],
"parents":[("انتخاب یک یا چند دانش‌آموز","parent_children"),("اطلاعات دانش‌آموز","students"),("نمرات کلاسی و امتحانی","student_grades"),("حضور و غیاب","attendance"),("کارنامه ماهیانه","monthly_report_cards"),("کارنامه مستمر و پایان ترم","report_cards"),("ملاقات با دبیر","parent_meeting_requests"),("ملاقات با معاون","parent_meeting_requests"),("ملاقات با مشاور","parent_meeting_requests"),("ملاقات با مدیریت","parent_meeting_requests"),("انتخابات و مراسمات انجمن اولیا","parent_activities"),("کلاس آموزش خانواده","parent_activities"),("بهداشت روان","parent_activities"),("کمک‌های داوطلبانه / پرداخت آنلاین","payment"),("صندوق پیام","messages")],
"finance":[("حساب‌ها","finance_accounts"),("تراکنش‌ها","finance_transactions"),("کمک‌های داوطلبانه","finance_donations"),("تعریف گزینه پرداخت","payment_offers"),("درخواست‌های پرداخت","payment_attempts"),("سوابق پرداخت","payment_records")],
"online":[("کلاس‌های آنلاین","online_classes"),("جلسات","online_class_sessions"),("دانش‌آموزان کلاس","online_class_students"),("دبیران کلاس","online_class_teachers"),("حضور آنلاین","online_class_students"),("تخته کلاس","smart_board_whiteboards")],
"smart_board":[("محتوای آموزشی","smart_board_content"),("فعالیت‌ها","smart_board_activities"),("آزمون‌های کوتاه","smart_board_quizzes"),("تخته‌های آموزشی","smart_board_whiteboards")],
"ai":[("گزارش تحلیلی کلاس به کلاس","ai_smart_reports"),("گزارش تحلیلی دانش‌آموز","ai_smart_reports"),("پرسش هوشمند","ai_questions"),("جلسات دستیار","ai_assistant_sessions")],
"messages":[("صندوق ورودی","messages"),("ارسال پیام","message_targets"),("مخاطبان","message_targets"),("وضعیت خواندن","message_reads")],
"reports":[("کارنامه‌ها","report_cards"),("نسخه‌های کارنامه","report_card_snapshots"),("نمرات","grades"),("حضور و غیاب","attendance"),("ارزیابی دانش‌آموزان","student_grades"),("گزارش هوشمند","ai_smart_reports")],
"schedule":[("برنامه هفتگی","weekly_schedule"),("برنامه تولیدشده","generated_weekly_schedule"),("برنامه امتحانات","exam_schedule"),("کلاس‌های دبیران","teacher_classes"),("صندلی امتحانی","exam_seat_assignments")],
"settings":[("تنظیمات حساب","account_settings"),("مشخصات مدرسه","school_profile"),("ساختار کلاس‌ها","school_class_config"),("حساب‌های سامانه","users")],
"student_info":[("اطلاعات شخصی","students"),("پایه و کلاس","student_class_info"),("نمرات","student_grades"),("حضور و غیاب","attendance"),("تکالیف","assignments"),("کارنامه","report_cards")]
}

FRIENDLY = {
"school_profile":"مشخصات مدرسه","school_class_config":"ساختار کلاس‌ها","users":"حساب‌های سامانه","students":"دانش‌آموزان","teachers":"دبیران","staff":"کادر و کارکنان","teacher_classes":"کلاس‌های دبیران","lesson_plans":"طرح درس","attendance":"حضور و غیاب","grades":"نمرات","student_grades":"ارزیابی دانش‌آموزان","assignments":"تکالیف","parents":"اولیا","parent_children":"ارتباط ولی و فرزند","parent_meetings":"جلسات اولیا","finance_accounts":"حساب‌های مالی","finance_transactions":"تراکنش‌های مالی","finance_donations":"کمک‌های داوطلبانه","payment_offers":"گزینه‌های پرداخت","payment_attempts":"درخواست‌های پرداخت","payment_records":"سوابق پرداخت","online_classes":"کلاس‌های آنلاین","online_class_sessions":"جلسات آنلاین","online_class_students":"دانش‌آموزان کلاس","online_class_teachers":"دبیران کلاس","educational_activities":"فعالیت‌های پرورشی","school_events":"رویدادهای مدرسه","counseling_records":"سوابق مشاوره","counseling_followups":"پیگیری مشاوره","smart_board_content":"محتوای تابلو","smart_board_activities":"فعالیت‌های تابلو","smart_board_quizzes":"آزمون‌های کوتاه","smart_board_whiteboards":"تخته‌های آموزشی","ai_assistant_sessions":"جلسات دستیار","ai_questions":"پرسش‌های هوشمند","ai_smart_reports":"گزارش‌های هوشمند","messages":"پیام‌ها","message_targets":"مخاطبان پیام","message_reads":"وضعیت خواندن","report_cards":"کارنامه‌ها","report_card_snapshots":"نسخه‌های کارنامه","weekly_schedule":"برنامه هفتگی","generated_weekly_schedule":"برنامه تولیدشده","exam_schedule":"برنامه امتحانات","account_settings":"تنظیمات حساب","teacher_exams":"آزمون‌های آنلاین","discipline_records":"موارد انضباطی","educational_followups":"پیگیری‌های آموزشی","academic_followups":"پیگیری‌های درسی","certificate_requests":"درخواست گواهی اشتغال به تحصیل","activity_offers":"مسابقات و فعالیت‌ها","activity_registrations":"ثبت‌نام فعالیت‌ها","student_council":"انتخابات شورای دانش‌آموزی","basij_registration":"عضویت بسیج دانش‌آموزی","school_ally":"طرح همیار مدرسه","school_mayor":"طرح شهردار مدرسه","cultural_competitions":"مسابقات فرهنگی","art_competitions":"مسابقات هنری","sport_competitions":"مسابقات ورزشی","morning_leaders":"مکبر","qari_registration":"قاری برنامه ظهرگاهی","morning_ceremony":"مراسم ظهرگاهی","student_referrals":"ارجاع دانش‌آموز","teacher_parent_meetings":"درخواست ملاقات اولیا","parent_meeting_requests":"درخواست ملاقات","khwarizmi_registrations":"جشنواره خوارزمی","monthly_report_cards":"کارنامه ماهیانه","class_seat_assignments":"شماره صندلی کلاسی","exam_seat_assignments":"شماره صندلی امتحانی","assignment_submissions":"ارسال تکالیف","parent_activities":"فعالیت‌های اولیا","student_class_info":"پایه و کلاس"
}

COLUMNS = {
    "id":"شناسه", "first_name":"نام", "last_name":"نام خانوادگی", "national_code":"کد ملی", "grade":"پایه",
    "class_name":"کلاس", "phone":"تلفن", "subject":"درس", "teacher_name":"دبیر", "score":"نمره",
    "max_score":"حداکثر نمره", "status":"وضعیت", "amount":"مبلغ", "title":"عنوان", "description":"توضیحات",
    "created_at":"تاریخ ثبت", "attendance_date":"تاریخ حضور", "exam_date":"تاریخ آزمون", "event_date":"تاریخ رویداد",
    "start_time_shamsi":"شروع", "end_time_shamsi":"پایان", "role":"نقش", "email":"ایمیل", "username":"نام کاربری",
    "term":"نوبت", "academic_year":"سال تحصیلی", "active":"فعال", "teacher_id":"شناسه دبیر", "student_id":"شناسه دانش‌آموز",
    "content":"محتوا", "question":"سؤال", "question_type":"نوع سؤال", "published":"منتشرشده", "duration":"مدت",
    "share_code":"کد اشتراک", "target_class_name":"کلاس مقصد", "start_at":"شروع", "end_at":"پایان",
}

HIDDEN = {"id", "created_at", "updated_at", "deleted_at"}

# Business-specific columns for each subpanel.
TABLE_FIELDS = {
    "students":["first_name","last_name","national_code","grade","class_name","phone"],
    "teachers":["first_name","last_name","subject","phone","national_code"],
    "staff":["first_name","last_name","role","phone"],
    "parents":["first_name","last_name","national_code","phone"],
    "parent_children":["parent_id","student_id","relationship","status"],
    "teacher_classes":["teacher_name","subject","grade","class_name","academic_year"],
    "attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],
    "grades":["student_id","teacher_id","subject","score","max_score","term"],
    "student_grades":["student_id","subject","score","max_score","term","academic_year"],
    "assignments":["student_id","teacher_id","title","subject","class_name","status"],
    "lesson_plans":["teacher_name","subject","grade","class_name","title","description"],
    "school_events":["title","event_date","status","description"],
    "weekly_schedule":["day_of_week","period","class_name","subject","teacher_name","grade"],
    "generated_weekly_schedule":["day_of_week","period","class_name","subject","teacher_name","grade"],
    "exam_schedule":["exam_date","subject","grade","class_name","start_at","end_at"],
    "report_cards":["student_id","grade","term","academic_year","status"],
    "report_card_snapshots":["student_id","term","academic_year","created_at"],
    "finance_accounts":["title","account_type","account_number","balance","status"],
    "finance_transactions":["title","amount","transaction_type","account_id","status","created_at"],
    "finance_donations":["title","amount","status","description","created_at"],
    "payment_offers":["title","amount","payment_reason","target_type","active","status"],
    "payment_attempts":["student_id","offer_id","amount","status","created_at"],
    "payment_records":["student_id","amount","status","gateway","created_at"],
    "online_classes":["title","subject","teacher","grade","class_name","status","start_time_shamsi","end_time_shamsi"],
    "online_class_sessions":["class_id","started_at","ended_at","status"],
    "online_class_students":["class_id","student_id","student_name","status"],
    "online_class_teachers":["class_id","teacher_id","teacher_name","status"],
    "smart_board_content":["title","content","status","created_at"],
    "smart_board_activities":["title","description","status","created_at"],
    "smart_board_quizzes":["title","question","question_type","correct_answer","points"],
    "smart_board_whiteboards":["title","class_id","teacher_id","status"],
    "educational_activities":["title","description","event_date","status"],
    "parent_meetings":["title","event_date","class_name","status","description"],
    "counseling_records":["student_id","counselor_id","subject","description","status","created_at"],
    "counseling_followups":["student_id","counselor_id","followup_date","description","status"],
    "ai_questions":["question","answer","category","created_at"],
    "ai_assistant_sessions":["title","status","created_at","updated_at"],
    "ai_smart_reports":["title","report_type","status","created_at"],
    "messages":["title","body","audience_type","audience_value","status","created_at"],
    "message_targets":["message_id","target_role","target_name","target_class_name","status"],
    "message_reads":["message_id","reader_id","read_at"],
    "school_profile":["title","description","academic_year","status"],
    "school_class_config":["grade","class_name","capacity","academic_year","status"],
    "users":["username","email","role","status","created_at"],
    "account_settings":["username","email","role","status"],
    "teacher_exams":["title","subject","grade","class_name","exam_type","duration","published","passing_score"],
    "quiz_questions":["quiz_id","question","question_type","correct_answer","points","auto_grade"],
    "discipline_records":["student_id","discipline_type","record_date","decision_type","deduct_score","referral_to","description"],
    "educational_followups":["student_id","followup_date","followup_items","decision"],
    "academic_followups":["student_id","followup_date","followup_items","decision"],
    "certificate_requests":["student_id","student_name","destination","request_date","status","executive_note"],
    "parent_meeting_requests":["student_id","parent_id","target_type","target_person","requested_date","reason","status"],
    "student_referrals":["student_id","teacher_id","referral_to","reason","referral_date","status"],
    "khwarizmi_registrations":["title","category","grade","class_name","student_id","status"],
    "assignment_submissions":["assignment_id","student_id","file_url","answer_text","submitted_at","status"],
    "class_seat_assignments":["class_id","student_id","seat_number","academic_year"],
    "exam_seat_assignments":["exam_id","student_id","subject","exam_date","seat_number"],
    "monthly_report_cards":["student_id","month_name","active","created_at"],
    "parent_activities":["title","activity_type","event_date","active","description"],
    "program_activations":["program_key","title","active","activated_by"],
    "lesson_plan_entries":["teacher_id","subject","weekly_sessions","session_no","teaching_amount","teaching_date","teaching_title","activity_type"],
    "teacher_parent_meetings":["teacher_id","student_id","parent_id","requested_date","status","manager_status","reason"],
    "morning_ceremony":["ceremony_date","title","qari_name","leader_name","program"],
    "activity_programs":["activity_key","title","category","active","amount","settings"],
}

# Explicit write policy. Reads remain available through the existing API for all visible tables.
EDITABLE = {
    "manager": {table for items in SUBMENUS.values() for _, table in items},
    "educational": {"teacher_classes","lesson_plans","attendance","grades","student_grades","assignments","weekly_schedule","exam_schedule","teacher_exams"},
    "executive": {"students","parents","parent_children","staff","attendance","school_events","school_class_config","messages"},
    "cultural": {"educational_activities","school_events","messages","smart_board_content"},
    "advisor": {"counseling_records","counseling_followups","messages"},
    "teacher": {"attendance","grades","student_grades","assignments","lesson_plans","teacher_exams"},
}

FORMS = {
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

class Surface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(11), spacing=dp(6), size_hint_y=None, **kwargs)
        with self.canvas.before:
            Color(*CARD)
            self.bg = RoundedRectangle(radius=[dp(16)])
        self.bind(pos=self._sync, size=self._sync)
    def _sync(self,*_):
        self.bg.pos=self.pos; self.bg.size=self.size

class ModuleWorkspaceScreen(Screen):
    """Reusable, touch-first, RTL operational workspace backed by the real Supabase API."""
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state=app_state; self.route="management"; self.return_to="dashboard"; self.table=None; self.rows=[]; self._build()

    def label(self,text,size="11sp",color=SECONDARY,bold=False,center=False):
        w=Label(text=rtl_text(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,halign="center" if center else "right",valign="middle")
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def btn(self,text,cb,color=PRIMARY,h=dp(40),width=None):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="10sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=h)
        if width is not None: b.size_hint_x=None; b.width=width
        b.bind(on_release=cb); return b

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(6))
        top=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        top.add_widget(self.btn("‹ بازگشت",self.go_back,PRIMARY,dp(40),dp(78)))
        self.title=self.label(APP_NAME,"18sp",PRIMARY,True,"center"); top.add_widget(self.title)
        top.add_widget(self.btn("⌂",self.go_dashboard,PRIMARY,dp(40),dp(45)))
        root.add_widget(top)
        root.add_widget(self.label(f"{SCHOOL_NAME}  •  سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}","9sp",SECONDARY,False,"center"))
        self.status=self.label("اتصال فعال • اطلاعات واقعی سامانه","9sp",SUCCESS,True,"center"); root.add_widget(self.status)
        self.subscroll=ScrollView(do_scroll_x=True,do_scroll_y=False,size_hint_y=None,height=dp(49))
        self.subbar=BoxLayout(orientation="horizontal",spacing=dp(5),size_hint_x=None)
        self.subbar.bind(minimum_width=self.subbar.setter("width")); self.subscroll.add_widget(self.subbar); root.add_widget(self.subscroll)
        self.body=BoxLayout(orientation="vertical",spacing=dp(6)); root.add_widget(self.body); self.add_widget(root)

    def role(self):
        raw=str(getattr(self.app_state,"role","student") or "student").strip().lower()
        return {"admin":"manager","administrator":"manager","مدیر":"manager","مدیریت":"manager","معاون آموزشی":"educational","معاون اجرایی":"executive","معاون پرورشی":"cultural","مشاور":"advisor","دبیر":"teacher","معلم":"teacher","دانش‌آموز":"student","ولی":"parent","اولیا":"parent"}.get(raw,raw)

    def can_write(self,table): return table in EDITABLE.get(self.role(),set())

    def set_module(self,route,return_to="dashboard"):
        self.route=route if route in SUBMENUS else "management"; self.return_to=return_to or "dashboard"; self.table=None; self.render()

    load_module=set_module

    def render(self):
        self.body.clear_widgets(); self.subbar.clear_widgets(); items=SUBMENUS[self.route]
        self.title.text=rtl_text(dict(items).get(items[0][1],items[0][0]) if items else self.route)
        for text,table in items:
            b=self.btn(text,lambda *_a,t=table:self.open_table(t),PRIMARY if table==self.table else (0.10,0.32,0.50,1),dp(39),dp(max(92, len(text)*9+42)))
            self.subbar.add_widget(b)
        if self.table:
            self.open_table(self.table,refresh_subbar=False); return
        hero=Surface(height=dp(112))
        hero.add_widget(self.label(dict(items).get(items[0][1],items[0][0]) if items else "پنل","21sp",PRIMARY,True,"center"))
        hero.add_widget(self.label("محیط عملیاتی یکپارچه • همه زیرپنل‌ها از همین داده‌های واقعی سامانه استفاده می‌کنند","10sp",SECONDARY,False,"center"))
        hero.add_widget(self.label(f"{len(items)} زیرپنل فعال برای این نقش","9sp",SUCCESS,True,"center")); self.body.add_widget(hero)
        stats=BoxLayout(size_hint_y=None,height=dp(76),spacing=dp(6))
        for caption,value in [("زیرپنل‌ها",str(len(items))), ("قابل ویرایش",str(sum(1 for _,t in items if self.can_write(t)))), ("منبع داده","Supabase")]:
            c=Surface(height=dp(70)); c.add_widget(self.label(value,"19sp",PRIMARY,True,"center")); c.add_widget(self.label(caption,"9sp",SECONDARY,False,"center")); stats.add_widget(c)
        self.body.add_widget(stats)
        scroll=ScrollView(do_scroll_x=False); grid=GridLayout(cols=1,spacing=dp(6),size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        for i,(text,table) in enumerate(items,1):
            c=Surface(height=dp(82)); row=BoxLayout(spacing=dp(5))
            badge=BoxLayout(size_hint_x=None,width=dp(45)); badge.add_widget(self.label(f"{i:02d}","12sp",WHITE,True,"center")); self._badge(badge)
            row.add_widget(badge); row.add_widget(self.label(text,"13sp",PRIMARY,True)); row.add_widget(self.btn("ورود",lambda *_a,t=table:self.open_table(t),SUCCESS if self.can_write(table) else PRIMARY,dp(40),dp(74)))
            c.add_widget(row); c.add_widget(self.label(("عملیات ثبت/ویرایش/حذف فعال" if self.can_write(table) else "مشاهده اطلاعات واقعی بر اساس سطح دسترسی"),"8sp",SECONDARY,False,"right")); grid.add_widget(c)
        scroll.add_widget(grid); self.body.add_widget(scroll)

    def _badge(self,w):
        with w.canvas.before:
            Color(*PRIMARY); bg=RoundedRectangle(radius=[dp(9)])
        w.bind(pos=lambda o,v:setattr(bg,"pos",v),size=lambda o,v:setattr(bg,"size",v))

    def open_table(self,table,refresh_subbar=True):
        self.table=table
        if refresh_subbar:
            self.render(); return
        self.body.clear_widgets(); self.title.text=rtl_text(FRIENDLY.get(table,table))
        hero=Surface(height=dp(76)); line=BoxLayout(size_hint_y=None,height=dp(34),spacing=dp(5)); line.add_widget(self.btn("‹ زیرپنل‌ها",lambda *_:self._back_to_submenus(),PRIMARY,dp(34),dp(82))); line.add_widget(self.label(FRIENDLY.get(table,table),"16sp",PRIMARY,True,"center")); line.add_widget(self.btn("↻",lambda *_:self.load_table(),PRIMARY,dp(34),dp(45))); hero.add_widget(line)
        self.search=TextInput(hint_text=rtl_text("جستجو در همین زیرپنل"),font_name=font_name(),font_size="10sp",halign="right",multiline=False,size_hint_y=None,height=dp(32),padding=[dp(8),dp(5)]); hero.add_widget(self.search); self.body.add_widget(hero)
        bar=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(5));
        if self.can_write(table): bar.add_widget(self.btn("＋ ثبت جدید",lambda *_:self.editor(table,None),SUCCESS,dp(38)))
        bar.add_widget(self.btn("جستجو",lambda *_:self.render_rows(self.filtered()),PRIMARY,dp(38))); bar.add_widget(self.btn("پاک کردن",lambda *_:self.clear_search(),SECONDARY,dp(38))); self.body.add_widget(bar)
        self.area=BoxLayout(orientation="vertical"); self.body.add_widget(self.area); self.load_table()

    def _back_to_submenus(self): self.table=None; self.render()
    def clear_search(self): self.search.text=""; self.render_rows(self.rows)
    def filtered(self):
        q=str(getattr(self,'search',None).text if hasattr(self,'search') else '').strip().lower(); return self.rows if not q else [r for r in self.rows if q in ' '.join(str(v) for v in r.values()).lower()]

    def load_table(self):
        table=self.table; self.status.text=rtl_text("در حال دریافت اطلاعات واقعی…"); self.status.color=SECONDARY
        def work():
            try: rows=self.app_state.api.table_select(table,{"limit":"150"}) or []; rows=rows if isinstance(rows,list) else []; Clock.schedule_once(lambda *_:self.loaded(rows,None),0)
            except Exception as exc: Clock.schedule_once(lambda *_:self.loaded([],str(exc)),0)
        Thread(target=work,daemon=True).start()

    def loaded(self,rows,error):
        self.rows=rows
        if error: self.status.text=rtl_text("خطا: "+error); self.status.color=(.8,.15,.15,1)
        else: self.status.text=rtl_text(f"{len(rows)} رکورد واقعی • {FRIENDLY.get(self.table,self.table)}"); self.status.color=SUCCESS
        self.render_rows(rows)

    def render_rows(self,rows):
        self.area.clear_widgets()
        if not rows:
            e=Surface(height=dp(130)); e.add_widget(self.label("رکوردی برای نمایش وجود ندارد","16sp",PRIMARY,True,"center")); e.add_widget(self.label("در صورت داشتن دسترسی، از «ثبت جدید» استفاده کنید.","9sp",SECONDARY,False,"center")); self.area.add_widget(e); return
        preferred = TABLE_FIELDS.get(self.table, [])
        keys = [k for k in preferred if any(isinstance(r,dict) and k in r for r in rows)]
        if not keys:
            for r in rows:
                if isinstance(r,dict):
                    for k in r:
                        if k not in HIDDEN and k not in keys: keys.append(k)
        keys=keys[:8]; totalw=max(dp(440),dp(135)*max(2,len(keys))+dp(140 if self.can_write(self.table) else 0))
        scroll=ScrollView(do_scroll_x=True); content=BoxLayout(orientation='vertical',size_hint=(None,None),width=totalw,spacing=dp(3),padding=dp(2)); content.bind(minimum_height=content.setter('height'))
        header=BoxLayout(size_hint=(None,None),width=totalw,height=dp(40),spacing=dp(2));
        for k in keys: header.add_widget(self.label(COLUMNS.get(k,k),"8sp",WHITE,True,"center"))
        if self.can_write(self.table): header.add_widget(self.label("عملیات","8sp",WHITE,True,"center"))
        self._header(header); content.add_widget(header)
        for i,r in enumerate(rows,1): content.add_widget(self.row(r,i,keys,totalw))
        scroll.add_widget(content); self.area.add_widget(scroll)

    def _header(self,w):
        with w.canvas.before: Color(*PRIMARY); bg=RoundedRectangle(radius=[dp(8)])
        w.bind(pos=lambda o,v:setattr(bg,'pos',v),size=lambda o,v:setattr(bg,'size',v))

    def row(self,r,index,keys,totalw):
        b=BoxLayout(size_hint=(None,None),width=totalw,height=dp(50),spacing=dp(2),padding=[dp(2),dp(2)])
        for k in keys:
            s=str(r.get(k,'')); b.add_widget(self.label(s[:24]+'…' if len(s)>25 else s,"8sp",SECONDARY,False,'center'))
        if self.can_write(self.table):
            a=BoxLayout(size_hint_x=None,width=dp(138),spacing=dp(3)); a.add_widget(self.btn('ویرایش',lambda *_a,x=dict(r):self.editor(self.table,x),PRIMARY,dp(44))); a.add_widget(self.btn('حذف',lambda *_a,x=dict(r):self.confirm_delete(self.table,x),(0.72,.16,.18,1),dp(44))); b.add_widget(a)
        if index%2==0:
            with b.canvas.before: Color(.94,.97,.985,1); bg=RoundedRectangle(radius=[dp(6)])
            b.bind(pos=lambda o,v:setattr(bg,'pos',v),size=lambda o,v:setattr(bg,'size',v))
        return b

    def editor(self,table,row):
        fields=[k for k in (FORMS.get(table) or self._infer(row)) if k not in HIDDEN]
        root=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(6)); sc=ScrollView(do_scroll_x=False); form=GridLayout(cols=1,spacing=dp(5),size_hint_y=None); form.bind(minimum_height=form.setter('height')); inputs={}
        for f in fields:
            form.add_widget(self.label(COLUMNS.get(f,f),"9sp",PRIMARY,True)); ti=TextInput(text='' if row is None else str(row.get(f,'')),font_name=font_name(),font_size='10sp',halign='right',multiline=False,size_hint_y=None,height=dp(40),padding=[dp(8),dp(6)]); inputs[f]=ti; form.add_widget(ti)
        sc.add_widget(form); root.add_widget(sc); actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5)); p=Popup(title=rtl_text(('ویرایش' if row else 'ثبت جدید')+' • '+FRIENDLY.get(table,table)),content=root,size_hint=(.94,.88),auto_dismiss=False); actions.add_widget(self.btn('انصراف',lambda *_:p.dismiss(),SECONDARY,dp(40))); actions.add_widget(self.btn('ذخیره',lambda *_:self.save(table,row,inputs,p),SUCCESS,dp(40))); root.add_widget(actions); p.open()

    def _infer(self,row): return [k for k in (row or {}).keys() if k not in HIDDEN] or ['title','description','status']

    def save(self,table,row,inputs,p):
        payload={k:v.text.strip() for k,v in inputs.items() if v.text.strip()!=''}
        if not payload: self.message('ثبت اطلاعات','حداقل یک فیلد را وارد کنید.'); return
        p.dismiss(); self.status.text=rtl_text('در حال ذخیره اطلاعات واقعی…')
        def work():
            try:
                if row is None: self.app_state.api.table_insert(table,payload); msg='رکورد جدید با موفقیت ثبت شد.'
                else:
                    rid=row.get('id')
                    if rid is None: raise RuntimeError('شناسه رکورد برای ویرایش پیدا نشد.')
                    self.app_state.api.table_update(table,{'id':'eq.'+str(rid)},payload); msg='رکورد با موفقیت ویرایش شد.'
                Clock.schedule_once(lambda *_:self.after_write(msg),0)
            except Exception as exc: Clock.schedule_once(lambda *_:self.write_error(str(exc)),0)
        Thread(target=work,daemon=True).start()

    def after_write(self,msg): self.status.text=rtl_text(msg); self.status.color=SUCCESS; self.load_table()
    def write_error(self,msg): self.status.text=rtl_text('ذخیره انجام نشد: '+msg); self.status.color=(.8,.15,.15,1)

    def confirm_delete(self,table,row):
        rid=row.get('id');
        if rid is None: self.message('حذف رکورد','شناسه رکورد موجود نیست.'); return
        root=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8)); root.add_widget(self.label('آیا از حذف این رکورد مطمئن هستید؟','14sp',PRIMARY,True,'center')); root.add_widget(self.label('این عملیات روی اطلاعات واقعی سامانه انجام می‌شود.','9sp',SECONDARY,False,'center')); actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5)); p=Popup(title=rtl_text('تأیید حذف'),content=root,size_hint=(.88,.36),auto_dismiss=False); actions.add_widget(self.btn('انصراف',lambda *_:p.dismiss(),SECONDARY,dp(40))); actions.add_widget(self.btn('حذف قطعی',lambda *_:self.delete(table,rid,p),(0.72,.16,.18,1),dp(40))); root.add_widget(actions); p.open()

    def delete(self,table,rid,p):
        p.dismiss(); self.status.text=rtl_text('در حال حذف اطلاعات واقعی…')
        def work():
            try: self.app_state.api.table_delete(table,{'id':'eq.'+str(rid)}); Clock.schedule_once(lambda *_:self.after_write('رکورد با موفقیت حذف شد.'),0)
            except Exception as exc: Clock.schedule_once(lambda *_:self.write_error(str(exc)),0)
        Thread(target=work,daemon=True).start()

    def message(self,title,text):
        root=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8)); root.add_widget(self.label(text,'10sp',SECONDARY,False,'center')); p=Popup(title=rtl_text(title),content=root,size_hint=(.88,.34)); root.add_widget(self.btn('متوجه شدم',lambda *_:p.dismiss(),PRIMARY,dp(40))); p.open()

    def go_dashboard(self,*_):
        if self.manager: self.manager.current=self.return_to or 'dashboard'
    def go_back(self,*_): self.go_dashboard()
