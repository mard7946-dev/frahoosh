const CFG=window.FRAHOOH_CONFIG||{};
const $=id=>document.getElementById(id);
let token=localStorage.getItem("frahoosh_access_token")||sessionStorage.getItem("frahoosh_access_token")||"";
let refreshToken=localStorage.getItem("frahoosh_refresh_token")||sessionStorage.getItem("frahoosh_refresh_token")||"";
let profile=JSON.parse(localStorage.getItem("frahoosh_profile")||sessionStorage.getItem("frahoosh_profile")||"null");
let catalog=null,currentPanel=null,currentTable=null,rows=[],selectedIndex=-1;
const panelTitles={management:"مدیریت",educational:"معاون آموزشی",executive:"معاون اجرایی",cultural:"معاون پرورشی",advisor:"مشاوره",teachers:"دبیران",students:"دانش‌آموزان",parents:"اولیا",finance:"مالی",online:"کلاس‌های آنلاین",teacher_exams:"آزمون آنلاین",smart_board:"تابلو هوشمند",ai:"هوش مصنوعی",reports:"گزارش‌ها",schedule:"برنامه هفتگی",messages:"صندوق پیام‌ها"};
const aliases={admin:"manager",administrator:"manager","مدیر":"manager","مدیریت":"manager","معاون آموزشی":"educational","معاون اجرایی":"executive","معاون پرورشی":"cultural","مشاور":"advisor","دبیر":"teacher","معلم":"teacher","دانش‌آموز":"student","ولی":"parent","اولیا":"parent"};
const roles={manager:"مدیریت",educational:"معاون آموزشی",executive:"معاون اجرایی",cultural:"معاون پرورشی",advisor:"مشاوره",teacher:"دبیر",student:"دانش‌آموز",parent:"ولی"};
const role=()=>aliases[String(profile?.role||"student").toLowerCase()]||String(profile?.role||"student");
const consumerWrite={student:new Set(["assignment_submissions","school_ally","basij_registration","school_mayor","student_council","certificate_requests"]),parent:new Set(["meeting_requests","parent_meeting_requests","transport_requests","parent_activities"])};
const managerRoles=new Set(["manager","educational","executive","cultural","advisor","teacher"]);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const norm=v=>String(v||"").replace(/[۰-۹٠-٩]/g,x=>{const a="۰۱۲۳۴۵۶۷۸۹",b="٠١٢٣٤٥٦٧٨٩";let i=a.indexOf(x);return i>=0?String(i):String(b.indexOf(x))});
const fieldLabels={national_code:"کد ملی",first_name:"نام",last_name:"نام خانوادگی",full_name:"نام و نام خانوادگی",username:"نام کاربری",email:"ایمیل",phone:"شماره تماس",mobile:"شماره همراه",role:"نقش",status:"وضعیت",gender:"جنسیت",birth_date:"تاریخ تولد",class_name:"کلاس",grade:"پایه",subject:"درس",teacher_name:"نام دبیر",student_name:"نام دانش‌آموز",date:"تاریخ",time:"زمان",description:"توضیحات",title:"عنوان",message:"پیام",score:"نمره",attendance_status:"وضعیت حضور",notes:"توضیحات",amount:"مبلغ",address:"آدرس",reason:"علت/موضوع",target:"مخاطب"};
const fieldLabel=k=>fieldLabels[k]||String(k).replaceAll("_"," ");
const ignoredExcelFields=new Set(["id","created_at","updated_at","deleted_at"]);
const excelKey=v=>String(v??"").replace(/^\uFEFF/,"").trim().replace(/\s+/g," ");
async function api(path,opt={}){
 const h={"apikey":CFG.supabase_anon_key,"Content-Type":"application/json",...(opt.headers||{})};
 if(token)h.Authorization="Bearer "+token;
 let r=await fetch(CFG.supabase_url.replace(/\/$/,"")+path,{...opt,headers:h});
 if(r.status===401&&refreshToken){const rr=await fetch(CFG.supabase_url+"/auth/v1/token?grant_type=refresh_token",{method:"POST",headers:{"apikey":CFG.supabase_anon_key,"Content-Type":"application/json"},body:JSON.stringify({refresh_token:refreshToken})});if(rr.ok){const d=await rr.json();token=d.access_token;refreshToken=d.refresh_token||refreshToken;saveSession();h.Authorization="Bearer "+token;r=await fetch(CFG.supabase_url.replace(/\/$/,"")+path,{...opt,headers:h})}}
 if(!r.ok)throw new Error((await r.text())||("HTTP "+r.status));return r.status===204?null:r.json();
}
function saveSession(){const store=$("remember").checked?localStorage:sessionStorage;store.setItem("frahoosh_access_token",token);store.setItem("frahoosh_refresh_token",refreshToken);store.setItem("frahoosh_profile",JSON.stringify(profile))}
async function login(){
 const id=norm($("identifier").value).trim(),pw=$("password").value;if(!id||!pw){setStatus("نام کاربری و رمز عبور را وارد کنید.",true);return}
 try{setStatus("در حال بررسی اطلاعات...");let email=id;
 if(!id.includes("@")){if(!/^\d{10}$/.test(id))throw Error("کد ملی باید ۱۰ رقمی باشد.");const e=await api("/rest/v1/rpc/lookup_auth_email_by_national_code",{method:"POST",body:JSON.stringify({p_national_code:id})});email=Array.isArray(e)?e[0]:e;if(!email)throw Error("برای این کد ملی حساب کاربری پیدا نشد.")}
 const d=await fetch(CFG.supabase_url+"/auth/v1/token?grant_type=password",{method:"POST",headers:{"apikey":CFG.supabase_anon_key,"Content-Type":"application/json"},body:JSON.stringify({email,password:pw})}).then(async r=>{if(!r.ok)throw Error((await r.text())||"ورود ناموفق بود.");return r.json()});
 token=d.access_token;refreshToken=d.refresh_token||"";profile=(await api("/rest/v1/account_settings?email=eq."+encodeURIComponent(email)+"&limit=1"))[0]||{role:"student",display_name:email,username:email,email};saveSession();renderDashboard();
 }catch(e){setStatus(e.message||"ورود انجام نشد.",true)}
}
async function loadCatalog(){catalog=await fetch("../shared/module_catalog.json").then(r=>{if(!r.ok)throw Error("قرارداد ماژول‌ها پیدا نشد.");return r.json()})}
function show(id){["login","dashboard","workspace"].forEach(x=>$(x).classList.toggle("hidden",x!==id))}
function setStatus(t,err=false){$("loginStatus").textContent=t;$("loginStatus").style.color=err?"#ff9d9d":"#7ee2a8"}
function allowedPanels(){
 const r=role();
 if(r==="manager")return Object.keys(catalog.panels||{});
 const map={educational:["educational"],executive:["executive"],cultural:["cultural"],advisor:["advisor"],teacher:["teachers"],student:["students"],parent:["parents"]};
 return map[r]||[];
}
function renderDashboard(){
 show("dashboard");$("schoolTitle").textContent=CFG.school_name||"دبیرستان";$("welcome").textContent="خوش آمدید، "+(profile?.display_name||profile?.username||"کاربر");
 const r=role();$("role").textContent="پنل "+(roles[r]||r)+" | دسترسی فعال";$("panels").innerHTML="";
 allowedPanels().forEach(k=>{const items=catalog.panels[k]||[],el=document.createElement("button");el.className="panel";el.innerHTML="<b>"+esc(panelTitles[k]||catalog.friendly?.[k]||k)+"</b><span>"+items.length+" زیرپنل عملیاتی</span>";el.onclick=()=>openPanel(k);$("panels").appendChild(el)});
}
function canWrite(table){
 const r=role();
 if(r==="manager"||managerRoles.has(r))return true;
 return !!consumerWrite[r]?.has(table);
}
function specialViewOnly(table){return (role()==="student"||role()==="parent")&&!canWrite(table)}
const meetingTables=new Set(["meeting_requests","parent_meeting_requests","teacher_meetings","meetings"]);
function openPanel(key){currentPanel=key;currentTable=null;selectedIndex=-1;show("workspace");$("workspaceTitle").textContent=panelTitles[key]||catalog.friendly?.[key]||key;$("workspaceMeta").textContent="محیط عملیاتی مشترک Web و Android • منبع داده: Supabase";renderModules()}
function renderModules(){
 const items=catalog.panels[currentPanel]||[];$("modules").innerHTML="";const excelAllowed=managerRoles.has(role());
 items.forEach(([label,table])=>{
  const card=document.createElement("div");card.className="module-card"+(table===currentTable?" active":"");
  const title=document.createElement("button");title.className="module";title.innerHTML="<b>"+esc(label)+"</b><span>"+esc(catalog.friendly?.[table]||table)+"</span>";title.onclick=()=>openTable(table);card.appendChild(title);
  if(excelAllowed&&!meetingTables.has(table)){
   const tools=document.createElement("div");tools.className="module-excel-tools";tools.innerHTML='<button type="button" data-excel-import>ورودی اکسل</button><button type="button" data-excel-export>خروجی اکسل</button>';
   tools.querySelector("[data-excel-import]").onclick=async()=>{if(await openTable(table))importExcel()};
   tools.querySelector("[data-excel-export]").onclick=async()=>{if(await openTable(table))downloadExcel(rows)};
   card.appendChild(tools);
  }
  $("modules").appendChild(card)
 });$("tableArea").innerHTML=""
}
async function openTable(table){
 currentTable=table;selectedIndex=-1;renderModules();$("tableArea").innerHTML='<div class="table-wrap"><div class="empty">در حال دریافت اطلاعات واقعی...</div></div>';
 try{rows=await api("/rest/v1/"+encodeURIComponent(table)+"?select=*&limit=300");if(!Array.isArray(rows))rows=[];renderTable(rows);return true}
 catch(e){rows=[];$("tableArea").innerHTML='<div class="table-wrap"><div class="empty">دریافت اطلاعات انجام نشد: '+esc(e.message)+'</div></div>';return false}
}
function tableKeys(data){const keys=[];data.forEach(r=>Object.keys(r||{}).forEach(k=>{if(!ignoredExcelFields.has(k)&&!keys.includes(k))keys.push(k)}));return keys}
function renderTable(data){
 const keys=tableKeys(data),write=canWrite(currentTable),viewOnly=specialViewOnly(currentTable);
 let html='<div class="table-wrap"><div class="table-tools"><input id="tableSearch" placeholder="جستجو در همین زیرپنل"><button class="primary" id="reload">تازه‌سازی</button>';
 if(write&&!viewOnly){const meeting=meetingTables.has(currentTable);html+='<button id="addRow">ثبت</button><button id="editRow">ویرایش</button><button class="danger" id="deleteRow">حذف</button>';if(!meeting)html+='<button id="importExcel">ورودی اکسل</button><button id="exportExcel">خروجی اکسل</button><button id="exportPdf">خروجی PDF</button>';}
 html+='</div><div class="crud-hint">'+(write&&!viewOnly?"یک ردیف را انتخاب کنید؛ سپس ویرایش یا حذف را بزنید.":"این زیرپنل برای این نقش فقط قابل مشاهده است.")+'</div>';
 if(!data.length){html+='<div class="empty">رکوردی برای نمایش وجود ندارد.</div></div>';$("tableArea").innerHTML=html;bindTools();return}
 html+='<table class="data-table"><thead><tr><th>انتخاب</th>'+keys.map(k=>"<th>"+esc(fieldLabel(k))+"</th>").join("")+'</tr></thead><tbody>'+data.map((r,i)=>"<tr data-index=\""+i+"\"><td><input type=\"radio\" name=\"rowpick\" value=\""+i+"\" "+(i===selectedIndex?"checked":"")+"></td>"+keys.map(k=>"<td>"+esc(r[k]===null||r[k]===undefined||r[k]===""?"—":r[k])+"</td>").join("")+"</tr>").join("")+'</tbody></table></div>';
 $("tableArea").innerHTML=html;
 document.querySelectorAll("input[name=rowpick]").forEach(x=>x.onchange=()=>{selectedIndex=Number(x.value)});
 $("reload").onclick=()=>openTable(currentTable);$("tableSearch").oninput=e=>{const q=e.target.value.toLowerCase();renderTable(rows.filter(r=>JSON.stringify(r).toLowerCase().includes(q)))};
 bindTools();
}
function bindTools(){
 const add=$("addRow"),edit=$("editRow"),del=$("deleteRow"),imp=$("importExcel"),exp=$("exportExcel"),pdf=$("exportPdf");
 if(add)add.onclick=()=>openEditor();
 if(edit)edit.onclick=()=>selectedIndex>=0?openEditor(rows[selectedIndex]):alert("ابتدا یک ردیف را انتخاب کنید.");
 if(del)del.onclick=deleteSelected;
 if(imp)imp.onclick=importExcel;
 if(exp)exp.onclick=()=>downloadExcel(rows);
 if(pdf)pdf.onclick=()=>window.print();
}
function editorFields(row){
 const keys=tableKeys([row||{}]).filter(k=>k!=="id");
 return keys.map(k=>'<label>'+esc(fieldLabel(k))+'<input data-field="'+esc(k)+'" value="'+esc(row?.[k]??"")+'"></label>').join("");
}
function openEditor(){
 const row=selectedIndex>=0?rows[selectedIndex]:null;
 const wrap=document.createElement("div");wrap.className="modal";wrap.innerHTML='<div class="modal-card"><h3>'+(row?"ویرایش رکورد":"ثبت رکورد")+'</h3><div class="form-grid">'+editorFields(row)+'</div><div class="modal-actions"><button id="saveRecord" class="primary">ذخیره</button><button id="cancelRecord" class="secondary">انصراف</button></div></div>';document.body.appendChild(wrap);
 $("cancelRecord").onclick=()=>wrap.remove();
 $("saveRecord").onclick=async()=>{const payload={};wrap.querySelectorAll("[data-field]").forEach(i=>{if(i.value!=="")payload[i.dataset.field]=i.value});try{if(row){const id=row.id;if(id===undefined||id===null)throw Error("این رکورد شناسه قابل ویرایش ندارد.");await api("/rest/v1/"+encodeURIComponent(currentTable)+"?id=eq."+encodeURIComponent(id),{method:"PATCH",headers:{"Prefer":"return=minimal"},body:JSON.stringify(payload)})}else await api("/rest/v1/"+encodeURIComponent(currentTable),{method:"POST",headers:{"Prefer":"return=minimal"},body:JSON.stringify(payload)});wrap.remove();selectedIndex=-1;await openTable(currentTable)}catch(e){alert("ذخیره انجام نشد: "+e.message)}};
}
async function deleteSelected(){
 if(selectedIndex<0){alert("ابتدا یک ردیف را انتخاب کنید.");return}
 const row=rows[selectedIndex];if(row.id===undefined||row.id===null){alert("این رکورد شناسه قابل حذف ندارد.");return}
 if(!confirm("این رکورد حذف شود؟"))return;
 try{await api("/rest/v1/"+encodeURIComponent(currentTable)+"?id=eq."+encodeURIComponent(row.id),{method:"DELETE",headers:{"Prefer":"return=minimal"}});selectedIndex=-1;await openTable(currentTable)}catch(e){alert("حذف انجام نشد: "+e.message)}
}
function excelColumns(data){
 const keys=tableKeys(data);
 return keys.length?keys:Object.keys(fieldLabels);
}
function downloadExcel(data){
 if(!window.XLSX){alert("کتابخانه Excel بارگذاری نشده است. صفحه را یک‌بار تازه‌سازی کنید.");return}
 const keys=excelColumns(data);
 const exportRows=data.map(r=>{const o={};keys.forEach(k=>{o[fieldLabel(k)]=r?.[k]??""});return o});
 if(!exportRows.length){const empty={};keys.forEach(k=>{empty[fieldLabel(k)]=""});exportRows.push(empty)}
 const ws=XLSX.utils.json_to_sheet(exportRows,{skipHeader:false});
 const wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,ws,"داده‌ها");
 XLSX.writeFile(wb,(catalog.friendly?.[currentTable]||currentTable)+"-فراهوش.xlsx",{bookType:"xlsx"});
}
function excelHeaderMap(){
 const map={};
 Object.entries(fieldLabels).forEach(([k,v])=>{map[excelKey(v)]=k;map[excelKey(k)]=k;map[excelKey(String(k).replaceAll("_"," "))]=k});
 tableKeys(rows).forEach(k=>{map[excelKey(k)]=k;map[excelKey(fieldLabel(k))]=k});
 return map;
}
function excelValue(v){
 if(v===undefined||v===null||v==="")return null;
 if(typeof v==="string"){
  const s=v.trim();
  if(s==="true"||s==="TRUE"||s==="بله")return true;
  if(s==="false"||s==="FALSE"||s==="خیر")return false;
  return s;
 }
 return v;
}
async function importExcel(){
 if(!window.XLSX){alert("کتابخانه Excel بارگذاری نشده است. صفحه را یک‌بار تازه‌سازی کنید.");return}
 const input=document.createElement("input");input.type="file";input.accept=".xlsx,.xls,.csv,.tsv";input.onchange=async()=>{
  const file=input.files?.[0];if(!file)return;
  try{
   const data=await file.arrayBuffer(),wb=XLSX.read(data,{type:"array",cellDates:false,raw:true});
   if(!wb.SheetNames.length)throw Error("هیچ Sheetای در فایل پیدا نشد.");
   const sheet=wb.Sheets[wb.SheetNames[0]],json=XLSX.utils.sheet_to_json(sheet,{defval:"",raw:true});
   if(!json.length)throw Error("فایل خالی است یا ردیف عنوان ندارد.");
   const map=excelHeaderMap(),payloads=json.map(source=>{
    const payload={};
    Object.entries(source).forEach(([header,value])=>{
     const key=map[excelKey(header)]||excelKey(header).replace(/\s+/g,"_");
     if(!ignoredExcelFields.has(key)&&key)payload[key]=excelValue(value);
    });
    return payload;
   }).filter(p=>Object.keys(p).length);
   if(!payloads.length)throw Error("هیچ ستون قابل شناسایی در فایل پیدا نشد.");
   let done=0;
   for(const payload of payloads){await api("/rest/v1/"+encodeURIComponent(currentTable),{method:"POST",headers:{"Prefer":"return=minimal"},body:JSON.stringify(payload)});done++}
   alert(done+" ردیف با موفقیت وارد شد.");await openTable(currentTable);
  }catch(e){alert("ورودی اکسل انجام نشد: "+(e.message||e))}
 };
 input.click();
}
function escText(s){return String(s??"").replace(/[\r\n]/g," ")}
$("loginBtn").onclick=login;$("password").addEventListener("keydown",e=>{if(e.key==="Enter")login()});$("forgot").onclick=()=>setStatus("بازیابی رمز باید از مسیر حساب کاربری/ایمیل ثبت‌شده انجام شود.");$("back").onclick=renderDashboard;$("refresh").onclick=()=>currentTable?openTable(currentTable):renderModules();$("logout").onclick=()=>{token="";refreshToken="";profile=null;sessionStorage.clear();localStorage.removeItem("frahoosh_access_token");localStorage.removeItem("frahoosh_refresh_token");localStorage.removeItem("frahoosh_profile");show("login")};
(async()=>{try{await loadCatalog();const saved=localStorage.getItem("frahoosh_access_token")||sessionStorage.getItem("frahoosh_access_token"),p=localStorage.getItem("frahoosh_profile")||sessionStorage.getItem("frahoosh_profile");if(saved&&p){token=saved;profile=JSON.parse(p);renderDashboard()}else show("login")}catch(e){setStatus("قرارداد مشترک Web بارگذاری نشد.",true)}})();