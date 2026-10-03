from datetime import datetime, timezone
import random

from kivy.clock import Clock
from kivy.uix.popup import Popup

from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView

from mobile.config import APP_NAME, PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE
from mobile.ui import font_name, rtl_text, fa_display, PersianTextInput, PersianSpinner

MANAGERS={"manager","educational","executive"}
CLASS_CREATORS={"manager","educational","executive"}
CLASS_MANAGERS={"manager","educational","executive"}


def role_of(state):
    # Login may keep the canonical role in profile while app_state.role is empty.
    # Resolve both sources so operational create/manage controls are not hidden.
    # A live workflow can be opened from a specific school panel. Prefer that active panel role over a stale profile role.
    profile = getattr(state, "profile", {}) or {}
    active_panel = str(getattr(state, "panel_role", "") or "").strip().lower()
    if active_panel:
        normalized_panel = {"management":"manager","teachers":"teacher","teacher_panel":"teacher","teacher_dashboard":"teacher","دبیران":"teacher","کادر و دبیران":"teacher"}.get(active_panel, active_panel)
        if normalized_panel in {"manager","educational","executive","cultural","advisor","teacher","staff","student","parent"}:
            return normalized_panel
    profile = getattr(state, "profile", {}) or {}
    user = getattr(state, "user", {}) or {}
    metadata = user.get("user_metadata", {}) if isinstance(user, dict) else {}
    candidates = [
        profile.get("role"),
        profile.get("user_role"),
        profile.get("school_role"),
        metadata.get("role"),
        metadata.get("user_role"),
        metadata.get("school_role"),
        getattr(state, "role", None),
        profile.get("user_type"),
        profile.get("account_type"),
        profile.get("permissions", {}).get("role") if isinstance(profile.get("permissions"), dict) else None,
    ]
    raw = next((str(v).strip().lower() for v in candidates if str(v or "").strip()), "")
    raw = raw.replace("\u200c", " ").replace("\u200f", "").replace("ي", "ی").replace("ك", "ک")
    raw = " ".join(raw.split())
    if not raw:
        token = str(getattr(getattr(state, "api", None), "access_token", "") or "")
        raw = "staff" if token else "student"
    return {
        "admin":"manager","administrator":"manager","principal":"manager","manager":"manager","management":"manager","management_panel":"manager","school_management":"manager","مدیریت پنل":"manager","پنل مدیریت":"manager",
        "مدیر":"manager","مدیریت":"manager","مدیر مدرسه":"manager","مدیریت مدرسه":"manager",
        "معاون آموزشی":"educational","معاونت آموزشی":"educational","educational":"educational","educational_deputy":"educational",
        "معاون اجرایی":"executive","معاونت اجرایی":"executive","اجرایی":"executive","executive":"executive","executive_deputy":"executive","کادر اجرایی":"executive",
        "معاون پرورشی":"cultural","معاونت پرورشی":"cultural","پرورشی":"cultural","cultural":"cultural","cultural_deputy":"cultural","کادر پرورشی":"cultural",
        "مشاور":"advisor","مشاوره":"advisor","counselor":"counselor","counseling":"counselor","advisor":"advisor",
        "دبیر":"teacher","معلم":"teacher","teacher":"teacher","teachers":"teacher","teacher_staff":"teacher","staff":"staff","school_staff":"staff","staff_teacher":"teacher",
        "دانش‌آموز":"student","دانش آموز":"student","student":"student",
        "ولی":"parent","اولیا":"parent","والد":"parent","parent":"parent","parents":"parent","guardian":"parent",
    }.get(raw, raw)


