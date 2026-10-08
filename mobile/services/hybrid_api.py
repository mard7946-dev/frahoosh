from mobile.services.api import SupabaseClient


class HybridApi(SupabaseClient):
    """Backward-compatible API name; all production data operations use Supabase.

    The previous implementation silently switched to a local SQLite store when a
    special bootstrap token was present. That path is not part of the school APK
    contract and could make a successful-looking operation bypass Supabase.
    Keep the class name for import compatibility, but make the backend unambiguous.
    """
    pass
