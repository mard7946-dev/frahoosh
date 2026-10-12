(()=>{"use strict";
const $=id=>document.getElementById(id);
function showError(message){
 const box=$("x");
 if(box) box.innerHTML=message+"<br><a style=\"display:inline-block;margin-top:18px;padding:12px 18px;background:#155eef;color:white;border-radius:10px;text-decoration:none\" href=\"/online-class/index.html\">بازگشت به ورود کلاس</a>";
}
async function getText(path,label){
 const response=await fetch(path,{cache:"no-store"});
 if(!response.ok) throw new Error(label+" ("+response.status+")");
 return response.text();
}
async function start(){
 let config=null;
 try{config=JSON.parse(sessionStorage.getItem("frahoosh_online_class_config")||"null")}catch(_){}
 if(!config){try{config=JSON.parse(localStorage.getItem("frahoosh_online_class_config")||"null")}catch(_){}}
 if(!config){showError("نشست کلاس آماده نیست؛ ابتدا از صفحه ورود، میزبان یا میهمان وارد شوید.");return;}
 try{
  let [html,patch]=await Promise.all([
   getText("/mobile/assets/online_class.html","بارگذاری محیط کلاس ناموفق بود"),
   getText("/online_class_apk/classroom_patch.js","بارگذاری کنترل‌های کلاس ناموفق بود")
  ]);
  if(!html.includes("const C=__CONFIG__;")) throw new Error("جایگاه تنظیمات محیط کلاس در فایل پیدا نشد.");
  html=html.replace("const C=__CONFIG__;","const C="+JSON.stringify(config)+";");
  const patchTag="<script>"+patch+"</scr"+"ipt>";
  if(html.includes("</body>")) html=html.replace("</body>",patchTag+"</body>");
  else html+=patchTag;
  document.open();
  document.write(html);
  document.close();
 }catch(error){
  showError("باز کردن کلاس انجام نشد: "+(error&&error.message?error.message:"خطای ناشناخته"));
 }
}
start();
})();