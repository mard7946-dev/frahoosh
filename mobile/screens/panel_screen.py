from mobile.screens.module import FinalModuleScreen


class PanelScreen(FinalModuleScreen):
    """Compatibility entry point used by the dashboard.

    The dashboard calls set_route(route). The actual rendering and table
    operations live in FinalModuleScreen/ModuleWorkspaceScreen so every panel
    uses the same real Supabase-backed workspace.
    """

    def set_route(self, route):
        self.set_module(route, "dashboard")


__all__ = ["PanelScreen"]
