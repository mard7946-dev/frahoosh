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

from mobile.screens.operational_centers import OpsRouter
from mobile.config import APP_NAME, CARD, PRIMARY, SCHOOL_NAME, SCHOOL_YEAR, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text, fa_display, PersianTextInput, PersianSpinner

# Build #936 baseline contract: login untouched; operational CRUD policy is defined below.
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
class ModuleItemCard(ButtonBehavior, BoxLayout):
    """A single module entry, presented vertically like a PanelCard body item."""
    def __init__(self, label, route, module_enter, **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=[dp(12), dp(7)],
            spacing=dp(8),
            size_hint_y=None,
            height=dp(46),
            **kwargs,
        )
        self.route = route
        self.module_enter = module_enter
        with self.canvas.before:
            Color(0.08, 0.16, 0.25, 1)
            self.bg = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._sync, size=self._sync)

        self.title = Label(
            text=fa_display(str(label)),
            font_name=font_name(),
            font_size="12.5sp",
            color=WHITE,
            bold=True,
            halign="right",
            valign="middle",
        )
        self.title.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.add_widget(self.title)

    def on_release(self):
        self.module_enter(self.route)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class ModuleCategoryCard(BoxLayout):
    """Module category: intentionally mirrors the dashboard PanelCard accordion."""
    def __init__(self, title, index, total, modules, module_enter, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(0),
            size_hint_y=None,
            **kwargs,
        )
        self.title_text = title
        self.modules = modules or []
        self.module_enter = module_enter
        self.expanded = False

        # This is the same shell/header/meta/body pattern used by PanelCard.
        with self.canvas.before:
            Color(0.045, 0.11, 0.20, 0.98)
            self.bg = RoundedRectangle(radius=[dp(20)])
        self.bind(pos=self._sync, size=self._sync)

        self.header = Button(
            text=fa_display(f"باز کردن  |  {title}"),
            font_name=font_name(),
            font_size="17sp",
            background_normal="",
            background_color=(0.055, 0.20, 0.34, 1),
            color=WHITE,
            bold=True,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(64),
        )
        self.header.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.header.bind(on_release=lambda *_: self.toggle())
        self.add_widget(self.header)

        self.meta = Label(
            text=fa_display(f"دسته {index} از {total}  -  {len(self.modules)} ماژول"),
            font_name=font_name(),
            font_size="10sp",
            color=(0.60, 0.82, 0.96, 1),
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(30),
        )
        self.meta.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.add_widget(self.meta)

        # IMPORTANT: modules are a vertical accordion body, NOT a two-column grid.
        self.body = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=[dp(2), dp(4)],
            size_hint_y=None,
            height=0,
        )
        self.add_widget(self.body)

        self._build_modules()
        self._set_expanded(False)

    def _build_modules(self):
        self.body.clear_widgets()
        for label, route in self.modules:
            self.body.add_widget(ModuleItemCard(label, route, self.module_enter))

    def toggle(self):
        self._set_expanded(not self.expanded)

    def _set_expanded(self, value):
        self.expanded = bool(value)
        if self.expanded:
            self.header.text = fa_display(f"بستن  |  {self.title_text}")
            self.body.height = (
                sum(w.height for w in self.body.children)
                + max(0, len(self.body.children) - 1) * dp(6)
                + dp(8)
            )
            self.height = dp(64) + dp(30) + self.body.height + dp(10)
        else:
            self.header.text = fa_display(f"باز کردن  |  {self.title_text}")
            self.body.height = 0
            self.height = dp(64) + dp(30) + dp(10)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size

