[app]

title = Frahoosh
package.name = frahooshmobile
package.domain = ir.frahoosh

source.dir = mobile
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json

version = 1.2.0

requirements = python3,kivy,requests,urllib3,arabic-reshaper,python-bidi

orientation = portrait

fullscreen = 0

android.api = 35
android.minapi = 23
android.ndk = 28c
android.ndk_api = 23

android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True

android.permissions = INTERNET

android.private_storage = True

[buildozer]

log_level = 2

warn_on_root = 1
