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

MANAGER_MENU = [
    ("مدیریت","management"),("معاون آموزشی","educational"),("معاون اجرایی","executive"),("معاون پرورشی","cultural"),
    ("مشاوره","advisor"),("دبیران","teachers"),("دانش‌آموزان","students"),("اولیا","parents"),
    ("مالی","finance"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("آزمون آنلاین","teacher_exams"),
    ("تابلو هوشمند","smart_board"),("هوش مصنوعی","ai"),("گزارش‌ها","reports"),("برنامه هفتگی","schedule"),
    ("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")
]

ROLE_MENU = {
    "executive":[("معاون اجرایی","executive"),("دانش‌آموزان","students"),("اولیا","parents"),("کلاس‌های آنلاین","online"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "educational":[("معاون آموزشی","educational"),("دانش‌آموزان","students"),("دبیران","teachers"),("کلاس‌های آنلاین","online"),("آزمون آنلاین","teacher_exams"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("برنامه هفتگی","schedule"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "cultural":[("معاون پرورشی","cultural"),("دانش‌آموزان","students"),("اولیا","parents"),("مشارکت و فعالیت‌ها","participation"),("پرداخت آنلاین","payment"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "advisor":[("مشاوره","advisor"),("دانش‌آموزان","students"),("اولیا","parents"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "teacher":[("پنل دبیر","teachers"),("آزمون آنلاین","teacher_exams"),("دانش‌آموزان","students"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "student":[("پنل دانش‌آموز","students"),("آزمون‌های آنلاین","teacher_exams"),("برنامه هفتگی","schedule"),("وضعیت تحصیلی","student_info"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")],
    "parent":[("پنل اولیا","parents"),("وضعیت تحصیلی فرزند","student_info"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")]
}

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
        self.add_widget(Label(text=rtl_text(title),font_name=font_name(),font_size="23sp",color=WHITE,bold=True,
                              halign="center",valign="middle",size_hint_y=None,height=dp(52)))
        self.add_widget(Label(text=rtl_text(f"پنل {index} از {total}"),font_name=font_name(),font_size="10sp",color=(0.55,0.85,1,1),
                              halign="center",valign="middle",size_hint_y=None,height=dp(26)))
        self.add_widget(Label(text=rtl_text(desc),font_name=font_name(),font_size="12sp",color=WHITE,
                              halign="center",valign="middle"))
        b=Button(text=rtl_text("ورود به پنل"),font_name=font_name(),font_size="14sp",background_normal="",
                 background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(50))
        b.bind(on_release=enter)
        self.add_widget(b)
    def _sync(self,*_):
        self.bg.pos=self.pos; self.bg.size=self.size

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
        # پنل‌های اصلی موبایل دقیقاً از ساختار پروژه مادر Noura گرفته شده‌اند:
        # مدیریت مدرسه، کادر اجرایی، مشاوره، دبیران، دانش‌آموزان و اولیا.
        # محتوای داخل هر پنل از ماژول‌های واقعی Supabase/shared catalog تغذیه می‌شود.
        r=self.role()
        mother_panels = [
            ("مدیریت مدرسه", "management"),
            ("کادر اجرایی", "executive"),
            ("مشاوره", "advisor"),
            ("دبیران", "teachers"),
            ("دانش‌آموزان", "students"),
            ("اولیا", "parents"),
        ]
        if r == "manager":
            return mother_panels
        role_panel = {
            "executive": ("کادر اجرایی", "executive"),
            "advisor": ("مشاوره", "advisor"),
            "teacher": ("دبیران", "teachers"),
            "student": ("دانش‌آموزان", "students"),
            "parent": ("اولیا", "parents"),
        }.get(r)
        return [role_panel] if role_panel else mother_panels

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
        nav=BoxLayout(size_hint=(.90,None),height=dp(56),pos_hint={"center_x":.5,"y":.018},spacing=dp(3),padding=dp(3))
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
            self.open_route(self.items()[0][1] if self.items() else "management")
        elif route=="messages":
            self.open_route("messages")
        elif route=="profile":
            self.open_route("settings")

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
            card=PanelCard(title,i,total,self.desc(route),lambda *_a,r=route:self.open_route(r),
                           route=route,size_hint_y=None,height=dp(154))
            self.grid.add_widget(card)
            Clock.schedule_once(lambda _dt,card=card:Animation(opacity=1,d=.22,t="out_quad").start(card),i*.035)
        return True

    def open_route(self,route):
        app=App.get_running_app()
        if app is None or app.sm is None:
            return
        try:
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
