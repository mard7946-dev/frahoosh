from mobile.services.api import SupabaseClient
from mobile.services.local_store import LocalStore


class HybridApi(SupabaseClient):
    """Remote Supabase for normal accounts; persistent local SQLite for demo admin."""
    def __init__(self):
        super().__init__()
        self.local = LocalStore()

    @property
    def local_mode(self):
        return self.access_token == "local-bootstrap-admin"

    def table_select(self, table, params=None):
        if self.local_mode:
            return self.local.select(table, params or {})
        return super().table_select(table, params)

    def table_insert(self, table, payload, return_representation=True):
        if self.local_mode:
            return self.local.insert(table, payload or {})
        return super().table_insert(table, payload, return_representation)

    def table_update(self, table, filters, payload):
        if self.local_mode:
            return self.local.update(table, filters or {}, payload or {})
        return super().table_update(table, filters, payload)

    def table_delete(self, table, filters):
        if self.local_mode:
            return self.local.delete(table, filters or {})
        return super().table_delete(table, filters)

    def rpc(self, function_name, payload=None):
        if self.local_mode:
            return self.local.rpc(function_name, payload or {})
        return super().rpc(function_name, payload)
