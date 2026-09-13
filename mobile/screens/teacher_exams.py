import json
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text

TEACHER_ROLES = {"teacher", "دبیر", "معلم"}
STUDENT_ROLES = {"student", "دانش‌آموز", "دانش آموز", "parent", "ولی", "اولیا"}

TYPE_LABELS = {
    "multiple_choice": "چهارگزینه‌ای",
    "true_false": "صحیح / غلط",
    "fill_blank": "جای خالی",
    "short_answer": "پاسخ کوتاه",
    "essay": "تشریحی",
}
TYPE_VALUES = tuple(TYPE_LABELS.keys())


def role_of(state):
    raw = str(getattr(state, "role", "student") or "student").strip().lower()
    aliases = {
        "مدیر": "manager", "مدیریت": "manager", "admin": "manager",
        "معاون آموزشی": "educational", "معاون اجرایی": "executive", "معاون پرورشی": "cultural",
        "دبیر": "teacher", "معلم": "teacher", "دانش‌آموز": "student", "دانش آموز": "student",
        "ولی": "parent", "اولیا": "parent",
    }
    return aliases.get(raw, raw)


def norm_digits(value):
    return str(value or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))


class TeacherExamsScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.questions = []
        self.current_attempt = None
        self.current_questions = []
        self.answers = {}
        self._timer = None
        self.remaining_seconds = 0
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        head = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(54), spacing=dp(8))
        back = Button(text=rtl_text("‹ داشبورد"), font_name=font_name(), background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(105))
        back.bind(on_release=lambda *_: self._back())
        head.add_widget(back)
        self.title = Label(text=rtl_text("آزمون آنلاین"), font_name=font_name(), font_size="21sp", bold=True, color=PRIMARY, halign="right", valign="middle")
        self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title); root.add_widget(head)
        self.status = Label(text="", font_name=font_name(), font_size="12sp", color=SECONDARY, halign="right", valign="middle", size_hint_y=None, height=dp(38))
        self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(9), padding=dp(5), size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args): self.show_home()

    def _clear(self):
        self._stop_timer(); self.body.clear_widgets()

    def _label(self, text, size="14sp", color=SECONDARY, height=58):
        w=Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, halign="right", valign="middle", size_hint_y=None, height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w

    def _button(self, text, callback, color=PRIMARY, height=48):
        b=Button(text=rtl_text(text), font_name=font_name(), font_size="14sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=dp(height)); b.bind(on_release=callback); self.body.add_widget(b); return b

    def _field(self, hint, height=50, multiline=False):
        f=TextInput(hint_text=rtl_text(hint), font_name=font_name(), font_size="14sp", multiline=multiline, size_hint_y=None, height=dp(height)); self.body.add_widget(f); return f

    def show_home(self):
        self._clear(); self.title.text=rtl_text("آزمون آنلاین")
        if role_of(self.app_state)=="teacher": self._teacher_home()
        else: self._student_home()

    def _teacher_home(self):
        self._label("طراحی استاندارد آزمون آنلاین", "20sp", PRIMARY, 55)
        self._label("پنج نوع سؤال، نمره مستقل، نمره‌دهی خودکار برای سؤال‌های غیرتشریحی، پشتیبانی از نمادهای ریاضی √ ² ³ π و توان/رادیکال، زمان‌بندی جداگانه برای هر کلاس و لینک آزمون برای مدارس دیگر.", height=100)
        self._button("ساخت آزمون جدید", lambda *_: self._new_exam(), SUCCESS)
        self._button("آزمون‌های من و لینک‌ها", lambda *_: self._load_teacher_exams())

    def _new_exam(self):
        self._clear(); self.questions=[]; self._label("ساخت آزمون جدید", "20sp", PRIMARY, 50)
        title=self._field("عنوان آزمون")
        subject=Spinner(text="ریاضی", values=("ریاضی","علوم","فارسی","انگلیسی","مطالعات اجتماعی","دینی","سایر"), size_hint_y=None, height=dp(50)); self.body.add_widget(subject)
        grade=self._field("پایه / کلاس")
        duration=self._field("مدت آزمون به دقیقه"); duration.text="45"
        max_attempts=self._field("حداکثر دفعات مجاز شرکت"); max_attempts.text="1"
        passing=self._field("نمره قبولی؛ اختیاری"); passing.text="0"
        desc=self._field("توضیحات و دستورالعمل آزمون", 85, True)
        self._label("در متن سؤال می‌توانید √49، √(x)، x²، x³، aⁿ، π، ≤، ≥، کسر و عبارت‌های ریاضی را مستقیماً بنویسید.", color=PRIMARY, height=65)
        self._button("افزودن سؤال", lambda *_: self._add_question_form(), SUCCESS)
        self._button("ذخیره آزمون و زمان‌بندی", lambda *_: self._save_exam(title,subject,grade,duration,max_attempts,passing,desc), PRIMARY)
        self._button("انصراف", lambda *_: self.show_home())

    def _add_question_form(self):
        n=len(self.questions)+1; self._label(f"سؤال {n}", "17sp", PRIMARY, 42)
        q=self._field("متن سؤال", 78, True)
        typ=Spinner(text="چهارگزینه‌ای", values=tuple(TYPE_LABELS.values()), size_hint_y=None, height=dp(50)); self.body.add_widget(typ)
        point=self._field("نمره سؤال"); point.text="1"
        opt=[self._field("گزینه ۱"),self._field("گزینه ۲"),self._field("گزینه ۳"),self._field("گزینه ۴")]
        correct=Spinner(text="گزینه ۱", values=("گزینه ۱","گزینه ۲","گزینه ۳","گزینه ۴"), size_hint_y=None, height=dp(48)); self.body.add_widget(correct)
        accepted=self._field("پاسخ‌های پذیرفته‌شده با | جدا شوند؛ برای جای‌خالی/پاسخ کوتاه", 60, True)
        self.questions.append({"q":q,"typ":typ,"point":point,"opt":opt,"correct":correct,"accepted":accepted})
        note=self._label("یادآوری امنیتی: این سؤال یک سؤال تشخیصی/ارزیابی است؛ دانش‌آموزان نباید پاسخ آن را در چت با دیگران مطرح کنند.", color=SECONDARY, height=55)
        def changed(spinner, value):
            mc=value==TYPE_LABELS["multiple_choice"]
            tf=value==TYPE_LABELS["true_false"]
            for w in opt: w.opacity=1 if mc else 0; w.disabled=not mc
            correct.opacity=1 if mc or tf else 0; correct.disabled=not (mc or tf)
            if tf: correct.values=("صحیح","غلط"); correct.text="صحیح"
            else: correct.values=("گزینه ۱","گزینه ۲","گزینه ۳","گزینه ۴"); correct.text="گزینه ۱"
            accepted.opacity=1 if value in (TYPE_LABELS["fill_blank"],TYPE_LABELS["short_answer"]) else 0
            accepted.disabled=not (value in (TYPE_LABELS["fill_blank"],TYPE_LABELS["short_answer"]))
        typ.bind(text=changed); changed(typ,typ.text)

    def _teacher_id(self):
        p=getattr(self.app_state,"profile",{}) or {}
        if p.get("linked_teacher_id"): return int(p["linked_teacher_id"])
        try:
            rows=self.app_state.api.table_select("teachers",{"national_code":f"eq.{self.app_state.national_code}","select":"id","limit":"1"})
            return int(rows[0]["id"]) if rows else None
        except Exception: return None

    def _save_exam(self,title,subject,grade,duration,max_attempts,passing,desc):
        if not title.text.strip() or not self.questions: return self._error("عنوان آزمون و حداقل یک سؤال لازم است.")
        tid=self._teacher_id()
        if not tid: return self._error("پرونده دبیر به حساب کاربری متصل نیست.")
        try:
            dur=max(1,int(norm_digits(duration.text or "45"))); attempts=max(1,int(norm_digits(max_attempts.text or "1"))); pass_score=max(0,float(norm_digits(passing.text or "0")))
        except Exception: return self._error("مدت، دفعات شرکت و نمره قبولی باید عدد باشند.")
        payload={"teacher_id":tid,"title":title.text.strip(),"subject":subject.text,"grade":grade.text.strip(),"class_name":grade.text.strip(),"exam_type":"آزمون استاندارد آنلاین","duration":dur,"description":desc.text.strip(),"published":False,"secure_mode":True,"standard_mode":True,"max_attempts":attempts,"passing_score":pass_score}
        self.status.text=rtl_text("در حال ذخیره آزمون..."); self.status.color=SECONDARY
        Thread(target=self._save_worker,args=(payload,dur),daemon=True).start()

    def _save_worker(self,payload,dur):
        try:
            created=self.app_state.api.table_insert("teacher_exams",payload); exam_id=int((created[0] if isinstance(created,list) else created)["id"])
            for item in self.questions:
                typ_label=item["typ"].text; typ=next((k for k,v in TYPE_LABELS.items() if v==typ_label),"multiple_choice")
                p=float(norm_digits(item["point"].text or "1")); data={"quiz_id":exam_id,"question":item["q"].text.strip(),"points":p,"question_type":typ,"auto_grade":typ!="essay","explanation":"","difficulty":"standard","cognitive_level":"assessment"}
                if typ=="multiple_choice":
                    opts=[x.text.strip() for x in item["opt"]]; data.update({"option1":opts[0],"option2":opts[1],"option3":opts[2],"option4":opts[3],"options_json":json.dumps(opts,ensure_ascii=False),"correct_answer":item["correct"].text.replace("گزینه ","").strip()})
                elif typ=="true_false": data["correct_answer"]="صحیح" if item["correct"].text=="صحیح" else "غلط"
                elif typ in ("fill_blank","short_answer"): data["accepted_answers"]=item["accepted"].text.strip(); data["correct_answer"]=item["accepted"].text.split("|")[0].strip() if item["accepted"].text.strip() else ""
                else: data["correct_answer"]=""
                self.app_state.api.table_insert("quiz_questions",data)
            self.app_state.api.table_update("teacher_exams",{"id":f"eq.{exam_id}"},{"published":True})
            Clock.schedule_once(lambda *_: self._schedule(exam_id,dur),0)
        except Exception as exc: Clock.schedule_once(lambda *_: self._error("ذخیره آزمون انجام نشد: "+str(exc)),0)

    def _schedule(self,exam_id,dur):
        self._clear(); self._label("زمان‌بندی آزمون", "20sp", PRIMARY, 50)
        self._label("برای یک آزمون مشترک، هر کلاس می‌تواند نوبت جدا داشته باشد؛ برای برگزاری هماهنگ، همان زمان را برای همه کلاس‌ها ثبت کنید.", height=80)
        date=self._field("تاریخ شمسی؛ مثال 1405/07/01")
        start=self._field("ساعت شروع؛ مثال 10:00")
        end=self._field("ساعت پایان؛ اگر خالی باشد از مدت آزمون محاسبه می‌شود")
        cls=self._field("کلاس")
        coord=Spinner(text="مستقل",values=("مستقل","هماهنگ"),size_hint_y=None,height=dp(48)); self.body.add_widget(coord)
        self._button("ثبت نوبت",lambda *_:self._save_slot(exam_id,dur,date,start,end,cls,coord),SUCCESS)
        self._button("ساخت لینک اشتراکی برای مدرسه دیگر",lambda *_:self._share_form(exam_id,dur),PRIMARY)
        self._button("بازگشت",lambda *_:self._load_teacher_exams())

    def _save_slot(self,exam_id,dur,date,start,end,cls,coord):
        if not date.text.strip() or not start.text.strip() or not cls.text.strip(): return self._error("تاریخ، ساعت شروع و کلاس الزامی است.")
        try:
            h,m=[int(x) for x in start.text.strip().split(":")[:2]]; total=h*60+m+dur; endv=end.text.strip() or f"{(total//60)%24:02d}:{total%60:02d}"
            self.app_state.api.table_insert("teacher_exam_slots",{"quiz_id":exam_id,"class_name":cls.text.strip(),"exam_date_shamsi":date.text.strip(),"start_time_shamsi":start.text.strip(),"end_time_shamsi":endv,"duration":dur,"coordinated":1 if coord.text=="هماهنگ" else 0,"secure_mode":1,"active":True})
            self._success("نوبت آزمون ثبت شد.")
        except Exception as exc:self._error("ثبت نوبت انجام نشد: "+str(exc))

    def _share_form(self,exam_id,dur):
        self._clear(); self._label("لینک آزمون برای مدارس دیگر", "20sp", PRIMARY, 50)
        self._label("کد مدرسه مقصد اختیاری است. اگر خالی باشد لینک برای دانش‌آموزان مدارس دیگر نیز قابل استفاده است. زمان شروع/پایان را می‌توانید هر زمان دلخواه تعیین کنید.",height=85)
        school=self._field("شناسه مدرسه مقصد؛ اختیاری")
        cls=self._field("کلاس مقصد؛ اختیاری")
        start=self._field("شروع ISO؛ مثال 2026-10-01T08:00:00-04:00؛ اختیاری")
        end=self._field("پایان ISO؛ اختیاری")
        d=self._field("مدت به دقیقه"); d.text=str(dur)
        self._button("ایجاد لینک اشتراکی",lambda *_:self._create_share(exam_id,school,cls,start,end,d),SUCCESS)
        self._button("بازگشت",lambda *_:self._schedule(exam_id,dur))

    def _create_share(self,exam_id,school,cls,start,end,d):
        try:
            dur=max(1,int(norm_digits(d.text or "45"))); payload={"p_quiz_id":int(exam_id),"p_target_school_id":school.text.strip() or None,"p_target_class_name":cls.text.strip() or None,"p_start_at":start.text.strip() or None,"p_end_at":end.text.strip() or None,"p_duration_minutes":dur}
            result=self.app_state.api.rpc("create_teacher_exam_share",payload); code=(result or {}).get("share_code") if isinstance(result,dict) else None
            if not code: raise RuntimeError("سرور کد اشتراک برنگرداند")
            link=f"https://frahoosh.ir/exam/{code}"
            self._clear(); self._label("لینک آزمون آماده است", "20sp", SUCCESS, 55); self._label(f"کد ورود: {code}\n\nلینک:\n{link}\n\nاین آزمون برای دانش‌آموزان مدارس دیگر هم قابل استفاده است و زمان آن از تنظیمات همین لینک کنترل می‌شود.",height=180)
            self._button("کپی لینک",lambda *_:self._copy(link),SUCCESS); self._button("بازگشت به آزمون‌ها",lambda *_:self._load_teacher_exams())
        except Exception as exc:self._error("ساخت لینک انجام نشد: "+str(exc))

    def _copy(self,text):
        try:
            from kivy.core.clipboard import Clipboard; Clipboard.copy(text); self._success("لینک در کلیپ‌بورد کپی شد.")
        except Exception:self._error("کپی لینک در این دستگاه در دسترس نیست.")

    def _load_teacher_exams(self):
        self._clear(); self._label("آزمون‌های من", "20sp", PRIMARY, 50)
        try:
            tid=self._teacher_id(); rows=self.app_state.api.table_select("teacher_exams",{"teacher_id":f"eq.{tid}","order":"id.desc","limit":"50"}) if tid else []
            for r in rows:
                self._label(f"{r.get('title','آزمون')}\n{r.get('subject','')} | {r.get('duration',45)} دقیقه | {'منتشر شده' if r.get('published') else 'پیش‌نویس'}",height=75)
                self._button("زمان‌بندی / لینک اشتراک",lambda *_ ,eid=r.get("id"),dur=r.get("duration",45):self._schedule(eid,int(dur or 45)),PRIMARY,44)
            if not rows:self._label("هنوز آزمونی ثبت نشده است.",height=70)
        except Exception as exc:self._error("دریافت آزمون‌ها انجام نشد: "+str(exc))
        self._button("ساخت آزمون جدید",lambda *_:self._new_exam(),SUCCESS)

    def _student_id(self):
        p=getattr(self.app_state,"profile",{}) or {}; nc=norm_digits(p.get("national_code") or getattr(self.app_state,"national_code","") or ""); email=str(p.get("email") or "").strip()
        try:
            params={"select":"id","limit":"1"}
            if nc: params["national_code"]=f"eq.{nc}"
            elif email: params["email"]=f"eq.{email}"
            rows=self.app_state.api.table_select("students",params); return int(rows[0]["id"]) if rows else None
        except Exception:return None

    def _student_home(self):
        self._label("ورود به آزمون آنلاین", "20sp", PRIMARY, 50)
        self._label("برای آزمون مدرسه خودتان، آزمون‌های منتشرشده را ببینید. برای آزمون یک مدرسه دیگر، کد اشتراک را وارد کنید. ترتیب سؤال‌ها برای هر تلاش تصادفی می‌شود و پاسخ سؤال تشریحی خودکار نمره نمی‌گیرد.",height=105)
        code=self._field("کد اشتراک آزمون؛ اختیاری")
        self._button("ورود با کد اشتراک",lambda *_:self._start_shared(code.text.strip()),SUCCESS)
        self._button("نمایش آزمون‌های مدرسه",lambda *_:self._load_student_exams(),PRIMARY)

    def _load_student_exams(self):
        self._clear(); self._label("آزمون‌های منتشرشده", "20sp", PRIMARY, 50)
        try:
            rows=self.app_state.api.table_select("teacher_exams",{"published":"eq.true","order":"id.desc","limit":"50"})
            for r in rows:
                self._label(f"{r.get('title','آزمون')}\n{r.get('subject','')} | {r.get('duration',45)} دقیقه",height=72)
                self._button("شروع آزمون",lambda *_ ,eid=r.get("id"):self._start_exam(int(eid)),SUCCESS,44)
            if not rows:self._label("در حال حاضر آزمون منتشرشده‌ای وجود ندارد.",height=70)
        except Exception as exc:self._error("دریافت آزمون‌ها انجام نشد: "+str(exc))
        self._button("بازگشت",lambda *_:self.show_home())

    def _start_exam(self,eid):
        sid=self._student_id()
        if not sid:return self._error("پرونده دانش‌آموز در سامانه پیدا نشد.")
        try:
            p=getattr(self.app_state,"profile",{}) or {}; username=str(p.get("username") or p.get("national_code") or getattr(self.app_state,"national_code","") or p.get("email") or "")
            result=self.app_state.api.rpc("start_teacher_exam",{"p_quiz_id":eid,"p_student_id":sid,"p_student_username":username}); self._open_attempt(result)
        except Exception as exc:self._error("شروع آزمون انجام نشد: "+str(exc))

    def _start_shared(self,code):
        if not code:return self._error("کد اشتراک را وارد کنید.")
        sid=self._student_id()
        if not sid:return self._error("پرونده دانش‌آموز در سامانه پیدا نشد.")
        try:
            p=getattr(self.app_state,"profile",{}) or {}; username=str(p.get("username") or p.get("national_code") or getattr(self.app_state,"national_code","") or p.get("email") or "")
            info=self.app_state.api.rpc("start_shared_teacher_exam",{"p_share_code":code,"p_student_id":sid,"p_student_username":username}); self._open_attempt(info)
        except Exception as exc:self._error("ورود به آزمون اشتراکی انجام نشد: "+str(exc))

    def _open_attempt(self,info):
        if not isinstance(info,dict) or not info.get("attempt_id"):return self._error("سرور تلاش آزمون را ایجاد نکرد.")
        self.current_attempt=int(info["attempt_id"]); self.remaining_seconds=int(info.get("duration") or 45)*60
        rows=self.app_state.api.rpc("get_teacher_exam_questions",{"p_attempt_id":self.current_attempt})
        self.current_questions=rows if isinstance(rows,list) else []
        self.answers={}; self._render_exam()

    def _render_exam(self):
        self._clear(); self.title.text=rtl_text("در حال برگزاری آزمون"); self._label("هشدار امنیتی: پاسخ سؤال‌های آزمون تشخیصی/ارزیابی را با دیگران در چت مطرح نکنید.",color=ERROR,height=65)
        self._label("زمان باقی‌مانده: --:--", "18sp", PRIMARY, 45); self.timer_label=self.body.children[0]
        for q in self.current_questions:
            self._label(f"{q.get('question','')}\nنمره: {q.get('points',1)}\nنوع: {TYPE_LABELS.get(q.get('question_type'),q.get('question_type',''))}","16sp",PRIMARY,105)
            typ=q.get("question_type")
            if typ=="multiple_choice":
                values=[q.get("option1",""),q.get("option2",""),q.get("option3",""),q.get("option4","")]
                for value in values:
                    b=Button(text=rtl_text(value),font_name=font_name(),font_size="14sp",background_normal="",background_color=PRIMARY,color=WHITE,size_hint_y=None,height=dp(48)); b.bind(on_release=lambda *_ ,qid=q["id"],ans=value:self._answer(qid,ans)); self.body.add_widget(b)
            elif typ=="true_false":
                for value in ("صحیح","غلط"):
                    self._button(value,lambda *_ ,qid=q["id"],ans=value:self._answer(qid,ans),PRIMARY,44)
            else:
                f=self._field("پاسخ شما",85,typ=="essay"); f.bind(text=lambda inst,val,qid=q["id"]:self.answers.__setitem__(qid,val))
        self._button("ثبت نهایی آزمون",lambda *_:self._submit(),SUCCESS)
        self._start_timer()

    def _answer(self,qid,answer): self.answers[qid]=answer; self._success("پاسخ ثبت شد.")

    def _start_timer(self):
        self._stop_timer(); self._timer=Clock.schedule_interval(self._tick,1)

    def _tick(self,dt):
        self.remaining_seconds-=1
        if self.remaining_seconds<=0:
            self._stop_timer(); self._submit(); return
        self.timer_label.text=rtl_text(f"زمان باقی‌مانده: {self.remaining_seconds//60:02d}:{self.remaining_seconds%60:02d}")

    def _stop_timer(self):
        if self._timer: self._timer.cancel(); self._timer=None

    def _submit(self):
        if not self.current_attempt:return
        self._stop_timer()
        answers=[{"question_id":int(k),"answer":str(v)} for k,v in self.answers.items()]
        try:
            result=self.app_state.api.rpc("submit_teacher_exam",{"p_attempt_id":self.current_attempt,"p_answers":answers}); self._clear(); self._label("آزمون ثبت شد", "22sp", SUCCESS, 65); self._label(f"نمره خودکار: {result.get('score',0)} از {result.get('max_score',0)}\nسؤال‌های تشریحی برای تصحیح دستی باقی می‌مانند.",height=100); self._button("بازگشت",lambda *_:self.show_home())
        except Exception as exc:self._error("ثبت پاسخ‌ها انجام نشد: "+str(exc))

    def _success(self,text): self.status.color=SUCCESS; self.status.text=rtl_text(text)
    def _error(self,text): self.status.color=ERROR; self.status.text=rtl_text(text)
    def _back(self):
        self._stop_timer()
        try:self.manager.current="dashboard"
        except Exception:pass
