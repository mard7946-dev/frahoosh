from datetime import datetime
from io import BytesIO
from pathlib import Path
import random
import requests
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME, SCHOOL_YEAR
from mobile.ui import font_name, fa_display, PersianTextInput

ALIASES={"management":"manager","manager":"manager","مدیر":"manager","مدیریت":"manager","educational":"educational","معاون آموزشی":"educational","معاونت آموزشی":"educational","executive":"executive","معاون اجرایی":"executive","معاونت اجرایی":"executive","cultural":"cultural","معاون پرورشی":"cultural","معاونت پرورشی":"cultural","advisor":"advisor","counselor":"advisor","مشاور":"advisor","مشاوره":"advisor","teacher":"teacher","teachers":"teacher","دبیر":"teacher","student":"student","دانش‌آموز":"student","دانش آموز":"student","parent":"parent","parents":"parent","ولی":"parent","اولیا":"parent","accountant":"finance","حسابدار":"finance","حسابدار مدرسه":"finance"}

def role_of(state):
    p=str(getattr(state,"panel_role","") or "").strip().lower()
    if p:
        p=p.replace("\u200c"," ")
        for k,v in ALIASES.items():
            if k in p:return v
    prof=getattr(state,"profile",{}) or {}
    for value in (prof.get("role"),prof.get("user_role"),prof.get("school_role"),getattr(state,"role",None)):
        raw=str(value or "").strip().lower().replace("\u200c"," ")
        if raw:
            for k,v in ALIASES.items():
                if k in raw:return v
    return "student"

