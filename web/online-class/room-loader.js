(()=>{"use strict";
const $=id=>document.getElementById(id);
function showError(message){const box=$("x");if(box)box.innerHTML=message+"<br><a style=\"display:inline-block;margin-top:18px;padding:12px 18px;background:#155eef;color:white;border-radius:10px;text-decoration:none\" href=\"index.html\">بازگشت به ورود کلاس</a>";}
async function getText(paths,label){let lastError=null;for(const path of paths){const c=new AbortController(),t=setTimeout(()=>c.abort(),12000);try{const u=new URL(path,location.href);u.searchParams.set("_v",Date.now());const r=await fetch(u.href,{cache:"no-store",signal:c.signal});if(!r.ok){const e=new Error(label+" ("+r.status+")");if(r.status===404){lastError=e;continue;}throw e;}return {text:await r.text(),path};}catch(e){if(e&&e.name==="AbortError")throw new Error(label+" — زمان پاسخ تمام شد.");if(/\(404\)/.test(String(e&&e.message||e))){lastError=e;continue;}throw e;}finally{clearTimeout(t);}}throw lastError||new Error(label);}
async function start(){let config=null;for(const store of [sessionStorage,localStorage]){try{config=JSON.parse(store.getItem("frahoosh_online_class_config")||"null")}catch(_){}if(config)break;}
if(!config){showError("نشست کلاس آماده نیست؛ ابتدا از صفحه ورود کلاس وارد شوید.");return;}
if(!config.url||!config.anon||!config.token||!config.classId||!config.userId){showError("اطلاعات نشست کلاس ناقص است؛ از صفحه ورود کلاس دوباره وارد شوید.");return;}
const box=$("x");if(box)box.textContent="در حال بارگذاری محیط کلاس…";
try{const [hr,pr]=await Promise.all([
getText(["/mobile/assets/online_class.html","/online_class_apk/app/src/main/assets/room_assets/online_class.html"],"بارگذاری محیط کلاس ناموفق بود"),
getText(["/online_class_apk/classroom_patch.js","/online_class_apk/app/src/main/assets/room_assets/classroom_patch.js"],"بارگذاری ابزارهای کلاس ناموفق بود")
]);let html=hr.text;if(!html.includes("const C=__CONFIG__;"))throw new Error("نسخه محیط کلاس با پیکربندی فعلی سازگار نیست.");config.guestInviteBase=new URL("index.html",location.href).href;html=html.replace("const C=__CONFIG__;","window.C="+JSON.stringify(config)+";const C=window.C;");const closeScript="</scr"+"ipt>";html=html.replace("</body>","<script>"+pr.text+closeScript+"</body>");const base=document.createElement("base");base.href=new URL(hr.path,location.href).href;html=html.replace(/<head([^>]*)>/i,"<head$1>"+base.outerHTML);document.open();document.write(html);document.close();}catch(e){showError("باز کردن کلاس انجام نشد: "+(e&&e.message?e.message:"خطای ناشناخته"));}}
start();
})();