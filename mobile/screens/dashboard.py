from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout

from mobile.config import APP_NAME, SCHOOL_NAME, BACKGROUND_PATH
from mobile.ui import font_name, rtl_text

ROLE_ALIASES = {
    "admin": "manager", "administrator": "manager", "manager": "manager",
    "مدیر": "manager", "مدیریت": "manager",
    "executive": "executive", "معاون اجرایی": "executive",
    "educational": "educational", "training": "educational", "معاون آموزشی": "educational",
    "cultural": "cultural", "پرورشی": "cultural", "معاون پرورشی": "cultural",
    "advisor": "advisor", "counselor": "advisor", "مشاور": "advisor", "مشاوره": "advisor",
    "teacher": "teacher", "teacher_staff": "teacher", "دبیر": "teacher", "معلم": "teacher",
    "student": "student", "دانش‌آموز": "student", "دانش آموز": "student",
    "parent": "parent", "parent_guardian": "parent", "guardian": "parent", "ولی": "parent", "اولیا": "parent",
}

ROLE_TITLES = {
    "manager": "مدیریت", "executive": "معاون اجرایی", "educational": "معاون آموزشی",
    "cultural": "معاون پرورشی", "advisor": "مشاوره", "teacher": "دبیر",
    "student": "دانش‌آموز", "parent": "ولی",
}

MANAGER_MENU = [
    ("مدیریت", "management"), ("معاون آموزشی", "educational"), ("معاون اجرایی", "executive"),
    ("معاون پرورشی", "cultural"), ("مشاوره", "advisor"), ("دبیران", "teachers"),
    ("اولیا", "parents"), ("دانش‌آموزان", "students"), ("مالی", "finance"),
    ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"),
    ("دستیار هوش مصنوعی", "ai"), ("گزارش‌ها", "reports"), ("صندوق پیام‌ها", "messages"),
    ("تنظیمات", "settings"), ("درباره برنامه", "about"),
]

