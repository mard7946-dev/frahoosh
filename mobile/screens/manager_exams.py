from kivy.metrics import dp
from mobile.screens.teacher_exams_v4 import TeacherExamsV4Screen
from mobile.ui import rtl_text
from mobile.config import PRIMARY, SUCCESS


class ManagerExamsScreen(TeacherExamsV4Screen):
    """Manager-facing entry to the same real exam engine used by teachers."""
    def show_home(self):
        self._clear(); self.title.text=rtl_text("مرکز آزمون آنلاین")
        self._label("مرکز طراحی و مدیریت آزمون", "22sp", PRIMARY, 54, True)
        self._label("ساخت آزمون با پنج نوع سؤال، تصحیح خودکار سؤال‌های غیرتشریحی، زمان‌بندی جداگانه برای هر کلاس و ساخت لینک اشتراک امن.", height=82)
        self._button("＋ ساخت آزمون جدید", lambda *_: self._new_exam(), SUCCESS)
        self._button("آزمون‌های ثبت‌شده و زمان‌بندی‌ها", lambda *_: self._load_exams())

    def _teacher_id(self):
        p=getattr(self.app_state,"profile",{}) or {}
        try:
            if p.get("linked_teacher_id"): return int(p["linked_teacher_id"])
        except Exception: pass
        try:
            rows=self.app_state.api.table_select("teachers", {"limit":"1"})
            return int(rows[0]["id"]) if rows else None
        except Exception:
            return None
