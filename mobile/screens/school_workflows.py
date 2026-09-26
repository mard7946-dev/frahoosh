from datetime import datetime, timezone, timedelta
import random
from pathlib import Path
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from mobile.ui import font_name, rtl_text, fa_display, PersianTextInput
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME, SCHOOL_YEAR

def role_of(state):
    active_panel=str(getattr(state,"panel_role","") or "").strip().lower()
    aliases={"management":"manager","teachers":"teacher","teacher_panel":"teacher","teacher_dashboard":"teacher","دبیران":"teacher","کادر و دبیران":"teacher","educational_panel":"educational","executive_panel":"executive"}
    if active_panel:
        return aliases.get(active_panel,active_panel)
    profile=getattr(state,"profile",{}) or {}
    candidates=[profile.get("role"),profile.get("user_role"),profile.get("school_role"),profile.get("user_type"),profile.get("account_type"),getattr(state,"role",None)]
    raw=next((str(v).strip().lower() for v in candidates if str(v or "").strip()),"student")
    return {
        "admin":"manager","administrator":"manager","principal":"manager","manager":"manager","management":"manager","school_management":"manager","مدیر":"manager","مدیریت":"manager","مدیریت مدرسه":"manager",
        "معاون آموزشی":"educational","educational":"educational","educational_deputy":"educational",
        "معاون اجرایی":"executive","اجرایی":"executive","executive":"executive","executive_deputy":"executive",
        "معاون پرورشی":"cultural","پرورشی":"cultural","cultural":"cultural","cultural_deputy":"cultural",
        "مشاور":"counselor","مشاوره":"counselor","counselor":"counselor","counseling":"counselor",
        "دبیر":"teacher","teacher":"teacher","کادر":"staff","staff":"staff","ولی":"parent","اولیا":"parent","parent":"parent","دانش‌آموز":"student","دانش آموز":"student","student":"student"
    }.get(raw,raw)

