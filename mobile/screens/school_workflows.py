from datetime import datetime, timezone, timedelta
import random
from pathlib import Path
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from mobile.ui import font_name, rtl_text, fa_display
from mobile.config import PRIMARY, SECONDARY, SUCCESS, ERROR, WHITE, SCHOOL_NAME, SCHOOL_YEAR

def role_of(state):
    profile=getattr(state,"profile",{}) or {}\n    candidates=[getattr(state,"role",None),profile.get("role"),profile.get("user_role"),profile.get("school_role"),profile.get("user_type"),profile.get("account_type")]\n    raw=next((str(v).strip().lower() for v in candidates if str(v or "").strip()),"student")\n    return {\n        "admin":"manager","administrator":"manager","principal":"manager","manager":"manager","management":"manager","school_management":"manager","مدیر":"manager","مدیریت":"manager","مدیریت مدرسه":"manager",\n        "معاون آموزشی":"educational","educational":"educational","educational_deputy":"educational",\n        "معاون اجرایی":"executive","اجرایی":"executive","executive":"executive","executive_deputy":"executive",\n        "معاون پرورشی":"cultural","پرورشی":"cultural","cultural":"cultural","cultural_deputy":"cultural",\n        "مشاور":"counselor","مشاوره":"counselor","counselor":"counselor","counseling":"counselor",\n        "دبیر":"teacher","teacher":"teacher","کادر":"staff","staff":"staff","ولی":"parent","اولیا":"parent","parent":"parent","دانش‌آموز":"student","دانش آموز":"student","student":"student"\n    }.get(raw,raw)