class OpsBase(Screen):
    def __init__(self,app_state=None,mode="",**kw):
        super().__init__(**kw); self.app_state=app_state; self.mode=mode; self._shell()
    def api(self):
        api=getattr(self.app_state,"api",None)
        if api is None: raise RuntimeError("اتصال پایگاه داده آماده نیست.")
        return api
    def insert(self,table,payload):
        try:
            result=self.api().table_insert(table,payload)
            self.status.text=fa_display("اطلاعات با موفقیت در پایگاه داده ذخیره شد."); self.status.color=SUCCESS
            return result
        except Exception as exc:
            self.status.text=fa_display("ذخیره در پایگاه داده انجام نشد: "+str(exc)); self.status.color=ERROR
            print("OPS INSERT ERROR",table,repr(exc)); return None
    def update(self,table,filters,payload):
        try:
            result=self.api().table_update(table,filters,payload)
            self.status.text=fa_display("ویرایش در پایگاه داده ذخیره شد."); self.status.color=SUCCESS
            return result
        except Exception as exc:
            self.status.text=fa_display("ویرایش در پایگاه داده انجام نشد: "+str(exc)); self.status.color=ERROR
            print("OPS UPDATE ERROR",table,repr(exc)); return None
    def delete_row(self,table,filters):
        try:
            result=self.api().table_delete(table,filters)
            self.status.text=fa_display("رکورد از پایگاه داده حذف شد."); self.status.color=SUCCESS
            return result
        except Exception as exc:
            self.status.text=fa_display("حذف از پایگاه داده انجام نشد: "+str(exc)); self.status.color=ERROR
            print("OPS DELETE ERROR",table,repr(exc)); return None
    def val(self,w):
        return w.get_logical_text().strip() if hasattr(w,"get_logical_text") else str(getattr(w,"text","") or "").strip()
    def lab(self,t,size="11sp",color=SECONDARY,b=False,h=40,center=False):
        w=Label(text=fa_display(str(t)),font_name=font_name(),font_size=size,color=color,bold=b,halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(h)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w
    def btn(self,t,cb,color=PRIMARY,h=44):
        b=Button(text=fa_display(t),font_name=font_name(),font_size="11sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(h)); b.bind(on_release=cb); return b
    def field(self,h,hgt=46,m=False):
        return PersianTextInput(hint_text=fa_display(h),font_name=font_name(),font_size="11sp",halign="right",multiline=m,size_hint_y=None,height=dp(hgt))
    def spinner(self,h,values):
        return Spinner(text=fa_display(h),values=tuple(fa_display(x) for x in values),font_name=font_name(),font_size="11sp",size_hint_y=None,height=dp(46))
    def _shell(self):
        root=BoxLayout(orientation="vertical",padding=dp(9),spacing=dp(6)); head=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        head.add_widget(self.btn("بازگشت",self.back,SECONDARY,42)); self.title=self.lab("مرکز عملیاتی","18sp",PRIMARY,True,42,True); head.add_widget(self.title); head.add_widget(self.btn("داشبورد",self.dashboard,PRIMARY,42)); root.add_widget(head)
        self.status=self.lab("آماده","9sp",SUCCESS,True,30,True); root.add_widget(self.status)
        sc=ScrollView(do_scroll_x=False); self.body=BoxLayout(orientation="vertical",spacing=dp(6),padding=dp(3),size_hint_y=None); self.body.bind(minimum_height=self.body.setter("height")); sc.add_widget(self.body); root.add_widget(sc); self.add_widget(root)
    def on_pre_enter(self,*_): self.load()
    def load(self):
        self.body.clear_widgets()
        fn={"activities":self.activities,"counseling":self.counseling,"schedule":self.schedule,"exam_schedule":self.exam_schedule,"discipline":self.discipline,"smart_board":self.smart_board,"cards":self.cards}.get(self.mode)
        if not fn:self.status.text=fa_display("ماژول عملیاتی ناشناخته است"); self.status.color=ERROR; return
        try:
            fn()
            self._append_real_tables()
        except Exception as e:self.status.text=fa_display("خطا: "+str(e)); self.status.color=ERROR
    def _append_real_tables(self):
        """Every operational center ends with a real database table.
        Forms remain specialized; this view makes the persisted records visible
        immediately instead of presenting a form-only/decorative module.
        """
        table_map={
            "activities":[
                ("activity_programs","تعریف فعالیت‌ها"),
                ("cultural_competitions","مسابقات فرهنگی"),
                ("art_competitions","مسابقات هنری"),
                ("sport_competitions","مسابقات ورزشی"),
                ("activity_registrations","ثبت‌نام فعالیت‌ها"),
                ("student_council","شورای دانش‌آموزی"),
                ("basij_registration","بسیج دانش‌آموزی"),
                ("school_ally","همیار مدرسه"),
                ("school_mayor","شهردار مدرسه"),
                ("morning_leaders","مکبر"),
                ("qari_registration","قاری"),
            ],
            "counseling":[
                ("counseling_records","پرونده‌های مشاوره"),
                ("counseling_followups","پیگیری جلسات"),
                ("counseling_guidance","هدایت تحصیلی"),
                ("student_referrals","ارجاعات"),
                ("counselor_board","تابلوی مشاوره"),
            ],
            "schedule":[("weekly_schedule","برنامه هفتگی"),("generated_weekly_schedule","برنامه تولیدشده")],
            "exam_schedule":[("exam_schedule","برنامه امتحانات"),("exam_seat_assignments","شماره صندلی امتحانات")],
            "discipline":[("discipline_records","سوابق انضباطی")],
            "smart_board":[
                ("smart_board_content","محتوای تابلو"),
                ("smart_board_activities","فعالیت‌های تابلو"),
                ("smart_board_quizzes","آزمونک‌های تابلو"),
                ("smart_board_whiteboards","تخته‌های آموزشی"),
            ],
            "cards":[("class_seat_assignments","شماره صندلی کلاسی"),("exam_seat_assignments","شماره صندلی امتحانی")],
        }
        for table,title in table_map.get(self.mode,[]):
            try:
                rows=self.api().table_select(table,{"order":"id.desc","limit":"50"}) or []
            except Exception as exc:
                self.body.add_widget(self.lab(f"{title}: خطا در دریافت اطلاعات — {exc}","9sp",ERROR,True,40,True))
                continue
            self.body.add_widget(self.lab(f"جدول واقعی | {title}","13sp",PRIMARY,True,36,True))
            if not rows:
                self.body.add_widget(self.lab("هنوز رکوردی ثبت نشده است.","9sp",SECONDARY,False,30,True))
                continue
            fields=[x[0] for x in self.OPS_FIELDS.get(table,[])]
            if not fields:
                fields=["id","title","status","created_at"]
            # Keep the mobile table readable: show at most six business columns.
            fields=[f for f in fields if f in rows[0] or f=="id"][:6]
            head=BoxLayout(size_hint_y=None,height=dp(38),spacing=dp(2))
            for f in fields:
                head.add_widget(self.lab({"id":"شناسه","title":"عنوان","status":"وضعیت","created_at":"تاریخ ثبت"}.get(f,f),"8sp",WHITE,True,34,True))
            self.body.add_widget(head)
            for row in rows[:50]:
                line=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(2))
                for f in fields:
                    val=str(row.get(f) or "—")
                    line.add_widget(self.lab(val[:42],"8sp",SECONDARY,False,40,True))
                self.body.add_widget(line)

    def back(self,*_):
        if self.manager:self.manager.current="panel"
    def dashboard(self,*_):
        if self.manager:self.manager.current="dashboard"
    def students(self):
        return self.api().table_select("students",{"order":"last_name.asc","limit":"500"}) or []
    def student_id(self):
        p=getattr(self.app_state,"profile",{}) or {}; sid=p.get("linked_student_id") or p.get("student_id")
        if sid:return int(sid)
        n=str(getattr(self.app_state,"national_code","") or ""); rows=self.api().table_select("students",{"national_code":"eq."+n,"limit":"1"}) or []
        return int(rows[0]["id"]) if rows else None
    def sname(self,s): return (" ".join(str(s.get(k) or "").strip() for k in ("first_name","last_name")).strip() or "دانش‌آموز")
    OPS_FIELDS = {
        "activity_programs":[("title","عنوان"),("activity_key","کلید فعالیت"),("category","دسته‌بندی"),("amount","هزینه"),("active","فعال")],
        "cultural_competitions":[("title","عنوان"),("category","دسته‌بندی"),("start_date","تاریخ شروع"),("end_date","تاریخ پایان"),("status","وضعیت"),("description","توضیحات")],
        "art_competitions":[("title","عنوان"),("category","دسته‌بندی"),("start_date","تاریخ شروع"),("end_date","تاریخ پایان"),("registration_start_shamsi","شروع ثبت‌نام"),("registration_end_shamsi","پایان ثبت‌نام"),("status","وضعیت"),("description","توضیحات")],
        "sport_competitions":[("title","عنوان"),("category","دسته‌بندی"),("sport_type","رشته ورزشی"),("participation_type","نوع مشارکت"),("start_date","تاریخ شروع"),("end_date","تاریخ پایان"),("registration_start_shamsi","شروع ثبت‌نام"),("registration_end_shamsi","پایان ثبت‌نام"),("fixed_amount","مبلغ"),("status","وضعیت"),("description","توضیحات")],
        "activity_registrations":[("participation_type","نوع مشارکت"),("team_members","اعضای گروه"),("competition_type","نوع مسابقه"),("payment_status","وضعیت پرداخت"),("status","وضعیت")],
        "student_council":[("position","سمت پیشنهادی"),("election_date","تاریخ انتخابات"),("votes","تعداد رأی"),("status","وضعیت")],
        "basij_registration":[("registration_date","تاریخ ثبت‌نام"),("note","توضیحات"),("status","وضعیت")],
        "school_ally":[("responsibility","مسئولیت"),("start_date","تاریخ شروع"),("end_date","تاریخ پایان"),("status","وضعیت")],
        "school_mayor":[("election_date","تاریخ انتخابات"),("votes","تعداد رأی"),("status","وضعیت")],
        "morning_leaders":[("role","نقش"),("ceremony_date","تاریخ مراسم"),("status","وضعیت")],
        "qari_registration":[("ceremony_date","تاریخ مراسم"),("status","وضعیت")],
        "counseling_records":[("title","عنوان جلسه"),("visit_reason","علت مراجعه"),("description","شرح جلسه"),("recommendations","توصیه‌ها"),("next_visit","پیگیری بعدی"),("status","وضعیت")],
        "counseling_followups":[("subject","موضوع"),("description","شرح"),("followup_date","تاریخ پیگیری"),("followup_items","موارد پیگیری"),("decision","تصمیم"),("status","وضعیت")],
        "counseling_guidance":[("grade","پایه"),("interest","علاقه‌مندی"),("aptitude","استعداد"),("recommendation","پیشنهاد"),("status","وضعیت")],
        "student_referrals":[("referral_to","ارجاع به"),("reason","علت"),("referral_date","تاریخ ارجاع"),("status","وضعیت")],
        "weekly_schedule":[("teacher","دبیر"),("teacher_id","شناسه دبیر"),("subject","درس"),("grade","پایه"),("class_names","کلاس‌ها"),("class_count","تعداد کلاس"),("hours","ساعت هفتگی"),("weekdays","روزهای هفته"),("bell_pattern","زنگ")],
        "exam_schedule":[("subject","درس"),("grade","پایه"),("start_date","شروع بازه"),("end_date","پایان بازه"),("weight","ضریب"),("exam_date","تاریخ امتحان"),("duration","مدت"),("exam_start_time","شروع"),("exam_end_time","پایان")],
        "discipline_records":[("title","مورد انضباطی"),("description","شرح"),("note","تصمیم/یادداشت"),("priority","اولویت"),("status","وضعیت")],
        "smart_board_content":[("title","عنوان"),("content","محتوا"),("content_date_shamsi","تاریخ نمایش"),("audience_type","مخاطبان"),("active","فعال")]
    }

    def _edit_record(self,table,row,fields,title=None):
        table=str(table)
        fields=fields or self.OPS_FIELDS.get(table,[])
        if not fields:
            self.status.text=fa_display("برای این رکورد فرم ویرایش تخصصی تعریف نشده است."); self.status.color=ERROR; return
        widgets={}
        self.body.clear_widgets()
        self.title.text=fa_display(title or "ویرایش رکورد")
        self.body.add_widget(self.lab("این ویرایش مستقیماً روی همان رکورد Supabase انجام می‌شود.","10sp",SECONDARY,False,40,True))
        for key,label in fields:
            w=self.field(label,72 if key in {"description","content","note","recommendations","team_members"} else 46,key in {"description","content","note","recommendations","team_members"})
            value=row.get(key)
            if value is not None: w.text=str(value)
            widgets[key]=w
            self.body.add_widget(self.lab(label,"9sp",PRIMARY,True,24))
            self.body.add_widget(w)
        def save(_):
            payload={k:self.val(w) for k,w in widgets.items()}
            if table in {"activity_programs"}:
                try: payload["amount"]=int(payload.get("amount") or 0)
                except: payload["amount"]=0
                payload["active"]=str(payload.get("active") or "").lower() not in {"0","false","خیر","غیرفعال"}
            if table in {"weekly_schedule"}:
                try: payload["class_count"]=int(payload.get("class_count") or 1); payload["hours"]=float(payload.get("hours") or 0)
                except: pass
            if table=="exam_schedule":
                try: payload["duration"]=int(payload.get("duration") or 60)
                except: payload["duration"]=60
            try:
                self.update(table,{"id":"eq."+str(row.get("id"))},payload)
                self.status.text=fa_display("ویرایش در پایگاه داده ذخیره شد."); self.status.color=SUCCESS
                self.load()
            except Exception as exc:
                self.status.text=fa_display("ویرایش ذخیره نشد: "+str(exc)); self.status.color=ERROR
        self.body.add_widget(self.btn("ذخیره ویرایش واقعی",save,SUCCESS,50))
        self.body.add_widget(self.btn("انصراف",lambda *_:self.load(),SECONDARY,42))

    def _delete_record(self,table,row):
        try:
            self.delete_row(table,{"id":"eq."+str(row.get("id"))})
            self.status.text=fa_display("رکورد از پایگاه داده حذف شد."); self.status.color=SUCCESS
            self.load()
        except Exception as exc:
            self.status.text=fa_display("حذف انجام نشد: "+str(exc)); self.status.color=ERROR

    def _record_card(self,table,row,summary,editable=True):
        card=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(92),padding=dp(6),spacing=dp(3))
        card.add_widget(self.lab(summary,"9sp",SECONDARY,False,40,True))
        if editable:
            actions=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(4))
            actions.add_widget(self.btn("ویرایش",lambda *_:self._edit_record(table,dict(row)),PRIMARY,38))
            actions.add_widget(self.btn("حذف",lambda *_:self._delete_record(table,dict(row)),ERROR,38))
            card.add_widget(actions)
        self.body.add_widget(card)

    def form(self,fields,save,title):
        self.body.clear_widgets(); self.title.text=fa_display(title); w={}
        for k,h in fields:
            x=self.field(h,72 if k in {"description","body","content","report","recommendation"} else 46,k in {"description","body","content","report","recommendation"}); w[k]=x; self.body.add_widget(self.lab(h,"9sp",PRIMARY,True,24)); self.body.add_widget(x)
        self.body.add_widget(self.btn("ثبت اطلاعات واقعی",lambda *_:save(w),SUCCESS,50)); self.body.add_widget(self.btn("بازگشت",lambda *_:self.load(),SECONDARY,42)); return w

