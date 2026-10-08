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

from mobile.config import PRIMARY, SECONDARY, SUCCESS, WHITE, CARD, ERROR
from mobile.ui import font_name, rtl_text, PersianTextInput


DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"]
BELLS = [1, 2, 3]


class WeeklyScheduleScreen(Screen):
    """Real school timetable backed by public.weekly_schedule_entries."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.rows = []
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

    def _role(self):
        return str(getattr(self.app_state, "role", "") or "").strip().lower().replace("‌", " ")

    def _can_write(self):
        return self._role() in {
            "manager", "admin", "administrator", "مدیر", "مدیریت",
            "educational", "معاون آموزشی", "معاونت آموزشی",
            "executive", "معاون اجرایی", "معاونت اجرایی",
        }

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        top = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        top.add_widget(self.btn("بازگشت", self.back, PRIMARY, 40))
        top.add_widget(self.label("برنامه هفتگی مدرسه", "18sp", PRIMARY, True, True, 42))
        top.add_widget(self.btn("داشبورد", self.dashboard, PRIMARY, 40))
        root.add_widget(top)
        root.add_widget(self.label("روز: شنبه تا چهارشنبه  •  زنگ: ۱ تا ۳  •  کلاس × درس × دبیر", "9sp", SECONDARY, False, True, 28))

        if self._can_write():
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
        return self._api().table_select(
            "weekly_schedule_entries",
            {"order": "weekday.asc,period.asc,id.asc", "limit": "300"},
        ) or []

    def _loaded(self, rows, error):
        if error:
            self.status.text = rtl_text("خطا در دریافت برنامه: " + error)
            self.status.color = ERROR
            return
        self.rows = list(rows or [])
        self.selected = None
        self.status.text = rtl_text(f"{len(self.rows)} ردیف واقعی برنامه هفتگی")
        self.status.color = SUCCESS
        self._render()

    def _render(self):
        self.area.clear_widgets()
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        grid = GridLayout(cols=6, spacing=dp(3), padding=dp(3), size_hint=(None, None), width=dp(6 * 185))
        grid.bind(minimum_height=grid.setter("height"))

        headers = ["زنگ", *DAYS]
        for h in headers:
            grid.add_widget(self._cell(h, True, 58))

        for period in BELLS:
            grid.add_widget(self._cell(f"زنگ {period}", True, 72))
            for day in DAYS:
                matches = [
                    r for r in self.rows
                    if str(r.get("weekday") or "").replace("‌", "") == day.replace("‌", "")
                    and int(r.get("period") or 0) == period
                ]
                text = "—" if not matches else "\n".join(
                    f"{r.get('class_name') or 'کلاس'} • {r.get('subject') or 'درس'}\n{r.get('teacher_name') or 'دبیر'}"
                    for r in matches[:3]
                )
                grid.add_widget(self._cell(text, False, 82))

        scroll.add_widget(grid)
        self.area.add_widget(scroll)
        self.area.add_widget(self.label("فهرست رکوردها — برای ویرایش یا حذف، یک ردیف را انتخاب کنید.", "9sp", SECONDARY, False, True, 30))

        lst_scroll = ScrollView(do_scroll_x=False)
        lst = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        lst.bind(minimum_height=lst.setter("height"))
        for row in self.rows:
            title = f"{row.get('weekday') or '-'} • زنگ {row.get('period') or '-'} • {row.get('class_name') or '-'} • {row.get('subject') or '-'} • {row.get('teacher_name') or '-'}"
            line = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(4))
            line.add_widget(self.label(title, "9sp", SECONDARY, False, False, 46))
            if self._can_write():
                line.add_widget(self.btn("انتخاب", lambda *_a, x=row: self._select(x), PRIMARY, 40))
            lst.add_widget(line)
        lst_scroll.add_widget(lst)
        self.area.add_widget(lst_scroll)

    def _cell(self, text, header=False, height=72):
        box = BoxLayout(orientation="vertical", padding=dp(5), size_hint=(None, None), width=dp(185), height=dp(height))
        box.add_widget(self.label(text, "9sp" if not header else "10sp", WHITE if header else SECONDARY, header, True, height - 4))
        from kivy.graphics import Color, RoundedRectangle
        with box.canvas.before:
            Color(*(PRIMARY if header else CARD))
            bg = RoundedRectangle(radius=[dp(7)])
        box.bind(pos=lambda o, v: setattr(bg, "pos", v), size=lambda o, v: setattr(bg, "size", v))
        return box

    def _select(self, row):
        self.selected = dict(row or {})
        self.status.text = rtl_text("ردیف برنامه انتخاب شد.")
        self.status.color = SUCCESS

    def editor(self, row):
        if row is not None and not row.get("id"):
            self.status.text = rtl_text("شناسه رکورد برای ویرایش موجود نیست.")
            self.status.color = ERROR
            return

        fields = [
            ("weekday", "روز (شنبه تا چهارشنبه)"),
            ("period", "زنگ (۱ تا ۳)"),
            ("class_name", "کلاس"),
            ("subject", "درس"),
            ("teacher_name", "دبیر"),
            ("teacher_id", "شناسه دبیر (اختیاری)"),
            ("room", "کلاس/اتاق (اختیاری)"),
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
        popup = Popup(title=rtl_text(("ویرایش" if row else "ثبت جدید") + " • برنامه هفتگی"), content=root, size_hint=(.95, .90), auto_dismiss=False)
        actions.add_widget(self.btn("انصراف", lambda *_: popup.dismiss(), SECONDARY, 40))
        actions.add_widget(self.btn("ذخیره", lambda *_: self.save(row, inputs, popup), SUCCESS, 40))
        root.add_widget(actions)
        popup.open()

    def save(self, row, inputs, popup):
        day = inputs["weekday"].text.strip()
        try:
            period = int(inputs["period"].text.strip().replace("۱", "1").replace("۲", "2").replace("۳", "3"))
        except ValueError:
            period = 0
        valid_day = day.replace("‌", "") in {x.replace("‌", "") for x in DAYS}
        if not valid_day or period not in BELLS:
            self.status.text = rtl_text("روز باید شنبه تا چهارشنبه و زنگ باید ۱ تا ۳ باشد.")
            self.status.color = ERROR
            return
        payload = {
            "weekday": day,
            "period": period,
            "class_name": inputs["class_name"].text.strip(),
            "subject": inputs["subject"].text.strip(),
            "teacher_name": inputs["teacher_name"].text.strip(),
            "room": inputs["room"].text.strip() or None,
        }
        teacher_id = inputs["teacher_id"].text.strip()
        if teacher_id:
            try:
                payload["teacher_id"] = int(teacher_id)
            except ValueError:
                self.status.text = rtl_text("شناسه دبیر باید عددی باشد.")
                self.status.color = ERROR
                return
        if not payload["class_name"] or not payload["subject"] or not payload["teacher_name"]:
            self.status.text = rtl_text("کلاس، درس و دبیر الزامی است.")
            self.status.color = ERROR
            return

        popup.dismiss()
        self.status.text = rtl_text("در حال ذخیره در Supabase…")
        self.status.color = SECONDARY

        def work():
            api = self._api()
            if row is None:
                return api.table_insert("weekly_schedule_entries", payload)
            return api.table_update("weekly_schedule_entries", {"id": "eq." + str(row["id"])}, payload)

        self._async(work, lambda _, e: self._write_done(e))

    def _write_done(self, error):
        if error:
            self.status.text = rtl_text("خطا: " + error)
            self.status.color = ERROR
        else:
            self.status.text = rtl_text("برنامه در Supabase ذخیره شد و دوباره بارگذاری می‌شود.")
            self.status.color = SUCCESS
            self.load()

    def delete_selected(self):
        if not self.selected or not self.selected.get("id"):
            self.status.text = rtl_text("ابتدا یک ردیف را انتخاب کنید.")
            self.status.color = ERROR
            return
        rid = self.selected["id"]
        self._async(
            lambda: self._api().table_delete("weekly_schedule_entries", {"id": "eq." + str(rid)}),
            lambda _, e: self._write_done(e),
        )

    def back(self, *_):
        if self.manager:
            self.manager.current = "panel"

    def dashboard(self, *_):
        if self.manager:
            self.manager.current = "dashboard"
