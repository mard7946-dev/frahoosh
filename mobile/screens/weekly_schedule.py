from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner

from mobile.config import PRIMARY, SECONDARY, SUCCESS, WHITE, CARD, ERROR, SCHOOL_NAME, SCHOOL_YEAR
from mobile.ui import font_name, rtl_text, PersianTextInput


DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه"]
BELLS = ["زنگ ۱", "زنگ ۲", "زنگ ۳", "زنگ ۴", "زنگ ۵", "زنگ ۶"]


class WeeklyScheduleScreen(Screen):
    """Canonical ZIP timetable: day × bell × class × subject × teacher."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.rows = []
        self.generated = []
        self.selected = None
        self._build()

    def label(self, text, size="10sp", color=SECONDARY, bold=False, center=False, height=34):
        w = Label(
            text=rtl_text(str(text)),
            font_name=font_name(),
            font_size=size,
            color=color,
            bold=bold,
            halign="center" if center else "right",
            valign="middle",
            size_hint_y=None,
            height=dp(height),
        )
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def btn(self, text, cb, color=PRIMARY, h=42):
        b = Button(
            text=rtl_text(text),
            font_name=font_name(),
            font_size="10sp",
            background_normal="",
            background_color=color,
            color=WHITE,
            size_hint_y=None,
            height=dp(h),
        )
        b.bind(on_release=cb)
        return b

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        top = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        top.add_widget(self.btn("بازگشت", self.back, PRIMARY, 40))
        top.add_widget(self.label("برنامه هفتگی مدرسه", "18sp", PRIMARY, True, True, 42))
        top.add_widget(self.btn("داشبورد", self.dashboard, PRIMARY, 40))
        root.add_widget(top)
        root.add_widget(
            self.label(
                f"{SCHOOL_NAME} • سال تحصیلی {SCHOOL_YEAR} • روز × زنگ × کلاس × درس × دبیر",
                "9sp", SECONDARY, False, True, 28,
            )
        )

        role = str(getattr(self.app_state, "role", "") or "").strip().lower()
        writable_roles = {"manager", "admin", "administrator", "مدیر", "مدیریت", "executive", "معاون اجرایی"}
        if role in writable_roles:
            actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
            actions.add_widget(self.btn("ثبت جدید", lambda *_: self.editor(None), SUCCESS, 40))
            actions.add_widget(self.btn("ویرایش", lambda *_: self.editor(self.selected), PRIMARY, 40))
            actions.add_widget(self.btn("حذف", lambda *_: self.delete_selected(), ERROR, 40))
            root.add_widget(actions)

        self.status = self.label("در حال دریافت برنامه واقعی…", "9sp", SUCCESS, True, True, 28)
        root.add_widget(self.status)
        self.area = BoxLayout(orientation="vertical", spacing=dp(5))
        root.add_widget(self.area)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        Clock.schedule_once(lambda *_: self.load(), 0.03)

    def _api(self):
        api = getattr(self.app_state, "api", None)
        if api is None:
            raise RuntimeError("سرویس داده آماده نیست.")
        return api

    def _async(self, work, done):
        def run():
            try:
                value = work()
                Clock.schedule_once(lambda *_: done(value, None), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: done(None, str(exc)), 0)
        Thread(target=run, daemon=True).start()

    def load(self, *_):
        self.status.text = rtl_text("در حال دریافت برنامه واقعی…")
        self._async(self._fetch, self._loaded)

    def _fetch(self):
        api = self._api()
        base = api.table_select("weekly_schedule", {"order": "id.desc", "limit": "200"}) or []
        try:
            generated = api.table_select(
                "generated_weekly_schedule",
                {"order": "id.desc", "limit": "300"},
            ) or []
        except Exception:
            generated = []
        return {"base": base, "generated": generated}

    def _loaded(self, data, error):
        if error:
            self.status.text = rtl_text("خطا در دریافت برنامه: " + error)
            self.status.color = ERROR
            return
        self.rows = list((data or {}).get("base") or [])
        self.generated = list((data or {}).get("generated") or [])
        self.selected = None
        self.status.text = rtl_text(
            f"{len(self.rows)} تعریف برنامه • {len(self.generated)} خانه تولیدشده"
        )
        self.status.color = SUCCESS
        self._render_timetable()

    @staticmethod
    def _contains_day(raw, day):
        raw = str(raw or "")
        return day in raw or day.replace("‌", "") in raw.replace("‌", "")

    @staticmethod
    def _bell_number(raw):
        text = str(raw or "")
        for i, bell in enumerate(BELLS, 1):
            if bell in text or str(i) in text:
                return i
        return 1

    def _render_timetable(self):
        self.area.clear_widgets()
        source = self.generated or self.rows
        if not source:
            self.status.text = rtl_text("ساختار برنامه هفتگی آماده است؛ هنوز رکوردی برای نمایش ثبت نشده.")
            self.status.color = SECONDARY

        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        grid = GridLayout(
            cols=7,
            spacing=dp(3),
            padding=dp(3),
            size_hint=(None, None),
            width=dp(7 * 190),
        )
        grid.bind(minimum_height=grid.setter("height"))

        grid.add_widget(self._cell("روز / زنگ", True))
        for day in DAYS:
            grid.add_widget(self._cell(day, True))

        for bell_no, bell in enumerate(BELLS, 1):
            grid.add_widget(self._cell(bell, True))
            for day in DAYS:
                matches = []
                for row in source:
                    row_day = row.get("weekday") or row.get("weekdays") or row.get("day")
                    row_bell = row.get("bell") or row.get("bell_pattern") or row.get("period")
                    if self._contains_day(row_day, day) and self._bell_number(row_bell) == bell_no:
                        matches.append(row)
                values = []
                for row in matches[:3]:
                    subject = row.get("subject") or "درس"
                    teacher = row.get("teacher") or row.get("teacher_name") or "دبیر"
                    cls = row.get("class_name") or row.get("class_names") or "کلاس"
                    values.append(f"{subject} • {teacher}\n{cls}")
                self._add_grid_cell(grid, "\n".join(values) if values else "—")

        scroll.add_widget(grid)
        self.area.add_widget(scroll)

        self.area.add_widget(
            self.label(
                ("برای ویرایش یا حذف، یک تعریف برنامه را از فهرست پایین انتخاب کنید."
                 if self.rows else "برای ساخت اولین برنامه، «ثبت جدید» را بزنید؛ جدول روز × زنگ همین حالا آماده است."),
                "9sp", SECONDARY, False, True, 30,
            )
        )
        list_scroll = ScrollView(do_scroll_x=False)
        lst = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        lst.bind(minimum_height=lst.setter("height"))
        for row in self.rows:
            title = " • ".join(
                [
                    str(row.get("teacher") or row.get("teacher_name") or "دبیر"),
                    str(row.get("subject") or "درس"),
                    str(row.get("class_names") or row.get("class_name") or "کلاس"),
                    str(row.get("weekdays") or "روز ثبت نشده"),
                    str(row.get("bell_pattern") or "زنگ ثبت نشده"),
                ]
            )
            line = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(4))
            line.add_widget(self.label(title, "9sp", SECONDARY, False, False, 46))
            line.add_widget(self.btn("انتخاب", lambda *_a, x=row: self._select(x), PRIMARY, 40))
            lst.add_widget(line)
        list_scroll.add_widget(lst)
        self.area.add_widget(list_scroll)

    def _add_grid_cell(self, grid, text):
        grid.add_widget(self._cell(text, False))

    def _cell(self, text, header=False):
        h = 66 if header else 92
        box = BoxLayout(
            orientation="vertical",
            padding=dp(5),
            size_hint=(None, None),
            width=dp(190),
            height=dp(h),
        )
        box.add_widget(self.label(text, "9sp" if not header else "10sp",
                                   WHITE if header else SECONDARY, header, True, h - 4))
        with box.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*(PRIMARY if header else CARD))
            bg = RoundedRectangle(radius=[dp(7)])
        box.bind(pos=lambda o, v: setattr(bg, "pos", v),
                 size=lambda o, v: setattr(bg, "size", v))
        return box

    def _select(self, row):
        self.selected = dict(row or {})
        self.status.text = rtl_text("تعریف برنامه انتخاب شد؛ ویرایش یا حذف را انتخاب کنید.")
        self.status.color = SUCCESS

    def editor(self, row):
        if row is not None and not row.get("id"):
            self.status.text = rtl_text("شناسه این برنامه برای ویرایش موجود نیست.")
            self.status.color = ERROR
            return

        fields = [
            ("teacher", "نام دبیر"),
            ("teacher_id", "شناسه دبیر"),
            ("subject", "درس"),
            ("grade", "پایه"),
            ("class_names", "کلاس / کلاس‌ها"),
            ("class_count", "تعداد کلاس"),
            ("hours", "ساعت هفتگی"),
            ("weekdays", "روزهای هفته (مثلاً شنبه، دوشنبه)"),
            ("bell_pattern", "زنگ / زنگ‌ها (مثلاً زنگ ۱)"),
        ]
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(5))
        scroll = ScrollView()
        form = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        inputs = {}

        for key, hint in fields:
            form.add_widget(self.label(hint, "9sp", PRIMARY, True, False, 26))
            ti = PersianTextInput(
                text="" if row is None else str(row.get(key, "")),
                hint_text=rtl_text(hint),
                font_name=font_name(),
                font_size="12sp",
                halign="right",
                multiline=False,
                size_hint_y=None,
                height=dp(42),
            )
            inputs[key] = ti
            form.add_widget(ti)

        scroll.add_widget(form)
        root.add_widget(scroll)
        actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        popup = Popup(
            title=rtl_text(("ویرایش" if row else "ثبت جدید") + " • برنامه هفتگی"),
            content=root,
            size_hint=(.95, .90),
            auto_dismiss=False,
        )
        actions.add_widget(self.btn("انصراف", lambda *_: popup.dismiss(), SECONDARY, 40))
        actions.add_widget(self.btn("ذخیره", lambda *_: self.save(row, inputs, popup), SUCCESS, 40))
        root.add_widget(actions)
        popup.open()

    def save(self, row, inputs, popup):
        payload = {k: v.text.strip() for k, v in inputs.items() if v.text.strip()}
        if not payload.get("teacher") or not payload.get("subject") or not payload.get("class_names"):
            self.status.text = rtl_text("نام دبیر، درس و کلاس الزامی است.")
            self.status.color = ERROR
            return
        try:
            payload["class_count"] = int(payload.get("class_count") or 1)
        except ValueError:
            payload["class_count"] = 1

        popup.dismiss()
        self.status.text = rtl_text("در حال ذخیره برنامه واقعی…")
        self.status.color = SECONDARY

        def work():
            api = self._api()
            if row is None:
                return api.table_insert("weekly_schedule", payload)
            rid = row.get("id")
            return api.table_update("weekly_schedule", {"id": "eq." + str(rid)}, payload)

        self._async(
            work,
            lambda _, e: self._write_done(
                "برنامه با موفقیت " + ("ثبت شد." if row is None else "ویرایش شد."), e
            ),
        )

    def _write_done(self, msg, error):
        self.status.text = rtl_text(("خطا: " + error) if error else msg)
        self.status.color = ERROR if error else SUCCESS
        if not error:
            self.load()

    def delete_selected(self):
        if not self.selected or not self.selected.get("id"):
            self.status.text = rtl_text("ابتدا یک تعریف برنامه را انتخاب کنید.")
            self.status.color = ERROR
            return
        rid = self.selected["id"]

        def work():
            return self._api().table_delete("weekly_schedule", {"id": "eq." + str(rid)})

        self._async(work, lambda _, e: self._write_done("برنامه حذف شد.", e))

    def back(self, *_):
        if self.manager:
            self.manager.current = "panel"

    def dashboard(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
