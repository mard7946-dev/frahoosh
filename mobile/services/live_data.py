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
        "parent_children",
        "discipline_records",
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

    def parent_student_ids(self):
        """Resolve all children linked to the logged-in parent from the canonical link table."""
        if str(getattr(self.app_state, "role", "")).lower() != "parent":
            return []
        p = self.profile
        u = self.user
        candidates = []
        for key in ("parent_id", "id", "user_id"):
            value = p.get(key) or u.get(key)
            if value: candidates.append((key, str(value)))
        if u.get("id"): candidates.append(("parent_user_id", str(u["id"])))
        if p.get("email") or u.get("email"):
            candidates.append(("email", str(p.get("email") or u.get("email"))))
        seen=set(); result=[]
        for field,value in candidates:
            try:
                _, rows=self._try_select(("parent_children",), {"select":"*", field:f"eq.{value}", "limit":"100"})
                for row in rows:
                    sid=self._first(row,"student_id","child_id","linked_student_id","student")
                    if sid and str(sid) not in seen:
                        seen.add(str(sid)); result.append(str(sid))
            except Exception:
                continue
        linked=self._first(p,"linked_student_id","student_id")
        if linked and str(linked) not in seen:
            result.append(str(linked))
        return result

    def _child_events(self, table, student_ids, limit=50):
        if not student_ids: return []
        rows=[]
        for sid in student_ids:
            try:
                _, data=self._try_select((table,), {"select":"*","student_id":f"eq.{sid}","order":"created_at.desc","limit":str(limit)})
                rows.extend(data)
            except Exception:
                continue
        return rows

    def parent_realtime_feed(self, limit=50):
        """Return the four parent-critical feeds from the same school tables."""
        student_ids=self.parent_student_ids()
        attendance=self._child_events("attendance",student_ids,limit)
        discipline=self._child_events("discipline_records",student_ids,limit)
        grades=self._child_events("grades",student_ids,limit)
        assignments=self._child_events("assignments",student_ids,limit)
        messages=[]
        p=self.profile; u=self.user
        for field,value in (("recipient_id",u.get("id")),("user_id",u.get("id")),("parent_id",p.get("id") or u.get("id")),("email",p.get("email") or u.get("email"))):
            if not value: continue
            try:
                _, data=self._try_select(("messages",), {"select":"*",field:f"eq.{value}","order":"created_at.desc","limit":str(limit)})
                messages.extend(data)
            except Exception:
                continue
        # RLS-safe fallback: message_targets normally carries recipient routing.
        for field,value in (("parent_id",p.get("id") or u.get("id")),("user_id",u.get("id")),("recipient_id",u.get("id"))):
            if not value: continue
            try:
                _, targets=self._try_select(("message_targets",), {"select":"*",field:f"eq.{value}","order":"created_at.desc","limit":str(limit)})
                ids=[self._first(x,"message_id","id") for x in targets]
                for mid in ids:
                    if mid:
                        _, data=self._try_select(("messages",), {"select":"*","id":f"eq.{mid}","limit":"1"})
                        messages.extend(data)
            except Exception:
                continue
        def unique_sorted(items):
            seen=set(); out=[]
            for row in items:
                key=str(self._first(row,"id","uuid","created_at"))+"|"+str(self._first(row,"title","subject","type"))
                if key not in seen: seen.add(key); out.append(row)
            return sorted(out,key=lambda x:str(x.get("created_at") or x.get("date") or ""),reverse=True)[:limit]
        return {"student_ids":student_ids,"attendance":unique_sorted(attendance),"discipline":unique_sorted(discipline),"grades":unique_sorted(grades),"activities":unique_sorted(assignments),"messages":unique_sorted(messages)}

    def parent_unread_notifications(self, seen_ids=None):
        feed=self.parent_realtime_feed(limit=30)
        seen=set(str(x) for x in (seen_ids or [])); events=[]
        mapping=(("attendance","حضور و غیاب"),("discipline","گزارش انضباطی"),("grades","نمره جدید"),("activities","فعالیت آموزشی"),("messages","پیام جدید"))
        for key,title in mapping:
            for row in feed.get(key,[]):
                rid=self._first(row,"id","uuid",default=self._first(row,"created_at","date"))
                if str(rid) not in seen:
                    events.append({"id":str(rid),"title":title,"row":row,"created_at":self._first(row,"created_at","date")})
        return sorted(events,key=lambda x:str(x.get("created_at") or ""),reverse=True), feed

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
