from threading import Thread
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.resources import resource_find
from mobile.ui import font_name, rtl_text
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from .catalog import ROLE_NAMES, ROLE_MODULES, TABLES, PANELS, PANEL_ROLES, PANEL_MODULES
HIDDEN={"id","created_at","updated_at","deleted_at"}; EDIT_ROLES={"manager","educational","executive","cultural","advisor","teacher"}
LABELS={"first_name":"نام","last_name":"نام خانوادگی","national_code":"کد ملی","student_code":"کد دانش‌آموزی","grade":"پایه","class_name":"کلاس","phone":"تلفن","parent_phone":"تلفن ولی","email":"ایمیل","address":"نشانی","subject":"درس","grades":"پایه‌های تدریس","role":"نقش","employee_code":"کد پرسنلی","employment_status":"وضعیت همکاری","student_id":"دانش‌آموز","teacher_id":"دبیر","teacher":"دبیر","teacher_name":"نام دبیر","status":"وضعیت","description":"توضیحات","title":"عنوان","exam_name":"نام آزمون","score":"نمره","grade_type":"نوع نمره","term":"نوبت","grade_date":"تاریخ نمره","due_date":"موعد","content":"محتوا","objective":"هدف","session_date":"تاریخ جلسه","meeting_at":"زمان جلسه","parent_name":"نام ولی","report":"گزارش","name":"نام کلاس","operation_type":"نوع عملیات","operation_date":"تاریخ عملیات","report_type":"نوع گزارش","report_date":"تاریخ گزارش","created_by":"ثبت‌کننده","hours":"ساعت","bell_pattern":"الگوی زنگ","class_names":"نام کلاس‌ها","exam_date":"تاریخ امتحان","duration":"مدت","weight":"ضریب","activity_title":"عنوان فعالیت","activity_kind":"نوع فعالیت","fee":"هزینه","payment_status":"وضعیت پرداخت","registration_date":"تاریخ ثبت","category":"دسته‌بندی","start_date":"شروع","end_date":"پایان","activity_id":"فعالیت","problem_type":"نوع مشکل","reported_by":"گزارش‌دهنده","checked_at":"زمان کنترل","check_number":"شماره کنترل","leave_time":"زمان خروج","class_id":"کلاس","lesson":"درس","join_url":"لینک ورود","meeting_url":"لینک جلسه","quiz_id":"آزمون","question_type":"نوع سؤال","question":"سؤال","options_json":"گزینه‌ها","correct_answer":"پاسخ صحیح","accepted_answers":"پاسخ‌های قابل قبول","points":"امتیاز","username":"کاربری","answer":"پاسخ","risk_level":"سطح ریسک","period":"دوره","target_type":"نوع هدف","target_id":"شناسه هدف","payment_date":"تاریخ پرداخت","amount":"مبلغ","parent_username":"کاربری ولی","event_type":"نوع رویداد","actor_username":"ثبت‌کننده"}
COLORS=[(0.02,.40,.78,1),(0,.58,.50,1),(.30,.22,.78,1),(.92,.45,.05,1),(.78,.08,.32,1),(.04,.55,.68,1),(.18,.30,.70,1),(.68,.28,.72,1)]
class CardButton(Button):
    def __init__(self,**kw): super().__init__(**kw); self.background_normal=""; self.background_down=""; self.color=WHITE; self.font_name=font_name(); self.font_size="12sp"; self.bold=True
