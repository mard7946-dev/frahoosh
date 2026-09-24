import json
from urllib.parse import urlencode
import requests
import certifi
from requests import RequestException

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
    """Perform a mobile-safe HTTPS request while preserving the complete Supabase client."""
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers or {},
            json=payload if payload is not None else None,
            params=params or None,
            timeout=timeout,
            verify=certifi.where(),
        )
        return _Response(response.status_code, response.content)
    except RequestException as exc:
        reason = str(exc).strip()
        lower = reason.lower()
        if "certificate verify failed" in lower:
            raise ApiError("گواهی امنیتی سرور قابل تأیید نیست.") from exc
        if "name or service not known" in lower or "nodename nor servname" in lower or "failed to resolve" in lower:
            raise ApiError("آدرس سرور پیدا نشد؛ تنظیمات Supabase را بررسی کنید.") from exc
        if "timed out" in lower or "timeout" in lower:
            raise ApiError("زمان ارتباط با سرور به پایان رسید.") from exc
        raise ApiError("ارتباط با سرور برقرار نشد: " + (reason or "خطای شبکه")) from exc
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
            return self._password_auth(identifier, password)

        if not identifier.isdigit() or len(identifier) != 10:
            raise ApiError("کد ملی باید ۱۰ رقم باشد.")

        # A national code is normally unique. During onboarding it can
        # temporarily collide (for example when several test accounts share
        # one placeholder code). Try every matching Auth email so the password
        # identifies the intended account instead of arbitrary LIMIT 1 order.
        emails = self.resolve_emails_by_national_code(identifier)
        if not emails:
            raise ApiError("برای این کد ملی، حساب کاربری در سامانه پیدا نشد.")

        last_error = None
        for email in emails:
            try:
                return self._password_auth(email, password)
            except ApiError as exc:
                last_error = exc
                if "کد ملی یا رمز عبور صحیح نیست" not in str(exc):
                    raise
        raise last_error or ApiError("کد ملی یا رمز عبور صحیح نیست.")

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

    def resolve_emails_by_national_code(self, national_code):
        if not self.configured:
            raise ApiError("تنظیمات اتصال به سرور وجود ندارد.")
        national_code = self._normalize_digits(national_code).strip()
        if not national_code:
            return []

        response = _request(
            "POST", f"{self.url}/rest/v1/rpc/lookup_auth_emails_by_national_code",
            headers=self._headers(False), payload={"p_national_code": national_code},
            timeout=API_TIMEOUT,
        )
        if response.ok:
            data = response.json() or []
            emails = []
            if isinstance(data, str):
                emails = [data]
            elif isinstance(data, list):
                for row in data:
                    if isinstance(row, str):
                        emails.append(row)
                    elif isinstance(row, dict):
                        value = row.get("email") or row.get("auth_email")
                        if value:
                            emails.append(str(value))
            return list(dict.fromkeys(x.strip() for x in emails if str(x).strip()))

        if response.status_code in (400, 404, 406):
            fallback = _request(
                "GET", f"{self.url}/rest/v1/account_settings",
                headers=self._headers(False),
                params={"select": "email", "national_code": f"eq.{national_code}"},
                timeout=API_TIMEOUT,
            )
            if fallback.ok:
                rows = fallback.json() or []
                emails = [str(row.get("email") or "").strip() for row in rows if isinstance(row, dict)]
                emails = list(dict.fromkeys(x for x in emails if x))
                if emails:
                    return emails

            single = _request(
                "POST", f"{self.url}/rest/v1/rpc/lookup_auth_email_by_national_code",
                headers=self._headers(False), payload={"p_national_code": national_code},
                timeout=API_TIMEOUT,
            )
            if single.ok:
                data = single.json()
                if isinstance(data, str) and data.strip():
                    return [data.strip()]
                if isinstance(data, list):
                    values = []
                    for row in data:
                        if isinstance(row, str) and row.strip():
                            values.append(row.strip())
                        elif isinstance(row, dict):
                            value = row.get("email") or row.get("auth_email")
                            if value:
                                values.append(str(value).strip())
                    return list(dict.fromkeys(x for x in values if x))

        raise ApiError(self._error(response, "حساب کاربری برای این کد ملی پیدا نشد."))

    def resolve_email_by_national_code(self, national_code):
        emails = self.resolve_emails_by_national_code(national_code)
        return emails[0] if emails else None

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
                    # account_settings keeps extensible role/link metadata in preferences.
                    # Promote canonical values so AppState.role does not silently fall back to student.
                    prefs = rows[0].get("preferences")
                    if isinstance(prefs, dict):
                        for key in ("role", "linked_student_id", "linked_teacher_id", "linked_staff_id"):
                            if prefs.get(key) not in (None, ""):
                                merged[key] = prefs.get(key)
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
            raise ApiError(self._data_error(response, f"خواندن جدول «{table}» انجام نشد."))
        return response.json()

    def table_insert(self, table, payload, return_representation=True):
        if not self.configured or not self.access_token:
            raise ApiError("نشست معتبر برای ثبت اطلاعات وجود ندارد.")
        response = self._authenticated_request("POST", f"{self.url}/rest/v1/{table}", payload=payload, prefer="return=representation" if return_representation else None)
        if not response.ok:
            raise ApiError(self._data_error(response, f"ثبت رکورد در جدول «{table}» انجام نشد."))
        return response.json()

    def table_update(self, table, filters, payload):
        if not self.configured or not self.access_token:
            raise ApiError("نشست معتبر برای ویرایش اطلاعات وجود ندارد.")
        response = self._authenticated_request("PATCH", f"{self.url}/rest/v1/{table}", payload=payload, params=dict(filters or {}), prefer="return=representation")
        if not response.ok:
            raise ApiError(self._data_error(response, f"ویرایش رکورد جدول «{table}» انجام نشد."))
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
            raise ApiError(self._data_error(response, f"حذف رکورد جدول «{table}» انجام نشد."))
        return response.json()

    def _data_error(self, response, default):
        """Keep backend CRUD failures visible enough to fix schema/RLS issues."""
        data = response.json()
        code = ""
        message = ""
        detail = ""
        hint = ""
        if isinstance(data, dict):
            code = str(data.get("code") or "").strip()
            message = str(data.get("message") or data.get("msg") or data.get("error_description") or data.get("error") or "").strip()
            detail = str(data.get("details") or data.get("detail") or "").strip()
            hint = str(data.get("hint") or "").strip()
        if response.status_code in (401, 403):
            prefix = "دسترسی به جدول مجاز نیست."
        elif response.status_code == 404:
            prefix = "جدول یا ستون در Data API پیدا نشد."
        elif response.status_code in (400, 406):
            prefix = "ساختار درخواست با جدول سامانه سازگار نیست."
        elif response.status_code == 409:
            prefix = "ثبت رکورد به علت تعارض داده انجام نشد."
        elif response.status_code >= 500:
            prefix = "سرور هنگام کار با جدول خطا داد."
        else:
            prefix = default
        diagnostics = " | ".join(x for x in (message, detail, hint, code) if x)
        return f"{prefix} {diagnostics}".strip() if diagnostics else default

    def _error(self, response, default="خطا در ارتباط با سرور"):
        data = response.json()
        message = ""
        if isinstance(data, dict):
            message = str(data.get("msg") or data.get("message") or data.get("error_description") or data.get("error") or "").strip()
        lower = message.lower()
        if "invalid login credentials" in lower:
            return "کد ملی یا رمز عبور صحیح نیست."
        if "email not confirmed" in lower:
            return "حساب کاربری هنوز تأیید نشده است."
        if response.status_code in (401, 403):
            return "دسترسی ورود به سامانه مجاز نیست."
        if response.status_code in (404, 406) and "rpc" in lower:
            return "سرویس ورود با کد ملی روی سرور فعال نشده است."
        if response.status_code in (400, 404, 406):
            return "اطلاعات ورود در سامانه پیدا نشد."
        if response.status_code >= 500:
            return "سرور سامانه موقتاً پاسخ نمی‌دهد."
        # Never send raw HTTP/ASCII diagnostics to the Persian UI.
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
