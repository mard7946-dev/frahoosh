from threading import Thread

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.resources import resource_find
from pathlib import Path

from mobile.config import APP_NAME, CARD, PRIMARY, SCHOOL_NAME, SCHOOL_YEAR, SECONDARY, SUCCESS, WHITE, PAYMENT_GATEWAY_URL
from mobile.ui import font_name, rtl_text, fa_display, PersianTextInput, PersianSpinner

class SelectableRow(ButtonBehavior, BoxLayout):
    """Touch-friendly table row: selecting it enables the module-level Edit/Delete buttons."""
    def __init__(self, owner=None, record=None, **kwargs):
        super().__init__(**kwargs)
        self.owner = owner
        self.record = dict(record or {})
    def on_press(self):
        if self.owner is not None:
            self.owner.selected_row = self.record
            try:
                self.owner.status.text = fa_display("رکورد انتخاب شد؛ از ویرایش یا حذف استفاده کنید.")
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
"students":[
("اطلاعات دانش‌آموز","students"),("پایه و کلاس","student_class_info"),("حضور و غیاب","attendance"),
("نمرات","student_grades"),("تکالیف","assignments"),("صندوق پیام","messages"),
("مسابقات و فعالیت‌ها","activity_registrations"),("شورای دانش‌آموزی","student_council"),
("بسیج","basij_registration"),("همیار مدرسه","school_ally"),("شهردار مدرسه","school_mayor"),
("ارسال تکالیف","assignment_submissions"),("برنامه هفتگی","weekly_schedule"),
("برنامه امتحانات","exam_schedule"),("صندلی کلاسی","class_seat_assignments"),
("صندلی امتحان","exam_seat_assignments"),("درخواست گواهی","certificate_requests"),
("کلاس آنلاین","online_classes"),("پرداخت آنلاین","payment")
],
"parents":[
("انتخاب یک یا چند دانش‌آموز","parent_children"),("اطلاعات دانش‌آموز","students"),
("کارنامه و نمرات","student_grades"),("حضور و غیاب","attendance"),
("کارنامه ماهانه","monthly_report_cards"),("کارنامه","report_cards"),
("انضباط","discipline_records"),("گزارش هوشمند","ai_smart_reports"),
("پیام‌ها و اطلاعیه‌ها","messages"),("ملاقات‌ها","meeting_requests"),
("نظرسنجی","survey_responses"),("برنامه هفتگی","weekly_schedule"),
("برنامه امتحانات","exam_schedule"),("سوابق پرداخت","payment_records"),
("پرداخت آنلاین","payment"),("سرویس مدرسه","transport_requests"),
("فعالیت‌های اولیا","parent_activities")
],
"finance":[("حساب‌ها","finance_accounts"),("تراکنش‌ها","finance_transactions"),("کمک‌های داوطلبانه","finance_donations"),("تعریف گزینه پرداخت","payment_offers"),("درخواست‌های پرداخت","payment_attempts"),("سوابق پرداخت","payment_records")],
"online":[("کلاس‌های آنلاین","online_classes"),("جلسات","online_class_sessions"),("دانش‌آموزان کلاس","online_class_students"),("دبیران کلاس","online_class_teachers"),("حضور آنلاین","online_attendance"),("تخته کلاس","smart_board_whiteboards")],
"smart_board":[("محتوای آموزشی","smart_board_content"),("فعالیت‌ها","smart_board_activities"),("آزمون‌های کوتاه","smart_board_quizzes"),("تخته‌های آموزشی","smart_board_whiteboards")],
"ai":[("گزارش تحلیلی کلاس به کلاس","ai_smart_reports"),("گزارش تحلیلی دانش‌آموز","ai_smart_reports"),("پرسش هوشمند","ai_questions"),("جلسات دستیار","ai_assistant_sessions")],
"messages":[("صندوق ورودی","messages"),("ارسال پیام","message_targets"),("مخاطبان","message_targets"),("وضعیت خواندن","message_reads")],
"reports":[("کارنامه‌ها","report_cards"),("نسخه‌های کارنامه","report_card_snapshots"),("نمرات","grades"),("حضور و غیاب","attendance"),("ارزیابی دانش‌آموزان","student_grades"),("گزارش هوشمند","ai_smart_reports")],
"schedule":[("برنامه هفتگی","weekly_schedule"),("برنامه تولیدشده","generated_weekly_schedule"),("برنامه امتحانات","exam_schedule"),("کلاس‌های دبیران","teacher_classes"),("صندلی امتحانی","exam_seat_assignments")],
"settings":[("تنظیمات حساب","account_settings"),("مشخصات مدرسه","school_profile"),("ساختار کلاس‌ها","school_class_config"),("حساب‌های سامانه","users")],
"student_info":[("اطلاعات شخصی","students"),("پایه و کلاس","student_class_info"),("نمرات","student_grades"),("حضور و غیاب","attendance"),("تکالیف","assignments"),("کارنامه","report_cards")],
"teacher_exams":[("آزمون آنلاین","teacher_exams"),("بانک سؤال","quiz_questions"),("زمان‌بندی","exam_schedule")],
"payment":[("پرداخت آنلاین","payment_offers"),("درخواست‌های پرداخت","payment_attempts"),("سوابق پرداخت","payment_records"),("تراکنش‌ها","payment_transactions")],
"messages":[("صندوق ورودی","messages"),("ارسال پیام","message_targets"),("وضعیت خواندن","message_reads")]
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
                modules = data.get("modules") or {}
                if panels:
                    return panels, friendly, modules
        except Exception as exc:
            print("SHARED MODULE CATALOG ERROR:", repr(exc))
    return None, None, {}

_shared_panels, _shared_friendly, _shared_modules = _load_shared_catalog()

def _module_fields(table):
    """Return the real field contract from the shared catalog plus local UI extras."""
    key = str(table or "").strip()
    local = list(TABLE_FIELDS.get(key) or []) if "TABLE_FIELDS" in globals() else []
    spec = (_shared_modules or {}).get(key) or {}
    shared = list(spec.get("fields") or []) if isinstance(spec, dict) else []
    result = []
    for field in shared + local:
        field = str(field or "").strip()
        if field and field not in result:
            result.append(field)
    return result


