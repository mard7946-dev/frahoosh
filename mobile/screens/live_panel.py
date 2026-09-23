from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text, fa_display
from mobile.services.live_data import LiveSchoolData

TITLES = {
    "management": "مدیریت مدرسه", "educational": "معاون آموزشی", "executive": "معاون اجرایی", "cultural": "معاون پرورشی", "advisor": "مشاوره",
    "teacher": "پنل دبیر", "teachers": "دبیران", "student": "پنل دانش‌آموز", "students": "دانش‌آموزان", "parent": "پنل اولیا", "parents": "اولیا",
    "finance": "مالی", "payment": "پرداخت آنلاین", "online": "کلاس‌های آنلاین", "smart_board": "تابلو هوشمند", "ai": "دستیار هوش مصنوعی",
    "messages": "صندوق پیام‌ها", "reports": "گزارش‌های مدرسه", "schedule": "برنامه هفتگی", "student_info": "وضعیت تحصیلی", "settings": "تنظیمات",
}

# Role-specific operational catalogue. Every item leads either to another live
# panel or to a data-backed module view; there are no dead print-only buttons.
SUBMENUS = {
    "management": [("داشبورد مدیریتی و آمار", "detail:reports"), ("مدیریت دانش‌آموزان", "panel:students"), ("مدیریت دبیران و کارکنان", "panel:teachers"), ("مدیریت اولیا", "panel:parents"), ("معاون آموزشی", "panel:educational"), ("معاون اجرایی", "panel:executive"), ("معاون پرورشی", "panel:cultural"), ("مشاوره", "panel:advisor"), ("امور مالی", "panel:finance"), ("پرداخت آنلاین", "panel:payment"), ("کلاس‌های آنلاین", "panel:online"), ("تابلو هوشمند", "panel:smart_board"), ("دستیار هوش مصنوعی", "panel:ai"), ("صندوق پیام‌ها", "panel:messages"), ("گزارش‌های مدیریتی", "panel:reports"), ("تنظیمات سامانه", "panel:settings")],
    "educational": [("مدیریت کلاس‌ها و دروس", "detail:online"), ("برنامه هفتگی", "detail:schedule"), ("دانش‌آموزان", "panel:students"), ("دبیران", "panel:teachers"), ("حضور و غیاب آموزشی", "detail:attendance"), ("نمرات و ارزشیابی", "detail:grades"), ("تکالیف و فعالیت‌های درسی", "detail:homework"), ("آزمون‌ها و امتحانات", "detail:exams"), ("کلاس‌های آنلاین", "panel:online"), ("گزارش‌های آموزشی", "panel:reports"), ("پیام‌رسانی آموزشی", "panel:messages")],
    "executive": [("پرونده و ثبت‌نام دانش‌آموزان", "panel:students"), ("اطلاعات و پرونده اولیا", "panel:parents"), ("کلاس‌ها و پایه‌ها", "detail:schedule"), ("حضور و غیاب", "detail:attendance"), ("رویدادها و امور اجرایی", "detail:events"), ("گزارش‌های اجرایی", "panel:reports"), ("صندوق پیام‌ها", "panel:messages"), ("تنظیمات حساب‌ها", "panel:settings")],
    "cultural": [("فعالیت‌های فرهنگی و پرورشی", "detail:cultural_activity"), ("پرونده فعالیت دانش‌آموزان", "panel:students"), ("رویدادها و مناسبت‌ها", "detail:events"), ("ارتباط با اولیا", "panel:parents"), ("تابلو هوشمند", "panel:smart_board"), ("گزارش‌های پرورشی", "panel:reports"), ("پیام‌ها", "panel:messages")],
    "advisor": [("پرونده دانش‌آموزان", "panel:students"), ("جلسات مشاوره", "detail:counseling"), ("پیگیری وضعیت دانش‌آموز", "detail:student_info"), ("ارتباط با اولیا", "panel:parents"), ("گزارش مشاوره", "panel:reports"), ("پیام‌ها", "panel:messages")],
    "teacher": [("کلاس‌های من", "detail:my_classes"), ("دانش‌آموزان کلاس", "panel:students"), ("حضور و غیاب", "detail:attendance"), ("ثبت و مشاهده نمرات", "detail:grades"), ("تکالیف", "detail:homework"), ("آزمون‌ها و امتحانات", "detail:exams"), ("کلاس آنلاین", "panel:online"), ("تابلو و ابزار تدریس", "panel:smart_board"), ("پیام‌ها و ارتباط با اولیا", "panel:messages")],
    "teachers": [("فهرست دبیران", "panel:teachers"), ("کلاس‌ها و دروس", "detail:my_classes"), ("برنامه هفتگی دبیران", "detail:schedule"), ("گزارش عملکرد آموزشی", "panel:reports"), ("کلاس‌های آنلاین", "panel:online"), ("پیام‌ها", "panel:messages")],
    "student": [("کلاس‌های من", "detail:my_classes"), ("برنامه هفتگی", "detail:schedule"), ("نمرات و کارنامه", "detail:student_info"), ("تکالیف و فعالیت‌ها", "detail:homework"), ("حضور و غیاب", "detail:attendance"), ("کلاس آنلاین", "panel:online"), ("تابلو هوشمند", "panel:smart_board"), ("پرداخت آنلاین", "panel:payment"), ("صندوق پیام‌ها", "panel:messages")],
    "students": [("فهرست دانش‌آموزان", "panel:students"), ("پرونده تحصیلی", "detail:student_info"), ("حضور و غیاب", "detail:attendance"), ("نمرات و کارنامه", "detail:grades"), ("تکالیف", "detail:homework"), ("کلاس‌ها و برنامه هفتگی", "detail:schedule"), ("گزارش دانش‌آموزان", "panel:reports")],
    "parent": [("فرزند من", "detail:children"), ("وضعیت تحصیلی فرزند", "detail:student_info"), ("حضور و غیاب فرزند", "detail:attendance"), ("نمرات و کارنامه", "detail:grades"), ("تکالیف و فعالیت‌ها", "detail:homework"), ("کلاس‌های آنلاین", "panel:online"), ("پرداخت آنلاین", "panel:payment"), ("پیام‌های مدرسه", "panel:messages"), ("گزارش‌ها", "panel:reports")],
    "parents": [("فهرست اولیا", "panel:parents"), ("فرزندان", "detail:children"), ("حضور و غیاب", "detail:attendance"), ("نمرات و کارنامه", "detail:grades"), ("پرداخت‌ها", "panel:payment"), ("کلاس‌های آنلاین", "panel:online"), ("پیام‌ها", "panel:messages")],
    "finance": [("داشبورد مالی", "detail:finance"), ("کمک‌های داوطلبانه و دریافت‌ها", "detail:payment_records"), ("سوابق پرداخت", "detail:payment_records"), ("تراکنش‌های آنلاین", "detail:payment_records"), ("گزارش مالی", "detail:reports"), ("تنظیمات پرداخت", "detail:payment")],
    "payment": [("گزینه‌های پرداخت", "detail:payment"), ("سوابق تراکنش‌ها", "detail:payment_records"), ("رسیدهای پرداخت", "detail:payment_records"), ("وضعیت پرداخت", "detail:payment_records")],
    "online": [("کلاس‌های فعال", "detail:online"), ("جلسات کلاس", "detail:online_sessions"), ("حضور و غیاب", "detail:attendance"), ("ورود و خروج دانش‌آموزان", "detail:online_activity"), ("گفت‌وگوی کلاس", "detail:online_chat"), ("تابلو و ابزار تدریس", "panel:smart_board"), ("گزارش جلسات", "panel:reports")],
    "smart_board": [("تابلو کلاس", "detail:smart_board"), ("محتوای آموزشی", "detail:smart_board"), ("ابزارهای تعاملی", "detail:smart_board_tools"), ("آزمون کوتاه", "detail:exams")],
    "ai": [("دستیار هوشمند", "detail:ai"), ("تحلیل آموزشی", "detail:ai"), ("تحلیل وضعیت دانش‌آموز", "detail:ai"), ("گزارش هوشمند", "detail:ai")],
    "messages": [("صندوق ورودی", "detail:messages"), ("پیام‌های مدرسه", "detail:messages"), ("پیام به دانش‌آموز", "detail:messages"), ("پیام به اولیا", "detail:messages"), ("پیام‌های خوانده‌نشده", "detail:messages")],
    "reports": [("گزارش مدیریتی", "detail:reports"), ("گزارش آموزشی", "detail:reports"), ("گزارش حضور و غیاب", "detail:attendance"), ("گزارش نمرات", "detail:grades"), ("گزارش تکالیف", "detail:homework"), ("گزارش مالی", "detail:finance")],
    "schedule": [("برنامه هفتگی", "detail:schedule"), ("برنامه کلاس‌ها", "detail:schedule"), ("برنامه دبیران", "detail:schedule"), ("جلسات آنلاین", "panel:online")],
    "student_info": [("مشخصات دانش‌آموز", "detail:student_info"), ("کارنامه و نمرات", "detail:grades"), ("حضور و غیاب", "detail:attendance"), ("تکالیف", "detail:homework"), ("کلاس آنلاین", "panel:online")],
    "settings": [("حساب کاربری", "detail:settings"), ("اطلاعات مدرسه", "detail:settings"), ("سال تحصیلی", "detail:settings"), ("اعلان‌ها", "detail:settings"), ("دسترسی‌ها و نقش‌ها", "detail:settings")],
}

