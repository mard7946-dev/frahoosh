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
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.app import App
from pathlib import Path
import json

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, BACKGROUND_PATH, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text, bundled_login_background

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
    "teacher": {"title":"دبیران","items":[["کلاس‌های من","teacher_classes"],["نمرات و کارنامه","student_grades"],["تکالیف","assignments"],["حضور و غیاب","attendance"],["آزمون‌ها","teacher_exams"],["طرح درس","lesson_plans"],["جلسات","meeting_requests"],["گزارش‌ها","reports"]]},
    "student": {"title":"دانش‌آموزان","items":[["انتخاب و اطلاعات من","students"],["کارنامه و نمرات","student_grades"],["تکالیف","assignments"],["پیام‌ها","messages"],["حضور و غیاب","attendance"],["مسابقات و فعالیت‌ها","activity_registrations"],["برنامه هفتگی","weekly_schedule"],["امتحانات","exam_schedule"],["گزارش عملکرد","ai_smart_reports"],["کلاس آنلاین","online_classes"],["پرداخت آنلاین","payment_offers"]]},
    "parent": {"title":"اولیا","items":[["انتخاب دانش‌آموز","parent_children"],["اطلاعات دانش‌آموز","students"],["کارنامه و نمرات","student_grades"],["حضور و غیاب","attendance"],["تکالیف و فعالیت‌های آموزشی","assignments"],["پیام‌ها و اطلاعیه‌ها","messages"],["برنامه هفتگی و امتحانات","weekly_schedule"],["جلسات با دبیران","meeting_requests"],["پرداخت‌ها و امور مالی","payment_records"],["پرداخت آنلاین","payment"],["فعالیت‌های فرهنگی و پرورشی","cultural_activity_registrations"]]},
    "finance": {"title":"مالی","items":[["پرداخت‌ها","payment_records"],["تراکنش‌ها","finance_transactions"],["حساب‌ها","finance_accounts"],["گزارش مالی","reports"],["تنظیمات پرداخت آنلاین","payment_offers"]]},
    "smart_board": {"title":"تابلو هوشمند","items":[["تخته آموزشی","smart_board_whiteboards"],["فایل‌ها","smart_board_content"],["تصاویر و ویدئوها","smart_board_media"],["ابزارهای تعاملی","smart_board_activities"]]},
    "ai": {"title":"هوش مصنوعی","items":[["دستیار هوشمند","ai_assistant_sessions"],["تحلیل آموزشی","ai_smart_reports"],["گزارش هوشمند","ai_smart_reports"],["پرسش و پاسخ","ai_questions"]]},
    "settings": {"title":"تنظیمات","items":[["تنظیمات حساب","account_settings"],["تنظیمات مدرسه","school_profile"],["پشتیبان‌گیری","account_settings"]]}
}

def _load_mother_panel_catalog():
    path = Path(__file__).resolve().parents[1] / "assets" / "mother_panel_catalog.json"
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            panels = data.get("panels") or {}
            if panels:
                return panels
    except Exception as exc:
        print("MOTHER PANEL CATALOG ERROR:", repr(exc))
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
        self.add_widget(Label(text=rtl_text(title),font_name=font_name(),font_size="17sp",color=WHITE,bold=True,
                              halign="center",valign="middle",size_hint_y=None,height=dp(52)))
        self.add_widget(Label(text=rtl_text(f"پنل {index} از {total}"),font_name=font_name(),font_size="10sp",color=(0.55,0.85,1,1),
                              halign="center",valign="middle",size_hint_y=None,height=dp(26)))
        self.add_widget(Label(text=rtl_text(desc),font_name=font_name(),font_size="9sp",color=WHITE,
                              halign="center",valign="middle"))
        b=Button(text=rtl_text("ورود به پنل"),font_name=font_name(),font_size="14sp",background_normal="",
                 background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(50))
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
    ("اولیا","parents"),
    ("دانش‌آموزان","students"),
    ("مالی","finance"),
    ("تابلوی هوشمند","smart_board"),
    ("آزمون آنلاین","teacher_exams"),
    ("کلاس آنلاین","online"),
    ("پرداخت آنلاین","payment"),
    ("هوش مصنوعی","ai"),
    ("صندوق پیام","messages"),
]

STUDENT_ALLOWED_PANELS = {key for _, key in PANEL_HUBS if key != "finance"}
PARENT_ALLOWED_PANELS = {key for _, key in PANEL_HUBS if key not in {"finance","online","teacher_exams"}}

