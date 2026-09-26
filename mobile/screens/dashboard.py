from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.app import App
from pathlib import Path
from threading import Thread
import json

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, BACKGROUND_PATH, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, fa_display, bundled_login_background

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
    "student": {"title":"دانش‌آموزان","items":[["تکالیف","assignment_submissions"],["صندوق پیام","messages"]]},
    "parent": {"title":"اولیا","items":[["پرداخت آنلاین","payment"],["صندوق پیام","messages"]]},
    "finance": {"title":"مالی","items":[["پرداخت‌ها","payment_records"],["تراکنش‌ها","finance_transactions"],["حساب‌ها","finance_accounts"],["گزارش مالی","reports"],["تنظیمات پرداخت آنلاین","payment_offers"]]},
    "smart_board": {"title":"تابلو هوشمند","items":[["تخته آموزشی","smart_board_whiteboards"],["فایل‌ها","smart_board_content"],["تصاویر و ویدئوها","smart_board_media"],["ابزارهای تعاملی","smart_board_activities"]]},
    "online": {"title":"کلاس آنلاین","items":[["کلاس‌های آنلاین","online_classes"],["جلسات","online_class_sessions"],["دانش‌آموزان کلاس","online_class_students"],["دبیران کلاس","online_class_teachers"],["حضور آنلاین","online_attendance"],["تخته کلاس","smart_board_whiteboards"]]},
    "teacher_exams": {"title":"آزمون آنلاین","items":[["آزمون‌های آنلاین","teacher_exams"],["بانک سؤال","quiz_questions"],["زمان‌بندی آزمون","exam_schedule"]]},
    "ai": {"title":"هوش مصنوعی","items":[["دستیار هوشمند","ai_assistant_sessions"],["تحلیل آموزشی","ai_smart_reports"],["گزارش هوشمند","ai_smart_reports"],["پرسش و پاسخ","ai_questions"]]},
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
    def __init__(self, title, index, total, desc, enter, route=None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(7), **kwargs)
        with self.canvas.before:
            Color(0.02, 0.10, 0.20, 0.90)
            self.bg = RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self._sync, size=self._sync)
        self.add_widget(PanelIcon(route or "about"))
        self.add_widget(Label(text=fa_display(title),font_name=font_name(),font_size="17sp",color=WHITE,bold=True,
                              halign="center",valign="middle",size_hint_y=None,height=dp(52)))
        self.add_widget(Label(text=fa_display(f"پنل {index} از {total}"),font_name=font_name(),font_size="10sp",color=(0.55,0.85,1,1),
                              halign="center",valign="middle",size_hint_y=None,height=dp(26)))
        self.add_widget(Label(text=fa_display(desc),font_name=font_name(),font_size="9sp",color=WHITE,
                              halign="center",valign="middle"))
        b=Button(text=fa_display("ورود به پنل"),font_name=font_name(),font_size="14sp",background_normal="",
                 background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(50),
                 halign="center",valign="middle")
        b.bind(on_release=enter)
        self.add_widget(b)
    def _sync(self,*_):
        self.bg.pos=self.pos; self.bg.size=self.size

PANEL_HUBS = [
    ("مدیریت","management"),
    ("معاون آموزشی","educational"),
    ("معاون اجرایی","executive"),
    ("معاون پرورشی","cultural"),
    ("مشاوره","advisor"),
    ("دبیران","teachers"),
    ("دانش‌آموزان","students"),
    ("اولیا","parents"),
    ("مالی","finance"),
    ("کلاس‌های آنلاین","online"),
    ("آزمون آنلاین","teacher_exams"),
    ("ملاقات‌ها","meetings"),
    ("تابلو هوشمند","smart_board"),
    ("هوش مصنوعی","ai"),
    ("صندوق پیام‌ها","messages"),
    ("گزارش‌ها","reports"),
    ("برنامه‌ریزی / زمان‌بندی","schedule"),
    ("تنظیمات","settings"),
    ("اطلاعات دانش‌آموز","student_info"),
    ("مشارکت","participation"),
]

