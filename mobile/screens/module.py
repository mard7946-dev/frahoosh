from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, CARD, BORDER
from mobile.ui import font_name, rtl_text, PersianTextInput

MODULE_TITLES = {
    "management": "مدیریت", "educational": "معاون آموزشی", "executive": "معاون اجرایی", "cultural": "معاون پرورشی", "advisor": "مشاوره",
    "teacher": "پنل دبیر", "teachers": "دبیران", "student": "پنل دانش‌آموز", "students": "دانش‌آموزان", "parent": "پنل اولیا", "parents": "اولیا",
    "finance": "مالی", "payment": "پرداخت آنلاین", "online": "کلاس‌های آنلاین", "smart_board": "تابلو هوشمند", "ai": "دستیار هوش مصنوعی",
    "messages": "صندوق پیام‌ها", "settings": "تنظیمات", "reports": "گزارش‌ها", "schedule": "برنامه هفتگی", "student_info": "وضعیت تحصیلی",
}

MODULE_TABLES = {
    "students": ["students", "student_records"], "student": ["students", "student_records"], "parents": ["parents", "parent_records"], "parent": ["parents", "parent_records"],
    "teachers": ["teachers", "staff"], "teacher": ["teachers", "staff"], "finance": ["payment_records", "financial_records"], "payment": ["payment_records"],
    "messages": ["messages", "message_records"], "online": ["online_classes", "classes"], "smart_board": ["smart_board", "smart_board_content"],
    "reports": ["reports", "report_cards"], "settings": ["account_settings", "school_settings"],
}


