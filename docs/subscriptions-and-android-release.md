# Frahoosh school subscriptions and Android release

## School subscription model

- Each school has a stable UUID, slug, school code, and status.
- Plans are seeded for 1, 2, 3, 6, 9, 12, and 24 months with capacity bands of 100, 200, 300, 500, 700, and 1000 students.
- Prices intentionally start at 0 IRR; the platform owner must set actual prices in the subscription-plan module before selling plans.
- The original school retains a legacy entitlement so existing users are not locked during rollout.
- Expiration is enforced by database row-level policies and operational RPC checks. School data is retained after expiry.
- A school manager can manage roles in the account-management module. Authentication IDs cannot be reassigned by ordinary school managers.

## Android signing and Play Protect

- The Android application ID is `ir.frahoosh`, version `1.6.9` (version code `169`).
- The build workflow rejects unexpected high-risk permissions and verifies the APK signature, then publishes a permission list, certificate report, and SHA-256 checksum.
- For a production release with a stable signing identity, configure GitHub Actions secrets: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, and `ANDROID_KEY_PASSWORD`.
- Without those secrets, the workflow builds a debug-signed test APK. A debug signature does not guarantee Play Protect acceptance and should not be used as the production distribution package.
- A Play Protect block cannot be reliably eliminated by renaming or rebuilding the APK. If it identifies the app as harmful, inspect the exact warning and submit the release for Google Play review or use a verified store distribution path.
