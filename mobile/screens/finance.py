import json, mimetypes
from pathlib import Path
from datetime import datetime
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, APP_NAME
from mobile.ui import font_name, fa_display
from mobile.services.export_service import export_excel, export_pdf

class FinanceScreen(Screen):
    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs); self.app_state=app_state; self._tx_id=None; self._build()

    def _build(self):
        root=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(7))
        head=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(7))
        b=Button(text=fa_display("‹ بازگشت"),font_name=font_name(),background_normal="",background_color=PRIMARY,color=WHITE,size_hint_x=None,width=dp(95)); b.bind(on_release=lambda *_:self._back()); head.add_widget(b)
        self.title=Label(text=fa_display("حسابداری مدرسه"),font_name=font_name(),font_size="20sp",bold=True,color=PRIMARY,halign="right",valign="middle"); self.title.bind(size=lambda o,v:setattr(o,"text_size",v)); head.add_widget(self.title); root.add_widget(head)
        self.status=Label(text="",font_name=font_name(),font_size="11sp",color=SECONDARY,size_hint_y=None,height=dp(36),halign="right",valign="middle"); self.status.bind(size=lambda o,v:setattr(o,"text_size",v)); root.add_widget(self.status)
        scroll=ScrollView(do_scroll_x=False); self.body=BoxLayout(orientation="vertical",spacing=dp(8),size_hint_y=None,padding=dp(4)); self.body.bind(minimum_height=self.body.setter("height")); scroll.add_widget(self.body); root.add_widget(scroll); self.add_widget(root); self.home()

    def _label(self,t,h=48,size="12sp",color=SECONDARY):
        w=Label(text=fa_display(t),font_name=font_name(),font_size=size,color=color,halign="right",valign="middle",size_hint_y=None,height=dp(h)); w.bind(size=lambda o,v:setattr(o,"text_size",v)); self.body.add_widget(w); return w
    def _button(self,t,cb,color=PRIMARY,h=46):
        b=Button(text=fa_display(t),font_name=font_name(),font_size="12sp",background_normal="",background_color=color,color=WHITE,size_hint_y=None,height=dp(h)); b.bind(on_release=cb); self.body.add_widget(b); return b
    def _field(self,h,hgt=46):
        f=TextInput(hint_text=fa_display(h),font_name=font_name(),font_size="12sp",size_hint_y=None,height=dp(hgt),halign="right"); self.body.add_widget(f); return f

    def home(self):
        self.body.clear_widgets(); self.title.text=fa_display("حسابداری مدرسه")
        self._label("دفتر حساب، حساب‌های مدرسه، درآمد/هزینه، بدهکار/بستانکار، پیوست فاکتور و چک و گزارش پایان سال مالی.",62,"13sp",PRIMARY)
        self._button("حساب‌های مدرسه",lambda *_:self.accounts(),PRIMARY)
        self._button("ثبت سند مالی",lambda *_:self.new_transaction(),SUCCESS)
        self._button("دفتر تراکنش‌ها و پیوست اسناد",lambda *_:self.transactions(),PRIMARY)
        self._button("گزارش و بستن سال مالی",lambda *_:self.year_end(),SECONDARY)

    def accounts(self):
        self.body.clear_widgets(); self.title.text=fa_display("حساب‌های مدرسه")
        title=self._field("نام حساب؛ مثال حساب بانکی مدرسه"); typ=self._field("نوع حساب؛ بانک / صندوق / درآمد / هزینه"); num=self._field("شماره حساب؛ اختیاری")
        self._button("ثبت حساب",lambda *_:self._save_account(title,typ,num),SUCCESS)
        try:
            rows=self.app_state.api.table_select("finance_accounts",{"order":"id.asc","limit":"200"})
            for r in rows:self._label(f"#{r.get('id')} | {r.get('title','')}\nنوع: {r.get('account_type','')} | موجودی: {r.get('balance',0)} | شماره: {r.get('account_number','')}",70)
        except Exception as e:self._error(str(e))
        self._button("بازگشت",lambda *_:self.home(),SECONDARY)
    def _save_account(self,t,typ,num):
        if not t.text.strip():return self._error("نام حساب الزامی است.")
        try:self.app_state.api.table_insert("finance_accounts",{"title":t.text.strip(),"account_type":typ.text.strip(),"account_number":num.text.strip(),"balance":0}); self._ok("حساب ثبت شد."); self.accounts()
        except Exception as e:self._error("ثبت حساب انجام نشد: "+str(e))

    def new_transaction(self):
        self.body.clear_widgets(); self.title.text=fa_display("ثبت سند مالی")
        title=self._field("شرح سند؛ مثال خرید لوازم آموزشی"); amount=self._field("مبلغ")
        typ=self._field("نوع؛ درآمد / هزینه / انتقال"); cat=self._field("دسته‌بندی")
        date=self._field("تاریخ تراکنش؛ مثال 1405/07/15"); inv=self._field("شماره فاکتور")
        counter=self._field("طرف حساب"); desc=self._field("توضیحات",70)
        self._label("برای سند دوبل: یکی از بدهکار/بستانکار را در مرحله بعد از ثبت دفتر تکمیل کنید. فاکتور یا تصویر چک را نیز می‌توانید به سند پیوست کنید.",62,"10sp")
        self._button("ثبت سند",lambda *_:self._save_tx(title,amount,typ,cat,date,inv,counter,desc),SUCCESS)
        self._button("بازگشت",lambda *_:self.home(),SECONDARY)
    def _save_tx(self,title,amount,typ,cat,date,inv,counter,desc):
        try:a=float(str(amount.text).replace(",","").strip())
        except:return self._error("مبلغ معتبر نیست.")
        if a<=0 or not title.text.strip():return self._error("شرح و مبلغ الزامی است.")
        try:
            rows=self.app_state.api.table_insert("finance_transactions",{"transaction_type":typ.text.strip() or "expense","title":title.text.strip(),"amount":a,"category":cat.text.strip(),"description":desc.text.strip(),"transaction_date":date.text.strip(),"invoice_number":inv.text.strip(),"counterparty":counter.text.strip(),"debit":a if (typ.text.strip() or "expense") in ("expense","debit") else 0,"credit":a if (typ.text.strip() or "expense") in ("income","credit") else 0})
            self._tx_id=int(rows[0]["id"] if isinstance(rows,list) else rows["id"]); self._ok("سند ثبت شد."); self.attach()
        except Exception as e:self._error("ثبت سند انجام نشد: "+str(e))

    def attach(self):
        self.body.clear_widgets(); self.title.text=fa_display("پیوست سند مالی")
        self._label("تصویر فاکتور، رسید، چک یا PDF را انتخاب کنید. فایل در فضای خصوصی مالی مدرسه ذخیره می‌شود.",65,"11sp",PRIMARY)
        self._button("انتخاب تصویر / PDF",lambda *_:self._pick_file(),SUCCESS)
        self._button("بدون پیوست؛ بازگشت به دفتر",lambda *_:self.transactions(),SECONDARY)

    def _pick_file(self):
        chooser=FileChooserListView(path=str(Path.home()),filters=["*.jpg","*.jpeg","*.png","*.webp","*.pdf"],multiselect=False)
        box=BoxLayout(orientation="vertical"); box.add_widget(chooser)
        row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5)); ok=Button(text=fa_display("انتخاب"),font_name=font_name()); cancel=Button(text=fa_display("انصراف"),font_name=font_name()); row.add_widget(ok); row.add_widget(cancel); box.add_widget(row)
        pop=Popup(title=fa_display("انتخاب سند"),content=box,size_hint=(.95,.85))
        cancel.bind(on_release=pop.dismiss)
        ok.bind(on_release=lambda *_:self._upload_selected(chooser,pop)); pop.open()

    def _upload_selected(self,chooser,pop):
        if not chooser.selection:return self._error("یک فایل انتخاب کنید.")
        path=Path(chooser.selection[0]); pop.dismiss()
        try:
            data=path.read_bytes(); mime=mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            object_path=f"{self.app_state.user_id if hasattr(self.app_state,'user_id') else 'staff'}/finance/{self._tx_id}_{path.name}"
            self.app_state.api.storage_upload("finance-documents",object_path,data,mime)
            self.app_state.api.table_insert("finance_transaction_attachments",{"transaction_id":self._tx_id,"file_path":object_path,"file_name":path.name,"mime_type":mime,"created_by":str(getattr(self.app_state,"national_code","") or "")})
            self._ok("فایل با موفقیت به سند مالی پیوست شد."); self.transactions()
        except Exception as e:self._error("بارگذاری سند انجام نشد: "+str(e))

    def transactions(self):
        self.body.clear_widgets(); self.title.text=fa_display("دفتر تراکنش‌ها")
        try:
            rows=self.app_state.api.table_select("finance_transactions",{"order":"id.desc","limit":"500"})
            total_d=sum(float(r.get("debit") or 0) for r in rows); total_c=sum(float(r.get("credit") or 0) for r in rows)
            self._label(f"جمع بدهکار: {total_d:,.0f} | جمع بستانکار: {total_c:,.0f} | مانده: {total_c-total_d:,.0f}",60,"13sp",PRIMARY)
            for r in rows:
                at=self.app_state.api.table_select("finance_transaction_attachments",{"transaction_id":f"eq.{r.get('id')}","limit":"20"})
                self._label(f"#{r.get('id')} | {r.get('title','')}\nمبلغ {r.get('amount',0)} | بدهکار {r.get('debit',0)} | بستانکار {r.get('credit',0)} | فاکتور {r.get('invoice_number','')}\nپیوست: {len(at)} فایل",84)
            fields=["id","transaction_type","title","amount","category","transaction_date","invoice_number","counterparty","debit","credit","description"]
            if rows:
                self._button("خروجی Excel دفتر مالی",lambda *_:self._export_file(rows,fields,"excel","دفتر_مالی"),SUCCESS)
                self._button("خروجی PDF دفتر مالی",lambda *_:self._export_file(rows,fields,"pdf","دفتر_مالی"),PRIMARY)
        except Exception as e:self._error("خواندن دفتر مالی انجام نشد: "+str(e))
        self._button("ثبت سند جدید",lambda *_:self.new_transaction(),SUCCESS); self._button("بازگشت",lambda *_:self.home(),SECONDARY)

    def _export_file(self,rows,fields,kind,title):
        try:
            path=export_excel(rows,fields,title) if kind=="excel" else export_pdf(rows,fields,title)
            self._ok("خروجی ایجاد شد: "+str(path))
        except Exception as e:self._error("خروجی ایجاد نشد: "+str(e))

    def year_end(self):
        self.body.clear_widgets(); self.title.text=fa_display("بستن سال مالی")
        year=self._field("سال مالی؛ مثال 1405-1406"); start=self._field("از تاریخ"); end=self._field("تا تاریخ")
        self._button("محاسبه و ثبت گزارش پایان سال",lambda *_:self._close_year(year,start,end),SUCCESS)
        self._button("بازگشت",lambda *_:self.home(),SECONDARY)
    def _close_year(self,year,start,end):
        try:
            rows=self.app_state.api.table_select("finance_transactions",{"order":"id.asc","limit":"5000"})
            sd=sum(float(r.get("debit") or 0) for r in rows); sc=sum(float(r.get("credit") or 0) for r in rows)
            cats={}
            for r in rows:cats[r.get("category") or "سایر"]=cats.get(r.get("category") or "سایر",0)+float(r.get("amount") or 0)
            snap={"transactions":len(rows),"total_debit":sd,"total_credit":sc,"net":sc-sd,"categories":cats}
            self.app_state.api.table_insert("finance_year_end_reports",{"fiscal_year":year.text.strip(),"period_start":start.text.strip(),"period_end":end.text.strip(),"total_debit":sd,"total_credit":sc,"net_balance":sc-sd,"snapshot_json":json.dumps(snap,ensure_ascii=False),"created_by":str(getattr(self.app_state,"national_code","") or "")})
            fields=["id","transaction_type","title","amount","category","transaction_date","invoice_number","counterparty","debit","credit","description"]
            stamp=year.text.strip().replace("/","-") or "سال"
            xp=export_excel(rows,fields,"گزارش_پایان_سال_"+stamp); pp=export_pdf(rows,fields,"گزارش_پایان_سال_"+stamp)
            self._ok("گزارش پایان سال ثبت و خروجی Excel/PDF ساخته شد. Excel: "+xp+" | PDF: "+pp)
        except Exception as e:self._error("بستن سال مالی انجام نشد: "+str(e))
    def _ok(self,t):self.status.color=SUCCESS; self.status.text=fa_display(t)
    def _error(self,t):self.status.color=ERROR; self.status.text=fa_display(t)
    def _back(self):
        try:self.manager.current="dashboard"
        except Exception:pass
