import json
import webbrowser
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from mobile.config import APP_NAME, SCHOOL_ID, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text

PAYMENT_MANAGERS = {"manager", "educational", "cultural"}
CLASS_MANAGERS = {"manager", "educational", "executive"}

PAYMENT_REASONS = [
    "شهریه",
    "کلاس فوق برنامه",
    "اردو",
    "آزمون و خدمات آموزشی",
    "فعالیت فرهنگی و پرورشی",
    "کتاب و خدمات آموزشی",
    "سایر خدمات مدرسه",
]
PAYMENT_AMOUNTS = [
    "۵۰۰٬۰۰۰ تومان",
    "۱٬۰۰۰٬۰۰۰ تومان",
    "۱٬۵۰۰٬۰۰۰ تومان",
    "۲٬۰۰۰٬۰۰۰ تومان",
    "۳٬۰۰۰٬۰۰۰ تومان",
    "۵٬۰۰۰٬۰۰۰ تومان",
]


def _role(app_state):
    try:
        value = str(app_state.role or "").strip().lower()
    except Exception:
        value = ""
    aliases = {
        "مدیر": "manager", "مدیریت": "manager", "admin": "manager",
        "معاون آموزشی": "educational", "معاون اجرایی": "executive",
        "معاون پرورشی": "cultural", "دبیر": "teacher", "معلم": "teacher",
        "دانش‌آموز": "student", "دانش آموز": "student", "ولی": "parent", "اولیا": "parent",
    }
    return aliases.get(value, value)


