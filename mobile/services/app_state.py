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
        return str(role or "unknown").strip().lower()

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
            return False
        if not payload.get("access_token"):
            self.logout()
            return False

        self.session = dict(payload)

        # sign_in() resolves numeric identifiers against public.users before
        # the dashboard is opened. Treat that canonical role as immutable for
        # this session; never merge a stale cached student role over it.
        canonical_profile = self.session.get("canonical_profile")
        canonical_role = str(self.session.get("canonical_role") or "").strip().lower()
        if isinstance(canonical_profile, dict) and canonical_role:
            self.session["profile"] = dict(canonical_profile)
            self.session["canonical_role"] = canonical_role

        # The Auth response normally already contains the school profile, but
        # older/partially configured Supabase projects can return only the Auth
        # user. Enrich the session immediately while the fresh bearer token is
        # available so role-aware panels do not silently fall back to student
        # mode. This is especially important for the manager account: CRUD
        # controls and operational workflows depend on the canonical role.
        if self.api is not None:
            try:
                user = self.session.get("user") or {}
                current_profile = self.session.get("profile")
                if not isinstance(current_profile, dict):
                    current_profile = {}
                # Always refresh the school profile after authentication.
                # A cached student/parent role must never override the current
                # staff/manager role and hide CRUD controls.
                try:
                    refreshed = self.api._profile(user)
                except Exception as profile_exc:
                    print("PROFILE REFRESH ERROR:", repr(profile_exc))
                    refreshed = None
                if isinstance(refreshed, dict):
                    merged = dict(current_profile)
                    merged.update(refreshed)
                    current_profile = merged

                # Numeric login is the authoritative onboarding identifier.
                # Resolve the canonical public.users row by that identifier as a
                # second path, so a stale Auth metadata role can never force the
                # dashboard into the student panel.
                login_identifier = str(self.session.get("login_identifier") or "").strip()
                normalized_identifier = self.api._normalize_digits(login_identifier)
                if normalized_identifier.isdigit() and len(normalized_identifier) == 10:
                    try:
                        canonical_by_code = self.api._profile_by_national_code(normalized_identifier)
                        if isinstance(canonical_by_code, dict) and canonical_by_code:
                            # public.users is authoritative whenever the
                            # canonical lookup is available.
                            current_profile = dict(canonical_by_code)
                            current_profile["email"] = (
                                current_profile.get("email")
                                or (user.get("email") if isinstance(user, dict) else "")
                                or ""
                            )
                        else:
                            # Do not turn a successful Auth login into a
                            # generic "server connection" failure merely
                            # because the second profile RPC is temporarily
                            # unavailable. _profile() already resolved the
                            # canonical identity by Auth email.
                            existing_code = self.api._normalize_digits(
                                str(current_profile.get("national_code")
                                    or current_profile.get("username") or "")
                            ).strip()
                            existing_role = str(
                                current_profile.get("role") or ""
                            ).strip().lower()
                            if existing_code != normalized_identifier or not existing_role:
                                print("CANONICAL LOGIN PROFILE NOT FOUND; refusing login")
                                self.logout()
                                return False
                    except Exception as code_exc:
                        print("CANONICAL LOGIN PROFILE ERROR:", repr(code_exc))
                        existing_code = self.api._normalize_digits(
                            str(current_profile.get("national_code")
                                or current_profile.get("username") or "")
                        ).strip()
                        existing_role = str(current_profile.get("role") or "").strip().lower()
                        if existing_code != normalized_identifier or not existing_role:
                            self.logout()
                            return False

                resolved_role = str(current_profile.get("role") or "").strip().lower()
                if not resolved_role:
                    print("LOGIN PROFILE MISSING ROLE; refusing session")
                    self.logout()
                    return False
                self.session["profile"] = current_profile
                self.session.pop("login_identifier", None)
            except Exception as exc:
                print("PROFILE ENRICHMENT ERROR:", repr(exc))

        if self.session.get("canonical_role"):
            self.session["profile"]["role"] = self.session["canonical_role"]
        self.session["remember_me"] = bool(remember)
        self._load_tokens()

        if remember:
            return save_session(self.session)

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