class ModuleScreen(Screen):
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.module_key = ""
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58), spacing=dp(8))
        self.back_button = Button(text=rtl_text("‹ داشبورد"), font_name=font_name(), font_size="14sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(100))
        self.back_button.bind(on_release=self.go_back)
        self.title_label = Label(text=rtl_text(APP_NAME), font_name=font_name(), font_size="22sp", bold=True, color=PRIMARY, halign="right", valign="middle")
        self.title_label.bind(size=self._sync_text_size)
        header.add_widget(self.back_button); header.add_widget(self.title_label); root.add_widget(header)
        self.status_label = Label(text="", font_name=font_name(), font_size="12sp", color=SECONDARY, halign="right", valign="middle", size_hint_y=None, height=dp(42))
        self.status_label.bind(size=self._sync_text_size); root.add_widget(self.status_label)
        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(10), size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root)

    def _sync_text_size(self, instance, value):
        instance.text_size = value

    def set_module(self, key): self.show_module(key)
    def load_module(self, key): self.show_module(key)

    def show_module(self, key):
        self.module_key = str(key or "").strip().lower()
        title = MODULE_TITLES.get(self.module_key, self.module_key or APP_NAME)
        self.title_label.text = rtl_text(title); self.body.clear_widgets(); self.status_label.text = rtl_text("در حال آماده‌سازی بخش...")
        self._build_module(self.module_key, title)

    def _build_module(self, key, title):
        builders = {"management": self._management, "educational": self._educational, "executive": self._executive, "cultural": self._cultural, "advisor": self._advisor,
                    "teacher": self._teacher, "teachers": self._teachers, "student": self._student, "students": self._students, "parent": self._parent, "parents": self._parents,
                    "finance": self._finance, "payment": self._payment, "online": self._online, "smart_board": self._smart_board, "ai": self._ai, "messages": self._messages,
                    "settings": self._settings, "reports": self._reports, "schedule": self._schedule, "student_info": self._student_info}
        builder = builders.get(key)
        if builder is None: self._generic(title); return
        try: builder()
        except Exception as exc: print("MODULE BUILD ERROR:", repr(exc)); self._error("خطا در آماده‌سازی این بخش.")

    def _add_title(self, text):
        label = Label(text=rtl_text(text), font_name=font_name(), font_size="20sp", bold=True, color=PRIMARY, halign="right", valign="middle", size_hint_y=None, height=dp(52))
        label.bind(size=self._sync_text_size); self.body.add_widget(label)

    def _add_info(self, text, height=90):
        label = Label(text=rtl_text(text), font_name=font_name(), font_size="14sp", color=SECONDARY, halign="right", valign="top", size_hint_y=None, height=dp(height))
        label.bind(size=self._sync_text_size); self.body.add_widget(label); return label

    def _button(self, text, callback, color=PRIMARY):
        button = Button(text=rtl_text(text), font_name=font_name(), font_size="15sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=dp(50))
        button.bind(on_release=callback); self.body.add_widget(button); return button

    def _error(self, text): self.status_label.text = rtl_text(text); self.status_label.color = ERROR
    def _success(self, text): self.status_label.text = rtl_text(text); self.status_label.color = SUCCESS

    def _generic(self, title):
        self._add_title(title); self._add_info("این بخش در نسخه موبایل فراهوش فعال است.\nاطلاعات از سامانه مرکزی دریافت می‌شود.", 100)
        self._button("بازخوانی اطلاعات", lambda *_: self.show_module(self.module_key), SUCCESS); self.status_label.text = rtl_text("بخش آماده استفاده است.")

    def _management(self):
        self._add_title("مدیریت مدرسه"); self._add_info(f"مدیریت مرکزی سامانه فراهوش\nمدرسه: {SCHOOL_NAME}\nسال تحصیلی: {SCHOOL_YEAR}", 120)
        self._button("مدیریت دانش‌آموزان", lambda *_: self.show_module("students")); self._button("مدیریت دبیران", lambda *_: self.show_module("teachers")); self._button("مدیریت مالی", lambda *_: self.show_module("finance")); self._button("تنظیمات سامانه", lambda *_: self.show_module("settings")); self.status_label.text = rtl_text("پنل مدیریت آماده است.")

    def _educational(self):
        self._add_title("معاون آموزشی"); self._add_info("مدیریت امور آموزشی، دبیران، کلاس‌ها، برنامه هفتگی و گزارش‌های آموزشی.")
        self._button("دانش‌آموزان", lambda *_: self.show_module("students")); self._button("دبیران", lambda *_: self.show_module("teachers")); self._button("کلاس‌های آنلاین", lambda *_: self.show_module("online")); self._button("گزارش‌ها", lambda *_: self.show_module("reports"))

    def _executive(self):
        self._add_title("معاون اجرایی"); self._add_info("مدیریت اجرایی مدرسه و اطلاعات ثبت‌نامی.")
        self._button("دانش‌آموزان", lambda *_: self.show_module("students")); self._button("اولیا", lambda *_: self.show_module("parents")); self._button("تنظیمات حساب‌ها", lambda *_: self.show_module("settings"))

    def _cultural(self):
        self._add_title("معاون پرورشی"); self._add_info("مدیریت فعالیت‌های پرورشی، تابلو هوشمند و ارتباط با دانش‌آموزان.")
        self._button("تابلو هوشمند", lambda *_: self.show_module("smart_board")); self._button("دانش‌آموزان", lambda *_: self.show_module("students"))

    def _advisor(self):
        self._add_title("مشاوره"); self._add_info("دسترسی به اطلاعات موردنیاز مشاوره و ارتباط با دانش‌آموزان و اولیا.")
        self._button("دانش‌آموزان", lambda *_: self.show_module("students")); self._button("اولیا", lambda *_: self.show_module("parents"))

    def _teacher(self):
        self._add_title("پنل دبیر"); self._add_info("مدیریت کلاس‌ها، دانش‌آموزان، کلاس آنلاین و محتوای آموزشی.")
        self._button("دانش‌آموزان", lambda *_: self.show_module("students")); self._button("کلاس‌های آنلاین", lambda *_: self.show_module("online")); self._button("تابلو هوشمند", lambda *_: self.show_module("smart_board"))

    def _teachers(self): self._add_title("دبیران"); self._add_info("فهرست دبیران و کارکنان آموزشی مدرسه."); self._load_table(MODULE_TABLES["teachers"])

    def _student(self):
        self._add_title("پنل دانش‌آموز"); self._add_info("دسترسی سریع به برنامه هفتگی، وضعیت تحصیلی، پرداخت و کلاس‌های آنلاین.")
        self._button("برنامه هفتگی", lambda *_: self.show_module("schedule")); self._button("وضعیت تحصیلی", lambda *_: self.show_module("student_info")); self._button("پرداخت آنلاین", lambda *_: self.show_module("payment"), SUCCESS); self._button("کلاس‌های آنلاین", lambda *_: self.show_module("online"))

    def _students(self): self._add_title("دانش‌آموزان"); self._add_info("فهرست دانش‌آموزان ثبت‌شده در سامانه."); self._load_table(MODULE_TABLES["students"])

    def _parent(self):
        self._add_title("پنل اولیا"); self._add_info("مشاهده وضعیت فرزند، کلاس‌های آنلاین و پرداخت‌های مدرسه.")
        self._button("وضعیت تحصیلی فرزند", lambda *_: self.show_module("student_info")); self._button("پرداخت آنلاین", lambda *_: self.show_module("payment"), SUCCESS); self._button("کلاس‌های آنلاین", lambda *_: self.show_module("online"))

    def _parents(self): self._add_title("اولیا"); self._add_info("فهرست و اطلاعات اولیای ثبت‌شده."); self._load_table(MODULE_TABLES["parents"])

    def _finance(self):
        self._add_title("مدیریت مالی"); self._add_info("ثبت و مشاهده سوابق پرداخت، مبلغ، علت پرداخت و وضعیت پرداخت.")
        self._button("سوابق پرداخت", lambda *_: self._load_table(["payment_records"])); self._button("تنظیمات پرداخت آنلاین", lambda *_: self._payment())

    def _payment(self):
        self._add_title("پرداخت آنلاین"); self._add_info("پرداخت‌های فعال مدرسه از این بخش نمایش داده می‌شوند."); self._load_table(["payment_records"], payment_mode=True)

    def _online(self):
        self._add_title("کلاس‌های آنلاین"); self._add_info("کلاس‌های فعال آنلاین و لینک ورود در این بخش نمایش داده می‌شوند."); self._load_table(MODULE_TABLES["online"])

    def _smart_board(self):
        self._add_title("تابلو هوشمند"); self._add_info("محتوای آموزشی، فایل‌ها، تصاویر، ویدئوها و آزمون‌های کوتاه."); self._load_table(MODULE_TABLES["smart_board"])

    def _ai(self):
        self._add_title("دستیار هوش مصنوعی"); self._add_info("ابزارهای هوشمند فراهوش")
        for title in ("دستیار هوشمند", "تحلیل آموزشی", "گزارش هوشمند", "پرسش و پاسخ"): self._button(title, self._ai_action)

    def _ai_action(self, button): self.status_label.text = rtl_text("درخواست شما برای دستیار هوشمند ثبت شد."); self.status_label.color = SUCCESS

    def _messages(self): self._add_title("صندوق پیام‌ها"); self._add_info("پیام‌های مدرسه و ارتباطات سامانه."); self._load_table(MODULE_TABLES["messages"])

    def _settings(self):
        self._add_title("تنظیمات"); profile = {}
        try: profile = self.app_state.profile or {}
        except Exception: pass
        name = profile.get("display_name") or profile.get("full_name") or "کاربر"; national_code = profile.get("national_code") or "ثبت نشده"
        self._add_info(f"نام: {name}\nکد ملی: {national_code}\nنقش: {self.app_state.role}", 120); self._button("بازخوانی حساب", lambda *_: self.show_module("settings"), SUCCESS)

    def _reports(self): self._add_title("گزارش‌ها"); self._add_info("گزارش‌های آموزشی و مدیریتی سامانه."); self._load_table(MODULE_TABLES["reports"])

    def _schedule(self): self._add_title("برنامه هفتگی"); self._add_info("برنامه هفتگی دانش‌آموز از سامانه مرکزی دریافت می‌شود."); self._load_table(["weekly_schedule", "schedules", "class_schedule"])

    def _student_info(self): self._add_title("وضعیت تحصیلی"); self._add_info("نمرات، وضعیت درسی و اطلاعات آموزشی دانش‌آموز."); self._load_table(["student_grades", "grades", "report_cards"])

    def _load_table(self, tables, payment_mode=False):
        if not isinstance(tables, list): tables = [tables]
        if self.app_state is None or self.app_state.api is None: self._error("اتصال به سامانه مرکزی آماده نیست."); return
        if not self.app_state.api.configured: self._error("تنظیمات اتصال سامانه مرکزی در این نسخه کامل نشده است."); return
        if not self.app_state.api.access_token: self._error("نشست کاربر معتبر نیست."); return
        loading = Label(text=rtl_text("در حال دریافت اطلاعات..."), font_name=font_name(), font_size="14sp", color=SECONDARY, size_hint_y=None, height=dp(55)); self.body.add_widget(loading)
        Thread(target=self._fetch_tables, args=(tables, payment_mode), daemon=True).start()

    def _fetch_tables(self, tables, payment_mode):
        result = None; used_table = None; last_error = None
        for table in tables:
            try:
                rows = self.app_state.api.table_select(table, {"select": "*", "limit": "50"})
                if isinstance(rows, list): result = rows; used_table = table; break
            except Exception as exc: last_error = exc
        Clock.schedule_once(lambda dt: self._render_rows(result, used_table, last_error, payment_mode), 0)

    def _render_rows(self, rows, table, error, payment_mode):
        self.body.clear_widgets()
        if rows is None:
            self._error("اطلاعات این بخش هنوز در سامانه مرکزی در دسترس نیست.")
            self._add_info("برای نمایش اطلاعات واقعی، جدول مربوطه باید در سامانه مرکزی وجود داشته باشد و نشست کاربر دسترسی لازم را داشته باشد.", 125); return
        if not rows:
            self._success("اطلاعاتی برای نمایش وجود ندارد."); self._add_info("در حال حاضر رکوردی ثبت نشده است.", 80); return
        self._success(f"{len(rows)} رکورد از سامانه مرکزی دریافت شد.")
        for index, row in enumerate(rows, 1): self._add_info(self._format_row(row, payment_mode, index), 105)

    def _format_row(self, row, payment_mode, index):
        if not isinstance(row, dict): return f"رکورد {index}: {row}"
        priority = ["title", "name", "full_name", "student_name", "subject", "course_name", "amount", "reason", "status", "date", "created_at"]
        parts = [f"{key}: {row.get(key)}" for key in priority if row.get(key) not in (None, "", [])]
        if not parts: parts = [f"{k}: {v}" for k, v in list(row.items())[:6]]
        return f"{index}. " + " | ".join(parts)

    def go_back(self, *_):
        if self.manager: self.manager.current = "live_panel" if self.manager.has_screen("live_panel") else "dashboard"