class OnlineClassScreen(Screen):
    def __init__(self,app_state=None,**kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self.current_id=None; self.selected_class=None; self.mic=True; self.camera=True; self._build(); self._checkpoint_events=[]; self._checkpoint_session_id=None; self._checkpoint_student_id=None; self._checkpoint_class_id=None; self._checkpoint_name=""
    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(7)); head=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(7))
        back=Button(text=fa_display("‹ داشبورد"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(100)); back.bind(on_release=lambda *_:self._back()); head.add_widget(back)
        self.title=Label(text=fa_display("کلاس‌های آنلاین"),font_name=font_name(),font_size="20sp",bold=True,color=PRIMARY,halign="right",valign="middle"); self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title); root.add_widget(head)
        self.status=Label(text="",font_name=font_name(),font_size="11sp",color=SECONDARY,halign="center",valign="middle",size_hint_y=None,height=dp(38)); self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False); self.body=BoxLayout(orientation="vertical",spacing=dp(8),padding=dp(4),size_hint_y=None); self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root)
    def on_pre_enter(self,*args): self.show_home()
    def _clear(self): self.body.clear_widgets(); self.current_id=None; self.selected_class=None
    def _label(self,text,size="13sp",color=SECONDARY,height=58,bold=False):
        w=Label(text=fa_display(text),font_name=font_name(),font_size=size,color=color,bold=bold,halign="right",valign="middle",size_hint_y=None,height=dp(height)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w
    def _button(self,text,cb,color=PRIMARY,height=46):
        b=Button(text=fa_display(text),font_name=font_name(),font_size="13sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(height)); b.bind(on_press=cb); self.body.add_widget(b); return b
    def _field(self,hint,height=48,multiline=False):
        f=PersianTextInput(hint_text=fa_display(hint),font_name=font_name(),font_size="13sp",multiline=multiline,size_hint_y=None,height=dp(height),halign="right",padding=[dp(10),dp(10)]); self.body.add_widget(f); return f
    def show_home(self):
        self._clear(); role=role_of(self.app_state); self._label("کلاس آنلاین واقعی","21sp",PRIMARY,52,True); self._label("ساخت کلاس، شروع/پایان جلسه، حضور و غیاب، گفت‌وگو، تخته مشترک، کنترل دوربین/میکروفون و اطلاع غیبت به ولی در همین پنل ثبت می‌شود.",height=82)
        if role in CLASS_CREATORS:
            # Only manager, executive deputy and educational deputy can form classes.
            # Teachers/students/parents may use the classes but cannot create them.
            # Keep the creation action above the class list so it is visible
            # immediately on a phone-sized screen.
            self._button("ساخت و تولید کلاس جدید",lambda *_:self._open_create_form(),SUCCESS,56)
            self._create_form()
        self._load_classes()

    def _open_create_form(self):
        self._clear()
        role=role_of(self.app_state)
        if role not in CLASS_CREATORS:
            return self._error("فقط مدیر، معاون اجرایی و معاون آموزشی اجازه تشکیل کلاس آنلاین دارند.")
        self._label("ساخت و تولید کلاس آنلاین","21sp",PRIMARY,52,True)
        self._create_form()
        self._button("بازگشت به فهرست کلاس‌ها",lambda *_:self.show_home(),SECONDARY,46)
    def _create_form(self):
        self._label("تشکیل کلاس آنلاین","21sp",PRIMARY,52,True)
        grade=self._field("پایه تحصیلی")
        class_name=self._field("نام کلاس")
        subject=self._field("نام درس")
        start=self._field("زمان شروع")
        end=self._field("زمان پایان")
        self._label("پس از ثبت کلاس، دبیران و دانش‌آموزان را می‌توانید به‌صورت دستی یا Excel متصل کنید.","12sp",SECONDARY,58,True)
        self._button("＋ ثبت کلاس",lambda *_:self._create(grade,class_name,subject,start,end),SUCCESS)
    def _create(self,grade,class_name,subject,start,end):
        api=getattr(self.app_state,"api",None)
        if api is None: return self._error("سرویس اتصال به پایگاه داده آماده نیست.")
        role=role_of(self.app_state)
        if role not in CLASS_CREATORS: return self._error("فقط مدیر، معاون اجرایی و معاون آموزشی اجازه تشکیل کلاس آنلاین دارند.")
        if not getattr(api,"access_token",""): return self._error("نشست ورود معتبر نیست؛ دوباره وارد فراهوش شوید.")
        vals=[]
        for w in (grade,class_name,subject,start,end):
            vals.append((w.get_logical_text() if hasattr(w,"get_logical_text") else w.text or "").strip())
        grade_value,class_value,subject_value,start_value,end_value=vals
        if not all(vals): return self._error("پایه، نام کلاس، نام درس، زمان شروع و زمان پایان الزامی است.")
        try:
            class_id=int(api.rpc("create_online_class_with_members",{
                "p_teacher_id":None,
                "p_subject":subject_value,
                "p_grade":grade_value,
                "p_class_name":class_value,
                "p_start_time":start_value,
                "p_end_time":end_value,
                "p_join_url":"frahoosh://pending",
            }))
            api.table_update("online_classes",{"id":"eq."+str(class_id)},{
                "join_url":"frahoosh://online-class/"+str(class_id),
                "meeting_url":"frahoosh://online-class/"+str(class_id)
            })
            self._ok("کلاس ساخته شد؛ اکنون می‌توانید چند دبیر و چند دانش‌آموز را دستی یا با Excel متصل کنید. کد کلاس: "+str(class_id))
            self._members(class_id)
        except Exception as exc:
            self._error("ثبت کلاس در Supabase انجام نشد: "+str(exc))
    def _load_classes(self):
        api=self.app_state.api
        role=role_of(self.app_state)
        try:
            if role=="teacher":
                memberships=api.table_select("online_class_teachers",{"teacher_id":"eq."+str(self._current_teacher_id()),"order":"class_id.desc","limit":"100"}) or []
                class_ids=[int(x["class_id"]) for x in memberships if x.get("class_id") is not None]
                if not class_ids:
                    self._label("هنوز کلاسی به این دبیر متصل نشده است.",height=55)
                    return
                filt="eq."+str(class_ids[0]) if len(class_ids)==1 else "in.("+",".join(str(x) for x in class_ids)+")"
                rows=api.table_select("online_classes",{"id":filt,"order":"id.desc","limit":"100"}) or []
            elif role=="student":
                memberships=api.table_select("online_class_students",{"student_id":"eq."+str(self._current_student_id()),"order":"class_id.desc","limit":"100"}) or []
                class_ids=[int(x["class_id"]) for x in memberships if x.get("class_id") is not None]
                if not class_ids:
                    self._label("هنوز کلاسی به این دانش‌آموز متصل نشده است.",height=55)
                    return
                filt="eq."+str(class_ids[0]) if len(class_ids)==1 else "in.("+",".join(str(x) for x in class_ids)+")"
                rows=api.table_select("online_classes",{"id":filt,"order":"id.desc","limit":"100"}) or []
            else:
                rows=api.table_select("online_classes",{"order":"id.desc","limit":"100"}) or []
        except Exception as exc:
            return self._error("خواندن کلاس‌ها انجام نشد: "+str(exc))
        if not rows:
            self._label("هنوز کلاسی ثبت نشده است.",height=55)
            return
        for r in rows:
            cid=r.get("id"); state=str(r.get("status") or "inactive")
            self._label(
                f"{r.get('teacher') or '-'} | {r.get('subject') or r.get('lesson') or '-'}\n"
                f"شروع: {r.get('start_clock') or r.get('start_time') or r.get('start_time_shamsi') or '-'}"
                f"   پایان: {r.get('end_clock') or r.get('end_time') or r.get('end_time_shamsi') or '-'}\n"
                f"وضعیت: {'فعال' if state=='active' else ('پایان‌یافته' if state=='ended' else 'غیرفعال')}",
                height=86,bold=True
            )
            if role in CLASS_MANAGERS:
                self._button("ویرایش کلاس",lambda *_ ,row=dict(r):self._edit_class(row),PRIMARY)
                self._button("حذف کلاس",lambda *_ ,x=cid:self._delete_class(x),ERROR)
                self._button("اتصال دانش‌آموز به کلاس",lambda *_ ,x=cid:self._add_student(x),SUCCESS)
                self._button("اتصال دبیر به کلاس",lambda *_ ,x=cid:self._add_teacher(x),SUCCESS)
                self._button("اعضای کلاس",lambda *_ ,x=cid:self._members(x),PRIMARY)
                self._button("خروجی اکسل کلاس‌ها",lambda *_:self._export_excel(),PRIMARY)
                self._button("ورودی اکسل کلاس‌ها",lambda *_:self._import_excel(),PRIMARY)
                if state!="active": self._button("شروع جلسه",lambda *_ ,x=cid:self._start(x),SUCCESS)
                if state=="active": self._button("پایان جلسه",lambda *_ ,x=cid:self._end(x),ERROR)
                self._button("حضور و غیاب",lambda *_ ,x=cid:self._attendance(x),PRIMARY)
                self._button("اعلام غیبت به ولی",lambda *_ ,x=cid:self._absence_notice(x),PRIMARY)
            if state=="active":
                url=r.get("join_url") or r.get("meeting_url")
                if url:self._button("ورود به جلسه و فعال‌سازی دوربین/میکروفون",lambda *_ ,u=url,x=cid:self._join(u,x),SUCCESS)
                self._button(f"میکروفون: {'روشن' if self.mic else 'خاموش'}",lambda *_:self._toggle_mic(),SECONDARY)
                self._button(f"دوربین: {'روشن' if self.camera else 'خاموش'}",lambda *_:self._toggle_camera(),SECONDARY)

    def _edit_class(self,row):
        self._clear()
        self._label("ویرایش کلاس #"+str(row.get("id")),"21sp",PRIMARY,52,True)
        teacher=self._field("نام دبیر"); teacher.set_logical_text(str(row.get("teacher") or ""))
        subject=self._field("نام درس"); subject.set_logical_text(str(row.get("subject") or row.get("lesson") or ""))
        start=self._field("زمان شروع"); start.set_logical_text(str(row.get("start_clock") or row.get("start_time") or row.get("start_time_shamsi") or ""))
        end=self._field("زمان پایان"); end.set_logical_text(str(row.get("end_clock") or row.get("end_time") or row.get("end_time_shamsi") or ""))
        self._button("ذخیره ویرایش",lambda *_:self._save_class_edit(row.get("id"),teacher,subject,start,end),SUCCESS)
        self._button("بازگشت",lambda *_:self.show_home(),SECONDARY)

    def _save_class_edit(self,cid,teacher,subject,start,end):
        try:
            teacher_value=(teacher.get_logical_text() if hasattr(teacher,"get_logical_text") else teacher.text).strip()
            subject_value=(subject.get_logical_text() if hasattr(subject,"get_logical_text") else subject.text).strip()
            start_value=(start.get_logical_text() if hasattr(start,"get_logical_text") else start.text).strip()
            end_value=(end.get_logical_text() if hasattr(end,"get_logical_text") else end.text).strip()
            if not teacher_value or not subject_value or not start_value or not end_value:
                return self._error("نام دبیر، نام درس، زمان شروع و زمان پایان الزامی است.")
            self.app_state.api.table_update("online_classes",{"id":f"eq.{cid}"},{
                "title":f"{subject_value} - {teacher_value}",
                "subject":subject_value,
                "lesson":subject_value,
                "teacher":teacher_value,
                "start_time":start_value,
                "end_time":end_value,
                "start_time_shamsi":start_value,
                "end_time_shamsi":end_value,
            })
            self._ok("کلاس با موفقیت ویرایش شد.")
            self.show_home()
        except Exception as exc:
            self._error("ویرایش کلاس انجام نشد: "+str(exc))

    def _delete_class(self,cid):
        try:
            rows=self.app_state.api.table_select("online_classes",{"id":f"eq.{cid}","limit":"1"}) or []
            if not rows: return self._error("کلاس پیدا نشد.")
            self.app_state.api.table_delete("online_classes",{"id":f"eq.{cid}"})
            self._ok("کلاس با موفقیت حذف شد."); self.show_home()
        except Exception as exc:
            self._error("حذف کلاس انجام نشد: "+str(exc))

    def _excel_path(self):
        from pathlib import Path
        p=Path("/storage/emulated/0/Download/frahoosh_online_classes.xlsx")
        try: p.parent.mkdir(parents=True,exist_ok=True)
        except Exception: pass
        return p

    def _export_excel(self):
        try:
            from openpyxl import Workbook
            rows=self.app_state.api.table_select("online_classes",{"limit":"1000"}) or []
            fields=["id","teacher","subject","start_time","end_time","status","join_url","meeting_url"]
            wb=Workbook(); ws=wb.active; ws.title="کلاس‌های آنلاین"
            ws.append(fields)
            for r in rows: ws.append([r.get(k,"") for k in fields])
            path=self._excel_path(); wb.save(str(path))
            self._ok("خروجی Excel ذخیره شد: Download/frahoosh_online_classes.xlsx")
        except Exception as exc:
            self._error("خروجی Excel انجام نشد: "+str(exc))

    def _import_excel(self):
        from pathlib import Path
        path=self._excel_path()
        if not path.is_file():
            return self._error("فایل frahoosh_online_classes.xlsx را در پوشه Download گوشی قرار دهید.")
        try:
            from openpyxl import load_workbook
            wb=load_workbook(str(path),read_only=True,data_only=True); ws=wb.active
            rows=list(ws.iter_rows(values_only=True))
            if not rows: return self._error("فایل Excel خالی است.")
            headers=[str(x or "").strip() for x in rows[0]]
            allowed={"title","teacher","subject","lesson","grade","class_name","duration","start_time","end_time","start_time_shamsi","end_time_shamsi","status","join_url","meeting_url"}
            inserted=0
            for values in rows[1:]:
                payload={}
                for i,v in enumerate(values):
                    if i>=len(headers) or headers[i] not in allowed or v in (None,""): continue
                    payload[headers[i]]=v
                if payload:
                    payload.setdefault("title", payload.get("subject") or "کلاس آنلاین")
                    payload.setdefault("duration", 60)
                    try: payload["duration"]=max(1,int(payload.get("duration") or 60))
                    except Exception: payload["duration"]=60
                    if payload.get("start_time") and not payload.get("start_time_shamsi"):
                        payload["start_time_shamsi"]=payload["start_time"]
                    if payload.get("end_time") and not payload.get("end_time_shamsi"):
                        payload["end_time_shamsi"]=payload["end_time"]
                    self.app_state.api.table_insert("online_classes",payload,return_representation=False); inserted+=1
            wb.close(); self._ok(f"{inserted} کلاس از Excel وارد شد."); self.show_home()
        except Exception as exc:
            self._error("ورودی Excel انجام نشد: "+str(exc))

    def _current_teacher_id(self):
        profile=getattr(self.app_state,"profile",{}) or {}
        value=profile.get("linked_teacher_id") or profile.get("teacher_id")
        if value:
            return int(value)
        national_code=str(profile.get("national_code") or "").strip()
        if national_code:
            rows=self.app_state.api.table_select("teachers",{"national_code":"eq."+national_code,"limit":"1"}) or []
            if rows and rows[0].get("id") is not None:
                return int(rows[0]["id"])
        raise RuntimeError("شناسه دبیر جاری در سامانه پیدا نشد.")

    def _current_student_id(self):
        profile=getattr(self.app_state,"profile",{}) or {}
        value=profile.get("linked_student_id") or profile.get("student_id")
        if value:
            return int(value)
        national_code=str(profile.get("national_code") or "").strip()
        if national_code:
            rows=self.app_state.api.table_select("students",{"national_code":"eq."+national_code,"limit":"1"}) or []
            if rows and rows[0].get("id") is not None:
                return int(rows[0]["id"])
        raise RuntimeError("شناسه دانش‌آموز جاری در سامانه پیدا نشد.")

    def _add_student(self,cid):
        self._clear()
        self._label("اتصال دانش‌آموز به کلاس #"+str(cid),"21sp",PRIMARY,50,True)
        try:
            rows=self.app_state.api.table_select("students",{"order":"id.asc","limit":"200"}) or []
        except Exception as exc:
            return self._error("فهرست دانش‌آموزان خوانده نشد: "+str(exc))
        self._student_rows=rows
        labels=[str(x.get("id"))+" | "+str(x.get("first_name") or "")+" "+str(x.get("last_name") or "")+" | "+str(x.get("class_name") or "") for x in rows]
        if not labels: return self._error("هیچ دانش‌آموزی در سامانه ثبت نشده است.")
        self._student_spin_map={fa_display(label):int(row.get("id")) for label,row in zip(labels,rows)}
        visual_labels=tuple(self._student_spin_map.keys())
        spin=PersianSpinner(text=visual_labels[0],values=visual_labels,font_size="12sp",size_hint_y=None,height=dp(50))
        self.body.add_widget(spin)
        self._button("ثبت اتصال دانش‌آموز",lambda *_:self._save_student(cid,spin),SUCCESS)
        self._label("یا ثبت دستی نام دانش‌آموز", "14sp", PRIMARY, 38, True)
        manual_name=self._field("نام و نام خانوادگی دانش‌آموز")
        manual_code=self._field("کد ملی (اختیاری)")
        self._button("ثبت دستی و اتصال دانش‌آموز",lambda *_:self._save_manual_member(cid,manual_name,manual_code,"student"),SUCCESS)
        self._button("ورود Excel دانش‌آموزان",lambda *_:self._import_member_excel(cid,"student"),PRIMARY)
        self._label("قالب Excel: id یا نام و نام خانوادگی یا کد ملی", "11sp", SECONDARY, 42)
        self._button("بازگشت",lambda *_:self.show_home(),SECONDARY)

    def _member_name(self, row, kind):
        if kind == "teacher":
            return (str(row.get("first_name") or "")+" "+str(row.get("last_name") or "")).strip()
        return (str(row.get("first_name") or "")+" "+str(row.get("last_name") or "")).strip()

    def _find_member_by_text(self, text, kind, national_code=""):
        table = "teachers" if kind == "teacher" else "students"
        value = str(text or "").strip()
        code = str(national_code or "").strip()
        rows = self.app_state.api.table_select(table, {"limit":"1000"}) or []
        def norm(v):
            return " ".join(str(v or "").replace("\u200c"," ").replace("ي","ی").replace("ك","ک").split()).strip().lower()
        if code:
            for row in rows:
                if str(row.get("national_code") or "").strip() == code:
                    return row
        wanted = norm(value)
        for row in rows:
            if norm(self._member_name(row, kind)) == wanted:
                return row
        return None

    def _save_manual_member(self, cid, name_input, code_input, kind):
        try:
            name=(name_input.get_logical_text() if hasattr(name_input,"get_logical_text") else name_input.text or "").strip()
            code=(code_input.get_logical_text() if hasattr(code_input,"get_logical_text") else code_input.text or "").strip()
            if not name and not code:
                return self._error("نام یا کد ملی را وارد کنید.")
            row=self._find_member_by_text(name, kind, code)
            if not row or row.get("id") is None:
                return self._error("این فرد در فهرست اصلی فراهوش پیدا نشد؛ ابتدا او را در بخش دانش‌آموزان یا دبیران ثبت کنید.")
            table="online_class_teachers" if kind == "teacher" else "online_class_students"
            id_field="teacher_id" if kind == "teacher" else "student_id"
            name_field="teacher_name" if kind == "teacher" else "student_name"
            member_id=int(row["id"])
            existing=self.app_state.api.table_select(table,{"class_id":"eq."+str(cid),id_field:"eq."+str(member_id),"limit":"1"}) or []
            if not existing:
                self.app_state.api.table_insert(table,{"class_id":cid,id_field:member_id,name_field:self._member_name(row,kind)})
            self._ok(("دبیر" if kind=="teacher" else "دانش‌آموز")+" به کلاس متصل شد.")
            self._members(cid)
        except Exception as exc:
            self._error("ثبت عضو انجام نشد: "+str(exc))

    def _import_member_excel(self, cid, kind):
        from pathlib import Path
        from openpyxl import load_workbook
        filename="frahoosh_online_class_teachers.xlsx" if kind=="teacher" else "frahoosh_online_class_students.xlsx"
        path=Path("/storage/emulated/0/Download/")+Path(filename)
        if not path.is_file():
            return self._error("فایل "+filename+" را در پوشه Download گوشی قرار دهید.")
        try:
            wb=load_workbook(str(path),read_only=True,data_only=True); ws=wb.active
            rows=list(ws.iter_rows(values_only=True)); wb.close()
            if not rows: return self._error("فایل Excel خالی است.")
            headers=[str(x or "").strip().lower() for x in rows[0]]
            allowed={"id","شناسه","name","نام","نام و نام خانوادگی","national_code","کد ملی"}
            table="online_class_teachers" if kind=="teacher" else "online_class_students"
            id_field="teacher_id" if kind=="teacher" else "student_id"
            name_field="teacher_name" if kind=="teacher" else "student_name"
            source_table="teachers" if kind=="teacher" else "students"
            inserted=0; skipped=0
            for values in rows[1:]:
                data={}
                for i,v in enumerate(values):
                    if i < len(headers) and headers[i] in allowed and v not in (None,""):
                        data[headers[i]]=v
                member_id=data.get("id") or data.get("شناسه")
                name=data.get("name") or data.get("نام") or data.get("نام و نام خانوادگی") or ""
                code=data.get("national_code") or data.get("کد ملی") or ""
                member=None
                if member_id:
                    found=self.app_state.api.table_select(source_table,{"id":"eq."+str(int(member_id)),"limit":"1"}) or []
                    member=found[0] if found else None
                if member is None:
                    member=self._find_member_by_text(name,kind,code)
                if not member or member.get("id") is None:
                    skipped+=1; continue
                mid=int(member["id"])
                existing=self.app_state.api.table_select(table,{"class_id":"eq."+str(cid),id_field:"eq."+str(mid),"limit":"1"}) or []
                if existing:
                    skipped+=1; continue
                self.app_state.api.table_insert(table,{"class_id":cid,id_field:mid,name_field:self._member_name(member,kind)})
                inserted+=1
            self._ok(str(inserted)+" "+("دبیر" if kind=="teacher" else "دانش‌آموز")+" از Excel به کلاس متصل شد؛ "+str(skipped)+" مورد تکراری/نامعتبر رد شد.")
            self._members(cid)
        except Exception as exc:
            self._error("ورودی Excel اعضای کلاس انجام نشد: "+str(exc))

    def _save_student(self,cid,spin):
        try:
            sid=self._student_spin_map.get(str(spin.text))
            if sid is None:
                return self._error("دانش‌آموز انتخاب‌شده معتبر نیست.")
            row=next((x for x in self._student_rows if int(x.get("id"))==int(sid)),None)
            if not row: return self._error("دانش‌آموز انتخاب‌شده پیدا نشد.")
            existing=self.app_state.api.table_select("online_class_students",{"class_id":"eq."+str(cid),"student_id":"eq."+str(sid),"limit":"1"}) or []
            if not existing:
                name=(str(row.get("first_name") or "")+" "+str(row.get("last_name") or "")).strip()
                self.app_state.api.table_insert("online_class_students",{"class_id":cid,"student_id":sid,"student_name":name})
            self._ok("دانش‌آموز به کلاس متصل شد."); self._members(cid)
        except Exception as exc:self._error("اتصال دانش‌آموز انجام نشد: "+str(exc))
    def _add_teacher(self,cid):
        self._clear()
        self._label("اتصال دبیر به کلاس #"+str(cid),"21sp",PRIMARY,50,True)
        try:
            rows=self.app_state.api.table_select("teachers",{"order":"id.asc","limit":"100"}) or []
        except Exception as exc:
            return self._error("فهرست دبیران خوانده نشد: "+str(exc))
        self._teacher_rows=rows
        labels=[str(x.get("id"))+" | "+str(x.get("first_name") or "")+" "+str(x.get("last_name") or "")+" | "+str(x.get("subject") or "") for x in rows]
        if not labels: return self._error("هیچ دبیری در سامانه ثبت نشده است.")
        self._teacher_spin_map={fa_display(label):int(row.get("id")) for label,row in zip(labels,rows)}
        visual_labels=tuple(self._teacher_spin_map.keys())
        spin=PersianSpinner(text=visual_labels[0],values=visual_labels,font_size="12sp",size_hint_y=None,height=dp(50))
        self.body.add_widget(spin)
        self._button("ثبت اتصال دبیر",lambda *_:self._save_teacher(cid,spin),SUCCESS)
        self._label("یا ثبت دستی نام دبیر", "14sp", PRIMARY, 38, True)
        manual_name=self._field("نام و نام خانوادگی دبیر")
        manual_code=self._field("کد ملی (اختیاری)")
        self._button("ثبت دستی و اتصال دبیر",lambda *_:self._save_manual_member(cid,manual_name,manual_code,"teacher"),SUCCESS)
        self._button("ورود Excel دبیران",lambda *_:self._import_member_excel(cid,"teacher"),PRIMARY)
        self._label("قالب Excel: id یا نام و نام خانوادگی یا کد ملی", "11sp", SECONDARY, 42)
        self._button("بازگشت",lambda *_:self.show_home(),SECONDARY)

    def _save_teacher(self,cid,spin):
        try:
            tid=self._teacher_spin_map.get(str(spin.text))
            if tid is None:
                return self._error("دبیر انتخاب‌شده معتبر نیست.")
            row=next((x for x in self._teacher_rows if int(x.get("id"))==int(tid)),None)
            if not row: return self._error("دبیر انتخاب‌شده پیدا نشد.")
            existing=self.app_state.api.table_select("online_class_teachers",{"class_id":"eq."+str(cid),"teacher_id":"eq."+str(tid),"limit":"1"}) or []
            if not existing:
                name=(str(row.get("first_name") or "")+" "+str(row.get("last_name") or "")).strip()
                self.app_state.api.table_insert("online_class_teachers",{"class_id":cid,"teacher_id":tid,"teacher_name":name})
            self._ok("دبیر به کلاس متصل شد."); self._members(cid)
        except Exception as exc:self._error("اتصال دبیر انجام نشد: "+str(exc))
    def _members(self,cid):
        self._clear()
        self._label("اعضای کلاس #"+str(cid),"21sp",PRIMARY,50,True)
        try:
            teachers=self.app_state.api.table_select("online_class_teachers",{"class_id":f"eq.{cid}","limit":"100"}) or []
            students=self.app_state.api.table_select("online_class_students",{"class_id":f"eq.{cid}","limit":"200"}) or []
        except Exception as exc:
            return self._error("خواندن اعضای کلاس انجام نشد: "+str(exc))
        self._label("دبیران متصل","15sp",SUCCESS,35,True)
        if not teachers:self._label("هنوز دبیری متصل نشده است.",38)
        for row in teachers:
            self._label(str(row.get("teacher_id"))+" | "+str(row.get("teacher_name") or "-"),"10sp",SECONDARY,40,True)
            self._button("حذف اتصال دبیر",lambda *_a,r=dict(row):self._delete_member("online_class_teachers",r),ERROR,38)
        self._label("دانش‌آموزان متصل","15sp",SUCCESS,35,True)
        if not students:self._label("هنوز دانش‌آموزی متصل نشده است.",38)
        for row in students:
            self._label(str(row.get("student_id"))+" | "+str(row.get("student_name") or "-"),"10sp",SECONDARY,40,True)
            self._button("حذف اتصال دانش‌آموز",lambda *_a,r=dict(row):self._delete_member("online_class_students",r),ERROR,38)
        self._button("＋ اتصال دانش‌آموز",lambda *_:self._add_student(cid),SUCCESS,42)
        self._button("＋ اتصال دبیر",lambda *_:self._add_teacher(cid),SUCCESS,42)
        self._button("بازگشت به کلاس‌ها",lambda *_:self.show_home(),SECONDARY,42)

    def _delete_member(self,table,row):
        try:
            row_id = row.get("id")
            if row_id is None:
                return self._error("شناسه اتصال کلاس پیدا نشد.")
            filters = {"id": "eq." + str(row_id)}
            self.app_state.api.table_delete(table, filters)
            self._members(row.get("class_id"))
        except Exception as exc:
            self._error("حذف اتصال انجام نشد: "+str(exc))
    def _start(self,cid):
        try:
            now=datetime.now(timezone.utc).isoformat()
            self.app_state.api.table_insert("online_class_sessions",{
                "class_id":cid,"started_at":now,"ended_at":None,"created_at":now
            })
            self.app_state.api.table_update("online_classes",{
                "id":f"eq.{cid}"
            },{
                "status":"active","activated_at":now
            })
            rows=self.app_state.api.table_select(
                "online_classes",{"id":f"eq.{cid}","limit":"1"}
            ) or []
            row=rows[0] if rows else {}
            url=str(row.get("join_url") or row.get("meeting_url") or "").strip()
            if not url:
                url=f"frahoosh://online-class/{cid}"
            profile=getattr(self.app_state,"profile",{}) or {}
            role=role_of(self.app_state)
            # Starting a session is the single entry point to the complete
            # classroom. The WebView contains board, participants, chat,
            # microphone, camera and screen sharing; do not open those as
            # separate Kivy screens.
            if self._open_virtual_classroom(url,cid,profile,role):
                return
            self._error("جلسه در سامانه فعال شد، اما اتاق کامل کلاس روی دستگاه باز نشد.")
        except Exception as exc:
            self._error("شروع جلسه انجام نشد: "+str(exc))
    def _end(self,cid):
        try:
            rows=self.app_state.api.table_select("online_class_sessions",{"class_id":f"eq.{cid}","order":"id.desc","limit":"1"});
            if rows:self.app_state.api.table_update("online_class_sessions",{"id":f"eq.{rows[0]['id']}"},{"ended_at":datetime.now(timezone.utc).isoformat()})
            self.app_state.api.table_update("online_classes",{"id":f"eq.{cid}"},{"status":"ended"}); self._ok("جلسه پایان یافت و زمان پایان ثبت شد."); self.show_home()
        except Exception as exc:self._error("پایان جلسه انجام نشد: "+str(exc))
    def _attendance(self,cid):
        self._clear(); self._label(f"حضور و غیاب جلسه #{cid}","21sp",PRIMARY,50,True)
        try:members=self.app_state.api.table_select("online_class_students",{"class_id":f"eq.{cid}","limit":"100"})
        except Exception as exc:return self._error(str(exc))
        if not members:self._label("دانش‌آموزان کلاس را می‌توان از جدول online_class_students به جلسه متصل کرد.",height=70)
        for m in members:
            sid=m.get("student_id"); name=m.get("student_name") or str(sid); self._button(f"{name} — حاضر",lambda *_ ,s=sid:self._mark(s,cid,"present"),SUCCESS,42); self._button(f"{name} — غایب",lambda *_ ,s=sid:self._mark(s,cid,"absent"),ERROR,42)
        self._button("بازگشت به کلاس‌ها",lambda *_:self.show_home())
    def _mark(self,sid,cid,status):
        try:self.app_state.api.table_insert("attendance",{"student_id":sid,"class_name":f"online:{cid}","subject":"کلاس آنلاین","attendance_date":datetime.now(timezone.utc).isoformat(),"status":status}); self._ok("حضور و غیاب ثبت شد.")
        except Exception as exc:self._error(str(exc))
    def _chat(self,cid):
        self._clear(); self._label(f"گفت‌وگوی کلاس #{cid}","21sp",PRIMARY,50,True)
        try:rows=self.app_state.api.table_select("messages",{"order":"id.desc","limit":"50"})
        except Exception:rows=[]
        for r in rows:
            if str(r.get("title") or "").startswith(f"کلاس #{cid}"):self._label(f"{r.get('sender_name','کاربر')}\n{r.get('body') or ''}",height=70)
        text=self._field("پیام کلاس",80,True); self._button("ارسال پیام",lambda *_:self._send_chat(cid,text),SUCCESS); self._button("بازگشت",lambda *_:self.show_home())
    def _send_chat(self,cid,text):
        if not text.text.strip():return self._error("متن پیام را وارد کنید.")
        try:self.app_state.api.table_insert("messages",{"sender_name":"کاربر فراهوش","title":f"کلاس #{cid} — گفت‌وگو","body":text.text.strip(),"audience_type":"online_class","audience_value":str(cid)}); self._ok("پیام ثبت شد."); self._chat(cid)
        except Exception as exc:self._error(str(exc))
    def _board(self,cid):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Line, Ellipse, Rectangle
        self._clear()
        self._label(f"تخته هوشمند مشترک کلاس #{cid}","21sp",PRIMARY,50,True)
        toolbar=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        for name,tool in (("قلم","pen"),("پاک‌کن","eraser"),("خط","line"),("مستطیل","rect"),("دایره","ellipse")):
            b=Button(text=fa_display(name),font_name=font_name(),font_size="11sp",background_normal="",background_color=PRIMARY if tool=="pen" else SECONDARY,color=WHITE)
            b.bind(on_release=lambda *_t,t=tool:self._set_board_tool(t))
            toolbar.add_widget(b)
        self.body.add_widget(toolbar)
        pages=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(5))
        self._board_page_label=Label(text=fa_display("صفحه 1"),font_name=font_name(),font_size="12sp",color=PRIMARY)
        pages.add_widget(self._board_page_label)
        for title,delta in (("صفحه قبلی",-1),("صفحه بعدی",1)):
            b=Button(text=fa_display(title),font_name=font_name(),font_size="11sp",background_normal="",background_color=SECONDARY,color=WHITE,size_hint_x=None,width=dp(105))
            b.bind(on_release=lambda *_ ,d=delta:self._change_board_page(cid,d))
            pages.add_widget(b)
        clear=Button(text=fa_display("پاک‌کردن صفحه"),font_name=font_name(),font_size="11sp",background_normal="",background_color=ERROR,color=WHITE,size_hint_x=None,width=dp(110))
        clear.bind(on_release=lambda *_:self._clear_board_page(cid))
        pages.add_widget(clear); self.body.add_widget(pages)
        board=Widget(size_hint_y=None,height=dp(390))
        with board.canvas.before:
            Color(0.98,0.98,0.98,1); board._bg=Rectangle(pos=board.pos,size=board.size)
        board.bind(pos=lambda o,v:setattr(board._bg,"pos",v),size=lambda o,v:setattr(board._bg,"size",v))
        self._board_widget=board; self._board_class_id=int(cid); self._board_page=int(getattr(self,"_board_page",1) or 1); self._board_tool="pen"; self._board_start=None
        board.bind(on_touch_down=lambda w,t:self._board_touch_down(w,t),on_touch_move=lambda w,t:self._board_touch_move(w,t),on_touch_up=lambda w,t:self._board_touch_up(w,t))
        self.body.add_widget(board)
        self._load_board_page(cid)
        self._label("تخته برای دبیر و دانش‌آموز مشترک است؛ هر خط/شکل در Supabase ذخیره می‌شود و با بازکردن صفحه دوباره قابل مشاهده است.",height=62)
        self._button("بازخوانی تخته",lambda *_:self._board(cid),PRIMARY)
        self._button("بازگشت",lambda *_:self.show_home(),SECONDARY)

    def _set_board_tool(self,tool):
        self._board_tool=str(tool or "pen")

    def _change_board_page(self,cid,delta):
        self._board_page=max(1,int(getattr(self,"_board_page",1))+int(delta))
        self._board(cid)

    def _load_board_page(self,cid):
        try:
            rows=self.app_state.api.table_select("smart_board_whiteboards",{"class_id":f"eq.{cid}","page_no":f"eq.{int(self._board_page)}","order":"id.asc","limit":"500"}) or []
            for row in rows:
                payload=str(row.get("payload") or "")
                if not payload: continue
                import json
                data=json.loads(payload)
                self._draw_saved(data)
        except Exception as exc:
            self._error("خواندن تخته انجام نشد: "+str(exc))

    def _draw_saved(self,data):
        from kivy.graphics import Color, Line, Ellipse, Rectangle
        b=self._board_widget; tool=str(data.get("tool") or "pen"); pts=data.get("points") or []
        if tool in ("pen","eraser","line") and len(pts)>=4:
            with b.canvas:
                Color(0.98,0.98,0.98,1) if tool=="eraser" else Color(0.05,0.12,0.25,1)
                Line(points=pts,width=8 if tool=="eraser" else 2.5)
        elif tool=="ellipse" and len(pts)>=4:
            x1,y1,x2,y2=pts[:4]
            with b.canvas: Color(0.05,0.12,0.25,1); Line(ellipse=(min(x1,x2),min(y1,y2),abs(x2-x1),abs(y2-y1)),width=2)
        elif tool=="rect" and len(pts)>=4:
            x1,y1,x2,y2=pts[:4]
            with b.canvas: Color(0.05,0.12,0.25,1); Line(rectangle=(min(x1,x2),min(y1,y2),abs(x2-x1),abs(y2-y1)),width=2)

    def _board_touch_down(self,widget,touch):
        if not widget.collide_point(*touch.pos): return False
        self._board_start=touch.pos; self._board_points=[touch.x,touch.y]; return True

    def _board_touch_move(self,widget,touch):
        if self._board_start is None: return False
        if self._board_tool not in ("pen","eraser"): return True
        self._board_points += [touch.x,touch.y]
        from kivy.graphics import Color, Line
        with widget.canvas:
            Color(0.98,0.98,0.98,1) if self._board_tool=="eraser" else Color(0.05,0.12,0.25,1)
            Line(points=self._board_points,width=8 if self._board_tool=="eraser" else 2.5)
        return True

    def _board_touch_up(self,widget,touch):
        if self._board_start is None: return False
        x1,y1=self._board_start; x2,y2=touch.pos; tool=self._board_tool
        if tool=="line":
            from kivy.graphics import Color, Line
            with widget.canvas: Color(0.05,0.12,0.25,1); Line(points=[x1,y1,x2,y2],width=2.5)
            points=[x1,y1,x2,y2]
        elif tool in ("rect","ellipse"):
            points=[x1,y1,x2,y2]; self._draw_saved({"tool":tool,"points":points})
        else: points=list(getattr(self,"_board_points",[x1,y1,x2,y2]))
        self._save_board_payload(self._board_class_id,self._board_page,tool,points)
        self._board_start=None; self._board_points=[]; return True

    def _save_board_payload(self,cid,page,tool,points):
        try:
            import json
            self.app_state.api.table_insert("smart_board_whiteboards",{
                "class_id":int(cid),"page_no":int(page),"tool":str(tool),
                "payload":json.dumps({"tool":tool,"points":points},ensure_ascii=False,separators=(",",":")),
                "shared":True,"title":f"صفحه {page}","content":"","created_at":datetime.now(timezone.utc).isoformat()
            },return_representation=False)
        except Exception as exc: self._error("ذخیره تخته انجام نشد: "+str(exc))

    def _clear_board_page(self,cid):
        try:
            self.app_state.api.table_delete("smart_board_whiteboards",{"class_id":f"eq.{cid}","page_no":f"eq.{int(self._board_page)}"})
            self._board(cid)
        except Exception as exc: self._error("پاک‌کردن صفحه انجام نشد: "+str(exc))

    def _absence_notice(self,cid):
        try:
            members=self.app_state.api.table_select("online_class_students",{"class_id":f"eq.{cid}","limit":"100"})
            sent=0
            for m in members:
                self.app_state.api.table_insert("messages",{"sender_name":"مدیریت مدرسه","title":"اطلاع غیبت کلاس آنلاین","body":f"دانش‌آموز {m.get('student_name') or m.get('student_id')} در جلسه آنلاین #{cid} غایب ثبت شد.","audience_type":"parent","student_id":m.get("student_id")}); sent+=1
            self._ok(f"اطلاع غیبت برای {sent} ولی در صندوق پیام‌ها ثبت شد.")
        except Exception as exc:self._error("ارسال اطلاع غیبت انجام نشد: "+str(exc))
    def _join(self,url,cid=None):
        try:
            profile=getattr(self.app_state,"profile",{}) or {}
            role=role_of(self.app_state)
            student_id=profile.get("linked_student_id") or profile.get("student_id")
            class_id=cid or self.current_id
            if role=="student" and student_id and class_id:
                sessions=self.app_state.api.table_select(
                    "online_class_sessions",
                    {"class_id":f"eq.{class_id}","order":"id.desc","limit":"1"}
                ) or []
                if sessions:
                    session=sessions[0]
                    name=str(profile.get("display_name") or getattr(self.app_state,"display_name","") or "دانش‌آموز")
                    links=self.app_state.api.table_select(
                        "online_class_students",
                        {"class_id":f"eq.{class_id}","student_id":f"eq.{student_id}","limit":"1"}
                    ) or []
                    if not links:
                        self.app_state.api.table_insert(
                            "online_class_students",
                            {"class_id":class_id,"student_id":student_id,"student_name":name}
                        )
                    self._checkpoint_session_id=int(session.get("id"))
                    self._checkpoint_student_id=int(student_id)
                    self._checkpoint_class_id=int(class_id)
                    self._checkpoint_name=name
                    self._record_checkpoint(1)
                    self._schedule_random_checkpoints(class_id)
            if self._open_virtual_classroom(str(url), class_id, profile, role):
                self._ok("کلاس مجازی باز شد؛ حضور شما در سامانه ثبت شد.")
            # _open_virtual_classroom writes the concrete launch error itself.
            # Do not overwrite that diagnostic with the old generic message.
        except Exception as exc:
            self._error("ورود به جلسه انجام نشد: "+str(exc))
    def _record_checkpoint(self, checkpoint_no, status="present"):
        if not self._checkpoint_session_id or not self._checkpoint_student_id or not self._checkpoint_class_id:
            return
        try:
            now=datetime.now(timezone.utc).isoformat()
            self.app_state.api.table_insert("online_attendance", {
                "class_id":self._checkpoint_class_id,"student_id":self._checkpoint_student_id,
                "student_name":self._checkpoint_name,"session_id":self._checkpoint_session_id,
                "checkpoint_no":int(checkpoint_no),"status":status,
                "source":"online_class_checkpoint","event_time":now,"recorded_at":now
            })
        except Exception as exc:
            print("ONLINE ATTENDANCE CHECKPOINT ERROR:",repr(exc))

    def _schedule_random_checkpoints(self, class_id):
        for ev in getattr(self,"_checkpoint_events",[]):
            try: ev.cancel()
            except Exception: pass
        self._checkpoint_events=[]
        try:
            rows=self.app_state.api.table_select("online_classes",{"id":f"eq.{class_id}","limit":"1"}) or []
            duration=int(rows[0].get("duration") or 45) if rows else 45
        except Exception:
            duration=45
        total=max(60,duration*60)
        first=random.uniform(total*0.25,total*0.45)
        second=random.uniform(total*0.60,total*0.82)
        if second <= first+30: second=min(total-10,first+60)
        self._checkpoint_events.append(Clock.schedule_once(lambda dt:self._checkpoint_prompt(2),first))
        self._checkpoint_events.append(Clock.schedule_once(lambda dt:self._checkpoint_prompt(3),second))

    def _checkpoint_prompt(self, checkpoint_no):
        if not self._checkpoint_session_id:
            return
        box=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(10))
        label=Label(text=fa_display("برای تأیید ادامه حضور در کلاس، حداکثر ۵ ثانیه فرصت دارید."),font_name=font_name(),halign="center",valign="middle")
        label.bind(size=lambda o,v:setattr(o,"text_size",v)); box.add_widget(label)
        button=Button(text=fa_display("تأیید حضور — ۵"),font_name=font_name(),size_hint_y=None,height=dp(50))
        box.add_widget(button)
        popup=Popup(title=fa_display("صحت‌سنجی حضور در کلاس"),content=box,size_hint=(.86,.34),auto_dismiss=False)
        state={"left":5,"done":False}
        def confirm(*_):
            if state["done"]: return
            state["done"]=True
            try: countdown.cancel()
            except Exception: pass
            popup.dismiss()
            self._record_checkpoint(checkpoint_no)
            self._ok("حضور شما برای ادامه کلاس تأیید شد.")
        def tick(dt):
            if state["done"]: return False
            state["left"]-=1
            if state["left"]<=0:
                state["done"]=True
                popup.dismiss()
                self._record_checkpoint(checkpoint_no,"absent_timeout")
                self._notify_parent_absence("عدم تأیید صحت‌سنجی حضور",checkpoint_no)
                self._close_virtual_classroom("عدم تأیید حضور در مهلت ۵ ثانیه")
                return False
            button.text=fa_display("تأیید حضور — "+str(state["left"]))
            return True
        button.bind(on_release=confirm)
        popup.open()
        countdown=Clock.schedule_interval(tick,1)

    def _notify_parent_absence(self, reason, checkpoint_no):
        try:
            sid=self._checkpoint_student_id
            rows=self.app_state.api.table_select("students",{"id":f"eq.{sid}","limit":"1"}) or []
            student=rows[0] if rows else {}
            student_name=(str(student.get("first_name") or "")+" "+str(student.get("last_name") or "")).strip() or self._checkpoint_name
            body=(f"دانش‌آموز {student_name} در کلاس آنلاین #{self._checkpoint_class_id} "
                  f"در صحت‌سنجی شماره {checkpoint_no} حضور را در مهلت ۵ ثانیه تأیید نکرد و از کلاس خارج شد.")
            self.app_state.api.table_insert("messages",{
                "sender":"مدیریت مدرسه","sender_name":"مدیریت مدرسه",
                "title":"هشدار حضور و غیاب کلاس آنلاین","body":body,"text":body,
                "audience_type":"parent","target_role":"parent","target_name":student_name,
                "audience_value":str(sid),"student_id":sid,"created_at":datetime.now(timezone.utc).isoformat()
            })
        except Exception as exc:
            print("PARENT ABSENCE MESSAGE ERROR:",repr(exc))

    def _close_virtual_classroom(self, reason=""):
        for ev in getattr(self,"_checkpoint_events",[]):
            try: ev.cancel()
            except Exception: pass
        self._checkpoint_events=[]
        container=getattr(self,"_active_webview_container",None)
        if container is not None:
            try:
                parent=container.getParent()
                if parent is not None: parent.removeView(container)
            except Exception as exc: print("VIRTUAL CLASSROOM CLOSE ERROR:",repr(exc))
        self._active_webview=None
        self._active_webview_container=None
        self._checkpoint_session_id=None
        self._error(reason or "کلاس بسته شد.")

    def _open_virtual_classroom(self, url, class_id, profile, role):
        """Open the complete Frahoosh classroom locally inside the Android app."""
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread
            from pathlib import Path
            import json
            import os
            PythonActivity=autoclass("org.kivy.android.PythonActivity")
            WebView=autoclass("android.webkit.WebView")
            WebViewClient=autoclass("android.webkit.WebViewClient")
            LayoutParams=autoclass("android.view.ViewGroup$LayoutParams")
            FrameLayout=autoclass("android.widget.FrameLayout")
            Button=autoclass("android.widget.Button")
            Color=autoclass("android.graphics.Color")
            activity=PythonActivity.mActivity
            web=WebView(activity)
            settings=web.getSettings()
            settings.setJavaScriptEnabled(True); settings.setDomStorageEnabled(True)
            settings.setMediaPlaybackRequiresUserGesture(False); settings.setAllowFileAccess(True); settings.setAllowContentAccess(True)
            web.setWebViewClient(WebViewClient())
            # The custom ChromeClient is required for WebRTC media permissions.
            # Keep a plain WebChromeClient fallback so a missing/old Java helper
            # cannot prevent the classroom WebView itself from opening.
            try:
                FrahooshWebChromeClient=autoclass("ir.frahoosh.FrahooshWebChromeClient")
                web.setWebChromeClient(FrahooshWebChromeClient())
            except Exception as exc:
                print("FRAHOOSH WEB CHROME CLIENT FALLBACK:",repr(exc))
                WebChromeClient=autoclass("android.webkit.WebChromeClient")
                web.setWebChromeClient(WebChromeClient())
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.CAMERA, Permission.RECORD_AUDIO])
            except Exception as exc: print("ANDROID MEDIA PERMISSION REQUEST ERROR:",repr(exc))
            candidates=[Path(__file__).resolve().parents[1] / "assets" / "online_class.html", Path(__file__).resolve().parent / "assets" / "online_class.html", Path(os.environ.get("ANDROID_PRIVATE","")) / "assets" / "online_class.html", Path(os.environ.get("ANDROID_APP_PATH","")) / "assets" / "online_class.html"]
            html_path=next((p for p in candidates if str(p) and p.is_file()), None)
            if html_path is None: raise FileNotFoundError("online_class.html not found; checked: "+", ".join(str(p) for p in candidates))
            html=html_path.read_text(encoding="utf-8")
            user=getattr(self.app_state,"user",{}) or {}
            user_id=str(user.get("id") or profile.get("user_id") or profile.get("id") or "")
            token=str(getattr(getattr(self.app_state,"api",None),"access_token","") or "")
            from mobile.config import SUPABASE_URL,SUPABASE_ANON_KEY
            name=str(profile.get("display_name") or getattr(self.app_state,"display_name","") or "کاربر فراهوش")
            cfg=json.dumps({"url":SUPABASE_URL,"anon":SUPABASE_ANON_KEY,"token":token,"userId":user_id,"classId":int(class_id),"name":name},ensure_ascii=False,separators=(",",":"))
            html=html.replace("__CONFIG__",cfg)
            container=FrameLayout(activity); container.setBackgroundColor(Color.BLACK)
            container.addView(web,LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.MATCH_PARENT))
            back=Button(activity); back.setText("بازگشت به فراهوش")
            params=FrameLayout.LayoutParams(LayoutParams.WRAP_CONTENT,LayoutParams.WRAP_CONTENT); params.topMargin=20; params.leftMargin=18
            container.addView(back,params)
            @run_on_ui_thread
            def close(*_):
                try:
                    parent=container.getParent()
                    if parent is not None: parent.removeView(container)
                    web.destroy()
                except Exception as exc: print("VIRTUAL CLASSROOM CLOSE ERROR:",repr(exc))
            back.setOnClickListener(lambda *_:close())
            @run_on_ui_thread
            def attach():
                activity.addContentView(container,LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.MATCH_PARENT))
                web.loadDataWithBaseURL("https://frahoosh.ir/online-class/",html,"text/html","UTF-8",None)
            attach()
            self._active_webview=web
            self._active_webview_container=container
            return True
        except Exception as exc:
            import traceback
            detail=f"{type(exc).__name__}: {exc}"
            print("FRAHOOSH INTERNAL CLASSROOM ERROR:",detail)
            print(traceback.format_exc())
            try: self._error("اتاق داخلی باز نشد\n"+detail)
            except Exception: pass
            return False

    def _toggle_mic(self):self.mic=not self.mic; self.show_home()
    def _toggle_camera(self):self.camera=not self.camera; self.show_home()
    def _ok(self,text):self.status.color=SUCCESS;self.status.text=fa_display(text)
    def _error(self,text):
        self.status.color=ERROR
        value=str(text or "")
        # Exception diagnostics contain paths, Java/Python class names and
        # punctuation. Do not pass them through Arabic reshaping: some
        # Android text providers render those shaped forms as square glyphs.
        diagnostic_tokens=("Error:","Exception:","FileNotFoundError:","ImportError:","JavaException:","AttributeError:","TypeError:","RuntimeError:")
        self.status.text=value if any(token in value for token in diagnostic_tokens) else fa_display(value)
    def _back(self):
        if self.manager:
            self.manager.current="dashboard"
