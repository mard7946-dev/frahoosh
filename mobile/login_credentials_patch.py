from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.textinput import TextInput

from mobile.ui import font_name, fa_display

FIELD = (0.02, 0.12, 0.30, 0.78)
WHITE = (1, 1, 1, 1)
CYAN = (0.03, 0.78, 0.94, 1)
MUTED = (0.72, 0.83, 0.96, 1)


class CredentialInput(TextInput):
    def __init__(self, *, masked=False, **kwargs):
        self.logical_text = str(kwargs.pop("text", "") or "")
        self.masked = bool(masked)
        kwargs.update(
            font_name=font_name(),
            multiline=False,
            halign="left",
            base_direction="ltr",
            padding=[dp(14), dp(9)],
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=WHITE,
            hint_text_color=MUTED,
            cursor_color=CYAN,
            size_hint_y=None,
            height=dp(47),
        )
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*FIELD)
            self._bg = RoundedRectangle(radius=[dp(16)])
            Color(0.15, 0.58, 0.95, 0.75)
            self._border = Line(rounded_rectangle=(0, 0, 0, 0, dp(16)), width=0.9)
        self.bind(pos=self._sync, size=self._sync)
        self._render()

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(16))

    def _render(self):
        self.text = ("*" * len(self.logical_text)) if self.masked else self.logical_text
        self.cursor = (len(self.text), 0)

    def insert_text(self, substring, from_undo=False):
        raw = str(substring or "")
        if raw:
            self.logical_text += raw
            self._render()

    def do_backspace(self, from_undo=False, mode="bkspc"):
        if self.logical_text:
            self.logical_text = self.logical_text[:-1]
            self._render()

    def get_logical_text(self):
        return self.logical_text

    def set_logical_text(self, value):
        self.logical_text = str(value or "")
        self._render()


def patch_login_screen(login_cls):
    def _field(self, hint, masked=False):
        return CredentialInput(
            hint_text=fa_display(hint),
            masked=masked,
        )
    login_cls._field = _field
    return login_cls
