"""
Timbor's Test Plugin
A custom plugin for FDC
"""

from core.plugin_system import PluginInterface, PluginType, PluginHooks, PluginInfo
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QMessageBox

class TimborsTestPluginDialog(QDialog):
    """Custom UI Dialog for Timbor's Test Plugin"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Timbor's Test Plugin")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.pushbutton_1 = QPushButton("Destruct")
        layout.addWidget(self.pushbutton_1)

        self.pushbutton_2 = QPushButton("Annihilate")
        layout.addWidget(self.pushbutton_2)
        
        self.pushbutton_1.clicked.connect(self.on_pushbutton_1_clicked)
        self.pushbutton_2.clicked.connect(self.on_pushbutton_2_clicked)

    def on_pushbutton_1_clicked(self):
        QMessageBox.information(self, "Action", "Destruct clicked!")

    def on_pushbutton_2_clicked(self):
        QMessageBox.information(self, "Action", "Annihilate clicked!")

class TimborsTestPlugin(PluginInterface):
    """A custom plugin for FDC"""

    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="Timbor's Test Plugin",
            version="1.0.0",
            description="A custom plugin for FDC",
            author="Timo P.",
            plugin_type=PluginType.UI_EXTENSION
        )
        self.menu_action = None


    def initialize(self, plugin_manager):
        """Called when plugin is first loaded"""
        return True

    def activate(self):
        """Called when plugin becomes active"""
        return True

    def deactivate(self):
        """Called when plugin is deactivated"""
        if hasattr(self, 'menu_action') and self.menu_action:
            self.menu_action.deleteLater()
            self.menu_action = None
        return True

    def shutdown(self):
        """Called when plugin is unloaded"""
        pass

    def get_hooks(self):
        """Return hook functions for events"""
        return {
            PluginHooks.APP_STARTUP: [self.on_app_startup],
            PluginHooks.UI_MENU_BAR_CREATED: [self.on_ui_menu_bar_created],
        }

    def on_app_startup(self, *args, **kwargs):
        """Handler for APP_STARTUP"""
        pass

    def on_ui_menu_bar_created(self, *args, **kwargs):
        """Handler for UI_MENU_BAR_CREATED"""
        for action in menu_bar.actions():
            if action.text() == "&Tools":
                tools_menu = action.menu()
                tools_menu.addSeparator()
                self.menu_action = tools_menu.addAction("Open Custom Tool")
                self.menu_action.triggered.connect(self.show_dialog)
                self.menu_item_1_action = tools_menu.addAction("Test Item")
                self.menu_item_1_action.triggered.connect(self.on_menu_item_1_clicked)
                break

    def show_dialog(self):
        """Shows the custom plugin dialog"""
        self.dialog = TimborsTestPluginDialog()
        self.dialog.exec()
    def on_menu_item_1_clicked(self):
        """Handler for Test Item menu item"""
        pass
