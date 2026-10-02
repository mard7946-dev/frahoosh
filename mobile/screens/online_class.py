from datetime import datetime, timezone
import webbrowser

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


def _is_legacy_management_account(state, profile):
    """Compatibility bridge for the existing production manager account.
    Its database row was historically stored with role=student and must not
    hide management-only workflows until the server-side role is corrected.
    """
    username = str((profile or {}).get("username") or "").strip().lower()
    email = str((profile or {}).get("email") or "").strip().lower()
    local = email.split("@", 1)[0] if "@" in email else ""
    return username in {"student", "student1"} or local in {"student", "student1"}

def role_of(state):
    # Login may keep the canonical role in profile while app_state.role is empty.
    # Resolve both sources so operational create/manage controls are not hidden.
    # A live workflow can be opened from a specific school panel. Prefer that active panel role over a stale profile role.
    profile = getattr(state, "profile", {}) or {}
    active_panel = "" if _is_legacy_management_account(state, profile) else str(getattr(state, "panel_role", "") or "").strip().lower()
    if active_panel:
        normalized_panel = {"management":"manager","teachers":"teacher","teacher_panel":"teacher","teacher_dashboard":"teacher","دبیران":"teacher","کادر و دبیران":"teacher"}.get(active_panel, active_panel)
        if normalized_panel in {"manager","educational","executive","cultural","advisor","teacher","staff","student","parent"}:
            return normalized_panel
    profile = getattr(state, "profile", {}) or {}
    if _is_legacy_management_account(state, profile):
        return "manager"
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
        super().__init__(**kwargs); self.app_state=app_state; self.current_id=None; self.selected_class=None; self.mic=True; self.camera=True; self._build()
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
        # The class is selected from the real teacher_classes relationship.
        # A teacher name alone is not enough to bind the correct students.
        try:
            teacher_rows=self.app_state.api.table_select("teachers",{"order":"first_name.asc","limit":"500"}) or []
        except Exception as exc:
            self._error("فهرست دبیران بارگذاری نشد: "+str(exc))
            return
        if not teacher_rows:
            self._error("هیچ دبیری در سامانه ثبت نشده است.")
            return

        self._create_teacher_rows=teacher_rows
        self._create_teacher_map={}
        labels=[]
        for row in teacher_rows:
            label=" ".join(str(row.get("first_name") or "").strip().split()+str(row.get("last_name") or "").strip().split()).strip()
            if not label:
                label=str(row.get("email") or "").strip()
            if label and row.get("id") is not None:
                display=fa_display(label)
                self._create_teacher_map[display]=int(row["id"])
                labels.append(display)

        teacher=PersianSpinner(text=labels[0],values=tuple(labels),size_hint_y=None,height=dp(50),font_size="13sp")
        self.body.add_widget(teacher)

        class_box=PersianSpinner(text="ابتدا دبیر را انتخاب کنید",values=("ابتدا دبیر را انتخاب کنید",),size_hint_y=None,height=dp(50),font_size="13sp")
        self.body.add_widget(class_box)

        subject=self._field("نام درس")
        start=self._field("زمان شروع")
        end=self._field("زمان پایان")

        def refresh_classes(*_):
            tid=self._create_teacher_map.get(str(teacher.text).strip())
            try:
                rel=self.app_state.api.table_select("teacher_classes",{
                    "teacher_id":"eq."+str(int(tid)),
                    "active":"eq.1",
                    "order":"grade.asc,class_name.asc",
                    "limit":"200"
                }) if tid else []
            except Exception as exc:
                return self._error("کلاس‌های دبیر بارگذاری نشد: "+str(exc))
            self._create_class_rows=rel or []
            values=[]
            self._create_class_map={}
            for row in self._create_class_rows:
                grade=str(row.get("grade") or "").strip()
                cname=str(row.get("class_name") or "").strip()
                if not cname: continue
                label=fa_display((grade+" — " if grade else "")+cname)
                self._create_class_map[label]=(grade,cname)
                values.append(label)
            if not values:
                values=["برای این دبیر کلاس واقعی ثبت نشده است"]
            class_box.values=tuple(values)
            class_box.text=values[0]

        teacher.bind(text=refresh_classes)
        refresh_classes()

        self._button("＋ تشکیل کلاس",lambda *_:self._create(teacher,class_box,subject,start,end),SUCCESS)

    def _create(self,teacher,class_box,subject,start,end):
    def _create(self,teacher,subject,start,end):
        api=getattr(self.app_state,"api",None)
        if api is None:
            return self._error("سرویس اتصال به پایگاه داده آماده نیست.")
        role=role_of(self.app_state)
        if role not in CLASS_CREATORS:
            return self._error("فقط مدیر، معاون اجرایی و معاون آموزشی اجازه تشکیل کلاس آنلاین دارند.")
        if not getattr(api,"access_token",""):
            return self._error("نشست ورود معتبر نیست؛ دوباره وارد فراهوش شوید.")

        teacher_label=str(teacher.text or "").strip()
        teacher_id=getattr(self,"_create_teacher_map",{}).get(teacher_label)
        subject_value=(subject.get_logical_text() if hasattr(subject,"get_logical_text") else subject.text or "").strip()
        start_value=(start.get_logical_text() if hasattr(start,"get_logical_text") else start.text or "").strip()
        end_value=(end.get_logical_text() if hasattr(end,"get_logical_text") else end.text or "").strip()

        if not teacher_id:
            return self._error("دبیر انتخاب‌شده معتبر نیست.")
        if not subject_value:
            return self._error("نام درس را وارد کنید.")
        if not start_value or not end_value:
            return self._error("زمان شروع و پایان را وارد کنید.")

        try:
            import secrets
            teacher_rows=api.table_select("teachers",{"id":"eq."+str(int(teacher_id)),"limit":"1"}) or []
            if not teacher_rows:
                return self._error("دبیر انتخاب‌شده در سامانه پیدا نشد.")
            teacher_row=teacher_rows[0]
            teacher_name=" ".join(
                str(teacher_row.get("first_name") or "").strip().split()
                + str(teacher_row.get("last_name") or "").strip().split()
            ).strip()
            safe_key="-".join((subject_value+" "+teacher_name).split()).replace("/","-")
            join_url="https://meet.jit.si/frahoosh-"+safe_key[:40]+"-"+secrets.token_hex(4)

            class_id=int(api.rpc("create_online_class_with_members", {
                "p_teacher_id":int(teacher_id),
                "p_subject":subject_value,
                "p_start_time":start_value,
                "p_end_time":end_value,
                "p_join_url":join_url,
            }))
            self._ok("کلاس ثبت شد؛ دبیر و دانش‌آموزان کلاس مربوطه به‌صورت واقعی متصل شدند. کد کلاس: "+str(class_id))
            self.show_home()
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
                self._button("گفت‌وگوی کلاس",lambda *_ ,x=cid:self._chat(x),PRIMARY)
                self._button("تخته مشترک / نوشتن روی تخته",lambda *_ ,x=cid:self._board(x),PRIMARY)
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
            allowed={"teacher","subject","start_time","end_time","status","join_url","meeting_url"}
            inserted=0
            for values in rows[1:]:
                payload={}
                for i,v in enumerate(values):
                    if i>=len(headers) or headers[i] not in allowed or v in (None,""): continue
                    payload[headers[i]]=v
                if payload.get("title"):
                    try: payload["duration"]=max(1,int(payload.get("duration") or 60))
                    except Exception: payload["duration"]=60
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
        self._button("بازگشت",lambda *_:self.show_home(),SECONDARY)

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
        try:self.app_state.api.table_insert("online_class_sessions",{"class_id":cid,"started_at":datetime.now(timezone.utc).isoformat(),"ended_at":None,"created_at":datetime.now(timezone.utc).isoformat()}); self.app_state.api.table_update("online_classes",{"id":f"eq.{cid}"},{"status":"active","activated_at":datetime.now(timezone.utc).isoformat()}); self._ok("جلسه شروع شد و در سامانه ثبت گردید."); self.show_home()
        except Exception as exc:self._error("شروع جلسه انجام نشد: "+str(exc))
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
        self._clear(); self._label(f"تخته مشترک کلاس #{cid}","21sp",PRIMARY,50,True); self._label("محتوای تخته به صورت واقعی در پایگاه داده ذخیره می‌شود و در بازخوانی جلسه قابل مشاهده است.",height=62)
        try:rows=self.app_state.api.table_select("smart_board_whiteboards",{"class_id":f"eq.{cid}","order":"id.asc","limit":"100"})
        except Exception:rows=[]
        for r in rows:self._label(str(r.get("content") or r.get("text") or ""),height=65)
        text=self._field("متن / یادداشت روی تخته",100,True); self._button("ثبت روی تخته",lambda *_:self._save_board(cid,text),SUCCESS); self._button("بازگشت",lambda *_:self.show_home())
    def _save_board(self,cid,text):
        if not text.text.strip():return self._error("متن تخته خالی است.")
        try:self.app_state.api.table_insert("smart_board_whiteboards",{"class_id":cid,"content":text.text.strip(),"created_at":datetime.now(timezone.utc).isoformat()}); self._ok("محتوای تخته ذخیره شد."); self._board(cid)
        except Exception as exc:self._error(str(exc))
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
                    self.app_state.api.table_insert(
                        "online_attendance",
                        {"class_id":class_id,"student_id":student_id,
                         "student_name":name,"status":"present",
                         "recorded_at":datetime.now(timezone.utc).isoformat()}
                    )
            webbrowser.open(str(url))
            self._ok("جلسه واقعی باز شد و ورود شما در سامانه ثبت شد؛ کنترل دوربین و میکروفون توسط سرویس جلسه انجام می‌شود.")
        except Exception as exc:
            self._error("ورود به جلسه انجام نشد: "+str(exc))
    def _toggle_mic(self):self.mic=not self.mic; self.show_home()
    def _toggle_camera(self):self.camera=not self.camera; self.show_home()
    def _ok(self,text):self.status.color=SUCCESS;self.status.text=fa_display(text)
    def _error(self,text):self.status.color=ERROR;self.status.text=fa_display(text)
    def _back(self):
        if self.manager:self.manager.current="dashboard"    def _create(teacher,class_box,subject,start,end):
        api=getattr(self.app_state,"api",None)
        if api is None:
            return self._error("سرویس اتصال به پایگاه داده آماده نیست.")
        role=role_of(self.app_state)
        if role not in CLASS_CREATORS:
            return self._error("فقط مدیر، معاون اجرایی و معاون آموزشی اجازه تشکیل کلاس آنلاین دارند.")
        if not getattr(api,"access_token",""):
            return self._error("نشست ورود معتبر نیست؛ دوباره وارد فراهوش شوید.")

        teacher_id=self._create_teacher_map.get(str(teacher.text).strip())
        class_info=self._create_class_map.get(str(class_box.text).strip())
        subject_value=(subject.get_logical_text() if hasattr(subject,"get_logical_text") else subject.text or "").strip()
        start_value=(start.get_logical_text() if hasattr(start,"get_logical_text") else start.text or "").strip()
        end_value=(end.get_logical_text() if hasattr(end,"get_logical_text") else end.text or "").strip()
        if not teacher_id: return self._error("دبیر انتخاب‌شده معتبر نیست.")
        if not class_info: return self._error("پایه و کلاس واقعی دبیر را انتخاب کنید.")
        if not subject_value: return self._error("نام درس را وارد کنید.")
        if not start_value or not end_value: return self._error("زمان شروع و پایان را وارد کنید.")
        grade_value,class_value=class_info
        if not class_value or class_value.startswith("برای این دبیر"):
            return self._error("برای این دبیر کلاس واقعی در سامانه ثبت نشده است.")

        try:
            import secrets
            teacher_rows=api.table_select("teachers",{"id":"eq."+str(int(teacher_id)),"limit":"1"}) or []
            if not teacher_rows: return self._error("دبیر انتخاب‌شده در سامانه پیدا نشد.")
            teacher_row=teacher_rows[0]
            teacher_name=" ".join(str(teacher_row.get("first_name") or "").strip().split()+str(teacher_row.get("last_name") or "").strip().split()).strip()
            safe_key="-".join((subject_value+" "+teacher_name+" "+class_value).split()).replace("/","-")
            join_url="https://meet.jit.si/frahoosh-"+safe_key[:40]+"-"+secrets.token_hex(4)
            result=api.rpc("create_online_class_with_members",{
                "p_teacher_id":int(teacher_id),"p_subject":subject_value,
                "p_grade":grade_value,"p_class_name":class_value,
                "p_start_time":start_value,"p_end_time":end_value,"p_join_url":join_url
            })
            class_id=int(result[0] if isinstance(result,list) else result)
            self._ok("کلاس ثبت شد و دبیر و دانش‌آموزان همان کلاس به‌صورت واقعی متصل شدند. کد کلاس: "+str(class_id))
            self.show_home()
        except Exception as exc:
            self._error("ثبت کلاس انجام نشد: "+str(exc))

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
                self._button("گفت‌وگوی کلاس",lambda *_ ,x=cid:self._chat(x),PRIMARY)
                self._button("تخته مشترک / نوشتن روی تخته",lambda *_ ,x=cid:self._board(x),PRIMARY)
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
            allowed={"teacher","subject","start_time","end_time","status","join_url","meeting_url"}
            inserted=0
            for values in rows[1:]:
                payload={}
                for i,v in enumerate(values):
                    if i>=len(headers) or headers[i] not in allowed or v in (None,""): continue
                    payload[headers[i]]=v
                if payload.get("title"):
                    try: payload["duration"]=max(1,int(payload.get("duration") or 60))
                    except Exception: payload["duration"]=60
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
        self._button("بازگشت",lambda *_:self.show_home(),SECONDARY)

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
        try:self.app_state.api.table_insert("online_class_sessions",{"class_id":cid,"started_at":datetime.now(timezone.utc).isoformat(),"ended_at":None,"created_at":datetime.now(timezone.utc).isoformat()}); self.app_state.api.table_update("online_classes",{"id":f"eq.{cid}"},{"status":"active","activated_at":datetime.now(timezone.utc).isoformat()}); self._ok("جلسه شروع شد و در سامانه ثبت گردید."); self.show_home()
        except Exception as exc:self._error("شروع جلسه انجام نشد: "+str(exc))
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
        self._clear(); self._label(f"تخته مشترک کلاس #{cid}","21sp",PRIMARY,50,True); self._label("محتوای تخته به صورت واقعی در پایگاه داده ذخیره می‌شود و در بازخوانی جلسه قابل مشاهده است.",height=62)
        try:rows=self.app_state.api.table_select("smart_board_whiteboards",{"class_id":f"eq.{cid}","order":"id.asc","limit":"100"})
        except Exception:rows=[]
        for r in rows:self._label(str(r.get("content") or r.get("text") or ""),height=65)
        text=self._field("متن / یادداشت روی تخته",100,True); self._button("ثبت روی تخته",lambda *_:self._save_board(cid,text),SUCCESS); self._button("بازگشت",lambda *_:self.show_home())
    def _save_board(self,cid,text):
        if not text.text.strip():return self._error("متن تخته خالی است.")
        try:self.app_state.api.table_insert("smart_board_whiteboards",{"class_id":cid,"content":text.text.strip(),"created_at":datetime.now(timezone.utc).isoformat()}); self._ok("محتوای تخته ذخیره شد."); self._board(cid)
        except Exception as exc:self._error(str(exc))
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
                    self.app_state.api.table_insert(
                        "online_attendance",
                        {"class_id":class_id,"student_id":student_id,
                         "student_name":name,"status":"present",
                         "recorded_at":datetime.now(timezone.utc).isoformat()}
                    )
            webbrowser.open(str(url))
            self._ok("جلسه واقعی باز شد و ورود شما در سامانه ثبت شد؛ کنترل دوربین و میکروفون توسط سرویس جلسه انجام می‌شود.")
        except Exception as exc:
            self._error("ورود به جلسه انجام نشد: "+str(exc))
    def _toggle_mic(self):self.mic=not self.mic; self.show_home()
    def _toggle_camera(self):self.camera=not self.camera; self.show_home()
    def _ok(self,text):self.status.color=SUCCESS;self.status.text=fa_display(text)
    def _error(self,text):self.status.color=ERROR;self.status.text=fa_display(text)
    def _back(self):
        if self.manager:self.manager.current="dashboard"
