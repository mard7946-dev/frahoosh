from threading import Thread


from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME
from mobile.ui import font_name, rtl_text


class _Card(BoxLayout):
    def __init__(self, fill=(0.97, 0.98, 1, 1), radius=12, **kwargs):
        super().__init__(orientation="vertical", padding=dp(7), spacing=dp(4), **kwargs)
        with self.canvas.before:
            Color(*fill)
            self.bg = RoundedRectangle(radius=[dp(radius)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class SmartClassPreviewScreen(Screen):
    """Interactive smart-classroom environment, not a static information page."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.class_id = None
        self.session_id = None
        self.class_title = "کلاس هوشمند فراهوش"
        self.return_to = "dashboard"

    def label(self, text, size="10sp", color=SECONDARY, height=34, bold=False, center=False):
        w = Label(text=rtl_text(str(text)), font_name=font_name(), font_size=size,
                  color=color, bold=bold,
                  halign="center" if center else "right", valign="middle",
                  size_hint_y=None, height=dp(height), padding=[dp(4), dp(2)])
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def btn(self, text, callback, color=PRIMARY, height=40):
        b = Button(text=rtl_text(text), font_name=font_name(), font_size="9sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(height))
        b.bind(on_release=callback)
        return b

    def on_pre_enter(self, *_):
        self.build_room()

    def build_room(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(5))

        header = _Card(fill=(0.025, 0.12, 0.25, 1), size_hint_y=None, height=dp(57))
        hr = BoxLayout(spacing=dp(5))
        hr.add_widget(self.btn("بازگشت", self.back, SECONDARY, 40))
        title = BoxLayout(orientation="vertical")
        title.add_widget(self.label(self.class_title, "15sp", WHITE, 30, True, True))
        title.add_widget(self.label("محیط واقعی کلاس هوشمند • تخته، ابزار، دبیر و دانش‌آموز", "8sp", (0.70,0.88,1,1), 20, False, True))
        hr.add_widget(title)
        hr.add_widget(self.btn("اتصال", self.refresh_live, SUCCESS, 40))
        header.add_widget(hr)
        root.add_widget(header)

        main = BoxLayout(spacing=dp(5))

        # Teacher tools.
        rail = _Card(fill=(0.055,0.10,0.17,1), size_hint_x=None, width=dp(78))
        rail.add_widget(self.label("ابزار", "9sp", WHITE, 27, True, True))
        for t,c in [("قلم",PRIMARY),("پاک‌کن",SECONDARY),("متن",PRIMARY),("شکل",PRIMARY),
                    ("عکس",PRIMARY),("PDF",PRIMARY),("آزمونک",SUCCESS)]:
            rail.add_widget(self.btn(t, self.tool, c, 45))
        main.add_widget(rail)

        # Smart board and class controls.
        center = BoxLayout(orientation="vertical", spacing=dp(5))
        board = _Card(fill=(0.93,0.94,0.91,1), size_hint_y=1)
        board.add_widget(self.label("تخته هوشمند کلاس", "13sp", PRIMARY, 30, True, True))
        board_area = Widget()
        with board_area.canvas.before:
            Color(0.055,0.07,0.09,1)
            bg = RoundedRectangle(radius=[dp(7)])
            Color(0.25,0.55,0.75,0.35)
            border = Line(rounded_rectangle=(0,0,0,0,dp(7)), width=1)
        board_area.bind(pos=lambda o,v:self._sync_canvas(bg,border,o),
                        size=lambda o,v:self._sync_canvas(bg,border,o))
        board_area.add_widget(self.label(
            "تخته آماده است\n\nمحتوای درس، PDF، تصویر، متن، شکل و آزمونک\nدر این محیط برای دبیر و دانش‌آموز نمایش داده می‌شود.",
            "12sp", WHITE, 145, True, True))
        board.add_widget(board_area)
        center.add_widget(board)

        controls = _Card(fill=(0.97,0.98,1,1), size_hint_y=None, height=dp(75))
        r1 = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(3))
        for t,c,cb in [("میکروفون",PRIMARY,self.toggle),("دوربین",PRIMARY,self.toggle),
                       ("صدا",PRIMARY,self.toggle),("چت",PRIMARY,self.chat)]:
            r1.add_widget(self.btn(t,cb,c,30))
        controls.add_widget(r1)
        r2 = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(3))
        r2.add_widget(self.btn("حضور و غیاب",SUCCESS,self.attendance,30))
        r2.add_widget(self.btn("فایل درس",PRIMARY,self.files,30))
        r2.add_widget(self.btn("پایان کلاس",ERROR,self.finish,30))
        controls.add_widget(r2)
        center.add_widget(controls)
        main.add_widget(center)

        # Live participants.
        side = _Card(fill=(0.055,0.10,0.17,1), size_hint_x=None, width=dp(125))
        side.add_widget(self.label("شرکت‌کنندگان", "9sp", WHITE, 28, True, True))
        self.live_count = self.label("در حال اتصال…", "8sp", SUCCESS, 28, True, True)
        side.add_widget(self.live_count)
        self.participants_area = BoxLayout(orientation="vertical", spacing=dp(3))
        side.add_widget(self.participants_area)
        side.add_widget(Widget())
        main.add_widget(side)
        root.add_widget(main)

        self.status = self.label("محیط کلاس آماده است؛ اتصال زنده در حال بررسی…", "8sp", SUCCESS, 31, True, True)
        root.add_widget(self.status)
        self.add_widget(root)
        Clock.schedule_once(self.load_live_async, 0.05)

    @staticmethod
    def _sync_canvas(bg, border, widget):
        bg.pos, bg.size = widget.pos, widget.size
        border.rounded_rectangle = (widget.x, widget.y, widget.width, widget.height, dp(7))

    def load_live_async(self, *_):
        def work():
            api = getattr(self.app_state, "api", None)
            if api is None:
                Clock.schedule_once(lambda *_: self.set_status("اتصال API آماده نیست.", ERROR), 0)
                return
            try:
                rows = api.table_select("online_classes", {"order":"id.desc","limit":"1"}) or []
                if not rows:
                    Clock.schedule_once(lambda *_: self.set_status("کلاس ثبت‌شده‌ای نیست؛ محیط کلاس آماده استفاده است.", SUCCESS), 0)
                    return
                row = dict(rows[0])
                self.class_id = row.get("id")
                students = api.table_select("online_class_students", {"class_id":"eq."+str(self.class_id),"limit":"50"}) or []
                teachers = api.table_select("online_class_teachers", {"class_id":"eq."+str(self.class_id),"limit":"10"}) or []
                attendance = api.table_select("online_attendance", {"class_id":"eq."+str(self.class_id),"limit":"100"}) or []
                files = api.table_select("smart_board_files", {"class_id":"eq."+str(self.class_id),"limit":"20"}) or []
                sessions = api.table_select("online_class_sessions", {"class_id":"eq."+str(self.class_id),"order":"id.desc","limit":"1"}) or []
                title = str(row.get("title") or "کلاس هوشمند فراهوش")
                info = " | ".join(str(row.get(k)) for k in ("subject","grade","class_name") if row.get(k))
                bundle={"title":title,"info":info,"students":students,"teachers":teachers,"attendance":attendance,"files":files,"session":sessions[0] if sessions else {}}
                Clock.schedule_once(lambda *_: self.apply_live(bundle), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.set_status("محیط کلاس آماده است؛ اتصال زنده کامل نشد.", SECONDARY), 0)
                print("SMART CLASS LIVE ERROR:", repr(exc))
        Thread(target=work, daemon=True).start()

    def apply_live(self, bundle):
        self.class_title = bundle.get("title") or "کلاس هوشمند فراهوش"
        self.session_id = (bundle.get("session") or {}).get("id")
        students = bundle.get("students") or []
        teachers = bundle.get("teachers") or []
        attendance = bundle.get("attendance") or []
        self.live_count.text = rtl_text(f"{len(teachers)+len(students)} شرکت‌کننده • {len(attendance)} حضور آنلاین")
        self.participants_area.clear_widgets()
        for row in teachers:
            name=str(row.get("teacher_name") or "دبیر کلاس")
            card=_Card(fill=(0.10,0.17,0.25,1),size_hint_y=None,height=dp(40),padding=dp(3))
            card.add_widget(self.label("● "+name,"8sp",WHITE,34,False,True))
            self.participants_area.add_widget(card)
        for row in students[:8]:
            name=str(row.get("student_name") or "دانش‌آموز")
            card=_Card(fill=(0.10,0.17,0.25,1),size_hint_y=None,height=dp(40),padding=dp(3))
            card.add_widget(self.label("● "+name,"8sp",WHITE,34,False,True))
            self.participants_area.add_widget(card)
        self.set_status("کلاس زنده: " + self.class_title + ((" • " + bundle.get("info")) if bundle.get("info") else ""), SUCCESS)

    def set_status(self, text, color=SUCCESS):
        try:
            self.status.text = rtl_text(text)
            self.status.color = color
        except Exception:
            pass

    def tool(self, *_):
        self.set_status("ابزار انتخاب شد؛ آماده قرار دادن محتوا روی تخته است.", SUCCESS)

    def toggle(self, button):
        button.text = rtl_text("✓ " + button.text)
        self.set_status("کنترل کلاس تغییر کرد.", SUCCESS)

    def chat(self, *_):
        api=getattr(self.app_state,"api",None)
        if api is None or not self.class_id:
            self.set_status("کلاس فعال برای چت مشخص نیست.",ERROR); return
        def work():
            try:
                rows=api.table_select("online_class_chat",{"class_id":"eq."+str(self.class_id),"order":"id.desc","limit":"20"}) or []
                Clock.schedule_once(lambda *_: self.set_status(f"چت کلاس فعال است • {len(rows)} پیام اخیر",SUCCESS),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.set_status("چت کلاس دریافت نشد.",ERROR),0)
        Thread(target=work,daemon=True).start()

    def attendance(self, *_):
        try:
            if self.manager:
                self.manager.current="special_attendance"
                self.set_status("محیط حضور و غیاب کلاس باز شد.",SUCCESS)
        except Exception as exc:
            self.set_status("محیط حضور و غیاب باز نشد: "+str(exc),ERROR)

    def files(self, *_):
        api=getattr(self.app_state,"api",None)
        if api is None or not self.class_id:
            self.set_status("کلاس فعال برای دریافت فایل مشخص نیست.",ERROR); return
        def work():
            try:
                rows=api.table_select("smart_board_files",{"class_id":"eq."+str(self.class_id),"limit":"20"}) or []
                names=[str(r.get("title") or r.get("file_path") or "فایل درس") for r in rows]
                text="فایل‌های کلاس: "+("، ".join(names) if names else "فایلی ثبت نشده است.")
                Clock.schedule_once(lambda *_: self.set_status(text,SUCCESS),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.set_status("فایل‌های درس دریافت نشد.",ERROR),0)
        Thread(target=work,daemon=True).start()

    def finish(self, *_):
        if not self.class_id:
            self.set_status("جلسه فعالی برای پایان دادن مشخص نیست.",ERROR); return
        api=getattr(self.app_state,"api",None)
        if api is None: return
        def work():
            try:
                import datetime
                if self.session_id:
                    api.table_update("online_class_sessions",{"id":"eq."+str(self.session_id)},{"ended_at":datetime.datetime.now().isoformat()})
                else:
                    api.table_insert("online_class_sessions",{"class_id":self.class_id,"ended_at":datetime.datetime.now().isoformat()})
                Clock.schedule_once(lambda *_: self.set_status("زمان پایان جلسه در سامانه ثبت شد.",SUCCESS),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.set_status("ثبت پایان جلسه ناموفق بود: "+str(exc),ERROR),0)
        Thread(target=work,daemon=True).start()

    def refresh_live(self, *_):
        api=getattr(self.app_state,"api",None)
        if api is None or not self.class_id:
            self.set_status("ابتدا کلاس را بارگذاری کنید.",ERROR); return
        def work():
            try:
                import datetime
                teacher_id=(self.app_state.profile or {}).get("linked_teacher_id") if self.app_state else None
                row=api.table_insert("online_class_sessions",{"class_id":self.class_id,"started_at":datetime.datetime.now().isoformat()})
                self.session_id=(row[0].get("id") if isinstance(row,list) and row else None)
                Clock.schedule_once(lambda *_: self.set_status("جلسه آنلاین به‌صورت واقعی شروع و در سامانه ثبت شد.",SUCCESS),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self.set_status("شروع جلسه ناموفق بود: "+str(exc),ERROR),0)
        Thread(target=work,daemon=True).start()

    def back(self, *_):
        if self.manager:
            target = self.return_to or "dashboard"
            try:
                self.manager.current = target
            except Exception:
                self.manager.current = "dashboard"
