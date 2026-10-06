import mimetypes
import uuid
from pathlib import Path
from threading import Thread
from datetime import datetime, timezone
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from mobile.ui import font_name, fa_display, PersianTextInput
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE

MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {"application/pdf", "image/jpeg", "image/png", "image/webp"}

class AssignmentSubmissionScreen(Screen):
    """Real student assignment submission: optional text plus private PDF/image upload."""
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.assignments = []
        self.selected_file = None
        self._build()

    def _label(self, text, size="11sp", color=SECONDARY, height=38, bold=False):
        w=Label(text=fa_display(str(text)),font_name=font_name(),font_size=size,color=color,bold=bold,
                halign="right",valign="middle",size_hint_y=None,height=dp(height))
        w.bind(size=lambda o,v:setattr(o,"text_size",v))
        return w

    def _button(self,text,cb,color=PRIMARY,height=44):
        b=Button(text=fa_display(text),font_name=font_name(),font_size="11sp",
                 background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(height))
        b.bind(on_release=cb); return b

    def _api(self):
        api=getattr(self.app_state,"api",None)
        if api is None: raise RuntimeError("سرویس داده آماده نیست.")
        return api

    def _student_id(self):
        p=getattr(self.app_state,"profile",{}) or {}
        value=p.get("linked_student_id") or p.get("student_id")
        if value: return int(value)
        nc=str(p.get("national_code") or "").strip()
        rows=self._api().table_select("students",{"national_code":"eq."+nc,"select":"id","limit":"1"}) or []
        if not rows: raise RuntimeError("پرونده دانش‌آموزی به حساب متصل نیست.")
        return int(rows[0]["id"])

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(9),spacing=dp(6))
        head=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(5))
        head.add_widget(self._button("بازگشت",self.back,SECONDARY,42))
        head.add_widget(self._label("ارسال تکلیف","18sp",PRIMARY,42,True))
        root.add_widget(head)
        self.status=self._label("در حال دریافت تکالیف…","10sp",SECONDARY,34,True)
        root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False)
        body=BoxLayout(orientation="vertical",spacing=dp(6),padding=[dp(3),dp(5)],size_hint_y=None)
        body.bind(minimum_height=body.setter("height")); self.body=body
        self.assignment_spinner=Spinner(text=fa_display("در حال دریافت…"),values=(),font_name=font_name(),font_size="11sp",size_hint_y=None,height=dp(46))
        body.add_widget(self._label("تکلیف", "10sp", PRIMARY,30,True)); body.add_widget(self.assignment_spinner)
        self.answer=PersianTextInput(hint_text=fa_display("پاسخ یا توضیح دانش‌آموز (اختیاری)"),font_name=font_name(),
                                     font_size="12sp",multiline=True,size_hint_y=None,height=dp(120),halign="right")
        body.add_widget(self._label("پاسخ", "10sp", PRIMARY,30,True)); body.add_widget(self.answer)
        self.file_label=self._label("فایلی انتخاب نشده است","10sp",SECONDARY,48,False)
        body.add_widget(self.file_label)
        body.add_widget(self._button("گرفتن عکس از تکلیف",self.take_photo,SUCCESS,46))
        body.add_widget(self._button("انتخاب تصویر یا PDF",self.pick_file,PRIMARY,46))
        body.add_widget(self._button("ثبت و ارسال واقعی",self.submit,PRIMARY,48))
        body.add_widget(self._button("بازگشت",self.back,SECONDARY,42))
        scroll.add_widget(body); root.add_widget(scroll); self.add_widget(root)

    def on_pre_enter(self,*_):
        Clock.schedule_once(lambda *_: self.load_assignments(),0.02)

    def load_assignments(self):
        self.status.text=fa_display("در حال دریافت تکالیف واقعی…")
        def work():
            try:
                rows=self._api().table_select("assignments",{"order":"id.desc","limit":"200"}) or []
                Clock.schedule_once(lambda *_: self._loaded(rows,None),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._loaded([],str(exc)),0)
        Thread(target=work,daemon=True).start()

    def _loaded(self,rows,error):
        if error:
            self.status.text=fa_display("دریافت تکالیف ناموفق بود: "+error); self.status.color=ERROR; return
        self.assignments=[dict(x) for x in (rows or []) if isinstance(x,dict)]
        values=[f"#{x.get('id')} | {x.get('title') or 'تکلیف'} | {x.get('subject') or ''}" for x in self.assignments]
        self.assignment_spinner.values=tuple(fa_display(x) for x in values)
        self.assignment_spinner.text=fa_display(values[0]) if values else fa_display("تکلیف فعالی یافت نشد")
        self.status.text=fa_display(f"{len(self.assignments)} تکلیف واقعی آماده ارسال است.")
        self.status.color=SUCCESS if self.assignments else ERROR

    def _selected_assignment(self):
        value=str(self.assignment_spinner.text or "")
        for row in self.assignments:
            label=f"#{row.get('id')} | {row.get('title') or 'تکلیف'} | {row.get('subject') or ''}"
            if value in (label,fa_display(label)): return row
        return self.assignments[0] if self.assignments else None

    def take_photo(self,*_):
        try:
            from android import activity
            from jnius import autoclass, cast
            PythonActivity=autoclass("org.kivy.android.PythonActivity")
            Intent=autoclass("android.content.Intent")
            Activity=autoclass("android.app.Activity")
            Bitmap=autoclass("android.graphics.Bitmap")
            current=cast("android.app.Activity",PythonActivity.mActivity)
            request_code=7320
            def on_result(code,result,intent):
                try: activity.unbind(on_activity_result=on_result)
                except Exception: pass
                if code!=request_code or result!=Activity.RESULT_OK or intent is None: return
                try:
                    extras=intent.getExtras()
                    bitmap=extras.get("data") if extras is not None else None
                    if bitmap is None: raise RuntimeError("عکس دوربین دریافت نشد.")
                    from java.io import ByteArrayOutputStream
                    out=ByteArrayOutputStream()
                    bitmap.compress(Bitmap.CompressFormat.JPEG,90,out)
                    self._set_file("assignment_photo.jpg","image/jpeg",bytes(out.toByteArray()))
                    self.status.text=fa_display("عکس تکلیف گرفته شد؛ اکنون ثبت و ارسال را بزنید.")
                    self.status.color=SUCCESS
                except Exception as exc:
                    self.status.text=fa_display("گرفتن عکس انجام نشد: "+str(exc)); self.status.color=ERROR
            activity.bind(on_activity_result=on_result)
            intent=Intent(Intent.ACTION_IMAGE_CAPTURE)
            if not intent.resolveActivity(current.getPackageManager()): raise RuntimeError("دوربین روی دستگاه در دسترس نیست.")
            current.startActivityForResult(intent,request_code)
        except Exception as exc:
            print("ANDROID ASSIGNMENT CAMERA:",repr(exc))
            self.status.text=fa_display("دوربین در این دستگاه در دسترس نیست: "+str(exc)); self.status.color=ERROR
    def pick_file(self,*_):
        try:
            from android import activity
            from jnius import autoclass, cast
            PythonActivity=autoclass("org.kivy.android.PythonActivity")
            Intent=autoclass("android.content.Intent"); Activity=autoclass("android.app.Activity")
            current=cast("android.app.Activity",PythonActivity.mActivity); request_code=7319
            def on_result(code,result,intent):
                try: activity.unbind(on_activity_result=on_result)
                except Exception: pass
                if code!=request_code or result!=Activity.RESULT_OK or intent is None: return
                try:
                    uri=intent.getData(); resolver=current.getContentResolver(); stream=resolver.openInputStream(uri)
                    from java.io import ByteArrayOutputStream
                    out=ByteArrayOutputStream()
                    while True:
                        value=stream.read()
                        if value==-1: break
                        out.write(value)
                    stream.close()
                    data=bytes(out.toByteArray())
                    name=str(uri.getLastPathSegment() or "assignment_file")
                    mime=str(resolver.getType(uri) or mimetypes.guess_type(name)[0] or "application/octet-stream")
                    self._set_file(name,mime,data)
                except Exception as exc:
                    self.status.text=fa_display("خواندن فایل انجام نشد: "+str(exc)); self.status.color=ERROR
            activity.bind(on_activity_result=on_result)
            intent=Intent(Intent.ACTION_OPEN_DOCUMENT); intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*"); intent.putExtra(Intent.EXTRA_MIME_TYPES,["application/pdf","image/jpeg","image/png","image/webp"])
            current.startActivityForResult(intent,request_code)
            return
        except Exception as exc:
            print("ANDROID ASSIGNMENT PICKER:",repr(exc))
        chooser=FileChooserListView(filters=["*.pdf","*.jpg","*.jpeg","*.png","*.webp"])
        root=BoxLayout(orientation="vertical",spacing=dp(5),padding=dp(6)); root.add_widget(chooser)
        actions=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(5)); pop=Popup(title=fa_display("انتخاب فایل"),content=root,size_hint=(.94,.82),auto_dismiss=False)
        actions.add_widget(self._button("انصراف",lambda *_:pop.dismiss(),SECONDARY,40))
        def choose(*_):
            if chooser.selection: 
                try:
                    path=Path(chooser.selection[0]); data=path.read_bytes(); mime=mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                    self._set_file(path.name,mime,data); pop.dismiss()
                except Exception as exc: self.status.text=fa_display("خواندن فایل انجام نشد: "+str(exc)); self.status.color=ERROR
        actions.add_widget(self._button("انتخاب",choose,SUCCESS,40)); root.add_widget(actions); pop.open()

    def _set_file(self,name,mime,data):
        if mime not in ALLOWED:
            raise RuntimeError("فقط PDF و تصویر مجاز است.")
        if len(data)>MAX_BYTES: raise RuntimeError("حجم فایل بیشتر از ۱۰ مگابایت است.")
        self.selected_file=(name,mime,data)
        self.file_label.text=fa_display(f"فایل انتخاب‌شده: {name} • {len(data)/1024/1024:.2f} MB")
        self.file_label.color=SUCCESS

    def submit(self,*_):
        assignment=self._selected_assignment()
        if not assignment: self.status.text=fa_display("ابتدا یک تکلیف انتخاب کنید."); self.status.color=ERROR; return
        answer=(self.answer.get_logical_text() if hasattr(self.answer,"get_logical_text") else self.answer.text or "").strip()
        if not answer and not self.selected_file: self.status.text=fa_display("پاسخ یا فایل را وارد کنید."); self.status.color=ERROR; return
        self.status.text=fa_display("در حال ارسال واقعی…"); self.status.color=SECONDARY
        def work():
            try:
                api=self._api(); sid=self._student_id()
                file_path=None; file_name=None; file_mime=None; file_size=None
                if self.selected_file:
                    file_name,file_mime,data=self.selected_file
                    uid=str((getattr(self.app_state,"profile",{}) or {}).get("auth_user_id") or "")
                    if not uid: raise RuntimeError("شناسه حساب احراز هویت پیدا نشد.")
                    safe_name=str(uuid.uuid4())+"-"+Path(file_name).name.replace("/","_").replace("\\","_")
                    file_path=uid+"/"+safe_name
                    api.storage_upload("assignment-files",file_path,data,file_mime); file_size=len(data)
                payload={"assignment_id":int(assignment["id"]),"student_id":sid,"answer_text":answer or None,
                         "submitted_at":datetime.now(timezone.utc).isoformat(),"status":"submitted"}
                if file_path: payload.update({"file_url":file_path,"file_name":file_name,"file_mime_type":file_mime,"file_size_bytes":file_size})
                api.table_insert("assignment_submissions",payload,return_representation=False)
                Clock.schedule_once(lambda *_: self._done("تکلیف با موفقیت ارسال شد."),0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: self._done("ارسال انجام نشد: "+str(exc),True),0)
        Thread(target=work,daemon=True).start()

    def _done(self,msg,error=False):
        self.status.text=fa_display(msg); self.status.color=ERROR if error else SUCCESS
        if not error: self.answer.text=""; self.selected_file=None; self.file_label.text=fa_display("فایلی انتخاب نشده است.")

    def back(self,*_):
        if self.manager: self.manager.current="panel"
