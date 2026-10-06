from datetime import datetime
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label

from mobile.ui import font_name, fa_display
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE


class StudentActivitiesRegistrationScreen(Screen):
    """Real student registration center for competitions and school groups.

    This screen deliberately avoids exposing raw database IDs. The student only
    chooses a real available activity and presses «ثبت نام».
    """

    def __init__(self, app_state=None, mode="all", **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.mode = mode or "all"
        self.student = {}
        self.competitions = []
        self._build()

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None:
            raise RuntimeError("سرویس داده آماده نیست.")
        return api

    def _profile(self):
        return getattr(self.app_state, "profile", {}) or {}

    def _student_id(self):
        profile = self._profile()
        value = profile.get("linked_student_id") or profile.get("student_id")
        if value:
            return int(value)
        national_code = str(profile.get("national_code") or getattr(self.app_state, "national_code", "") or "").strip()
        if not national_code:
            raise RuntimeError("پرونده دانش‌آموزی به حساب متصل نیست.")
        rows = self._api().table_select("students", {"national_code": "eq." + national_code, "select": "*", "limit": "1"}) or []
        if not rows:
            raise RuntimeError("پرونده دانش‌آموزی پیدا نشد.")
        self.student = dict(rows[0])
        return int(rows[0]["id"])

    def _student_name(self):
        if self.student:
            return (str(self.student.get("first_name") or "") + " " + str(self.student.get("last_name") or "")).strip()
        profile = self._profile()
        return str(profile.get("display_name") or getattr(self.app_state, "display_name", "") or "دانش‌آموز").strip()

    def _label(self, text, size="11sp", color=SECONDARY, height=38, bold=False):
        w = Label(
            text=fa_display(str(text)), font_name=font_name(), font_size=size,
            color=color, bold=bold, halign="right", valign="middle",
            size_hint_y=None, height=dp(height),
        )
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _button(self, text, callback, color=PRIMARY, height=44):
        b = Button(
            text=fa_display(text), font_name=font_name(), font_size="11sp",
            background_normal="", background_color=color, color=WHITE,
            size_hint_y=None, height=dp(height),
        )
        b.bind(on_release=callback)
        return b

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        header.add_widget(self._button("بازگشت", self.back, SECONDARY, 42))
        header.add_widget(self._label("ثبت‌نام فعالیت‌های دانش‌آموزی", "17sp", PRIMARY, 42, True))
        root.add_widget(header)

        self.status = self._label("در حال دریافت اطلاعات واقعی…", "10sp", SECONDARY, 38, True)
        root.add_widget(self.status)

        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(7), padding=[dp(3), dp(5)], size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        Clock.schedule_once(lambda *_: self.load(), 0.02)

    def load(self):
        self.status.text = fa_display("در حال دریافت گزینه‌های قابل ثبت‌نام…")
        def work():
            try:
                sid = self._student_id()
                api = self._api()
                student_rows = api.table_select("students", {"id": "eq." + str(sid), "limit": "1"}) or []
                if student_rows:
                    self.student = dict(student_rows[0])
                self.competitions = self._load_competitions(api)
                registrations = {
                    "student_council": api.table_select("student_council", {"student_id": "eq." + str(sid), "limit": "1"}) or [],
                    "basij_registration": api.table_select("basij_registration", {"student_id": "eq." + str(sid), "limit": "1"}) or [],
                    "school_ally": api.table_select("school_ally", {"student_id": "eq." + str(sid), "limit": "1"}) or [],
                    "school_mayor": api.table_select("school_mayor", {"student_id": "eq." + str(sid), "limit": "1"}) or [],
                    "activity_registrations": api.table_select("activity_registrations", {"student_id": "eq." + str(sid), "limit": "200"}) or [],
                }
                Clock.schedule_once(lambda *_: self._render(registrations), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error(str(exc)), 0)

        Thread(target=work, daemon=True).start()

    def _load_competitions(self, api):
        sources = [
            ("مسابقه", "competitions", "title", "status"),
            ("مسابقه فرهنگی", "cultural_competitions", "title", "status"),
            ("مسابقه هنری", "art_competitions", "title", "status"),
            ("مسابقه ورزشی", "sport_competitions", "title", "status"),
            ("فعالیت", "activity_programs", "title", "active"),
            ("پیشنهاد فعالیت", "activity_offers", "title", "active"),
        ]
        result = []
        for source_label, table, title_field, state_field in sources:
            try:
                rows = api.table_select(table, {"order": "id.desc", "limit": "100"}) or []
                for row in rows:
                    state = row.get(state_field)
                    if state is False or str(state).strip().lower() in {"inactive", "غیرفعال", "بسته", "closed", "منقضی"}:
                        continue
                    title = str(row.get(title_field) or "بدون عنوان").strip()
                    if title:
                        result.append({
                            "source": table,
                            "source_label": source_label,
                            "id": row.get("id"),
                            "title": title,
                            "category": str(row.get("category") or row.get("sport_type") or source_label),
                        })
            except Exception as exc:
                print("STUDENT ACTIVITY SOURCE ERROR", table, repr(exc))
        return result

    def _render(self, registrations):
        self.body.clear_widgets()
        self.body.add_widget(self._label(
            f"سلام {self._student_name()}؛ ثبت‌نام‌ها مستقیماً در سامانه ذخیره می‌شوند.",
            "10sp", SUCCESS, 46, True
        ))

        if self.mode in {"all", "competitions"}:
            self._render_competitions(registrations.get("activity_registrations") or [])

        direct = [
            ("student_council", "شورای دانش‌آموزی", "ثبت‌نام در انتخابات شورای دانش‌آموزی"),
            ("basij_registration", "بسیج دانش‌آموزی", "درخواست عضویت در بسیج دانش‌آموزی"),
            ("school_ally", "همیار مدرسه", "ثبت‌نام به‌عنوان همیار مدرسه"),
            ("school_mayor", "شهردار مدرسه", "ثبت‌نام برای طرح شهردار مدرسه"),
        ]
        for key, title, action in direct:
            if self.mode not in {"all", key}:
                continue
            rows = registrations.get(key) or []
            box = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(5), size_hint_y=None)
            box.height = dp(92)
            box.add_widget(self._label(title, "14sp", PRIMARY, 34, True))
            if rows:
                current = rows[0]
                box.add_widget(self._label("وضعیت ثبت‌نام: " + str(current.get("status") or "در انتظار بررسی"), "10sp", SUCCESS, 32))
            else:
                box.add_widget(self._button("ثبت‌نام", lambda *_a, k=key: self._register_direct(k), SUCCESS, 42))
            self.body.add_widget(box)

        if not self.body.children:
            self.body.add_widget(self._label("گزینه‌ای برای این بخش پیدا نشد.", "11sp", ERROR, 50, True))
        self.status.text = fa_display("اطلاعات واقعی بارگذاری شد.")
        self.status.color = SUCCESS

    def _render_competitions(self, registrations):
        self.body.add_widget(self._label("مسابقات و فعالیت‌های قابل ثبت‌نام", "15sp", PRIMARY, 42, True))
        registered_ids = {str(x.get("activity_id")) for x in registrations if x.get("activity_id") is not None}
        if not self.competitions:
            self.body.add_widget(self._label("فعلاً مسابقه یا فعالیت فعالی برای ثبت‌نام وجود ندارد.", "10sp", ERROR, 46))
            return
        for item in self.competitions:
            box = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(4), size_hint_y=None)
            box.height = dp(104)
            box.add_widget(self._label(
                f"{item['title']}  •  {item['source_label']}  •  {item['category']}",
                "11sp", WHITE, 38, True
            ))
            if str(item.get("id")) in registered_ids:
                box.add_widget(self._label("ثبت‌نام شما قبلاً ثبت شده است.", "10sp", SUCCESS, 32))
            else:
                box.add_widget(self._button(
                    "ثبت‌نام در این مورد",
                    lambda *_a, item=item: self._register_competition(item),
                    SUCCESS, 42
                ))
            self.body.add_widget(box)

    def _register_direct(self, table):
        def work():
            try:
                sid = self._student_id()
                api = self._api()
                name = self._student_name()
                existing = api.table_select(table, {"student_id": "eq." + str(sid), "limit": "1"}) or []
                if existing:
                    raise RuntimeError("برای شما قبلاً ثبت‌نام شده است.")
                today = datetime.now().strftime("%Y-%m-%d")
                payload = {"student_id": sid, "student_name": name, "status": "pending"}
                if table == "student_council":
                    payload["election_year"] = "سال تحصیلی جاری"
                elif table == "basij_registration":
                    payload["registration_date"] = today
                api.table_insert(table, payload)
                Clock.schedule_once(lambda *_: self._done("ثبت‌نام شما با موفقیت ثبت شد."), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error("ثبت‌نام انجام نشد: " + str(exc)), 0)
        self.status.text = fa_display("در حال ثبت‌نام واقعی…")
        Thread(target=work, daemon=True).start()

    def _register_competition(self, item):
        def work():
            try:
                sid = self._student_id()
                api = self._api()
                existing = api.table_select("activity_registrations", {
                    "student_id": "eq." + str(sid),
                    "activity_id": "eq." + str(item["id"]),
                    "limit": "1",
                }) or []
                if existing:
                    raise RuntimeError("برای این مسابقه قبلاً ثبت‌نام شده است.")
                api.table_insert("activity_registrations", {
                    "activity_id": item["id"],
                    "student_id": sid,
                    "participation_type": "انفرادی",
                    "team_members": "",
                    "competition_type": item["category"],
                    "payment_status": "بدون پرداخت",
                    "status": "pending",
                })
                Clock.schedule_once(lambda *_: self._done("ثبت‌نام در مسابقه با موفقیت ثبت شد."), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._error("ثبت‌نام مسابقه انجام نشد: " + str(exc)), 0)
        self.status.text = fa_display("در حال ثبت‌نام واقعی…")
        Thread(target=work, daemon=True).start()

    def _done(self, message):
        self.status.text = fa_display(message)
        self.status.color = SUCCESS
        self.load()

    def _error(self, message):
        self.status.text = fa_display(message)
        self.status.color = ERROR

    def back(self, *_):
        if self.manager:
            self.manager.current = "panel"
