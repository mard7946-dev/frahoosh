from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
from kivy.metrics import dp
from kivy.resources import resource_find
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from mobile.config import (
    APP_NAME, SCHOOL_NAME, APP_SLOGAN, SYSTEM_TITLE, LOGIN_USERNAME_HINT, LOGIN_PASSWORD_HINT,
    SUCCESS, WHITE, ERROR,
)
from mobile.ui import font_name, title_font_name, fa_display, PersianTextInput, CredentialTextInput



INK = (0.055, 0.10, 0.18, 1)
MUTED = (0.39, 0.46, 0.56, 1)
BLUE = (0.06, 0.43, 0.86, 1)
BLUE_DARK = (0.035, 0.24, 0.58, 1)
FIELD_BG = (0.965, 0.978, 0.995, 1)
BORDER = (0.84, 0.88, 0.94, 1)
WHITE = (1, 1, 1, 1)

class LoginScreen(Screen):
    # Credential fields use LTR direction for account identifiers.
    """Responsive Android login. Authentication and remember-me use the real app services."""

    def __init__(self, app_state=None, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._busy = False
        self._auto_login_checked = False
        self._build()

    def label(self, value, size="11sp", color=WHITE, bold=False, halign="right"):
        w = Label(
            text=fa_display(str(value)),
            font_name=font_name(),
            font_size=size,
            color=color,
            bold=bold,
            halign=halign,
            valign="middle",
        )
        w.bind(size=lambda o, v: setattr(o, "text_size", v))
        return w

    def _field(self, hint, password=False):
        common = dict(
            hint_text=str(hint), font_name=font_name(), font_size="13sp", multiline=False,
            size_hint_y=None, height=dp(46), halign="right", padding=[dp(13), dp(9)],
            background_normal="", background_active="", background_color=(0, 0, 0, 0),
            foreground_color=INK, hint_text_color=(0.56, 0.62, 0.70, 1),
            cursor_color=BLUE, selection_color=(0.10, 0.43, 0.86, 0.18),
        )
        if password:
            field = CredentialTextInput(masked=True, **common)
        else:
            field = PersianTextInput(password=False, **common)
        with field.canvas.before:
            Color(*FIELD_BG)
            field._bg = RoundedRectangle(radius=[dp(13)])
            Color(*BORDER)
            field._border = Line(rounded_rectangle=(0, 0, 0, 0, dp(13)), width=0.8)
        def sync(*_):
            field._bg.pos = field.pos; field._bg.size = field.size
            field._border.rounded_rectangle = (field.x, field.y, field.width, field.height, dp(13))
        field.bind(pos=sync, size=sync)
        return field


