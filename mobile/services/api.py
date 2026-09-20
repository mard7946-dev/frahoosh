import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from mobile.config import SUPABASE_URL, SUPABASE_ANON_KEY, API_TIMEOUT


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
            return json.loads(self._body.decode("utf-8"))
        except Exception:
            return {}

    def text(self):
        return self._body.decode("utf-8", errors="replace")


def _request(method, url, headers=None, payload=None, params=None, timeout=15):
    if params:
        query = urlencode(params, doseq=True)
        url += ("&" if "?" in url else "?") + query
    req_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=req_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return _Response(response.status, response.read())
    except HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return _Response(exc.code, body)
    except URLError as exc:
        raise ApiError("ارتباط با سرور برقرار نشد: " + str(exc.reason)) from exc
    except TimeoutError as exc:
        raise ApiError("زمان ارتباط با سرور به پایان رسید.") from exc
    except OSError as exc:
        raise ApiError("خطای شبکه: " + str(exc)) from exc


class SupabaseClient:
    def __init__(self):
        self.url = (SUPABASE_URL or "").rstrip("/")
        self.key = SUPABASE_ANON_KEY or ""
        self.access_token = ""
        self.refresh_token = ""
        self.expires_in = None
        self.expires_at = None
        self.token_type = "bearer"

    @property
    def configured(self):
        return bool(self.url and self.key)

    def _headers(self, authenticated=False):
        headers = {"apikey": self.key, "Content-Type": "application/json"}
        if authenticated and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    @staticmethod
    def _normalize_digits(value):
        value = str(value or "")
        return value.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))

    def sign_in(self, identifier, password):
        identifier = self._normalize_digits(identifier).strip()
        password = password or ""
        if not identifier:
            raise ApiError("کد ملی را وارد کنید.")
        if not password:
            raise ApiError("رمز عبور را وارد کنید.")

        if not self.configured:
            raise ApiError("تنظیمات اتصال سرور در برنامه وجود ندارد.")

        if "@" in identifier:
            email = identifier
        else:
            if not identifier.isdigit() or len(identifier) != 10:
                raise ApiError("کد ملی باید ۱۰ رقم باشد.")
            email = self.resolve_email_by_national_code(identifier)
            if not email:
                raise ApiError("برای این کد ملی، حساب کاربری در سامانه پیدا نشد.")
        return self._password_auth(email, password)

    def _password_auth(self, email, password):
        response = _request(
            "POST", f"{self.url}/auth/v1/token?grant_type=password",
            headers=self._headers(), payload={"email": email, "password": password},
            timeout=API_TIMEOUT,
        )
        if not response.ok:
            raise ApiError(self._error(response, "کد ملی یا رمز عبور صحیح نیست."))
        data = response.json() or {}
        self.access_token = data.get("access_token") or ""
        self.refresh_token = data.get("refresh_token") or ""
        self.expires_in = data.get("expires_in")
        self.expires_at = data.get("expires_at")
        self.token_type = data.get("token_type") or "bearer"
        if not self.access_token:
            raise ApiError("سرور نشست معتبر ایجاد نکرد.")
        user = data.get("user") or {}
        profile = self._profile(user)
        profile.setdefault("email", user.get("email", email))
        return {
            "user": user,
            "profile": profile,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
        }

    def resolve_email_by_national_code(self, national_code):
        if not self.configured:
            raise ApiError("تنظیمات اتصال به سرور وجود ندارد.")
        national_code = self._normalize_digits(national_code).strip()
        if not national_code:
            return None
        response = _request(
            "POST", f"{self.url}/rest/v1/rpc/lookup_auth_email_by_national_code",
            headers=self._headers(False), payload={"p_national_code": national_code},
            timeout=API_TIMEOUT,
        )
        if response.ok:
            data = response.json()
            if isinstance(data, str):
                return data.strip() or None
            if isinstance(data, list) and data and isinstance(data[0], str):
                return data[0].strip() or None
            return None

        # Older Supabase projects may not yet have the RPC. If the canonical
        # account_settings table is readable to anon, use it as a compatibility
        # path instead of turning a missing function into a login failure.
        if response.status_code in (400, 404, 406):
            fallback = _request(
                "GET", f"{self.url}/rest/v1/account_settings",
                headers=self._headers(False),
                params={
                    "select": "email",
                    "national_code": f"eq.{national_code}",
                    "limit": "1",
                },
                timeout=API_TIMEOUT,
            )
            if fallback.ok:
                rows = fallback.json() or []
                if rows and isinstance(rows[0], dict):
                    email = str(rows[0].get("email") or "").strip()
                    if email:
                        return email
        raise ApiError(self._error(response, "حساب کاربری برای این کد ملی پیدا نشد."))

    def send_password_recovery(self, identifier):
        identifier = self._normalize_digits(identifier).strip()
        if not identifier:
            raise ApiError("نام کاربری یا کد ملی را وارد کنید.")
        if "@" in identifier:
            email = identifier
        else:
            if not identifier.isdigit() or len(identifier) != 10:
                raise ApiError("کد ملی باید ۱۰ رقم باشد.")
            email = self.resolve_email_by_national_code(identifier)
            if not email:
                raise ApiError("برای این کد ملی، حساب کاربری در سامانه پیدا نشد.")

        response = _request(
            "POST",
            f"{self.url}/auth/v1/recover",
            headers=self._headers(),
            payload={"email": email},
            timeout=API_TIMEOUT,
        )
        if not response.ok:
            raise ApiError(self._error(response, "ارسال لینک بازیابی رمز انجام نشد."))
        return True

    def get_user(self):
        if not self.configured or not self.access_token or self.access_token == "local-bootstrap-admin":
            return None
        response = _request("GET", f"{self.url}/auth/v1/user", headers=self._headers(True), timeout=API_TIMEOUT)
        if not response.ok:
            return None
        data = response.json() or {}
        return data if isinstance(data, dict) else None

    def validate_session(self):
        if self.access_token == "local-bootstrap-admin":
            return True
        user = self.get_user()
        return bool(user and user.get("id"))

    def _profile(self, user):
        user = user if isinstance(user, dict) else {}
        metadata = user.get("user_metadata") or {}
        profile = {
            key: metadata[key]
            for key in ("role", "display_name", "full_name", "username", "national_code", "first_name", "last_name", "linked_student_id", "linked_teacher_id", "linked_staff_id")
            if key in metadata
        }
        email = str(user.get("email") or "").strip()
        if not self.configured or not email:
            profile.setdefault("email", email)
            return profile
        try:
            response = _request(
                "GET", f"{self.url}/rest/v1/account_settings",
                headers=self._headers(True), params={"email": f"eq.{email}", "limit": "1"}, timeout=API_TIMEOUT,
            )
            if response.ok:
                rows = response.json() or []
                if rows and isinstance(rows[0], dict):
                    merged = dict(profile)
                    merged.update(rows[0])
                    return merged
        except Exception:
            pass
        profile.setdefault("email", email)
        profile.setdefault("username", email)
        profile.setdefault("display_name", email)
        return profile

    def refresh_access_token(self):
        if not self.configured or not self.refresh_token:
            return False
        response = _request(
            "POST", f"{self.url}/auth/v1/token?grant_type=refresh_token",
            headers=self._headers(), payload={"refresh_token": self.refresh_token}, timeout=API_TIMEOUT,
        )
        if not response.ok:
            self.access_token = ""
            self.refresh_token = ""
            return False
        data = response.json() or {}
        token = data.get("access_token") or ""
        if not token:
            self.access_token = ""
            self.refresh_token = ""
            return False
        self.access_token = token
        self.refresh_token = data.get("refresh_token") or self.refresh_token
        self.expires_in = data.get("expires_in")
        self.expires_at = data.get("expires_at")
        self.token_type = data.get("token_type") or self.token_type
        return True

    def _authenticated_request(self, method, url, payload=None, params=None, prefer=None):
        if not self.configured or not self.access_token:
            raise ApiError("نشست معتبر وجود ندارد.")
        headers = self._headers(True)
        if prefer:
            headers["Prefer"] = prefer
        response = _request(method, url, headers=headers, payload=payload, params=params or {}, timeout=API_TIMEOUT)
        if response.status_code == 401 and self.refresh_access_token():
            headers = self._headers(True)
            if prefer:
                headers["Prefer"] = prefer
            response = _request(method, url, headers=headers, payload=payload, params=params or {}, timeout=API_TIMEOUT)
        return response

    def table_select(self, table, params=None):
        response = self._authenticated_request("GET", f"{self.url}/rest/v1/{table}", params=params)
        if not response.ok:
            raise ApiError(self._error(response))
        return response.json()

    def table_insert(self, table, payload, return_representation=True):
        if not self.configured or not self.access_token:
            raise ApiError("نشست معتبر برای ثبت اطلاعات وجود ندارد.")
        response = self._authenticated_request("POST", f"{self.url}/rest/v1/{table}", payload=payload, prefer="return=representation" if return_representation else None)
        if not response.ok:
            raise ApiError(self._error(response))
        return response.json()

    def table_update(self, table, filters, payload):
        if not self.configured or not self.access_token:
            raise ApiError("نشست معتبر برای ویرایش اطلاعات وجود ندارد.")
        response = self._authenticated_request("PATCH", f"{self.url}/rest/v1/{table}", payload=payload, params=dict(filters or {}), prefer="return=representation")
        if not response.ok:
            raise ApiError(self._error(response))
        return response.json()

    def rpc(self, function_name, payload=None):
        if not self.configured or not self.access_token:
            raise ApiError("نشست معتبر برای اجرای عملیات وجود ندارد.")
        response = self._authenticated_request("POST", f"{self.url}/rest/v1/rpc/{function_name}", payload=payload or {})
        if not response.ok:
            raise ApiError(self._error(response))
        return response.json()

    def table_delete(self, table, filters):
        if not self.configured or not self.access_token:
            raise ApiError("نشست معتبر برای حذف اطلاعات وجود ندارد.")
        response = self._authenticated_request("DELETE", f"{self.url}/rest/v1/{table}", params=filters or {})
        if not response.ok:
            raise ApiError(self._error(response))
        return response.json()

    def _error(self, response, default="خطا در ارتباط با سرور"):
        data = response.json()
        if isinstance(data, dict):
            message = data.get("msg") or data.get("message") or data.get("error_description") or data.get("error")
            if message:
                text = str(message)
                lower = text.lower()
                if "invalid login credentials" in lower:
                    return "کد ملی یا رمز عبور صحیح نیست."
                if "email not confirmed" in lower:
                    return "حساب کاربری هنوز تأیید نشده است."
                return text
        return default

    def sign_out(self):
        if self.configured and self.access_token and self.access_token != "local-bootstrap-admin":
            try:
                _request("POST", f"{self.url}/auth/v1/logout", headers=self._headers(True), timeout=API_TIMEOUT)
            except Exception:
                pass
        self.access_token = ""
        self.refresh_token = ""
        self.expires_in = None
        self.expires_at = None
        self.token_type = "bearer"
        return True
