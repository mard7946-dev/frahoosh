import json
from urllib.parse import urlencode
import requests
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
    """Perform a mobile-safe HTTPS request.

    requests is already bundled by Buildozer and uses the Python CA bundle,
    which is more reliable on Android than urllib's platform certificate
    lookup. Keep HTTP errors as responses so Supabase JSON errors remain
    distinguishable from genuine network failures.
    """
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers or {},
            json=payload if payload is not None else None,
            params=params or None,
            timeout=timeout,
        )
        return _Response(response.status_code, response.content)
    except RequestException as exc:
        reason = str(exc).strip()
        if "certificate verify failed" in reason.lower():
            raise ApiError("گواهی امنیتی سرور قابل تأیید نیست.") from exc
        if "name or service not known" in reason.lower() or "nodename nor servname" in reason.lower() or "failed to resolve" in reason.lower():
            raise ApiError("آدرس سرور پیدا نشد؛ تنظیمات Supabase را بررسی کنید.") from exc
        if "timed out" in reason.lower() or "timeout" in reason.lower():
            raise ApiError("زمان ارتباط با سرور به پایان رسید.") from exc
        raise ApiError("ارتباط با سرور برقرار نشد: " + (reason or "خطای شبکه")) from exc
    except OSError as exc:
        raise ApiError("خطای شبکه: " + str(exc)) from exc