# The uploaded v16.12 ZIP is the authoritative UI contract.  Android must use
# its exact panel/module membership; the shared catalog is only used for table
# fields and labels.  Every module below resolves to a real backend table.
_MOTHER_MODULES = {
    "management":[("مدیریت کاربران و کارکنان","users"),("حضور و غیاب","attendance"),("انضباط","discipline_records"),("کلاس آنلاین","online"),("برنامه هفتگی و برنامه امتحانات","schedule"),("گزارش‌ها و آمار","reports"),("تنظیمات مدرسه","settings"),("ملاقات‌ها","meeting_requests"),("مالی","finance")],
    "executive":[("دانش‌آموزان","students"),("حضور و غیاب","attendance"),("انضباط","discipline_records"),("کلاس‌ها","executive_classes"),("کارکنان","staff"),("پرونده‌ها","archive_items"),("امور اجرایی","executive_operations"),("گزارش‌ها","executive_reports"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("درخواست‌های ملاقات","meeting_requests")],
    "educational":[("حضور و غیاب","attendance"),("ارجاعات آموزشی","student_referrals"),("جلسات","meeting_requests"),("اطلاع‌رسانی","messages"),("امتحانات","teacher_exams"),("بانک سؤال","quiz_questions"),("گزارش‌های آموزشی","ai_smart_reports"),("تأیید و مدیریت ملاقات‌ها","meeting_requests")],
    "cultural":[("حضور و غیاب","attendance"),("انضباط","discipline_records"),("فعالیت‌های فرهنگی","educational_activities"),("مسابقات","cultural_competitions"),("برنامه‌های پرورشی","school_events"),("ثبت‌نام فعالیت‌ها","cultural_activity_registrations"),("گزارش‌های پرورشی","cultural_reports"),("درخواست‌های ملاقات","meeting_requests")],
    "advisor":[("حضور و غیاب","attendance"),("انضباط","discipline_records"),("پرونده مشاوره","counseling_records"),("جلسات","meeting_requests"),("پیگیری دانش‌آموز","counseling_followups"),("ارجاعات","student_referrals"),("هدایت تحصیلی","counseling_followups"),("گزارش مشاوره","ai_smart_reports"),("درخواست‌های ملاقات","meeting_requests")],
    "teachers":[("کلاس‌های من","teacher_classes"),("نمرات و کارنامه","student_grades"),("تکالیف","assignments"),("حضور و غیاب","attendance"),("آزمون‌ها","teacher_exams"),("طرح درس","lesson_plans"),("جلسات","meeting_requests"),("گزارش‌ها","teacher_activities"),("ملاقات با اولیا","teacher_parent_meetings")],
    "students":[("انتخاب و اطلاعات من","students"),("پایه و کلاس","student_class_info"),("نمرات","student_grades"),("تکالیف","assignment_submissions"),("پیام‌ها","messages"),("حضور و غیاب","attendance"),("مسابقات و فعالیت‌ها","activity_registrations"),("برنامه هفتگی","weekly_schedule"),("امتحانات","exam_schedule"),("گزارش عملکرد","ai_smart_reports"),("کلاس آنلاین","online_classes"),("پرداخت آنلاین","payment_offers")],
    "parents":[("انتخاب دانش‌آموز","parent_children"),("اطلاعات دانش‌آموز","students"),("کارنامه و نمرات","student_grades"),("حضور و غیاب","attendance"),("تکالیف و فعالیت‌های آموزشی","assignments"),("پیام‌ها و اطلاعیه‌ها","messages"),("برنامه هفتگی و امتحانات","schedule"),("جلسات با دبیران","teacher_meetings"),("پرداخت‌ها و امور مالی","payment_records"),("پرداخت آنلاین","payment_offers"),("فعالیت‌های فرهنگی و پرورشی","cultural_activity_registrations"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("تعیین وقت ملاقات","meeting_requests")],
    "finance":[("پرداخت‌ها","payment_records"),("تراکنش‌ها","finance_transactions"),("حساب‌ها","finance_accounts"),("کمک‌های داوطلبانه","finance_donations"),("گزینه‌های پرداخت آنلاین","payment_offers"),("درخواست‌های پرداخت","payment_attempts"),("تراکنش‌های پرداخت","payment_transactions")],
    "smart_board":[("تخته آموزشی","smart_board_whiteboards"),("محتوای آموزشی","smart_board_content"),("فعالیت‌های تعاملی","smart_board_activities"),("آزمون‌های کوتاه","smart_board_quizzes"),("فایل‌ها","smart_board_files"),("تصاویر و ویدئوها","smart_board_media"),("ابزارهای تعاملی","smart_board_interactive_tools")],
    "ai":[("دستیار هوشمند","ai_assistant_sessions"),("تحلیل آموزشی","ai_educational_analysis"),("گزارش هوشمند","ai_smart_reports"),("پرسش و پاسخ","ai_questions")],
    "online":[("کلاس‌های آنلاین","online_classes"),("جلسات","online_class_sessions"),("دانش‌آموزان کلاس","online_class_students"),("دبیران کلاس","online_class_teachers"),("حضور آنلاین","online_attendance"),("فعالیت کلاس","online_class_activity"),("اعلان‌های کلاس","online_class_notifications"),("تنظیمات کلاس","online_class_settings"),("کنترل حضور مرحله‌ای","online_presence_checks"),("چت کلاس","online_class_chat"),("رویدادهای تخته","online_class_board_events"),("گزارش هوشمند کلاس","online_class_ai_reports"),("تخته کلاس","smart_board_whiteboards")],
    "teacher_exams":[("آزمون‌های آنلاین","teacher_exams"),("بانک سؤال","quiz_questions"),("زمان‌بندی آزمون","exam_schedule"),("اتصال آزمون به کلاس","teacher_exams")],
    "payment":[("گزینه‌های پرداخت","payment_offers"),("درخواست‌های پرداخت","payment_attempts"),("سوابق پرداخت","payment_records"),("تراکنش‌های پرداخت","payment_transactions")],
    "messages":[("صندوق ورودی","messages"),("مخاطبان پیام","message_targets"),("تحویل پیام","message_delivery"),("وضعیت خواندن","message_reads")],
    "reports":[("کارنامه‌ها","report_cards"),("نسخه‌های کارنامه","report_card_snapshots"),("نمرات","grades"),("حضور و غیاب","attendance"),("ارزیابی دانش‌آموزان","student_grades"),("گزارش هوشمند","ai_smart_reports")],
    "schedule":[("برنامه هفتگی","weekly_schedule"),("برنامه تولیدشده","generated_weekly_schedule"),("برنامه امتحانات","exam_schedule"),("کلاس‌های دبیران","teacher_classes"),("صندلی امتحانی","exam_seat_assignments")],
    "settings":[("تنظیمات حساب","account_settings"),("مشخصات مدرسه","school_profile"),("ساختار کلاس‌ها","school_class_config"),("حساب‌های سامانه","users"),("پشتیبان‌گیری","backup_records")],
}

_MOTHER_TABLE_ALIASES = {
    "users":"users","virtual":"online_classes","planning":"weekly_schedule","reports":"ai_smart_reports","settings":"school_profile","students":"students","staff":"staff","meeting_requests":"meeting_requests","certificate_requests":"certificate_requests","attendance":"attendance","account_settings":"account_settings",
    "class_management":"executive_classes","student_archive":"archive_items","executive_operations":"executive_operations","executive_reports":"executive_reports",
    "referrals":"student_referrals","meetings":"meeting_requests","notifications":"school_events","exams":"teacher_exams","questions":"quiz_questions",
    "cultural_activities":"educational_activities","competitions":"competitions","educational_programs":"school_events","activity_registrations":"cultural_activity_registrations","cultural_reports":"cultural_reports",
    "counseling_records":"counseling_records","student_followup":"counseling_followups","academic_guidance":"counseling_followups","counseling_reports":"ai_smart_reports",
    "classes":"teacher_classes","grades":"grades","teacher_activities":"teacher_activities","assignments":"assignments","lesson":"lesson_plans","student_profile":"students","activities":"activity_registrations","performance_report":"ai_smart_reports","weekly_schedule":"weekly_schedule","online_payment":"payment_offers","payment":"payment_offers",
    "children":"parent_children","student_info":"students","educational_activities":"educational_activities","schedule_exams":"weekly_schedule","teacher_meetings":"teacher_meetings","payments_finance":"payment_records",
    "payments":"payment_records","transactions":"finance_transactions","accounts":"finance_accounts","financial_reports":"finance_transactions","payment_settings":"payment_offers",
    "whiteboard":"smart_board_whiteboards","files":"smart_board_files","media":"smart_board_media","interactive_tools":"smart_board_interactive_tools",
    "assistant":"ai_assistant_sessions","educational_analysis":"ai_educational_analysis","smart_reports":"ai_smart_reports","qa":"ai_questions",
    "online_classes":"online_classes","online_class_sessions":"online_class_sessions","online_class_students":"online_class_students","online_class_teachers":"online_class_teachers","online_attendance":"online_attendance",
    "teacher_exams":"teacher_exams","quiz_questions":"quiz_questions","quiz_schedules":"exam_schedule","quiz_links":"teacher_exams",
    "payment_offers":"payment_offers","payment_attempts":"payment_attempts","payment_records":"payment_records","payment_transactions":"payment_transactions",
    "messages":"messages","message_targets":"message_targets","message_reads":"message_reads","smart_board_whiteboards":"smart_board_whiteboards","smart_class_preview":"smart_class_preview",
    "school_settings":"school_profile","backup":"backup_records"
}

# The shared ZIP/Web catalog is the authoritative complete module map.
# Keep _MOTHER_MODULES only as a compatibility fallback for older builds.
if _shared_panels:
    SUBMENUS = {k: [tuple(item) for item in v] for k, v in _shared_panels.items()}
elif _MOTHER_MODULES:
    SUBMENUS = _MOTHER_MODULES

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

COLUMNS.update({
    "quantity":"تعداد", "location":"محل نگهداری", "archived":"بایگانی‌شده", "card_type":"نوع کارت",
    "code":"کد", "audience":"مخاطبان", "start_at":"شروع", "end_at":"پایان", "created_by":"ثبت‌کننده",
    "followup_item":"مورد پیگیری", "date_shamsi":"تاریخ شمسی", "registration_start_shamsi":"شروع ثبت‌نام",
    "registration_end_shamsi":"پایان ثبت‌نام", "sport_type":"رشته ورزشی", "fixed_amount":"مبلغ ثابت",
    "role":"نقش", "weekly_sessions":"جلسات هفتگی", "session_no":"شماره جلسه", "teaching_amount":"میزان تدریس",
    "teaching_date":"تاریخ تدریس", "teaching_title":"عنوان تدریس", "activity_type":"نوع فعالیت",
    "school_year":"سال تحصیلی", "classroom_seat":"صندلی کلاسی", "exam_seat":"صندلی امتحانی",
    "parent_id":"شناسه ولی", "parent_name":"نام ولی", "target_role":"نقش مخاطب", "target_name":"نام مخاطب",
    "requested_date_shamsi":"تاریخ درخواست شمسی", "requested_time":"ساعت درخواست", "educational_approval":"تأیید معاون آموزشی",
    "manager_approval":"تأیید مدیریت", "registration_date":"تاریخ ثبت", "certificate_type":"نوع گواهی",
    "reason":"علت", "report":"گزارش", "meeting_at":"زمان جلسه"
})

COLUMNS.update({
    "content_date_shamsi":"تاریخ شمسی محتوا","board_date":"تاریخ تخته","file_path":"مسیر فایل","file_type":"نوع فایل",
    "media_path":"مسیر رسانه","media_type":"نوع رسانه","activity_text":"شرح فعالیت","quiz_date_shamsi":"تاریخ آزمونک",
    "correct_option":"گزینه صحیح","tool_type":"نوع ابزار","configuration":"تنظیمات ابزار","request_date_shamsi":"تاریخ درخواست",
    "analysis_date_shamsi":"تاریخ تحلیل","risk_level":"سطح ریسک","report_type":"نوع گزارش","target_id":"شناسه هدف",
    "grade_type":"نوع نمره","grade_date":"تاریخ نمره","activity_date":"تاریخ فعالیت","operation_type":"نوع عملیات",
    "report_date":"تاریخ گزارش","created_by":"ثبت‌کننده","fee":"هزینه","registration_date":"تاریخ ثبت‌نام",
    "start_date":"تاریخ شروع","end_date":"تاریخ پایان","weight":"ضریب","bell_pattern":"الگوی زنگ","class_names":"کلاس‌ها",
    "capacity":"ظرفیت","weekdays":"روزهای هفته","program_key":"کلید برنامه","activity_key":"کلید فعالیت",
    "student_name":"نام دانش‌آموز","parent_username":"نام کاربری ولی","vehicle_type":"نوع وسیله","origin":"مبدأ","destination":"مقصد",
    "counterparty":"طرف حساب","debit":"بدهکار","credit":"بستانکار","invoice_number":"شماره فاکتور","transaction_date":"تاریخ تراکنش",
    "payment_type":"نوع پرداخت","gateway":"درگاه","reference":"شماره مرجع","authority":"شماره پیگیری",
    "requested_date":"تاریخ درخواست","requested_time":"ساعت درخواست","target_person":"شخص مورد ملاقات","target_type":"نوع مخاطب",
    "attempt_id":"شناسه تلاش آزمون","question_id":"شناسه سؤال","answer":"پاسخ","auto_correct":"تصحیح خودکار","teacher_score":"نمره دبیر",
    "started_at":"شروع","submitted_at":"ارسال","student_username":"نام کاربری دانش‌آموز","max_score":"حداکثر نمره",
    "seat_number":"شماره صندلی","academic_year":"سال تحصیلی","exam_id":"شناسه امتحان","assignment_id":"شناسه تکلیف",
    "answer_text":"پاسخ تکلیف","file_url":"فایل پیوست","status":"وضعیت","active":"فعال","settings":"تنظیمات"
})

# Replace the legacy hard-coded table map with the ZIP canonical contract.
# The JSON catalog is the single source for Web + Android module fields.
CANONICAL_OPERATIONS = {
    str(_spec.get("table") or _module_id): tuple(_spec.get("operations") or ("create", "update", "delete"))
    for _module_id, _spec in (_shared_modules.items() if isinstance(_shared_modules, dict) else [])
    if isinstance(_spec, dict)
}

HIDDEN = {"created_at", "updated_at", "deleted_at"}

COLUMNS.update({
    "permissions":"سطح دسترسی","linked_student_id":"دانش‌آموز مرتبط","linked_teacher_id":"دبیر مرتبط","linked_staff_id":"کارمند مرتبط",
    "display_name":"نام نمایشی","nationality":"ملیت","religion":"دین","sect":"مذهب","photo":"تصویر",
    "description":"توضیحات","subject":"درس","assessment_type":"نوع ارزیابی","assessment_title":"عنوان ارزیابی",
    "coefficient":"ضریب","manager_released":"تأیید مدیریت","due_date":"مهلت تحویل","active":"فعال",
    "weekdays":"روزهای هفته","weekday":"روز","bell":"زنگ","period":"ساعت/زنگ","start_date":"تاریخ شروع","end_date":"تاریخ پایان",
    "exam_start_time":"ساعت شروع","exam_end_time":"ساعت پایان","lesson":"مبحث/جلسه","start_time":"زمان شروع","end_time":"زمان پایان",
    "pages":"صفحات","record":"ضبط","smart_board":"تخته هوشمند","quiz":"آزمونک","camera":"دوربین","microphone":"میکروفون",
    "started_at":"شروع جلسه","ended_at":"پایان جلسه","student_name":"نام دانش‌آموز","teacher_name":"نام دبیر",
    "join_time":"زمان ورود","leave_time":"زمان خروج","last_activity":"آخرین فعالیت","title":"عنوان","text":"متن",
    "sender":"فرستنده","receiver":"گیرنده","sender_user_id":"شناسه فرستنده","sender_name":"نام فرستنده",
    "target_role":"نقش مخاطب","target_name":"نام مخاطب","target_class_name":"کلاس مخاطب","message_id":"پیام",
    "target_type":"نوع مخاطب","target_value":"مقدار مخاطب","read_at":"زمان خواندن",
    "counterparty":"طرف حساب","debit":"بدهکار","credit":"بستانکار","invoice_number":"شماره فاکتور",
    "account_type":"نوع حساب","account_number":"شماره حساب","gateway":"درگاه","reference":"شماره مرجع","authority":"شماره پیگیری",
    "payment_type":"نوع پرداخت","payment_reason":"علت پرداخت","manual_amount":"مبلغ دستی","gateway_enabled":"درگاه فعال",
    "term":"نوبت","average":"معدل","snapshot_data":"نسخه کارنامه","generated_date_shamsi":"تاریخ صدور",
    "school_name":"نام مدرسه","school_code":"کد مدرسه","principal_name":"نام مدیر","academic_year":"سال تحصیلی",
    "logo_path":"مسیر لوگو","capacity":"ظرفیت","grade_level":"پایه","report_date":"تاریخ کارنامه",
    "class_id":"کلاس","file_path":"مسیر فایل","file_type":"نوع فایل","media_path":"مسیر رسانه","media_type":"نوع رسانه",
    "tool_type":"نوع ابزار","content_date_shamsi":"تاریخ محتوای شمسی","board_date":"تاریخ تخته",
    "activity_text":"شرح فعالیت","activity_date_shamsi":"تاریخ فعالیت","correct_option":"گزینه صحیح",
    "username":"نام کاربری","answer":"پاسخ","answered_at":"زمان پاسخ","request_date_shamsi":"تاریخ درخواست",
    "period":"دوره","score":"امتیاز","risk_level":"سطح ریسک","analysis_date_shamsi":"تاریخ تحلیل",
    "report_type":"نوع گزارش","target_id":"شناسه هدف","created_by":"ثبت‌کننده","report_date_shamsi":"تاریخ گزارش",
    "visit_reason":"علت مراجعه","recommendations":"توصیه‌ها","next_visit":"مراجعه بعدی","reason_summary":"خلاصه علت",
    "interest":"علاقه","aptitude":"استعداد","recommendation":"پیشنهاد هدایت تحصیلی","body":"متن","active":"فعال",
    "parent_phone":"شماره تماس ولی","meeting_date":"تاریخ جلسه","requester":"درخواست‌کننده","requester_role":"نقش درخواست‌کننده",
    "requester_name":"نام درخواست‌کننده","student_name":"نام دانش‌آموز","parent_username":"نام کاربری ولی","parent_name":"نام ولی",
    "target_user_id":"شناسه مخاطب","target_username":"نام کاربری مخاطب","target_person":"شخص مقصد","requested_date":"تاریخ درخواست",
    "requested_time":"ساعت درخواست","reason":"علت","final_date":"تاریخ نهایی","final_time":"ساعت نهایی",
    "manager_status":"وضعیت مدیر","manager_note":"یادداشت مدیر","educational_status":"وضعیت آموزشی","educational_note":"یادداشت آموزشی",
    "discipline_type":"نوع مورد انضباطی","record_date":"تاریخ ثبت","decision_type":"نوع تصمیم","deduct_score":"کسر نمره",
    "referral_to":"ارجاع به","priority":"اولویت","deduction":"کسر نمره","actor_username":"ثبت‌کننده","actor_role":"نقش ثبت‌کننده",
    "note":"یادداشت","election_year":"سال انتخابات","registration_date":"تاریخ ثبت‌نام","participation_type":"تیمی/انفرادی",
    "team_members":"اعضای تیم","competition_type":"نوع مسابقه","payment_status":"وضعیت پرداخت","activity_id":"فعالیت",
    "activity_title":"عنوان فعالیت","activity_kind":"نوع فعالیت","fee":"هزینه","category":"دسته‌بندی","start_date":"شروع",
    "end_date":"پایان","program_key":"کلید برنامه","settings":"تنظیمات","student_code":"شماره دانش‌آموزی",
    "seat_number":"شماره صندلی","month_name":"ماه","file_url":"فایل","answer_text":"پاسخ دانش‌آموز","submitted_at":"زمان ارسال",
    "survey_id":"نظرسنجی","respondent_username":"کاربر پاسخ‌دهنده","respondent_role":"نقش پاسخ‌دهنده","question_id":"سؤال",
    "created_at":"تاریخ ثبت"
})

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
"payment_offers":["title","amount","target_type","target_value","description","status","payment_url","gateway","gateway_enabled","manual_amount","payment_reason"],"payment_attempts":["offer_id","student_id","payer_username","payer_role","amount","status","gateway_ref","description"],"payment_records":["student_id","parent_username","title","amount","payment_type","gateway","authority","reference","status","payment_date","description"],
"online_classes":["title","subject","lesson","teacher","grade","class_name","duration","pages","record","smart_board","quiz","camera","microphone","start_time","end_time","status","activated_by","join_url","meeting_url"],"online_class_sessions":["class_id","started_at","ended_at"],"online_class_students":["class_id","student_id","student_name"],"online_class_teachers":["class_id","teacher_id","teacher_name"],"online_attendance":["class_id","student_id","join_time","leave_time","status","last_activity"],
"smart_board_content":["title","content","class_id","teacher_id","content_date_shamsi"],"smart_board_activities":["title","activity_text","class_id","teacher_id","activity_date_shamsi"],"smart_board_quizzes":["title","question","option_a","option_b","option_c","option_d","correct_option","class_id","teacher_id","quiz_date_shamsi"],"smart_board_whiteboards":["title","content","class_id","teacher_id","board_date"],
"educational_activities":["title","subject","grade","class_name","teacher_id","student_id","description","activity_date","status"],"counseling_records":["student_name","visit_reason","recommendations","next_visit","reason_summary"],"counseling_followups":["student_id","subject","description","status"],
"ai_questions":["username","role","question","answer","student_id","answered_at","answer_date_shamsi"],"ai_assistant_sessions":["username","role","title","context","request_date_shamsi"],"ai_smart_reports":["title","report_type","target_type","target_id","report","created_by","report_date_shamsi"],
"messages":["sender","receiver","text","sender_user_id","sender_name","title","body","audience_type","audience_value"],
"online_class_chat":["class_id","session_id","sender_id","sender_name","sender_role","message"],"message_targets":["message_id","target_type","target_value","target_role","target_id","read_at"],"message_delivery":["message_id","username","received_at","seen_at"],
"school_profile":["school_name","school_code","principal_name","phone","address","academic_year","logo_path","request_date_shamsi"],"school_class_config":["total_classes","grade7_classes","grade8_classes","grade9_classes"],"users":["username","password","role","permissions","linked_student_id","linked_teacher_id","linked_staff_id","display_name"],"account_settings":["username","display_name","phone","email","preferences","national_code","role","auth_user_id"],
"teacher_exams":["teacher_id","title","subject","grade","class_name","exam_type","exam_date","duration","description","published","secure_mode","share_enabled","share_code","standard_mode","max_attempts","passing_score"],"quiz_questions":["quiz_id","question","option1","option2","option3","option4","correct_answer","points","question_type","image_url","options_json","accepted_answers","explanation","difficulty","cognitive_level","auto_grade","negative_score"],
"discipline_records":["student_id","teacher_id","title","description","priority","status","item_id","deduction","actor_username","actor_role","note"],"educational_followups":["student_id","followup_date","followup_items","decision","status"],"academic_followups":["student_id","followup_date","followup_items","decision","status"],"certificates":["student_id","title","code"],"parent_meetings":["student_id","teacher_id","parent_phone","reason","meeting_date","status"],
"meeting_requests":["title","requester_username","requester_role","requester_name","student_id","student_name","parent_username","parent_name","target_role","target_user_id","target_username","target_name","requested_day","requested_date","requested_time","reason","description","status","manager_status","manager_note","educational_status","educational_note","final_date","final_time","final_note"],"student_registrations":["student_id","activity_id","activity_title","activity_kind","fee","payment_status","payment_url","payment_reference","registration_code","registration_date","status"],"cultural_activity_registrations":["activity_id","activity_title","activity_kind","student_id","student_name","fee","payment_status","registration_code","registration_date","status"],"student_referrals":["student_id","teacher_id","referral_to","reason","referral_date","status"],"teacher_activities":["teacher_id","student_id","title","activity_type","subject","score","description","activity_date"],"teacher_attendance":["student_id","teacher_id","class_name","subject","attendance_date","status","description"],"teacher_parent_meetings":["teacher_id","student_id","parent_id","requested_date","status","manager_status","reason"],"activity_offers":["title","category","event_date","active","amount","settings"],"activity_registrations":["activity_id","student_id","participation_type","team_members","competition_type","payment_status","status"],"khwarizmi_registrations":["title","category","grade","class_name","student_id","status"],"class_seats":["student_id","class_name","seat_no"],"exam_seats":["student_id","exam_name","seat_no"],"monthly_report_cards":["student_id","month_name","active"],"competitions":["title","category","start_date","end_date","status","description"],"executive_requests":["title","requester","status","description","role"],"executive_operations":["operation_type","title","student_id","class_name","description","status","operation_date","created_by"],"executive_reports":["title","report_type","student_id","class_name","payload","report_date","created_by"],"assets":["title","category","quantity","location","archived"],"archive_items":["title","student_id","location","description"],"backup_records":["file_path","backup_type","size_bytes","status","created_by"],"surveys":["title","description","status","audience","start_at","end_at","created_by"],"survey_questions":["survey_id","question","question_type","options","required","sort_order"],"survey_responses":["survey_id","respondent_username","respondent_role","student_id"],"program_activations":["program_key","title","active","activated_by"],"student_council":["student_id","student_name","election_year","status"],"basij_registration":["student_id","student_name","registration_date","status"],"school_ally":["student_id","student_name","role","status"],"school_mayor":["student_id","student_name","status"],"cultural_competitions":["title","category","start_date","end_date","status","description"],"art_competitions":["title","category","start_date","end_date","status","description"],"sport_competitions":["title","category","start_date","end_date","status","description"],"morning_leaders":["student_id","student_name","status"],"qari_registration":["student_id","student_name","status"],"morning_ceremony":["title","program_key","active","description"],"parent_activities":["title","description","activity_date","status"],"student_class_info":["student_id","grade","class_name","academic_year"],"message_reads":["message_id","username","read_at"],"certificate_requests":["student_id","student_name","destination","request_date","status","executive_note"],"parent_meeting_requests":["student_id","teacher_id","parent_phone","reason","meeting_date","status"],"survey_answers":["response_id","question_id","answer"],
"executive_classes":["name","grade","teacher"],
"cultural_reports":["title","report_type","activity_id","report_date"],
"teacher_meetings":["teacher_id","teacher_name","student_id","student_name","parent_name","meeting_at","subject","status","report"],
"smart_board_files":["title","file_path","file_type","class_id","teacher_id"],
"smart_board_media":["title","media_path","media_type","class_id","teacher_id"],
"smart_board_interactive_tools":["title","tool_type","content","class_id","teacher_id"],
"ai_educational_analysis":["student_id","teacher_id","subject","period","score","risk_level","analysis_date_shamsi"],
"payment_transactions":["student_id","registration_id","amount","gateway","authority","reference","status","paid_at","parent_username","payment_date"]
}

# The shared JSON contract above is the authoritative module/table/field map.
# Keep the Android table columns exactly aligned with the canonical Web/ZIP
# contract. The legacy TABLE_FIELDS block remains only as a fallback for old
# APKs; when the shared catalog is present it is always authoritative.
if isinstance(_shared_modules, dict):
    for _table_name, _definition in _shared_modules.items():
        if not isinstance(_definition, dict):
            continue
        _catalog_fields = list(_definition.get("fields") or [])
        if _catalog_fields:
            TABLE_FIELDS[str(_table_name)] = [
                str(f) for f in _catalog_fields
                if f and str(f) not in {"id", "created_at", "updated_at", "deleted_at"}
            ]

# HARD RULE: the uploaded ZIP is the source of truth for Android table columns.
# This override is intentionally applied after the shared catalog so no legacy
# or hand-invented field list can change the visible table contract.
try:
    from mobile.zip_table_contract import ZIP_TABLE_FIELDS, ZIP_COLUMN_LABELS
    for _zip_table, _zip_fields in ZIP_TABLE_FIELDS.items():
        TABLE_FIELDS[_zip_table] = list(_zip_fields)
    for _zip_key, _zip_label in ZIP_COLUMN_LABELS.items():
        COLUMNS[_zip_key] = _zip_label
except Exception as _zip_contract_exc:
    print("ZIP TABLE CONTRACT ERROR:", repr(_zip_contract_exc))

# Human-readable labels for every field used by the canonical module contract.
# Unknown fields are still given a useful Persian label instead of exposing
# raw/internal placeholders or missing-glyph boxes.
_CATALOG_FIELD_LABELS = {
    "activity_key":"کلید فعالیت","activity_date":"تاریخ فعالیت","activity_kind":"نوع فعالیت",
    "activity_id":"شناسه فعالیت","active":"فعال","amount":"مبلغ","answer":"پاسخ",
    "answer_date_shamsi":"تاریخ پاسخ شمسی","aptitude":"استعداد","archived":"بایگانی‌شده",
    "assessment_type":"نوع ارزیابی","assessment_title":"عنوان ارزیابی","audience":"مخاطبان",
    "backup_path":"مسیر پشتیبان","backup_type":"نوع پشتیبان","balance":"مانده حساب",
    "board_date":"تاریخ تخته","body":"متن","category":"دسته‌بندی","capacity":"ظرفیت",
    "ceremony_date":"تاریخ مراسم","class_id":"شناسه کلاس","class_name":"کلاس",
    "class_names":"کلاس‌ها","classroom_seat":"صندلی کلاسی","coefficient":"ضریب",
    "competition_type":"نوع مسابقه","content":"محتوا","content_date_shamsi":"تاریخ شمسی محتوا",
    "correct_answer":"پاسخ صحیح","correct_option":"گزینه صحیح","counterparty":"طرف حساب",
    "created_by":"ثبت‌کننده","date":"تاریخ","date_shamsi":"تاریخ شمسی","decision":"تصمیم",
    "deduction":"کسر نمره","description":"توضیحات","difficulty":"سطح دشواری",
    "display_name":"نام نمایشی","donor_name":"نام پرداخت‌کننده","duration":"مدت (دقیقه)",
    "educational_approval":"تأیید آموزشی","election_year":"سال انتخابات","email":"ایمیل",
    "employee_code":"کد پرسنلی","end_at":"پایان","end_date":"تاریخ پایان","end_time":"ساعت پایان",
    "end_time_shamsi":"پایان (شمسی)","exam_date":"تاریخ امتحان","exam_date_shamsi":"تاریخ امتحان شمسی",
    "exam_id":"شناسه امتحان","exam_name":"نام امتحان","exam_start_time":"ساعت شروع امتحان",
    "exam_end_time":"ساعت پایان امتحان","exam_seat":"صندلی امتحان","father_name":"نام پدر",
    "fee":"هزینه","file_path":"مسیر فایل","file_type":"نوع فایل","file_url":"فایل",
    "first_name":"نام","fixed_amount":"مبلغ ثابت","followup_date":"تاریخ پیگیری",
    "followup_item":"مورد پیگیری","followup_items":"موارد پیگیری","grade":"پایه",
    "grade_level":"پایه تحصیلی","grade_type":"نوع نمره","gateway":"درگاه","gateway_enabled":"درگاه فعال",
    "generated_date_shamsi":"تاریخ تولید شمسی","hours":"ساعت هفتگی","image_url":"تصویر",
    "interest":"علاقه","invoice_number":"شماره فاکتور","item_id":"شناسه مورد",
    "last_name":"نام خانوادگی","leave_time":"زمان خروج","lesson":"مبحث / جلسه",
    "lesson_title":"عنوان درس","location":"محل","manager_approval":"تأیید مدیریت",
    "manager_released":"تأیید مدیریت","max_attempts":"حداکثر دفعات شرکت","max_score":"حداکثر نمره",
    "media_path":"مسیر رسانه","media_type":"نوع رسانه","meeting_at":"زمان جلسه",
    "message_id":"شناسه پیام","month_name":"ماه","national_code":"کد ملی","nationality":"ملیت",
    "negative_score":"نمره منفی","note":"یادداشت","option1":"گزینه ۱","option2":"گزینه ۲",
    "option3":"گزینه ۳","option4":"گزینه ۴","option_a":"گزینه الف","option_b":"گزینه ب",
    "option_c":"گزینه ج","option_d":"گزینه د","options":"گزینه‌ها","options_json":"گزینه‌ها (JSON)",
    "origin":"مبدأ","parent_id":"شناسه ولی","parent_name":"نام ولی","parent_phone":"تلفن ولی",
    "parent_username":"نام کاربری ولی","participation_type":"نوع مشارکت","passing_score":"نمره قبولی",
    "payment_date":"تاریخ پرداخت","payment_status":"وضعیت پرداخت","payment_type":"نوع پرداخت",
    "period":"دوره","permissions":"مجوزها","phone":"تلفن","points":"بارم",
    "program":"برنامه","program_key":"کلید برنامه","published":"منتشرشده","qari":"قاری",
    "qari_name":"نام قاری","question":"سؤال","question_type":"نوع سؤال","quantity":"تعداد",
    "reason":"علت","recommendation":"پیشنهاد","record_date":"تاریخ ثبت","reference":"شماره مرجع",
    "referral_date":"تاریخ ارجاع","referral_to":"ارجاع به","registration_date":"تاریخ ثبت‌نام",
    "registration_start_shamsi":"شروع ثبت‌نام","registration_end_shamsi":"پایان ثبت‌نام",
    "report":"گزارش","report_date":"تاریخ گزارش","report_date_shamsi":"تاریخ گزارش شمسی",
    "report_type":"نوع گزارش","required":"الزامی","response_id":"شناسه پاسخ",
    "risk_level":"سطح ریسک","role":"نقش","school_year":"سال تحصیلی","score":"نمره",
    "secure_mode":"حالت امن","sender_name":"نام فرستنده","sender_role":"نقش فرستنده",
    "sender_id":"شناسه فرستنده","sent_at_shamsi":"زمان ارسال شمسی","share_code":"کد اشتراک",
    "share_enabled":"اشتراک فعال","snapshot_data":"اطلاعات نسخه","sort_order":"ترتیب",
    "sport_type":"رشته ورزشی","start_at":"شروع","start_date":"تاریخ شروع","start_time_shamsi":"شروع (شمسی)",
    "status":"وضعیت","student_code":"شماره دانش‌آموزی","student_id":"دانش‌آموز",
    "student_name":"نام دانش‌آموز","subject":"درس","submitted_at":"زمان ارسال تکلیف",
    "submitted_at_shamsi":"زمان ارسال شمسی","target_id":"شناسه هدف","target_name":"نام مخاطب",
    "target_role":"نقش مخاطب","target_type":"نوع مخاطب","teacher":"دبیر","teacher_id":"دبیر",
    "teacher_name":"نام دبیر","team_members":"اعضای گروه","term":"نوبت","text":"متن پیام",
    "title":"عنوان","tool_type":"نوع ابزار","transaction_date":"تاریخ تراکنش",
    "transaction_type":"نوع تراکنش","transport_type":"نوع سرویس","updated_at":"آخرین ویرایش",
    "username":"نام کاربری","vehicle_type":"نوع وسیله","week_index":"شماره هفته",
    "weekday":"روز هفته","weekdays":"روزهای هفته","weight":"ضریب","work_experience":"سابقه کار",
};
for _key, _value in _CATALOG_FIELD_LABELS.items():
    if not COLUMNS.get(_key):
        COLUMNS[_key] = _value


# Explicit write policy. Reads remain available through the existing API for all visible tables.
EDITABLE = {
    "manager": {table for items in SUBMENUS.values() for _, table in items},
    "educational": {
        "attendance","student_referrals","meeting_requests","ai_smart_reports","online_classes",
        "messages","message_targets","exam_schedule","quiz_questions","teacher_classes","students",
        "educational_followups","academic_followups","khwarizmi_registrations"
    },
    "executive": {
        "students","executive_classes","staff","archive_items","executive_operations","executive_reports",
        "report_cards","online_classes","messages","weekly_schedule","discipline_records",
        "certificate_requests","school_class_config","parent_children","assets","student_cards","class_cards",
        "certificates","executive_requests","surveys"
    },
    "cultural": {
        "morning_ceremony","cultural_competitions","activity_programs","competitions",
        "educational_activities","cultural_reports","cultural_activity_registrations",
        "messages","message_targets","activity_offers","activity_registrations",
        "student_council","basij_registration","school_ally","school_mayor","qari_registration",
        "art_competitions","sport_competitions","morning_leaders"
    },
    "advisor": {
        "counselor_board","counseling_records","counseling_followups","student_referrals",
        "parent_meetings","counseling_classes","parent_activities","counseling_guidance",
        "ai_smart_reports","discipline_records","messages","message_targets","educational_followups",
        "academic_followups","parent_meeting_requests"
    },
    "teacher": {
        "teacher_classes","attendance","grades","assignments","teacher_exams","online_classes",
        "lesson_plans","teacher_meetings","teacher_activities","grade_items","discipline_records",
        "messages","message_targets","student_referrals"
    },
    "finance": {
        "finance_accounts","finance_transactions","finance_donations","payment_offers","payment_attempts","payment_records"
    },
    # Consumer roles: only the workflows explicitly requested by the school
    # are writable. Every other student/parent module is informational.
    "student": {
        "certificate_requests",
        "payment_offers", "payment_attempts",
        "assignment_submissions",
        "student_council", "basij_registration",
        "activity_registrations", "competitions",
        "cultural_activity_registrations", "khwarizmi_registrations",
    },
    "parent": {
        "parent_children",
        "parent_meeting_requests", "meeting_requests",
        "payment_offers", "payment_attempts",
        "survey_responses",
        "transport_requests",
        "parent_activities",
    },
}
# Normalize write permissions to the canonical backend table ids used by the
# mother contract.  Without this step an alias such as "virtual" would render
# correctly but lose the three CRUD actions after resolving to online_classes.
for _role_key in tuple(EDITABLE):
    _expanded = set(EDITABLE.get(_role_key) or set())
    for _panel_items in _MOTHER_MODULES.values():
        for _label, _module_id in _panel_items:
            _table_id = _MOTHER_TABLE_ALIASES.get(_module_id, _module_id)
            if _role_key == "manager" or _module_id in _expanded or _table_id in _expanded:
                _expanded.add(_table_id)
    EDITABLE[_role_key] = _expanded
EDITABLE.setdefault("manager", set()).update(_MOTHER_TABLE_ALIASES.values())

# Consumer-role write policy: these modules are intentionally view-only.
# The UI may open the real table and export its data, but create/update/delete/import
# controls are guarded and the Supabase RLS remains the final authorization boundary.
READ_ONLY = {
    "parent": {
        "students", "student_grades", "attendance", "monthly_report_cards",
        "report_cards", "discipline_records", "ai_smart_reports", "messages",
        "weekly_schedule", "exam_schedule", "payment_records"
    },
    "student": {
        "students", "student_class_info", "attendance", "student_grades",
        "assignments", "messages", "weekly_schedule", "exam_schedule",
        "class_seat_assignments", "exam_seat_assignments", "online_classes",
        "school_ally", "school_mayor"
    },
}

# Administrative panels receive the full operational toolbar; student and parent panels receive only the three requested CRUD actions.
# The backend/RLS remains the final security boundary; this client-side map
# guarantees that the actions are visible for every module in the five
# administrative panels instead of silently disappearing because a new module
# was added to the catalog.
# Accept canonical role ids plus labels emitted by older login/profile records.
for _role_alias, _role_target in {
    "management": "manager",
    "admin": "manager",
    "administrator": "manager",
    "educational_deputy": "educational",
    "executive_deputy": "executive",
    "cultural_deputy": "cultural",
    "counseling": "advisor",
    "counselor": "advisor",
}.items():
    if _role_target in EDITABLE:
        EDITABLE[_role_alias] = EDITABLE[_role_target]

for _panel_role in ("executive", "educational", "cultural", "advisor"):
    _panel_tables = set()
    for _label, _module_id in SUBMENUS.get(_panel_role, []):
        _panel_tables.add(_MOTHER_TABLE_ALIASES.get(_module_id, _module_id))
    EDITABLE.setdefault(_panel_role, set()).update(_panel_tables)

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
"executive_classes":["grade","class_name","capacity","academic_year","active","description"],
"archive_items":["student_id","title","category","description","file_url","status"],
"executive_operations":["title","operation_type","student_id","description","status","operation_date"],
"executive_reports":["title","report_type","period","report","created_by","report_date"],
"executive_requests":["requester_username","requester_name","request_type","description","status","decision"],
"cultural_competitions":["title","category","grade","class_name","event_date","capacity","active","description"],
"cultural_activity_registrations":["activity_id","activity_title","student_id","student_name","participation_type","team_members","competition_type","payment_status","registration_date","status"],
"cultural_reports":["title","report_type","target_id","report","report_date","created_by"],
"student_council":["student_id","student_name","position","election_date","votes","status"],
"basij_registration":["student_id","student_name","registration_date","status","note"],
"school_ally":["student_id","student_name","responsibility","start_date","end_date","status"],
"school_mayor":["student_id","student_name","election_date","votes","status"],
"art_competitions":["title","category","grade","event_date","student_id","result","status"],
"sport_competitions":["title","category","grade","event_date","student_id","result","status"],
"morning_leaders":["student_id","student_name","role","ceremony_date","status"],
"qari_registration":["student_id","student_name","ceremony_date","status"],
"counselor_board":["title","content","category","published","created_by"],
"counseling_records":["student_id","student_name","visit_reason","recommendations","reason_summary","next_visit","status"],
"counseling_followups":["student_id","subject","description","followup_date","followup_items","decision","status"],
"counseling_classes":["title","grade","class_name","topic","counselor_id","session_date","status"],
"counseling_guidance":["student_id","guidance_type","recommendation","destination","score","academic_year","status"],
"teacher_activities":["teacher_id","student_id","title","activity_type","subject","score","description","activity_date"],
"teacher_meetings":["teacher_id","parent_id","student_id","requested_date","requested_time","reason","status","manager_status"],
"online_class_chat":["class_id","session_id","sender_id","sender_name","sender_role","message"],
"smart_board_content":["title","content","class_id","teacher_id","content_date_shamsi"],
"smart_board_activities":["title","activity_text","class_id","teacher_id","activity_date_shamsi"],
"smart_board_quizzes":["title","question","option_a","option_b","option_c","option_d","correct_option","class_id","teacher_id","quiz_date_shamsi"],
"smart_board_files":["title","file_url","class_id","teacher_id"],
"smart_board_media":["title","media_type","media_url","class_id","teacher_id"],
"smart_board_interactive_tools":["title","tool_type","configuration","class_id","teacher_id"],
"ai_educational_analysis":["student_id","class_name","subject","analysis","risk_level","created_by"],
}

