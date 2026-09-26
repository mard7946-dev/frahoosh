const CFG=window.FRAHOOH_CONFIG||{};
const $=id=>document.getElementById(id);
let token=localStorage.getItem("frahoosh_access_token")||sessionStorage.getItem("frahoosh_access_token")||"";
let refreshToken=localStorage.getItem("frahoosh_refresh_token")||sessionStorage.getItem("frahoosh_refresh_token")||"";
let profile=JSON.parse(localStorage.getItem("frahoosh_profile")||sessionStorage.getItem("frahoosh_profile")||"null");
let catalog=null,currentPanel=null,currentTable=null,rows=[];
const panelTitles={management:"مدیریت",educational:"معاون آموزشی",executive:"معاون اجرایی",cultural:"معاون پرورشی",advisor:"مشاوره",teachers:"دبیران",students:"دانش‌آموزان",parents:"اولیا"};
const aliases={admin:"manager",administrator:"manager","مدیر":"manager","مدیریت":"manager","معاون آموزشی":"educational","معاون اجرایی":"executive","معاون پرورشی":"cultural","مشاور":"advisor","دبیر":"teacher","معلم":"teacher","دانش‌آموز":"student","ولی":"parent","اولیا":"parent"};
const roles={manager:"مدیریت",educational:"معاون آموزشی",executive:"معاون اجرایی",cultural:"معاون پرورشی",advisor:"مشاوره",teacher:"دبیر",student:"دانش‌آموز",parent:"ولی"};
const role=()=>aliases[String(profile?.role||"student").toLowerCase()]||String(profile?.role||"student");
async function loadCatalog(){catalog=await fetch("../shared/module_catalog.json").then(r=>{if(!r.ok)throw Error("قرارداد ماژول‌ها پیدا نشد.");return r.json()})}
function show(id){["login","dashboard","workspace"].forEach(x=>$(x).classList.toggle("hidden",x!==id))}
function setStatus(t,err=false){$("loginStatus").textContent=t;$("loginStatus").style.color=err?"#ff9d9d":"#7ee2a8"}
function norm(v){return String(v||"").replace(/[۰-۹٠-٩]/g,x=>{const a="۰۱۲۳۴۵۶۷۸۹",b="٠١٢٣٤٥٦٧٨٩";let i=a.indexOf(x);return i>=0?String(i):String(b.indexOf(x))})}
function route(){return location.hash||"#login"}
function navigate(hash){if(location.hash!==hash)location.hash=hash;}
async function refreshSession(){
if(!token)return false;
const r=await fetch(CFG.supabase_url.replace(/\/$/,"")+"/auth/v1/user",{headers:{"apikey":CFG.supabase_publishable_key,"Authorization":"Bearer "+token}});
if(r.ok)return true;
if(refreshToken){
 const rr=await fetch(CFG.supabase_url.replace(/\/$/,"")+"/auth/v1/token?grant_type=refresh_token",{method:"POST",headers:{"apikey":CFG.supabase_publishable_key,"Content-Type":"application/json"},body:JSON.stringify({refresh_token:refreshToken})});
 if(rr.ok){const d=await rr.json();token=d.access_token;refreshToken=d.refresh_token||refreshToken;saveSession();return true;}
}
return false;
}
function requireAuth(){if(!token){show("login");navigate("#login");return false;}return true;}
async function api(path,opt={}){
const h={"apikey":CFG.supabase_publishable_key,"Content-Type":"application/json",...(opt.headers||{})};if(token)h.Authorization="Bearer "+token;
let r=await fetch(CFG.supabase_url.replace(/\/$/,"")+path,{...opt,headers:h});
if(r.status===401&&refreshToken){const rr=await fetch(CFG.supabase_url+"/auth/v1/token?grant_type=refresh_token",{method:"POST",headers:{"apikey":CFG.supabase_publishable_key,"Content-Type":"application/json"},body:JSON.stringify({refresh_token:refreshToken})});if(rr.ok){const d=await rr.json();token=d.access_token;refreshToken=d.refresh_token||refreshToken;saveSession();h.Authorization="Bearer "+token;r=await fetch(CFG.supabase_url.replace(/\/$/,"")+path,{...opt,headers:h})}}
if(!r.ok)throw new Error((await r.text())||("HTTP "+r.status));return r.status===204?null:r.json()
}
function saveSession(){const remember=$("remember")?.checked??true;const store=remember?localStorage:sessionStorage;store.setItem("frahoosh_access_token",token);store.setItem("frahoosh_refresh_token",refreshToken);store.setItem("frahoosh_profile",JSON.stringify(profile))}
async function login(){
const id=norm($("identifier").value).trim(),pw=$("password").value;if(!id||!pw){setStatus("نام کاربری و رمز عبور را وارد کنید.",true);return}
try{setStatus("در حال بررسی اطلاعات...");let email=id;
if(!id.includes("@")){if(!/^\d{10}$/.test(id))throw Error("کد ملی باید ۱۰ رقمی باشد.");const e=await api("/rest/v1/rpc/lookup_auth_email_by_national_code",{method:"POST",body:JSON.stringify({p_national_code:id})});email=Array.isArray(e)?e[0]:e;if(!email)throw Error("برای این کد ملی حساب کاربری پیدا نشد.")}
const d=await fetch(CFG.supabase_url+"/auth/v1/token?grant_type=password",{method:"POST",headers:{"apikey":CFG.supabase_publishable_key,"Content-Type":"application/json"},body:JSON.stringify({email,password:pw})}).then(async r=>{if(!r.ok)throw Error((await r.text())||"ورود ناموفق بود.");return r.json()});
token=d.access_token;refreshToken=d.refresh_token||"";
profile=(await api("/rest/v1/account_settings?email=eq."+encodeURIComponent(email)+"&limit=1"))[0]||{role:"student",display_name:email,username:email,email};saveSession();navigate("#dashboard");renderDashboard()
}catch(e){setStatus(e.message||"ورود انجام نشد.",true)}
}
function allowedPanelKey(){const r=role();return {manager:"management",educational:"educational",executive:"executive",cultural:"cultural",advisor:"advisor",teacher:"teachers",student:"students",parent:"parents"}[r]||r}
function renderDashboard(){if(!requireAuth())return;show("dashboard");$("schoolTitle").textContent=CFG.school_name||"دبیرستان";$("welcome").textContent="خوش آمدید، "+(profile?.display_name||profile?.username||"کاربر فراهوش");const r=role(),k=allowedPanelKey();$("role").textContent="پنل "+(roles[r]||catalog.friendly[k]||"کاربر")+" | دسترسی فعال";$("panels").innerHTML="";const items=catalog.panels[k]||[];const el=document.createElement("button");el.className="panel";el.innerHTML="<b>"+(roles[r]||catalog.friendly[k]||k)+"</b><span>"+items.length+" زیرپنل عملیاتی</span>";el.onclick=()=>openPanel(k);$("panels").appendChild(el)}
function openPanel(key){if(!requireAuth())return;currentPanel=key;navigate("#workspace");currentTable=null;show("workspace");$("workspaceTitle").textContent=panelTitles[key]||roles[key]||catalog.friendly[key]||key;$("workspaceMeta").textContent="محیط عملیاتی مشترک Web و Android • منبع داده: Supabase";renderModules()}
function renderModules(){const items=catalog.panels[currentPanel]||[];$("modules").innerHTML="";items.forEach(([label,table])=>{const b=document.createElement("button");b.className="module"+(table===currentTable?" active":"");b.innerHTML="<b>"+label+"</b><span>"+(catalog.friendly[table]||table)+"</span>";b.onclick=()=>openTable(table);$("modules").appendChild(b)});$("tableArea").innerHTML=""}
async function openTable(table){if(!requireAuth())return;currentTable=table;renderModules();$("tableArea").innerHTML='<div class="table-wrap"><div class="empty">در حال دریافت اطلاعات واقعی...</div></div>';try{rows=await api("/rest/v1/"+encodeURIComponent(table)+"?limit=150");if(!Array.isArray(rows))rows=[];renderTable(rows)}catch(e){$("tableArea").innerHTML='<div class="table-wrap"><div class="empty">دریافت اطلاعات انجام نشد: '+esc(e.message)+'</div></div>'}}
const fieldLabels={national_code:"کد ملی",first_name:"نام",last_name:"نام خانوادگی",full_name:"نام و نام خانوادگی",username:"نام کاربری",email:"ایمیل",phone:"شماره تماس",mobile:"شماره همراه",role:"نقش",status:"وضعیت",gender:"جنسیت",birth_date:"تاریخ تولد",class_name:"کلاس",grade:"پایه",subject:"درس",teacher_name:"نام دبیر",student_name:"نام دانش‌آموز",date:"تاریخ",time:"زمان",description:"توضیحات",title:"عنوان",message:"پیام",score:"نمره",attendance_status:"وضعیت حضور",notes:"توضیحات"};
const fieldLabel=k=>fieldLabels[k]||String(k).replaceAll("_"," ");
const formatCell=v=>v===null||v===undefined||v===""?"—":typeof v==="boolean"?(v?"بله":"خیر"):v;
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
function renderTable(data){const keys=[];data.forEach(r=>Object.keys(r||{}).forEach(k=>{if(!["id","created_at","updated_at","deleted_at"].includes(k)&&!keys.includes(k))keys.push(k)}));let html='<div class="table-wrap"><div class="table-tools"><input id="tableSearch" placeholder="جستجو در همین زیرپنل"><button class="primary" id="reload">تازه‌سازی</button></div>';if(!data.length){html+='<div class="empty">رکوردی برای نمایش وجود ندارد.</div></div>';$("tableArea").innerHTML=html;$("reload").onclick=()=>openTable(currentTable);return}html+='<table class="data-table"><thead><tr>'+keys.map(k=>"<th>"+esc(fieldLabel(k))+"</th>").join("")+'</tr></thead><tbody>'+data.map(r=>"<tr>"+keys.map(k=>"<td>"+esc(formatCell(r[k]))+"</td>").join("")+"</tr>").join("")+'</tbody></table></div>';$("tableArea").innerHTML=html;$("reload").onclick=()=>openTable(currentTable);$("tableSearch").oninput=e=>{const q=e.target.value.toLowerCase();renderTable(rows.filter(r=>JSON.stringify(r).toLowerCase().includes(q)))}
}
$("loginBtn").onclick=login;$("password").addEventListener("keydown",e=>{if(e.key==="Enter")login()});$("forgot").onclick=()=>setStatus("بازیابی رمز باید از مسیر حساب کاربری/ایمیل ثبت‌شده انجام شود.");$("back").onclick=renderDashboard;$("refresh").onclick=()=>currentTable?openTable(currentTable):renderModules();$("logout").onclick=()=>{fetch(CFG.supabase_url.replace(/\/$/,"")+"/auth/v1/logout",{method:"POST",headers:{"apikey":CFG.supabase_publishable_key,"Authorization":"Bearer "+token}}).catch(()=>{});token="";refreshToken="";profile=null;sessionStorage.clear();localStorage.removeItem("frahoosh_access_token");localStorage.removeItem("frahoosh_refresh_token");localStorage.removeItem("frahoosh_profile");show("login");navigate("#login")};
window.addEventListener("hashchange",async()=>{const r=route();if(r!=="#login"&&!await refreshSession()){token="";refreshToken="";profile=null;show("login");navigate("#login");return;}if(r==="#dashboard")renderDashboard();else if(r.startsWith("#workspace"))show("workspace");else show("login")});
(async()=>{try{await loadCatalog();const saved=localStorage.getItem("frahoosh_access_token")||sessionStorage.getItem("frahoosh_access_token");const p=localStorage.getItem("frahoosh_profile")||sessionStorage.getItem("frahoosh_profile");if(saved&&p){token=saved;refreshToken=localStorage.getItem("frahoosh_refresh_token")||sessionStorage.getItem("frahoosh_refresh_token")||"";profile=JSON.parse(p);if(await refreshSession())renderDashboard();else {token="";refreshToken="";profile=null;show("login");navigate("#login")}}else {show("login");navigate("#login")}}catch(e){setStatus("قرارداد مشترک Web بارگذاری نشد.",true)}})();