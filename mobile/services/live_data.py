from mobile.services.api import ApiError


class LiveSchoolData:
    """Read-only live data bridge for the mobile panels.

    It deliberately reads the canonical Frahoosh v16 school tables instead of
    inventing mobile-only tables. Write workflows are added only where the
    server schema/RLS is known and verified.
    """

    TABLES = (
        "messages",
        "message_targets",
        "message_reads",
        "students",
        "parents",
        "teachers",
        "staff",
        "attendance",
        "grades",
        "assignments",
        "online_classes",
        "online_class_sessions",
        "online_presence_checks",
        "online_class_activity",
        "online_class_notifications",
        "online_class_students",
        "online_class_teachers",
        "online_class_chat",
        "online_class_board_events",
        "online_class_settings",
        "school_events",
        "event_audiences",
    )

    def __init__(self, app_state):
        self.app_state = app_state

    @property
    def api(self):
        return getattr(self.app_state, "api", None)

    @property
    def profile(self):
        value = getattr(self.app_state, "profile", {})
        return value if isinstance(value, dict) else {}

    @property
    def user(self):
        value = getattr(self.app_state, "user", {})
        return value if isinstance(value, dict) else {}

    def _select(self, table, params=None):
        if self.api is None:
            raise ApiError("سرویس اتصال به مدرسه آماده نیست.")
        return self.api.table_select(table, params or {})

    def _try_select(self, tables, params=None):
        last = None
        for table in tables:
            try:
                rows = self._select(table, params)
                return table, rows if isinstance(rows, list) else []
            except Exception as exc:
                last = exc
        if last:
            raise last
        return None, []

    @staticmethod
    def _first(row, *keys, default=""):
        if not isinstance(row, dict):
            return default
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                return value
        return default

    def connection_state(self):
        if self.api is None:
            return False, "سرویس اتصال ساخته نشده است."
        if not getattr(self.api, "configured", False):
            return False, "تنظیمات Supabase در برنامه وجود ندارد."
        if not getattr(self.api, "access_token", ""):
            return False, "نشست کاربر معتبر نیست."
        if self.api.access_token == "local-bootstrap-admin":
            return False, "ورود مدیریتی اولیه فعال است؛ برای داده واقعی باید حساب Supabase استفاده شود."
        return True, "اتصال واقعی سامانه فعال است."

    def inbox(self, limit=50):
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(limit),
        }
        _, messages = self._try_select(("messages",), params)
        return messages

    def current_student(self):
        national = str(self._first(self.profile, "national_code", "national_id", "username"))
        linked = self._first(self.profile, "linked_student_id", "student_id")
        filters = []
        if linked:
            filters.append({"id": f"eq.{linked}", "limit": "1"})
        if national:
            filters.extend([
                {"national_code": f"eq.{national}", "limit": "1"},
                {"national_id": f"eq.{national}", "limit": "1"},
                {"student_code": f"eq.{national}", "limit": "1"},
            ])
        for params in filters:
            try:
                _, rows = self._try_select(("students",), {"select": "*", **params})
                if rows:
                    return rows[0]
            except Exception:
                continue
        return {}

    def student_summary(self):
        student = self.current_student()
        student_id = self._first(student, "id", "student_id")
        if not student_id:
            return {"student": student, "attendance": [], "grades": [], "assignments": []}

        def by_student(table):
            try:
                _, rows = self._try_select(
                    (table,),
                    {
                        "select": "*",
                        "student_id": f"eq.{student_id}",
                        "order": "created_at.desc",
                        "limit": "30",
                    },
                )
                return rows
            except Exception:
                return []

        return {
            "student": student,
            "attendance": by_student("attendance"),
            "grades": by_student("grades"),
            "assignments": by_student("assignments"),
        }

    def online_classes(self, limit=30):
        _, rows = self._try_select(
            ("online_classes", "classes"),
            {
                "select": "*",
                "order": "created_at.desc",
                "limit": str(limit),
            },
        )
        return rows

    def online_sessions(self, class_id=None, limit=30):
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(limit),
        }
        if class_id:
            params["class_id"] = f"eq.{class_id}"
        _, rows = self._try_select(("online_class_sessions",), params)
        return rows

    def online_presence(self, session_id=None, student_id=None, limit=30):
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(limit),
        }
        if session_id:
            params["session_id"] = f"eq.{session_id}"
        if student_id:
            params["student_id"] = f"eq.{student_id}"
        _, rows = self._try_select(("online_presence_checks",), params)
        return rows

    def online_activity(self, session_id=None, limit=50):
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(limit),
        }
        if session_id:
            params["session_id"] = f"eq.{session_id}"
        _, rows = self._try_select(("online_class_activity",), params)
        return rows

    def dashboard_counts(self):
        result = {}
        for key, table in (
            ("دانش‌آموزان", "students"),
            ("دبیران", "teachers"),
            ("پیام‌ها", "messages"),
            ("کلاس‌های آنلاین", "online_classes"),
        ):
            try:
                _, rows = self._try_select((table,), {"select": "id", "limit": "500"})
                result[key] = len(rows)
            except Exception:
                result[key] = None
        return result
