import json
import os
from pathlib import Path

APP_NAME = "فراهوش"
SYSTEM_TITLE = "سامانه هوشمند آموزشی یکپارچه مدرسه"
SCHOOL_NAME = "دبیرستان سردار شهید حاجی‌زاده ۲"

PRIMARY = (0.12, 0.35, 0.62, 1)
SECONDARY = (0.35, 0.40, 0.48, 1)
SUCCESS = (0.10, 0.55, 0.30, 1)
ERROR = (0.75, 0.12, 0.12, 1)
WHITE = (1, 1, 1, 1)
CARD = (0.97, 0.98, 1.0, 1)
BORDER = (0.80, 0.84, 0.90, 1)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONT_REGULAR = ASSETS_DIR / "NotoSansArabic-Regular.ttf"
FONT_BOLD = ASSETS_DIR / "NotoSansArabic-Bold.ttf"
# The current repository does not contain a background image. Keep this
# optional so Dashboard can always be imported and displayed.
BACKGROUND_PATH = ""

API_TIMEOUT = 15


def _load_runtime_config():
    candidates = [
        BASE_DIR / "runtime_config.json",
        Path.cwd() / "mobile" / "runtime_config.json",
        Path.cwd() / "runtime_config.json",
    ]

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

SUPABASE_URL = str(
    os.environ.get("FRAHOOSH_SUPABASE_URL")
    or _RUNTIME.get("supabase_url")
    or _RUNTIME.get("FRAHOOSH_SUPABASE_URL")
    or ""
).strip()

SUPABASE_ANON_KEY = str(
    os.environ.get("FRAHOOSH_SUPABASE_ANON_KEY")
    or _RUNTIME.get("supabase_anon_key")
    or _RUNTIME.get("FRAHOOSH_SUPABASE_ANON_KEY")
    or ""
).strip()

SCHOOL_ID = str(
    os.environ.get("FRAHOOSH_SCHOOL_ID")
    or _RUNTIME.get("school_id")
    or _RUNTIME.get("FRAHOOSH_SCHOOL_ID")
    or ""
).strip()

SCHOOL_YEAR = str(
    os.environ.get("FRAHOOSH_SCHOOL_YEAR")
    or _RUNTIME.get("school_year")
    or _RUNTIME.get("FRAHOOSH_SCHOOL_YEAR")
    or ""
).strip()
