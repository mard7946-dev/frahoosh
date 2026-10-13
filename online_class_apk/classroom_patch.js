(()=>{"use strict";
const C=window.C||{},$=id=>document.getElementById(id);
const role=String(C.role||"student").toLowerCase();
const student=["student","دانش‌آموز","guest","میهمان"].includes(role);
const teacher=["teacher","دبیر"].includes(role);
const controller=["teacher","دبیر","manager","مدیر","executive","معاون اجرایی","educational","معاون آموزشی","counselor","مشاوره","principal","admin"].includes(role);
let target="",presence=new Map(),latestNames=new Map();
const headers={"apikey":C.anon,"Authorization":"Bearer "+C.token,"Content-Type":"application/json"};
async function api(path,opts={}){const r=await fetch(C.url+"/rest/v1/"+path,{...opts,headers:{...headers,...(opts.headers||{})}});if(!r.ok)throw Error(await r.text());const t=await r.text();return t?JSON.parse(t):null}
async function sig(type,p={},to=null){try{await api("online_class_signals",{method:"POST",headers:{...headers,"Prefer":"return=minimal"},body:JSON.stringify({class_id:C.classId,sender_user_id:C.userId,receiver_user_id:to,signal_type:type,payload:p})})}catch(e){console.warn("Classroom signal failed",e)}}
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
 $("saveStudentPermissions").onclick=async()=>{if(!target){alert("ابتدا دانش‌آموز متصل را انتخاب کنید.");return}const permissions={mic:$("permMic").checked,cam:$("permCam").checked,pen:$("permPen").checked,eraser:$("permEraser").checked,file:$("permFile").checked};await sig("tools_permission",{permissions,allowed:Object.values(permissions).some(Boolean)},target);$("studentToolStatus").textContent="مجوزهای انتخاب‌شده برای این دانش‌آموز ثبت شد."};
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
   const payload=rows[0].payload,permissions=payload.permissions||{mic:false,cam:false,pen:!!payload.allowed,eraser:!!payload.allowed,file:!!payload.allowed};
   if(typeof setStudentToolsPermission==="function")setStudentToolsPermission(permissions);
   const status=$("permStatus");if(status)status.textContent="مجوزهای صدا، تصویر، قلم، پاک‌کن و فایل مطابق تنظیم دبیر اعمال شده‌اند؛ سایر ابزارها غیرفعال‌اند.";
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