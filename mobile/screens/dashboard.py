from kivy.metrics import dp, Metrics
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.app import App
from pathlib import Path
from threading import Thread
import json

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, BACKGROUND_PATH, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, title_font_name, rtl_text, fa_display, bundled_login_background

def _android_navigation_inset_dp():
    """Return the Android navigation-bar inset in Kivy dp units.

    Kivy 2.3.1 does not expose Window.safe_area, so read the real Android
    WindowInsets when available and keep a conservative fallback for older
    devices/desktop preview. This keeps the fixed footer above the system bar.
    """
    fallback = dp(24)
    try:
        from kivy.utils import platform
        if platform != "android":
            return dp(8)
        from jnius import autoclass
        Build = autoclass("android.os.Build")
        Activity = autoclass("org.kivy.android.PythonActivity")
        activity = Activity.mActivity
        decor = activity.getWindow().getDecorView()
        sdk = int(Build.VERSION.SDK_INT)
        inset_px = 0
        root_insets = decor.getRootWindowInsets()
        if root_insets is not None:
            if sdk >= 30:
                WindowInsetsType = autoclass("android.view.WindowInsets$Type")
                inset = root_insets.getInsetsIgnoringVisibility(
                    WindowInsetsType.navigationBars()
                )
                inset_px = int(inset.bottom)
            elif sdk >= 20:
                inset_px = int(root_insets.getSystemWindowInsetBottom())
        if inset_px > 0:
            return max(dp(8), inset_px / float(Metrics.density or 1.0))
    except Exception:
        pass
    return fallback


ROLE_ALIASES = {
    "admin":"manager","administrator":"manager","manager":"manager","مدیر":"manager","مدیریت":"manager",
    "executive":"executive","معاون اجرایی":"executive","educational":"educational","معاون آموزشی":"educational",
    "cultural":"cultural","پرورشی":"cultural","معاون پرورشی":"cultural","advisor":"advisor","counselor":"advisor","مشاور":"advisor",
    "teacher":"teacher","teacher_staff":"teacher","دبیر":"teacher","معلم":"teacher","student":"student","دانش‌آموز":"student","دانش آموز":"student",
    "parent":"parent","parent_guardian":"parent","guardian":"parent","ولی":"parent","اولیا":"parent"
}
ROLE_TITLES = {
    "manager":"مدیریت","executive":"معاون اجرایی","educational":"معاون آموزشی","cultural":"معاون پرورشی",
    "advisor":"مشاوره","teacher":"دبیر","student":"دانش‌آموز","parent":"ولی"
}

MOTHER_PANEL_CATALOG = {
    "manager": {"title":"مدیریت","items":[["مدیریت کاربران و کارکنان","users"],["کلاس آنلاین","online_classes"],["برنامه هفتگی و برنامه امتحانات","weekly_schedule"],["گزارش‌ها و آمار","reports"],["تنظیمات مدرسه","school_profile"]]},
    "executive": {"title":"معاونت اجرایی","items":[["دانش‌آموزان","students"],["کلاس‌ها","school_class_config"],["کارکنان","staff"],["پرونده‌ها","students"],["امور اجرایی","discipline_records"],["گزارش‌ها","reports"]]},
    "educational": {"title":"معاونت آموزشی","items":[["حضور و غیاب","attendance"],["ارجاعات آموزشی","educational_followups"],["جلسات","meeting_requests"],["اطلاع‌رسانی","messages"],["امتحانات","teacher_exams"],["بانک سؤال","teacher_exams"],["گزارش‌های آموزشی","ai_smart_reports"]]},
    "cultural": {"title":"معاونت پرورشی","items":[["فعالیت‌های فرهنگی","educational_activities"],["مسابقات","cultural_competitions"],["برنامه‌های پرورشی","educational_activities"],["ثبت‌نام فعالیت‌ها","activity_registrations"],["گزارش‌های پرورشی","cultural_reports"]]},
    "advisor": {"title":"مشاور","items":[["پرونده مشاوره","counseling_records"],["جلسات","meeting_requests"],["پیگیری دانش‌آموز","counseling_followups"],["ارجاعات","student_referrals"],["هدایت تحصیلی","counseling_guidance"],["گزارش مشاوره","ai_smart_reports"]]},
    "teacher": {"title":"دبیران","items":[["کلاس‌های من","teacher_classes"],["کلاس آنلاین","online"],["نمرات و کارنامه","student_grades"],["تکالیف","assignments"],["حضور و غیاب","attendance"],["آزمون‌ها","teacher_exams"],["طرح درس","lesson_plans"],["جلسات","meeting_requests"],["گزارش‌ها","reports"]]},
    "student": {"title":"دانش‌آموزان","items":[["آموزش من","students"],["حضور و غیاب","attendance"],["نمرات و کارنامه","student_grades"],["برنامه هفتگی","weekly_schedule"],["برنامه امتحانات","exam_schedule"],["آزمون‌ها","teacher_exams"],["تکالیف","assignment_submissions"],["درخواست گواهی","certificate_requests"],["فعالیت‌های مدرسه","activity_registrations"],["صندوق پیام","messages"]]},
    "parent": {"title":"اولیا","items":[["فرزند من","parent_children"],["اطلاعات دانش‌آموز","students"],["حضور و غیاب","attendance"],["نمرات و کارنامه","student_grades"],["برنامه هفتگی","weekly_schedule"],["برنامه امتحانات","exam_schedule"],["انضباط","discipline_records"],["ملاقات و ارتباط","parent_meeting_requests"],["صندوق پیام","messages"],["پرداخت و خدمات","payment_records"],["فعالیت‌های اولیا","parent_activities"]]},
    "finance": {"title":"مالی","items":[["پرداخت‌ها","payment_records"],["تراکنش‌ها","finance_transactions"],["حساب‌ها","finance_accounts"],["گزارش مالی","reports"],["تعریف گزینه پرداخت","payment_offers"]]},
    "smart_board": {"title":"تابلو هوشمند","items":[["تخته آموزشی","smart_board_whiteboards"],["فایل‌ها","smart_board_content"],["تصاویر و ویدئوها","smart_board_media"],["ابزارهای تعاملی","smart_board_activities"]]},
    "online": {"title":"کلاس آنلاین","items":[["کلاس‌های آنلاین","online_classes"],["جلسات","online_class_sessions"],["دانش‌آموزان کلاس","online_class_students"],["دبیران کلاس","online_class_teachers"],["حضور آنلاین","online_attendance"],["تخته کلاس","smart_board_whiteboards"]]},
    "teacher_exams": {"title":"آزمون آنلاین","items":[["آزمون‌های آنلاین","teacher_exams"],["بانک سؤال","quiz_questions"],["زمان‌بندی آزمون","exam_schedule"]]},
    "ai": {"title":"هوش مصنوعی","items":[["دستیار هوشمند","ai_assistant_sessions"],["تحلیل آموزشی","ai_smart_reports"],["گزارش هوشمند","ai_smart_reports"],["پرسش و پاسخ","ai_questions"]]},
    "reports": {"title":"گزارش‌ها","items":[["کارنامه‌ها","report_cards"],["نمرات","student_grades"],["حضور و غیاب","attendance"],["گزارش آموزشی هوشمند","ai_smart_reports"],["گزارش اجرایی","executive_reports"]]},
    "schedule": {"title":"برنامه هفتگی","items":[["برنامه هفتگی","weekly_schedule"],["برنامه امتحانات","exam_schedule"],["چیدمان صندلی کلاس","class_seat_assignments"],["چیدمان صندلی آزمون","exam_seat_assignments"]]},
    "settings": {"title":"تنظیمات","items":[["تنظیمات حساب","account_settings"],["تنظیمات مدرسه","school_profile"],["پشتیبان‌گیری","account_settings"]]}
}

def _load_mother_panel_catalog():
    # The shared v16.12 ZIP-backed catalog is the single source of truth.
    # Do not use the reduced legacy mother_panel_catalog.json for navigation.
    candidates = [
        Path(__file__).resolve().parents[2] / "shared" / "module_catalog.json",
        Path.cwd() / "shared" / "module_catalog.json",
    ]
    try:
        for path in candidates:
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
                panels = data.get("panels") or {}
                if panels:
                    aliases = {"manager":"management","teacher":"teachers","student":"students","parent":"parents"}
                    return {
                        key: {"title": key, "items": panels.get(source, [])}
                        for key, source in {**{k:k for k in panels}, **aliases}.items()
                        if source in panels
                    }
    except Exception as exc:
        print("SHARED MODULE CATALOG ERROR:", repr(exc))
    return MOTHER_PANEL_CATALOG

MOTHER_PANEL_CATALOG = _load_mother_panel_catalog()


