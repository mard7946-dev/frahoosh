from threading import Thread
import webbrowser

from kivy.clock import Clock
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

def digits(v): return str(v or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789"))

class OperationsScreen(Screen):
    def __init__(self,app_state=None,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.route="messages"; self._build()
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(8)); head=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(54),spacing=dp(8))
        back=Button(text=rtl_text("‹ بازگشت"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(100)); back.bind(on_release=lambda *_:self._back()); head.add_widget(back)
        self.title=Label(text=rtl_text(APP_NAME),font_name=font_name(),font_size="21sp",bold=True,color=PRIMARY,halign="right",valign="middle"); self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title); root.add_widget(head)
        self.status=Label(text="",font_name=font_name(),font_size="12sp",color=SECONDARY,halign="right",valign="middle",size_hint_y=None,height=dp(42)); self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False); self.body=BoxLayout(orientation="vertical",spacing=dp(9),padding=dp(4),size_hint_y=None); self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root)
    def set_route(self,route):
        self.route=route; self.body.clear_widgets(); self.title.text=rtl_text({"payment":"پرداخت آنلاین","messages":"صندوق پیام‌ها","online":"کلاس‌های آنلاین"}.get(route,APP_NAME))
        if route=="payment":self._payment()
        elif route=="online":self._online()
        else:self._messages()
    def _label(self,text,size="14sp",color=SECONDARY,height=68):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,halign="right",valign="middle",size_hint_y=None,height=dp(height)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w
    def _button(self,text,cb,color=PRIMARY,height=48):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="14sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(height)); b.bind(on_release=cb); self.body.add_widget(b); return b
    def _payment(self):
        if role_of(self.app_state) in PAYMENT_MANAGERS:self._payment_management()
        else:self._payment_user()
    def _payment_management(self):
        self._label("مدیریت گزینه‌های پرداخت\nگزینه‌ها در payment_offers ذخیره می‌شوند و مبلغ را خود سامانه تعیین می‌کند.",height=82)
        title=self._field("عنوان پرداخت؛ مثال شهریه مهر"); reason=self._field("علت پرداخت؛ اختیاری"); amount=self._field("مبلغ به ریال")
        self._button("ثبت گزینه پرداخت",lambda *_:self._save_offer(title,reason,amount),SUCCESS); self._button("بازخوانی گزینه‌ها",lambda *_:self.set_route("payment")); self._load_offers()
    def _save_offer(self,title,reason,amount):
        try:a=int(digits(amount.text).replace(",","") or 0)
        except Exception:return self._error("مبلغ باید عدد باشد.")
        if a<=0 or not title.text.strip():return self._error("عنوان و مبلغ الزامی است.")
        try:
            self.app_state.api.table_insert("payment_offers",{"title":title.text.strip(),"amount":a,"target_type":"school","target_value":SCHOOL_ID,"description":reason.text.strip(),"active":1,"manual_amount":0,"payment_reason":reason.text.strip(),"gateway_enabled":True}); self._success("گزینه پرداخت در سامانه ثبت شد.")
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
        self._label("مدیریت کلاس آنلاین\nکلاس واقعی در online_classes ذخیره می‌شود و با RPC امن فعال می‌گردد.",height=82)
        fields=[self._field("عنوان کلاس"),self._field("درس / موضوع"),self._field("نام دبیر"),self._field("پایه"),self._field("کلاس"),self._field("مدت به دقیقه"),self._field("لینک ورود به کلاس"),self._field("ساعت شروع؛ اختیاری"),self._field("ساعت پایان؛ اختیاری")]
        fields[5].text="60"
        self._button("ساخت کلاس",lambda *_:self._create_class(*fields),SUCCESS); self._load_classes(True)
    def _create_class(self,title,subject,teacher,grade,cls,duration,join,start,end):
        if not title.text.strip():return self._error("عنوان کلاس الزامی است.")
        try:dur=max(1,int(digits(duration.text or "60")))
        except Exception:return self._error("مدت کلاس باید عدد باشد.")
        try:
            self.app_state.api.table_insert("online_classes",{"title":title.text.strip(),"subject":subject.text.strip(),"lesson":subject.text.strip(),"teacher":teacher.text.strip(),"grade":grade.text.strip(),"class_name":cls.text.strip(),"duration":dur,"start_time":start.text.strip(),"end_time":end.text.strip(),"status":"inactive","created_at_shamsi":"","start_time_shamsi":start.text.strip(),"end_time_shamsi":end.text.strip(),"join_url":join.text.strip(),"meeting_url":join.text.strip()}); self._success("کلاس ساخته شد و برای فعال‌سازی آماده است."); self._load_classes(True)
        except Exception as exc:self._error("ساخت کلاس انجام نشد: "+str(exc))
    def _online_user(self):self._label("کلاس‌های آنلاین\nفقط کلاس‌های واقعی سامانه نمایش داده می‌شوند.",height=72); self._load_classes(False)
    def _load_classes(self,management=False):
        try:rows=self.app_state.api.table_select("online_classes",{"order":"id.desc","limit":"50"})
        except Exception as exc:return self._error("خواندن کلاس‌ها انجام نشد: "+str(exc))
        for r in rows:
            state=str(r.get("status") or "inactive"); self._label(f"{r.get('title') or 'کلاس آنلاین'}\n{r.get('subject','')} | {r.get('class_name','')} | {r.get('duration',0)} دقیقه\nوضعیت: {'فعال' if state=='active' else 'غیرفعال'}",height=82)
            if management and r.get("id") and state!="active":self._button("فعال‌سازی کلاس",lambda *_ ,cid=r["id"]:self._activate_class(cid),SUCCESS,44)
            if state=="active" and r.get("join_url"):self._button("ورود به کلاس",lambda *_ ,u=r["join_url"]:self._open_url(u),PRIMARY,44)
        if not rows:self._label("کلاسی ثبت نشده است.",height=60)
    def _activate_class(self,cid):
        try:self.app_state.api.rpc("activate_online_class",{"p_class_id":int(cid)}); self._success("کلاس فعال شد."); self._load_classes(True)
        except Exception as exc:self._error("فعال‌سازی انجام نشد: "+str(exc))
    def _messages(self):
        self._label("صندوق پیام‌ها\nپیام‌های ورودی و خروجی از سامانه مرکزی خوانده می‌شوند.",height=72); self._load_messages()
        receiver=self._field("گیرنده؛ ایمیل یا نام کاربری",50); title=self._field("عنوان پیام"); text=self._field("متن پیام",85,True); self._button("ارسال پیام",lambda *_:self._send_message(receiver,title,text),SUCCESS)
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