class BaseWorkflow(Screen):
    def __init__(self,app_state=None,**kw): super().__init__(**kw); self.app_state=app_state
    def lab(self,t,h=42,s="11sp",c=SECONDARY,b=False):
        w=Label(text=fa_display(str(t)),font_name=font_name(),font_size=s,color=c,bold=b,halign="right",valign="middle",size_hint_y=None,height=dp(h)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w
    def btn(self,t,cb,c=PRIMARY,h=44):
        b=Button(text=fa_display(t),font_name=font_name(),font_size="11sp",
                 background_normal="",background_color=c,color=WHITE,
                 size_hint_y=None,height=dp(h))
        try:
            b.always_release = True
        except Exception:
            pass
        fired = {"value": False}
        def run(*_):
            if fired["value"]:
                return
            fired["value"] = True
            try:
                cb()
            except Exception as exc:
                print("WORKFLOW BUTTON CALLBACK ERROR:", repr(exc))
                self.msg("اجرای عملیات با خطا روبه‌رو شد: " + str(exc), ERROR)
            finally:
                fired["value"] = False
        b.bind(on_release=run)
        return b
    def field(self,h,m=False): return PersianTextInput(hint_text=fa_display(h),font_name=font_name(),font_size="12sp",halign="right",multiline=m,size_hint_y=None,height=dp(70 if m else 46))
    def _spinner(self,text,values,height=46):
        s=Spinner(text=fa_display(text),values=tuple(fa_display(v) for v in values),
                  font_name=font_name(),font_size="12sp",size_hint_y=None,height=dp(height),
                  background_normal="",background_color=(0.05,0.18,0.34,1),color=WHITE)
        return s
    def api(self): return getattr(self.app_state,"api",None)
    def username(self):
        p=getattr(self.app_state,"profile",{}) or {}; u=getattr(self.app_state,"user",{}) or {}
        return str(u.get("email") or p.get("email") or p.get("username") or "").strip()
    def back(self,*_):
        if self.manager:self.manager.current="dashboard"
    def msg(self,t,c=SUCCESS):
        from kivy.uix.popup import Popup
        Popup(title=fa_display("فراهوش"),content=self.lab(t,100,c=c),size_hint=(.9,.35)).open()

class CertificateWorkflowScreen(BaseWorkflow):
    def on_pre_enter(self,*_): self.build()
    def build(self):
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(6)); root.add_widget(self.lab("گواهی اشتغال به تحصیل",50,"21sp",PRIMARY,True))
        role=role_of(self.app_state)
        if role in {"student","parent"}: self.request(root)
        elif role=="executive": self.review(root)
        else: root.add_widget(self.lab("درخواست‌های تأییدشده در این نقش قابل مشاهده‌اند.",55))
        root.add_widget(self.btn("بازگشت",self.back,SECONDARY)); self.add_widget(root)
    def request(self,root):
        api=self.api(); students=[]
        try:
            if role_of(self.app_state)=="parent":
                links=api.table_select("parent_children",{"parent_username":f"eq.{self.username()}","limit":"50"}) or []
                for x in links: students += api.table_select("students",{"id":f"eq.{x.get('student_id')}","limit":"1"}) or []
            else:
                sid=(getattr(self.app_state,"profile",{}) or {}).get("linked_student_id"); students=api.table_select("students",{"id":f"eq.{sid}","limit":"1"}) if sid else []
        except Exception: students=[]
        self.students=students; names=[f"{s.get('first_name','')} {s.get('last_name','')}".strip() for s in students] or ["پرونده‌ای پیدا نشد"]
        self.student=Spinner(text=fa_display(names[0]),values=tuple(fa_display(x) for x in names),font_name=font_name(),size_hint_y=None,height=dp(46))
        self.dest=self.field("فقط به منظور ارائه به")
        root.add_widget(self.lab("دانش‌آموز",30)); root.add_widget(self.student); root.add_widget(self.dest); root.add_widget(self.btn("ثبت درخواست",self.submit,SUCCESS))
        try:
            rows=api.table_select("certificate_requests",{"order":"id.desc","limit":"50"}) or []
            for r in rows:
                if r.get("status")=="approved" and str(r.get("student_id")) in {str(s.get("id")) for s in students}:
                    root.add_widget(self.lab(f"#{r.get('id')} • {r.get('student_name')} • تأیید شد",42))
                    root.add_widget(self.btn("دریافت گواهی PDF",lambda *_a,row=r:self.make_pdf(row),PRIMARY,40))
        except Exception: pass
    def submit(self,*_):
        if not self.students or not self.api(): return
        s=self.students[max(0,[f"{x.get('first_name','')} {x.get('last_name','')}".strip() for x in self.students].index(str(self.student.text)) if str(self.student.text) in [f"{x.get('first_name','')} {x.get('last_name','')}".strip() for x in self.students] else 0)]
        try:
            self.api().table_insert("certificate_requests",{"student_id":s.get("id"),"student_name":f"{s.get('first_name','')} {s.get('last_name','')}".strip(),"destination":self.dest.text.strip(),"request_date":datetime.now().strftime("%Y-%m-%d"),"status":"pending_executive",})
            self.build()
        except Exception as e:self.msg("ثبت نشد: "+str(e),ERROR)
    def review(self,root):
        try: rows=self.api().table_select("certificate_requests",{"order":"id.desc","limit":"100"}) or []
        except Exception: rows=[]
        for r in rows:
            root.add_widget(self.lab(f"#{r.get('id')} | {r.get('student_name')} | {r.get('destination','-')} | {r.get('status')}",50))
            if r.get("status")=="pending_executive": root.add_widget(self.btn("تأیید معاون اجرایی و صدور",lambda *_a,row=r:self.approve(row),SUCCESS))
    def approve(self,row):
        try:self.api().table_update("certificate_requests",{"id":f"eq.{row['id']}"},{"status":"approved","approved_at":datetime.now(timezone.utc).isoformat(),"executive_note":"تأیید شد"}); self.build()
        except Exception as e:self.msg(str(e),ERROR)
    def make_pdf(self,row):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            from kivy.app import App
            fp=font_name(); pdfmetrics.registerFont(TTFont("FrahooshCert",fp))
            path=Path(App.get_running_app().user_data_dir)/f"گواهی_{row.get('student_name','student')}.pdf"; c=canvas.Canvas(str(path),pagesize=A4); w,h=A4
            rtl=lambda t:get_display(reshape(str(t)))
            def line(t,y,size=12): c.setFont("FrahooshCert",size); c.drawRightString(w-55,y,rtl(t))
            c.drawCentredString(w/2,h-65,rtl("جمهوری اسلامی ایران")); c.drawCentredString(w/2,h-88,rtl("وزارت آموزش وپرورش")); c.drawCentredString(w/2,h-125,rtl("گواهی اشتغال به تحصیل"))
            rows=self.api().table_select("students",{"id":f"eq.{row.get('student_id')}","limit":"1"}) or []; s=rows[0] if rows else {}
            name=row.get("student_name") or ""; code=s.get("national_code") or s.get("student_code") or ""; father=s.get("father_name") or ""; birth=s.get("birth_date") or s.get("birth_date_shamsi") or ""; grade=s.get("grade") or ""
            school_code=str((getattr(self.app_state,"profile",{}) or {}).get("school_code") or "")
            line("شماره:",h-160); line(f"بدین وسیله گواهی میشود: {name} کد ملی {code} فرزند: {father}",h-195); line(f"شماره شناسنامه: {s.get('birth_certificate_no') or code} تاریخ تولد: {birth} سال تحصیلی: {SCHOOL_YEAR}",h-230); line(f"در مدرسه: {SCHOOL_NAME} ({school_code}) در پایه: {grade}",h-265); line("مشغول به تحصیل میباشد",h-300); line(f"این گواهی طبق تقاضای مورخ : {row.get('request_date','')}",h-335); line(f"فقط به منظور ارائه به: {row.get('destination','')}",h-370); line("صادر گردید و فاقد هرگونه ارزش دیگری می باشد.",h-405); line("دوره تحصیلی: دوره متوسطه اول",h-440); line("تاریخ",h-475); line("مهر و امضا مدیر مدرسه",h-515); line("مدیر( فاقد اعتبار بدون مهر و امضا)",h-545); c.save(); self.msg("گواهی ساخته شد: "+str(path),SUCCESS)
        except Exception as e:self.msg("ساخت PDF ناموفق: "+str(e),ERROR)

