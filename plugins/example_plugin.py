"""
Example Plugin for Fallout Dialogue Creator

This plugin demonstrates how to create custom plugins for the application.
It adds a simple menu item and shows dialogue statistics.
"""

from core.plugin_system import PluginInterface, PluginType, PluginHooks, PluginInfo

class ExamplePlugin(PluginInterface):
    """Example plugin demonstrating basic functionality"""

    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="Example Plugin",
            version="1.0.0",
            description="Demonstrates plugin functionality with menu integration",
            author="Fallout Dialogue Creator Team",
            plugin_type=PluginType.UI_EXTENSION
        )
        self.menu_action = None

    def initialize(self, plugin_manager):
        """Initialize the plugin"""
        print(f"Initializing {self.plugin_info.name}")
        return True

    def activate(self):
        """Activate the plugin"""
        print(f"Activating {self.plugin_info.name}")
        return True

    def deactivate(self):
        """Deactivate the plugin"""
        print(f"Deactivating {self.plugin_info.name}")
        if self.menu_action:
            # Remove menu action if it exists
            pass
        return True

    def get_hooks(self):
        """Return hook functions"""
        return {
            PluginHooks.APP_STARTUP: [self.on_app_startup],
            PluginHooks.UI_MENU_BAR_CREATED: [self.on_menu_bar_created],
            PluginHooks.DIALOGUE_LOADED: [self.on_dialogue_loaded],
        }

    def on_app_startup(self, app):
        """Called when application starts"""
        print("Example Plugin: Application startup detected")

    def on_menu_bar_created(self, menu_bar):
        """Called when menu bar is created - add our menu item"""
        print("Example Plugin: Adding menu item")

        # Find the Tools menu
        tools_menu = None
        for action in menu_bar.actions():
            if action.text() == "&Tools":
                tools_menu = action.menu()
                break

        if tools_menu:
            # Add separator and our action
            tools_menu.addSeparator()
            self.menu_action = tools_menu.addAction("Example Plugin Statistics")
            self.menu_action.triggered.connect(self.show_statistics)

    def on_dialogue_loaded(self, dialogue):
        """Called when a dialogue is loaded"""
        print(f"Example Plugin: Dialogue loaded - {dialogue.npcname}")
        print(f"  Nodes: {dialogue.nodecount}")
        print(f"  Custom procedures: {len(dialogue.customprocs)}")

    def show_statistics(self):
        """Show dialogue statistics in a message box"""
        from PyQt6.QtWidgets import QMessageBox

        # This would normally get the current dialogue from the plugin manager
        # For now, just show a placeholder message
        QMessageBox.information(
            None,  # No parent widget available in this context
            "Example Plugin",
            "This is an example plugin!\n\n"
            "Plugins can:\n"
            "• Add menu items\n"
            "• Respond to application events\n"
            "• Extend functionality\n"
            "• Process dialogues\n\n"
            "Check the plugin documentation for details."
        )