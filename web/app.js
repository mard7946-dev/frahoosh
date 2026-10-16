const CFG=window.FRAHOOH_CONFIG||{};
const $=id=>document.getElementById(id);
let token=localStorage.getItem("frahoosh_access_token")||sessionStorage.getItem("frahoosh_access_token")||"";
let refreshToken=localStorage.getItem("frahoosh_refresh_token")||sessionStorage.getItem("frahoosh_refresh_token")||"";
let profile=JSON.parse(localStorage.getItem("frahoosh_profile")||sessionStorage.getItem("frahoosh_profile")||"null");
let catalog=null,currentPanel=null,currentTable=null,rows=[],selectedIndex=-1,platformAdmin=false,subscriptionState={expired:false,unknown:true,record:null};
const panelTitles={management:"مدیریت",educational:"معاون آموزشی",executive:"معاون اجرایی",cultural:"معاون پرورشی",advisor:"مشاوره",teachers:"دبیران",students:"دانش‌آموزان",parents:"اولیا",finance:"مالی",online:"کلاس‌های آنلاین",teacher_exams:"آزمون آنلاین",smart_board:"تابلو هوشمند",ai:"هوش مصنوعی",reports:"گزارش‌ها",schedule:"برنامه هفتگی",messages:"صندوق پیام‌ها"};
const aliases={admin:"manager",administrator:"manager","مدیر":"manager","مدیریت":"manager","معاون آموزشی":"educational","معاون اجرایی":"executive","معاون پرورشی":"cultural","مشاور":"advisor","دبیر":"teacher","معلم":"teacher","دانش‌آموز":"student","ولی":"parent","اولیا":"parent"};
const roles={manager:"مدیریت",educational:"معاون آموزشی",executive:"معاون اجرایی",cultural:"معاون پرورشی",advisor:"مشاوره",teacher:"دبیر",student:"دانش‌آموز",parent:"ولی"};
const role=()=>aliases[String(profile?.role||"student").toLowerCase()]||String(profile?.role||"student");
const consumerWrite={student:new Set(["assignment_submissions","school_ally","basij_registration","school_mayor","student_council","certificate_requests"]),parent:new Set(["meeting_requests","parent_meeting_requests","transport_requests","parent_activities"])};
const managerRoles=new Set(["manager","educational","executive","cultural","advisor","teacher"]);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const norm=v=>String(v||"").replace(/[۰-۹٠-٩]/g,x=>{const a="۰۱۲۳۴۵۶۷۸۹",b="٠١٢٣٤٥٦٧٨٩";let i=a.indexOf(x);return i>=0?String(i):String(b.indexOf(x))});
const fieldLabels={national_code:"کد ملی",first_name:"نام",last_name:"نام خانوادگی",full_name:"نام و نام خانوادگی",username:"نام کاربری",email:"ایمیل",phone:"شماره تماس",mobile:"شماره همراه",role:"نقش",status:"وضعیت",gender:"جنسیت",birth_date:"تاریخ تولد",class_name:"کلاس",grade:"پایه",subject:"درس",teacher_name:"نام دبیر",student_name:"نام دانش‌آموز",date:"تاریخ",time:"زمان",description:"توضیحات",title:"عنوان",message:"پیام",score:"نمره",attendance_status:"وضعیت حضور",notes:"توضیحات",amount:"مبلغ",address:"آدرس",reason:"علت/موضوع",target:"مخاطب",tenant_school_id:"شناسه مدرسه",school_id:"شناسه مدرسه",school_code:"کد مدرسه",slug:"شناسه یکتا",plan_id:"طرح اشتراک",plan_code:"کد طرح",duration_months:"مدت اشتراک (ماه)",student_limit:"ظرفیت دانش‌آموز",price_irr:"قیمت (ریال)",grace_days:"مهلت تمدید (روز)",starts_at:"شروع اشتراک",ends_at:"پایان اشتراک",payment_reference:"شناسه پرداخت",owner_auth_user_id:"مدیر مدرسه",auth_user_id:"شناسه حساب کاربری",is_active:"فعال",created_by:"ثبت‌کننده"};
const fieldLabel=k=>fieldLabels[k]||String(k).replaceAll("_"," ");
const ignoredExcelFields=new Set(["id","created_at","updated_at","deleted_at","_auth_user_id"]);
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
 const id=norm($("identifier").value).trim(),pw=$("password").value;
 if(!id||!pw){setStatus("نام کاربری و رمز عبور را وارد کنید.",true);return}
 try{
  setStatus("در حال بررسی اطلاعات...");
  let email=id;
  if(!id.includes("@")){
   if(!/^\d{8,12}$/.test(id))throw Error("نام کاربری باید ۸ تا ۱۲ رقم باشد؛ یا ایمیل ثبت‌شده را وارد کنید.");
   const lookup=await api("/rest/v1/rpc/lookup_auth_email_by_national_code",{method:"POST",body:JSON.stringify({p_national_code:id})});
   email=Array.isArray(lookup)?lookup[0]:lookup;
   if(!email)throw Error("برای این نام کاربری یا کد ملی حساب کاربری پیدا نشد.");
  }
  const d=await fetch(CFG.supabase_url.replace(/\/$/,"")+"/auth/v1/token?grant_type=password",{method:"POST",headers:{"apikey":CFG.supabase_anon_key,"Content-Type":"application/json"},body:JSON.stringify({email,password:pw})}).then(async r=>{if(!r.ok){let message="نام کاربری یا رمز عبور صحیح نیست.";try{const body=await r.json();message=body.msg||body.message||body.error_description||message}catch(_){}throw Error(message)}return r.json()});
  token=d.access_token;refreshToken=d.refresh_token||"";
  let profileRows=await api("/rest/v1/account_settings?select=*&email=eq."+encodeURIComponent(email)+"&limit=1");
  if((!Array.isArray(profileRows)||!profileRows.length)&&d.user?.id){
   profileRows=await api("/rest/v1/account_settings?select=*&auth_user_id=eq."+encodeURIComponent(d.user.id)+"&limit=1");
  }
  profile=Array.isArray(profileRows)&&profileRows[0]?profileRows[0]:{};
  const metadata=d.user?.user_metadata||{};
  profile={...metadata,...profile,email:profile.email||email,auth_user_id:profile.auth_user_id||d.user?.id,username:profile.username||id,display_name:profile.display_name||profile.full_name||profile.name||profile.username||id};
  if(!profile.role)throw Error("ورود تأیید شد، اما نقش حساب از اطلاعات مدرسه دریافت نشد؛ اتصال این حساب به account_settings باید بررسی شود.");
  saveSession();await loadPlatformAdmin();await loadSubscriptionState();renderDashboard();
 }catch(e){setStatus(e.message||"ورود انجام نشد.",true)}
}
async function loadCatalog(){catalog=await fetch("../shared/module_catalog.json").then(r=>{if(!r.ok)throw Error("قرارداد ماژول‌ها پیدا نشد.");return r.json()})}
function show(id){["login","dashboard","workspace"].forEach(x=>$(x).classList.toggle("hidden",x!==id))}
function setStatus(t,err=false){$("loginStatus").textContent=t;$("loginStatus").style.color=err?"#ff9d9d":"#7ee2a8"}
function allowedPanels(){
 const r=role();
 if(subscriptionState.expired&&!platformAdmin)return ["management"];
 if(r==="manager")return Object.keys(catalog.panels||{});
 const map={educational:["educational"],executive:["executive"],cultural:["cultural"],advisor:["advisor"],teacher:["teachers"],student:["students"],parent:["parents"]};
 return map[r]||[];
}
function renderDashboard(){
 show("dashboard");$("schoolTitle").textContent=CFG.school_name||"دبیرستان";$("welcome").textContent="خوش آمدید، "+(profile?.display_name||profile?.username||"کاربر");
 const r=role();$("role").textContent="پنل "+(roles[r]||r)+(subscriptionState.expired&&!platformAdmin?" | اشتراک منقضی شده":" | دسترسی فعال");$("status").textContent=subscriptionState.expired&&!platformAdmin?"اشتراک مدرسه پایان یافته است؛ بخش‌های آموزشی تا تمدید اشتراک قفل هستند. از بخش «اشتراک مدارس» وضعیت را ببینید.":subscriptionState.unknown?"وضعیت اشتراک هنوز قابل تأیید نیست.":subscriptionState.record?"پایان اشتراک: "+new Date(subscriptionState.record.ends_at).toLocaleDateString("fa-IR")+" | ظرفیت: "+subscriptionState.record.student_limit+" دانش‌آموز":"";$("status").style.color=subscriptionState.expired&&!platformAdmin?"#b42318":"#66758b";$("panels").innerHTML="";
 allowedPanels().forEach(k=>{const items=catalog.panels[k]||[],el=document.createElement("button");el.className="panel";el.innerHTML="<b>"+esc(panelTitles[k]||catalog.friendly?.[k]||k)+"</b><span>"+items.length+" زیرپنل عملیاتی</span>";el.onclick=()=>openPanel(k);$("panels").appendChild(el)});
}
function canWrite(table){
 const r=role();
 // Student and teacher directory edits are reserved for the school manager.
 // Supabase RLS remains the final authorization boundary.
 if(table==="students"||table==="teachers")return r==="manager";
 if(["schools","subscription_plans","school_subscriptions"].includes(table))return platformAdmin;
 if(table==="school_memberships")return platformAdmin||r==="manager";
 // Only the school manager can assign or change school roles; RLS remains the final authority.
 if(table==="account_settings")return r==="manager"||platformAdmin;
 if(r==="manager"||managerRoles.has(r))return true;
 return !!consumerWrite[r]?.has(table);
}
function specialViewOnly(table){return (role()==="student"||role()==="parent")&&!canWrite(table)}
const meetingTables=new Set(["meeting_requests","parent_meeting_requests","teacher_meetings","meetings"]);
async function loadPlatformAdmin(){
 platformAdmin=false;
 const uid=profile?.auth_user_id;
 if(!uid)return;
 try{const rows=await api("/rest/v1/platform_admins?auth_user_id=eq."+encodeURIComponent(uid)+"&select=auth_user_id&limit=1");platformAdmin=Array.isArray(rows)&&rows.length>0}catch(e){platformAdmin=false}
}
async function loadSubscriptionState(){
 subscriptionState={expired:false,unknown:true,record:null};
 try{
  let schoolId=profile?.tenant_school_id;
  if(!schoolId&&profile?.auth_user_id){const a=await api("/rest/v1/account_settings?auth_user_id=eq."+encodeURIComponent(profile.auth_user_id)+"&select=tenant_school_id&limit=1");schoolId=a?.[0]?.tenant_school_id; if(schoolId)profile.tenant_school_id=schoolId}
  if(!schoolId)return;
  const results=await Promise.all([
   api("/rest/v1/school_subscriptions?school_id=eq."+encodeURIComponent(schoolId)+"&select=status,starts_at,ends_at,grace_days,student_limit&order=ends_at.desc&limit=1"),
   api("/rest/v1/schools?id=eq."+encodeURIComponent(schoolId)+"&select=status&limit=1")
  ]);
  const rows=results[0],schoolRows=results[1];
  const record=Array.isArray(rows)&&rows.length?rows[0]:null;
  if(!record){subscriptionState={expired:true,unknown:false,record:null};return}
  const deadline=new Date(record.ends_at).getTime()+Math.max(0,Number(record.grace_days)||0)*86400000;
  const schoolActive=Array.isArray(schoolRows)&&schoolRows.length>0&&schoolRows[0].status==="active";
  const startAt=new Date(record.starts_at||0).getTime();const active=schoolActive&&["active","past_due"].includes(String(record.status||"").toLowerCase())&&Number.isFinite(startAt)&&Date.now()>=startAt&&Number.isFinite(deadline)&&Date.now()<=deadline;
  subscriptionState={expired:!active,unknown:false,record};
 }catch(e){subscriptionState={expired:false,unknown:true,record:null}}
}
function openPanel(key){currentPanel=key;currentTable=null;selectedIndex=-1;show("workspace");$("workspaceTitle").textContent=panelTitles[key]||catalog.friendly?.[key]||key;$("workspaceMeta").textContent="محیط عملیاتی مشترک Web و Android • منبع داده: Supabase";renderModules()}
function renderModules(){
 let items=catalog.panels[currentPanel]||[];if(currentPanel==="management"&&subscriptionState.expired&&!platformAdmin)items=items.filter(([,table])=>["schools","subscription_plans","school_subscriptions"].includes(table));$("modules").innerHTML="";const excelAllowed=managerRoles.has(role());
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

function localDateTimeValue(d){const x=new Date(d.getTime()-d.getTimezoneOffset()*60000);return x.toISOString().slice(0,16)}
async function renderSubscriptionWorkspace(){
 const area=$("tableArea");
 area.innerHTML='<div class="table-wrap"><div class="empty">در حال بارگذاری اطلاعات اشتراک...</div></div>';
 try{
  const results=await Promise.all([
   api("/rest/v1/schools?select=id,slug,name,school_code,owner_auth_user_id,status,created_at&order=created_at.desc&limit=300"),
   api("/rest/v1/subscription_plans?select=id,plan_code,name,duration_months,student_min,student_limit,price_irr,is_active&is_active=eq.true&order=duration_months.asc&limit=200"),
   api("/rest/v1/school_subscriptions?select=id,school_id,plan_id,duration_months,student_min,student_limit,price_irr,starts_at,ends_at,grace_days,status,payment_reference,created_at&order=created_at.desc&limit=300")
  ]);
  const schools=Array.isArray(results[0])?results[0]:[];
  const plans=Array.isArray(results[1])?results[1]:[];
  const subscriptions=Array.isArray(results[2])?results[2]:[];
  const schoolMap=Object.fromEntries(schools.map(x=>[x.id,x]));
  const planMap=Object.fromEntries(plans.map(x=>[x.id,x]));
  let html='<div class="table-wrap"><h3>مدیریت اشتراک مدارس</h3><p class="crud-hint">هر مدرسه شناسه و ظرفیت مستقل دارد. پس از پایان اشتراک، دسترسی عملیاتی از سمت پایگاه داده محدود می‌شود و اطلاعات حذف نمی‌شود.</p>';
  if(platformAdmin){
   html+='<section class="subscription-admin-card"><h4>تعرفه طرح‌های اشتراک</h4><p class="crud-hint">قیمت‌ها عمداً از پیش تعیین نشده‌اند؛ برای هر ترکیب مدت و ظرفیت، قیمت را به ریال وارد و ذخیره کنید.</p><div class="table-wrap"><table class="data-table"><thead><tr><th>مدت (ماه)</th><th>ظرفیت دانش‌آموز</th><th>قیمت (ریال)</th><th>عملیات</th></tr></thead><tbody>'+plans.map(p=>'<tr><td>'+Number(p.duration_months).toLocaleString("fa-IR")+'</td><td>'+Number(p.student_min).toLocaleString("fa-IR")+' تا '+Number(p.student_limit).toLocaleString("fa-IR")+'</td><td><input type="number" min="0" step="1000" data-plan-price="'+esc(p.id)+'" value="'+Number(p.price_irr||0)+'" aria-label="قیمت طرح"></td><td><button type="button" data-save-plan="'+esc(p.id)+'">ذخیره قیمت</button></td></tr>').join("")+'</tbody></table></div><div class="message" id="subPlanPriceStatus"></div></section>';
   html+='<section class="subscription-admin-card"><h4>ثبت مدرسه جدید</h4><div class="form-grid"><label>نام مدرسه<input id="subSchoolName" required placeholder="نام کامل مدرسه"></label><label>شناسه یکتا (لاتین)<input id="subSchoolSlug" required placeholder="school-city-01"></label><label>کد مدرسه (اختیاری)<input id="subSchoolCode" placeholder="کد مدرسه"></label><label>شناسه حساب مدیر (اختیاری)<input id="subOwnerId" placeholder="UUID حساب Auth موجود"></label><label>ایمیل مدیر (برای ایجاد پیوند حساب)<input id="subOwnerEmail" type="email" placeholder="manager@example.com"></label></div><button class="primary" id="subCreateSchool">ثبت مدرسه</button><div class="message" id="subSchoolStatus"></div></section>';
   html+='<section class="subscription-admin-card"><h4>فعال‌سازی یا تمدید اشتراک</h4><div class="form-grid"><label>مدرسه<select id="subTargetSchool"><option value="">انتخاب مدرسه</option>'+schools.map(x=>'<option value="'+esc(x.id)+'">'+esc(x.name)+' — '+esc(x.slug)+'</option>').join("")+'</select></label><label>طرح اشتراک<select id="subPlan"><option value="">انتخاب مدت و ظرفیت</option>'+plans.map(x=>'<option value="'+esc(x.id)+'">'+esc(x.name)+' | '+(Number(x.price_irr||0)>0?Number(x.price_irr).toLocaleString("fa-IR")+' ریال':'قیمت تعیین نشده')+'</option>').join("")+'</select></label><label>شروع اشتراک<input id="subStart" type="datetime-local" value="'+localDateTimeValue(new Date())+'"></label><label>مهلت تمدید<select id="subGrace"><option value="0">بدون مهلت اضافی</option><option value="3">۳ روز</option><option value="7">۷ روز</option><option value="15">۱۵ روز</option></select></label></div><button class="primary" id="subActivate">فعال‌سازی / تمدید اشتراک</button><div class="message" id="subPlanStatus"></div></section>';
  }
  html+='<h4>فهرست اشتراک‌ها</h4>';
  if(!subscriptions.length)html+='<div class="empty">اشتراکی برای نمایش وجود ندارد.</div>';
  else html+='<div class="table-wrap"><table class="data-table"><thead><tr><th>مدرسه</th><th>طرح</th><th>شروع</th><th>پایان</th><th>ظرفیت</th><th>قیمت (ریال)</th><th>وضعیت</th></tr></thead><tbody>'+subscriptions.map(x=>{
   const school=schoolMap[x.school_id]||{},plan=planMap[x.plan_id]||{};
   const deadline=new Date(x.ends_at).getTime()+Math.max(0,Number(x.grace_days)||0)*86400000;
   const active=["active","past_due"].includes(String(x.status||"").toLowerCase())&&Number.isFinite(deadline)&&Date.now()<=deadline&&school.status!=="suspended";
   return '<tr><td>'+esc(school.name||x.school_id)+'</td><td>'+esc(plan.name||("اشتراک "+Number(x.duration_months||0)+" ماهه"))+'</td><td>'+esc(new Date(x.starts_at).toLocaleDateString("fa-IR"))+'</td><td>'+esc(new Date(x.ends_at).toLocaleDateString("fa-IR"))+'</td><td>'+Number(x.student_min||1).toLocaleString("fa-IR")+' تا '+Number(x.student_limit||0).toLocaleString("fa-IR")+'</td><td>'+(Number(x.price_irr||0)>0?Number(x.price_irr).toLocaleString("fa-IR")+' ریال':'تعیین نشده')+'</td><td>'+(active?'<span class="status-active">فعال</span>':'<span class="status-expired">منقضی / متوقف</span>')+'</td></tr>';
  }).join("")+'</tbody></table></div>';
  html+='</div>';
  area.innerHTML=html;
  if(platformAdmin){
   area.querySelectorAll("[data-save-plan]").forEach(button=>button.onclick=async()=>{
    const planId=button.getAttribute("data-save-plan"),input=area.querySelector('[data-plan-price="'+planId+'"]'),price=Number(input?.value),status=$("subPlanPriceStatus");
    if(!Number.isSafeInteger(price)||price<0){status.textContent="قیمت باید عدد صحیح و نامنفی به ریال باشد.";return}
    button.disabled=true;
    try{
     await api("/rest/v1/subscription_plans?id=eq."+encodeURIComponent(planId),{method:"PATCH",headers:{"Prefer":"return=minimal"},body:JSON.stringify({price_irr:price,updated_at:new Date().toISOString()})});
     status.textContent="قیمت طرح ذخیره شد.";
    }catch(e){status.textContent="ذخیره قیمت انجام نشد: "+(e.message||e)}
    finally{button.disabled=false}
   });
   $("subCreateSchool").onclick=async()=>{
    const name=$("subSchoolName").value.trim(),slug=$("subSchoolSlug").value.trim().toLowerCase(),code=$("subSchoolCode").value.trim();let ownerId=$("subOwnerId").value.trim();const ownerEmail=$("subOwnerEmail").value.trim();
    const status=$("subSchoolStatus");
    if(!name||!slug){status.textContent="نام مدرسه و شناسه یکتا الزامی است.";return}
    if(!/^[a-z0-9][a-z0-9-]{2,62}$/.test(slug)){status.textContent="شناسه یکتا باید لاتین، بدون فاصله و شامل حروف کوچک، عدد یا خط تیره باشد.";return}
    if(!ownerId&&!ownerEmail){status.textContent="برای جلوگیری از ساخت مدرسه بدون مدیر، شناسه حساب Auth یا ایمیل مدیر موجود را وارد کنید.";return}
    try{
     let ownerAccount=null;
     if(ownerId){
      const matches=await api("/rest/v1/account_settings?auth_user_id=eq."+encodeURIComponent(ownerId)+"&select=username,email,auth_user_id&limit=1");
      ownerAccount=matches?.[0]||null;
     }else if(ownerEmail){
      const matches=await api("/rest/v1/account_settings?email=eq."+encodeURIComponent(ownerEmail)+"&select=username,email,auth_user_id&limit=1");
      ownerAccount=matches?.[0]||null;
      ownerId=ownerAccount?.auth_user_id||"";
     }
     if(!ownerId||(!ownerAccount&&!ownerEmail))throw Error("مدیر باید حساب Auth موجود داشته باشد. ابتدا حساب را بسازید و سپس شناسه یا ایمیل آن را وارد کنید.");
     const payload={name,slug,status:"active",owner_auth_user_id:ownerId};
     if(code)payload.school_code=code;
     if(ownerId)payload.owner_auth_user_id=ownerId;
     const created=await api("/rest/v1/schools",{method:"POST",headers:{"Prefer":"return=representation"},body:JSON.stringify(payload)});
     const school=Array.isArray(created)?created[0]:created;
     if(ownerId){
      const existing=await api("/rest/v1/account_settings?auth_user_id=eq."+encodeURIComponent(ownerId)+"&select=username,email&limit=1");
      if(existing.length){
       await api("/rest/v1/account_settings?auth_user_id=eq."+encodeURIComponent(ownerId),{method:"PATCH",headers:{"Prefer":"return=minimal"},body:JSON.stringify({tenant_school_id:school.id,role:"manager"})});
      }else if(ownerEmail){
       await api("/rest/v1/account_settings",{method:"POST",headers:{"Prefer":"return=minimal"},body:JSON.stringify({username:ownerEmail,email:ownerEmail,display_name:"مدیر مدرسه",role:"manager",auth_user_id:ownerId,tenant_school_id:school.id})});
      }else{
       throw Error("مدرسه ثبت شد، اما حساب مدیر به‌علت نبود رکورد account_settings متصل نشد. ایمیل مدیر را وارد کنید تا پیوند حساب تکمیل شود.");
      }
     }
     status.textContent="مدرسه ثبت شد. اکنون از بخش فعال‌سازی اشتراک، طرح و ظرفیت را انتخاب کنید.";
     $("subSchoolName").value="";$("subSchoolSlug").value="";$("subSchoolCode").value="";$("subOwnerId").value="";$("subOwnerEmail").value="";
     await renderSubscriptionWorkspace();
    }catch(e){status.textContent="ثبت مدرسه کامل نشد: "+(e.message||e)}
   };
   $("subActivate").onclick=async()=>{
    const schoolId=$("subTargetSchool").value,planId=$("subPlan").value,startValue=$("subStart").value,grace=Number($("subGrace").value||0),status=$("subPlanStatus");
    if(!schoolId||!planId){status.textContent="مدرسه و طرح اشتراک را انتخاب کنید.";return}
    const plan=plans.find(p=>p.id===planId);if(!plan){status.textContent="طرح اشتراک پیدا نشد.";return}if(Number(plan.price_irr||0)<=0){status.textContent="قیمت این طرح هنوز تعیین نشده است؛ ابتدا در بخش «طرح‌های اشتراک» قیمت را ثبت کنید.";return}
    const start=startValue?new Date(startValue):new Date();
    if(!Number.isFinite(start.getTime())){status.textContent="زمان شروع معتبر نیست.";return}
    const end=new Date(start.getTime());const dayOfMonth=end.getDate();end.setDate(1);end.setMonth(end.getMonth()+Number(plan.duration_months));end.setDate(Math.min(dayOfMonth,new Date(end.getFullYear(),end.getMonth()+1,0).getDate()));
    try{
     await api("/rest/v1/school_subscriptions",{method:"POST",headers:{"Prefer":"return=minimal"},body:JSON.stringify({school_id:schoolId,plan_id:planId,starts_at:start.toISOString(),ends_at:end.toISOString(),grace_days:grace,status:"active",created_by:profile?.auth_user_id||null})});
     status.textContent="اشتراک ثبت شد و محدودیت ظرفیت از سمت پایگاه داده اعمال می‌شود.";
     await loadSubscriptionState();await renderSubscriptionWorkspace();
    }catch(e){status.textContent="ثبت اشتراک انجام نشد: "+(e.message||e)}
   };
  }
 }catch(e){area.innerHTML='<div class="table-wrap"><div class="empty">بارگذاری اشتراک‌ها انجام نشد: '+esc(e.message||e)+'</div></div>'}
}

async function openTable(table){
 currentTable=table;selectedIndex=-1;renderModules();if(table==="school_subscriptions"){await renderSubscriptionWorkspace();return true}$("tableArea").innerHTML='<div class="table-wrap"><div class="empty">در حال دریافت اطلاعات واقعی...</div></div>';
 try{
  rows=await api("/rest/v1/"+encodeURIComponent(table)+"?select=*&limit=300");
  if(!Array.isArray(rows))rows=[];
  if(table==="users"){
   try{
    const accounts=await api("/rest/v1/account_settings?select=username,email,national_code,auth_user_id&limit=1000");
    const byKey=new Map();
    (Array.isArray(accounts)?accounts:[]).forEach(a=>{
     if(!a.auth_user_id)return;
     [a.username,a.email,a.national_code].filter(Boolean).forEach(k=>byKey.set(String(k).trim().toLowerCase(),a.auth_user_id));
    });
    rows=rows.map(r=>({...r,_auth_user_id:byKey.get(String(r.username||"").trim().toLowerCase())||byKey.get(String(r.email||"").trim().toLowerCase())||byKey.get(String(r.national_code||"").trim().toLowerCase())||null}));
   }catch(e){rows=rows.map(r=>({...r,_auth_user_id:null}))}
  }
  renderTable(rows);return true
}
 catch(e){rows=[];$("tableArea").innerHTML='<div class="table-wrap"><div class="empty">دریافت اطلاعات انجام نشد: '+esc(e.message)+'</div></div>';return false}
}
function tableKeys(data){const keys=[];const showIds=["schools","subscription_plans","school_subscriptions","school_memberships"].includes(currentTable);data.forEach(r=>Object.keys(r||{}).forEach(k=>{if((!ignoredExcelFields.has(k)||(showIds&&k==="id"))&&!keys.includes(k))keys.push(k)}));return keys}
function renderTable(data){
 const keys=tableKeys(data),write=canWrite(currentTable),viewOnly=specialViewOnly(currentTable);
 const rowActions=write&&!viewOnly&&["students","teachers"].includes(currentTable);
 const authDeleteActions=write&&!viewOnly&&["users","account_settings"].includes(currentTable);
 let html='<div class="table-wrap"><div class="table-tools"><input id="tableSearch" placeholder="جستجو در همین زیرپنل"><button class="primary" id="reload">تازه‌سازی</button>';
 if(write&&!viewOnly){const meeting=meetingTables.has(currentTable);html+='<button id="addRow">ثبت</button>';if(!rowActions)html+='<button id="editRow">ویرایش</button><button class="danger" id="deleteRow">حذف</button>';if(!meeting)html+='<button id="importExcel">ورودی اکسل</button><button id="exportExcel">خروجی اکسل</button><button id="exportPdf">خروجی PDF</button>';}
 html+='</div><div class="crud-hint">'+(write&&!viewOnly?"یک ردیف را انتخاب کنید؛ سپس ویرایش یا حذف را بزنید.":"این زیرپنل برای این نقش فقط قابل مشاهده است.")+'</div>';
 if(!data.length){html+='<div class="empty">رکوردی برای نمایش وجود ندارد.</div></div>';$("tableArea").innerHTML=html;bindTools();return}
 html+='<table class="data-table"><thead><tr><th>انتخاب</th>'+(rowActions?'<th>عملیات</th>':'')+keys.map(k=>"<th>"+esc(fieldLabel(k))+"</th>").join("")+'</tr></thead><tbody>'+data.map((r,i)=>"<tr data-index=\""+i+"\"><td><input type=\"radio\" name=\"rowpick\" value=\""+i+"\" "+(selectedIndex>=0&&rows[selectedIndex]&&String(rows[selectedIndex].id)===String(r.id)?"checked":"")+"></td>"+(rowActions?'<td><button type="button" data-row-edit="'+esc(r.id)+'">ویرایش</button><button type="button" class="danger" data-row-delete="'+esc(r.id)+'">حذف</button></td>':"")+keys.map(k=>"<td>"+esc(r[k]===null||r[k]===undefined||r[k]===""?"—":r[k])+"</td>").join("")+"</tr>").join("")+'</tbody></table></div>';
 $("tableArea").innerHTML=html;
 if(authDeleteActions){
  const table=$("tableArea").querySelector("table.data-table");
  const head=table?.querySelector("thead tr");
  if(head){const th=document.createElement("th");th.textContent="عملیات";head.appendChild(th)}
  table?.querySelectorAll("tbody tr").forEach(tr=>{
   const row=data[Number(tr.dataset.index)];const td=document.createElement("td");
   const authUserId=row?._auth_user_id||row?.auth_user_id;if(authUserId){const button=document.createElement("button");button.type="button";button.className="danger";button.textContent="حذف حساب Supabase";button.dataset.authUserDelete=String(authUserId);td.appendChild(button)}
   else td.textContent="حساب Auth متصل نیست";
   tr.appendChild(td);
  });
 }
 $("tableArea").querySelectorAll("input[name=rowpick]").forEach(x=>x.onchange=()=>{const picked=data[Number(x.value)];selectedIndex=picked?rows.findIndex(r=>String(r.id)===String(picked.id)):-1});
 $("tableArea").querySelectorAll("[data-row-edit]").forEach(button=>button.onclick=()=>{const row=data.find(r=>String(r.id)===button.dataset.rowEdit);if(!row){alert("رکورد برای ویرایش پیدا نشد.");return}selectedIndex=rows.findIndex(r=>String(r.id)===String(row.id));openEditor(row)});
 $("tableArea").querySelectorAll("[data-row-delete]").forEach(button=>button.onclick=()=>{const row=data.find(r=>String(r.id)===button.dataset.rowDelete);if(!row){alert("رکورد برای حذف پیدا نشد.");return}deleteRecord(row)});
 $("tableArea").querySelectorAll("[data-auth-user-delete]").forEach(button=>button.onclick=()=>{const row=data.find(r=>String(r._auth_user_id||r.auth_user_id)===button.dataset.authUserDelete);if(!row){alert("حساب کاربری برای حذف پیدا نشد.");return}deleteAuthUser(row)});
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
 const spec=catalog?.modules?.[currentTable];
 const configured=Array.isArray(spec?.fields)?spec.fields:[];
 const existing=tableKeys([row||{}]).filter(k=>k!=="id");
 const keys=[...new Set([...configured,...existing])].filter(k=>!ignoredExcelFields.has(k)&&k!=="id"&&k!=="tenant_school_id");
 return keys.map(k=>{
  const value=row?.[k]??"";
  const numeric=["id","student_id","teacher_id","parent_id","class_id","assignment_id","exam_id","activity_id","children_count","teaching_hours","duration","duration_months","student_limit","grace_days","amount","price_irr","score","max_score","coefficient","quantity","fixed_amount"].includes(k);
  const multiline=["description","content","answer_text","message","note","executive_note","report","reason"].includes(k);
  const input=multiline
   ? '<textarea data-field="'+esc(k)+'" rows="3">'+esc(value)+'</textarea>'
   : '<input data-field="'+esc(k)+'" type="'+(numeric?"number":"text")+'" value="'+esc(value)+'">';
  return '<label>'+esc(fieldLabel(k))+input+'</label>';
 }).join("");
}
function openEditor(rowOverride){
 const row=arguments.length?rowOverride:(selectedIndex>=0?rows[selectedIndex]:null);
 const wrap=document.createElement("div");wrap.className="modal";wrap.innerHTML='<div class="modal-card"><h3>'+(row?"ویرایش رکورد":"ثبت رکورد")+'</h3><div class="form-grid">'+editorFields(row)+'</div><div class="modal-actions"><button id="saveRecord" class="primary">ذخیره</button><button id="cancelRecord" class="secondary">انصراف</button></div></div>';document.body.appendChild(wrap);
 $("cancelRecord").onclick=()=>wrap.remove();
 $("saveRecord").onclick=async()=>{const payload={};wrap.querySelectorAll("[data-field]").forEach(i=>{if(i.value!=="")payload[i.dataset.field]=i.type==="number"?Number(i.value):i.value});try{
 const spec=catalog?.modules?.[currentTable];
 const required=(spec?.fields||[]).filter(k=>currentTable==="online_classes"&&k==="title");
 const missing=required.filter(k=>payload[k]===undefined||payload[k]===null||payload[k]==="");
 if(missing.length)throw Error("فیلدهای الزامی را وارد کنید: "+missing.map(fieldLabel).join("، "));
if(row){const id=row.id;if(id===undefined||id===null)throw Error("این رکورد شناسه قابل ویرایش ندارد.");await api("/rest/v1/"+encodeURIComponent(currentTable)+"?id=eq."+encodeURIComponent(id),{method:"PATCH",headers:{"Prefer":"return=minimal"},body:JSON.stringify(payload)})}else await api("/rest/v1/"+encodeURIComponent(currentTable),{method:"POST",headers:{"Prefer":"return=minimal"},body:JSON.stringify(payload)});wrap.remove();selectedIndex=-1;await openTable(currentTable)}catch(e){alert("ذخیره انجام نشد: "+e.message)}};
}
async function deleteAuthUser(row){
 if(role()!=="manager"&&!platformAdmin){alert("فقط مدیر مجاز به حذف حساب کاربری است.");return}
 if(!row||!row.auth_user_id){alert("این رکورد به حساب احراز هویت Supabase متصل نیست.");return}
 if(!confirm("حساب ورود Supabase این کاربر حذف شود؟ این کاربر دیگر نمی‌تواند وارد سامانه شود. اطلاعات دانش‌آموز/دبیر به‌صورت جداگانه حذف نمی‌شود."))return;
 try{
  const response=await fetch(CFG.supabase_url+"/functions/v1/admin-delete-user",{method:"POST",headers:{"apikey":CFG.supabase_anon_key,"Authorization":"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({auth_user_id:row.auth_user_id})});
  const result=await response.json().catch(()=>({}));
  if(!response.ok)throw Error(result.error||("HTTP "+response.status));
  selectedIndex=-1;alert(result.message||"حساب ورود Supabase حذف شد.");await openTable(currentTable);
 }catch(e){alert("حذف حساب Supabase انجام نشد: "+(e.message||e))}
}
async function deleteSelected(){
 if(selectedIndex<0){alert("ابتدا یک ردیف را انتخاب کنید.");return}
 return deleteRecord(rows[selectedIndex]);
}
async function deleteRecord(row){
 if(!row){alert("رکورد برای حذف پیدا نشد.");return}
 if(row.id===undefined||row.id===null){alert("این رکورد شناسه قابل حذف ندارد.");return}
 if(!confirm("این رکورد حذف شود؟"))return;
 try{const deleted=await api("/rest/v1/"+encodeURIComponent(currentTable)+"?id=eq."+encodeURIComponent(row.id),{method:"DELETE",headers:{"Prefer":"return=representation"}});if(!Array.isArray(deleted)||deleted.length===0)throw Error("هیچ رکوردی حذف نشد. احتمالاً دسترسی حذف در Supabase مجاز نیست یا رکورد تغییر کرده است؛ فهرست را تازه‌سازی و سیاست‌های دسترسی را بررسی کنید.");selectedIndex=-1;await openTable(currentTable)}catch(e){alert("حذف انجام نشد: "+e.message)}
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
(async()=>{try{await loadCatalog();const saved=localStorage.getItem("frahoosh_access_token")||sessionStorage.getItem("frahoosh_access_token"),p=localStorage.getItem("frahoosh_profile")||sessionStorage.getItem("frahoosh_profile");if(saved&&p){token=saved;profile=JSON.parse(p);await loadPlatformAdmin();await loadSubscriptionState();renderDashboard()}else show("login")}catch(e){setStatus("قرارداد مشترک Web بارگذاری نشد.",true)}})();