ROLE_MENU = {
    "executive": [("معاون اجرایی", "executive"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "educational": [("معاون آموزشی", "educational"), ("دانش‌آموزان", "students"), ("دبیران", "teachers"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("گزارش‌ها", "reports"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "cultural": [("معاون پرورشی", "cultural"), ("دانش‌آموزان", "students"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "advisor": [("مشاوره", "advisor"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "teacher": [("پنل دبیر", "teacher"), ("دانش‌آموزان", "students"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "student": [("پنل دانش‌آموز", "student"), ("برنامه هفتگی", "schedule"), ("وضعیت تحصیلی", "student_info"), ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "parent": [("پنل اولیا", "parent"), ("وضعیت تحصیلی فرزند", "student_info"), ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
}

class HamburgerButton(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._color = Color(1, 1, 1, 1)
            self._line1 = Line(width=2.2); self._line2 = Line(width=2.2); self._line3 = Line(width=2.2)
        self.bind(pos=self._update_lines, size=self._update_lines)
    def _update_lines(self, *_):
        left = self.x + self.width * .18; right = self.x + self.width * .82
        for line, factor in ((self._line1,.70),(self._line2,.50),(self._line3,.30)):
            y = self.y + self.height * factor; line.points = [left,y,right,y]

class DashboardScreen(Screen):
    drawer_width = NumericProperty(0)
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs); self.app_state = app_state; self.drawer_open = False; self.logout_button = None; self._build_ui()

    def _build_ui(self):
        self.clear_widgets(); root = FloatLayout()
        self.background = Image(source=BACKGROUND_PATH, allow_stretch=True, keep_ratio=False, size_hint=(1,1), pos_hint={"x":0,"y":0}); root.add_widget(self.background)
        self.overlay_background = Widget()
        with self.overlay_background.canvas: self.overlay_color = Color(.02,.08,.16,.18); self.overlay_rect = Rectangle()
        self.overlay_background.bind(pos=self._update_overlay, size=self._update_overlay); root.add_widget(self.overlay_background)
        self.header = FloatLayout(size_hint=(1,None),height=dp(150),pos_hint={"top":1})
        with self.header.canvas: self.header_color=Color(.02,.15,.28,.82); self.header_rect=RoundedRectangle(radius=[0])
        self.header.bind(pos=self._update_header,size=self._update_header); root.add_widget(self.header)
        self.menu_button=HamburgerButton(size_hint=(None,None),size=(dp(62),dp(62)),pos_hint={"right":.98,"top":.94}); self.menu_button.bind(on_touch_down=self._hamburger_touch); self.header.add_widget(self.menu_button)
        self.title_label=Label(text=rtl_text("سامانه هوشمند مدیریت مدرسه"),font_name=font_name(),font_size="23sp",bold=True,color=(1,1,1,1),halign="right",valign="middle",size_hint=(.78,None),height=dp(45),pos_hint={"right":.91,"top":.78}); self.title_label.bind(size=self._sync_text_size); self.header.add_widget(self.title_label)
        self.school_label=Label(text=rtl_text(SCHOOL_NAME),font_name=font_name(),font_size="15sp",color=(.86,.96,1,1),halign="right",valign="middle",size_hint=(.78,None),height=dp(34),pos_hint={"right":.91,"top":.48}); self.school_label.bind(size=self._sync_text_size); self.header.add_widget(self.school_label)
        self.welcome_card=FloatLayout(size_hint=(.90,None),height=dp(150),pos_hint={"center_x":.5,"top":.78})
        with self.welcome_card.canvas: self.welcome_color=Color(1,1,1,.92); self.welcome_rect=RoundedRectangle(radius=[dp(22)])
        self.welcome_card.bind(pos=self._update_welcome,size=self._update_welcome); root.add_widget(self.welcome_card)
        self.welcome_title=Label(text=rtl_text("خوش آمدید"),font_name=font_name(),font_size="23sp",bold=True,color=(.02,.18,.32,1),halign="right",valign="middle",size_hint=(.88,None),height=dp(48),pos_hint={"right":.95,"top":.82}); self.welcome_title.bind(size=self._sync_text_size); self.welcome_card.add_widget(self.welcome_title)
        self.role_label=Label(text="",font_name=font_name(),font_size="16sp",color=(.10,.30,.42,1),halign="right",valign="middle",size_hint=(.88,None),height=dp(40),pos_hint={"right":.95,"top":.52}); self.role_label.bind(size=self._sync_text_size); self.welcome_card.add_widget(self.role_label)
        self.status_label=Label(text=rtl_text("سامانه آماده استفاده است"),font_name=font_name(),font_size="14sp",color=(.12,.40,.35,1),halign="right",valign="middle",size_hint=(.88,None),height=dp(32),pos_hint={"right":.95,"top":.28}); self.status_label.bind(size=self._sync_text_size); self.welcome_card.add_widget(self.status_label)
        self.hint_card=FloatLayout(size_hint=(.90,None),height=dp(100),pos_hint={"center_x":.5,"y":.08})
        with self.hint_card.canvas: self.hint_color=Color(.02,.16,.28,.78); self.hint_rect=RoundedRectangle(radius=[dp(20)])
        self.hint_card.bind(pos=self._update_hint,size=self._update_hint); root.add_widget(self.hint_card)
        self.hint_label=Label(text=rtl_text("برای مشاهده امکانات سامانه، دکمه سه‌خطی بالای صفحه را لمس کنید."),font_name=font_name(),font_size="14sp",color=(1,1,1,.95),halign="center",valign="middle",size_hint=(.90,.80),pos_hint={"center_x":.5,"center_y":.5}); self.hint_label.bind(size=self._sync_text_size); self.hint_card.add_widget(self.hint_label)
        self.drawer_overlay=Button(text="",background_normal="",background_color=(0,0,0,.42),size_hint=(1,1),pos_hint={"x":0,"y":0},opacity=0,disabled=True); self.drawer_overlay.bind(on_release=self.close_drawer); root.add_widget(self.drawer_overlay)
        self.drawer=FloatLayout(size_hint=(None,1),width=dp(320),x=-dp(320),pos_hint={"y":0})
        with self.drawer.canvas: self.drawer_color=Color(.025,.10,.18,.99); self.drawer_rect=RoundedRectangle(radius=[0])
        self.drawer.bind(pos=self._update_drawer,size=self._update_drawer); root.add_widget(self.drawer); self._build_drawer(); self.add_widget(root)

    def _build_drawer(self):
        self.drawer.clear_widgets()
        self.drawer.add_widget(Label(text=rtl_text(APP_NAME),font_name=font_name(),font_size="25sp",bold=True,color=(1,1,1,1),size_hint=(1,None),height=dp(60),pos_hint={"top":.98}))
        self.menu_role=Label(text="",font_name=font_name(),font_size="13sp",color=(.65,.86,.96,1),size_hint=(.92,None),height=dp(38),pos_hint={"center_x":.5,"top":.90}); self.drawer.add_widget(self.menu_role)
        self.menu_scroll=ScrollView(size_hint=(.94,.72),pos_hint={"center_x":.5,"top":.82},do_scroll_x=False)
        self.menu_box=BoxLayout(orientation="vertical",spacing=dp(8),padding=[dp(4),dp(4),dp(4),dp(12)],size_hint_y=None); self.menu_box.bind(minimum_height=self.menu_box.setter("height")); self.menu_scroll.add_widget(self.menu_box); self.drawer.add_widget(self.menu_scroll)
        self.logout_button=Button(text=rtl_text("خروج از حساب"),font_name=font_name(),font_size="15sp",background_normal="",background_color=(.55,.12,.14,1),color=(1,1,1,1),size_hint=(.88,None),height=dp(48),pos_hint={"center_x":.5,"y":.025}); self.logout_button.bind(on_release=self.logout); self.drawer.add_widget(self.logout_button)

    def _get_role(self):
        raw = ""
        try:
            raw = self.app_state.role
        except Exception as exc:
            print("DASHBOARD ROLE ERROR:", repr(exc))
        raw = str(raw or "student").strip().lower()
        return ROLE_ALIASES.get(raw, raw)

    def _get_display_name(self):
        try:
            return str(self.app_state.display_name or "کاربر فراهوش")
        except Exception as exc:
            print("DASHBOARD NAME ERROR:", repr(exc)); return "کاربر فراهوش"

    def refresh(self):
        role=self._get_role(); display_name=self._get_display_name(); role_title=ROLE_TITLES.get(role,"کاربر")
        self.welcome_title.text=rtl_text(f"خوش آمدید، {display_name}"); self.role_label.text=rtl_text(f"نقش کاربری: {role_title}"); self.menu_role.text=rtl_text(f"{display_name} | {role_title}"); self._populate_menu(role)

    def _populate_menu(self, role):
        self.menu_box.clear_widgets(); items=MANAGER_MENU if role=="manager" else ROLE_MENU.get(role,[("صندوق پیام‌ها","messages"),("درباره برنامه","about")])
        for title,route in items:
            button=Button(text=rtl_text(title),font_name=font_name(),font_size="14sp",background_normal="",background_color=(.04,.22,.34,1),color=(1,1,1,1),halign="right",valign="middle",size_hint_y=None,height=dp(46)); button.bind(size=self._sync_text_size); button.bind(on_release=lambda btn,r=route:self._menu_selected(r)); self.menu_box.add_widget(button)

    def _hamburger_touch(self, widget, touch):
        if widget.collide_point(*touch.pos):
            if touch.is_mouse_scrolling: return False
            self.toggle_drawer(); return True
        return False

    def toggle_drawer(self): self.close_drawer() if self.drawer_open else self.open_drawer()
    def open_drawer(self,*_):
        self.drawer_open=True; self.drawer_overlay.disabled=False; self.drawer_overlay.opacity=1; Animation(x=0,duration=.25,t="out_quad").start(self.drawer)
    def close_drawer(self,*_):
        if not self.drawer_open: return
        self.drawer_open=False; animation=Animation(x=-dp(320),duration=.22,t="in_quad"); animation.bind(on_complete=self._drawer_closed); animation.start(self.drawer); self.drawer_overlay.disabled=True; self.drawer_overlay.opacity=0
    def _drawer_closed(self,*_): self.drawer.x=-dp(320)
    def _menu_selected(self,route):
        self.close_drawer()
        if route=="about": self._show_about(); return
        self._go_to("module",module=route)
    def _go_to(self,screen_name,**kwargs):
        if not self.manager: return
        try:
            if not self.manager.has_screen(screen_name): self.status_label.text=rtl_text("صفحه موردنظر در دسترس نیست."); return
            screen=self.manager.get_screen(screen_name); module_name=kwargs.get("module")
            if hasattr(screen,"set_module"): screen.set_module(module_name)
            elif hasattr(screen,"load_module"): screen.load_module(module_name)
            self.manager.current=screen_name
        except Exception as exc:
            print("DASHBOARD NAV ERROR:",repr(exc)); self.status_label.text=rtl_text("خطا در باز کردن بخش موردنظر.")
    def _show_about(self): self.status_label.text=rtl_text("سامانه هوشمند آموزشی یکپارچه مدرسه")
    def logout(self,*_):
        try: self.app_state.logout()
        except Exception as exc: print("LOGOUT ERROR:",repr(exc))
        if self.manager: self.manager.current="login"
    def _sync_text_size(self, widget, value): widget.text_size=value
    def _update_overlay(self,*_): self.overlay_rect.pos=self.overlay_background.pos; self.overlay_rect.size=self.overlay_background.size
    def _update_header(self,*_): self.header_rect.pos=self.header.pos; self.header_rect.size=self.header.size
    def _update_welcome(self,*_): self.welcome_rect.pos=self.welcome_card.pos; self.welcome_rect.size=self.welcome_card.size
    def _update_hint(self,*_): self.hint_rect.pos=self.hint_card.pos; self.hint_rect.size=self.hint_card.size
    def _update_drawer(self,*_): self.drawer_rect.pos=self.drawer.pos; self.drawer_rect.size=self.drawer.size
