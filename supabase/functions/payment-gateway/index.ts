// Frahoosh payment gateway bridge (ZarinPal v4).
//
// Routes (same function, selected by ?op=):
//   POST ?op=start   body {attempt_id}  — requires the user's JWT. Loads the caller's own
//                    payment_attempt (RLS-scoped), asks ZarinPal for an authority and returns {url}.
//   GET  ?op=callback&attempt_id=..&Authority=..&Status=OK|NOK — called by ZarinPal in the
//                    browser. Verifies server-side, updates payment_attempts, inserts payment_records.
//
// Secrets (supabase secrets set ...): ZARINPAL_MERCHANT_ID (required)
//   ZARINPAL_SANDBOX=true|false (default false)  PAYMENT_AMOUNT_UNIT=IRT|IRR (default IRT)
// Deploy with --no-verify-jwt (the callback is called by the gateway without a JWT; the start
// route validates the JWT itself).
import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...cors, "Content-Type": "application/json" } });
const page = (title: string, msg: string, ok: boolean) =>
  new Response(
    `<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">` +
      `<body style="font-family:sans-serif;text-align:center;padding:48px 16px;background:#f4f8fc">` +
      `<h2 style="color:${ok ? "#177a3c" : "#b3261e"}">${title}</h2><p>${msg}</p><p>می‌توانید به برنامهٔ فراهوش برگردید.</p></body></html>`,
    { status: 200, headers: { ...cors, "Content-Type": "text/html; charset=utf-8" } },
  );

function secretKey() {
  let k = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  const raw = Deno.env.get("SUPABASE_SECRET_KEYS") ?? "";
  if (raw) { try { k = JSON.parse(raw).default ?? k; } catch (_) { /* keep */ } }
  return k;
}
const zp = () => (Deno.env.get("ZARINPAL_SANDBOX") === "true"
  ? "https://sandbox.zarinpal.com/pg/v4/payment"
  : "https://payment.zarinpal.com/pg/v4/payment");
const startPay = () => (Deno.env.get("ZARINPAL_SANDBOX") === "true"
  ? "https://sandbox.zarinpal.com/pg/StartPay/"
  : "https://payment.zarinpal.com/pg/StartPay/");
const unit = () => (Deno.env.get("PAYMENT_AMOUNT_UNIT") === "IRR" ? "IRR" : "IRT");

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const u = new URL(req.url);
  const op = u.searchParams.get("op") ?? "";
  const url = Deno.env.get("SUPABASE_URL") ?? "";
  const merchant = Deno.env.get("ZARINPAL_MERCHANT_ID") ?? "";
  const key = secretKey();
  if (!url || !key || !merchant) return json({ error: "درگاه پرداخت هنوز در سرور تنظیم نشده است" }, 503);
  const admin = createClient(url, key);

  // ---------------- start ----------------
  if (op === "start" && req.method === "POST") {
    const auth = req.headers.get("Authorization") ?? "";
    if (!auth.startsWith("Bearer ")) return json({ error: "احراز هویت الزامی است" }, 401);
    const { data: who, error: werr } = await admin.auth.getUser(auth.slice(7));
    if (werr || !who?.user) return json({ error: "نشست کاربر معتبر نیست" }, 401);

    const body = await req.json().catch(() => ({}));
    const attemptId = Number(body.attempt_id);
    if (!Number.isFinite(attemptId)) return json({ error: "شناسه پرداخت نامعتبر است" }, 400);

    // Read through the caller's own JWT so RLS decides ownership.
    const anon = Deno.env.get("SUPABASE_ANON_KEY") ?? "";
    const userClient = createClient(url, anon, { global: { headers: { Authorization: auth } } });
    const { data: att, error: aerr } = await userClient.from("payment_attempts").select("*").eq("id", attemptId).maybeSingle();
    if (aerr || !att) return json({ error: "درخواست پرداخت پیدا نشد یا متعلق به شما نیست" }, 404);
    if (String(att.status ?? "").toLowerCase() === "paid") return json({ error: "این پرداخت قبلاً انجام شده است" }, 409);
    const amount = Math.round(Number(att.amount));
    if (!(amount > 0)) return json({ error: "مبلغ پرداخت نامعتبر است" }, 400);

    const cb = `${url}/functions/v1/payment-gateway?op=callback&attempt_id=${attemptId}`;
    const r = await fetch(`${zp()}/request.json`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        merchant_id: merchant, amount, currency: unit(), callback_url: cb,
        description: String(att.description ?? "پرداخت فراهوش").slice(0, 200),
        metadata: { attempt_id: String(attemptId) },
      }),
    }).then((x) => x.json()).catch(() => null);
    const authority = r?.data?.authority;
    if (r?.data?.code !== 100 || !authority) {
      return json({ error: "ایجاد تراکنش در درگاه ناموفق بود", gateway: r?.errors ?? null }, 502);
    }
    await admin.from("payment_attempts").update({ authority, gateway: "zarinpal", status: "redirected" }).eq("id", attemptId);
    return json({ url: startPay() + authority, authority });
  }

  // ---------------- callback ----------------
  if (op === "callback" && req.method === "GET") {
    const attemptId = Number(u.searchParams.get("attempt_id"));
    const authority = u.searchParams.get("Authority") ?? "";
    const status = u.searchParams.get("Status") ?? "";
    if (!Number.isFinite(attemptId) || !authority) return page("درخواست نامعتبر", "اطلاعات بازگشت از درگاه کامل نیست.", false);

    const { data: att } = await admin.from("payment_attempts").select("*").eq("id", attemptId).maybeSingle();
    // The authority must match what we stored at start; prevents replaying a callback onto another attempt.
    if (!att || att.authority !== authority) return page("درخواست نامعتبر", "تراکنش با درخواست ثبت‌شده مطابقت ندارد.", false);
    if (String(att.status).toLowerCase() === "paid") return page("پرداخت قبلاً تأیید شده", `کد پیگیری: ${att.reference ?? ""}`, true);

    if (status !== "OK") {
      await admin.from("payment_attempts").update({ status: "failed" }).eq("id", attemptId);
      return page("پرداخت انجام نشد", "پرداخت لغو یا ناموفق بود.", false);
    }
    const v = await fetch(`${zp()}/verify.json`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ merchant_id: merchant, amount: Math.round(Number(att.amount)), authority }),
    }).then((x) => x.json()).catch(() => null);
    const code = v?.data?.code;
    if (code !== 100 && code !== 101) {
      await admin.from("payment_attempts").update({ status: "failed" }).eq("id", attemptId);
      return page("تأیید پرداخت ناموفق", "درگاه پرداخت را تأیید نکرد. در صورت کسر وجه با مدرسه تماس بگیرید.", false);
    }
    const ref = String(v.data.ref_id ?? "");
    await admin.from("payment_attempts").update({ status: "paid", reference: ref, gateway_ref: ref }).eq("id", attemptId);
    const today = new Date().toISOString().slice(0, 10);
    const { error: ierr } = await admin.from("payment_records").insert({
      student_id: att.student_id ?? null, parent_username: att.payer_username ?? att.username ?? null,
      title: att.description ?? "پرداخت آنلاین", amount: att.amount, status: "paid",
      payment_date: today, reference: ref, authority,
    });
    if (ierr) console.error("payment_records insert failed", ierr.message);
    return page("پرداخت موفق", `کد پیگیری: ${ref}`, true);
  }
  return json({ error: "مسیر نامعتبر" }, 404);
});
