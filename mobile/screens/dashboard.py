from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, SCHOOL_NAME, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

ROLE_ALIASES={"admin":"manager","administrator":"manager","manager":"manager","مدیر":"manager","مدیریت":"manager","executive":"executive","معاون اجرایی":"executive","educational":"educational","training":"educational","معاون آموزشی":"educational","cultural":"cultural","پرورشی":"cultural","معاون پرورشی":"cultural","advisor":"advisor","counselor":"advisor","مشاور":"advisor","teacher":"teacher","teacher_staff":"teacher","دبیر":"teacher","معلم":"teacher","student":"student","دانش‌آموز":"student","دانش آموز":"student","parent":"parent","parent_guardian":"parent","guardian":"parent","ولی":"parent","اولیا":"parent"}
ROLE_TITLES={"manager":"مدیریت","executive":"معاون اجرایی","educational":"معاون آموزشی","cultural":"معاون پرورشی","advisor":"مشاوره","teacher":"دبیر","student":"دانش‌آموز","parent":"ولی"}
MANAGER_MENU=[("مدیریت","management"),("معاون آموزشی","educational"),("معاون اجرایی","executive"),("معاون پرورشی","cultural"),("مشاوره","advisor"),("دبیران","teachers"),("اولیا","parents"),("دانش‌آموزان","students"),("مالی","finance"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("دستیار هوش مصنوعی","ai"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")]
ROLE_MENU={"executive":[("معاون اجرایی","executive"),("دانش‌آموزان","students"),("اولیا","parents"),("کلاس‌های آنلاین","online"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],"educational":[("معاون آموزشی","educational"),("دانش‌آموزان","students"),("دبیران","teachers"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],"cultural":[("معاون پرورشی","cultural"),("دانش‌آموزان","students"),("اولیا","parents"),("پرداخت آنلاین","payment"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],"advisor":[("مشاوره","advisor"),("دانش‌آموزان","students"),("اولیا","parents"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],"teacher":[("پنل دبیر","teacher"),("آزمون آنلاین","teacher_exams"),("دانش‌آموزان","students"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],"student":[("پنل دانش‌آموز","student"),("آزمون‌های آنلاین","teacher_exams"),("برنامه هفتگی","schedule"),("وضعیت تحصیلی","student_info"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")],"parent":[("پنل اولیا","parent"),("وضعیت تحصیلی فرزند","student_info"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")]} 
LIVE_ROUTES={"management","educational","executive","cultural","advisor","teachers","students","parents","teacher","student","parent","finance","payment","online","smart_board","ai","messages","reports","schedule","student_info","settings"}
OPERATIONS_ROUTES={"payment","online","messages"}


class DashboardScreen(Screen):
    def __init__(self,app_state=None,**kwargs):
        super().__init__(**kwargs)
        self.app_state=app_state
        self._build_ui()

    def on_pre_enter(self, *args):
        """Last-line route guard for direct attempts to open the dashboard."""
        try:
            if self.app_state is None or not self.app_state.logged_in:
                if self.manager:
                    self.manager.current = "login"
                return
        except Exception:
            if self.manager:
                self.manager.current = "login"
            return
        return super().on_pre_enter(*args)

    def _make_label(self,text,size,color=SECONDARY,bold=False):
        l=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="center",valign="middle"); l.bind(size=lambda o,v:setattr(o,"text_size",v)); return l
    def _build_ui(self):
        root=BoxLayout(orientation="vertical",padding=[dp(18)]*4,spacing=dp(10)); h=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(105),spacing=dp(4)); h.add_widget(self._make_label(APP_NAME,"30sp",PRIMARY,True)); h.add_widget(self._make_label("سامانه هوشمند آموزشی یکپارچه مدرسه","18sp",PRIMARY,True)); h.add_widget(self._make_label(SCHOOL_NAME,"13sp",SECONDARY)); root.add_widget(h)
        self.welcome_label=self._make_label("خوش آمدید","22sp",PRIMARY,True); self.role_label=self._make_label("","15sp"); self.status_label=self._make_label("سامانه آماده استفاده است","13sp",SUCCESS); root.add_widget(self.welcome_label); root.add_widget(self.role_label); root.add_widget(self.status_label)
        scroll=ScrollView(do_scroll_x=False); self.menu_box=GridLayout(cols=1,spacing=dp(9),padding=[dp(2),dp(8),dp(2),dp(8)],size_hint_y=None); self.menu_box.bind(minimum_height=self.menu_box.setter("height")); scroll.add_widget(self.menu_box); root.add_widget(scroll)
        b=Button(text=rtl_text("خروج از حساب"),font_name=font_name(),font_size="15sp",background_normal="",background_color=(0.65,0.12,0.14,1),color=WHITE,size_hint_y=None,height=dp(48)); b.bind(on_release=self.logout); root.add_widget(b); self.add_widget(root)
    def _get_role(self):
        try: raw=self.app_state.role
        except Exception: raw="student"
        return ROLE_ALIASES.get(str(raw or "student").strip().lower(),str(raw or "student").strip().lower())
    def _get_display_name(self):
        try:return str(self.app_state.display_name or "کاربر فراهوش")
        except Exception:return "کاربر فراهوش"
    def refresh(self):
        if self.app_state is None or not self.app_state.logged_in:
            return False
        role=self._get_role(); name=self._get_display_name(); title=ROLE_TITLES.get(role,"کاربر"); self.welcome_label.text=rtl_text(f"خوش آمدید، {name}"); self.role_label.text=rtl_text(f"ورود موفق به پنل {title} | {SCHOOL_NAME}"); self.status_label.text=rtl_text(f"{name} عزیز، امکانات اختصاصی پنل {title} در اختیار شماست."); self._populate_menu(role); return True
    def _populate_menu(self,role):
        self.menu_box.clear_widgets(); items=MANAGER_MENU if role=="manager" else ROLE_MENU.get(role,[("صندوق پیام‌ها","messages"),("درباره برنامه","about")])
        for title,route in items:
            b=Button(text=rtl_text(title),font_name=font_name(),font_size="15sp",background_normal="",background_color=(0.08,0.30,0.48,1),color=WHITE,size_hint_y=None,height=dp(50)); b.bind(on_release=lambda btn,r=route:self._menu_selected(r)); self.menu_box.add_widget(b)
    def _open_operations(self,route):
        if not self.manager.has_screen("operations"):
            from mobile.screens.operations import OperationsScreen; self.manager.add_widget(OperationsScreen(name="operations",app_state=self.app_state))
        s=self.manager.get_screen("operations"); s.set_route(route); self.manager.current="operations"
    def _open_exam(self):
        if not self.manager.has_screen("teacher_exams"):
            from mobile.screens.teacher_exams_v4 import TeacherExamsV4Screen; self.manager.add_widget(TeacherExamsV4Screen(name="teacher_exams",app_state=self.app_state))
        self.manager.current="teacher_exams"
    def _menu_selected(self,route):
        if self.app_state is None or not self.app_state.logged_in:
            if self.manager:self.manager.current="login"
            return
        if route=="about": self.status_label.text=rtl_text("فراهوش؛ سامانه هوشمند آموزشی یکپارچه مدرسه"); return
        if route=="teacher_exams": self._open_exam(); return
        if not self.manager:return
        try:
            if route in OPERATIONS_ROUTES: self._open_operations(route); return
            if route in LIVE_ROUTES:
                if not self.manager.has_screen("live_panel"):
                    from mobile.screens.live_panel import LivePanelScreen; self.manager.add_widget(LivePanelScreen(name="live_panel",app_state=self.app_state))
                p=self.manager.get_screen("live_panel"); p.set_panel(route); self.manager.current="live_panel"; return
            if not self.manager.has_screen("module"):
                from mobile.screens.module import ModuleScreen; self.manager.add_widget(ModuleScreen(name="module",app_state=self.app_state))
            m=self.manager.get_screen("module"); m.set_module(route); self.manager.current="module"
        except Exception as exc: print("DASHBOARD NAV ERROR:",repr(exc)); self.status_label.text=rtl_text("این بخش آماده استفاده است؛ داده‌های آن از سامانه مدرسه خوانده می‌شوند.")
    def logout(self,*_):
        try:
            if self.app_state is not None:self.app_state.logout()
        except Exception:pass
        if self.manager:self.manager.current="login"
