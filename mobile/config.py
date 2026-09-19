import json
import os
from pathlib import Path

APP_NAME = "فراهوش"
APP_VERSION = "1.6.0"
APP_SLOGAN = "یادگیری هوشمند- مدرسه ای یکپارچه- دانش آموز خلاق"
LOGIN_USERNAME_HINT = "نام کاربری"
LOGIN_PASSWORD_HINT = "رمز عبور"
SYSTEM_TITLE = "سامانه مدیریت هوشمند یکپارچه مدرسه"
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONT_REGULAR = ASSETS_DIR / "NotoSansArabic-Regular.ttf"
FONT_BOLD = ASSETS_DIR / "NotoSansArabic-Bold.ttf"
LOGO_PATH = str(ASSETS_DIR / "frahoosh_logo.png")


def _load_runtime_config():
    candidates = [BASE_DIR / "runtime_config.json", Path.cwd() / "mobile" / "runtime_config.json", Path.cwd() / "runtime_config.json"]
    for path in candidates:
        try:
            if path.is_file():
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    return data
        except Exception as exc:
            print("RUNTIME CONFIG ERROR:", repr(exc))
    return {}


_RUNTIME = _load_runtime_config()

# Defaults keep the demo usable even when runtime_config.json is not generated.
SCHOOL_NAME = str(os.environ.get("FRAHOOSH_SCHOOL_NAME") or _RUNTIME.get("school_name") or _RUNTIME.get("FRAHOOSH_SCHOOL_NAME") or "دبیرستان سردار شهید حاجی زاده ۲").strip()
SCHOOL_ID = str(os.environ.get("FRAHOOSH_SCHOOL_ID") or _RUNTIME.get("school_id") or _RUNTIME.get("FRAHOOSH_SCHOOL_ID") or "").strip()
SCHOOL_YEAR = str(os.environ.get("FRAHOOSH_SCHOOL_YEAR") or _RUNTIME.get("school_year") or _RUNTIME.get("FRAHOOSH_SCHOOL_YEAR") or "۱۴۰۵-۱۴۰۶").strip()
WEB_URL = str(os.environ.get("FRAHOOSH_WEB_URL") or _RUNTIME.get("web_url") or _RUNTIME.get("FRAHOOSH_WEB_URL") or "https://frahoosh.ir").strip().rstrip("/")

PRIMARY = (0.12, 0.35, 0.62, 1)
SECONDARY = (0.35, 0.40, 0.48, 1)
SUCCESS = (0.10, 0.55, 0.30, 1)
ERROR = (0.75, 0.12, 0.12, 1)
WHITE = (1, 1, 1, 1)
CARD = (0.97, 0.98, 1.0, 1)
BORDER = (0.80, 0.84, 0.90, 1)
# Always resolve the bundled portrait artwork from the APK itself. Runtime/local paths can point to a desktop file that does not exist on Android.
_BACKGROUND_CANDIDATES = [
    ASSETS_DIR / "frahoosh_background_final.jpg",
    ASSETS_DIR / "frahoosh_background_final_small.jpg",
    ASSETS_DIR / "frahoosh_bg_270.jpg",
    ASSETS_DIR / "frahoosh_background.jpg",
    ASSETS_DIR / "frahoosh_login_background.jpg",
]
BACKGROUND_PATH = str(next((p for p in _BACKGROUND_CANDIDATES if p.is_file()), ASSETS_DIR / "frahoosh_background.jpg"))
API_TIMEOUT = 15
SUPABASE_URL = str(os.environ.get("FRAHOOSH_SUPABASE_URL") or _RUNTIME.get("supabase_url") or _RUNTIME.get("FRAHOOSH_SUPABASE_URL") or "").strip()
SUPABASE_ANON_KEY = str(os.environ.get("FRAHOOSH_SUPABASE_ANON_KEY") or _RUNTIME.get("supabase_anon_key") or _RUNTIME.get("FRAHOOSH_SUPABASE_ANON_KEY") or "").strip()
PAYMENT_GATEWAY_URL = str(os.environ.get("FRAHOOSH_PAYMENT_GATEWAY_URL") or _RUNTIME.get("payment_gateway_url") or _RUNTIME.get("FRAHOOSH_PAYMENT_GATEWAY_URL") or "").strip()
