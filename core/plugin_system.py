"""
Plugin System for Fallout Dialogue Creator

Provides a modular architecture for extending the application with custom plugins.
Supports UI extensions, dialogue processors, custom parsers, and scripting extensions.

Architecture:
- PluginManager: Central registry and lifecycle management
- PluginInterface: Base class for all plugins
- Hook system: Event-driven plugin activation
- Sandboxed execution: Isolated plugin environments

⚠️ SECURITY WARNING: This plugin system uses Python's importlib to dynamically
load and execute plugin code. Plugins have full access to the Python interpreter
and can execute arbitrary code. Only install plugins from trusted sources.

Security considerations:
- Plugins are loaded from the plugins/ directory (bundled) or ~/.fallout_dialogue_creator/plugins/ (user)
- No code signing or sandboxing is implemented
- Malicious plugins can read/write files, execute commands, and access system resources
- Only enable plugins from trusted authors
- Review plugin source code before installation

For production use, consider implementing:
- Code signing for plugins
- Sandboxed execution (e.g., using RestrictedPython)
- Plugin manifest with permissions
"""

import importlib
import inspect
import logging
import os
import sys
from typing import Dict, List, Optional, Any, Type, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


def get_app_bundle_path() -> Optional[Path]:
    """
    Get the path to the application bundle (frozen executable) or None if running in development.
    
    This function detects if the application is running as a PyInstaller bundled executable
    and returns the correct path for bundled resources.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundled executable
        # _MEIPASS is the path to the temporary extracted bundle
        return Path(sys._MEIPASS)
    return None


def get_app_base_path() -> Path:
    """
    Get the base path of the application.
    
    In development: returns the directory containing the source files.
    In frozen executable: returns the directory containing the executable or the _MEIPASS path.
    """
    bundle_path = get_app_bundle_path()
    if bundle_path:
        return bundle_path
    
    # Development mode: use the directory containing this file (core/) and go up to project root
    return Path(__file__).parent.parent

class PluginType(Enum):
    """Types of plugins supported by the system"""
    UI_EXTENSION = "ui_extension"
    DIALOGUE_PROCESSOR = "dialogue_processor"
    PARSER_EXTENSION = "parser_extension"
    SCRIPTING_EXTENSION = "scripting_extension"
    TESTING_EXTENSION = "testing_extension"
    EXPORT_EXTENSION = "export_extension"

class PluginState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class PluginInfo:
    """Metadata for a plugin"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    requires_restart: bool = False

@dataclass
class PluginInstance:
    """Runtime information for a loaded plugin"""
    info: PluginInfo
    module: Any
    instance: Any
    state: PluginState = PluginState.UNLOADED
    hooks: Dict[str, List[Callable]] = field(default_factory=dict)
    error_message: str = ""

class PluginInterface:
    """
    Base interface that all plugins must implement

    Plugins should inherit from this class and override the necessary methods.
    """

    def __init__(self):
        self.plugin_info = PluginInfo(
            name="Base Plugin",
            version="1.0.0",
            description="Base plugin interface",
            author="Unknown",
            plugin_type=PluginType.UI_EXTENSION
        )

    def initialize(self, plugin_manager) -> bool:
        """
        Called when the plugin is first loaded
        Return True if initialization successful
        """
        return True

    def activate(self) -> bool:
        """
        Called when the plugin becomes active
        Return True if activation successful
        """
        return True

    def deactivate(self) -> bool:
        """
        Called when the plugin is deactivated
        Return True if deactivation successful
        """
        return True

    def shutdown(self):
        """Called when the plugin is unloaded"""
        pass

    def get_hooks(self) -> Dict[str, List[Callable]]:
        """
        Return dictionary of hook functions
        Keys are hook names, values are lists of callable functions
        """
        return {}