class OperationalCenterScreen(OpsBase):
    def activities(self):
        self.title.text=fa_display("ثبت‌نام مسابقات، اردوها و فعالیت‌ها"); role=role_of(self.app_state)
        self.body.add_widget(self.lab("ثبت‌ها مستقیماً در جداول تخصصی Supabase ذخیره می‌شوند.", "10sp", SECONDARY,False,48,True))
        if role in {"manager","cultural","educational","executive","advisor"}:
            self.body.add_widget(self.btn("＋ تعریف اردو / جشنواره / فعالیت",lambda *_:self.activity_form(),SUCCESS,46))
            for table,title in (("cultural_competitions","مسابقه فرهنگی"),("art_competitions","مسابقه هنری"),("sport_competitions","مسابقه ورزشی")):
                self.body.add_widget(self.btn("＋ "+title,lambda *_ ,t=table,n=title:self.competition_form(t,n),PRIMARY,42))
            self.staff_list()
        else:self.student_register()
    def activity_form(self):
        self.form([("title","عنوان فعالیت / اردو / جشنواره"),("activity_key","کلید فعالیت"),("category","دسته‌بندی"),("amount","هزینه"),("active","فعال؟")],self.save_activity,"تعریف فعالیت")
    def save_activity(self,w):
        p={k:self.val(v) for k,v in w.items()}
        try:p["amount"]=int(p.get("amount") or 0)
        except:p["amount"]=0
        p["active"]=str(p.get("active") or "بله") not in {"خیر","0","false"}; self.insert("activity_programs",p); self.load()
    def competition_form(self,table,title):
        def save(w):
            p={k:self.val(v) for k,v in w.items()}
            p["status"]="active"
            if table=="sport_competitions":p["sport_type"]=p.get("category","")
            self.insert(table,p); self.load()
        fields=[("title","عنوان مسابقه"),("category","دسته‌بندی"),("start_date","تاریخ شروع"),("end_date","تاریخ پایان"),("description","توضیحات")];
        if table in {"art_competitions","sport_competitions"}: fields += [("registration_start_shamsi","شروع ثبت‌نام"),("registration_end_shamsi","پایان ثبت‌نام")]
        self.form(fields,save,title)
    def student_register(self):
        sid=self.student_id()
        if not sid:self.body.add_widget(self.lab("پرونده دانش‌آموز پیدا نشد.","11sp",ERROR,True,50,True));return
        programs=self.api().table_select("activity_programs",{"active":"eq.true","order":"id.desc","limit":"100"}) or []
        self.body.add_widget(self.lab("ثبت‌نام فعالیت‌ها و اردوها","14sp",PRIMARY,True,38,True))
        current=self.api().table_select("activity_registrations",{"student_id":"eq."+str(sid),"order":"id.desc","limit":"100"}) or []
        if current:
            self.body.add_widget(self.lab("ثبت‌نام‌های فعلی من","12sp",PRIMARY,True,32,True))
            for row in current:
                self.body.add_widget(self.lab(f"#{row.get('id')} | {row.get('competition_type') or '-'} | {row.get('payment_status') or '-'} | {row.get('status') or '-'}","9sp",SECONDARY,False,30))
                self.body.add_widget(self.btn("لغو ثبت‌نام",lambda *_a,x=dict(row):self.cancel_registration(x),ERROR,38))
        for r in programs:
            self.body.add_widget(self.lab(f"{r.get('title') or '-'} | {r.get('category') or '-'} | هزینه {r.get('amount') or 0}","10sp",SECONDARY,False,36)); self.body.add_widget(self.btn("ثبت‌نام",lambda *_a,x=dict(r):self.reg_program(x),SUCCESS,40))
        for table,label in (("cultural_competitions","مسابقه فرهنگی"),("art_competitions","مسابقه هنری"),("sport_competitions","مسابقه ورزشی")):
            for r in self.api().table_select(table,{"order":"id.desc","limit":"50"}) or []:
                self.body.add_widget(self.lab(f"{label}: {r.get('title') or '-'}","10sp",SECONDARY,False,34)); self.body.add_widget(self.btn("ثبت‌نام مسابقه",lambda *_a,x=dict(r):self.reg_comp(x),SUCCESS,40))
        simple_specs = (
            ("student_council","شورای دانش‌آموزی",[("position","سمت پیشنهادی"),("election_date","تاریخ انتخابات")]),
            ("basij_registration","بسیج دانش‌آموزی",[("registration_date","تاریخ ثبت‌نام"),("note","توضیحات")]),
            ("school_ally","همیار مدرسه",[("responsibility","مسئولیت"),("start_date","تاریخ شروع"),("end_date","تاریخ پایان")]),
            ("school_mayor","شهردار مدرسه",[("election_date","تاریخ انتخابات")]),
            ("morning_leaders","مکبر",[("role","نقش"),("ceremony_date","تاریخ مراسم")]),
            ("qari_registration","قاری برنامه ظهرگاهی",[("ceremony_date","تاریخ مراسم")]),
        )
        for table,label,fields in simple_specs:
            rows = self.api().table_select(table,{"student_id":"eq."+str(sid),"order":"id.desc","limit":"20"}) or []
            self.body.add_widget(self.lab(f"{label} | {len(rows)} ثبت", "11sp", PRIMARY, True, 32, True))
            self.body.add_widget(self.btn("ثبت / درخواست جدید",lambda *_a,t=table,n=label,fs=fields:self.simple_student_form(t,n,fs),SUCCESS,40))
            for row in rows:
                self._record_card(table,dict(row),f"#{row.get('id')} | {label} | وضعیت: {row.get('status') or '-'}",editable=True)
    def cancel_registration(self,row):
        try:
            self.delete_row("activity_registrations",{"id":"eq."+str(row.get("id")),"student_id":"eq."+str(self.student_id())})
            self.status.text=fa_display("ثبت‌نام فعالیت لغو و از پایگاه داده حذف شد."); self.status.color=SUCCESS
            self.load()
        except Exception as exc:
            self.status.text=fa_display("لغو ثبت‌نام انجام نشد: "+str(exc)); self.status.color=ERROR

    def simple_student_form(self,table,label,fields,row=None):
        sid=self.student_id()
        student=(self.api().table_select("students",{"id":"eq."+str(sid),"limit":"1"}) or [{}])[0]
        widgets={}
        self.body.clear_widgets()
        self.title.text=fa_display(label)
        for key,hint in fields:
            w=self.field(hint,72 if key in {"note","description"} else 46,key in {"note","description"})
            if row and row.get(key) is not None: w.text=str(row.get(key))
            widgets[key]=w
            self.body.add_widget(self.lab(hint,"9sp",PRIMARY,True,24))
            self.body.add_widget(w)
        def save(_):
            p={k:self.val(v) for k,v in widgets.items()}
            p.update({"student_id":sid,"student_name":self.sname(student),"status":str((row or {}).get("status") or "pending")})
            if table=="student_council" and not p.get("election_year"): p["election_year"]=SCHOOL_YEAR
            try:
                if row:
                    self.update(table,{"id":"eq."+str(row.get("id")),"student_id":"eq."+str(sid)},p)
                else:
                    self.insert(table,p)
                self.status.text=fa_display("اطلاعات با موفقیت ذخیره شد."); self.status.color=SUCCESS
                self.load()
            except Exception as exc:
                self.status.text=fa_display("ذخیره انجام نشد: "+str(exc)); self.status.color=ERROR
        self.body.add_widget(self.btn("ثبت / ذخیره",save,SUCCESS,48))
        self.body.add_widget(self.btn("بازگشت",lambda *_:self.load(),SECONDARY,42))

    def cancel_simple(self,table,row):
        try:
            self.delete_row(table,{"id":"eq."+str(row.get("id")),"student_id":"eq."+str(self.student_id())})
            self.status.text=fa_display("ثبت‌نام حذف شد."); self.status.color=SUCCESS
            self.load()
        except Exception as exc:
            self.status.text=fa_display("حذف ثبت‌نام انجام نشد: "+str(exc)); self.status.color=ERROR

    def reg_program(self,r):
        sid=self.student_id(); old=self.api().table_select("activity_registrations",{"activity_id":"eq."+str(r["id"]),"student_id":"eq."+str(sid),"limit":"1"}) or []
        if old:return
        self.insert("activity_registrations",{"activity_id":r["id"],"student_id":sid,"participation_type":"انفرادی","team_members":"","competition_type":r.get("category") or "فعالیت","payment_status":"pending","status":"active"}); self.status.text=fa_display("ثبت‌نام فعالیت با موفقیت ذخیره شد."); self.status.color=SUCCESS
    def reg_comp(self,r):
        sid=self.student_id(); old=self.api().table_select("activity_registrations",{"student_id":"eq."+str(sid),"competition_type":"eq."+str(r.get("title") or ""),"limit":"1"}) or []
        if old:return
        self.insert("activity_registrations",{"activity_id":r.get("id"),"student_id":sid,"participation_type":"انفرادی","team_members":"","competition_type":r.get("title") or "مسابقه","payment_status":"pending","status":"active"}); self.status.text=fa_display("ثبت‌نام مسابقه ذخیره شد."); self.status.color=SUCCESS
    def reg_simple(self,table,label):
        sid=self.student_id(); old=self.api().table_select(table,{"student_id":"eq."+str(sid),"limit":"1"}) or []
        if old:return
        s=(self.api().table_select("students",{"id":"eq."+str(sid),"limit":"1"}) or [{}])[0]; p={"student_id":sid,"student_name":self.sname(s),"status":"pending"}
        if table=="student_council":p["election_year"]=SCHOOL_YEAR
        if table=="school_ally":p["role"]="همیار"
        if table=="morning_leaders":p.update({"grade":s.get("grade") or "","class_name":s.get("class_name") or "","role":label,"date_shamsi":""})
        self.insert(table,p); self.status.text=fa_display("درخواست ثبت شد."); self.status.color=SUCCESS
    def staff_list(self):
        self.body.add_widget(self.lab("تعریف‌ها و ثبت‌نام‌های واقعی","14sp",PRIMARY,True,38,True))
        for table,label in (("activity_programs","اردو / جشنواره / فعالیت"),("cultural_competitions","مسابقات فرهنگی"),("art_competitions","مسابقات هنری"),("sport_competitions","مسابقات ورزشی")):
            rows=self.api().table_select(table,{"order":"id.desc","limit":"50"}) or []
            self.body.add_widget(self.lab(f"{label}: {len(rows)}","10sp",SECONDARY,False,30))
            for r in rows[:20]:
                self._record_card(table,dict(r),f"#{r.get('id')} | {r.get('title') or '-'} | وضعیت: {r.get('status') or ('فعال' if r.get('active') else '-')}",editable=True)
        for table,label in (("activity_registrations","ثبت‌نام فعالیت‌ها"),("student_council","شورا"),("basij_registration","بسیج"),("school_ally","همیار"),("school_mayor","شهردار"),("morning_leaders","مکبر"),("qari_registration","قاری")):
            rows=self.api().table_select(table,{"order":"id.desc","limit":"50"}) or []
            self.body.add_widget(self.lab(f"{label}: {len(rows)}","10sp",SECONDARY,False,30))
            for r in rows[:30]:
                name=r.get("student_name") or r.get("student_id") or "-"
                self._record_card(table,dict(r),f"#{r.get('id')} | {name} | وضعیت: {r.get('status') or '-'}",editable=True)

