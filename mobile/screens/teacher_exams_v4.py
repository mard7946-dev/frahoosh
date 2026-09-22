import json
from datetime import datetime, timezone
from threading import Thread

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
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

TYPES = [
    ("multiple_choice", "تستی چهارگزینه‌ای"),
    ("true_false", "صحیح و غلط"),
    ("fill_blank", "جای خالی"),
    ("short_answer", "پاسخ کوتاه"),
    ("essay", "سؤال تشریحی"),
]
TYPE_TO_LABEL = dict(TYPES)
LABEL_TO_TYPE = {v: k for k, v in TYPES}


def role_of(state):
    # Resolve the role from the authenticated profile as well as app_state.
    # This keeps the teacher exam authoring controls visible after login.
    profile = getattr(state, "profile", {}) or {}
    candidates = [
        getattr(state, "role", None),
        profile.get("role"),
        profile.get("user_role"),
        profile.get("permissions", {}).get("role") if isinstance(profile.get("permissions"), dict) else None,
    ]
    raw = next((str(v).strip().lower() for v in candidates if str(v or "").strip()), "student")
    return {
        "admin":"manager", "administrator":"manager", "principal":"manager",
        "manager":"manager", "مدیر":"manager", "مدیریت":"manager",
        "معاون آموزشی":"educational", "educational":"educational",
        "معاون اجرایی":"executive", "اجرایی":"executive", "executive":"executive",
        "معاون پرورشی":"cultural", "پرورشی":"cultural", "cultural":"cultural",
        "دبیر":"teacher", "معلم":"teacher", "teacher_staff":"teacher",
        "teacher":"teacher", "teachers":"teacher",
        "دانش‌آموز":"student", "دانش آموز":"student", "student":"student",
        "ولی":"parent", "اولیا":"parent", "parent":"parent", "parents":"parent",
    }.get(raw, raw)


class _SecurityNote(BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(10), dp(3)], size_hint_y=None, height=dp(43), **kwargs)
        with self.canvas.before:
            Color(0.94, 0.95, 0.97, 1)
            self.bg = RoundedRectangle(radius=[dp(9)])
        self.bind(pos=lambda o,v:setattr(self.bg,"pos",v), size=lambda o,v:setattr(self.bg,"size",v))
        label=Label(text=rtl_text(text), font_name=font_name(), font_size="9sp", color=SECONDARY,
                    halign="right", valign="middle")
        label.bind(size=lambda o,v:setattr(o,"text_size",v)); self.add_widget(label)


