/**
 * Frahoosh standalone online-class Cloudflare API.
 * Staging migration slice: identity, manager-only onboarding, classes and signals.
 * The live web/APK remain unchanged until a parity-tested cutover.
 */
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Max-Age": "86400",
};

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...corsHeaders, ...extra },
  });
}
function fail(status, error, message) { return json({ ok: false, error, message }, status); }
function id() { return crypto.randomUUID(); }
function b64(bytes) {
  let s = "";
  for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}
async function digest(value) {
  return b64(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
}
async function passwordHash(password, salt) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", salt: new TextEncoder().encode(salt), iterations: 210000, hash: "SHA-256" }, key, 256);
  return b64(bits);
}
function safeUser(row) {
  return { id: row.id, username: row.username, first_name: row.first_name, last_name: row.last_name, role: row.role };
}
async function bodyJson(request) {
  try { return await request.json(); } catch { return null; }
}
async function currentUser(request, env) {
  const header = request.headers.get("Authorization") || "";
  const token = header.match(/^Bearer\s+(.+)$/i)?.[1];
  if (!token) return null;
  return env.DB.prepare(
    "SELECT u.id,u.username,u.first_name,u.last_name,u.role,u.active FROM auth_sessions s JOIN app_users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>? LIMIT 1"
  ).bind(await digest(token), new Date().toISOString()).first().then(u => u && u.active ? u : null);
}
async function classAccess(env, user, classId) {
  const row = await env.DB.prepare("SELECT * FROM online_classes WHERE id=?").bind(classId).first();
  if (!row) return { row: null, membership: null };
  if (["manager", "academic_deputy"].includes(user.role)) return { row, membership: { member_role: user.role, can_draw: 1, can_erase: 1, can_audio: 1, can_video: 1 } };
  const membership = await env.DB.prepare("SELECT * FROM class_members WHERE class_id=? AND user_id=?").bind(classId, user.id).first();
  if (row.teacher_user_id === user.id && !membership) return { row, membership: { member_role: "teacher", can_draw: 1, can_erase: 1, can_audio: 1, can_video: 1 } };
  return { row, membership };
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (path === "/health" && request.method === "GET") {
      return json({
        ok: true, service: "frahoosh-online-class-api", stage: "staging-migration",
        d1Configured: Boolean(env.DB), r2Configured: Boolean(env.CLASS_FILES),
        productionReady: false,
        features: ["login", "manager-onboarding", "classes", "class-signals"],
        pending: ["production identity migration", "R2 upload/download", "web/APK parity tests"],
      });
    }
    if (!env.DB) return fail(503, "database_unavailable", "D1 binding DB is not configured.");

    if (path === "/api/auth/login" && request.method === "POST") {
      const input = await bodyJson(request);
      if (!input || typeof input.username !== "string" || typeof input.password !== "string" ||
          input.username.length > 120 || input.password.length > 1024) return fail(400, "invalid_input", "نام کاربری و رمز عبور معتبر الزامی است.");
      const user = await env.DB.prepare("SELECT * FROM app_users WHERE username=? COLLATE NOCASE LIMIT 1").bind(input.username.trim()).first();
      if (!user || !user.active || (await passwordHash(input.password, user.password_salt)) !== user.password_hash) {
        return fail(401, "invalid_credentials", "نام کاربری یا رمز عبور صحیح نیست.");
      }
      const token = b64(crypto.getRandomValues(new Uint8Array(32)));
      const expires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
      await env.DB.prepare("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(?,?,?)").bind(await digest(token), user.id, expires).run();
      return json({ ok: true, token, expires_at: expires, user: safeUser(user) });
    }

    if (path === "/api/admin/users" && request.method === "POST") {
      const input = await bodyJson(request);
      if (!input || typeof input.username !== "string" || typeof input.password !== "string" ||
          typeof input.first_name !== "string" || typeof input.last_name !== "string" ||
          !["manager", "academic_deputy", "teacher", "student"].includes(input.role) ||
          input.username.trim().length < 3 || input.username.length > 120 ||
          input.password.length < 10 || input.password.length > 1024 ||
          !input.first_name.trim() || !input.last_name.trim()) {
        return fail(400, "invalid_input", "اطلاعات کاربر کامل نیست؛ رمز باید حداقل ۱۰ نویسه داشته باشد.");
      }
      const count = await env.DB.prepare("SELECT COUNT(*) AS n FROM app_users").first();
      const user = await currentUser(request, env);
      const bootstrapOk = count.n === 0 && typeof env.BOOTSTRAP_SECRET === "string" &&
        env.BOOTSTRAP_SECRET.length >= 24 && input.bootstrap_secret === env.BOOTSTRAP_SECRET &&
        input.role === "manager";
      if (!bootstrapOk && (!user || user.role !== "manager")) return fail(403, "forbidden", "ثبت‌نام عمومی غیرفعال است؛ فقط مدیر مجاز است.");
      const salt = b64(crypto.getRandomValues(new Uint8Array(16)));
      const hash = await passwordHash(input.password, salt);
      const newUser = { id: id(), username: input.username.trim(), first_name: input.first_name.trim(), last_name: input.last_name.trim(), role: input.role };
      try {
        await env.DB.prepare("INSERT INTO app_users(id,username,first_name,last_name,role,password_hash,password_salt) VALUES(?,?,?,?,?,?,?)")
          .bind(newUser.id, newUser.username, newUser.first_name, newUser.last_name, newUser.role, hash, salt).run();
      } catch (e) {
        if (String(e).toLowerCase().includes("unique")) return fail(409, "username_exists", "این نام کاربری قبلاً ثبت شده است.");
        throw e;
      }
      return json({ ok: true, user: newUser }, 201);
    }

    const user = await currentUser(request, env);
    if (!user) return fail(401, "unauthorized", "برای ادامه باید وارد شوید.");

    if (path === "/api/auth/me" && request.method === "GET") return json({ ok: true, user: safeUser(user) });
    if (path === "/api/auth/logout" && request.method === "POST") {
      const token = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
      if (token) await env.DB.prepare("DELETE FROM auth_sessions WHERE token_hash=?").bind(await digest(token)).run();
      return json({ ok: true });
    }

    if (path === "/api/classes" && request.method === "GET") {
      let result;
      if (["manager", "academic_deputy"].includes(user.role)) {
        result = await env.DB.prepare("SELECT * FROM online_classes ORDER BY created_at DESC LIMIT 200").all();
      } else {
        result = await env.DB.prepare(
          "SELECT DISTINCT c.* FROM online_classes c LEFT JOIN class_members m ON m.class_id=c.id AND m.user_id=? WHERE c.teacher_user_id=? OR m.user_id=? ORDER BY c.created_at DESC LIMIT 200"
        ).bind(user.id, user.id, user.id).all();
      }
      return json({ ok: true, classes: result.results || [] });
    }

    if (path === "/api/classes" && request.method === "POST") {
      if (!["manager", "academic_deputy"].includes(user.role)) return fail(403, "forbidden", "فقط مدیر یا معاون آموزشی می‌تواند کلاس بسازد.");
      const input = await bodyJson(request);
      if (!input || typeof input.title !== "string" || !input.title.trim() || input.title.length > 200) return fail(400, "invalid_input", "عنوان کلاس الزامی است.");
      const duration = Number(input.duration_minutes ?? 50);
      if (!Number.isInteger(duration) || duration < 1 || duration > 240) return fail(400, "invalid_duration", "مدت کلاس باید بین ۱ تا ۲۴۰ دقیقه باشد.");
      let teacher = null;
      if (input.teacher_user_id) {
        teacher = await env.DB.prepare("SELECT id FROM app_users WHERE id=? AND role='teacher' AND active=1").bind(String(input.teacher_user_id)).first();
        if (!teacher) return fail(400, "invalid_teacher", "دبیر انتخاب‌شده معتبر نیست.");
      }
      const classId = id();
      await env.DB.prepare("INSERT INTO online_classes(id,title,subject,grade,class_name,teacher_user_id,status,duration_minutes,created_by) VALUES(?,?,?,?,?,?,'scheduled',?,?)")
        .bind(classId, input.title.trim(), String(input.subject || "").slice(0,160), String(input.grade || "").slice(0,40), String(input.class_name || "").slice(0,40), teacher?.id || null, duration, user.id).run();
      if (teacher) await env.DB.prepare("INSERT INTO class_members(class_id,user_id,member_role,can_draw,can_erase,can_audio,can_video) VALUES(?,?, 'teacher',1,1,1,1)").bind(classId, teacher.id).run();
      return json({ ok: true, class: await env.DB.prepare("SELECT * FROM online_classes WHERE id=?").bind(classId).first() }, 201);
    }


    const filesMatch = path.match(/^\/api\/classes\/([a-f0-9-]+)\/files(?:\/([a-f0-9-]+))?$/i);
    if (filesMatch) {
      const classId = filesMatch[1];
      const fileId = filesMatch[2] || null;
      const { row, membership } = await classAccess(env, user, classId);
      if (!row) return fail(404, "class_not_found", "کلاس پیدا نشد.");
      if (!membership && !["manager", "academic_deputy"].includes(user.role)) return fail(403, "forbidden", "شما عضو این کلاس نیستید.");
      if (!env.CLASS_FILES) return fail(503, "storage_unavailable", "اتصال فضای فایل فعال نیست.");

      if (!fileId && request.method === "GET") {
        const rows = await env.DB.prepare("SELECT id,original_name,content_type,size_bytes,uploaded_by,created_at FROM class_files WHERE class_id=? ORDER BY created_at DESC LIMIT 200").bind(classId).all();
        return json({ ok: true, files: rows.results || [] });
      }
      if (!fileId && request.method === "POST") {
        if (!["manager", "academic_deputy"].includes(user.role) && !(user.role === "teacher" && (row.teacher_user_id === user.id || membership?.member_role === "teacher"))) return fail(403, "forbidden", "فقط دبیر مسئول کلاس یا مدیریت می‌تواند فایل بارگذاری کند.");
        if (row.status === "ended") return fail(409, "class_ended", "کلاس پایان یافته است.");
        const size = Number(request.headers.get("Content-Length") || 0);
        if (!Number.isSafeInteger(size) || size < 1 || size > 20 * 1024 * 1024 || !request.body) return fail(413, "invalid_file_size", "حجم فایل باید حداکثر ۲۰ مگابایت باشد.");
        const rawName = url.searchParams.get("filename") || "class-file";
        const name = rawName.split(/[\\/]/).pop().replace(/[\\r\\n"]/g, "_").slice(0, 180) || "class-file";
        const type = (request.headers.get("Content-Type") || "application/octet-stream").split(";")[0].trim().toLowerCase();
        const allowedTypes = new Set(["application/pdf","image/png","image/jpeg","image/webp","text/plain","application/vnd.openxmlformats-officedocument.presentationml.presentation","application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","application/vnd.ms-powerpoint","application/msword","application/vnd.ms-excel","audio/mpeg","audio/webm","video/mp4","video/webm"]);
        if (!allowedTypes.has(type)) return fail(415, "unsupported_file_type", "نوع این فایل پشتیبانی نمی‌شود.");
        const fileKeyId = id();
        const objectKey = classId + "/" + fileKeyId;
        await env.CLASS_FILES.put(objectKey, request.body, { httpMetadata: { contentType: type }, customMetadata: { originalName: name, classId: classId, uploadedBy: user.id } });
        try {
          await env.DB.prepare("INSERT INTO class_files(id,class_id,object_key,original_name,content_type,size_bytes,uploaded_by) VALUES(?,?,?,?,?,?,?)")
            .bind(fileKeyId, classId, objectKey, name, type, size, user.id).run();
        } catch (e) {
          await env.CLASS_FILES.delete(objectKey);
          throw e;
        }
        return json({ ok: true, file: { id: fileKeyId, original_name: name, content_type: type, size_bytes: size } }, 201);
      }
      if (fileId && request.method === "GET") {
        const meta = await env.DB.prepare("SELECT * FROM class_files WHERE id=? AND class_id=?").bind(fileId, classId).first();
        if (!meta) return fail(404, "file_not_found", "فایل پیدا نشد.");
        const object = await env.CLASS_FILES.get(meta.object_key);
        if (!object) return fail(404, "file_not_found", "محتوای فایل پیدا نشد.");
        const dispositionName = encodeURIComponent(meta.original_name).replace(/['()]/g, escape);
        return new Response(object.body, { status: 200, headers: {
          ...corsHeaders, "Content-Type": meta.content_type, "Content-Length": String(meta.size_bytes),
          "Content-Disposition": "attachment; filename*=UTF-8''" + dispositionName,
          "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"
        }});
      }
      if (fileId && request.method === "DELETE") {
        const meta = await env.DB.prepare("SELECT * FROM class_files WHERE id=? AND class_id=?").bind(fileId, classId).first();
        if (!meta) return fail(404, "file_not_found", "فایل پیدا نشد.");
        if (!["manager", "academic_deputy"].includes(user.role) && !(user.role === "teacher" && (row.teacher_user_id === user.id || membership?.member_role === "teacher") && meta.uploaded_by === user.id)) {
          return fail(403, "forbidden", "اجازه حذف این فایل را ندارید.");
        }
        await env.CLASS_FILES.delete(meta.object_key);
        await env.DB.prepare("DELETE FROM class_files WHERE id=?").bind(fileId).run();
        return json({ ok: true });
      }
      return fail(405, "method_not_allowed", "این روش برای فایل پشتیبانی نمی‌شود.");
    }

    const classMatch = path.match(/^\/api\/classes\/([a-f0-9-]+)(?:\/(start|end|signals))?$/i);
    if (classMatch) {
      const classId = classMatch[1];
      const action = classMatch[2] || "";
      const { row, membership } = await classAccess(env, user, classId);
      if (!row) return fail(404, "class_not_found", "کلاس پیدا نشد.");
      if (action === "end" && request.method === "POST") {
        if (!["manager", "academic_deputy"].includes(user.role) && !(user.role === "teacher" && (row.teacher_user_id === user.id || membership?.member_role === "teacher"))) {
          return fail(403, "forbidden", "اجازه پایان دادن به این کلاس را ندارید.");
        }
        if (!env.CLASS_FILES) return fail(503, "storage_unavailable", "برای پاک‌سازی امن فایل‌ها، اتصال فضای فایل لازم است.");
        let cursor;
        do {
          const page = await env.CLASS_FILES.list({ prefix: classId + "/", cursor, limit: 1000 });
          if (page.objects.length) await env.CLASS_FILES.delete(page.objects.map(object => object.key));
          cursor = page.truncated ? page.cursor : undefined;
        } while (cursor);
        await env.DB.prepare("DELETE FROM class_files WHERE class_id=?").bind(classId).run();
        await env.DB.prepare("UPDATE online_classes SET status='ended',ended_at=? WHERE id=?").bind(new Date().toISOString(), classId).run();
        return json({ ok: true, class: await env.DB.prepare("SELECT * FROM online_classes WHERE id=?").bind(classId).first(), filesDeleted: true });
      }
      if (action === "start" && request.method === "POST") {
        if (!["manager", "academic_deputy"].includes(user.role) && !(user.role === "teacher" && (row.teacher_user_id === user.id || membership?.member_role === "teacher"))) {
          return fail(403, "forbidden", "اجازه شروع این کلاس را ندارید.");
        }
        await env.DB.prepare("UPDATE online_classes SET status='active',started_at=COALESCE(started_at,?),ended_at=NULL WHERE id=?")
          .bind(new Date().toISOString(), classId).run();
        return json({ ok: true, class: await env.DB.prepare("SELECT * FROM online_classes WHERE id=?").bind(classId).first() });
      }
      if (action === "signals" && request.method === "GET") {
        if (!membership && !["manager", "academic_deputy"].includes(user.role)) return fail(403, "forbidden", "شما عضو این کلاس نیستید.");
        const after = Math.max(0, Number(url.searchParams.get("after") || 0));
        const signals = await env.DB.prepare("SELECT id,user_id,kind,payload_json,created_at FROM class_signals WHERE class_id=? AND id>? ORDER BY id ASC LIMIT 200").bind(classId, after).all();
        return json({ ok: true, signals: (signals.results || []).map(s => ({ ...s, payload: JSON.parse(s.payload_json) })) });
      }
      if (action === "signals" && request.method === "POST") {
        if (!membership && !["manager", "academic_deputy"].includes(user.role)) return fail(403, "forbidden", "شما عضو این کلاس نیستید.");
        if (row.status !== "active") return fail(409, "class_not_started", "کلاس هنوز شروع نشده است.");
        const input = await bodyJson(request);
        const kinds = ["presence", "leave", "board", "permissions", "audio", "video", "chat"];
        if (!input || !kinds.includes(input.kind)) return fail(400, "invalid_signal", "نوع پیام کلاس معتبر نیست.");
        if (input.kind === "permissions" && !["manager", "academic_deputy"].includes(user.role) && !(user.role === "teacher" && (row.teacher_user_id === user.id || membership?.member_role === "teacher"))) return fail(403, "permission_denied", "فقط دبیر مسئول کلاس یا مدیریت می‌تواند مجوزها را تغییر دهد.");
        if (user.role === "student" && input.kind === "board" && !membership.can_draw) return fail(403, "permission_denied", "اجازه استفاده از تخته را ندارید.");
        if (user.role === "student" && input.kind === "audio" && !membership.can_audio) return fail(403, "permission_denied", "اجازه استفاده از صدا را ندارید.");
        if (user.role === "student" && input.kind === "video" && !membership.can_video) return fail(403, "permission_denied", "اجازه استفاده از تصویر را ندارید.");
        const payload = JSON.stringify(input.payload ?? {});
        if (payload.length > 16000) return fail(413, "payload_too_large", "پیام کلاس بیش از حد بزرگ است.");
        const inserted = await env.DB.prepare("INSERT INTO class_signals(class_id,user_id,kind,payload_json) VALUES(?,?,?,?)").bind(classId, user.id, input.kind, payload).run();
        return json({ ok: true, id: inserted.meta?.last_row_id ?? null }, 201);
      }
      if (!membership && !["manager", "academic_deputy"].includes(user.role)) return fail(403, "forbidden", "شما عضو این کلاس نیستید.");
      if (user.role === "student" && row.status !== "active") return fail(403, "class_not_started", "دانش‌آموز تا شروع کلاس توسط دبیر نمی‌تواند وارد شود.");
      if (request.method === "GET") return json({ ok: true, class: row, membership });
    }

    return fail(404, "not_found", "مسیر درخواست‌شده وجود ندارد.");
  },
};
