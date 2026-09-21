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
from mobile.ui import font_name, rtl_text
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME, SCHOOL_YEAR

def role_of(state):
    raw=str(getattr(state,"role","student") or "student").strip().lower()
    return {"admin":"manager","administrator":"manager","مدیر":"manager","مدیریت":"manager","معاون آموزشی":"educational","educational":"educational","معاون اجرایی":"executive","executive":"executive","دبیر":"teacher","teacher":"teacher","کادر":"staff","staff":"staff","مشاور":"counselor","counselor":"counselor","ولی":"parent","اولیا":"parent","parent":"parent","دانش‌آموز":"student","دانش آموز":"student","student":"student"}.get(raw,raw)

class BaseWorkflow(Screen):
    def __init__(self,app_state=None,**kw): super().__init__(**kw); self.app_state=app_state
    def lab(self,t,h=42,s="11sp",c=SECONDARY,b=False):
        w=Label(text=rtl_text(str(t)),font_name=font_name(),font_size=s,color=c,bold=b,halign="right",valign="middle",size_hint_y=None,height=dp(h)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w
    def btn(self,t,cb,c=PRIMARY,h=44):
        b=Button(text=rtl_text(t),font_name=font_name(),font_size="11sp",background_normal="",background_color=c,color=WHITE,size_hint_y=None,height=dp(h)); b.bind(on_release=cb); return b
    def field(self,h,m=False): return TextInput(hint_text=rtl_text(h),font_name=font_name(),font_size="12sp",halign="right",multiline=m,size_hint_y=None,height=dp(70 if m else 46))
    def api(self): return getattr(self.app_state,"api",None)
    def username(self):
        p=getattr(self.app_state,"profile",{}) or {}; u=getattr(self.app_state,"user",{}) or {}
        return str(u.get("email") or p.get("email") or p.get("username") or "").strip()
    def back(self,*_):
        if self.manager:self.manager.current="dashboard"
    def msg(self,t,c=SUCCESS):
        from kivy.uix.popup import Popup
        Popup(title=rtl_text("فراهوش"),content=self.lab(t,100,c=c),size_hint=(.9,.35)).open()

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
        self.student=Spinner(text=rtl_text(names[0]),values=tuple(rtl_text(x) for x in names),font_name=font_name(),size_hint_y=None,height=dp(46))
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
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(6)); root.add_widget(self.lab("تعیین وقت ملاقات",50,"21sp",PRIMARY,True))
        role=role_of(self.app_state)
        if role in {"parent","teacher","staff","counselor","educational","executive","cultural","manager"}: self.request(root)
        if role in {"manager","educational","executive","cultural"}: self.review(root,role)
        root.add_widget(self.lab("درخواست تا تأیید نهایی مدیر برای درخواست‌کننده و مخاطب نمایش داده نمی‌شود.",55)); root.add_widget(self.btn("بازگشت",self.back,SECONDARY)); self.add_widget(root)
    def request(self,root):
        self.target=self.field("مخاطب مورد ملاقات"); self.reason=self.field("علت ملاقات"); self.date=self.field("روز ملاقات"); self.time=self.field("ساعت ملاقات")
        for label,w in [("مخاطب",self.target),("علت",self.reason),("روز",self.date),("ساعت",self.time)]: root.add_widget(self.lab(label,28)); root.add_widget(w)
        root.add_widget(self.btn("ثبت درخواست",self.create,SUCCESS))
    def create(self,*_):
        if not all(x.text.strip() for x in [self.target,self.reason,self.date,self.time]): return
        p={"student_id":(getattr(self.app_state,"profile",{}) or {}).get("linked_student_id"),"teacher_id":None,"parent_phone":(getattr(self.app_state,"profile",{}) or {}).get("phone") or "","target_type":role_of(self.app_state),"target_person":self.target.text.strip(),"requested_date":self.date.text.strip(),"reason":self.reason.text.strip(),"status":"pending_responsible"}
        try:self.api().table_insert("meeting_requests",p); self.msg("درخواست ثبت شد؛ پس از تأیید مسئول مربوط و مدیر قابل مشاهده است."); self.build()
        except Exception as e:self.msg(str(e),ERROR)
    def review(self,root,role):
        try: rows=self.api().table_select("meeting_requests",{"order":"id.desc","limit":"100"}) or []
        except Exception: rows=[]
        for r in rows:
            root.add_widget(self.lab(f"#{r.get('id')} | {r.get('requester_name') or r.get('requester_username')} → {r.get('target_name')} | {r.get('requested_date')} {r.get('requested_time')} | {r.get('status')}",52))
            if role=="manager" and r.get("status") in {"pending_responsible","responsible_approved"}: root.add_widget(self.btn("تأیید نهایی مدیر",lambda *_a,row=r:self.final(row),SUCCESS))
            elif role!="manager" and r.get("status")=="pending_responsible": root.add_widget(self.btn("تأیید مسئول مربوط",lambda *_a,row=r:self.responsible(row),PRIMARY))
    def responsible(self,row):
        try:self.api().table_update("meeting_requests",{"id":f"eq.{row['id']}"},{"status":"responsible_approved"}); self.build()
        except Exception: pass
    def final(self,row):
        try:self.api().table_update("meeting_requests",{"id":f"eq.{row['id']}"},{"status":"approved"}); self.build()
        except Exception: pass

