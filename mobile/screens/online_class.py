from datetime import datetime, timezone
import webbrowser

from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text

MANAGERS={"manager","educational","executive"}


def role_of(state):
    raw=str(getattr(state,"role","student") or "student").strip().lower()
    return {"admin":"manager","administrator":"manager","مدیر":"manager","مدیریت":"manager","معاون آموزشی":"educational","معاون اجرایی":"executive","معاون پرورشی":"cultural","دبیر":"teacher","معلم":"teacher","دانش‌آموز":"student","دانش آموز":"student","ولی":"parent","اولیا":"parent"}.get(raw,raw)


class OnlineClassScreen(Screen):
    def __init__(self,app_state=None,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.current_id=None; self.mic=True; self.camera=True; self._build()
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(7)); head=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(7))
        back=Button(text=rtl_text("‹ داشبورد"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(100)); back.bind(on_release=lambda *_:self._back()); head.add_widget(back)
        self.title=Label(text=rtl_text("کلاس‌های آنلاین"),font_name=font_name(),font_size="20sp",bold=True,color=PRIMARY,halign="right",valign="middle"); self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title); root.add_widget(head)
        self.status=Label(text="",font_name=font_name(),font_size="11sp",color=SECONDARY,halign="center",valign="middle",size_hint_y=None,height=dp(38)); self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False); self.body=BoxLayout(orientation="vertical",spacing=dp(8),padding=dp(4),size_hint_y=None); self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root)
    def on_pre_enter(self,*args): self.show_home()
    def _clear(self): self.body.clear_widgets(); self.current_id=None
    def _label(self,text,size="13sp",color=SECONDARY,height=58,bold=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="right",valign="middle",size_hint_y=None,height=dp(height)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w
    def _button(self,text,cb,color=PRIMARY,height=46):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="13sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(height)); b.bind(on_release=cb); self.body.add_widget(b); return b
    def _field(self,hint,height=48,multiline=False):
        f=TextInput(hint_text=rtl_text(hint),font_name=font_name(),font_size="13sp",multiline=multiline,size_hint_y=None,height=dp(height),halign="right",padding=[dp(10),dp(10)]); self.body.add_widget(f); return f
    def show_home(self):
        self._clear(); role=role_of(self.app_state); self._label("کلاس آنلاین واقعی","21sp",PRIMARY,52,True); self._label("ساخت کلاس، شروع/پایان جلسه، حضور و غیاب، گفت‌وگو، تخته مشترک، کنترل دوربین/میکروفون و اطلاع غیبت به ولی در همین پنل ثبت می‌شود.",height=82)
        if role in MANAGERS:self._create_form()
        self._load_classes()
    def _create_form(self):
        title=self._field("عنوان کلاس"); subject=self._field("درس / موضوع"); teacher=self._field("نام دبیر"); grade=self._field("پایه"); cls=self._field("نام کلاس"); duration=self._field("مدت به دقیقه"); duration.text="60"; join=self._field("لینک جلسه واقعی؛ اختیاری")
        self._button("＋ ساخت کلاس",lambda *_:self._create(title,subject,teacher,grade,cls,duration,join),SUCCESS)
    def _create(self,title,subject,teacher,grade,cls,duration,join):
        try:d=max(1,int(duration.text.strip() or 60))
        except Exception:return self._error("مدت کلاس باید عدد باشد.")
        if not title.text.strip():return self._error("عنوان کلاس الزامی است.")
        try:
            self.app_state.api.table_insert("online_classes",{"title":title.text.strip(),"subject":subject.text.strip(),"lesson":subject.text.strip(),"teacher":teacher.text.strip(),"grade":grade.text.strip(),"class_name":cls.text.strip(),"duration":d,"status":"inactive","join_url":join.text.strip(),"meeting_url":join.text.strip()}); self._ok("کلاس در پایگاه داده ثبت شد."); self.show_home()
        except Exception as exc:self._error("ساخت کلاس انجام نشد: "+str(exc))
    def _load_classes(self):
        try:rows=self.app_state.api.table_select("online_classes",{"order":"id.desc","limit":"50"})
        except Exception as exc:return self._error("خواندن کلاس‌ها انجام نشد: "+str(exc))
        if not rows:self._label("هنوز کلاسی ثبت نشده است.",height=55); return
        for r in rows:
            cid=r.get("id"); state=str(r.get("status") or "inactive"); self._label(f"#{cid} | {r.get('title') or 'کلاس آنلاین'}\n{r.get('subject','')} | پایه {r.get('grade','')} | کلاس {r.get('class_name','')} | دبیر {r.get('teacher','')}\nوضعیت: {'فعال' if state=='active' else ('پایان‌یافته' if state=='ended' else 'غیرفعال')}",height=92,bold=True)
            if role_of(self.app_state) in MANAGERS:
                if state!="active": self._button("▶ شروع جلسه",lambda *_ ,x=cid:self._start(x),SUCCESS)
                if state=="active": self._button("■ پایان جلسه",lambda *_ ,x=cid:self._end(x),ERROR)
                self._button("حضور و غیاب",lambda *_ ,x=cid:self._attendance(x),PRIMARY)
                self._button("گفت‌وگوی کلاس",lambda *_ ,x=cid:self._chat(x),PRIMARY)
                self._button("تخته مشترک / نوشتن روی تخته",lambda *_ ,x=cid:self._board(x),PRIMARY)
                self._button("اعلام غیبت به ولی",lambda *_ ,x=cid:self._absence_notice(x),PRIMARY)
            if state=="active":
                url=r.get("join_url") or r.get("meeting_url")
                if url:self._button("ورود به جلسه و فعال‌سازی دوربین/میکروفون",lambda *_ ,u=url:self._join(u),SUCCESS)
                self._button(f"میکروفون: {'روشن' if self.mic else 'خاموش'}",lambda *_:self._toggle_mic(),SECONDARY)
                self._button(f"دوربین: {'روشن' if self.camera else 'خاموش'}",lambda *_:self._toggle_camera(),SECONDARY)
    def _start(self,cid):
        try:self.app_state.api.table_insert("online_class_sessions",{"class_id":cid,"started_at":datetime.now(timezone.utc).isoformat()}); self.app_state.api.table_update("online_classes",{"id":f"eq.{cid}"},{"status":"active"}); self._ok("جلسه شروع شد و در سامانه ثبت گردید."); self.show_home()
        except Exception as exc:self._error("شروع جلسه انجام نشد: "+str(exc))
    def _end(self,cid):
        try:
            rows=self.app_state.api.table_select("online_class_sessions",{"class_id":f"eq.{cid}","order":"id.desc","limit":"1"});
            if rows:self.app_state.api.table_update("online_class_sessions",{"id":f"eq.{rows[0]['id']}"},{"ended_at":datetime.now(timezone.utc).isoformat()})
            self.app_state.api.table_update("online_classes",{"id":f"eq.{cid}"},{"status":"ended"}); self._ok("جلسه پایان یافت و زمان پایان ثبت شد."); self.show_home()
        except Exception as exc:self._error("پایان جلسه انجام نشد: "+str(exc))
    def _attendance(self,cid):
        self._clear(); self._label(f"حضور و غیاب جلسه #{cid}","21sp",PRIMARY,50,True)
        try:members=self.app_state.api.table_select("online_class_students",{"class_id":f"eq.{cid}","limit":"100"})
        except Exception as exc:return self._error(str(exc))
        if not members:self._label("دانش‌آموزان کلاس را می‌توان از جدول online_class_students به جلسه متصل کرد.",height=70)
        for m in members:
            sid=m.get("student_id"); name=m.get("student_name") or str(sid); self._button(f"{name} — حاضر",lambda *_ ,s=sid:self._mark(s,cid,"present"),SUCCESS,42); self._button(f"{name} — غایب",lambda *_ ,s=sid:self._mark(s,cid,"absent"),ERROR,42)
        self._button("بازگشت به کلاس‌ها",lambda *_:self.show_home())
    def _mark(self,sid,cid,status):
        try:self.app_state.api.table_insert("attendance",{"student_id":sid,"class_name":f"online:{cid}","subject":"کلاس آنلاین","attendance_date":datetime.now(timezone.utc).isoformat(),"status":status}); self._ok("حضور و غیاب ثبت شد.")
        except Exception as exc:self._error(str(exc))
    def _chat(self,cid):
        self._clear(); self._label(f"گفت‌وگوی کلاس #{cid}","21sp",PRIMARY,50,True)
        try:rows=self.app_state.api.table_select("messages",{"order":"id.desc","limit":"50"})
        except Exception:rows=[]
        for r in rows:
            if str(r.get("title") or "").startswith(f"کلاس #{cid}"):self._label(f"{r.get('sender_name','کاربر')}\n{r.get('body') or ''}",height=70)
        text=self._field("پیام کلاس",80,True); self._button("ارسال پیام",lambda *_:self._send_chat(cid,text),SUCCESS); self._button("بازگشت",lambda *_:self.show_home())
    def _send_chat(self,cid,text):
        if not text.text.strip():return self._error("متن پیام را وارد کنید.")
        try:self.app_state.api.table_insert("messages",{"sender_name":"کاربر فراهوش","title":f"کلاس #{cid} — گفت‌وگو","body":text.text.strip(),"audience_type":"online_class","audience_value":str(cid)}); self._ok("پیام ثبت شد."); self._chat(cid)
        except Exception as exc:self._error(str(exc))
    def _board(self,cid):
        self._clear(); self._label(f"تخته مشترک کلاس #{cid}","21sp",PRIMARY,50,True); self._label("محتوای تخته به صورت واقعی در پایگاه داده ذخیره می‌شود و در بازخوانی جلسه قابل مشاهده است.",height=62)
        try:rows=self.app_state.api.table_select("smart_board_whiteboards",{"class_id":f"eq.{cid}","order":"id.asc","limit":"100"})
        except Exception:rows=[]
        for r in rows:self._label(str(r.get("content") or r.get("text") or ""),height=65)
        text=self._field("متن / یادداشت روی تخته",100,True); self._button("ثبت روی تخته",lambda *_:self._save_board(cid,text),SUCCESS); self._button("بازگشت",lambda *_:self.show_home())
    def _save_board(self,cid,text):
        if not text.text.strip():return self._error("متن تخته خالی است.")
        try:self.app_state.api.table_insert("smart_board_whiteboards",{"class_id":cid,"content":text.text.strip(),"created_at":datetime.now(timezone.utc).isoformat()}); self._ok("محتوای تخته ذخیره شد."); self._board(cid)
        except Exception as exc:self._error(str(exc))
    def _absence_notice(self,cid):
        try:
            members=self.app_state.api.table_select("online_class_students",{"class_id":f"eq.{cid}","limit":"100"})
            sent=0
            for m in members:
                self.app_state.api.table_insert("messages",{"sender_name":"مدیریت مدرسه","title":"اطلاع غیبت کلاس آنلاین","body":f"دانش‌آموز {m.get('student_name') or m.get('student_id')} در جلسه آنلاین #{cid} غایب ثبت شد.","audience_type":"parent","student_id":m.get("student_id")}); sent+=1
            self._ok(f"اطلاع غیبت برای {sent} ولی در صندوق پیام‌ها ثبت شد.")
        except Exception as exc:self._error("ارسال اطلاع غیبت انجام نشد: "+str(exc))
    def _join(self,url):
        try:webbrowser.open(str(url)); self._ok("جلسه واقعی در لینک تعیین‌شده باز شد؛ کنترل دوربین و میکروفون توسط سرویس جلسه انجام می‌شود.")
        except Exception:self._error("باز کردن جلسه انجام نشد.")
    def _toggle_mic(self):self.mic=not self.mic; self.show_home()
    def _toggle_camera(self):self.camera=not self.camera; self.show_home()
    def _ok(self,text):self.status.color=SUCCESS;self.status.text=rtl_text(text)
    def _error(self,text):self.status.color=ERROR;self.status.text=rtl_text(text)
    def _back(self):
        if self.manager:self.manager.current="dashboard"