class PluginManager(QObject):
    """
    Central plugin management system

    Handles plugin discovery, loading, lifecycle management, and hook dispatching.
    """

    plugin_loaded = pyqtSignal(PluginInstance)
    plugin_unloaded = pyqtSignal(str)  # plugin name
    plugin_error = pyqtSignal(str, str)  # plugin name, error message

    def __init__(self, plugin_dirs: List[Path] = None):
        super().__init__()
        
        # Determine the correct base path for the application
        app_base_path = get_app_base_path()
        
        if plugin_dirs is None:
            # Use default plugin directories - look in the bundled plugins folder
            # In frozen mode: _MEIPASS/plugins, in dev mode: ./plugins
            bundled_plugins_dir = app_base_path / "plugins"
            
            # Also check user plugins directory
            user_plugins_dir = Path.home() / ".fallout_dialogue_creator" / "plugins"
            
            self.plugin_dirs = [bundled_plugins_dir, user_plugins_dir]
        else:
            self.plugin_dirs = plugin_dirs
            
        self.plugins: Dict[str, PluginInstance] = {}
        self.active_plugins: Dict[str, PluginInstance] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        
        # Track trusted plugins (plugin_name -> bool)
        self._trusted_plugins: Dict[str, bool] = {}
        
        logger.info(f"PluginManager initialized. Base path: {app_base_path}")
        logger.info(f"Plugin directories: {self.plugin_dirs}")

        # Create plugin directories if they don't exist (only for user plugins)
        for plugin_dir in self.plugin_dirs:
            # Only create user plugins directory automatically
            if plugin_dir == Path.home() / ".fallout_dialogue_creator" / "plugins":
                plugin_dir.mkdir(parents=True, exist_ok=True)

    def discover_plugins(self) -> List[PluginInfo]:
        """Discover available plugins in plugin directories"""
        discovered_plugins = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue

            # Look for Python files that might be plugins
            for py_file in plugin_dir.glob("*.py"):
                try:
                    plugin_info = self._inspect_plugin_file(py_file)
                    if plugin_info:
                        discovered_plugins.append(plugin_info)
                except Exception as e:
                    logger.warning(f"Failed to inspect plugin {py_file}: {e}")

        return discovered_plugins

    def _inspect_plugin_file(self, file_path: Path) -> Optional[PluginInfo]:
        """Inspect a Python file to see if it's a valid plugin"""
        try:
            # Import the module temporarily
            module_name = f"plugin_{file_path.stem}_{hash(str(file_path))}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for plugin classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, PluginInterface) and
                    obj != PluginInterface):
                    # Create instance to get info
                    instance = obj()
                    return instance.plugin_info

        except Exception as e:
            logger.warning(f"Error inspecting {file_path}: {e}")
            return None

    def load_plugin(self, plugin_name: str, plugin_file: Path) -> bool:
        """
        Load a plugin by name and file path
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} already loaded")
            return False

        try:
            # Import the plugin module
            module_name = f"plugin_{plugin_name}_{hash(str(plugin_file))}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if not spec or not spec.loader:
                raise ImportError(f"Could not load spec for {plugin_file}")

            module = importlib.util.module_from_spec(spec)

            # Create plugin instance
            plugin_instance = PluginInstance(
                info=PluginInfo("", "", "", "", PluginType.UI_EXTENSION),
                module=module,
                instance=None,
                state=PluginState.LOADING
            )
            self.plugins[plugin_name] = plugin_instance

            # Execute module
            spec.loader.exec_module(module)

            # Find plugin class and instantiate
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, PluginInterface) and
                    obj != PluginInterface):
                    plugin_class = obj
                    break

            if not plugin_class:
                raise ImportError(f"No PluginInterface subclass found in {plugin_file}")

            instance = plugin_class()
            plugin_instance.instance = instance
            plugin_instance.info = instance.plugin_info
            plugin_instance.state = PluginState.LOADED

            # Initialize plugin
            if not instance.initialize(self):
                raise RuntimeError("Plugin initialization failed")

            # Register hooks
            plugin_instance.hooks = instance.get_hooks()
            for hook_name, hook_functions in plugin_instance.hooks.items():
                if hook_name not in self.hooks:
                    self.hooks[hook_name] = []
                self.hooks[hook_name].extend(hook_functions)

            plugin_instance.state = PluginState.ACTIVE
            self.active_plugins[plugin_name] = plugin_instance

            logger.info(f"Plugin {plugin_name} loaded successfully")
            self.plugin_loaded.emit(plugin_instance)
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            if plugin_name in self.plugins:
                plugin_instance = self.plugins[plugin_name]
                plugin_instance.state = PluginState.ERROR
                plugin_instance.error_message = str(e)
                self.plugin_error.emit(plugin_name, str(e))
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name not in self.plugins:
            return False

        plugin_instance = self.plugins[plugin_name]

        try:
            # Deactivate and shutdown
            if plugin_instance.instance:
                plugin_instance.instance.deactivate()
                plugin_instance.instance.shutdown()

            # Remove hooks
            for hook_name, hook_functions in plugin_instance.hooks.items():
                if hook_name in self.hooks:
                    for hook_func in hook_functions:
                        if hook_func in self.hooks[hook_name]:
                            self.hooks[hook_name].remove(hook_func)

            # Remove from active plugins
            if plugin_name in self.active_plugins:
                del self.active_plugins[plugin_name]

            plugin_instance.state = PluginState.UNLOADED
            logger.info(f"Plugin {plugin_name} unloaded")
            self.plugin_unloaded.emit(plugin_name)
            return True

        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            plugin_instance.state = PluginState.ERROR
            plugin_instance.error_message = str(e)
            return False

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call all functions registered for a hook
        Returns list of return values from hook functions
        """
        if hook_name not in self.hooks:
            return []

        results = []
        for hook_func in self.hooks[hook_name]:
            try:
                result = hook_func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in hook {hook_name}: {e}")

        return results

    def get_plugin(self, plugin_name: str) -> Optional[PluginInstance]:
        """Get a loaded plugin instance"""
        return self.plugins.get(plugin_name)

    def get_active_plugins(self) -> Dict[str, PluginInstance]:
        """Get all active plugins"""
        return self.active_plugins.copy()

    def get_plugin_info(self) -> List[PluginInfo]:
        """Get information about all loaded plugins"""
        return [plugin.info for plugin in self.plugins.values()]
    
    def is_plugin_trusted(self, plugin_name: str) -> bool:
        """Check if a plugin is marked as trusted"""
        return self._trusted_plugins.get(plugin_name, False)
    
    def set_plugin_trusted(self, plugin_name: str, trusted: bool) -> None:
        """Mark a plugin as trusted or untrusted"""
        self._trusted_plugins[plugin_name] = trusted
        logger.debug(f"Plugin {plugin_name} marked as {'trusted' if trusted else 'untrusted'}")
    
    def should_warn_about_plugin(self, plugin_name: str) -> bool:
        """Check if we should warn about loading a plugin (not trusted and not previously loaded)"""
        return not self.is_plugin_trusted(plugin_name) and plugin_name not in self.plugins
    
    def get_security_warning_message(self, plugin_info: PluginInfo) -> str:
        """Generate a security warning message for a plugin"""
        return (
            f"Security Warning: Loading plugin '{plugin_info.name}' v{plugin_info.version}\n"
            f"Author: {plugin_info.author}\n\n"
            f"This plugin has full access to your system and can:\n"
            f"- Read/write files\n"
            f"- Execute commands\n"
            f"- Access system resources\n\n"
            f"Only load plugins from trusted sources. Continue?"
        )