class Base(Screen):
    def label(self,t,size="11sp",color=WHITE,h=40,bold=False,center=False):
        w=Label(text=rtl_text(t),font_name=font_name(),font_size=size,color=color,bold=bold,halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(h)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w
    def button(self,t,cb,color=PRIMARY,h=46):
        b=CardButton(text=rtl_text(t),size_hint_y=None,height=dp(h),background_color=color); b.bind(on_release=cb); return b
class RebuildDashboard(Base):
    def __init__(self,app_state=None,**kw): super().__init__(**kw); self.app_state=app_state; self._build()
    def role(self):
        r=str(getattr(self.app_state,"role","student") or "student").lower(); return {"admin":"manager","administrator":"manager","teachers":"teacher","students":"student","parents":"parent","executive_staff":"executive","counselor":"advisor"}.get(r,r)
    def visible(self):
        g={"manager":[x[0] for x in PANELS],"educational":["educational","executive","online","teacher_exams","smart_board","reports","schedule","messages","settings","about"],"executive":["executive","students","parents","finance","payment","schedule","reports","messages","settings","about"],"cultural":["cultural","students","parents","online","reports","messages","settings","about"],"advisor":["advisor","students","parents","ai","reports","messages","settings","about"],"teacher":["teachers","online","teacher_exams","smart_board","students","parents","reports","schedule","messages","settings","about"],"student":["students","online","teacher_exams","smart_board","reports","schedule","messages","settings","about"],"parent":["parents","online","teacher_exams","payment","reports","schedule","messages","settings","about"]}; return g.get(self.role(),g["student"])
    def bg(self):
        for p in ("mobile/assets/frahoosh_dashboard_bg.jpg","assets/frahoosh_dashboard_bg.jpg"):
            q=resource_find(p)
            if q:return q
        return None
    def _build(self):
        root=FloatLayout(); src=self.bg()
        root.add_widget(Image(source=src or "mobile/assets/frahoosh_login_mobile.jpg",allow_stretch=True,keep_ratio=False,size_hint=(1,1),pos_hint={"x":0,"y":0}))
        veil=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(6),size_hint=(1,1),pos_hint={"x":0,"y":0}); veil.add_widget(self.label("فراهوش","25sp",WHITE,50,True,True)); veil.add_widget(self.label(f"{getattr(self.app_state,'display_name','کاربر فراهوش')}  •  {ROLE_NAMES.get(self.role(),'کاربر')}","12sp",WHITE,32,True,True))
        sc=ScrollView(do_scroll_x=False); grid=GridLayout(cols=2,spacing=dp(7),padding=dp(4),size_hint_y=None); grid.bind(minimum_height=grid.setter("height")); visible=self.visible()
        for i,(key,title) in enumerate(PANELS):
            if key not in visible: continue
            b=self.button(title,lambda *_ ,k=key:self.open_panel(k),COLORS[i%len(COLORS)],58); b.opacity=0; grid.add_widget(b); Clock.schedule_once(lambda dt,w=b:Animation(opacity=1,x=w.x+dp(8),d=.18,t="out_quad").start(w),.02*i)
        sc.add_widget(grid); veil.add_widget(sc); root.add_widget(veil); self.add_widget(root)
    def open_panel(self,key): self.app_state._app.open_workspace(key)
class RebuildWorkspace(Base):
    def __init__(self,app_state=None,panel_key="management",**kw): super().__init__(**kw); self.app_state=app_state; self.panel_key=panel_key; self._build()
    def role(self): return PANEL_ROLES.get(self.panel_key,str(getattr(self.app_state,"role","student") or "student"))
    def modules(self): return PANEL_MODULES.get(self.panel_key) or ROLE_MODULES.get(self.role(),ROLE_MODULES["student"])
    def _build(self):
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(9),spacing=dp(6)); h=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(5)); h.add_widget(self.button("داشبورد",lambda *_:self.app_state._app.show_dashboard(),SECONDARY,42)); h.add_widget(self.label("پنل واقعی • "+ROLE_NAMES.get(self.role(),"کاربر"),"18sp",WHITE,46,True)); root.add_widget(h); root.add_widget(self.label("ماژول‌های اختصاصی این پنل • اتصال مستقیم به داده واقعی","10sp",WHITE,34,True))
        sc=ScrollView(do_scroll_x=False); grid=GridLayout(cols=2,spacing=dp(7),padding=dp(3),size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        for i,(key,title,table) in enumerate(self.modules()): grid.add_widget(self.button(title,lambda *_ ,k=key,t=table:self.open_module(k,t),COLORS[i%len(COLORS)],64))
        sc.add_widget(grid); root.add_widget(sc); self.add_widget(root)
    def open_module(self,key,table):
        if key=="attendance": return self.app_state._app.open_action("attendance")
        if key=="discipline": return self.app_state._app.open_action("discipline")
        if key in ("online_attendance","attendance_online"): return self.app_state._app.open_action("online_attendance")
        self.app_state._app.open_table(key,table,self.role())
class RebuildTable(Base):
    def __init__(self,app_state=None,table="",title="",role="student",**kw): super().__init__(**kw); self.app_state=app_state; self.table=table; self.title=title; self.role=role; self.rows=[]; self._build()
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5)); h=BoxLayout(size_hint_y=None,height=dp(45),spacing=dp(5)); h.add_widget(self.button("بازگشت",lambda *_:self.app_state._app.show_workspace(),SECONDARY,40)); h.add_widget(self.label(self.title,"17sp",WHITE,45,True)); root.add_widget(h); self.status=self.label("دریافت داده واقعی…","10sp",WHITE,32,True); root.add_widget(self.status); self.area=BoxLayout(orientation="vertical",spacing=dp(5),size_hint_y=None); self.area.bind(minimum_height=self.area.setter("height")); sc=ScrollView(do_scroll_x=False); sc.add_widget(self.area); root.add_widget(sc); self.add_widget(root); Thread(target=self._load,daemon=True).start()
    def _load(self):
        try: rows=self.app_state.api.table_select(self.table,{"limit":"200"}) or []; Clock.schedule_once(lambda *_:self.render(rows),0)
        except Exception as e: print("TABLE LOAD ERROR",repr(e)); Clock.schedule_once(lambda *_:self.fail(),0)
    def render(self,rows):
        self.rows=[dict(x) for x in rows if isinstance(x,dict)]; self.area.clear_widgets(); fields=[f for f in TABLES.get(self.table,[]) if f not in HIDDEN]
        if not fields and self.rows: fields=list(self.rows[0].keys())
        if self.role in EDIT_ROLES:self.area.add_widget(self.button("＋ افزودن رکورد واقعی",lambda *_:self.form(None),SUCCESS,46))
        self.area.add_widget(self.label("  |  ".join(LABELS.get(f,f) for f in fields),"10sp",WHITE,45,True,True))
        if not self.rows:self.area.add_widget(self.label("رکوردی وجود ندارد.","12sp",WHITE,55,True,True))
        for row in self.rows:
            card=BoxLayout(orientation="vertical",padding=dp(7),spacing=dp(2),size_hint_y=None,height=dp(150)); card.add_widget(self.label("\n".join(f"{LABELS.get(f,f)}: {row.get(f,'—') or '—'}" for f in fields[:6]),"10sp",WHITE,108))
            if self.role in EDIT_ROLES:
                a=BoxLayout(size_hint_y=None,height=dp(32),spacing=dp(4)); a.add_widget(self.button("ویرایش",lambda *_ ,r=row:self.form(r),PRIMARY,30)); a.add_widget(self.button("حذف",lambda *_ ,r=row:self.delete(r),ERROR,30)); card.add_widget(a)
            self.area.add_widget(card)
        self.status.text=rtl_text(f"{len(self.rows)} رکورد واقعی")
    def form(self,row): self.app_state._app.open_overlay(CrudForm(name="crud_form",app_state=self.app_state,table=self.table,title=self.title,role=self.role,row=row,fields=TABLES.get(self.table,[]),on_done=self._load))
    def delete(self,row):
        def work():
            try:self.app_state.api.table_delete(self.table,{"id":f"eq.{row.get('id')}"}); Clock.schedule_once(lambda *_:self._load(),0)
            except Exception as e: print("DELETE ERROR",repr(e))
        Thread(target=work,daemon=True).start()
    def fail(self): self.status.text=rtl_text("دریافت داده انجام نشد؛ جزئیات در گزارش برنامه ثبت شد."); self.status.color=ERROR
