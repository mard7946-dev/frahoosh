from datetime import datetime, timezone
import webbrowser

from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, SCHOOL_ID, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text

PAYMENT_MANAGERS={"manager","educational","cultural"}
CLASS_MANAGERS={"manager","educational","executive"}

def role_of(state):
    raw=str(getattr(state,"role","student") or "student").strip().lower()
    return {"مدیر":"manager","مدیریت":"manager","admin":"manager","معاون آموزشی":"educational","معاون اجرایی":"executive","معاون پرورشی":"cultural","دبیر":"teacher","معلم":"teacher","دانش‌آموز":"student","دانش آموز":"student","ولی":"parent","اولیا":"parent"}.get(raw,raw)

def digits(v):return str(v or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789"))

def now_iso():return datetime.now(timezone.utc).isoformat()

class OperationsScreen(Screen):
    def __init__(self,app_state=None,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.route="messages"; self._build()
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(8)); head=BoxLayout(size_hint_y=None,height=dp(54),spacing=dp(8))
        back=Button(text=rtl_text("‹ بازگشت"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(100)); back.bind(on_release=lambda *_:self._back()); head.add_widget(back)
        self.title=Label(text=rtl_text(APP_NAME),font_name=font_name(),font_size="21sp",bold=True,color=PRIMARY,halign="right",valign="middle"); self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title); root.add_widget(head)
        self.status=Label(text="",font_name=font_name(),font_size="12sp",color=SECONDARY,halign="right",valign="middle",size_hint_y=None,height=dp(42)); self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False); self.body=BoxLayout(orientation="vertical",spacing=dp(9),padding=dp(4),size_hint_y=None); self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root)
    def set_route(self,route):
        self.route=route; self.body.clear_widgets(); self.title.text=rtl_text({"payment":"پرداخت آنلاین","messages":"صندوق پیام‌ها","online":"کلاس‌های آنلاین","meetings":"ملاقات با مدرسه"}.get(route,APP_NAME))
        if route=="payment":self._payment()
        elif route=="online":self._online()
        elif route=="meetings":self._meetings()
        else:self._messages()
    def _label(self,text,size="14sp",color=SECONDARY,height=68):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,halign="right",valign="middle",size_hint_y=None,height=dp(height)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w
    def _button(self,text,cb,color=PRIMARY,height=48):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="13sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(height)); b.bind(on_release=cb); self.body.add_widget(b); return b
    def _meetings(self):
        role=role_of(self.app_state)
        self._label("ملاقات با مدرسه", "21sp", PRIMARY, 52, True)
        self._label("درخواست ملاقات از مسیر واقعی سامانه ثبت می‌شود و تأیید مدیر، سپس ارجاع و تعیین زمان توسط معاون آموزشی در همان رکورد انجام می‌شود.", height=82)
        if role == "parent":
            self._parent_meeting_form()
        elif role in {"teacher","advisor","executive","cultural"}:
            self._staff_meeting_form(role)
        if role in {"manager","educational","executive","cultural","advisor","teacher","parent"}:
            self._load_meetings(role)

    def _meeting_field(self,hint):
        return self._field(hint,50,False)

    def _profile_email(self):
        p=getattr(self.app_state,"profile",{}) or {}
        return str(p.get("email") or p.get("username") or getattr(self.app_state,"display_name","") or "").strip()

    def _profile_id(self,key):
        p=getattr(self.app_state,"profile",{}) or {}
        value=p.get(key)
        try:return int(value) if value not in (None,"") else None
        except Exception:return None

    def _parent_meeting_form(self):
        self._label("ثبت درخواست ملاقات", "16sp", PRIMARY, 44, True)
        students=self._safe_rows("students")
        if not students:
            self._label("پرونده فرزند در دسترس نیست؛ ابتدا ارتباط والد و دانش‌آموز را در پرونده اولیا ثبت کنید.",height=70)
            return
        student_map={}
        for s in students:
            sid=s.get("id"); label=f"{s.get('first_name','')} {s.get('last_name','')} | {s.get('grade','')} {s.get('class_name','')}".strip()
            student_map[label]=sid
        sp_student=Spinner(text=next(iter(student_map)),values=list(student_map),size_hint_y=None,height=dp(50)); self.body.add_widget(sp_student)
        target_sp=Spinner(text="دبیر",values=["دبیر","کادر","مشاور"],size_hint_y=None,height=dp(50)); self.body.add_widget(target_sp)
        names=self._target_names("teacher")
        teacher_sp=Spinner(text=(names[0] if names else "انتخاب فرد"),values=names or ["انتخاب فرد"],size_hint_y=None,height=dp(50)); self.body.add_widget(teacher_sp)
        date=self._meeting_field("تاریخ ملاقات")
        time=self._meeting_field("ساعت ملاقات")
        reason=self._meeting_field("علت ملاقات")
        self._button("ثبت درخواست ملاقات",lambda *_:self._create_meeting(student_map.get(sp_student.text),sp_student.text,teacher_sp.text,target_sp.text,date.text,time.text,reason.text),SUCCESS)

    def _staff_meeting_form(self,role):
        self._label("درخواست ملاقات با ولی", "16sp", PRIMARY, 44, True)
        students=self._safe_rows("students")
        student_map={}
        for s in students:
            label=f"{s.get('first_name','')} {s.get('last_name','')} | {s.get('grade','')} {s.get('class_name','')}".strip()
            student_map[label]=s.get("id")
        if not student_map:
            self._label("فهرست دانش‌آموزان در دسترس نیست.",height=60); return
        sp=Spinner(text=next(iter(student_map)),values=list(student_map),size_hint_y=None,height=dp(50)); self.body.add_widget(sp)
        parents=self._safe_rows("parents")
        parent_map={}
        for p in parents:
            label=f"{p.get('first_name','')} {p.get('last_name','')}".strip()
            parent_map[label]=p.get("id")
        parent_sp=Spinner(text=(next(iter(parent_map)) if parent_map else "ولی دانش‌آموز"),values=list(parent_map) or ["ولی دانش‌آموز"],size_hint_y=None,height=dp(50)); self.body.add_widget(parent_sp)
        date=self._meeting_field("تاریخ ملاقات")
        time=self._meeting_field("ساعت ملاقات")
        reason=self._meeting_field("علت ملاقات")
        self._button("ثبت درخواست ملاقات با ولی",lambda *_:self._create_meeting(student_map.get(sp.text),sp.text,parent_sp.text,"parent",date.text,time.text,reason.text),SUCCESS)

    def _target_names(self,kind):
        table={"teacher":"teachers","staff":"staff","advisor":"staff"}.get(kind,kind)
        rows=self._safe_rows(table)
        names=[]
        for r in rows:
            role=str(r.get("role") or "").lower()
            if kind=="advisor" and role not in {"advisor","مشاور","counselor","مشاوره"}: continue
            label=f"{r.get('first_name','')} {r.get('last_name','')}".strip()
            if label:names.append(label)
        return names[:100]

    def _safe_rows(self,table):
        try:return self.app_state.api.table_select(table,{"limit":"100","order":"id.asc"}) or []
        except Exception:return []

    def _create_meeting(self,student_id,student_label,target_name,target_role,date,time,reason):
        if not student_id or not target_name or target_name=="انتخاب فرد": return self._error("دانش‌آموز و فرد مورد ملاقات را انتخاب کنید.")
        if not date.strip() or not time.strip() or not reason.strip(): return self._error("تاریخ، ساعت و علت ملاقات الزامی است.")
        role=role_of(self.app_state); email=self._profile_email()
        payload={
            "requester_id":self._profile_id("id"),
            "requester_username":email,
            "requester_role":role,
            "student_id":int(student_id),
            "student_name":student_label,
            "target_role":target_role,
            "target_name":target_name,
            "target_username":target_name,
            "requested_date_shamsi":date.strip(),
            "requested_time":time.strip(),
            "reason":reason.strip(),
            "status":"pending_manager",
            "manager_status":"pending",
            "educational_status":"pending"
        }
        try:
            self.app_state.api.table_insert("school_meeting_requests",payload)
            self._success("درخواست ملاقات ثبت شد و برای تأیید مدیر ارسال گردید.")
            self.set_route("meetings")
        except Exception as exc:self._error("ثبت درخواست ملاقات انجام نشد: "+str(exc))

    def _load_meetings(self,role):
        self._label("درخواست‌های ملاقات", "16sp", PRIMARY, 44, True)
        rows=self._safe_rows("school_meeting_requests")
        if not rows:
            self._label("درخواستی برای نمایش وجود ندارد.",height=60); return
        for row in rows[:80]:
            status=row.get("status") or "pending_manager"
            title=f"#{row.get('id')} | {row.get('student_name','')} | {row.get('target_name','')}"
            detail=f"{row.get('requested_date_shamsi','')} — {row.get('requested_time','')} | علت: {row.get('reason','')}\nوضعیت: {status}"
            self._label(title+"\n"+detail,height=82)
            rid=row.get("id")
            if role=="manager" and status=="pending_manager":
                self._button("تأیید مدیر",lambda *_ ,x=rid:self._meeting_status(x,"manager"),SUCCESS,42)
                self._button("رد درخواست",lambda *_ ,x=rid:self._meeting_status(x,"reject_manager"),ERROR,42)
            elif role=="educational" and status=="pending_educational":
                self._button("تأیید و تعیین وقت نهایی",lambda *_ ,x=rid:self._meeting_status(x,"educational"),SUCCESS,42)
                self._button("رد توسط معاون آموزشی",lambda *_ ,x=rid:self._meeting_status(x,"reject_educational"),ERROR,42)

    def _meeting_status(self,rid,action):
        now=now_iso()
        if action=="manager":
            payload={"manager_status":"approved","status":"pending_educational","manager_approved_at":now}
            msg="درخواست تأیید شد و به معاون آموزشی ارجاع شد."
        elif action=="reject_manager":
            payload={"manager_status":"rejected","status":"rejected","manager_approved_at":now}
            msg="درخواست توسط مدیر رد شد."
        elif action=="educational":
            payload={"educational_status":"approved","status":"confirmed","educational_approved_at":now}
            msg="ملاقات تأیید نهایی شد."
        else:
            payload={"educational_status":"rejected","status":"rejected","educational_approved_at":now}
            msg="درخواست توسط معاون آموزشی رد شد."
        try:
            self.app_state.api.table_update("school_meeting_requests",{"id":f"eq.{int(rid)}"},payload)
            self._success(msg); self.set_route("meetings")
        except Exception as exc:self._error("تغییر وضعیت درخواست انجام نشد: "+str(exc))

    def _payment(self):
        if role_of(self.app_state) in PAYMENT_MANAGERS:self._payment_management()
        else:self._payment_user()
    def _payment_management(self):
        self._label("مدیریت گزینه‌های پرداخت\nگزینه‌ها در payment_offers ذخیره می‌شوند و مبلغ را خود سامانه تعیین می‌کند.",height=82)
        title=self._field("عنوان پرداخت؛ مثال کمک‌های داوطلبانه"); reason=self._field("علت پرداخت؛ اختیاری"); amount=self._field("مبلغ به ریال")
        self._button("ثبت گزینه پرداخت",lambda *_:self._save_offer(title,reason,amount),SUCCESS); self._button("بازخوانی گزینه‌ها",lambda *_:self.set_route("payment")); self._load_offers()
    def _save_offer(self,title,reason,amount):
        try:a=int(digits(amount.text).replace(",","") or 0)
        except Exception:return self._error("مبلغ باید عدد باشد.")
        if a<=0 or not title.text.strip():return self._error("عنوان و مبلغ الزامی است.")
        try:self.app_state.api.table_insert("payment_offers",{"title":title.text.strip(),"amount":a,"target_type":"school","target_value":SCHOOL_ID,"description":reason.text.strip(),"active":1,"manual_amount":0,"payment_reason":reason.text.strip(),"gateway_enabled":True}); self._success("گزینه پرداخت در سامانه ثبت شد.")
        except Exception as exc:self._error("ثبت گزینه پرداخت انجام نشد: "+str(exc))
    def _load_offers(self):
        try:rows=self.app_state.api.table_select("payment_offers",{"active":"eq.1","order":"id.desc","limit":"50"})
        except Exception as exc:return self._error("خواندن گزینه‌های پرداخت انجام نشد: "+str(exc))
        for r in rows:self._label(f"{r.get('title','پرداخت')}\nمبلغ: {r.get('amount',0)} ریال\n{r.get('payment_reason') or r.get('description') or ''}",height=78)
        if not rows:self._label("هنوز گزینه پرداخت فعالی ثبت نشده است.",height=60)
    def _student_id(self):
        p=getattr(self.app_state,"profile",{}) or {}; nc=digits(p.get("national_code") or getattr(self.app_state,"national_code","") or ""); email=str(p.get("email") or "")
        try:
            params={"select":"id","limit":"1"}; params["national_code"]=f"eq.{nc}" if nc else f"eq.{email}"; rows=self.app_state.api.table_select("students",params); return int(rows[0]["id"]) if rows else None
        except Exception:return None
    def _payment_user(self):
        self._label("پرداخت مدرسه\nفقط گزینه‌های فعال و تأییدشده مدرسه نمایش داده می‌شوند.",height=75)
        try:rows=self.app_state.api.table_select("payment_offers",{"active":"eq.1","order":"id.desc","limit":"50"})
        except Exception as exc:return self._error("گزینه‌های پرداخت در دسترس نیست: "+str(exc))
        values=[]; by_title={}
        for r in rows:
            text=f"{r.get('title','پرداخت')} — {r.get('amount',0)} ریال"; values.append(text); by_title[text]=r
        if not values:self._label("در حال حاضر گزینه پرداخت فعالی وجود ندارد.",height=60); return
        sp=Spinner(text=values[0],values=values,size_hint_y=None,height=dp(50)); self.body.add_widget(sp); self._button("ایجاد درخواست پرداخت",lambda *_:self._start_payment(by_title.get(sp.text)),SUCCESS); self._button("مشاهده سوابق پرداخت",lambda *_:self._history())
    def _start_payment(self,offer):
        if not offer:return self._error("گزینه پرداخت انتخاب نشده است.")
        sid=self._student_id()
        if not sid:return self._error("پرونده دانش‌آموز در سامانه پیدا نشد.")
        try:
            attempt=self.app_state.api.rpc("create_payment_attempt",{"p_offer_id":int(offer["id"]),"p_student_id":sid}); row=attempt if isinstance(attempt,dict) else (attempt[0] if attempt else {}); aid=row.get("id")
            from mobile.config import PAYMENT_GATEWAY_URL
            if not PAYMENT_GATEWAY_URL:return self._success(f"درخواست پرداخت #{aid} ثبت شد. درگاه در تنظیمات امن سامانه فعال نشده است.")
            webbrowser.open(PAYMENT_GATEWAY_URL.rstrip("?")+"?attempt_id="+str(aid)); self._success("درخواست پرداخت ثبت و درگاه باز شد؛ نتیجه فقط با callback رسمی باید تأیید شود.")
        except Exception as exc:self._error("ایجاد درخواست پرداخت انجام نشد: "+str(exc))
    def _history(self):
        try:
            email=str((getattr(self.app_state,"profile",{}) or {}).get("email") or ""); rows=self.app_state.api.table_select("payment_attempts",{"payer_username":f"eq.{email}","order":"id.desc","limit":"50"}); self.body.clear_widgets(); self._label("سوابق پرداخت","20sp",PRIMARY,50)
            for r in rows:self._label(f"#{r.get('id')} | {r.get('description','')}\nمبلغ: {r.get('amount',0)} | وضعیت: {r.get('status','در انتظار')}",height=78)
            if not rows:self._label("سابقه‌ای ثبت نشده است.",height=60)
        except Exception as exc:self._error("خواندن سوابق پرداخت انجام نشد: "+str(exc))
    def _online(self):
        if role_of(self.app_state) in CLASS_MANAGERS:self._online_management()
        else:self._online_user()
    def _online_management(self):
        self._label("مدیریت کلاس آنلاین\nکلاس، جلسه و اعضای آن در جداول واقعی سامانه ذخیره می‌شود.",height=82)
        fields=[self._field("عنوان کلاس"),self._field("درس / موضوع"),self._field("نام دبیر"),self._field("پایه"),self._field("کلاس"),self._field("مدت به دقیقه"),self._field("لینک ورود به جلسه"),self._field("ساعت شروع؛ اختیاری"),self._field("ساعت پایان؛ اختیاری")]; fields[5].text="60"
        self._button("ساخت کلاس واقعی",lambda *_:self._create_class(*fields),SUCCESS); self._load_classes(True)
    def _create_class(self,title,subject,teacher,grade,cls,duration,join,start,end):
        if not title.text.strip():return self._error("عنوان کلاس الزامی است.")
        try:dur=max(1,int(digits(duration.text or "60")))
        except Exception:return self._error("مدت کلاس باید عدد باشد.")
        try:
            self.app_state.api.table_insert("online_classes",{"title":title.text.strip(),"subject":subject.text.strip(),"lesson":subject.text.strip(),"teacher":teacher.text.strip(),"grade":grade.text.strip(),"class_name":cls.text.strip(),"duration":dur,"status":"active","start_time_shamsi":start.text.strip(),"end_time_shamsi":end.text.strip(),"join_url":join.text.strip(),"meeting_url":join.text.strip()}); self._success("کلاس در سامانه ثبت شد."); self.set_route("online")
        except Exception as exc:self._error("ساخت کلاس انجام نشد: "+str(exc))
    def _online_user(self):self._label("کلاس‌های آنلاین\nکلاس‌های فعال و جلسات واقعی سامانه در اینجا نمایش داده می‌شوند.",height=72); self._load_classes(False)
    def _load_classes(self,management=False):
        try:rows=self.app_state.api.table_select("online_classes",{"order":"id.desc","limit":"50"})
        except Exception as exc:return self._error("خواندن کلاس‌ها انجام نشد: "+str(exc))
        for r in rows:
            cid=r.get("id"); state=str(r.get("status") or "inactive"); self._label(f"#{cid} | {r.get('title') or 'کلاس آنلاین'}\n{r.get('subject','')} | پایه {r.get('grade','')} | کلاس {r.get('class_name','')} | {r.get('duration',0)} دقیقه\nوضعیت: {'فعال' if state=='active' else ('پایان‌یافته' if state=='ended' else 'غیرفعال')}",height=90)
            if management and cid:
                if state!="active":self._button("فعال‌سازی / شروع جلسه",lambda *_ ,x=cid:self._start_session(x),SUCCESS,44)
                if state=="active":self._button("پایان جلسه",lambda *_ ,x=cid:self._end_session(x),ERROR,44)
                self._button("حضور و غیاب جلسه",lambda *_ ,x=cid:self._attendance(x),PRIMARY,44)
                self._button("گفت‌وگوی کلاس",lambda *_ ,x=cid:self._class_chat(x),PRIMARY,44)
            if state=="active":
                if r.get("join_url"):self._button("ورود به کلاس / دوربین و میکروفون",lambda *_ ,u=r["join_url"]:self._open_url(u),PRIMARY,44)
                else:self._label("برای ارتباط صوتی/تصویری، لینک جلسه واقعی را در ساخت کلاس ثبت کنید.","10sp",SECONDARY,48)
        if not rows:self._label("کلاسی ثبت نشده است.",height=60)
    def _start_session(self,cid):
        try:
            self.app_state.api.table_insert("online_class_sessions",{"class_id":int(cid),"started_at":now_iso()}); self.app_state.api.table_update("online_classes",{"id":f"eq.{int(cid)}"},{"status":"active"}); self._success("جلسه شروع شد و زمان شروع در سامانه ثبت شد."); self.set_route("online")
        except Exception as exc:self._error("شروع جلسه انجام نشد: "+str(exc))
    def _end_session(self,cid):
        try:
            sessions=self.app_state.api.table_select("online_class_sessions",{"class_id":f"eq.{int(cid)}","order":"id.desc","limit":"1"});
            if sessions:self.app_state.api.table_update("online_class_sessions",{"id":f"eq.{sessions[0]['id']}"},{"ended_at":now_iso()})
            self.app_state.api.table_update("online_classes",{"id":f"eq.{int(cid)}"},{"status":"ended"}); self._success("جلسه پایان یافت و زمان پایان ثبت شد."); self.set_route("online")
        except Exception as exc:self._error("پایان جلسه انجام نشد: "+str(exc))
    def _attendance(self,cid):
        try:
            members=self.app_state.api.table_select("online_class_students",{"class_id":f"eq.{int(cid)}","limit":"100"})
            self.body.clear_widgets(); self._label(f"حضور و غیاب کلاس #{cid}","20sp",PRIMARY,50,True)
            for m in members:
                sid=m.get("student_id"); name=m.get("student_name") or str(sid); self._button(f"{name} — حاضر",lambda *_ ,x=sid:self._save_attendance(x,cid,"present"),SUCCESS,42); self._button(f"{name} — غایب",lambda *_ ,x=sid:self._save_attendance(x,cid,"absent"),ERROR,42)
            if not members:self._label("هنوز دانش‌آموزی به این کلاس آنلاین تخصیص داده نشده است.",height=60)
            self._button("بازگشت به کلاس‌ها",lambda *_:self.set_route("online"))
        except Exception as exc:self._error("خواندن اعضای کلاس انجام نشد: "+str(exc))
    def _save_attendance(self,sid,cid,status):
        try:
            self.app_state.api.table_insert("attendance",{"student_id":sid,"class_name":f"online:{cid}","subject":"کلاس آنلاین","attendance_date":now_iso(),"status":status}); self._success("حضور و غیاب ثبت شد.")
        except Exception as exc:self._error("ثبت حضور و غیاب انجام نشد: "+str(exc))
    def _class_chat(self,cid):
        self.body.clear_widgets(); self._label(f"گفت‌وگوی کلاس #{cid}","20sp",PRIMARY,50,True)
        try:
            rows=self.app_state.api.table_select("messages",{"order":"id.desc","limit":"50"})
            for r in rows:
                if str(r.get("title") or "").startswith(f"کلاس #{cid}"):self._label(f"{r.get('sender_name','کاربر')}\n{r.get('body') or ''}",height=70)
        except Exception:pass
        text=self._field("پیام کلاس",80,True); self._button("ارسال پیام به کلاس",lambda *_:self._send_class_message(cid,text),SUCCESS); self._button("بازگشت به کلاس‌ها",lambda *_:self.set_route("online"))
    def _send_class_message(self,cid,text):
        if not text.text.strip():return self._error("متن پیام را وارد کنید.")
        try:self.app_state.api.table_insert("messages",{"title":f"کلاس #{cid} — گفت‌وگو","body":text.text.strip(),"audience_type":"online_class","audience_value":str(cid)}); self._success("پیام کلاس ثبت شد.")
        except Exception as exc:self._error("ارسال پیام انجام نشد: "+str(exc))
    def _messages(self):
        self._label("صندوق پیام‌ها\nپیام‌های ورودی و خروجی از سامانه مرکزی خوانده می‌شوند.",height=72); self._load_messages(); receiver=self._field("گیرنده؛ ایمیل یا نام کاربری",50); title=self._field("عنوان پیام"); text=self._field("متن پیام",85,True); self._button("ارسال پیام",lambda *_:self._send_message(receiver,title,text),SUCCESS)
    def _load_messages(self):
        try:
            rows=self.app_state.api.table_select("messages",{"order":"id.desc","limit":"50"})
            for r in rows:self._label(f"{r.get('title') or 'پیام'}\n{r.get('body') or r.get('text') or ''}",height=85)
            if not rows:self._label("پیامی برای نمایش وجود ندارد.",height=60)
        except Exception as exc:self._error("خواندن پیام‌ها انجام نشد: "+str(exc))
    def _send_message(self,receiver,title,text):
        if not receiver.text.strip() or not text.text.strip():return self._error("گیرنده و متن پیام الزامی است.")
        try:self.app_state.api.rpc("send_school_message",{"p_receiver":receiver.text.strip(),"p_title":title.text.strip(),"p_body":text.text.strip(),"p_audience_type":"user","p_audience_value":None}); self._success("پیام با موفقیت ثبت و ارسال شد.")
        except Exception as exc:self._error("ارسال پیام انجام نشد: "+str(exc))
    def _field(self,hint,height=50,multiline=False):
        f=TextInput(hint_text=rtl_text(hint),font_name=font_name(),font_size="14sp",multiline=multiline,size_hint_y=None,height=dp(height)); self.body.add_widget(f); return f
    def _open_url(self,url):
        try:webbrowser.open(url)
        except Exception:self._error("باز کردن لینک انجام نشد.")
    def _success(self,text):self.status.color=SUCCESS;self.status.text=rtl_text(text)
    def _error(self,text):self.status.color=ERROR;self.status.text=rtl_text(text)
    def _back(self):
        try:self.manager.current="dashboard"
        except Exception:pass
