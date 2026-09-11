from kivy.animation import Animation
from kivy.graphics import (
    Color,
    RoundedRectangle,
    Rectangle,
    Line,
)
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView

from mobile.config import (
    APP_NAME,
    SCHOOL_NAME,
    BACKGROUND_PATH,
    PRIMARY,
)

from mobile.ui import (
    font_name,
    rtl_text,
)


ROLE_ALIASES = {

    "admin": "manager",
    "administrator": "manager",
    "manager": "manager",
    "مدیر": "manager",
    "مدیریت": "manager",

    "executive": "executive",
    "معاون اجرایی": "executive",

    "educational": "educational",
    "training": "educational",
    "معاون آموزشی": "educational",

    "cultural": "cultural",
    "پرورشی": "cultural",
    "معاون پرورشی": "cultural",

    "advisor": "advisor",
    "counselor": "advisor",
    "مشاور": "advisor",
    "مشاوره": "advisor",

    "teacher": "teacher",
    "teacher_staff": "teacher",
    "دبیر": "teacher",
    "معلم": "teacher",

    "student": "student",
    "دانش‌آموز": "student",
    "دانش آموز": "student",

    "parent": "parent",
    "parent_guardian": "parent",
    "guardian": "parent",
    "ولی": "parent",
    "اولیا": "parent",
}


ROLE_TITLES = {

    "manager": "مدیریت",
    "executive": "معاون اجرایی",
    "educational": "معاون آموزشی",
    "cultural": "معاون پرورشی",
    "advisor": "مشاوره",
    "teacher": "دبیر",
    "student": "دانش‌آموز",
    "parent": "ولی",
}


MANAGER_MENU = [

    ("مدیریت", "management"),
    ("معاون آموزشی", "educational"),
    ("معاون اجرایی", "executive"),
    ("معاون پرورشی", "cultural"),
    ("مشاوره", "advisor"),
    ("دبیران", "teachers"),
    ("اولیا", "parents"),
    ("دانش‌آموزان", "students"),
    ("مالی", "finance"),
    ("پرداخت آنلاین", "payment"),
    ("کلاس‌های آنلاین", "online"),
    ("تابلو هوشمند", "smart_board"),
    ("دستیار هوش مصنوعی", "ai"),
    ("گزارش‌ها", "reports"),
    ("صندوق پیام‌ها", "messages"),
    ("تنظیمات", "settings"),
    ("درباره برنامه", "about"),
]


ROLE_MENU = {

    "executive": [
        ("معاون اجرایی", "executive"),
        ("دانش‌آموزان", "students"),
        ("اولیا", "parents"),
        ("صندوق پیام‌ها", "messages"),
        ("تنظیمات", "settings"),
        ("درباره برنامه", "about"),
    ],

    "educational": [
        ("معاون آموزشی", "educational"),
        ("دانش‌آموزان", "students"),
        ("دبیران", "teachers"),
        ("کلاس‌های آنلاین", "online"),
        ("تابلو هوشمند", "smart_board"),
        ("گزارش‌ها", "reports"),
        ("صندوق پیام‌ها", "messages"),
        ("درباره برنامه", "about"),
    ],

    "cultural": [
        ("معاون پرورشی", "cultural"),
        ("دانش‌آموزان", "students"),
        ("تابلو هوشمند", "smart_board"),
        ("صندوق پیام‌ها", "messages"),
        ("درباره برنامه", "about"),
    ],

    "advisor": [
        ("مشاوره", "advisor"),
        ("دانش‌آموزان", "students"),
        ("اولیا", "parents"),
        ("صندوق پیام‌ها", "messages"),
        ("درباره برنامه", "about"),
    ],

    "teacher": [
        ("پنل دبیر", "teacher"),
        ("دانش‌آموزان", "students"),
        ("کلاس‌های آنلاین", "online"),
        ("تابلو هوشمند", "smart_board"),
        ("صندوق پیام‌ها", "messages"),
        ("درباره برنامه", "about"),
    ],

    "student": [
        ("پنل دانش‌آموز", "student"),
        ("برنامه هفتگی", "schedule"),
        ("وضعیت تحصیلی", "student_info"),
        ("پرداخت آنلاین", "payment"),
        ("کلاس‌های آنلاین", "online"),
        ("تابلو هوشمند", "smart_board"),
        ("صندوق پیام‌ها", "messages"),
        ("درباره برنامه", "about"),
    ],

    "parent": [
        ("پنل اولیا", "parent"),
        ("وضعیت تحصیلی فرزند", "student_info"),
        ("پرداخت آنلاین", "payment"),
        ("کلاس‌های آنلاین", "online"),
        ("تابلو هوشمند", "smart_board"),
        ("صندوق پیام‌ها", "messages"),
        ("درباره برنامه", "about"),
    ],
}


