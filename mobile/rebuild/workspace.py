from threading import Thread
import base64
import os
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.resources import resource_find
from mobile.ui import font_name, rtl_text
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from .catalog import ROLE_NAMES, ROLE_MODULES, TABLES, PANELS, PANEL_ROLES, PANEL_MODULES

HIDDEN={"id","created_at","updated_at","deleted_at"}
EDIT_ROLES={"manager","educational","executive","cultural","advisor","teacher"}

LABELS={
 "first_name":"نام","last_name":"نام خانوادگی","national_code":"کد ملی","student_code":"کد دانش‌آموزی",
 "grade":"پایه","class_name":"کلاس","phone":"تلفن","parent_phone":"تلفن ولی","email":"ایمیل","address":"نشانی",
 "subject":"درس","grades":"پایه‌های تدریس","role":"نقش","employee_code":"کد پرسنلی","employment_status":"وضعیت همکاری",
 "student_id":"شناسه دانش‌آموز","teacher_id":"شناسه دبیر","teacher":"دبیر","teacher_name":"نام دبیر","class_count":"تعداد کلاس",
 "status":"وضعیت","description":"توضیحات","title":"عنوان","exam_name":"نام آزمون","score":"نمره","grade_type":"نوع نمره",
 "term":"نوبت","grade_date":"تاریخ نمره","due_date":"موعد","content":"محتوا","objective":"هدف","session_date":"تاریخ جلسه",
 "meeting_at":"زمان جلسه","parent_name":"نام ولی","report":"گزارش","name":"نام کلاس","operation_type":"نوع عملیات",
 "operation_date":"تاریخ عملیات","report_type":"نوع گزارش","report_date":"تاریخ گزارش","created_by":"ثبت‌کننده",
 "subject":"درس","hours":"ساعت","bell_pattern":"الگوی زنگ","class_names":"نام کلاس‌ها","exam_date":"تاریخ امتحان",
 "duration":"مدت","weight":"ضریب","activity_title":"عنوان فعالیت","activity_kind":"نوع فعالیت","fee":"هزینه",
 "payment_status":"وضعیت پرداخت","registration_date":"تاریخ ثبت","category":"دسته‌بندی","start_date":"شروع","end_date":"پایان",
 "activity_id":"شناسه فعالیت","problem_type":"نوع مشکل","reported_by":"گزارش‌دهنده","checked_at":"زمان کنترل",
 "check_number":"شماره کنترل","leave_time":"زمان خروج","class_id":"شناسه کلاس","lesson":"درس","join_url":"لینک ورود",
 "meeting_url":"لینک جلسه","quiz_id":"شناسه آزمون","question_type":"نوع سؤال","question":"سؤال","options_json":"گزینه‌ها",
 "correct_answer":"پاسخ صحیح","accepted_answers":"پاسخ‌های قابل قبول","points":"امتیاز","username":"کاربری",
 "answer":"پاسخ","risk_level":"سطح ریسک","period":"دوره","report_type":"نوع گزارش","target_type":"نوع هدف","target_id":"شناسه هدف",
 "payment_date":"تاریخ پرداخت","amount":"مبلغ","parent_username":"کاربری ولی","event_type":"نوع رویداد","actor_username":"ثبت‌کننده",
}

class CardButton(Button):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.background_normal=""
        self.background_down=""
        self.background_color=kwargs.get("background_color",(0.08,0.35,0.65,1))
        self.color=WHITE
        self.font_name=font_name()
        self.font_size="12sp"
        self.bold=True

