from kivy.app import App
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from mobile.config import CARD, PRIMARY, SECONDARY, SUCCESS, WHITE, APP_NAME, SCHOOL_NAME, SCHOOL_YEAR
from mobile.ui import font_name, rtl_text
from mobile.screens.module_workspace import ModuleWorkspaceScreen, SUBMENUS, FRIENDLY

MODULE_DESCRIPTIONS = {
    "management": "مدیریت یکپارچه مدرسه، کاربران، کارکنان و اطلاعات پایه.",
    "educational": "امور آموزشی، کلاس‌ها، حضور و غیاب، نمرات و آزمون‌ها.",
    "executive": "پرونده‌ها، کارکنان، کلاس‌ها و عملیات اجرایی.",
    "cultural": "فعالیت‌های پرورشی، فرهنگی و رویدادهای مدرسه.",
    "advisor": "سوابق، جلسات و پیگیری‌های مشاوره.",
    "teachers": "کلاس، حضور و غیاب، نمره، تکلیف و آزمون دبیران.",
    "students": "اطلاعات، نمرات، حضور و غیاب و فعالیت‌های دانش‌آموزان.",
    "parents": "اطلاعات فرزند، نمرات، حضور و غیاب و ارتباط با مدرسه.",
    "finance": "حساب‌ها، تراکنش‌ها، کمک‌های داوطلبانه و پرداخت‌ها.",
    "online": "کلاس‌های آنلاین، جلسات، حضور، تخته و ارتباط کلاس.",
    "teacher_exams": "ساخت و مدیریت آزمون، بانک سؤال و زمان‌بندی.",
    "smart_board": "محتوای آموزشی، فعالیت‌ها، آزمونک و تخته کلاس.",
    "messages": "صندوق پیام، مخاطبان و وضعیت خواندن.",
    "ai": "پرسش‌ها، جلسات و گزارش‌های هوشمند.",
    "reports": "کارنامه، نمرات، حضور و گزارش‌های آموزشی.",
    "schedule": "برنامه هفتگی و برنامه امتحانات.",
}

class FeatureCard(BoxLayout):
    def __init__(self, title, subtitle, callback, number, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(12), dp(9)], spacing=dp(4),
                         size_hint_y=None, height=dp(132), **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, .985)
            self.bg = RoundedRectangle(radius=[dp(16)])
        self.bind(pos=self._sync, size=self._sync)
        top = BoxLayout(size_hint_y=None, height=dp(27), spacing=dp(7))
        badge = Label(text=rtl_text(str(number)), font_name=font_name(), font_size="10sp",
                      bold=True, color=WHITE, size_hint_x=None, width=dp(30),
                      halign="center", valign="middle")
        with badge.canvas.before:
            Color(*PRIMARY)
            badge_bg = RoundedRectangle(radius=[dp(10)])
        badge.bind(pos=lambda o, v: setattr(badge_bg, "pos", v),
                   size=lambda o, v: setattr(badge_bg, "size", v))
        top.add_widget(badge)
        title_w = Label(text=rtl_text(title), font_name=font_name(), font_size="12sp",
                        bold=True, color=PRIMARY, halign="right", valign="middle")
        title_w.bind(size=lambda o, v: setattr(o, "text_size", v))
        top.add_widget(title_w)
        self.add_widget(top)
        desc = Label(text=rtl_text(subtitle), font_name=font_name(), font_size="8sp",
                     color=SECONDARY, halign="right", valign="middle",
                     size_hint_y=None, height=dp(28))
        desc.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.add_widget(desc)
        btn = Button(text=rtl_text("باز کردن جدول و عملیات"), font_name=font_name(), font_size="10sp",
                     background_normal="", background_color=SUCCESS, color=WHITE,
                     size_hint_y=None, height=dp(38))
        btn.bind(on_release=callback)
        self.add_widget(btn)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size

class ProfessionalModuleScreen(ModuleWorkspaceScreen):
    """Landing screen backed by the real ModuleWorkspace CRUD engine.

    The previous professional landing page had its own read-only table renderer.
    This class deliberately uses the canonical ModuleWorkspaceScreen for every table.
    """

    def show_module(self, key):
        self.module_key = str(key or "").strip().lower()
        self.set_module(self.module_key, return_to="dashboard")

    def set_module(self, route, return_to="dashboard"):
        # Mother-panel ids (users, virtual, planning, finance, etc.) are
        # operational routes too.  Do not silently redirect an unknown id to
        # the management landing page; let the canonical workspace resolver
        # map it to its real Supabase table.
        route = str(route or "").strip()
        self.module_key = route
        return ModuleWorkspaceScreen.set_module(self, route, return_to=return_to)

    load_module = set_module

    def render(self):
        self._ensure_built()
        self.body.clear_widgets()
        self.subbar.clear_widgets()
        items = SUBMENUS.get(self.route, [])
        title = FRIENDLY.get(self.route, self.route or APP_NAME)
        self.title.text = rtl_text(title)

        hero = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(3),
                         size_hint_y=None, height=dp(94))
        with hero.canvas.before:
            Color(*CARD)
            bg = RoundedRectangle(radius=[dp(16)])
        hero.bind(pos=lambda o, v: setattr(bg, "pos", v),
                  size=lambda o, v: setattr(bg, "size", v))
        hero.add_widget(self.label(title, "19sp", PRIMARY, True, "center"))
        hero.add_widget(self.label(
            MODULE_DESCRIPTIONS.get(self.route, "هر زیرپنل به جدول واقعی Supabase متصل است."),
            "9sp", SECONDARY, False, "center"))
        hero.add_widget(self.label(
            f"{SCHOOL_NAME} • سال تحصیلی {SCHOOL_YEAR or '۱۴۰۵-۱۴۰۶'}",
            "8sp", PRIMARY, False, "center"))
        self.body.add_widget(hero)

        from kivy.uix.scrollview import ScrollView
        from kivy.uix.gridlayout import GridLayout
        scroll = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=2, spacing=dp(8), padding=dp(4), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for i, (text, table) in enumerate(items, 1):
            subtitle = f"جدول: {FRIENDLY.get(table, table)} • داده واقعی"
            grid.add_widget(FeatureCard(
                text, subtitle, lambda *_a, t=table: self.open_table(t), i
            ))
        scroll.add_widget(grid)
        self.body.add_widget(scroll)
        self.status.text = rtl_text(
            f"{len(items)} زیرپنل عملیاتی • جدول واقعی + ثبت/ویرایش/حذف برای نقش مجاز"
        )
        self.status.color = SUCCESS

    def open_table(self, table, refresh_subbar=True):
        table = str(table or "").strip()
        app = App.get_running_app()

        if table == "online_classes" and app is not None and hasattr(app, "ensure_online_workflow"):
            screen = app.ensure_online_workflow()
            if screen is not None and self.manager is not None:
                self.manager.current = screen.name
                return screen

        if table == "teacher_exams" and app is not None and hasattr(app, "ensure_exam_authoring"):
            screen = app.ensure_exam_authoring()
            if screen is not None and self.manager is not None:
                self.manager.current = screen.name
                return screen

        return ModuleWorkspaceScreen.open_table(self, table, refresh_subbar=refresh_subbar)

    _open_table = open_table