class CounselingCenterScreen(OpsBase):
    def counseling(self):
        self.title.text=fa_display("مرکز عملیاتی مشاوره")
        role=role_of(self.app_state)
        self.body.add_widget(self.lab("پرونده مشاوره: دانش‌آموز | علت | تاریخ | اقدامات | جلسه بعد | روند | نتیجه","10sp",SECONDARY,False,48,True))
        if role in {"manager","educational","advisor"}:
            for text,fn in (("＋ ثبت جلسه مشاوره",self.counsel_form),("＋ ثبت پیگیری",self.follow_form),("＋ ثبت هدایت تحصیلی",self.guidance_form),("＋ ثبت ارجاع دانش‌آموز",self.referral_form),("تابلو اعلانات مشاور",self.board_form)):
                self.body.add_widget(self.btn(text,lambda *_a,f=fn:f(),SUCCESS if "ثبت" in text else PRIMARY,44))
            self.list_records()
        else:
            sid=self.student_id()
            for table,label in (("counseling_records","سوابق جلسات"),("counseling_followups","پیگیری‌ها"),("counseling_guidance","هدایت تحصیلی"),("student_referrals","ارجاعات")):
                try:
                    filt={"student_id":"eq."+str(sid),"order":"id.desc","limit":"30"} if sid else {"order":"id.desc","limit":"30"}
                    rows=self.api().table_select(table,filt) or []
                except Exception: rows=[]
                self.body.add_widget(self.lab(f"{label}: {len(rows)}","11sp",PRIMARY,True,34))
                for row in rows:self.body.add_widget(self.lab(f"#{row.get('id')} | {row.get('title') or row.get('subject') or row.get('reason') or row.get('recommendation') or '-'}","9sp",SECONDARY,False,34))
    def picker(self):
        rows=self.students(); vals=[f"{r.get('id')} | {self.sname(r)} | {r.get('grade') or '-'} | {r.get('class_name') or '-'}" for r in rows]; return rows,self.spinner("انتخاب دانش‌آموز",vals or ["پرونده‌ای نیست"])
    def add_picker(self,sp):self.body.add_widget(sp,index=2)
    def counselform(self,fields,save,title):
        rows,sp=self.picker(); w=self.form(fields,lambda x:save(x,rows,sp),title); self.add_picker(sp); return w
    def counsel_form(self):
        self.counselform([("visit_reason","علت مراجعه"),("session_date","تاریخ"),("actions_taken","اقدامات انجام‌شده"),("next_visit","جلسه بعد"),("progress","روند"),("result","نتیجه")],self.save_counsel,"ثبت جلسه مشاوره")
    def save_counsel(self,w,rows,sp):
        i=list(sp.values).index(sp.text) if sp.text in sp.values else 0;s=rows[i] if rows else {};p={k:self.val(v) for k,v in w.items()};p.update({"student_id":s.get("id"),"student_name":self.sname(s),"title":"جلسه مشاوره","description":p.get("actions_taken") or "","recommendations":p.get("result") or "","status":"open"});self.insert("counseling_records",p);self.load()
    def follow_form(self):
        self.counselform([("subject","موضوع پیگیری"),("description","شرح پیگیری"),("followup_date","تاریخ پیگیری"),("followup_items","موارد پیگیری‌شده"),("decision","تصمیم")],self.save_follow,"ثبت پیگیری")
    def save_follow(self,w,rows,sp):
        i=list(sp.values).index(sp.text) if sp.text in sp.values else 0;s=rows[i] if rows else {};p={k:self.val(v) for k,v in w.items()};p.update({"student_id":s.get("id"),"status":"open"});self.insert("counseling_followups",p);self.load()
    def guidance_form(self):
        self.counselform([("grade","پایه"),("interest","علاقه‌مندی"),("aptitude","استعداد"),("recommendation","پیشنهاد هدایت تحصیلی")],self.save_guidance,"هدایت تحصیلی")
    def save_guidance(self,w,rows,sp):
        i=list(sp.values).index(sp.text) if sp.text in sp.values else 0;s=rows[i] if rows else {};p={k:self.val(v) for k,v in w.items()};p["student_id"]=s.get("id");self.insert("counseling_guidance",p);self.load()
    def referral_form(self):
        self.counselform([("referral_to","ارجاع به"),("reason","علت ارجاع"),("status","وضعیت")],self.save_referral,"ارجاع دانش‌آموز")
    def save_referral(self,w,rows,sp):
        i=list(sp.values).index(sp.text) if sp.text in sp.values else 0;s=rows[i] if rows else {};p={k:self.val(v) for k,v in w.items()};p.update({"student_id":s.get("id"),"referral_date":datetime.now().strftime("%Y-%m-%d")});self.insert("student_referrals",p);self.load()
    def board_form(self):self.form([("title","عنوان تابلو مشاور"),("body","متن اطلاعیه"),("created_by","ثبت‌کننده")],self.save_board,"تابلو اعلانات مشاور")
    def save_board(self,w):
        p={k:self.val(v) for k,v in w.items()};p["active"]=True;self.insert("counselor_board",p);self.load()
    def list_records(self):
        for t,n in (("counseling_records","جلسات"),("counseling_followups","پیگیری‌ها"),("counseling_guidance","هدایت تحصیلی"),("student_referrals","ارجاعات")):
            rows=self.api().table_select(t,{"order":"id.desc","limit":"30"}) or []
            self.body.add_widget(self.lab(f"{n}: {len(rows)}","12sp",PRIMARY,True,34))
            if t=="counseling_records":
                self._table(["دانش‌آموز","علت","تاریخ","اقدامات","جلسه بعد","روند","نتیجه"],[
                    [r.get("student_name") or r.get("student_id") or "-",r.get("visit_reason") or "-",r.get("session_date") or "-",r.get("actions_taken") or "-",r.get("next_visit") or "-",r.get("progress") or "-",r.get("result") or "-"]
                    for r in rows[:30]
                ])
                for r in rows[:30]:
                    self._record_card(t,dict(r),f"#{r.get('id')} | {r.get('student_name') or r.get('student_id') or '-'}",editable=True)
            else:
                for r in rows[:30]:
                    self._record_card(t,dict(r),f"#{r.get('id')} | {r.get('student_name') or r.get('student_id') or '-'} | {r.get('title') or r.get('subject') or r.get('reason') or '-'}",editable=True)