class MeetingWorkflowScreen(BaseWorkflow):
    """Real meeting request workflow: requester, subject, target, day/date/time, CRUD and approval."""
    def on_pre_enter(self,*_):
        self.build()

    def build(self):
        self.clear_widgets()
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5))
        root.add_widget(self.lab("تعیین وقت ملاقات",48,"21sp",PRIMARY,True))
        scroll=ScrollView(do_scroll_x=False,do_scroll_y=True)
        body=BoxLayout(orientation="vertical",spacing=dp(5),padding=[dp(3),dp(8)],size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))
        scroll.add_widget(body); root.add_widget(scroll)
        role=role_of(self.app_state)
        if role in {"parent","teacher","staff","counselor","advisor","educational","executive","cultural","manager","student"}:
            self.request(body)
        if role in {"manager","educational","executive","cultural","advisor"}:
            self.review(body,role)
        body.add_widget(self.lab("تاریخ ثبت درخواست به‌صورت خودکار ثبت می‌شود. پس از ثبت، درخواست در صندوق پیام مخاطب نیز اطلاع‌رسانی می‌شود.",58,"10sp",SECONDARY))
        root.add_widget(self.btn("بازگشت",self.back,SECONDARY))
        self.add_widget(root)

    def request(self,body):
        self._body=body
        self.title_field=self.field("عنوان / موضوع ملاقات")
        self.target_role=self._spinner("نوع مخاطب",["دبیر","معاون آموزشی","معاون اجرایی","معاون پرورشی","مشاور","مدیریت","ولی","دانش‌آموز"])
        self.target=self.field("نام شخص مورد ملاقات")
        self.day=self._spinner("روز هفته",["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه"])
        self.date=self.field("تاریخ ملاقات؛ مثال ۱۴۰۵/۰۷/۰۱")
        self.time=self.field("ساعت ملاقات؛ مثال ۱۰:۳۰")
        self.reason=self.field("موضوع / علت ملاقات")
        self.details=self.field("توضیحات تکمیلی",True)
        for label,w in [
            ("عنوان ملاقات",self.title_field),("نوع مخاطب",self.target_role),("نام شخص",self.target),
            ("روز",self.day),("تاریخ",self.date),("ساعت",self.time),("موضوع",self.reason),("توضیحات",self.details)
        ]:
            body.add_widget(self.lab(label,24,"10sp",SECONDARY,True)); body.add_widget(w)
        body.add_widget(self.btn("ثبت درخواست ملاقات",self.create,SUCCESS,48))
        body.add_widget(self.btn("پاک کردن فرم",lambda *_:self._clear_request_form(),SECONDARY,42))
        body.add_widget(self.lab("درخواست‌های ثبت‌شده من",35,"13sp",PRIMARY,True))
        self._load_my_requests(body)

    def _clear_request_form(self):
        for w in [self.title_field,self.target,self.date,self.time,self.reason,self.details]:
            w.text=""
        self._ok_msg("فرم پاک شد.")

    def _ok_msg(self,text):
        self.msg(text,SUCCESS)

    def _value(self,w):
        return (w.get_logical_text() if hasattr(w,"get_logical_text") else str(getattr(w,"text","") or "")).strip()

    def _load_my_requests(self,body):
        try:
            username=self.username()
            rows=self.api().table_select("meeting_requests",{"requester_username":f"eq.{username}","order":"id.desc","limit":"50"}) or []
        except Exception as exc:
            body.add_widget(self.lab("خواندن درخواست‌های قبلی ناموفق بود: "+str(exc),42,"9sp",ERROR)); return
        if not rows:
            body.add_widget(self.lab("هنوز درخواست ملاقاتی ثبت نشده است.",40,"10sp",SECONDARY)); return
        for row in rows:
            title=row.get("title") or row.get("reason") or "ملاقات"
            meta=f"#{row.get('id')} | {title} | {row.get('target_name') or '-'} | {row.get('requested_day') or '-'} | {row.get('requested_date') or '-'} | {row.get('requested_time') or '-'} | {row.get('status') or '-'}"
            body.add_widget(self.lab(meta,58,"9sp",WHITE,True))
            actions=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(4))
            b1=self.btn("ویرایش",lambda *_a,r=dict(row):self.edit_request(r),PRIMARY,40)
            b2=self.btn("حذف",lambda *_a,r=dict(row):self.delete_request(r),ERROR,40)
            actions.add_widget(b1); actions.add_widget(b2); body.add_widget(actions)

    def create(self,*_):
        vals=[self._value(self.title_field),self._value(self.target),self._value(self.date),self._value(self.time),self._value(self.reason)]
        if not all(vals):
            self.msg("عنوان، نام مخاطب، تاریخ، ساعت و موضوع ملاقات الزامی است.",ERROR); return
        role=role_of(self.app_state); profile=getattr(self.app_state,"profile",{}) or {}
        label=self._value(self.target_role)
        target_role={"دبیر":"teacher","معاون آموزشی":"educational","معاون اجرایی":"executive","معاون پرورشی":"cultural","مشاور":"advisor","مدیریت":"manager","ولی":"parent","دانش‌آموز":"student"}.get(label,"staff")
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload={
            "title":vals[0],"requester_username":self.username(),
            "requester_name":getattr(self.app_state,"display_name","کاربر") or "کاربر",
            "requester_role":role,"target_username":self._value(self.target),"target_name":self._value(self.target),
            "target_role":target_role,"student_id":profile.get("linked_student_id"),
            "teacher_id":profile.get("linked_teacher_id") or profile.get("teacher_id"),
            "parent_id":profile.get("linked_parent_id") or profile.get("parent_id"),
            "parent_phone":profile.get("phone") or "","requested_day":self._value(self.day),
            "requested_date":self._value(self.date),"requested_time":self._value(self.time),
            "reason":self._value(self.reason),"description":self._value(self.details),
            "status":"pending_manager","manager_status":"pending"
        }
        try:
            # The request does not need the inserted row back. Using
            # return=minimal keeps the write independent from a SELECT policy
            # on the old production meeting table.
            self.api().table_insert("meeting_requests",payload,return_representation=False)
            # Immediate inbox delivery when the target is a known username.
            target_username=self._value(self.target)
            try:
                if target_username:
                    self.api().table_insert("messages",{
                        "sender":self.username(),"sender_name":getattr(self.app_state,"display_name","کاربر") or "کاربر",
                        "receiver":target_username,"title":"درخواست جدید ملاقات",
                        "body":f"درخواست ملاقات «{vals[0]}» برای {self._value(self.date)} ساعت {self._value(self.time)} ثبت شد.",
                        "audience_type":"user","audience_value":target_username
                    })
            except Exception as notify_exc:
                print("MEETING TARGET NOTIFICATION ERROR:",repr(notify_exc))
            self.msg("درخواست ملاقات با موفقیت ثبت شد و اطلاع‌رسانی آن انجام شد.",SUCCESS)
            self.build()
        except Exception as exc:
            self.msg("ثبت درخواست ملاقات انجام نشد: "+str(exc),ERROR)

    def edit_request(self,row):
        self.clear_widgets()
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5))
        root.add_widget(self.lab("ویرایش درخواست ملاقات",48,"20sp",PRIMARY,True))
        scroll=ScrollView(do_scroll_x=False)
        body=BoxLayout(orientation="vertical",spacing=dp(5),padding=[dp(3),dp(8)],size_hint_y=None)
        body.bind(minimum_height=body.setter("height")); scroll.add_widget(body); root.add_widget(scroll)
        self.edit_id=row.get("id")
        self.title_field=self.field("عنوان ملاقات"); self.title_field.text=str(row.get("title") or "")
        self.target=self.field("نام شخص"); self.target.text=str(row.get("target_name") or row.get("target_username") or "")
        self.day=self._spinner("روز هفته",["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه"]); self.day.text=fa_display(str(row.get("requested_day") or "شنبه"))
        self.date=self.field("تاریخ"); self.date.text=str(row.get("requested_date") or "")
        self.time=self.field("ساعت"); self.time.text=str(row.get("requested_time") or "")
        self.reason=self.field("موضوع"); self.reason.text=str(row.get("reason") or "")
        self.details=self.field("توضیحات",True); self.details.text=str(row.get("description") or "")
        for w in [self.title_field,self.target,self.day,self.date,self.time,self.reason,self.details]: body.add_widget(w)
        body.add_widget(self.btn("ذخیره ویرایش",self.save_edit,SUCCESS,48))
        body.add_widget(self.btn("حذف درخواست",lambda *_:self.delete_request(row),ERROR,45))
        body.add_widget(self.btn("بازگشت",self.build,SECONDARY,45))
        self.add_widget(root)

    def save_edit(self,*_):
        try:
            if not all(self._value(x) for x in [self.title_field,self.target,self.date,self.time,self.reason]):
                self.msg("فیلدهای اصلی را کامل کنید.",ERROR); return
            self.api().table_update("meeting_requests",{"id":f"eq.{self.edit_id}"},{
                "title":self._value(self.title_field),"target_name":self._value(self.target),"target_username":self._value(self.target),
                "requested_day":self._value(self.day),"requested_date":self._value(self.date),
                "requested_time":self._value(self.time),"reason":self._value(self.reason),"description":self._value(self.details)
            }, return_representation=False)
            self.msg("درخواست ملاقات ویرایش شد.",SUCCESS); self.build()
        except Exception as exc:self.msg("ویرایش انجام نشد: "+str(exc),ERROR)

    def delete_request(self,row):
        try:
            self.api().table_delete("meeting_requests",{"id":f"eq.{row.get('id')}"})
            self.msg("درخواست ملاقات حذف شد.",SUCCESS); self.build()
        except Exception as exc:self.msg("حذف انجام نشد: "+str(exc),ERROR)

    def review(self,body,role):
        body.add_widget(self.lab("درخواست‌های ملاقات برای بررسی",40,"15sp",PRIMARY,True))
        try: rows=self.api().table_select("meeting_requests",{"order":"id.desc","limit":"100"}) or []
        except Exception as exc:
            body.add_widget(self.lab("خواندن درخواست‌ها ناموفق بود: "+str(exc),42,"9sp",ERROR)); return
        for row in rows:
            body.add_widget(self.lab(
                f"#{row.get('id')} | {row.get('title') or row.get('reason') or 'ملاقات'} | درخواست‌کننده: {row.get('requester_name') or '-'} | مخاطب: {row.get('target_name') or '-'} | {row.get('requested_day') or '-'} | {row.get('requested_date') or '-'} | {row.get('requested_time') or '-'} | {row.get('status') or '-'}",
                76,"9sp",WHITE,True))
            actions=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(4))
            actions.add_widget(self.btn("تأیید",lambda *_a,r=dict(row):self.approve(r),SUCCESS,40))
            actions.add_widget(self.btn("رد",lambda *_a,r=dict(row):self.reject(r),ERROR,40))
            actions.add_widget(self.btn("حذف",lambda *_a,r=dict(row):self.delete_request(r),SECONDARY,40))
            body.add_widget(actions)

    def approve(self,row):
        try:
            self.api().table_update("meeting_requests",{"id":f"eq.{row.get('id')}"},{"status":"approved","manager_status":"approved"}, return_representation=False)
            self._notify(row,"درخواست ملاقات شما تأیید شد.")
            self.msg("درخواست تأیید شد.",SUCCESS); self.build()
        except Exception as exc:self.msg("تأیید انجام نشد: "+str(exc),ERROR)

    def reject(self,row):
        try:
            self.api().table_update("meeting_requests",{"id":f"eq.{row.get('id')}"},{"status":"rejected","manager_status":"rejected"}, return_representation=False)
            self._notify(row,"درخواست ملاقات شما رد شد.")
            self.msg("درخواست رد شد.",SUCCESS); self.build()
        except Exception as exc:self.msg("رد درخواست انجام نشد: "+str(exc),ERROR)

    def _notify(self,row,text):
        try:
            self.api().table_insert("messages",{
                "sender":"school","sender_name":"مدرسه","receiver":row.get("requester_username"),
                "title":"وضعیت درخواست ملاقات","body":text,
                "audience_type":"user","audience_value":row.get("requester_username")
            })
        except Exception as exc: print("MEETING STATUS NOTIFICATION ERROR:",repr(exc))

