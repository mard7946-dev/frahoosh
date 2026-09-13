import json

from mobile.screens.teacher_exams_v2 import TeacherExamsV2Screen
from mobile.config import PRIMARY, SECONDARY, SUCCESS


class TeacherExamsV3Screen(TeacherExamsV2Screen):
    """Exam center with secure shared attempts and real auto-grading submission."""

    def _open_shared(self, code):
        code=(code or "").strip().rstrip("/").split("/")[-1]
        if not code:
            self._error("کد اشتراک را وارد کنید.")
            return
        try:
            exam=self.app_state.api.rpc("get_shared_exam",{"p_share_code":code})
            exam=exam[0] if isinstance(exam,list) and exam else exam
            if not exam:
                raise RuntimeError("آزمون پیدا نشد یا زمان آن فعال نیست.")
            student_id=(getattr(self.app_state,"profile",{}) or {}).get("linked_student_id")
            try: student_id=int(student_id) if student_id else None
            except Exception: student_id=None
            username=str((getattr(self.app_state,"profile",{}) or {}).get("username") or getattr(self.app_state,"national_code","") or "").strip()
            if not username:
                raise RuntimeError("شناسه دانش‌آموز برای شروع آزمون مشخص نیست.")
            attempt=self.app_state.api.rpc("start_shared_teacher_exam",{"p_share_code":code,"p_student_id":student_id,"p_student_username":username})
            attempt=attempt[0] if isinstance(attempt,list) and attempt else attempt
            self._render_attempt(code,exam,attempt)
        except Exception as exc:
            self._error(str(exc))

    def _render_attempt(self,code,exam,attempt):
        self._clear(); self._attempt_id=int(attempt["attempt_id"]); self._attempt_answers={}
        self._label(exam.get("title","آزمون"),"22sp",PRIMARY,52,True)
        self._label(f"{exam.get('subject','')}  •  مدت {attempt.get('duration') or exam.get('duration',45)} دقیقه\nآزمون امن است؛ ترتیب سؤال‌ها و گزینه‌ها برای شما اختصاصی است.",height=70)
        questions=self.app_state.api.rpc("get_shared_attempt_questions",{"p_attempt_id":self._attempt_id}) or []
        for i,q in enumerate(questions,1):
            self._label(f"{i}. {q.get('question','')}","16sp",PRIMARY,82,True)
            qid=int(q["id"]); typ=q.get("question_type")
            if typ=="essay":
                w=self._field("پاسخ تشریحی...",115,True)
            elif typ in ("fill_blank","short_answer"):
                w=self._field("پاسخ شما...")
            else:
                w=self._answer_spinner(qid,q.get("options_json") or "[]")
            self._attempt_answers[qid]=w
            self._label("▧  این سؤال بخشی از آزمون ارزیابی است؛ لطفاً درباره پاسخ آن در هیچ چتی گفتگو نکنید.","10sp",SECONDARY,40)
        self._button("ارسال نهایی آزمون",lambda *_:self._submit_attempt(),SUCCESS)
        self._button("انصراف",lambda *_:self.show_home(),PRIMARY)

    def _answer_spinner(self,qid,options_json):
        try: options=json.loads(options_json)
        except Exception: options=[]
        options=[str(x) for x in options]
        if not options: options=["گزینه‌ای وجود ندارد"]
        w=__import__('kivy.uix.spinner',fromlist=['Spinner']).Spinner(text=options[0],values=tuple(options),size_hint_y=None,height=__import__('kivy.metrics',fromlist=['dp']).dp(50))
        self.body.add_widget(w); return w

    def _submit_attempt(self):
        answers=[]
        for qid,w in self._attempt_answers.items():
            answers.append({"question_id":qid,"answer":str(getattr(w,"text","") or "")})
        try:
            for qid,w in self._attempt_answers.items():
                if hasattr(w,"values"):
                    answers=[a for a in answers if a["question_id"]!=qid]+[{"question_id":qid,"answer":str(w.text)}]
            result=self.app_state.api.rpc("submit_teacher_exam",{"p_attempt_id":self._attempt_id,"p_answers":answers})
            result=result[0] if isinstance(result,list) and result else result
            self._clear(); self._label("آزمون با موفقیت ثبت شد","23sp",SUCCESS,60,True)
            self._label(f"نمره خودکار: {result.get('score',0)} از {result.get('max_score',0)}", "20sp", PRIMARY,60,True)
            self._label("سؤال‌های تشریحی برای دبیر ارسال شده‌اند و نیاز به تصحیح دستی دارند.",height=65)
            self._button("بازگشت به مرکز آزمون",lambda *_:self.show_home(),PRIMARY)
        except Exception as exc:self._error("ثبت آزمون انجام نشد: "+str(exc))