class PanelIcon(Widget):
    """Vector icon: no font glyphs, so it can never become a square."""
    def __init__(self, route, **kwargs):
        super().__init__(**kwargs)
        self.route = route or "about"
        self.size_hint_y = None
        self.height = dp(62)
        from kivy.graphics import Ellipse, Line
        with self.canvas:
            Color(0.08, 0.55, 0.85, 1)
            self.badge = Ellipse()
            Color(1, 1, 1, 1)
            self.stroke = Line(width=1.8)
            self.shape = Line(width=2.2)
        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *_):
        cx, cy = self.center
        r = min(self.width, self.height) * .34
        self.badge.pos = (cx-r, cy-r)
        self.badge.size = (2*r, 2*r)
        self.stroke.circle = (cx, cy, r)
        self.shape.points = self._points(cx, cy, r*.62)

    def _points(self, cx, cy, s):
        import math
        rt = self.route
        if rt in ("management", "settings"):
            pts=[]
            for i in range(8):
                a=i*math.pi/4
                pts += [cx+s*math.cos(a), cy+s*math.sin(a),
                        cx+s*.42*math.cos(a), cy+s*.42*math.sin(a)]
            return pts
        if rt in ("educational", "teachers", "students"):
            return [cx-s,cy-s*.45,cx,cy-s,cx+s,cy-s*.45,cx+s,cy+s*.7,
                    cx,cy+s,cx-s,cy+s*.7,cx-s,cy-s*.45,cx,cy]
        if rt in ("executive", "finance", "payment"):
            return [cx-s,cy-s*.45,cx+s,cy-s*.45,cx+s,cy+s*.7,cx-s,cy+s*.7,
                    cx-s,cy-s*.45,cx-s*.35,cy-s*.75,cx+s*.35,cy-s*.75]
        if rt in ("advisor", "parents"):
            return [cx,cy+s*.45,cx-s*.38,cy+s*.05,cx-s*.62,cy-s*.7,
                    cx+s*.62,cy-s*.7,cx+s*.38,cy+s*.05,cx,cy+s*.45]
        if rt in ("cultural", "about"):
            return [cx,cy+s,cx+s*.25,cy+s*.28,cx+s,cy+s*.18,cx+s*.42,cy-s*.15,
                    cx+s*.58,cy-s*.8,cx,cy-s*.35,cx-s*.58,cy-s*.8,
                    cx-s*.42,cy-s*.15,cx-s,cy+s*.18,cx-s*.25,cy+s*.28,cx,cy+s]
        if rt in ("online", "smart_board"):
            return [cx-s,cy-s*.7,cx+s,cy-s*.7,cx+s,cy+s*.45,cx-s,cy+s*.45,
                    cx-s,cy-s*.7,cx-s*.2,cy-s,cx+s*.2,cy-s]
        if rt in ("teacher_exams", "reports", "schedule"):
            return [cx-s*.75,cy+s,cx-s*.75,cy-s*.75,cx+s*.75,cy-s*.75,
                    cx+s*.75,cy+s,cx-s*.75,cy+s]
        if rt == "messages":
            return [cx-s,cy+s*.45,cx+s,cy+s*.45,cx+s,cy-s*.45,cx+s*.2,cy-s*.45,
                    cx-s*.15,cy-s,cx-s*.15,cy-s*.45,cx-s,cy+s*.45]
        return [cx-s,cy,cx+s,cy,cx,cy-s,cx,cy+s]

class PanelCard(BoxLayout):
    """Static expandable panel card. Tapping the header reveals its real modules."""
    def __init__(self, title, index, total, desc, enter, route=None, modules=None, module_enter=None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(0), size_hint_y=None, **kwargs)
        self.title_text = title
        self.route = route or "about"
        self.desc_text = desc
        self.enter = enter
        self.modules = modules or []
        self.module_enter = module_enter or enter
        self.expanded = False
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
            text=fa_display(f"پنل {index} از {total}  -  {len(self.modules)} ماژول"),
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

        self.body = BoxLayout(orientation="vertical", spacing=dp(6), padding=[dp(2), dp(4)], size_hint_y=None)
        self.body.height = 0
        self.add_widget(self.body)

        self._build_modules()
        self._set_expanded(False)

    def _build_modules(self):
        self.body.clear_widgets()
        for category, items in self.modules:
            if category:
                head = Label(
                    text=fa_display(category),
                    font_name=font_name(),
                    font_size="13sp",
                    color=(0.55, 0.82, 1, 1),
                    bold=True,
                    halign="right",
                    valign="middle",
                    size_hint_y=None,
                    height=dp(34),
                )
                head.bind(size=lambda o, v: setattr(o, "text_size", v))
                self.body.add_widget(head)
            for label, route in items:
                button = Button(
                    text=fa_display(f"  {label}"),
                    font_name=font_name(),
                    font_size="12.5sp",
                    background_normal="",
                    background_color=(0.08, 0.16, 0.25, 1),
                    color=WHITE,
                    halign="right",
                    valign="middle",
                    size_hint_y=None,
                    height=dp(46),
                )
                button.bind(size=lambda o, v: setattr(o, "text_size", v))
                button.bind(on_release=lambda *_a, r=route: self.module_enter(r))
                self.body.add_widget(button)

    def toggle(self):
        self._set_expanded(not self.expanded)

    def _set_expanded(self, value):
        self.expanded = bool(value)
        if self.expanded:
            self.header.text = fa_display(f"بستن  |  {self.title_text}")
            self.body.height = sum(w.height for w in self.body.children) + max(0, len(self.body.children)-1) * dp(6) + dp(8)
            self.height = dp(64) + dp(30) + self.body.height + dp(10)
        else:
            self.header.text = fa_display(f"باز کردن  |  {self.title_text}")
            self.body.height = 0
            self.height = dp(64) + dp(30) + dp(10)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size

PANEL_HUBS = [
    ("مدیریت","management"),
    ("معاون اجرایی","executive"),
    ("معاون آموزشی","educational"),
    ("معاون پرورشی","cultural"),
    ("مشاوره","advisor"),
    ("دبیران","teachers"),
    ("اولیا","parents"),
    ("دانش‌آموز","students"),
    ("مالی","finance"),
    ("تابلو هوشمند","smart_board"),
    ("هوش مصنوعی","ai"),
    ("کلاس‌های آنلاین","online"),
    ("آزمون آنلاین","teacher_exams"),
    ("گزارش‌ها","reports"),
    ("برنامه هفتگی","schedule"),
    ("صندوق پیام‌ها","messages"),
    ("تنظیمات","settings"),
    ("درباره برنامه","about"),
]
STUDENT_ALLOWED_PANELS = {"students"}
PARENT_ALLOWED_PANELS = {"parents"}