class OperationsScreen(Screen):
    """Real operational entry points for payment, messaging and online classes."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.route = "messages"
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(9))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(55), spacing=dp(8))
        back = Button(text=rtl_text("‹ بازگشت"), font_name=font_name(), font_size="14sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(100))
        back.bind(on_release=lambda *_: self._back())
        header.add_widget(back)
        self.title = Label(text=rtl_text(APP_NAME), font_name=font_name(), font_size="21sp", bold=True, color=PRIMARY, halign="right", valign="middle")
        self.title.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        header.add_widget(self.title)
        root.add_widget(header)
        self.status = Label(text="", font_name=font_name(), font_size="12sp", color=SECONDARY, halign="right", valign="middle", size_hint_y=None, height=dp(42))
        self.status.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        root.add_widget(self.status)
        self.body = BoxLayout(orientation="vertical", spacing=dp(9), padding=dp(4), size_hint_y=None)
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView(do_scroll_x=False)
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def set_route(self, route):
        self.route = route
        self.title.text = rtl_text({"payment": "پرداخت آنلاین", "messages": "صندوق پیام‌ها", "online": "کلاس‌های آنلاین"}.get(route, APP_NAME))
        self.body.clear_widgets()
        self.status.color = SUCCESS
        self.status.text = rtl_text(self._welcome())
        if route == "payment":
            self._payment()
        elif route == "online":
            self._online()
        else:
            self._messages()

    def _welcome(self):
        role_titles = {"manager": "مدیریت", "educational": "معاون آموزشی", "executive": "معاون اجرایی", "cultural": "معاون پرورشی", "advisor": "مشاوره", "teacher": "دبیر", "student": "دانش‌آموز", "parent": "ولی"}
        return f"خوش آمدید به پنل {role_titles.get(_role(self.app_state), 'کاربری')} فراهوش؛ امکانات این بخش از سامانه مرکزی مدرسه ارائه می‌شود."

    def _label(self, text, size="14sp", color=SECONDARY, height=70):
        label = Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, halign="right", valign="middle", size_hint_y=None, height=dp(height))
        label.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        self.body.add_widget(label)
        return label

    def _button(self, text, callback, color=PRIMARY):
        button = Button(text=rtl_text(text), font_name=font_name(), font_size="14sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=dp(50))
        button.bind(on_release=callback)
        self.body.add_widget(button)
        return button

    def _payment(self):
        role = _role(self.app_state)
        if role in PAYMENT_MANAGERS:
            self._payment_management()
        else:
            self._payment_student_parent()

    def _payment_management(self):
        self._label("تنظیمات پرداخت مدرسه\nاین بخش فقط برای مدیریت، معاون آموزشی و معاون پرورشی قابل ویرایش است.", height=90)
        reason = Spinner(text=PAYMENT_REASONS[0], values=PAYMENT_REASONS, size_hint_y=None, height=dp(50))
        amount = Spinner(text=PAYMENT_AMOUNTS[0], values=PAYMENT_AMOUNTS, size_hint_y=None, height=dp(50))
        self.body.add_widget(reason)
        self.body.add_widget(amount)
        self._label("وضعیت: گزینه‌های پرداخت باید در Backend مرکزی ثبت شوند تا برای دانش‌آموز و ولی نمایش داده شوند.", height=80)
        self._button("ثبت گزینه پرداخت در سامانه", lambda *_: self._save_payment_option(reason.text, amount.text), SUCCESS)
        self._button("بازخوانی گزینه‌های پرداخت", lambda *_: self.set_route("payment"))

    def _save_payment_option(self, reason, amount_text):
        api = getattr(self.app_state, "api", None)
        if api is None or not getattr(api, "access_token", "") or api.access_token == "local-bootstrap-admin":
            self._error("برای ثبت تنظیمات پرداخت، حساب واقعی Supabase لازم است.")
            return
        try:
            amount_digits = "".join(ch for ch in amount_text if ch.isdigit())
            payload = {"school_id": SCHOOL_ID, "title": reason, "amount": int(amount_digits or 0), "is_active": True}
            api.table_insert("payment_options", payload)
            self._success("گزینه پرداخت در سامانه ثبت شد.")
        except Exception as exc:
            print("PAYMENT OPTION ERROR:", repr(exc))
            self._error("ثبت انجام نشد؛ جدول payment_options یا مجوز RLS باید در Backend فعال باشد.")

    def _payment_student_parent(self):
        self._label("پرداخت مدرسه\nمبلغ و علت پرداخت را فقط از گزینه‌های تأییدشده مدرسه انتخاب کنید؛ امکان واردکردن مبلغ آزاد وجود ندارد.", height=100)
        reason = Spinner(text=PAYMENT_REASONS[0], values=PAYMENT_REASONS, size_hint_y=None, height=dp(50))
        amount = Spinner(text=PAYMENT_AMOUNTS[0], values=PAYMENT_AMOUNTS, size_hint_y=None, height=dp(50))
        self.body.add_widget(reason)
        self.body.add_widget(amount)
        self._label("پس از تأیید، برنامه شما را به درگاه رسمی مدرسه می‌برد و رسید/شماره پیگیری در سامانه ثبت خواهد شد.", height=85)
        self._button("ادامه و ورود به درگاه پرداخت", lambda *_: self._start_payment(reason.text, amount.text), SUCCESS)
        self._button("مشاهده سوابق پرداخت", lambda *_: self._history())

    def _start_payment(self, reason, amount_text):
        try:
            from mobile.config import PAYMENT_GATEWAY_URL
        except Exception:
            PAYMENT_GATEWAY_URL = ""
        if not PAYMENT_GATEWAY_URL:
            self._error("درگاه پرداخت هنوز در تنظیمات امن سامانه ثبت نشده است.")
            return
        amount_digits = "".join(ch for ch in amount_text if ch.isdigit())
        profile = getattr(self.app_state, "profile", {}) or {}
        params = {
            "school_id": SCHOOL_ID,
            "amount": amount_digits,
            "reason": reason,
            "national_code": str(profile.get("national_code") or profile.get("username") or ""),
        }
        query = "&".join(f"{k}={__import__('urllib.parse', fromlist=['quote']).quote(str(v))}" for k, v in params.items())
        try:
            webbrowser.open(PAYMENT_GATEWAY_URL.rstrip("?") + "?" + query)
            self._success("درگاه پرداخت باز شد؛ پس از پرداخت رسید را نگه دارید.")
        except Exception as exc:
            print("PAYMENT OPEN ERROR:", repr(exc))
            self._error("باز کردن درگاه پرداخت انجام نشد.")

    def _history(self):
        self._error("برای نمایش رسیدهای واقعی، جدول payment_records باید در Backend با نشست کاربر قابل خواندن باشد.")

    def _online(self):
        role = _role(self.app_state)
        if role in CLASS_MANAGERS:
            self._online_management()
        else:
            self._online_view()

    def _online_management(self):
        self._label("مدیریت کلاس‌های آنلاین\nساخت و فعال‌سازی کلاس فقط برای مدیریت، معاون آموزشی و معاون اجرایی مجاز است.", height=95)
        self.class_name = TextInput(hint_text=rtl_text("نام کلاس"), font_name=font_name(), multiline=False, size_hint_y=None, height=dp(50))
        self.subject = TextInput(hint_text=rtl_text("درس / موضوع"), font_name=font_name(), multiline=False, size_hint_y=None, height=dp(50))
        self.join_url = TextInput(hint_text=rtl_text("لینک ورود به کلاس"), font_name=font_name(), multiline=False, size_hint_y=None, height=dp(50))
        for field in (self.class_name, self.subject, self.join_url):
            self.body.add_widget(field)
        self._button("ساخت کلاس آنلاین", self._create_class, SUCCESS)
        self._label("کلاس ساخته‌شده در همین بخش و برای دبیر/دانش‌آموزان مجاز قابل مشاهده خواهد بود.", height=70)
        self._load_classes()

    def _online_view(self):
        self._label("کلاس‌های آنلاین فعال\nکلاس‌های شما از سامانه مرکزی خوانده می‌شوند. کلاس غیرفعال برای ورود دانش‌آموز قابل استفاده نیست.", height=90)
        self._load_classes()

    def _load_classes(self):
        api = getattr(self.app_state, "api", None)
        if api is None or not getattr(api, "access_token", "") or api.access_token == "local-bootstrap-admin":
            self._label("برای نمایش کلاس‌های واقعی، باید نشست Supabase معتبر باشد.", color=ERROR, height=70)
            return
        Thread(target=self._fetch_classes, daemon=True).start()

    def _fetch_classes(self):
        try:
            rows = self.app_state.api.table_select("online_classes", {"select": "*", "order": "created_at.desc", "limit": "50"})
            Clock.schedule_once(lambda *_: self._render_classes(rows if isinstance(rows, list) else []), 0)
        except Exception as exc:
            print("ONLINE CLASS LOAD ERROR:", repr(exc))
            Clock.schedule_once(lambda *_: self._label("کلاس‌ها هنوز در Backend در دسترس نیستند.", color=ERROR, height=70), 0)

    def _render_classes(self, rows):
        for row in rows:
            if not isinstance(row, dict):
                continue
            title = row.get("title") or row.get("name") or "کلاس آنلاین"
            subject = row.get("subject") or row.get("course") or ""
            active = row.get("is_active")
            state = "فعال" if active else "غیرفعال"
            self._label(f"{title}\n{subject}\nوضعیت: {state}", height=80)
            if _role(self.app_state) in CLASS_MANAGERS and row.get("id"):
                self._button("فعال / غیرفعال کردن این کلاس", lambda *_ , cid=row.get("id"), current=bool(active): self._toggle_class(cid, current), PRIMARY)
            if active and (row.get("join_url") or row.get("url") or row.get("meeting_url")):
                url = row.get("join_url") or row.get("url") or row.get("meeting_url")
                self._button("ورود به کلاس", lambda *_ , u=url: webbrowser.open(str(u)), SUCCESS)

    def _create_class(self, *_):
        api = getattr(self.app_state, "api", None)
        if api is None or not getattr(api, "access_token", "") or api.access_token == "local-bootstrap-admin":
            self._error("ساخت کلاس نیازمند نشست واقعی Supabase است.")
            return
        title = self.class_name.text.strip()
        subject = self.subject.text.strip()
        url = self.join_url.text.strip()
        if not title:
            self._error("نام کلاس را وارد کنید.")
            return
        payload = {"school_id": SCHOOL_ID, "title": title, "subject": subject, "join_url": url, "is_active": False}
        try:
            api.table_insert("online_classes", payload)
            self._success("کلاس ساخته شد و تا زمان فعال‌سازی، برای ورود دانش‌آموزان غیرفعال است.")
            self._load_classes()
        except Exception as exc:
            print("ONLINE CLASS CREATE ERROR:", repr(exc))
            self._error("ساخت کلاس انجام نشد؛ ساختار online_classes و RLS Backend باید با این عملیات هماهنگ باشد.")

    def _toggle_class(self, class_id, current):
        try:
            self.app_state.api.table_update("online_classes", {"id": f"eq.{class_id}"}, {"is_active": not current})
            self._success("وضعیت کلاس تغییر کرد.")
            self.set_route("online")
        except Exception as exc:
            print("ONLINE CLASS TOGGLE ERROR:", repr(exc))
            self._error("تغییر وضعیت کلاس انجام نشد.")

    def _messages(self):
        self._label("صندوق پیام یکپارچه فراهوش\nپیام‌های مدرسه، آموزشی، اجرایی، پرورشی، مالی و اعلان‌های کلاس آنلاین در یک صندوق نمایش داده می‌شوند.", height=100)
        api = getattr(self.app_state, "api", None)
        if api is None or not getattr(api, "access_token", "") or api.access_token == "local-bootstrap-admin":
            self._label("برای دریافت پیام‌های واقعی باید نشست Supabase معتبر باشد.", color=ERROR, height=70)
            return
        Thread(target=self._fetch_messages, daemon=True).start()

    def _fetch_messages(self):
        try:
            rows = self.app_state.api.table_select("messages", {"select": "*", "order": "created_at.desc", "limit": "50"})
            Clock.schedule_once(lambda *_: self._render_messages(rows if isinstance(rows, list) else []), 0)
        except Exception as exc:
            print("MESSAGE LOAD ERROR:", repr(exc))
            Clock.schedule_once(lambda *_: self._label("صندوق پیام هنوز از Backend قابل دریافت نیست.", color=ERROR, height=70), 0)

    def _render_messages(self, rows):
        if not rows:
            self._label("پیام خوانده‌نشده یا پیام عمومی برای این حساب وجود ندارد.", color=SECONDARY, height=70)
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            title = row.get("title") or row.get("subject") or "پیام فراهوش"
            body = row.get("body") or row.get("content") or row.get("message") or ""
            created = row.get("created_at") or ""
            self._label(f"{title}\n{body}\n{created}", height=105)

    def _success(self, text):
        self.status.color = SUCCESS
        self.status.text = rtl_text(text)

    def _error(self, text):
        self.status.color = ERROR
        self.status.text = rtl_text(text)

    def _back(self):
        if self.manager:
            self.manager.current = "dashboard"
