import json
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView

from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, WEB_URL
from mobile.ui import font_name, rtl_text

TYPE_LABELS = {
    "multiple_choice": "تستی چهارگزینه‌ای",
    "true_false": "صحیح / غلط",
    "fill_blank": "جای خالی",
    "short_answer": "پاسخ کوتاه",
    "essay": "تشریحی",
}


def role_of(state):
    raw = str(getattr(state, "role", "student") or "student").strip().lower()
    return {"مدیر":"manager", "مدیریت":"manager", "معاون آموزشی":"educational", "معاون اجرایی":"executive", "معاون پرورشی":"cultural", "دبیر":"teacher", "معلم":"teacher", "دانش‌آموز":"student", "دانش آموز":"student", "ولی":"parent", "اولیا":"parent"}.get(raw, raw)


class TeacherExamsV2Screen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.questions = []
        self.exam_id = None
        self.exam_duration = 45
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        head = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        back = Button(text=rtl_text("‹ داشبورد"), font_name=font_name(), background_normal="", background_color=PRIMARY, color=WHITE, size_hint_x=None, width=dp(105))
        back.bind(on_release=lambda *_: self._back())
        head.add_widget(back)
        self.title = Label(text=rtl_text("مرکز آزمون آنلاین"), font_name=font_name(), font_size="21sp", bold=True, color=PRIMARY, halign="right", valign="middle")
        self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title)
        root.add_widget(head)
        self.status = Label(text="", font_name=font_name(), font_size="12sp", color=SECONDARY, halign="center", valign="middle", size_hint_y=None, height=dp(38))
        self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False)
        self.body=BoxLayout(orientation="vertical",spacing=dp(9),padding=[dp(4),dp(4)],size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll)
        self.add_widget(root)

    def _clear(self): self.body.clear_widgets()
    def _label(self,text,size="14sp",color=SECONDARY,height=52,bold=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="right",valign="middle",size_hint_y=None,height=dp(height)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w
    def _button(self,text,cb,color=PRIMARY,height=48):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="14sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(height)); b.bind(on_release=cb); self.body.add_widget(b); return b
    def _field(self,hint,height=50,multiline=False):
        f=TextInput(hint_text=rtl_text(hint),font_name=font_name(),font_size="14sp",multiline=multiline,size_hint_y=None,height=dp(height),halign="right",padding=[dp(12),dp(12)]); self.body.add_widget(f); return f
    def _error(self,text): self.status.text=rtl_text(text); self.status.color=ERROR
    def _ok(self,text): self.status.text=rtl_text(text); self.status.color=SUCCESS
    def _back(self):
        if self.manager:self.manager.current="dashboard"
    def on_pre_enter(self,*args): self.show_home()

    def show_home(self):
        self._clear(); self.title.text=rtl_text("مرکز آزمون آنلاین")
        if role_of(self.app_state)=="teacher":
            self._teacher_home()
        else:
            self._student_home()

    def _teacher_home(self):
        self._label("مرکز طراحی آزمون دبیر","22sp",PRIMARY,54,True)
        self._label("آزمون را یک‌بار طراحی کنید؛ برای کلاس‌های مختلف زمان مستقل بدهید و در صورت نیاز همان آزمون را با لینک امن برای دانش‌آموزان مدرسه دیگر به اشتراک بگذارید.",height=82)
        self._button("＋ ساخت آزمون استاندارد",lambda *_:self._new_exam(),SUCCESS)
        self._button("آزمون‌های من / زمان‌بندی / لینک‌ها",lambda *_:self._load_exams())

    def _student_home(self):
        self._label("آزمون آنلاین","22sp",PRIMARY,54,True)
        self._label("کد اشتراک یا لینک آزمون دبیر را وارد کنید. ترتیب سؤال‌ها و گزینه‌ها برای هر شرکت‌کننده تصادفی می‌شود.",height=70)
        code=self._field("کد اشتراک یا انتهای لینک")
        self._button("ورود به آزمون",lambda *_:self._open_shared(code.text.strip()),SUCCESS)

    def _new_exam(self):
        self._clear(); self.questions=[]; self._label("ساخت آزمون استاندارد","22sp",PRIMARY,52,True)
        title=self._field("عنوان آزمون")
        subject=Spinner(text="ریاضی",values=("ریاضی","فیزیک","شیمی","زیست","علوم","فارسی","انگلیسی","عربی","دینی","مطالعات اجتماعی","سایر"),size_hint_y=None,height=dp(50)); self.body.add_widget(subject)
        grade=self._field("پایه / رشته / کلاس")
        duration=self._field("مدت پیش‌فرض به دقیقه"); duration.text="45"
        desc=self._field("دستورالعمل آزمون",80,True)
        mode=Spinner(text="استاندارد",values=("استاندارد","تشخیصی"),size_hint_y=None,height=dp(50)); self.body.add_widget(mode)
        self._label("انواع سؤال: تستی، صحیح و غلط، جای خالی، پاسخ کوتاه و تشریحی. به جز تشریحی، سیستم خودکار تصحیح می‌کند.",color=PRIMARY,height=62)
        self._button("＋ افزودن سؤال",lambda *_:self._add_question(),SUCCESS)
        self._button("ذخیره آزمون",lambda *_:self._save_exam(title,subject,grade,duration,desc,mode),PRIMARY)
        self._button("انصراف",lambda *_:self.show_home())

    def _add_question(self):
        n=len(self.questions)+1
        self._label(f"سؤال {n}","17sp",PRIMARY,38,True)
        typ=Spinner(text="تستی چهارگزینه‌ای",values=tuple(TYPE_LABELS.values()),size_hint_y=None,height=dp(50)); self.body.add_widget(typ)
        q=self._field("متن سؤال؛ مثال ریاضی: √49 + 2² = ؟",82,True)
        difficulty=Spinner(text="متوسط",values=("آسان","متوسط","سخت","چالشی"),size_hint_y=None,height=dp(48)); self.body.add_widget(difficulty)
        cognitive=Spinner(text="دانش",values=("دانش","درک","کاربرد","تحلیل","ارزیابی"),size_hint_y=None,height=dp(48)); self.body.add_widget(cognitive)
        points=self._field("نمره سؤال"); points.text="1"
        opts=[self._field("گزینه ۱"),self._field("گزینه ۲"),self._field("گزینه ۳"),self._field("گزینه ۴")]
        correct=Spinner(text="گزینه ۱",values=("گزینه ۱","گزینه ۲","گزینه ۳","گزینه ۴"),size_hint_y=None,height=dp(48)); self.body.add_widget(correct)
        accepted=self._field("پاسخ‌های قابل قبول برای جای خالی/کوتاه؛ با | جدا کنید")
        self.questions.append((typ,q,difficulty,cognitive,points,opts,correct,accepted))
        self._label("پس‌زمینه امنیتی آزمون: لطفاً درباره پاسخ این سؤال در هیچ چتی گفتگو نشود.","10sp",SECONDARY,38)

    def _teacher_id(self):
        p=getattr(self.app_state,"profile",{}) or {}
        if p.get("linked_teacher_id"):
            try:return int(p["linked_teacher_id"])
            except Exception:pass
        try:
            rows=self.app_state.api.table_select("teachers",{"national_code":f"eq.{self.app_state.national_code}","select":"id","limit":"1"})
            return int(rows[0]["id"]) if rows else None
        except Exception:return None

    def _save_exam(self,title,subject,grade,duration,desc,mode):
        if not title.text.strip() or not self.questions:self._error("عنوان آزمون و حداقل یک سؤال لازم است.");return
        try:dur=max(1,int(duration.text.strip() or 45))
        except Exception:self._error("مدت آزمون باید عدد باشد.");return
        tid=self._teacher_id()
        if not tid:self._error("حساب دبیر به پرونده دبیر متصل نشده است.");return
        payload={"teacher_id":tid,"title":title.text.strip(),"subject":subject.text,"grade":grade.text.strip(),"class_name":grade.text.strip(),"exam_type":"آزمون آنلاین","duration":dur,"description":desc.text.strip(),"published":False,"secure_mode":True,"standard_mode":mode.text=="استاندارد","max_attempts":1,"passing_score":0}
        self.status.text=rtl_text("در حال ذخیره آزمون و سؤال‌ها..."); self.status.color=SECONDARY
        Thread(target=self._save_worker,args=(payload,dur),daemon=True).start()

    def _save_worker(self,payload,dur):
        try:
            created=self.app_state.api.table_insert("teacher_exams",payload); row=created[0] if isinstance(created,list) else created; exam_id=int(row["id"])
            for typ,q,difficulty,cognitive,points,opts,correct,accepted in self.questions:
                kind=next((k for k,v in TYPE_LABELS.items() if v==typ.text),"multiple_choice")
                values=[x.text.strip() for x in opts]
                if kind=="true_false":values=["صحیح","غلط"]
                correct_value=correct.text if kind=="multiple_choice" else ("صحیح" if kind=="true_false" and correct.text=="گزینه ۱" else ("غلط" if kind=="true_false" else ""))
                self.app_state.api.table_insert("quiz_questions",{"quiz_id":exam_id,"question":q.text.strip(),"option1":values[0] if values else "","option2":values[1] if len(values)>1 else "","option3":values[2] if len(values)>2 else "","option4":values[3] if len(values)>3 else "","correct_answer":correct_value,"points":float(points.text or 1),"question_type":kind,"options_json":json.dumps(values,ensure_ascii=False),"accepted_answers":accepted.text.strip(),"difficulty":difficulty.text,"cognitive_level":cognitive.text,"auto_grade":kind!="essay"})
            self.app_state.api.table_update("teacher_exams",{"id":f"eq.{exam_id}"},{"published":True})
            Clock.schedule_once(lambda *_:self._schedule(exam_id,dur),0)
        except Exception as exc:Clock.schedule_once(lambda *_:self._error("ذخیره آزمون انجام نشد: "+str(exc)),0)

    def _schedule(self,exam_id,dur):
        self._clear(); self._label("زمان‌بندی و اشتراک","22sp",PRIMARY,52,True)
        self._label("برای هر کلاس نوبت جدا بسازید. برای مدرسه دیگر لینک اشتراک بسازید و مدت/زمان همان لینک را مستقل تعیین کنید.",height=70)
        cls=self._field("کلاس یا همه کلاس‌ها")
        date=self._field("تاریخ شمسی؛ مثال 1405/07/01")
        start=self._field("ساعت شروع؛ مثال 10:00")
        end=self._field("ساعت پایان؛ اختیاری")
        self._button("ثبت نوبت این کلاس",lambda *_:self._slot(exam_id,dur,cls,date,start,end),SUCCESS)
        self._button("＋ لینک اشتراک برای مدرسه دیگر",lambda *_:self._share_form(exam_id,dur),PRIMARY)
        self._button("بازگشت",lambda *_:self._load_exams())

    def _slot(self,exam_id,dur,cls,date,start,end):
        if not cls.text.strip() or not date.text.strip() or not start.text.strip():self._error("کلاس، تاریخ و ساعت شروع لازم است.");return
        try:
            h,m=[int(x) for x in start.text.strip().split(":")[:2]]; total=h*60+m+dur; et=end.text.strip() or f"{(total//60)%24:02d}:{total%60:02d}"
            self.app_state.api.table_insert("teacher_exam_slots",{"quiz_id":exam_id,"class_name":cls.text.strip(),"exam_date_shamsi":date.text.strip(),"start_time_shamsi":start.text.strip(),"end_time_shamsi":et,"duration":dur,"coordinated":0,"secure_mode":1,"active":True})
            self._ok("نوبت ثبت شد. برای کلاس بعدی می‌توانید زمان دیگری تعیین کنید.")
        except Exception as exc:self._error("ثبت نوبت انجام نشد: "+str(exc))

    def _share_form(self,exam_id,dur):
        self._clear(); self._label("ساخت لینک اشتراک","22sp",PRIMARY,52,True)
        school=self._field("نام یا شناسه مدرسه مقصد؛ اختیاری")
        cls=self._field("کلاس مقصد؛ اختیاری")
        start=self._field("شروع؛ YYYY-MM-DD HH:MM؛ اختیاری")
        end=self._field("پایان؛ YYYY-MM-DD HH:MM؛ اختیاری")
        duration=self._field("مدت این اشتراک به دقیقه"); duration.text=str(dur)
        self._button("تولید لینک",lambda *_:self._create_share(exam_id,school,cls,start,end,duration),SUCCESS)
        self._button("بازگشت",lambda *_:self._schedule(exam_id,dur))

    def _iso(self,value):
        t=(value or "").strip()
        if not t:return None
        return t.replace(" ","T")+":00+03:30" if len(t)==16 else t

    def _create_share(self,exam_id,school,cls,start,end,duration):
        try:dm=max(1,int(duration.text.strip() or self.exam_duration))
        except Exception:self._error("مدت باید عدد باشد.");return
        try:
            row=self.app_state.api.table_insert("teacher_exam_shares",{"quiz_id":exam_id,"shared_by_teacher_id":self._teacher_id(),"target_school_id":school.text.strip() or None,"target_class_name":cls.text.strip() or None,"start_at":self._iso(start.text),"end_at":self._iso(end.text),"duration_minutes":dm,"active":True})
            item=row[0] if isinstance(row,list) else row; code=item.get("share_code")
            link=f"{WEB_URL}/exam/{code}"
            self._clear(); self._label("لینک اشتراک آماده است","22sp",SUCCESS,52,True); self._label("کد: "+str(code),"16sp",PRIMARY,50,True); self._label(link,"12sp",SECONDARY,70); self._label("این لینک همان آزمون را در مدرسه مقصد اجرا می‌کند و زمان/مدت آن مستقل است.",height=65); self._button("ساخت اشتراک دیگر",lambda *_:self._share_form(exam_id,dm),PRIMARY); self._button("بازگشت",lambda *_:self._load_exams())
        except Exception as exc:self._error("تولید لینک انجام نشد: "+str(exc))

    def _load_exams(self):
        self._clear(); self._label("آزمون‌های من","22sp",PRIMARY,52,True)
        try:
            tid=self._teacher_id(); rows=self.app_state.api.table_select("teacher_exams",{"teacher_id":f"eq.{tid}","order":"created_at.desc","limit":"50"}) if tid else []
            if not rows:self._label("هنوز آزمونی ثبت نشده است.",height=60)
            for row in rows:
                eid=int(row["id"]); dur=int(row.get("duration") or 45)
                self._label(f"{row.get('title','آزمون')}  •  {row.get('subject','')}  •  {dur} دقیقه\n{'منتشر شده' if row.get('published') else 'پیش‌نویس'}",height=68, bold=True)
                self._button("زمان‌بندی / لینک اشتراک",lambda *_e,eid=eid,dur=dur:self._schedule(eid,dur),PRIMARY,44)
        except Exception as exc:self._error("دریافت آزمون‌ها انجام نشد: "+str(exc))

    def _open_shared(self,code):
        code=(code or "").strip().rstrip("/").split("/")[-1]
        if not code:self._error("کد اشتراک را وارد کنید.");return
        try:
            exam=self.app_state.api.rpc("get_shared_exam",{"p_share_code":code}); exam=exam[0] if isinstance(exam,list) and exam else exam
            if not exam:raise RuntimeError("آزمون پیدا نشد یا زمان آن فعال نیست.")
            qs=self.app_state.api.rpc("get_shared_exam_questions",{"p_share_code":code}) or []
            self._render_student_exam(code,exam,qs)
        except Exception as exc:self._error(str(exc))

    def _render_student_exam(self,code,exam,qs):
        self._clear(); self._label(exam.get("title","آزمون"),"22sp",PRIMARY,52,True)
        self._label(f"{exam.get('subject','')}  •  مدت {exam.get('duration',45)} دقیقه",height=45)
        for i,q in enumerate(qs,1):
            self._label(f"{i}. {q.get('question','')}","16sp",PRIMARY,82,True)
            if q.get("question_type")=="essay":self._field("پاسخ تشریحی...",110,True)
            elif q.get("question_type") in ("fill_blank","short_answer"):self._field("پاسخ شما...")
            else:
                try:opts=json.loads(q.get("options_json") or "[]")
                except Exception:opts=[]
                for op in opts:self._button(str(op),lambda *_:None,PRIMARY,44)
            self._label("▧  آزمون ارزیابی است؛ لطفاً درباره پاسخ این سؤال در هیچ چتی گفتگو نکنید.","10sp",SECONDARY,38)
        self._button("پایان آزمون",lambda *_:self._ok("آزمون برای تصحیح و ثبت نتیجه آماده شد."),SUCCESS)
