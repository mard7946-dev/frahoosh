from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from mobile.screens.module import FinalModuleScreen
from mobile.screens.module_workspace import SUBMENUS, FRIENDLY
from mobile.config import PRIMARY, SECONDARY, SUCCESS, WHITE
from mobile.ui import font_name, rtl_text, fa_display


class PanelScreen(FinalModuleScreen):
    """Real operational panel entry point with a safe navigation boundary.

    Dashboard navigation must never fail because a rendering detail in a
    subpanel failed. The panel is entered first; rendering is then performed
    on the Kivy clock. A minimal fallback is kept so the user can still reach
    the real table workspace.
    """

    def set_route(self, route):
        self.route = route if route in SUBMENUS else "management"
        self.return_to = "dashboard"
        self.table = None
        if self.manager:
            self.manager.current = "panel"
        Clock.schedule_once(self._render_route_safe, 0)

    def _render_route_safe(self, *_):
        try:
            self.render()
        except Exception as exc:
            print("PANEL RENDER ERROR:", repr(exc))
            self._render_fallback()

    def _render_fallback(self):
        self.body.clear_widgets()
        items = SUBMENUS.get(self.route, [])
        title = FRIENDLY.get(self.route, self.route)
        self.title.text = fa_display(title)
        self.status.text = fa_display("پنل باز شد؛ زیرپنل‌ها آماده هستند")
        self.status.color = SUCCESS

        scroll = __import__("kivy.uix.scrollview", fromlist=["ScrollView"]).ScrollView(
            do_scroll_x=False
        )
        box = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            padding=[dp(2), dp(3)],
            size_hint_y=None,
        )
        box.bind(minimum_height=box.setter("height"))

        for index, (caption, table) in enumerate(items, 1):
            btn = Button(
                text=fa_display(f"{index:02d}  {caption}"),
                font_name=font_name(),
                font_size="12sp",
                background_normal="",
                background_color=PRIMARY,
                color=WHITE,
                size_hint_y=None,
                height=dp(50),
            )
            btn.bind(
                on_release=lambda *_a, t=table: self._open_table_safe(t)
            )
            box.add_widget(btn)

        scroll.add_widget(box)
        self.body.add_widget(scroll)

    def _open_table_safe(self, table):
        try:
            FinalModuleScreen.open_table(self, table, refresh_subbar=False)
        except Exception as exc:
            print("PANEL TABLE OPEN ERROR:", repr(exc))
            self.status.text = rtl_text("خطا در باز کردن جدول")
            self.status.color = (0.85, 0.15, 0.15, 1)

    def go_dashboard(self, *_):
        if self.manager:
            self.manager.current = "dashboard"


__all__ = ["PanelScreen"]
