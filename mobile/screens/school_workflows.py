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
        b=Button(text=fa_display(t),font_name=font_name(),font_size="11sp",background_normal="",background_color=c,color=WHITE,size_hint_y=None,height=dp(h)); b.bind(on_press=cb); return b
    def field(self,h,m=False): return PersianTextInput(hint_text=fa_display(h),font_name=font_name(),font_size="12sp",halign="right",multiline=m,size_hint_y=None,height=dp(70 if m else 46))
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
    def on_pre_enter(self,*_): self.build()

    def build(self):
        self.clear_widgets()
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(6))
        root.add_widget(self.lab("تعیین وقت ملاقات",50,"21sp",PRIMARY,True))
        role=role_of(self.app_state)
        if role in {"parent","teacher","staff","counselor","educational","executive","cultural","manager","student"}:
            self.request(root)
        if role in {"manager","educational","executive","cultural"}:
            self.review(root,role)
        root.add_widget(self.lab("درخواست پس از ثبت برای بررسی مسئول مربوط و تأیید نهایی مدیر ارسال می‌شود.",55))
        root.add_widget(self.btn("بازگشت",self.back,SECONDARY))
        self.add_widget(root)

    def request(self,root):
        self.target_role=self._spinner("نوع مخاطب",["دبیر","کادر اجرایی","مشاور","مدیریت","ولی"])
        self.target=self.field("نام یا نام کاربری مخاطب")
        self.reason=self.field("علت ملاقات")
        self.day=self._spinner("روز هفته",["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه"])
        self.date=self.field("تاریخ ملاقات؛ مثال ۱۴۰۵/۰۷/۰۱")
        self.time=self.field("ساعت ملاقات؛ مثال ۱۰:۳۰")
        self.details=self.field("توضیحات تکمیلی",70); self.details.multiline=True
        for label,w in [("مخاطب",self.target),("علت ملاقات",self.reason),("روز",self.day),("تاریخ",self.date),("ساعت",self.time),("توضیحات",self.details)]:
            root.add_widget(self.lab(label,28)); root.add_widget(w)
        root.add_widget(self.btn("ثبت درخواست ملاقات",self.create,SUCCESS))

    def create(self,*_):
        values=[self.target,self.reason,self.date,self.time]
        if not all(x.text.strip() for x in values):
            self.msg("مخاطب، علت، تاریخ و ساعت الزامی است.",ERROR); return
        role=role_of(self.app_state)
        profile=getattr(self.app_state,"profile",{}) or {}
        target=self.target.text.strip()
        target_type=str(self.target_role.text).strip()
        target_role={"دبیر":"teacher","کادر اجرایی":"staff","مشاور":"counselor","مدیریت":"manager","ولی":"parent"}.get(target_type,"teacher")
        p={"requester_username":self.username(),"requester_name":getattr(self.app_state,"display_name","کاربر") or "کاربر","requester_role":role,
           "target_username":target,"target_name":target,"target_role":target_role,
           "student_id":profile.get("linked_student_id"),
           "teacher_id":profile.get("linked_teacher_id") or profile.get("teacher_id"),
           "parent_id":profile.get("linked_parent_id") or profile.get("parent_id"),
           "parent_phone":profile.get("phone") or "",
           "requested_day":str(self.day.text).strip(),"requested_date":self.date.text.strip(),
           "requested_time":self.time.text.strip(),"reason":self.reason.text.strip(),
           "description":self.details.text.strip(),"status":"pending_manager","manager_status":"pending"}
        try:
            self.api().table_insert("meeting_requests",p)
            self.msg("درخواست ملاقات ثبت شد و برای بررسی مسئول مربوط و مدیر ارسال شد.")
            self.build()
        except Exception as e:
            self.msg("ثبت درخواست ملاقات انجام نشد: "+str(e),ERROR)

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
    ALIASES={"users":"users","virtual":"online_classes","planning":"weekly_schedule","reports":"ai_smart_reports","settings":"school_profile","class_management":"executive_classes","student_archive":"archive_items","executive_operations":"executive_operations","referrals":"student_referrals","meetings":"meeting_requests","meeting_requests":"meeting_requests","notifications":"school_events","exams":"teacher_exams","questions":"quiz_questions","cultural_activities":"educational_activities","competitions":"competitions","educational_programs":"school_events","activity_registrations":"cultural_activity_registrations","cultural_reports":"cultural_reports","counseling_records":"counseling_records","student_followup":"counseling_followups","academic_guidance":"counseling_followups","counseling_reports":"ai_smart_reports","classes":"teacher_classes","grades":"grades","assignments":"assignments","lesson":"lesson_plans","student_profile":"students","activities":"activity_registrations","performance_report":"ai_smart_reports","weekly_schedule":"weekly_schedule","online_payment":"payment_offers","children":"parent_children","student_info":"students","educational_activities":"educational_activities","schedule_exams":"exam_schedule","teacher_meetings":"teacher_meetings","payments_finance":"payment_records","payments":"payment_records","transactions":"finance_transactions","accounts":"finance_accounts","financial_reports":"finance_transactions","payment_settings":"payment_offers","whiteboard":"smart_board_whiteboards","files":"smart_board_files","media":"smart_board_media","interactive_tools":"smart_board_interactive_tools","assistant":"ai_assistant_sessions","educational_analysis":"ai_educational_analysis","smart_reports":"ai_smart_reports","qa":"ai_questions","online_classes":"online_classes","certificate_requests":"certificate_requests"}
    def __init__(self,app_state=None,panel_key="manager",**kw): super().__init__(app_state,**kw); self.panel_key=panel_key
    def on_pre_enter(self,*_): self.build()
    def build(self):
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(9),spacing=dp(6)); root.add_widget(self.lab(f"ورودی و خروجی اطلاعات • {self.panel_key}",48,"19sp",PRIMARY,True)); root.add_widget(self.lab("خروجی Excel/PDF از داده زنده و ورود Excel به جدول انتخاب‌شده.",48))
        self.path=self.field("برای ورود Excel مسیر فایل را وارد کنید"); self.table=self.field("نام جدول مقصد مثل students")
        root.add_widget(self.path); root.add_widget(self.table); root.add_widget(self.btn("خروجی Excel کل پنل",self.excel,SUCCESS)); root.add_widget(self.btn("خروجی PDF کل پنل",self.pdf,PRIMARY)); root.add_widget(self.btn("ورود Excel",self.imp,SECONDARY)); root.add_widget(self.btn("بازگشت",self.back,SECONDARY)); self.status=self.lab("",55); root.add_widget(self.status); self.add_widget(root)
    def modules(self):
        try:
            from mobile.screens.dashboard import MOTHER_PANEL_CATALOG
            key={"management":"manager","teachers":"teacher","students":"student","parents":"parent"}.get(self.panel_key,self.panel_key); return (MOTHER_PANEL_CATALOG.get(key) or {}).get("items") or []
        except Exception:return []
    def excel(self,*_):
        from openpyxl import Workbook
        from mobile.services.export_service import app_dir
        try:
            path=app_dir()/f"frahoosh_{self.panel_key}.xlsx"; wb=Workbook(); wb.remove(wb.active); used=set()
            for label,route in self.modules():
                table=self.ALIASES.get(route,route); name=str(table)[:25] or "data"; base=name; n=1
                while name in used:n+=1; name=f"{base[:22]}_{n}"
                used.add(name); ws=wb.create_sheet(name); rows=self.api().table_select(table,{"select":"*","order":"id.desc","limit":"1000"}) or []; fields=list(rows[0].keys()) if rows else ["status"]
                for j,k in enumerate(fields,1):ws.cell(1,j,k)
                for i,row in enumerate(rows,2):
                    for j,k in enumerate(fields,1):ws.cell(i,j,str(row.get(k,"")))
            wb.save(path); self.status.text = fa_display("Excel: "+str(path))
        except Exception as e:self.status.text = fa_display("Excel ناموفق: "+str(e))
    def pdf(self,*_):
        from reportlab.lib.pagesizes import A4,landscape
        from reportlab.pdfgen import canvas
        from mobile.services.export_service import app_dir
        try:
            path=app_dir()/f"frahoosh_{self.panel_key}.pdf"; c=canvas.Canvas(str(path),pagesize=landscape(A4)); w,h=landscape(A4); y=h-30; c.setFont("Helvetica",9); c.drawString(25,y,"Frahoosh "+self.panel_key); y-=22
            for label,route in self.modules():
                if y<35:c.showPage();y=h-30
                table=self.ALIASES.get(route,route); rows=self.api().table_select(table,{"select":"*","limit":"1000"}) or []; c.drawString(35,y,f"{label}: {len(rows)}"); y-=13
                for row in rows[:20]:
                    if y<25:c.showPage();y=h-30
                    c.drawString(45,y,str(row)[:150]); y-=10
            c.save(); self.status.text = fa_display("PDF: "+str(path))
        except Exception as e:self.status.text = fa_display("PDF ناموفق: "+str(e))
    def imp(self,*_):
        try:
            from mobile.services.export_service import import_excel
            rows=import_excel(self.path.text.strip()); table=self.table.text.strip(); count=0
            for row in rows:
                try:self.api().table_insert(table,row); count+=1
                except Exception: pass
            self.status.text = fa_display(f"{count} ردیف وارد شد.")
        except Exception as e:self.status.text = fa_display("ورود Excel ناموفق: "+str(e))
