from threading import Thread
import webbrowser

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, SCHOOL_ID, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, PAYMENT_GATEWAY_URL
from mobile.ui import font_name, rtl_text


ROLE_ALIASES = {
    "admin": "manager", "administrator": "manager", "manager": "manager", "مدیر": "manager", "مدیریت": "manager",
    "student": "student", "دانش‌آموز": "student", "دانش آموز": "student",
    "parent": "parent", "parent_guardian": "parent", "guardian": "parent", "ولی": "parent", "اولیا": "parent",
}

PARENT_ACTIVITIES = [
    ("انجمن و اولیا", "شرکت در انتخابات انجمن و اولیا"),
    ("مشاوره خانواده", "شرکت در کلاس‌های مشاوره خانواده"),
    ("سلامت خانواده", "شرکت در کلاس‌های مشاوره سلامت"),
    ("کارگاه‌های تربیتی", "شرکت در کارگاه‌ها و نشست‌های تربیتی"),
    ("همراهی مدرسه", "اعلام آمادگی برای همکاری داوطلبانه با مدرسه"),
]

STUDENT_ACTIVITIES = [
    ("شورای دانش‌آموزی", "شرکت در انتخابات شورای دانش‌آموزی"),
    ("بسیج دانش‌آموزی", "عضویت در بسیج دانش‌آموزی"),
    ("خوارزمی", "شرکت در جشنواره خوارزمی"),
    ("ورزشی", "شرکت در مسابقات ورزشی درون مدرسه"),
    ("فرهنگی", "شرکت در مسابقات فرهنگی"),
    ("هنری", "شرکت در مسابقات هنری"),
]

KHARAZMI = [
    "پژوهش", "برنامه‌نویسی و هوش مصنوعی", "علوم پایه", "نجوم و فضا", "دست‌سازه و فناوری", "ادبیات و علوم انسانی", "محیط زیست", "ریاضی", "زبان و ادبیات", "کارآفرینی و کسب‌وکار"
]
CULTURAL = ["قرآن و عترت", "معارف و نهج‌البلاغه", "کتابخوانی و ادبیات", "سرود و آواها", "رسانه و فضای مجازی", "مسابقات فرهنگی عمومی"]
ARTISTIC = ["نقاشی", "خوشنویسی", "گرافیک", "عکاسی", "فیلم کوتاه", "تئاتر", "موسیقی", "هنرهای تجسمی"]
SPORTS = ["فوتبال", "شطرنج", "والیبال", "بسکتبال", "هندبال"]


def role_of(state):
    raw = str(getattr(state, "role", "student") or "student").strip().lower()
    return ROLE_ALIASES.get(raw, raw)


def digits(value):
    return str(value or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))


