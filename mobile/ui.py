from pathlib import Path
import unicodedata

from kivy.core.text import LabelBase
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.resources import resource_find, resource_add_path

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception as exc:
    arabic_reshaper = None
    get_display = None
    print("PERSIAN SHAPER UNAVAILABLE:", repr(exc))

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
        return "FrahooshBTitr"

    # BTitrBd.ttf is the required Frahoosh typeface. Do not replace it.
    # Resolve it through both the normal filesystem path and Kivy's packaged
    # resource path so the APK never silently falls back to Roboto (which
    # produces □ for Persian glyphs).
    candidates = [
        Path(FONT_REGULAR),
        Path(__file__).resolve().parent / "assets" / "BTitrBd.ttf",
    ]
    try:
        packaged = resource_find("mobile/assets/BTitrBd.ttf") or resource_find("assets/BTitrBd.ttf")
        if packaged:
            candidates.insert(0, Path(packaged))
    except Exception as exc:
        print("FONT RESOURCE LOOKUP ERROR:", repr(exc))

    regular = next((p for p in candidates if p.is_file()), None)
    if regular is None:
        print("FONT FILE NOT FOUND:", [str(p) for p in candidates])
        return ""

    try:
        # Keep BTitr for both weights. The important fix is deterministic APK
        # resolution; never substitute another typeface for the module UI.
        LabelBase.register(
            name="FrahooshBTitr",
            fn_regular=str(regular),
            fn_bold=str(regular),
        )
        _FONT_REGISTERED = True
        print("FRAHOOSH BTITR REGISTERED:", str(regular))
        return "FrahooshBTitr"


    except Exception as exc:

        print(
            "FONT REGISTER ERROR:",
            repr(exc)
        )

        return ""



def fa_display(value):
    """Render Persian once for BTitr widgets that use normal Kivy text layout.

    TextInput keeps logical Persian text; labels/buttons receive the shaped
    visual string.  Presentation-form input is returned unchanged so callers
    can safely pass an already-rendered value through another UI helper.
    """
    text = rtl_text(value)
    if not text:
        return text
    # Do not reshape an already visually shaped Arabic/Persian string.
    if any("\uFE70" <= ch <= "\uFEFF" for ch in text):
        return text
    try:
        if arabic_reshaper is not None and get_display is not None:
            return get_display(arabic_reshaper.reshape(text))
    except Exception as exc:
        print("PERSIAN DISPLAY SHAPE ERROR:", repr(exc))
    return text

def font_name():
    # Use the bundled Arabic/Persian-capable face. Roboto in the Android
    # Kivy package does not contain the required Persian glyphs.
    registered = register_fonts()
    return registered or "Roboto"


def bundled_login_background():
    """Resolve the exact bundled portrait Frahoosh artwork on Android."""
    asset_dir = Path(__file__).resolve().parent / "assets"
    try:
        for candidate in (asset_dir / "frahoosh_login_mobile.jpg",):
            if candidate.is_file():
                return str(candidate)
        resource_add_path(str(asset_dir))
        for name in ("frahoosh_login_mobile.jpg", "mobile/assets/frahoosh_login_mobile.jpg", "assets/frahoosh_login_mobile.jpg"):
            found = resource_find(name)
            if found:
                return found
    except Exception as exc:
        print("LOGIN ART RESOURCE ERROR:", repr(exc))
    return None



def rtl_text(value):

    text = unicodedata.normalize("NFKC", str(value or ""))


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

        # Kivy/SDL2 performs Arabic shaping at render time when the
        # widget is configured for Persian/Arabic. Pre-shaping creates Arabic
        # presentation-form codepoints that BTitrBd.ttf may not contain,
        # producing square glyphs on Android. Keep the logical Persian text.
        return text


    except Exception as exc:

        print(
            "RTL RENDER ERROR:",
            repr(exc)
        )

        return text



class PersianTextInput(TextInput):
    """RTL-safe Persian editor with canonical logical text."""
    def __init__(self, **kwargs):
        register_fonts()
        initial = unicodedata.normalize("NFKC", str(kwargs.pop("text", "") or ""))
        self.logical_text = initial
        self._rendering_persian = False
        kwargs.setdefault("font_name", font_name())
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("multiline", False)
        kwargs.setdefault("cursor_width", 2)
        super().__init__(**kwargs)
        self._render_visual()
        self.bind(text=self._capture_external_text, focus=self._focus_changed)

    def _visual(self, logical):
        # Keep TextInput logical Unicode text; only labels/buttons are bidi-shaped.
        # Feeding fa_display() back into TextInput corrupts subsequent Persian input.
        return logical

    def _render_visual(self):
        if self._rendering_persian:
            return
        self._rendering_persian = True
        try:
            visual = self._visual(self.logical_text)
            self.text = visual
            self.cursor = (len(visual), 0)
        finally:
            self._rendering_persian = False

    def insert_text(self, substring, from_undo=False):
        if self._rendering_persian:
            return super().insert_text(substring, from_undo=from_undo)
        raw = unicodedata.normalize("NFKC", str(substring or ""))
        if raw:
            self.logical_text += raw
            self._render_visual()

    def do_backspace(self, from_undo=False, mode="bkspc"):
        if self._rendering_persian or not self.logical_text:
            return
        self.logical_text = self.logical_text[:-1]
        self._render_visual()

    def _capture_external_text(self, _widget, value):
        if not self._rendering_persian:
            self.logical_text = unicodedata.normalize("NFKC", str(value or ""))

    def _focus_changed(self, _widget, focused):
        self._render_visual()

    def set_logical_text(self, value):
        self.logical_text = unicodedata.normalize("NFKC", str(value or ""))
        self._render_visual()

    def get_logical_text(self):
        return str(self.logical_text if self.logical_text is not None else "")


class PersianSpinnerOption(Button):
    """Spinner dropdown option using the same bundled Persian font."""
    def __init__(self, **kwargs):
        register_fonts()
        kwargs.setdefault("font_name", font_name())
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
