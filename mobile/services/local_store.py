import json
import os
import random
import sqlite3
import secrets
import string
from datetime import datetime, timezone


class LocalStore:
    """Small SQLite-backed store used only by the demo/bootstrap account.

    It keeps the APK operational even before a Supabase account is provisioned.
    Real Supabase-authenticated users continue to use the remote database.
    """
    def __init__(self):
        try:
            from kivy.app import App
            app = App.get_running_app()
            base = app.user_data_dir if app else os.path.join(os.path.expanduser("~"), ".frahoosh")
        except Exception:
            base = os.path.join(os.path.expanduser("~"), ".frahoosh")
        os.makedirs(base, exist_ok=True)
        self.path = os.path.join(base, "frahoosh_local.db")
        self._init()

    def _connect(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    @staticmethod
    def _name(table):
        return "t_" + "".join(ch if ch.isalnum() else "_" for ch in str(table))

    def _init(self):
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS __rows (table_name TEXT, row_id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)")
            db.commit()
        self._seed()

    def _seed(self):
        if self.select("students", {"limit":"1"}):
            return
        self.insert("school_profile", {"school_name":"دبیرستان سردارشهیدحاجی زاده ۲","school_code":"FRAH-02","principal_name":"مدیریت مدرسه","academic_year":"۱۴۰۵-۱۴۰۶","phone":"","address":"شهرقدس"})
        self.insert("school_class_config", {"total_classes":9,"grade7_classes":3,"grade8_classes":3,"grade9_classes":3})
        self.insert("teachers", {"first_name":"علی","last_name":"رضایی","national_code":"1111111111","subject":"ریاضی","grades":"هفتم، هشتم، نهم","employment_status":"فعال"})
        self.insert("teachers", {"first_name":"مریم","last_name":"احمدی","national_code":"2222222222","subject":"علوم","grades":"هفتم، هشتم","employment_status":"فعال"})
        self.insert("teachers", {"first_name":"رضا","last_name":"کریمی","national_code":"3333333333","subject":"فارسی","grades":"نهم","employment_status":"فعال"})
        self.insert("staff", {"first_name":"حسن","last_name":"مدیریت","role":"مدیر","phone":"","employment_status":"فعال"})
        for i, item in enumerate((("امیر","محمدی","هفتم","الف"),("سارا","حسینی","هفتم","ب"),("علی","اکبری","هشتم","الف"),("نگار","کاظمی","نهم","الف")), 1):
            self.insert("students", {"first_name":item[0],"last_name":item[1],"national_code":f"000000000{i}","grade":item[2],"class_name":item[3],"phone":""})
        self.insert("teacher_classes", {"teacher_name":"علی رضایی","subject":"ریاضی","grade":"هفتم","class_name":"الف","active":True})
        self.insert("teacher_classes", {"teacher_name":"مریم احمدی","subject":"علوم","grade":"هفتم","class_name":"ب","active":True})
        self.insert("online_classes", {"title":"کلاس نمونه ریاضی هفتم","subject":"ریاضی","lesson":"ریاضی","teacher":"علی رضایی","grade":"هفتم","class_name":"الف","duration":60,"start_time_shamsi":"","end_time_shamsi":"","status":"inactive","join_url":"","meeting_url":""})
        self.insert("messages", {"sender_name":"مدیریت مدرسه","title":"خوش آمدید","body":"سامانه فراهوش برای مدیریت هوشمند مدرسه آماده است.","audience_type":"manager"})
        self.insert("finance_accounts", {"title":"حساب مدرسه","account_type":"school","balance":0,"active":True})
        self.insert("payment_offers", {"title":"کمک‌های داوطلبانه","amount":100000,"payment_reason":"مشارکت مدرسه","target_type":"school","target_value":"FRAH-02","active":True,"gateway_enabled":False,"manual_amount":False})

    def insert(self, table, payload):
        data = dict(payload or {})
        with self._connect() as db:
            cur = db.execute("INSERT INTO __rows(table_name,data) VALUES(?,?)", (str(table), json.dumps(data, ensure_ascii=False)))
            rid = cur.lastrowid
            data["id"] = rid
            db.execute("UPDATE __rows SET data=? WHERE row_id=?", (json.dumps(data, ensure_ascii=False), rid))
            db.commit()
        return data

    @staticmethod
    def _match(row, params):
        for key, expr in (params or {}).items():
            if key in {"limit","order","select"}:
                continue
            value = row.get(key)
            expr = str(expr)
            if expr.startswith("eq.") and str(value) != expr[3:]: return False
            if expr.startswith("neq.") and str(value) == expr[4:]: return False
            if expr.startswith("ilike."):
                needle = expr[7:].replace("%", "").lower()
                if needle not in str(value or "").lower(): return False
        return True

    def select(self, table, params=None):
        with self._connect() as db:
            rows = [json.loads(r["data"]) for r in db.execute("SELECT data FROM __rows WHERE table_name=? ORDER BY row_id", (str(table),))]
        rows = [r for r in rows if self._match(r, params)]
        order = str((params or {}).get("order") or "")
        if order:
            field, _, direction = order.partition(".")
            rows.sort(key=lambda x: str(x.get(field) or ""), reverse=(direction.lower()=="desc"))
        limit = (params or {}).get("limit")
        if limit:
            try: rows = rows[:max(0,int(limit))]
            except Exception: pass
        select = (params or {}).get("select")
        if select and select != "*":
            cols = [x.strip() for x in str(select).split(",")]
            rows = [{k:r.get(k) for k in cols} for r in rows]
        return rows

    def update(self, table, filters, payload):
        rows = self.select(table, filters)
        changed=[]
        with self._connect() as db:
            for row in rows:
                row.update(payload or {})
                changed.append(row)
                db.execute("UPDATE __rows SET data=? WHERE table_name=? AND row_id=?", (json.dumps(row,ensure_ascii=False),str(table),int(row.get("id"))))
            db.commit()
        return changed

    def delete(self, table, filters):
        rows=self.select(table,filters)
        with self._connect() as db:
            for row in rows: db.execute("DELETE FROM __rows WHERE table_name=? AND row_id=?",(str(table),int(row.get("id"))))
            db.commit()
        return rows

    def rpc(self, name, payload):
        p=payload or {}
        if name=="create_payment_attempt":
            offers=self.select("payment_offers", {"id":f"eq.{p.get('p_offer_id')}"}); offer=offers[0] if offers else {}
            return self.insert("payment_attempts", {"offer_id":p.get("p_offer_id"),"student_id":p.get("p_student_id"),"payer_username":"0053409531","amount":offer.get("amount",0),"status":"pending","created_at":datetime.now(timezone.utc).isoformat()})
        if name=="send_school_message":
            return self.insert("messages", {"sender_name":"مدیر فراهوش","title":p.get("p_title") or "پیام","body":p.get("p_body") or "","audience_type":p.get("p_audience_type") or "user","audience_value":p.get("p_audience_value")})
        if name=="create_teacher_exam_share":
            code="FRAH-"+secrets.token_hex(4).upper()
            return self.insert("teacher_exam_shares", {"quiz_id":p.get("p_quiz_id"),"share_code":code,"target_school_id":p.get("p_target_school_id"),"target_class_name":p.get("p_target_class_name"),"start_at":p.get("p_start_at"),"end_at":p.get("p_end_at"),"duration_minutes":p.get("p_duration_minutes"),"active":True})
        if name=="get_shared_exam":
            shares=self.select("teacher_exam_shares", {"share_code":f"eq.{p.get('p_share_code')}"})
            if not shares:return None
            s=shares[0]; exams=self.select("teacher_exams", {"id":f"eq.{s.get('quiz_id')}"})
            if not exams:return None
            exam=dict(exams[0]); exam["share_code"]=s.get("share_code"); exam["duration"]=s.get("duration_minutes") or exam.get("duration",45); return exam
        if name=="start_shared_teacher_exam":
            shares=self.select("teacher_exam_shares", {"share_code":f"eq.{p.get('p_share_code')}"});
            if not shares: raise RuntimeError("آزمون پیدا نشد.")
            s=shares[0]; attempt=self.insert("teacher_exam_attempts", {"quiz_id":s.get("quiz_id"),"student_id":p.get("p_student_id"),"student_username":p.get("p_student_username"),"started_at":datetime.now(timezone.utc).isoformat(),"status":"started","score":0}); return {"attempt_id":attempt["id"],"duration":s.get("duration_minutes") or 45}
        if name=="get_shared_attempt_questions":
            ats=self.select("teacher_exam_attempts", {"id":f"eq.{p.get('p_attempt_id')}"});
            if not ats:return []
            qs=self.select("quiz_questions", {"quiz_id":f"eq.{ats[0].get('quiz_id')}"}); random.shuffle(qs)
            for q in qs:
                try: opts=json.loads(q.get("options_json") or "[]"); random.shuffle(opts); q["options_json"]=json.dumps(opts,ensure_ascii=False)
                except Exception: pass
            return qs
        if name=="submit_teacher_exam":
            ats=self.select("teacher_exam_attempts", {"id":f"eq.{p.get('p_attempt_id')}"});
            if not ats: raise RuntimeError("تلاش آزمون پیدا نشد.")
            attempt=ats[0]; qs=self.select("quiz_questions", {"quiz_id":f"eq.{attempt.get('quiz_id')}"}); answers={str(x.get("question_id")):str(x.get("answer") or "").strip() for x in (p.get("p_answers") or [])}; score=0; maximum=0
            for q in qs:
                points=float(q.get("points") or 1); maximum+=points; kind=q.get("question_type"); ans=answers.get(str(q.get("id")),""); correct=str(q.get("correct_answer") or "").strip(); accepted=[x.strip() for x in str(q.get("accepted_answers") or "").split("|") if x.strip()]
                if kind=="essay": continue
                ok=ans==correct or (accepted and ans in accepted)
                if ok: score+=points
                self.insert("teacher_exam_answers", {"attempt_id":attempt["id"],"question_id":q.get("id"),"answer":ans,"auto_correct":bool(ok),"score":points if ok else 0})
            self.update("teacher_exam_attempts", {"id":f"eq.{attempt['id']}"}, {"status":"submitted","submitted_at":datetime.now(timezone.utc).isoformat(),"score":score,"max_score":maximum})
            return {"score":score,"max_score":maximum}
        raise RuntimeError("عملیات محلی ناشناخته است: "+str(name))
