import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

const ROLE_ALIASES: Record<string,string> = {
  manager: "manager", executive: "executive", educational: "educational",
  cultural: "cultural", advisor: "advisor", counselor: "advisor",
  teacher: "teacher", student: "student", parent: "parent",
};

function text(v: unknown) { return String(v ?? "").trim(); }

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return response({ error: "POST required" }, 405);

  const authHeader = req.headers.get("Authorization") ?? "";
  if (!authHeader.startsWith("Bearer ")) return response({ error: "احراز هویت الزامی است" }, 401);

  const url = Deno.env.get("SUPABASE_URL") ?? "";
  let secretKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  const secretKeysRaw = Deno.env.get("SUPABASE_SECRET_KEYS") ?? "";
  if (secretKeysRaw) {
    try { secretKey = JSON.parse(secretKeysRaw).default ?? secretKey; } catch (_) {}
  }
  if (!url || !secretKey) return response({ error: "تنظیمات سرویس سمت سرور کامل نیست" }, 500);

  const admin = createClient(url, secretKey);
  const token = authHeader.slice("Bearer ".length);
  const { data: callerData, error: callerError } = await admin.auth.getUser(token);
  if (callerError || !callerData?.user) return response({ error: "نشست کاربر معتبر نیست" }, 401);

  const callerId = callerData.user.id;
  const { data: callerProfile, error: profileError } = await admin
    .from("account_settings")
    .select("role,username,national_code,display_name")
    .eq("auth_user_id", callerId)
    .maybeSingle();

  const allowedCallers = ["manager","executive","educational","cultural"];
  if (profileError || !allowedCallers.includes(text(callerProfile?.role).toLowerCase())) {
    return response({ error: "فقط مدیریت و معاونان مجاز به افزودن گروهی افراد هستند" }, 403);
  }

  const body = await req.json().catch(() => ({}));
  const people = Array.isArray(body.people) ? body.people : [];
  if (!people.length || people.length > 500) {
    return response({ error: "تعداد رکوردها باید بین 1 تا 500 باشد" }, 400);
  }

  const results: any[] = [];

  async function upsertPersonProfile(p: any, role: string) {
    const common = {
      first_name: text(p.first_name),
      last_name: text(p.last_name),
      national_code: text(p.national_code),
    };
    if (role === "student") {
      const { data: existing } = await admin.from("students").select("id").eq("national_code", common.national_code).maybeSingle();
      const payload = {
        ...common,
        student_code: text(p.student_code) || null,
        grade: text(p.grade) || null,
        class_name: text(p.class_name) || null,
        phone: text(p.phone) || null,
        parent_phone: text(p.parent_phone) || null,
        father_name: text(p.father_name) || null,
        mother_name: text(p.mother_name) || null,
        birth_date: text(p.birth_date) || null,
        email: text(p.email).toLowerCase() || null,
        address: text(p.address) || null,
        description: text(p.description) || null,
        nationality: text(p.nationality) || null,
        religion: text(p.religion) || null,
        sect: text(p.sect) || null,
      };
      const q = existing
        ? admin.from("students").update(payload).eq("id", existing.id)
        : admin.from("students").insert(payload);
      const { data, error } = await q.select("id").single();
      if (error) throw error;
      return { student_id: data.id };
    }

    if (role === "teacher") {
      const { data: existing } = await admin.from("teachers").select("id").eq("national_code", common.national_code).maybeSingle();
      const payload = {
        ...common,
        phone: text(p.phone) || null,
        mobile: text(p.mobile || p.phone) || null,
        email: text(p.email).toLowerCase() || null,
        subject: text(p.subject) || null,
        grades: text(p.grades) || null,
        description: text(p.description) || null,
        lessons: text(p.lessons) || null,
        employment_status: text(p.employment_status) || null,
        employee_code: text(p.employee_code) || null,
      };
      const q = existing
        ? admin.from("teachers").update(payload).eq("id", existing.id)
        : admin.from("teachers").insert(payload);
      const { data, error } = await q.select("id").single();
      if (error) throw error;
      return { teacher_id: data.id };
    }

    if (["manager","executive","educational","cultural","advisor"].includes(role)) {
      const { data: existing } = await admin.from("staff").select("id").eq("national_code", common.national_code).maybeSingle();
      const payload = {
        ...common,
        role,
        phone: text(p.phone) || null,
        description: text(p.description) || null,
        work_experience: text(p.work_experience) || null,
        employee_code: text(p.employee_code) || null,
        religion: text(p.religion) || null,
        sect: text(p.sect) || null,
        employment_status: text(p.employment_status) || null,
      };
      const q = existing
        ? admin.from("staff").update(payload).eq("id", existing.id)
        : admin.from("staff").insert(payload);
      const { data, error } = await q.select("id").single();
      if (error) throw error;
      return { staff_id: data.id };
    }

    return {};
  }

  for (const raw of people) {
    const p = raw && typeof raw === "object" ? raw : {};
    const nationalCode = text(p.national_code);
    const email = text(p.email).toLowerCase();
    const password = text(p.password);
    const role = ROLE_ALIASES[text(p.role).toLowerCase()] ?? "";
    const displayName = text(p.display_name) || [text(p.first_name), text(p.last_name)].filter(Boolean).join(" ");

    if (!nationalCode || !email || !password || !role) {
      results.push({ national_code:nationalCode, email, success:false, error:"کد ملی، ایمیل، رمز و نقش الزامی است" });
      continue;
    }

    try {
      let userId = "";
      const { data: created, error: createError } = await admin.auth.admin.createUser({
        email, password, email_confirm: true,
        user_metadata: {
          role, display_name: displayName, national_code: nationalCode,
          first_name: text(p.first_name), last_name: text(p.last_name),
        },
      });
      if (!createError && created?.user?.id) {
        userId = created.user.id;
      } else {
        const { data: existing } = await admin.from("account_settings")
          .select("auth_user_id").eq("national_code", nationalCode).maybeSingle();
        userId = text(existing?.auth_user_id);
        if (!userId) throw createError ?? new Error("حساب Auth موجود نیست.");
        const { error: updateAuthError } = await admin.auth.admin.updateUserById(userId, {
          password, email, user_metadata: {
            role, display_name: displayName, national_code: nationalCode,
            first_name: text(p.first_name), last_name: text(p.last_name),
          },
        });
        if (updateAuthError) throw updateAuthError;
      }

      const profileIds = await upsertPersonProfile(p, role);

      const account = {
        username: text(p.username) || nationalCode,
        display_name: displayName,
        email,
        national_code: nationalCode,
        role,
        auth_user_id: userId,
        phone: text(p.phone) || null,
        preferences: {
          bulk_imported: true,
          imported_by: callerId,
          ...(typeof p.preferences === "object" && p.preferences ? p.preferences : {}),
          ...profileIds,
        },
      };
      const { error: accountError } = await admin.from("account_settings")
        .upsert(account, { onConflict:"national_code" });
      if (accountError) throw accountError;

      if (role === "parent" && text(p.child_national_code)) {
        const { data: child } = await admin.from("students").select("id")
          .eq("national_code", text(p.child_national_code)).maybeSingle();
        if (!child?.id) throw new Error("دانش‌آموز معرفی‌شده برای ولی پیدا نشد.");
        const { error: linkError } = await admin.from("parent_children").upsert({
          parent_username: nationalCode, student_id: child.id
        }, { onConflict:"parent_username,student_id" });
        if (linkError) throw linkError;
      }

      results.push({
        national_code:nationalCode, email, role, auth_user_id:userId,
        ...profileIds, success:true
      });
    } catch (e) {
      results.push({ national_code:nationalCode, email, role, success:false, error:String(e?.message ?? e) });
    }
  }

  return response({
    ok:true, total:people.length,
    succeeded:results.filter(x=>x.success).length,
    failed:results.filter(x=>!x.success).length,
    results
  });
});
