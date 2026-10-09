"""Small dependency-free Jalali (Shamsi) helpers for display."""
from datetime import datetime, timedelta, timezone

_TEHRAN = timezone(timedelta(hours=3, minutes=30))
_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
MONTHS = ("فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
          "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند")


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100)
            + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1])
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def fa_digits(value):
    return str(value).translate(_FA_DIGITS)


def parse_ts(value):
    """Parse a Supabase timestamptz string into an aware datetime (or None)."""
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        try:
            dt = datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_TEHRAN)


def jalali_date(dt):
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    return f"{fa_digits(jd)} {MONTHS[jm - 1]} {fa_digits(jy)}"


def jalali_time(dt):
    return fa_digits(dt.strftime("%H:%M"))


def day_key(dt):
    return (dt.year, dt.month, dt.day)
