from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.app import App
from pathlib import Path
from threading import Thread
import json

from mobile.config import APP_NAME, SCHOOL_NAME, SCHOOL_YEAR, BACKGROUND_PATH, PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text, bundled_login_background

ROLE_ALIASES = {
    "admin":"manager","administrator":"manager","manager":"manager","مدیر":"manager","مدیریت":"manager",
    "executive":"executive","معاون اجرایی":"executive","educational":"educational","معاون آموزشی":"educational",
    "cultural":"cultural","پرورشی":"cultural","معاون پرورشی":"cultural","advisor":"advisor","counselor":"advisor","مشاور":"advisor",
    "teacher":"teacher","teacher_staff":"teacher","دبیر":"teacher","معلم":"teacher","student":"student","دانش‌آموز":"student","دانش آموز":"student",
    "parent":"parent","parent_guardian":"parent","guardian":"parent","ولی":"parent","اولیا":"parent"
}
ROLE_TITLES = {
    "manager":"مدیریت","executive":"معاون اجرایی","educational":"معاون آموزشی","cultural":"معاون پرورشی",
    "advisor":"مشاوره","teacher":"دبیر","student":"دانش‌آموز","parent":"ولی"