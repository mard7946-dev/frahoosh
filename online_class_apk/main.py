from kivy.app import App
from kivy.uix.widget import Widget
from jnius import autoclass
from android.runnable import run_on_ui_thread
from android.permissions import request_permissions, Permission
class Root(Widget): pass
class AppMain(App):
    def build(self):
        request_permissions([Permission.INTERNET, Permission.CAMERA, Permission.RECORD_AUDIO])
        return Root()
    def on_start(self):
        Activity=autoclass("org.kivy.android.PythonActivity")
        Launcher=autoclass("ir.frahoosh.ClassroomLauncher")
        Launcher.open(Activity.mActivity, "https://frahoosh.ir/online-class/")
AppMain().run()
