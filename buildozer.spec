[app]

title = Frahoosh
package.name = frahooshmobile
package.domain = ir.frahoosh

source.dir = mobile
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json

version = 1.2.0

requirements = python3==3.11.10,hostpython3==3.11.10,kivy==2.3.1,requests==2.32.3,urllib3,arabic-reshaper==3.0.0,python-bidi==0.4.2

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 24
android.ndk = 25c
android.ndk_api = 24

android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True
android.permissions = INTERNET
android.private_storage = True

# Pin python-for-android to the exact revision used by the last known green APK build.
p4a.fork = kivy
p4a.branch = develop
p4a.commit = 5865575

[buildozer]
log_level = 2
warn_on_root = 1
