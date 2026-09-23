from threading import Thread
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from mobile.ui import font_name, rtl_text, fa_display, PersianTextInput
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME


class MessageComposeScreen(Screen):
    """Operational messaging for students and parents: type + recipient + body + send."""
    MESSAGE_TYPES = ("پرسش", "درخواست", "گزارش مشکل", "اطلاع‌رسانی", "سایر")

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.targets = []
        self._build()

    def label(self, text, size="11sp", color=SECONDARY, bold=False, center=False, height=34):
        w = Label(
            text=fa_display(str(text)), font_name=font_name(), font_size=size,
            color=color, bold=bold, halign="center" if center else "right",
            valign="middle", size_hint_y=None, height=dp(height),
        )
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def btn(self, text, cb, color=PRIMARY, h=44):
        b = Button(
            text=fa_display(text), font_name=font_name(), font_size="10sp",
            background_normal="", background_color=color, color=WHITE,
            size_hint_y=None, height=dp(h),
        )
        b.bind(on_release=cb)
        return b

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(7))
        top = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        top.add_widget(self.btn("بازگشت", self.back, SECONDARY, 42))
        top.add_widget(self.label("ارسال پیام", "18sp", PRIMARY, True, True, 42))
        top.add_widget(self.btn("صندوق ورودی", self.inbox, PRIMARY, 42))
        root.add_widget(top)
        root.add_widget(self.label(SCHOOL_NAME + " • پیام مستقیم", "9sp", SECONDARY, False, True, 25))

        self.status = self.label("در حال دریافت مخاطبان…", "9sp", SECONDARY, True, True, 28)
        root.add_widget(self.status)

        form = BoxLayout(orientation="vertical", spacing=dp(6))
        form.add_widget(self.label("نوع پیام", "10sp", PRIMARY, True, False, 28))
        self.type_spinner = Spinner(
            text=fa_display(self.MESSAGE_TYPES[0]),
            values=tuple(fa_display(x) for x in self.MESSAGE_TYPES),
            font_name=font_name(), size_hint_y=None, height=dp(46)
        )
        form.add_widget(self.type_spinner)

        form.add_widget(self.label("نام مخاطب", "10sp", PRIMARY, True, False, 28))
        self.target_spinner = Spinner(
            text=fa_display("در حال دریافت مخاطبان…"), values=(),
            font_name=font_name(), size_hint_y=None, height=dp(46)
        )
        form.add_widget(self.target_spinner)

        form.add_widget(self.label("متن پیام", "10sp", PRIMARY, True, False, 28))
        self.body_input = PersianTextInput(
            hint_text=rtl_text("متن پیام را وارد کنید"),
            font_size="12sp", multiline=True, size_hint_y=None, height=dp(180)
        )
        form.add_widget(self.body_input)
        form.add_widget(self.btn("ارسال پیام", self.send, SUCCESS, 48))
        root.add_widget(form)
        root.add_widget(self.label("پیام پس از ارسال در صندوق پیام ثبت می‌شود و مخاطب آن را در حساب خود می‌بیند.", "9sp", SECONDARY, False, True, 42))
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.app_state = getattr(__import__("kivy.app", fromlist=["App"]).App.get_running_app(), "app_state", self.app_state)
        Clock.schedule_once(lambda *_: self.load_targets(), 0.02)

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None:
            raise RuntimeError("سرویس داده آماده نیست.")
        return api

    def _username(self):
        p = getattr(self.app_state, "profile", {}) or {}
        user = getattr(self.app_state, "user", {}) or {}
        return str(p.get("username") or p.get("email") or user.get("email") or getattr(self.app_state, "national_code", "") or "").strip()

    def _role(self):
        raw = str(getattr(self.app_state, "role", "student") or "student").strip().lower()
        return {
            "دانش‌آموز": "student", "ولی": "parent", "اولیا": "parent",
            "دبیر": "teacher", "معلم": "teacher", "مشاور": "advisor",
            "مدیر": "manager", "مدیریت": "manager"
        }.get(raw, raw)

    def _async(self, work, done):
        def run():
            try:
                result = work()
                Clock.schedule_once(lambda *_: done(result, None), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: done(None, str(exc)), 0)
        Thread(target=run, daemon=True).start()

    def load_targets(self):
        self.status.text = rtl_text("در حال دریافت فهرست مخاطبان مجاز…")
        self._async(self._fetch_targets, self._targets_loaded)

    def _fetch_targets(self):
        api = self._api()
        users = api.table_select("users", {"limit": "500"}) or []
        allowed_roles = {
            "manager", "admin", "مدیر", "مدیریت",
            "educational", "معاون آموزشی",
            "executive", "معاون اجرایی",
            "cultural", "معاون پرورشی",
            "advisor", "counselor", "مشاور",
            "teacher", "دبیر", "معلم",
            "student", "دانش‌آموز", "دانش آموز",
            "parent", "parents", "ولی", "اولیا", "والد"
        }
        current_role = self._role()
        result = []
        seen = set()
        for row in users:
            role = str(row.get("role") or "").strip()
            username = str(row.get("username") or "").strip()
            name = str(row.get("display_name") or "").strip()
            if role.lower() not in {x.lower() for x in allowed_roles} or not username:
                continue
            if username == self._username() or username in seen:
                continue
            if not name:
                name = username
            result.append({
                "username": username, "name": name, "role": role,
                "user_id": row.get("id")
            })
            seen.add(username)
        result.sort(key=lambda x: x["name"])
        return result

    def _targets_loaded(self, targets, error):
        if error:
            self.status.text = rtl_text("دریافت مخاطبان ناموفق بود: " + error)
            self.status.color = ERROR
            return
        self.targets = targets or []
        values = []
        for t in self.targets:
            role = (" • " + t["role"]) if t.get("role") else ""
            values.append(fa_display(t["name"] + role))
        self.target_spinner.values = tuple(values)
        self.target_spinner.text = values[0] if values else fa_display("مخاطب مجاز یافت نشد")
        self.status.text = rtl_text(str(len(self.targets)) + " مخاطب برای ارسال پیام آماده است.")
        self.status.color = SUCCESS if self.targets else ERROR

    def _selected_target(self):
        value = str(self.target_spinner.text or "")
        for t in self.targets:
            role = (" • " + t["role"]) if t.get("role") else ""
            if value == t["name"] + role or value == fa_display(t["name"] + role):
                return t
        return self.targets[0] if self.targets else None

    def send(self, *_):
        target = self._selected_target()
        body = str(self.body_input.text or "").strip()
        if not target:
            self.status.text = rtl_text("ابتدا نام مخاطب را از فهرست انتخاب کنید.")
            self.status.color = ERROR
            return
        if not body:
            self.status.text = rtl_text("متن پیام را وارد کنید.")
            self.status.color = ERROR
            return
        title = str(self.type_spinner.text or self.MESSAGE_TYPES[0]).strip()
        sender = self._username()
        if not sender:
            self.status.text = rtl_text("هویت فرستنده مشخص نیست؛ دوباره وارد حساب شوید.")
            self.status.color = ERROR
            return
        sender_name = str((getattr(self.app_state, "profile", {}) or {}).get("display_name") or sender)
        payload = {
            "sender": sender,
            "receiver": target["username"],
            "text": body,
            "sender_user_id": (getattr(self.app_state, "profile", {}) or {}).get("user_id"),
            "sender_name": sender_name,
            "title": title,
            "body": body,
            "audience_type": "direct",
            "audience_value": target["username"],
            "target_role": target.get("role"),
            "target_name": target.get("name"),
            "target_class_name": None,
        }
        self.status.text = rtl_text("در حال ارسال پیام واقعی…")
        self.status.color = SECONDARY

        def work():
            api = self._api()
            rows = api.table_insert("messages", payload, return_representation=True) or []
            message_id = rows[0].get("id") if rows and isinstance(rows[0], dict) else None
            if message_id:
                api.table_insert("message_targets", {
                    "message_id": message_id,
                    "target_role": target.get("role"),
                    "target_name": target.get("name"),
                    "target_class_name": None,
                }, return_representation=False)
            return message_id

        self._async(work, self._sent)

    def _sent(self, message_id, error):
        if error:
            self.status.text = rtl_text("ارسال پیام ناموفق بود: " + error)
            self.status.color = ERROR
            return
        self.body_input.text = ""
        self.status.text = rtl_text("پیام با موفقیت ارسال شد.")
        self.status.color = SUCCESS

    def inbox(self, *_):
        if self.manager:
            self.manager.current = "panel"
            Clock.schedule_once(lambda *_: self._open_inbox(), 0.05)

    def _open_inbox(self):
        try:
            panel = self.manager.get_screen("panel")
            panel.set_module("messages", return_to="dashboard")
        except Exception as exc:
            self.status.text = rtl_text("باز کردن صندوق ورودی انجام نشد: " + str(exc))
            self.status.color = ERROR

    def back(self, *_):
        if self.manager:
            self.manager.current = "panel"
