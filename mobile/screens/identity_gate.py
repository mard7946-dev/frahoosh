from threading import Thread
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, CARD, SCHOOL_NAME
from mobile.ui import font_name, rtl_text, PersianTextInput
from kivy.graphics import Color, RoundedRectangle

class IdentityGateScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state=app_state
        self.pending_route="dashboard"
        self.data={}
        self._build()

    def label(self,text,size="11sp",color=SECONDARY,bold=False,center=False,height=34):
        w=Label(text=rtl_text(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v))
        return w

    def btn(self,text,cb,color=PRIMARY,h=44):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="10sp",
                 background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(h))
        b.bind(on_release=cb)
        return b

    def _card(self,fill=CARD,height=170):
        c=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(5),size_hint_y=None,height=dp(height))
        with c.canvas.before:
            Color(*fill); c._bg=RoundedRectangle(radius=[dp(14)])
        c.bind(pos=lambda o,v:setattr(c._bg,"pos",v),size=lambda o,v:setattr(c._bg,"size",v))
        return c

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(9),spacing=dp(7))
        root.add_widget(self.label("تأیید اطلاعات کاربری","20sp",PRIMARY,True,True,45))
        root.add_widget(self.label(SCHOOL_NAME+" • بررسی اولیه فقط در اولین ورود","9sp",SECONDARY,False,True,28))
        self.status=self.label("در حال دریافت اطلاعات شما…","9sp",SECONDARY,True,True,30)
        root.add_widget(self.status)
        self.scroll=ScrollView(do_scroll_x=False,do_scroll_y=True)
        self.body=BoxLayout(orientation="vertical",spacing=dp(7),size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter("height"))
        self.scroll.add_widget(self.body); root.add_widget(self.scroll)
        actions=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(6))
        actions.add_widget(self.btn("تأیید و ثبت نهایی",self.confirm,SUCCESS,46))
        actions.add_widget(self.btn("مغایرت دارم؛ پیام به مدرسه",self.discrepancy,PRIMARY,46))
        root.add_widget(actions)
        self.add_widget(root)

    def on_pre_enter(self,*_):
        self.app_state=getattr(__import__("kivy.app",fromlist=["App"]).App.get_running_app(),"app_state",self.app_state)
        Clock.schedule_once(lambda *_:self.load(),0.02)

    def _api(self):
        api=getattr(self.app_state,"api",None)
        if api is None: raise RuntimeError("سرویس داده آماده نیست.")
        return api

    def _async(self,work,done):
        def run():
            try: result=work(); Clock.schedule_once(lambda *_:done(result,None),0)
            except Exception as exc: Clock.schedule_once(lambda *_:done(None,str(exc)),0)
        Thread(target=run,daemon=True).start()

    def load(self):
        self.status.text=rtl_text("در حال بررسی تأیید قبلی و اطلاعات شما…")
        self._async(self._data,self._loaded)

    def _data(self):
        api=self._api(); p=dict(getattr(self.app_state,"profile",{}) or {})
        user=getattr(self.app_state,"user",{}) or {}
        username=p.get("username") or p.get("email") or user.get("email") or getattr(self.app_state,"national_code","")
        auth_id=user.get("id")
        checks=[]
        if auth_id:
            checks=api.table_select("identity_confirmations",{"auth_user_id":"eq."+str(auth_id),"order":"confirmed_at.desc","limit":"1"}) or []
        if not checks and username:
            checks=api.table_select("identity_confirmations",{"username":"eq."+str(username),"order":"confirmed_at.desc","limit":"1"}) or []
        if checks:
            return {"confirmed":True}
        role=str(getattr(self.app_state,"role","student") or "student").strip().lower()
        source={}; source_table="account_settings"
        if role in ("student","دانش‌آموز"):
            sid=p.get("linked_student_id") or p.get("student_id")
            rows=api.table_select("students",{"id":"eq."+str(sid),"limit":"1"}) if sid else api.table_select("students",{"national_code":"eq."+str(getattr(self.app_state,"national_code","")),"limit":"1"}) if getattr(self.app_state,"national_code","") else []
            source=rows[0] if rows else {}; source_table="students"
        elif role in ("teacher","دبیر","معلم"):
            tid=p.get("linked_teacher_id") or p.get("teacher_id")
            rows=api.table_select("teachers",{"id":"eq."+str(tid),"limit":"1"}) if tid else api.table_select("teachers",{"national_code":"eq."+str(getattr(self.app_state,"national_code","")),"limit":"1"}) if getattr(self.app_state,"national_code","") else []
            source=rows[0] if rows else {}; source_table="teachers"
        elif role in ("parent","parents","ولی","اولیا"):
            links=api.table_select("parent_children",{"parent_username":"eq."+str(username),"limit":"20"}) or []
            children=[]
            for link in links:
                rows=api.table_select("students",{"id":"eq."+str(link.get("student_id")),"limit":"1"}) or []
                if rows: children.append(rows[0])
            source={"children":children}; source_table="parent_children"
        else:
            sid=p.get("linked_staff_id") or p.get("staff_id")
            rows=api.table_select("staff",{"id":"eq."+str(sid),"limit":"1"}) if sid else api.table_select("staff",{"national_code":"eq."+str(getattr(self.app_state,"national_code","")),"limit":"1"}) if getattr(self.app_state,"national_code","") else []
            source=rows[0] if rows else {}; source_table="staff"
        return {"confirmed":False,"account":p,"source":source,"source_table":source_table,"role":role,"username":username,"auth_id":auth_id}

    def _loaded(self,data,error):
        if error:
            self.status.text=rtl_text("دریافت اطلاعات انجام نشد: "+error); self.status.color=ERROR; return
        if data.get("confirmed"):
            self._finish(); return
        self.data=data; self.body.clear_widgets()
        p=data.get("account") or {}; role=data.get("role") or "-"
        c=self._card(height=190)
        for title,key,value in [
            ("نام نمایشی","display_name",p.get("display_name") or getattr(self.app_state,"display_name","-")),
            ("نام کاربری","username",p.get("username") or data.get("username") or "-"),
            ("کد ملی","national_code",p.get("national_code") or getattr(self.app_state,"national_code","-")),
            ("تلفن","phone",p.get("phone") or "-"),("ایمیل","email",p.get("email") or "-"),("نقش","role",p.get("role") or role)]:
            c.add_widget(self.label(title+": "+str(value or "-"),"10sp",SECONDARY,False,False,27))
        self.body.add_widget(c)
        source=data.get("source") or {}
        if source.get("children") is not None:
            self.body.add_widget(self.label("اطلاعات فرزندان متصل","13sp",PRIMARY,True,True,32))
            for child in source.get("children") or []:
                self._profile_card(child)
            if not source.get("children"): self.body.add_widget(self.label("فرزندی برای این حساب متصل نشده است.","11sp",ERROR,True,True,55))
        elif source:
            self.body.add_widget(self.label("اطلاعات پرونده مدرسه","13sp",PRIMARY,True,True,32))
            self._profile_card(source)
        else:
            self.body.add_widget(self.label("پرونده اختصاصی هنوز تکمیل نشده؛ اطلاعات حساب را بررسی و تأیید کنید.","11sp",ERROR,True,True,60))
        self.status.text=rtl_text("اگر اطلاعات درست است تأیید کنید؛ این مرحله فقط یک بار انجام می‌شود."); self.status.color=SUCCESS

    def _profile_card(self,r):
        c=self._card(height=170)
        pairs=[("نام","first_name"),("نام خانوادگی","last_name"),("کد ملی","national_code"),("سمت / نقش","role"),
               ("درس","subject"),("پایه / کلاس","class_name"),("کد پرسنلی","employee_code"),("تلفن","phone")]
        for title,key in pairs:
            if r.get(key) not in (None,""): c.add_widget(self.label(title+": "+str(r.get(key)),"10sp",SECONDARY,False,False,25))
        self.body.add_widget(c)

    def confirm(self,*_):
        if not self.data: return
        self.status.text=rtl_text("در حال ثبت نهایی اطلاعات…")
        d=self.data; p=d.get("account") or {}; source=d.get("source") or {}
        snapshot={"account":p,"source":source}
        def work():
            api=self._api()
            existing=api.table_select("identity_confirmations",{"username":"eq."+str(d.get("username") or ""),"order":"confirmed_at.desc","limit":"1"}) or []
            if not existing:
                api.table_insert("identity_confirmations",{"auth_user_id":d.get("auth_id"),"username":d.get("username"),"role":d.get("role") or "student","profile_table":d.get("source_table"),"profile_id":source.get("id") if isinstance(source,dict) else None,"student_id":source.get("id") if d.get("source_table")=="students" and isinstance(source,dict) else None,"confirmation_status":"confirmed","snapshot":snapshot},return_representation=False)
            # Persist the final state in the user's own account record.
            try:
                api.table_update("account_settings",{"username":"eq."+str(d.get("username") or "")},{"identity_confirmed":True,"identity_confirmed_at":__import__("datetime").datetime.utcnow().isoformat()+"Z","identity_snapshot":snapshot})
            except Exception:
                pass
            return True
        self._async(work,self._confirmed)

    def _confirmed(self,result,error):
        if error:
            self.status.text=rtl_text("ثبت نهایی انجام نشد: "+error); self.status.color=ERROR; return
        self.app_state.session["identity_confirmed"]=True
        try:
            from mobile.services.session import save_session
            save_session(self.app_state.session)
        except Exception: pass
        self.status.text=rtl_text("اطلاعات شما ثبت نهایی شد.")
        Clock.schedule_once(lambda *_:self._finish(),0.25)

    def discrepancy(self,*_):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(7))
        ti=PersianTextInput(hint_text=rtl_text("شرح دقیق مغایرت را بنویسید"),font_size="12sp",multiline=True,size_hint_y=None,height=dp(150))
        root.add_widget(ti)
        pop=Popup(title=rtl_text("گزارش مغایرت اطلاعات"),content=root,size_hint=(.94,.60),auto_dismiss=False)
        root.add_widget(self.btn("ارسال به مدیریت / معاونت اجرایی",lambda *_:self._send(ti,pop),SUCCESS,44))
        root.add_widget(self.btn("انصراف",lambda *_:pop.dismiss(),SECONDARY,44)); pop.open()

    def _send(self,ti,pop):
        text=ti.text.strip()
        if not text: return
        pop.dismiss(); d=self.data or {}
        payload={"sender":d.get("username") or getattr(self.app_state,"national_code",""),"receiver":"manager","text":"مغایرت اطلاعات کاربر: "+text,"sender_user_id":d.get("auth_id"),"sender_name":getattr(self.app_state,"display_name",""),"title":"مغایرت اطلاعات کاربر","body":text,"audience_type":"role","audience_value":"manager","target_role":"manager","target_name":"مدیریت / معاونت اجرایی"}
        def work():
            row=self._api().table_insert("messages",payload)
            if isinstance(row,list) and row and row[0].get("id"):
                self._api().table_insert("message_targets",{"message_id":row[0]["id"],"target_role":"manager","target_name":"مدیریت / معاونت اجرایی"})
            return True
        self._async(work,lambda r,e:self._send_done(e))

    def _send_done(self,error):
        self.status.text=rtl_text("پیام مغایرت ارسال شد؛ پس از بررسی مدرسه دوباره وارد شوید." if not error else "ارسال پیام ناموفق بود: "+error)
        self.status.color=SUCCESS if not error else ERROR

    def _finish(self):
        if self.manager:
            self.manager.current=self.pending_route if self.pending_route in ("dashboard","panel") else "dashboard"
