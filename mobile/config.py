from mobile.services.api import SupabaseClient
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
            self.api = SupabaseClient()
        except Exception as exc:
            print(
                "SUPABASE CLIENT ERROR:",
                repr(exc)
            )
            self.api = None

        try:
            self.session = (
                load_session()
                or {}
            )
        except Exception as exc:
            print(
                "SESSION LOAD ERROR:",
                repr(exc)
            )
            self.session = {}

        self._load_tokens()

    # -----------------------------------------------
    # TOKEN
    # -----------------------------------------------

    def _load_tokens(self):

        if self.api is None:
            return

        session = (
            self.session
            if isinstance(
                self.session,
                dict
            )
            else {}
        )

        self.api.access_token = (
            session.get(
                "access_token",
                ""
            )
            or ""
        )

        self.api.refresh_token = (
            session.get(
                "refresh_token",
                ""
            )
            or ""
        )

        self.api.expires_in = (
            session.get(
                "expires_in"
            )
        )

        self.api.expires_at = (
            session.get(
                "expires_at"
            )
        )

        self.api.token_type = (
            session.get(
                "token_type",
                "bearer"
            )
            or "bearer"
        )

    # -----------------------------------------------
    # AUTH STATE
    # -----------------------------------------------

    @property
    def logged_in(self):

        return bool(
            self.api is not None
            and isinstance(
                self.session,
                dict
            )
            and self.session
            and self.api.access_token
        )

    @property
    def profile(self):

        if not isinstance(
            self.session,
            dict
        ):
            return {}

        profile = (
            self.session.get(
                "profile"
            )
            or {}
        )

        return (
            profile
            if isinstance(
                profile,
                dict
            )
            else {}
        )

    @property
    def user(self):

        if not isinstance(
            self.session,
            dict
        ):
            return {}

        user = (
            self.session.get(
                "user"
            )
            or {}
        )

        return (
            user
            if isinstance(
                user,
                dict
            )
            else {}
        )

    @property
    def role(self):

        profile = self.profile

        role = (
            profile.get("role")
            or self.user.get("role")
            or "student"
        )

        return str(
            role
        ).strip().lower()

    @property
    def national_code(self):

        profile = self.profile

        return str(
            profile.get(
                "national_code"
            )
            or profile.get(
                "nationalcode"
            )
            or profile.get(
                "national_id"
            )
            or ""
        ).strip()

    @property
    def display_name(self):

        profile = self.profile

        name = (
            profile.get(
                "display_name"
            )
            or profile.get(
                "full_name"
            )
            or profile.get(
                "name"
            )
            or self.user.get(
                "user_metadata",
                {}
            ).get(
                "full_name"
            )
            if isinstance(
                self.user.get(
                    "user_metadata",
                    {}
                ),
                dict
            )
            else None
        )

        if not name:
            name = (
                profile.get(
                    "first_name"
                )
                or self.user.get(
                    "email"
                )
                or "کاربر فراهوش"
            )

        return str(name)

    # -----------------------------------------------
    # SESSION
    # -----------------------------------------------

    def set_session(
        self,
        payload
    ):

        payload = (
            payload
            if isinstance(
                payload,
                dict
            )
            else {}
        )

        access_token = (
            payload.get(
                "access_token"
            )
            or ""
        )

        if not access_token:

            self.session = {}

            if self.api is not None:

                self.api.access_token = ""
                self.api.refresh_token = ""

            clear_session()

            return False

        self.session = dict(
            payload
        )

        saved = save_session(
            self.session
        )

        self._load_tokens()

        return bool(saved)

    def persist_refreshed_token(self):

        if (
            self.api is None
            or not self.api.access_token
        ):
            return False

        if not isinstance(
            self.session,
            dict
        ):
            self.session = {}

        self.session[
            "access_token"
        ] = self.api.access_token

        if self.api.refresh_token:
            self.session[
                "refresh_token"
            ] = self.api.refresh_token

        if self.api.expires_in is not None:
            self.session[
                "expires_in"
            ] = self.api.expires_in

        if self.api.expires_at is not None:
            self.session[
                "expires_at"
            ] = self.api.expires_at

        if self.api.token_type:
            self.session[
                "token_type"
            ] = self.api.token_type

        return save_session(
            self.session
        )

    def refresh_session(self):

        if (
            self.api is None
            or not self.api.refresh_token
        ):
            return False

        try:

            refreshed = (
                self.api.refresh_access_token()
            )

        except Exception as exc:

            print(
                "TOKEN REFRESH ERROR:",
                repr(exc)
            )

            return False

        if not refreshed:
            return False

        return self.persist_refreshed_token()

    def logout(self):

        if self.api is not None:

            try:
                self.api.sign_out()
            except Exception:
                pass

            self.api.access_token = ""
            self.api.refresh_token = ""
            self.api.expires_in = None
            self.api.expires_at = None
            self.api.token_type = "bearer"

        clear_session()

        self.session = {}

        return True
