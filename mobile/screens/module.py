# Frahoosh final mobile module entry point.
# Accordion navigation only: no PageLayout and no swipe between subpanels.
from mobile.screens.professional_workspace import ProfessionalWorkspaceScreen
from mobile.screens.module_workspace import ModuleWorkspaceScreen, SUBMENUS, FRIENDLY

# The dashboard already exposes participation; keep it a real module route.
SUBMENUS.setdefault("participation", [
    ("فعالیت‌ها", "educational_activities"),
    ("رویدادها", "school_events"),
    ("مشارکت اولیا", "parent_meetings"),
])
FRIENDLY.setdefault("participation", "مشارکت و فعالیت‌ها")


class FinalModuleScreen(ProfessionalWorkspaceScreen):
    """Stable final entry point used by main.py."""

    def open_table(self, table, refresh_subbar=True):
        # Generic tables still use the proven Supabase table/editor implementation.
        # Calling the base implementation directly prevents our accordion render()
        # from intercepting a request to open a real table.
        if table in ("teacher_exams", "online_classes", "messages", "payment_offers"):
            return super().open_table(table, refresh_subbar=False)
        return ModuleWorkspaceScreen.open_table(self, table, refresh_subbar=False)

    def _start_session(self, class_id):
        # Supabase supplies created_at; started_at is filled when a real session
        # starts through the dedicated session controls rather than sending SQL
        # syntax as a text value to the API.
        if not class_id:
            return
        self._write_async("online_class_sessions", {"class_id": class_id}, "جلسه آنلاین ثبت شد.")


ModuleScreen = FinalModuleScreen
ProfessionalModuleScreen = FinalModuleScreen

__all__ = ["ModuleScreen", "ProfessionalModuleScreen", "FinalModuleScreen"]