class OnlineClassWorkflowScreen(BaseWorkflow):
    """Operational online-class lifecycle shared by manager, deputies, teachers and students."""
    STAFF_ROLES = {"manager", "educational", "executive", "cultural", "advisor", "counselor", "teacher"}

    def on_pre_enter(self, *_):
        self.build()

    def build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(5))
        root.add_widget(self.lab("کلاس آنلاین واقعی", 48, "20sp", PRIMARY, True))
        role = role_of(self.app_state)
        if role in self.STAFF_ROLES:
            root.add_widget(self.btn("ایجاد کلاس آنلاین", self.show_create_form, SUCCESS))
            self._create_area = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(0), spacing=dp(4))
            root.add_widget(self._create_area)
        self.list_box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        root.add_widget(self.list_box)
        root.add_widget(self.lab("دانش‌آموز فقط پس از شروع جلسه توسط دبیر/مسئول مجاز وارد می‌شود؛ حضور و راستی‌آزمایی در جداول واقعی ثبت می‌شود.", 58))
        root.add_widget(self.btn("بازگشت", self.back, SECONDARY))
        self.add_widget(root)
        self._load_classes()

    def _load_classes(self):
        try:
            rows = self.api().table_select("online_classes", {"order": "id.desc", "limit": "50"}) or []
        except Exception as exc:
            rows = []
            self.msg("دریافت کلاس‌ها ناموفق بود: " + str(exc), ERROR)
        role = role_of(self.app_state)
        if role in {"student", "parent"}:
            rows = [r for r in rows if str(r.get("status", "")).lower() == "active"]
        self.classes = rows
        self.list_box.clear_widgets()
        for row in rows:
            self._add_class_row(row)

    def _add_class_row(self, row):
        role = role_of(self.app_state)
        title = row.get("title") or "کلاس آنلاین"
        meta = " | ".join(str(x or "") for x in (row.get("subject"), row.get("class_name"), row.get("teacher"), row.get("start_time_shamsi"), row.get("end_time_shamsi")) if str(x or "").strip())
        self.list_box.add_widget(self.lab(f"#{row.get('id')} • {title} • {meta}", 42, "10sp", WHITE, True))
        if role in {"manager", "educational", "executive", "cultural", "advisor", "counselor"}:
            status = str(row.get("status") or "inactive")
            if status != "active":
                self.list_box.add_widget(self.btn("فعال‌سازی کلاس", lambda *_a, r=row: self.activate(r), SUCCESS, 40))
            else:
                self.list_box.add_widget(self.btn("غیرفعال‌سازی کلاس", lambda *_a, r=row: self.deactivate(r), SECONDARY, 40))
            self.list_box.add_widget(self.btn("شروع جلسه", lambda *_a, r=row: self.start_session(r), PRIMARY, 40))
        elif role == "teacher":
            if str(row.get("status") or "") == "active":
                self.list_box.add_widget(self.btn("شروع جلسه / ورود", lambda *_a, r=row: self.start_session(r), PRIMARY, 40))
            else:
                self.list_box.add_widget(self.lab("این کلاس هنوز توسط مسئول مجاز فعال نشده است.", 36, "9sp", SECONDARY))
        elif role == "student":
            self.list_box.add_widget(self.btn("ورود به کلاس", lambda *_a, r=row: self.join(r), PRIMARY, 42))

    def show_create_form(self, *_):
        if getattr(self, "_create_open", False):
            return
        self._create_open = True
        fields = [("title","عنوان کلاس"),("subject","درس"),("lesson","مبحث/جلسه"),("teacher","نام دبیر"),("grade","پایه"),("class_name","کلاس"),("duration","مدت (دقیقه)"),("start_time_shamsi","ساعت شروع"),("end_time_shamsi","ساعت پایان"),("join_url","لینک ورود"),("meeting_url","لینک جلسه")]
        self.form = {}
        self._create_area.clear_widgets()
        for key, hint in fields:
            w = self.field(hint)
            if key == "duration": w.text = "60"
            self.form[key] = w
            self._create_area.add_widget(w)
        actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(4))
        actions.add_widget(self.btn("ذخیره کلاس", self.create_class, SUCCESS, 40))
        actions.add_widget(self.btn("انصراف", self.close_create_form, SECONDARY, 40))
        self._create_area.add_widget(actions)
        self._create_area.height = dp(len(fields) * 46 + 42)

    def close_create_form(self, *_):
        self._create_open = False
        self._create_area.clear_widgets()
        self._create_area.height = 0

    def create_class(self, *_):
        payload = {key: (widget.get_logical_text() if hasattr(widget,"get_logical_text") else widget.text).strip() for key, widget in self.form.items() if (widget.get_logical_text() if hasattr(widget,"get_logical_text") else widget.text).strip()}
        if not payload.get("title"):
            self.msg("عنوان کلاس را وارد کنید.", ERROR); return
        try: payload["duration"] = int(payload.get("duration") or 60)
        except ValueError: payload["duration"] = 60
        role = role_of(self.app_state)
        payload["status"] = "active" if role in {"manager","educational","executive","cultural","advisor","counselor"} else "pending"
        if not payload.get("teacher"): payload["teacher"] = getattr(self.app_state,"display_name","") or self.username()
        created = (self.api().table_insert("online_classes", payload) or [{}])[0]
        class_id = created.get("id")
        profile = getattr(self.app_state,"profile",{}) or {}
        teacher_id = profile.get("linked_teacher_id") or profile.get("teacher_id")
        if class_id and teacher_id:
            try: self.api().table_insert("online_class_teachers",{"class_id":class_id,"teacher_id":teacher_id,"teacher_name":payload.get("teacher","")})
            except Exception as exc: print("ONLINE CLASS TEACHER LINK ERROR:",repr(exc))
        self.close_create_form()
        self.msg("کلاس آنلاین در سامانه ثبت شد." if payload["status"]=="active" else "کلاس ثبت شد و برای فعال‌سازی مسئول مجاز ارسال شد.",SUCCESS)
        self._load_classes()

    def activate(self,row):
        try: self.api().table_update("online_classes",{"id":f"eq.{row['id']}"},{"status":"active"}); self._load_classes()
        except Exception as exc: self.msg("فعال‌سازی ناموفق: "+str(exc),ERROR)

    def deactivate(self,row):
        try: self.api().table_update("online_classes",{"id":f"eq.{row['id']}"},{"status":"inactive"}); self._load_classes()

        except Exception as exc: self.msg("غیرفعال‌سازی ناموفق: "+str(exc),ERROR)

    def start_session(self,row):
        try:
            api=self.api()
            active=api.table_select("online_class_sessions",{"class_id":f"eq.{row['id']}","ended_at":"is.null","order":"id.desc","limit":"1"}) or []
            if active: self.msg("جلسه فعال است؛ دانش‌آموزان می‌توانند وارد شوند.",SUCCESS); return
            api.table_insert("online_class_sessions",{"class_id":row["id"],"started_at":datetime.now(timezone.utc).isoformat()})
            api.table_update("online_classes",{"id":f"eq.{row['id']}"},{"status":"active"})
            self.msg("جلسه کلاس شروع شد.",SUCCESS); self._load_classes()
        except Exception as exc: self.msg("شروع جلسه ناموفق: "+str(exc),ERROR)

    def join(self,row):
        api=self.api(); profile=getattr(self.app_state,"profile",{}) or {}; student_id=profile.get("linked_student_id") or profile.get("student_id")
        if role_of(self.app_state)!="student" or not student_id:
            self.msg("این عملیات برای ورود دانش‌آموز به جلسه است.",ERROR); return
        try:
            sessions=api.table_select("online_class_sessions",{"class_id":f"eq.{row['id']}","ended_at":"is.null","order":"id.desc","limit":"1"}) or []
            if not sessions: self.msg("جلسه هنوز توسط دبیر یا مسئول مجاز شروع نشده است.",ERROR); return
            session=sessions[0]; student_name=str(profile.get("display_name") or getattr(self.app_state,"display_name","") or ""); now=datetime.now(timezone.utc).isoformat()
            links=api.table_select("online_class_students",{"class_id":f"eq.{row['id']}","student_id":f"eq.{student_id}","limit":"1"}) or []
            if not links: api.table_insert("online_class_students",{"class_id":row["id"],"student_id":student_id,"student_name":student_name})
            api.table_insert("online_attendance",{"class_id":row["id"],"session_id":session.get("id"),"student_id":student_id,"student_name":student_name,"status":"present","event_time":now,"source":"online","checkpoint_no":0})
            api.table_insert("online_class_activity",{"class_id":row["id"],"session_id":session.get("id"),"student_id":student_id,"event_type":"join","event_time":now,"metadata":{}})
            api.table_insert("online_class_notifications",{"class_id":row["id"],"student_id":student_id,"recipient":self.username(),"recipient_role":"student","title":"ورود به کلاس آنلاین","message":"ورود شما به کلاس ثبت شد."})
            duration=max(12,int(row.get("duration",60) or 60)); upper=max(7,duration-5); count=2 if upper-5>=2 else 1
            for n,offset in enumerate(sorted(random.sample(range(5,upper),count)),1):
                api.table_insert("online_presence_checks",{"class_id":row["id"],"session_id":session.get("id"),"student_id":student_id,"checkpoint_no":n,"scheduled_at":(datetime.now(timezone.utc)+timedelta(minutes=offset)).isoformat(),"response":"pending"})
            self.msg("ورود ثبت شد؛ حضورهای راستی‌آزمایی نیز برای این جلسه ثبت شد.",SUCCESS)
        except Exception as exc: self.msg("ورود به کلاس ناموفق: "+str(exc),ERROR)