SUBMENUS = {
"management":[("اطلاعات مدرسه","school_profile"),("دانش‌آموزان","students"),("دبیران","teachers"),("کادر و کارکنان","staff"),("پایه و کلاس‌ها","school_class_config"),("حساب‌های سامانه","users"),("رویدادها","school_events"),("صندوق پیام","messages"),("کارنامه‌ها","report_cards"),("برنامه هفتگی","weekly_schedule"),("آزمون آنلاین","teacher_exams"),("کلاس آنلاین","online_classes"),("مالی","finance_accounts"),("تابلو هوشمند","smart_board_content"),("نمونه کلاس هوشمند","smart_class_preview"),("ملاقات‌ها","meeting_requests"),("گزارش‌های مدیریتی","report_cards")],
"educational":[("ملاقات‌ها","meeting_requests"),("پرونده اطلاعاتی دانش‌آموز","students"),("پرونده پرسنلی همکاران","staff"),("کلاس‌های دبیران","teacher_classes"),("فعال‌سازی کلاس آنلاین","online_classes"),("برنامه هفتگی","weekly_schedule"),("برنامه امتحانی","exam_schedule"),("پیگیری آموزشی","educational_followups"),("پیگیری درسی","academic_followups"),("پیگیری انضباطی","discipline_records"),("ثبت انضباطی","discipline_records"),("نمرات و کارنامه‌ها","student_grades"),("ریز نمرات","grade_items"),("فعالیت‌های دبیران","teacher_activities"),("گزارش آموزشی هوشمند","ai_smart_reports"),("جشنواره خوارزمی","khwarizmi_registrations"),("آزمون آنلاین","teacher_exams"),("جلسات دبیر و ولی","teacher_parent_meetings"),("صندوق پیام","messages")],
"executive":[("ملاقات با اولیا","meeting_requests"),("پرونده دانش‌آموزی","students"),("پرونده پرسنلی کارکنان","staff"),("ارتباط اولیا و فرزند","parent_children"),("کلاس‌ها","executive_classes"),("فعال‌سازی برنامه هفتگی","weekly_schedule"),("فعال‌سازی کارنامه ماهیانه","monthly_report_cards"),("کارنامه مستمر و پایان ترم","report_cards"),("ثبت انضباطی","discipline_records"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("امور اجرایی","executive_operations"),("درخواست‌های اجرایی","executive_requests"),("پرونده‌های بایگانی","archive_items"),("گزارش‌های اجرایی","executive_reports"),("اموال و تجهیزات","assets"),("نظرسنجی‌ها","surveys"),("کلاس‌های آنلاین","online_classes"),("رویدادها و مراسمات","school_events"),("صندوق پیام","messages")],
"cultural":[("ملاقات با اولیا","meeting_requests"),("پیام‌های پرورشی","messages"),("تعریف فعالیت و اردو","activity_programs"),("ایجاد مسابقات","activity_offers"),("مسابقات فرهنگی","cultural_competitions"),("مسابقات هنری","art_competitions"),("مسابقات ورزشی","sport_competitions"),("ثبت‌نام‌های فعالیت","activity_registrations"),("فعالیت‌ها و مراسمات","educational_activities"),("انتخابات شورای دانش‌آموزی","student_council"),("بسیج دانش‌آموزی","basij_registration"),("همیار مدرسه","school_ally"),("شهردار مدرسه","school_mayor"),("مکبر","morning_leaders"),("قاری برنامه ظهرگاهی","qari_registration"),("جدول مراسم ظهرگاهی","morning_ceremony"),("ثبت انضباطی","discipline_records"),("گزارش‌های پرورشی","cultural_reports"),("صندوق پیام","messages")],
"advisor":[("ملاقات با اولیا","meeting_requests"),("پرونده‌های مشاوره","counseling_records"),("کلاس‌های مشاوره","counseling_classes"),("پیگیری جلسات","counseling_followups"),("هدایت تحصیلی","counseling_guidance"),("ارجاع دانش‌آموز","student_referrals"),("پیگیری آموزشی","educational_followups"),("پیگیری درسی","academic_followups"),("دانش‌آموزان","students"),("اولیا","parent_children"),("جلسات اولیا","parent_meetings"),("درخواست‌های ملاقات","parent_meeting_requests"),("گزارش‌های مشاوره","ai_smart_reports"),("تابلوی مشاور","counselor_board"),("موارد انضباطی","discipline_records"),("صندوق پیام","messages")],
"teachers":[("کلاس‌های من","teacher_classes"),("طرح درس","lesson_plans"),("برنامه هفتگی","weekly_schedule"),("کلاس‌های آنلاین فعال","online_classes"),("آزمون آنلاین","teacher_exams"),("بانک سؤال","quiz_questions"),("حضور و غیاب","attendance"),("نمرات درسی","grades"),("ریز نمرات","grade_items"),("ارزیابی دانش‌آموزان","student_grades"),("تکالیف","assignments"),("موارد انضباطی","discipline_records"),("ارجاع دانش‌آموز","student_referrals"),("فعالیت‌های دبیر","teacher_activities"),("ملاقات با اولیا","meeting_requests"),("جلسات دبیر و ولی","teacher_parent_meetings"),("صندوق پیام","messages")],
"students":[
("اطلاعات دانش‌آموز","students"),("پایه و کلاس","student_class_info"),("حضور و غیاب","attendance"),
("نمرات","student_grades"),("تکالیف دبیران","assignment_submissions"),("صندوق پیام","messages"),
("ثبت‌نام مسابقات","student_competitions"),("ثبت‌نام جشنواره‌ها","student_competitions"),("ثبت‌نام مسابقات و فعالیت‌ها","student_competitions"),("ثبت‌نام شورای دانش‌آموزی","student_council_registration"),
("ثبت‌نام بسیج","student_basij_registration"),("ثبت‌نام همیار مدرسه","student_ally_registration"),("ثبت‌نام شهردار مدرسه","student_mayor_registration"),
("برنامه هفتگی","weekly_schedule"),("برنامه امتحانات","exam_schedule"),("صندلی کلاسی","class_seat_assignments"),
("صندلی امتحان","exam_seat_assignments"),("درخواست گواهی","certificate_requests"),
("کلاس آنلاین","online_classes")
],
"parents":[
("انتخاب یک یا چند دانش‌آموز","parent_children"),("اطلاعات دانش‌آموز","students"),
("کارنامه و نمرات","student_grades"),("حضور و غیاب","attendance"),
("کارنامه ماهانه","monthly_report_cards"),("کارنامه","report_cards"),
("انضباط","discipline_records"),("گزارش هوشمند","ai_smart_reports"),
("پیام‌ها و اطلاعیه‌ها","messages"),("ملاقات‌ها","meeting_requests"),
("نظرسنجی","survey_responses"),("برنامه هفتگی","weekly_schedule"),
("برنامه امتحانات","exam_schedule"),("سوابق پرداخت","payment_records"),
("سرویس مدرسه","transport_requests"),
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
"payment":[("درخواست‌های پرداخت","payment_attempts"),("سوابق پرداخت","payment_records"),("تراکنش‌ها","payment_transactions")],
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
    "management":[("مدیریت کاربران و کارکنان","users"),("کلاس آنلاین","online"),("برنامه هفتگی و برنامه امتحانات","schedule"),("گزارش‌ها و آمار","reports"),("تنظیمات مدرسه","settings"),("ملاقات‌ها","meeting_requests"),("مالی","finance")],
    "executive":[("دانش‌آموزان","students"),("کلاس‌ها","executive_classes"),("کارکنان","staff"),("پرونده‌ها","archive_items"),("امور اجرایی","executive_operations"),("گزارش‌ها","executive_reports"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("درخواست‌های ملاقات","meeting_requests")],
    "educational":[("حضور و غیاب","attendance"),("ارجاعات آموزشی","student_referrals"),("جلسات","meeting_requests"),("اطلاع‌رسانی","messages"),("امتحانات","teacher_exams"),("بانک سؤال","quiz_questions"),("گزارش‌های آموزشی","ai_smart_reports"),("تأیید و مدیریت ملاقات‌ها","meeting_requests")],
    "cultural":[("فعالیت‌های فرهنگی","educational_activities"),("مسابقات","cultural_competitions"),("برنامه‌های پرورشی","school_events"),("ثبت‌نام فعالیت‌ها","cultural_activity_registrations"),("گزارش‌های پرورشی","cultural_reports"),("درخواست‌های ملاقات","meeting_requests")],
    "advisor":[("پرونده مشاوره","counseling_records"),("جلسات","meeting_requests"),("پیگیری دانش‌آموز","counseling_followups"),("ارجاعات","student_referrals"),("هدایت تحصیلی","counseling_followups"),("گزارش مشاوره","ai_smart_reports"),("درخواست‌های ملاقات","meeting_requests")],
    "teachers":[("کلاس‌های من","teacher_classes"),("نمرات و کارنامه","student_grades"),("تکالیف","assignments"),("حضور و غیاب","attendance"),("آزمون‌ها","teacher_exams"),("طرح درس","lesson_plans"),("جلسات","meeting_requests"),("گزارش‌ها","teacher_activities"),("ملاقات با اولیا","teacher_parent_meetings")],
    "students":[("انتخاب و اطلاعات من","students"),("پایه و کلاس","student_class_info"),("نمرات","student_grades"),("تکالیف","assignment_submissions"),("پیام‌ها","messages"),("حضور و غیاب","attendance"),("مسابقات و فعالیت‌ها","activity_registrations"),("برنامه هفتگی","weekly_schedule"),("امتحانات","exam_schedule"),("گزارش عملکرد","ai_smart_reports"),("کلاس آنلاین","online_classes")],
    "parents":[("انتخاب دانش‌آموز","parent_children"),("اطلاعات دانش‌آموز","students"),("کارنامه و نمرات","student_grades"),("حضور و غیاب","attendance"),("تکالیف و فعالیت‌های آموزشی","assignments"),("پیام‌ها و اطلاعیه‌ها","messages"),("برنامه هفتگی و امتحانات","schedule"),("جلسات با دبیران","teacher_meetings"),("پرداخت‌ها و امور مالی","payment_records"),("فعالیت‌های فرهنگی و پرورشی","cultural_activity_registrations"),("درخواست گواهی اشتغال به تحصیل","certificate_requests"),("تعیین وقت ملاقات","meeting_requests")],
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
    "users":"account_settings","virtual":"online_classes","planning":"weekly_schedule","reports":"ai_smart_reports","settings":"school_profile","students":"students","staff":"staff","meeting_requests":"meeting_requests","certificate_requests":"certificate_requests","attendance":"attendance","account_settings":"account_settings",
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
"school_profile":"مشخصات مدرسه","school_class_config":"ساختار کلاس‌ها","users":"حساب‌های سامانه","students":"دانش‌آموزان","teachers":"دبیران","staff":"کادر و کارکنان","teacher_classes":"کلاس‌های دبیران","lesson_plans":"طرح درس","attendance":"حضور و غیاب","grades":"نمرات","student_grades":"ارزیابی دانش‌آموزان","assignments":"تکالیف","parents":"اولیا","parent_children":"ارتباط ولی و فرزند","parent_meetings":"جلسات اولیا","finance_accounts":"حساب‌های مالی","finance_transactions":"تراکنش‌های مالی","finance_donations":"کمک‌های داوطلبانه","payment_offers":"گزینه‌های پرداخت","payment_attempts":"درخواست‌های پرداخت","payment_records":"سوابق پرداخت","online_classes":"کلاس‌های آنلاین","online_class_sessions":"جلسات آنلاین","online_class_students":"دانش‌آموزان کلاس","online_class_teachers":"دبیران کلاس","educational_activities":"فعالیت‌های پرورشی","school_events":"رویدادهای مدرسه","counseling_records":"سوابق مشاوره","counseling_followups":"پیگیری مشاوره","smart_board_content":"محتوای تابلو","smart_board_activities":"فعالیت‌های تابلو","smart_board_quizzes":"آزمون‌های کوتاه","smart_board_whiteboards":"تخته‌های آموزشی","ai_assistant_sessions":"جلسات دستیار","ai_questions":"پرسش‌های هوشمند","ai_smart_reports":"گزارش‌های هوشمند","messages":"پیام‌ها","message_targets":"مخاطبان پیام","message_reads":"وضعیت خواندن","report_cards":"کارنامه‌ها","report_card_snapshots":"نسخه‌های کارنامه","weekly_schedule":"برنامه هفتگی","generated_weekly_schedule":"برنامه تولیدشده","exam_schedule":"برنامه امتحانات","account_settings":"تنظیمات حساب","teacher_exams":"آزمون‌های آنلاین","discipline_records":"موارد انضباطی","educational_followups":"پیگیری‌های آموزشی","academic_followups":"پیگیری‌های درسی","certificate_requests":"درخواست گواهی اشتغال به تحصیل","activity_offers":"مسابقات و فعالیت‌ها","activity_registrations":"ثبت‌نام فعالیت‌ها","student_council":"انتخابات شورای دانش‌آموزی","basij_registration":"عضویت بسیج دانش‌آموزی","school_ally":"طرح همیار مدرسه","school_mayor":"طرح شهردار مدرسه","cultural_competitions":"مسابقات فرهنگی","art_competitions":"مسابقات هنری","sport_competitions":"مسابقات ورزشی","morning_leaders":"مکبر","qari_registration":"قاری برنامه ظهرگاهی","morning_ceremony":"مراسم ظهرگاهی","student_referrals":"ارجاع دانش‌آموز","teacher_parent_meetings":"درخواست ملاقات اولیا","parent_meeting_requests":"درخواست ملاقات","meeting_requests":"ملاقات و درخواست جلسه","smart_class_preview":"نمونه کلاس هوشمند","khwarizmi_registrations":"جشنواره خوارزمی","monthly_report_cards":"کارنامه ماهیانه","class_seat_assignments":"شماره صندلی کلاسی","exam_seat_assignments":"شماره صندلی امتحانی","assignment_submissions":"ارسال تکالیف","parent_activities":"فعالیت‌های اولیا","student_class_info":"پایه و کلاس","module_activations":"فعال‌سازی قابلیت‌ها"
}

if _shared_friendly:
    FRIENDLY.update(_shared_friendly)

COLUMNS = {
    "id":"شناسه", "father_name":"نام پدر","mother_name":"نام مادر","birth_certificate_place":"محل صدور","birth_place":"محل تولد","religion":"دین","sect":"مذهب","nationality":"ملیت","student_phone":"شماره تماس دانش‌آموز","father_phone":"شماره تماس پدر","mother_phone":"شماره تماس مادر","personnel_code":"کد پرسنلی","service_years":"سابقه خدمت","discipline_type":"نوع مورد انضباطی","record_date":"تاریخ ثبت","decision_type":"نوع تصمیم","deduct_score":"میزان کسر نمره","referral_to":"ارجاع به","followup_date":"تاریخ پیگیری","followup_items":"موارد پیگیری‌شده","decision":"تصمیم","destination":"محل ارائه گواهی","request_date":"تاریخ درخواست","executive_note":"یادداشت معاون اجرایی","participation_type":"تیمی / انفرادی","team_members":"همگروهی‌ها","competition_type":"نوع مسابقه","payment_status":"وضعیت پرداخت","category":"دسته‌بندی","active":"فعال","activated_by":"فعال‌سازی توسط","reason":"علت","referral_date":"تاریخ ارجاع","requested_date":"تاریخ درخواست ملاقات","manager_status":"تأیید مدیر","file_url":"فایل","answer_text":"پاسخ","submitted_at":"زمان ارسال","seat_number":"شماره صندلی","month_name":"ماه","program_key":"کلید برنامه","account_type":"نوع حساب","account_number":"شماره حساب","balance":"موجودی","transaction_type":"نوع تراکنش","offer_id":"گزینه پرداخت","gateway":"درگاه","target_type":"نوع مخاطب","payment_reason":"علت پرداخت","audience_type":"نوع مخاطب","audience_value":"مخاطب","body":"متن پیام","target_role":"نقش مخاطب","target_name":"نام مخاطب","target_class_name":"کلاس مخاطب","first_name":"نام", "last_name":"نام خانوادگی", "national_code":"کد ملی", "grade":"پایه",
    "class_name":"کلاس", "phone":"تلفن", "subject":"درس", "teacher_name":"دبیر", "score":"نمره",
    "max_score":"حداکثر نمره", "status":"وضعیت", "amount":"مبلغ", "title":"عنوان", "description":"توضیحات",
    "created_at":"تاریخ ثبت", "attendance_date":"تاریخ حضور", "exam_date":"تاریخ آزمون", "event_date":"تاریخ رویداد",
    "start_time_shamsi":"شروع", "end_time_shamsi":"پایان", "role":"نقش", "email":"ایمیل", "username":"نام کاربری", "password":"رمز اولیه ورود", "child_national_code":"کد ملی فرزند",
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
    "school_year":"سال تحصیلی",
    "source_username":"کاربر مبدأ", "target_username":"کاربر مقصد",
    "relationship_type":"نوع ارتباط", "target_role":"نقش مقصد", "active":"فعال", "classroom_seat":"صندلی کلاسی", "exam_seat":"صندلی امتحانی",
    "parent_id":"شناسه ولی", "parent_name":"نام ولی", "target_role":"نقش مخاطب", "target_name":"نام مخاطب",
    "requested_date_shamsi":"تاریخ درخواست شمسی", "requested_time":"ساعت درخواست", "educational_approval":"تأیید معاون آموزشی",
    "manager_approval":"تأیید مدیریت", "registration_date":"تاریخ ثبت", "certificate_type":"نوع گواهی",
    "reason":"علت", "report":"گزارش", "meeting_at":"زمان جلسه","due_date":"مهلت ارسال","expires_at":"تاریخ انقضا","max_file_size_mb":"حداکثر حجم فایل (MB)","file_name":"نام فایل","file_mime_type":"نوع فایل","file_size_bytes":"حجم فایل (بایت)"
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

HIDDEN = {"created_at", "updated_at", "deleted_at", "password"}

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
"school_relationships":["source_username","target_username","target_role","relationship_type","active"],
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
"meeting_requests":["title","requester_username","requester_role","requester_name","student_id","student_name","parent_username","parent_name","target_role","target_user_id","target_username","target_name","requested_day","requested_date","requested_time","reason","description","status","manager_status","manager_note","educational_status","educational_note","final_date","final_time","final_note"],"student_registrations":["student_id","activity_id","activity_title","activity_kind","fee","payment_status","payment_url","payment_reference","registration_code","registration_date","status"],"cultural_activity_registrations":["activity_id","activity_title","activity_kind","student_id","student_name","fee","payment_status","registration_code","registration_date","status"],"student_referrals":["student_id","teacher_id","referral_to","reason","referral_date","status"],"teacher_activities":["teacher_id","student_id","title","activity_type","subject","score","description","activity_date"],"teacher_attendance":["student_id","teacher_id","class_name","subject","attendance_date","status","description"],"teacher_parent_meetings":["teacher_id","student_id","parent_id","requested_date","status","manager_status","reason"],"activity_offers":["title","category","event_date","active","amount","settings"],"activity_registrations":["activity_id","student_id","participation_type","team_members","competition_type","payment_status","status"],"khwarizmi_registrations":["title","category","grade","class_name","student_id","status"],"class_seats":["student_id","class_name","seat_no"],"exam_seats":["student_id","exam_name","seat_no"],"monthly_report_cards":["student_id","month_name","active"],"competitions":["title","category","start_date","end_date","status","description"],"executive_requests":["title","requester","status","description","role"],"executive_operations":["operation_type","title","student_id","class_name","description","status","operation_date","created_by"],"executive_reports":["title","report_type","student_id","class_name","payload","report_date","created_by"],"assets":["title","category","quantity","location","archived"],"archive_items":["title","student_id","location","description"],"backup_records":["file_path","backup_type","size_bytes","status","created_by"],"surveys":["title","description","status","audience","start_at","end_at","created_by"],"survey_questions":["survey_id","question","question_type","options","required","sort_order"],"survey_responses":["survey_id","respondent_username","respondent_role","student_id","submitted_at"],
    "survey_responses_legacy":["survey_id","respondent_username","respondent_role","student_id"],"program_activations":["program_key","title","active","activated_by"],"student_council":["student_id","student_name","election_year","status"],"basij_registration":["student_id","student_name","registration_date","status"],"school_ally":["student_id","student_name","role","status"],"school_mayor":["student_id","student_name","status"],"cultural_competitions":["title","category","start_date","end_date","status","description"],"art_competitions":["title","category","start_date","end_date","status","description"],"sport_competitions":["title","category","start_date","end_date","status","description"],"morning_leaders":["student_id","student_name","status"],"qari_registration":["student_id","student_name","status"],"morning_ceremony":["title","program_key","active","description"],"parent_activities":["title","description","activity_date","status"],"student_class_info":["student_id","grade","class_name","academic_year"],"message_reads":["message_id","username","read_at"],"certificate_requests":["student_id","student_name","destination","request_date","status","executive_note"],"parent_meeting_requests":["student_id","teacher_id","parent_phone","reason","meeting_date","status"],"survey_answers":["response_id","question_id","answer"],
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
        "attendance","student_referrals","meeting_requests","ai_smart_reports",
        "messages","message_targets","exam_schedule","quiz_questions","teacher_classes","students",
        "educational_followups","academic_followups","khwarizmi_registrations","module_activations","teacher_activities","grade_items","teacher_parent_meetings",
        "grades","student_grades","grade_items","teacher_exams","discipline_records","weekly_schedule",
        "assignments","lesson_plans"
    },
    "executive": {
        "students","executive_classes","staff","archive_items","executive_operations","executive_reports",
        "report_cards","messages","weekly_schedule","discipline_records",
        "certificate_requests","school_class_config","parent_children","school_relationships","assets","student_cards","class_cards","executive_operations","executive_requests","archive_items","surveys",
        "certificates","executive_requests","surveys","module_activations"
    },
    "cultural": {
        "morning_ceremony","cultural_competitions","activity_programs","competitions",
        "educational_activities","cultural_reports","cultural_activity_registrations",
        "messages","message_targets","activity_offers","activity_registrations",
        "student_council","basij_registration","school_ally","school_mayor","qari_registration","module_activations",
        "art_competitions","sport_competitions","morning_leaders"
    },
    "responsible": {
        "educational_followups","academic_followups"
    },
    "advisor": {
        "counselor_board","counseling_records","counseling_followups","student_referrals","counseling_classes","counseling_guidance","parent_meetings","parent_meeting_requests",
        "parent_meetings","counseling_classes","parent_activities","counseling_guidance",
        "ai_smart_reports","discipline_records","messages","message_targets","educational_followups","academic_followups",
        "academic_followups","parent_meeting_requests"
    },
    "teacher": {
        "teacher_classes","attendance","grades","assignments","teacher_exams","quiz_questions","grade_items","student_grades","teacher_activities","teacher_parent_meetings",
        "lesson_plans","teacher_meetings","teacher_activities","grade_items","discipline_records",
        "messages","message_targets","student_referrals"
    },
    "finance": {
        "finance_accounts","finance_transactions","finance_donations","payment_offers","payment_attempts","payment_records"
    },
    # Consumer roles: only the workflows explicitly requested by the school
    # are writable. Every other student/parent module is informational.
    "student": {
        "assignment_submissions",
        "activity_registrations",
        "school_ally",
        "basij_registration",
        "school_mayor",
        "student_council",
        "certificate_requests",
        "payment_attempts",
    },
    "parent": {
        "payment_attempts",
        "meeting_requests",
        "transport_requests",
        "parent_activities",
        "parent_children",
        "survey_responses",
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
    "assignments":["student_id","teacher_id","title","subject","class_name","description","status","due_date","max_file_size_mb","expires_at"],
    "attendance":["student_id","teacher_id","class_name","subject","attendance_date","status"],
    "grades":["student_id","teacher_id","subject","score","max_score","term"],
    "teacher_exams":["teacher_id","title","subject","grade","class_name","exam_type","duration","description","published","secure_mode","max_attempts","passing_score"],
    "online_classes":["title","subject","lesson","teacher","grade","class_name","duration","start_time_shamsi","end_time_shamsi","status","join_url","meeting_url"],
    "finance_donations":["title","description","amount","status"],
    "messages":["title","description","status"],
    "module_activations":["module_key","active","activated_by","activated_at","settings"],
    "school_profile":["title","description"],
    "school_relationships":["source_username","target_username","target_role","relationship_type","active"],
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
    "assignment_submissions":["assignment_id","student_id","file_url","file_name","file_mime_type","file_size_bytes","answer_text","submitted_at","status","expires_at"],
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
    "school_relationships":"ارتباط افراد مدرسه؛ اتصال ولی، دانش‌آموز، دبیر و کارکنان",
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
        self.parent_selected_student_id=None

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
        ignored.  This does not duplicate CRUD/Excel/PDF actions.
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
            except Exception:
                pass

            def _run(_dt):
                try:
                    cb(instance)
                except Exception as exc:
                    print("MODULE BUTTON CALLBACK ERROR:", repr(exc))
                    try:
                        self.status.text=fa_display("اجرای عملیات با خطا روبه‌رو شد: "+str(exc))
                        self.status.color=(.8,.15,.15,1)
                    except Exception:
                        pass
                finally:
                    # Re-arm after the current touch cycle so the next tap is
                    # always accepted.
                    fired["value"] = False
            Clock.schedule_once(_run, 0)

        # Kivy Button.on_press/on_release dispatch the button instance;
        # they do not pass a touch object.  The previous two-argument handlers
        # therefore raised TypeError before any CRUD/Excel/PDF callback ran,
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
            "management":"manager", "manager":"manager", "accountant":"accountant", "حسابدار":"accountant", "educational":"educational",
            "executive":"executive", "cultural":"cultural", "advisor":"advisor","responsible":"responsible","مسئول مربوطه":"responsible",
            "teachers":"teacher", "teacher":"teacher", "staff":"staff"
        }.get(panel_role, panel_role)
        if panel_role in {"manager","educational","executive","cultural","advisor","teacher","staff","accountant","responsible"}:
            role = panel_role
        # The UI must mirror the same role/table contract as Supabase RLS.
        # Never show write controls for a table merely because the account is
        # a school staff member; that was the source of "not authorized"
        # errors on restricted workflows such as online-class creation.
        return resolved in EDITABLE.get(role, set())

    def set_module(self,route,return_to="dashboard"):
        self._ensure_built()
        # Resolve the exact ZIP/mother module id to its canonical Supabase table.
        # Never fall back to the management panel: an unknown module is a real
        # integration error and must not silently open the wrong panel.
        route = str(route or "").strip()
        # Dedicated operational centers receive the active panel role through
        # AppState as well. Without this handoff, an activities module opened
        # from a deputy panel could incorrectly fall back to the student view.
        try:
            if self.app_state is not None and self.panel_role:
                self.app_state.panel_role = self.panel_role
        except Exception:
            pass
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
        # Dedicated workflows must be reached before the generic CRUD workspace.
        # These modules have business rules/PDF/approval flows that a plain table
        # editor cannot provide.
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app is not None:
                special = None
                if canonical == "assignment_submissions":
                    special = app.ensure_assignment_submission_workflow()
                elif canonical == "certificate_requests":
                    special = app.ensure_certificate_workflow()
                elif canonical in {"meeting_requests","parent_meeting_requests","teacher_meetings","teacher_parent_meetings","meetings"}:
                    special = app.ensure_meetings()
                elif canonical in {"finance","finance_accounts","finance_transactions","payment_records","payment_offers"}:
                    special = app.ensure_finance()
                elif canonical in {"online_classes","virtual"}:
                    special = app.ensure_online_workflow()
                elif canonical in {"finance_accounts","finance_transactions","payment_records","payment_offers","finance_donations","reports","finance"}:
                    from mobile.screens.finance import FinanceScreen
                    try:
                        special = app.sm.get_screen("finance")
                    except Exception:
                        special = FinanceScreen(name="finance", app_state=self.app_state)
                        app.sm.add_widget(special)
                elif canonical in {"teacher_exams","quiz_links"}:
                    special = app.ensure_exam_authoring()
                elif canonical == "module_activations":
                    special = app.ensure_module_activation_workflow()
                if special is not None:
                    self.manager.current = special.name
                    return
        except Exception as exc:
            print("SPECIAL WORKFLOW ROUTE ERROR:", repr(exc))
            raise

        # معاون اجرایی برای اسناد و چیدمان‌های اجرایی از مرکز تخصصی خودش استفاده می‌کند.
        # این مسیر عمداً قبل از مرکز عمومی اجرا می‌شود تا این ماژول‌ها به صفحه
        # «آماده» یا CRUD عمومی سقوط نکنند و جدول تخصصی هر موضوع نمایش داده شود.
        try:
            if self.role() == "executive" and canonical in {
                "report_cards", "student_grades",
                "student_cards", "class_cards",
                "exam_schedule",
                "class_seat_assignments", "class_seats",
                "exam_seat_assignments", "exam_seats",
                "certificates", "certificate_requests"
            }:
                app = App.get_running_app()
                if app is not None:
                    screen = app.ensure_executive_center()
                    if screen is None:
                        raise RuntimeError("مرکز عملیاتی معاون اجرایی ساخته نشد.")
                    screen.initial_action = {
                        "report_cards": "report_cards", "student_grades": "report_cards",
                        "student_cards": "cards", "class_cards": "cards",
                        "exam_schedule": "exam_schedule",
                        "class_seat_assignments": "class_seats", "class_seats": "class_seats",
                        "exam_seat_assignments": "exam_seats", "exam_seats": "exam_seats",
                        "certificates": "certificates", "certificate_requests": "certificates"
                    }[canonical]
                    if self.manager:
                        self.manager.current = screen.name
                    return
        except Exception as exc:
            print("EXECUTIVE SPECIAL ROUTE ERROR:", repr(exc))
            raise

        # Dedicated operational centers own the modules that require structured
        # forms/tables rather than the generic CRUD fallback.
        try:
            from kivy.app import App
            from mobile.screens.operational_centers import OpsRouter
            app = App.get_running_app()
            if app is not None and OpsRouter.mode_for(canonical):
                screen = app.ensure_operational_center(canonical)
                if screen is None:
                    raise RuntimeError("مرکز عملیاتی این ماژول آماده نشد.")
                if self.manager:
                    self.manager.current = screen.name
                return
        except Exception as exc:
            print("OPERATIONAL CENTER ROUTE ERROR:", repr(exc))
            raise

        # A concrete module route (for example executive_classes, students,
        # discipline_records, cultural_reports) must open its real table directly.
        # Previously it fell through with table=None and render() treated the
        # table id as a panel key, producing an empty/"آماده‌سازی" screen.
        if canonical not in SUBMENUS and canonical != "smart_class_preview":
            self.return_to = return_to or "dashboard"
            self.table = canonical
            self.route = canonical
            self.selected_row = None
            self.render()
            return

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
            "executive":"executive", "cultural":"cultural", "advisor":"advisor", "responsible":"responsible",
            "مسئول مربوطه":"responsible",
            "teachers":"teacher", "teacher":"teacher", "staff":"staff"
        }.get(value, value)

    def _panel_key(self):
        panel = str(self.route or "").strip().lower()
        return {
            "manager": "management",
            "management": "management",
            "teacher": "teachers",
            "teachers": "teachers",
            "parent": "parents",
            "parents": "parents",
            "student": "students",
            "students": "students",
        }.get(panel, panel)

    def _panel_category_map(self):
        # Category names/order come directly from the approved UI contract.
        # Route ids remain the existing real modules; this method only groups them.
        return {
            "management": [
                ("ارتباطات افراد", {"school_relationships"}),
                ("فعالیت آموزشی", {"report_cards","grades","class_seat_assignments","exam_seat_assignments","student_grades","teacher_exams","exam_schedule","weekly_schedule","teacher_classes","school_class_config"}),
                ("فعالیت‌های پرورشی", {"activity_registrations","activity_offers","educational_activities","art_competitions","sport_competitions","cultural_competitions","activity_programs","school_events","student_council","school_ally","basij_registration","school_mayor"}),
                ("دانش‌آموزان", {"students","archive_items","student_files","certificate_requests","discipline_records","attendance"}),
                ("دبیران و کارکنان", {"teachers","staff","teacher_activities","lesson_plans"}),
                ("اولیا", {"parent_children","parent_meeting_requests","meeting_requests","parent_activities"}),
                ("کلاس و مدرسه", {"executive_classes","online_classes","online_class_sessions","school_profile","smart_board_content"}),
                ("ارتباطات", {"messages","message_targets","message_reads","message_delivery","school_events"}),
                ("امور مالی", {"finance_accounts","finance_transactions","finance_donations","payment_offers","payment_attempts","payment_records","payment_transactions"}),
                ("گزارش‌ها و آمار", {"ai_smart_reports","executive_reports","cultural_reports","report_card_snapshots","surveys"}),
                ("مدیریت سامانه", {"users","account_settings","module_activations","backup_records"}),
            ],
            "executive": [
                ("ارتباطات افراد", {"school_relationships","parent_children"}),
                ("امور دانش‌آموزی", {"students","archive_items","certificate_requests","student_files","parent_children"}),
                ("امور کلاس‌ها", {"executive_classes","school_class_config","weekly_schedule","class_seat_assignments","exam_seat_assignments","attendance","discipline_records"}),
                ("امور امتحانات", {"exam_schedule","report_cards","exam_seat_assignments"}),
                ("امور کارکنان", {"staff","teachers","teacher_activities"}),
                ("امور اولیا", {"parent_children","meeting_requests","parent_meeting_requests","executive_requests","messages"}),
                ("اسناد و گزارش‌ها", {"archive_items","certificates","report_cards","executive_reports","ai_smart_reports"}),
            ],
            "educational": [
                ("برنامه‌ریزی آموزشی", {"teacher_classes","school_class_config","weekly_schedule","lesson_plans","teachers","staff"}),
                ("ارزشیابی", {"grades","student_grades","report_cards","teacher_exams","exam_schedule","quiz_questions","grade_items"}),
                ("آموزش آنلاین", {"online_classes","online_class_sessions","online_attendance","smart_board_whiteboards","assignments"}),
                ("وضعیت تحصیلی", {"students","student_referrals","educational_followups","academic_followups","discipline_records"}),
                ("گزارش‌های آموزشی", {"ai_smart_reports","executive_reports","student_grades","grade_items"}),
            ],
            "cultural": [
                ("فعالیت‌های پرورشی", {"educational_activities","activity_registrations","activity_programs","morning_ceremony","qari_registration","morning_leaders"}),
                ("مسابقات و جشنواره‌ها", {"cultural_competitions","art_competitions","sport_competitions","competitions","activity_offers"}),
                ("تشکل‌های دانش‌آموزی", {"student_council","school_ally","school_mayor","basij_registration"}),
                ("مناسبت‌ها و برنامه‌ها", {"school_events","messages","message_targets"}),
                ("گزارش پرورشی", {"cultural_reports","ai_smart_reports","discipline_records"}),
            ],
            "advisor": [
                ("پرونده مشاوره", {"counseling_records","students","parent_children","counseling_classes"}),
                ("جلسات", {"meeting_requests","parent_meetings","parent_meeting_requests","counseling_followups"}),
                ("پیگیری دانش‌آموز", {"student_referrals","counseling_followups","educational_followups","academic_followups"}),
                ("ارتباط با خانواده", {"parent_activities","parent_children","messages","message_targets"}),
                ("گزارش‌ها", {"ai_smart_reports","counseling_guidance","discipline_records"}),
            ],
            "teachers": [
                ("آموزش", {"teacher_classes","weekly_schedule","grades","student_grades","grade_items"}),
                ("ارزشیابی", {"grades","student_grades","teacher_exams","quiz_questions","exam_schedule","report_cards"}),
                ("تکالیف", {"assignments","assignment_submissions"}),
                ("کلاس آنلاین", {"online_classes","online_class_sessions","online_attendance","smart_board_whiteboards","online_class_chat"}),
                ("دانش‌آموزان", {"students","student_referrals","teacher_activities","discipline_records"}),
                ("ارتباطات", {"messages","message_targets","teacher_meetings","teacher_parent_meetings"}),
            ],
            "parents": [
                ("فرزند من", {"parent_children","students","student_grades","report_cards","monthly_report_cards","attendance","assignments","teacher_exams"}),
                ("ملاقات‌ها", {"meeting_requests","parent_meeting_requests","teacher_parent_meetings"}),
                ("پرداخت‌ها", {"finance_donations","payment_attempts","payment_records","payment_transactions"}),
                ("ارتباط با مدرسه", {"messages","message_targets","message_reads","school_events"}),
                ("خدمات دانش‌آموز", {"transport_requests","parent_children"}),
                ("فعالیت‌های اولیا", {"parent_activities","survey_responses"}),
            ],
            "students": [
                ("آموزش من", {"student_class_info","weekly_schedule","student_grades","report_cards","teacher_exams","exam_schedule","online_classes"}),
                ("تکالیف", {"assignments","assignment_submissions"}),
                ("کلاس آنلاین", {"online_classes","online_class_sessions","online_attendance","smart_board_whiteboards"}),
                ("فعالیت‌های مدرسه", {"activity_registrations","cultural_activity_registrations","student_council","school_ally","school_mayor","basij_registration"}),
                ("درخواست‌ها", {"certificate_requests","student_referrals"}),
                ("ارتباطات", {"messages","message_reads","school_events"}),
                ("پرداخت", {"payment_attempts","payment_records","payment_transactions"}),
            ],
            "finance": [
                ("دریافت‌ها", {"finance_donations","payment_records","finance_transactions","payment_transactions"}),
                ("درخواست‌های مالی", {"payment_attempts","payment_offers"}),
                ("تنظیمات مالی", {"finance_accounts","payment_offers"}),
                ("گزارش مالی", {"finance_transactions","payment_records","payment_transactions"}),
            ],
            "smart_board": [
                ("تابلو", {"smart_board_whiteboards","smart_board_content","smart_board_media","smart_board_activities"}),
                ("اطلاع‌رسانی", {"school_events","messages","message_targets"}),
                ("محتوای آموزشی", {"smart_board_content","smart_board_files","smart_board_media","smart_board_interactive_tools","smart_board_activities","smart_board_quizzes"}),
            ],
            "ai": [
                ("دستیار هوشمند", {"ai_assistant_sessions","ai_questions"}),
                ("آموزش هوشمند", {"ai_questions","teacher_exams","quiz_questions","ai_educational_analysis"}),
                ("تحلیل مدرسه", {"ai_educational_analysis","ai_smart_reports"}),
            ],
            "messages": [
                ("پیام‌ها", {"messages","message_reads","message_delivery"}),
                ("ارسال پیام", {"message_targets"}),
                ("اطلاعیه‌ها", {"school_events"}),
            ],
            "settings": [
                ("مدرسه", {"school_profile","school_class_config","weekly_schedule","exam_schedule"}),
                ("کاربران و دسترسی", {"users","permissions","account_settings"}),
                ("ظاهر سامانه", {"school_profile","account_settings"}),
                ("تنظیمات عمومی", {"messages","payment_offers","online_classes","module_activations","backup_records"}),
            ],
            "about": [
                ("معرفی", {"about_frahoosh","app_features","app_version"}),
                ("اطلاعات", {"school_profile","app_info","school_year"}),
                ("قوانین", {"usage_rules","privacy_policy"}),
            ],
        }

    def _module_category(self, table):
        for category, routes in self._panel_category_map().get(self._panel_key(), []):
            if table in routes:
                return category
        # Never create a new visual category. Unknown legacy routes are placed
        # in the closest existing category for that panel.
        configured = self._panel_category_map().get(self._panel_key(), [])
        return configured[-1][0] if configured else "مدیریت سامانه"

    def _group_module_items(self, items):
        configured = self._panel_category_map().get(self._panel_key(), [])
        grouped = {category: [] for category, _ in configured}
        for item in items:
            if not item or len(item) < 2:
                continue
            category = self._module_category(item[1])
            grouped.setdefault(category, []).append(item)
        return [(category, grouped[category]) for category, _ in configured if grouped.get(category)]

    def _panel_header_text(self):
        titles = {
            "management": ("پنل مدیریت", "مدیریت و نظارت یکپارچه مدرسه"),
            "executive": ("پنل معاون اجرایی", "مدیریت امور اجرایی، دانش‌آموزی و اسناد مدرسه"),
            "educational": ("پنل معاون آموزشی", "برنامه‌ریزی آموزشی، ارزشیابی و پیگیری تحصیلی"),
            "cultural": ("پنل معاون پرورشی", "مدیریت فعالیت‌های پرورشی، فرهنگی و تشکل‌های دانش‌آموزی"),
            "advisor": ("پنل مشاوره", "پرونده، جلسات و پیگیری وضعیت دانش‌آموزان"),
            "teachers": ("پنل دبیران", "کلاس‌ها، تدریس، ارزشیابی و ارتباط با خانواده"),
            "parents": ("پنل اولیا", "اطلاعات فرزند و خدمات ارتباطی والدین"),
            "students": ("پنل دانش‌آموز", "آموزش، تکالیف، کلاس آنلاین و خدمات دانش‌آموزی"),
            "finance": ("پنل مالی", "دریافت‌ها، پرداخت‌ها، حساب‌ها و گزارش مالی"),
            "smart_board": ("پنل تابلو هوشمند", "محتوای آموزشی و اطلاع‌رسانی مدرسه"),
            "ai": ("پنل هوش مصنوعی", "دستیار، آموزش هوشمند و تحلیل مدرسه"),
            "messages": ("پنل صندوق پیام‌ها", "پیام‌های دریافتی، ارسالی و اطلاعیه‌های مدرسه"),
            "settings": ("پنل تنظیمات", "تنظیمات مدرسه، کاربران، ظاهر و سامانه"),
            "about": ("پنل درباره برنامه", "معرفی فراهوش، امکانات، اطلاعات و قوانین"),
        }
        return titles.get(self._panel_key(), (APP_NAME, "مدیریت هوشمند مدرسه"))

    def render(self):
        self._ensure_built()
        self.body.clear_widgets()
        self.subbar.clear_widgets()
        self.subscroll.height = 0
        self.subscroll.opacity = 0
        items = SUBMENUS.get(self.route) or []
        self.body.size_hint_y = 1

        panel_title, panel_desc = self._panel_header_text()
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(108),
            padding=[dp(16), dp(10)],
            spacing=dp(4),
        )
        with header.canvas.before:
            Color(0.045, 0.11, 0.20, 0.98)
            bg = RoundedRectangle(radius=[dp(20)])
        header.bind(pos=lambda o,v: setattr(bg, "pos", v),
                    size=lambda o,v: setattr(bg, "size", v))
        header.add_widget(self.label(panel_title, "20sp", WHITE, True, "center"))
        header.add_widget(self.label(panel_desc, "10sp", SECONDARY, False, "center"))
        self.body.add_widget(header)

        if self.table:
            self.open_table(self.table, refresh_subbar=False)
            return

        groups = self._group_module_items(items)
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(3),
        )
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(3), dp(8), dp(3), dp(16)],
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))
        if not groups:
            empty = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(96),
                padding=[dp(12), dp(16)],
            )
            with empty.canvas.before:
                Color(0.045, 0.11, 0.20, 0.98)
                empty_bg = RoundedRectangle(radius=[dp(18)])
            empty.bind(
                pos=lambda o, v: setattr(empty_bg, "pos", v),
                size=lambda o, v: setattr(empty_bg, "size", v),
            )
            empty.add_widget(self.label(
                "برای این پنل ماژول فعالی در قرارداد سامانه ثبت نشده است.",
                "11sp", WHITE, True, "center"
            ))
            content.add_widget(empty)
        else:
            for index, (category, category_items) in enumerate(groups, 1):
                content.add_widget(
                    ModuleCategoryCard(
                        category,
                        index,
                        len(groups),
                        category_items,
                        self.set_module,
                    )
                )
        scroll.add_widget(content)
        self.body.add_widget(scroll)
        self.title.text = fa_display(panel_title)
        self.status.text = fa_display(
            f"{len(items)} ماژول • {len(groups)} دسته کاری • "
            + ("برای ورود، دسته را باز کنید" if groups else "ماژولی برای نمایش وجود ندارد")
        )

    def _badge(self,w):
        with w.canvas.before:
            Color(*PRIMARY); bg=RoundedRectangle(radius=[dp(9)])
        w.bind(pos=lambda o,v:setattr(bg,"pos",v),size=lambda o,v:setattr(bg,"size",v))

    def _current_username(self):
        profile = getattr(self.app_state, "profile", {}) or {}
        user = getattr(self.app_state, "user", {}) or {}
        role = str(profile.get("role") or getattr(self.app_state, "role", "") or "").strip().lower()
        if role in ("parent","parents","ولی","اولیا"):
            return str(profile.get("national_code") or "").strip()
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

    def _open_parent_directory(self):
        self.body.clear_widgets()
        self.table = None
        self.title.text = fa_display("پروفایل اولیا و ارتباط فرزند")
        self.body.add_widget(self.label("فهرست واقعی حساب‌های ولی و دانش‌آموزان متصل‌شده در مدرسه", "10sp", SECONDARY, False, "center"))
        try:
            links = self.app_state.api.table_select("parent_children", {"limit":"500"}) or []
            students = self.app_state.api.table_select("students", {"limit":"500"}) or []
        except Exception as exc:
            self.body.add_widget(self.label("خواندن اطلاعات انجام نشد: " + str(exc), "10sp", ERROR, True, "center"))
            self.body.add_widget(self.btn("بازگشت", lambda *_: self._back_to_submenus(), PRIMARY, dp(42)))
            return
        student_by_id = {str(s.get("id")): s for s in students}
        grouped = {}
        for link in links:
            username = str(link.get("parent_username") or "").strip()
            if not username:
                continue
            grouped.setdefault(username, []).append(student_by_id.get(str(link.get("student_id"))) or {})
        if not grouped:
            self.body.add_widget(self.label("هیچ حساب ولی متصل به دانش‌آموز در پایگاه داده ثبت نشده است.", "11sp", SECONDARY, False, "center"))
        for username, children in sorted(grouped.items()):
            names = []
            for student in children:
                name = " ".join(str(student.get(k) or "").strip() for k in ("first_name", "last_name")).strip()
                names.append(name or ("دانش‌آموز " + str(student.get("id") or "")))
            card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(105), padding=dp(9), spacing=dp(4))
            with card.canvas.before:
                Color(0.02, 0.10, 0.20, 0.92)
                bg = RoundedRectangle(radius=[dp(14)])
            card.bind(pos=lambda o,v,bg=bg:setattr(bg,"pos",v), size=lambda o,v,bg=bg:setattr(bg,"size",v))
            card.add_widget(self.label("حساب ولی: " + username, "12sp", WHITE, True, "center"))
            card.add_widget(self.label("فرزند/فرزندان: " + "، ".join(names), "10sp", SECONDARY, False, "center"))
            self.body.add_widget(card)
        self.body.add_widget(self.btn("بازگشت", lambda *_: self._back_to_submenus(), PRIMARY, dp(42)))

    def _open_parent_children(self):
        self.body.clear_widgets()
        self.table = None
        self.title.text = fa_display("اطلاعات فرزندان")
        username = self._current_username()
        selected_text = "هیچ فرزندی برای عملیات انتخاب نشده است." if not self.parent_selected_student_id else f"فرزند انتخاب‌شده برای عملیات: {self.parent_selected_student_id}"
        self.body.add_widget(self.label("یک یا چند فرزند متصل را می‌توانید برای عملیات والد انتخاب کنید.", "10sp", SECONDARY, False, "center"))
        self.body.add_widget(self.label(selected_text, "10sp", WHITE, True, "center"))
        try:
            current = self.app_state.api.table_select("parent_children", {"parent_username":"eq."+username, "limit":"200"}) or []
            students = self.app_state.api.table_select("students", {"order":"last_name.asc", "limit":"300"}) or []
        except Exception as exc:
            self.body.add_widget(self.label("خواندن اطلاعات انجام نشد: "+str(exc), "10sp", ERROR, True, "center"))
            self.body.add_widget(self.btn("بازگشت", lambda *_: self._back_to_submenus(), PRIMARY, dp(42)))
            return
        if not current:
            self.body.add_widget(self.label("هنوز دانش‌آموز مرتبطی برای این حساب ثبت نشده است.", "10sp", SECONDARY, False, "center"))
        for link in current:
            sid = link.get("student_id")
            student = next((s for s in students if str(s.get("id")) == str(sid)), None)
            name = f"{student.get('first_name','')} {student.get('last_name','')}" if student else f"دانش‌آموز شماره {sid}"
            self.body.add_widget(self.label(name, "12sp", WHITE, True, "center"))
            self.body.add_widget(self.btn("انتخاب این دانش‌آموز", lambda *_args, sid=sid: self._select_parent_child(sid), PRIMARY, dp(40)))
        self.body.add_widget(self.btn("بازگشت", lambda *_: self._back_to_submenus(), PRIMARY, dp(42)))

    def _select_parent_child(self, student_id):
        try:
            self.parent_selected_student_id = int(student_id)
            self.message("انتخاب دانش‌آموز", "این دانش‌آموز برای عملیات والد انتخاب شد.")
            self._open_parent_children()
        except Exception as exc:
            self.message("انتخاب دانش‌آموز", "انتخاب دانش‌آموز انجام نشد: " + str(exc))

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

    def _message_sender_email(self):
        profile = dict(getattr(self.app_state, "profile", {}) or {})
        email = str(profile.get("email") or "").strip()
        if email:
            return email
        username = str(profile.get("username") or profile.get("national_code") or "").strip()
        if username:
            try:
                rows = self.app_state.api.table_select("account_settings", {"username":"eq."+username, "limit":"1"}) or []
                if rows and rows[0].get("email"):
                    return str(rows[0]["email"]).strip()
            except Exception as exc:
                print("MESSAGE SENDER LOOKUP ERROR:", repr(exc))
        return ""

    def open_message_center(self):
        self.table = "messages"
        self.body.clear_widgets()
        self.title.text = fa_display("صندوق پیام و ارسال پیام")
        root = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(5))
        root.add_widget(self.btn("زیرپنل‌ها", self._back_to_submenus, PRIMARY, dp(40), dp(82)))
        root.add_widget(self.label("ارسال پیام مستقیم", "16sp", PRIMARY, True, "center"))
        receiver = self.field("ایمیل گیرنده", 44, False)
        title = self.field("عنوان پیام", 44, False)
        body = self.field("متن پیام", 110, True)
        root.add_widget(receiver); root.add_widget(title); root.add_widget(body)
        root.add_widget(self.btn("ارسال پیام", lambda *_: self._send_message(receiver, title, body), SUCCESS, dp(46)))
        root.add_widget(self.label("پیام‌های اخیر", "12sp", PRIMARY, True, 34, True))
        self.body.add_widget(root)
        self.area = BoxLayout(orientation="vertical")
        self.body.add_widget(self.area)
        self._load_message_inbox()

    def _send_message(self, receiver, title, body):
        sender = self._message_sender_email()
        target = self.val(receiver)
        subject = self.val(title)
        text_value = self.val(body)
        if not sender:
            raise ValueError("ایمیل حساب فرستنده در پروفایل ثبت نشده است.")
        if not target or "@" not in target:
            raise ValueError("ایمیل گیرنده را وارد کنید.")
        if not subject or not text_value:
            raise ValueError("عنوان و متن پیام الزامی است.")
        payload = {"sender":sender,"receiver":target,"title":subject,"body":text_value,
                   "text":text_value,"audience_type":"direct","audience_value":target,
                   "sender_name":str((getattr(self.app_state,"profile",{}) or {}).get("display_name") or sender)}
        self.insert("messages", payload)
        self.status.text = fa_display("پیام با موفقیت برای گیرنده ارسال شد.")
        self.status.color = SUCCESS
        receiver.text = ""; title.text = ""; body.text = ""
        self._load_message_inbox()

    def _load_message_inbox(self):
        try:
            rows = self.app_state.api.table_select("messages", {"order":"id.desc","limit":"25"}) or []
        except Exception as exc:
            self.area.clear_widgets()
            self.area.add_widget(self.label("دریافت پیام‌ها با خطا روبه‌رو شد: "+str(exc), "10sp", SECONDARY, False, 50, True))
            return
        self.area.clear_widgets()
        self._table(["فرستنده","گیرنده","عنوان","متن","تاریخ"],
                    [[r.get("sender"),r.get("receiver"),r.get("title"),r.get("body"),r.get("created_at")] for r in rows])

    def open_table(self,table,refresh_subbar=True):
        # Student and parent accounts are consumer/read-only roles. Their
        # dashboard exposes only assignments/messages (student) and
        # messages/online-payment (parent). Block legacy/deep links to staff
        # workflows so they can never reach a staff CRUD screen.
        role = self.role()
        logical_table = str(table or "").strip()
        if logical_table in {"messages", "message_targets"}:
            self.open_message_center()
            return self
        # The executive deputy has dedicated workflows for the six operational
        # areas; do not route these to the generic read-only table viewer.
        if role in {"executive", "معاون اجرایی"} and logical_table in {
            "certificate_requests", "report_cards", "class_seat_assignments",
            "exam_seat_assignments", "executive_requests"
        }:
            try:
                from mobile.screens.executive_center import ExecutiveCenterScreen
                name = "executive_center"
                screen = self.manager.get_screen(name) if self.manager and name in self.manager.screen_names else None
                if screen is None and self.manager:
                    screen = ExecutiveCenterScreen(name=name, app_state=self.app_state)
                    self.manager.add_widget(screen)
                if screen is None:
                    raise RuntimeError("مرکز اجرایی آماده نشد.")
                screen.app_state = self.app_state
                routes = {
                    "students": "identity",
                    "certificate_requests": "certificates",
                    "report_cards": "report_cards",
                    "class_seat_assignments": "class_seats",
                    "exam_seat_assignments": "exam_seats",
                    "executive_requests": "requests",
                }
                getattr(screen, routes[logical_table])()
                self.manager.current = name
                return
            except Exception as exc:
                print("EXECUTIVE CENTER OPEN ERROR:", repr(exc))
                self.status.text = fa_display("مرکز اجرایی باز نشد: " + str(exc))
                self.status.color = ERROR
                return
        # Student participation workflows are dedicated screens: they never
        # expose raw database IDs or generic CRUD forms to the student.
        student_registration_modes = {
            "student_competitions": "competitions",
            "student_council_registration": "student_council",
            "student_basij_registration": "basij_registration",
            "student_ally_registration": "school_ally",
            "student_mayor_registration": "school_mayor",
        }
        if role in {"student", "دانش‌آموز"} and logical_table in student_registration_modes:
            try:
                from kivy.app import App
                app = App.get_running_app()
                from mobile.screens.student_activities import StudentActivitiesRegistrationScreen
                name = "student_activities_registration"
                screen = self.manager.get_screen(name) if self.manager and name in self.manager.screen_names else None
                if screen is None and app is not None:
                    screen = StudentActivitiesRegistrationScreen(
                        app_state=(getattr(app, "app_state", None) or self.app_state),
                        mode=student_registration_modes[logical_table],
                        name=name,
                    )
                    self.manager.add_widget(screen)
                if screen is None:
                    raise RuntimeError("محیط ثبت‌نام دانش‌آموز آماده نشد.")
                screen.mode = student_registration_modes[logical_table]
                screen.app_state = (getattr(app, "app_state", None) or self.app_state)
                if self.manager:
                    self.manager.current = name
                return
            except Exception as exc:
                print("STUDENT REGISTRATION OPEN ERROR:", repr(exc))
                self.status.text = fa_display("محیط ثبت‌نام باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                return
        # Parent accounts must never enter the live-class or exam workspaces.
        if role == "parent" and logical_table in {"online","online_classes","virtual","online_class_sessions","teacher_exams","exams","quiz_questions"}:
            self.status.text = fa_display("این بخش برای حساب اولیا فعال نیست.")
            self.status.color = (.75, .18, .18, 1)
            return
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

        if table in ("teacher_exams", "exams", "quiz_questions", "teacher_exam_shares"):
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

        if table in ("meeting_requests", "parent_meeting_requests", "teacher_meetings", "teacher_parent_meetings", "meetings"):
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

        if table == "assignment_submissions" and self.role() in {"student","دانش‌آموز"}:
            try:
                from kivy.app import App
                app = App.get_running_app()
                screen = app.ensure_assignment_submission_workflow() if app is not None else None
                if screen is None:
                    raise RuntimeError("محیط ارسال تکلیف آماده نشد.")
                screen.return_to = "panel"
                if self.manager:
                    self.manager.current = screen.name
                return
            except Exception as exc:
                print("ASSIGNMENT SUBMISSION WORKFLOW ERROR:", repr(exc))
                self.status.text = fa_display("محیط ارسال تکلیف باز نشد: " + str(exc))
                self.status.color = (.8, .15, .15, 1)
                return

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

        # The manager's parent panel is a school-wide directory, not a self-only
        # parent-child view. Render the real linked parent accounts directly.
        if table == "parent_children" and self.role() == "manager":
            self._open_parent_directory()
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
        # Only modules explicitly writable for the active role receive CRUD.
        # Every authenticated role may still use read-only exports where allowed. 
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
                if table == "assignments" and self.role() == "teacher":
                    bar=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(5))
                    bar.add_widget(self.btn("ثبت",_guard_write(lambda: self.editor(table,None)),SUCCESS,dp(38)))
                    bar.add_widget(self.btn("ویرایش",_guard_write(self._edit_selected_row),PRIMARY,dp(38)))
                    bar.add_widget(self.btn("حذف",_guard_write(self._delete_selected_row),(0.72,.16,.18,1),dp(38)))
                    self.body.add_widget(bar)
                    self.status.text=fa_display("ثبت، ویرایش و حذف تکالیف فعال است")
                else:
                    bar=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(82),spacing=dp(4))
                    row1=BoxLayout(size_hint_y=None,height=dp(39),spacing=dp(4))
                    row2=BoxLayout(size_hint_y=None,height=dp(39),spacing=dp(4))
                    row1.add_widget(self.btn("ثبت",_guard_write(lambda: self.editor(table,None)),SUCCESS,dp(38)))
                    row1.add_widget(self.btn("ویرایش",_guard_write(self._edit_selected_row),PRIMARY,dp(38)))
                    row1.add_widget(self.btn("حذف",_guard_write(self._delete_selected_row),(0.72,.16,.18,1),dp(38)))
                    row1.add_widget(self.btn("خروجی اکسل",lambda *_:self.export_excel(),(0.08,.42,.62,1),dp(38)))
                    row2.add_widget(self.btn("ورودی اکسل اطلاعات هویتی" if table == "students" else "ورودی اکسل",_guard_write(self.import_excel),(0.42,.30,.62,1),dp(38)))
                    row2.add_widget(self.btn("قالب Excel",lambda *_:self.export_excel_template(),(0.18,.48,.64,1),dp(38)))
                    row2.add_widget(self.btn("گزارش PDF",lambda *_:self.export_pdf(),(0.50,.28,.58,1),dp(38)))
                    bar.add_widget(row1); bar.add_widget(row2)
                    self.body.add_widget(bar)
                    self.status.text = fa_display("عملیات واقعی فعال است و به پایگاه داده مدرسه متصل است")
        else:
            if not consumer:
                bar=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(5))
                bar.add_widget(self.btn("خروجی اکسل",lambda *_:self.export_excel(),(0.08,.42,.62,1),dp(38)))
                bar.add_widget(self.btn("خروجی PDF",lambda *_:self.export_pdf(),(0.50,.28,.58,1),dp(38)))
                self.body.add_widget(bar)
            self.status.text = fa_display("حالت مشاهده‌ای؛ این بخش فقط برای مشاهده اطلاعات است")
        self.area=BoxLayout(orientation="vertical"); self.body.add_widget(self.area); self.load_table()

    def _excel_path(self):
        """Return a writable private staging path; Android publication is handled by MediaStore."""
        table=str(self.table or "table")
        filename="frahoosh_"+table+".xlsx"
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

    def _publish_excel_android(self, path):
        """Publish a generated XLSX into the user's public Downloads/Frahoosh folder."""
        try:
            from kivy.utils import platform
            if platform != "android":
                return None
            from jnius import autoclass, cast
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            MediaStore = autoclass("android.provider.MediaStore")
            ContentValues = autoclass("android.content.ContentValues")
            BuildVersion = autoclass("android.os.Build$VERSION")
            current = cast("android.app.Activity", PythonActivity.mActivity)
            if int(BuildVersion.SDK_INT) < 29:
                return None

            values = ContentValues()
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, path.name)
            values.put(MediaStore.MediaColumns.MIME_TYPE, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            values.put(MediaStore.MediaColumns.RELATIVE_PATH, "Download/Frahoosh")
            values.put(MediaStore.MediaColumns.IS_PENDING, 1)
            resolver = current.getContentResolver()
            uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
            if uri is None:
                raise RuntimeError("MediaStore نتوانست فایل Excel را ایجاد کند.")
            stream = resolver.openOutputStream(uri)
            if stream is None:
                raise RuntimeError("مسیر خروجی Excel قابل باز شدن نیست.")
            stream.write(path.read_bytes())
            stream.flush()
            stream.close()
            done = ContentValues()
            done.put(MediaStore.MediaColumns.IS_PENDING, 0)
            resolver.update(uri, done, None, None)
            return str(uri.toString())
        except Exception as exc:
            print("ANDROID EXCEL PUBLISH ERROR:", repr(exc))
            return None

    def export_excel(self):
        table=str(self.table or "").strip()
        if not table:
            return
        self.status.text = fa_display("در حال ساخت فایل Excel…")
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
                path=self._excel_path()
                wb.save(str(path))
                published=self._publish_excel_android(path)
                msg="خروجی Excel در پوشه Download/Frahoosh ذخیره شد." if published else f"خروجی Excel ذخیره شد: {path}"
                Clock.schedule_once(lambda *_: self._excel_done(msg),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.write_error("خروجی Excel انجام نشد: "+str(exc)),0)
        Thread(target=work,daemon=True).start()

    def export_excel_template(self):
        """Create a ready-to-fill Excel template using the exact module field contract."""
        table=str(self.table or "").strip()
        if not table:
            return
        self.status.text = fa_display("در حال ساخت قالب Excel…")
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
                published=self._publish_excel_android(template)
                msg="قالب Excel در پوشه Download/Frahoosh ذخیره شد." if published else "قالب Excel آماده شد: "+str(template)
                Clock.schedule_once(lambda *_: self._excel_done(msg),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.write_error("ساخت قالب Excel انجام نشد: "+str(exc)),0)
        Thread(target=work,daemon=True).start()

    def export_pdf(self):
        table=str(self.table or "").strip()
        if not table:
            return
        self.status.text = fa_display("در حال ساخت گزارش PDF…")
        def work():
            try:
                from mobile.services.document_service import export_table_pdf
                rows=self.app_state.api.table_select(table,{"limit":"2000"}) or []
                rows=[dict(x) for x in rows if isinstance(x,dict)]
                fields=[f for f in (_module_fields(table) or []) if f not in HIDDEN]
                if not fields and rows:
                    fields=[k for k in rows[0] if k not in HIDDEN]
                # Save PDF reports beside Excel exports in Download.
                output=self._excel_path().parent
                output.mkdir(parents=True,exist_ok=True)
                path=output/("frahoosh_"+table+"_report.pdf")
                export_table_pdf(table,rows,fields,COLUMNS,str(path),title=FRIENDLY.get(table,table))
                Clock.schedule_once(lambda *_: self._excel_done("گزارش PDF ذخیره شد: "+str(path)),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.write_error("گزارش PDF انجام نشد: "+str(exc)),0)
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
                    Clock.schedule_once(lambda *_: self.write_error("انتخاب فایل Excel لغو شد."), 0)
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
                        lambda *_: self.write_error("خواندن فایل Excel انجام نشد: " + str(exc)), 0
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
        self.status.text = fa_display("در حال خواندن فایل Excel و ثبت گروهی…")
        if table in ("users", "account_settings"):
            def bulk_work():
                try:
                    from openpyxl import load_workbook
                    wb=load_workbook(str(path),read_only=True,data_only=True)
                    ws=wb.active; values=list(ws.iter_rows(values_only=True))
                    wb.close()
                    if not values: raise RuntimeError("فایل Excel خالی است.")
                    headers=[str(x or "").strip() for x in values[0]]
                    reverse={str(v):k for k,v in COLUMNS.items()}
                    fields=[reverse.get(h,h) for h in headers]
                    people=[]
                    for row in values[1:]:
                        p={}
                        for i,value in enumerate(row):
                            if i<len(fields) and fields[i] and value not in (None,""):
                                p[fields[i]]=self._payload_value(fields[i],value)
                        if p: people.append(p)
                    if not people: raise RuntimeError("هیچ رکوردی برای ورود پیدا نشد.")
                    result=self.app_state.api.invoke_function("bulk-import-users",{"people":people})
                    ok=int(result.get("succeeded",0) or 0); bad=int(result.get("failed",0) or 0)
                    Clock.schedule_once(lambda *_: self._excel_done(f"ورود گروهی انجام شد: {ok} موفق، {bad} خطا."),0)
                except Exception as exc:
                    Clock.schedule_once(lambda *_: self.write_error("ورود گروهی کاربران انجام نشد: "+str(exc)),0)
            Thread(target=bulk_work,daemon=True).start()
            return

        def work():
            try:
                from openpyxl import load_workbook
                wb=load_workbook(str(path),read_only=True,data_only=True)
                ws=wb.active
                values=list(ws.iter_rows(values_only=True))
                if not values:
                    raise RuntimeError("فایل Excel خالی است.")
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
                Clock.schedule_once(lambda *_: self._excel_done(f"{inserted} رکورد از Excel وارد شد."),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.write_error("ورودی Excel انجام نشد: "+str(exc)),0)

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
                self.status.text = fa_display("فایل Excel را انتخاب کنید…")
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
                    "ورودی Excel",
                    f"برای ثبت گروهی، فایل Excel را انتخاب کنید.\n"
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
                if table == "messages" and safe_rows:
                    username = str((getattr(self.app_state, "profile", {}) or {}).get("username") or "").strip()
                    if username:
                        for message in safe_rows:
                            mid = message.get("id")
                            if mid is not None:
                                try:
                                    api.table_insert("message_reads", {"message_id": mid, "username": username, "seen_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}, return_representation=False)
                                except Exception as read_exc:
                                    print("MESSAGE READ RECEIPT ERROR:", repr(read_exc))
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
            # label() is the single canonical RTL rendering boundary. Do not
            # pre-shape the value here or Persian text gets bidi-shaped twice.
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

    def _relationship_options(self, table, field, existing):
        """Build real foreign-key choices so modules connect by IDs, not free text."""
        relation_tables = {
            "student_id": "students", "teacher_id": "teachers",
            "assignment_id": "assignments", "exam_id": "teacher_exams", "quiz_id": "teacher_exams",
            "activity_id": "activity_offers", "offer_id": "payment_offers", "question_id": "quiz_questions",
            "attempt_id": "teacher_exam_attempts", "message_id": "messages",
        }
        table_specific = {
            "class_id": {
                "online_class_sessions": "online_classes",
                "online_class_students": "online_classes",
                "online_class_teachers": "online_classes",
                "online_attendance": "online_classes",
                "online_class_activity": "online_classes",
                "online_class_ai_reports": "online_classes",
                "online_class_notifications": "online_classes",
                "online_presence_checks": "online_classes",
                "smart_board_content": "online_classes",
                "smart_board_whiteboards": "online_classes",
                "smart_board_files": "online_classes",
                "smart_board_media": "online_classes",
                "smart_board_interactive_tools": "online_classes",
                "smart_board_quizzes": "online_classes",
                "smart_board_activities": "online_classes",
            }
        }
        table = (table_specific.get(field, {}).get(table) if field in table_specific else relation_tables.get(field))
        if not table:
            return None
        try:
            rows = self.app_state.api.table_select(table, {"limit": "200", "order": "id.asc"}) or []
        except Exception as exc:
            print("RELATION OPTIONS ERROR:", field, repr(exc))
            rows = []
        if not rows:
            return None

        def display(row):
            rid = row.get("id")
            if field == "student_id":
                name = f"{row.get('first_name','')} {row.get('last_name','')}".strip() or row.get("student_name") or "دانش‌آموز"
                tail = row.get("class_name") or row.get("grade") or ""
            elif field == "teacher_id":
                name = f"{row.get('first_name','')} {row.get('last_name','')}".strip() or row.get("teacher_name") or "دبیر"
                tail = row.get("subject") or ""
            elif field == "class_id":
                name = row.get("title") or "کلاس آنلاین"
                tail = f"{row.get('teacher','')} {row.get('subject','')}".strip()
            elif field in {"assignment_id"}:
                name = row.get("title") or "تکلیف"
                tail = row.get("subject") or ""
            elif field in {"exam_id","quiz_id"}:
                name = row.get("title") or "آزمون"
                tail = row.get("subject") or ""
            elif field == "activity_id":
                name = row.get("title") or "فعالیت"
                tail = row.get("category") or ""
            elif field == "offer_id":
                name = row.get("title") or "گزینه پرداخت"
                tail = row.get("amount") or ""
            elif field == "question_id":
                name = row.get("question") or "سؤال"
                tail = row.get("question_type") or ""
            elif field == "attempt_id":
                name = f"تلاش آزمون #{rid}"
                tail = row.get("student_username") or row.get("status") or ""
            else:
                name = row.get("title") or f"رکورد #{rid}"
                tail = row.get("status") or ""
            return f"#{rid} | {name}" + (f" | {tail}" if str(tail or "").strip() else "")

        labels = [display(r) for r in rows if r.get("id") is not None]
        mapping = {}
        for row, label in zip([r for r in rows if r.get("id") is not None], labels):
            mapping[label] = row.get("id")
            mapping[fa_display(label)] = row.get("id")
        current = str(existing or "").strip()
        selected = next((label for label, value in mapping.items() if str(value) == current), labels[0] if labels else "")
        return labels, selected, mapping

    def editor(self,table,row):
        # The shared ZIP/Web contract is authoritative for forms too. This prevents
        # a module from silently falling back to decorative fields.
        canonical = list(_module_fields(table) or [])
        fields=[k for k in (canonical or FORMS.get(table) or self._infer(row)) if k not in HIDDEN]
        # Never expose internal metadata or an unknown placeholder as a form field.
        fields=[k for k in fields if k and k not in {"password","school_id"}]
        root=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(6)); sc=ScrollView(do_scroll_x=False); form=GridLayout(cols=1,spacing=dp(5),size_hint_y=None); form.bind(minimum_height=form.setter('height')); inputs={}
        spinner_values = {
            "module_key": ("activity_registrations","student_council","school_mayor","school_ally","basij_registration","certificate_requests","parent_children","transport_requests","parent_activities","survey_responses","teacher_exams","online_classes"),
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
            relation = self._relationship_options(table, f, existing)
            if relation:
                relation_labels, relation_selected, relation_map = relation
                ti = PersianSpinner(
                    text=relation_selected,
                    values=tuple(relation_labels),
                    font_name=font_name(),
                    font_size="11sp",
                    size_hint_y=None,
                    height=dp(44),
                )
                ti._frahoosh_relation_map = relation_map
            elif f in spinner_values:
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
            relation_map = getattr(widget, "_frahoosh_relation_map", None)
            if relation_map and raw in relation_map:
                raw = str(relation_map[raw])
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
                    # Management/deputies control which student/parent workflows are open.
                    if table == "module_activations":
                        if str(role).lower() not in {"manager","educational","executive","cultural"}:
                            raise RuntimeError("فقط مدیریت و معاونان مجاز به فعال‌سازی قابلیت‌ها هستند.")
                        from datetime import datetime, timezone
                        payload["activated_at"] = payload.get("activated_at") or datetime.now(timezone.utc).isoformat()
                        auth_id = profile.get("auth_user_id") or profile.get("user_id")
                        if auth_id:
                            payload["activated_by"] = auth_id
                    consumer_activation = {
                        "activity_registrations":"activity_registrations",
                        "cultural_activity_registrations":"activity_registrations",
                        "student_council":"student_council",
                        "school_mayor":"school_mayor",
                        "school_ally":"school_ally",
                        "basij_registration":"basij_registration",
                        "certificate_requests":"certificate_requests",
                        "transport_requests":"transport_requests",
                        "parent_activities":"parent_activities",
                        "parent_children":"parent_children",
                        "survey_responses":"survey_responses",
                        "teacher_exams":"teacher_exams",
                        "online_classes":"online_classes",
                    }
                    if role in ("student","دانش‌آموز","parent","parents","ولی","اولیا") and table in consumer_activation:
                        activation_key = consumer_activation[table]
                        active_rows = api.rpc("is_module_active", {"p_module_key": activation_key})
                        active = bool(active_rows if isinstance(active_rows, bool) else (active_rows[0] if isinstance(active_rows,list) and active_rows else active_rows))
                        if not active:
                            raise RuntimeError("این قابلیت هنوز توسط مدیریت یا معاون مربوطه فعال نشده است.")
                    if role in ("teacher", "دبیر", "معلم") and table in {"grades","student_grades","attendance","assignments","discipline_records","teacher_exams","lesson_plans","teacher_activities"}:
                        tid = profile.get("linked_teacher_id") or profile.get("teacher_id")
                        if tid and not payload.get("teacher_id"):
                            payload["teacher_id"] = tid
                    if role in ("student","دانش‌آموز") and table in {"student_grades","attendance","assignments","assignment_submissions","discipline_records","student_council","basij_registration","school_ally","school_mayor","certificate_requests","student_referrals","activity_registrations","cultural_activity_registrations"}:
                        sid = profile.get("linked_student_id") or profile.get("student_id")
                        if sid and not payload.get("student_id"):
                            payload["student_id"] = sid
                    if role in ("parent","parents","ولی","اولیا"):
                        username = profile.get("national_code") or profile.get("username") or profile.get("email")
                        if username and not payload.get("parent_username") and table in {"parent_activities","transport_requests","payment_attempts","parent_meeting_requests","parent_children"}:
                            payload["parent_username"] = username
                        if username and table == "survey_responses":
                            from datetime import datetime, timezone
                            payload["respondent_username"] = username
                            payload["respondent_role"] = "parent"
                            payload["submitted_at"] = payload.get("submitted_at") or datetime.now(timezone.utc).isoformat()
                        # Parent-facing workflows must always carry a real child relationship.
                        if table in {"transport_requests","payment_attempts","meeting_requests","parent_meeting_requests"} and not payload.get("student_id"):
                            try:
                                if self.parent_selected_student_id:
                                    payload["student_id"] = self.parent_selected_student_id
                                else:
                                    links = api.table_select("parent_children", {"parent_username":f"eq.{username}","limit":"50"}) or []
                                    if links:
                                        payload["student_id"] = links[0].get("student_id")
                            except Exception as rel_exc:
                                print("PARENT CHILD RELATION SAVE ERROR:", repr(rel_exc))
                    # Fill backend-required audit/link fields that are not user inputs.
                    from datetime import datetime, timezone
                    now_iso = datetime.now(timezone.utc).isoformat()
                    if table in {"discipline_records","online_class_sessions","online_class_ai_reports","online_class_notifications","online_presence_checks","parent_meetings","surveys","discipline_items"}:
                        payload.setdefault("created_at", now_iso)
                    if table == "discipline_settings":
                        payload.setdefault("updated_at", now_iso)
                    if table == "survey_responses":
                        payload.setdefault("submitted_at", now_iso)
                    if table == "message_targets":
                        payload.setdefault("target_type", payload.get("target_role") or payload.get("target_name") or "role")
                        payload.setdefault("created_at", now_iso)
                    if table == "finance_accounts":
                        payload.setdefault("title", payload.get("description") or payload.get("account_type") or "حساب مدرسه")
                    if table == "payment_offers":
                        payload.setdefault("target_type", payload.get("category") or "school")
                    if table == "backup_records" and not payload.get("file_path"):
                        raise RuntimeError("برای پشتیبان‌گیری باید فایل واقعی انتخاب و بارگذاری شود.")
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

# UI contract: module categories intentionally use the same vertical accordion pattern as dashboard panels.

# FINAL PROFESSIONAL MODULE CARD OVERRIDE
# Module entries are deliberately mini-panels, not plain list rows.
# The category itself remains the accordion: category -> professional module cards.
class ModuleItemCard(ButtonBehavior, BoxLayout):
    """Professional module card using the same visual language as PanelCard."""
    def __init__(self, label, route, module_enter, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(0),
            size_hint_y=None,
            height=dp(112),
            **kwargs,
        )
        self.route = route
        self.module_enter = module_enter

        with self.canvas.before:
            Color(0.045, 0.11, 0.20, 0.98)
            self.bg = RoundedRectangle(radius=[dp(20)])
        self.bind(pos=self._sync, size=self._sync)

        # Same 64dp professional header language as PanelCard.
        self.header = Button(
            text=fa_display(f"ورود به ماژول  |  {label}"),
            font_name=font_name(),
            font_size="15.5sp",
            background_normal="",
            background_color=(0.055, 0.20, 0.34, 1),
            color=WHITE,
            bold=True,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(64),
        )
        self.header.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.header.bind(on_release=self._open)
        self.add_widget(self.header)

        # Keep the second line identical in structure to PanelCard's meta line,
        # but make it useful: every module is explicitly identified as operational.
        self.meta = Label(
            text=fa_display("ماژول عملیاتی  •  برای ورود لمس کنید"),
            font_name=font_name(),
            font_size="10sp",
            color=(0.60, 0.82, 0.96, 1),
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(30),
        )
        self.meta.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.add_widget(self.meta)

    def _open(self, *_):
        self.module_enter(self.route)

    def on_release(self):
        self.module_enter(self.route)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size
