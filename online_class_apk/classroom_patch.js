(()=>{"use strict";
const C=window.C||{},$=id=>document.getElementById(id);
const role=String(C.role||"student").toLowerCase();
const student=["student","دانش‌آموز","guest","میهمان"].includes(role);
const teacher=["teacher","دبیر"].includes(role);
const controller=["teacher","دبیر","manager","مدیر","executive","executive_deputy","معاون اجرایی","معاونت اجرایی","educational","educational_deputy","معاون آموزشی","معاونت آموزشی","cultural","cultural_deputy","معاون پرورشی","معاونت پرورشی","counselor","مشاوره","principal","administrator","admin"].includes(role);
let target="",presence=new Map(),latestNames=new Map(),lastAppliedPermissions="";
const headers={"apikey":C.anon,"Authorization":"Bearer "+C.token,"Content-Type":"application/json"};
async function api(path,opts={}){const r=await fetch(C.url+"/rest/v1/"+path,{...opts,headers:{...headers,...(opts.headers||{})}});if(!r.ok)throw Error(await r.text());const t=await r.text();return t?JSON.parse(t):null}
async function sig(type,p={},to=null){try{await api("online_class_signals",{method:"POST",headers:{...headers,"Prefer":"return=minimal"},body:JSON.stringify({class_id:C.classId,sender_user_id:C.userId,receiver_user_id:to,signal_type:type,payload:{...(p||{}),sessionId:C.sessionId??null}})})}catch(e){console.warn("Classroom signal failed",e)}}
function esc(s){return String(s??"").replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]))}
function rosterMarkup(rows){
 const now=Date.now(),latest=new Map();
 for(const r of rows||[]){if(!r.sender_user_id||latest.has(r.sender_user_id))continue;latest.set(r.sender_user_id,r)}
 const people=[];
 for(const [id,r] of latest){
  const when=Date.parse(r.created_at||"");
  if(r.signal_type==="leave"||!Number.isFinite(when)||now-when>20000)continue;
  const name=r.payload?.name||"کاربر کلاس";
  people.push({id,name});
 }
 latestNames=new Map(people.map(p=>[p.id,p.name]));
 $("participants").innerHTML=people.map(p=>'<div class="person"><b>'+esc(p.name)+'</b><br><span style="color:#5ee39a">● متصل به کلاس</span></div>').join("")||'<div class="person">هنوز دانش‌آموزی وارد کلاس نشده است.</div>';
 const select=$("chatTarget");
 if(select&&controller){
  const previous=target||select.value;
  select.innerHTML='<option value="">انتخاب دانش‌آموز</option>'+people.filter(p=>p.id!==C.userId).map(p=>'<option value="'+esc(p.id)+'">'+esc(p.name)+'</option>').join("");
  if(people.some(p=>p.id===previous))select.value=previous;else target=select.value="";
 }
}
async function refreshRoster(){
 try{
  const rows=await api("online_class_signals?class_id=eq."+encodeURIComponent(C.classId)+"&signal_type=in.(join,presence,leave)&order=id.desc&limit=500");
  rosterMarkup(rows);
 }catch(e){console.warn("Could not refresh classroom participants",e)}
}
function buildTeacherControls(){
 if($("teacherControls"))return;
 const p=document.createElement("div");p.className="panel";p.id="teacherControls";
 p.innerHTML='<b>مجوزهای دانش‌آموز انتخاب‌شده</b><div class="row" style="margin-top:6px"><select id="chatTarget"><option value="">انتخاب دانش‌آموز متصل</option></select></div><div class="row" style="margin-top:8px"><label><input type="checkbox" id="permMic"> میکروفون</label><label><input type="checkbox" id="permCam"> دوربین</label><label><input type="checkbox" id="permPen"> قلم</label><label><input type="checkbox" id="permEraser"> پاک‌کن</label><label><input type="checkbox" id="permFile"> اشتراک فایل</label></div><div class="row"><button id="saveStudentPermissions">ثبت مجوزها</button><button id="denyStudentTools" class="danger">لغو همه مجوزها</button></div><div class="status" id="studentToolStatus">ابتدا دانش‌آموز متصل را انتخاب کنید. سایر ابزارهای دانش‌آموز غیرفعال می‌مانند.</div>';
 document.querySelector(".boardwrap")?.prepend(p);
 $("chatTarget").addEventListener("change",e=>{target=e.target.value});
 $("saveStudentPermissions").onclick=async()=>{if(!target){alert("ابتدا دانش‌آموز متصل را انتخاب کنید.");return}const permissions={mic:$("permMic").checked,cam:$("permCam").checked,pen:$("permPen").checked,eraser:$("permEraser").checked,file:$("permFile").checked};await sig("tools_permission",{permissions,allowed:Object.values(permissions).some(Boolean),sessionId:C.sessionId??null},target);$("studentToolStatus").textContent="مجوزهای انتخاب‌شده برای این دانش‌آموز ثبت شد."};
 $("denyStudentTools").onclick=async()=>{if(!target){alert("ابتدا دانش‌آموز متصل را انتخاب کنید.");return}const permissions={mic:false,cam:false,pen:false,eraser:false,file:false};["permMic","permCam","permPen","permEraser","permFile"].forEach(id=>$(id).checked=false);await sig("tools_permission",{permissions,allowed:false},target);$("studentToolStatus").textContent="همه مجوزهای اختیاری این دانش‌آموز لغو شد."};
}
function restrictStudentUI(){
 const chat=document.querySelector(".chat");if(chat)chat.style.display="none";
 const side=document.querySelector(".side");if(side)side.style.display="none";
 const layout=document.querySelector(".layout");if(layout)layout.style.gridTemplateColumns="1fr";
 const quiz=$("quizPanel");if(quiz){quiz.style.display="block";const create=$("quizCreate");if(create)create.style.display="none";const results=$("quizResults");if(results)results.style.display="none"}
 const quizToggle=$("quizToggle");if(quizToggle){quizToggle.style.display="inline-block";quizToggle.disabled=false;quizToggle.textContent="آزمونک‌های منتشرشده"}
 for(const id of ["screen","prev","next","clear","clearAll","color","size","teacherToolPermission"]){const el=$(id);if(el)el.style.display="none"}
 document.querySelectorAll("[data-tool]").forEach(el=>{const ok=["pen","eraser"].includes(el.dataset.tool);el.style.display=ok?"inline-block":"none"});
 const fileManager=$("fileManager");if(fileManager)fileManager.style.display="block";
 const file=$("file");if(file){file.disabled=true;file.style.display="block"}
 
 for(const id of ["mic","cam"]){const el=$(id);if(el){el.style.display="inline-block";el.disabled=true;el.title="برای فعال‌سازی باید دبیر مجوز بدهد";}}
 if(!$("studentPermissions")){
  const p=document.createElement("div");p.className="panel";p.id="studentPermissions";
  p.innerHTML="<b>دسترسی ابزارها</b><div id=permStatus>تا اجازه دبیر داده نشود، قلم، پاک‌کن و اشتراک فایل/ویدیو غیرفعال است.</div>";
  document.querySelector(".boardwrap")?.prepend(p);
 }
}
async function pollPermissions(){
 if(!student)return;
 try{
  const rows=await api("online_class_signals?class_id=eq."+encodeURIComponent(C.classId)+"&receiver_user_id=eq."+encodeURIComponent(C.userId)+"&signal_type=eq.tools_permission&order=id.desc&limit=1");
  if(rows&&rows[0]&&(typeof rows[0].payload?.allowed==="boolean"||rows[0].payload?.permissions)){
   const payload=rows[0].payload;
   if(!payload.sessionId||String(payload.sessionId)!==String(C.sessionId||""))return;
   const permissions=payload.permissions||{mic:false,cam:false,pen:!!payload.allowed,eraser:!!payload.allowed,file:!!payload.allowed};
   const signature=JSON.stringify(permissions);
   if(signature!==lastAppliedPermissions){lastAppliedPermissions=signature;if(typeof setStudentToolsPermission==="function")setStudentToolsPermission(permissions)}
   const status=$("permStatus");if(status)status.textContent="مجوزهای صدا، تصویر، قلم، پاک‌کن و فایل فقط برای نشست فعال همین کلاس اعمال می‌شوند.";
  }
 }catch(e){console.warn("Could not check student tool permissions",e)}
}
function install(){
 if(!C.token||!C.classId||!C.userId)return;
 if(student)restrictStudentUI();
 if(teacher)buildTeacherControls();
 sig("presence",{name:C.name,role});
 setInterval(()=>sig("presence",{name:C.name,role}),5000);
 refreshRoster();setInterval(refreshRoster,5000);
 if(student){pollPermissions();setInterval(pollPermissions,2500)}
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install);else setTimeout(install,100);
})();