class ScheduleCenterScreen(OpsBase):
    def schedule(self):
        self.title.text=fa_display("برنامه هفتگی مدرسه");self.body.add_widget(self.lab("جدول واقعی: شنبه تا چهارشنبه × زنگ ۱ تا ۳ × کلاس × درس × دبیر. هر ردیف مستقل در Supabase ذخیره می‌شود.","10sp",SECONDARY,False,48,True))
        if role_of(self.app_state) in {"manager","educational"}: self.body.add_widget(self.btn("＋ ثبت ردیف برنامه",lambda *_:self.week_form(),SUCCESS,46))
        rows=self.api().table_select("weekly_schedule",{"order":"id.desc","limit":"200"}) or [];self.body.add_widget(self.lab(f"{len(rows)} ردیف ثبت شده","12sp",PRIMARY,True,34))
        for r in rows:
            self._record_card("weekly_schedule",dict(r),f"#{r.get('id')} | {r.get('weekdays') or '-'} | {r.get('bell_pattern') or '-'} | {r.get('class_names') or '-'} | {r.get('subject') or '-'} | {r.get('teacher') or '-'}",editable=role_of(self.app_state) in {"manager","educational"})
    def week_form(self):self.form([("weekdays","روز"),("bell_pattern","زنگ"),("class_names","کلاس"),("subject","درس"),("teacher","دبیر"),("teacher_id","شناسه دبیر"),("grade","پایه")],self.save_week,"ثبت برنامه هفتگی")
    def save_week(self,w):
        p={k:self.val(v) for k,v in w.items()}
        try:p["class_count"]=int(p.get("class_count") or 1);p["hours"]=float(p.get("hours") or 0)
        except:pass
        self.insert("weekly_schedule",p);self.load()
    def exam_schedule(self):
        self.title.text=fa_display("برنامه امتحانات");self.body.add_widget(self.lab("تاریخ، ساعت شروع/پایان و مدت هر امتحان ثبت می‌شود؛ صندلی هر امتحان مستقل و تصادفی است.","10sp",SECONDARY,False,52,True))
        can_edit=role_of(self.app_state) in {"manager","educational"}
        if can_edit:self.body.add_widget(self.btn("＋ ثبت امتحان",lambda *_:self.exam_form(),SUCCESS,46))
        rows=self.api().table_select("exam_schedule",{"order":"exam_date.asc","limit":"200"}) or []
        for r in rows:
            self._record_card("exam_schedule",dict(r),f"#{r.get('id')} | {r.get('subject') or '-'} | پایه {r.get('grade') or '-'} | {r.get('exam_date') or '-'} | {r.get('exam_start_time') or '-'} تا {r.get('exam_end_time') or '-'} | {r.get('duration') or '-'} دقیقه",editable=can_edit)
            if can_edit:
                self.body.add_widget(self.btn("تولید صندلی‌های این امتحان",lambda *_a,x=dict(r):self.make_exam_seats(x),PRIMARY,40))
    def exam_form(self):self.form([("subject","درس"),("grade","پایه"),("start_date","شروع بازه"),("end_date","پایان بازه"),("weight","ضریب"),("exam_date","تاریخ امتحان"),("duration","مدت به دقیقه"),("exam_start_time","ساعت شروع"),("exam_end_time","ساعت پایان")],self.save_exam,"ثبت برنامه امتحانی")
    def save_exam(self,w):
        p={k:self.val(v) for k,v in w.items()}
        try:p["duration"]=int(p.get("duration") or 60)
        except:p["duration"]=60
        self.insert("exam_schedule",p);self.load()
    def make_exam_seats(self,row):
        students=self.api().table_select("students",{"grade":"eq."+str(row.get("grade") or ""),"order":"id.asc","limit":"500"}) or []
        random.Random(str(row.get("id"))).shuffle(students)
        for i,s in enumerate(students,1):
            old=self.api().table_select("exam_seat_assignments",{"exam_id":"eq."+str(row.get("id")),"student_id":"eq."+str(s.get("id")),"limit":"1"}) or [];p={"exam_id":str(row.get("id")),"student_id":s.get("id"),"subject":row.get("subject") or "","exam_date":row.get("exam_date") or "","seat_number":i}
            if old:self.update("exam_seat_assignments",{"id":"eq."+str(old[0]["id"])},p)
            else:self.insert("exam_seat_assignments",p)
        self.status.text=fa_display(f"برای {len(students)} دانش‌آموز صندلی مستقل و تصادفی ثبت شد.");self.status.color=SUCCESS