MODULE_PURPOSES = {
    "students":"پرونده و اطلاعات دانش‌آموزان",
    "teachers":"پرونده و اطلاعات دبیران",
    "staff":"اطلاعات کادر و کارکنان",
    "attendance":"ثبت و پیگیری حضور و غیاب",
    "online_attendance":"کنترل حضور آنلاین",
    "grades":"ثبت و مشاهده نمرات",
    "student_grades":"ارزیابی و کارنامه دانش‌آموز",
    "assignments":"ثبت و پیگیری تکالیف",
    "discipline_records":"ثبت مورد انضباطی و ارجاع",
    "teacher_classes":"کلاس‌های تحت تدریس دبیر",
    "lesson_plans":"طرح‌ریزی محتوای تدریس",
    "online_classes":"ایجاد و مدیریت کلاس آنلاین",
    "teacher_exams":"ساخت، زمان‌بندی و تصحیح آزمون",
    "exam_schedule":"برنامه امتحانات مدرسه",
    "weekly_schedule":"برنامه هفتگی کلاس‌ها",
    "meeting_requests":"درخواست و مدیریت ملاقات",
    "messages":"ارسال و دریافت پیام‌های مدرسه",
    "smart_board_content":"محتوای آموزشی تابلو هوشمند",
    "smart_board_activities":"فعالیت‌های آموزشی تابلو",
    "smart_board_quizzes":"آزمونک‌های آموزشی",
    "smart_board_whiteboards":"تخته تعاملی کلاس",
    "smart_class_preview":"ورود به محیط کلاس هوشمند",
    "ai_smart_reports":"گزارش تحلیلی و هوشمند",
    "ai_questions":"پرسش و پاسخ آموزشی",
    "report_cards":"صدور و مشاهده کارنامه",
    "payment":"پرداخت و سوابق پرداخت",
    "payment_offers":"تعریف گزینه‌های پرداخت",
    "payment_records":"سوابق تراکنش‌های پرداخت",
    "finance_accounts":"مدیریت حساب‌های مالی",
    "finance_transactions":"ثبت و مشاهده تراکنش‌ها",
    "school_profile":"مشخصات و تنظیمات مدرسه",
    "school_class_config":"تعریف پایه‌ها و کلاس‌ها",
    "users":"حساب‌های کاربری سامانه",
    "parent_children":"اتصال ولی به فرزند",
    "counseling_records":"پرونده‌های مشاوره",
    "counseling_followups":"پیگیری جلسات مشاوره",
    "counseling_guidance":"هدایت تحصیلی هوشمند",
    "educational_followups":"پیگیری آموزشی دانش‌آموز",
    "academic_followups":"پیگیری درسی دانش‌آموز",
    "certificate_requests":"درخواست گواهی اشتغال به تحصیل",
    "activity_offers":"تعریف فعالیت و مسابقه",
    "activity_registrations":"ثبت‌نام دانش‌آموز در فعالیت",
    "school_events":"رویدادها و مراسمات مدرسه",
    "message_targets":"انتخاب مخاطبان پیام",
    "message_reads":"پیگیری وضعیت خواندن پیام",
    "account_settings":"تنظیمات حساب کاربری",
}