# Professional module grouping. Route IDs stay canonical; only presentation changes.
MODULE_CATEGORY_GROUPS = {
    "management": [
        ("فعالیت آموزشی", {"grades","report_cards","class_seat_assignments","exam_seat_assignments","exam_schedule","weekly_schedule","online_classes","school_class_config"}),
        ("فعالیت‌های پرورشی", {"educational_activities","cultural_competitions","activity_registrations","student_council","basij_registration","school_mayor","morning_ceremony","activity_programs","cultural_activity_registrations"}),
        ("دانش‌آموزان و پرونده‌ها", {"students","archive_items","certificates","student_cards","parent_children","discipline_records"}),
        ("دبیران و کارکنان", {"teachers","staff"}),
        ("کلاس و مدرسه", {"class_cards","assets","school_events"}),
        ("ارتباطات", {"messages","meeting_requests"}),
        ("مالی", {"payment_records","finance_transactions","finance_accounts","payment_offers"}),
        ("گزارش‌ها و آمار", {"ai_smart_reports","surveys"}),
        ("مدیریت سامانه", {"users","school_profile","module_activations"}),
    ],
    "executive": [
        ("امور دانش‌آموزی", {"students","archive_items","student_cards","certificates","report_cards"}),
        ("کلاس و برنامه‌ریزی", {"executive_classes","class_cards","class_seat_assignments","exam_seat_assignments","weekly_schedule","exam_schedule"}),
        ("امور کارکنان", {"staff"}),
        ("امور اجرایی", {"executive_operations","executive_requests"}),
        ("کلاس آنلاین و ارتباطات", {"online_classes","messages"}),
        ("گزارش‌ها", {"executive_reports"}),
    ],
    "educational": [
        ("برنامه‌ریزی آموزشی", {"attendance","online_classes","exam_schedule","quiz_questions","grade_items"}),
        ("ارزشیابی و آزمون", {"quiz_questions","exam_schedule","grade_items"}),
        ("پیگیری آموزشی", {"student_referrals","educational_followups","academic_followups","discipline_records"}),
        ("ارتباطات", {"meeting_requests","messages","message_targets"}),
        ("گزارش‌های آموزشی", {"ai_smart_reports"}),
        ("فعالیت‌های آموزشی", {"khwarizmi_registrations","module_activations"}),
    ],
    "cultural": [
        ("فعالیت‌های پرورشی", {"morning_ceremony","activity_programs","educational_activities","activity_programs"}),
        ("مسابقات و جشنواره‌ها", {"cultural_competitions","art_competitions","sport_competitions","khwarizmi_registrations"}),
        ("تشکل‌های دانش‌آموزی", {"student_council","basij_registration","school_mayor","morning_leaders","qari_registration"}),
        ("گزارش و انضباط", {"cultural_reports","discipline_records"}),
        ("ارتباطات", {"messages","message_targets"}),
        ("تنظیم قابلیت‌ها", {"module_activations"}),
    ],
    "advisor": [
        ("پرونده مشاوره", {"counseling_records","counseling_followups","student_referrals"}),
        ("جلسات و خانواده", {"parent_meetings","parent_activities","counseling_classes"}),
        ("هدایت تحصیلی", {"counseling_guidance"}),
        ("گزارش‌ها", {"ai_smart_reports","discipline_records"}),
        ("ارتباطات", {"messages","message_targets"}),
    ],
    "teachers": [
        ("کلاس و تدریس", {"teacher_classes","lesson_plans","grade_items"}),
        ("ارزشیابی", {"grades","student_grades","teacher_exams","quiz_questions","teacher_exam_shares"}),
        ("تکالیف", {"assignments","assignment_submissions"}),
        ("کلاس آنلاین", {"online_classes","online_class_sessions","online_class_students","online_class_teachers","online_attendance"}),
        ("ارتباط با اولیا", {"teacher_meetings","teacher_parent_meetings"}),
        ("پیگیری دانش‌آموز", {"student_referrals","discipline_records"}),
        ("ارتباطات", {"messages","message_targets"}),
        ("گزارش‌ها", {"teacher_activities"}),
    ],
    "parents": [
        ("فرزند من", {"parent_children","students","student_grades","attendance","monthly_report_cards","report_cards","discipline_records"}),
        ("آموزش و برنامه", {"weekly_schedule","exam_schedule","teacher_exams"}),
        ("ملاقات و ارتباط", {"parent_meeting_requests","teacher_parent_meetings","messages"}),
        ("پرداخت و خدمات", {"payment_records","transport_requests"}),
        ("فعالیت‌های اولیا", {"parent_activities","survey_responses"}),
    ],
    "students": [
        ("آموزش من", {"students","student_class_info","attendance","student_grades","weekly_schedule","exam_schedule","class_seat_assignments","exam_seat_assignments","report_cards","teacher_exams"}),
        ("تکالیف", {"assignments","assignment_submissions"}),
        ("فعالیت‌های مدرسه", {"activity_registrations","student_council","basij_registration","school_ally","school_mayor"}),
        ("درخواست‌ها", {"certificate_requests"}),
        ("ارتباطات", {"messages"}),
    ],
    "finance": [
        ("دریافت‌ها و پرداخت‌ها", {"payment_records","payment_offers","finance_transactions"}),
        ("حساب‌ها", {"finance_accounts"}),
        ("گزارش مالی", {"finance_transactions"}),
    ],
    "smart_board": [
        ("تابلو و محتوای آموزشی", {"smart_board_whiteboards","smart_board_content","smart_board_files","smart_board_media"}),
        ("ابزارهای تعاملی", {"smart_board_interactive_tools","smart_board_activities","smart_board_quizzes"}),
    ],
    "ai": [
        ("دستیار هوشمند", {"ai_assistant_sessions","ai_questions"}),
        ("تحلیل و گزارش", {"ai_educational_analysis","ai_smart_reports"}),
    ],
    "messages": [
        ("صندوق پیام‌ها", {"messages","message_targets","message_reads"}),
    ],
    "settings": [
        ("حساب و مدرسه", {"account_settings","school_profile"}),
        ("پشتیبان‌گیری", {"backup_records"}),
    ],
    "about": [],
}

PANEL_MODULE_SOURCE = {
    "management":"management", "educational":"educational", "executive":"executive",
    "cultural":"cultural", "advisor":"advisor", "teachers":"teachers",
    "parents":"parents", "students":"students", "staff":"staff", "finance":"finance",
    "smart_board":"smart_board", "online":"online", "ai":"ai", "messages":"messages",
    "teacher_exams":"teacher_exams", "payment":"payment"
}

