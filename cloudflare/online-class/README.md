# Frahoosh Online Class — Cloudflare migration

This directory contains the first isolated staging API slice. It does **not** replace the live classroom and does not modify existing web/APK runtime files.

## Implemented in this branch

- `GET /health`: service/configuration status; intentionally reports `productionReady: false`.
- `POST /api/auth/login`: username/password login with salted PBKDF2-SHA-256 password hashes and hashed bearer tokens stored in D1.
- `GET /api/auth/me` and `POST /api/auth/logout`.
- `POST /api/admin/users`: public registration is disabled. The first manager can be bootstrapped only when the user table is empty and a secret of at least 24 characters is configured as Worker secret `BOOTSTRAP_SECRET`. After that, only a manager can create accounts.
- `GET /api/classes`, `POST /api/classes`: manager/academic deputy can create classes; teacher/student lists are limited to assigned/membership classes.
- `POST /api/classes/:id/start`: manager, academic deputy, or assigned teacher.
- `GET/POST /api/classes/:id/signals`: authenticated class membership, active-class checks, and basic student tool permission checks.

## Still not complete

- The current web and APK clients still use the old Supabase Auth/REST/RPC/Storage endpoints. They have **not** been switched to this API.
- Existing user accounts, password/reset workflows, tenant/school scope, enrolment, attendance, detailed teacher permission UI, chat, and board event formats have not been fully migrated.
- R2 upload/download endpoints and automatic cleanup after class ends are not implemented yet.
- Signals currently provide a first API layer, not a guarantee that the existing browser clients understand the new payload format.
- No Cloudflare account resources have been created or deployed by this repository change.

The D1 migration is a clean **new staging schema**; it does not copy production data and must not be treated as a schema-perfect export of Supabase.

## Local validation

From this directory, with Node.js and Python 3 installed:

```sh
node --check worker.js
python tests/schema_smoke.py
```

With Wrangler authenticated to the intended Cloudflare account, first verify the resource names and IDs. Provision D1/R2 only in a staging account/environment, configure `BOOTSTRAP_SECRET` using `npx wrangler secret put BOOTSTRAP_SECRET`, and apply the D1 migration:

```sh
npx wrangler d1 create frahoosh-online-class
npx wrangler r2 bucket create frahoosh-online-class-files
npx wrangler d1 migrations apply frahoosh-online-class --remote
npx wrangler dev
```

Before deployment, paste the real `database_id` returned by D1 creation into `wrangler.jsonc`. Confirm the R2 bucket name matches exactly. Never put Cloudflare API tokens, R2 S3 credentials, passwords, or service-role keys in source control. Use Worker R2 bindings rather than exposing bucket keys to browsers.

## Required cutover order

1. Export and review the actual standalone-classroom data model, Auth rules, RLS, and RPC behavior.
2. Agree on how existing users will be securely migrated/reset; do not copy password hashes blindly or enable public registration.
3. Run this schema and Worker only in staging; test manager, teacher, student and forbidden-access cases.
4. Port enrolment, permissions, attendance, board event payloads and R2 file lifecycle.
5. Adapt a staging copy of web and APK to this API and test button → API → stored result → refreshed UI, including camera/microphone permissions and live signalling.
6. Confirm no old Supabase endpoint remains in the staged standalone path.
7. Only then cut over production, keeping the existing build available for rollback.

## Acceptance checklist

- [ ] Cloudflare staging resources provisioned and health endpoint checked.
- [ ] Authentication and role/ownership authorization tests pass.
- [ ] Existing account migration/reset plan approved and tested.
- [ ] R2 objects remain private and are accessible only to class members.
- [ ] Teacher permission changes propagate to student clients.
- [ ] Audio/video signalling, board tools, attendance and file lifecycle pass web and APK tests.
- [ ] No runtime request to Supabase remains in the migrated standalone classroom path.
- [ ] Production cutover and rollback are documented.
