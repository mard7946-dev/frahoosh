import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const respond = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });
const clean = (value: unknown) => String(value ?? "").replace(/[\u200c\u200f\u202a-\u202e]/g, "").trim();
function normalizeDigits(value: string) {
  return value
    .replace(/[۰-۹]/g, d => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d)))
    .replace(/[٠-٩]/g, d => String("٠١٢٣٤٥٦٧٨٩".indexOf(d)));
}
function usernameVariants(raw: string) {
  const value = normalizeDigits(clean(raw));
  const digits = value.replace(/\D/g, "");
  const variants = new Set<string>([value]);
  if (digits) variants.add(digits);
  if (digits.startsWith("0098") && digits.length === 14) variants.add("0" + digits.slice(4));
  if (digits.startsWith("98") && digits.length === 12) variants.add("0" + digits.slice(2));
  if (digits.startsWith("9") && digits.length === 10) variants.add("0" + digits);
  if (digits.startsWith("0") && digits.length === 11) variants.add(digits.slice(1));
  return [...variants].filter(Boolean);
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return respond({ message: "درخواست نامعتبر است." }, 405);

  const body = await req.json().catch(() => ({}));
  const username = clean(body?.username);
  const password = String(body?.password ?? "");
  if (!username || !password || username.length > 160 || password.length > 1024) {
    return respond({ message: "نام کاربری و رمز عبور را کامل وارد کنید." }, 400);
  }

  const url = Deno.env.get("SUPABASE_URL") ?? "";
  const secretBundle = Deno.env.get("SUPABASE_SECRET_KEYS") ?? "";
  let serviceKey = "";
  try { serviceKey = JSON.parse(secretBundle).default ?? ""; } catch (_) {}
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY") ?? req.headers.get("apikey") ?? "";
  if (!url || !serviceKey || !anonKey) {
    return respond({ message: "سرویس ورود موقتاً در دسترس نیست." }, 503);
  }

  const admin = createClient(url, serviceKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const auth = createClient(url, anonKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const variants = usernameVariants(username);
  const emails = new Set<string>();
  const addEmails = (rows: Array<{ email?: string | null }> | null) => {
    for (const row of rows ?? []) {
      const email = clean(row.email).toLowerCase();
      if (email && email.includes("@")) emails.add(email);
    }
  };

  try {
    // Resolve account usernames on the server; never expose account emails to the client.
    const byUsername = await admin.from("account_settings").select("email").in("username", variants).limit(10);
    if (byUsername.error) throw byUsername.error;
    addEmails(byUsername.data);

    // If the username is a mobile number, support teachers whose account username
    // is still their national code and whose phone is stored in the teachers table.
    if (!emails.size && /^\d{10,14}$/.test(normalizeDigits(username).replace(/\D/g, ""))) {
      const [byPhone, byMobile] = await Promise.all([
        admin.from("teachers").select("national_code").in("phone", variants).limit(10),
        admin.from("teachers").select("national_code").in("mobile", variants).limit(10),
      ]);
      if (byPhone.error || byMobile.error) throw byPhone.error ?? byMobile.error;
      const codes = [...new Set([...(byPhone.data ?? []), ...(byMobile.data ?? [])]
        .map((row: { national_code?: string | null }) => clean(row.national_code)).filter(Boolean))];
      if (codes.length) {
        const byCode = await admin.from("account_settings").select("email").in("national_code", codes).limit(10);
        if (byCode.error) throw byCode.error;
        addEmails(byCode.data);
      }
      if (!emails.size) {
        const byCode = await admin.from("account_settings").select("email").in("national_code", variants).limit(10);
        if (byCode.error) throw byCode.error;
        addEmails(byCode.data);
      }
    }
  } catch (_) {
    return respond({ message: "بررسی حساب انجام نشد؛ کمی بعد دوباره تلاش کنید." }, 503);
  }

  // Avoid trying multiple accounts for one input, and never disclose whether a username exists.
  if (emails.size !== 1) {
    return respond({ message: "نام کاربری یا رمز عبور صحیح نیست؛ شماره را همان‌طور که مدیر ثبت کرده وارد کنید." }, 401);
  }
  const email = [...emails][0];
  const { data, error } = await auth.auth.signInWithPassword({ email, password });
  if (error || !data.session || !data.user) {
    return respond({ message: "نام کاربری یا رمز عبور صحیح نیست؛ شماره را همان‌طور که مدیر ثبت کرده وارد کنید." }, 401);
  }
  return respond({ session: data.session, user: data.user });
});
