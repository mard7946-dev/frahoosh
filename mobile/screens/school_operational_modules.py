from datetime import datetime
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_YEAR
from mobile.ui import font_name, fa_display, PersianTextInput
from mobile.screens.operational_centers import role_of

DAYS = ["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه"]
BELL_LABELS = {1:"زنگ اول",2:"زنگ دوم",3:"زنگ سوم"}

class SchoolModulesScreen(Screen):
    """Specialized Android implementation of the Web operational module contract."""
    def __init__(self, app_state=None, route="", **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.route = str(route or "")
        self._build_shell()

    def api(self):
        api = getattr(self.app_state, "api", None)
        if api is None: raise RuntimeError("اتصال پایگاه داده آماده نیست.")
        return api

    def val(self, w):
        return w.get_logical_text().strip() if hasattr(w,"get_logical_text") else str(getattr(w,"text","") or "").strip()

    def lab(self, text, size="10sp", color=SECONDARY, bold=False, h=38, center=False):
        w=Label(text=fa_display(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(h))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def field(self, hint, h=46, multi=False):
        return PersianTextInput(hint_text=fa_display(hint),font_name=font_name(),font_size="11sp",
                                halign="right",multiline=multi,size_hint_y=None,height=dp(h))

    def btn(self, text, cb, color=PRIMARY, h=44):
        b=Button(text=fa_display(text),font_name=font_name(),font_size="11sp",background_normal="",
                 background_color=color,color=WHITE,size_hint_y=None,height=dp(h))
        b.bind(on_release=cb); return b

    def spin(self, text, values):
        return Spinner(text=fa_display(text),values=tuple(fa_display(x) for x in values),
                       font_name=font_name(),font_size="11sp",size_hint_y=None,height=dp(46))

    def _build_shell(self):
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(6))
        head=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        head.add_widget(self.btn("بازگشت",self.back,SECONDARY,42))
        self.title=self.lab("مرکز عملیاتی", "17sp", PRIMARY, True, 42, True)
        head.add_widget(self.title)
        root.add_widget(head)
        self.status=self.lab("آماده","9sp",SUCCESS,True,28,True); root.add_widget(self.status)
        sc=ScrollView(do_scroll_x=False,bar_width=dp(3))
        self.body=BoxLayout(orientation="vertical",spacing=dp(6),padding=dp(3),size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height")); sc.add_widget(self.body); root.add_widget(sc)
        self.add_widget(root)

    def on_pre_enter(self,*_):
        self.render_route()

    def clear(self,title):
        self.body.clear_widgets(); self.title.text=fa_display(title)

    def role(self): return role_of(self.app_state)

    def today(self): return datetime.now().strftime("%Y-%m-%d")

    def profile(self): return getattr(self.app_state,"profile",{}) or {}

    def student_id(self):
        p=self.profile()
        for k in ("linked_student_id","student_id"):
            if p.get(k):
                try:return int(p[k])
                except: pass
        n=str(p.get("national_code") or getattr(self.app_state,"national_code","") or "").strip()
        if n:
            rows=self.api().table_select("students",{"national_code":"eq."+n,"limit":"1"}) or []
            if rows:return int(rows[0]["id"])
        try:
            u=str(getattr(self.app_state,"user",{}).get("username") or p.get("username") or "").strip()
            if u:
                rows=self.api().table_select("students",{"email":"eq."+u,"limit":"1"}) or []
                if rows:return int(rows[0]["id"])
        except: pass
        return None

    def student(self,sid=None):
        sid=sid or self.student_id()
        if not sid:return {}
        rows=self.api().table_select("students",{"id":"eq."+str(sid),"limit":"1"}) or []
        return rows[0] if rows else {}

    def sname(self,s):
        return (" ".join(str(s.get(k) or "").strip() for k in ("first_name","last_name")).strip() or "دانش‌آموز")

    def rows(self,table,params=None):
        return self.api().table_select(table,params or {"order":"id.desc","limit":"200"}) or []

    def insert(self,table,payload):
        result=self.api().table_insert(table,payload)
        self.status.text=fa_display("ثبت با موفقیت انجام شد."); self.status.color=SUCCESS
        return result

    def update(self,table,filters,payload):
        result=self.api().table_update(table,filters,payload)
        self.status.text=fa_display("ویرایش با موفقیت انجام شد."); self.status.color=SUCCESS
        return result

    def render_route(self):
        try:
            fn={
                "grades":self.grades,"student_grades":self.grades,"report_cards":self.grades,
                "student_cards":self.student_cards,
                "weekly_schedule":self.weekly_schedule,
                "exam_schedule":self.exam_schedule,"exam_seat_assignments":self.exam_schedule,
                "activity_offers":self.activities,"activity_registrations":self.activities,
                "student_council":lambda:self.consent_activity("student_council","شورای دانش‌آموزی"),
                "basij_registration":lambda:self.consent_activity("basij_registration","بسیج دانش‌آموزی"),
                "school_ally":lambda:self.consent_activity("school_ally","همیار مدرسه"),
                "school_mayor":lambda:self.consent_activity("school_mayor","شهردار مدرسه"),
                "khwarizmi_registrations":lambda:self.consent_activity("khwarizmi_registrations","جشنواره خوارزمی"),
                "educational_activities":self.educational_activities,
                "parent_activities":self.parent_activities,
                "transport_requests":self.transport,
                "discipline_records":self.discipline,
                "counseling_records":self.counseling,
                "counseling_followups":self.counseling_followups,
                "counseling_guidance":self.counseling_guidance,
                "counseling_classes":self.counseling_classes,
                "student_referrals":self.student_referrals,
                "counselor_board":self.counselor_board,
                "educational_followups":self.educational_followups,
                "academic_followups":self.academic_followups,
                "cultural_reports":self.counseling_reports,
                "ai_smart_reports":self.counseling_reports,
                "attendance":self.attendance,
                "messages":self.messages,
            }.get(self.route)
            if not fn: raise RuntimeError("این ماژول در مرکز تخصصی تعریف نشده است.")
            fn()
        except Exception as exc:
            self.clear("خطا در ماژول")
            self.body.add_widget(self.lab(str(exc),"10sp",ERROR,True,70,True))
            self.status.text=fa_display("بارگذاری ماژول ناموفق بود."); self.status.color=ERROR

    def grades(self):
        self.clear("کارنامه / نمرات")
        role=self.role(); can=role in {"teacher","manager","educational"}
        self.body.add_widget(self.lab("ردیف | درس | نوع آزمون | نام آزمون | نمره کل | نمره کسب‌شده","10sp",PRIMARY,True,44,True))
        if can:
            self.body.add_widget(self.lab("ثبت نمره برای دبیر فعال است؛ محدودیت درس/دبیر در Supabase اعمال می‌شود.","9sp",SECONDARY,False,42,True))
            sid=self.field("شناسه دانش‌آموز"); subject=self.field("نام درس"); typ=self.field("نوع آزمون، مثلاً شفاهی"); exam=self.field("نام آزمون")
            maxs=self.field("نمره کل آزمون"); score=self.field("نمره کسب‌شده"); cls=self.field("کلاس")
            for w in (sid,subject,typ,exam,maxs,score,cls): self.body.add_widget(w)
            self.body.add_widget(self.btn("ثبت نمره",lambda *_:self._save_grade(sid,subject,typ,exam,maxs,score,cls),SUCCESS,48))
        grade_params={"select":"id,student_id,subject,grade_type,exam_name,max_score,score,class_name,source_grade_id","order":"id.desc","limit":"300"}
        if role in {"student","parent"}:
            sid=self.student_id()
            if sid: grade_params["student_id"]="eq."+str(sid)
        data=self.rows("grades",grade_params)
        if not data:
            self.body.add_widget(self.lab("هنوز نمره‌ای ثبت نشده است.","10sp",SECONDARY,False,44,True)); return
        for i,r in enumerate(data,1):
            row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(3))
            row.add_widget(self.lab(f"{i} | {r.get('subject') or '—'} | {r.get('grade_type') or '—'} | {r.get('exam_name') or '—'} | {r.get('max_score') or '—'} | {r.get('score') or '—'}","9sp",SECONDARY,False,44,False))
            if can:
                row.add_widget(self.btn("ویرایش",lambda *_a,x=dict(r):self._edit_grade(x),PRIMARY,42))
                row.add_widget(self.btn("حذف",lambda *_a,x=dict(r):self._delete_row("grades",x.get("id"),self.grades),ERROR,42))
            self.body.add_widget(row)

    def _edit_grade(self,row):
        sid=self.field("شناسه دانش‌آموز"); subject=self.field("نام درس"); typ=self.field("نوع آزمون"); exam=self.field("نام آزمون")
        maxs=self.field("نمره کل آزمون"); score=self.field("نمره کسب‌شده"); cls=self.field("کلاس")
        for w,v in ((sid,row.get("student_id")),(subject,row.get("subject")),(typ,row.get("grade_type")),(exam,row.get("exam_name")),(maxs,row.get("max_score")),(score,row.get("score")),(cls,row.get("class_name"))):
            w.text=str(v or ""); self.body.add_widget(w)
        self.body.add_widget(self.btn("ذخیره ویرایش",lambda *_:self._update_grade(row,sid,subject,typ,exam,maxs,score,cls),SUCCESS,48))

    def _update_grade(self,row,sid,subject,typ,exam,maxs,score,cls):
        payload={"student_id":int(self.val(sid)),"subject":self.val(subject),"grade_type":self.val(typ),"exam_name":self.val(exam),
                 "max_score":float(self.val(maxs) or 0),"score":float(self.val(score) or 0),"class_name":self.val(cls)}
        self.update("grades",{"id":"eq."+str(row.get("id"))},payload); self.grades()

    def _delete_row(self,table,rid,refresh):
        if not rid: raise ValueError("شناسه رکورد مشخص نیست.")
        self.api().table_delete(table,{"id":"eq."+str(rid)})
        self.status.text=fa_display("رکورد با موفقیت حذف شد."); self.status.color=SUCCESS
        refresh()

    def _save_grade(self,sid,subject,typ,exam,maxs,score,cls):
        if not self.val(subject) or not self.val(sid): raise ValueError("شناسه دانش‌آموز و نام درس الزامی است.")
        payload={"student_id":int(self.val(sid)),"subject":self.val(subject),"grade_type":self.val(typ),
                 "exam_name":self.val(exam),"max_score":float(self.val(maxs) or 0),"score":float(self.val(score) or 0),
                 "class_name":self.val(cls),"assessment_date":self.today(),"school_year":SCHOOL_YEAR}
        p=self.profile()
        payload["teacher_id"]=p.get("teacher_id") or p.get("linked_teacher_id")
        self.insert("grades",payload); self.grades()

    def student_cards(self):
        self.clear("کارت دانش‌آموزی")
        sid=self.student_id(); s=self.student(sid)
        if not sid or not s:
            self.body.add_widget(self.lab("پرونده دانش‌آموز پیدا نشد.","10sp",ERROR,True,52,True)); return
        cards=self.rows("student_cards",{"student_id":"eq."+str(sid),"limit":"1"})
        c=cards[0] if cards else {}
        seats=self.rows("class_seat_assignments",{"student_id":"eq."+str(sid),"academic_year":"eq."+SCHOOL_YEAR,"limit":"1"})
        seat=seats[0].get("seat_number") if seats else s.get("classroom_seat") or "—"
        self.body.add_widget(self.lab("کارت هویتی دانش‌آموز","15sp",PRIMARY,True,40,True))
        fields=[("نام و نام خانوادگی",c.get("full_name") or self.sname(s)),("کد ملی",c.get("national_code") or s.get("national_code")),
                ("پایه",c.get("grade") or s.get("grade")),("کلاس",c.get("class_name") or s.get("class_name")),
                ("سال تحصیلی",c.get("school_year") or SCHOOL_YEAR)]
        for k,v in fields:
            self.body.add_widget(self.lab(f"{k}: {v or '—'}","11sp",SECONDARY,False,38))
        self.body.add_widget(self.lab("شماره صندلی کلاس","13sp",PRIMARY,True,38,True))
        self.body.add_widget(self.lab(f"دانش‌آموز {self.sname(s)}، شماره صندلی کلاسی شما {seat} است.","11sp",WHITE,True,52,True))
        self.body.add_widget(self.lab("در حفظ صندلی خود کوشا باشید؛ در صورت آسیب به صندلی، خسارت آن را پرداخت خواهید کرد.","9sp",SECONDARY,False,60,True))

    def weekly_schedule(self):
        self.clear("برنامه هفتگی")
        role=self.role(); editable=role in {"manager","educational","teacher"}
        self.body.add_widget(self.lab("شنبه تا چهارشنبه | زنگ اول، زنگ دوم، زنگ سوم | برای هر کلاس مستقل","9sp",SECONDARY,False,42,True))
        if editable:
            cls=self.field("کلاس"); day=self.spin("روز",DAYS); period=self.spin("زنگ",list(BELL_LABELS.values())); subject=self.field("درس"); teacher=self.field("نام دبیر")
            for w in (cls,day,period,subject,teacher): self.body.add_widget(w)
            self.body.add_widget(self.btn("ثبت خانه برنامه",lambda *_:self._save_week(cls,day,period,subject,teacher),SUCCESS,46))
        rows=self.rows("weekly_schedule_entries",{"order":"weekday.asc,period.asc","limit":"300"})
        self._week_table(rows)
        if editable and rows:
            self.body.add_widget(self.lab("مدیریت رکوردهای برنامه هفتگی","10sp",PRIMARY,True,38,True))
            for r in rows:
                row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(3))
                label=f"{r.get('class_name') or '—'} | {r.get('weekday') or '—'} | {BELL_LABELS.get(int(r.get('period') or 0), r.get('period') or '—')} | {r.get('subject') or '—'} | {r.get('teacher_name') or '—'}"
                row.add_widget(self.lab(label,"9sp",SECONDARY,False,44,False))
                row.add_widget(self.btn("ویرایش",lambda *_a,x=dict(r):self._edit_week(x),PRIMARY,42))
                row.add_widget(self.btn("حذف",lambda *_a,x=dict(r):self._delete_row("weekly_schedule_entries",x.get("id"),self.weekly_schedule),ERROR,42))
                self.body.add_widget(row)

    def _save_week(self,cls,day,period,subject,teacher):
        p={"class_name":self.val(cls),"weekday":self.val(day),"period":self._period(period),"subject":self.val(subject),
           "teacher_name":self.val(teacher),"academic_year":SCHOOL_YEAR}
        if not p["class_name"] or not p["subject"]: raise ValueError("کلاس و درس الزامی است.")
        self.insert("weekly_schedule_entries",p); self.weekly_schedule()

    def _period(self,w):
        t=self.val(w); return next((k for k,v in BELL_LABELS.items() if v==t),int(t) if t.isdigit() else 1)

    def _edit_week(self,row):
        self.clear("ویرایش برنامه هفتگی")
        cls=self.field("کلاس"); day=self.spin("روز",DAYS); period=self.spin("زنگ",list(BELL_LABELS.values()))
        subject=self.field("درس"); teacher=self.field("نام دبیر")
        cls.text=str(row.get("class_name") or "")
        day.text=fa_display(str(row.get("weekday") or DAYS[0]))
        period.text=fa_display(BELL_LABELS.get(int(row.get("period") or 1),"زنگ اول"))
        subject.text=str(row.get("subject") or ""); teacher.text=str(row.get("teacher_name") or "")
        for w in (cls,day,period,subject,teacher): self.body.add_widget(w)
        self.body.add_widget(self.btn("ذخیره ویرایش",lambda *_:self._update_week(row,cls,day,period,subject,teacher),SUCCESS,48))
        self.body.add_widget(self.btn("انصراف",self.weekly_schedule,SECONDARY,42))

    def _update_week(self,row,cls,day,period,subject,teacher):
        payload={"class_name":self.val(cls),"weekday":self.val(day),"period":self._period(period),
                 "subject":self.val(subject),"teacher_name":self.val(teacher),"academic_year":SCHOOL_YEAR}
        if not payload["class_name"] or not payload["subject"]: raise ValueError("کلاس و درس الزامی است.")
        self.update("weekly_schedule_entries",{"id":"eq."+str(row.get("id"))},payload)
        self.weekly_schedule()

    def _week_table(self,rows):
        g=GridLayout(cols=4,spacing=dp(2),size_hint_y=None)
        g.bind(minimum_height=g.setter("height"))
        for x in ["روز","زنگ اول","زنگ دوم","زنگ سوم"]: g.add_widget(self.lab(x,"9sp",WHITE,True,42,True))
        for d in DAYS:
            g.add_widget(self.lab(d,"9sp",PRIMARY,True,48,True))
            for p in (1,2,3):
                found=next((r for r in rows if r.get("weekday")==d and int(r.get("period") or 0)==p),None)
                txt=(str(found.get("subject") or "—") if found else "—")
                g.add_widget(self.lab(txt,"9sp",SECONDARY,False,54,True))
        self.body.add_widget(g)

    def exam_schedule(self):
        self.clear("برنامه امتحانی")
        role=self.role(); editable=role in {"manager","educational"}
        self.body.add_widget(self.lab("این قسمت در برنامه امتحانی شما نمایش داده خواهد شد.","10sp",PRIMARY,True,42,True))
        if editable:
            subject=self.field("نام درس"); date=self.field("تاریخ آزمون"); start=self.field("زمان شروع"); end=self.field("زمان پایان")
            scope=self.field("بودجه‌بندی"); grade=self.field("پایه / کلاس")
            for w in (subject,date,start,end,scope,grade): self.body.add_widget(w)
            self.body.add_widget(self.btn("ثبت برنامه امتحان",lambda *_:self._save_exam(subject,date,start,end,scope,grade),SUCCESS,46))
        exams=self.rows("exam_schedule",{"order":"exam_date.asc,id.asc","limit":"300"})
        sid=self.student_id()
        seats=self.rows("exam_seat_assignments",{"student_id":"eq."+str(sid),"limit":"300"}) if sid else []
        data=[]
        for i,e in enumerate(exams,1):
            seat=next((x for x in seats if str(x.get("subject") or "")==str(e.get("subject") or "") and str(x.get("exam_date") or "")==str(e.get("exam_date") or "")),{})
            data.append([i,e.get("subject"),e.get("exam_date"),e.get("exam_start_time"),e.get("exam_end_time"),e.get("syllabus_scope") or "—",seat.get("seat_number") or "—"])
        self._table(["ردیف","نام درس","تاریخ آزمون","زمان شروع","زمان پایان","بودجه‌بندی","شماره صندلی"],data)

    def _save_exam(self,subject,date,start,end,scope,grade):
        p={"subject":self.val(subject),"exam_date":self.val(date),"exam_start_time":self.val(start),"exam_end_time":self.val(end),
           "syllabus_scope":self.val(scope),"grade":self.val(grade),"school_year":SCHOOL_YEAR}
        if not p["subject"] or not p["exam_date"]: raise ValueError("درس و تاریخ آزمون الزامی است.")
        self.insert("exam_schedule",p); self.exam_schedule()

    def consent_activity(self,table,title):
        self.clear(title); sid=self.student_id(); name=self.profile().get("display_name") or self.sname(self.student(sid))
        if self.role() not in {"student","parent"}:
            rows=self.rows(table,{"order":"id.desc","limit":"200"})
            self.body.add_widget(self.lab("فهرست ثبت‌نام‌ها و وضعیت تأیید","10sp",PRIMARY,True,42,True))
            self._table(["شناسه","دانش‌آموز","وضعیت","تاریخ"],[[r.get("id"),r.get("student_name") or r.get("student_id"),r.get("status"),r.get("created_at") or "—"] for r in rows]); return
        text=f"اینجانب {name} تمایل خود را برای ثبت‌نام در {title} اعلام می‌کنم."
        self.body.add_widget(self.lab(text,"13sp",PRIMARY,True,100,True))
        self.body.add_widget(self.btn("ثبت و تأیید",lambda *_:self._confirm_consent(table,title,sid,name),SUCCESS,52))

    def _confirm_consent(self,table,title,sid,name):
        p={"student_id":sid,"student_name":name,"status":"confirmed"}
        if table=="khwarizmi_registrations": p.update({"title":title,"category":"جشنواره"})
        self.insert(table,p); self.status.text=fa_display("ثبت و تأیید انجام شد."); self.status.color=SUCCESS

    def activities(self):
        self.clear("مسابقات و جشنواره‌ها")
        role=self.role(); rows=self.rows("activity_offers",{"active":"eq.true","order":"id.desc","limit":"100"})
        if role in {"student","parent"}:
            if not rows:self.body.add_widget(self.lab("مسابقه یا جشنواره فعالی ثبت نشده است.","10sp",SECONDARY,False,50,True)); return
            self.body.add_widget(self.lab("نوع مسابقه یا جشنواره در هر گزینه مشخص شده است.","9sp",SECONDARY,False,40,True))
            sid=self.student_id(); name=self.profile().get("display_name") or self.sname(self.student(sid))
            for r in rows:
                typ=r.get("category") or "مسابقه"
                self.body.add_widget(self.lab(f"{r.get('title') or '—'} | نوع: {typ}","10sp",PRIMARY,True,42))
                self.body.add_widget(self.btn("ثبت و تأیید",lambda *_a,x=dict(r):self._register_offer(x,sid,name),SUCCESS,42))
        else:
            for r in rows:self.body.add_widget(self.lab(f"{r.get('title')} | نوع: {r.get('category') or '—'} | تاریخ: {r.get('event_date') or '—'}","10sp",SECONDARY,False,40))

    def _register_offer(self,r,sid,name):
        self.insert("activity_registrations",{"activity_id":r.get("id"),"student_id":sid,"competition_type":r.get("category") or "مسابقه","status":"confirmed","student_name":name})
        self.activities()

    def educational_activities(self):
        self.clear("فعالیت‌های پرورشی")
        role=self.role(); rows=self.rows("educational_activities",{"order":"id.desc","limit":"100"})
        if role in {"student","parent"}:
            sid=self.student_id(); name=self.profile().get("display_name") or self.sname(self.student(sid))
            if not rows:self.body.add_widget(self.lab("فعالیتی برای ثبت وجود ندارد.","10sp",SECONDARY,False,50,True)); return
            for r in rows:
                title=r.get("title") or "این فعالیت"
                self.body.add_widget(self.lab(f"اینجانب {name} تمایل خود را برای شرکت در {title} اعلام می‌کنم.","11sp",PRIMARY,True,72,True))
                self.body.add_widget(self.btn("ثبت و تأیید",lambda *_a,x=dict(r):self._register_educational(x,sid),SUCCESS,44))
        else:
            for r in rows:self.body.add_widget(self.lab(f"{r.get('title') or '—'} | {r.get('activity_date') or '—'}","10sp",SECONDARY,False,40))

    def _register_educational(self,r,sid):
        self.insert("educational_activities",{"title":r.get("title"),"student_id":sid,"status":"confirmed","activity_date":self.today(),"description":"ثبت تمایل و تأیید کاربر"})
        self.educational_activities()

    def parent_activities(self):
        self.clear("فعالیت‌های اولیا")
        rows=self.rows("parent_activities",{"order":"id.desc","limit":"100"})
        role=self.role(); name=self.profile().get("display_name") or "اینجانب"
        if role=="parent":
            if not rows:self.body.add_widget(self.lab("فعالیتی برای اولیا آماده نشده است.","10sp",SECONDARY,False,50,True)); return
            for r in rows:
                title=r.get("title") or "این فعالیت"
                self.body.add_widget(self.lab(f"اینجانب {name} تمایل خود را برای شرکت در {title} اعلام می‌کنم.","11sp",PRIMARY,True,72,True))
                self.body.add_widget(self.btn("ثبت و تأیید",lambda *_a,x=dict(r):self._register_parent_activity(x),SUCCESS,44))
        else:
            for r in rows:self.body.add_widget(self.lab(f"{r.get('title') or '—'} | {r.get('activity_type') or '—'} | {r.get('activity_date') or '—'}","10sp",SECONDARY,False,42))

    def _register_parent_activity(self,r):
        self.insert("parent_activities",{"title":r.get("title"),"parent_username":self.profile().get("username") or self.profile().get("national_code"),
                                         "status":"confirmed","activity_date":self.today(),"activity_type":r.get("activity_type"),"consent_text":f"اینجانب {self.profile().get('display_name') or 'ولی'} تمایل خود را برای شرکت در {r.get('title') or 'این فعالیت'} اعلام می‌کنم."})
        self.parent_activities()

    def transport(self):
        self.clear("ثبت سرویس مدرسه")
        role=self.role()
        rows=self.rows("transport_requests",{"order":"id.desc","limit":"100"})
        if role in {"student","parent"}:
            address=self.field("آدرس دقیق محل سکونت",80,True); self.body.add_widget(address)
            self.body.add_widget(self.lab("درخواست سرویس را دارم.","11sp",PRIMARY,True,36,True))
            self.body.add_widget(self.btn("درخواست سرویس را دارم — تأیید و ثبت",lambda *_:self._save_transport(address),SUCCESS,50))
            self._table(["آدرس","وضعیت","تاریخ"],[[r.get("address"),r.get("status"),r.get("created_at")] for r in rows])
        else:
            self._table(["دانش‌آموز","آدرس","وضعیت","تاریخ"],[[r.get("student_id"),r.get("address"),r.get("status"),r.get("created_at")] for r in rows])

    def _save_transport(self,address):
        a=self.val(address)
        if not a: raise ValueError("آدرس دقیق الزامی است.")
        profile=self.profile()
        parent_username=profile.get("national_code") or profile.get("username")
        self.insert("transport_requests",{"student_id":self.student_id(),"parent_username":parent_username,
                                         "address":a,"status":"pending"})
        self.transport()

    def discipline(self):
        self.clear("انضباط")
        role=self.role()
        if role in {"student","parent"}:
            sid=self.student_id(); rows=self.rows("discipline_records",{"student_id":"eq."+str(sid),"status":"eq.confirmed","order":"id.desc","limit":"100"}) if sid else []
            self._table(["مورد انضباطی","تاریخ بی‌انضباطی","مقدار کسر نمره","وضعیت"],[[r.get("title"),r.get("incident_date") or r.get("created_at"),r.get("deduction"),"تأیید شده"] for r in rows]); return
        students=self.rows("students",{"order":"last_name.asc","limit":"300"})
        vals=[f"{s.get('id')} | {self.sname(s)} | {s.get('class_name') or '—'}" for s in students]
        sp=self.spin("انتخاب دانش‌آموز",vals or ["پرونده‌ای نیست"]); typ=self.field("مورد انضباطی، مثلاً تأخیر در ورود به کلاس"); date=self.field("تاریخ بی‌انضباطی"); ded=self.field("مقدار کسر نمره")
        date.text=self.today()
        for w in (sp,typ,date,ded): self.body.add_widget(w)
        self.body.add_widget(self.btn("ثبت مورد انضباطی",lambda *_:self._save_discipline(students,sp,typ,date,ded),SUCCESS,48))
        rows=self.rows("discipline_records",{"order":"id.desc","limit":"100"})
        self._table(["مورد","تاریخ","کسر نمره","وضعیت"],[[r.get("title"),r.get("incident_date") or r.get("created_at"),r.get("deduction"),r.get("status")] for r in rows])
        if role in {"educational","manager"}:
            pending=[r for r in rows if str(r.get("status") or "").lower()=="pending"]
            if pending:
                self.body.add_widget(self.lab("موارد در انتظار تأیید","10sp",PRIMARY,True,38,True))
                for r in pending:
                    self.body.add_widget(self.btn(f"تأیید: {r.get('title') or 'مورد انضباطی'} | دانش‌آموز {r.get('student_id')}",
                        lambda *_a,x=dict(r):self._approve_discipline(x),SUCCESS,44))

    def _save_discipline(self,students,sp,typ,date,ded):
        try:
            idx=list(sp.values).index(sp.text) if sp.text in sp.values else 0
            s=students[idx] if students else {}
            if not s.get("id") or not self.val(typ):
                raise ValueError("دانش‌آموز و مورد انضباطی الزامی است.")
            teacher_id=self.profile().get("teacher_id") or self.profile().get("linked_teacher_id")
            self.insert("discipline_records",{"student_id":s.get("id"),"teacher_id":teacher_id,
                         "title":self.val(typ),"incident_date":self.val(date) or self.today(),
                         "deduction":float(self.val(ded) or 0),"status":"pending",
                         "actor_username":self.profile().get("username"),"actor_role":self.role()})
            self.status.text=fa_display("مورد انضباطی ثبت شد و برای تأیید معاون آموزشی ارسال شد.")
            self.status.color=SUCCESS
            self.discipline()
        except Exception as exc:
            self.status.text=fa_display("ثبت مورد انضباطی انجام نشد: "+str(exc))
            self.status.color=(.8,.15,.15,1)
            print("DISCIPLINE SAVE ERROR:",repr(exc))

    def _approve_discipline(self,row):
        rid=row.get("id")
        if not rid: raise ValueError("شناسه مورد انضباطی مشخص نیست.")
        actor=self.profile().get("username") or self.profile().get("national_code") or ""
        self.update("discipline_records",{"id":"eq."+str(rid)},{"status":"confirmed","actor_username":actor,"actor_role":self.role()})
        self.status.text=fa_display("مورد انضباطی تأیید شد و در سوابق دانش‌آموز قرار گرفت."); self.status.color=SUCCESS
        self.discipline()

    def counseling(self):
        self.clear("پنل مشاوره")
        role=self.role()
        rows=self.rows("counseling_records",{"order":"id.desc","limit":"300"})
        self.body.add_widget(self.lab("پرونده جلسات مشاوره","10sp",PRIMARY,True,40,True))
        self._table(["نام دانش‌آموز","علت مراجعه","تاریخ مراجعه","کارهای انجام شده","جلسه بعدی","پیشرفت","نتیجه"],
                    [[r.get("student_name"),r.get("visit_reason"),r.get("session_date"),r.get("actions_taken"),r.get("next_visit"),r.get("progress"),r.get("result")] for r in rows])
        if role in {"manager","educational","advisor"}:
            self.body.add_widget(self.lab("مدیریت پرونده‌های مشاوره","10sp",PRIMARY,True,36,True))
            for r in rows:
                row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(3))
                row.add_widget(self.lab(f"{r.get('id')} | {r.get('student_name') or '—'} | {r.get('visit_reason') or '—'}","9sp",SECONDARY,False,44,False))
                row.add_widget(self.btn("ویرایش",lambda *_a,x=dict(r):self._edit_counsel(x),PRIMARY,42))
                row.add_widget(self.btn("حذف",lambda *_a,x=dict(r):self._delete_row("counseling_records",x.get("id"),self.counseling),ERROR,42))
                self.body.add_widget(row)
            name=self.field("نام دانش‌آموز"); reason=self.field("علت مراجعه"); date=self.field("تاریخ مراجعه"); actions=self.field("کارهای انجام شده",72,True)
            nxt=self.field("جلسه بعدی"); progress=self.field("پیشرفت",72,True); result=self.field("نتیجه",72,True)
            date.text=self.today()
            for w in (name,reason,date,actions,nxt,progress,result): self.body.add_widget(w)
            self.body.add_widget(self.btn("ثبت جلسه مشاوره",lambda *_:self._save_counsel(name,reason,date,actions,nxt,progress,result),SUCCESS,48))

    def counseling_followups(self):
        self._counsel_simple("پیگیری جلسات مشاوره","counseling_followups",
            ["student_id","subject","description","followup_date","followup_items","decision","status"])

    def educational_followups(self):
        self._counsel_simple("پیگیری آموزشی","educational_followups",
            ["student_id","student_name","class_name","date_shamsi","followup_item","followup_items","note","decision","status"])

    def academic_followups(self):
        self._counsel_simple("پیگیری درسی","academic_followups",
            ["student_id","student_name","class_name","date_shamsi","followup_item","followup_items","note","decision","status"])

    def counseling_guidance(self):
        self._counsel_simple("هدایت تحصیلی","counseling_guidance",
            ["student_id","guidance_type","recommendation","destination","score","academic_year","status"])

    def counseling_classes(self):
        self._counsel_simple("کلاس‌های مشاوره","counseling_classes",
            ["title","grade","class_name","topic","counselor_id","session_date","status"])

    def student_referrals(self):
        self._counsel_simple("ارجاع دانش‌آموز","student_referrals",
            ["student_id","teacher_id","referral_to","reason","referral_date","status"])

    def counselor_board(self):
        self._counsel_simple("تابلوی مشاور","counselor_board",
            ["title","content","category","published","created_by"])

    def counseling_reports(self):
        self.clear("گزارش‌های مشاوره")
        rows=self.rows("counseling_records",{"order":"id.desc","limit":"300"})
        self.body.add_widget(self.lab(f"تعداد پرونده‌های مشاوره: {len(rows)}","11sp",PRIMARY,True,42,True))
        self._table(["نام دانش‌آموز","علت مراجعه","تاریخ مراجعه","پیشرفت","نتیجه"],
                    [[r.get("student_name"),r.get("visit_reason"),r.get("session_date"),r.get("progress"),r.get("result")] for r in rows])

    def _counsel_simple(self,title,table,fields):
        self.clear(title)
        role=self.role()
        rows=self.rows(table,{"order":"id.desc","limit":"200"})
        self._table(["شناسه"]+fields,[[r.get("id")]+[r.get(k) for k in fields] for r in rows])
        if role not in {"manager","educational","executive","advisor"}: return
        self.body.add_widget(self.lab("مدیریت رکوردهای مشاوره","10sp",PRIMARY,True,36,True))
        for r in rows:
            row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(3))
            preview=" | ".join(str(r.get(k) or "—") for k in fields[:3])
            row.add_widget(self.lab(f"{r.get('id')} | {preview}","9sp",SECONDARY,False,44,False))
            row.add_widget(self.btn("ویرایش",lambda *_a,x=dict(r):self._edit_counsel_simple(title,table,fields,x),PRIMARY,42))
            row.add_widget(self.btn("حذف",lambda *_a,x=dict(r):self._delete_row(table,x.get("id"),self.render_route),ERROR,42))
            self.body.add_widget(row)
        self.body.add_widget(self.lab("ثبت رکورد جدید","10sp",PRIMARY,True,36,True))
        widgets=[]
        for k in fields:
            w=self.field(k)
            widgets.append((k,w))
            self.body.add_widget(w)
        self.body.add_widget(self.btn("ثبت",lambda *_:self._save_counsel_simple(table,widgets),SUCCESS,46))

    def _edit_counsel_simple(self,title,table,fields,row):
        self.clear(title + " - ویرایش")
        widgets=[]
        for k in fields:
            w=self.field(k); w.text=str(row.get(k) or "")
            widgets.append((k,w)); self.body.add_widget(w)
        self.body.add_widget(self.btn("ذخیره ویرایش",lambda *_:self._update_counsel_simple(table,row,widgets),SUCCESS,46))
        self.body.add_widget(self.btn("انصراف",self.render_route,SECONDARY,42))

    def _update_counsel_simple(self,table,row,widgets):
        payload={k:self.val(w) for k,w in widgets if self.val(w)}
        self.update(table,{"id":"eq."+str(row.get("id"))},payload)
        self.render_route()

    def _save_counsel_simple(self,table,widgets):
        payload={k:self.val(w) for k,w in widgets if self.val(w)}
        self.insert(table,payload)
        self.render_route()

    def _edit_counsel(self,row):
        self.clear("ویرایش پرونده مشاوره")
        name=self.field("نام دانش‌آموز"); reason=self.field("علت مراجعه"); date=self.field("تاریخ مراجعه")
        actions=self.field("کارهای انجام شده",72,True); nxt=self.field("جلسه بعدی")
        progress=self.field("پیشرفت",72,True); result=self.field("نتیجه",72,True)
        for w,v in ((name,row.get("student_name")),(reason,row.get("visit_reason")),(date,row.get("session_date")),(actions,row.get("actions_taken")),(nxt,row.get("next_visit")),(progress,row.get("progress")),(result,row.get("result"))):
            w.text=str(v or ""); self.body.add_widget(w)
        self.body.add_widget(self.btn("ذخیره ویرایش",lambda *_:self._update_counsel(row,name,reason,date,actions,nxt,progress,result),SUCCESS,48))
        self.body.add_widget(self.btn("انصراف",self.counseling,SECONDARY,42))

    def _update_counsel(self,row,name,reason,date,actions,nxt,progress,result):
        if not self.val(name) or not self.val(reason): raise ValueError("نام دانش‌آموز و علت مراجعه الزامی است.")
        self.update("counseling_records",{"id":"eq."+str(row.get("id"))},{"student_name":self.val(name),"visit_reason":self.val(reason),"session_date":self.val(date) or self.today(),"actions_taken":self.val(actions),"next_visit":self.val(nxt),"progress":self.val(progress),"result":self.val(result)})
        self.counseling()

    def _save_counsel(self,name,reason,date,actions,nxt,progress,result):
        if not self.val(name) or not self.val(reason): raise ValueError("نام دانش‌آموز و علت مراجعه الزامی است.")
        self.insert("counseling_records",{"student_name":self.val(name),"visit_reason":self.val(reason),"session_date":self.val(date) or self.today(),
                    "actions_taken":self.val(actions),"next_visit":self.val(nxt),"progress":self.val(progress),"result":self.val(result),"status":"active"})
        self.counseling()

    def messages(self):
        self.clear("صندوق پیام‌ها")
        p=self.profile(); role=self.role()
        sender=str(p.get("email") or getattr(getattr(self.app_state,"user",{}),"email","") or p.get("username") or "").strip()
        sender_name=self.sname(p) if p.get("first_name") or p.get("last_name") else str(p.get("display_name") or p.get("username") or sender)
        self.body.add_widget(self.lab("ارسال پیام مستقیم به یک گیرنده","11sp",PRIMARY,True,40,True))
        receiver=self.field("ایمیل / شناسه کاربری گیرنده")
        title=self.field("عنوان پیام")
        body=self.field("متن پیام",110,True)
        for w in (receiver,title,body): self.body.add_widget(w)
        self.body.add_widget(self.btn("ارسال پیام",lambda *_:self._send_message(sender,sender_name,receiver,title,body),SUCCESS,48))
        self.body.add_widget(self.lab("پیام‌های ارسالی و دریافتی","11sp",PRIMARY,True,40,True))
        params={"order":"id.desc","limit":"100"}
        if sender:
            params["or"]=f"(sender.eq.{sender},receiver.eq.{sender})"
        rows=self.rows("messages",params)
        self._table(["فرستنده","گیرنده","عنوان","متن","تاریخ"],
                    [[r.get("sender"),r.get("receiver"),r.get("title") or "—",r.get("body") or r.get("text") or "—",r.get("created_at")] for r in rows])

    def _send_message(self,sender,sender_name,receiver,title,body):
        to=self.val(receiver); subject=self.val(title); text=self.val(body)
        if not sender or not to or not text:
            raise ValueError("گیرنده و متن پیام الزامی است.")
        payload={"sender":sender,"receiver":to,"text":text,"sender_user_id":self.profile().get("user_id"),
                 "sender_name":sender_name,"title":subject,"body":text,"audience_type":"direct","audience_value":to}
        self.insert("messages",payload)
        self.messages()

    def attendance(self):
        self.clear("حضور و غیاب")
        role=self.role()
        if role=="teacher": return self.attendance_teacher()
        if role in {"educational","executive","manager"}: return self.attendance_approval()
        sid=self.student_id()
        rows=self.rows("attendance",{"student_id":"eq."+str(sid),"approval_status":"eq.approved","order":"attendance_date.desc","limit":"100"}) if sid else []
        self.body.add_widget(self.lab("سوابق فقط پس از تأیید معاون آموزشی نمایش داده می‌شود.","10sp",PRIMARY,True,44,True))
        self._table(["تاریخ","درس","کلاس","وضعیت"],[[r.get("attendance_date") or r.get("date"),r.get("subject"),r.get("class_name"),r.get("status")] for r in rows])

    def attendance_teacher(self):
        teacher_id=self.profile().get("teacher_id") or self.profile().get("linked_teacher_id")
        classes=self.rows("teacher_classes",{"teacher_id":"eq."+str(teacher_id or 0),"limit":"100"})
        self.body.add_widget(self.lab("برای هر کلاس و زنگ، فهرست دانش‌آموزان نمایش داده می‌شود و با یک ثبت نهایی ارسال می‌گردد.","9sp",SECONDARY,False,52,True))
        if not classes:
            self.body.add_widget(self.lab("کلاسی برای این دبیر تعریف نشده است.","10sp",SECONDARY,False,50,True))
            return
        for class_row in classes:
            current_class=dict(class_row)
            self.body.add_widget(
                self.lab(
                    f"{current_class.get('class_name') or 'کلاس'} | {current_class.get('subject') or 'درس'}",
                    "11sp",PRIMARY,True,36,True
                )
            )
            self.body.add_widget(
                self.btn(
                    "ثبت حضور این کلاس",
                    lambda *_a, selected=current_class:self.attendance_roster(selected),
                    SUCCESS,42
                )
            )

    def attendance_roster(self,c):
        self.clear("ثبت حضور و غیاب")
        cls=c.get("class_name") or ""; subject=c.get("subject") or ""
        students=self.rows("students",{"class_name":"eq."+cls,"order":"last_name.asc","limit":"300"})
        period=self.spin("انتخاب زنگ",list(BELL_LABELS.values()))
        self.body.add_widget(self.lab(f"{cls} | {subject}","12sp",PRIMARY,True,38,True)); self.body.add_widget(period)
        selects=[]
        for s in students:
            row=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(4))
            row.add_widget(self.lab(self.sname(s),"10sp",SECONDARY,True,40))
            sp=self.spin("حاضر",["حاضر","غایب"]); row.add_widget(sp); selects.append((s,sp)); self.body.add_widget(row)
        self.body.add_widget(self.btn("ثبت نهایی همه برای تأیید معاون آموزشی",lambda *_:self._submit_attendance(cls,subject,period,selects),SUCCESS,50))
        self.body.add_widget(self.btn("بازگشت",self.attendance,SECONDARY,42))

    def _submit_attendance(self,cls,subject,period,selects):
        p=self._period(period); teacher=self.profile().get("teacher_id") or self.profile().get("linked_teacher_id")
        batch=self.api().table_insert("attendance_batches",{"class_name":cls,"subject":subject,"period":p,"attendance_date":self.today(),"teacher_id":teacher,"status":"pending","submitted_at":datetime.now().isoformat()})
        if isinstance(batch,list) and batch: bid=batch[0].get("id")
        elif isinstance(batch,dict): bid=batch.get("id")
        else: bid=None
        if not bid: raise RuntimeError("شماره ثبت حضور ایجاد نشد.")
        items=[]
        for s,sp in selects:
            status="present" if self.val(sp)=="حاضر" else "absent"
            items.append({"batch_id":bid,"student_id":s.get("id"),"teacher_id":teacher,"subject":subject,"class_name":cls,
                          "attendance_date":self.today(),"date":self.today(),"status":status,"approval_status":"pending"})
        if items:self.api().table_insert("attendance",items)
        self.status.text=fa_display("حضور و غیاب برای تأیید معاون آموزشی ارسال شد."); self.status.color=SUCCESS
        self.attendance()

    def attendance_approval(self):
        batches=self.rows("attendance_batches",{"status":"eq.pending","order":"id.desc","limit":"100"})
        if not batches:self.body.add_widget(self.lab("موردی در انتظار تأیید نیست.","10sp",SECONDARY,False,50,True)); return
        for b in batches:
            self.body.add_widget(self.lab(f"{b.get('class_name')} | {b.get('subject')} | {b.get('attendance_date')} | {BELL_LABELS.get(int(b.get('period') or 0), 'زنگ '+str(b.get('period')))}","10sp",PRIMARY,True,42))
            self.body.add_widget(self.btn("تأیید و ارسال برای اولیا",lambda *_a,x=dict(b):self._approve_batch(x),SUCCESS,44))

    def _approve_batch(self,b):
        now=datetime.now().isoformat(); actor=self.profile().get("username") or self.profile().get("national_code")
        self.update("attendance_batches",{"id":"eq."+str(b.get("id"))},{"status":"approved","approved_at":now,"approved_by":actor})
        self.update("attendance",{"batch_id":"eq."+str(b.get("id"))},{"approval_status":"approved","approved_at":now,"approved_by":actor})
        self.attendance()

    def _table(self,headers,rows):
        if not rows:
            self.body.add_widget(self.lab("رکوردی برای نمایش وجود ندارد.","10sp",SECONDARY,False,44,True)); return
        g=GridLayout(cols=len(headers),spacing=dp(1),size_hint_y=None)
        g.bind(minimum_height=g.setter("height"))
        for h in headers:g.add_widget(self.lab(h,"8sp",WHITE,True,42,True))
        for row in rows:
            for x in row:g.add_widget(self.lab(str(x if x not in (None,"") else "—")[:45],"8sp",SECONDARY,False,46,True))
        self.body.add_widget(g)

    def back(self,*_):
        if self.manager:self.manager.current="panel"