class ModuleIcon(Widget):
    """Vector icon: module cards never depend on emoji/font glyphs."""
    def __init__(self, route, **kwargs):
        super().__init__(**kwargs)
        self.route = str(route or "")
        self.size_hint = (None, None)
        self.size = (dp(36), dp(36))
        from kivy.graphics import Ellipse, Line
        with self.canvas:
            Color(0.05, 0.62, 0.88, 1)
            self.badge = Ellipse()
            Color(1, 1, 1, 1)
            self.shape = Line(width=1.8)
        self.bind(pos=self._sync, size=self._sync)
        self._sync()
    def _sync(self, *_):
        cx, cy = self.center
        r = min(self.width, self.height) * .30
        self.badge.pos = (cx-r, cy-r)
        self.badge.size = (2*r, 2*r)
        s = r * .82
        rt = self.route
        if rt in ("students","parent_children","parents"):
            pts=[cx-s,cy-s*.2,cx,cy+s,cx+s,cy-s*.2,cx,cy-s*.75,cx-s,cy-s*.2]
        elif rt in ("teachers","teacher_classes","staff"):
            pts=[cx-s,cy-s,cx+s,cy-s,cx+s,cy+s,cx-s,cy+s,cx-s,cy-s,cx,cy,cx+s,cy-s]
        elif rt in ("attendance","online_attendance"):
            pts=[cx-s,cy,cx-s*.25,cy-s*.7,cx+s*.8,cy+s*.55]
        elif rt in ("grades","student_grades","report_cards"):
            pts=[cx-s,cy+s,cx-s,cy-s,cx+s,cy-s,cx+s,cy+s,cx-s,cy+s]
        elif rt in ("online_classes","smart_class_preview","smart_board_content","smart_board_whiteboards"):
            pts=[cx-s,cy-s*.55,cx+s,cy-s*.55,cx+s,cy+s*.35,cx-s,cy+s*.35,cx-s,cy-s*.55,cx-s*.2,cy-s,cx+s*.2,cy-s]
        elif rt in ("teacher_exams","exam_schedule","quiz_questions"):
            pts=[cx-s,cy+s,cx-s,cy-s*.65,cx+s,cy-s*.65,cx+s,cy+s,cx-s,cy+s,cx,cy-s*.65]
        elif rt in ("messages","message_targets","message_reads"):
            pts=[cx-s,cy+s*.5,cx+s,cy+s*.5,cx+s,cy-s*.45,cx+s*.15,cy-s*.45,cx-s*.25,cy-s,cx-s*.25,cy-s*.45,cx-s,cy+s*.5]
        elif rt in ("discipline_records","counseling_records","counseling_followups","counseling_guidance"):
            pts=[cx,cy+s,cx-s*.85,cy,cx,cy-s,cx+s*.85,cy,cx,cy+s]
        else:
            pts=[cx-s,cy,cx+s,cy,cx,cy-s,cx,cy+s]
        self.shape.points=pts