class ExamAuthoringScreen(BaseWorkflow):
    TYPES=[("multiple_choice","تستی"),("fill_blank","جای خالی"),("short_answer","پاسخ کوتاه"),("true_false","صحیح/غلط"),("matching","وصل کردنی"),("essay","تشریحی")]
    def on_pre_enter(self,*_): self.build()
    def build(self):
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5)); root.add_widget(self.lab("طراح آزمون آنلاین",48,"20sp",PRIMARY,True))
        self.title=self.field("عنوان آزمون"); self.subject=self.field("درس"); self.cls=self.field("کلاس"); self.duration=self.field("مدت آزمون")
        for x in [self.title,self.subject,self.cls,self.duration]: root.add_widget(x)
        self.exam_date=self.field("تاریخ آزمون"); self.start_time=self.field("ساعت شروع"); self.end_time=self.field("ساعت پایان"); self.share_code=self.field("کد انتشار")
        for x in [self.exam_date,self.start_time,self.end_time,self.share_code]: root.add_widget(x)
        self.qtype=Spinner(text="تستی",values=tuple(x[1] for x in self.TYPES),font_name=font_name(),size_hint_y=None,height=dp(45)); root.add_widget(self.qtype)
        tool=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(3))
        for symbol in ("√","∑","∫","²","³","≤","≥"): tool.add_widget(self.btn(symbol,lambda *_a,s=symbol:self._symbol(s),SECONDARY,40))
        root.add_widget(tool)
        self.q=self.field("متن سؤال؛ رادیکال، فرمول و نماد ریاضی را وارد کنید",100,True); self.opts=self.field("گزینه‌ها / جواب‌ها؛ در وصل‌کردنی شماره جواب را جلوی گزینه بنویسید",90,True)
        root.add_widget(self.q); root.add_widget(self.opts); root.add_widget(self.lab("این سؤال تشخیصی است؛ لطفاً هیچ چتی به آن جواب ندهید.",40,"8sp",SECONDARY))
        root.add_widget(self.btn("افزودن سؤال",self.addq,SUCCESS)); root.add_widget(self.btn("ساخت آزمون",self.create,PRIMARY)); root.add_widget(self.btn("خروجی PDF آزمون",self.export_pdf,SECONDARY)); root.add_widget(self.btn("خروجی Excel نمرات",self.export_scores,SECONDARY)); root.add_widget(self.btn("بازگشت",self.back,SECONDARY)); self.questions=[]
    def _symbol(self,s): self.q.text += s
    def addq(self,*_):
        typ=dict((v,k) for k,v in self.TYPES).get(str(self.qtype.text),"multiple_choice"); self.questions.append({"question":self.q.text.strip(),"question_type":typ,"option1":(self.opts.text.splitlines()+["","","",""])[0],"option2":(self.opts.text.splitlines()+["","","",""])[1],"option3":(self.opts.text.splitlines()+["","","",""])[2],"option4":(self.opts.text.splitlines()+["","","",""])[3],"correct_answer":"","points":1,"diagnostic_note":"این سؤال تشخیصی است؛ لطفاً هیچ چتی به آن جواب ندهید."}); self.q.text=""; self.opts.text=""
    def create(self,*_):
        if not self.questions or not self.title.text.strip(): return
        try:
            ex=(self.api().table_insert("teacher_exams",{"title":self.title.text.strip(),"subject":self.subject.text.strip(),"class_name":self.cls.text.strip(),"duration":int(self.duration.text or 45),"teacher":getattr(self.app_state,"display_name",""),"secure_mode":True,"published":False,"share_enabled":bool(self.share_code.text.strip()),"share_code":self.share_code.text.strip() or None}) or [{}])[0]
            for q in self.questions:
                q["quiz_id"]=ex.get("id"); self.api().table_insert("quiz_questions",q)
            for cls_name in [x.strip() for x in self.cls.text.split(",") if x.strip()]:
                try:self.api().table_insert("teacher_exam_slots",{"quiz_id":ex.get("id"),"class_name":cls_name,"exam_date_shamsi":self.exam_date.text.strip(),"start_time_shamsi":self.start_time.text.strip(),"end_time_shamsi":self.end_time.text.strip(),"duration":int(self.duration.text or 45),"coordinated":False,"secure_mode":True,"active":True})
                except Exception as slot_exc: print("EXAM SLOT ERROR:",repr(slot_exc))
            self.msg("آزمون، بانک سؤال و زمان‌بندی کلاس‌ها ذخیره شد.",SUCCESS)
        except Exception as e:self.msg(str(e),ERROR)

    def _last_exam(self):
        try:return (self.api().table_select("teacher_exams",{"order":"id.desc","limit":"1"}) or [None])[0]
        except Exception:return None
    def export_scores(self,*_):
        try:
            from mobile.services.export_service import export_excel
            ex=self._last_exam(); rows=self.api().table_select("teacher_exam_attempts",{"quiz_id":f"eq.{ex.get('id')}","limit":"1000"}) if ex else []
            path=export_excel(rows or [],list((rows or [{}])[0].keys()) or ["student_id","score"],"frahoosh_exam_scores"); self.msg("خروجی Excel نمرات ساخته شد: "+path,SUCCESS)
        except Exception as e:self.msg("خروجی Excel ناموفق: "+str(e),ERROR)
    def export_pdf(self,*_):
        try:
            from mobile.services.export_service import export_pdf
            ex=self._last_exam(); rows=self.api().table_select("quiz_questions",{"quiz_id":f"eq.{ex.get('id')}","limit":"1000"}) if ex else []
            path=export_pdf(rows or [],["question","question_type","option1","option2","option3","option4","points"],"آزمون فراهوش"); self.msg("PDF آزمون ساخته شد: "+path,SUCCESS)
        except Exception as e:self.msg("خروجی PDF ناموفق: "+str(e),ERROR)

