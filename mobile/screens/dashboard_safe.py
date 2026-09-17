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

MANAGER_MENU = [
    ("مدیریت", "management"), ("معاون آموزشی", "educational"), ("معاون اجرایی", "executive"),
    ("معاون پرورشی", "cultural"), ("مشاوره", "advisor"), ("دبیران", "teachers"),
    ("اولیا", "parents"), ("دانش‌آموزان", "students"), ("مالی", "finance"),
    ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("آزمون آنلاین", "teacher_exams"),
    ("تابلو هوشمند", "smart_board"), ("دستیار هوش مصنوعی", "ai"), ("گزارش‌ها", "reports"),
    ("برنامه هفتگی", "schedule"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"),
    ("درباره برنامه", "about")
]
ROLE_ALIASES = {
    "admin":"manager", "administrator":"manager", "manager":"manager", "مدیر":"manager", "مدیریت":"manager",
    "executive":"executive", "معاون اجرایی":"executive", "educational":"educational", "training":"educational",
    "معاون آموزشی":"educational", "cultural":"cultural", "پرورشی":"cultural", "معاون پرورشی":"cultural",
    "advisor":"advisor", "counselor":"advisor", "مشاور":"advisor", "teacher":"teacher", "teacher_staff":"teacher",
    "دبیر":"teacher", "معلم":"teacher", "student":"student", "دانش‌آموز":"student", "دانش آموز":"student",
    "parent":"parent", "parent_guardian":"parent", "guardian":"parent", "ولی":"parent", "اولیا":"parent"
}
ROLE_TITLES = {"manager":"مدیریت", "executive":"معاون اجرایی", "educational":"معاون آموزشی", "cultural":"معاون پرورشی", "advisor":"مشاوره", "teacher":"دبیر", "student":"دانش‌آموز", "parent":"ولی"}
ROLE_MENU = {
    "executive":[("معاون اجرایی","executive"),("دانش‌آموزان","students"),("اولیا","parents"),("کلاس‌های آنلاین","online"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "educational":[("معاون آموزشی","educational"),("دانش‌آموزان","students"),("دبیران","teachers"),("کلاس‌های آنلاین","online"),("آزمون آنلاین","teacher_exams"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("برنامه هفتگی","schedule"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "cultural":[("معاون پرورشی","cultural"),("دانش‌آموزان","students"),("اولیا","parents"),("مشارکت و فعالیت‌ها","participation"),("پرداخت آنلاین","payment"),("تابلو هوشمند","smart_board"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "advisor":[("مشاوره","advisor"),("دانش‌آموزان","students"),("اولیا","parents"),("گزارش‌ها","reports"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "teacher":[("پنل دبیر","teacher"),("آزمون آنلاین","teacher_exams"),("دانش‌آموزان","students"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("تنظیمات","settings"),("درباره برنامه","about")],
    "student":[("پنل دانش‌آموز","student"),("آزمون‌های آنلاین","teacher_exams"),("برنامه هفتگی","schedule"),("وضعیت تحصیلی","student_info"),("مشارکت و فعالیت‌ها","participation"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")],
    "parent":[("پنل اولیا","parent"),("وضعیت تحصیلی فرزند","student_info"),("مشارکت اولیا","participation"),("پرداخت آنلاین","payment"),("کلاس‌های آنلاین","online"),("تابلو هوشمند","smart_board"),("صندوق پیام‌ها","messages"),("درباره برنامه","about")]
}
OPERATIONS_ROUTES = {"payment", "online", "messages"}

class PanelCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(18), spacing=dp(10), **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, .985)
            self.bg = RoundedRectangle(radius=[dp(20)])
        self.bind(pos=self._sync, size=self._sync)
    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size

class SwipeArea(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pages = []
        self.index = 0
        self.on_change = None
        self._touch_start = None
        self._touch_moved = False
    def set_pages(self, pages):
        self.clear_widgets()
        self.pages = list(pages or [])
        self.index = 0
        if self.pages:
            self.add_widget(self.pages[0])
        self._notify()
    def _notify(self):
        if callable(self.on_change):
            self.on_change(self.index, len(self.pages))
    def show(self, index):
        if not self.pages:
            return
        index = max(0, min(int(index), len(self.pages)-1))
        if index == self.index and self.children:
            self._notify(); return
        self.clear_widgets()
        self.index = index
        self.add_widget(self.pages[index])
        self._notify()
    def next(self): self.show(self.index + 1)
    def previous(self): self.show(self.index - 1)
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start = touch.pos
            self._touch_moved = False
        return super().on_touch_down(touch)
    def on_touch_up(self, touch):
        handled = super().on_touch_up(touch)
        if self._touch_start is not None:
            dx = touch.x - self._touch_start[0]
            dy = touch.y - self._touch_start[1]
            self._touch_start = None
            if abs(dy) > dp(35) and abs(dy) > abs(dx) * 1.15:
                self._touch_moved = True
                if dy < 0: self.next()
                else: self.previous()
                return True
        return handled

class DashboardScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.drawer_open = False
        self._build_ui()
    def _label(self, text, size="13sp", color=SECONDARY, bold=False, center=False):
        w = Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color,
                  bold=bold, halign="center" if center else "right", valign="middle")
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w
    def _build_ui(self):
        root = FloatLayout()
        with root.canvas.before:
            Color(.94, .97, .985, 1)
            self.bg = RoundedRectangle()
        root.bind(pos=lambda o,v:setattr(self.bg,"pos",v), size=lambda o,v:setattr(self.bg,"size",v))
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        header = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        menu = Button(text="☰", font_size="25sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(50))
        menu.bind(on_release=self.toggle_drawer)
        header.add_widget(menu)
        try:
            header.add_widget(Image(source=LOGO_PATH, size_hint_x=None, width=dp(48), allow_stretch=True, keep_ratio=True))
        except Exception:
            pass
        titles = BoxLayout(orientation="vertical")
        titles.add_widget(self._label(APP_NAME, "19sp", PRIMARY, True))
        titles.add_widget(self._label("سامانه هوشمند آموزشی یکپارچه مدرسه", "9sp"))
        header.add_widget(titles)
        content.add_widget(header)
        welcome = PanelCard(size_hint_y=None, height=dp(76), padding=dp(10))
        self.welcome = self._label("خوش آمدید", "18sp", PRIMARY, True)
        self.role_text = self._label("", "10sp", SECONDARY, True)
        self.school_text = self._label(SCHOOL_NAME, "10sp", PRIMARY, True)
        welcome.add_widget(self.welcome); welcome.add_widget(self.role_text); welcome.add_widget(self.school_text)
        content.add_widget(welcome)
        self.status = self._label("", "9sp", SUCCESS, True, True)
        content.add_widget(self.status)
        content.add_widget(self._label("پنل‌های شما", "14sp", PRIMARY, True, True))
        self.frame = PanelCard(size_hint_y=1, padding=dp(8))
        self.deck = SwipeArea(size_hint=(1,1))
        self.deck.on_change = self._deck_changed
        self.frame.add_widget(self.deck)
        content.add_widget(self.frame)
        self.counter = self._label("", "9sp", SUCCESS, True, True)
        content.add_widget(self.counter)
        content.add_widget(self._label(f"{SCHOOL_NAME} | سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}", "8sp", SECONDARY, False, True))
        out = Button(text=rtl_text("خروج از حساب"), font_name=font_name(), font_size="11sp", background_normal="", background_color=(.65,.12,.14,1), color=WHITE, size_hint_y=None, height=dp(34))
        out.bind(on_release=self.logout); content.add_widget(out)
        root.add_widget(content)
        self.drawer_layer = FloatLayout(size_hint=(1,1), opacity=0, disabled=True)
        self.drawer_layer.add_widget(Button(background_normal="", background_color=(0,0,0,.28), size_hint=(1,1), on_release=self.close_drawer))
        self.drawer = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(5), size_hint=(None,1), width=dp(280), pos_hint={"right":1})
        self.drawer.add_widget(self._label(APP_NAME, "18sp", PRIMARY, True, True))
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView(do_scroll_x=False)
        self.drawer_box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self.drawer_box.bind(minimum_height=self.drawer_box.setter("height")); scroll.add_widget(self.drawer_box); self.drawer.add_widget(scroll)
        close = Button(text=rtl_text("بستن منو"), font_name=font_name(), background_normal="", background_color=PRIMARY, color=WHITE, size_hint_y=None, height=dp(38))
        close.bind(on_release=self.close_drawer); self.drawer.add_widget(close); self.drawer_layer.add_widget(self.drawer); root.add_widget(self.drawer_layer)
        self.add_widget(root)
    def role(self):
        try: raw = self.app_state.role
        except Exception: raw = "student"
        raw = str(raw or "student").strip().lower()
        return ROLE_ALIASES.get(raw, raw)
    def items(self):
        r = self.role()
        return MANAGER_MENU if r == "manager" else ROLE_MENU.get(r, [("صندوق پیام‌ها","messages"),("درباره برنامه","about")])
    def refresh(self):
        if self.app_state is None or not self.app_state.logged_in:
            return False
        items = self.items(); role = self.role(); name = str(getattr(self.app_state, "display_name", "کاربر فراهوش") or "کاربر فراهوش")
        self.welcome.text = rtl_text(f"خوش آمدید، {name}")
        self.role_text.text = rtl_text(f"پنل {ROLE_TITLES.get(role,'کاربر')} | دسترسی فعال")
        self.school_text.text = rtl_text(SCHOOL_NAME)
        self.status.text = rtl_text(f"{len(items)} پنل فعال — برای ورود، کارت پنل را لمس کنید.")
        self.drawer_box.clear_widgets(); pages=[]
        for i,(title,route) in enumerate(items,1):
            page = PanelCard()
            page.add_widget(self._label(title, "23sp", PRIMARY, True, True))
            page.add_widget(self._label(f"پنل {i} از {len(items)}", "10sp", SECONDARY, False, True))
            page.add_widget(self._label(self.desc(route), "11sp", SECONDARY, False, True))
            enter = Button(text=rtl_text("ورود به محیط پنل"), font_name=font_name(), font_size="13sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_y=None, height=dp(48))
            enter.bind(on_release=lambda *_args, r=route: self.open(r)); page.add_widget(enter); pages.append(page)
            db = Button(text=rtl_text(title), font_name=font_name(), font_size="12sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_y=None, height=dp(40))
            db.bind(on_release=lambda *_args, r=route: self.open(r)); self.drawer_box.add_widget(db)
        self.deck.set_pages(pages)
        return True
    def _deck_changed(self, index, total):
        self.counter.text = rtl_text(f"پنل {index+1} از {total}") if total else rtl_text("پنلی وجود ندارد")
    def desc(self, route):
        return {
            "management":"مدیریت دانش‌آموزان، دبیران، کارکنان و کلاس‌ها.", "educational":"دروس، نمرات، حضور و غیاب و برنامه آموزشی.",
            "executive":"پرونده دانش‌آموزان، اولیا و امور اجرایی.", "cultural":"فعالیت‌های فرهنگی و پرورشی مدرسه.",
            "advisor":"پرونده و پیگیری جلسات مشاوره.", "teachers":"فهرست دبیران و کلاس‌ها.", "students":"پرونده و وضعیت تحصیلی دانش‌آموزان.",
            "parents":"اولیا و وضعیت تحصیلی فرزندان.", "finance":"حساب‌ها، تراکنش‌ها و کمک‌های داوطلبانه.", "payment":"پرداخت و سوابق تراکنش.",
            "online":"کلاس، جلسه، حضور و غیاب و گفت‌وگو.", "teacher_exams":"آزمون آنلاین، سؤال و نمره.", "smart_board":"محتوای آموزشی تابلو هوشمند.",
            "ai":"دستیار هوشمند و گزارش‌های تحلیلی.", "reports":"گزارش‌های آموزشی و حضور و غیاب.", "schedule":"برنامه هفتگی و امتحانات.",
            "messages":"صندوق پیام‌ها.", "settings":"تنظیمات حساب و مدرسه.", "about":"اطلاعات سامانه فراهوش."
        }.get(route, "ورود به بخش عملیاتی سامانه.")
    def toggle_drawer(self,*_): self.close_drawer() if self.drawer_open else self.open_drawer()
    def open_drawer(self,*_): self.drawer_open=True; self.drawer_layer.opacity=1; self.drawer_layer.disabled=False
    def close_drawer(self,*_): self.drawer_open=False; self.drawer_layer.opacity=0; self.drawer_layer.disabled=True
    def open(self, route):
        if self.app_state is None or not self.app_state.logged_in:
            if self.manager: self.manager.current="login"
            return
        self.close_drawer()
        if route == "about":
            if not self.manager.has_screen("about"):
                from mobile.screens.about import AboutScreen; self.manager.add_widget(AboutScreen(name="about", app_state=self.app_state))
            self.manager.current="about"; return
        if route == "participation":
            if not self.manager.has_screen("participation"):
                from mobile.screens.participation import ParticipationScreen; self.manager.add_widget(ParticipationScreen(name="participation", app_state=self.app_state))
            self.manager.get_screen("participation").set_route(self.role()); self.manager.current="participation"; return
        if route == "teacher_exams":
            if not self.manager.has_screen("teacher_exams"):
                from mobile.screens.teacher_exams_v4 import TeacherExamsV4Screen; self.manager.add_widget(TeacherExamsV4Screen(name="teacher_exams", app_state=self.app_state))
            self.manager.current="teacher_exams"; return
        if route in OPERATIONS_ROUTES:
            if not self.manager.has_screen("operations"):
                from mobile.screens.operations import OperationsScreen; self.manager.add_widget(OperationsScreen(name="operations", app_state=self.app_state))
            self.manager.get_screen("operations").set_route(route); self.manager.current="operations"; return
        if not self.manager.has_screen("module"):
            from mobile.screens.module import ModuleScreen; self.manager.add_widget(ModuleScreen(name="module", app_state=self.app_state))
        self.manager.get_screen("module").set_module(route,"dashboard"); self.manager.current="module"
    def on_pre_enter(self,*_):
        try:
            if self.app_state is None or not self.app_state.logged_in:
                if self.manager: self.manager.current="login"
                return
        except Exception:
            if self.manager: self.manager.current="login"
            return
        self.refresh()
    def logout(self,*_):
        try:
            if self.app_state: self.app_state.logout()
        except Exception: pass
        if self.manager: self.manager.current="login"