# Hook constants - predefined hook points in the application
class PluginHooks:
    """Predefined hook points for plugins"""

    # Application lifecycle
    APP_STARTUP = "app_startup"
    APP_SHUTDOWN = "app_shutdown"

    # UI events
    UI_MAIN_WINDOW_CREATED = "ui_main_window_created"
    UI_MENU_BAR_CREATED = "ui_menu_bar_created"
    UI_TOOLBAR_CREATED = "ui_toolbar_created"

    # Dialogue events
    DIALOGUE_LOADED = "dialogue_loaded"
    DIALOGUE_SAVED = "dialogue_saved"
    DIALOGUE_MODIFIED = "dialogue_modified"

    # Node events
    NODE_CREATED = "node_created"
    NODE_MODIFIED = "node_modified"
    NODE_DELETED = "node_deleted"

    # Option events
    OPTION_CREATED = "option_created"
    OPTION_MODIFIED = "option_modified"
    OPTION_DELETED = "option_deleted"

    # Testing events
    TESTING_STARTED = "testing_started"
    TESTING_COMPLETED = "testing_completed"

    # Scripting events
    SCRIPT_EXECUTED = "script_executed"
    SCRIPT_VALIDATED = "script_validated"

    # Parser events
    PARSER_FILE_LOADED = "parser_file_loaded"
    PARSER_FILE_SAVED = "parser_file_saved"
    
    # AI events (NEW)
    AI_INITIALIZED = "ai_initialized"
    AI_REQUEST_STARTED = "ai_request_started"
    AI_REQUEST_COMPLETED = "ai_request_completed"
    AI_SUGGESTION_GENERATED = "ai_suggestion_generated"
    AI_ERROR = "ai_error"

# Example plugin template
PLUGIN_TEMPLATE = '''
"""
Example Plugin for Fallout Dialogue Creator

This is a template for creating custom plugins.
"""

from core.plugin_system import PluginInterface, PluginType, PluginHooks, PluginInfo

class ExamplePlugin(PluginInterface):
    """Example plugin demonstrating basic functionality"""

    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="Example Plugin",
            version="1.0.0",
            description="Demonstrates plugin functionality",
            author="Your Name",
            plugin_type=PluginType.UI_EXTENSION
        )

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
        return True

    def get_hooks(self):
        """Return hook functions"""
        return {
            PluginHooks.APP_STARTUP: [self.on_app_startup],
            PluginHooks.DIALOGUE_LOADED: [self.on_dialogue_loaded],
        }

    def on_app_startup(self, app):
        """Called when application starts"""
        print("Plugin: Application startup detected")

    def on_dialogue_loaded(self, dialogue):
        """Called when a dialogue is loaded"""
        print(f"Plugin: Dialogue loaded - {dialogue.npcname}")
'''