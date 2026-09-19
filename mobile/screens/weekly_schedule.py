from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

from mobile.config import PRIMARY, SECONDARY, SUCCESS, WHITE, CARD, SCHOOL_NAME
from mobile.ui import font_name, rtl_text, PersianTextInput


DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه"]
BELLS = ["زنگ ۱", "زنگ ۲", "زنگ ۳", "زنگ ۴", "زنگ ۵", "زنگ ۶"]


class WeeklyScheduleScreen(Screen):
    """Real timetable view plus the same three record operations used by modules."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.rows = []
        self.generated = []
        self.selected = None
        self._build()

    def label(self, text, size="10sp", color=SECONDARY, bold=False, center=False, height=34):
        w = Label(text=rtl_text(str(text)), font_name=font_name(), font_size=size,
                  color=color, bold=bold, halign="center" if center else "right",
                  valign="middle", size_hint_y=None, height=dp(height))
        w.bind(size=lambda o,v:setattr(o, "text_size", v))
        return w

    def btn(self, text, cb, color=PRIMARY, h=42):
        b=Button(text=rtl_text(text),font_name=font_name(),font_size="10sp",
                 background_normal="",background_color=color,color=WHITE,
                 size_hint_y=None,height=dp(h))
        b.bind(on_release=cb)
        return b

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(6))
        top=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(5))
        top.add_widget(self.btn("بازگشت", self.back, PRIMARY, 40))
        top.add_widget(self.label("برنامه هفتگی مدرسه", "18sp", PRIMARY, True, True, 42))
        root.add_widget(top)
        root.add_widget(self.label(f"{SCHOOL_NAME} • جدول واقعی روز × زنگ × کلاس × درس × دبیر", "9sp", SECONDARY, False, True, 26))
        self.status=self.label("در حال دریافت برنامه…","9sp",SUCCESS,True,True,26)
        root.add_widget(self.status)

        actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5))
        actions.add_widget(self.btn("ثبت جدید",lambda *_:self.editor(None),SUCCESS,40))
        actions.add_widget(self.btn("ویرایش",lambda *_:self.editor(self.selected),PRIMARY,40))
        actions.add_widget(self.btn("حذف",lambda *_:self.delete_selected(),(0.72,.16,.18,1),40))
        root.add_widget(actions)

        self.area=BoxLayout(orientation="vertical",spacing=dp(5))
        root.add_widget(self.area)
        self.add_widget(root)

    def on_pre_enter(self,*_):
        Clock.schedule_once(lambda *_:self.load(),0.03)

    def _api(self):
        api=getattr(self.app_state,"api",None)
        if api is None: raise RuntimeError("سرویس داده آماده نیست.")
        return api

    def _async(self,work,done):
        def run():
            try:
                value=work()
                Clock.schedule_once(lambda *_:done(value,None),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_:done(None,str(exc)),0)
        Thread(target=run,daemon=True).start()

    def load(self,*_):
        self.status.text=rtl_text("در حال دریافت برنامه واقعی…")
        self._async(self._fetch,self._loaded)

    def _fetch(self):
        api=self._api()
        base=api.table_select("weekly_schedule",{"limit":"200"}) or []
        generated=[]
        try:
            generated=api.table_select("generated_weekly_schedule",{"limit":"300"}) or []
        except Exception:
            generated=[]
        return {"base":base,"generated":generated}

    def _loaded(self,data,error):
        if error:
            self.status.text=rtl_text("خطا در دریافت برنامه: "+error)
            return
        self.rows=list((data or {}).get("base") or [])
        self.generated=list((data or {}).get("generated") or [])
        self.status.text=rtl_text(f"{len(self.rows)} تعریف برنامه • {len(self.generated)} جلسه زمان‌بندی‌شده")
        self._render_timetable()

    def _render_timetable(self):
        self.area.clear_widgets()
        source=self.generated or self.rows
        if not source:
            self.area.add_widget(self.label("هنوز برنامه هفتگی ثبت نشده است.","15sp",PRIMARY,True,True,100))
            return

        scroll=ScrollView(do_scroll_x=True,do_scroll_y=True)
        width=dp(6*190+90)
        grid=GridLayout(cols=7,spacing=dp(3),padding=dp(3),size_hint=(None,None),width=width)
        grid.bind(minimum_height=grid.setter("height"))
        grid.add_widget(self._cell("زنگ / روز",True))
        for d in DAYS: grid.add_widget(self._cell(d,True))

        for bell in BELLS:
            grid.add_widget(self._cell(bell,True))
            for day in DAYS:
                matches=[r for r in source if self._day(r)==day and self._bell(r)==bell]
                text="—"
                if matches:
                    vals=[]
                    for r in matches[:2]:
                        vals.append(" | ".join([str(r.get("subject") or "درس نامشخص"),
                                                str(r.get("teacher") or r.get("teacher_name") or "دبیر نامشخص"),
                                                str(r.get("class_name") or r.get("class_names") or "کلاس")]))
                    text="\n".join(vals)
                cell=self._cell(text,False)
                grid.add_widget(cell)
        scroll.add_widget(grid)
        self.area.add_widget(scroll)

        self.area.add_widget(self.label("برای ویرایش یا حذف، ابتدا یک تعریف برنامه را از فهرست پایین انتخاب کنید.","9sp",SECONDARY,False,True,32))
        list_scroll=ScrollView(do_scroll_x=False)
        lst=BoxLayout(orientation="vertical",spacing=dp(4),size_hint_y=None)
        lst.bind(minimum_height=lst.setter("height"))
        for r in self.rows:
            row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(4))
            title=" • ".join([str(r.get("teacher") or r.get("teacher_name") or "دبیر"),
                              str(r.get("subject") or "درس"),
                              str(r.get("class_names") or r.get("class_name") or "کلاس"),
                              str(r.get("weekdays") or "روز")])
            row.add_widget(self.label(title,"9sp",SECONDARY,False,False,44))
            row.add_widget(self.btn("انتخاب",lambda *_a,x=r:self._select(x),PRIMARY,40))
            lst.add_widget(row)
        list_scroll.add_widget(lst)
        self.area.add_widget(list_scroll)

    def _cell(self,text,header=False):
        c=BoxLayout(orientation="vertical",padding=dp(5),size_hint=(None,None),width=dp(190),height=dp(66 if header else 86))
        c.add_widget(self.label(text,"9sp",WHITE if header else SECONDARY,header,True, c.height))
        from kivy.graphics import Color, RoundedRectangle
        with c.canvas.before:
            Color(*(PRIMARY if header else CARD))
            bg=RoundedRectangle(radius=[dp(7)])
        c.bind(pos=lambda o,v:setattr(bg,"pos",v),size=lambda o,v:setattr(bg,"size",v))
        return c

    def _day(self,r):
        raw=str(r.get("weekday") or r.get("weekdays") or r.get("day") or "")
        for d in DAYS:
            if d in raw: return d
        mapping={"Saturday":"شنبه","Sunday":"یکشنبه","Monday":"دوشنبه","Tuesday":"سه‌شنبه","Wednesday":"چهارشنبه","Thursday":"پنجشنبه"}
        for en,fa in mapping.items():
            if en.lower() in raw.lower(): return fa
        return DAYS[0]

    def _bell(self,r):
        raw=str(r.get("bell") or r.get("bell_pattern") or r.get("period") or r.get("lesson_period") or "")
        for i,b in enumerate(BELLS,1):
            if str(i) in raw or b in raw: return b
        return BELLS[0]

    def _select(self,row):
        self.selected=row
        self.status.text=rtl_text("یک تعریف برنامه انتخاب شد؛ برای ویرایش یا حذف اقدام کنید.")

    def editor(self,row):
        fields=[("teacher","نام دبیر"),("subject","نام درس"),("grade","پایه"),("class_names","نام کلاس‌ها"),("hours","ساعت هفتگی"),("bell_pattern","الگوی زنگ"),("weekdays","روزهای هفته")]
        root=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(5))
        scroll=ScrollView()
        form=BoxLayout(orientation="vertical",size_hint_y=None,spacing=dp(5))
        form.bind(minimum_height=form.setter("height"))
        inputs={}
        for k,h in fields:
            form.add_widget(self.label(h,"9sp",PRIMARY,True,False,26))
            ti=PersianTextInput(text="" if row is None else str(row.get(k,"")),hint_text=rtl_text(h),
                               font_name=font_name(),font_size="12sp",halign="right",
                               size_hint_y=None,height=dp(42))
            inputs[k]=ti; form.add_widget(ti)
        scroll.add_widget(form); root.add_widget(scroll)
        actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5))
        p=Popup(title=rtl_text(("ویرایش" if row else "ثبت جدید")+" • برنامه هفتگی"),content=root,size_hint=(.94,.88),auto_dismiss=False)
        actions.add_widget(self.btn("انصراف",lambda *_:p.dismiss(),SECONDARY,40))
        actions.add_widget(self.btn("ذخیره",lambda *_:self.save(row,inputs,p),SUCCESS,40))
        root.add_widget(actions); p.open()

    def save(self,row,inputs,p):
        payload={k:v.text.strip() for k,v in inputs.items() if v.text.strip()}
        if not payload:
            self.status.text=rtl_text("حداقل اطلاعات برنامه را وارد کنید."); return
        p.dismiss()
        self.status.text=rtl_text("در حال ذخیره…")
        def work():
            if row is None: self._api().table_insert("weekly_schedule",payload)
            else: self._api().table_update("weekly_schedule",{"id":"eq."+str(row.get("id"))},payload)
        self._async(work,lambda _,e:self._write_done("برنامه ثبت شد." if row is None else "برنامه ویرایش شد.",e))

    def _write_done(self,msg,error):
        self.status.text=rtl_text(("خطا: "+error) if error else msg)
        if not error: self.load()

    def delete_selected(self):
        if not self.selected or not self.selected.get("id"):
            self.status.text=rtl_text("ابتدا یک ردیف از تعریف برنامه را انتخاب کنید.")
            return
        rid=self.selected["id"]
        def work(): self._api().table_delete("weekly_schedule",{"id":"eq."+str(rid)})
        self._async(work,lambda _,e:self._write_done("برنامه حذف شد.",e))

    def back(self,*_):
        if self.manager: self.manager.current="panel"