PANEL_MODULE_SOURCE = {
    "management":"management", "educational":"educational", "executive":"executive",
    "cultural":"cultural", "advisor":"advisor", "teachers":"teachers",
    "parents":"parents", "students":"students", "finance":"finance",
    "smart_board":"smart_board", "online":"online", "ai":"ai", "messages":"messages",
    "teacher_exams":"teachers", "payment":"finance"
}

class PanelHubScreen(Screen):
    def __init__(self, app_state=None, panel_key="students", **kwargs):
        super().__init__(**kwargs)
        self.app_state=app_state
        self.panel_key=panel_key
        self._build()

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
        with root.canvas.before:
            Color(0.02,0.08,0.18,0.96)
            self.bg=RoundedRectangle(radius=[dp(18)])
        root.bind(pos=lambda o,v:setattr(self.bg,"pos",v),size=lambda o,v:setattr(self.bg,"size",v))
        title=dict(PANEL_HUBS).get(self.panel_key,self.panel_key)
        head=BoxLayout(size_hint_y=None,height=dp(58))
        head.add_widget(Label(text=rtl_text(title),font_name=font_name(),font_size="21sp",color=WHITE,bold=True))
        back=Button(text=rtl_text("بازگشت"),font_name=font_name(),size_hint_x=None,width=dp(92),
                    background_normal="",background_color=PRIMARY,color=WHITE)
        back.bind(on_release=lambda *_: setattr(self.manager,"current","dashboard") if self.manager else None)
        head.add_widget(back); root.add_widget(head)
        self.scroll=ScrollView(do_scroll_x=False)
        self.grid=GridLayout(cols=2,spacing=dp(8),padding=dp(4),size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid); root.add_widget(self.scroll)
        self.add_widget(root)

    def refresh(self):
        from mobile.screens.module_workspace import SUBMENUS
        source=PANEL_MODULE_SOURCE.get(self.panel_key,self.panel_key)
        items=SUBMENUS.get(source,[])
        self.grid.clear_widgets()
        for label,route in items:
            b=Button(text=rtl_text(label),font_name=font_name(),font_size="13sp",
                     background_normal="",background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(58))
            b.bind(on_release=lambda *_a,r=route:self._open(r))
            self.grid.add_widget(b)

    def _open(self,route):
        app=App.get_running_app()
        if app is None: return
        if route=="teacher_exams":
            screen=app.ensure_exam()
            if screen: app.sm.current="teacher_exams"
            return
        panel=app.ensure_panel()
        if panel:
            panel.set_route(route)
            app.sm.current="panel"

    def on_pre_enter(self,*_):
        self.refresh()

