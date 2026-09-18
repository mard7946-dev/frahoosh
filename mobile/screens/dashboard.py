from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, LOGO_PATH, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

ROLE_ALIASES = {"admin":"manager","administrator":"manager","manager":"manager","مدیر":"manager","مدیریت":"manager","executive":"executive","معاون اجرایی":"executive","educational":"educational","training":"educational","معاون آموزشی":"educational","cultural":"cultural","پرورشی":"cultural","معاون پرورشی":"cultural","advisor":"advisor","counselor":"advisor","مشاور":"advisor","teacher":"teacher","teacher_staff":"teacher","دبیر":"teacher","معلم":"teacher","student":"student","دانش‌آموز":"student","دانش آموز":"student","parent":"parent","parent_guardian":"parent","guardian":"parent","ولی":"parent","اولیا":"parent"}
ROLE_TITLES = {"manager":"مدیریت", "executive":"معاون اجرایی", "educational":"معاون آموزشی", "cultural":"معاون پرورشی", "advisor":"مشاوره", "teacher":"دبیر", "student":"دانش‌آموز", "parent":"ولی"}
MANAGER_MENU = [("مدیریت","management"),("معاون آموزشی","educational"),("معاون اجرایی","executive"),("معاون پرورشی","cultural"),("مشاوره","advisor"),("دبیران","teachers"),("اولیا","parents"),("دانش‌آموزان","students"),("مالی","finance"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("نمونه کلاس هوشمند","smart_class_demo"),("آزمون آنلاین","teacher_exams"),("تابلو هوشمند","smart_board"),("دستیار هوش مصنوعی","ai"),("گزارش‌ها","reports"),("برنامه هفتگی","schedule"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")]
ROLE_MENU = {
"executive":[("معاون اجرایی","executive"),("دانش‌آموزان","students"),("اولیا","parents"),("کلاس‌های آنلاین","online"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"educational":[("معاون آموزشی","educational"),("دانش‌آموزان","students"),("دبیران","teachers"),("کلاس‌های آنلاین","online"),("آزمون آنلاین","teacher_exams"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("برنامه هفتگی","schedule"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"cultural":[("معاون پرورشی","cultural"),("دانش‌آموزان","students"),("اولیا","parents"),("مشارکت و فعالیت‌ها","participation"),("پرداخت آنلاین","payment"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"advisor":[("مشاوره","advisor"),("دانش‌آموزان","students"),("اولیا","parents"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"teacher":[("پنل دبیر","teacher"),("آزمون آنلاین","teacher_exams"),("دانش‌آموزان","students"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"student":[("پنل دانش‌آموز","student"),("آزمون‌های آنلاین","teacher_exams"),("برنامه هفتگی","schedule"),("وضعیت تحصیلی","student_info"),("مشارکت و فعالیت‌ها","participation"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")],
"parent":[("پنل اولیا","parent"),("وضعیت تحصیلی فرزند","student_info"),("مشارکت اولیا","participation"),("پرداخت آنلاین","payment"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")]
}
OPERATIONS_ROUTES = {"payment","online","messages"}

class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(6), **kwargs)
        with self.canvas.before:
            Color(1,1,1,.98); self.bg=RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self._sync,size=self._sync)
    def _sync(self,*_): self.bg.pos=self.pos; self.bg.size=self.size

class SwipeDeck(ScrollView):
    """Panel container without PageLayout/swipe navigation.
    Panels are opened from the hamburger drawer; this container only provides vertical scrolling.
    """
    def __init__(self, **kwargs):
        super().__init__(do_scroll_x=False, do_scroll_y=True, bar_width=dp(4), **kwargs)
        self.on_index_change=None
        self._box=BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(4), size_hint_y=None)
        self._box.bind(minimum_height=self._box.setter("height"))
        self.add_widget(self._box)
    def set_pages(self,pages):
        self._box.clear_widgets()
        for page in pages or []:
            page.size_hint_y=None
            self._box.add_widget(page)
        if callable(self.on_index_change):
            self.on_index_change(0,len(pages or []))

class DashboardScreen(Screen):
    def __init__(self,app_state=None,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.drawer_open=False; self._build_ui()
    def _label(self,text,size="13sp",color=SECONDARY,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="center" if center else "right",valign="middle"); w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w
    def _build_ui(self):
        root=FloatLayout()
        with root.canvas.before:
            Color(.94,.97,.985,1); self.bg=RoundedRectangle()
        root.bind(pos=lambda o,v:setattr(self.bg,"pos",v),size=lambda o,v:setattr(self.bg,"size",v))
        content=BoxLayout(orientation="vertical",padding=dp(11),spacing=dp(7))
        header=BoxLayout(size_hint_y=None,height=dp(58),spacing=dp(8))
        menu=Button(text="☰",font_size="26sp",background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(52)); menu.bind(on_release=self.toggle_drawer); header.add_widget(menu)
        logo=Image(source=LOGO_PATH,size_hint_x=None,width=dp(52),allow_stretch=True,keep_ratio=True); header.add_widget(logo)
        titles=BoxLayout(orientation="vertical"); titles.add_widget(self._label(APP_NAME,"20sp",PRIMARY,True)); titles.add_widget(self._label("سامانه هوشمند آموزشی یکپارچه مدرسه","10sp")); header.add_widget(titles); content.add_widget(header)
        welcome=Card(size_hint_y=None,height=dp(86),padding=dp(13)); self.welcome=self._label("خوش آمدید","19sp",PRIMARY,True); self.role_text=self._label("","11sp",SECONDARY,True); self.school_text=self._label(SCHOOL_NAME,"11sp",PRIMARY,True); welcome.add_widget(self.welcome); welcome.add_widget(self.role_text); welcome.add_widget(self.school_text); content.add_widget(welcome)
        self.status=self._label("","10sp",SUCCESS,True,True); content.add_widget(self.status); content.add_widget(self._label("پنل‌های سامانه","15sp",PRIMARY,True))
        self.frame=Card(size_hint_y=1,padding=dp(8),spacing=dp(4)); self.deck=SwipeDeck(size_hint_y=1); self.deck.on_index_change=self._deck_changed; self.frame.add_widget(self.deck); content.add_widget(self.frame)
        self.counter=self._label("","10sp",SUCCESS,True,True); content.add_widget(self.counter)
        content.add_widget(self._label(f"{SCHOOL_NAME} | سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}","9sp",SECONDARY,False,True))
        out=Button(text=rtl_text("خروج از حساب"),font_name=font_name(),font_size="12sp",background_normal="",background_color=(.65,.12,.14,1),color=WHITE,size_hint_y=None,height=dp(38)); out.bind(on_release=self.logout); content.add_widget(out)
        root.add_widget(content)
        self.drawer_layer=FloatLayout(size_hint=(1,1),opacity=0,disabled=True); self.drawer_layer.add_widget(Button(background_normal="",background_color=(0,0,0,.28),size_hint=(1,1),on_release=self.close_drawer))
        self.drawer=BoxLayout(orientation="vertical",padding=dp(11),spacing=dp(6),size_hint=(None,1),width=dp(285),pos_hint={"right":1}); self.drawer.add_widget(self._label(APP_NAME,"19sp",PRIMARY,True,True)); self.drawer.add_widget(self._label("منوی سامانه","10sp",SECONDARY,False,True))
        from kivy.uix.scrollview import ScrollView
        self.drawer_scroll=ScrollView(do_scroll_x=False); self.drawer_box=BoxLayout(orientation="vertical",spacing=dp(5),size_hint_y=None); self.drawer_box.bind(minimum_height=self.drawer_box.setter("height")); self.drawer_scroll.add_widget(self.drawer_box); self.drawer.add_widget(self.drawer_scroll)
        close=Button(text=rtl_text("بستن منو"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(40)); close.bind(on_release=self.close_drawer); self.drawer.add_widget(close); self.drawer_layer.add_widget(self.drawer); root.add_widget(self.drawer_layer); self.add_widget(root)
    def role(self):
        try: raw=self.app_state.role
        except Exception: raw="student"
        raw=str(raw or "student").strip().lower(); return ROLE_ALIASES.get(raw,raw)
    def items(self):
        r=self.role(); return MANAGER_MENU if r=="manager" else ROLE_MENU.get(r,[("صندوق پیام‌ها","messages"),("درباره برنامه","about")])
    def refresh(self):
        if self.app_state is None or not self.app_state.logged_in:return False
        role=self.role(); items=self.items(); name=str(getattr(self.app_state,"display_name","کاربر فراهوش") or "کاربر فراهوش")
        self.welcome.text=rtl_text(f"خوش آمدید، {name}"); self.role_text.text=rtl_text(f"پنل {ROLE_TITLES.get(role,'کاربر')} | دسترسی فعال"); self.school_text.text=rtl_text(SCHOOL_NAME); self.status.text=rtl_text(f"{len(items)} پنل فعال — هر پنل را انتخاب کنید تا وارد محیط عملیاتی آن شوید.")
        self.drawer_box.clear_widgets(); pages=[]
        for index,(title,route) in enumerate(items,1):
            page=Card(padding=dp(18),spacing=dp(9)); page.add_widget(self._label(title,"24sp",PRIMARY,True,True)); page.add_widget(self._label(f"پنل {index} از {len(items)}","10sp",SECONDARY,False,True)); page.add_widget(self._label(self.desc(route),"12sp",SECONDARY,False,True))
            enter=Button(text=rtl_text("ورود به این پنل"),font_name=font_name(),font_size="14sp",background_normal="",background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(52)); enter.bind(on_release=lambda *_args,r=route:self.open(r)); page.add_widget(enter); pages.append(page)
            db=Button(text=rtl_text(title),font_name=font_name(),font_size="13sp",background_normal="",background_color=(.08,.30,.48,1),color=WHITE,size_hint_y=None,height=dp(42)); db.bind(on_release=lambda *_args,r=route:self.open(r)); self.drawer_box.add_widget(db)
        self.deck.set_pages(pages); return True
    def _deck_changed(self,index,total): self.counter.text=rtl_text(f"پنل {index+1} از {total}") if total else rtl_text("پنلی وجود ندارد")
    def desc(self,route):
        return {"management":"مدیریت دانش‌آموزان، دبیران، کارکنان، کلاس‌ها و اطلاعات مدرسه.","educational":"کلاس‌ها، دروس، حضور و غیاب، نمرات، تکالیف و برنامه آموزشی.","executive":"پرونده دانش‌آموزان، اولیا، ثبت‌نام و امور اجرایی.","cultural":"فعالیت‌های فرهنگی و پرورشی و رویدادهای مدرسه.","advisor":"پرونده دانش‌آموز و پیگیری جلسات مشاوره.","teachers":"فهرست دبیران و کلاس‌های آنان.","students":"پرونده، نمرات و حضور و غیاب دانش‌آموزان.","parents":"اولیا و وضعیت تحصیلی فرزندان.","finance":"حساب‌ها، تراکنش‌ها و کمک‌های داوطلبانه.","payment":"گزینه‌های پرداخت و سوابق تراکنش.","online":"کلاس، جلسه، حضور و غیاب، گفت‌وگو و تخته کلاس.","smart_class_demo":"نمونه کامل کلاس هوشمند برای آشنایی مدیریت با تخته، فایل، صوت، تصویر، آزمون و تجربه هر نقش.","teacher_exams":"آزمون آنلاین و مدیریت سؤال و نمره.","smart_board":"محتوای آموزشی و فعالیت‌های تابلو هوشمند.","ai":"دستیار هوشمند، پرسش و گزارش‌های تحلیلی.","reports":"گزارش‌های آموزشی، نمرات و حضور و غیاب.","schedule":"برنامه هفتگی و برنامه امتحانات.","messages":"صندوق پیام‌ها و مخاطبان مدرسه.","settings":"تنظیمات حساب و اطلاعات مدرسه.","about":"اطلاعات سامانه فراهوش و نسخه برنامه."}.get(route,"ورود به بخش عملیاتی سامانه.")
    def toggle_drawer(self,*_): self.close_drawer() if self.drawer_open else self.open_drawer()
    def open_drawer(self,*_): self.drawer_open=True; self.drawer_layer.opacity=1; self.drawer_layer.disabled=False
    def close_drawer(self,*_): self.drawer_open=False; self.drawer_layer.opacity=0; self.drawer_layer.disabled=True
    def open(self,route):
        if self.app_state is None or not self.app_state.logged_in:
            if self.manager:self.manager.current="login"
            return
        self.close_drawer()
        if route=="about":
            if not self.manager.has_screen("about"):
                from mobile.screens.about import AboutScreen; self.manager.add_widget(AboutScreen(name="about",app_state=self.app_state))
            self.manager.current="about"; return
        if route=="smart_class_demo":
            if not self.manager.has_screen("module"):
                from mobile.screens.module import ModuleScreen; self.manager.add_widget(ModuleScreen(name="module",app_state=self.app_state))
            self.manager.get_screen("module").set_module(route,"dashboard"); self.manager.current="module"; return
        if route=="participation":
            if not self.manager.has_screen("participation"):
                from mobile.screens.participation import ParticipationScreen; self.manager.add_widget(ParticipationScreen(name="participation",app_state=self.app_state))
            self.manager.get_screen("participation").set_route(self.role()); self.manager.current="participation"; return
        if route=="teacher_exams":
            if not self.manager.has_screen("teacher_exams"):
                from mobile.screens.teacher_exams_v4 import TeacherExamsV4Screen; self.manager.add_widget(TeacherExamsV4Screen(name="teacher_exams",app_state=self.app_state))
            self.manager.current="teacher_exams"; return
        if route in OPERATIONS_ROUTES:
            if not self.manager.has_screen("operations"):
                from mobile.screens.operations import OperationsScreen; self.manager.add_widget(OperationsScreen(name="operations",app_state=self.app_state))
            self.manager.get_screen("operations").set_route(route); self.manager.current="operations"; return
        if not self.manager.has_screen("module"):
            from mobile.screens.module import ModuleScreen; self.manager.add_widget(ModuleScreen(name="module",app_state=self.app_state))
        self.manager.get_screen("module").set_module(route,"dashboard"); self.manager.current="module"
    def on_pre_enter(self,*_):
        try:
            if self.app_state is None or not self.app_state.logged_in:
                if self.manager:self.manager.current="login"
                return
        except Exception:
            if self.manager:self.manager.current="login"
            return
        self.refresh()
    def logout(self,*_):
        try:
            if self.app_state:self.app_state.logout()
        except Exception: pass
        if self.manager:self.manager.current="login"