class PanelHubScreen(Screen):
    def __init__(self, app_state=None, panel_key="students", **kwargs):
        super().__init__(**kwargs)
        self.app_state=app_state
        self.panel_key=panel_key
        self._build()
        # Render the mother modules immediately as well as on every entry.
        # This avoids relying on ScreenManager lifecycle timing on Android.
        Clock.schedule_once(lambda *_: self.refresh(), 0)

    def _build(self):
        root = BoxLayout(orientation="horizontal", padding=[dp(12),dp(12),dp(12),dp(12)], spacing=dp(12))

        # LEFT: quiet, editorial-style rotating guidance area.
        self.info_panel = BoxLayout(orientation="vertical", padding=[dp(20), dp(22)],
                                    spacing=dp(12), size_hint_x=0.40)
        with self.info_panel.canvas.before:
            Color(0.925, 0.965, 0.995, 1)
            self.info_bg = RoundedRectangle(radius=[dp(20)])
        self.info_panel.bind(pos=lambda o,v:setattr(self.info_bg,"pos",v),
                             size=lambda o,v:setattr(self.info_bg,"size",v))

        self.info_kicker = Label(text=fa_display("راهنمای سریع فراهوش"),
                                 font_name=font_name(), font_size="11sp",
                                 color=(0.08,0.36,0.66,1), bold=True,
                                 halign="right", valign="middle",
                                 size_hint_y=None, height=dp(34))
        self.info_kicker.bind(size=lambda o,v:setattr(o,"text_size",v))
        self.info_panel.add_widget(self.info_kicker)

        self.info_title = Label(text=fa_display("نکته کاربردی"),
                                font_name=font_name(), font_size="21sp", bold=True,
                                color=(0.05,0.25,0.48,1), halign="right",
                                valign="middle", size_hint_y=None, height=dp(58))
        self.info_title.bind(size=lambda o,v:setattr(o,"text_size",v))
        self.info_panel.add_widget(self.info_title)

        self.info_rule = BoxLayout(size_hint_y=None, height=dp(3))
        with self.info_rule.canvas.before:
            Color(0.16,0.50,0.86,0.85)
            self.info_rule_bg = RoundedRectangle(radius=[dp(2)])
        self.info_rule.bind(pos=lambda o,v:setattr(self.info_rule_bg,"pos",v),
                            size=lambda o,v:setattr(self.info_rule_bg,"size",v))
        self.info_panel.add_widget(self.info_rule)

        self.info_text = Label(
            text="",
            font_name=font_name(), font_size="13sp", color=(0.10,0.23,0.38,1),
            halign="right", valign="top", line_height=1.25,
            padding=[dp(2), dp(4)])
        def _sync_info_text(widget, size):
            widget.text_size = (max(dp(80), size[0] - dp(4)), None)
        self.info_text.bind(size=_sync_info_text)
        self.info_panel.add_widget(self.info_text)

        self.info_hint = Label(text=fa_display("نکته‌ها به‌صورت خودکار جابه‌جا می‌شوند"),
                               font_name=font_name(), font_size="10.5sp",
                               color=(0.24,0.40,0.58,1), halign="right",
                               valign="bottom", size_hint_y=None, height=dp(38))
        self.info_hint.bind(size=lambda o,v:setattr(o,"text_size",v))
        self.info_panel.add_widget(self.info_hint)
        self._tips=[]; self._tip_index=0; self._tip_event=None
        root.add_widget(self.info_panel)

        # RIGHT: professional module workspace; categories and rows stay flat/linear.
        right = BoxLayout(orientation="vertical", spacing=dp(8), padding=[dp(14),dp(12)], size_hint_x=0.60)
        with right.canvas.before:
            Color(0.965,0.985,1,1)
            self.right_bg = RoundedRectangle(radius=[dp(22)])
        right.bind(pos=lambda o,v:setattr(self.right_bg,"pos",v), size=lambda o,v:setattr(self.right_bg,"size",v))
        head = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(10), padding=[dp(10),dp(4)])
        with head.canvas.before:
            Color(0.07,0.32,0.52,1)
            self.head_bg = RoundedRectangle(radius=[dp(15)])
        head.bind(pos=lambda o,v:setattr(self.head_bg,"pos",v), size=lambda o,v:setattr(self.head_bg,"size",v))
        title = {route:title for title,route in PANEL_HUBS}.get(self.panel_key,self.panel_key)
        self.panel_title = Label(text=fa_display("ماژورهای "+title),
                                 font_name=font_name(), font_size="17sp", bold=True,
                                 color=WHITE, halign="right", valign="middle")
        self.panel_title.bind(size=lambda o,v:setattr(o,"text_size",v))
        head.add_widget(self.panel_title)
        back = Button(text=fa_display("بازگشت"), font_name=font_name(), font_size="11sp",
                      size_hint_x=None, width=dp(72), height=dp(34), size_hint_y=None,
                      background_normal="", background_down="", background_color=(0.12,0.43,0.64,1),
                      color=(0.78,0.90,1,1))
        back.bind(on_release=lambda *_: setattr(self.manager,"current","dashboard") if self.manager else None)
        head.add_widget(back)
        right.add_widget(head)

        self.module_scroll = ScrollView(do_scroll_x=False, bar_width=dp(4),
                                        scroll_type=["bars","content"])
        self.module_box = BoxLayout(orientation="vertical", spacing=dp(10),
                                    padding=[dp(2),dp(2)], size_hint_y=None)
        self.module_box.bind(minimum_height=self.module_box.setter("height"))
        self.module_scroll.add_widget(self.module_box)
        right.add_widget(self.module_scroll)
        root.add_widget(right)
        self.add_widget(root)

    def _start_info_tips(self):
        if self._tip_event is not None:
            self._tip_event.cancel()
        self._tip_index=0
        self._tip_event=Clock.schedule_interval(self._next_info_tip,6.5)
        Clock.schedule_once(self._next_info_tip,0)

    def _next_info_tip(self,*_):
        if not self._tips:
            return
        value=self._tips[self._tip_index % len(self._tips)]
        self._tip_index+=1
        try:
            Animation(opacity=0.12,duration=0.24).start(self.info_text)
            def reveal(_dt):
                self.info_text.text=fa_display(value)
                Animation(opacity=1,duration=0.42).start(self.info_text)
            Clock.schedule_once(reveal,0.26)
        except Exception:
            self.info_text.text=fa_display(value)
    def _has_panel_access(self, panel_key):
        role = self._active_role()
        if role == "manager":
            return True
        role_panels = {
            "executive": {"executive"},
            "educational": {"educational"},
            "cultural": {"cultural"},
            "advisor": {"advisor"},
            "teacher": {"teachers"},
            "student": {"students"},
            "parent": {"parents"},
        }
        return panel_key in role_panels.get(role, set())

    def refresh(self):
        if not self._has_panel_access(self.panel_key):
            try: self.manager.current="dashboard"
            except Exception: pass
            print("PANEL ACCESS DENIED:",self._active_role(),self.panel_key)
            return

        catalog_key={"management":"manager","executive":"executive","educational":"educational",
                     "cultural":"cultural","advisor":"advisor","teachers":"teacher","staff":"staff",
                     "students":"student","parents":"parent","finance":"finance",
                     "smart_board":"smart_board","ai":"ai"}.get(self.panel_key,self.panel_key)
        catalog=MOTHER_PANEL_CATALOG.get(catalog_key) or {}
        items=list(catalog.get("items") or [])
        # Parent accounts must never be offered the online-exam workspace.
        # Keep the canonical shared catalog intact, but enforce the school
        # access contract at the Android presentation boundary as well.
        if self.panel_key=="parents":
            items=[item for item in items if str(item[1]) not in {"teacher_exams","online","online_classes","online_class_sessions"}]
        if self.panel_key=="staff":
            items=[("کادر و کارکنان","staff")]
        if self.panel_key=="meetings":
            items=[("ثبت و پیگیری ملاقات","meeting_requests")]
        elif self.panel_key=="teacher_exams":
            items=[("مرکز طراحی آزمون آنلاین","teacher_exams")]
        elif self.panel_key=="online":
            items=[("مرکز کلاس آنلاین","online_classes")]

        self.module_box.clear_widgets()
        title={route:title for title,route in PANEL_HUBS}.get(self.panel_key,self.panel_key)
        tip_map={
            "teachers":["می‌توانید فعالیت‌های آموزشی، حضور و غیاب و نمرات کلاس‌های خود را از همین پنل پیگیری کنید.",
                        "ماژورها بر اساس موضوع آموزشی و ارتباطی مرتب شده‌اند تا دسترسی سریع‌تر باشد.",
                        "پس از ثبت اطلاعات، نتیجه را در همان بخش عملیاتی بررسی کنید."],
            "management":["امکانات مدیریتی برای نظارت یکپارچه بر بخش‌های مختلف مدرسه در یکجا گردآوری شده‌اند.",
                          "گزارش هر بخش را از ماژور مرتبط با همان موضوع دنبال کنید."],
            "executive":["امور پرونده، کلاس‌بندی و درخواست‌های اجرایی از این پنل قابل پیگیری هستند.",
                         "برای پیگیری درخواست‌ها، وضعیت و سوابق هر مورد را در بخش مربوط بررسی کنید."],
            "educational":["برنامه‌ریزی آموزشی، ارزشیابی و کلاس‌های مدرسه در این پنل دسته‌بندی شده‌اند.",
                           "اطلاعات آموزشی را در ماژور مرتبط با پایه، کلاس یا درس ثبت کنید."],
            "parents":["از این پنل می‌توانید وضعیت آموزشی و درخواست‌های مرتبط با فرزندتان را پیگیری کنید.",
                       "برای پیگیری پاسخ مدرسه، صندوق پیام‌ها و وضعیت درخواست را بررسی کنید."],
            "students":["تکالیف، آزمون‌ها و درخواست‌های دانش‌آموزی از این پنل در دسترس هستند.",
                        "پس از ارسال تکلیف یا درخواست، وضعیت ثبت آن را پیگیری کنید."]
        }
        self._tips=tip_map.get(self.panel_key,[
            f"پنل «{title}» امکانات مرتبط با مسئولیت‌های این بخش را یکجا در دسترس قرار می‌دهد.",
            "هر گزینه شما را مستقیماً به بخش عملیاتی مربوط هدایت می‌کند.",
            "برای پیدا کردن سریع‌تر امکانات، دسته‌بندی‌ها را دنبال کنید."
        ])

        if not items:
            empty=Label(text=fa_display("برای این پنل هنوز ماژوری تعریف نشده است."),
                        font_name=font_name(),font_size="14sp",color=(0.38,0.47,0.58,1),
                        halign="right",valign="middle",size_hint_y=None,height=dp(56))
            self.module_box.add_widget(empty)
            self._start_info_tips()
            return

        grouped=[]
        groups=MODULE_CATEGORY_GROUPS.get(self.panel_key) or []
        remaining=list(items)
        for category,route_ids in groups:
            selected=[]
            for item in list(remaining):
                label,route=item
                if route in route_ids:
                    selected.append(item)
                    remaining.remove(item)
            if selected:
                grouped.append((category,selected))
        if remaining:
            grouped.append(("سایر امکانات",remaining))
        if not grouped:
            grouped=[("",items)]

        for category,group_items in grouped:
            section=BoxLayout(orientation="vertical",spacing=0,
                              padding=[dp(4),dp(2)],size_hint_y=None)
            if category:
                heading=BoxLayout(size_hint_y=None,height=dp(36),padding=[dp(8),0])
                with heading.canvas.before:
                    Color(0.91,0.965,0.995,1)
                    heading_bg=RoundedRectangle(radius=[dp(10)])
                heading.bind(pos=lambda o,v,bg=heading_bg:setattr(bg,"pos",v),
                             size=lambda o,v,bg=heading_bg:setattr(bg,"size",v))
                heading_label=Label(text=fa_display(category),font_name=font_name(),
                                    font_size="12.5sp",bold=True,color=(0.08,0.30,0.54,1),
                                    halign="right",valign="middle")
                heading_label.bind(size=lambda o,v:setattr(o,"text_size",v))
                heading.add_widget(heading_label)
                section.add_widget(heading)
            for index,(label,route) in enumerate(group_items):
                row=Button(text=fa_display(str(label)),
                           font_name=font_name(),font_size="12.5sp",
                           background_normal="",background_down="",
                           background_color=(1,1,1,0),
                           color=(0.12,0.20,0.30,1),
                           halign="right",valign="middle",
                           size_hint_y=None,height=dp(52))
                row.bind(size=lambda o,v:setattr(o,"text_size",(max(dp(80),v[0]-dp(24)),v[1])))
                row.bind(on_release=lambda *_a,r=route:self._open(r))
                section.add_widget(row)
                if index < len(group_items)-1:
                    divider=BoxLayout(size_hint_y=None,height=dp(1))
                    with divider.canvas.before:
                        Color(0.88,0.93,0.97,1)
                        line=Rectangle(pos=divider.pos,size=divider.size)
                    divider.bind(pos=lambda o,v,ln=line:setattr(ln,"pos",v),
                                 size=lambda o,v,ln=line:setattr(ln,"size",v))
                    section.add_widget(divider)
            section.height=sum(w.height for w in section.children)+dp(8)
            self.module_box.add_widget(section)

        self._start_info_tips()
    def _module_purpose(self,label,route):
        return {
            "دانش‌آموزان":"پرونده، اطلاعات هویتی، کلاس و سوابق دانش‌آموز.",
            "دبیران":"پرونده پرسنلی، کلاس‌ها، نمرات و فعالیت‌های آموزشی.",
            "حضور و غیاب":"ثبت، اصلاح و گزارش حضور و غیاب.",
            "آزمون آنلاین":"طراحی، زمان‌بندی، انتشار و نمره آزمون.",
            "کلاس آنلاین":"جلسه، دانش‌آموزان، حضور و کنترل ادامه کلاس.",
            "درخواست گواهی":"درخواست و صدور گواهی اشتغال به تحصیل.",
            "درخواست ملاقات":"ثبت درخواست، تأیید مسئول و تأیید نهایی مدیر.",
        }.get(label,"ثبت، ویرایش، حذف، گزارش و تبادل اطلاعات واقعی سامانه.")

    def _active_role(self):
        profile = getattr(self.app_state, "profile", {}) or {}
        raw = str(
            profile.get("role") or profile.get("user_role") or
            profile.get("school_role") or getattr(self.app_state, "role", "") or ""
        ).strip().lower()
        return {
            "admin":"manager","administrator":"manager","management":"manager",
            "manager":"manager","مدیر":"manager","مدیریت":"manager",
            "معاون آموزشی":"educational","educational":"educational","educational_deputy":"educational",
            "معاون اجرایی":"executive","executive":"executive","executive_deputy":"executive",
            "معاون پرورشی":"cultural","cultural":"cultural",
            "دبیر":"teacher","teacher":"teacher","دانش‌آموز":"student","student":"student",
            "ولی":"parent","اولیا":"parent","parent":"parent",
        }.get(raw, raw)

    def _open_meeting_workflow(self):
        app=App.get_running_app()
        try:
            target=app.ensure_meeting_workflow()
            if target is None:
                raise RuntimeError("مرکز ملاقات آماده نشد.")
            app.sm.current=target.name
        except Exception as exc:
            print("MEETING OPEN ERROR:",repr(exc))

    def _open_online_create(self):
        app=App.get_running_app()
        try:
            target=app.ensure_online_workflow()
            if target is None: raise RuntimeError("مرکز کلاس آنلاین آماده نشد.")
            app.sm.current=target.name
            if hasattr(target, "_open_create_form"):
                Clock.schedule_once(lambda *_: target._open_create_form(), 0.05)
        except Exception as exc:
            print("ONLINE CREATE OPEN ERROR:",repr(exc))

    def _open_exam_create(self):
        app=App.get_running_app()
        try:
            target=app.ensure_exam_authoring()
            if target is None: raise RuntimeError("مرکز آزمون آنلاین آماده نشد.")
            app.sm.current=target.name
            if hasattr(target, "_new_exam"):
                Clock.schedule_once(lambda *_: target._new_exam(), 0.05)
        except Exception as exc:
            print("EXAM CREATE OPEN ERROR:",repr(exc))

    def _open_io(self,route):
        app=App.get_running_app()
        if not app: return
        try:
            screen=app.ensure_panel_io(self.panel_key)
            if screen:
                app.sm.current=screen.name
        except Exception as exc: print("MODULE IO ERROR:",repr(exc))

    def _open(self,route):
        """Open a module on the next Kivy frame.
        
        ScreenManager mutations from inside Button.on_release can race the
        current transition on Android. The previous implementation created the
        operational Screen synchronously and converted any construction/timing
        exception into the visible red "پنل عملیاتی آماده نشد" message.
        """
        app=App.get_running_app()
        if app is None:
            return
        route=str(route or "").strip()

        def navigate(_dt):
            try:
                target=None
                try:
                    if route == "certificate_requests":
                        target=app.ensure_certificate_workflow()
                    elif route in {"meeting_requests","parent_meeting_requests","teacher_meetings","meetings"}:
                        target=app.ensure_meeting_workflow()
                    elif route in {"online_classes","virtual"}:
                        target=app.ensure_online_workflow()
                    elif route in {"teacher_exams","exams","questions","quiz_questions"}:
                        target=app.ensure_exam_authoring()
                except Exception as workflow_exc:
                    print("DEDICATED WORKFLOW FALLBACK:",repr(workflow_exc))
                    target=None

                if target is not None:
                    app.sm.current=target.name
                    return

                panel=app.ensure_panel()
                if panel is None:
                    raise RuntimeError("پنل عملیاتی آماده نشد؛ ساخت ModuleWorkspaceScreen شکست خورد.")
                if hasattr(panel, "set_panel_role"):
                    panel.set_panel_role(self.panel_key)
                panel.set_route(route)
                if app.sm.current != "panel":
                    app.sm.current="panel"
            except Exception as exc:
                print("MOTHER MODULE OPEN ERROR:",repr(exc))
                try:
                    self.grid.add_widget(Button(
                        text=rtl_text("خطای بازکردن ماژول: "+str(exc)),
                        font_name=font_name(),font_size="11sp",
                        background_normal="",background_color=(0.65,0.12,0.12,1),
                        color=WHITE,size_hint_y=None,height=dp(54),
                    ))
                except Exception:
                    pass

        Clock.schedule_once(navigate,0)

    def on_pre_enter(self,*_):
        if not self._has_panel_access(self.panel_key):
            try:
                if self.manager:
                    self.manager.current = "dashboard"
            except Exception:
                pass
            return
        # Kivy calls this synchronously while ScreenManager.current is changed.
        # An exception here bubbles back into open_dashboard() and is reported
        # incorrectly as "dashboard did not open" even though authentication
        # succeeded. Keep the lifecycle boundary non-throwing on Android.
        if self.app_state is None or not getattr(self.app_state,"logged_in",False):
            try:
                if self.manager:
                    self.manager.current="login"
            except Exception as exc:
                print("DASHBOARD LOGIN REDIRECT ERROR:",repr(exc))
            return
        try:
            self.refresh()
        except Exception as exc:
            print("DASHBOARD PRE-ENTER REFRESH ERROR:",repr(exc))
            try:
                self.welcome.text=rtl_text("ورود موفق بود؛ داشبورد آماده است.")
                self.role_text.text=rtl_text("پنل‌ها در حال آماده‌سازی هستند...")
            except Exception:
                pass
        if self.role() in {"parent","student","teacher","manager","educational","executive","cultural","advisor","counselor"}:
            try:
                self._start_parent_poll()
            except Exception as exc:
                print("DASHBOARD NOTIFICATION POLL START ERROR:",repr(exc))

