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
    """Return Android-safe visual Persian text for normal LTR Kivy widgets.

    Widgets using this helper intentionally do not set Kivy's RTL text engine;
    BTitr stays the active font and python-bidi performs the visual ordering.
    Widgets that explicitly use text_language/base_direction must use rtl_text().
    """
    text = rtl_text(value)
    if not text:
        return text
    try:
        if arabic_reshaper is None or get_display is None:
            print("PERSIAN DISPLAY SHAPER MISSING:", repr(text))
            return text
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
    """Persian-aware editor.

    Kivy TextInput can show isolated Arabic glyphs while the user is typing.
    Keep the stored value in normal logical Persian, and shape it only when the
    field loses focus. This keeps CRUD payloads clean while making completed
    fields readable on Android.
    """
    def __init__(self, **kwargs):
        register_fonts()
        self.logical_text = unicodedata.normalize("NFKC", str(kwargs.get("text", "") or ""))
        self._shaping = False
        kwargs.setdefault("font_name", font_name())
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("multiline", False)
        kwargs.setdefault("cursor_width", 2)
        super().__init__(**kwargs)
        self.bind(text=self._capture_text, focus=self._focus_changed)

    def _capture_text(self, *_):
        if not self._shaping:
            self.logical_text = unicodedata.normalize("NFKC", str(self.text or ""))

    def _focus_changed(self, _widget, focused):
        if self._shaping:
            return
        # Password fields must never pass through Arabic reshaping.  Kivy
        # masks their logical value with password_mask; reshaping the stored
        # password can turn the visible mask into missing-glyph boxes and can
        # also change the value sent to authentication.
        if getattr(self, "password", False):
            self._shaping = True
            try:
                self.text = self.logical_text
            finally:
                self._shaping = False
            return
        if focused:
            self._shaping = True
            try:
                self.text = self.logical_text
            finally:
                self._shaping = False
        else:
            # Keep the logical Persian string unchanged. Kivy shapes it at
            # render time; storing presentation forms corrupts CRUD payloads.
            self.logical_text = unicodedata.normalize("NFKC", str(self.text or ""))

    def get_logical_text(self):
        return str(self.logical_text if self.logical_text is not None else self.text or "")


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
