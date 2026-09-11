from pathlib import Path

from kivy.core.text import LabelBase
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput

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
            fn_bold=str(
                bold
                if bold.is_file()
                else regular
            ),
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

    if register_fonts():

        return "Frahoosh"

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

    def __init__(self, **kwargs):

        register_fonts()

        kwargs.setdefault(
            "font_name",
            font_name()
        )

        kwargs.setdefault(
            "halign",
            "right"
        )

        kwargs.setdefault(
            "multiline",
            False
        )

        kwargs.setdefault(
            "cursor_width",
            2
        )


        super().__init__(
            **kwargs
        )



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
