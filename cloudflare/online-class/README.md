# Frahoosh Online Class — Cloudflare migration

This directory is an isolated migration scaffold. It does **not** replace the currently deployed classroom and does not modify the existing APK/web files.

## Current status

- Worker health endpoint: implemented at `GET /health`.
- D1 and R2 binding names: declared in `wrangler.jsonc`; resources still need to be provisioned in the intended Cloudflare account.
- Login, user/role checks, class management, attendance, classroom signalling, and file upload/download: **not migrated**.
- Existing web/APK still call Supabase endpoints. Do not switch their runtime configuration to this Worker until parity tests pass.
- Unknown API routes return HTTP 501 (fail closed); no class data or R2 objects are publicly exposed.

## Deploy locally / to a test Worker

From this directory, with an authenticated Cloudflare Wrangler session:

```sh
npx wrangler dev
```

The config declares D1 and R2 bindings. Review the resource names in the Cloudflare account before deploying. A deployment may provision resources; do not run production deployment until the account and resource names have been verified.

Health check:

```sh
curl http://localhost:8787/health
```

A healthy scaffold returns `productionReady: false` deliberately.

## Migration order (required)

1. Inventory the real Supabase schema, RLS policies, RPC definitions, and Auth claims used by the standalone classroom.
2. Define the Cloudflare identity/session model and explicit role/ownership checks before exposing any D1 or R2 data.
3. Create versioned D1 migrations from the verified schema; do not guess columns or copy production data into a new database.
4. Port APIs in small slices: login/session, class list/create, enrolment/attendance, teacher permissions and classroom signals.
5. Add private R2 upload/download endpoints only after authenticated class membership, file-size/type limits, and object ownership checks are tested.
6. Add integration tests for manager, teacher, student and guest; include denied-access cases.
7. Point a staging copy of web and APK at the Worker, then test the complete flow: button → API → persisted result → refreshed display, including audio/video signalling and board permissions.
8. Cut over production only after staging parity succeeds. Keep the current Supabase-backed build available for rollback until the cutover is verified.

## Secrets

Never commit Cloudflare API tokens, R2 Access Key IDs, R2 Secret Access Keys, Supabase service-role keys, or user credentials. Prefer Worker bindings for R2 access rather than putting S3 keys in browser code. Use Wrangler secrets for any server-side secret that is genuinely required.

## Acceptance checklist

- [ ] Worker deployed to a non-production environment.
- [ ] D1 migrations reviewed and applied to staging.
- [ ] Authentication and role/ownership authorization tests pass.
- [ ] R2 objects are private and inaccessible without authorized membership.
- [ ] Teacher permission changes propagate to student clients.
- [ ] Audio/video signalling, board tools, attendance and file lifecycle pass web and APK tests.
- [ ] No runtime request to Supabase remains in the migrated standalone classroom path.
- [ ] Production cutover and rollback are documented.
