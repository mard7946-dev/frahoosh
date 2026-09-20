"""Frahoosh Android entrypoint — startup-safe V16.12 runtime.

The Android APK must enter the login boundary before importing any heavy
workspace/service modules. The mobile.main app deliberately keeps those imports
lazy and provides an emergency login fallback when a later module fails.
"""
from mobile.main import FrahooshApp


if __name__ == "__main__":
    FrahooshApp().run()
