from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from mobile.screens.login import LoginScreen
from mobile.services.app_state import AppState
from .workspace import RebuildDashboard, RebuildWorkspace, RebuildTable
from .actions import SchoolActionScreen

class FrahooshRebuildApp(App):
    def __init__(self,**kwargs):
        super().__init__(**kwargs); self.app_state=None; self.sm=None; self._workspace=None

    def build(self):
        self.title="فراهوش"
        self.sm=ScreenManager()
        self.sm.add_widget(LoginScreen(name="login",app_state=None))
        self.sm.current="login"
        Clock.schedule_once(self._load_state,0.05)
        return self.sm

    def _load_state(self,*_):
        try:
            self.app_state=AppState(); self.app_state._app=self
            login=self.sm.get_screen("login"); login.app_state=self.app_state
        except Exception as exc: print("REBUILD APP STATE ERROR:",repr(exc))

    def open_dashboard(self):
        try:
            if not self.app_state: self._load_state()
            if not self.sm.has_screen("dashboard"):
                self.sm.add_widget(RebuildDashboard(name="dashboard",app_state=self.app_state))
            self.show_dashboard(); return True
        except Exception as exc:
            print("REBUILD DASHBOARD ERROR:",repr(exc)); return False

    def show_dashboard(self):
        self.sm.current="dashboard"

    def open_workspace(self,panel_key="management"):
        if not self.sm.has_screen("workspace"):
            self.sm.add_widget(RebuildWorkspace(name="workspace",app_state=self.app_state,panel_key=panel_key))
        screen=self.sm.get_screen("workspace"); screen.panel_key=panel_key; screen.clear_widgets(); screen._build()
        self.sm.current="workspace"

    def show_workspace(self):
        self.sm.current="workspace"

    def open_table(self,key,table,role):
        name="table_"+str(table)
        if self.sm.has_screen(name): self.sm.remove_widget(self.sm.get_screen(name))
        self.sm.add_widget(RebuildTable(name=name,app_state=self.app_state,table=table,title=key,role=role))
        self.sm.current=name

    def open_action(self,mode):
        name="action_"+mode
        if self.sm.has_screen(name): self.sm.remove_widget(self.sm.get_screen(name))
        self.sm.add_widget(SchoolActionScreen(name=name,app_state=self.app_state,mode=mode))
        self.sm.current=name

if __name__=="__main__":
    FrahooshRebuildApp().run()
