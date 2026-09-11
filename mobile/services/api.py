import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from mobile.config import (
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    API_TIMEOUT,
)


class ApiError(RuntimeError):
    pass


class _Response:

    def __init__(self, status, body):
        self.status_code = status
        self._body = body or b""

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        if not self._body:
            return {}

        try:
            return json.loads(
                self._body.decode("utf-8")
            )
        except Exception:
            return {}

    def text(self):
        return self._body.decode(
            "utf-8",
            errors="replace"
        )


def _request(
    method,
    url,
    headers=None,
    payload=None,
    params=None,
    timeout=15,
):

    if params:
        query = urlencode(
            params,
            doseq=True
        )
        url += (
            "&" if "?" in url else "?"
        ) + query

    data = None
    req_headers = dict(headers or {})

    if payload is not None:
        data = json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")

        req_headers["Content-Type"] = (
            "application/json"
        )

    request = Request(
        url,
        data=data,
        headers=req_headers,
        method=method,
    )

    try:

        with urlopen(
            request,
            timeout=timeout
        ) as response:

            return _Response(
                response.status,
                response.read(),
            )

    except HTTPError as exc:

        try:
            body = exc.read()
        except Exception:
            body = b""

        return _Response(
            exc.code,
            body,
        )

    except URLError as exc:

        raise ApiError(
            "خطای اتصال به سرور: "
            + str(exc.reason)
        ) from exc

    except TimeoutError as exc:

        raise ApiError(
            "زمان اتصال به سرور به پایان رسید."
        ) from exc

    except OSError as exc:

        raise ApiError(
            "خطای شبکه: "
            + str(exc)
        ) from exc