class DashboardScreen(Screen):
    """Mobile dashboard: animated swipeable panels inside a half-screen frame over the agreed artwork."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state=app_state
        self._build()

    def label(self,text,size="11sp",color=WHITE,bold=False,center=True):
        w=Label(text=rtl_text(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle")
        w.bind(size=lambda o,v:setattr(o,"text_size",v))
        return w

    def role(self):
        raw=str(getattr(self.app_state,"role","student") or "student").strip().lower()
        return ROLE_ALIASES.get(raw,raw)

    def items(self):
        role=self.role()
        if role=="student":
            return [(title,"panelhub:"+key) for title,key in PANEL_HUBS if key in STUDENT_ALLOWED_PANELS]
        if role=="parent":
            return [(title,"panelhub:"+key) for title,key in PANEL_HUBS if key in PARENT_ALLOWED_PANELS]
        entry=MOTHER_PANEL_CATALOG.get(role) or MOTHER_PANEL_CATALOG.get("student")
        return [tuple(item) for item in (entry.get("items") or [])]


    def _build(self):
        root=FloatLayout()
        background_source = bundled_login_background()
        bg=Image(source=background_source or "",size_hint=(1,1),allow_stretch=True,keep_ratio=True,fit_mode="contain",nocache=True)
        root.add_widget(bg)
        if background_source:
            Clock.schedule_once(lambda *_: bg.reload(), 0.20)
        overlay=FloatLayout(size_hint=(1,1))
        with overlay.canvas.before:
            Color(0,0,0,0.22); self.tint=RoundedRectangle()
        overlay.bind(pos=lambda o,v:setattr(self.tint,"pos",v),size=lambda o,v:setattr(self.tint,"size",v))
        root.add_widget(overlay)
        content=BoxLayout(orientation="vertical",padding=[dp(14),dp(8),dp(14),dp(78)],spacing=dp(5))
        head=BoxLayout(size_hint_y=None,height=dp(56))
        head.add_widget(self.label(APP_NAME,"25sp",WHITE,True,True)); content.add_widget(head)
        self.welcome=self.label("خوش آمدید","14sp",WHITE,True,True); content.add_widget(self.welcome)
        self.role_text=self.label("","10sp",(0.88,0.96,1,1),False,True); content.add_widget(self.role_text)
        frame=BoxLayout(orientation="vertical",padding=dp(8))
        with frame.canvas.before:
            Color(0.02,0.08,0.18,0.64); self.frame_bg=RoundedRectangle(radius=[dp(22)])
        frame.bind(pos=lambda o,v:setattr(self.frame_bg,"pos",v),size=lambda o,v:setattr(self.frame_bg,"size",v))
        self.grid_scroll=ScrollView(do_scroll_x=False,do_scroll_y=True,bar_width=dp(3))
        self.grid=GridLayout(cols=2,spacing=dp(7),padding=dp(3),size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.grid_scroll.add_widget(self.grid); frame.add_widget(self.grid_scroll); content.add_widget(frame)
        root.add_widget(content)
        nav=BoxLayout(size_hint=(.90,None),height=dp(56),pos_hint={"center_x":.5,"y":.075},spacing=dp(3),padding=dp(3))
        with nav.canvas.before:
            Color(0.01,0.08,0.17,0.92); self.nav_bg=RoundedRectangle(radius=[dp(24)])
        nav.bind(pos=lambda o,v:setattr(self.nav_bg,"pos",v),size=lambda o,v:setattr(self.nav_bg,"size",v))
        for title,route in (("خانه","home"),("ماژول‌ها","modules"),("پیام‌ها","messages"),("پروفایل","profile")):
            b=Button(text=rtl_text(title),font_name=font_name(),font_size="10sp",background_normal="",background_color=(0,0,0,0),color=WHITE)
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
                "کلاس آنلاین": "online_classes",
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
        self.welcome.text=rtl_text(f"خوش آمدید، {getattr(self.app_state,'display_name','کاربر فراهوش')}")
        self.role_text.text=rtl_text(f"پنل {ROLE_TITLES.get(role,'کاربر')} • دسترسی فعال")
        self.grid.clear_widgets()
        total=len(items)
        for i,(title,route) in enumerate(items,1):
            real_route = self.resolve_module_route(role, title, route)
            card=PanelCard(title,i,total,self.desc(real_route),lambda *_a,r=real_route:self.open_route(r),
                           route=real_route,size_hint_y=None,height=dp(148))
            self.grid.add_widget(card)
            Clock.schedule_once(lambda _dt,card=card:Animation(opacity=1,d=.22,t="out_quad").start(card),i*.035)
        return True

    def open_route(self,route):
        app=App.get_running_app()
        if app is None or app.sm is None:
            return
        try:
            if str(route).startswith("panelhub:"):
                key=str(route).split(":",1)[1]
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
                screen=app.ensure_exam()
                if screen: app.sm.current="teacher_exams"
                return
            panel=app.ensure_panel()
            if panel is None:
                raise RuntimeError("پنل عملیاتی آماده نشد.")
            panel.set_route(route)
            app.sm.current="panel"
        except Exception as exc:
            print("DASHBOARD ROUTE ERROR:",repr(exc))
            try:
                self.role_text.text=rtl_text("خطا در باز کردن پنل؛ دوباره تلاش کنید.")
                self.role_text.color=(1,.35,.35,1)
                Clock.schedule_once(lambda _dt:self._restore_role_status(),2.5)
            except Exception:
                pass

    def _restore_role_status(self,*_):
        try:
            role=self.role()
            self.role_text.text=rtl_text(f"پنل {ROLE_TITLES.get(role,'کاربر')} • دسترسی فعال")
            self.role_text.color=(0.88,0.96,1,1)
        except Exception:
            pass

    def on_pre_enter(self,*_):
        if self.app_state is None or not getattr(self.app_state,"logged_in",False):
            if self.manager:self.manager.current="login"
            return
        self.refresh()

    def logout(self,*_):
        try:
            if self.app_state:self.app_state.logout()
        except Exception: pass
        if self.manager:self.manager.current="login"