class ParticipationScreen(Screen):
    """Real school participation/registration form backed by Supabase tables."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.route = "student"
        self.activity = None
        self.checks = {}
        self.sport_mode = "انفرادی"
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        head = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(54), spacing=dp(8))
        back = Button(text=rtl_text("‹ بازگشت"), font_name=font_name(), font_size="14sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(105))
        back.bind(on_release=lambda *_: self._back())
        head.add_widget(back)
        self.title = Label(text=rtl_text("مشارکت و فعالیت‌ها"), font_name=font_name(), font_size="20sp", bold=True, color=PRIMARY, halign="right", valign="middle")
        self.title.bind(size=lambda o, v: setattr(o, "text_size", v))
        head.add_widget(self.title)
        root.add_widget(head)
        self.status = Label(text="", font_name=font_name(), font_size="12sp", color=SECONDARY, halign="right", valign="middle", size_hint_y=None, height=dp(42))
        self.status.bind(size=lambda o, v: setattr(o, "text_size", v))
        root.add_widget(self.status)
        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(4), size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def set_route(self, route):
        self.route = role_of(self.app_state) if route in ("participation", "student", "parent") else route
        self._render_home()

    def _clear(self):
        self.body.clear_widgets()
        self.checks = {}
        self.activity = None

    def _label(self, text, size="14sp", color=SECONDARY, height=56, bold=False):
        w = Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, bold=bold, halign="right", valign="middle", size_hint_y=None, height=dp(height), padding=(dp(6), dp(4)))
        w.bind(size=lambda o, v: setattr(o, "text_size", (v[0] - dp(12), None)))
        self.body.add_widget(w)
        return w

    def _button(self, text, callback, color=PRIMARY, height=48):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="14sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=dp(height))
        b.bind(on_release=callback)
        self.body.add_widget(b)
        return b

    def _render_home(self):
        self._clear()
        role = role_of(self.app_state)
        if role == "parent":
            self.title.text = rtl_text("مشارکت اولیا")
            self._label("در این بخش، ولی می‌تواند در برنامه‌های مشارکتی مدرسه ثبت‌نام کند. موارد قابل انتخاب و هزینه‌ها از سامانه مدرسه خوانده می‌شوند.", height=78)
            items = PARENT_ACTIVITIES
        else:
            self.title.text = rtl_text("مشارکت و فعالیت دانش‌آموز")
            self._label("فعالیت موردنظر را انتخاب کنید. در گزینه‌های چندانتخابی می‌توانید یک یا چند محور را انتخاب کنید.", height=72)
            items = STUDENT_ACTIVITIES
        for key, text in items:
            self._button(text, lambda *_ , k=key: self._open_activity(k), PRIMARY, 50)
        self._button("سوابق ثبت‌نام‌های من", lambda *_: self._history(), SECONDARY, 48)

    def _open_activity(self, key):
        self.activity = key
        self._clear()
        if self.route == "parent":
            label = dict(PARENT_ACTIVITIES).get(key, key)
        else:
            label = dict(STUDENT_ACTIVITIES).get(key, key)
        self.title.text = rtl_text(label)
        self._label(label + "\nانتخاب‌های خود را مشخص و سپس ثبت نهایی کنید.", "15sp", PRIMARY, 72, True)

        if key == "خوارزمی":
            self._multi("محورهای خوارزمی", KHARAZMI)
        elif key == "ورزشی":
            self._multi("رشته‌های ورزشی؛ یک یا چند مورد", SPORTS)
            self._sport_fields()
        elif key == "فرهنگی":
            self._multi("محورهای فرهنگی؛ یک یا چند مورد", CULTURAL)
        elif key == "هنری":
            self._multi("محورهای هنری؛ یک یا چند مورد", ARTISTIC)
        else:
            self._label("برای این فعالیت نیاز به انتخاب زیرمحور نیست. با ثبت نهایی، درخواست شما در پرونده فعالیت‌های مدرسه ذخیره می‌شود.", height=76)
        self._load_offer_and_submit()

    def _multi(self, heading, options):
        self._label(heading, "14sp", SECONDARY, 42, True)
        grid = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(2))
        grid.bind(minimum_height=grid.setter("height"))
        for option in options:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(46), spacing=dp(8))
            cb = CheckBox(size_hint_x=None, width=dp(42))
            self.checks[option] = cb
            row.add_widget(cb)
            lab = Label(text=rtl_text(option), font_name=font_name(), font_size="14sp", color=SECONDARY, halign="right", valign="middle")
            lab.bind(size=lambda o, v: setattr(o, "text_size", v))
            row.add_widget(lab)
            grid.add_widget(row)
        self.body.add_widget(grid)

    def _sport_fields(self):
        self._label("نوع شرکت در مسابقه", "14sp", SECONDARY, 42, True)
        sp = Spinner(text="انفرادی", values=("انفرادی", "تیمی"), size_hint_y=None, height=dp(48))
        sp.bind(text=lambda _s, v: self._set_sport_mode(v))
        self.body.add_widget(sp)
        self.team_name = self._field("نام تیم؛ فقط برای شرکت تیمی")
        self.team_members = self._field("نام اعضای گروه؛ هر نفر در یک خط", 100)

    def _set_sport_mode(self, value):
        self.sport_mode = value
        if hasattr(self, "team_name"):
            self.team_name.disabled = value != "تیمی"
        if hasattr(self, "team_members"):
            self.team_members.disabled = value != "تیمی"

    def _field(self, hint, height=48):
        w = TextInput(hint_text=rtl_text(hint), font_name=font_name(), font_size="14sp", halign="right", multiline=height > 55, size_hint_y=None, height=dp(height), padding=[dp(10), dp(10)])
        self.body.add_widget(w)
        return w

    def _load_offer_and_submit(self):
        self.offer = None
        self._label("در حال خواندن شرایط و هزینه این فعالیت از سامانه مدرسه...", "12sp", SECONDARY, 42)
        Thread(target=self._fetch_offer, daemon=True).start()

    def _fetch_offer(self):
        try:
            rows = self.app_state.api.table_select("activity_offers", {"activity_key": f"eq.{self.activity}", "active": "eq.1", "limit": "1"})
            offer = rows[0] if rows else None
            Clock.schedule_once(lambda *_: self._offer_ready(offer), 0)
        except Exception as exc:
            Clock.schedule_once(lambda *_: self._error("شرایط فعالیت از سرور خوانده نشد: " + str(exc)), 0)

    def _offer_ready(self, offer):
        self.offer = offer
        amount = 0
        if offer:
            try: amount = int(offer.get("amount") or 0)
            except Exception: amount = 0
        if offer is None:
            self._label("مدرسه هنوز این فعالیت را برای ثبت‌نام فعال نکرده است.", "13sp", ERROR, 60, True)
            return
        if amount <= 0:
            self._label("این فعالیت رایگان است.", "14sp", SUCCESS, 52, True)
        else:
            self._label(f"هزینه تعیین‌شده توسط مدرسه: {amount:,} ریال", "14sp", PRIMARY, 52, True)
        self._button("ثبت نهایی درخواست", lambda *_: self._submit(), SUCCESS, 50)

    def _selected(self):
        return [name for name, cb in self.checks.items() if cb.active]

    def _submit(self):
        if not self.offer:
            return self._error("این فعالیت هنوز توسط مدرسه فعال نشده است.")
        selected = self._selected()
        if self.activity in ("خوارزمی", "ورزشی", "فرهنگی", "هنری") and not selected:
            return self._error("حداقل یک مورد را انتخاب کنید.")
        if self.activity == "ورزشی" and self.sport_mode == "تیمی":
            if not getattr(self, "team_name", None) or not self.team_name.text.strip():
                return self._error("برای شرکت تیمی، نام تیم الزامی است.")
            if not getattr(self, "team_members", None) or not self.team_members.text.strip():
                return self._error("نام اعضای تیم را وارد کنید.")
        payload = {
            "school_id": SCHOOL_ID or None,
            "activity_key": self.activity,
            "role": role_of(self.app_state),
            "national_code": getattr(self.app_state, "national_code", "") or None,
            "display_name": getattr(self.app_state, "display_name", "کاربر فراهوش"),
            "selections": selected,
            "sport_mode": self.sport_mode if self.activity == "ورزشی" else None,
            "team_name": getattr(self, "team_name", None).text.strip() if self.activity == "ورزشی" and hasattr(self, "team_name") else None,
            "team_members": getattr(self, "team_members", None).text.strip().splitlines() if self.activity == "ورزشی" and hasattr(self, "team_members") and self.team_members.text.strip() else [],
            "offer_id": self.offer.get("id"),
            "amount": int(self.offer.get("amount") or 0),
            "payment_status": "free" if int(self.offer.get("amount") or 0) <= 0 else "pending",
        }
        try:
            rows = self.app_state.api.table_insert("activity_registrations", payload)
            row = rows[0] if isinstance(rows, list) and rows else (rows if isinstance(rows, dict) else {})
            rid = row.get("id")
            amount = int(payload["amount"])
            if amount <= 0:
                self._success("ثبت‌نام با موفقیت انجام شد؛ این فعالیت رایگان است.")
            elif PAYMENT_GATEWAY_URL and rid:
                webbrowser.open(PAYMENT_GATEWAY_URL.rstrip("?") + "?activity_registration_id=" + str(rid))
                self._success("درخواست ثبت شد و درگاه پرداخت باز شد. نتیجه پرداخت باید با callback رسمی تأیید شود.")
            else:
                self._success("درخواست ثبت شد و در انتظار پرداخت است؛ درگاه هنوز در تنظیمات مدرسه فعال نشده است.")
        except Exception as exc:
            self._error("ثبت درخواست انجام نشد: " + str(exc))

    def _history(self):
        self._clear()
        self.title.text = rtl_text("سوابق مشارکت")
        self._label("درخواست‌های ثبت‌شده شما در سامانه مدرسه:", height=50)
        try:
            nc = getattr(self.app_state, "national_code", "") or ""
            rows = self.app_state.api.table_select("activity_registrations", {"national_code": f"eq.{nc}", "order": "id.desc", "limit": "50"})
            for row in rows:
                selected = row.get("selections") or []
                if isinstance(selected, list): selected = "، ".join(map(str, selected))
                self._label(f"{row.get('activity_key','فعالیت')}\nانتخاب‌ها: {selected}\nوضعیت پرداخت: {row.get('payment_status','-')}", height=82)
            if not rows: self._label("هنوز سابقه‌ای برای شما ثبت نشده است.", height=60)
        except Exception as exc:
            self._error("خواندن سوابق انجام نشد: " + str(exc))
        self._button("‹ بازگشت به فهرست فعالیت‌ها", lambda *_: self._render_home(), SECONDARY, 48)

    def _success(self, text):
        self.status.text = rtl_text(text)
        self.status.color = SUCCESS

    def _error(self, text):
        self.status.text = rtl_text(text)
        self.status.color = ERROR

    def _back(self):
        if self.manager:
            self.manager.current = "dashboard"