class DisciplineCenterScreen(OpsBase):
    def discipline(self):
        self.title.text=fa_display("پنل انضباطی مدرسه")
        role=role_of(self.app_state)
        if role not in {"manager","educational","executive","cultural","advisor","teacher"}:
            sid=self.student_id()
            self.body.add_widget(self.lab("سوابق انضباطی پرونده شما","13sp",PRIMARY,True,38,True))
            try:
                filt={"student_id":"eq."+str(sid),"order":"id.desc","limit":"50"} if sid else {"order":"id.desc","limit":"50"}
                rows=self.api().table_select("discipline_records",filt) or []
            except Exception: rows=[]
            if not rows:self.body.add_widget(self.lab("سابقه‌ای ثبت نشده است.","10sp",SECONDARY,False,42,True))
            for r in rows:self.body.add_widget(self.lab(f"#{r.get('id')} | {r.get('title') or '-'} | {r.get('status') or '-'} | {r.get('description') or ''}","9sp",SECONDARY,False,48))
            return
        rows=self.students();vals=[f"{r.get('id')} | {self.sname(r)} | {r.get('grade') or '-'} | {r.get('class_name') or '-'}" for r in rows]
        sp=self.spinner("انتخاب دانش‌آموز",vals or ["پرونده‌ای نیست"]);self.body.add_widget(sp)
        cases=["تأخیر در ورود به کلاس","تأخیر در ورود به دبیرستان","رفتار نامناسب با دانش‌آموزان","عدم استفاده از لباس فرم","موی بلند و نامتعارف","آوردن ابزار غیر دانش‌آموزی","بی‌احترامی به عوامل دبیرستان","آسیب زدن به اموال دبیرستان"]
        typ=self.spinner("علت / مورد انضباطی",cases);self.body.add_widget(typ)
        desc=self.field("شرح / توضیحات",72,True);note=self.field("یادداشت / تصمیم",72,True);self.body.add_widget(desc);self.body.add_widget(note)
        self.body.add_widget(self.btn("ثبت مورد انضباطی",lambda *_:self.save_disc(rows,sp,typ,desc,note),SUCCESS,50))
        self.body.add_widget(self.lab("سوابق اخیر","13sp",PRIMARY,True,36,True))
        for r in self.api().table_select("discipline_records",{"order":"id.desc","limit":"50"}) or []:
            self._record_card("discipline_records",dict(r),f"#{r.get('id')} | دانش‌آموز {r.get('student_id')} | {r.get('title') or '-'} | {r.get('status') or '-'}",editable=True)
    def save_disc(self,rows,sp,typ,desc,note):
        i=list(sp.values).index(sp.text) if sp.text in sp.values else 0;s=rows[i] if rows else {}
        p={"student_id":s.get("id"),"title":str(typ.text or ""),"description":self.val(desc),"note":self.val(note),"priority":"normal","status":"pending","actor_username":str((getattr(self.app_state,"profile",{}) or {}).get("username") or getattr(self.app_state,"national_code","") or ""),"actor_role":role_of(self.app_state),"created_at":datetime.now().isoformat()}
        tid=(getattr(self.app_state,"profile",{}) or {}).get("linked_teacher_id") or (getattr(self.app_state,"profile",{}) or {}).get("teacher_id")
        if tid:p["teacher_id"]=tid
        self.insert("discipline_records",p);self.status.text=fa_display("مورد انضباطی ثبت شد.");self.status.color=SUCCESS

class SmartBoardCenterScreen(OpsBase):
    def smart_board(self):
        self.title.text=fa_display("تابلو هوشمند مدرسه");role=role_of(self.app_state);write=role in {"manager","educational","cultural","advisor"}
        if write:self.body.add_widget(self.btn("＋ ثبت پیام مهم مدرسه",lambda *_:self.board_form(),SUCCESS,48))
        self.body.add_widget(self.lab("پیام‌های فعال مدرسه برای دانش‌آموز و ولی قابل مشاهده هستند.","10sp",SECONDARY,False,44,True))
        rows=self.api().table_select("smart_board_content",{"active":"eq.true","order":"id.desc","limit":"100"}) or []
        for r in rows:
            self._record_card("smart_board_content",dict(r),f"#{r.get('id')} | {r.get('title') or 'اطلاعیه'} | {r.get('content') or ''}",editable=write)
    def board_form(self):self.form([("title","عنوان پیام مهم"),("content","متن پیام"),("content_date_shamsi","تاریخ نمایش")],self.save_board,"انتشار پیام روی تابلو")
    def save_board(self,w):
        p={k:self.val(v) for k,v in w.items()};p.update({"active":True,"audience_type":"student_parent","created_by":str((getattr(self.app_state,"profile",{}) or {}).get("username") or getattr(self.app_state,"national_code","") or "")});self.insert("smart_board_content",p);self.load()