class OnlineClassWorkflowScreen(BaseWorkflow):
    def on_pre_enter(self,*_): self.build()
    def build(self):
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5)); root.add_widget(self.lab("کلاس آنلاین واقعی",48,"20sp",PRIMARY,True))
        try: classes=self.api().table_select("online_classes",{"order":"id.desc","limit":"30"}) or []
        except Exception: classes=[]
        for c in classes: root.add_widget(self.btn(f"{c.get('title','کلاس')} | {c.get('class_name','')}",lambda *_a,row=c:self.join(row),PRIMARY))
        root.add_widget(self.lab("ورود + دو حضور شناور برای هر زنگ ثبت می‌شود؛ در صورت عدم تأیید، غیبت و اعلان ثبت خواهد شد.",60)); root.add_widget(self.btn("بازگشت",self.back,SECONDARY)); self.add_widget(root)
    def join(self,c):
        api=self.api(); p=getattr(self.app_state,"profile",{}) or {}; sid=p.get("linked_student_id") or p.get("student_id"); cid=c.get("id"); now=datetime.now(timezone.utc)
        try:
            ss=api.table_select("online_class_sessions",{"class_id":f"eq.{cid}","order":"id.desc","limit":"1"}) or []; session=ss[0] if ss else (api.table_insert("online_class_sessions",{"class_id":cid,"started_at":now.isoformat()}) or [{}])[0]
            if role_of(self.app_state)=="student" and sid:
                api.table_insert("online_attendance",{"class_id":cid,"session_id":session.get("id"),"student_id":sid,"status":"present","checkpoint_no":0})
                for recipient,title in [("parent","حضور دانش‌آموز در کلاس"),("educational","حضور دانش‌آموز در کلاس")]:
                    api.table_insert("online_class_notifications",{"class_id":cid,"student_id":sid,"recipient":recipient,"recipient_role":recipient,"title":title,"message":"ورود دانش‌آموز ثبت شد."})
                duration=max(12,int(c.get("duration",50) or 50)); offsets=sorted(random.sample(range(5,max(7,duration-5)),2))
                for n,off in enumerate(offsets,1): api.table_insert("online_presence_checks",{"class_id":cid,"session_id":session.get("id"),"student_id":sid,"checkpoint_no":n,"scheduled_at":(now+timedelta(minutes=off)).isoformat(),"response":"pending"})
            self.msg("حضور ورود ثبت شد؛ دو زمان شناور برای تأیید ادامه کلاس تعیین شد.",SUCCESS)
        except Exception as e:self.msg("ثبت حضور ناموفق: "+str(e),ERROR)

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
        root.add_widget(self.btn("افزودن سؤال",self.addq,SUCCESS)); root.add_widget(self.btn("ساخت آزمون",self.create,PRIMARY)); root.add_widget(self.btn("بازگشت",self.back,SECONDARY)); self.questions=[]
    def _symbol(self,s): self.q.text += s
    def addq(self,*_):
        typ=dict((v,k) for k,v in self.TYPES).get(str(self.qtype.text),"multiple_choice"); self.questions.append({"question":self.q.text.strip(),"question_type":typ,"option1":(self.opts.text.splitlines()+["","","",""])[0],"option2":(self.opts.text.splitlines()+["","","",""])[1],"option3":(self.opts.text.splitlines()+["","","",""])[2],"option4":(self.opts.text.splitlines()+["","","",""])[3],"correct_answer":"","points":1,"diagnostic_note":"این سؤال تشخیصی است؛ لطفاً هیچ چتی به آن جواب ندهید."}); self.q.text=""; self.opts.text=""
    def create(self,*_):
        if not self.questions or not self.title.text.strip(): return
        try:
            ex=(self.api().table_insert("teacher_exams",{"title":self.title.text.strip(),"subject":self.subject.text.strip(),"class_name":self.cls.text.strip(),"duration":int(self.duration.text or 45),"teacher":getattr(self.app_state,"display_name",""),"secure_mode":True,"published":False,"share_enabled":bool(self.share_code.text.strip()),"share_code":self.share_code.text.strip() or None}) or [{}])[0]
            for q in self.questions:
                q["quiz_id"]=ex.get("id"); self.api().table_insert("quiz_questions",q)
            self.msg("آزمون و بانک سؤال واقعی ذخیره شد.",SUCCESS)
        except Exception as e:self.msg(str(e),ERROR)

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
            wb.save(path); self.status.text=rtl_text("Excel: "+str(path))
        except Exception as e:self.status.text=rtl_text("Excel ناموفق: "+str(e))
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
            c.save(); self.status.text=rtl_text("PDF: "+str(path))
        except Exception as e:self.status.text=rtl_text("PDF ناموفق: "+str(e))
    def imp(self,*_):
        try:
            from mobile.services.export_service import import_excel
            rows=import_excel(self.path.text.strip()); table=self.table.text.strip(); count=0
            for row in rows:
                try:self.api().table_insert(table,row); count+=1
                except Exception: pass
            self.status.text=rtl_text(f"{count} ردیف وارد شد.")
        except Exception as e:self.status.text=rtl_text("ورود Excel ناموفق: "+str(e))