class DashboardScreen(Screen):
    """Mobile dashboard: static, professional multi-column panel hub. No swipe/carousel animation is used."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state=app_state
        self._parent_seen=set()
        self._parent_poll_event=None
        self._parent_poll_busy=False
        try:
            self._build()
        except Exception as exc:
            # The dashboard is the first screen after authentication. If one
            # optional visual/widget resource is broken on a particular Android
            # build, never return a false dashboard to LoginScreen. Render the
            # same real panel entry points with a dependency-light fallback.
            print("DASHBOARD BUILD ERROR:", repr(exc))
            self._build_safe_fallback(exc)

    def _build_safe_fallback(self, exc=None):
        self.clear_widgets()
        root=BoxLayout(orientation="vertical",padding=[dp(12),dp(12),dp(12),dp(74)],spacing=dp(6))
        with root.canvas.before:
            Color(0.02,0.08,0.18,1)
            self._safe_bg=RoundedRectangle()
        root.bind(pos=lambda o,v:setattr(self._safe_bg,"pos",v),size=lambda o,v:setattr(self._safe_bg,"size",v))
        self.welcome=self.label("خوش آمدید","18sp",WHITE,True,True)
        self.role_text=self.label("داشبورد فراهوش","11sp",(0.88,0.96,1,1),False,True)
        self.parent_alert=self.label("","9sp",WHITE,False,True)
        root.add_widget(self.welcome)
        root.add_widget(self.role_text)
        root.add_widget(self.parent_alert)
        scroll=ScrollView(do_scroll_x=False,do_scroll_y=True)
        self.grid=GridLayout(cols=2,spacing=dp(8),padding=dp(4),size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)
        self.grid_scroll=scroll
        root.add_widget(Widget(size_hint_y=None,height=dp(1)))
        self.add_widget(root)
        # Keep the canonical role-aware dashboard entry list. Each button opens
        # the existing PanelHubScreen, so the fallback is not a fake module.
        try:
            items=self.items()
        except Exception:
            items=[(title,"panelhub:"+key) for title,key in PANEL_HUBS]
        total=len(items)
        for i,(title,route) in enumerate(items,1):
            card=PanelCard(title,i,total,self.desc(route.replace("panelhub:","")),lambda *_a,r=route:self.open_route(r),
                           route=route.replace("panelhub:",""),size_hint_y=None,height=dp(170))
            self.grid.add_widget(card)
        print("DASHBOARD SAFE FALLBACK ACTIVE:", repr(exc))

    def label(self,text,size="11sp",color=WHITE,bold=False,center=True):
        w=Label(text=rtl_text(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle")
        w.bind(size=lambda o,v:setattr(o,"text_size",v))
        return w

    def role(self):
        raw=str(getattr(self.app_state,"role","unknown") or "unknown").strip().lower()
        return ROLE_ALIASES.get(raw,raw)

    def items(self):
        role = self.role()
        if role == "manager":
            return [(title, "panelhub:" + key) for title, key in PANEL_HUBS]
        own_panel = {
            "executive": "executive",
            "educational": "educational",
            "cultural": "cultural",
            "advisor": "advisor",
            "teacher": "teachers",
            "student": "students",
            "parent": "parents",
        }.get(role)
        if own_panel:
            for title, key in PANEL_HUBS:
                if key == own_panel:
                    return [(title, "panelhub:" + key)]
        return []


    def _build(self):
        # Reference layout: right navigation rail + top header + statistics +
        # analysis/quick-access cards. Everything is native Kivy widgets.
        root=BoxLayout(orientation="horizontal", spacing=dp(0), padding=[dp(6),dp(6),dp(6),dp(8)])

        main=BoxLayout(orientation="vertical", padding=[dp(10),dp(8),dp(10),dp(4)], spacing=dp(0))
        with main.canvas.before:
            Color(0.94,0.95,0.97,1)
            main_bg=RoundedRectangle(radius=[dp(22)])
        main.bind(pos=lambda o,v:setattr(main_bg,"pos",v), size=lambda o,v:setattr(main_bg,"size",v))

        content=BoxLayout(orientation="vertical", padding=[dp(0),dp(0),dp(0),dp(8)], spacing=dp(8), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        content_scroll=ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=dp(3), size_hint_y=1)
        content_scroll.add_widget(content)

        header=BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(78), padding=[dp(10),dp(6)])
        with header.canvas.before:
            Color(1,1,1,1)
            header_bg=RoundedRectangle(radius=[dp(14)])
        header.bind(pos=lambda o,v:setattr(header_bg,"pos",v), size=lambda o,v:setattr(header_bg,"size",v))

        title_box=BoxLayout(orientation="vertical", padding=[dp(6),dp(3)])
        self.header_title=self.label("سامانه مدیریت هوشمند دبیرستان","20sp",(0.06,0.12,0.20,1),True,False)
        self.header_subtitle=self.label(f"{SCHOOL_NAME}  |  {SCHOOL_YEAR}","10sp",(0.30,0.38,0.46,1),False,False)
        title_box.add_widget(self.header_title)
        title_box.add_widget(self.header_subtitle)
        header.add_widget(title_box)

        logo=Image(source=str(BACKGROUND_PATH) if Path(str(BACKGROUND_PATH)).is_file() else "",size_hint_x=None,width=dp(72),allow_stretch=True,keep_ratio=True)
        header.add_widget(logo)
        content.add_widget(header)

        # Compact live-school status badge: fixed height prevents a large blank
        # area and keeps the green status readable on the white workspace.
        self.parent_alert=self.label("", "10sp", (0.07,0.38,0.22,1), True, True)
        self.parent_alert.size_hint_y=None
        self.parent_alert.height=dp(42)
        self.parent_alert.padding=[dp(10),dp(4)]
        with self.parent_alert.canvas.before:
            Color(0.86,0.97,0.90,1)
            self._alert_bg=RoundedRectangle(radius=[dp(15)])
        self.parent_alert.bind(pos=lambda o,v:setattr(self._alert_bg,"pos",v),
                               size=lambda o,v:setattr(self._alert_bg,"size",v))
        content.add_widget(self.parent_alert)

        stats=GridLayout(cols=2,spacing=dp(8),size_hint_y=None,height=dp(150),padding=[dp(1),dp(1)])
        self.stat_widgets=[]
        for caption,route in (
            ("تعداد دانش‌آموزان","students"),
            ("تعداد دبیران و کارکنان","staff"),
            ("تعداد کلاس‌ها","school_class_config"),
            ("پیام‌های جدید","messages"),
        ):
            card=BoxLayout(orientation="vertical",padding=[dp(12),dp(7)],spacing=dp(2))
            with card.canvas.before:
                Color(1,1,1,1)
                cb=RoundedRectangle(radius=[dp(14)])
            card.bind(pos=lambda o,v,bg=cb:setattr(bg,"pos",v),size=lambda o,v,bg=cb:setattr(bg,"size",v))
            value=self.label("—","24sp",(0.05,0.25,0.45,1),True,True)
            caption_w=self.label(caption,"10sp",(0.32,0.38,0.45,1),False,True)
            card.add_widget(value); card.add_widget(caption_w)
            card.bind(on_touch_up=lambda w,t,r=route: self._quick_route(w,t,r) or True)
            self.stat_widgets.append((route,value))
            stats.add_widget(card)
        content.add_widget(stats)

        lower=GridLayout(cols=1,spacing=dp(8),size_hint_y=None,padding=[dp(1),dp(1)])
        lower.bind(minimum_height=lower.setter("height"))

        analysis=BoxLayout(orientation="vertical",padding=[dp(12),dp(8)],spacing=dp(4),size_hint_y=None,height=dp(145))
        with analysis.canvas.before:
            Color(1,1,1,1)
            ab=RoundedRectangle(radius=[dp(14)])
        analysis.bind(pos=lambda o,v:setattr(ab,"pos",v),size=lambda o,v:setattr(ab,"size",v))
        analysis.add_widget(self.label("تحلیل و گزارش هوشمند","15sp",(0.06,0.12,0.20,1),True,False))
        analysis.add_widget(self.label("نمای کلی وضعیت آموزشی و مدیریتی مدرسه","10sp",(0.35,0.40,0.46,1),False,False))
        self.analysis_text=self.label("برای مشاهده جزئیات، از پنل‌های سمت راست استفاده کنید.","11sp",(0.16,0.23,0.30,1),False,False)
        analysis.add_widget(self.analysis_text)
        lower.add_widget(analysis)

        quick=BoxLayout(orientation="vertical",padding=[dp(12),dp(8)],spacing=dp(6),size_hint_y=None,height=dp(190))
        with quick.canvas.before:
            Color(1,1,1,1)
            qb=RoundedRectangle(radius=[dp(14)])
        quick.bind(pos=lambda o,v:setattr(qb,"pos",v),size=lambda o,v:setattr(qb,"size",v))
        quick.add_widget(self.label("دسترسی سریع","15sp",(0.06,0.12,0.20,1),True,False))
        qrow=GridLayout(cols=2,spacing=dp(6))
        for caption,route in (("دانش‌آموزان","students"),("کلاس آنلاین","online"),("آزمون‌ها","teacher_exams"),("صندوق پیام‌ها","messages")):
            b=Button(text=fa_display(caption),font_name=font_name(),font_size="11sp",
                     background_normal="",background_color=(0.08,0.36,0.58,1),color=WHITE)
            b.bind(size=lambda o,v:setattr(o,"text_size",v))
            b.bind(on_release=lambda *_a,r=route:self._quick_route(None,None,r))
            qrow.add_widget(b)
        quick.add_widget(qrow)
        lower.add_widget(quick)

        self.grid_scroll=ScrollView(do_scroll_x=False,do_scroll_y=True,bar_width=dp(3),size_hint_y=None,height=dp(1))
        self.grid=GridLayout(cols=1,spacing=dp(8),size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.grid_scroll.add_widget(self.grid)
        # Keep the canonical panel cards available below the reference dashboard
        # content on smaller screens.
        content.add_widget(lower)

        # Bottom navigation is fixed inside the school workspace and sits above
        # the Android system navigation/home area. On Kivy versions without a
        # native safe-area API we keep a conservative 24dp reserve.
        nav_inset = _android_navigation_inset_dp()
        footer=BoxLayout(size_hint_y=None,height=dp(68),spacing=dp(5),padding=[dp(2),dp(6),dp(2),dp(10)])
        for caption,route in (("خانه","home"),("پنل‌ها","panels"),("ماژول‌ها","modules"),("پیام‌ها","messages"),("پروفایل","profile")):
            b=Button(text=fa_display(caption),font_name=font_name(),font_size="9.5sp",
                     padding=[dp(2),dp(3)],
                     background_normal="",background_color=(0.09,0.20,0.30,1),color=WHITE,
                     bold=True, halign="center", valign="middle")
            b.bind(size=lambda o,v:setattr(o,"text_size",v))
            b.bind(on_release=lambda *_a,r=route:self._bottom_nav(r))
            footer.add_widget(b)
        content.add_widget(Widget(size_hint_y=None,height=dp(8)))
        main.add_widget(content_scroll)
        main.add_widget(footer)
        # Reserve the actual Android navigation inset below the footer so the
        # buttons never sit underneath the gesture/3-button navigation area.
        main.add_widget(Widget(size_hint_y=None,height=nav_inset))
        root.add_widget(main)

        # Right-side navigation, matching the supplied reference image.
        # Compact navigation rail gives the white workspace more width.
        side=BoxLayout(orientation="vertical",size_hint_x=None,width=dp(148),padding=[dp(7),dp(8)],spacing=dp(5))
        with side.canvas.before:
            Color(0.07,0.32,0.52,1)
            sb=RoundedRectangle(radius=[dp(22)])
        side.bind(pos=lambda o,v:setattr(sb,"pos",v),size=lambda o,v:setattr(sb,"size",v))

        brand=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(76),padding=[dp(4),dp(4)])
        brand.add_widget(self.label("فراهوش","25sp",WHITE,True,True))
        brand.add_widget(self.label("سامانه مدیریت هوشمند مدرسه","8.5sp",(0.72,0.86,0.96,1),False,True))
        side.add_widget(brand)

        self.side_scroll=ScrollView(do_scroll_x=False,do_scroll_y=True,bar_width=dp(2))
        self.side_list=BoxLayout(orientation="vertical",spacing=dp(5),size_hint_y=None,padding=[dp(1),dp(1)])
        self.side_list.bind(minimum_height=self.side_list.setter("height"))
        self.side_scroll.add_widget(self.side_list)
        side.add_widget(self.side_scroll)

        root.add_widget(side)
        self.add_widget(root)

        self._build_reference_sidebar()
        self._refresh_reference_stats()

    def _allowed_panel_keys(self):
        role = self.role()
        if role == "manager":
            return {route for _title, route in PANEL_HUBS}
        role_panel = {
            "executive": "executive",
            "educational": "educational",
            "cultural": "cultural",
            "advisor": "advisor",
            "teacher": "teachers",
            "student": "students",
            "parent": "parents",
        }.get(role)
        allowed = {"about"}
        if role_panel:
            allowed.add(role_panel)
        return allowed

    def _build_reference_sidebar(self):
        self.side_list.clear_widgets()
        self.stat_widgets = []
        allowed = self._allowed_panel_keys()
        for title, route in PANEL_HUBS:
            if route not in allowed:
                continue
            b = Button(
                text=fa_display(title),
                font_name=font_name(),
                font_size="11.5sp",
                background_normal="",
                background_color=(0.08, 0.20, 0.32, 1),
                color=WHITE,
                bold=True,
                halign="right",
                valign="middle",
                size_hint_y=None,
                height=dp(42),
            )
            b.bind(size=lambda o, v: setattr(o, "text_size", v))
            b.bind(on_release=lambda *_a, r=route: self._quick_route(None, None, "panelhub:"+r) if r not in {"about"} else self.open_route("about"))
            self.side_list.add_widget(b)

    def _refresh_reference_stats(self):
        # Keep the reference visual real: values are filled from app state when
        # already available, otherwise shown as a neutral dash instead of fake data.
        profile=getattr(self.app_state,"profile",{}) or {}
        values={
            "students": profile.get("student_count") or profile.get("students_count"),
            "staff": profile.get("staff_count") or profile.get("teacher_count"),
            "school_class_config": profile.get("class_count") or profile.get("classes_count"),
            "messages": profile.get("unread_count") or profile.get("message_count"),
        }
        for route,w in getattr(self,"stat_widgets",[]):
            value=values.get(route)
            w.text=fa_display(str(value) if value is not None else "—")

    def _quick_route(self, widget, touch, route):
        if touch is not None and widget is not None and not widget.collide_point(*touch.pos):
            return False
        if route in {"students","staff","school_class_config","messages","online","teacher_exams"}:
            try:
                self.open_route("panelhub:"+({"students":"students","staff":"management","school_class_config":"executive"}.get(route,route)))
                return True
            except Exception:
                pass
        try:
            self.open_route(route)
            return True
        except Exception:
            return False

    def _bottom_nav(self,route):
        if route=="home":
            if self.manager:self.manager.current="dashboard"
        elif route=="panels":
            if self.manager:self.manager.current="dashboard"
            Clock.schedule_once(lambda *_: setattr(self.side_scroll, "scroll_y", 1), 0)
        elif route=="modules":
            try:
                role_panel = {
                    "manager": "management",
                    "executive": "executive",
                    "educational": "educational",
                    "cultural": "cultural",
                    "advisor": "advisor",
                    "teacher": "teachers",
                    "student": "students",
                    "parent": "parents",
                }.get(self.role(), "management")
                self.open_route("panelhub:" + role_panel)
            except Exception:
                self.grid_scroll.scroll_y = 1
        elif route=="messages":
            self.open_route("messages")
        elif route=="profile":
            self.open_route("settings")

    def resolve_module_route(self, role, title, fallback_route):
        try:
            from mobile.screens.module_workspace import SUBMENUS
            wanted = str(title).strip()
            for label, real_route in (SUBMENUS.get(role) or []):
                if str(label).strip() == wanted:
                    return real_route
            common = {
                "گزارش عملکرد": "ai_smart_reports",
                                "کلاس آنلاین": "online",
                "بانک سؤال": "teacher_exams",
                "هدایت تحصیلی": "counseling_followups",
                "گزارش‌های آموزشی": "ai_smart_reports",
                "گزارش مشاوره": "report_cards",
                "تنظیمات مدرسه": "school_profile",
                "گزارش‌ها و آمار": "report_cards",
                "گزارش‌ها": "report_cards",
            }
            return common.get(wanted, fallback_route)
        except Exception as exc:
            print("MODULE ROUTE RESOLVE ERROR:", repr(exc))
            return fallback_route

    def desc(self,route):
        return {
            "management":"اطلاعات مدرسه، دانش‌آموزان، دبیران، کارکنان، کلاس‌ها، پیام‌ها، گزارش‌ها و تنظیمات مدیریت.",
            "executive":"پرونده دانش‌آموزی، کارکنان، کلاس‌ها، گواهی‌ها، کارنامه‌ها، ملاقات‌ها و امور اجرایی.",
            "advisor":"پرونده‌های مشاوره، پیگیری جلسات، ارتباط با والدین، گزارش‌ها و هدایت تحصیلی هوشمند.",
            "teachers":"کلاس‌های من، طرح درس، برنامه هفتگی، حضور و غیاب، نمرات، تکالیف، آزمون و کلاس آنلاین.",
            "students":"اطلاعات شخصی، پایه و کلاس، نمرات، حضور و غیاب، تکالیف، برنامه و کلاس‌های آنلاین.",
            "parents":"فرزندان، نمرات، حضور و غیاب، کارنامه‌ها، ملاقات‌ها، آموزش خانواده و پیام‌های مدرسه.",
            "finance":"حساب‌ها، تراکنش‌ها، کمک‌ها و سوابق پرداخت.",
            "payment":"گزینه‌های پرداخت، درخواست و سوابق تراکنش.",
            "online":"کلاس‌های آنلاین، جلسات، دانش‌آموزان، دبیران و حضور سه‌مرحله‌ای.",
            "teacher_exams":"ایجاد، زمان‌بندی، انتشار و تصحیح آزمون آنلاین.",
            "reports":"کارنامه، نمرات، حضور و گزارش‌های اجرایی و هوشمند.",
            "schedule":"برنامه هفتگی، امتحانات و چیدمان صندلی‌ها.",
            "smart_board":"محتوای آموزشی، تخته، فایل، فعالیت و آزمونک.",
            "ai":"پرسش هوشمند، جلسات دستیار و گزارش‌های تحلیلی.",
            "reports":"کارنامه، نمرات، حضور و گزارش‌های هوشمند.",
            "schedule":"برنامه هفتگی، امتحانات و صندلی‌های آزمون.",
            "messages":"صندوق ورودی، ارسال، مخاطبان و وضعیت خواندن پیام.",
            "settings":"تنظیمات حساب، مدرسه و ساختار کلاس‌ها.",
            "about":"اطلاعات سامانه فراهوش و نسخه برنامه.",
            "participation":"فعالیت‌ها و مشارکت‌های ثبت‌شده."
        }.get(route,"محیط عملیاتی واقعی سامانه فراهوش.")

    def _group_modules(self, panel_key, modules):
        groups = MODULE_CATEGORY_GROUPS.get(panel_key) or []
        if not groups:
            return [("", modules)] if modules else []
        remaining = list(modules)
        grouped = []
        for category, route_ids in groups:
            selected = []
            for item in list(remaining):
                label, route = item
                if route in route_ids:
                    selected.append(item)
                    remaining.remove(item)
            if selected:
                grouped.append((category, selected))
        if remaining:
            grouped.append(("سایر امکانات", remaining))
        return grouped

    def _panel_modules(self, role, panel_key):
        catalog_key = {
            "management":"manager",
            "teachers":"teacher",
            "students":"student",
            "parents":"parent",
        }.get(panel_key, panel_key)
        catalog = MOTHER_PANEL_CATALOG.get(catalog_key) or {}
        raw_items = catalog.get("items") or []
        if panel_key == "parents":
            raw_items = [item for item in raw_items if str(item[1]) not in {"teacher_exams","online","online_classes","online_class_sessions"}]
        if panel_key == "staff":
            raw_items = [("کادر و کارکنان","staff")]
        if panel_key == "online":
            raw_items = [("کلاس‌های آنلاین","online_classes"),("جلسات","online_class_sessions"),
                         ("دانش‌آموزان کلاس","online_class_students"),("دبیران کلاس","online_class_teachers"),
                         ("حضور آنلاین","online_attendance"),("تخته کلاس","smart_board_whiteboards")]
        if panel_key == "teacher_exams":
            raw_items = [("آزمون‌های آنلاین","teacher_exams"),("بانک سؤال","quiz_questions"),("زمان‌بندی آزمون","exam_schedule")]
        if panel_key == "messages":
            raw_items = [("صندوق پیام‌ها","messages")]
        if panel_key == "finance":
            raw_items = [("پرداخت‌ها","payment_records"),("تراکنش‌ها","finance_transactions"),
                         ("حساب‌ها","finance_accounts"),("گزارش مالی","reports"),("تعریف گزینه پرداخت","payment_offers")]
        if panel_key == "smart_board":
            raw_items = [("تخته آموزشی","smart_board_whiteboards"),("فایل‌ها","smart_board_content"),
                         ("تصاویر و ویدئوها","smart_board_media"),("ابزارهای تعاملی","smart_board_activities")]
        if panel_key == "ai":
            raw_items = [("دستیار هوشمند","ai_assistant_sessions"),("تحلیل آموزشی","ai_smart_reports"),
                         ("گزارش هوشمند","ai_smart_reports"),("پرسش و پاسخ","ai_questions")]
        if panel_key == "settings":
            raw_items = [("تنظیمات حساب","account_settings"),("تنظیمات مدرسه","school_profile"),("پشتیبان‌گیری","account_settings")]
        result=[]
        for item in raw_items:
            if not item or len(item) < 2 or not item[0]:
                continue
            label, fallback = str(item[0]), str(item[1])
            result.append((label, self.resolve_module_route(role, label, fallback)))
        return result

    def refresh(self):
        if self.app_state is None or not getattr(self.app_state,"logged_in",False): return False
        role=self.role()
        items=self.items()
        self.welcome.text=fa_display(f"خوش آمدید، {getattr(self.app_state,'display_name','کاربر فراهوش')}")
        self.role_text.text=fa_display(f"پنل {ROLE_TITLES.get(role,'کاربر')}  -  {len(items)} بخش اصلی")
        self.grid.clear_widgets()
        self._build_reference_sidebar()
        total=len(items)
        for i,(title,route) in enumerate(items,1):
            panel_key=route.split(":",1)[1] if str(route).startswith("panelhub:") else route
            modules=self._group_modules(panel_key, self._panel_modules(role,panel_key))
            card=PanelCard(
                title,i,total,self.desc(panel_key),
                lambda *_a,r=route:self.open_route(r),
                route=panel_key,
                modules=modules,
                module_enter=self.open_route,
                size_hint_y=None,
            )
            self.grid.add_widget(card)
        return True

    def open_route(self,route):
        route_key = str(route or "")
        if route_key.startswith("panelhub:"):
            panel_key = route_key.split(":",1)[1]
            role = self.role()
            allowed = role == "manager" or panel_key == {
                "executive":"executive","educational":"educational","cultural":"cultural",
                "advisor":"advisor","teacher":"teachers","student":"students","parent":"parents"
            }.get(role)
            if not allowed:
                print("DASHBOARD ACCESS DENIED:", role, panel_key)
                return
        app=App.get_running_app()
        if app is None or app.sm is None:
            return
        try:
            # Online class and online exam are first-class operational
            # workspaces. Do not route the teacher through a generic/empty
            # panel hub: open the real creation center directly.
            if route == "online":
                if self.role() == "parent":
                    print("DASHBOARD ACCESS DENIED: parent online class")
                    return
                self.app_state.panel_role = self.role()
                screen=app.ensure_online_workflow()
                if screen is None:
                    raise RuntimeError("مرکز کلاس آنلاین آماده نشد.")
                app.sm.current=screen.name
                return
            if route == "teacher_exams":
                if self.role() == "parent":
                    print("DASHBOARD ACCESS DENIED: parent online exam")
                    return
                self.app_state.panel_role = self.role()
                screen=app.ensure_exam_authoring()
                if screen is None:
                    raise RuntimeError("مرکز آزمون آنلاین آماده نشد.")
                app.sm.current=screen.name
                return
            if str(route).startswith("panelhub:"):
                key=str(route).split(":",1)[1]
                self.app_state.panel_role = self.role()
                name="panelhub_"+key
                try:
                    screen=app.sm.get_screen(name)
                except Exception:
                    screen=PanelHubScreen(name=name,app_state=self.app_state,panel_key=key)
                    app.sm.add_widget(screen)
                app.sm.current=name
                return
            if route=="about":
                from mobile.screens.about import AboutScreen
                try: screen=app.sm.get_screen("about")
                except Exception:
                    screen=AboutScreen(name="about",app_state=self.app_state); app.sm.add_widget(screen)
                app.sm.current="about"; return
            if route=="participation":
                from mobile.screens.participation import ParticipationScreen
                try: screen=app.sm.get_screen("participation")
                except Exception:
                    screen=ParticipationScreen(name="participation",app_state=self.app_state); app.sm.add_widget(screen)
                screen.set_route(self.role()); app.sm.current="participation"; return
            if route=="teacher_exams":
                try:
                    screen=app.ensure_exam()
                    if screen:
                        app.sm.current="teacher_exams"
                        return
                except Exception as exam_exc:
                    print("TEACHER EXAM WORKFLOW FALLBACK:",repr(exam_exc))
                # Fall through to the canonical mother/table workspace.
            panel=app.ensure_panel()
            if panel is None:
                raise RuntimeError("پنل عملیاتی آماده نشد.")
            # Activate the real workspace first; do not render a module while
            # the dashboard is still the current Screen on Android.
            app.sm.current="panel"
            panel.set_route(route)
        except Exception as exc:
            print("DASHBOARD ROUTE ERROR:",repr(exc))
            try:
                self.role_text.text=rtl_text("خطا در باز کردن پنل؛ دوباره تلاش کنید.")
                self.role_text.color=(1,.35,.35,1)
                Clock.schedule_once(lambda _dt:self._restore_role_status(),2.5)
            except Exception:
                pass

    def _start_parent_poll(self):
        if self._parent_poll_event is None:
            self._parent_poll_event = Clock.schedule_interval(self._poll_parent_notifications, 2.0)
        Clock.schedule_once(self._poll_parent_notifications, 0)

    def _poll_parent_notifications(self, *_):
        if self._parent_poll_busy or self.app_state is None:
            return
        self._parent_poll_busy=True
        def worker():
            try:
                from mobile.services.live_data import LiveSchoolData
                events, feed = LiveSchoolData(self.app_state).parent_unread_notifications(self._parent_seen)
                ids=[e["id"] for e in events]
                if ids:
                    self._parent_seen.update(ids)
                    latest=events[0]
                    title=latest.get("title","اعلان جدید")
                    count=len(events)
                    msg=f"صندوق پیام - {title} - {count} مورد جدید"
                else:
                    total=sum(len(feed.get(k,[])) for k in ("attendance","discipline","grades","activities","messages"))
                    msg=f"اعلان‌های لحظه‌ای فعال - {total} رویداد مدرسه"
                Clock.schedule_once(lambda _dt,m=msg:self._set_parent_alert(m),0)
            except Exception as exc:
                print("PARENT LIVE FEED ERROR:",repr(exc))
                Clock.schedule_once(lambda _dt:self._set_parent_alert("اتصال اعلان‌های مدرسه در حال بررسی است."),0)
            finally:
                self._parent_poll_busy=False
        Thread(target=worker,daemon=True).start()

    def _set_parent_alert(self,message):
        try:
            self.parent_alert.text=fa_display(message)
            self.parent_alert.color=(0.07,0.38,0.22,1)
        except Exception:
            pass

    def _start_parent_poll(self):
        if self._parent_poll_event is None:
            self._parent_poll_event = Clock.schedule_interval(self._poll_parent_notifications, 5.0)
        Clock.schedule_once(self._poll_parent_notifications, 0)

    def _poll_parent_notifications(self, *_):
        if self._parent_poll_busy or self.app_state is None:
            return
        self._parent_poll_busy=True
        def worker():
            try:
                from mobile.services.live_data import LiveSchoolData
                events, feed = LiveSchoolData(self.app_state).parent_unread_notifications(self._parent_seen)
                ids=[e["id"] for e in events]
                if ids:
                    self._parent_seen.update(ids)
                    latest=events[0]
                    msg=f'صندوق پیام - {latest.get("title","اعلان جدید")} - {len(events)} مورد جدید'
                else:
                    total=sum(len(feed.get(k,[])) for k in ("attendance","discipline","grades","activities","messages"))
                    msg=f"اعلان‌های لحظه‌ای فعال - {total} رویداد مدرسه"
                Clock.schedule_once(lambda _dt,m=msg:self._set_parent_alert(m),0)
            except Exception as exc:
                print("PARENT LIVE FEED ERROR:",repr(exc))
                Clock.schedule_once(lambda _dt:self._set_parent_alert("اتصال اعلان‌های مدرسه در حال بررسی است."),0)
            finally:
                self._parent_poll_busy=False
        Thread(target=worker,daemon=True).start()

    def _set_parent_alert(self,message):
        try:
            self.parent_alert.text=rtl_text(message)
            self.parent_alert.color=(0.07,0.38,0.22,1)
        except Exception:
            pass

    def _restore_role_status(self,*_):
        try:
            role=self.role()
            self.role_text.text=rtl_text(f"پنل {ROLE_TITLES.get(role,'کاربر')} - دسترسی فعال")
            self.role_text.color=(0.88,0.96,1,1)
        except Exception:
            pass

    def on_pre_enter(self,*_):
        # Never let a dashboard refresh exception escape the Kivy lifecycle.
        # On Android an uncaught exception here can terminate the process
        # exactly after the login screen reports success.
        if self.app_state is None or not getattr(self.app_state,"logged_in",False):
            if self.manager:
                self.manager.current="login"
            return
        try:
            self.refresh()
        except Exception as exc:
            print("DASHBOARD PRE-ENTER REFRESH ERROR:", repr(exc))
            try:
                self.welcome.text = rtl_text("ورود موفق بود؛ داشبورد آماده شد.")
                self.role_text.text = rtl_text("در حال آماده‌سازی پنل‌ها...")
            except Exception:
                pass
        if self.role() in {"parent","student","teacher","manager","educational","executive","cultural","advisor","counselor"}:
            try:
                self._start_parent_poll()
            except Exception as exc:
                print("DASHBOARD NOTIFICATION POLL START ERROR:", repr(exc))

    def logout(self,*_):
        try:
            if self.app_state:self.app_state.logout()
        except Exception: pass
        if self.manager:self.manager.current="login"
