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
  const username = text(body.username).replace(/[۰-۹]/g, d => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d))).replace(/[٠-٩]/g, d => String("٠١٢٣٤٥٦٧٨٩".indexOf(d)));
  const nationalCode = text(body.national_code).replace(/[۰-۹]/g, d => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d))).replace(/[٠-٩]/g, d => String("٠١٢٣٤٥٦٧٨٩".indexOf(d)));
  const email = (text(body.email) || (username + "@users.frahoosh.ir")).toLowerCase();
  const password = text(body.password) || "12345", phone = text(body.phone), subject = text(body.subject);
  const displayName = [firstName, lastName].filter(Boolean).join(" ");
  if (!firstName || !lastName || !username || !nationalCode) {
    return respond({ error: "نام، نام خانوادگی، نام کاربری و کد ملی دبیر الزامی است." }, 400);
  }
  if (!/^\d{8,12}$/.test(username)) return respond({ error: "نام کاربری باید عددی و بین ۸ تا ۱۲ رقم باشد." }, 400);
  if (!/^\d{10}$/.test(nationalCode)) return respond({ error: "کد ملی باید ۱۰ رقم باشد." }, 400);
  if (!/^\S+@\S+\.\S+$/.test(email)) return respond({ error: "ایمیل واردشده معتبر نیست." }, 400);
  if (password !== "12345") return respond({ error: "رمز اولیه حساب دبیر باید 12345 باشد." }, 400);

  const { data: usernameOwner, error: usernameError } = await admin
    .from("account_settings").select("username,national_code,role,auth_user_id")
    .eq("username", username).maybeSingle();
  if (usernameError) return respond({ error: "بررسی یکتایی نام کاربری ناموفق بود." }, 500);
  if (usernameOwner && usernameOwner.national_code !== nationalCode) return respond({ error: "این نام کاربری قبلاً به حساب دیگری اختصاص یافته است." }, 409);
  if (usernameOwner?.auth_user_id) return respond({ error: "برای این نام کاربری قبلاً حساب ورود ساخته شده است." }, 409);

  const { data: existingByCode, error: existingError } = await admin
    .from("account_settings").select("username,role,auth_user_id")
    .eq("national_code", nationalCode).maybeSingle();
  if (existingError) return respond({ error: "بررسی حساب قبلی ناموفق بود." }, 500);
  if (existingByCode?.auth_user_id) return respond({ error: "برای این دبیر قبلاً حساب ورود ساخته شده است." }, 409);
  if (existingByCode && normRole(existingByCode.role) !== "teacher" && normRole(existingByCode.role) !== "دبیر") {
    return respond({ error: "این کد ملی به نقش دیگری متصل است؛ ابتدا اطلاعات آن حساب باید توسط مدیر بررسی شود." }, 409);
  }

  const { data: created, error: createError } = await admin.auth.admin.createUser({
    email, password, email_confirm: true,
    user_metadata: { role: "teacher", display_name: displayName, national_code: nationalCode, username, must_change_password: true }
  });
  if (createError || !created.user) {
    return respond({ error: createError?.message ?? "ساخت حساب احراز هویت ناموفق بود." }, 400);
  }

  const finalUsername = username;
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

    const accountRow = { username: finalUsername, display_name: displayName, email, national_code: nationalCode,
      role: "teacher", auth_user_id: created.user.id, phone: phone || "", preferences: "{}" };
    const accountWrite = existingByCode
      ? await admin.from("account_settings").update(accountRow).eq("username", existingByCode.username)
      : usernameOwner
        ? await admin.from("account_settings").update(accountRow).eq("username", usernameOwner.username)
        : await admin.from("account_settings").insert(accountRow);
    if (accountWrite.error) throw accountWrite.error;

    return respond({ success: true, username: finalUsername, role: "teacher", message: "حساب دبیر ایجاد شد." }, 201);
  } catch (e) {
    await admin.auth.admin.deleteUser(created.user.id);
    return respond({ error: "ذخیره پروفایل دبیر ناموفق بود؛ حساب موقت حذف شد. " + text((e as Error)?.message) }, 500);
  }
});