DETAIL_TO_MODULE = {
    "reports": "reports", "online": "online", "online_sessions": "online", "attendance": "students", "grades": "student_info", "homework": "student_info", "exams": "reports", "events": "reports", "cultural_activity": "cultural", "counseling": "advisor", "student_info": "student_info", "my_classes": "online", "children": "students", "finance": "finance", "payment": "payment", "payment_records": "payment", "online_activity": "online", "online_chat": "online", "smart_board": "smart_board", "smart_board_tools": "smart_board", "ai": "ai", "messages": "messages", "settings": "settings", "schedule": "schedule",
}
ROLE_ALIASES = {"admin":"manager", "administrator":"manager", "manager":"manager", "مدیر":"manager", "مدیریت":"manager", "executive":"executive", "معاون اجرایی":"executive", "educational":"educational", "training":"educational", "معاون آموزشی":"educational", "cultural":"cultural", "پرورشی":"cultural", "معاون پرورشی":"cultural", "advisor":"advisor", "counselor":"advisor", "مشاور":"advisor", "teacher":"teacher", "teacher_staff":"teacher", "دبیر":"teacher", "معلم":"teacher", "student":"student", "دانش‌آموز":"student", "دانش آموز":"student", "parent":"parent", "parent_guardian":"parent", "guardian":"parent", "ولی":"parent", "اولیا":"parent"}
ROLE_LABELS = {"manager":"مدیریت", "educational":"معاون آموزشی", "executive":"معاون اجرایی", "cultural":"معاون پرورشی", "advisor":"مشاوره", "teacher":"دبیر", "student":"دانش‌آموز", "parent":"ولی"}

class LivePanelScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.data = LiveSchoolData(app_state)
        self.route = "messages"
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(9))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(54), spacing=dp(8))
        back = Button(text=fa_display("‹ داشبورد"), font_name=font_name(), font_size="14sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(100))
        back.bind(on_release=lambda *_: self._back())
        header.add_widget(back)
        self.title = Label(text=rtl_text(APP_NAME), font_name=font_name(), font_size="21sp", bold=True, color=PRIMARY, halign="right", valign="middle")
        self.title.bind(size=lambda obj, value: setattr(obj, "text_size", value)); header.add_widget(self.title); root.add_widget(header)
        self.status = Label(text="", font_name=font_name(), font_size="12sp", color=SECONDARY, halign="right", valign="middle", size_hint_y=None, height=dp(42))
        self.status.bind(size=lambda obj, value: setattr(obj, "text_size", value)); root.add_widget(self.status)
        scroll = ScrollView(do_scroll_x=False); self.body = BoxLayout(orientation="vertical", padding=dp(4), spacing=dp(9), size_hint_y=None); self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root)

    def set_panel(self, route):
        self.route = str(route or "messages").strip().lower()
        role = self._role(); self.title.text = rtl_text(TITLES.get(self.route, APP_NAME)); self.body.clear_widgets(); self.status.color = SUCCESS; self.status.text = rtl_text(f"پنل {TITLES.get(self.route, APP_NAME)} برای {ROLE_LABELS.get(role, 'کاربر')}")
        self._add_card("دسترسی سریع", "تمام زیرمجموعه‌های این پنل در دسترس هستند. اطلاعات هر بخش از داده‌های واقعی حساب شما خوانده می‌شود.")
        self._add_button("نمایش اطلاعات و آمار واقعی", lambda *_: self._show_live_summary(), SUCCESS)
        for title, target in SUBMENUS.get(self.route, []): self._add_button(title, lambda *_ , t=target: self._open_target(t), PRIMARY)
        self._add_button("↻ تازه‌سازی اطلاعات", lambda *_: self.set_panel(self.route), SECONDARY)

    def _show_live_summary(self):
        self.body.clear_widgets(); self._add_card("خلاصه زنده سامانه", "در حال دریافت آمار واقعی مدرسه…")
        Thread(target=self._fetch_counts, daemon=True).start()

    def _fetch_counts(self):
        try:
            counts = self.data.dashboard_counts()
        except Exception as exc:
            counts = {"خطا": str(exc)}
        Clock.schedule_once(lambda *_: self._render_counts(counts), 0)

    def _render_counts(self, counts):
        self.body.clear_widgets(); self._add_card("خلاصه زنده سامانه", "این اعداد از پایگاه داده مدرسه خوانده شده‌اند؛ داده ساختگی در آن‌ها استفاده نشده است.")
        if "خطا" in counts:
            self._add_card("وضعیت", "اطلاعات خلاصه در حال حاضر از سرور قابل دریافت نیست؛ سایر زیرپنل‌ها همچنان قابل انتخاب هستند.")
        else:
            for name, value in counts.items():
                self._add_card(name, "دریافت نشد" if value is None else f"{value} رکورد")
        self._add_button("‹ بازگشت به پنل", lambda *_: self.set_panel(self.route), PRIMARY)

    def _role(self):
        raw = str(getattr(self.app_state, "role", "student") or "student").strip().lower(); return ROLE_ALIASES.get(raw, raw)

    def _open_target(self, target):
        if not self.manager: return
        try:
            if target.startswith("panel:"):
                self.set_panel(target.split(":", 1)[1]); return
            if target.startswith("detail:"):
                key = target.split(":", 1)[1]; module_key = DETAIL_TO_MODULE.get(key, key)
                if not self.manager.has_screen("module"):
                    from mobile.screens.module import ModuleScreen
                    self.manager.add_widget(ModuleScreen(name="module", app_state=self.app_state))
                module = self.manager.get_screen("module"); module.set_module(module_key, return_to="live_panel"); self.manager.current = "module"
        except Exception as exc:
            print("LIVE PANEL NAV ERROR:", repr(exc)); self.status.color = ERROR; self.status.text = rtl_text("باز کردن زیرپنل انجام نشد.")

    def _add_card(self, title, text):
        box = BoxLayout(orientation="vertical", padding=[dp(12), dp(10)], spacing=dp(4), size_hint_y=None, height=dp(82))
        head = Label(text=rtl_text(title), font_name=font_name(), font_size="16sp", bold=True, color=PRIMARY, halign="right", valign="middle", size_hint_y=None, height=dp(30)); head.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        body = Label(text=rtl_text(str(text)), font_name=font_name(), font_size="13sp", color=SECONDARY, halign="right", valign="top"); body.bind(size=lambda obj, value: setattr(obj, "text_size", value)); box.add_widget(head); box.add_widget(body); self.body.add_widget(box)

    def _add_button(self, text, callback, color=PRIMARY):
        button = Button(text=rtl_text(text), font_name=font_name(), font_size="14sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=dp(48)); button.bind(on_release=callback); self.body.add_widget(button)

    def _back(self):
        if self.manager: self.manager.current = "dashboard"
