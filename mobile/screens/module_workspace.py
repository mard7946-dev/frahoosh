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
from kivy.uix.behaviors import ButtonBehavior

from mobile.config import APP_NAME, CARD, PRIMARY, SCHOOL_NAME, SCHOOL_YEAR, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text, PersianTextInput

class SelectableRow(ButtonBehavior, BoxLayout):
    """Touch-friendly table row: selecting it enables the module-level Edit/Delete buttons."""
    def __init__(self, owner=None, record=None, **kwargs):
        super().__init__(**kwargs)
        self.owner = owner
        self.record = dict(record or {})
    def on_release(self):
        if self.owner is not None:
            self.owner.selected_row = self.record
            try:
                self.owner.status.text = rtl_text("رکورد انتخاب شد؛ از ویرایش یا حذف استفاده کنید.")
                self.owner.status.color = SUCCESS
            except Exception:
                pass

# One shared operational vocabulary for Android and the future web client.
# Both clients must bind these keys to the same Supabase tables and field names.
SUBMENUS = {
"management":[("اطلاعات مدرسه","school_profile"),("دانش‌آموزان","students"),("دبیران","teachers"),("کادر و کارکنان","staff"),("پایه و کلاس‌ها","school_class_config"),("حساب‌های سامانه","users"),("رویدادها","school_events"),("صندوق پیام","messages"),("کارنامه‌ها","report_cards"),("برنامه هفتگی","weekly_schedule"),("آزمون آنلاین","teacher_exams"),("کلاس آنلاین","online_classes"),("مالی","finance_accounts"),("پرداخت آنلاین","payment_offers"),("تابلو هوشمند","smart_board_content"),("نمونه کلاس هوشمند","smart_class_preview"),("ملاقات‌ها","meeting_requests"),("گزارش‌های مدیریتی","report_cards")],
"educational":[("ملاقات‌ها","meeting_requests"),("پرونده اطلاعاتی دانش‌آموز","students"),("پرونده پرسنلی همکاران","staff"),("کلاس‌های دبیران","teacher_classes"),("فعال‌سازی کلاس آنلاین","online_classes"),("برنامه هفتگی","weekly_schedule"),("برنامه امتحانی","exam_schedule"),("پیگیری آموزشی","educational_followups"),("پیگیری درسی","academic_followups"),("پیگیری انضباطی","discipline_records"),("ثبت انضباطی","discipline_records"),("نمرات و کارنامه‌ها","student_grades"),("گزارش آموزشی هوشمند","ai_smart_reports"),("جشنواره خوارزمی","khwarizmi_registrations"),("آزمون آنلاین","teacher_exams"),("صندوق پیام","messages")],
"executive":[("ملاقات با اولیا","meeting_requests"),("پرونده دانش‌آموزی","students"),("پرونده پرسنلی کارکنان","staff"),("اولیا و ارتباط فرزند","parent_children"),("فعال‌سازی برنامه هفتگی","weekly_schedule"),("فعال‌سازی کارنامه ماهیانه","monthly_report_cards"),("فعال‌سازی کارنامه مستمر و پایان ترم","report_cards"),("ثبت انضباطی","discipline_records"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("کلاس‌های آنلاین","online_classes"),("رویدادها و مراسمات","school_events"),("صندوق پیام","messages")],
"cultural":[("ملاقات با اولیا","meeting_requests"),("پیام‌های پرورشی","messages"),("ایجاد مسابقات","activity_offers"),("مسابقات فرهنگی","cultural_competitions"),("مسابقات هنری","art_competitions"),("مسابقات ورزشی","sport_competitions"),("فعالیت‌ها و مراسمات","educational_activities"),("انتخابات شورای دانش‌آموزی","student_council"),("بسیج دانش‌آموزی","basij_registration"),("شهردار مدرسه","school_mayor"),("مکبر","morning_leaders"),("قاری برنامه ظهرگاهی","qari_registration"),("جدول مراسم ظهرگاهی","morning_ceremony"),("ثبت انضباطی","discipline_records"),("صندوق پیام","messages")],
"advisor":[("ملاقات با اولیا","meeting_requests"),("پرونده‌های مشاوره","counseling_records"),("پیگیری جلسات","counseling_followups"),("دانش‌آموزان","students"),("اولیا","parent_children"),("ملاقات و درخواست جلسه","meeting_requests"),("گزارش‌های مشاوره","report_cards"),("صندوق پیام","messages")],
"teachers":[("کلاس‌های من","teacher_classes"),("طرح درس","lesson_plans"),("برنامه هفتگی","weekly_schedule"),("کلاس‌های آنلاین فعال","online_classes"),("آزمون آنلاین","teacher_exams"),("حضور و غیاب","attendance"),("نمرات درسی","grades"),("تکالیف","assignments"),("موارد انضباطی","discipline_records"),("ارجاع دانش‌آموز","student_referrals"),("ملاقات با اولیا","meeting_requests"),("صندوق پیام","messages")],
"students":[("اطلاعات شخصی","students"),("پایه و کلاس","student_class_info"),("نمرات","student_grades"),("وضعیت حضور و غیاب","attendance"),("کلاس‌های آنلاین فعال","online_classes"),("شرکت در فعالیت‌ها","activity_registrations"),("انتخابات شورای دانش‌آموزی","student_council"),("بسیج دانش‌آموزی","basij_registration"),("همیار مدرسه","school_ally"),("شهردار مدرسه","school_mayor"),("ارسال تکالیف","assignment_submissions"),("برنامه هفتگی","weekly_schedule"),("برنامه امتحانی","exam_schedule"),("شماره صندلی کلاسی","class_seat_assignments"),("شماره صندلی امتحانی","exam_seat_assignments"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("صندوق پیام","messages"),("کمک‌های داوطلبانه / پرداخت آنلاین","payment_offers")],
"parents":[("انتخاب یک یا چند دانش‌آموز","parent_children"),("اطلاعات دانش‌آموز","students"),("نمرات کلاسی و امتحانی","student_grades"),("حضور و غیاب","attendance"),("کارنامه ماهیانه","monthly_report_cards"),("کارنامه مستمر و پایان ترم","report_cards"),("ملاقات با دبیر","meeting_requests"),("ملاقات با کادر","meeting_requests"),("ملاقات با مشاور","meeting_requests"),("ملاقات با مدیریت","meeting_requests"),("انتخابات و مراسمات انجمن اولیا","parent_activities"),("کلاس آموزش خانواده","parent_activities"),("بهداشت روان","parent_activities"),("کمک‌های داوطلبانه / پرداخت آنلاین","payment"),("صندوق پیام","messages")],
"finance":[("حساب‌ها","finance_accounts"),("تراکنش‌ها","finance_transactions"),("کمک‌های داوطلبانه","finance_donations"),("تعریف گزینه پرداخت","payment_offers"),("درخواست‌های پرداخت","payment_attempts"),("سوابق پرداخت","payment_records")],
"online":[("کلاس‌های آنلاین","online_classes"),("جلسات","online_class_sessions"),("دانش‌آموزان کلاس","online_class_students"),("دبیران کلاس","online_class_teachers"),("حضور آنلاین","online_attendance"),("تخته کلاس","smart_board_whiteboards")],
"smart_board":[("محتوای آموزشی","smart_board_content"),("فعالیت‌ها","smart_board_activities"),("آزمون‌های کوتاه","smart_board_quizzes"),("تخته‌های آموزشی","smart_board_whiteboards")],
"ai":[("گزارش تحلیلی کلاس به کلاس","ai_smart_reports"),("گزارش تحلیلی دانش‌آموز","ai_smart_reports"),("پرسش هوشمند","ai_questions"),("جلسات دستیار","ai_assistant_sessions")],
"messages":[("صندوق ورودی","messages"),("ارسال پیام","message_targets"),("مخاطبان","message_targets"),("وضعیت خواندن","message_reads")],
"reports":[("کارنامه‌ها","report_cards"),("نسخه‌های کارنامه","report_card_snapshots"),("نمرات","grades"),("حضور و غیاب","attendance"),("ارزیابی دانش‌آموزان","student_grades"),("گزارش هوشمند","ai_smart_reports")],
"schedule":[("برنامه هفتگی","weekly_schedule"),("برنامه تولیدشده","generated_weekly_schedule"),("برنامه امتحانات","exam_schedule"),("کلاس‌های دبیران","teacher_classes"),("صندلی امتحانی","exam_seat_assignments")],
"settings":[("تنظیمات حساب","account_settings"),("مشخصات مدرسه","school_profile"),("ساختار کلاس‌ها","school_class_config"),("حساب‌های سامانه","users")],
"student_info":[("اطلاعات شخصی","students"),("پایه و کلاس","student_class_info"),("نمرات","student_grades"),("حضور و غیاب","attendance"),("تکالیف","assignments"),("کارنامه","report_cards")]
}

# Canonical module catalog shared with the Web client. The large in-file map remains
# as a safe fallback for older APKs, but new builds always prefer the shared contract.
def _load_shared_catalog():
    import json
    from pathlib import Path
    candidates = [
        Path(__file__).resolve().parents[2] / "shared" / "module_catalog.json",
        Path.cwd() / "shared" / "module_catalog.json",
    ]
    for path in candidates:
        try:
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
                panels = data.get("panels") or {}
                friendly = data.get("friendly") or {}
                if panels:
                    return panels, friendly
        except Exception as exc:
            print("SHARED MODULE CATALOG ERROR:", repr(exc))
    return None, None

_shared_panels, _shared_friendly = _load_shared_catalog()
if _shared_panels:
    SUBMENUS = {k: [tuple(item) for item in v] for k, v in _shared_panels.items()}

FRIENDLY = {
"school_profile":"مشخصات مدرسه","school_class_config":"ساختار کلاس‌ها","users":"حساب‌های سامانه","students":"دانش‌آموزان","teachers":"دبیران","staff":"کادر و کارکنان","teacher_classes":"کلاس‌های دبیران","lesson_plans":"طرح درس","attendance":"حضور و غیاب","grades":"نمرات","student_grades":"ارزیابی دانش‌آموزان","assignments":"تکالیف","parents":"اولیا","parent_children":"ارتباط ولی و فرزند","parent_meetings":"جلسات اولیا","finance_accounts":"حساب‌های مالی","finance_transactions":"تراکنش‌های مالی","finance_donations":"کمک‌های داوطلبانه","payment_offers":"گزینه‌های پرداخت","payment_attempts":"درخواست‌های پرداخت","payment_records":"سوابق پرداخت","online_classes":"کلاس‌های آنلاین","online_class_sessions":"جلسات آنلاین","online_class_students":"دانش‌آموزان کلاس","online_class_teachers":"دبیران کلاس","educational_activities":"فعالیت‌های پرورشی","school_events":"رویدادهای مدرسه","counseling_records":"سوابق مشاوره","counseling_followups":"پیگیری مشاوره","smart_board_content":"محتوای تابلو","smart_board_activities":"فعالیت‌های تابلو","smart_board_quizzes":"آزمون‌های کوتاه","smart_board_whiteboards":"تخته‌های آموزشی","ai_assistant_sessions":"جلسات دستیار","ai_questions":"پرسش‌های هوشمند","ai_smart_reports":"گزارش‌های هوشمند","messages":"پیام‌ها","message_targets":"مخاطبان پیام","message_reads":"وضعیت خواندن","report_cards":"کارنامه‌ها","report_card_snapshots":"نسخه‌های کارنامه","weekly_schedule":"برنامه هفتگی","generated_weekly_schedule":"برنامه تولیدشده","exam_schedule":"برنامه امتحانات","account_settings":"تنظیمات حساب","teacher_exams":"آزمون‌های آنلاین","discipline_records":"موارد انضباطی","educational_followups":"پیگیری‌های آموزشی","academic_followups":"پیگیری‌های درسی","certificate_requests":"درخواست گواهی اشتغال به تحصیل","activity_offers":"مسابقات و فعالیت‌ها","activity_registrations":"ثبت‌نام فعالیت‌ها","student_council":"انتخابات شورای دانش‌آموزی","basij_registration":"عضویت بسیج دانش‌آموزی","school_ally":"طرح همیار مدرسه","school_mayor":"طرح شهردار مدرسه","cultural_competitions":"مسابقات فرهنگی","art_competitions":"مسابقات هنری","sport_competitions":"مسابقات ورزشی","morning_leaders":"مکبر","qari_registration":"قاری برنامه ظهرگاهی","morning_ceremony":"مراسم ظهرگاهی","student_referrals":"ارجاع دانش‌آموز","teacher_parent_meetings":"درخواست ملاقات اولیا","parent_meeting_requests":"درخواست ملاقات","meeting_requests":"ملاقات و درخواست جلسه","smart_class_preview":"نمونه کلاس هوشمند","khwarizmi_registrations":"جشنواره خوارزمی","monthly_report_cards":"کارنامه ماهیانه","class_seat_assignments":"شماره صندلی کلاسی","exam_seat_assignments":"شماره صندلی امتحانی","assignment_submissions":"ارسال تکالیف","parent_activities":"فعالیت‌های اولیا","student_class_info":"پایه و کلاس"
}

if _shared_friendly:
    FRIENDLY.update(_shared_friendly)

COLUMNS = {
    "id":"شناسه", "father_name":"نام پدر","mother_name":"نام مادر","birth_certificate_place":"محل صدور","birth_place":"محل تولد","religion":"دین","sect":"مذهب","nationality":"ملیت","student_phone":"شماره تماس دانش‌آموز","father_phone":"شماره تماس پدر","mother_phone":"شماره تماس مادر","personnel_code":"کد پرسنلی","service_years":"سابقه خدمت","discipline_type":"نوع مورد انضباطی","record_date":"تاریخ ثبت","decision_type":"نوع تصمیم","deduct_score":"میزان کسر نمره","referral_to":"ارجاع به","followup_date":"تاریخ پیگیری","followup_items":"موارد پیگیری‌شده","decision":"تصمیم","destination":"محل ارائه گواهی","request_date":"تاریخ درخواست","executive_note":"یادداشت معاون اجرایی","participation_type":"تیمی / انفرادی","team_members":"همگروهی‌ها","competition_type":"نوع مسابقه","payment_status":"وضعیت پرداخت","category":"دسته‌بندی","active":"فعال","activated_by":"فعال‌سازی توسط","reason":"علت","referral_date":"تاریخ ارجاع","requested_date":"تاریخ درخواست ملاقات","manager_status":"تأیید مدیر","file_url":"فایل","answer_text":"پاسخ","submitted_at":"زمان ارسال","seat_number":"شماره صندلی","month_name":"ماه","program_key":"کلید برنامه","account_type":"نوع حساب","account_number":"شماره حساب","balance":"موجودی","transaction_type":"نوع تراکنش","offer_id":"گزینه پرداخت","gateway":"درگاه","target_type":"نوع مخاطب","payment_reason":"علت پرداخت","audience_type":"نوع مخاطب","audience_value":"مخاطب","body":"متن پیام","target_role":"نقش مخاطب","target_name":"نام مخاطب","target_class_name":"کلاس مخاطب","first_name":"نام", "last_name":"نام خانوادگی", "national_code":"کد ملی", "grade":"پایه",
    "class_name":"کلاس", "phone":"تلفن", "subject":"درس", "teacher_name":"دبیر", "score":"نمره",
    "max_score":"حداکثر نمره", "status":"وضعیت", "amount":"مبلغ", "title":"عنوان", "description":"توضیحات",
    "created_at":"تاریخ ثبت", "attendance_date":"تاریخ حضور", "exam_date":"تاریخ آزمون", "event_date":"تاریخ رویداد",
    "start_time_shamsi":"شروع", "end_time_shamsi":"پایان", "role":"نقش", "email":"ایمیل", "username":"نام کاربری",
    "term":"نوبت", "academic_year":"سال تحصیلی", "active":"فعال", "teacher_id":"شناسه دبیر", "student_id":"شناسه دانش‌آموز", "student_code":"شماره دانش‌آموزی", "birth_date":"تاریخ تولد", "parent_phone":"شماره تماس ولی", "employee_code":"کد پرسنلی", "employment_status":"وضعیت استخدام", "work_experience":"سابقه کار", "teaching_hours":"ساعات تدریس", "grades":"پایه‌های تدریس", "settings":"تنظیمات", "invoice_no":"شماره فاکتور", "invoice_number":"شماره فاکتور", "reference":"شماره مرجع", "authority":"شماره پیگیری", "transaction_date":"تاریخ تراکنش", "donor_name":"نام پرداخت‌کننده", "payment_type":"نوع پرداخت", "payment_date":"تاریخ پرداخت",
    "content":"محتوا", "question":"سؤال", "question_type":"نوع سؤال", "published":"منتشرشده", "duration":"مدت",
    "share_code":"کد اشتراک", "target_class_name":"کلاس مقصد", "start_at":"شروع", "end_at":"پایان",
}

HIDDEN = {"id", "created_at", "updated_at", "deleted_at"}

# Business-specific columns for each subpanel.
TABLE_FIELDS = {
"students":["first_name","last_name","national_code","student_code","grade","class_name","phone","parent_phone","father_name","mother_name","birth_date","email","address","nationality","religion","sect"],
"teachers":["first_name","last_name","national_code","phone","email","subject","grades","employee_code","employment_status"],
"staff":["first_name","last_name","role","phone","work_experience","employee_code","national_code","religion","sect","employment_status","teaching_hours"],
"parents":["parent_username","student_id"],"parent_children":["parent_username","student_id"],
"teacher_classes":["teacher_id","teacher_name","subject","grade","class_name","active"],
"attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],
"grades":["student_id","teacher_id","subject","exam_name","score","grade_type","term","max_score","grade_date","title"],
"student_grades":["student_id","teacher_id","subject","class_name","assessment_type","assessment_title","score","coefficient","grade_date","term","manager_released"],
"assignments":["student_id","teacher_id","title","description","status","due_date","subject","class_name"],
"lesson_plans":["teacher_id","teacher_name","subject","grade","class_name","title","content","session_date","lesson_title","description","plan_date"],
"school_events":["title","description","event_date","status"],"weekly_schedule":["teacher","hours","grade","class_count","subject","bell_pattern","class_names","teacher_id","weekdays"],
"generated_weekly_schedule":["teacher","subject","grade","class_name","weekday","bell","week_index"],"exam_schedule":["subject","grade","start_date","end_date","weight","exam_date","duration","exam_start_time","exam_end_time"],
"report_cards":["student_id","term","average","description","grade_level","academic_year","report_date"],"report_card_snapshots":["student_id","term","academic_year","average","generated_date_shamsi"],
"finance_accounts":["title","balance"],"finance_transactions":["transaction_type","title","amount","category","description","transaction_date"],"finance_donations":["donor_name","amount","description","donation_date"],
"payment_offers":["title","amount","target_type","target_value","description","active","manual_amount","payment_reason","gateway_enabled"],"payment_attempts":["offer_id","student_id","payer_username","payer_role","amount","status","gateway_ref","description"],"payment_records":["student_id","parent_username","title","amount","payment_type","gateway","authority","reference","status","payment_date","description"],
"online_classes":["title","subject","lesson","teacher","grade","class_name","duration","pages","record","smart_board","quiz","camera","microphone","start_time","end_time","status","activated_by","join_url","meeting_url"],"online_class_sessions":["class_id","started_at","ended_at"],"online_class_students":["class_id","student_id","student_name"],"online_class_teachers":["class_id","teacher_id","teacher_name"],"online_attendance":["class_id","student_id","join_time","leave_time","status","last_activity"],
"smart_board_content":["title","content","class_id","teacher_id","content_date_shamsi"],"smart_board_activities":["title","activity_text","class_id","teacher_id","activity_date_shamsi"],"smart_board_quizzes":["title","question","option_a","option_b","option_c","option_d","correct_option","class_id","teacher_id","quiz_date_shamsi"],"smart_board_whiteboards":["title","content","class_id","teacher_id","board_date"],
"educational_activities":["title","subject","grade","class_name","teacher_id","student_id","description","activity_date","status"],"counseling_records":["student_name","visit_reason","recommendations","next_visit","reason_summary"],"counseling_followups":["student_id","subject","description","status"],
"ai_questions":["username","role","question","answer","student_id","answered_at","answer_date_shamsi"],"ai_assistant_sessions":["username","role","title","context","request_date_shamsi"],"ai_smart_reports":["title","report_type","target_type","target_id","report","created_by","report_date_shamsi"],
"messages":["sender","receiver","text","sender_user_id","sender_name","title","body","audience_type","audience_value"],"message_targets":["message_id","target_type","target_value","target_role","target_id","read_at"],"message_delivery":["message_id","username","received_at","seen_at"],
"school_profile":["school_name","school_code","principal_name","phone","address","academic_year","logo_path","request_date_shamsi"],"school_class_config":["total_classes","grade7_classes","grade8_classes","grade9_classes"],"users":["username","password","role","permissions","linked_student_id","linked_teacher_id","linked_staff_id","display_name"],"account_settings":["username","display_name","phone","email","preferences","national_code","role","auth_user_id"],
"teacher_exams":["teacher_id","title","subject","grade","class_name","exam_type","exam_date","duration","description","published","secure_mode","share_enabled","share_code","standard_mode","max_attempts","passing_score"],"quiz_questions":["quiz_id","question","option1","option2","option3","option4","correct_answer","points","question_type","image_url","options_json","accepted_answers","explanation","difficulty","cognitive_level","auto_grade","negative_score"],
"discipline_records":["student_id","teacher_id","title","description","priority","status","item_id","deduction","actor_username","actor_role","note"],"educational_followups":["student_id","followup_date","followup_items","decision","status"],"academic_followups":["student_id","followup_date","followup_items","decision","status"],"certificates":["student_id","title","code"],"parent_meetings":["student_id","teacher_id","parent_phone","reason","meeting_date","status"],
"meeting_requests":["requester_username","requester_role","requester_name","student_id","student_name","parent_username","parent_name","target_role","target_user_id","target_username","target_name","requested_date","requested_time","reason","description","status","manager_status","manager_note","educational_status","educational_note","final_date","final_time","final_note"],"student_registrations":["student_id","activity_id","activity_title","activity_kind","fee","payment_status","payment_url","payment_reference","registration_code","registration_date","status"],"cultural_activity_registrations":["activity_id","activity_title","activity_kind","student_id","student_name","fee","payment_status","registration_code","registration_date","status"],"student_referrals":["student_id","teacher_id","referral_to","reason","referral_date","status"],"teacher_activities":["teacher_id","student_id","title","activity_type","subject","score","description","activity_date"],"teacher_attendance":["student_id","teacher_id","class_name","subject","attendance_date","status","description"],"teacher_parent_meetings":["teacher_id","student_id","parent_id","requested_date","status","manager_status","reason"],"activity_offers":["title","category","event_date","active","amount","settings"],"activity_registrations":["activity_id","student_id","participation_type","team_members","competition_type","payment_status","status"],"khwarizmi_registrations":["title","category","grade","class_name","student_id","status"],"class_seats":["student_id","class_name","seat_no"],"exam_seats":["student_id","exam_name","seat_no"],"monthly_report_cards":["student_id","month_name","active"],"competitions":["title","category","start_date","end_date","status","description"],"executive_requests":["title","requester","status","description","role"],"executive_operations":["operation_type","title","student_id","class_name","description","status","operation_date","created_by"],"executive_reports":["title","report_type","student_id","class_name","payload","report_date","created_by"],"assets":["title","category","quantity","location","archived"],"archive_items":["title","student_id","location","description"],"backup_records":["file_path","backup_type","size_bytes","status","created_by"],"surveys":["title","description","status","audience","start_at","end_at","created_by"],"survey_questions":["survey_id","question","question_type","options","required","sort_order"],"survey_responses":["survey_id","respondent_username","respondent_role","student_id"],"program_activations":["program_key","title","active","activated_by"],"student_council":["student_id","student_name","election_year","status"],"basij_registration":["student_id","student_name","registration_date","status"],"school_ally":["student_id","student_name","role","status"],"school_mayor":["student_id","student_name","status"],"cultural_competitions":["title","category","start_date","end_date","status","description"],"art_competitions":["title","category","start_date","end_date","status","description"],"sport_competitions":["title","category","start_date","end_date","status","description"],"morning_leaders":["student_id","student_name","status"],"qari_registration":["student_id","student_name","status"],"morning_ceremony":["title","program_key","active","description"],"parent_activities":["title","description","activity_date","status"],"student_class_info":["student_id","grade","class_name","academic_year"],"message_reads":["message_id","username","read_at"],"certificate_requests":["student_id","student_name","destination","request_date","status","executive_note"],"parent_meeting_requests":["student_id","teacher_id","parent_phone","reason","meeting_date","status"],"survey_answers":["response_id","question_id","answer"]
}

# Explicit write policy. Reads remain available through the existing API for all visible tables.
EDITABLE = {
    "manager": {table for items in SUBMENUS.values() for _, table in items},
    "educational": {"meeting_requests","teacher_classes","lesson_plans","attendance","grades","student_grades","assignments","weekly_schedule","exam_schedule","teacher_exams","online_classes","discipline_records","educational_followups","academic_followups","khwarizmi_registrations","ai_smart_reports","staff","students"},
    "executive": {"meeting_requests","students","parents","parent_children","staff","attendance","school_events","school_class_config","messages","weekly_schedule","monthly_report_cards","report_cards","discipline_records","certificate_requests","online_classes","program_activations"},
    "cultural": {"meeting_requests","educational_activities","school_events","messages","smart_board_content","activity_offers","activity_registrations","student_council","basij_registration","school_ally","school_mayor","cultural_competitions","art_competitions","sport_competitions","morning_leaders","qari_registration","morning_ceremony","discipline_records","program_activations"},
    "advisor": {"meeting_requests","counseling_records","counseling_followups","messages"},
    "teacher": {"attendance","grades","student_grades","assignments","lesson_plans","lesson_plan_entries","teacher_exams","discipline_records","student_referrals","teacher_parent_meetings","messages"},
}

FORMS = {
    "students":["first_name","last_name","father_name","mother_name","national_code","birth_certificate_place","birth_place","religion","sect","nationality","student_phone","father_phone","mother_phone","grade","class_name"],
    "teachers":["first_name","last_name","father_name","national_code","personnel_code","birth_certificate_place","birth_place","nationality","religion","sect","service_years","phone","subject"],
    "staff":["first_name","last_name","father_name","national_code","personnel_code","birth_certificate_place","birth_place","nationality","religion","sect","service_years","phone","role"],
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
    "discipline_records":["student_id","discipline_type","record_date","decision_type","deduct_score","referral_to","description"],
    "educational_followups":["student_id","followup_date","followup_items","decision"],
    "academic_followups":["student_id","followup_date","followup_items","decision"],
    "certificate_requests":["student_id","student_name","destination","request_date","status","executive_note"],
    "student_referrals":["student_id","teacher_id","referral_to","reason","referral_date","status"],
    "teacher_parent_meetings":["teacher_id","student_id","parent_id","requested_date","status","manager_status","reason"],
    "activity_offers":["title","category","event_date","active","amount","settings"],
    "activity_registrations":["activity_id","student_id","participation_type","team_members","competition_type","payment_status","status"],
    "program_activations":["program_key","title","active","activated_by"],
    "khwarizmi_registrations":["title","category","grade","class_name","student_id","status"],
    "assignment_submissions":["assignment_id","student_id","file_url","answer_text","submitted_at","status"],
    "class_seat_assignments":["class_id","student_id","seat_number","academic_year"],
    "exam_seat_assignments":["exam_id","student_id","subject","exam_date","seat_number"],
    "monthly_report_cards":["student_id","month_name","active","created_at"],
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
        top.add_widget(self.btn("بازگشت",self.go_back,PRIMARY,dp(40),dp(78)))
        self.title=self.label(APP_NAME,"18sp",PRIMARY,True,"center"); top.add_widget(self.title)
        top.add_widget(self.btn("داشبورد",self.go_dashboard,PRIMARY,dp(40),dp(45)))
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
        scroll=ScrollView(do_scroll_x=False); grid=GridLayout(cols=2,spacing=dp(8),padding=[dp(2),dp(2)],size_hint_y=None); grid.bind(minimum_height=grid.setter('height'))
        for i,(text,table) in enumerate(items,1):
            c=Surface(height=dp(128),size_hint_y=None,padding=dp(10))
            row=BoxLayout(size_hint_y=None,height=dp(54),spacing=dp(6))
            badge=BoxLayout(size_hint_x=None,width=dp(42)); badge.add_widget(self.label(f"{i:02d}","11sp",WHITE,True,"center")); self._badge(badge)
            row.add_widget(badge)
            title_box=BoxLayout(orientation="vertical",spacing=dp(2))
            title_box.add_widget(self.label(text,"13sp",PRIMARY,True,"right"))
            title_box.add_widget(self.label(FRIENDLY.get(table,table),"8sp",SECONDARY,False,"right"))
            row.add_widget(title_box)
            c.add_widget(row)
            c.add_widget(self.label(("ثبت / ویرایش / حذف" if self.can_write(table) else "مشاهده اطلاعات بر اساس سطح دسترسی"),"8sp",SECONDARY,False,"right"))
            c.add_widget(self.btn("ورود به محیط این بخش",lambda *_a,t=table:self.open_table(t),SUCCESS if self.can_write(table) else PRIMARY,dp(38)))
            grid.add_widget(c)
        scroll.add_widget(grid); self.body.add_widget(scroll)

    def _badge(self,w):
        with w.canvas.before:
            Color(*PRIMARY); bg=RoundedRectangle(radius=[dp(9)])
        w.bind(pos=lambda o,v:setattr(bg,"pos",v),size=lambda o,v:setattr(bg,"size",v))

    def open_table(self,table,refresh_subbar=True):
        # "نمونه کلاس هوشمند" is an interactive classroom, not a Supabase table.
        # Route it directly to the real classroom screen so the generic table
        # loader does not query a non-table key and show "خطا در نمایش اطلاعات".
        if table == "smart_class_preview":
            try:
                from kivy.app import App
                app = App.get_running_app()
                screen = app.ensure_smart_class_preview() if app is not None else None
                if screen is None:
                    raise RuntimeError("محیط کلاس هوشمند آماده نشد.")
                screen.return_to = "panel"
                self.table = None
                if self.manager:
                    self.manager.current = "smart_class_preview"
                return
            except Exception as exc:
                print("SMART CLASS OPEN ERROR:", repr(exc))
                self.status.text = rtl_text("محیط کلاس هوشمند باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                return

        self.table=table
        if refresh_subbar:
            self.render(); return
        self.body.clear_widgets(); self.title.text=rtl_text(FRIENDLY.get(table,table))
        hero=Surface(height=dp(58)); line=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5)); line.add_widget(self.btn("زیرپنل‌ها",lambda *_:self._back_to_submenus(),PRIMARY,dp(40),dp(82))); line.add_widget(self.label(FRIENDLY.get(table,table),"16sp",PRIMARY,True,"center")); hero.add_widget(line); self.body.add_widget(hero)
        if self.can_write(table):
            # The module has exactly three data operations.
            bar=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(5))
            bar.add_widget(self.btn("ثبت جدید",lambda *_:self.editor(table,None),SUCCESS,dp(38)))
            bar.add_widget(self.btn("ویرایش",lambda *_:self._edit_selected_row(),PRIMARY,dp(38)))
            bar.add_widget(self.btn("حذف",lambda *_:self._delete_selected_row(),(0.72,.16,.18,1),dp(38)))
            self.body.add_widget(bar)
        self.area=BoxLayout(orientation="vertical"); self.body.add_widget(self.area); self.load_table()

    def _edit_selected_row(self):
        row=getattr(self,"selected_row",None)
        if row is None:
            self.message("ویرایش","ابتدا یک رکورد را از جدول انتخاب کنید.")
            return
        self.editor(self.table,row)

    def _delete_selected_row(self):
        row=getattr(self,"selected_row",None)
        if row is None:
            self.message("حذف","ابتدا یک رکورد را از جدول انتخاب کنید.")
            return
        self.confirm_delete(self.table,row)

    def _back_to_submenus(self): self.table=None; self.render()

    def load_table(self):
        # Android: start backend work after the navigation callback has returned.
        table = str(self.table or "").strip()
        if not table:
            self.status.text = rtl_text("شناسه زیرپنل معتبر نیست.")
            self.status.color = (.8, .15, .15, 1)
            return
        self.status.text = rtl_text("در حال دریافت اطلاعات واقعی… (حداکثر ۲۵ رکورد)")
        self.status.color = SECONDARY
        def work():
            try:
                api = getattr(self.app_state, "api", None)
                if api is None:
                    raise RuntimeError("اتصال سرویس داده آماده نیست.")
                rows = api.table_select(table, {"limit": "25"}) or []
                if not isinstance(rows, list):
                    rows = []
                safe_rows = [dict(r) for r in rows if isinstance(r, dict)]
                Clock.schedule_once(lambda *_: self._safe_loaded(safe_rows[:25], None), 0)
            except Exception as exc:
                message = str(exc) or exc.__class__.__name__
                Clock.schedule_once(lambda *_: self._safe_loaded([], message), 0)
        Clock.schedule_once(lambda *_: Thread(target=work, daemon=True).start(), 0.05)

    def _safe_loaded(self, rows, error):
        try:
            if self.manager is None:
                return
            self.loaded(rows, error)
        except Exception as exc:
            print("MODULE TABLE RENDER ERROR:", repr(exc))
            try:
                self.status.text = rtl_text("خطا در نمایش اطلاعات: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
            except Exception:
                pass

    def loaded(self,rows,error):
        # Supabase is expected to return a list of dictionaries. Normalize the
        # response before touching any Kivy widget so a malformed/empty response
        # can never terminate the Android UI thread.
        rows = rows if isinstance(rows, list) else []
        rows = [dict(r) for r in rows if isinstance(r, dict)]
        self.rows=rows
        if error:
            self.status.text=rtl_text("خطا در دریافت اطلاعات: "+str(error))
            self.status.color=(.8,.15,.15,1)
            self.render_rows([])
            return
        self.status.text=rtl_text(f"{len(rows)} رکورد واقعی • {FRIENDLY.get(self.table,self.table)}")
        self.status.color=SUCCESS
        self.render_rows(rows)

    def render_rows(self,rows):
        try:
            self.area.clear_widgets()
            rows = [dict(r) for r in (rows or []) if isinstance(r, dict)]
            if not rows:
                e=Surface(height=dp(130))
                e.add_widget(self.label("رکوردی برای نمایش وجود ندارد","16sp",PRIMARY,True,"center"))
                e.add_widget(self.label("در صورت داشتن دسترسی، از «ثبت جدید» استفاده کنید.","9sp",SECONDARY,False,"center"))
                self.area.add_widget(e)
                return
            preferred = TABLE_FIELDS.get(self.table, [])
            keys = [k for k in preferred if any(k in r for r in rows)]
            if not keys:
                for r in rows:
                    for k in r:
                        if k not in HIDDEN and k not in keys:
                            keys.append(k)
            if not keys:
                keys = ["title","description","status"]
            # Keep the Web-defined business columns that actually exist in the
            # live response. Android uses horizontal touch scrolling for wide tables.
            col_w=dp(230)
            action_w=dp(175 if self.can_write(self.table) else 0)
            totalw=max(dp(720),col_w*max(2,len(keys))+action_w)
            scroll=ScrollView(do_scroll_x=True,do_scroll_y=True)
            content=BoxLayout(orientation='vertical',size_hint=(None,None),width=totalw,spacing=dp(3),padding=dp(2))
            content.bind(minimum_height=content.setter('height'))
            header=BoxLayout(size_hint=(None,None),width=totalw,height=dp(78),spacing=dp(3),padding=[dp(4),dp(4)])
            for k in keys:
                cell=self.label(COLUMNS.get(k,"اطلاعات"),"18sp",WHITE,True,"center")
                cell.size_hint_x=None
                cell.width=col_w
                header.add_widget(cell)
            if self.can_write(self.table):
                op=self.label("عملیات","16sp",WHITE,True,"center")
                op.size_hint_x=None
                op.width=action_w
                header.add_widget(op)
            self._header(header)
            content.add_widget(header)
            for i,r in enumerate(rows,1):
                try:
                    content.add_widget(self.row(r,i,keys,totalw))
                except Exception as row_exc:
                    print("MODULE ROW RENDER ERROR:", repr(row_exc))
            scroll.add_widget(content)
            self.area.add_widget(scroll)
        except Exception as exc:
            print("MODULE TABLE RENDER ERROR:", repr(exc))
            try:
                self.status.text=rtl_text("خطا در نمایش جدول: "+str(exc))
                self.status.color=(.8,.15,.15,1)
                self.area.clear_widgets()
                fallback=Surface(height=dp(150))
                fallback.add_widget(self.label("نمایش جدول با خطا روبه‌رو شد","14sp",ERROR if 'ERROR' in globals() else (.8,.15,.15,1),True,"center"))
                fallback.add_widget(self.label("داده‌ها حفظ شده‌اند؛ دوباره تازه‌سازی کنید.","9sp",SECONDARY,False,"center"))
                self.area.add_widget(fallback)
            except Exception:
                pass

    def _header(self,w):
        with w.canvas.before: Color(*PRIMARY); bg=RoundedRectangle(radius=[dp(8)])
        w.bind(pos=lambda o,v:setattr(bg,'pos',v),size=lambda o,v:setattr(bg,'size',v))

    def row(self,r,index,keys,totalw):
        b=SelectableRow(owner=self,record=r,size_hint=(None,None),width=totalw,height=dp(100),spacing=dp(3),padding=[dp(5),dp(5)])
        for k in keys:
            raw = r.get(k, "")
            s = str(raw).strip()
            if not s or all(ch in "□�▯" for ch in s):
                s = "ثبت نشده"
            cell=self.label(s,"17sp",SECONDARY,False,'center')
            cell.size_hint_x=None
            cell.width=dp(230)
            b.add_widget(cell)
        if index%2==0:
            with b.canvas.before: Color(.94,.97,.985,1); bg=RoundedRectangle(radius=[dp(6)])
            b.bind(pos=lambda o,v:setattr(bg,'pos',v),size=lambda o,v:setattr(bg,'size',v))
        return b

    def editor(self,table,row):
        fields=[k for k in (FORMS.get(table) or self._infer(row)) if k not in HIDDEN]
        root=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(6)); sc=ScrollView(do_scroll_x=False); form=GridLayout(cols=1,spacing=dp(5),size_hint_y=None); form.bind(minimum_height=form.setter('height')); inputs={}
        for f in fields:
            form.add_widget(self.label(COLUMNS.get(f,f),"9sp",PRIMARY,True)); ti=PersianTextInput(text='' if row is None else str(row.get(f,'')),font_name=font_name(),font_size='12sp',halign='right',multiline=False,size_hint_y=None,height=dp(44),padding=[dp(8),dp(6)]); inputs[f]=ti; form.add_widget(ti)
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
