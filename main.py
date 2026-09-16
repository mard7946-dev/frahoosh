"""Frahoosh Android entrypoint.

Buildozer uses the repository root as source.dir, so Android starts this file.
The real application entrypoint lives in mobile.main; keeping a second emergency
login implementation here caused the APK to bypass the real login UI/state flow.
"""

from mobile.main import FrahooshApp


if __name__ == "__main__":
    FrahooshApp().run()
