import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const respond = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });
const text = (v: unknown) => String(v ?? "").trim();
const normRole = (v: unknown) => text(v).toLowerCase();

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return respond({ error: "فقط درخواست POST پذیرفته می‌شود." }, 405);

  const authHeader = req.headers.get("Authorization") ?? "";
  if (!authHeader.startsWith("Bearer ")) return respond({ error: "برای حذف حساب باید وارد شده باشید." }, 401);

  const url = Deno.env.get("SUPABASE_URL") ?? "";
  let serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  const secretBundle = Deno.env.get("SUPABASE_SECRET_KEYS") ?? "";
  if (secretBundle) {
    try { serviceKey = JSON.parse(secretBundle).default ?? serviceKey; } catch (_) {}
  }
  if (!url || !serviceKey) return respond({ error: "تنظیمات امن سرویس حذف حساب کامل نیست." }, 500);

  const admin = createClient(url, serviceKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: authData, error: authError } = await admin.auth.getUser(authHeader.slice(7));
  if (authError || !authData.user) return respond({ error: "نشست ورود معتبر نیست؛ دوباره وارد شوید." }, 401);

  const callerId = authData.user.id;
  const { data: caller, error: callerError } = await admin
    .from("account_settings")
    .select("role,tenant_school_id")
    .eq("auth_user_id", callerId)
    .maybeSingle();
  if (callerError) return respond({ error: "بررسی نقش و مدرسه مدیر ناموفق بود." }, 500);

  const { data: platformRow, error: platformError } = await admin
    .from("platform_admins")
    .select("auth_user_id")
    .eq("auth_user_id", callerId)
    .maybeSingle();
  if (platformError) return respond({ error: "بررسی دسترسی مدیر سامانه ناموفق بود." }, 500);
  const isPlatformAdmin = !!platformRow;
  const callerRole = normRole(caller?.role);
  const managerRoles = ["manager", "مدیر", "مدیریت", "principal", "administrator", "admin"];
  if (!isPlatformAdmin && !managerRoles.includes(callerRole)) {
    return respond({ error: "فقط مدیر مدرسه اجازه حذف حساب کاربری را دارد." }, 403);
  }

  const body = await req.json().catch(() => ({}));
  const targetId = text(body.auth_user_id);
  if (!targetId) return respond({ error: "شناسه حساب کاربری الزامی است." }, 400);
  if (targetId === callerId) return respond({ error: "حذف حسابی که با آن وارد شده‌اید مجاز نیست." }, 400);

  const { data: target, error: targetError } = await admin
    .from("account_settings")
    .select("auth_user_id,tenant_school_id,role,username")
    .eq("auth_user_id", targetId)
    .maybeSingle();
  if (targetError) return respond({ error: "حساب هدف بررسی نشد." }, 500);
  if (!target) return respond({ error: "رکورد حساب کاربری پیدا نشد." }, 404);

  if (!isPlatformAdmin) {
    if (!caller?.tenant_school_id || target.tenant_school_id !== caller.tenant_school_id) {
      return respond({ error: "حذف فقط برای کاربران همین مدرسه مجاز است؛ شناسه مدرسه حساب‌ها باید مشخص و یکسان باشد." }, 403);
    }
    if (managerRoles.includes(normRole(target.role))) {
      return respond({ error: "مدیر مدرسه نمی‌تواند حساب مدیریتی را از این بخش حذف کند." }, 403);
    }
  }

  const { data: targetPlatform, error: targetPlatformError } = await admin
    .from("platform_admins")
    .select("auth_user_id")
    .eq("auth_user_id", targetId)
    .maybeSingle();
  if (targetPlatformError) return respond({ error: "بررسی حساب مدیر سامانه هدف ناموفق بود." }, 500);
  if (targetPlatform) return respond({ error: "حذف حساب مدیر سامانه از این بخش مجاز نیست." }, 403);

  const { error: deleteError } = await admin.auth.admin.deleteUser(targetId);
  if (deleteError) return respond({ error: "حذف حساب احراز هویت ناموفق بود: " + deleteError.message }, 400);

  // Auth deletion may cascade to this row depending on the configured FK.
  // Remove any remaining account mapping without touching student/teacher records.
  const { error: profileDeleteError } = await admin
    .from("account_settings")
    .delete()
    .eq("auth_user_id", targetId);
  if (profileDeleteError) {
    return respond({
      success: true,
      partial: true,
      message: "حساب ورود حذف شد، اما پاک‌سازی رکورد account_settings کامل نشد؛ بررسی پایگاه داده لازم است.",
    }, 200);
  }

  return respond({ success: true, message: "حساب ورود Supabase و پیوند account_settings حذف شد. اطلاعات دانش‌آموز/دبیر دست‌نخورده ماند." });
});
