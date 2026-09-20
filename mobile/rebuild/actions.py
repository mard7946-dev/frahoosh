from threading import Thread
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from mobile.ui import font_name, rtl_text
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE

DISCIPLINE_TYPES = (
    "بی‌نظمی","تأخیر","عدم انجام تکلیف","رفتار نامناسب",
    "ترک کلاس بدون اجازه","استفاده غیرمجاز از تلفن همراه",
    "درگیری / مشاجره","سایر",
)

class SchoolActionScreen(Screen):
    def __init__(self, app_state=None, mode="attendance", **kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.mode=mode
        self.students=[]; self.values={}; self._build()

    def _label(self,text,size="12sp",color=SECONDARY,height=42,bold=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def _button(self,text,cb,color=PRIMARY,height=44):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="12sp",
                 background_normal="",background_color=color,color=WHITE,
                 size_hint_y=None,height=dp(height)); b.bind(on_release=cb); return b

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(6))
        head=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6))
        back=self._button("بازگشت",lambda *_:setattr(self.manager,"current","workspace"),PRIMARY,40)
        head.add_widget(back); head.add_widget(self._label(self._title(),"18sp",PRIMARY,46,True)); root.add_widget(head)
        self.status=self._label("در حال دریافت فهرست دانش‌آموزان…","10sp",SECONDARY,36,True); root.add_widget(self.status)
        self.body=BoxLayout(orientation="vertical",spacing=dp(5),size_hint_y=None); self.body.bind(minimum_height=self.body.setter("height"))
        from kivy.uix.scrollview import ScrollView
        sc=ScrollView(do_scroll_x=False); sc.add_widget(self.body); root.add_widget(sc); self.add_widget(root)
        Thread(target=self._fetch_students,daemon=True).start()

    def _title(self):
        return {"attendance":"حضور و غیاب کلاس","discipline":"ثبت مورد انضباطی","online_attendance":"کنترل حضور کلاس آنلاین"}.get(self.mode,"عملیات مدرسه")

    def _fetch_students(self):
        try:
            rows=self.app_state.api.table_select("students",{"limit":"500"}) or []
            Clock.schedule_once(lambda *_:self._render_students(rows),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._fail(str(exc)),0)

    def _fail(self,msg):
        self.status.text=rtl_text("دریافت اطلاعات انجام نشد."); self.status.color=ERROR
        self.body.clear_widgets(); self.body.add_widget(self._label("خطای فنی در گزارش برنامه ثبت شد.","12sp",ERROR,55,True))

    def _render_students(self,rows):
        self.students=[dict(r) for r in rows if isinstance(r,dict)]
        self.body.clear_widgets()
        if self.mode=="discipline": self._render_discipline()
        elif self.mode=="online_attendance": self._render_online()
        else: self._render_attendance()

    def _student_name(self,s):
        return (str(s.get("first_name") or "")+" "+str(s.get("last_name") or "")).strip() or str(s.get("student_code") or s.get("id") or "دانش‌آموز")

    def _render_attendance(self):
        self.body.add_widget(self._label("برای هر دانش‌آموز دقیقاً یکی از دو وضعیت «حاضر» یا «غایب» را انتخاب کنید.","11sp",PRIMARY,52,True))
        for s in self.students:
            row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(4))
            row.add_widget(self._label(self._student_name(s),"12sp",PRIMARY,48,True))
            self.values[int(s["id"])]=Spinner(text=rtl_text("حاضر"),values=(rtl_text("حاضر"),rtl_text("غایب")),
                                              font_name=font_name(),size_hint_x=.42)
            row.add_widget(self.values[int(s["id"])]); self.body.add_widget(row)
        self.body.add_widget(self._button("ثبت حضور و غیاب و ارسال به معاون آموزشی و اولیا",self._save_attendance,SUCCESS,50))

    def _save_attendance(self,*_):
        def work():
            try:
                from datetime import datetime
                date=datetime.now().strftime("%Y-%m-%d")
                for s in self.students:
                    sid=int(s["id"]); status=self.values[sid].text
                    self.app_state.api.table_insert("attendance",{"student_id":sid,"date":date,"status":status,"description":"ثبت توسط دبیر"})
                    self._notify(s,"حضور و غیاب",f"{self._student_name(s)}: {status}")
                Clock.schedule_once(lambda *_:self._done("حضور و غیاب ثبت شد و مسیر گزارش‌دهی انجام شد."),0)
            except Exception as exc: Clock.schedule_once(lambda *_:self._fail(str(exc)),0)
        Thread(target=work,daemon=True).start()

    def _render_discipline(self):
        self.body.add_widget(self._label("همه نقش‌های مدرسه می‌توانند دانش‌آموز را انتخاب کنند و نوع مشکل از فهرست انتخاب می‌شود.","11sp",PRIMARY,58,True))
        self.student=Spinner(text=rtl_text("انتخاب دانش‌آموز"),values=tuple(rtl_text(self._student_name(s)) for s in self.students),
                             font_name=font_name(),size_hint_y=None,height=dp(46))
        self.kind=Spinner(text=rtl_text(DISCIPLINE_TYPES[0]),values=tuple(rtl_text(x) for x in DISCIPLINE_TYPES),
                          font_name=font_name(),size_hint_y=None,height=dp(46))
        self.note=TextInput(hint_text=rtl_text("توضیحات مورد"),font_name=font_name(),multiline=True,size_hint_y=None,height=dp(90))
        self.body.add_widget(self._label("دانش‌آموز")); self.body.add_widget(self.student)
        self.body.add_widget(self._label("نوع مشکل")); self.body.add_widget(self.kind)
        self.body.add_widget(self.note)
        self.body.add_widget(self._button("ثبت و ارسال به معاون آموزشی سپس اولیا",self._save_discipline,SUCCESS,50))

    def _save_discipline(self,*_):
        if not self.students:return
        index=max(0,self.student.values.index(self.student.text)) if self.student.text in self.student.values else 0
        s=self.students[index]
        def work():
            try:
                payload={"student_id":int(s["id"]),"problem_type":self.kind.text,"description":self.note.text.strip(),
                         "status":"pending","reported_by":str(getattr(self.app_state,"national_code","") or "")}
                self.app_state.api.table_insert("discipline_records",payload)
                self._notify(s,"گزارش انضباطی",f"{self.kind.text} - {self.note.text.strip()}")
                Clock.schedule_once(lambda *_:self._done("مورد انضباطی ثبت شد."),0)
            except Exception as exc: Clock.schedule_once(lambda *_:self._fail(str(exc)),0)
        Thread(target=work,daemon=True).start()

    def _render_online(self):
        self.body.add_widget(self._label("سه کنترل حضور برای هر کلاس: شروع، کنترل دوم و کنترل سوم. عدم تأیید، کلاس را می‌بندد و گزارش برای اولیا ثبت می‌شود.","11sp",PRIMARY,78,True))
        for s in self.students:
            row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(4))
            row.add_widget(self._label(self._student_name(s),"12sp",PRIMARY,48,True))
            sp=Spinner(text=rtl_text("تأیید شد"),values=(rtl_text("تأیید شد"),rtl_text("عدم تأیید"),rtl_text("خروج")),
                       font_name=font_name(),size_hint_x=.44)
            self.values[int(s["id"])]=sp; row.add_widget(sp); self.body.add_widget(row)
        self.body.add_widget(self._button("ثبت کنترل حضور آنلاین",self._save_online,SUCCESS,50))

    def _save_online(self,*_):
        def work():
            try:
                from datetime import datetime
                now=datetime.now().isoformat()
                for s in self.students:
                    sid=int(s["id"]); v=self.values[sid].text
                    status="confirmed" if v=="تأیید شد" else ("failed" if v=="عدم تأیید" else "left")
                    self.app_state.api.table_insert("online_attendance",{"student_id":sid,"status":status,"check_number":1,"checked_at":now,"leave_time":now if status=="left" else None})
                    if status!="confirmed": self._notify(s,"کنترل حضور کلاس آنلاین",f"وضعیت: {v}")
                Clock.schedule_once(lambda *_:self._done("کنترل حضور آنلاین ثبت شد."),0)
            except Exception as exc: Clock.schedule_once(lambda *_:self._fail(str(exc)),0)
        Thread(target=work,daemon=True).start()

    def _notify(self,student,title,body):
        try:
            api=self.app_state.api; sid=student.get("id")
            api.table_insert("messages",{"title":title,"body":body,"audience_type":"role","audience_value":"educational","sender_name":"فراهوش"})
            api.table_insert("messages",{"title":title,"body":body,"audience_type":"parent","audience_value":str(sid or student.get("parent_phone") or ""), "sender_name":"فراهوش"})
        except Exception as exc: print("NOTIFICATION CHAIN ERROR:",repr(exc))

    def _done(self,msg):
        self.status.text=rtl_text(msg); self.status.color=SUCCESS