class HamburgerButton(Widget):

    def __init__(self, **kwargs):

        super().__init__(
            **kwargs
        )

        with self.canvas:

            self._color = Color(
                1,
                1,
                1,
                1
            )

            self._line1 = Line(
                width=2.2
            )

            self._line2 = Line(
                width=2.2
            )

            self._line3 = Line(
                width=2.2
            )

        self.bind(
            pos=self._update_lines,
            size=self._update_lines,
        )

    def _update_lines(self, *_):

        left = (
            self.x
            + self.width * 0.18
        )

        right = (
            self.x
            + self.width * 0.82
        )

        y1 = (
            self.y
            + self.height * 0.70
        )

        y2 = (
            self.y
            + self.height * 0.50
        )

        y3 = (
            self.y
            + self.height * 0.30
        )

        self._line1.points = [
            left,
            y1,
            right,
            y1,
        ]

        self._line2.points = [
            left,
            y2,
            right,
            y2,
        ]

        self._line3.points = [
            left,
            y3,
            right,
            y3,
        ]


class DashboardScreen(Screen):

    drawer_width = NumericProperty(
        0
    )

    def __init__(
        self,
        app_state,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.app_state = app_state
        self.drawer_open = False
        self.logout_button = None

        self._build_ui()

    def _build_ui(self):

        self.clear_widgets()

        root = FloatLayout()

        self.background = Image(
            source=BACKGROUND_PATH,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={
                "x": 0,
                "y": 0
            },
        )

        root.add_widget(
            self.background
        )

        self.overlay_background = Widget()

        with self.overlay_background.canvas:

            self.overlay_color = Color(
                0.02,
                0.08,
                0.16,
                0.18
            )

            self.overlay_rect = Rectangle()

        self.overlay_background.bind(
            pos=self._update_overlay,
            size=self._update_overlay,
        )

        root.add_widget(
            self.overlay_background
        )

        self.header = FloatLayout(
            size_hint=(1, None),
            height=dp(150),
            pos_hint={
                "top": 1
            },
        )

        with self.header.canvas:

            self.header_color = Color(
                0.02,
                0.15,
                0.28,
                0.82
            )

            self.header_rect = RoundedRectangle(
                radius=[0]
            )

        self.header.bind(
            pos=self._update_header,
            size=self._update_header,
        )

        root.add_widget(
            self.header
        )

        self.menu_button = HamburgerButton(
            size_hint=(None, None),
            size=(
                dp(62),
                dp(62)
            ),
            pos_hint={
                "right": 0.98,
                "top": 0.94,
            },
        )

        self.menu_button.bind(
            on_touch_down=self._hamburger_touch
        )

        self.header.add_widget(
            self.menu_button
        )

        self.title_label = Label(
            text=rtl_text(
                "سامانه هوشمند مدیریت مدرسه"
            ),
            font_name=font_name(),
            font_size="23sp",
            bold=True,
            color=(1, 1, 1, 1),
            halign="right",
            valign="middle",
            size_hint=(0.78, None),
            height=dp(45),
            pos_hint={
                "right": 0.91,
                "top": 0.78
            },
        )

        self.title_label.bind(
            size=self._sync_text_size
        )

        self.header.add_widget(
            self.title_label
        )

        self.school_label = Label(
            text=rtl_text(
                SCHOOL_NAME
            ),
            font_name=font_name(),
            font_size="15sp",
            color=(
                0.86,
                0.96,
                1,
                1
            ),
            halign="right",
            valign="middle",
            size_hint=(0.78, None),
            height=dp(34),
            pos_hint={
                "right": 0.91,
                "top": 0.48
            },
        )

        self.school_label.bind(
            size=self._sync_text_size
        )

        self.header.add_widget(
            self.school_label
        )

        self.welcome_card = FloatLayout(
            size_hint=(0.90, None),
            height=dp(150),
            pos_hint={
                "center_x": 0.5,
                "top": 0.78
            },
        )

        with self.welcome_card.canvas:

            self.welcome_color = Color(
                1,
                1,
                1,
                0.92
            )

            self.welcome_rect = RoundedRectangle(
                radius=[dp(22)]
            )

        self.welcome_card.bind(
            pos=self._update_welcome,
            size=self._update_welcome,
        )

        root.add_widget(
            self.welcome_card
        )

        self.welcome_title = Label(
            text=rtl_text(
                "خوش آمدید"
            ),
            font_name=font_name(),
            font_size="23sp",
            bold=True,
            color=(
                0.02,
                0.18,
                0.32,
                1
            ),
            halign="right",
            valign="middle",
            size_hint=(0.88, None),
            height=dp(48),
            pos_hint={
                "right": 0.95,
                "top": 0.82
            },
        )

        self.welcome_title.bind(
            size=self._sync_text_size
        )

        self.welcome_card.add_widget(
            self.welcome_title
        )

        self.role_label = Label(
            text="",
            font_name=font_name(),
            font_size="16sp",
            color=(
                0.10,
                0.30,
                0.42,
                1
            ),
            halign="right",
            valign="middle",
            size_hint=(0.88, None),
            height=dp(40),
            pos_hint={
                "right": 0.95,
                "top": 0.52
            },
        )

        self.role_label.bind(
            size=self._sync_text_size
        )

        self.welcome_card.add_widget(
            self.role_label
        )

        self.status_label = Label(
            text=rtl_text(
                "سامانه آماده استفاده است"
            ),
            font_name=font_name(),
            font_size="14sp",
            color=(
                0.12,
                0.40,
                0.35,
                1
            ),
            halign="right",
            valign="middle",
            size_hint=(0.88, None),
            height=dp(32),
            pos_hint={
                "right": 0.95,
                "top": 0.28
            },
        )

        self.status_label.bind(
            size=self._sync_text_size
        )

        self.welcome_card.add_widget(
            self.status_label
        )

        self.hint_card = FloatLayout(
            size_hint=(0.90, None),
            height=dp(100),
            pos_hint={
                "center_x": 0.5,
                "y": 0.08
            },
        )

        with self.hint_card.canvas:

            self.hint_color = Color(
                0.02,
                0.16,
                0.28,
                0.78
            )

            self.hint_rect = RoundedRectangle(
                radius=[dp(20)]
            )

        self.hint_card.bind(
            pos=self._update_hint,
            size=self._update_hint,
        )

        root.add_widget(
            self.hint_card
        )

        self.hint_label = Label(
            text=rtl_text(
                "برای مشاهده امکانات سامانه، "
                "دکمه سه‌خطی بالای صفحه را لمس کنید."
            ),
            font_name=font_name(),
            font_size="14sp",
            color=(
                1,
                1,
                1,
                0.95
            ),
            halign="center",
            valign="middle",
            size_hint=(0.90, 0.80),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.5
            },
        )

        self.hint_label.bind(
            size=self._sync_text_size
        )

        self.hint_card.add_widget(
            self.hint_label
        )

        self.drawer_overlay = Button(
            text="",
            background_normal="",
            background_color=(
                0,
                0,
                0,
                0.42
            ),
            size_hint=(1, 1),
            pos_hint={
                "x": 0,
                "y": 0
            },
            opacity=0,
            disabled=True,
        )

        self.drawer_overlay.bind(
            on_release=self.close_drawer
        )

        root.add_widget(
            self.drawer_overlay
        )

        self.drawer = FloatLayout(
            size_hint=(None, 1),
            width=dp(320),
            x=-dp(320),
            pos_hint={
                "y": 0
            },
        )

        with self.drawer.canvas:

            self.drawer_color = Color(
                0.025,
                0.10,
                0.18,
                0.99
            )

            self.drawer_rect = RoundedRectangle(
                radius=[0]
            )

        self.drawer.bind(
            pos=self._update_drawer,
            size=self._update_drawer,
        )

        root.add_widget(
            self.drawer
        )

        self._build_drawer()

        self.add_widget(
            root
        )

    def _build_drawer(self):

        self.drawer.clear_widgets()

        title = Label(
            text=rtl_text(
                APP_NAME
            ),
            font_name=font_name(),
            font_size="25sp",
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(60),
            pos_hint={
                "top": 0.98
            },
        )

        self.drawer.add_widget(
            title
        )

        self.menu_role = Label(
            text="",
            font_name=font_name(),
            font_size="13sp",
            color=(
                0.65,
                0.86,
                0.96,
                1
            ),
            size_hint=(0.92, None),
            height=dp(38),
            pos_hint={
                "center_x": 0.5,
                "top": 0.90
            },
        )

        self.drawer.add_widget(
            self.menu_role
        )

        self.menu_scroll = ScrollView(
            size_hint=(0.94, 0.72),
            pos_hint={
                "center_x": 0.5,
                "top": 0.82
            },
            do_scroll_x=False,
        )

        self.menu_box = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[
                dp(4),
                dp(4),
                dp(4),
                dp(12),
            ],
            size_hint_y=None,
        )

        self.menu_box.bind(
            minimum_height=
            self.menu_box.setter(
                "height"
            )
        )

        self.menu_scroll.add_widget(
            self.menu_box
        )

        self.drawer.add_widget(
            self.menu_scroll
        )

        self.logout_button = Button(
            text=rtl_text(
                "خروج از حساب"
            ),
            font_name=font_name(),
            font_size="15sp",
            background_normal="",
            background_color=(
                0.55,
                0.12,
                0.14,
                1
            ),
            color=(1, 1, 1, 1),
            size_hint=(0.88, None),
            height=dp(48),
            pos_hint={
                "center_x": 0.5,
                "y": 0.025
            },
        )

        self.logout_button.bind(
            on_release=self.logout
        )

        self.drawer.add_widget(
            self.logout_button
        )

    def refresh(self):

        role = self._get_role()
        display_name = self._get_display_name()

        role_title = ROLE_TITLES.get(
            role,
            "کاربر"
        )

        self.welcome_title.text = rtl_text(
            f"خوش آمدید، {display_name}"
        )

        self.role_label.text = rtl_text(
            f"نقش کاربری: {role_title}"
        )

        self.menu_role.text = rtl_text(
            f"{display_name} | {role_title}"
        )

        self._populate_menu(
            role
        )

    def _populate_menu(self, role):

        self.menu_box.clear_widgets()

        items = (
            MANAGER_MENU
            if role == "manager"
            else ROLE_MENU.get(
                role,
                [
                    (
                        "صندوق پیام‌ها",
                        "messages"
                    ),
                    (
                        "درباره برنامه",
                        "about"
                    ),
                ]
            )
        )

        for title, route in items:

            button = Button(
                text=rtl_text(title),
                font_name=font_name(),
                font_size="14sp",
                background_normal="",
                background_color=(
                    0.04,
                    0.22,
                    0.34,
                    1
                ),
                color=(1, 1, 1, 1),
                halign="right",
                valign="middle",
                size_hint_y=None,
                height=dp(46),
            )

            button.bind(
                size=self._sync_text_size
            )

            button.bind(
                on_release=lambda btn,
                r=route:
                self._menu_selected(r)
            )

            self.menu_box.add_widget(
                button
            )

    def _hamburger_touch(
        self,
        widget,
        touch
    ):

        if widget.collide_point(
            *touch.pos
        ):

            if touch.is_mouse_scrolling:
                return False

            self.toggle_drawer()

            return True

        return False

    def toggle_drawer(self):

        if self.drawer_open:
            self.close_drawer()
        else:
            self.open_drawer()

    def open_drawer(self, *_):

        self.drawer_open = True

        self.drawer_overlay.disabled = False
        self.drawer_overlay.opacity = 1

        Animation(
            x=0,
            duration=0.25,
            t="out_quad"
        ).start(
            self.drawer
        )

    def close_drawer(self, *_):

        if not self.drawer_open:
            return

        self.drawer_open = False

        animation = Animation(
            x=-dp(320),
            duration=0.22,
            t="in_quad"
        )

        animation.bind(
            on_complete=self._drawer_closed
        )

        animation.start(
            self.drawer
        )

        self.drawer_overlay.disabled = True
        self.drawer_overlay.opacity = 0

    def _drawer_closed(self, *_):
        self.drawer.x = -dp(320)

    def _menu_selected(
        self,
        route
    ):

        self.close_drawer()

        if route == "about":

            self._show_about()

            return

        self._go_to(
            "module",
            module=route
        )

    def _go_to(
        self,
        screen_name,
        **kwargs
    ):

        if not self.manager:
            return

        try:

            if not self.manager.has_screen(
                screen_name
            ):

                self.status_label.text = rtl_text(
                    "صفحه موردنظر در دسترس نیست."
                )

                return

            screen = self.manager.get_screen(
                screen_name
            )

            module_name = kwargs.get(
                "module"
            )

            if hasattr(
                screen,
                "set_module"
            ):

                screen.set_module(
                    module_name
                )

            elif hasattr(
                screen,
                "load_module"
            ):

                screen.load_module(
                    module_name
                )

            self.manager.current = (
                screen_name
            )

        except Exception as exc:

            print(
                "ROUTE ERROR:",
                repr(exc)
            )

            self.status_label.text = rtl_text(
                "باز کردن این بخش با خطا مواجه شد."
            )

    def _show_about(self):

        self.status_label.text = rtl_text(
            "فراهوش | سامانه هوشمند آموزشی مدارس"
        )

        self.hint_label.text = rtl_text(
            "نام برنامه: فراهوش\n"
            "سامانه هوشمند آموزشی یکپارچه\n"
            "سال تحصیلی: ۱۴۰۵ - ۱۴۰۶"
        )

    def logout(self, *_):

        try:

            if self.app_state:
                self.app_state.logout()

        except Exception as exc:

            print(
                "LOGOUT ERROR:",
                repr(exc)
            )

        self.close_drawer()

        if self.manager:
            self.manager.current = "login"

    def _get_role(self):

        role = None

        try:
            role = self.app_state.role
        except Exception:
            pass

        if not role:
            role = "student"

        role = str(
            role
        ).strip().lower()

        return ROLE_ALIASES.get(
            role,
            role
        )

    def _get_display_name(self):

        try:

            value = (
                self.app_state.display_name
            )

            if value:
                return str(value)

        except Exception:
            pass

        return "کاربر فراهوش"

    def _update_overlay(
        self,
        instance,
        value
    ):

        self.overlay_rect.pos = value
        self.overlay_rect.size = instance.size

    def _update_header(
        self,
        instance,
        value
    ):

        self.header_rect.pos = value
        self.header_rect.size = instance.size

    def _update_welcome(
        self,
        instance,
        value
    ):

        self.welcome_rect.pos = value
        self.welcome_rect.size = instance.size

    def _update_hint(
        self,
        instance,
        value
    ):

        self.hint_rect.pos = value
        self.hint_rect.size = instance.size

    def _update_drawer(
        self,
        instance,
        value
    ):

        self.drawer_rect.pos = value
        self.drawer_rect.size = instance.size

    def _sync_text_size(
        self,
        instance,
        value
    ):

        instance.text_size = value

    def on_pre_enter(
        self,
        *args
    ):

        try:
            self.refresh()
        except Exception as exc:
            print(
                "DASHBOARD REFRESH ERROR:",
                repr(exc)
            )

        return super().on_pre_enter(
            *args
        )

    def on_leave(
        self,
        *args
    ):

        if self.drawer_open:
            self.close_drawer()

        return super().on_leave(
            *args
        )