class SupabaseClient:

    def __init__(self):

        self.url = (
            SUPABASE_URL or ""
        ).rstrip("/")

        self.key = (
            SUPABASE_ANON_KEY or ""
        )

        self.access_token = ""
        self.refresh_token = ""
        self.expires_in = None
        self.expires_at = None
        self.token_type = "bearer"

    @property
    def configured(self):
        return bool(
            self.url
            and self.key
        )

    def _headers(self, authenticated=False):

        headers = {
            "apikey": self.key,
            "Content-Type": "application/json",
        }

        if (
            authenticated
            and self.access_token
        ):
            headers["Authorization"] = (
                f"Bearer {self.access_token}"
            )

        return headers

    # -------------------------------------------------
    # AUTHENTICATION
    # -------------------------------------------------

    def sign_in(
        self,
        identifier,
        password
    ):

        if not self.configured:
            raise ApiError(
                "اتصال سرور در این نسخه تنظیم نشده است."
            )

        identifier = (
            identifier or ""
        ).strip()

        password = password or ""

        if not identifier:
            raise ApiError(
                "کد ملی را وارد کنید."
            )

        if not password:
            raise ApiError(
                "رمز عبور را وارد کنید."
            )

        # کاربر طبق طراحی فراهوش با کد ملی وارد می‌شود.
        # اگر ایمیل وارد شود نیز برای سازگاری قدیمی پذیرفته می‌شود.
        if "@" in identifier:

            email = identifier

        else:

            if not identifier.isdigit():
                raise ApiError(
                    "کد ملی باید فقط شامل اعداد باشد."
                )

            if len(identifier) != 10:
                raise ApiError(
                    "کد ملی باید ۱۰ رقم باشد."
                )

            email = (
                self.resolve_email_by_national_code(
                    identifier
                )
            )

            if not email:
                raise ApiError(
                    "کاربری با این کد ملی پیدا نشد."
                )

        response = _request(
            "POST",
            f"{self.url}/auth/v1/token"
            "?grant_type=password",
            headers=self._headers(),
            payload={
                "email": email,
                "password": password,
            },
            timeout=API_TIMEOUT,
        )

        if not response.ok:

            raise ApiError(
                self._error(
                    response,
                    "کد ملی یا رمز عبور صحیح نیست."
                )
            )

        data = response.json() or {}

        self.access_token = (
            data.get("access_token")
            or ""
        )

        self.refresh_token = (
            data.get("refresh_token")
            or ""
        )

        self.expires_in = (
            data.get("expires_in")
        )

        self.expires_at = (
            data.get("expires_at")
        )

        self.token_type = (
            data.get("token_type")
            or "bearer"
        )

        if not self.access_token:
            raise ApiError(
                "سرور نشست معتبر ایجاد نکرد."
            )

        user = (
            data.get("user")
            or {}
        )

        profile = self._profile(user)

        # اگر national_code در account_settings موجود باشد
        # به پروفایل اضافه می‌شود.
        profile.setdefault(
            "email",
            user.get("email", email)
        )

        return {
            "user": user,
            "profile": profile,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
        }

    def resolve_email_by_national_code(
        self,
        national_code
    ):

        if not self.configured:
            raise ApiError(
                "اتصال سرور فعال نیست."
            )

        national_code = str(
            national_code or ""
        ).strip()

        # مسیر اصلی:
        # account_settings.national_code
        tables = [
            "account_settings",
        ]

        for table in tables:

            try:

                response = _request(
                    "GET",
                    f"{self.url}/rest/v1/{table}",
                    headers=self._headers(),
                    params={
                        "national_code": (
                            f"eq.{national_code}"
                        ),
                        "select": (
                            "email"
                        ),
                        "limit": "1",
                    },
                    timeout=API_TIMEOUT,
                )

                if response.ok:

                    rows = (
                        response.json()
                        or []
                    )

                    if (
                        isinstance(rows, list)
                        and rows
                        and isinstance(
                            rows[0],
                            dict
                        )
                    ):

                        email = rows[0].get(
                            "email"
                        )

                        if email:
                            return email

            except Exception:
                continue

        return None

    # -------------------------------------------------
    # PROFILE
    # -------------------------------------------------

    def _profile(self, user):

        user = (
            user
            if isinstance(user, dict)
            else {}
        )

        metadata = (
            user.get("user_metadata")
            or {}
        )

        profile = {}

        for key in (
            "role",
            "display_name",
            "full_name",
            "username",
            "national_code",
            "first_name",
            "last_name",
        ):

            if key in metadata:
                profile[key] = (
                    metadata[key]
                )

        email = (
            user.get("email")
            or ""
        )

        if not self.configured:
            profile.setdefault(
                "email",
                email
            )
            return profile

        # account_settings منبع اصلی پروفایل برنامه
        try:

            response = _request(
                "GET",
                f"{self.url}/rest/v1/account_settings",
                headers=self._headers(True),
                params={
                    "email": f"eq.{email}",
                    "limit": "1",
                },
                timeout=API_TIMEOUT,
            )

            if response.ok:

                rows = (
                    response.json()
                    or []
                )

                if (
                    rows
                    and isinstance(
                        rows[0],
                        dict
                    )
                ):

                    merged = dict(profile)

                    merged.update(
                        rows[0]
                    )

                    return merged

        except Exception:
            pass

        profile.setdefault(
            "email",
            email
        )

        profile.setdefault(
            "username",
            email
        )

        profile.setdefault(
            "display_name",
            email
        )

        return profile

    # -------------------------------------------------
    # TOKEN
    # -------------------------------------------------

    def refresh_access_token(self):

        if (
            not self.configured
            or not self.refresh_token
        ):
            return False

        response = _request(
            "POST",
            f"{self.url}/auth/v1/token"
            "?grant_type=refresh_token",
            headers=self._headers(),
            payload={
                "refresh_token":
                    self.refresh_token
            },
            timeout=API_TIMEOUT,
        )

        if not response.ok:

            self.access_token = ""
            self.refresh_token = ""
            self.expires_in = None
            self.expires_at = None

            return False

        data = response.json() or {}

        token = (
            data.get("access_token")
            or ""
        )

        if not token:

            self.access_token = ""
            self.refresh_token = ""

            return False

        self.access_token = token

        new_refresh = (
            data.get("refresh_token")
        )

        if new_refresh:
            self.refresh_token = (
                new_refresh
            )

        self.expires_in = (
            data.get("expires_in")
        )

        self.expires_at = (
            data.get("expires_at")
        )

        self.token_type = (
            data.get("token_type")
            or self.token_type
            or "bearer"
        )

        return True

    # -------------------------------------------------
    # GENERIC TABLE METHODS
    # -------------------------------------------------

    def table_select(
        self,
        table,
        params=None
    ):

        if not self.configured:
            raise ApiError(
                "اتصال سرور فعال نیست."
            )

        if not self.access_token:
            raise ApiError(
                "نشست معتبر وجود ندارد."
            )

        table = str(
            table or ""
        ).strip()

        if not table:
            raise ApiError(
                "نام جدول مشخص نیست."
            )

        request_params = (
            params
            if params is not None
            else {
                "select": "*",
                "limit": "50",
            }
        )

        response = _request(
            "GET",
            f"{self.url}/rest/v1/{table}",
            headers=self._headers(True),
            params=request_params,
            timeout=API_TIMEOUT,
        )

        if (
            response.status_code == 401
            and self.refresh_token
        ):

            if self.refresh_access_token():

                response = _request(
                    "GET",
                    f"{self.url}/rest/v1/{table}",
                    headers=self._headers(True),
                    params=request_params,
                    timeout=API_TIMEOUT,
                )

        if not response.ok:

            raise ApiError(
                self._error(
                    response
                )
            )

        return response.json()

    def table_insert(
        self,
        table,
        payload,
        return_representation=True
    ):

        if not self.configured:
            raise ApiError(
                "اتصال سرور فعال نیست."
            )

        if not self.access_token:
            raise ApiError(
                "نشست معتبر وجود ندارد."
            )

        headers = self._headers(True)

        if return_representation:
            headers["Prefer"] = (
                "return=representation"
            )

        response = _request(
            "POST",
            f"{self.url}/rest/v1/{table}",
            headers=headers,
            payload=payload,
            timeout=API_TIMEOUT,
        )

        if not response.ok:
            raise ApiError(
                self._error(response)
            )

        return response.json()

    def table_update(
        self,
        table,
        filters,
        payload
    ):

        if not self.configured:
            raise ApiError(
                "اتصال سرور فعال نیست."
            )

        if not self.access_token:
            raise ApiError(
                "نشست معتبر وجود ندارد."
            )

        params = dict(
            filters or {}
        )

        headers = self._headers(True)

        headers["Prefer"] = (
            "return=representation"
        )

        response = _request(
            "PATCH",
            f"{self.url}/rest/v1/{table}",
            headers=headers,
            params=params,
            payload=payload,
            timeout=API_TIMEOUT,
        )

        if not response.ok:
            raise ApiError(
                self._error(response)
            )

        return response.json()

    def table_delete(
        self,
        table,
        filters
    ):

        if not self.configured:
            raise ApiError(
                "اتصال سرور فعال نیست."
            )

        if not self.access_token:
            raise ApiError(
                "نشست معتبر وجود ندارد."
            )

        response = _request(
            "DELETE",
            f"{self.url}/rest/v1/{table}",
            headers=self._headers(True),
            params=filters or {},
            timeout=API_TIMEOUT,
        )

        if not response.ok:
            raise ApiError(
                self._error(response)
            )

        return True

    # -------------------------------------------------
    # ERROR
    # -------------------------------------------------

    def _error(
        self,
        response,
        default="خطای سرور"
    ):

        try:

            payload = (
                response.json()
                or {}
            )

            if isinstance(
                payload,
                dict
            ):

                return (
                    payload.get("message")
                    or payload.get(
                        "error_description"
                    )
                    or payload.get("msg")
                    or payload.get("hint")
                    or payload.get("details")
                    or default
                )

        except Exception:
            pass

        return (
            f"{default} "
            f"({response.status_code})"
        )

    # -------------------------------------------------
    # SIGN OUT
    # -------------------------------------------------

    def sign_out(self):

        if (
            self.configured
            and self.access_token
        ):

            try:

                _request(
                    "POST",
                    f"{self.url}/auth/v1/logout",
                    headers=self._headers(True),
                    timeout=API_TIMEOUT,
                )

            except Exception:
                pass

        self.access_token = ""
        self.refresh_token = ""
        self.expires_in = None
        self.expires_at = None
        self.token_type = "bearer"
    
                                    
