from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_ID, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text

ROLE_ALIASES = {
    "admin": "manager", "administrator": "manager", "manager": "manager", "مدیر": "manager", "مدیریت": "manager",
    "executive": "executive", "معاون اجرایی": "executive", "educational": "educational", "training": "educational", "معاون آموزشی": "educational",
    "cultural": "cultural", "پرورشی": "cultural", "معاون پرورشی": "cultural", "advisor": "advisor", "counselor": "advisor", "مشاور": "advisor",
    "teacher": "teacher", "teacher_staff": "teacher", "دبیر": "teacher", "معلم": "teacher", "student": "student", "دانش‌آموز": "student",
    "دانش آموز": "student", "parent": "parent", "parent_guardian": "parent", "guardian": "parent", "ولی": "parent", "اولیا": "parent",
}
ROLE_TITLES = {"manager": "مدیریت", "executive": "معاون اجرایی", "educational": "معاون آموزشی", "cultural": "معاون پرورشی", "advisor": "مشاوره", "teacher": "دبیر", "student": "دانش‌آموز", "parent": "ولی"}
MANAGER_MENU = [
    ("مدیریت", "management"), ("معاون آموزشی", "educational"), ("معاون اجرایی", "executive"), ("معاون پرورشی", "cultural"),
    ("مشاوره", "advisor"), ("دبیران", "teachers"), ("اولیا", "parents"), ("دانش‌آموزان", "students"), ("مالی", "finance"),
    ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("دستیار هوش مصنوعی", "ai"),
    ("گزارش‌ها", "reports"), ("برنامه هفتگی", "schedule"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")
]
ROLE_MENU = {
    "executive": [("معاون اجرایی", "executive"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("کلاس‌های آنلاین", "online"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "educational": [("معاون آموزشی", "educational"), ("دانش‌آموزان", "students"), ("دبیران", "teachers"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("گزارش‌ها", "reports"), ("برنامه هفتگی", "schedule"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "cultural": [("معاون پرورشی", "cultural"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("مشارکت و فعالیت‌ها", "participation"), ("پرداخت آنلاین", "payment"), ("تابلو هوشمند", "smart_board"), ("گزارش‌ها", "reports"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "advisor": [("مشاوره", "advisor"), ("دانش‌آموزان", "students"), ("اولیا", "parents"), ("گزارش‌ها", "reports"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "teacher": [("پنل دبیر", "teacher"), ("آزمون آنلاین", "teacher_exams"), ("دانش‌آموزان", "students"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("تنظیمات", "settings"), ("درباره برنامه", "about")],
    "student": [("پنل دانش‌آموز", "student"), ("آزمون‌های آنلاین", "teacher_exams"), ("برنامه هفتگی", "schedule"), ("وضعیت تحصیلی", "student_info"), ("مشارکت و فعالیت‌ها", "participation"), ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
    "parent": [("پنل اولیا", "parent"), ("وضعیت تحصیلی فرزند", "student_info"), ("مشارکت اولیا", "participation"), ("پرداخت آنلاین", "payment"), ("کلاس‌های آنلاین", "online"), ("تابلو هوشمند", "smart_board"), ("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")],
}
OPERATIONS_ROUTES = {"payment", "online", "messages"}
DEFAULT_SCHOOL_NAME = "دبیرستان سردارشهیدحاجی زاده ۲"


class _Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(5), **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 0.97)
            self.bg = RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class DashboardScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.drawer_open = False
        self._build_ui()

    def on_pre_enter(self, *args):
        try:
            if self.app_state is None or not self.app_state.logged_in:
                if self.manager:
                    self.manager.current = "login"
                return
        except Exception:
            if self.manager:
                self.manager.current = "login"
            return
        self.refresh()
        return super().on_pre_enter(*args)

    def _label(self, text, size="14sp", color=SECONDARY, bold=False, halign="right"):
        w = Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, bold=bold, halign=halign, valign="middle")
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _panel_button(self, title, route):
        b = Button(text=rtl_text(title), font_name=font_name(), font_size="14sp", background_normal="", background_color=(0.10, 0.35, 0.62, 1), color=WHITE, size_hint_y=None, height=dp(58))
        b.bind(on_release=lambda btn, r=route: self._menu_selected(r))
        return b

    def _build_ui(self):
        root = FloatLayout()
        with root.canvas.before:
            Color(0.94, 0.97, 0.985, 1)
            self.bg = RoundedRectangle()
        root.bind(pos=lambda o, v: setattr(self.bg, "pos", v), size=lambda o, v: setattr(self.bg, "size", v))

        self.content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(9))
        header = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(9))
        self.menu_button = Button(text="☰", font_size="27sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(56))
        self.menu_button.bind(on_release=self.toggle_drawer)
        header.add_widget(self.menu_button)
        titles = BoxLayout(orientation="vertical")
        titles.add_widget(self._label(APP_NAME, "21sp", PRIMARY, True))
        titles.add_widget(self._label("سامانه هوشمند مدیریت مدرسه", "11sp", SECONDARY))
        header.add_widget(titles)
        self.content.add_widget(header)

        self.welcome = _Card(size_hint_y=None, height=dp(105))
        self.welcome_title = self._label("خوش آمدید", "21sp", PRIMARY, True)
        self.welcome.add_widget(self.welcome_title)
        self.role_label = self._label("", "13sp", SECONDARY, True)
        self.welcome.add_widget(self.role_label)
        self.school_label = self._label("", "12sp", PRIMARY, True)
        self.welcome.add_widget(self.school_label)
        self.content.add_widget(self.welcome)

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_y=1)
        body = BoxLayout(orientation="vertical", spacing=dp(9), padding=[dp(2), dp(3)], size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))
        self.home_status = self._label("", "12sp", SUCCESS, True)
        body.add_widget(self.home_status)
        body.add_widget(self._label("پنل‌های سامانه", "17sp", PRIMARY, True))
        self.panel_grid = GridLayout(cols=1, spacing=dp(8), padding=[dp(2), dp(2)], size_hint_y=None)
        self.panel_grid.bind(minimum_height=self.panel_grid.setter("height"))
        body.add_widget(self.panel_grid)
        body.add_widget(self._label("صفحه پنل‌ها قابل حرکت است؛ با کشیدن انگشت به بالا و پایین همه بخش‌ها را ببینید. با لمس هر پنل، بخش واقعی و اطلاعات مربوط به آن باز می‌شود.", "12sp", SECONDARY))
        info = _Card(size_hint_y=None, height=dp(86))
        info.add_widget(self._label("اطلاعات مدرسه", "14sp", PRIMARY, True))
        info.add_widget(self._label(f"سال تحصیلی: {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}", "12sp"))
        info.add_widget(self._label(f"مدرسه: {SCHOOL_NAME or DEFAULT_SCHOOL_NAME}", "12sp"))
        body.add_widget(info)
        scroll.add_widget(body)
        self.content.add_widget(scroll)

        logout = Button(text=rtl_text("خروج از حساب"), font_name=font_name(), font_size="13sp", background_normal="", background_color=(0.65, 0.12, 0.14, 1), color=WHITE, size_hint_y=None, height=dp(44))
        logout.bind(on_release=self.logout)
        self.content.add_widget(logout)
        root.add_widget(self.content)

        self.drawer_layer = FloatLayout(size_hint=(1, 1), opacity=0, disabled=True)
        self.drawer_layer.add_widget(Button(background_normal="", background_color=(0, 0, 0, 0.28), size_hint=(1, 1), on_release=self.close_drawer))
        drawer = BoxLayout(orientation="vertical", padding=[dp(12), dp(12)], spacing=dp(7), size_hint=(None, 1), width=dp(285), pos_hint={"right": 1})
        with drawer.canvas.before:
            Color(0.97, 0.985, 0.99, 1)
            drawer.bg = RoundedRectangle(radius=[dp(18)])
        drawer.bind(pos=lambda o, v: setattr(o.bg, "pos", v), size=lambda o, v: setattr(o.bg, "size", v))
        drawer.add_widget(self._label(APP_NAME, "21sp", PRIMARY, True, "center"))
        drawer.add_widget(self._label("منوی سامانه", "12sp", SECONDARY, False, "center"))
        self.drawer_scroll = ScrollView(do_scroll_x=False)
        self.drawer_menu = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.drawer_menu.bind(minimum_height=self.drawer_menu.setter("height"))
        self.drawer_scroll.add_widget(self.drawer_menu)
        drawer.add_widget(self.drawer_scroll)
        drawer_close = Button(text=rtl_text("بستن منو"), font_name=font_name(), font_size="13sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_y=None, height=dp(44))
        drawer_close.bind(on_release=self.close_drawer)
        drawer.add_widget(drawer_close)
        self.drawer_layer.add_widget(drawer)
        root.add_widget(self.drawer_layer)
        self.add_widget(root)

    def _get_role(self):
        try:
            raw = self.app_state.role
        except Exception:
            raw = "student"
        raw = str(raw or "student").strip().lower()
        return ROLE_ALIASES.get(raw, raw)

    def _get_display_name(self):
        try:
            return str(self.app_state.display_name or "کاربر فراهوش")
        except Exception:
            return "کاربر فراهوش"

    def refresh(self):
        if self.app_state is None or not self.app_state.logged_in:
            return False
        role = self._get_role()
        name = self._get_display_name()
        items = MANAGER_MENU if role == "manager" else ROLE_MENU.get(role, [("صندوق پیام‌ها", "messages"), ("درباره برنامه", "about")])
        self.welcome_title.text = rtl_text(f"خوش آمدید، {name}")
        self.role_label.text = rtl_text(f"پنل {ROLE_TITLES.get(role, 'کاربر')} | دسترسی فعال")
        self.school_label.text = rtl_text(f"{SCHOOL_NAME or DEFAULT_SCHOOL_NAME} | سال {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}")
        self.home_status.text = rtl_text(f"{len(items)} بخش فعال است — برای ورود روی هر پنل بزنید.")
        self._populate_drawer(items)
        self.panel_grid.clear_widgets()
        for title, route in items:
            self.panel_grid.add_widget(self._panel_button(title, route))
        return True

    def _populate_drawer(self, items):
        self.drawer_menu.clear_widgets()
        for title, route in items:
            b = Button(text=rtl_text(title), font_name=font_name(), font_size="14sp", background_normal="", background_color=(0.08, 0.30, 0.48, 1), color=WHITE, size_hint_y=None, height=dp(46))
            b.bind(on_release=lambda btn, r=route: self._menu_selected(r))
            self.drawer_menu.add_widget(b)

    def toggle_drawer(self, *_):
        if self.drawer_open:
            self.close_drawer()
        else:
            self.open_drawer()

    def open_drawer(self, *_):
        self.drawer_open = True
        self.drawer_layer.opacity = 1
        self.drawer_layer.disabled = False

    def close_drawer(self, *_):
        self.drawer_open = False
        self.drawer_layer.opacity = 0
        self.drawer_layer.disabled = True

    def _open_operations(self, route):
        if not self.manager.has_screen("operations"):
            from mobile.screens.operations import OperationsScreen
            self.manager.add_widget(OperationsScreen(name="operations", app_state=self.app_state))
        self.manager.get_screen("operations").set_route(route)
        self.close_drawer()
        self.manager.current = "operations"

    def _open_exam(self):
        if not self.manager.has_screen("teacher_exams"):
            from mobile.screens.teacher_exams_v4 import TeacherExamsV4Screen
            self.manager.add_widget(TeacherExamsV4Screen(name="teacher_exams", app_state=self.app_state))
        self.close_drawer()
        self.manager.current = "teacher_exams"

    def _open_about(self):
        if not self.manager.has_screen("about"):
            from mobile.screens.about import AboutScreen
            self.manager.add_widget(AboutScreen(name="about", app_state=self.app_state))
        self.close_drawer()
        self.manager.current = "about"

    def _open_participation(self):
        if not self.manager.has_screen("participation"):
            from mobile.screens.participation import ParticipationScreen
            self.manager.add_widget(ParticipationScreen(name="participation", app_state=self.app_state))
        s = self.manager.get_screen("participation")
        s.set_route(self._get_role())
        self.close_drawer()
        self.manager.current = "participation"

    def _open_module(self, route):
        if not self.manager.has_screen("module"):
            from mobile.screens.module import ModuleScreen
            self.manager.add_widget(ModuleScreen(name="module", app_state=self.app_state))
        m = self.manager.get_screen("module")
        m.set_module(route, "dashboard")
        self.close_drawer()
        self.manager.current = "module"

    def _menu_selected(self, route):
        if self.app_state is None or not self.app_state.logged_in:
            if self.manager:
                self.manager.current = "login"
            return
        if route == "about":
            self._open_about(); return
        if route == "participation":
            self._open_participation(); return
        if route == "teacher_exams":
            self._open_exam(); return
        if route in OPERATIONS_ROUTES:
            self._open_operations(route); return
        if self.manager:
            self._open_module(route)

    def logout(self, *_):
        try:
            if self.app_state is not None:
                self.app_state.logout()
        except Exception:
            pass
        if self.manager:
            self.manager.current = "login"
