from threading import Thread
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from mobile.ui import font_name, rtl_text
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from .catalog import ROLE_NAMES, ROLE_MODULES, TABLES, PANELS

HIDDEN={"created_at","updated_at","deleted_at"}
SPECIAL={"attendance","discipline","online_attendance"}

class RebuildDashboard(Screen):
    def __init__(self,app_state=None,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self._build()

    def _label(self,text,size="12sp",color=SECONDARY,height=42,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def _button(self,text,cb,color=PRIMARY):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="12sp",background_normal="",
                 background_color=color,color=WHITE,size_hint_y=None,height=dp(50)); b.bind(on_release=cb); return b

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(7))
        root.add_widget(self._label("فراهوش","24sp",PRIMARY,48,True,True))
        name=getattr(self.app_state,"display_name","کاربر فراهوش"); role=ROLE_NAMES.get(getattr(self.app_state,"role","student"),"کاربر")
        root.add_widget(self._label(f"{name}  •  {role}","12sp",SECONDARY,36,True,True))
        sc=ScrollView(do_scroll_x=False); grid=GridLayout(cols=2,spacing=dp(7),padding=dp(4),size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        for key,title in PANELS:
            b=self._button(title,lambda *_ ,k=key:self.open_panel(k),PRIMARY if key not in ("about","settings") else SECONDARY); grid.add_widget(b)
        sc.add_widget(grid); root.add_widget(sc); self.add_widget(root)

    def open_panel(self,key):
        app=self.app_state._app
        app.open_workspace(key)

class RebuildWorkspace(Screen):
    def __init__(self,app_state=None,panel_key="management",**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.panel_key=panel_key; self._build()

    def _label(self,text,size="12sp",color=SECONDARY,height=42,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def _button(self,text,cb,color=PRIMARY,height=46):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="12sp",background_normal="",
                 background_color=color,color=WHITE,size_hint_y=None,height=dp(height)); b.bind(on_release=cb); return b

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(9),spacing=dp(5))
        head=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(5))
        head.add_widget(self._button("داشبورد",lambda *_:self._dashboard(),PRIMARY,40))
        head.add_widget(self._label("پنل اختصاصی "+ROLE_NAMES.get(self._role(),"کاربر"),"18sp",PRIMARY,46,True))
        root.add_widget(head)
        self.status=self._label("","10sp",SECONDARY,32,True); root.add_widget(self.status)
        sc=ScrollView(do_scroll_x=False); grid=GridLayout(cols=2,spacing=dp(6),padding=dp(3),size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        for key,title,table in ROLE_MODULES.get(self._role(),ROLE_MODULES["student"]):
            grid.add_widget(self._button(title,lambda *_ ,k=key,t=table:self.open_module(k,t),PRIMARY))
        sc.add_widget(grid); root.add_widget(sc); self.add_widget(root)

    def _role(self):
        r=str(getattr(self.app_state,"role","student") or "student").lower()
        return {"admin":"manager","administrator":"manager","مدیر":"manager"}.get(r,r)

    def _dashboard(self):
        self.app_state._app.show_dashboard()

    def open_module(self,key,table):
        if key=="attendance": return self.app_state._app.open_action("attendance")
        if key=="discipline": return self.app_state._app.open_action("discipline")
        if key=="online_attendance": return self.app_state._app.open_action("online_attendance")
        self.app_state._app.open_table(key,table,self._role())

class RebuildTable(Screen):
    def __init__(self,app_state=None,table="",title="",role="student",**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.table=table; self.title=title; self.role=role; self.rows=[]; self._build()

    def _label(self,text,size="11sp",color=SECONDARY,height=40,bold=False,center=False):
        w=Label(text=rtl_text(text),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="center" if center else "right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v)); return w

    def _button(self,text,cb,color=PRIMARY,height=44):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="11sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(height)); b.bind(on_release=cb); return b

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5))
        head=BoxLayout(size_hint_y=None,height=dp(45),spacing=dp(5)); head.add_widget(self._button("بازگشت",lambda *_:self.app_state._app.show_workspace(),PRIMARY,40)); head.add_widget(self._label(self.title,"18sp",PRIMARY,45,True)); root.add_widget(head)
        self.status=self._label("در حال دریافت داده‌های واقعی…","10sp",SECONDARY,34,True); root.add_widget(self.status)
        self.area=BoxLayout(orientation="vertical",spacing=dp(3),size_hint_y=None); self.area.bind(minimum_height=self.area.setter("height"))
        sc=ScrollView(do_scroll_x=False); sc.add_widget(self.area); root.add_widget(sc)
        self.add_widget(root); Thread(target=self._load,daemon=True).start()

    def _load(self):
        try:
            params={"limit":"100"}
            rows=self.app_state.api.table_select(self.table,params) or []
            Clock.schedule_once(lambda *_:self._render(rows),0)
        except Exception as exc: Clock.schedule_once(lambda *_:self._error(str(exc)),0)

    def _render(self,rows):
        self.rows=[r for r in rows if isinstance(r,dict)]
        self.area.clear_widgets()
        fields=[f for f in TABLES.get(self.table,[]) if f not in HIDDEN]
        if not fields and self.rows: fields=list(self.rows[0].keys())
        self.area.add_widget(self._label("  |  ".join(fields),"10sp",PRIMARY,52,True,True))
        if not self.rows:
            self.area.add_widget(self._label("رکوردی برای نمایش وجود ندارد.","13sp",SECONDARY,60,True,True))
        for row in self.rows:
            vals=[]
            for f in fields: vals.append(str(row.get(f,"") if row.get(f,"") is not None else ""))
            text="\n".join(f"{f}: {v or '—'}" for f,v in zip(fields,vals))
            self.area.add_widget(self._label(text,"11sp",SECONDARY,max(58,34*min(len(fields),5))))
        self.status.text=rtl_text(f"{len(self.rows)} رکورد از جدول «{self.table}»")

    def _error(self,msg):
        self.status.text=rtl_text("خطای فنی در دریافت داده‌ها؛ جزئیات در گزارش برنامه ثبت شد."); self.status.color=ERROR