/* Local roster manager: all staff/student identity rows remain on this device, never sent to Supabase. */
(function localRosterManager(){
 "use strict";
 const C=window.C||{},$=id=>document.getElementById(id);
 const role=String(C.role||"").trim().toLowerCase();
 const manager=["manager","مدیر","مدیریت","principal","admin","administrator"].includes(role);
 const teacherOrManager=manager||["teacher","دبیر","educational","معاون آموزشی","executive","معاون اجرایی"].includes(role);
 if(!teacherOrManager)return;
 const key="frahoosh_local_roster_v1_"+String(C.classId||"general");
 const required=["role","first_name","last_name","class_code","person_code"];
 const fields=[
  {key:"role",label:"نوع کاربر",required:true,options:["دانش‌آموز","دبیر"]},
  {key:"first_name",label:"نام",required:true},
  {key:"last_name",label:"نام خانوادگی",required:true},
  {key:"class_code",label:"کد کلاس",required:true},
  {key:"person_code",label:"شناسه دانش‌آموز/دبیر",required:true},
  {key:"grade",label:"پایه",required:false},
  {key:"group",label:"گروه/رشته",required:false}
 ];
 let roster=[];
 const normalize=s=>String(s??"").trim().replace(/ي/g,"ی").replace(/ك/g,"ک").replace(/\s+/g," ");
 const escape=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
 function load(){try{const r=JSON.parse(localStorage.getItem(key)||"[]");roster=Array.isArray(r)?r:[]}catch(_){roster=[]}}
 function save(){localStorage.setItem(key,JSON.stringify(roster))}
 function addStyles(){if($("fraRosterStyle"))return;const s=document.createElement("style");s.id="fraRosterStyle";s.textContent="#fraRosterBtn{background:#d9b45b;color:#09182a}#fraRosterShade{position:fixed;inset:0;z-index:100000;background:#020812dd;display:grid;place-items:center;padding:12px;font-family:Tahoma,Arial,sans-serif}#fraRosterBox{width:min(900px,100%);max-height:94dvh;overflow:auto;background:#10243a;color:#f7f9fc;border:1px solid #d9b45b;border-radius:16px;padding:14px;box-shadow:0 18px 60px #0009}#fraRosterBox h2,#fraRosterBox h3{color:#f3c65b;margin:7px 0 12px}#fraRosterBox input,#fraRosterBox select{width:100%;min-width:0;padding:9px;border:1px solid #3a536d;border-radius:8px;background:#071727;color:white;font:inherit}#fraRosterBox label{display:block;font-size:12px;margin:4px 0}#fraRosterBox .fr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}#fraRosterBox .fr-actions{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0}#fraRosterBox button{padding:9px 12px;border:1px solid #3a536d;border-radius:8px;background:#1b4164;color:white;font:inherit;font-weight:bold}#fraRosterBox button.fr-gold{background:#d9b45b;color:#071727}#fraRosterBox button.fr-red{background:#822d3a}#fraRosterBox .fr-help{font-size:12px;line-height:1.9;color:#d1deed}#fraRosterBox .fr-tablewrap{overflow:auto;max-height:32dvh}#fraRosterBox table{border-collapse:collapse;width:100%;font-size:12px}#fraRosterBox th,#fraRosterBox td{border:1px solid #334b64;padding:7px;text-align:right;white-space:nowrap}#fraRosterBox th{background:#193753;color:#f3c65b}@media(max-width:520px){#fraRosterBox{padding:10px}#fraRosterBox .fr-actions button{flex:1 1 auto}}";document.head.appendChild(s)}
 function ensureButton(){if($("fraRosterBtn"))return;const b=document.createElement("button");b.id="fraRosterBtn";b.type="button";b.textContent="مدیریت اطلاعات دبیر و دانش‌آموز";b.onclick=openPanel;const host=document.querySelector("header .toolbar")||document.querySelector("header");host?.appendChild(b)}
 function panelField(f){if(f.options)return '<div><label for="fr_'+f.key+'">'+f.label+(f.required?' <b style="color:#ff7474">*</b>':'')+'</label><select id="fr_'+f.key+'" '+(f.required?'required':'')+'>'+f.options.map(o=>'<option value="'+escape(o)+'">'+escape(o)+'</option>').join("")+'</select></div>';return '<div><label for="fr_'+f.key+'">'+f.label+(f.required?' <b style="color:#ff7474">*</b>':'')+'</label><input id="fr_'+f.key+'" data-field="'+f.key+'" '+(f.required?'required':'')+' autocomplete="off"></div>'}
 function tableMarkup(){if(!roster.length)return '<p class="fr-help">هنوز اطلاعاتی در حافظه همین دستگاه ثبت نشده است.</p>';return '<div class="fr-tablewrap"><table><thead><tr><th>نوع</th><th>نام</th><th>نام خانوادگی</th><th>کد کلاس</th><th>شناسه</th><th>پایه</th><th>گروه/رشته</th><th>حذف</th></tr></thead><tbody>'+roster.map((r,i)=>'<tr><td>'+escape(r.role)+'</td><td>'+escape(r.first_name)+'</td><td>'+escape(r.last_name)+'</td><td>'+escape(r.class_code)+'</td><td>'+escape(r.person_code)+'</td><td>'+escape(r.grade)+'</td><td>'+escape(r.group)+'</td><td><button type="button" class="fr-red" data-delete="'+i+'">حذف</button></td></tr>').join("")+'</tbody></table></div>'}
 function openPanel(){load();addStyles();if($("fraRosterShade"))$("fraRosterShade").remove();const shade=document.createElement("div");shade.id="fraRosterShade";shade.innerHTML='<section id="fraRosterBox" dir="rtl" role="dialog" aria-modal="true" aria-label="مدیریت اطلاعات دبیران و دانش‌آموزان"><div class="fr-actions" style="justify-content:space-between"><h2>اطلاعات دبیران و دانش‌آموزان</h2><button type="button" id="frClose" class="fr-red">بستن</button></div><p class="fr-help">فیلدهای ستاره‌دار (*) اجباری‌اند. فایل اکسل و فرم دستی دقیقاً از ستون‌های یکسان استفاده می‌کنند. اطلاعات فقط در حافظه همین دستگاه ذخیره می‌شود و به Supabase ارسال نمی‌شود.</p><div class="fr-actions"><button type="button" id="frTemplate" class="fr-gold">دریافت قالب اکسل</button><button type="button" id="frExport">خروجی اکسل اطلاعات</button><button type="button" id="frImportBtn">ورود اطلاعات از اکسل</button><input id="frImportFile" type="file" accept=".xlsx,.xls,.csv" style="display:none"></div><h3>ثبت دستی اطلاعات</h3><form id="frForm"><div class="fr-grid">'+fields.map(panelField).join("")+'</div><div class="fr-actions"><button class="fr-gold" type="submit">ثبت اطلاعات</button><button type="reset">پاک‌کردن فرم</button></div></form><p id="frStatus" class="fr-help" role="status" aria-live="polite"></p><h3>اطلاعات ذخیره‌شده روی این دستگاه (<span id="frCount">'+roster.length+'</span>)</h3><div id="frTable">'+tableMarkup()+'</div><div class="fr-actions"><button type="button" id="frClear" class="fr-red">پاک‌کردن همه اطلاعات این دستگاه</button></div></section>';document.body.appendChild(shade);
 const close=()=>shade.remove();$("frClose").onclick=close;shade.addEventListener("click",e=>{if(e.target===shade)close()});
 $("frForm").onsubmit=e=>{e.preventDefault();const row={};for(const f of fields)row[f.key]=normalize($("fr_"+f.key).value);const missing=fields.filter(f=>f.required&&!row[f.key]);if(missing.length){$("frStatus").textContent="این فیلدها اجباری‌اند: "+missing.map(f=>f.label).join("، ");return}const duplicate=roster.some(x=>normalize(x.role)===row.role&&normalize(x.class_code)===row.class_code&&normalize(x.person_code)===row.person_code);if(duplicate){$("frStatus").textContent="این شناسه برای همین نوع کاربر و کد کلاس قبلاً ثبت شده است.";return}roster.push(row);save();renderTable();e.target.reset();$("frStatus").textContent="اطلاعات در همین دستگاه ذخیره شد."};
 $("frImportBtn").onclick=()=>$("frImportFile").click();
 $("frImportFile").onchange=async e=>{const file=e.target.files?.[0];if(!file)return;try{const rows=await parseFile(file);const normalized=rows.map(r=>{const out={};for(const f of fields){const aliases={[f.key]:f.key,[f.label]:f.key,["نوع کاربر"]: "role",["نام"]: "first_name",["نام خانوادگی"]:"last_name",["کد کلاس"]:"class_code",["شناسه دانش‌آموز/دبیر"]:"person_code",["شناسه دانش آموز/دبیر"]:"person_code",["گروه/رشته"]:"group"};for(const k of Object.keys(r)){if(aliases[normalize(k)]===f.key||normalize(k)===f.key)out[f.key]=normalize(r[k])}}return out});const invalid=normalized.findIndex(r=>fields.some(f=>f.required&&!r[f.key]));if(invalid>=0)throw Error("ردیف اکسل "+(invalid+2)+" یکی از ستون‌های اجباری را ندارد یا خالی است.");const seen=new Set(roster.map(x=>x.role+"|"+x.class_code+"|"+x.person_code));let added=0;for(const row of normalized){const k=row.role+"|"+row.class_code+"|"+row.person_code;if(seen.has(k))continue;roster.push(row);seen.add(k);added++}save();renderTable();$("frStatus").textContent=added+" ردیف وارد شد؛ ردیف‌های تکراری نادیده گرفته شدند. اطلاعات فقط محلی ذخیره شد."}catch(err){$("frStatus").textContent="ورود فایل انجام نشد: "+(err.message||"ساختار فایل را بررسی کنید.")}finally{e.target.value=""}};
 $("frTemplate").onclick=()=>exportWorkbook([], "قالب_اطلاعات_فراهوش");
 $("frExport").onclick=()=>exportWorkbook(roster,"اطلاعات_محلی_فراهوش");
 $("frClear").onclick=()=>{if(confirm("تمام اطلاعات دبیران و دانش‌آموزان ذخیره‌شده روی این دستگاه حذف شود؟")){roster=[];save();renderTable();$("frStatus").textContent="اطلاعات محلی پاک شد."}};
 $("frTable").onclick=e=>{const b=e.target.closest("[data-delete]");if(!b)return;roster.splice(Number(b.dataset.delete),1);save();renderTable();$("frStatus").textContent="ردیف حذف شد."};
 }
 function renderTable(){const box=$("frTable");if(box)box.innerHTML=tableMarkup();const count=$("frCount");if(count)count.textContent=roster.length}
 function headersRow(){return ["نوع کاربر","نام","نام خانوادگی","کد کلاس","شناسه دانش‌آموز/دبیر","پایه","گروه/رشته"]}
 function valuesRow(r){return [r.role||"",r.first_name||"",r.last_name||"",r.class_code||"",r.person_code||"",r.grade||"",r.group||""]}
 function exportWorkbook(rows,base){const matrix=[headersRow(),...rows.map(valuesRow)];if(window.XLSX){const ws=XLSX.utils.aoa_to_sheet(matrix);const wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,ws,"اطلاعات");XLSX.writeFile(wb,base+".xlsx");return}downloadText("\\ufeff"+matrix.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(",")).join("\r\n"),base+".csv","text/csv;charset=utf-8");}
 function downloadText(text,name,type){const blob=new Blob([text],{type}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
 function parseCSV(text){const rows=[];let row=[],cell="",quoted=false;for(let i=0;i<text.length;i++){const ch=text[i];if(ch==='"'&&quoted&&text[i+1]==='"'){cell+='"';i++}else if(ch==='"'){quoted=!quoted}else if((ch===","||ch===";"||ch==="\t")&&!quoted){row.push(cell);cell=""}else if((ch==="\n"||ch==="\r")&&!quoted){if(ch==="\r"&&text[i+1]==="\n")i++;row.push(cell);if(row.some(v=>String(v).trim()))rows.push(row);row=[];cell=""}else cell+=ch}row.push(cell);if(row.some(v=>String(v).trim()))rows.push(row);if(rows.length<2)throw Error("فایل CSV خالی است یا سطر عنوان ندارد.");const headers=rows.shift().map(normalize);return rows.map(cells=>Object.fromEntries(headers.map((h,i)=>[h,cells[i]??""])))}
 async function loadXLSX(){if(window.XLSX)return;await new Promise((resolve,reject)=>{const s=document.createElement("script");s.src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js";s.onload=resolve;s.onerror=()=>reject(Error("کتابخانه خواندن اکسل بارگذاری نشد؛ اینترنت را بررسی کنید یا فایل CSV وارد کنید."));document.head.appendChild(s)})}
 async function parseFile(file){const ext=file.name.toLowerCase().split(".").pop();if(ext==="csv")return parseCSV(await file.text());await loadXLSX();const wb=XLSX.read(await file.arrayBuffer(),{type:"array"});const ws=wb.Sheets[wb.SheetNames[0]];return XLSX.utils.sheet_to_json(ws,{defval:""}).map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[normalize(k),v])))}
 load();if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",ensureButton,{once:true});else ensureButton();
})();
