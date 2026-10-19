/**
 * Frahoosh standalone online-class Cloudflare API (migration scaffold).
 *
 * Intentionally does not replace the live Supabase-backed web/APK yet.
 * Do not add public data or upload routes until identity/session validation
 * and authorization have been ported and tested.
 */
const corsHeaders = {
  "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Max-Age": "86400",
};

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...corsHeaders,
      ...extraHeaders,
    },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    const url = new URL(request.url);
    if (url.pathname === "/health" && request.method === "GET") {
      return json({
        ok: true,
        service: "frahoosh-online-class-api",
        stage: "migration-scaffold",
        d1Configured: Boolean(env.DB),
        r2Configured: Boolean(env.CLASS_FILES),
        productionReady: false,
        message: "Authentication and classroom API migration are not complete.",
      });
    }

    // Fail closed: no classroom data or files are exposed by this scaffold.
    return json({
      ok: false,
      error: "not_implemented",
      message: "This endpoint is not enabled until authentication and role checks are migrated.",
    }, 501);
  },
};
