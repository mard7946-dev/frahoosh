from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text
from mobile.services.live_data import LiveSchoolData


TITLES = {
    "management": "مدیریت مدرسه",
    "educational": "معاون آموزشی",
    "executive": "معاون اجرایی",
    "teacher": "پنل دبیر",
    "teachers": "دبیران",
    "student": "پنل دانش‌آموز",
    "students": "دانش‌آموزان",
    "parent": "پنل اولیا",
    "parents": "اولیا",
    "online": "کلاس هوشمند آنلاین",
    "messages": "صندوق پیام‌ها",
    "reports": "گزارش‌های مدرسه",
    "schedule": "برنامه هفتگی",
    "student_info": "وضعیت تحصیلی",
}


class LivePanelScreen(Screen):
    """Live mobile panels backed by the canonical Frahoosh school tables."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.data = LiveSchoolData(app_state)
        self.route = "messages"
        self._build()

    def _build(self):
        root = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(9),
        )

        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(8),
        )
        back = Button(
            text=rtl_text("‹ داشبورد"),
            font_name=font_name(),
            font_size="14sp",
            background_normal="",
            background_color=PRIMARY,
            color=WHITE,
            size_hint_x=None,
            width=dp(100),
        )
        back.bind(on_release=lambda *_: self._back())
        header.add_widget(back)

        self.title = Label(
            text=rtl_text(APP_NAME),
            font_name=font_name(),
            font_size="21sp",
            bold=True,
            color=PRIMARY,
            halign="right",
            valign="middle",
        )
        self.title.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        header.add_widget(self.title)
        root.add_widget(header)

        self.status = Label(
            text="",
            font_name=font_name(),
            font_size="12sp",
            color=SECONDARY,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(45),
        )
        self.status.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        root.add_widget(self.status)

        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(
            orientation="vertical",
            padding=dp(4),
            spacing=dp(9),
            size_hint_y=None,
        )
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)

        self.add_widget(root)

    def set_panel(self, route):
        self.route = str(route or "messages").strip().lower()
        self.title.text = rtl_text(TITLES.get(self.route, APP_NAME))
        self.body.clear_widgets()
        self.status.color = SECONDARY
        self.status.text = rtl_text("در حال دریافت اطلاعات واقعی از سامانه مدرسه...")
        Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            connected, message = self.data.connection_state()
            if not connected:
                Clock.schedule_once(lambda *_: self._show_connection(message), 0)
                return

            if self.route == "messages":
                payload = ("messages", self.data.inbox())
            elif self.route in ("online",):
                payload = ("online", self.data.online_classes())
            elif self.route in ("student", "student_info"):
                payload = ("student", self.data.student_summary())
            elif self.route in ("management", "educational", "executive", "teachers", "students", "parents", "reports", "teacher", "parent"):
                payload = ("counts", self.data.dashboard_counts())
            else:
                payload = ("messages", self.data.inbox())

            Clock.schedule_once(lambda *_: self._render(payload), 0)
        except Exception as exc:
            Clock.schedule_once(lambda *_: self._show_error(str(exc)), 0)

    def _show_connection(self, message):
        self.status.color = ERROR
        self.status.text = rtl_text(message)
        self._add_card("اتصال واقعی", message)
        self._add_card(
            "نکته مهم",
            "این صفحه داده ساختگی نشان نمی‌دهد. برای دسترسی کامل به داده‌های Supabase، ورود باید با نشست واقعی Supabase انجام شود.",
        )
        self._add_button("بازگشت به داشبورد", lambda *_: self._back(), PRIMARY)

    def _show_error(self, message):
        self.status.color = ERROR
        self.status.text = rtl_text("دریافت اطلاعات انجام نشد.")
        self._add_card("خطای سامانه", message)
        self._add_button("تلاش دوباره", lambda *_: self.set_panel(self.route), SUCCESS)

    def _render(self, payload):
        kind, data = payload
        self.body.clear_widgets()
        self.status.color = SUCCESS
        self.status.text = rtl_text("اطلاعات از سامانه مرکزی دریافت شد.")

        if kind == "messages":
            self._render_messages(data)
        elif kind == "online":
            self._render_online(data)
        elif kind == "student":
            self._render_student(data)
        else:
            self._render_counts(data)

        self._add_button("بازخوانی", lambda *_: self.set_panel(self.route), SUCCESS)

    def _render_messages(self, rows):
        if not rows:
            self._add_card("صندوق پیام‌ها", "در حال حاضر پیام قابل نمایش وجود ندارد.")
            return
        for row in rows:
            title = self._first(row, "title", "subject", "name", default="پیام فراهوش")
            text = self._first(row, "content", "text", "body", "message", default="")
            date = self._first(row, "created_at", "date", "sent_at", default="")
            self._add_card(str(title), f"{text}\n\n{date}")

    def _render_online(self, rows):
        if not rows:
            self._add_card("کلاس‌های آنلاین", "هنوز کلاس آنلاین قابل نمایش ثبت نشده است.")
            self._add_card(
                "هسته کلاس هوشمند",
                "این بخش به جلسات کلاس، سه مرحله صحت‌سنجی حضور، ثبت خروج/عدم‌تأیید، پیام والدین و قفل آموزشی متصل خواهد شد.",
            )
            return
        for row in rows:
            title = self._first(row, "title", "name", "class_name", "subject", default="کلاس آنلاین")
            teacher = self._first(row, "teacher_name", "teacher", default="")
            status = self._first(row, "status", "state", default="")
            self._add_card(str(title), f"دبیر: {teacher}\nوضعیت: {status}")

    def _render_student(self, payload):
        student = payload.get("student") or {}
        name = self._first(student, "full_name", "name", default="دانش‌آموز")
        self._add_card("دانش‌آموز", str(name))
        self._add_card("حضور و غیاب", self._summary_text(payload.get("attendance"), "حضور"))
        self._add_card("نمرات", self._summary_text(payload.get("grades"), "نمره"))
        self._add_card("تکالیف", self._summary_text(payload.get("assignments"), "تکلیف"))

    def _render_counts(self, counts):
        for title, value in counts.items():
            text = "اطلاعات قابل دریافت نیست" if value is None else f"تعداد ثبت‌شده: {value}"
            self._add_card(title, text)

        self._add_card(
            "جریان یکپارچه فراهوش",
            "ثبت رویدادهای آموزشی، انضباطی، نمره، تکلیف و حضور باید از منبع اصلی به صندوق پیام دانش‌آموز و اولیای مرتبط برسد.",
        )

    def _summary_text(self, rows, label):
        rows = rows or []
        if not rows:
            return f"موردی برای نمایش {label} ثبت نشده است."
        return f"{len(rows)} مورد در سامانه ثبت شده است."

    def _add_card(self, title, text):
        box = BoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(10)],
            spacing=dp(4),
            size_hint_y=None,
            height=dp(96),
        )
        head = Label(
            text=rtl_text(title),
            font_name=font_name(),
            font_size="16sp",
            bold=True,
            color=PRIMARY,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(32),
        )
        head.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        body = Label(
            text=rtl_text(str(text)),
            font_name=font_name(),
            font_size="13sp",
            color=SECONDARY,
            halign="right",
            valign="top",
        )
        body.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        box.add_widget(head)
        box.add_widget(body)
        self.body.add_widget(box)

    def _add_button(self, text, callback, color):
        button = Button(
            text=rtl_text(text),
            font_name=font_name(),
            font_size="14sp",
            background_normal="",
            background_color=color,
            color=WHITE,
            size_hint_y=None,
            height=dp(48),
        )
        button.bind(on_release=callback)
        self.body.add_widget(button)

    @staticmethod
    def _first(row, *keys, default=""):
        if not isinstance(row, dict):
            return default
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                return value
        return default

    def _back(self):
        if self.manager:
            self.manager.current = "dashboard"