class CrudForm(Base):
    def __init__(self,app_state=None,table="",title="",role="student",row=None,fields=None,on_done=None,**kw): super().__init__(**kw); self.app_state=app_state; self.table=table; self.title=title; self.role=role; self.row=row or {}; self.fields=[f for f in(fields or []) if f not in HIDDEN]; self.on_done=on_done; self.inputs={}; self._build()
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(4)); root.add_widget(self.label(("ویرایش " if self.row else "افزودن ")+self.title,"18sp",WHITE,45,True)); sc=ScrollView(do_scroll_x=False); body=BoxLayout(orientation="vertical",spacing=dp(3),size_hint_y=None); body.bind(minimum_height=body.setter("height"))
        for f in self.fields: body.add_widget(self.label(LABELS.get(f,f),"10sp",WHITE,27,True)); inp=TextInput(text=str(self.row.get(f,"") or ""),font_name=font_name(),font_size="11sp",multiline=False,size_hint_y=None,height=dp(40),halign="right"); self.inputs[f]=inp; body.add_widget(inp)
        sc.add_widget(body); root.add_widget(sc); a=BoxLayout(size_hint_y=None,height=dp(45),spacing=dp(5)); a.add_widget(self.button("انصراف",lambda *_:self.app_state._app.close_overlay(),SECONDARY,42)); a.add_widget(self.button("ذخیره واقعی",self.save,SUCCESS,42)); root.add_widget(a); self.add_widget(root)
    def save(self,*_):
        payload={f:self.inputs[f].text.strip() for f in self.fields if self.inputs[f].text.strip()}
        def work():
            try:
                if self.row:self.app_state.api.table_update(self.table,{"id":f"eq.{self.row.get('id')}"},payload)
                else:self.app_state.api.table_insert(self.table,payload)
                Clock.schedule_once(lambda *_:self.done(),0)
            except Exception as e: print("SAVE ERROR",repr(e))
        Thread(target=work,daemon=True).start()
    def done(self):
        if self.on_done:self.on_done()
        self.app_state._app.close_overlay()
