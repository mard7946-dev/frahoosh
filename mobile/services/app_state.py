from mobile.services.hybrid_api import HybridApi

from mobile.services.session import (
    load_session,
    save_session,
    clear_session,
)


class AppState:

    def __init__(self):
        self.session = {}
        self.api = None

        try:
            self.api = HybridApi()
        except Exception as exc:
            print("API INIT ERROR:", repr(exc))
            self.api = None

        try:
            self.session = load_session() or {}
        except Exception:
            self.session = {}

        self._load_tokens()

    def _load_tokens(self):
        if self.api is None:
            return
        session = self.session if isinstance(self.session, dict) else {}
        self.api.access_token = session.get("access_token", "") or ""
        self.api.refresh_token = session.get("refresh_token", "") or ""
        self.api.expires_in = session.get("expires_in")
        self.api.expires_at = session.get("expires_at")
        self.api.token_type = session.get("token_type", "bearer") or "bearer"

    @property
    def user(self):
        if not isinstance(self.session, dict):
            return {}
        value = self.session.get("user") or {}
        return value if isinstance(value, dict) else {}

    @property
    def profile(self):
        if not isinstance(self.session, dict):
            return {}
        value = self.session.get("profile") or {}
        return value if isinstance(value, dict) else {}

    @property
    def role(self):
        profile = self.profile
        user = self.user
        role = profile.get("role") or user.get("role")
        metadata = user.get("user_metadata")
        if not role and isinstance(metadata, dict):
            role = metadata.get("role")
        value = str(role or "unknown").strip().lower()
        return {
            "counselor": "advisor",
            "counselling": "advisor",
            "accounting": "accountant",
            "finance": "accountant",
            "حسابدار": "accountant",
            "مشاور": "advisor",
            "مشاوره": "advisor",
        }.get(value, value)

    @property
    def national_code(self):
        p = self.profile
        return str(p.get("national_code") or p.get("nationalcode") or p.get("national_id") or "").strip()

    @property
    def display_name(self):
        p = self.profile
        for key in ("display_name", "full_name", "name"):
            if p.get(key):
                return str(p[key])
        user = self.user
        metadata = user.get("user_metadata")
        if isinstance(metadata, dict):
            for key in ("display_name", "full_name", "name"):
                if metadata.get(key):
                    return str(metadata[key])
        for key in ("display_name", "full_name", "name"):
            if user.get(key):
                return str(user[key])
        return user.get("email") or "کاربر فراهوش"

    @property
    def logged_in(self):
        return bool(self.api is not None and self.api.access_token and isinstance(self.session, dict))

    def set_session(self, payload, remember=True):
        if not isinstance(payload, dict):
            raise RuntimeError("پاسخ ورود نامعتبر است.")
        if not payload.get("access_token"):
            self.logout()
            raise RuntimeError("توکن ورود از Supabase دریافت نشد.")

        self.session = dict(payload)

        canonical_profile = self.session.get("canonical_profile")
        canonical_role = str(self.session.get("canonical_role") or "").strip().lower()
        if isinstance(canonical_profile, dict) and canonical_role:
            self.session["profile"] = dict(canonical_profile)
            self.session["canonical_role"] = canonical_role

        if self.api is not None:
            user = self.session.get("user") or {}
            current_profile = self.session.get("profile")
            if not isinstance(current_profile, dict):
                current_profile = {}

            try:
                refreshed = self.api._profile(user)
            except Exception as profile_exc:
                print("PROFILE REFRESH ERROR:", repr(profile_exc))
                refreshed = None

            if isinstance(refreshed, dict):
                merged = dict(current_profile)
                merged.update(refreshed)
                current_profile = merged

            login_identifier = str(self.session.get("login_identifier") or "").strip()
            normalized_identifier = self.api._normalize_digits(login_identifier)

            if normalized_identifier.isdigit() and len(normalized_identifier) == 10:
                try:
                    canonical_by_code = self.api._profile_by_national_code(normalized_identifier)
                    if isinstance(canonical_by_code, dict) and canonical_by_code:
                        current_profile = dict(current_profile)
                        current_profile.update(canonical_by_code)
                        current_profile["email"] = (
                            current_profile.get("email")
                            or (user.get("email") if isinstance(user, dict) else "")
                            or ""
                        )
                except Exception as code_exc:
                    print("CANONICAL LOGIN PROFILE UPGRADE ERROR:", repr(code_exc))

            resolved_role = str(current_profile.get("role") or "").strip().lower()
            if not resolved_role:
                print("LOGIN PROFILE MISSING ROLE; refusing session")
                self.logout()
                raise RuntimeError(
                    "نقش کاربر از Supabase دریافت نشد؛ "
                    "ایمیل حساب و رکورد account_settings را بررسی کنید."
                )

            self.session["profile"] = current_profile

        if self.session.get("canonical_role"):
            self.session["profile"]["role"] = self.session["canonical_role"]

        self.session["remember_me"] = bool(remember)
        self._load_tokens()

        if remember:
            persisted = save_session(self.session)
            if not persisted:
                print("SESSION PERSISTENCE WARNING: login remains valid in memory")
            return True

        clear_session()
        return True

    def persist_refreshed_token(self):
        if self.api is None or not self.api.access_token:
            return False
        if not isinstance(self.session, dict):
            self.session = {}
        self.session["access_token"] = self.api.access_token
        if self.api.refresh_token:
            self.session["refresh_token"] = self.api.refresh_token
        if self.api.expires_in is not None:
            self.session["expires_in"] = self.api.expires_in
        if self.api.expires_at is not None:
            self.session["expires_at"] = self.api.expires_at
        if self.api.token_type:
            self.session["token_type"] = self.api.token_type
        if not self.session.get("remember_me", False):
            return True
        return save_session(self.session)

    def refresh_session(self):
        if self.api is None or not self.api.refresh_token:
            return False
        try:
            if self.api.refresh_access_token():
                return self.persist_refreshed_token()
        except Exception as exc:
            print("REFRESH ERROR:", repr(exc))
        return False


    def subscription_status(self):
        """Return the server-backed school subscription state for UI gating.

        Tenant data policies remain the security boundary; this check only keeps
        expired schools from seeing operational panels in the mobile UI.
        """
        state = {"expired": False, "unknown": True, "platform_admin": False, "school_id": None, "record": None}
        if self.api is None or not self.api.access_token:
            return state

        user_id = str((self.user or {}).get("id") or "").strip()
        if not user_id:
            return state

        try:
            admins = self.api.table_select("platform_admins", {
                "select": "auth_user_id", "auth_user_id": "eq." + user_id, "limit": "1"
            })
            if isinstance(admins, list) and admins:
                return {"expired": False, "unknown": False, "platform_admin": True, "school_id": None, "record": None}

            school_id = str((self.profile or {}).get("tenant_school_id") or "").strip()
            if not school_id:
                accounts = self.api.table_select("account_settings", {
                    "select": "tenant_school_id", "auth_user_id": "eq." + user_id, "limit": "1"
                })
                if isinstance(accounts, list) and accounts:
                    school_id = str(accounts[0].get("tenant_school_id") or "").strip()
            if not school_id:
                return state

            state["school_id"] = school_id
            schools = self.api.table_select("schools", {
                "select": "status", "id": "eq." + school_id, "limit": "1"
            })
            subscriptions = self.api.table_select("school_subscriptions", {
                "select": "status,starts_at,ends_at,grace_days,student_limit",
                "school_id": "eq." + school_id,
                "order": "ends_at.desc",
                "limit": "1",
            })
            record = subscriptions[0] if isinstance(subscriptions, list) and subscriptions else None
            if not record or not isinstance(schools, list) or not schools:
                return {"expired": True, "unknown": False, "platform_admin": False, "school_id": school_id, "record": record}

            from datetime import datetime, timedelta, timezone

            def parse_instant(value):
                if not value:
                    return None
                text = str(value).strip().replace("Z", "+00:00")
                parsed = datetime.fromisoformat(text)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)

            now = datetime.now(timezone.utc)
            starts = parse_instant(record.get("starts_at"))
            ends = parse_instant(record.get("ends_at"))
            grace = max(0, int(record.get("grace_days") or 0))
            deadline = ends + timedelta(days=grace) if ends else None
            active = (
                str(schools[0].get("status") or "").lower() == "active"
                and str(record.get("status") or "").lower() in {"active", "past_due"}
                and starts is not None and now >= starts
                and deadline is not None and now <= deadline
            )
            return {"expired": not active, "unknown": False, "platform_admin": False, "school_id": school_id, "record": record}
        except Exception as exc:
            print("SUBSCRIPTION STATUS CHECK ERROR:", repr(exc))
            return state

    def logout(self):
        try:
            if self.api is not None:
                self.api.sign_out()
        except Exception:
            pass
        clear_session()
        self.session = {}
        if self.api is not None:
            self.api.access_token = ""
            self.api.refresh_token = ""
            self.api.expires_in = None
            self.api.expires_at = None
            self.api.token_type = "bearer"
        return True
