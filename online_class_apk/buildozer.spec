[app]
title = فراهوش کلاس آنلاین
package.name = frahooshclassroom
package.domain = ir.frahoosh
source.dir = .
source.include_exts = py,kv
version = 1.0.0
android.numeric_version = 10000
requirements = python3==3.11.10,hostpython3==3.11.10,kivy==2.3.1,pyjnius
orientation = landscape
fullscreen = 1
android.api = 35
android.minapi = 24
android.ndk = 28c
android.ndk_api = 24
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.permissions = INTERNET,CAMERA,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS
android.add_src = java
p4a.branch = master
p4a.commit = 957a3e5

[buildozer]
log_level = 2
warn_on_root = 1