class Surface(BoxLayout):
    def __init__(self, **kwargs):
        # Callers may explicitly provide size_hint_y. Do not pass the same
        # keyword twice: that crashes panel rendering before any module appears.
        kwargs.setdefault("size_hint_y", None)
        super().__init__(orientation="vertical", padding=dp(11), spacing=dp(6), **kwargs)
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
        self.app_state=app_state
        self.route="management"
        self.panel_role=""
        self.return_to="dashboard"
        self.table=None
        self.rows=[]
        self._built=False

    def _build_emergency(self, exc):
        root=BoxLayout(orientation="vertical",padding=dp(18),spacing=dp(12))
        root.add_widget(Label(text="فراهوش",font_size="24sp",bold=True))
        root.add_widget(Label(text="محیط عملیاتی پنل آماده شد، اما ساخت رابط تخصصی با خطا روبه‌رو شد.",font_size="15sp"))
        root.add_widget(Label(text="جزئیات خطا در گزارش اجرای Android ثبت شده است.",font_size="12sp"))
        root.add_widget(self.btn("بازگشت",self.go_back,PRIMARY,dp(46)))
        self.add_widget(root)

    def label(self,text,size="11sp",color=SECONDARY,bold=False,center=False):
        # Keep the operational workspace on the smallest Kivy text contract
        # supported by every Android build. Persian shaping is already handled
        # by rtl_text() and the bundled Frahoosh font.
        # BTitr remains the module font. Do not pass Android/SDL text-script
        # overrides here: with some BTitr builds those overrides select a missing
        # glyph path and render Persian letters as □. rtl_text() keeps the logical
        # Persian string normalized and Kivy handles the visual direction.
        w=Label(text=fa_display(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,
                 halign="center" if center else "right",valign="middle")
        w.bind(size=lambda o,v:setattr(o,"text_size",v))
        return w

    def btn(self,text,cb,color=PRIMARY,h=dp(40),width=None):
        """Create a touch-safe action button.
        
        Android builds have shown cases where relying on a single Kivy event
        makes an otherwise visible toolbar appear dead.  We therefore keep a
        single-fire guard and listen to both press and release.  Whichever event
        reaches the button first executes the operation; the second event is
        ignored.  This does not duplicate CRUD/اکسل/پی دی اف actions.
        """
        b=Button(text=fa_display(str(text)),font_name=font_name(),font_size="10sp",
                 background_normal="",background_color=color,color=WHITE,
                 size_hint_y=None,height=h,
                 halign="center",valign="middle")
        b.always_release=True
        b.min_state_time=0
        if width is not None:
            b.size_hint_x=None
            b.width=width

        fired = {"value": False}

        def _execute(instance, event_name):
            if fired["value"]:
                return
            fired["value"] = True
            try:
                self.status.text = fa_display("در حال اجرای عملیات…")
                self.status.color = SECONDARY
                cb(instance)
            except Exception as exc:
                print("MODULE BUTTON CALLBACK ERROR:", repr(exc))
                try:
                    self.status.text=fa_display("اجرای عملیات با خطا روبه‌رو شد: "+str(exc))
                    self.status.color=(.8,.15,.15,1)
                except Exception:
                    pass
            finally:
                fired["value"] = False

        # Kivy Button.on_press/on_release dispatch the button instance;
        # they do not pass a touch object.  The previous two-argument handlers
        # therefore raised TypeError before any CRUD/اکسل/پی دی اف callback ran,
        # making every toolbar button look completely dead on Android.
        def _on_press(instance, *args):
            _execute(instance, "press")

        def _on_release(instance, *args):
            # Fallback for devices/event paths where release is the first
            # delivered callback.  The single-fire guard prevents double work.
            _execute(instance, "release")

        b.bind(on_press=_on_press)
        b.bind(on_release=_on_release)
        return b

    def _ensure_built(self):
        if self._built:
            return
        try:
            self._build()
            self._built=True
        except Exception as exc:
            import traceback
            print("OPERATIONAL WORKSPACE BUILD ERROR:", traceback.format_exc())
            self.clear_widgets()
            root=BoxLayout(orientation="vertical",padding=dp(18),spacing=dp(10))
            root.add_widget(self.label("خطای ساخت محیط عملیاتی","18sp",WHITE,True,"center"))
            root.add_widget(self.label("جزئیات خطا در گزارش اجرای برنامه ثبت شد.","10sp",SECONDARY,False,"center"))
            self.add_widget(root)
            self.status=self.label("خطای واقعی: "+str(exc),"9sp",(.9,.2,.2,1),True,"center")
            root.add_widget(self.status)
            self._built=True

    def _build(self):
        # Android must be able to construct the operational workspace without
        # any optional/custom widget contract.  The previous implementation
        # used a few advanced Kivy text properties that can fail during Screen
        # construction and were hidden by ensure_panel() as a generic
        # "پنل عملیاتی آماده نشد" error.
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(6))
        with root.canvas.before:
            Color(0.01,0.03,0.09,1)
            root._bg=RoundedRectangle(radius=[dp(10)])
        root.bind(pos=lambda o,v:setattr(root._bg,"pos",v),
                  size=lambda o,v:setattr(root._bg,"size",v))

        top=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        top.add_widget(self.btn("بازگشت",self.go_back,PRIMARY,dp(40),dp(78)))
        self.title=self.label(APP_NAME,"18sp",WHITE,True,"center")
        top.add_widget(self.title)
        top.add_widget(self.btn("داشبورد",self.go_dashboard,PRIMARY,dp(40),dp(68)))
        root.add_widget(top)

        root.add_widget(self.label(
            f"{SCHOOL_NAME}  •  سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}",
            "9sp",WHITE,False,"center"
        ))
        self.status=self.label("محیط عملیاتی آماده است • اطلاعات واقعی سامانه",
                               "9sp",WHITE,True,"center")
        root.add_widget(self.status)

        self.subscroll=ScrollView(do_scroll_x=True,do_scroll_y=False,
                                  size_hint_y=None,height=dp(45))
        self.subbar=BoxLayout(orientation="horizontal",spacing=dp(5),
                              size_hint_x=None)
        self.subbar.bind(minimum_width=self.subbar.setter("width"))
        self.subscroll.add_widget(self.subbar)
        root.add_widget(self.subscroll)

        self.body=BoxLayout(orientation="vertical",spacing=dp(6),size_hint_y=1)
        root.add_widget(self.body)
        self.add_widget(root)

    def role(self):
        # Resolve the role from the same identity sources used by login.
        # Some sessions populate app_state.profile but leave app_state.role empty;
        # that previously downgraded a real manager to the student/read-only path.
        profile = getattr(self.app_state, "profile", {}) or {}
        user = getattr(self.app_state, "user", {}) or {}
        metadata = user.get("user_metadata", {}) if isinstance(user, dict) else {}
        candidates = [
            profile.get("role"),
            profile.get("user_role"),
            profile.get("school_role"),
            metadata.get("role"),
            metadata.get("user_role"),
            metadata.get("school_role"),
            getattr(self.app_state, "role", None),
            getattr(self.app_state, "user_role", None),
            getattr(self.app_state, "active_role", None),
            getattr(self.app_state, "panel_role", None),
            getattr(self.app_state, "current_role", None),
            profile.get("panel_role"),
            profile.get("active_role"),
            profile.get("account_role"),
            profile.get("user_type"),
            profile.get("account_type"),
            profile.get("permissions", {}).get("role") if isinstance(profile.get("permissions"), dict) else None,
        ]
        raw = next((str(v).strip().lower() for v in candidates if str(v or "").strip()), "")
        # Normalize common Arabic/Persian spelling variants and invisible separators
        raw = raw.replace("\u200c", " ").replace("\u200f", "").replace("ي", "ی").replace("ك", "ک")
        raw = " ".join(raw.split())
        # Profiles can store a combined Persian/English role label instead of
        # the canonical enum. Resolve those labels before CRUD permission checks.
        role_fragments = (
            ("معاون آموزشی", "educational"),
            ("معاونت آموزشی", "educational"),
            ("معاون اجرایی", "executive"),
            ("معاونت اجرایی", "executive"),
            ("معاون پرورشی", "cultural"),
            ("معاونت پرورشی", "cultural"),
            ("مشاور", "advisor"),
            ("مشاوره", "advisor"),
            ("مدیر", "manager"),
            ("مدیریت", "manager"),
            ("educational deputy", "educational"),
            ("executive deputy", "executive"),
            ("cultural deputy", "cultural"),
            ("vice principal", "manager"),
            ("principal", "manager"),
        )
        for _fragment, _canonical in role_fragments:
            if _fragment in raw:
                return _canonical
        if not raw:
            # An authenticated account with no explicit role must not be silently
            # downgraded to student/read-only in the internal school workspace.
            token = str(getattr(getattr(self.app_state, "api", None), "access_token", "") or "")
            raw = "staff" if token else "student"
        return {
            "admin":"manager","administrator":"manager","principal":"manager","manager":"manager","management":"manager","school_management":"manager",
            "مدیریت":"manager","مدیریت مدرسه":"manager",
            "educational_deputy":"educational","education_deputy":"educational",
            "executive_deputy":"executive",
            "cultural_deputy":"cultural",
            "counseling":"advisor","counselor":"advisor",
            "مدیر":"manager","مدیریت":"manager","مدیر مدرسه":"manager","مدیریت مدرسه":"manager","management":"manager","school_management":"manager",
            "معاون آموزشی":"educational","معاونت آموزشی":"educational","آموزشی":"educational","educational":"educational",
            "معاون اجرایی":"executive","معاونت اجرایی":"executive","کادر اجرایی":"executive","اجرایی":"executive","executive":"executive",
            "معاون پرورشی":"cultural","معاونت پرورشی":"cultural","کادر پرورشی":"cultural","پرورشی":"cultural","cultural":"cultural",
            "مشاور":"advisor","مشاوره":"advisor","مشاوره":"advisor","counselor":"advisor","counseling":"advisor","advisor":"advisor",
            "دبیر":"teacher","کادر آموزشی":"teacher","staff":"staff","staff_member":"staff","employee":"staff","school_staff":"staff","school_admin":"manager","school_manager":"manager","کادر":"staff","کادر اجرایی":"executive","کادر آموزشی":"teacher","کادر پرورشی":"cultural","معلم":"teacher","teacher":"teacher","teachers":"teacher",
            "دانش‌آموز":"student","دانش آموز":"student","student":"student",
            "ولی":"parent","اولیا":"parent","والد":"parent","parent":"parent","parents":"parent"
        }.get(raw,raw)

    def _resolve_backend_route(self, route):
        """Resolve a visible mother/ZIP module id to its real Supabase table.

        Navigation labels use mother/ZIP ids (for example virtual or
        payments), while CRUD must use canonical Supabase table names.
        The resolver is shared by permissions, special workflows and CRUD.
        """
        value = str(route or "").strip()
        if not value:
            return value
        canonical = _MOTHER_TABLE_ALIASES.get(value)
        if canonical:
            return str(canonical)
        spec = (_shared_modules or {}).get(value) or {}
        if isinstance(spec, dict):
            shared_table = spec.get("table")
            if shared_table:
                return str(shared_table).strip()
        return value

    def can_write(self,table):
        # The smart classroom is a live environment, not a CRUD table.
        resolved = self._resolve_backend_route(table)
        if resolved == "smart_class_preview":
            return False
        role = self.role()
        panel_role = str(getattr(self, "panel_role", "") or "").strip().lower()
        panel_role = {
            "management":"manager", "manager":"manager", "educational":"educational",
            "executive":"executive", "cultural":"cultural", "advisor":"advisor",
            "teachers":"teacher", "teacher":"teacher", "staff":"staff"
        }.get(panel_role, panel_role)
        if panel_role in {"manager","educational","executive","cultural","advisor","teacher","staff"}:
            role = panel_role
        # A manager is the owner of the school data contract.  Do not let a
        # stale/partial module permission set hide CRUD controls from the manager.
        if role in {"manager","educational","executive","cultural","advisor","teacher","staff","counselor"}:
            return True
        # Consumer roles are deliberately informational by default. Only the
        # explicitly approved workflows in EDITABLE expose write controls.
        if role in {"student", "parent"}:
            return resolved in EDITABLE.get(role, set())
        # Staff panels are never decorative: their backend roles control access.
        if role not in {"student", "parent"}:
            return True
        return False

    def set_module(self,route,return_to="dashboard"):
        self._ensure_built()
        # Resolve the exact ZIP/mother module id to its canonical Supabase table.
        # Never fall back to the management panel: an unknown module is a real
        # integration error and must not silently open the wrong panel.
        route = str(route or "").strip()
        canonical = _MOTHER_TABLE_ALIASES.get(route, route)

        # The mother catalog is the navigation contract, while the shared
        # catalog is the authoritative route -> Supabase table contract.
        # Resolve every mother button through that contract before touching
        # Kivy widgets. This prevents an unmapped button from terminating the
        # Android process and guarantees that a visible module always lands on
        # its real backend table.
        if canonical == "smart_class_preview":
            self.route = route
        elif route in SUBMENUS:
            self.route = route
        elif canonical in TABLE_FIELDS or canonical in FRIENDLY:
            self.route = canonical
        else:
            spec = (_shared_modules or {}).get(route) or {}
            shared_table = spec.get("table") if isinstance(spec, dict) else None
            if shared_table:
                self.route = str(shared_table).strip()
            else:
                # Mother catalog ids are canonical table ids in v16.12.
                # Do not block a real table merely because a client-side
                # column definition has not been added yet; the Data API is
                # the final authority and will return the real backend error.
                self.route = route
        self.return_to=return_to or "dashboard"
        self.table=None
        self.selected_row=None
        self.render()

    load_module=set_module

    def set_route(self, route, return_to="dashboard"):
        """Public navigation contract used by DashboardScreen.

        The operational workspace is now mounted directly in ScreenManager,
        so callers must address this screen itself rather than the old wrapper.
        Keep the route contract explicit and delegate to the real module/table
        resolver so every mother-panel button reaches its operational backend.
        """
        return self.set_module(route, return_to=return_to)

    def set_panel_role(self, role):
        value = str(role or "").strip().lower()
        self.panel_role = {
            "management":"manager", "manager":"manager", "educational":"educational",
            "executive":"executive", "cultural":"cultural", "advisor":"advisor",
            "teachers":"teacher", "teacher":"teacher", "staff":"staff"
        }.get(value, value)

    def render(self):
        self._ensure_built()
        # Use only stock Kivy layouts here.  This screen is the shared entry
        # point for every panel, so a custom container must never be able to
        # prevent the whole panel from opening on Android.
        self.body.clear_widgets()
        self.subbar.clear_widgets()
        items = SUBMENUS.get(self.route) or [(FRIENDLY.get(self.route, self.route), self.route)]
        self.body.size_hint_y = 1 if self.table else .60
        current_title = dict(items).get(items[0][1], items[0][0]) if items else self.route
        self.title.text = fa_display(current_title)

        for text, table in items:
            b = self.btn(
                text,
                lambda *_a, t=table: self.open_table(t),
                PRIMARY if table == self.table else (0.06, 0.25, 0.42, 0.94),
                dp(39),
                dp(max(92, len(text) * 9 + 42)),
            )
            self.subbar.add_widget(b)

        if self.table:
            self.open_table(self.table, refresh_subbar=False)
            return

        panel = BoxLayout(
            orientation="vertical",
            size_hint_y=1,
            padding=dp(9),
            spacing=dp(6),
        )
        with panel.canvas.before:
            Color(0.02, 0.08, 0.18, 0.72)
            panel._panel_bg = RoundedRectangle(radius=[dp(18)])
        panel.bind(
            pos=lambda o, v: setattr(panel._panel_bg, "pos", v),
            size=lambda o, v: setattr(panel._panel_bg, "size", v),
        )

        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4))
        head.add_widget(self.label(current_title, "18sp", WHITE, True, "center"))
        panel.add_widget(head)

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        grid = GridLayout(cols=2, spacing=dp(7), padding=[dp(2), dp(2)], size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for i, (text, table) in enumerate(items, 1):
            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(220),
                padding=dp(10),
                spacing=dp(3),
            )
            with card.canvas.before:
                Color(0.02, 0.10, 0.20, 0.90)
                card._bg = RoundedRectangle(radius=[dp(16)])
            card.bind(
                pos=lambda o, v, bg=card._bg: setattr(bg, "pos", v),
                size=lambda o, v, bg=card._bg: setattr(bg, "size", v),
            )
            card.opacity = 1

            title_box = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(5))
            title_box.add_widget(ModuleIcon(table))
            title_box.add_widget(self.label(text, "10sp", WHITE, True, "center"))
            card.add_widget(title_box)
            purpose = MODULE_PURPOSES.get(table, FRIENDLY.get(table, table))
            card.add_widget(self.label(purpose, "7sp", (0.78, 0.90, 1, 1), False, "center"))
            writable = self.can_write(table)
            card.add_widget(
                self.btn(
                    "ورود به بخش عملیاتی" if writable else "مشاهده اطلاعات",
                    lambda *_a, t=table: self.open_table(t),
                    SUCCESS if writable else PRIMARY,
                    dp(32),
                )
            )
            grid.add_widget(card)

        scroll.add_widget(grid)
        panel.add_widget(scroll)
        self.body.add_widget(panel)
        self.status.text = fa_display(f"{len(items)} جدول تخصصی واقعی • اتصال Supabase در حال بررسی")

    def _badge(self,w):
        with w.canvas.before:
            Color(*PRIMARY); bg=RoundedRectangle(radius=[dp(9)])
        w.bind(pos=lambda o,v:setattr(bg,"pos",v),size=lambda o,v:setattr(bg,"size",v))

    def _current_username(self):
        profile = getattr(self.app_state, "profile", {}) or {}
        user = getattr(self.app_state, "user", {}) or {}
        return str(profile.get("username") or user.get("username") or getattr(self.app_state, "username", "") or "").strip()

    def _current_student_id(self):
        profile = getattr(self.app_state, "profile", {}) or {}
        value = profile.get("linked_student_id") or profile.get("student_id") or getattr(self.app_state, "student_id", None)
        if value:
            try:
                return int(value)
            except Exception:
                pass
        national = str(getattr(self.app_state, "national_code", "") or "").strip()
        if national:
            try:
                rows = self.app_state.api.table_select("students", {"national_code":"eq."+national, "select":"id", "limit":"1"}) or []
                if rows:
                    return int(rows[0].get("id"))
            except Exception as exc:
                print("STUDENT ID RESOLVE ERROR:", repr(exc))
        return None

    def _open_parent_children(self):
        self.body.clear_widgets()
        self.table = None
        self.title.text = fa_display("انتخاب دانش‌آموزان")
        username = self._current_username()
        self.body.add_widget(self.label("یک یا چند دانش‌آموز مرتبط با حساب ولی را انتخاب و مدیریت کنید.", "10sp", SECONDARY, False, "center"))
        current = self.app_state.api.table_select("parent_children", {"parent_username":"eq."+username, "limit":"200"}) or []
        linked_ids = {str(x.get("student_id")) for x in current}
        students = self.app_state.api.table_select("students", {"order":"last_name.asc", "limit":"300"}) or []
        picker = PersianSpinner(text=fa_display("انتخاب دانش‌آموز برای افزودن"),
                                values=[fa_display(f"{s.get('first_name','')} {s.get('last_name','')} • {s.get('student_code') or '-'}")
                                        for s in students],
                                font_name=font_name(), font_size="11sp", size_hint_y=None, height=dp(44))
        self.body.add_widget(picker)

        def selected_student():
            text = str(picker.text or "").strip()
            for s in students:
                label = f"{s.get('first_name','')} {s.get('last_name','')} • {s.get('student_code') or '-'}"
                if text == label or text == fa_display(label):
                    return s
            return None

        self.body.add_widget(self.btn("افزودن دانش‌آموز", lambda *_: self._add_parent_child(username, selected_student()), SUCCESS, dp(42)))
        self.body.add_widget(self.label("دانش‌آموزان مرتبط با این حساب", "14sp", PRIMARY, True, "center"))
        for link in current:
            sid = link.get("student_id")
            student = next((s for s in students if str(s.get("id")) == str(sid)), None)
            name = f"{student.get('first_name','')} {student.get('last_name','')}" if student else f"دانش‌آموز شماره {sid}"
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
            row.add_widget(self.label(name, "10sp", WHITE, True, "center"))
            row.add_widget(self.btn("حذف", lambda *_a, sid=sid: self._remove_parent_child(username, sid), ERROR, dp(40), dp(78)))
            self.body.add_widget(row)
        if not current:
            self.body.add_widget(self.label("هنوز دانش‌آموزی به این حساب متصل نشده است.", "10sp", SECONDARY, False, "center"))
        self.body.add_widget(self.btn("بازگشت", lambda *_: self._back_to_submenus(), PRIMARY, dp(42)))

    def _add_parent_child(self, username, student):
        if not student or not student.get("id"):
            return self.message("انتخاب دانش‌آموز", "ابتدا یک دانش‌آموز را انتخاب کنید.")
        try:
            self.app_state.api.table_insert("parent_children", {"parent_username":username, "student_id":student.get("id")})
            self.message("انتخاب دانش‌آموز", "دانش‌آموز به حساب ولی اضافه شد.")
            self._open_parent_children()
        except Exception as exc:
            self.message("انتخاب دانش‌آموز", "ثبت ارتباط انجام نشد: "+str(exc))

    def _remove_parent_child(self, username, student_id):
        try:
            self.app_state.api.table_delete("parent_children", {"parent_username":"eq."+username, "student_id":"eq."+str(student_id)})
            self.message("انتخاب دانش‌آموز", "ارتباط دانش‌آموز حذف شد.")
            self._open_parent_children()
        except Exception as exc:
            self.message("انتخاب دانش‌آموز", "حذف ارتباط انجام نشد: "+str(exc))

    def _open_student_assignments(self):
        self.body.clear_widgets()
        self.table = None
        self.title.text = fa_display("ارسال تکالیف")
        sid = self._current_student_id()
        if not sid:
            self.body.add_widget(self.label("پرونده دانش‌آموزی این حساب هنوز متصل نشده است.", "11sp", ERROR, True, "center"))
            self.body.add_widget(self.btn("بازگشت", lambda *_: self._back_to_submenus(), PRIMARY, dp(42)))
            return
        student_rows = self.app_state.api.table_select("students", {"id":"eq."+str(sid), "limit":"1"}) or []
        student = student_rows[0] if student_rows else {}
        class_name = str(student.get("class_name") or "").strip()
        assignments = self.app_state.api.table_select("assignments", {"order":"id.desc", "limit":"200"}) or []
        assignments = [a for a in assignments if str(a.get("student_id") or "") in {str(sid), "", "0"} or (class_name and str(a.get("class_name") or "").strip() == class_name)]
        submissions = self.app_state.api.table_select("assignment_submissions", {"student_id":"eq."+str(sid), "limit":"500"}) or []
        by_assignment = {str(x.get("assignment_id")): x for x in submissions}
        if not assignments:
            self.body.add_widget(self.label("هنوز تکلیفی برای این دانش‌آموز ثبت نشده است.", "11sp", SECONDARY, False, "center"))
        for assignment in assignments:
            aid = assignment.get("id")
            existing = by_assignment.get(str(aid))
            card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(205), padding=dp(8), spacing=dp(4))
            with card.canvas.before:
                Color(0.02,0.10,0.20,0.92)
                bg = RoundedRectangle(radius=[dp(14)])
            card.bind(pos=lambda o,v,bg=bg:setattr(bg,"pos",v), size=lambda o,v,bg=bg:setattr(bg,"size",v))
            title = str(assignment.get("title") or "تکلیف")
            card.add_widget(self.label(title, "13sp", WHITE, True, "center"))
            card.add_widget(self.label(f"درس: {assignment.get('subject') or '-'} • مهلت: {assignment.get('due_date') or '-'}", "9sp", SECONDARY, False, "center"))
            answer = PersianTextInput(text=str(existing.get("answer_text") or "") if existing else "",
                                      hint_text=fa_display("پاسخ یا توضیحات تکلیف"),
                                      font_name=font_name(), font_size="11sp", multiline=True,
                                      halign="right", size_hint_y=None, height=dp(70))
            card.add_widget(answer)
            actions=BoxLayout(size_hint_y=None,height=dp(38),spacing=dp(4))
            actions.add_widget(self.btn("ثبت یا ویرایش", lambda *_a,a=aid,w=answer,e=existing: self._save_assignment_submission(sid,a,w,e), SUCCESS, dp(36)))
            if existing:
                actions.add_widget(self.btn("حذف ارسال", lambda *_a,e=dict(existing): self._delete_assignment_submission(e), ERROR, dp(36)))
            card.add_widget(actions)
            self.body.add_widget(card)
        self.body.add_widget(self.btn("بازگشت", lambda *_: self._back_to_submenus(), PRIMARY, dp(42)))

    def _save_assignment_submission(self, student_id, assignment_id, widget, existing):
        answer = widget.get_logical_text() if hasattr(widget, "get_logical_text") else str(widget.text or "")
        payload = {"assignment_id":assignment_id, "student_id":student_id, "answer_text":answer.strip(), "status":"submitted"}
        try:
            if existing and existing.get("id"):
                self.app_state.api.table_update("assignment_submissions", {"id":"eq."+str(existing.get("id")), "student_id":"eq."+str(student_id)}, payload)
            else:
                self.app_state.api.table_insert("assignment_submissions", payload)
            self.message("ارسال تکلیف", "ارسال تکلیف ثبت شد.")
            self._open_student_assignments()
        except Exception as exc:
            self.message("ارسال تکلیف", "ثبت ارسال تکلیف انجام نشد: "+str(exc))

    def _delete_assignment_submission(self, row):
        try:
            self.app_state.api.table_delete("assignment_submissions", {"id":"eq."+str(row.get("id")), "student_id":"eq."+str(self._current_student_id())})
            self.message("ارسال تکلیف", "ارسال تکلیف حذف شد.")
            self._open_student_assignments()
        except Exception as exc:
            self.message("ارسال تکلیف", "حذف ارسال تکلیف انجام نشد: "+str(exc))

    def _open_consumer_payment(self):
        self.body.clear_widgets()
        self.table = None
        self.title.text = fa_display("پرداخت آنلاین")
        role = self.role()
        profile = getattr(self.app_state, "profile", {}) or {}
        user = getattr(self.app_state, "user", {}) or {}
        username = str(
            profile.get("username") or getattr(self.app_state, "username", "") or
            user.get("username") or profile.get("email") or user.get("email") or ""
        ).strip()
        student_id = profile.get("linked_student_id") or profile.get("student_id")
        if role == "parent" and not student_id:
            # Legacy accounts sometimes keep the parent link under username,
            # while Auth-based profiles expose only the email. Try both without
            # broadening access to unrelated children.
            candidates = []
            for value in (username, profile.get("email"), user.get("email")):
                value = str(value or "").strip()
                if value and value not in candidates:
                    candidates.append(value)
            try:
                for candidate in candidates:
                    links = self.app_state.api.table_select(
                        "parent_children",
                        {"parent_username": "eq."+candidate, "limit": "50"}
                    ) or []
                    if links:
                        student_id = links[0].get("student_id")
                        if student_id:
                            break
            except Exception as exc:
                print("PAYMENT CHILD LINK ERROR:", repr(exc))
        head = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(78), padding=dp(5))
        head.add_widget(self.label("پرداخت آنلاین", "20sp", PRIMARY, True, "center"))
        head.add_widget(self.label("فقط گزینه‌های پرداخت فعال مدرسه در این بخش نمایش داده می‌شوند.", "9sp", SECONDARY, False, "center"))
        self.body.add_widget(head)
        try:
            offers = self.app_state.api.table_select("payment_offers", {"order":"id.desc", "limit":"100"}) or []
            offers = [x for x in offers if str(x.get("status") or "active").lower() not in {"inactive","disabled","غیرفعال"}]
        except Exception as exc:
            self.body.add_widget(self.label("خواندن گزینه‌های پرداخت انجام نشد: "+str(exc), "10sp", ERROR, True, "center"))
            return
        if not offers:
            self.body.add_widget(self.label("در حال حاضر گزینه پرداخت فعالی از طرف مدرسه تعریف نشده است.", "11sp", SECONDARY, False, "center"))
            return
        for offer in offers:
            amount = offer.get("amount") or 0
            card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(150), padding=dp(10), spacing=dp(4))
            with card.canvas.before:
                Color(0.02,0.10,0.20,0.92)
                bg = RoundedRectangle(radius=[dp(14)])
            card.bind(pos=lambda o,v,bg=bg:setattr(bg,"pos",v), size=lambda o,v,bg=bg:setattr(bg,"size",v))
            card.add_widget(self.label(str(offer.get("title") or "گزینه پرداخت"), "13sp", WHITE, True, "center"))
            card.add_widget(self.label("مبلغ: "+str(amount)+" تومان", "11sp", SECONDARY, True, "center"))
            desc = str(offer.get("description") or "").strip()
            if desc:
                card.add_widget(self.label(desc, "8sp", SECONDARY, False, "center"))
            b = self.btn("ادامه پرداخت آنلاین", lambda *_a, o=dict(offer), sid=student_id, u=username: self._submit_payment_offer(o,sid,u), SUCCESS, dp(42))
            card.add_widget(b)
            self.body.add_widget(card)
        self.body.add_widget(self.btn("بازگشت به پنل", lambda *_: self._back_to_submenus(), PRIMARY, dp(42)))

    def _submit_payment_offer(self, offer, student_id, username):
        if not student_id:
            self.message("پرداخت آنلاین", "برای انجام پرداخت، ابتدا دانش‌آموز مرتبط با حساب مشخص شود.")
            return
        amount = offer.get("amount") or 0
        payload = {
            "offer_id": offer.get("id"),
            "student_id": student_id,
            "payer_username": username or None,
            "payer_role": self.role(),
            "amount": amount,
            "status": "pending",
            "description": offer.get("description") or offer.get("title") or "پرداخت آنلاین",
        }
        try:
            # The inserted id is not required by the UI. Avoid requesting a
            # representation because legacy RLS policies may allow INSERT but
            # not SELECT on payment_attempts.
            self.app_state.api.table_insert("payment_attempts", payload, return_representation=False)
            payment_url = str(offer.get("payment_url") or PAYMENT_GATEWAY_URL or "").strip()
            if payment_url and payment_url.startswith(("https://", "http://")):
                import webbrowser
                webbrowser.open(payment_url)
                self.message("پرداخت آنلاین", "درخواست پرداخت ثبت شد و درگاه پرداخت باز شد.")
            else:
                self.message("پرداخت آنلاین", "درخواست پرداخت ثبت شد؛ درگاه آنلاین هنوز برای این گزینه تنظیم نشده است.")
            print("PAYMENT ATTEMPT CREATED")
        except Exception as exc:
            self.message("پرداخت آنلاین", "ثبت درخواست پرداخت انجام نشد: "+str(exc))

    def open_table(self,table,refresh_subbar=True):
        # Student and parent accounts are consumer/read-only roles. Their
        # dashboard exposes only assignments/messages (student) and
        # messages/online-payment (parent). Block legacy/deep links to staff
        # workflows so they can never reach a staff CRUD screen.
        role = self.role()
        logical_table = str(table or "").strip()
        # Student/parent messaging has a dedicated composer with a recipient
        # dropdown; do not downgrade it to a generic CRUD table.
        if table in ("online", "online_classes", "virtual", "online_class_sessions"):
            try:
                from kivy.app import App
                app = App.get_running_app()
                screen = app.ensure_online_workflow() if app is not None else None
                if screen is None:
                    raise RuntimeError("محیط کلاس آنلاین آماده نشد.")
                # Preserve the active school panel role inside the dedicated workflow.
                # The workflow must not fall back to the login/profile role when a deputy panel is open.
                if hasattr(screen, "panel_role"):
                    screen.panel_role = getattr(self, "panel_role", "")
                screen.return_to = "panel"
                if self.manager:
                    self.manager.current = screen.name
                return
            except Exception as exc:
                print("ONLINE CLASS OPEN ERROR:", repr(exc))
                self.status.text = fa_display("محیط کلاس آنلاین باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                return

        if table in ("teacher_exams", "exams", "quiz_questions"):
            try:
                from kivy.app import App
                app = App.get_running_app()
                screen = app.ensure_exam_authoring() if app is not None else None
                if screen is None:
                    raise RuntimeError("مرکز آزمون آنلاین آماده نشد.")
                # Preserve the active school panel role for the dedicated exam workflow.
                if hasattr(screen, "panel_role"):
                    screen.panel_role = getattr(self, "panel_role", "")
                screen.return_to = "panel"
                if self.manager:
                    self.manager.current = screen.name
                return
            except Exception as exc:
                print("ONLINE EXAM OPEN ERROR:", repr(exc))
                self.status.text = fa_display("مرکز آزمون آنلاین باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                return

        if table in ("meeting_requests", "parent_meeting_requests", "teacher_meetings", "meetings"):
            try:
                from kivy.app import App
                app = App.get_running_app()
                screen = app.ensure_meeting_workflow() if app is not None else None
                if screen is None:
                    raise RuntimeError("محیط ملاقات‌ها آماده نشد.")
                screen.return_to = "panel"
                if self.manager:
                    self.manager.current = screen.name
                return
            except Exception as exc:
                print("MEETING WORKFLOW OPEN ERROR:", repr(exc))
                self.status.text = fa_display("محیط ملاقات‌ها باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)

        if table == "messages":
            try:
                from kivy.app import App
                app = App.get_running_app()
                # Messaging is a school-wide feature. Every authenticated role
                # opens the same real composer/inbox workflow.
                if app is not None:
                    screen = app.ensure_message_workflow()
                    if screen is None:
                        raise RuntimeError("محیط ارسال پیام آماده نشد.")
                    screen.return_to = "panel"
                    if self.manager:
                        self.manager.current = screen.name
                    return
            except Exception as exc:
                print("MESSAGE WORKFLOW ERROR:", repr(exc))
                self.status.text = fa_display("محیط ارسال پیام باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                return
        # Special school workflows use student-bound operational screens instead
        # of the generic CRUD renderer.
        if table in ("attendance", "discipline_records", "online_attendance"):
            try:
                from kivy.app import App
                app = App.get_running_app()
                mode = None
                if table == "attendance" and self.role() == "teacher":
                    mode = "attendance"
                elif table == "discipline_records":
                    mode = "discipline"
                elif table == "online_attendance":
                    mode = "online_attendance"
                if mode and app is not None:
                    screen = app.ensure_school_action(mode)
                    if screen is None:
                        raise RuntimeError("محیط عملیاتی این بخش آماده نشد.")
                    screen.return_to = "panel"
                    if self.manager:
                        self.manager.current = screen.name
                    return
            except Exception as exc:
                print("SPECIAL SCHOOL ACTION ERROR:", repr(exc))
                self.status.text = fa_display("محیط عملیاتی باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                return

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
                self.status.text = fa_display("محیط کلاس هوشمند باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                return

    def _open_parent_student_records(self, table):
        """Show only records belonging to children explicitly linked to this parent."""
        try:
            username = self._current_username()
            links = self.app_state.api.table_select(
                "parent_children", {"parent_username": "eq." + username, "limit": "100"}
            ) or []
            child_ids = [x.get("student_id") for x in links if x.get("student_id") is not None]
            rows = []
            for sid in child_ids:
                params = {"student_id": "eq." + str(sid), "limit": "500", "order": "id.desc"}
                if table == "discipline_records":
                    params["status"] = "eq.approved"
                try:
                    rows.extend(self.app_state.api.table_select(table, params) or [])
                except Exception as child_exc:
                    print("PARENT RECORD LOAD ERROR:", table, sid, repr(child_exc))
            self.table = table
            self.body.clear_widgets()
            self.title.text = fa_display(FRIENDLY.get(table, table))
            self.body.add_widget(self.btn("زیرپنل‌ها", lambda *_: self._back_to_submenus(), PRIMARY, dp(40), dp(82)))
            self.body.add_widget(self.label(FRIENDLY.get(table, table), "16sp", PRIMARY, True, "center"))
            if not rows:
                empty = self.label("برای فرزند متصل به این حساب رکوردی ثبت نشده است.", "10sp", SECONDARY, False, True)
                empty.size_hint_y = None; empty.height = dp(58)
                self.body.add_widget(empty)
            else:
                keys = [k for k in (_module_fields(table) or []) if k not in HIDDEN]
                if not keys:
                    keys = [k for k in rows[0].keys() if k not in HIDDEN]
                header = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(3))
                for k in keys[:6]:
                    header.add_widget(self.label(COLUMNS.get(k, k), "9sp", WHITE, True, "center"))
                self.area = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(3))
                self.area.bind(minimum_height=self.area.setter("height"))
                for row in rows:
                    self.area.add_widget(self.row(row, len(self.area.children), keys[:6], dp(1380)))
                self.body.add_widget(self.area)
            self.status.text = fa_display("اطلاعات فقط از فرزندان متصل به حساب ولی نمایش داده می‌شود.")
            self.status.color = SUCCESS
        except Exception as exc:
            self.status.text = fa_display("نمایش اطلاعات فرزند انجام نشد: " + str(exc))
            self.status.color = ERROR

        if self.role() == "parent" and table in ("attendance", "discipline_records"):
            self._open_parent_student_records(table)
            return

        if table in ("attendance", "teacher_attendance"):
            try:
                from kivy.app import App
                app = App.get_running_app()
                screen = app.ensure_attendance_discipline("attendance") if app is not None else None
                if screen is None:
                    raise RuntimeError("محیط حضور و غیاب آماده نشد.")
                if self.manager:
                    self.manager.current = screen.name
                return
            except Exception as exc:
                self.status.text = fa_display("محیط حضور و غیاب باز نشد: " + str(exc))
                self.status.color = ERROR
                return

        if table == "discipline_records":
            try:
                from kivy.app import App
                app = App.get_running_app()
                screen = app.ensure_attendance_discipline("discipline") if app is not None else None
                if screen is None:
                    raise RuntimeError("محیط انضباط آماده نشد.")
                if self.manager:
                    self.manager.current = screen.name
                return
            except Exception as exc:
                self.status.text = fa_display("محیط انضباط باز نشد: " + str(exc))
                self.status.color = ERROR
                return

        # Student/parent online payment is a real operational workflow.
        # The offer is configured by school management; the consumer can submit
        # a payment request and, when a payment URL is configured, continue to it.
        if table == "parent_children" and self.role() == "parent":
            self._open_parent_children()
            return

        if table == "assignment_submissions" and self.role() == "student":
            self._open_student_assignments()
            return

        if table in ("payment", "payment_offers") and self.role() in {"student", "parent"}:
            self._open_consumer_payment()
            return

        # Mother/ZIP module buttons carry logical ids; all operational paths use the canonical Supabase table.
        table = self._resolve_backend_route(table)
        self.table=table
        # A selection belongs only to the currently open table. Never carry a row
        # from another module into Edit/Delete.
        self.selected_row=None
        if refresh_subbar:
            self.render(); return
        self.body.clear_widgets(); self.title.text=fa_display(FRIENDLY.get(table,table))
        hero=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(58),padding=dp(6),spacing=dp(4))
        line=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5))
        line.add_widget(self.btn("زیرپنل‌ها",lambda *_:self._back_to_submenus(),PRIMARY,dp(40),dp(82)))
        line.add_widget(self.label(FRIENDLY.get(table,table),"16sp",PRIMARY,True,"center"))
        hero.add_widget(line); self.body.add_widget(hero)
        can_write = self.can_write(table)
        consumer = self.role() in {"student", "parent"}
        export_roles = {"manager", "educational", "executive", "cultural", "advisor"}
        can_export = self.role() in export_roles
        if can_write:
            def _guard_write(action):
                def _run(*_args):
                    if not self.can_write(table):
                        self.message("دسترسی ثبت اطلاعات", "این نقش اجازه ثبت، ویرایش یا حذف این جدول را ندارد.")
                        return
                    action()
                return _run

            if consumer:
                # دانش‌آموز و ولی فقط عملیات واقعی خودشان را می‌بینند:
                # ثبت، ویرایش و حذف. ابزارهای خروجی برای این دو نقش حذف شده‌اند.
                bar=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(5))
                bar.add_widget(self.btn("ثبت",_guard_write(lambda: self.editor(table,None)),SUCCESS,dp(38)))
                bar.add_widget(self.btn("ویرایش",_guard_write(self._edit_selected_row),PRIMARY,dp(38)))
                bar.add_widget(self.btn("حذف",_guard_write(self._delete_selected_row),(0.72,.16,.18,1),dp(38)))
                self.body.add_widget(bar)
                self.status.text = fa_display("عملیات ثبت، ویرایش و حذف برای این بخش فعال است")
            else:
                bar=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(82),spacing=dp(4))
                row1=BoxLayout(size_hint_y=None,height=dp(39),spacing=dp(4))
                row2=BoxLayout(size_hint_y=None,height=dp(39),spacing=dp(4))
                row1.add_widget(self.btn("ثبت جدید",_guard_write(lambda: self.editor(table,None)),SUCCESS,dp(38)))
                row1.add_widget(self.btn("ویرایش",_guard_write(self._edit_selected_row),PRIMARY,dp(38)))
                row1.add_widget(self.btn("حذف",_guard_write(self._delete_selected_row),(0.72,.16,.18,1),dp(38)))
                if can_export:
                    row1.add_widget(self.btn("خروجی اکسل",lambda *_:self.export_excel(),(0.08,.42,.62,1),dp(38)))
                    row2.add_widget(self.btn("قالب اکسل",lambda *_:self.export_excel_template(),(0.18,.48,.58,1),dp(38)))
                    row2.add_widget(self.btn("ورودی اکسل",_guard_write(self.import_excel),(0.42,.30,.62,1),dp(38)))
                    row2.add_widget(self.btn("خروجی پی دی اف",lambda *_:self.export_pdf(),(0.50,.28,.58,1),dp(38)))
                bar.add_widget(row1); bar.add_widget(row2)
                self.body.add_widget(bar)
                self.status.text = fa_display("عملیات واقعی فعال است و به پایگاه داده مدرسه متصل است")
        else:
            if not consumer:
                bar=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(5))
                if can_export:
                    bar.add_widget(self.btn("خروجی اکسل",lambda *_:self.export_excel(),(0.08,.42,.62,1),dp(38)))
                    bar.add_widget(self.btn("خروجی پی دی اف",lambda *_:self.export_pdf(),(0.50,.28,.58,1),dp(38)))
                self.body.add_widget(bar)
            self.status.text = fa_display("حالت مشاهده‌ای؛ این بخش فقط برای مشاهده اطلاعات است")
        self.area=BoxLayout(orientation="vertical"); self.body.add_widget(self.area); self.load_table()

    def _excel_path(self):
        # Android 10+ uses scoped storage.  Direct writes to the public Download
        # directory can fail even when the directory exists, so verify a real
        # write first and fall back to the app's persistent files directory.
        table=str(self.table or "table")
        filename="frahoosh_"+table+".xlsx"
        try:
            download=Path("/storage/emulated/0/Download")
            download.mkdir(parents=True,exist_ok=True)
            probe=download/(".frahoosh_write_test_"+table)
            probe.write_bytes(b"1")
            probe.unlink(missing_ok=True)
            return download/filename
        except Exception as exc:
            print("PUBLIC DOWNLOAD NOT WRITABLE:", repr(exc))
            try:
                app_dir=Path(getattr(self.app_state, "user_data_dir", "") or "")
                if not str(app_dir):
                    from kivy.app import App
                    app=App.get_running_app()
                    app_dir=Path(getattr(app, "user_data_dir", ".") or ".")
                app_dir.mkdir(parents=True,exist_ok=True)
                return app_dir/filename
            except Exception:
                return Path(".")/filename

    def export_excel(self):
        table=str(self.table or "").strip()
        if not table:
            return
        self.status.text = fa_display("در حال ساخت فایل اکسل…")
        def work():
            try:
                from openpyxl import Workbook
                api=self.app_state.api
                rows=api.table_select(table,{"limit":"1000"}) or []
                rows=[dict(x) for x in rows if isinstance(x,dict)]
                fields=[f for f in _module_fields(table) if f not in HIDDEN]
                if not fields and rows:
                    fields=[k for k in rows[0] if k not in HIDDEN]
                wb=Workbook(); ws=wb.active; ws.title="فراهوش"
                ws.append([COLUMNS.get(f,f) for f in fields])
                for row in rows:
                    ws.append([row.get(f,"") for f in fields])
                path=self._excel_path(); wb.save(str(path))
                msg=f"خروجی اکسل ذخیره شد: {path}"
                Clock.schedule_once(lambda *_: self._excel_done(msg),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.write_error("خروجی اکسل انجام نشد: "+str(exc)),0)
        Thread(target=work,daemon=True).start()

    def export_excel_template(self):
        """Create a ready-to-fill اکسل template using the exact module field contract."""
        table=str(self.table or "").strip()
        if not table:
            return
        self.status.text = fa_display("در حال ساخت قالب اکسل…")
        def work():
            try:
                from openpyxl import Workbook
                fields=[f for f in (_module_fields(table) or []) if f not in HIDDEN]
                if not fields:
                    raise RuntimeError("برای این ماژول قرارداد فیلد قابل ورود تعریف نشده است.")
                wb=Workbook(); ws=wb.active; ws.title="فراهوش"
                ws.append([COLUMNS.get(f,f) for f in fields])
                ws.append(["" for _ in fields])
                path=self._excel_path(); template=path.with_name(path.stem+"_template.xlsx")
                wb.save(str(template))
                Clock.schedule_once(lambda *_: self._excel_done("قالب اکسل آماده شد: "+str(template)),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.write_error("ساخت قالب اکسل انجام نشد: "+str(exc)),0)
        Thread(target=work,daemon=True).start()

    def export_pdf(self):
        table=str(self.table or "").strip()
        if not table:
            return
        self.status.text = fa_display("در حال ساخت گزارش پی دی اف…")
        def work():
            try:
                from mobile.services.document_service import export_table_pdf
                rows=self.app_state.api.table_select(table,{"limit":"2000"}) or []
                rows=[dict(x) for x in rows if isinstance(x,dict)]
                fields=[f for f in (_module_fields(table) or []) if f not in HIDDEN]
                if not fields and rows:
                    fields=[k for k in rows[0] if k not in HIDDEN]
                # Save پی دی اف reports beside اکسل exports in Download.
                output=self._excel_path().parent
                output.mkdir(parents=True,exist_ok=True)
                path=output/("frahoosh_"+table+"_report.pdf")
                export_table_pdf(table,rows,fields,COLUMNS,str(path),title=FRIENDLY.get(table,table))
                Clock.schedule_once(lambda *_: self._excel_done("گزارش پی دی اف ذخیره شد: "+str(path)),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.write_error("گزارش پی دی اف انجام نشد: "+str(exc)),0)
        Thread(target=work,daemon=True).start()

    def _pick_excel_android(self):
        """Use Android's system document picker instead of guessing a Download path."""
        try:
            from android import activity
            from jnius import autoclass, cast
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Activity = autoclass("android.app.Activity")
            current = cast("android.app.Activity", PythonActivity.mActivity)
            request_code = 4817

            def on_result(request_code_value, result_code, intent):
                if request_code_value != request_code:
                    return
                try:
                    activity.unbind(on_activity_result=on_result)
                except Exception:
                    pass
                if result_code != Activity.RESULT_OK or intent is None:
                    Clock.schedule_once(lambda *_: self.write_error("انتخاب فایل اکسل لغو شد."), 0)
                    return
                try:
                    uri = intent.getData()
                    if uri is None:
                        raise RuntimeError("فایل انتخاب‌شده قابل دسترسی نیست.")
                    resolver = current.getContentResolver()
                    stream = resolver.openInputStream(uri)
                    if stream is None:
                        raise RuntimeError("امکان خواندن فایل انتخاب‌شده وجود ندارد.")
                    from java.io import ByteArrayOutputStream
                    out = ByteArrayOutputStream()
                    while True:
                        value = stream.read()
                        if value == -1:
                            break
                        out.write(value)
                    stream.close()
                    data = bytes(out.toByteArray())
                    target = Path(getattr(self.app_state, "user_data_dir", "") or ".") / "frahoosh_selected_import.xlsx"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    Clock.schedule_once(lambda *_: self._import_excel_path(target), 0)
                except Exception as exc:
                    print("ANDROID EXCEL PICKER ERROR:", repr(exc))
                    Clock.schedule_once(
                        lambda *_: self.write_error("خواندن فایل اکسل انجام نشد: " + str(exc)), 0
                    )

            activity.bind(on_activity_result=on_result)
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            intent.putExtra(
                Intent.EXTRA_MIME_TYPES,
                [
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel",
                    "application/octet-stream",
                ],
            )
            current.startActivityForResult(intent, request_code)
            return True
        except Exception as exc:
            print("ANDROID EXCEL PICKER START ERROR:", repr(exc))
            return False

    def _import_excel_path(self, path):
        table=str(self.table or "").strip()
        if not table:
            return
        self.status.text = fa_display("در حال خواندن فایل اکسل و ثبت گروهی…")
        def work():
            try:
                from openpyxl import load_workbook
                wb=load_workbook(str(path),read_only=True,data_only=True)
                ws=wb.active
                values=list(ws.iter_rows(values_only=True))
                if not values:
                    raise RuntimeError("فایل اکسل خالی است.")
                headers=[str(x or "").strip() for x in values[0]]
                reverse={str(v):k for k,v in COLUMNS.items()}
                fields=[reverse.get(h,h) for h in headers]
                allowed=set(_module_fields(table) or [])
                fields=[f if f in allowed else None for f in fields]
                inserted=0
                for row in values[1:]:
                    payload={}
                    for i,value in enumerate(row):
                        if i>=len(fields) or not fields[i] or value in (None,""):
                            continue
                        payload[fields[i]]=self._payload_value(fields[i],value)
                    if payload:
                        self.app_state.api.table_insert(table,payload,return_representation=False)
                        inserted+=1
                wb.close()
                try:
                    Path(path).unlink(missing_ok=True)
                except Exception:
                    pass
                Clock.schedule_once(lambda *_: self._excel_done(f"{inserted} رکورد از اکسل وارد شد."),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.write_error("ورودی اکسل انجام نشد: "+str(exc)),0)

        Thread(target=work,daemon=True).start()

    def import_excel(self):
        table=str(self.table or "").strip()
        if not table:
            return
        # On Android, let the system file picker grant access to the selected
        # document. This works with Android 10+ scoped storage and does not
        # depend on direct /storage/emulated/0/Download access.
        try:
            from kivy.utils import platform
            if platform == "android" and self._pick_excel_android():
                self.status.text = fa_display("فایل اکسل را انتخاب کنید…")
                return
        except Exception as exc:
            print("EXCEL PICKER FALLBACK:", repr(exc))

        path=self._excel_path()
        if not path.is_file():
            template=path.with_name(path.stem+"_template.xlsx")
            if template.is_file():
                path=template
            else:
                self.message(
                    "ورودی اکسل",
                    f"برای ثبت گروهی، فایل اکسل را انتخاب کنید.\n"
                    f"در نسخه دسکتاپ مسیر پیش‌فرض: {path.name}"
                )
                return
        self._import_excel_path(path)

    def _excel_done(self,message):
        self.status.text = fa_display(message)
        self.status.color=SUCCESS
        self.load_table()

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
            self.status.text = fa_display("شناسه زیرپنل معتبر نیست.")
            self.status.color = (.8, .15, .15, 1)
            return
        self.status.text = fa_display("در حال دریافت اطلاعات واقعی… (حداکثر ۲۵ رکورد)")
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
                self.status.text = fa_display("خطا در نمایش اطلاعات: " + str(exc))
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
        self.selected_row=None
        if error:
            self.status.text = fa_display("خطا در دریافت اطلاعات: "+str(error))
            self.status.color=(.8,.15,.15,1)
            self.render_rows([])
            return
        self.status.text = fa_display(f"{len(rows)} رکورد واقعی • {FRIENDLY.get(self.table,self.table)}")
        self.status.color=SUCCESS
        self.render_rows(rows)

    def render_rows(self,rows):
        """Render the real canonical table even when it currently has zero rows.

        The ZIP/shared catalog is the schema authority. Empty data must not turn
        a real module into a decorative empty card: its actual columns remain
        visible so the user can immediately understand what belongs in each
        field and can use ثبت جدید when permitted.
        """
        try:
            self.area.clear_widgets()
            rows = [dict(r) for r in (rows or []) if isinstance(r, dict)]

            preferred = list(_module_fields(self.table) or [])
            keys = [k for k in preferred if k not in HIDDEN]
            if not keys:
                for r in rows:
                    for k in r:
                        if k not in HIDDEN and k not in keys:
                            keys.append(k)

            if not keys:
                empty = Surface(height=dp(150))
                empty.add_widget(self.label(
                    "ساختار جدول این زیرپنل هنوز در قرارداد مشترک تعریف نشده است.",
                    "13sp", PRIMARY, True, "center"
                ))
                self.area.add_widget(empty)
                return

            col_w = dp(230)
            totalw = max(dp(720), col_w * max(1, len(keys)))

            scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
            content = BoxLayout(
                orientation="vertical",
                size_hint=(None, None),
                width=totalw,
                spacing=dp(3),
                padding=dp(2),
            )
            content.bind(minimum_height=content.setter("height"))

            header = BoxLayout(
                size_hint=(None, None),
                width=totalw,
                height=dp(78),
                spacing=dp(3),
                padding=[dp(4), dp(4)],
            )
            for k in keys:
                cell = self.label(
                    COLUMNS.get(k, k),
                    "18sp",
                    WHITE,
                    True,
                    "center",
                )
                cell.size_hint_x = None
                cell.width = col_w
                header.add_widget(cell)
            self._header(header)
            content.add_widget(header)

            if rows:
                for i, r in enumerate(rows, 1):
                    try:
                        content.add_widget(self.row(r, i, keys, totalw))
                    except Exception as row_exc:
                        print("MODULE ROW RENDER ERROR:", repr(row_exc))
            else:
                empty_row = BoxLayout(
                    size_hint=(None, None),
                    width=totalw,
                    height=dp(96),
                    padding=[dp(8), dp(8)],
                )
                empty_row.add_widget(self.label(
                    "هنوز رکوردی در این جدول ثبت نشده است.",
                    "14sp",
                    PRIMARY,
                    True,
                    "center",
                ))
                content.add_widget(empty_row)

            scroll.add_widget(content)
            self.area.add_widget(scroll)
        except Exception as exc:
            print("MODULE TABLE RENDER ERROR:", repr(exc))
            try:
                self.status.text = fa_display("خطا در نمایش جدول: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                self.area.clear_widgets()
                fallback = Surface(height=dp(150))
                fallback.add_widget(self.label(
                    "نمایش جدول با خطا روبه‌رو شد",
                    "14sp",
                    (.8, .15, .15, 1),
                    True,
                    "center",
                ))
                fallback.add_widget(self.label(
                    "داده‌ها حفظ شده‌اند؛ دوباره وارد زیرپنل شوید.",
                    "9sp",
                    SECONDARY,
                    False,
                    "center",
                ))
                self.area.add_widget(fallback)
            except Exception:
                pass

    def _header(self, header):
        """Apply a lightweight visual header background without custom widgets."""
        with header.canvas.before:
            Color(0.04, 0.24, 0.38, 1)
            bg = RoundedRectangle(radius=[dp(8)])
        header.bind(
            pos=lambda o, v: setattr(bg, "pos", v),
            size=lambda o, v: setattr(bg, "size", v),
        )
        bg.pos = header.pos
        bg.size = header.size

    def row(self,r,index,keys,totalw):
        b=SelectableRow(owner=self,record=r,size_hint=(None,None),width=totalw,height=dp(100),spacing=dp(3),padding=[dp(5),dp(5)])
        for k in keys:
            raw = r.get(k, "")
            s = fa_display(str(raw).strip())
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
        # The shared ZIP/Web contract is authoritative for forms too. This prevents
        # a module from silently falling back to decorative fields.
        canonical = list(_module_fields(table) or [])
        fields=[k for k in (canonical or FORMS.get(table) or self._infer(row)) if k not in HIDDEN]
        # Never expose internal metadata or an unknown placeholder as a form field.
        fields=[k for k in fields if k and k not in {"password","school_id"}]
        root=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(6)); sc=ScrollView(do_scroll_x=False); form=GridLayout(cols=1,spacing=dp(5),size_hint_y=None); form.bind(minimum_height=form.setter('height')); inputs={}
        spinner_values = {
            "active": ("فعال", "غیرفعال"),
            "published": ("منتشرشده", "پیش‌نویس"),
            "secure_mode": ("فعال", "غیرفعال"),
            "share_enabled": ("فعال", "غیرفعال"),
            "manager_released": ("تأیید شده", "در انتظار تأیید"),
            "status": ("فعال", "در انتظار", "تأیید شد", "رد شد", "بسته", "لغو شد"),
            "priority": ("کم", "عادی", "زیاد", "فوری"),
            "transaction_type": ("بدهکار", "بستانکار"),
            "payment_status": ("پرداخت نشده", "در انتظار پرداخت", "پرداخت شده", "لغو شده"),
            "grade_type": ("مستمر", "کلاسی", "امتحانی", "فعالیت", "نهایی"),
            "term": ("نوبت اول", "نوبت دوم", "مستمر"),
            "employment_status": ("فعال", "مرخصی", "پایان همکاری"),
        }
        multiline_fields = {
            "description", "content", "body", "text", "note", "report",
            "reason", "recommendation", "followup_items", "decision",
        }
        for f in fields:
            label_text = COLUMNS.get(f, f)
            form.add_widget(self.label(label_text, "9sp", PRIMARY, True))
            existing = "" if row is None else str(row.get(f, ""))
            if existing and all(ch in "□�▯" for ch in existing.strip()):
                existing = ""
            if f in spinner_values:
                values = tuple(spinner_values[f])
                selected = existing if existing and existing in spinner_values[f] else values[0]
                ti = PersianSpinner(
                    text=selected,
                    values=values,
                    font_name=font_name(),
                    font_size="11sp",
                    size_hint_y=None,
                    height=dp(44),
                )
            else:
                ti = PersianTextInput(
                    text=existing,
                    hint_text=fa_display(label_text),
                    font_name=font_name(),
                    font_size="12sp",
                    halign="right",
                    multiline=f in multiline_fields,
                    size_hint_y=None,
                    height=dp(72 if f in multiline_fields else 44),
                    padding=[dp(8), dp(6)],
                )
            inputs[f] = ti
            form.add_widget(ti)
        sc.add_widget(form); root.add_widget(sc); actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5)); p=Popup(title=fa_display(('ویرایش' if row else 'ثبت جدید')+' • '+FRIENDLY.get(table,table)),content=root,size_hint=(.94,.88),auto_dismiss=False); actions.add_widget(self.btn('انصراف',lambda *_:p.dismiss(),SECONDARY,dp(40))); actions.add_widget(self.btn('ذخیره',lambda *_:self.save(table,row,inputs,p),SUCCESS,dp(40))); root.add_widget(actions); p.open()

    def _infer(self,row): return [k for k in (row or {}).keys() if k not in HIDDEN] or ['title','description','status']

    @staticmethod
    def _payload_value(field, raw):
        value = str(raw or "").strip()
        if value == "":
            return None

        # Supabase/PostgREST accepts numeric and boolean values more reliably
        # when Android sends the correct JSON scalar instead of a text-only
        # representation.
        numeric_fields = {
            "amount","balance","debit","credit","coefficient","score","max_score",
            "duration","max_attempts","passing_score","deduction","deduct_score",
            "class_count","capacity","quantity","fee","weight","points","negative_score",
            "seat_number","week_index","teaching_hours","fixed_amount",
        }
        boolean_fields = {
            "active","published","secure_mode","share_enabled","standard_mode",
            "record","smart_board","quiz","camera","microphone","manager_released",
            "gateway_enabled","auto_grade","required","archived",
        }
        json_fields = {
            "preferences","permissions","settings","program","options","options_json",
            "snapshot_data","selections","team_members",
        }

        if field in boolean_fields:
            low = value.lower()
            if low in {"true","1","yes","بله","فعال","بله است"}:
                return True
            if low in {"false","0","no","خیر","غیرفعال","خیر است"}:
                return False

        if field in numeric_fields:
            try:
                return float(value) if any(ch in value for ch in ".") else int(value)
            except ValueError:
                return value

        if field in json_fields:
            import json
            try:
                return json.loads(value)
            except Exception:
                # A Persian text entry is still valid JSON content.
                return value

        return value

    def save(self,table,row,inputs,p):
        payload={}
        for k, widget in inputs.items():
            raw = (widget.get_logical_text() if hasattr(widget, "get_logical_text") else str(widget.text or "")).strip()
            if raw:
                payload[k] = self._payload_value(k, raw)
        if not payload:
            self.message('ثبت اطلاعات','حداقل یک فیلد را وارد کنید.'); return
        p.dismiss(); self.status.text = fa_display('در حال ذخیره اطلاعات واقعی…')
        def work():
            try:
                api = self.app_state.api
                if table == "grades":
                    # A teacher grade is one business record, but it feeds three
                    # canonical views: grades, student_grades and grade_items.
                    # Keep the source id so later edits do not create duplicates.
                    if row is None:
                        created = api.table_insert("grades", payload) or []
                        if not isinstance(created, list) or not created or not created[0].get("id"):
                            raise RuntimeError("شناسه نمره پس از ثبت دریافت نشد.")
                        source_id = created[0]["id"]
                        api.table_update(
                            "grades", {"id":"eq."+str(source_id)},
                            {"source_grade_id": source_id},
                        )
                        source_row = dict(payload)
                        source_row["source_grade_id"] = source_id
                        student_payload = {
                            "source_grade_id": source_id,
                            "student_id": payload.get("student_id"),
                            "teacher_id": payload.get("teacher_id"),
                            "subject": payload.get("subject"),
                            "class_name": payload.get("class_name"),
                            "assessment_type": payload.get("grade_type"),
                            "assessment_title": payload.get("title") or payload.get("exam_name"),
                            "score": payload.get("score"),
                            "coefficient": 1,
                            "grade_date": payload.get("grade_date"),
                            "description": payload.get("description"),
                            "term": payload.get("term"),
                            "manager_released": False,
                        }
                        api.table_insert("student_grades", student_payload)
                        api.table_insert("grade_items", {
                            "source_grade_id": source_id,
                            "student_id": payload.get("student_id"),
                            "teacher_id": payload.get("teacher_id"),
                            "subject": payload.get("subject"),
                            "grade_type": payload.get("grade_type"),
                            "term": payload.get("term"),
                            "score": payload.get("score"),
                            "grade_date": payload.get("grade_date"),
                            "description": payload.get("description"),
                        })
                        msg='نمره ثبت شد و به کارنامه/ارزیابی دانش‌آموز متصل شد.'
                    else:
                        rid=row.get("id")
                        if rid is None:
                            raise RuntimeError('شناسه رکورد برای ویرایش پیدا نشد.')
                        api.table_update("grades", {"id":"eq."+str(rid)}, payload)
                        source_id = row.get("source_grade_id") or rid
                        # Update the linked student record; if an older record
                        # predates the link, create the mirror exactly once.
                        mirrors = api.table_select(
                            "student_grades", {"source_grade_id":"eq."+str(source_id), "limit":"1"}
                        ) or []
                        student_payload = {
                            "source_grade_id": source_id,
                            "student_id": payload.get("student_id", row.get("student_id")),
                            "teacher_id": payload.get("teacher_id", row.get("teacher_id")),
                            "subject": payload.get("subject", row.get("subject")),
                            "class_name": payload.get("class_name", row.get("class_name")),
                            "assessment_type": payload.get("grade_type", row.get("grade_type")),
                            "assessment_title": payload.get("title", row.get("title")) or payload.get("exam_name", row.get("exam_name")),
                            "score": payload.get("score", row.get("score")),
                            "coefficient": 1,
                            "grade_date": payload.get("grade_date", row.get("grade_date")),
                            "description": payload.get("description", row.get("description")),
                            "term": payload.get("term", row.get("term")),
                        }
                        if mirrors and mirrors[0].get("id"):
                            api.table_update("student_grades", {"id":"eq."+str(mirrors[0]["id"])}, student_payload)
                        else:
                            api.table_insert("student_grades", {**student_payload, "manager_released": False})
                        items = api.table_select(
                            "grade_items", {"source_grade_id":"eq."+str(source_id), "limit":"1"}
                        ) or []
                        item_payload = {
                            "source_grade_id": source_id,
                            "student_id": payload.get("student_id", row.get("student_id")),
                            "teacher_id": payload.get("teacher_id", row.get("teacher_id")),
                            "subject": payload.get("subject", row.get("subject")),
                            "grade_type": payload.get("grade_type", row.get("grade_type")),
                            "term": payload.get("term", row.get("term")),
                            "score": payload.get("score", row.get("score")),
                            "grade_date": payload.get("grade_date", row.get("grade_date")),
                            "description": payload.get("description", row.get("description")),
                        }
                        if items and items[0].get("id"):
                            api.table_update("grade_items", {"id":"eq."+str(items[0]["id"])}, item_payload)
                        else:
                            api.table_insert("grade_items", item_payload)
                        msg='نمره و نسخه‌های مرتبط با موفقیت ویرایش شد.'
                else:
                    role = self.role()
                    profile = getattr(self.app_state, "profile", {}) or {}
                    if role in ("teacher", "دبیر", "معلم") and table in {"grades","student_grades","attendance","assignments","discipline_records","teacher_exams","lesson_plans","teacher_activities"}:
                        tid = profile.get("linked_teacher_id") or profile.get("teacher_id")
                        if tid and not payload.get("teacher_id"):
                            payload["teacher_id"] = tid
                    if role in ("student","دانش‌آموز") and table in {"student_grades","attendance","assignments","assignment_submissions","discipline_records"}:
                        sid = profile.get("linked_student_id") or profile.get("student_id")
                        if sid and not payload.get("student_id"):
                            payload["student_id"] = sid
                    if row is None:
                        api.table_insert(table,payload); msg='رکورد جدید با موفقیت ثبت شد.'
                    else:
                        rid=row.get('id')
                        if rid is None: raise RuntimeError('شناسه رکورد برای ویرایش پیدا نشد.')
                        api.table_update(table,{'id':'eq.'+str(rid)},payload); msg='رکورد با موفقیت ویرایش شد.'
                Clock.schedule_once(lambda *_:self.after_write(msg),0)
            except Exception as exc: Clock.schedule_once(lambda *_:self.write_error(str(exc)),0)
        Thread(target=work,daemon=True).start()

    def after_write(self,msg): self.selected_row=None; self.status.text = fa_display(msg); self.status.color=SUCCESS; self.load_table()
    def write_error(self,msg): self.status.text = fa_display('ذخیره انجام نشد: '+msg); self.status.color=(.8,.15,.15,1)

    def confirm_delete(self,table,row):
        rid=row.get('id');
        if rid is None: self.message('حذف رکورد','شناسه رکورد موجود نیست.'); return
        root=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8)); root.add_widget(self.label('آیا از حذف این رکورد مطمئن هستید؟','14sp',PRIMARY,True,'center')); root.add_widget(self.label('این عملیات روی اطلاعات واقعی سامانه انجام می‌شود.','9sp',SECONDARY,False,'center')); actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5)); p=Popup(title=fa_display('تأیید حذف'),content=root,size_hint=(.88,.36),auto_dismiss=False); actions.add_widget(self.btn('انصراف',lambda *_:p.dismiss(),SECONDARY,dp(40))); actions.add_widget(self.btn('حذف قطعی',lambda *_:self.delete(table,rid,p),(0.72,.16,.18,1),dp(40))); root.add_widget(actions); p.open()

    def delete(self,table,rid,p):
        p.dismiss(); self.status.text = fa_display('در حال حذف اطلاعات واقعی…')
        def work():
            try: self.app_state.api.table_delete(table,{'id':'eq.'+str(rid)}); Clock.schedule_once(lambda *_:self.after_write('رکورد با موفقیت حذف شد.'),0)
            except Exception as exc: Clock.schedule_once(lambda *_:self.write_error(str(exc)),0)
        Thread(target=work,daemon=True).start()

    def message(self,title,text):
        root=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8)); root.add_widget(self.label(text,'10sp',SECONDARY,False,'center')); p=Popup(title=fa_display(title),content=root,size_hint=(.88,.34)); root.add_widget(self.btn('متوجه شدم',lambda *_:p.dismiss(),PRIMARY,dp(40))); p.open()

    def go_dashboard(self,*_):
        if self.manager: self.manager.current=self.return_to or 'dashboard'
    def go_back(self,*_): self.go_dashboard()
