"""Frahoosh Android entrypoint.

Buildozer uses the repository root as source.dir, so this file is the real
Android process entrypoint. Keep it intentionally tiny: importing dashboards,
services, panels, fonts, or Supabase code here can crash the process before
Login is visible.
"""

from mobile.main import FrahooshApp


if __name__ == "__main__":
    FrahooshApp().run()
