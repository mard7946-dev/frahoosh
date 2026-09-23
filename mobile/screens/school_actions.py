from datetime import datetime
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView

from mobile.ui import font_name, rtl_text, fa_display
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE


DISCIPLINE_TYPES = (
    "بی‌نظمی",
    "تأخیر",
    "عدم انجام تکلیف",
    "رفتار نامناسب",
    "ترک کلاس بدون اجازه",
    "استفاده غیرمجاز از تلفن همراه",
    "درگیری / مشاجره",
    "سایر",
)


def _role(state):
    raw = str(getattr(state, "role", "") or "").strip().lower()
    return {
        "admin": "manager", "administrator": "manager", "مدیر": "manager",
        "معاون آموزشی": "educational", "معاون اجرایی": "executive",
        "معاون پرورشی": "cultural", "مشاور": "advisor",
        "دبیر": "teacher", "معلم": "teacher",
        "دانش‌آموز": "student", "ولی": "parent", "اولیا": "parent",
    }.get(raw, raw)


class _Base(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.students = []
        self._build()

    def label(self, text, size="12sp", color=SECONDARY, height=42, bold=False):
        w = Label(text=fa_display(str(text)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="right", valign="middle",
                  size_hint_y=None, height=dp(height))
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def button(self, text, cb, color=PRIMARY, height=44):
        b = Button(text=fa_display(text), font_name=font_name(), font_size="12sp",
                   background_normal="", background_color=color, color=WHITE,
                   size_hint_y=None, height=dp(height))
        b.bind(on_release=cb)
        return b

    def _root(self, title):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        head.add_widget(self.button("بازگشت", lambda *_: self.back(), PRIMARY, 40))
        head.add_widget(self.label(title, "19sp", PRIMARY, 46, True))
        root.add_widget(head)
        self.status = self.label("", "10sp", SECONDARY, 38, True)
        root.add_widget(self.status)
        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(3), size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

    def back(self):
        if self.manager:
            self.manager.current = "panel"

    def _load_students(self, callback):
        def work():
            try:
                api = self.app_state.api
                rows = api.table_select("students", {"limit": "500"}) or []
                rows = [dict(r) for r in rows if isinstance(r, dict)]
                Clock.schedule_once(lambda *_: callback(rows, None), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: callback([], str(exc)), 0)
        Thread(target=work, daemon=True).start()

    def _notify(self, title, body, student):
        """Persist the required notification chain: educational deputy, then parent."""
        try:
            api=self.app_state.api; sid=student.get("id"); parent_phone=student.get("parent_phone")
            try:
                api.table_insert("messages",{"title":title,"body":body,"audience_type":"role","audience_value":"educational","sender_name":"فراهوش"})
            except Exception as exc: print("EDUCATIONAL NOTIFICATION ERROR:",repr(exc))
            try:
                api.table_insert("messages",{"title":title,"body":body,"audience_type":"parent","audience_value":str(sid or parent_phone or ""),"sender_name":"فراهوش"})
            except Exception as exc: print("PARENT NOTIFICATION ERROR:",repr(exc))
            try:
                api.table_insert("school_events",{"event_type":title,"title":title,"actor_username":str(getattr(self.app_state,"national_code","") or "")})
            except Exception: pass
        except Exception as exc: print("NOTIFICATION CHAIN ERROR:",repr(exc))



class TeacherAttendanceScreen(_Base):
    """Class attendance: one student list with explicit Present/Absent choice."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(app_state=app_state, **kwargs)
        self.values = {}

    def _build(self):
        self._root("حضور و غیاب کلاس")
        self.class_spinner = Spinner(text=fa_display("انتخاب کلاس"), values=(), size_hint_y=None,
                                     height=dp(45), font_name=font_name(), font_size="12sp")
        self.body.add_widget(self.class_spinner)
        self.subject = self.label("درس را بعداً می‌توان از برنامه دبیر گرفت؛ فعلاً ثبت حضور مستقل از درس است.", "9sp", SECONDARY, 38)
        self.body.add_widget(self.subject)
        self.list_box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.body.add_widget(self.list_box)
        self.save_btn = self.button("ثبت حضور و غیاب و ارسال گزارش", self.save_all, SUCCESS, 48)
        self.body.add_widget(self.save_btn)
        self._load_students(self.loaded)

    def loaded(self, rows, error):
        if error:
            self.status.text = fa_display("دریافت دانش‌آموزان انجام نشد: " + error); self.status.color = ERROR; return
        self.students = rows
        classes = sorted({str(s.get("class_name") or "").strip() for s in rows if str(s.get("class_name") or "").strip()})
        self.class_spinner.values = tuple(fa_display(x) for x in classes) or (fa_display("همه کلاس‌ها"),)
        if classes: self.class_spinner.text = fa_display(classes[0])
        self.render()

    def render(self):
        self.list_box.clear_widgets()
        selected = str(self.class_spinner.text or "").strip()
        rows = [s for s in self.students if selected in ("انتخاب کلاس", "همه کلاس‌ها") or str(s.get("class_name") or "").strip() == selected]
        self.values = {}
        for s in rows:
            sid = s.get("id")
            self.values[str(sid)] = "present"
            line = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4))
            line.add_widget(self.label(f"{s.get('first_name','')} {s.get('last_name','')}  •  {s.get('student_code','')}", "11sp", PRIMARY, 48, True))
            p = self.button("حاضر", lambda *_ ,i=str(sid): self.set_value(i, "present"), SUCCESS, 42)
            a = self.button("غایب", lambda *_ ,i=str(sid): self.set_value(i, "absent"), (0.72,.16,.18,1), 42)
            line.add_widget(p); line.add_widget(a)
            self.list_box.add_widget(line)
        self.class_spinner.bind(text=lambda *_: self.render())

    def set_value(self, sid, value):
        self.values[sid] = value
        self.status.text = rtl_text("وضعیت انتخاب شد؛ برای ثبت نهایی دکمه پایین را بزنید.")
        self.status.color = SUCCESS

    def save_all(self, *_):
        if not self.students: return
        selected = str(self.class_spinner.text or "").strip()
        rows = [s for s in self.students if selected in ("انتخاب کلاس", "همه کلاس‌ها") or str(s.get("class_name") or "").strip() == selected]
        date = datetime.now().strftime("%Y-%m-%d")
        self.status.text = rtl_text("در حال ثبت حضور و غیاب…"); self.status.color = SECONDARY
        def work():
            ok = 0
            for s in rows:
                try:
                    sid = s.get("id"); st = self.values.get(str(sid), "present")
                    self.app_state.api.table_insert("attendance", {
                        "student_id": sid, "date": date, "status": st,
                        "description": "ثبت توسط دبیر",
                    })
                    self._notify("حضور و غیاب", f"وضعیت حضور دانش‌آموز: {'حاضر' if st == 'present' else 'غایب'}", s)
                    ok += 1
                except Exception:
                    pass
            Clock.schedule_once(lambda *_: self.done(ok, len(rows)), 0)
        Thread(target=work, daemon=True).start()

    def done(self, ok, total):
        self.status.text = rtl_text(f"{ok} از {total} رکورد ثبت شد؛ گزارش حضور برای معاون آموزشی و اطلاع‌رسانی والدین در صف پیام قرار گرفت.")
        self.status.color = SUCCESS if ok else ERROR


class DisciplineScreen(_Base):
    """School-wide discipline entry bound to the real student list."""

    def _build(self):
        self._root("ثبت انضباطی")
        self.student_spinner = Spinner(text=fa_display("انتخاب دانش‌آموز"), values=(), size_hint_y=None,
                                       height=dp(45), font_name=font_name(), font_size="12sp")
        self.type_spinner = Spinner(text=rtl_text("نوع مشکل انضباطی"), values=tuple(fa_display(x) for x in DISCIPLINE_TYPES),
                                    size_hint_y=None, height=dp(45), font_name=font_name(), font_size="12sp")
        self.note = self.label("پس از انتخاب دانش‌آموز، نوع مورد را از منوی کشویی انتخاب کنید.", "10sp", SECONDARY, 42)
        self.body.add_widget(self.student_spinner); self.body.add_widget(self.type_spinner); self.body.add_widget(self.note)
        self.body.add_widget(self.button("ثبت مورد انضباطی → معاون آموزشی → اولیا", self.save, SUCCESS, 48))
        self._load_students(self.loaded)

    def loaded(self, rows, error):
        if error:
            self.status.text = rtl_text("دریافت دانش‌آموزان انجام نشد: " + error); self.status.color = ERROR; return
        self.students = rows
        self.student_map = {}
        values = []
        for s in rows:
            label = f"{s.get('first_name','')} {s.get('last_name','')} • {s.get('class_name','')} • {s.get('student_code','')}"
            values.append(label); self.student_map[fa_display(label)] = s
        self.student_spinner.values = tuple(fa_display(x) for x in values)
        if values: self.student_spinner.text = fa_display(values[0])

    def save(self, *_):
        selected = str(self.student_spinner.text or "").strip()
        student = self.student_map.get(selected)
        kind = str(self.type_spinner.text or "").strip()
        if not student or selected == fa_display("انتخاب دانش‌آموز") or kind == fa_display("نوع مشکل انضباطی"):
            self.status.text = rtl_text("دانش‌آموز و نوع مشکل انضباطی را انتخاب کنید."); self.status.color = ERROR; return
        try:
            self.app_state.api.table_insert("discipline_records", {
                "student_id": student.get("id"),
                "discipline_type": kind,
                "record_date": datetime.now().strftime("%Y-%m-%d"),
                "decision_type": "بررسی معاون آموزشی",
                "description": "ثبت توسط " + (_role(self.app_state) or "کاربر"),
                "actor_username": str(getattr(self.app_state, "national_code", "") or ""),
            })
            self._notify("مورد انضباطی", f"مورد «{kind}» برای دانش‌آموز ثبت شد و برای معاون آموزشی ارسال شد.", student)
            self.status.text = rtl_text("ثبت شد؛ ابتدا در صف معاون آموزشی قرار گرفت و سپس برای اطلاع ولی ارسال می‌شود.")
            self.status.color = SUCCESS
        except Exception as exc:
            self.status.text = rtl_text("ثبت مورد انضباطی انجام نشد: " + str(exc)); self.status.color = ERROR


class OnlineAttendanceScreen(_Base):
    """Three checkpoints. Stage 2/3 cannot be submitted until their configured delay."""
    def _build(self):
        self._root("حضور و غیاب سه‌مرحله‌ای کلاس آنلاین")
        self.class_spinner=Spinner(text=fa_display("انتخاب کلاس"),values=(),size_hint_y=None,height=dp(45),font_name=font_name(),font_size="12sp"); self.body.add_widget(self.class_spinner)
        self.delay2=Spinner(text=fa_display("مرحله ۲: پنج دقیقه بعد"),values=tuple(fa_display(x) for x in ("۱ دقیقه بعد","۵ دقیقه بعد","۱۰ دقیقه بعد","۱۵ دقیقه بعد")),size_hint_y=None,height=dp(45),font_name=font_name(),font_size="12sp"); self.body.add_widget(self.delay2)
        self.delay3=Spinner(text=fa_display("مرحله ۳: ده دقیقه بعد"),values=tuple(fa_display(x) for x in ("۲ دقیقه بعد","۱۰ دقیقه بعد","۲۰ دقیقه بعد","۳۰ دقیقه بعد")),size_hint_y=None,height=dp(45),font_name=font_name(),font_size="12sp"); self.body.add_widget(self.delay3)
        self.body.add_widget(self.label("مرحله ۱ ابتدای زنگ است؛ مرحله‌های ۲ و ۳ در زمان‌های متفاوت فعال می‌شوند. عدم تأیید هر مرحله، ادامه کلاس دانش‌آموز را می‌بندد و گزارش برای ولی ثبت می‌شود.","10sp",SECONDARY,72))
        self.stage_label=self.label("مرحله ۱ از ۳","17sp",PRIMARY,45,True); self.body.add_widget(self.stage_label)
        self.list_box=BoxLayout(orientation="vertical",spacing=dp(4),size_hint_y=None); self.list_box.bind(minimum_height=self.list_box.setter("height")); self.body.add_widget(self.list_box)
        self.next_btn=self.button("ثبت مرحله ۱ و فعال‌سازی راستی‌آزمایی",self.save_stage,SUCCESS,48); self.body.add_widget(self.next_btn)
        self.stage=1; self.values={}; self.stage_ready=True; self._stage_event=None; self._load_students(self.loaded)
    @staticmethod
    def _minutes(text,fallback):
        digits={"۱":"1","۲":"2","۳":"3","۴":"4","۵":"5","۶":"6","۷":"7","۸":"8","۹":"9","۰":"0"}; s="".join(digits.get(ch,ch) for ch in str(text or ""))
        for n in (1,2,5,10,15,20,30):
            if str(n) in s:return n
        return fallback
    def loaded(self,rows,error):
        if error:self.status.text=rtl_text("دریافت دانش‌آموزان انجام نشد: "+error); self.status.color=ERROR; return
        self.students=rows; classes=sorted({str(s.get("class_name") or "").strip() for s in rows if str(s.get("class_name") or "").strip()}); self.class_spinner.values=tuple(rtl_text(x) for x in classes) or (rtl_text("همه کلاس‌ها"),)
        if classes:self.class_spinner.text=rtl_text(classes[0])
        self.render()
    def render(self):
        self.list_box.clear_widgets(); selected=str(self.class_spinner.text or "").strip(); rows=[s for s in self.students if selected in ("انتخاب کلاس","همه کلاس‌ها") or str(s.get("class_name") or "").strip()==selected]
        for s in rows:
            sid=str(s.get("id")); self.values.setdefault(sid,"present"); line=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(4)); line.add_widget(self.label(f"{s.get('first_name','')} {s.get('last_name','')}","11sp",PRIMARY,46,True)); line.add_widget(self.button("تأیید حضور",lambda *_ ,i=sid:self.set_value(i,"present"),SUCCESS,40)); line.add_widget(self.button("عدم تأیید",lambda *_ ,i=sid:self.set_value(i,"failed"),(0.72,.16,.18,1),40)); self.list_box.add_widget(line)
    def set_value(self,sid,value):
        if not self.stage_ready:return
        self.values[sid]=value; self.status.text=rtl_text("انتخاب‌ها ثبت نشده‌اند؛ دکمه مرحله را بزنید."); self.status.color=SUCCESS
    def _lock_until_next_stage(self,minutes):
        self.stage_ready=False; self.next_btn.disabled=True; self.status.text=rtl_text(f"مرحله بعدی پس از {minutes} دقیقه فعال می‌شود."); self.status.color=SECONDARY
        if self._stage_event:self._stage_event.cancel()
        self._stage_event=Clock.schedule_once(lambda *_:self._unlock_stage(),minutes*60)
    def _unlock_stage(self):
        self.stage_ready=True; self.next_btn.disabled=False; self.status.text=rtl_text(f"مرحله {self.stage} از ۳ اکنون فعال است."); self.status.color=SUCCESS
    def save_stage(self,*_):
        if not self.stage_ready:return
        selected=str(self.class_spinner.text or "").strip(); rows=[s for s in self.students if selected in ("انتخاب کلاس","همه کلاس‌ها") or str(s.get("class_name") or "").strip()==selected]; stage=self.stage; now=datetime.now().isoformat()
        def work():
            for s in rows:
                sid=s.get("id"); value=self.values.get(str(sid),"present")
                try:
                    classes=self.app_state.api.table_select("online_classes",{"class_name":f"eq.{s.get('class_name')}","limit":"1"}) or []
                    class_row=classes[0] if classes else None
                    if not class_row: raise RuntimeError("کلاس آنلاین برای این کلاس پیدا نشد.")
                    sessions=self.app_state.api.table_select("online_class_sessions",{"class_id":f"eq.{class_row.get('id')}","ended_at":"is.null","order":"id.desc","limit":"1"}) or []
                    session=sessions[0] if sessions else (self.app_state.api.table_insert("online_class_sessions",{"class_id":class_row.get("id"),"started_at":now}) or [{}])[0]
                    self.app_state.api.table_insert("online_attendance",{"class_id":class_row.get("id"),"session_id":session.get("id"),"student_id":sid,"student_name":f"{s.get('first_name','')} {s.get('last_name','')}".strip(),"event_time":now,"source":"teacher_checkpoint","checkpoint_no":stage,"status":f"check{stage}_{value}"})
                    self.app_state.api.table_insert("online_class_activity",{"class_id":class_row.get("id"),"session_id":session.get("id"),"student_id":sid,"event_type":f"checkpoint_{stage}","event_time":now,"metadata":{"result":value}})
                    if value=="failed":self._notify("کلاس آنلاین",f"راستی‌آزمایی مرحله {stage} تأیید نشد؛ ادامه کلاس برای این دانش‌آموز بسته شد.",s)
                except Exception as exc:print("ONLINE ATTENDANCE SAVE ERROR:",repr(exc))
            Clock.schedule_once(lambda *_:self.after_stage(stage),0)
        Thread(target=work,daemon=True).start()
    def after_stage(self,stage):
        if stage>=3:
            self.stage_ready=False; self.next_btn.disabled=True; self.status.text=rtl_text("هر سه مرحله ثبت شد؛ دانش‌آموزان تأییدشده می‌توانند ادامه کلاس را داشته باشند."); self.status.color=SUCCESS; return
        self.stage+=1; self.stage_ready=False; self.stage_label.text=fa_display(f"مرحله {self.stage} از ۳ • راستی‌آزمایی جدید"); self.next_btn.text=fa_display(f"ثبت مرحله {self.stage}"); delay=self._minutes(self.delay2.text,5) if self.stage==2 else self._minutes(self.delay3.text,10); self._lock_until_next_stage(delay)


class SchoolActionsScreen(Screen):
    """Small dispatcher so special workflows stay independent from generic CRUD."""
    def __init__(self, app_state=None, mode="attendance", **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.mode = mode
        self.current = None
        self._open()

    def _open(self):
        mapping = {
            "attendance": TeacherAttendanceScreen,
            "discipline": DisciplineScreen,
            "online_attendance": OnlineAttendanceScreen,
        }
        cls = mapping.get(self.mode, TeacherAttendanceScreen)
        self.current = cls(name="action_inner", app_state=self.app_state)
        self.add_widget(self.current)
