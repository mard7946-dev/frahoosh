[app]

title = Frahoosh
package.name = frahooshmobile
package.domain = ir.frahoosh

# Keep the package identity stable so new APKs are upgrades, not separate apps.
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json

version = 1.3.0
android.numeric_version = 130

requirements = python3,kivy,requests,urllib3,arabic-reshaper,python-bidi

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 24
android.ndk = 28c
android.ndk_api = 24

android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True
android.permissions = INTERNET
android.private_storage = True

p4a.branch = develop
p4a.commit = 5865575

[buildozer]
log_level = 2
warn_on_root = 1
