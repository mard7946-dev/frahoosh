"""Reusable bordered, right-to-left data grid for screens outside the module workspace."""
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

from mobile.ui import font_name, fa_display

_BORDER = (0.52, 0.62, 0.72, 1)


def _cell(text, width, height, bg, color, bold=False, size="12sp", max_chars=30):
    s = str(text if text is not None else "").replace("\n", " ").strip()
    if len(s) > max_chars:
        s = s[: max_chars - 1] + "\u2026"
    w = Label(text=fa_display(s), font_name=font_name(), font_size=size, color=color, bold=bold,
              halign="center", valign="middle", size_hint=(None, None), width=width, height=height)
    w.bind(size=lambda o, v: setattr(o, "text_size", v))
    with w.canvas.before:
        Color(*bg)
        fill = Rectangle(pos=w.pos, size=w.size)
    with w.canvas.after:
        Color(*_BORDER)
        line = Line(rectangle=(w.x, w.y, w.width, w.height), width=1)

    def upd(*_):
        fill.pos, fill.size = w.pos, w.size
        line.rectangle = (w.x, w.y, w.width, w.height)
    w.bind(pos=upd, size=upd)
    return w


def build_grid(columns, rows, header_color=(0.04, 0.24, 0.38, 1), row_h=44, max_height=460,
               footer=None, number_title="ردیف"):
    """columns: [(title, width_dp, getter(row)->text | (text, colour))] in LOGICAL order
    (first column ends up at the right). footer: optional list of texts, one per column."""
    from mobile.services.jalali import fa_digits
    num_w = dp(48)
    widths = [dp(c[1]) for c in columns]
    total_w = num_w + sum(widths)
    rh = dp(row_h)
    content = BoxLayout(orientation="vertical", size_hint=(None, None), width=total_w, spacing=0, padding=0)
    content.bind(minimum_height=content.setter("height"))

    def line(cells_builder, h):
        b = BoxLayout(size_hint=(None, None), width=total_w, height=h, spacing=0, padding=0)
        cells_builder(b)
        return b

    def head(b):
        for (title, _w, _g), w in reversed(list(zip(columns, widths))):
            b.add_widget(_cell(title, w, dp(46), header_color, (1, 1, 1, 1), True, "12.5sp", 24))
        b.add_widget(_cell(number_title, num_w, dp(46), header_color, (1, 1, 1, 1), True, "12.5sp", 6))
    content.add_widget(line(head, dp(46)))

    for i, r in enumerate(rows, 1):
        bg = (0.93, 0.96, 0.985, 1) if i % 2 == 0 else (1, 1, 1, 1)

        def body(b, r=r, bg=bg, i=i):
            for (title, _w, getter), w in reversed(list(zip(columns, widths))):
                try:
                    v = getter(r)
                except Exception:
                    v = ""
                text, colour = (v if isinstance(v, tuple) else (v, None))
                b.add_widget(_cell(text, w, rh, bg, colour or (0.25, 0.30, 0.38, 1), colour is not None,
                                   "12sp", max(6, int(w / dp(7.2)))))
            b.add_widget(_cell(fa_digits(i), num_w, rh, bg, (0.12, 0.35, 0.62, 1), True, "12sp", 6))
        content.add_widget(line(body, rh))

    if footer:
        def foot(b):
            for t, w in reversed(list(zip(footer, widths))):
                b.add_widget(_cell(t, w, dp(46), (0.88, 0.92, 0.97, 1), (0.05, 0.15, 0.30, 1), True, "12.5sp", 26))
            b.add_widget(_cell("", num_w, dp(46), (0.88, 0.92, 0.97, 1), (0, 0, 0, 1)))
        content.add_widget(line(foot, dp(46)))

    sv = ScrollView(do_scroll_x=True, do_scroll_y=True, size_hint_y=None, bar_width=dp(4))
    sv.height = min(dp(max_height), dp(46) * (2 if footer else 1) + rh * len(rows) + dp(6))
    sv.add_widget(content)
    Clock.schedule_once(lambda *_: setattr(sv, "scroll_x", 1), 0)
    return sv