class RebuildDashboard(Screen):
    def __init__(self,app_state=None,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self._build()

    def _label(self,text,size="12sp",color=SECONDARY,height=42,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def _role(self):
        r=str(getattr(self.app_state,"role","student") or "student").lower()
        return {"admin":"manager","administrator":"manager","مدیر":"manager","teachers":"teacher","students":"student","parents":"parent","executive_staff":"executive","counselor":"advisor"}.get(r,r)

    def _visible_panels(self):
        role=self._role()
        groups={
          "manager":["management","educational","executive","cultural","advisor","teachers","students","parents","finance","payment","online","teacher_exams","smart_board","ai","reports","schedule","messages","settings","about"],
          "educational":["educational","online","teacher_exams","smart_board","reports","schedule","messages","settings","about"],
          "executive":["executive","students","parents","finance","payment","reports","schedule","messages","settings","about"],
          "cultural":["cultural","students","parents","messages","reports","settings","about"],
          "advisor":["advisor","students","parents","ai","reports","messages","settings","about"],
          "teacher":["teachers","students","online","teacher_exams","smart_board","reports","schedule","messages","settings","about"],
          "student":["students","online","teacher_exams","smart_board","messages","schedule","settings","about"],
          "parent":["parents","students","online","teacher_exams","payment","smart_board","messages","settings","about"],
        }
        return groups.get(role,groups["student"])

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(7))
        with root.canvas.before:
            Color(0.02,0.07,0.16,0.96)
            self.bg=RoundedRectangle(pos=root.pos,size=root.size,radius=[dp(18)])
        root.bind(pos=lambda *_:self._sync_bg(root),size=lambda *_:self._sync_bg(root))

        bg_path=self._ensure_background()
        if bg_path:
            bg=Image(source=bg_path,allow_stretch=True,keep_ratio=False,opacity=0.82,size_hint=(1,1))
            root.add_widget(bg)
        content=BoxLayout(orientation="vertical",padding=[dp(8),dp(8)],spacing=dp(6))
        content.add_widget(self._label("فراهوش","25sp",WHITE,48,True,True))
        content.add_widget(self._label(f"پنل‌های واقعی • {ROLE_NAMES.get(self._role(),'کاربر')}","11sp",(0.75,0.9,1,1),34,True,True))

        sc=ScrollView(do_scroll_x=False)
        grid=GridLayout(cols=2,spacing=dp(7),padding=dp(4),size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for key,title in PANELS:
            if key not in self._visible_panels(): continue
            b=CardButton(text=rtl_text(title),size_hint_y=None,height=dp(56),
                         background_color=(0.06,0.32,0.62,0.94))
            b.bind(on_release=lambda *_ ,k=key:self.open_panel(k))
            grid.add_widget(b)
        sc.add_widget(grid); content.add_widget(sc); root.add_widget(content); self.add_widget(root)

    def _ensure_background(self):
        try:
            from kivy.app import App
            target=os.path.join(App.get_running_app().user_data_dir,"frahoosh_dashboard_background.jpg")
            if not os.path.exists(target):
                from .background_data import DASHBOARD_JPEG_B64
                with open(target,"wb") as fh:
                    fh.write(base64.b64decode(DASHBOARD_JPEG_B64))
            return target
        except Exception as exc:
            print("DASHBOARD BACKGROUND ERROR:",repr(exc))
            return None

    def _sync_bg(self,root):
        self.bg.pos=root.pos; self.bg.size=root.size

    def open_panel(self,key):
        self.app_state._app.open_workspace(key)

class RebuildWorkspace(Screen):
    def __init__(self,app_state=None,panel_key="management",**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.panel_key=panel_key; self._build()

    def _role(self):
        r=str(getattr(self.app_state,"role","student") or "student").lower()
        return {"admin":"manager","administrator":"manager","مدیر":"manager","teachers":"teacher","students":"student","parents":"parent","executive_staff":"executive","counselor":"advisor"}.get(r,r)

    def _label(self,text,size="12sp",color=SECONDARY,height=42,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def _button(self,text,cb,color=PRIMARY,height=46):
        b=CardButton(text=rtl_text(text),size_hint_y=None,height=dp(height),background_color=color)
        b.bind(on_release=cb); return b

    def _build(self):
        self.clear_widgets()
        root=BoxLayout(orientation="vertical",padding=dp(9),spacing=dp(6))
        head=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(5))
        head.add_widget(self._button("داشبورد",lambda *_:self._dashboard(),PRIMARY,40))
        panel_title=dict(PANELS).get(self.panel_key,"پنل اختصاصی")
        head.add_widget(self._label(panel_title+" • "+ROLE_NAMES.get(self._role(),"کاربر"),"18sp",PRIMARY,46,True))
        root.add_widget(head)
        root.add_widget(self._label("همه ماژول‌های این پنل واقعی و متصل به داده هستند.","10sp",SUCCESS,30,True))
        sc=ScrollView(do_scroll_x=False)
        grid=GridLayout(cols=2,spacing=dp(7),padding=dp(3),size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        module_role=PANEL_ROLES.get(self.panel_key,self._role())
        modules=PANEL_MODULES.get(self.panel_key) or ROLE_MODULES.get(module_role,ROLE_MODULES["student"])
        for key,title,table in modules:
            b=self._button(title,lambda *_ ,k=key,t=table:self.open_module(k,t),PRIMARY,52)
            grid.add_widget(b)
        sc.add_widget(grid); root.add_widget(sc); self.add_widget(root)

    def _dashboard(self): self.app_state._app.show_dashboard()

    def open_module(self,key,table):
        if key=="attendance": return self.app_state._app.open_action("attendance")
        if key=="discipline": return self.app_state._app.open_action("discipline")
        if key=="online_attendance": return self.app_state._app.open_action("online_attendance")
        self.app_state._app.open_table(key,table,self._role())

class RebuildTable(Screen):
    def __init__(self,app_state=None,table="",title="",role="student",**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.table=table; self.title=title; self.role=role; self.rows=[]; self.fields=[]; self._build()

    def _label(self,text,size="11sp",color=SECONDARY,height=40,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def _button(self,text,cb,color=PRIMARY,height=44):
        b=CardButton(text=rtl_text(text),size_hint_y=None,height=dp(height),background_color=color)
        b.bind(on_release=cb); return b

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5))
        head=BoxLayout(size_hint_y=None,height=dp(45),spacing=dp(5))
        head.add_widget(self._button("بازگشت",lambda *_:self.app_state._app.show_workspace(),PRIMARY,40))
        head.add_widget(self._label(self.title,"18sp",PRIMARY,45,True)); root.add_widget(head)
        tools=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(5))
        self.status=self._label("در حال دریافت داده‌های واقعی…","10sp",SECONDARY,34,True)
        tools.add_widget(self.status)
        if self.role in EDIT_ROLES and self.table not in {"school_events"}:
            tools.add_widget(self._button("افزودن رکورد",lambda *_:self._open_form(None),SUCCESS,42))
        root.add_widget(tools)
        self.area=BoxLayout(orientation="vertical",spacing=dp(5),size_hint_y=None)
        self.area.bind(minimum_height=self.area.setter("height"))
        sc=ScrollView(do_scroll_x=False); sc.add_widget(self.area); root.add_widget(sc)
        self.add_widget(root); Thread(target=self._load,daemon=True).start()

    def _load(self):
        try:
            rows=self.app_state.api.table_select(self.table,{"limit":"200","order":"id.desc"}) or []
            Clock.schedule_once(lambda *_:self._render(rows),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._error(),0)

    def _render(self,rows):
        self.rows=[dict(r) for r in rows if isinstance(r,dict)]
        self.area.clear_widgets()
        self.fields=[f for f in TABLES.get(self.table,[]) if f not in HIDDEN]
        if not self.fields and self.rows: self.fields=list(self.rows[0].keys())
        self.area.add_widget(self._label(" • ".join(LABELS.get(f,f) for f in self.fields),"10sp",PRIMARY,48,True,True))
        if not self.rows:
            self.area.add_widget(self._label("رکوردی برای نمایش وجود ندارد.","13sp",SECONDARY,70,True,True))
        for row in self.rows:
            card=BoxLayout(orientation="vertical",padding=dp(7),spacing=dp(2),size_hint_y=None,
                           height=dp(max(84,32*min(len(self.fields),6)+40)))
            with card.canvas.before:
                Color(0.97,0.98,1,0.96)
                rr=RoundedRectangle(pos=card.pos,size=card.size,radius=[dp(12)])
            card.bind(pos=lambda o,*_:self._sync_card(o,rr),size=lambda o,*_:self._sync_card(o,rr))
            for f in self.fields[:6]:
                value=str(row.get(f,"") if row.get(f,"") is not None else "")
                card.add_widget(self._label(f"{LABELS.get(f,f)}: {value or '—'}","10sp",SECONDARY,28))
            if self.role in EDIT_ROLES:
                actions=BoxLayout(size_hint_y=None,height=dp(34),spacing=dp(5))
                actions.add_widget(self._button("ویرایش",lambda *_ ,r=row:self._open_form(r),PRIMARY,32))
                actions.add_widget(self._button("حذف",lambda *_ ,r=row:self._delete(r),ERROR,32))
                card.add_widget(actions)
            self.area.add_widget(card)
        self.status.text=rtl_text(f"{len(self.rows)} رکورد واقعی از «{self.title}»")

    def _sync_card(self,card,rr):
        rr.pos=card.pos; rr.size=card.size

    def _open_form(self,row):
        form=CrudForm(name="crud_"+str(self.table),app_state=self.app_state,table=self.table,title=self.title,role=self.role,row=row,fields=self.fields or TABLES.get(self.table,[]),on_done=self._reload)
        self.app_state._app.open_overlay(form)

    def _reload(self):
        Thread(target=self._load,daemon=True).start()

    def _delete(self,row):
        def work():
            try:
                self.app_state.api.table_delete(self.table,{"id":f"eq.{row.get('id')}"})
                Clock.schedule_once(lambda *_:self._reload(),0)
            except Exception as exc: print("DELETE ERROR:",repr(exc))
        Thread(target=work,daemon=True).start()

    def _error(self):
        self.status.text=rtl_text("دریافت داده انجام نشد؛ اتصال یا نام جدول را بررسی کنید."); self.status.color=ERROR

class CrudForm(Screen):
    def __init__(self,app_state=None,table="",title="",role="student",row=None,fields=None,on_done=None,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.table=table; self.title=title; self.role=role; self.row=row or {}; self.fields=[f for f in (fields or []) if f not in HIDDEN]; self.on_done=on_done; self.inputs={}; self._build()

    def _label(self,text,size="11sp",color=SECONDARY,height=38,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(5))
        root.add_widget(self._label(("ویرایش " if self.row else "افزودن ")+self.title,"18sp",PRIMARY,45,True))
        sc=ScrollView(do_scroll_x=False)
        body=BoxLayout(orientation="vertical",spacing=dp(4),size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))
        for f in self.fields:
            body.add_widget(self._label(LABELS.get(f,f),"10sp",SECONDARY,30,True))
            inp=TextInput(text=str(self.row.get(f,"") or ""),font_name=font_name(),font_size="11sp",
                          multiline=False,size_hint_y=None,height=dp(42),halign="right",
                          hint_text=rtl_text(LABELS.get(f,f)))
            self.inputs[f]=inp; body.add_widget(inp)
        sc.add_widget(body); root.add_widget(sc)
        actions=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(5))
        actions.add_widget(CardButton(text=rtl_text("انصراف"),size_hint_y=None,height=dp(44),background_color=SECONDARY,on_release=self._close))
        save=CardButton(text=rtl_text("ذخیره واقعی"),size_hint_y=None,height=dp(44),background_color=SUCCESS)
        save.bind(on_release=self._save); actions.add_widget(save); root.add_widget(actions)
        self.add_widget(root)

    def _close(self,*_): self.app_state._app.close_overlay()

    def _save(self,*_):
        payload={f:self.inputs[f].text.strip() for f in self.fields if self.inputs[f].text.strip()!=""}
        def work():
            try:
                if self.row:
                    self.app_state.api.table_update(self.table,{"id":f"eq.{self.row.get('id')}"},payload)
                else:
                    self.app_state.api.table_insert(self.table,payload)
                Clock.schedule_once(lambda *_:self._saved(),0)
            except Exception as exc:
                print("SAVE ERROR:",repr(exc)); Clock.schedule_once(lambda *_:self._failed(),0)
        Thread(target=work,daemon=True).start()

    def _saved(self):
        if self.on_done: self.on_done()
        self._close()

    def _failed(self):
        self.add_widget(self._label("ذخیره انجام نشد؛ جزئیات در گزارش برنامه ثبت شد.","11sp",ERROR,40,True))

