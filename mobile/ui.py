from pathlib import Path

from kivy.core.text import LabelBase
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner

from mobile.config import (
    FONT_REGULAR,
    FONT_BOLD,
    CARD,
    BORDER,
)


_FONT_REGISTERED = False


def register_fonts():

    global _FONT_REGISTERED

    if _FONT_REGISTERED:
        return "Frahoosh"

    regular = Path(FONT_REGULAR)
    bold = Path(FONT_BOLD)

    if not regular.is_file():

        print(
            "FONT FILE NOT FOUND:",
            regular
        )

        return ""

    try:

        LabelBase.register(
            name="Frahoosh",
            fn_regular=str(regular),
            # Use the same known-complete Arabic/Persian glyph set for
            # bold labels as regular text. A separate bold face was producing
            # missing-glyph boxes (□) for Persian characters on some Android
            # builds.
            fn_bold=str(regular),
        )

        _FONT_REGISTERED = True

        return "Frahoosh"


    except Exception as exc:

        print(
            "FONT REGISTER ERROR:",
            repr(exc)
        )

        return ""



def font_name():
    # Android Kivy builds were showing missing-glyph boxes with the bundled
    # Noto face on the real device. Use Roboto as the runtime font; rtl_text()
    # performs Persian shaping before labels are drawn.
    return "Roboto"



def rtl_text(value):

    text = str(value or "")


    text = text.replace(
        "ي",
        "ی"
    )

    text = text.replace(
        "ى",
        "ی"
    )

    text = text.replace(
        "ك",
        "ک"
    )

    text = text.replace(
        "ۀ",
        "هٔ"
    )

    text = text.replace(
        "ة",
        "ه"
    )


    try:

        import arabic_reshaper

        from bidi.algorithm import (
            get_display
        )


        reshaped = (
            arabic_reshaper.reshape(
                text
            )
        )


        return get_display(
            reshaped
        )


    except Exception as exc:

        print(
            "RTL RENDER ERROR:",
            repr(exc)
        )

        return text



class PersianTextInput(TextInput):
    """Persian-aware editor.

    Kivy TextInput can show isolated Arabic glyphs while the user is typing.
    Keep the stored value in normal logical Persian, and shape it only when the
    field loses focus. This keeps CRUD payloads clean while making completed
    fields readable on Android.
    """
    def __init__(self, **kwargs):
        register_fonts()
        self.logical_text = str(kwargs.get("text", "") or "")
        self._shaping = False
        kwargs.setdefault("font_name", font_name())
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("base_direction", "rtl")
        kwargs.setdefault("text_language", "fa")
        kwargs.setdefault("font_script_name", "Arab")
        kwargs.setdefault("multiline", False)
        kwargs.setdefault("cursor_width", 2)
        super().__init__(**kwargs)
        self.bind(text=self._capture_text, focus=self._focus_changed)

    def _capture_text(self, *_):
        if not self._shaping:
            self.logical_text = str(self.text or "")

    def _focus_changed(self, _widget, focused):
        if self._shaping:
            return
        if focused:
            self._shaping = True
            try:
                self.text = self.logical_text
            finally:
                self._shaping = False
        else:
            self.logical_text = str(self.text or "")
            shaped = rtl_text(self.logical_text)
            if shaped and shaped != self.text:
                self._shaping = True
                try:
                    self.text = shaped
                finally:
                    self._shaping = False

    def get_logical_text(self):
        return str(self.logical_text if self.logical_text is not None else self.text or "")


class PersianSpinnerOption(Button):
    """Spinner dropdown option using the same bundled Persian font."""
    def __init__(self, **kwargs):
        register_fonts()
        kwargs.setdefault("font_name", font_name())
        kwargs.setdefault("font_script_name", "Arab")
        kwargs.setdefault("text_language", "fa")
        kwargs.setdefault("font_size", "12sp")
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("text_size", (None, None))
        kwargs.setdefault("color", (1, 1, 1, 1))
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", (0.08, 0.20, 0.34, 1))
        super().__init__(**kwargs)
        self.bind(size=lambda o, v: setattr(o, "text_size", v))


def PersianSpinner(**kwargs):
    """Factory so every CRUD dropdown gets a Persian-safe option class."""
    kwargs.setdefault("option_cls", PersianSpinnerOption)
    kwargs.setdefault("font_name", font_name())
    kwargs.setdefault("font_script_name", "Arab")
    kwargs.setdefault("text_language", "fa")
    kwargs.setdefault("font_size", "11sp")
    return Spinner(**kwargs)



class Card(Widget):

    def __init__(
        self,
        radius=18,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )


        with self.canvas.before:


            self._color = Color(
                *CARD
            )


            self._rect = RoundedRectangle(

                pos=self.pos,

                size=self.size,

                radius=[
                    radius
                ],

            )


            self._line_color = Color(
                *BORDER
            )


            self._line = Line(

                rounded_rectangle=(

                    self.x,

                    self.y,

                    self.width,

                    self.height,

                    radius,

                ),

                width=0.8,

            )


        self.bind(
            pos=self._sync,
            size=self._sync,
        )



    def _sync(self, *_):

        self._rect.pos = self.pos

        self._rect.size = self.size


        r = (
            self._line
            .rounded_rectangle[4]
        )


        self._line.rounded_rectangle = (

            self.x,

            self.y,

            self.width,

            self.height,

            r,

        )      
