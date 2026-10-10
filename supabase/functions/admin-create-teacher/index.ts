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
  if (!authHeader.startsWith("Bearer ")) return respond({ error: "برای ایجاد حساب باید وارد شده باشید." }, 401);

  const url = Deno.env.get("SUPABASE_URL") ?? "";
  const secretBundle = Deno.env.get("SUPABASE_SECRET_KEYS") ?? "";
  let serviceKey = "";
  try { serviceKey = JSON.parse(secretBundle).default ?? ""; } catch (_) {}
  if (!url || !serviceKey) return respond({ error: "تنظیمات امن سرویس ایجاد حساب کامل نیست." }, 500);

  const admin = createClient(url, serviceKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: authData, error: authError } = await admin.auth.getUser(authHeader.slice(7));
  if (authError || !authData.user) return respond({ error: "نشست ورود معتبر نیست؛ دوباره وارد شوید." }, 401);

  const { data: caller, error: callerError } = await admin
    .from("account_settings").select("role")
    .eq("auth_user_id", authData.user.id).maybeSingle();
  if (callerError) return respond({ error: "نقش کاربر جاری بررسی نشد." }, 500);
  if (!["manager", "مدیر", "principal", "administrator", "admin"].includes(normRole(caller?.role))) {
    return respond({ error: "فقط مدیر مدرسه اجازه ایجاد حساب دبیر را دارد." }, 403);
  }

  const body = await req.json().catch(() => ({}));
  const firstName = text(body.first_name), lastName = text(body.last_name);
  const nationalCode = text(body.national_code), email = text(body.email).toLowerCase();
  const password = text(body.password), phone = text(body.phone), subject = text(body.subject);
  const displayName = [firstName, lastName].filter(Boolean).join(" ");
  if (!firstName || !lastName || !nationalCode || !email || !password) {
    return respond({ error: "نام، نام خانوادگی، کد ملی، ایمیل و رمز عبور الزامی است." }, 400);
  }
  if (!/^\S+@\S+\.\S+$/.test(email)) return respond({ error: "ایمیل واردشده معتبر نیست." }, 400);
  if (nationalCode.length < 8 || nationalCode.length > 12) return respond({ error: "کد ملی یا شناسه واردشده معتبر نیست." }, 400);
  if (password.length < 8) return respond({ error: "رمز عبور باید دست‌کم ۸ نویسه داشته باشد." }, 400);

  const { data: existing, error: existingError } = await admin
    .from("account_settings").select("username,role,auth_user_id")
    .eq("national_code", nationalCode).maybeSingle();
  if (existingError) return respond({ error: "بررسی حساب قبلی ناموفق بود." }, 500);
  if (existing?.auth_user_id) return respond({ error: "برای این کد ملی قبلاً حساب ورود ساخته شده است." }, 409);
  if (existing && normRole(existing.role) !== "teacher" && normRole(existing.role) !== "دبیر") {
    return respond({ error: "این کد ملی به نقش دیگری متصل است؛ ابتدا اطلاعات آن حساب باید توسط مدیر بررسی شود." }, 409);
  }

  const { data: created, error: createError } = await admin.auth.admin.createUser({
    email, password, email_confirm: true,
    user_metadata: { role: "teacher", display_name: displayName, national_code: nationalCode }
  });
  if (createError || !created.user) {
    return respond({ error: createError?.message ?? "ساخت حساب احراز هویت ناموفق بود." }, 400);
  }

  const username = existing?.username || nationalCode;
  try {
    const { data: oldTeacher, error: teacherLookupError } = await admin
      .from("teachers").select("id").eq("national_code", nationalCode).maybeSingle();
    if (teacherLookupError) throw teacherLookupError;
    const teacherRow = {
      first_name: firstName, last_name: lastName, national_code: nationalCode,
      email, phone: phone || null, mobile: phone || null, subject: subject || null,
      employment_status: "فعال"
    };
    const teacherWrite = oldTeacher
      ? await admin.from("teachers").update(teacherRow).eq("id", oldTeacher.id)
      : await admin.from("teachers").insert(teacherRow);
    if (teacherWrite.error) throw teacherWrite.error;

    const { error: accountError } = await admin.from("account_settings").upsert({
      username, display_name: displayName, email, national_code: nationalCode,
      role: "teacher", auth_user_id: created.user.id, phone: phone || "",
      preferences: "{}"
    }, { onConflict: "username" });
    if (accountError) throw accountError;

    return respond({ success: true, username, email, role: "teacher", message: "حساب دبیر ایجاد شد." }, 201);
  } catch (e) {
    await admin.auth.admin.deleteUser(created.user.id);
    return respond({ error: "ذخیره پروفایل دبیر ناموفق بود؛ حساب موقت حذف شد. " + text((e as Error)?.message) }, 500);
  }
});
