from datetime import datetime, timezone
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, fa_display, PersianTextInput
from mobile.screens.operational_centers import role_of


class SchoolRelationshipsScreen(Screen):
    """Real school relationship directory backed by public.school_relationships."""
    RELATION_TYPES = ("ارتباط کاری", "ارتباط آموزشی", "ارتباط پرورشی", "ارتباط مشاوره‌ای", "ارتباط اجرایی", "ارتباط مستقیم")

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.targets = []
        self.rows = []
        self._build()

    def api(self):
        api = getattr(self.app_state, "api", None)
        if api is None:
            raise RuntimeError("اتصال پایگاه داده آماده نیست.")
        return api

    def role(self):
        return role_of(self.app_state)

    def profile(self):
        return getattr(self.app_state, "profile", {}) or {}

    def username(self):
        p = self.profile()
        u = getattr(self.app_state, "user", {}) or {}
        return str(p.get("username") or p.get("email") or u.get("email") or getattr(self.app_state, "national_code", "") or "").strip()

    def label(self, text, size="10sp", color=SECONDARY, bold=False, h=40, center=False):
        w = Label(text=fa_display(str(text)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="center" if center else "right",
                  valign="middle", size_hint_y=None, height=dp(h))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def btn(self, text, cb, color=PRIMARY, h=42):
        b = Button(text=fa_display(text), font_name=font_name(), font_size="10sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(h))
        b.bind(on_release=cb)
        return b

    def field(self, hint, h=44):
        return PersianTextInput(hint_text=fa_display(hint), font_name=font_name(),
                                font_size="11sp", halign="right", size_hint_y=None, height=dp(h))

    def spin(self, hint, values):
        return Spinner(text=fa_display(hint), values=tuple(fa_display(v) for v in values),
                       font_name=font_name(), font_size="10sp", size_hint_y=None, height=dp(44))

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        head.add_widget(self.btn("بازگشت", self.back, SECONDARY, 40))
        head.add_widget(self.label("ارتباط افراد مدرسه", "17sp", PRIMARY, True, 40, True))
        head.add_widget(self.btn("پیام‌رسانی", self.open_messages, PRIMARY, 40))
        root.add_widget(head)
        self.status = self.label("در حال دریافت ارتباط‌های واقعی…", "9sp", SECONDARY, True, 30, True)
        root.add_widget(self.status)
        sc = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(3), size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        sc.add_widget(self.body)
        root.add_widget(sc)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.load()

    def load(self):
        self.body.clear_widgets()
        try:
            self.rows = self.api().table_select("school_relationships", {"order": "id.desc", "limit": "500"}) or []
            self.targets = self.api().table_select(
                "account_settings",
                {"select": "username,display_name,role,email", "order": "display_name.asc", "limit": "500"},
            ) or []
            self.status.text = fa_display(f"{len(self.rows)} ارتباط واقعی از Supabase")
            self.status.color = SUCCESS
            self.render()
        except Exception as exc:
            self.status.text = fa_display("دریافت ارتباط‌ها ناموفق بود: " + str(exc))
            self.status.color = ERROR

    def render(self):
        role = self.role()
        writable = role in {"manager", "executive"}
        self.body.add_widget(self.label(
            "این بخش فهرست واقعی ارتباط‌های مجاز مدرسه را نگهداری می‌کند. پیام مستقیم از دکمه پیام‌رسانی انجام می‌شود.",
            "10sp", SECONDARY, False, 54, True,
        ))
        if writable:
            self.body.add_widget(self.label("تعریف ارتباط جدید", "12sp", PRIMARY, True, 34, True))
            target_names = []
            target_map = {}
            for row in self.targets:
                username = str(row.get("username") or "").strip()
                if not username or username == self.username():
                    continue
                name = str(row.get("display_name") or username).strip()
                role_name = str(row.get("role") or "").strip()
                value = f"{name} | {username}" + (f" | {role_name}" if role_name else "")
                target_names.append(value)
                target_map[value] = row
            target = self.spin("انتخاب فرد مدرسه", target_names or ["فردی پیدا نشد"])
            role_input = self.field("نقش مخاطب")
            relation = self.spin("نوع ارتباط", self.RELATION_TYPES)
            target_username = self.field("نام کاربری مخاطب (در صورت نبود فهرست)")
            active = self.spin("وضعیت", ["فعال", "غیرفعال"])
            for w in (target, role_input, relation, target_username, active):
                self.body.add_widget(w)
            def save(*_):
                selected = target_map.get(target.text)
                username = str((selected or {}).get("username") or self._value(target_username)).strip()
                if not username or username == self.username():
                    self.status.text = fa_display("مخاطب معتبر را انتخاب یا نام کاربری آن را وارد کنید.")
                    self.status.color = ERROR
                    return
                target_role = str((selected or {}).get("role") or self._value(role_input)).strip()
                payload = {
                    "source_username": self.username(),
                    "target_username": username,
                    "target_role": target_role,
                    "relationship_type": self._value(relation),
                    "active": self._value(active) == "فعال",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    self.api().table_insert("school_relationships", payload, return_representation=False)
                    self.status.text = fa_display("ارتباط در پایگاه داده ثبت شد.")
                    self.status.color = SUCCESS
                    self.load()
                except Exception as exc:
                    self.status.text = fa_display("ثبت ارتباط انجام نشد: " + str(exc))
                    self.status.color = ERROR
            self.body.add_widget(self.btn("ثبت ارتباط واقعی", save, SUCCESS, 46))

        if not self.rows:
            self.body.add_widget(self.label("ارتباطی برای نمایش ثبت نشده است.", "10sp", SECONDARY, True, 48, True))
            return
        self.body.add_widget(self.label("فهرست ارتباط‌ها", "12sp", PRIMARY, True, 34, True))
        grid = GridLayout(cols=5, spacing=dp(1), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for h in ("مبدأ", "مقصد", "نقش", "نوع ارتباط", "وضعیت"):
            grid.add_widget(self.label(h, "8sp", WHITE, True, 38, True))
        for row in self.rows:
            values = [
                row.get("source_username") or "—",
                row.get("target_username") or "—",
                row.get("target_role") or "—",
                row.get("relationship_type") or "—",
                "فعال" if row.get("active") else "غیرفعال",
            ]
            for value in values:
                grid.add_widget(self.label(str(value), "8sp", SECONDARY, False, 42, True))
            if writable:
                actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(3))
                actions.add_widget(self.btn("حذف", lambda *_a, rid=row.get("id"): self.delete(rid), ERROR, 40))
                self.body.add_widget(actions)
        self.body.add_widget(grid)

    def delete(self, rid):
        if not rid:
            return
        try:
            self.api().table_delete("school_relationships", {"id": "eq." + str(rid)})
            self.status.text = fa_display("ارتباط حذف شد.")
            self.status.color = SUCCESS
            self.load()
        except Exception as exc:
            self.status.text = fa_display("حذف ارتباط انجام نشد: " + str(exc))
            self.status.color = ERROR

    def _value(self, widget):
        return str(getattr(widget, "text", "") or "").strip()

    def open_messages(self, *_):
        if self.manager:
            try:
                from kivy.app import App
                screen = App.get_running_app().ensure_message_workflow()
                self.manager.current = screen.name
            except Exception as exc:
                self.status.text = fa_display("باز کردن پیام‌رسانی انجام نشد: " + str(exc))
                self.status.color = ERROR

    def back(self, *_):
        if self.manager:
            self.manager.current = "panel"