STUDENT_ALLOWED_PANELS = {"students"}
PARENT_ALLOWED_PANELS = {"parents"}

PANEL_MODULE_SOURCE = {
    "management":"management", "educational":"educational", "executive":"executive",
    "cultural":"cultural", "advisor":"advisor", "teachers":"teachers",
    "parents":"parents", "students":"students", "finance":"finance",
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
        root=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
        with root.canvas.before:
            Color(0.02,0.08,0.18,0.96)
            self.bg=RoundedRectangle(radius=[dp(18)])
        root.bind(pos=lambda o,v:setattr(self.bg,"pos",v),size=lambda o,v:setattr(self.bg,"size",v))
        title={route: title for title, route in PANEL_HUBS}.get(self.panel_key,self.panel_key)
        head=BoxLayout(size_hint_y=None,height=dp(58))
        head.add_widget(Label(text=fa_display(title),font_name=font_name(),font_size="18sp",color=WHITE,bold=True))
        back=Button(text=fa_display("بازگشت"),font_name=font_name(),size_hint_x=None,width=dp(78),
                    background_normal="",background_color=PRIMARY,color=WHITE)
        back.bind(on_release=lambda *_: setattr(self.manager,"current","dashboard") if self.manager else None)
        head.add_widget(back); root.add_widget(head)
        # Dedicated creation actions for the two first-class teaching workspaces.
        # Keep them visible at the top of their panel, before the module list.
        if self.panel_key == "meetings":
            create=Button(text=fa_display("＋ ثبت یا پیگیری ملاقات"),font_name=font_name(),font_size="14sp",
                           background_normal="",background_color=SUCCESS,color=WHITE,
                           size_hint_y=None,height=dp(52))
            create.bind(on_release=lambda *_: self._open_meeting_workflow())
            root.add_widget(create)
        # Staff/management panels get one explicit, real import/export center.
        # Student/parent panels keep their restricted consumer workflow.
        if self.panel_key not in {"students", "parents", "meetings"}:
            io=Button(text=fa_display("ورودی و خروجی Excel / PDF"),font_name=font_name(),font_size="12sp",
                      background_normal="",background_color=(0.08,0.34,0.52,1),color=WHITE,
                      size_hint_y=None,height=dp(46))
            io.bind(on_release=lambda *_: self._open_io(self.panel_key))
            root.add_widget(io)
        if self.panel_key == "online":
            active_role = self._active_role()
            if active_role in {"manager","educational","executive"}:
                create=Button(text=fa_display("＋ تشکیل کلاس جدید"),font_name=font_name(),font_size="14sp",
                               background_normal="",background_color=SUCCESS,color=WHITE,
                               size_hint_y=None,height=dp(52))
                create.bind(on_release=lambda *_: self._open_online_create())
                root.add_widget(create)
        elif self.panel_key == "teacher_exams":
            create=Button(text=fa_display("＋ ساخت آزمون جدید"),font_name=font_name(),font_size="14sp",
                           background_normal="",background_color=SUCCESS,color=WHITE,
                           size_hint_y=None,height=dp(52))
            create.bind(on_release=lambda *_: self._open_exam_create())
            root.add_widget(create)
        self.scroll=ScrollView(do_scroll_x=False)
        self.grid=GridLayout(cols=2,spacing=dp(8),padding=dp(4),size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid); root.add_widget(self.scroll)
        self.add_widget(root)

    def refresh(self):
        # The uploaded v16.12 mother ZIP is the single source of truth for
        # panel/module membership.  Do not derive this screen from the backend
        # catalog or from a secondary navigation map.
        catalog_key = {
            "management": "manager",
            "executive": "executive",
            "educational": "educational",
            "cultural": "cultural",
            "advisor": "advisor",
            "teachers": "teacher",
            "students": "student",
            "parents": "parent",
            "finance": "finance",
            "smart_board": "smart_board",
            "ai": "ai",
        }.get(self.panel_key, self.panel_key)
        catalog = MOTHER_PANEL_CATALOG.get(catalog_key) or {}
        items = catalog.get("items") or []

        # These are first-class operational centers, not generic CRUD tables.
        # Always expose their real workflow entry point even if the mother ZIP
        # catalog has no dedicated navigation section for them.
        if self.panel_key == "meetings":
            items = [("ثبت و پیگیری ملاقات", "meeting_requests")]
        elif self.panel_key == "teacher_exams":
            items = [("مرکز طراحی آزمون آنلاین", "teacher_exams")]
        elif self.panel_key == "online":
            items = [("مرکز کلاس آنلاین", "online_classes")]
        self.grid.clear_widgets()
        if not items:
            # Keep a visible diagnostic instead of silently rendering an empty
            # panel when a panel key is ever mistyped.
            b=Button(
                text=fa_display("ماژول‌های این پنل در قرارداد مادر پیدا نشد"),
                font_name=font_name(), font_size="13sp",
                background_normal="", background_color=(0.65,0.12,0.12,1),
                color=WHITE, size_hint_y=None, height=dp(58),
            )
            self.grid.add_widget(b)
            print("MOTHER PANEL EMPTY:", self.panel_key, catalog_key)
            return
        for label,route in items:
            card=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5),size_hint_y=None,height=dp(132))
            with card.canvas.before:
                Color(0.03,0.14,0.25,0.96)
                card_bg=RoundedRectangle(radius=[dp(14)])
            card.bind(pos=lambda o,v,bg=card_bg:setattr(bg,"pos",v),size=lambda o,v,bg=card_bg:setattr(bg,"size",v))
            card.add_widget(Label(text=fa_display(label),font_name=font_name(),font_size="13sp",bold=True,color=WHITE,
                                  halign="center",valign="middle",size_hint_y=None,height=dp(34)))
            card.add_widget(Label(text=fa_display(self._module_purpose(label,route)),font_name=font_name(),font_size="8sp",
                                  color=(0.75,0.9,1,1),halign="center",valign="middle"))
            actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(4))
            # Every mother module has one operational entry point.  Excel/PDF
            # is an export/import utility, not the module itself, and showing it
            # beside every module was the source of the generic "ورودی و خروجی"
            # page being mistaken for the real module workspace.
            if route in {"meeting_requests","parent_meeting_requests","teacher_meetings","meetings"}:
                enter=Button(text=fa_display("ورود به محیط واقعی ملاقات"),
                             font_name=font_name(),font_size="10sp",
                             background_normal="",background_color=SUCCESS,color=WHITE,
                             halign="center",valign="middle")
                enter.bind(on_release=lambda *_a:self._open_meeting_workflow())
            else:
                enter=Button(text=fa_display("ورود به جدول تخصصی و عملیات"),
                             font_name=font_name(),font_size="10sp",
                             background_normal="",background_color=SUCCESS,color=WHITE,
                             halign="center",valign="middle")
                enter.bind(on_release=lambda *_a,r=route:self._open(r))
            actions.add_widget(enter); card.add_widget(actions)
            self.grid.add_widget(card)

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
        if app is None or app.sm is None:
            return
        def navigate(_dt):
            try:
                try:
                    target=app.ensure_meeting_workflow()
                except Exception as primary_exc:
                    print("MEETING WORKFLOW BUILD ERROR:",repr(primary_exc))
                    target=None
                # Keep the older real meeting screen as a compatibility fallback
                # for APKs whose workflow dependencies are unavailable.
                if target is None:
                    target=app.ensure_meetings()
                if target is None:
                    raise RuntimeError("مرکز ملاقات آماده نشد.")
                app.sm.current=target.name
            except Exception as exc:
                print("MEETING OPEN ERROR:",repr(exc))
                try:
                    self.grid.add_widget(Button(
                        text=fa_display("خطای بازکردن ملاقات: "+str(exc)),
                        font_name=font_name(),font_size="10sp",
                        background_normal="",background_color=(0.65,0.12,0.12,1),
                        color=WHITE,size_hint_y=None,height=dp(54),
                    ))
                except Exception:
                    pass
        Clock.schedule_once(navigate,0)

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
                        text=fa_display("خطای بازکردن ماژول: "+str(exc)),
                        font_name=font_name(),font_size="11sp",
                        background_normal="",background_color=(0.65,0.12,0.12,1),
                        color=WHITE,size_hint_y=None,height=dp(54),
                    ))
                except Exception:
                    pass

        Clock.schedule_once(navigate,0)

    def on_pre_enter(self,*_):
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
                self.welcome.text=fa_display("ورود موفق بود؛ داشبورد آماده است.")
                self.role_text.text=fa_display("پنل‌ها در حال آماده‌سازی هستند...")
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
        w=Label(text=fa_display(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle")
        w.bind(size=lambda o,v:setattr(o,"text_size",v))
        return w

    def role(self):
        raw=str(getattr(self.app_state,"role","student") or "student").strip().lower()
        return ROLE_ALIASES.get(raw,raw)

    def items(self):
        # The dashboard is the school-wide panel directory. Every authenticated
        # account sees the same professional panel cards; the operational/read-only
        # policy is enforced after entering a panel, at the module level.
        return [(title, "panelhub:" + key) for title, key in PANEL_HUBS]


    def _build(self):
        root=FloatLayout()
        # The dashboard is intentionally independent of the login artwork.
        # A full-screen image made the panel UI look washed-out/gray on some
        # Android devices and reduced contrast.  Use a clean professional
        # surface so the actual panels are the visual focus.
        with root.canvas.before:
            Color(0.025,0.07,0.14,1)
            self.dashboard_bg=RoundedRectangle()
        root.bind(pos=lambda o,v:setattr(self.dashboard_bg,"pos",v),
                  size=lambda o,v:setattr(self.dashboard_bg,"size",v))
        content=BoxLayout(orientation="vertical",padding=[dp(14),dp(12),dp(14),dp(84)],spacing=dp(8))
        head=BoxLayout(size_hint_y=None,height=dp(56))
        head.add_widget(self.label(APP_NAME,"25sp",WHITE,True,True)); content.add_widget(head)
        self.welcome=self.label("خوش آمدید","14sp",WHITE,True,True); content.add_widget(self.welcome)
        self.role_text=self.label("","10sp",(0.88,0.96,1,1),False,True); content.add_widget(self.role_text)
        self.parent_alert=self.label("","11sp",WHITE,True,True); content.add_widget(self.parent_alert)
        frame=BoxLayout(orientation="vertical",padding=dp(8))
        with frame.canvas.before:
            Color(0.02,0.08,0.18,0.64); self.frame_bg=RoundedRectangle(radius=[dp(22)])
        frame.bind(pos=lambda o,v:setattr(self.frame_bg,"pos",v),size=lambda o,v:setattr(self.frame_bg,"size",v))
        self.grid_scroll=ScrollView(do_scroll_x=False,do_scroll_y=True,bar_width=dp(3))
        self.grid=GridLayout(cols=2,spacing=dp(10),padding=dp(4),size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.grid_scroll.add_widget(self.grid); frame.add_widget(self.grid_scroll); content.add_widget(frame)
        root.add_widget(content)
        nav=BoxLayout(size_hint=(.90,None),height=dp(56),pos_hint={"center_x":.5,"y":.02},spacing=dp(3),padding=dp(3))
        with nav.canvas.before:
            Color(0.01,0.08,0.17,0.92); self.nav_bg=RoundedRectangle(radius=[dp(24)])
        nav.bind(pos=lambda o,v:setattr(self.nav_bg,"pos",v),size=lambda o,v:setattr(self.nav_bg,"size",v))
        for title,route in (("خانه","home"),("ماژول‌ها","modules"),("پیام‌ها","messages"),("پروفایل","profile")):
            b=Button(text=fa_display(title),font_name=font_name(),font_size="10sp",background_normal="",background_color=(0,0,0,0),color=WHITE)
            b.bind(on_release=lambda *_a,r=route:self._bottom_nav(r)); nav.add_widget(b)
        root.add_widget(nav); self.add_widget(root)

    def _bottom_nav(self,route):
        if route=="home":
            if self.manager:self.manager.current="dashboard"
        elif route=="modules":
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
                "پرداخت آنلاین": "payment",
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
            "smart_board":"محتوای آموزشی، تخته، فایل، فعالیت و آزمونک.",
            "ai":"پرسش هوشمند، جلسات دستیار و گزارش‌های تحلیلی.",
            "reports":"کارنامه، نمرات، حضور و گزارش‌های هوشمند.",
            "schedule":"برنامه هفتگی، امتحانات و صندلی‌های آزمون.",
            "messages":"صندوق ورودی، ارسال، مخاطبان و وضعیت خواندن پیام.",
            "settings":"تنظیمات حساب، مدرسه و ساختار کلاس‌ها.",
            "about":"اطلاعات سامانه فراهوش و نسخه برنامه.",
            "participation":"فعالیت‌ها و مشارکت‌های ثبت‌شده."
        }.get(route,"محیط عملیاتی واقعی سامانه فراهوش.")

    def refresh(self):
        if self.app_state is None or not getattr(self.app_state,"logged_in",False): return False
        role=self.role(); items=self.items()
        self.welcome.text=fa_display(f"خوش آمدید، {getattr(self.app_state,'display_name','کاربر فراهوش')}")
        self.role_text.text=fa_display(f"پنل {ROLE_TITLES.get(role,'کاربر')} • دسترسی فعال")
        self.grid.clear_widgets()
        total=len(items)
        for i,(title,route) in enumerate(items,1):
            real_route = self.resolve_module_route(role, title, route)
            card=PanelCard(title,i,total,self.desc(real_route),lambda *_a,r=real_route:self.open_route(r),
                           route=real_route,size_hint_y=None,height=dp(170))
            self.grid.add_widget(card)
        return True

    def open_route(self,route):
        app=App.get_running_app()
        if app is None or app.sm is None:
            return
        try:
            # Online class and online exam are first-class operational
            # workspaces. Do not route the teacher through a generic/empty
            # panel hub: open the real creation center directly.
            if route == "online":
                self.app_state.panel_role = self.role()
                screen=app.ensure_online_workflow()
                if screen is None:
                    raise RuntimeError("مرکز کلاس آنلاین آماده نشد.")
                app.sm.current=screen.name
                return
            if route == "teacher_exams":
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
                self.role_text.text=fa_display("خطا در باز کردن پنل؛ دوباره تلاش کنید.")
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
                    msg=f"صندوق پیام • {title} • {count} مورد جدید"
                else:
                    total=sum(len(feed.get(k,[])) for k in ("attendance","discipline","grades","activities","messages"))
                    msg=f"اعلان‌های لحظه‌ای فعال • {total} رویداد مدرسه"
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
            self.parent_alert.color=(0.72,1,0.82,1)
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
                    msg=f'صندوق پیام • {latest.get("title","اعلان جدید")} • {len(events)} مورد جدید'
                else:
                    total=sum(len(feed.get(k,[])) for k in ("attendance","discipline","grades","activities","messages"))
                    msg=f"اعلان‌های لحظه‌ای فعال • {total} رویداد مدرسه"
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
            self.parent_alert.color=(0.72,1,0.82,1)
        except Exception:
            pass

    def _restore_role_status(self,*_):
        try:
            role=self.role()
            self.role_text.text=fa_display(f"پنل {ROLE_TITLES.get(role,'کاربر')} • دسترسی فعال")
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
                self.welcome.text = fa_display("ورود موفق بود؛ داشبورد آماده شد.")
                self.role_text.text = fa_display("در حال آماده‌سازی پنل‌ها...")
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
