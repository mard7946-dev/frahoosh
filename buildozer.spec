[app]

title = Frahoosh
package.name = frahooshmobile
package.domain = ir.frahoosh
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json
version = 1.5.4
android.numeric_version = 154
requirements = python3==3.11.10,hostpython3==3.11.10,kivy==2.3.1,requests==2.32.3,urllib3,arabic-reshaper==3.0.0,python-bidi==0.6.6
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.sdk_path = /usr/local/lib/android/sdk
android.ndk = 28c
android.ndk_path = /usr/local/lib/android/sdk/ndk/28.2.13676358
android.ndk_api = 24
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.permissions = INTERNET
android.private_storage = True
p4a.branch = develop
p4a.commit = 5865575

[buildozer]
log_level = 2
warn_on_root = 1
