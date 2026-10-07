from datetime import datetime, timezone
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, fa_display

MODULES = [
    ("شورا", "student_council"),
    ("بسیج", "basij_registration"),
    ("همیار مدرسه", "school_ally"),
    ("شهردار مدرسه", "school_mayor"),
    ("مسابقات", "competitions"),
    ("جشنواره‌ها", "activity_programs"),
    ("فعالیت‌های آموزشی", "educational_activities"),
    ("فعالیت‌های فرهنگی/پرورشی", "cultural_activity_registrations"),
    ("سرویس مدرسه", "transport_requests"),
    ("فعالیت‌های اولیا", "parent_activities"),
    ("گواهی‌ها", "certificate_requests"),
    ("ارسال تکالیف", "assignment_submissions"),
]

ALIASES = {
    "manager": "manager", "مدیر": "manager", "مدیریت": "manager",
    "educational": "educational", "معاون آموزشی": "educational",
    "executive": "executive", "معاون اجرایی": "executive",
    "student": "student", "دانش‌آموز": "student", "دانش آموز": "student",
    "parent": "parent", "parents": "parent", "ولی": "parent", "اولیا": "parent",
}

def role_of(state):
    values = [getattr(state, "panel_role", ""), getattr(state, "role", "")]
    values.append((getattr(state, "profile", {}) or {}).get("role", ""))
    for raw in values:
        text = str(raw or "").strip().lower().replace("‌", " ")
        for key, value in ALIASES.items():
            if key in text:
                return value
    return "student"

class ModuleActivationScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build()

    def _label(self, text, size="10sp", color=SECONDARY, bold=False, height=40):
        w = Label(text=fa_display(text), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="right", valign="middle",
                  size_hint_y=None, height=dp(height))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _button(self, text, callback, color=PRIMARY, height=44):
        b = Button(text=fa_display(text), font_name=font_name(), font_size="10sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(height))
        b.bind(on_release=callback)
        return b

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None:
            raise RuntimeError("سرویس داده آماده نیست.")
        return api

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        head.add_widget(self._button("بازگشت", self.back, SECONDARY, 42))
        head.add_widget(self._label("درخواست فعال‌سازی قابلیت‌ها", "17sp", PRIMARY, True, 42))
        head.add_widget(self._button("داشبورد", self.dashboard, PRIMARY, 42))
        root.add_widget(head)
        self.status = self._label("در حال بارگذاری وضعیت قابلیت‌ها…", "9sp", SECONDARY, True, 30)
        root.add_widget(self.status)
        sc = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(5), padding=dp(3), size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        sc.add_widget(self.body)
        root.add_widget(sc)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.load()

    def load(self):
        self.body.clear_widgets()
        try:
            role = role_of(self.app_state)
            rows = self._api().table_select("module_activations", {"order": "module_key.asc", "limit": "200"}) or []
            by_key = {str(r.get("module_key")): r for r in rows}
            if role in {"manager", "educational", "executive"}:
                pending = [r for r in rows if str(r.get("status") or "") == "pending"]
                self.body.add_widget(self._label("درخواست‌های در انتظار تصمیم", "13sp", PRIMARY, True, 36))
                if not pending:
                    self.body.add_widget(self._label("درخواست در انتظاری وجود ندارد.", "10sp", SECONDARY, False, 42))
                for row in pending:
                    key = str(row.get("module_key") or "")
                    title = dict(MODULES).get(key, key)
                    card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(88), spacing=dp(3))
                    card.add_widget(self._label(f"{title} | درخواست‌شده در {row.get('requested_at') or '—'}", "10sp", SECONDARY, True, 38))
                    actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(4))
                    actions.add_widget(self._button("تأیید", lambda *_a, r=dict(row): self.decide(r, True), SUCCESS, 40))
                    actions.add_widget(self._button("رد", lambda *_a, r=dict(row): self.decide(r, False), ERROR, 40))
                    card.add_widget(actions)
                    self.body.add_widget(card)
                self.status.text = fa_display("گردش‌کار درخواست‌ها آماده تصمیم‌گیری است.")
            else:
                self.body.add_widget(self._label("قابلیت موردنظر را انتخاب و درخواست فعال‌سازی ثبت کنید.", "11sp", PRIMARY, True, 44))
                for title, key in MODULES:
                    row = by_key.get(key)
                    status = str((row or {}).get("status") or "ثبت نشده")
                    active = bool((row or {}).get("active"))
                    if active:
                        action = self._label("فعال است", "9sp", SUCCESS, True, 40)
                    elif status == "pending":
                        action = self._label("در انتظار تأیید مدیریت/معاون", "9sp", PRIMARY, True, 40)
                    elif status == "rejected":
                        action = self._button("درخواست مجدد", lambda *_a, k=key: self.request(k), PRIMARY, 40)
                    else:
                        action = self._button("درخواست فعال‌سازی", lambda *_a, k=key: self.request(k), SUCCESS, 40)
                    card = BoxLayout(size_hint_y=None, height=dp(78), spacing=dp(5))
                    card.add_widget(self._label(title, "11sp", SECONDARY, True, 70))
                    card.add_widget(action)
                    self.body.add_widget(card)
                self.status.text = fa_display("وضعیت درخواست‌ها از Supabase خوانده شد.")
        except Exception as exc:
            self.status.text = fa_display("خطا در دریافت درخواست‌ها: " + str(exc))
            self.status.color = ERROR

    def request(self, module_key):
        try:
            result = self._api().rpc("request_module_activation", {"p_module_key": module_key})
            self.status.text = fa_display("درخواست ثبت شد و برای بررسی ارسال گردید.")
            self.status.color = SUCCESS
            self.load()
        except Exception as exc:
            self.status.text = fa_display("ثبت درخواست انجام نشد: " + str(exc))
            self.status.color = ERROR

    def decide(self, row, approved):
        try:
            profile = getattr(self.app_state, "profile", {}) or {}
            actor = profile.get("username") or profile.get("national_code") or ""
            payload = {
                "status": "approved" if approved else "rejected",
                "active": bool(approved),
                "decision_at": datetime.now(timezone.utc).isoformat(),
                "decision_note": "تأیید شد" if approved else "رد شد",
            }
            if actor:
                payload["decision_by"] = profile.get("auth_user_id") or profile.get("user_id")
            self._api().table_update("module_activations", {"module_key": "eq." + str(row.get("module_key"))}, payload)
            self.status.text = fa_display("تصمیم با موفقیت ثبت شد.")
            self.status.color = SUCCESS
            self.load()
        except Exception as exc:
            self.status.text = fa_display("ثبت تصمیم انجام نشد: " + str(exc))
            self.status.color = ERROR

    def back(self, *_):
        if self.manager:
            self.manager.current = "panel"

    def dashboard(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
