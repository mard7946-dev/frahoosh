# Keep existing screen imports stable while upgrading the module landing page.
# The professional subclass preserves the existing Supabase CRUD/table engine.
try:
    from mobile.screens.module_professional import ProfessionalModuleScreen
    from mobile.screens import module as _module
    _module.ModuleScreen = ProfessionalModuleScreen
except Exception as exc:
    print("PROFESSIONAL MODULE UI LOAD ERROR:", repr(exc))
