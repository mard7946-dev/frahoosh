from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.carousel import Carousel
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

SCHOOL="دبیرستان سردارشهیدحاجی زاده ۲"
ALIASES={"admin":"manager","administrator":"manager","مدیر":"manager","مدیریت":"manager","executive":"executive","معاون اجرایی":"executive","educational":"educational","معاون آموزشی":"educational","cultural":"cultural","معاون پرورشی":"cultural","advisor":"advisor","مشاور":"advisor","teacher":"teacher","دبیر":"teacher","معلم":"teacher","student":"student","دانش‌آموز":"student","دانش آموز":"student","parent":"parent","ولی":"parent","اولیا":"parent"}
TITLES={"manager":"مدیریت","executive":"معاون اجرایی","educational":"معاون آموزشی","cultural":"معاون پرورشی","advisor":"مشاوره","teacher":"دبیر","student":"دانش‌آموز","parent":"ولی"}
MANAGER=[("مدیریت","management"),("معاون آموزشی","educational"),("معاون اجرایی","executive"),("معاون پرورشی","cultural"),("مشاوره","advisor"),("دبیران","teachers"),("اولیا","parents"),("دانش‌آموزان","students"),("مالی","finance"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("آزمون آنلاین","teacher_exams"),("تابلو هوشمند","smart_board"),("دستیار هوش مصنوعی","ai"),("گزارش‌ها","reports"),("برنامه هفتگی","schedule"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")]
ROLES={
"executive":[("معاون اجرایی","executive"),("دانش‌آموزان","students"),("اولیا","parents"),("کلاس‌های آنلاین","online"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"educational":[("معاون آموزشی","educational"),("دانش‌آموزان","students"),("دبیران","teachers"),("کلاس‌های آنلاین","online"),("آزمون آنلاین","teacher_exams"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("برنامه هفتگی","schedule"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"cultural":[("معاون پرورشی","cultural"),("دانش‌آموزان","students"),("اولیا","parents"),("مشارکت و فعالیت‌ها","participation"),("پرداخت آنلاین","payment"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"advisor":[("مشاوره","advisor"),("دانش‌آموزان","students"),("اولیا","parents"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"teacher":[("پنل دبیر","teacher"),("آزمون آنلاین","teacher_exams"),("دانش‌آموزان","students"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
"student":[("پنل دانش‌آموز","student"),("آزمون‌های آنلاین","teacher_exams"),("برنامه هفتگی","schedule"),("وضعیت تحصیلی","student_info"),("مشارکت و فعالیت‌ها","participation"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")],
"parent":[("پنل اولیا","parent"),("وضعیت تحصیلی فرزند","student_info"),("مشارکت اولیا","participation"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")]
}

class Card(BoxLayout):
    def __init__(self,**kw):
        super().__init__(orientation="vertical",padding=dp(13),spacing=dp(8),**kw)
        with self.canvas.before: Color(1,1,1,.98); self.bg=RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self.sync,size=self.sync)
    def sync(self,*_): self.bg.pos=self.pos; self.bg.size=self.size

class DashboardScreen(Screen):
    def __init__(self,app_state=None,**kw): super().__init__(**kw); self.app_state=app_state; self.drawer_open=False; self.build()
    def label(self,text,size="13sp",color=SECONDARY,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="center" if center else "right",valign="middle"); w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w
    def role(self):
        r=str(getattr(self.app_state,"role","student") or "student").strip().lower(); return ALIASES.get(r,r)
    def items(self):
        r=self.role(); return MANAGER if r=="manager" else ROLES.get(r,[("صندوق پیام‌ها","messages"),("درباره برنامه","about")])
    def build(self):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(7)); h=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(7)); menu=Button(text="☰",font_size="26sp",background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(54)); menu.bind(on_release=self.toggle); h.add_widget(menu); t=BoxLayout(orientation="vertical"); t.add_widget(self.label(APP_NAME,"20sp",PRIMARY,True)); t.add_widget(self.label("سامانه هوشمند مدیریت مدرسه","10sp")); h.add_widget(t); root.add_widget(h)
        w=Card(size_hint_y=None,height=dp(80)); self.welcome=self.label("خوش آمدید","18sp",PRIMARY,True); self.role_text=self.label(""); self.school=self.label(SCHOOL,"11sp",PRIMARY,True); w.add_widget(self.welcome);w.add_widget(self.role_text);w.add_widget(self.school);root.add_widget(w);root.add_widget(self.label("پنل‌های سامانه","15sp",PRIMARY,True))
        self.frame=Card(size_hint_y=1,padding=dp(8)); self.frame.add_widget(self.label("با حرکت انگشت بالا یا پایین، پنل‌ها یکی‌یکی جابه‌جا می‌شوند.","10sp",SECONDARY,False,True)); self.carousel=Carousel(direction="top",loop=False,anim_move_duration=.2);self.frame.add_widget(self.carousel);root.add_widget(self.frame);self.counter=self.label("","10sp",SUCCESS,True,True);root.add_widget(self.counter);root.add_widget(self.label(f"{SCHOOL} | سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}","10sp",SECONDARY,False,True));out=Button(text=rtl_text("خروج از حساب"),font_name=font_name(),background_normal="",background_color=(.65,.12,.14,1),color=WHITE,size_hint_y=None,height=dp(40));out.bind(on_release=self.logout);root.add_widget(out);self.add_widget(root)
        self.drawer=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(6),size_hint=(None,1),width=dp(285),pos_hint={"right":1},opacity=0,disabled=True);self.drawer.add_widget(self.label(APP_NAME,"19sp",PRIMARY,True,True));self.ds=ScrollView(do_scroll_x=False);self.db=BoxLayout(orientation="vertical",spacing=dp(6),size_hint_y=None);self.db.bind(minimum_height=self.db.setter("height"));self.ds.add_widget(self.db);self.drawer.add_widget(self.ds);c=Button(text=rtl_text("بستن منو"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(42));c.bind(on_release=self.close);self.drawer.add_widget(c);self.add_widget(self.drawer)
    def on_pre_enter(self,*_):
        if not self.app_state or not self.app_state.logged_in:
            if self.manager:self.manager.current="login"
        else:self.refresh()
    def refresh(self):
        items=self.items();r=self.role();name=str(getattr(self.app_state,"display_name","کاربر فراهوش") or "کاربر فراهوش");self.welcome.text=rtl_text(f"خوش آمدید، {name}");self.role_text.text=rtl_text(f"پنل {TITLES.get(r,'کاربر')} | دسترسی فعال");self.school.text=rtl_text(SCHOOL);self.counter.text=rtl_text(f"پنل ۱ از {len(items)}");self.carousel.clear_widgets();self.db.clear_widgets()
        for i,(title,route) in enumerate(items,1):
            p=Card(padding=dp(16));p.add_widget(self.label(title,"23sp",PRIMARY,True,True));p.add_widget(self.label(f"پنل {i} از {len(items)}","11sp",SECONDARY,False,True));p.add_widget(self.label(self.desc(route),"13sp",SECONDARY,False,True));b=Button(text=rtl_text("ورود و اجرای عملیات واقعی"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(52));b.bind(on_release=lambda *_ ,x=route:self.open(x));p.add_widget(b);self.carousel.add_widget(p);d=Button(text=rtl_text(title),font_name=font_name(),background_normal="",background_color=(.08,.30,.48,1),color=WHITE,size_hint_y=None,height=dp(42));d.bind(on_release=lambda *_ ,x=route:self.open(x));self.db.add_widget(d)
        self.carousel.index=0;return True
    def desc(self,r):
        return {"management":"مدیریت دانش‌آموزان، دبیران، کارکنان، کلاس‌ها و اطلاعات مدرسه.","educational":"کلاس‌ها، حضور و غیاب، نمرات، تکالیف و برنامه آموزشی.","executive":"پرونده دانش‌آموزان، اولیا، ثبت‌نام و امور اجرایی.","cultural":"فعالیت‌های فرهنگی و پرورشی و رویدادها.","advisor":"پرونده و پیگیری جلسات مشاوره.","teachers":"فهرست دبیران و کلاس‌های آنان.","students":"پرونده، نمرات و حضور و غیاب دانش‌آموزان.","parents":"اولیا و وضعیت تحصیلی فرزندان.","finance":"حساب‌ها، تراکنش‌ها و کمک‌های داوطلبانه.","payment":"گزینه‌های پرداخت و سوابق تراکنش.","online":"کلاس، جلسه، حضور و غیاب، گفت‌وگو، تخته و اطلاع غیبت.","teacher_exams":"پنج نوع سؤال، تصحیح خودکار، زمان‌بندی، اشتراک و آزمون واقعی.","smart_board":"محتوای آموزشی و ابزارهای تعاملی.","ai":"پرسش و تحلیل آموزشی.","reports":"گزارش‌های مدرسه و آموزشی.","schedule":"برنامه هفتگی کلاس‌ها و دبیران.","messages":"صندوق پیام‌ها و ارسال پیام.","settings":"تنظیمات حساب و مدرسه.","about":"اطلاعات برنامه و مدرسه."}.get(r,"امکانات اجرایی این بخش بر اساس نقش کاربر.")
    def open(self,r):
        if not self.manager:return
        try:
            if r=="online":
                from mobile.screens.online_class import OnlineClassScreen; s=self.manager.get_screen("online") if self.manager.has_screen("online") else OnlineClassScreen(name="online",app_state=self.app_state); 
                if not self.manager.has_screen("online"):self.manager.add_widget(s)
                self.manager.current="online";return
            if r=="teacher_exams":
                if self.role()=="manager":
                    from mobile.screens.manager_exams import ManagerExamsScreen; s=self.manager.get_screen("teacher_exams") if self.manager.has_screen("teacher_exams") else ManagerExamsScreen(name="teacher_exams",app_state=self.app_state)
                else:
                    from mobile.screens.teacher_exams_v4 import TeacherExamsV4Screen; s=self.manager.get_screen("teacher_exams") if self.manager.has_screen("teacher_exams") else TeacherExamsV4Screen(name="teacher_exams",app_state=self.app_state)
                if not self.manager.has_screen("teacher_exams"):self.manager.add_widget(s)
                self.manager.current="teacher_exams";return
            if r=="about":
                from mobile.screens.about import AboutScreen;s=self.manager.get_screen("about") if self.manager.has_screen("about") else AboutScreen(name="about",app_state=self.app_state)
                if not self.manager.has_screen("about"):self.manager.add_widget(s)
                self.manager.current="about";return
            if r=="participation":
                from mobile.screens.participation import ParticipationScreen;s=self.manager.get_screen("participation") if self.manager.has_screen("participation") else ParticipationScreen(name="participation",app_state=self.app_state)
                if not self.manager.has_screen("participation"):self.manager.add_widget(s)
                s.set_route(self.role());self.manager.current="participation";return
            if r in {"payment","messages"}:
                from mobile.screens.operations import OperationsScreen;s=self.manager.get_screen("operations") if self.manager.has_screen("operations") else OperationsScreen(name="operations",app_state=self.app_state)
                if not self.manager.has_screen("operations"):self.manager.add_widget(s)
                s.set_route(r);self.manager.current="operations";return
            from mobile.screens.module import ModuleScreen;s=self.manager.get_screen("module") if self.manager.has_screen("module") else ModuleScreen(name="module",app_state=self.app_state)
            if not self.manager.has_screen("module"):self.manager.add_widget(s)
            s.set_module(r,"dashboard");self.manager.current="module"
        except Exception as exc:print("DASHBOARD OPEN ERROR",repr(exc))
    def toggle(self,*_):
        if self.drawer_open:self.close()
        else:self.drawer_open=True;self.drawer.opacity=1;self.drawer.disabled=False
    def close(self,*_):self.drawer_open=False;self.drawer.opacity=0;self.drawer.disabled=True
    def logout(self,*_):
        try:self.app_state.logout()
        except Exception:pass
        if self.manager:self.manager.current="login"