class TeacherExamsV4Screen(Screen):
    """Full online exam center: standard question types, scheduling and secure sharing."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state=app_state; self.questions=[]; self._build(); self._answers={}; self._attempt_id=None

    def _build(self):
        root=BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        head=BoxLayout(size_hint_y=None,height=dp(54),spacing=dp(8))
        back=Button(text=rtl_text("‹ داشبورد"),font_name=font_name(),font_size="13sp",background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(105))
        back.bind(on_release=lambda *_:self._back()); head.add_widget(back)
        self.title=Label(text=rtl_text("مرکز آزمون آنلاین"),font_name=font_name(),font_size="21sp",bold=True,color=PRIMARY,halign="right",valign="middle")
        self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title); root.add_widget(head)
        self.status=Label(text="",font_name=font_name(),font_size="11sp",color=SECONDARY,halign="center",valign="middle",size_hint_y=None,height=dp(38))
        self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False); self.body=BoxLayout(orientation="vertical",spacing=dp(9),padding=[dp(3),dp(4)],size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root)

    def _clear(self): self.body.clear_widgets()
    def _label(self,text,size="14sp",color=SECONDARY,height=52,bold=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="right",valign="middle",size_hint_y=None,height=dp(height)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w
    def _button(self,text,cb,color=PRIMARY,height=48):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="13sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(height)); b.bind(on_release=cb); self.body.add_widget(b); return b
    def _field(self,hint,height=50,multiline=False):
        f=TextInput(hint_text=rtl_text(hint),font_name=font_name(),font_size="13sp",multiline=multiline,size_hint_y=None,height=dp(height),halign="right",padding=[dp(12),dp(12)]); self.body.add_widget(f); return f
    def _spinner(self,text,values):
        s=Spinner(text=rtl_text(text),values=tuple(rtl_text(x) for x in values),font_name=font_name(),font_size="13sp",size_hint_y=None,height=dp(50)); self.body.add_widget(s); return s
    def _error(self,text): self.status.text=rtl_text(text); self.status.color=ERROR
    def _ok(self,text): self.status.text=rtl_text(text); self.status.color=SUCCESS
    def _back(self):
        if self.manager:self.manager.current="dashboard"
    def on_pre_enter(self,*args): self.show_home()

    def show_home(self):
        self._clear(); self.title.text=rtl_text("مرکز آزمون آنلاین")
        if role_of(self.app_state)=="teacher":
            self._label("مرکز طراحی و مدیریت آزمون","22sp",PRIMARY,54,True)
            self._label("آزمون را یک‌بار استاندارد طراحی کنید، سپس برای هر کلاس زمان متفاوت بدهید یا همان آزمون را با لینک امن برای دانش‌آموزان مدرسه دیگر به اشتراک بگذارید.",height=78)
            self._button("＋ ساخت آزمون جدید",lambda *_:self._new_exam(),SUCCESS)
            self._button("آزمون‌های من و زمان‌بندی‌ها",lambda *_:self._load_exams())
        else:
            self._label("ورود به آزمون","22sp",PRIMARY,54,True)
            self._label("کد اشتراک یا لینک آزمون دبیر را وارد کنید. برای هر دانش‌آموز ترتیب سؤال‌ها و گزینه‌ها مستقل می‌شود.",height=72)
            code=self._field("کد اشتراک یا لینک آزمون")
            self._button("شروع آزمون",lambda *_:self._open_shared(code.text.strip()),SUCCESS)
            self._label("آزمون‌های فعال مدرسه نیز در همین بخش نمایش داده می‌شوند.","10sp",SECONDARY,42)

    def _new_exam(self):
        self._clear(); self.questions=[]; self._label("ساخت آزمون استاندارد","22sp",PRIMARY,52,True)
        title=self._field("عنوان آزمون")
        subject=self._spinner("ریاضی",["ریاضی","فیزیک","شیمی","زیست","علوم","فارسی","انگلیسی","عربی","دینی","مطالعات اجتماعی","سایر"])
        grade=self._field("پایه / رشته")
        duration=self._field("مدت پیش‌فرض آزمون (دقیقه)"); duration.text="45"
        attempts=self._field("حداکثر تعداد شرکت هر دانش‌آموز"); attempts.text="1"
        passing=self._field("نمره قبولی (اختیاری)"); passing.text="0"
        mode=self._spinner("استاندارد",["استاندارد","تشخیصی"])
        desc=self._field("دستورالعمل آزمون",82,True)
        self._label("انواع سؤال قابل انتخاب: تستی، صحیح و غلط، جای خالی، پاسخ کوتاه و تشریحی. به جز تشریحی، تصحیح خودکار انجام می‌شود.","11sp",PRIMARY,65)
        self._button("＋ افزودن سؤال",lambda *_:self._add_question(),SUCCESS)
        self._button("ذخیره آزمون و رفتن به زمان‌بندی",lambda *_:self._save_exam(title,subject,grade,duration,attempts,passing,mode,desc),PRIMARY)
        self._button("انصراف",lambda *_:self.show_home())

    def _add_question(self):
        n=len(self.questions)+1
        self._label(f"سؤال {n}","17sp",PRIMARY,38,True)
        typ=self._spinner("تستی چهارگزینه‌ای",[v for _,v in TYPES])
        q=self._field("متن سؤال؛ برای ریاضی: √49 + 2² = ؟",82,True)
        # Formula toolbar for the teacher: symbols are inserted directly into
        # the question editor, so scientific notation does not depend on a
        # separate keyboard or chat assistant.
        toolbar=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(4))
        for symbol in ("√", "²", "³", "ⁿ", "÷", "×", "±", "π", "∞", "≠", "≤", "≥", "∑"):
            b=Button(text=symbol,font_name=font_name(),font_size="15sp",
                     background_normal="",background_color=PRIMARY,color=WHITE,
                     size_hint_x=None,width=dp(42))
            b.bind(on_release=lambda *_a,s=symbol:self._insert_formula(q,s))
            toolbar.add_widget(b)
        self.body.add_widget(toolbar)
        difficulty=self._spinner("متوسط",["آسان","متوسط","سخت","چالشی"])
        cognitive=self._spinner("دانش",["دانش","درک","کاربرد","تحلیل","ارزیابی"])
        points=self._field("نمره سؤال"); points.text="1"
        opts=[self._field("گزینه ۱"),self._field("گزینه ۲"),self._field("گزینه ۳"),self._field("گزینه ۴")]
        correct=self._spinner("گزینه ۱",["گزینه ۱","گزینه ۲","گزینه ۳","گزینه ۴"])
        accepted=self._field("پاسخ‌های قابل قبول برای جای خالی/کوتاه؛ با | جدا کنید")
        negative=self._field("نمره منفی در پاسخ غلط (اختیاری)"); negative.text="0"
        self.questions.append({"typ":typ,"q":q,"difficulty":difficulty,"cognitive":cognitive,"points":points,"opts":opts,"correct":correct,"accepted":accepted,"negative":negative})
        self._body_refresh_question_visibility(self.questions[-1])
        self._label("راهنما: برای تستی چهار گزینه را پر کنید؛ برای صحیح/غلط سیستم گزینه‌ها را تنظیم می‌کند؛ برای جای خالی و پاسخ کوتاه، پاسخ‌های پذیرفته‌شده را با | جدا کنید.","10sp",SECONDARY,54)
        self.body.add_widget(_SecurityNote("این سؤال بخشی از یک آزمون تشخیصی/ارزیابی است؛ لطفاً درباره پاسخ آن در هیچ چتی گفتگو نکنید."))
        typ.bind(text=lambda *_:self._body_refresh_question_visibility(self.questions[-1]))

    @staticmethod
    def _insert_formula(field, symbol):
        try:
            field.insert_text(symbol)
            field.focus = True
        except Exception:
            try:
                field.text = (field.text or "") + symbol
            except Exception:
                pass

    def _body_refresh_question_visibility(self,item):
        kind=LABEL_TO_TYPE.get(item["typ"].text, "multiple_choice")
        mc=kind=="multiple_choice"; tf=kind=="true_false"; needs_text=kind in ("fill_blank","short_answer")
        for w in item["opts"]: w.opacity=1 if mc or tf else 0; w.disabled=not (mc or tf)
        item["correct"].opacity=1 if mc or tf else 0; item["correct"].disabled=not (mc or tf)
        item["accepted"].opacity=1 if needs_text else 0; item["accepted"].disabled=not needs_text
        item["negative"].opacity=1; item["negative"].disabled=False
        if tf:
            item["opts"][0].text="صحیح"; item["opts"][1].text="غلط"; item["opts"][2].text=""; item["opts"][3].text=""
            item["correct"].values=(rtl_text("صحیح"),rtl_text("غلط")); item["correct"].text=rtl_text("صحیح")
        elif mc:
            item["correct"].values=(rtl_text("گزینه ۱"),rtl_text("گزینه ۲"),rtl_text("گزینه ۳"),rtl_text("گزینه ۴"))
            if not item["correct"].text.startswith("گزینه"): item["correct"].text=rtl_text("گزینه ۱")

    def _teacher_id(self):
        p=getattr(self.app_state,"profile",{}) or {}
        try:
            if p.get("linked_teacher_id"): return int(p["linked_teacher_id"])
        except Exception: pass
        try:
            rows=self.app_state.api.table_select("teachers",{"national_code":f"eq.{self.app_state.national_code}","select":"id","limit":"1"})
            return int(rows[0]["id"]) if rows else None
        except Exception:return None

    def _save_exam(self,title,subject,grade,duration,attempts,passing,mode,desc):
        if not title.text.strip() or not self.questions:self._error("عنوان آزمون و حداقل یک سؤال لازم است.");return
        try: dur=max(1,min(600,int(duration.text.strip() or 45))); mx=max(1,int(attempts.text.strip() or 1)); ps=max(0,float(passing.text.strip() or 0))
        except Exception:self._error("مدت، تعداد دفعات و نمره قبولی باید عدد باشند.");return
        tid=self._teacher_id()
        if not tid:self._error("حساب دبیر به پرونده دبیر متصل نشده است.");return
        self.status.text=rtl_text("در حال ذخیره آزمون…"); self.status.color=SECONDARY
        payload={"teacher_id":tid,"title":title.text.strip(),"subject":subject.text,"grade":grade.text.strip(),"class_name":grade.text.strip(),"exam_type":"آزمون آنلاین","duration":dur,"description":desc.text.strip(),"published":False,"secure_mode":True,"standard_mode":mode.text==rtl_text("استاندارد"),"max_attempts":mx,"passing_score":ps}
        Thread(target=self._save_worker,args=(payload,dur),daemon=True).start()

    def _save_worker(self,payload,dur):
        try:
            created=self.app_state.api.table_insert("teacher_exams",payload); row=created[0] if isinstance(created,list) else created; eid=int(row["id"])
            for item in self.questions:
                kind=LABEL_TO_TYPE.get(item["typ"].text,"multiple_choice")
                values=[w.text.strip() for w in item["opts"]]
                if kind=="true_false": values=["صحیح","غلط"]
                correct=item["correct"].text.strip() if kind in ("multiple_choice","true_false") else ""
                try: pts=float(item["points"].text or 1); neg=float(item["negative"].text or 0)
                except Exception: pts=1; neg=0
                payload_q={"quiz_id":eid,"question":item["q"].text.strip(),"option1":values[0] if values else "","option2":values[1] if len(values)>1 else "","option3":values[2] if len(values)>2 else "","option4":values[3] if len(values)>3 else "","correct_answer":correct,"points":pts,"question_type":kind,"options_json":json.dumps(values,ensure_ascii=False),"accepted_answers":item["accepted"].text.strip(),"difficulty":item["difficulty"].text,"cognitive_level":item["cognitive"].text,"auto_grade":kind!="essay","negative_score":neg}
                self.app_state.api.table_insert("quiz_questions",payload_q)
            self.app_state.api.table_update("teacher_exams",{"id":f"eq.{eid}"},{"published":True})
            Clock.schedule_once(lambda *_:self._schedule(eid,dur),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._error("ذخیره آزمون انجام نشد: "+str(exc)),0)

    def _schedule(self,eid,dur):
        self._clear(); self._label("زمان‌بندی آزمون","22sp",PRIMARY,52,True)
        self._label("یک آزمون را برای چند کلاس با زمان مشترک یا برای هر کلاس با زمان متفاوت منتشر کنید.",height=65)
        cls=self._field("کلاس‌ها با زمان مشترک: هفتم-الف، هفتم-ب، هفتم-ج")
        per=self._field("زمان متفاوت اختیاری: هفتم-الف=10:00؛ هفتم-ب=11:00؛ هفتم-ج=10:00",78,True)
        date=self._field("تاریخ شمسی؛ مثال 1405/07/01"); start=self._field("ساعت شروع مشترک؛ مثال 10:00"); end=self._field("ساعت پایان مشترک؛ اگر خالی باشد از مدت محاسبه می‌شود")
        self._label("کلاس‌های بدون زمان اختصاصی از زمان مشترک استفاده می‌کنند. کلاس‌های دارای «=» زمان خودشان را می‌گیرند.","10sp",SECONDARY,55)
        self._button("ثبت زمان‌بندی کلاس‌ها",lambda *_:self._save_slot(eid,dur,cls,per,date,start,end),SUCCESS)
        self._button("＋ ساخت لینک انتشار برای مدرسه دیگر",lambda *_:self._share_form(eid,dur),PRIMARY)
        self._button("بازگشت به آزمون‌های من",lambda *_:self._load_exams())
    def _save_slot(self,eid,dur,cls,per,date,start,end):
        if not date.text.strip():self._error("تاریخ آزمون لازم است.");return
        common=start.text.strip(); common_end=end.text.strip()
        try:
            if common and not common_end:
                h,m=[int(x) for x in common.split(":")[:2]]; t=h*60+m+dur; common_end=f"{(t//60)%24:02d}:{t%60:02d}"
            mapping={}
            for part in (per.text or "").replace("،",",").replace("؛",";").split(";"):
                part=part.strip()
                if not part or "=" not in part:continue
                name,window=part.split("=",1); bits=window.strip().split("-",1); mapping[name.strip()]=(bits[0].strip(),bits[1].strip() if len(bits)>1 else "")
            classes=[x.strip() for x in (cls.text or "").replace("،",",").split(",") if x.strip()]
            classes += [x for x in mapping if x not in classes]
            if not classes:classes=list(mapping)
            if not classes:raise RuntimeError("حداقل یک کلاس لازم است.")
            starts={}
            for name in classes:
                st,en=mapping.get(name,(common,common_end));
                if not st:raise RuntimeError(f"زمان شروع کلاس «{name}» مشخص نیست.")
                if not en:
                    h,m=[int(x) for x in st.split(":")[:2]]; t=h*60+m+dur; en=f"{(t//60)%24:02d}:{t%60:02d}"
                starts[name]=st
                self.app_state.api.table_insert("teacher_exam_slots",{"quiz_id":eid,"class_name":name,"exam_date_shamsi":date.text.strip(),"start_time_shamsi":st,"end_time_shamsi":en,"duration":dur,"coordinated":1 if len(set(starts.values()))==1 and len(starts)==len(classes) else 0,"secure_mode":1,"active":True})
            self._ok(f"زمان‌بندی {len(classes)} کلاس ثبت شد؛ زمان مشترک یا متفاوت قابل استفاده است.")
        except Exception as exc:self._error("ثبت زمان‌بندی انجام نشد: "+str(exc))

    def _share_form(self,eid,dur):
        self._clear(); self._label("لینک اشتراک امن آزمون","22sp",PRIMARY,52,True)
        self._label("این آزمون می‌تواند برای دانش‌آموزان مدرسه دیگر هم قابل استفاده باشد. زمان شروع، پایان، مدرسه هدف، کلاس هدف و مدت این اشتراک مستقل از آزمون اصلی است.",height=82)
        school=self._field("شناسه یا نام مدرسه مقصد (اختیاری)")
        cls=self._field("کلاس مقصد (اختیاری)")
        start=self._field("شروع اشتراک؛ مثال 2026-09-20T08:00:00+03:30 (اختیاری)")
        end=self._field("پایان اشتراک؛ مثال 2026-09-20T09:00:00+03:30 (اختیاری)")
        d=self._field("مدت این اشتراک به دقیقه"); d.text=str(dur)
        self._button("ساخت لینک اشتراک",lambda *_:self._create_share(eid,school,cls,start,end,d),SUCCESS)
        self._button("بازگشت",lambda *_:self._schedule(eid,dur))

    def _create_share(self,eid,school,cls,start,end,d):
        try: minutes=max(1,min(600,int(d.text.strip() or 45)))
        except Exception:self._error("مدت اشتراک باید عدد باشد.");return
        try:
            s=self._parse_dt(start.text.strip()); e=self._parse_dt(end.text.strip())
            result=self.app_state.api.rpc("create_teacher_exam_share",{"p_quiz_id":eid,"p_target_school_id":school.text.strip(),"p_target_class_name":cls.text.strip(),"p_start_at":s,"p_end_at":e,"p_duration_minutes":minutes})
            row=result[0] if isinstance(result,list) else result; code=str(row.get("share_code") or "").strip()
            if not code: raise RuntimeError("کد اشتراک ساخته نشد.")
            link=f"{WEB_URL}/exam/share/{code}"
            Clipboard.copy(link)
            self._clear(); self._label("لینک اشتراک آماده شد","22sp",SUCCESS,52,True)
            self._label("لینک زیر برای شما کپی شد. می‌توانید آن را برای دانش‌آموزان یا دبیران مدرسه مقصد ارسال کنید.",height=65)
            self._field("لینک اشتراک")
            self.body.children[0].text=link
            self._label(f"کد اشتراک: {code}\nمدت: {minutes} دقیقه\nمدرسه مقصد: {school.text.strip() or 'بدون محدودیت'}\nکلاس مقصد: {cls.text.strip() or 'بدون محدودیت'}",height=100)
            self._button("کپی دوباره لینک",lambda *_:Clipboard.copy(link),PRIMARY)
            self._button("ساخت اشتراک جدید با زمان دیگر",lambda *_:self._share_form(eid,minutes),SUCCESS)
            self._button("بازگشت",lambda *_:self._load_exams())
        except Exception as exc:self._error("ساخت لینک انجام نشد: "+str(exc))

    @staticmethod
    def _parse_dt(value):
        if not value:return None
        v=value.replace(" ","T")
        if v.endswith("Z"):v=v[:-1]+"+00:00"
        try:return datetime.fromisoformat(v).astimezone(timezone.utc).isoformat()
        except Exception:raise RuntimeError("زمان باید به قالب ISO مانند 2026-09-20T08:00:00+03:30 باشد.")

    def _load_exams(self):
        self._clear(); self._label("آزمون‌های من","22sp",PRIMARY,52,True); self._label("آزمون‌ها و نوبت‌های ثبت‌شده از پایگاه داده خوانده می‌شوند.",height=50)
        Thread(target=self._fetch_exams,daemon=True).start()

    def _fetch_exams(self):
        try:
            tid=self._teacher_id(); rows=self.app_state.api.table_select("teacher_exams",{"teacher_id":f"eq.{tid}","order":"created_at.desc","limit":"50"}) if tid else []
            Clock.schedule_once(lambda *_:self._render_exams(rows),0)
        except Exception as exc:Clock.schedule_once(lambda *_:self._error("دریافت آزمون‌ها انجام نشد: "+str(exc)),0)

    def _render_exams(self,rows):
        if not rows:self._label("هنوز آزمونی ثبت نشده است.",color=SECONDARY,height=65)
        for row in rows:
            eid=int(row["id"]); dur=int(row.get("duration") or 45)
            self._label(f"{row.get('title','آزمون')}\n{row.get('subject','')}  •  {dur} دقیقه  •  {'منتشر شده' if row.get('published') else 'پیش‌نویس'}","15sp",PRIMARY,65,True)
            self._button("زمان‌بندی / ساخت لینک اشتراک",lambda *_ ,i=eid,d=dur:self._schedule(i,d),PRIMARY,45)

    def _open_shared(self,code):
        code=(code or "").strip().rstrip("/").split("/")[-1]
        if not code:self._error("کد یا لینک آزمون را وارد کنید.");return
        try:
            exam=self.app_state.api.rpc("get_shared_exam",{"p_share_code":code}); exam=exam[0] if isinstance(exam,list) and exam else exam
            if not exam:raise RuntimeError("آزمون پیدا نشد یا در این زمان فعال نیست.")
            p=getattr(self.app_state,"profile",{}) or {}; student_id=p.get("linked_student_id")
            try:student_id=int(student_id) if student_id else None
            except Exception:student_id=None
            username=str(p.get("username") or getattr(self.app_state,"national_code","") or "").strip()
            if not username:raise RuntimeError("شناسه کاربر برای شروع آزمون مشخص نیست.")
            eligible, reason = self._check_exam_eligibility(student_id)
            if not eligible:
                raise RuntimeError(reason)
            attempt=self.app_state.api.rpc("start_shared_teacher_exam",{"p_share_code":code,"p_student_id":student_id,"p_student_username":username}); attempt=attempt[0] if isinstance(attempt,list) and attempt else attempt
            self._render_attempt(exam,attempt)
        except Exception as exc:self._error(str(exc))

    def _check_exam_eligibility(self, student_id):
        if not student_id:
            return True, ""
        try:
            today=datetime.now().strftime("%Y-%m-%d")
            attendance=self.app_state.api.table_select("attendance",{
                "student_id":f"eq.{student_id}","date":f"eq.{today}","limit":"20"
            }) or []
            if any(str(r.get("status","")).lower() in ("absent","غایب","failed") for r in attendance):
                return False, "به دلیل غیبت ثبت‌شده امروز، امکان شرکت در آزمون وجود ندارد."
            online=self.app_state.api.table_select("online_attendance",{
                "student_id":f"eq.{student_id}","limit":"100"
            }) or []
            failed=[r for r in online if "failed" in str(r.get("status","")).lower() or "عدم" in str(r.get("status",""))]
            exits=sum(1 for r in online if r.get("leave_time"))
            if failed:
                return False, "به دلیل عدم تأیید حضور در کلاس آنلاین، امکان شرکت در آزمون وجود ندارد."
            if exits > 2:
                return False, "به دلیل خروج بیش از حد ثبت‌شده از کلاس‌های آنلاین، امکان شرکت در آزمون وجود ندارد."
            return True, ""
        except Exception as exc:
            print("EXAM ELIGIBILITY CHECK ERROR:", repr(exc))
            # Do not silently block a student when the attendance service is
            # temporarily unavailable; the server-side exam RPC remains the
            # authoritative security boundary.
            return True, ""

    def _render_attempt(self,exam,attempt):
        self._clear(); self._attempt_id=int(attempt["attempt_id"]); self._answers={}
        self._label(exam.get("title","آزمون"),"22sp",PRIMARY,55,True)
        self._label(f"{exam.get('subject','')}  •  مدت {attempt.get('duration') or exam.get('duration',45)} دقیقه\nترتیب سؤال‌ها برای شما اختصاصی است و پاسخ صحیح نمایش داده نمی‌شود.",height=72)
        qs=self.app_state.api.rpc("get_shared_attempt_questions",{"p_attempt_id":self._attempt_id}) or []
        for i,q in enumerate(qs,1):
            self._label(f"{i}. {q.get('question','')}","16sp",PRIMARY,82,True)
            qid=int(q["id"]); kind=q.get("question_type")
            if kind in ("multiple_choice","true_false"):
                try:opts=json.loads(q.get("options_json") or "[]")
                except Exception:opts=[]
                w=Spinner(text=str(opts[0]) if opts else "انتخاب پاسخ",values=tuple(str(x) for x in opts),font_name=font_name(),font_size="13sp",size_hint_y=None,height=dp(50)); self.body.add_widget(w)
            elif kind=="essay": w=self._field("پاسخ تشریحی…",120,True)
            else:w=self._field("پاسخ شما…")
            self._answers[qid]=w
            self.body.add_widget(_SecurityNote("این سؤال بخشی از آزمون تشخیصی/ارزیابی است؛ لطفاً درباره پاسخ آن در هیچ چتی گفتگو نکنید."))
        self._button("ارسال نهایی آزمون",lambda *_:self._submit_attempt(),SUCCESS)

    def _submit_attempt(self):
        answers=[]
        for qid,w in self._answers.items():answers.append({"question_id":qid,"answer":str(getattr(w,"text","") or "")})
        try:
            result=self.app_state.api.rpc("submit_teacher_exam",{"p_attempt_id":self._attempt_id,"p_answers":answers}); result=result[0] if isinstance(result,list) else result
            self._clear(); self._label("آزمون ثبت شد","23sp",SUCCESS,60,True)
            self._label(f"نمره خودکار: {result.get('score',0)} از {result.get('max_score',0)}","20sp",PRIMARY,60,True)
            self._label("سؤال‌های تشریحی برای تصحیح دستی دبیر باقی می‌مانند.",height=60)
            self._button("بازگشت به مرکز آزمون",lambda *_:self.show_home())
        except Exception as exc:self._error("ثبت آزمون انجام نشد: "+str(exc))
