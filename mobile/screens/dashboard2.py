from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.carousel import Carousel
from kivy.graphics import Color, RoundedRectangle

from mobile.config import APP_NAME, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

ROLE_ALIASES = {
    "admin": "manager", "administrator": "manager", "manager": "manager", "مدیر": "manager", "مدیریت": "manager",
    "executive": "executive", "معاون اجرایی": "executive", "educational": "educational", "training": "educational", "معاون آموزشی": "educational",
    "cultural": "cultural", "پرورشی": "cultural", "معاون پرورشی": "cultural", "advisor": "advisor", "counselor": "advisor", "مشاور": "advisor",
    "teacher": "teacher", "teacher_staff": "teacher", "دبیر": "teacher", "معلم": "teacher", "student": "student", "دانش‌آموز": "student", "دانش آموز": "student",
    "parent": "parent", "parent_guardian": "parent", "guardian": "parent", "ولی": "parent", "اولیا": "parent",
}
ROLE_TITLES = {"manager":"مدیریت", "executive":"معاون اجرایی", "educational":"معاون آموزشی", "cultural":"معاون پرورشی", "advisor":"مشاوره", "teacher":"دبیر", "student":"دانش‌آموز", "parent":"ولی"}
MANAGER_MENU = [
    ("مدیریت", "management"), ("معاون آموزشی", "educational"), ("معاون اجرایی", "executive"), ("معاون پرورشی", "cultural"),
    ("مشاوره", "advisor"), ("دبیران", "teachers"), ("اولیا", "parents"), ("دانش‌آموزان", "students"), ("مالی", "finance"),
    ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("آزمون آنلاین", "teacher_exams"), ("تابلو هوشمند", "smart_board"),
    ("دستیار هوش مصنوعی", "ai"), ("گزارش‌ها", "reports"), ("برنامه هفتگی", "schedule"), ("صندوق پیام‌ها", "messages"),
    ("تنظیمات", "settings"), ("درباره برنامه", "about")
]
ROLE_MENU = {
    "executive": [("معاون اجرایی", "executive"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("کلاس‌های آنلاین", "online"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "educational": [("معاون آموزشی", "educational"), ("دانش‌آموزان", "students"), ("دبیران", "teachers"), ("کلاس‌های آنلاین", "online"), ("آزمون آنلاین", "teacher_exams"), ("تابلو هوشمند", "smart_board"), ("گزارش‌ها", "reports"), ("برنامه هفتگی", "schedule"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "cultural": [("معاون پرورشی", "cultural"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("مشارکت و فعالیت‌ها", "participation"), ("پرداخت آنلاین", "payment"), ("تابلو هوشمند", "smart_board"), ("گزارش‌ها", "reports"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "advisor": [("مشاوره", "advisor"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("گزارش‌ها", "reports"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "teacher": [("پنل دبیر", "teacher"), ("آزمون آنلاین", "teacher_exams"), ("دانش‌آموزان", "students"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "student": [("پنل دانش‌آموز", "student"), ("آزمون‌های آنلاین", "teacher_exams"), ("برنامه هفتگی", "schedule"), ("وضعیت تحصیلی", "student_info"), ("مشارکت و فعالیت‌ها", "participation"), ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "parent": [("پنل اولیا", "parent"), ("وضعیت تحصیلی فرزند", "student_info"), ("مشارکت اولیا", "participation"), ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
}
OPS = {"payment", "online", "messages"}
SCHOOL = "دبیرستان سردارشهیدحاجی زاده ۲"

class _Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(5), **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 0.98)
            self.bg = RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self._sync, size=self._sync)
    def _sync(self, *_):
        self.bg.pos = self.pos; self.bg.size = self.size

class DashboardScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs); self.app_state = app_state; self.drawer_open = False; self._build()
    def _label(self, text, size="13sp", color=SECONDARY, bold=False, center=False):
        w = Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, bold=bold,
                  halign="center" if center else "right", valign="middle")
        w.bind(size=lambda o,v:setattr(o, "text_size", v)); return w
    def _role(self):
        raw = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
        return ROLE_ALIASES.get(raw, raw)
    def _items(self):
        role = self._role(); return MANAGER_MENU if role == "manager" else ROLE_MENU.get(role, [("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")])
    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        menu = Button(text="☰", font_size="26sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(54)); menu.bind(on_release=self.toggle_drawer); header.add_widget(menu)
        titles = BoxLayout(orientation="vertical"); titles.add_widget(self._label(APP_NAME, "20sp", PRIMARY, True)); titles.add_widget(self._label("سامانه هوشمند مدیریت مدرسه", "10sp")); header.add_widget(titles); root.add_widget(header)
        welcome = _Card(size_hint_y=None, height=dp(82)); self.welcome_title=self._label("خوش آمدید", "18sp", PRIMARY, True); self.role_label=self._label("", "11sp", SECONDARY, True); self.school_label=self._label("", "11sp", PRIMARY, True); welcome.add_widget(self.welcome_title); welcome.add_widget(self.role_label); welcome.add_widget(self.school_label); root.add_widget(welcome)
        root.add_widget(self._label("پنل‌های سامانه", "15sp", PRIMARY, True))
        self.panel_frame = _Card(size_hint_y=1, padding=dp(9))
        self.panel_hint = self._label("با کشیدن انگشت به بالا یا پایین، هر بار یک پنل جابه‌جا می‌شود.", "10sp", SECONDARY, False, True); self.panel_frame.add_widget(self.panel_hint)
        self.carousel = Carousel(direction="top", loop=False, size_hint_y=1, anim_move_duration=0.20)
        self.panel_frame.add_widget(self.carousel); root.add_widget(self.panel_frame)
        self.counter = self._label("", "10sp", SUCCESS, True, True); root.add_widget(self.counter)
        root.add_widget(self._label(f"{SCHOOL} | سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}", "10sp", SECONDARY, False, True))
        logout=Button(text=rtl_text("خروج از حساب"),font_name=font_name(),font_size="12sp",background_normal="",background_color=(0.65,0.12,0.14,1),color=WHITE,size_hint_y=None,height=dp(40)); logout.bind(on_release=self.logout); root.add_widget(logout)
        self.add_widget(root)
        self.drawer = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6), size_hint=(None, 1), width=dp(285), pos_hint={"right":1}, opacity=0, disabled=True)
        with self.drawer.canvas.before: Color(0.97,0.985,0.99,1); self.drawer.bg=RoundedRectangle(radius=[dp(16)])
        self.drawer.bind(pos=lambda o,v:setattr(o.bg,"pos",v), size=lambda o,v:setattr(o.bg,"size",v)); self.drawer.add_widget(self._label(APP_NAME,"19sp",PRIMARY,True,True)); self.drawer_scroll=__import__('kivy.uix.scrollview',fromlist=['ScrollView']).ScrollView(do_scroll_x=False); self.drawer_box=BoxLayout(orientation="vertical",spacing=dp(6),size_hint_y=None); self.drawer_box.bind(minimum_height=self.drawer_box.setter("height")); self.drawer_scroll.add_widget(self.drawer_box); self.drawer.add_widget(self.drawer_scroll); close=Button(text=rtl_text("بستن منو"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(42)); close.bind(on_release=self.close_drawer); self.drawer.add_widget(close); self.add_widget(self.drawer)
    def on_pre_enter(self, *args):
        if self.app_state is None or not self.app_state.logged_in:
            if self.manager: self.manager.current="login"
            return
        self.refresh()
    def refresh(self):
        if self.app_state is None or not self.app_state.logged_in: return False
        items=self._items(); name=str(getattr(self.app_state,"display_name","کاربر فراهوش") or "کاربر فراهوش"); role=self._role()
        self.welcome_title.text=rtl_text(f"خوش آمدید، {name}"); self.role_label.text=rtl_text(f"پنل {ROLE_TITLES.get(role,'کاربر')} | دسترسی فعال"); self.school_label.text=rtl_text(f"{SCHOOL} | سال {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}"); self.counter.text=rtl_text(f"پنل ۱ از {len(items)}")
        self.carousel.clear_widgets(); self.drawer_box.clear_widgets()
        for i,(title,route) in enumerate(items,1):
            page=_Card(padding=dp(16), spacing=dp(9)); page.add_widget(self._label(title,"22sp",PRIMARY,True,True)); page.add_widget(self._label(f"پنل {i} از {len(items)}","11sp",SECONDARY,False,True)); page.add_widget(self._label(self._description(route),"13sp",SECONDARY,False,True)); b=Button(text=rtl_text("ورود به پنل و اجرای عملیات"),font_name=font_name(),font_size="14sp",background_normal="",background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(52)); b.bind(on_release=lambda *_ ,r=route:self._open(r)); page.add_widget(b); self.carousel.add_widget(page)
            db=Button(text=rtl_text(title),font_name=font_name(),font_size="12sp",background_normal="",background_color=(0.08,0.30,0.48,1),color=WHITE,size_hint_y=None,height=dp(42)); db.bind(on_release=lambda *_ ,r=route:self._open(r)); self.drawer_box.add_widget(db)
        self.carousel.index=0
        return True
    def _description(self,route):
        return {"management":"مدیریت کاربران، دانش‌آموزان، دبیران، کلاس‌ها، آمار و اطلاعات مدرسه.","educational":"کلاس‌ها، دروس، حضور و غیاب، نمرات، تکالیف و برنامه‌ریزی آموزشی.","executive":"پرونده دانش‌آموزان، اولیا، ثبت‌نام و امور اجرایی مدرسه.","cultural":"فعالیت‌های فرهنگی و پرورشی، رویدادها و مشارکت دانش‌آموزان.","advisor":"پرونده دانش‌آموز، جلسات و پیگیری‌های مشاوره.","teachers":"فهرست دبیران، کارکنان و کلاس‌های دبیران.","students":"فهرست و پرونده تحصیلی دانش‌آموزان، حضور و غیاب و نمرات.","parents":"اولیا، فرزندان و وضعیت تحصیلی.","finance":"حساب‌ها، تراکنش‌ها و کمک‌های داوطلبانه.","payment":"گزینه‌های پرداخت و سوابق تراکنش.","online":"ساخت و مدیریت کلاس آنلاین، جلسه، حضور و غیاب، گفت‌وگو و ورود به جلسه.","teacher_exams":"ساخت آزمون، پنج نوع سؤال، تصحیح خودکار، زمان‌بندی و اشتراک امن.","smart_board":"محتوای آموزشی و ابزارهای تعاملی تابلو.","ai":"پرسش، تحلیل آموزشی و گزارش هوشمند.","reports":"گزارش‌های مدیریتی، آموزشی، حضور و غیاب و نمرات.","schedule":"برنامه هفتگی کلاس‌ها و دبیران.","messages":"ارسال، دریافت و پیگیری پیام‌ها.","settings":"تنظیمات حساب، مدرسه و دسترسی‌ها.","about":"اطلاعات برنامه و مدرسه."}.get(route,"اطلاعات و عملیات این بخش بر اساس نقش کاربر نمایش داده می‌شود.")
    def _open(self,route):
        if not self.manager: return
        if route=="about":
            from mobile.screens.about import AboutScreen; s=self.manager.get_screen("about") if self.manager.has_screen("about") else AboutScreen(name="about",app_state=self.app_state); 
            if not self.manager.has_screen("about"): self.manager.add_widget(s)
            self.manager.current="about"; return
        if route=="participation":
            from mobile.screens.participation import ParticipationScreen; s=self.manager.get_screen("participation") if self.manager.has_screen("participation") else ParticipationScreen(name="participation",app_state=self.app_state); 
            if not self.manager.has_screen("participation"): self.manager.add_widget(s)
            s.set_route(self._role()); self.manager.current="participation"; return
        if route=="teacher_exams":
            from mobile.screens.teacher_exams_v4 import TeacherExamsV4Screen; s=self.manager.get_screen("teacher_exams") if self.manager.has_screen("teacher_exams") else TeacherExamsV4Screen(name="teacher_exams",app_state=self.app_state); 
            if not self.manager.has_screen("teacher_exams"): self.manager.add_widget(s)
            self.manager.current="teacher_exams"; return
        if route in OPS:
            from mobile.screens.operations import OperationsScreen; s=self.manager.get_screen("operations") if self.manager.has_screen("operations") else OperationsScreen(name="operations",app_state=self.app_state); 
            if not self.manager.has_screen("operations"): self.manager.add_widget(s)
            s.set_route(route); self.manager.current="operations"; return
        from mobile.screens.module import ModuleScreen; s=self.manager.get_screen("module") if self.manager.has_screen("module") else ModuleScreen(name="module",app_state=self.app_state); 
        if not self.manager.has_screen("module"): self.manager.add_widget(s)
        s.set_module(route,"dashboard"); self.manager.current="module"
    def toggle_drawer(self,*_):
        if self.drawer_open:self.close_drawer()
        else:self.open_drawer()
    def open_drawer(self,*_):self.drawer_open=True;self.drawer.opacity=1;self.drawer.disabled=False
    def close_drawer(self,*_):self.drawer_open=False;self.drawer.opacity=0;self.drawer.disabled=True
    def logout(self,*_):
        try:self.app_state.logout()
        except Exception:pass
        if self.manager:self.manager.current="login"
