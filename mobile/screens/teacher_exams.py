import random
from datetime import datetime
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text


MANAGER_ROLES = {"manager", "executive", "educational", "cultural", "advisor", "teacher"}
TEACHER_ROLES = {"teacher"}
STUDENT_ROLES = {"student", "parent"}


def role_of(state):
    raw = str(getattr(state, "role", "student") or "student").strip().lower()
    return {"مدیر":"manager", "مدیریت":"manager", "معاون آموزشی":"educational", "معاون اجرایی":"executive", "معاون پرورشی":"cultural", "دبیر":"teacher", "معلم":"teacher", "دانش‌آموز":"student", "دانش آموز":"student", "ولی":"parent", "اولیا":"parent"}.get(raw, raw)


class TeacherExamsScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.questions = []
        self.answer_buttons = {}
        self.current_attempt = None
        self.current_questions = []
        self.answers = {}
        self.remaining_seconds = 0
        self._timer = None
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52), spacing=dp(8))
        back = Button(text=rtl_text("‹ داشبورد"), font_name=font_name(), font_size="14sp", background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(100))
        back.bind(on_release=lambda *_: self._back())
        header.add_widget(back)
        self.title = Label(text=rtl_text("آزمون آنلاین"), font_name=font_name(), font_size="21sp", bold=True, color=PRIMARY, halign="right", valign="middle")
        self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); header.add_widget(self.title); root.add_widget(header)
        self.status = Label(text="", font_name=font_name(), font_size="12sp", color=SECONDARY, halign="right", valign="middle", size_hint_y=None, height=dp(38))
        self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        self.scroll = ScrollView(do_scroll_x=False)
        self.body = BoxLayout(orientation="vertical", spacing=dp(9), padding=dp(5), size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height")); self.scroll.add_widget(self.body); root.add_widget(self.scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.show_home()

    def _label(self, text, size="14sp", color=SECONDARY, height=58):
        w=Label(text=rtl_text(text), font_name=font_name(), font_size=size, color=color, halign="right", valign="middle", size_hint_y=None, height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w

    def _button(self, text, callback, color=PRIMARY, height=48):
        b=Button(text=rtl_text(text), font_name=font_name(), font_size="14sp", background_normal="", background_color=color, color=WHITE, size_hint_y=None, height=dp(height)); b.bind(on_release=callback); self.body.add_widget(b); return b

    def _field(self, hint, height=50, multiline=False):
        f=TextInput(hint_text=rtl_text(hint), font_name=font_name(), font_size="14sp", multiline=multiline, size_hint_y=None, height=dp(height)); self.body.add_widget(f); return f

    def show_home(self):
        self._stop_timer(); self.body.clear_widgets(); self.answer_buttons={}; self.title.text=rtl_text("آزمون آنلاین")
        r=role_of(self.app_state)
        if r in TEACHER_ROLES: self._teacher_home()
        else: self._student_home()

    def _teacher_home(self):
        self._label("طراح آزمون آنلاین", "20sp", PRIMARY, 55)
        self._label("آزمون چهارگزینه‌ای استاندارد بسازید، برای هر سؤال نمره بدهید، سؤال‌ها را با متن و نمادهای ریاضی مثل √، ²، ³، π و توان/رادیکال وارد کنید و یک آزمون مشترک را برای هر کلاس در زمان متفاوت یا هم‌زمان برگزار کنید.", height=100)
        self._button("ساخت آزمون جدید", lambda *_: self._new_exam(), SUCCESS)
        self._button("آزمون‌های من", lambda *_: self._load_teacher_exams())

    def _new_exam(self):
        self.body.clear_widgets(); self.questions=[]; self._label("ساخت آزمون", "20sp", PRIMARY, 50)
        title=self._field("عنوان آزمون")
        subject=Spinner(text="ریاضی", values=("ریاضی","علوم","فارسی","انگلیسی","مطالعات اجتماعی","دینی","سایر"), size_hint_y=None, height=dp(50)); self.body.add_widget(subject)
        grade=self._field("پایه / کلاس")
        duration=self._field("مدت آزمون به دقیقه (مثلاً 45)"); duration.text="45"
        desc=self._field("توضیحات و دستورالعمل آزمون", 80, True)
        self._label("نکته: در سؤال‌های ریاضی می‌توانید مستقیم از √، √(x)، x²، x³، aⁿ، π، ≤، ≥ و کسرهای متنی استفاده کنید.", color=PRIMARY, height=70)
        self._button("افزودن سؤال", lambda *_: self._add_question_form(), SUCCESS)
        self._button("ذخیره و زمان‌بندی آزمون", lambda *_: self._save_exam(title, subject, grade, duration, desc), PRIMARY)
        self._button("انصراف", lambda *_: self.show_home())

    def _add_question_form(self):
        n=len(self.questions)+1; self._label(f"سؤال {n}", "17sp", PRIMARY, 40)
        q=self._field("متن سؤال؛ مثال: √49 + 2² چند است؟", 75, True)
        opts=[self._field("گزینه ۱"),self._field("گزینه ۲"),self._field("گزینه ۳"),self._field("گزینه ۴")]
        correct=Spinner(text="گزینه ۱", values=("گزینه ۱","گزینه ۲","گزینه ۳","گزینه ۴"), size_hint_y=None, height=dp(48)); self.body.add_widget(correct)
        points=self._field("نمره سؤال"); points.text="1"
        self.questions.append((q,opts,correct,points))
        self._label("پس‌زمینه امنیتی: این سؤال متعلق به یک آزمون تشخیصی/ارزیابی است؛ لطفاً درباره پاسخ سؤال در هیچ چتی گفتگو نشود.", color=SECONDARY, height=55)

    def _teacher_id(self):
        p=getattr(self.app_state,"profile",{}) or {}; linked=p.get("linked_teacher_id")
        if linked: return int(linked)
        try:
            rows=self.app_state.api.table_select("teachers", {"national_code":f"eq.{self.app_state.national_code}","select":"id","limit":"1"})
            return int(rows[0]["id"]) if rows else None
        except Exception: return None

    def _save_exam(self,title,subject,grade,duration,desc):
        if not title.text.strip() or not self.questions: self._set_error("عنوان آزمون و حداقل یک سؤال لازم است."); return
        tid=self._teacher_id()
        if not tid: self._set_error("حساب دبیر به پرونده دبیر متصل نشده است."); return
        try: dur=max(1,int(duration.text.strip() or "45")); payload={"teacher_id":tid,"title":title.text.strip(),"subject":subject.text,"grade":grade.text.strip(),"class_name":grade.text.strip(),"exam_type":"آزمون آنلاین","duration":dur,"description":desc.text.strip(),"published":False,"secure_mode":True}
        except Exception: self._set_error("مدت آزمون باید عدد باشد."); return
        self.status.text=rtl_text("در حال ذخیره آزمون و سؤال‌ها..."); self.status.color=SECONDARY
        Thread(target=self._save_exam_worker,args=(payload,dur),daemon=True).start()

    def _save_exam_worker(self,payload,dur):
        try:
            created=self.app_state.api.table_insert("teacher_exams",payload); exam_id=int((created[0] if isinstance(created,list) else created)["id"])
            for q,opts,correct,points in self.questions:
                cp={"quiz_id":exam_id,"question":q.text.strip(),"option1":opts[0].text.strip(),"option2":opts[1].text.strip(),"option3":opts[2].text.strip(),"option4":opts[3].text.strip(),"correct_answer":correct.text,"points":float(points.text or 1),"question_type":"multiple_choice"}
                self.app_state.api.table_insert("quiz_questions",cp)
            self.app_state.api.table_update("teacher_exams",{"id":f"eq.{exam_id}"},{"published":True})
            Clock.schedule_once(lambda *_: self._schedule_exam(exam_id,dur),0)
        except Exception as exc:
            print("EXAM SAVE ERROR",repr(exc)); Clock.schedule_once(lambda *_: self._set_error("ذخیره آزمون انجام نشد: "+str(exc)),0)

    def _schedule_exam(self,exam_id,dur):
        self.body.clear_widgets(); self._label("زمان‌بندی برگزاری", "20sp", PRIMARY, 50)
        self._label("یک آزمون مشترک می‌تواند برای هر کلاس زمان جدا داشته باشد یا همه کلاس‌ها با یک زمان هماهنگ برگزار شوند.", height=75)
        date=self._field("تاریخ شمسی؛ مثال 1405/07/01")
        start=self._field("ساعت شروع؛ مثال 10:00"); end=self._field("ساعت پایان؛ مثال 10:45"); end.text=""
        cls=self._field("نام کلاس؛ برای برگزاری مشترک می‌توانید «همه کلاس‌ها» بنویسید")
        coordinated=Spinner(text="برگزاری مستقل برای هر کلاس", values=("برگزاری مستقل برای هر کلاس","برگزاری هماهنگ برای همه کلاس‌ها"), size_hint_y=None,height=dp(48)); self.body.add_widget(coordinated)
        self._button("ثبت نوبت آزمون",lambda *_: self._save_slot(exam_id,dur,date,start,end,cls,coordinated),SUCCESS)
        self._button("افزودن نوبت دیگر",lambda *_: self._schedule_exam(exam_id,dur))
        self._button("بازگشت به آزمون‌ها",lambda *_: self._load_teacher_exams())

    def _save_slot(self,exam_id,dur,date,start,end,cls,coordinated):
        if not date.text.strip() or not start.text.strip() or not cls.text.strip(): self._set_error("تاریخ، ساعت شروع و کلاس را وارد کنید."); return
        try:
            h,m=[int(x) for x in start.text.strip().split(":")[:2]]; total=h*60+m+dur; end_text=end.text.strip() or f"{(total//60)%24:02d}:{total%60:02d}"
            payload={"quiz_id":exam_id,"class_name":cls.text.strip(),"exam_date_shamsi":date.text.strip(),"start_time_shamsi":start.text.strip(),"end_time_shamsi":end_text,"duration":dur,"coordinated":1 if coordinated.text.startswith("برگزاری هماهنگ") else 0,"secure_mode":1}
            self.app_state.api.table_insert("teacher_exam_slots",payload); self._success("نوبت آزمون ثبت شد؛ می‌توانید برای کلاس بعدی زمان دیگری ثبت کنید.")
        except Exception as exc: self._set_error("ثبت زمان‌بندی انجام نشد: "+str(exc))

    def _load_teacher_exams(self):
        self.body.clear_widgets(); self._label("آزمون‌های من", "20sp", PRIMARY, 50); self._label("آزمون‌ها از پایگاه داده مدرسه خوانده می‌شوند.",height=55)
        Thread(target=self._fetch_teacher_exams,daemon=True).start()

    def _fetch_teacher_exams(self):
        try:
            tid=self._teacher_id(); rows=self.app_state.api.table_select("teacher_exams",{"teacher_id":f"eq.{tid}","order":"created_at.desc","limit":"50"}) if tid else []
            Clock.schedule_once(lambda *_: self._render_teacher_exams(rows),0)
        except Exception as exc: Clock.schedule_once(lambda *_: self._set_error("دریافت آزمون‌ها انجام نشد: "+str(exc)),0)

    def _render_teacher_exams(self,rows):
        if not rows: self._label("هنوز آزمونی ثبت نشده است.",color=SECONDARY,height=70)
        for row in rows:
            self._label(f"{row.get('title','آزمون')} | {row.get('subject','')} | {row.get('duration',45)} دقیقه\nوضعیت: {'منتشر شده' if row.get('published') else 'پیش‌نویس'}",height=75)
            self._button("مدیریت زمان‌بندی",lambda _,eid=row.get("id"),dur=row.get("duration",45):self._schedule_exam(eid,int(dur or 45)),PRIMARY,42)
        self._button("ساخت آزمون جدید",lambda *_:self._new_exam(),SUCCESS)

    def _student_home(self):
        self._label("آزمون‌های آنلاین", "20sp", PRIMARY, 50)
        self._label("فقط آزمون‌هایی که دبیر منتشر کرده و زمان برگزاری آن‌ها فعال است در این بخش نمایش داده می‌شوند. ترتیب سؤال‌ها و گزینه‌ها برای هر دانش‌آموز می‌تواند متفاوت باشد.",height=90)
        self._button("دریافت آزمون‌های فعال",lambda *_:self._load_student_exams(),SUCCESS)

    def _load_student_exams(self):
        self.body.clear_widgets(); self._label("آزمون‌های فعال", "20sp", PRIMARY, 50)
        Thread(target=self._fetch_student_exams,daemon=True).start()

    def _fetch_student_exams(self):
        try:
            rows=self.app_state.api.table_select("teacher_exams",{"published":"eq.true","order":"created_at.desc","limit":"50"})
            Clock.schedule_once(lambda *_:self._render_student_exams(rows),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._set_error("آزمون‌های فعال دریافت نشد: "+str(exc)),0)

    def _render_student_exams(self,rows):
        if not rows: self._label("در حال حاضر آزمون فعالی برای شما ثبت نشده است.",height=70)
        for row in rows:
            self._label(f"{row.get('title','آزمون')}\nدرس: {row.get('subject','')} | مدت: {row.get('duration',45)} دقیقه",height=75)
            self._button("شروع آزمون",lambda _,qid=row.get("id"),dur=row.get("duration",45):self._start_exam(int(qid),int(dur or 45)),SUCCESS,44)

    def _start_exam(self,quiz_id,duration):
        self.body.clear_widgets(); self._label("آماده‌سازی آزمون...", "19sp", PRIMARY, 55)
        Thread(target=self._start_exam_worker,args=(quiz_id,duration),daemon=True).start()

    def _start_exam_worker(self,quiz_id,duration):
        try:
            username=getattr(self.app_state,"profile",{}).get("username") or self.app_state.national_code or getattr(self.app_state,"display_name","student")
            result=self.app_state.api.rpc("start_teacher_exam",{"p_quiz_id":quiz_id,"p_student_id":(getattr(self.app_state,"profile",{}).get("linked_student_id") or None),"p_student_username":username})
            attempt_id=int(result.get("attempt_id") if isinstance(result,dict) else result[0].get("attempt_id"))
            questions=self.app_state.api.rpc("get_teacher_exam_questions",{"p_attempt_id":attempt_id}) or []
            Clock.schedule_once(lambda *_:self._render_exam(attempt_id,questions,duration),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._set_error("شروع آزمون انجام نشد: "+str(exc)),0)

    def _render_exam(self,attempt_id,questions,duration):
        self.current_attempt=attempt_id; self.current_questions=list(questions); self.answers={}; self.body.clear_widgets(); self._label("آزمون تشخیصی", "20sp", PRIMARY, 50)
        warning=self._label("⛔ این سؤال/آزمون تشخیصی است. لطفاً برای پاسخ‌گویی به این سؤال در هیچ چتی گفتگو نکنید.\nترتیب سؤال‌ها و گزینه‌ها برای شما به‌صورت چرخشی نمایش داده می‌شود.",color=SECONDARY,height=82)
        self.remaining_seconds=max(1,int(duration))*60; self.timer_label=self._label("زمان باقی‌مانده: --:--","17sp",ERROR,45)
        random.shuffle(self.current_questions)
        for i,q in enumerate(self.current_questions,1):
            qid=int(q["id"] if isinstance(q,dict) else q.id); text=q.get("question","") if isinstance(q,dict) else q.question
            self._label(f"{i}) {text}","16sp",PRIMARY,82)
            values=[q.get("option1","") ,q.get("option2","") ,q.get("option3","") ,q.get("option4","")] if isinstance(q,dict) else [q.option1,q.option2,q.option3,q.option4]
            pairs=list(enumerate(values,1)); random.shuffle(pairs); group=[]
            for num,val in pairs:
                b=ToggleButton(text=rtl_text(f"گزینه {num}: {val}"),font_name=font_name(),font_size="14sp",size_hint_y=None,height=dp(48),group=f"q{qid}",background_normal="",background_color=(0.15,0.35,0.55,1),color=WHITE)
                b.bind(on_release=lambda btn,qid=qid,num=num:self._choose(qid,num)); self.body.add_widget(b); group.append(b)
            self.answer_buttons[qid]=group
        self._button("ثبت نهایی آزمون",lambda *_:self._submit_exam(),SUCCESS,52); self._timer=Clock.schedule_interval(self._tick,1)

    def _choose(self,qid,num): self.answers[int(qid)]=str(num)
    def _tick(self,dt):
        self.remaining_seconds-=1; m=max(0,self.remaining_seconds)//60; s=max(0,self.remaining_seconds)%60; self.timer_label.text=rtl_text(f"زمان باقی‌مانده: {m:02d}:{s:02d}")
        if self.remaining_seconds<=0: self._submit_exam()
    def _submit_exam(self):
        if not self.current_attempt: return
        self._stop_timer(); payload=[{"question_id":int(qid),"answer":str(ans)} for qid,ans in self.answers.items()]
        try:
            result=self.app_state.api.rpc("submit_teacher_exam",{"p_attempt_id":int(self.current_attempt),"p_answers":payload}); score=result.get("score",0) if isinstance(result,dict) else 0
            self.body.clear_widgets(); self._label("آزمون ثبت شد", "21sp", SUCCESS, 55); self._label(f"پاسخ‌های شما با موفقیت ثبت شد. نمره: {score}",height=70); self._button("بازگشت",lambda *_:self.show_home())
        except Exception as exc: self._set_error("ثبت آزمون انجام نشد: "+str(exc))

    def _stop_timer(self):
        if self._timer: self._timer.cancel(); self._timer=None
    def _set_error(self,text): self.status.text=rtl_text(text); self.status.color=ERROR
    def _success(self,text): self.status.text=rtl_text(text); self.status.color=SUCCESS
    def _back(self):
        self._stop_timer()
        if self.manager: self.manager.current="dashboard"