class CardsCenterScreen(OpsBase):
    def cards(self):
        self.title.text=fa_display("کارت دانش‌آموزی و کارت امتحان");role=role_of(self.app_state)
        if role in {"manager","executive","educational"}:
            self.body.add_widget(self.btn("تولید کارت دانش‌آموزی",lambda *_:self.card_picker(False),SUCCESS,46));self.body.add_widget(self.btn("تولید کارت امتحان",lambda *_:self.card_picker(True),PRIMARY,46));self.body.add_widget(self.btn("تولید شماره صندلی کلاسی",lambda *_:self.class_seat_form(),SECONDARY,46))
        else:
            sid=self.student_id()
            if sid:self.body.add_widget(self.btn("دریافت کارت دانش‌آموزی من",lambda *_:self.make_student_card(sid),SUCCESS,46));self.body.add_widget(self.btn("دریافت کارت امتحان من",lambda *_:self.make_exam_card(sid),PRIMARY,46))
        self.body.add_widget(self.lab("کارت دانش‌آموزی: مشخصات هویتی، مدرسه، پایه، کلاس، صندلی کلاسی، QR و محل عکس.","10sp",SECONDARY,False,52,True));self.body.add_widget(self.lab("کارت امتحان: مشخصات هویتی، جدول امتحانات، زمان هر امتحان و صندلی مستقل برای هر امتحان.","10sp",SECONDARY,False,52,True))
    def card_picker(self,exam):
        rows=self.students();vals=[f"{r.get('id')} | {self.sname(r)}" for r in rows];sp=self.spinner("انتخاب دانش‌آموز",vals or ["پرونده‌ای نیست"]);self.body.add_widget(sp);self.body.add_widget(self.btn("ساخت PDF",lambda *_:self.make_exam_card(rows[list(sp.values).index(sp.text)]["id"]) if exam else self.make_student_card(rows[list(sp.values).index(sp.text)]["id"]),SUCCESS,46))
    def class_seat_form(self):
        rows=self.students();classes=sorted(set(str(r.get("class_name") or "").strip() for r in rows if str(r.get("class_name") or "").strip()));sp=self.spinner("انتخاب کلاس",classes or ["کلاسی نیست"]);self.body.add_widget(sp);self.body.add_widget(self.btn("تولید صندلی‌های تصادفی کلاس",lambda *_:self.make_class_seats(sp,rows),SUCCESS,46))
    def make_class_seats(self,sp,rows):
        cls=str(sp.text); roster=[r for r in rows if str(r.get("class_name") or "")==cls];random.Random(f"{cls}|{SCHOOL_YEAR}").shuffle(roster)
        for i,s in enumerate(roster,1):
            old=self.api().table_select("class_seat_assignments",{"student_id":"eq."+str(s["id"]),"academic_year":"eq."+SCHOOL_YEAR,"limit":"1"}) or [];p={"class_id":cls,"student_id":s["id"],"seat_number":i,"academic_year":SCHOOL_YEAR}
            if old:self.update("class_seat_assignments",{"id":"eq."+str(old[0]["id"])},p)
            else:self.insert("class_seat_assignments",p)
        self.status.text=fa_display(f"شماره صندلی {len(roster)} دانش‌آموز کلاس ثبت شد.");self.status.color=SUCCESS
    def student(self,sid):return (self.api().table_select("students",{"id":"eq."+str(sid),"limit":"1"}) or [{}])[0]
    def seat(self,sid):
        a=self.api().table_select("class_seat_assignments",{"student_id":"eq."+str(sid),"academic_year":"eq."+SCHOOL_YEAR,"limit":"1"}) or []
        if a:return a[0].get("seat_number")
        a=self.api().table_select("class_seats",{"student_id":"eq."+str(sid),"limit":"1"}) or [];return a[0].get("seat_no") if a else "-"
    def pdf_font(self):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        base=Path(__file__).resolve().parent.parent/"assets";pdfmetrics.registerFont(TTFont("FrahooshPDF",str(base/"NotoSansArabic-Regular.ttf")));pdfmetrics.registerFont(TTFont("FrahooshPDFB",str(base/"NotoSansArabic-Bold.ttf")))
    def rtl_draw(self,c,t,x,y,size=10,b=False):
        from arabic_reshaper import reshape
        from bidi.algorithm import get_display
        c.setFont("FrahooshPDFB" if b else "FrahooshPDF",size);c.drawRightString(x,y,get_display(reshape(str(t or ""))))
    def qr(self,c,text,x,y,size=72):
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics import renderPDF
        from reportlab.graphics.shapes import Drawing
        q=QrCodeWidget(str(text));q.barWidth=size;q.barHeight=size;d=Drawing(size,size);d.add(q);renderPDF.draw(d,c,x,y)
    def photo(self,c,s,x,y,w,h):
        from reportlab.lib.utils import ImageReader
        v=str(s.get("photo") or "").strip()
        if not v:c.rect(x,y,w,h);self.rtl_draw(c,"محل عکس",x+w-8,y+h/2,10);return
        try:
            data=requests.get(v,timeout=5).content if v.startswith("http") else Path(v).read_bytes();c.drawImage(ImageReader(BytesIO(data)),x,y,w,h,preserveAspectRatio=True,anchor="c")
        except:c.rect(x,y,w,h);self.rtl_draw(c,"محل عکس",x+w-8,y+h/2,10)
    def make_student_card(self,sid):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        self.pdf_font(); s=self.student(sid)
        path=Path(App.get_running_app().user_data_dir)/f"کارت_دانش‌آموزی_{sid}.pdf"
        c=canvas.Canvas(str(path),pagesize=A4); w,h=A4
        c.setLineWidth(1); c.rect(28,h-500,w-56,470)
        self.rtl_draw(c,SCHOOL_NAME,w-50,h-58,17,True); self.rtl_draw(c,"کارت دانش‌آموزی",w-50,h-84,15,True)
        self.rtl_draw(c,f"سال تحصیلی: {SCHOOL_YEAR}",w-50,h-108,9)
        self.photo(c,s,42,h-205,105,115)
        fields=[
            ("نام و نام خانوادگی",self.sname(s)),("نام پدر",s.get("father_name")),
            ("نام مادر",s.get("mother_name")),("کد ملی",s.get("national_code")),
            ("شماره شناسنامه",s.get("birth_certificate_no") or s.get("identity_number")),
            ("تاریخ تولد",s.get("birth_date") or s.get("birth_date_shamsi")),
            ("محل صدور",s.get("birth_certificate_place")),("محل تولد",s.get("birth_place")),
            ("ملیت",s.get("nationality")),("دین",s.get("religion")),("مذهب",s.get("sect")),
            ("شماره تماس دانش‌آموز",s.get("student_phone")),("شماره تماس پدر",s.get("father_phone")),
            ("شماره تماس مادر",s.get("mother_phone")),("پایه",s.get("grade")),
            ("کلاس",s.get("class_name")),("شماره صندلی کلاسی",self.seat(sid))
        ]
        y=h-135; left=175; right=w-50; col=right-285
        for idx,(lab,val) in enumerate(fields):
            x=right if idx%2==0 else col
            yy=y-(idx//2)*30
            self.rtl_draw(c,f"{lab}: {val or '-'}",x,yy,8)
            c.line(x-245,yy-6,x,yy-6)
        self.rtl_draw(c,f"مدرسه: {SCHOOL_NAME}",w-50,h-455,9)
        self.qr(c,f"frahoosh://student/{sid}",w-135,h-470,78)
        c.save(); self.status.text=fa_display("کارت دانش‌آموزی کامل و جدول‌بندی‌شده PDF ساخته شد."); self.status.color=SUCCESS
    def make_exam_card(self,sid):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        self.pdf_font(); s=self.student(sid)
        exams=self.api().table_select("exam_schedule",{"grade":"eq."+str(s.get("grade") or ""),"order":"exam_date.asc","limit":"100"}) or []
        if not exams:self.status.text=fa_display("برنامه امتحانی این پایه هنوز ثبت نشده است.");self.status.color=ERROR;return
        for ex in exams:
            roster=self.api().table_select("students",{"grade":"eq."+str(ex.get("grade") or s.get("grade") or ""),"limit":"500"}) or []
            random.Random(str(ex.get("id"))).shuffle(roster)
            for i,st in enumerate(roster,1):
                old=self.api().table_select("exam_seat_assignments",{"exam_id":"eq."+str(ex.get("id")),"student_id":"eq."+str(st.get("id")),"limit":"1"}) or []
                p={"exam_id":str(ex.get("id")),"student_id":st.get("id"),"subject":ex.get("subject") or "","exam_date":ex.get("exam_date") or "","seat_number":i}
                if old:self.update("exam_seat_assignments",{"id":"eq."+str(old[0]["id"])},p)
                else:self.insert("exam_seat_assignments",p)
        path=Path(App.get_running_app().user_data_dir)/f"کارت_امتحان_{sid}.pdf";c=canvas.Canvas(str(path),pagesize=A4);w,h=A4
        c.setLineWidth(1);c.rect(28,h-610,w-56,580)
        self.rtl_draw(c,SCHOOL_NAME,w-50,h-58,16,True);self.rtl_draw(c,"کارت امتحان",w-50,h-84,15,True);self.rtl_draw(c,f"سال تحصیلی: {SCHOOL_YEAR}",w-50,h-108,9)
        y=h-135
        identity=[("نام و نام خانوادگی",self.sname(s)),("نام پدر",s.get("father_name")),("کد ملی",s.get("national_code")),("شماره شناسنامه",s.get("birth_certificate_no") or s.get("identity_number")),("تاریخ تولد",s.get("birth_date") or s.get("birth_date_shamsi")),("پایه",s.get("grade")),("کلاس",s.get("class_name"))]
        for idx,(lab,val) in enumerate(identity):
            x=w-50 if idx%2==0 else w/2+20; yy=y-(idx//2)*25;self.rtl_draw(c,f"{lab}: {val or '-'}",x,yy,8);c.line(x-250,yy-6,x,yy-6)
        y-=120;c.setFont("FrahooshPDFB",11);c.drawRightString(w-50,y,"جدول برنامه امتحانی و شماره صندلی");y-=20
        headers=[("درس",w-60),("تاریخ",w-230),("شروع",w-330),("پایان",w-405),("مدت",w-475),("صندلی",w-540)]
        c.line(45,y,w-45,y);y-=18
        for lab,x in headers:self.rtl_draw(c,lab,x,y,8,True)
        y-=18;c.line(45,y,w-45,y)
        for ex in exams:
            a=self.api().table_select("exam_seat_assignments",{"exam_id":"eq."+str(ex.get("id")),"student_id":"eq."+str(sid),"limit":"1"}) or []
            seat=a[0].get("seat_number") if a else "-"
            vals=[ex.get("subject") or "-",ex.get("exam_date") or "-",ex.get("exam_start_time") or "-",ex.get("exam_end_time") or "-",ex.get("duration") or "-",seat]
            xs=[w-60,w-230,w-330,w-405,w-475,w-540]
            for val,x in zip(vals,xs):self.rtl_draw(c,val,x,y,8)
            c.line(45,y-8,w-45,y-8);y-=25
        self.qr(c,f"frahoosh://exam-card/{sid}",w-135,h-575,72);c.save();self.status.text=fa_display("کارت امتحان جدول‌بندی‌شده ساخته شد؛ شماره صندلی هر امتحان مستقل و تصادفی است.");self.status.color=SUCCESS

class OpsRouter:
    # Specialized modules provide parity with the Web operational contract.
    SCHOOL_ROUTES={"grades","student_grades","report_cards","student_cards","weekly_schedule","exam_schedule","exam_seat_assignments","activity_offers","activity_programs","activity_registrations","cultural_activity_registrations","student_council","basij_registration","school_ally","school_mayor","khwarizmi_registrations","educational_activities","parent_activities","transport_requests","discipline_records","counseling_records","counseling_followups","counseling_guidance","counseling_classes","student_referrals","counselor_board","educational_followups","academic_followups","cultural_reports","attendance","messages","competitions","festivals"}
    MAP={"activity_programs":"activities","activity_offers":"activities","activity_registrations":"activities","cultural_activity_registrations":"activities","competitions":"activities","cultural_competitions":"activities","art_competitions":"activities","sport_competitions":"activities","student_council":"activities","basij_registration":"activities","school_ally":"activities","school_mayor":"activities","morning_leaders":"activities","qari_registration":"activities","khwarizmi_registrations":"activities","counseling_records":"counseling","counseling_followups":"counseling","counseling_guidance":"counseling","counseling_classes":"counseling","student_referrals":"counseling","counselor_board":"counseling","educational_followups":"school_educational_followups","academic_followups":"school_academic_followups","cultural_reports":"school_cultural_reports","weekly_schedule":"schedule","generated_weekly_schedule":"schedule","exam_schedule":"exam_schedule","discipline_records":"discipline","discipline_items":"discipline","messages":"school_messages","smart_board_content":"smart_board","smart_board_activities":"smart_board","smart_board_quizzes":"smart_board","student_cards":"cards","class_cards":"cards","certificates":"cards","class_seat_assignments":"cards","class_seats":"cards","exam_cards":"cards","exam_seat_assignments":"exam_schedule","exam_seats":"exam_schedule"}
    @classmethod
    def mode_for(cls,route):
        route=str(route or "").strip()
        if route in {"competitions","festivals"}: return "school_activity_offers"
        if route in cls.SCHOOL_ROUTES:return "school_"+route
        return cls.MAP.get(route)
    @classmethod
    def create(cls,state,route):
        route=str(route or "").strip(); mode=cls.mode_for(route)
        if not mode:return None
        if mode.startswith("school_"):
            from mobile.screens.school_operational_modules import SchoolModulesScreen
            effective_route="activity_offers" if route in {"competitions","festivals"} else route
            return SchoolModulesScreen(name="ops_"+mode,app_state=state,route=effective_route)
        K={"activities":OperationalCenterScreen,"counseling":CounselingCenterScreen,"schedule":ScheduleCenterScreen,"exam_schedule":ScheduleCenterScreen,"discipline":DisciplineCenterScreen,"smart_board":SmartBoardCenterScreen,"cards":CardsCenterScreen}[mode]
        return K(name="ops_"+mode,app_state=state,mode=mode)
