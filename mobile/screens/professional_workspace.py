from threading import Thread

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from mobile.config import APP_NAME, CARD, PRIMARY, SCHOOL_NAME, SCHOOL_YEAR, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text
from mobile.screens.module_workspace import ModuleWorkspaceScreen, SUBMENUS, FRIENDLY


class ProfessionalWorkspaceScreen(ModuleWorkspaceScreen):
    """Operational module workspace: collapsible subpanels, no PageLayout/swipe navigation."""

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6))
        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        top.add_widget(self.btn("بازگشت", self.go_back, PRIMARY, dp(40), dp(78)))
        self.title = self.label(APP_NAME, "18sp", PRIMARY, True, "center")
        top.add_widget(self.title)
        top.add_widget(self.btn("داشبورد", self.go_dashboard, PRIMARY, dp(40), dp(45)))
        root.add_widget(top)
        root.add_widget(self.label(SCHOOL_NAME + "  •  سال تحصیلی " + (SCHOOL_YEAR or "۱۴۰۵-۱۴۰۶"), "9sp", SECONDARY, False, "center"))
        self.status = self.label("محیط عملیاتی آماده است", "9sp", SUCCESS, True, "center")
        root.add_widget(self.status)

        # The professional landing UI replaces ModuleWorkspaceScreen._build().
        # Keep the table-workspace widgets that ModuleWorkspaceScreen.open_table()
        # expects, otherwise the first real module tap reaches an incomplete
        # screen and Android can terminate while Kivy is processing the callback.
        self.subscroll = ScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height=dp(49),
        )
        self.subbar = BoxLayout(
            orientation="horizontal",
            spacing=dp(5),
            size_hint_x=None,
        )
        self.subbar.bind(minimum_width=self.subbar.setter("width"))
        self.subscroll.add_widget(self.subbar)

        self.body = BoxLayout(orientation="vertical", spacing=dp(7))
        root.add_widget(self.body)
        self.add_widget(root)

    def set_module(self, route, return_to="dashboard"):
        self.route = route if route in SUBMENUS else "management"
        self.return_to = return_to or "dashboard"
        self.table = None
        self.render()

    load_module = set_module

    def render(self):
        self.body.clear_widgets()
        items = SUBMENUS.get(self.route, [])
        self.title.text = rtl_text(FRIENDLY.get(items[0][1], items[0][0]) if items else APP_NAME)

        intro = self._surface(dp(84))
        intro.add_widget(self.label(FRIENDLY.get(self.route, self.route), "20sp", PRIMARY, True, "center"))
        intro.add_widget(self.label("زیرپنل‌ها کشویی و مستقل هستند؛ برای باز کردن هر بخش روی عنوان آن بزنید.", "9sp", SECONDARY, False, "center"))
        self.body.add_widget(intro)

        scroll = ScrollView(do_scroll_x=False)
        box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        for index, (text, table) in enumerate(items, 1):
            box.add_widget(self._accordion(text, table, index))
        scroll.add_widget(box)
        self.body.add_widget(scroll)

    def _surface(self, height):
        s = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(5), size_hint_y=None, height=height)
        with s.canvas.before:
            Color(*CARD)
            bg = RoundedRectangle(radius=[dp(15)])
        s.bind(pos=lambda o, v: setattr(bg, "pos", v), size=lambda o, v: setattr(bg, "size", v))
        return s

    def _accordion(self, text, table, index):
        holder = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(52), spacing=dp(3))
        header = Button(text=rtl_text("باز کردن: " + text), font_name=font_name(), font_size="12sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_y=None, height=dp(48))
        content = BoxLayout(orientation="vertical", size_hint_y=None, height=0, padding=dp(8), spacing=dp(5))
        header.bind(on_release=lambda *_: self._toggle(holder, header, content, table, text))
        holder.add_widget(header)
        holder.add_widget(content)
        return holder

    def _toggle(self, holder, header, content, table, text):
        if content.height > 0:
            content.clear_widgets()
            content.height = 0
            holder.height = dp(52)
            header.text = rtl_text("باز کردن: " + text)
            return
        content.clear_widgets()
        header.text = rtl_text("بستن: " + text)
        if table in ("teacher_exams", "quiz_questions", "online_classes", "online_class_sessions"):
            self._special_content(content, table)
        elif table in ("messages", "message_targets", "message_reads"):
            self._message_content(content)
        elif table in ("payment_offers", "finance_donations", "payment_records", "payment_attempts"):
            self._payment_content(content, table)
        else:
            content.add_widget(self.btn("ورود به محیط عملیاتی این بخش", lambda *_: self.open_table(table), SUCCESS if self.can_write(table) else PRIMARY, dp(42)))
            content.add_widget(self.label(self._purpose(table), "9sp", SECONDARY, False, "center"))
        content.height = dp(max(86, 55 + len(content.children) * 45))
        holder.height = dp(52) + content.height

    def _purpose(self, table):
        return {
            "students": "پرونده دانش‌آموز، مشخصات، پایه و کلاس.",
            "teachers": "مشخصات و فهرست دبیران مدرسه.",
            "attendance": "ثبت و مشاهده حضور، غیبت و تأخیر دانش‌آموزان.",
            "grades": "ثبت نمرات و ارزیابی‌های درسی.",
            "student_grades": "ارزیابی عملکرد تحصیلی هر دانش‌آموز.",
            "assignments": "ثبت تکلیف و پیگیری وضعیت انجام آن.",
            "lesson_plans": "ثبت و مدیریت طرح درس دبیر.",
            "weekly_schedule": "برنامه هفتگی کلاس‌ها و دبیران.",
            "exam_schedule": "زمان‌بندی امتحانات مدرسه.",
            "finance_accounts": "حساب‌ها و مقصدهای مالی مدرسه.",
            "school_events": "رویدادها و برنامه‌های مدرسه.",
        }.get(table, "اطلاعات واقعی این بخش از سامانه مدرسه.")

    def _special_content(self, content, table):
        if table in ("teacher_exams", "quiz_questions"):
            if table == "teacher_exams":
                content.add_widget(self.btn("＋ ساخت آزمون جدید", lambda *_: self._exam_editor(), SUCCESS, dp(42)))
                content.add_widget(self.btn("آزمون‌های من و مدیریت سؤالات", lambda *_: self._exam_list(), PRIMARY, dp(42)))
                content.add_widget(self.label("پنج نوع سؤال، کلید پاسخ، بارم، تصحیح خودکار و انتشار آزمون در همین محیط مدیریت می‌شود.", "9sp", SECONDARY, False, "center"))
            else:
                self._question_list(content, None)
        else:
            content.add_widget(self.btn("＋ ایجاد کلاس آنلاین", lambda *_: self._online_editor(), SUCCESS, dp(42)))
            content.add_widget(self.btn("کلاس‌ها و مدیریت جلسه", lambda *_: self._online_list(), PRIMARY, dp(42)))
            content.add_widget(self.label("زمان‌بندی، فعال‌سازی، جلسه، حضور، تخته و لینک ورود از همین بخش مدیریت می‌شود.", "9sp", SECONDARY, False, "center"))

    def _popup_form(self, title, fields, save_cb, size=(.94, .88)):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        sc = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        form.bind(minimum_height=form.setter("height"))
        inputs = {}
        for key, hint in fields:
            form.add_widget(self.label(hint, "9sp", PRIMARY, True))
            ti = TextInput(font_name=font_name(), font_size="10sp", halign="right", multiline=False, size_hint_y=None, height=dp(40), padding=[dp(8), dp(6)])
            inputs[key] = ti
            form.add_widget(ti)
        sc.add_widget(form)
        root.add_widget(sc)
        actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        p = Popup(title=rtl_text(title), content=root, size_hint=size, auto_dismiss=False)
        actions.add_widget(self.btn("انصراف", lambda *_: p.dismiss(), SECONDARY, dp(40)))
        actions.add_widget(self.btn("ذخیره", lambda *_: save_cb(inputs, p), SUCCESS, dp(40)))
        root.add_widget(actions)
        p.open()

    def _exam_editor(self):
        self._popup_form("ساخت آزمون آنلاین", [
            ("title", "عنوان آزمون"), ("subject", "درس"), ("grade", "پایه"), ("class_name", "کلاس"),
            ("duration", "مدت آزمون به دقیقه"), ("description", "توضیحات"), ("max_attempts", "حداکثر دفعات شرکت"), ("passing_score", "نمره قبولی"),
        ], self._save_exam, (.94, .9))

    def _save_exam(self, inputs, popup):
        payload = {k: v.text.strip() for k, v in inputs.items() if v.text.strip()}
        payload.setdefault("exam_type", "آزمون آنلاین")
        payload.setdefault("published", False)
        payload.setdefault("secure_mode", True)
        payload.setdefault("standard_mode", True)
        try:
            payload["duration"] = int(payload.get("duration", 45))
            payload["max_attempts"] = int(payload.get("max_attempts", 1))
            payload["passing_score"] = float(payload.get("passing_score", 0))
        except ValueError:
            self.message("ساخت آزمون", "مدت، دفعات شرکت و نمره قبولی باید عددی باشند.")
            return
        if not payload.get("title"):
            self.message("ساخت آزمون", "عنوان آزمون الزامی است.")
            return
        popup.dismiss()
        self._write_async("teacher_exams", payload, "آزمون با موفقیت ساخته شد.")

    def _exam_list(self):
        self.table = "teacher_exams"
        self.body.clear_widgets()
        head = self._surface(dp(74))
        head.add_widget(self.label("مدیریت آزمون‌های آنلاین دبیر", "17sp", PRIMARY, True, "center"))
        head.add_widget(self.btn("＋ آزمون جدید", lambda *_: self._exam_editor(), SUCCESS, dp(38)))
        self.body.add_widget(head)
        area = BoxLayout(orientation="vertical")
        self.body.add_widget(area)
        self._load_to(area, "teacher_exams", self._exam_card)

    def _exam_card(self, area, row):
        card = self._surface(dp(118))
        title = row.get("title", "بدون عنوان")
        info = " | ".join(str(row.get(k, "")) for k in ("subject", "grade", "class_name") if row.get(k))
        card.add_widget(self.label(title, "13sp", PRIMARY, True, "center"))
        card.add_widget(self.label(info or "درس/کلاس هنوز تعیین نشده", "9sp", SECONDARY, False, "center"))
        card.add_widget(self.label("انتشار: " + ("فعال" if row.get("published") else "پیش‌نویس") + "  •  مدت: " + str(row.get("duration", "45")) + " دقیقه", "9sp", SECONDARY, False, "center"))
        actions = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(4))
        actions.add_widget(self.btn("سؤالات", lambda *_a, rid=row.get("id"): self._question_list_popup(rid), PRIMARY, dp(38)))
        actions.add_widget(self.btn("انتشار/لغو", lambda *_a, r=dict(row): self._toggle_exam(r), SUCCESS, dp(38)))
        actions.add_widget(self.btn("حذف", lambda *_a, rid=row.get("id"): self._delete_simple("teacher_exams", rid), (0.72,.16,.18,1), dp(38)))
        card.add_widget(actions)
        area.add_widget(card)

    def _question_list_popup(self, quiz_id):
        self._question_list(self.body, quiz_id)

    def _question_list(self, parent, quiz_id):
        if quiz_id is None:
            parent.add_widget(self.label("ابتدا یک آزمون را انتخاب کنید تا سؤال‌های همان آزمون مدیریت شود.", "9sp", SECONDARY, False, "center"))
            return
        parent.add_widget(self.btn("＋ سؤال جدید", lambda *_: self._question_editor(quiz_id), SUCCESS, dp(42)))
        self._load_to(parent, "quiz_questions", self._question_card, filters={"quiz_id":"eq." + str(quiz_id)})

    def _question_card(self, parent, row):
        card = self._surface(dp(112))
        card.add_widget(self.label(str(row.get("question", "سؤال بدون متن")), "11sp", PRIMARY, True, "right"))
        card.add_widget(self.label("نوع: " + str(row.get("question_type", "multiple_choice")) + "  •  بارم: " + str(row.get("points", 1)) + "  •  تصحیح خودکار: " + ("بله" if row.get("auto_grade", True) else "خیر"), "9sp", SECONDARY, False, "right"))
        card.add_widget(self.label("کلید پاسخ: " + str(row.get("correct_answer", "—")), "9sp", SECONDARY, False, "right"))
        parent.add_widget(card)

    def _question_editor(self, quiz_id):
        self._popup_form("ثبت سؤال آزمون", [
            ("question", "متن سؤال"), ("question_type", "نوع سؤال: multiple_choice / true_false / fill_blank / short_answer / essay"),
            ("option1", "گزینه ۱"), ("option2", "گزینه ۲"), ("option3", "گزینه ۳"), ("option4", "گزینه ۴"),
            ("correct_answer", "کلید پاسخ"), ("accepted_answers", "پاسخ‌های قابل قبول با | جدا شوند"), ("points", "بارم"), ("negative_score", "نمره منفی"),
        ], lambda inputs, popup: self._save_question(inputs, popup, quiz_id), (.96, .94))

    def _save_question(self, inputs, popup, quiz_id):
        payload = {k: v.text.strip() for k, v in inputs.items() if v.text.strip()}
        payload["quiz_id"] = quiz_id
        payload.setdefault("question_type", "multiple_choice")
        payload.setdefault("points", 1)
        payload.setdefault("auto_grade", payload["question_type"] != "essay")
        try:
            payload["points"] = float(payload.get("points", 1))
            payload["negative_score"] = float(payload.get("negative_score", 0))
        except ValueError:
            self.message("سؤال", "بارم و نمره منفی باید عددی باشند.")
            return
        if not payload.get("question"):
            self.message("سؤال", "متن سؤال الزامی است.")
            return
        popup.dismiss()
        self._write_async("quiz_questions", payload, "سؤال با موفقیت ثبت شد.")

    def _toggle_exam(self, row):
        rid = row.get("id")
        if rid is None: return
        payload = {"published": not bool(row.get("published"))}
        self._update_async("teacher_exams", rid, payload, "وضعیت انتشار آزمون تغییر کرد.")

    def _online_editor(self):
        self._popup_form("ایجاد کلاس آنلاین", [
            ("title", "عنوان کلاس"), ("subject", "درس"), ("lesson", "مبحث/جلسه"), ("teacher", "نام دبیر"),
            ("grade", "پایه"), ("class_name", "کلاس"), ("duration", "مدت به دقیقه"),
            ("start_time_shamsi", "تاریخ و ساعت شروع"), ("end_time_shamsi", "تاریخ و ساعت پایان"), ("join_url", "لینک ورود"), ("meeting_url", "لینک جلسه"),
        ], self._save_online, (.96, .92))

    def _save_online(self, inputs, popup):
        payload = {k: v.text.strip() for k, v in inputs.items() if v.text.strip()}
        payload.setdefault("status", "active")
        try: payload["duration"] = int(payload.get("duration", 60))
        except ValueError:
            self.message("کلاس آنلاین", "مدت باید عددی باشد."); return
        if not payload.get("title") or not payload.get("class_name"):
            self.message("کلاس آنلاین", "عنوان کلاس و نام کلاس الزامی است."); return
        popup.dismiss(); self._write_async("online_classes", payload, "کلاس آنلاین با موفقیت ایجاد شد.")

    def _online_list(self):
        self.table = "online_classes"; self.body.clear_widgets()
        head = self._surface(dp(74)); head.add_widget(self.label("مدیریت کلاس‌های آنلاین", "17sp", PRIMARY, True, "center")); head.add_widget(self.btn("＋ ایجاد کلاس", lambda *_: self._online_editor(), SUCCESS, dp(38))); self.body.add_widget(head)
        area = BoxLayout(orientation="vertical"); self.body.add_widget(area); self._load_to(area, "online_classes", self._online_card)

    def _online_card(self, area, row):
        card = self._surface(dp(150))
        card.add_widget(self.label(str(row.get("title", "کلاس بدون عنوان")), "13sp", PRIMARY, True, "center"))
        card.add_widget(self.label("درس: " + str(row.get("subject", "—")) + "  •  کلاس: " + str(row.get("class_name", "—")) + "  •  دبیر: " + str(row.get("teacher", "—")), "9sp", SECONDARY, False, "center"))
        card.add_widget(self.label("شروع: " + str(row.get("start_time_shamsi", "—")) + "  •  پایان: " + str(row.get("end_time_shamsi", "—")), "9sp", SECONDARY, False, "center"))
        actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        active = str(row.get("status", "inactive")) == "active"
        actions.add_widget(self.btn("فعال‌سازی" if not active else "غیرفعال‌سازی", lambda *_a, r=dict(row): self._toggle_class(r), SUCCESS if not active else PRIMARY, dp(40)))
        actions.add_widget(self.btn("شروع جلسه", lambda *_a, rid=row.get("id"): self._start_session(rid), PRIMARY, dp(40)))
        actions.add_widget(self.btn("حذف", lambda *_a, rid=row.get("id"): self._delete_simple("online_classes", rid), (0.72,.16,.18,1), dp(40)))
        card.add_widget(actions); area.add_widget(card)

    def _toggle_class(self, row):
        self._update_async("online_classes", row.get("id"), {"status": "inactive" if row.get("status") == "active" else "active"}, "وضعیت کلاس تغییر کرد.")

    def _start_session(self, class_id):
        if not class_id: return
        self._write_async("online_class_sessions", {"class_id": class_id, "started_at": "now()"}, "جلسه آنلاین ثبت شد.")

    def _message_content(self, content):
        content.add_widget(self.btn("＋ ارسال پیام جدید", lambda *_: self._message_editor(), SUCCESS, dp(42)))
        content.add_widget(self.btn("صندوق ورودی", lambda *_: self._open_generic("messages"), PRIMARY, dp(42)))
        content.add_widget(self.label("مخاطب باید در فرم پیام مشخص شود؛ نقش، فرد یا کلاس مقصد بدون انتخاب مخاطب اجازه ارسال ندارد.", "9sp", SECONDARY, False, "center"))

    def _message_editor(self):
        self._popup_form("ارسال پیام مدرسه", [
            ("target_role", "نقش مخاطب: مدیر / معاون / دبیر / دانش‌آموز / ولی"),
            ("target_name", "نام فرد یا عنوان گروه مخاطب"), ("target_class_name", "کلاس مقصد (در صورت گروهی بودن)"),
            ("title", "عنوان پیام"), ("description", "متن پیام"),
        ], self._save_message, (.96, .9))

    def _save_message(self, inputs, popup):
        payload = {k: v.text.strip() for k, v in inputs.items() if v.text.strip()}
        if not payload.get("target_role") or not (payload.get("target_name") or payload.get("target_class_name")):
            self.message("ارسال پیام", "ابتدا نقش و فرد/گروه یا کلاس مقصد را مشخص کنید."); return
        if not payload.get("title") or not payload.get("description"):
            self.message("ارسال پیام", "عنوان و متن پیام الزامی است."); return
        popup.dismiss(); self._write_async("messages", payload, "پیام ثبت شد و مخاطب آن مشخص است.")

    def _payment_content(self, content, table):
        if table == "payment_offers":
            content.add_widget(self.btn("＋ تعریف کمک داوطلبانه", lambda *_: self._payment_editor(), SUCCESS, dp(42)))
            content.add_widget(self.label("مدیر مبلغ و مقصد پرداخت را تعریف می‌کند؛ مبلغ آزاد برای پرداخت‌کننده فعال نمی‌شود.", "9sp", SECONDARY, False, "center"))
        elif table in ("payment_records", "payment_attempts"):
            content.add_widget(self.btn("مشاهده سوابق پرداخت", lambda *_: self._open_generic(table), PRIMARY, dp(42)))
        else:
            content.add_widget(self.btn("مدیریت کمک‌های داوطلبانه", lambda *_: self._open_generic(table), PRIMARY, dp(42)))

    def _payment_editor(self):
        self._popup_form("تعریف کمک داوطلبانه", [("title", "عنوان"), ("description", "توضیحات"), ("amount", "مبلغ ثابت"), ("status", "وضعیت: active / inactive")], self._save_payment, (.94, .72))

    def _save_payment(self, inputs, popup):
        payload = {k: v.text.strip() for k, v in inputs.items() if v.text.strip()}
        if not payload.get("title") or not payload.get("amount"):
            self.message("کمک داوطلبانه", "عنوان و مبلغ ثابت الزامی است."); return
        try: payload["amount"] = float(payload["amount"])
        except ValueError: self.message("کمک داوطلبانه", "مبلغ باید عددی باشد."); return
        payload.setdefault("status", "active"); popup.dismiss(); self._write_async("payment_offers", payload, "کمک داوطلبانه با مبلغ ثابت ثبت شد.")

    def _open_generic(self, table):
        self.table = table
        self.body.clear_widgets()
        head = self._surface(dp(65)); head.add_widget(self.label(FRIENDLY.get(table, table), "16sp", PRIMARY, True, "center")); self.body.add_widget(head)
        area = BoxLayout(orientation="vertical"); self.body.add_widget(area); self._load_to(area, table, self._generic_card)

    def _generic_card(self, area, row):
        card = self._surface(dp(88))
        vals = [str(v) for k, v in row.items() if k not in ("id", "created_at", "updated_at")][:4]
        card.add_widget(self.label(" • ".join(vals), "9sp", SECONDARY, False, "right")); area.add_widget(card)

    def _load_to(self, area, table, renderer, filters=None):
        def work():
            try:
                query = {"limit": "150"}
                if filters: query.update(filters)
                rows = self.app_state.api.table_select(table, query) or []
                rows = rows if isinstance(rows, list) else []
                Clock.schedule_once(lambda *_: self._loaded_area(area, rows, renderer), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._area_error(area, str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _loaded_area(self, area, rows, renderer):
        area.clear_widgets()
        if not rows:
            area.add_widget(self.label("رکوردی ثبت نشده است.", "12sp", SECONDARY, True, "center")); return
        for row in rows: renderer(area, row)

    def _area_error(self, area, error):
        area.clear_widgets(); area.add_widget(self.label("خطا در دریافت اطلاعات: " + error, "9sp", SECONDARY, False, "center"))

    def _write_async(self, table, payload, success):
        self.status.text = rtl_text("در حال ذخیره اطلاعات واقعی…")
        def work():
            try:
                self.app_state.api.table_insert(table, payload)
                Clock.schedule_once(lambda *_: self._write_done(success), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._write_failed(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _update_async(self, table, rid, payload, success):
        if not rid: return
        def work():
            try:
                self.app_state.api.table_update(table, {"id": "eq." + str(rid)}, payload)
                Clock.schedule_once(lambda *_: self._write_done(success), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._write_failed(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _delete_simple(self, table, rid):
        if not rid: return
        def work():
            try:
                self.app_state.api.table_delete(table, {"id": "eq." + str(rid)})
                Clock.schedule_once(lambda *_: self._write_done("رکورد حذف شد."), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._write_failed(str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _write_done(self, text):
        self.status.text = rtl_text(text); self.status.color = SUCCESS

    def _write_failed(self, text):
        self.status.text = rtl_text("عملیات انجام نشد: " + text); self.status.color = (.8, .15, .15, 1)


ModuleScreen = ProfessionalWorkspaceScreen