class PanelIOWorkflowScreen(BaseWorkflow):
    """Real panel-level Excel/PDF transfer center for staff panels."""
    ALIASES={
        "users":"users","virtual":"online_classes","planning":"weekly_schedule","reports":"ai_smart_reports",
        "settings":"school_profile","class_management":"executive_classes","student_archive":"archive_items",
        "executive_operations":"executive_operations","referrals":"student_referrals","meetings":"meeting_requests",
        "meeting_requests":"meeting_requests","notifications":"school_events","exams":"teacher_exams",
        "questions":"quiz_questions","cultural_activities":"educational_activities","competitions":"competitions",
        "educational_programs":"school_events","activity_registrations":"cultural_activity_registrations",
        "cultural_reports":"cultural_reports","counseling_records":"counseling_records",
        "student_followup":"counseling_followups","academic_guidance":"counseling_followups",
        "counseling_reports":"ai_smart_reports","classes":"teacher_classes","grades":"grades",
        "assignments":"assignments","lesson":"lesson_plans","student_profile":"students",
        "activities":"activity_registrations","performance_report":"ai_smart_reports",
        "weekly_schedule":"weekly_schedule","online_payment":"payment_offers","children":"parent_children",
        "student_info":"students","educational_activities":"educational_activities","schedule_exams":"exam_schedule",
        "teacher_meetings":"teacher_meetings","payments_finance":"payment_records","payments":"payment_records",
        "transactions":"finance_transactions","accounts":"finance_accounts","financial_reports":"finance_transactions",
        "payment_settings":"payment_offers","whiteboard":"smart_board_whiteboards","files":"smart_board_files",
        "media":"smart_board_media","interactive_tools":"smart_board_interactive_tools",
        "assistant":"ai_assistant_sessions","educational_analysis":"ai_educational_analysis",
        "smart_reports":"ai_smart_reports","qa":"ai_questions","online_classes":"online_classes",
        "certificate_requests":"certificate_requests"
    }

    def __init__(self,app_state=None,panel_key="manager",**kw):
        super().__init__(app_state,**kw)
        self.panel_key=panel_key
        self._choices=[]
        self._picker_bound=False

    def on_pre_enter(self,*_):
        self.build()

    def modules(self):
        try:
            from mobile.screens.dashboard import MOTHER_PANEL_CATALOG
            key={"management":"manager","teachers":"teacher","students":"student","parents":"parent"}.get(self.panel_key,self.panel_key)
            return (MOTHER_PANEL_CATALOG.get(key) or {}).get("items") or []
        except Exception:
            return []

    def _table_choices(self):
        result=[]
        seen=set()
        for label,route in self.modules():
            table=self.ALIASES.get(route,route)
            if not table or table in seen:
                continue
            seen.add(table)
            result.append((str(label),str(table)))
        return result

    def build(self):
        self.clear_widgets()
        root=BoxLayout(orientation="vertical",padding=dp(9),spacing=dp(6))
        root.add_widget(self.lab("ورودی و خروجی اطلاعات • "+str(self.panel_key),48,"19sp",PRIMARY,True))
        root.add_widget(self.lab("برای هر جدول پنل، خروجی Excel یا PDF بگیرید و Excel را دوباره وارد همان جدول کنید.",52,"10sp",SECONDARY,False,True))

        choices=self._table_choices()
        self._choices=choices
        labels=[x[0] for x in choices] or ["جدولی برای این پنل تعریف نشده است."]
        self.table_spinner=Spinner(text=labels[0],values=labels,size_hint_y=None,height=dp(46),
                                   font_name=font_name(),font_size="11sp",
                                   background_normal="",background_color=(0.05,0.30,0.48,1),
                                   color=WHITE)
        root.add_widget(self.lab("انتخاب ماژول / جدول",28,"10sp",SECONDARY,True))
        root.add_widget(self.table_spinner)

        actions=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        actions.add_widget(self.btn("خروجی Excel",self.excel,SUCCESS,46))
        actions.add_widget(self.btn("خروجی PDF",self.pdf,PRIMARY,46))
        root.add_widget(actions)

        actions2=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        actions2.add_widget(self.btn("قالب Excel",self.template,SECONDARY,46))
        actions2.add_widget(self.btn("ورودی Excel",self.imp,(0.08,.42,.62,1),46))
        root.add_widget(actions2)

        self.status=self.lab("",62,"9sp",SECONDARY,False,True)
        root.add_widget(self.status)
        root.add_widget(self.btn("بازگشت",self.back,SECONDARY,44))
        self.add_widget(root)

    def selected_table(self):
        label=str(getattr(self,"table_spinner",None).text if getattr(self,"table_spinner",None) else "")
        for title,table in self._choices:
            if title==label:
                return table
        return self._choices[0][1] if self._choices else ""

    def selected_label(self):
        label=str(getattr(self,"table_spinner",None).text if getattr(self,"table_spinner",None) else "")
        return label or self.selected_table()

    def _rows(self,table):
        return [dict(x) for x in (self.api().table_select(table,{"order":"id.desc","limit":"2000"}) or []) if isinstance(x,dict)]

    def _fields(self,rows):
        if rows:
            keys=[]
            for row in rows:
                for key in row:
                    if key not in {"id","created_at","updated_at","deleted_at"} and key not in keys:
                        keys.append(key)
            return keys
        return []

    def excel(self,*_):
        table=self.selected_table()
        if not table:
            self.status.text=fa_display("ابتدا یک ماژول انتخاب کنید.")
            return
        try:
            from mobile.services.export_service import export_excel
            rows=self._rows(table); fields=self._fields(rows)
            if not fields:
                raise RuntimeError("این جدول هنوز رکوردی برای خروجی ندارد.")
            path=export_excel(rows,fields,title="frahoosh_"+table)
            self.status.text=fa_display("خروجی Excel ساخته شد: "+path)
            self.status.color=SUCCESS
        except Exception as exc:
            self.status.text=fa_display("خروجی Excel ناموفق بود: "+str(exc))
            self.status.color=ERROR

    def template(self,*_):
        table=self.selected_table()
        if not table:
            self.status.text=fa_display("ابتدا یک ماژول انتخاب کنید.")
            return
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment
            from mobile.services.export_service import app_dir
            rows=self._rows(table); fields=self._fields(rows)
            if not fields:
                fields=["title","description","status"]
            wb=Workbook(); ws=wb.active; ws.title="فراهوش"; ws.sheet_view.rightToLeft=True
            for col,key in enumerate(fields,1):
                cell=ws.cell(1,col,key); cell.font=Font(name="Noto Sans Arabic",size=11,bold=True); cell.alignment=Alignment(horizontal="right")
            ws.freeze_panes="A2"
            path=app_dir()/("frahoosh_"+table+"_template.xlsx"); wb.save(path)
            self.status.text=fa_display("قالب Excel ساخته شد: "+str(path)); self.status.color=SUCCESS
        except Exception as exc:
            self.status.text=fa_display("ساخت قالب Excel ناموفق بود: "+str(exc)); self.status.color=ERROR

    def pdf(self,*_):
        table=self.selected_table()
        if not table:
            self.status.text=fa_display("ابتدا یک ماژول انتخاب کنید.")
            return
        try:
            from mobile.services.export_service import export_pdf
            rows=self._rows(table); fields=self._fields(rows)
            if not fields:
                raise RuntimeError("این جدول هنوز رکوردی برای خروجی ندارد.")
            path=export_pdf(rows,fields,title="گزارش "+self.selected_label())
            self.status.text=fa_display("خروجی PDF ساخته شد: "+path); self.status.color=SUCCESS
        except Exception as exc:
            self.status.text=fa_display("خروجی PDF ناموفق بود: "+str(exc)); self.status.color=ERROR

    def _pick_excel_android(self):
        try:
            from android import activity
            from jnius import autoclass, cast
            PythonActivity=autoclass("org.kivy.android.PythonActivity")
            Intent=autoclass("android.content.Intent")
            Activity=autoclass("android.app.Activity")
            current=cast("android.app.Activity",PythonActivity.mActivity)
            request_code=5819
            def on_result(code,result_code,intent):
                if code!=request_code:
                    return
                try: activity.unbind(on_activity_result=on_result)
                except Exception: pass
                if result_code!=Activity.RESULT_OK or intent is None:
                    self.status.text=fa_display("انتخاب فایل Excel لغو شد."); return
                try:
                    uri=intent.getData()
                    resolver=current.getContentResolver()
                    stream=resolver.openInputStream(uri)
                    from java.io import ByteArrayOutputStream
                    out=ByteArrayOutputStream()
                    while True:
                        value=stream.read()
                        if value==-1: break
                        out.write(value)
                    stream.close()
                    target=Path(getattr(self.app_state,"user_data_dir",".") or ".")/"panel_import.xlsx"
                    target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(bytes(out.toByteArray()))
                    self._import_path(target)
                except Exception as exc:
                    self.status.text=fa_display("خواندن فایل Excel ناموفق بود: "+str(exc)); self.status.color=ERROR
            activity.bind(on_activity_result=on_result)
            intent=Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            current.startActivityForResult(intent,request_code)
            return True
        except Exception as exc:
            print("PANEL IO PICKER ERROR:",repr(exc)); return False

    def _import_path(self,path):
        table=self.selected_table()
        if not table:
            return
        try:
            from mobile.services.export_service import import_excel
            rows=import_excel(str(path)); count=0
            for row in rows:
                payload={str(k):v for k,v in row.items() if str(k).strip()}
                if payload:
                    self.api().table_insert(table,payload,return_representation=False); count+=1
            try: Path(path).unlink(missing_ok=True)
            except Exception: pass
            self.status.text=fa_display(f"{count} رکورد Excel وارد جدول «{self.selected_label()}» شد.")
            self.status.color=SUCCESS
        except Exception as exc:
            self.status.text=fa_display("ورودی Excel ناموفق بود: "+str(exc)); self.status.color=ERROR

    def imp(self,*_):
        if self._pick_excel_android():
            self.status.text=fa_display("فایل Excel را انتخاب کنید…"); self.status.color=SECONDARY
            return
        self.status.text=fa_display("در نسخه دسکتاپ، فایل Excel را با مسیر برنامه وارد کنید.")
