"""
Dialogue management and business logic

This module provides the DialogManager class which handles:
- Loading and saving dialogue files via FMF parser
- Managing dialogue state and modifications
- Integration with the Dialogue Testing Engine for validation
- Player character management
- Node and option manipulation

The DialogManager serves as the main interface between the UI and core dialogue functionality.
"""

from typing import Optional, List
from pathlib import Path
import logging
from PyQt6.QtCore import QObject, pyqtSignal

from models.dialogue import Dialogue, DialogueNode, PlayerCharacter, PlayerOption
from .settings import Settings
from .fmf_parser import FMFParser
from .parse_worker import ParseWorker
from .dialogue_testing_engine import DialogueTestingEngine, TestReport
from .scripting_engine import ScriptingEngine, DialogueScriptContext, ScriptExecutionReport
from .plugin_system import PluginManager, PluginHooks

logger = logging.getLogger(__name__)

class DialogManager(QObject):
    """Manages dialogue data and operations"""

    # Signals
    dialogue_loaded = pyqtSignal(Dialogue)
    dialogue_changed = pyqtSignal()
    node_selected = pyqtSignal(int)  # node index
    parsing_progress = pyqtSignal(int, str)  # progress percentage, current operation
    parsing_error = pyqtSignal(str)  # error message

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.current_dialogue: Optional[Dialogue] = None
        self.current_file: Optional[Path] = None
        self.player = PlayerCharacter()
        self.is_modified = False
        self.fmf_parser = FMFParser()
        self.testing_engine = DialogueTestingEngine()
        self.scripting_engine = ScriptingEngine()
        self.plugin_manager = PluginManager()
        self._selected_node_index: int = -1  # Track selected node index

    def new_dialogue(self) -> Dialogue:
        """Create a new empty dialogue"""
        dialogue = Dialogue()
        dialogue.filename = "untitled"
        self.current_dialogue = dialogue
        self.current_file = None
        self.is_modified = False
        self.dialogue_loaded.emit(dialogue)
        logger.info("Created new dialogue")
        return dialogue

    def load_dialogue(self, file_path: Path) -> bool:
        """Load dialogue from file using background worker"""
        try:
            logger.debug(f"FMF parsing initiated for file: {file_path}")
            # Create and start parse worker
            self.parse_worker = ParseWorker(file_path)
            self.parse_worker.progress_updated.connect(self.parsing_progress.emit)
            self.parse_worker.parsing_finished.connect(self._on_parsing_finished)
            self.parse_worker.parsing_error.connect(self._on_parsing_error)
            self.parse_worker.start()

            logger.info(f"Started parsing dialogue from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to start parsing: {e}")
            return False

    def _on_parsing_finished(self, dialogue: Dialogue):
        """Handle successful parsing completion"""
        dialogue.filename = str(self.parse_worker.file_path)

        self.current_dialogue = dialogue
        self.current_file = self.parse_worker.file_path
        self.is_modified = False
        self.dialogue_loaded.emit(dialogue)

        # Notify plugins
        self.plugin_manager.call_hook(PluginHooks.DIALOGUE_LOADED, dialogue)

        # Clean up worker - wait for thread to finish first
        if self.parse_worker and self.parse_worker.isRunning():
            self.parse_worker.wait(5000)  # Wait up to 5 seconds
        self.parse_worker.deleteLater()
        self.parse_worker = None

        logger.info(f"Loaded dialogue from {self.current_file}")

    def _on_parsing_error(self, error_msg: str):
        """Handle parsing error"""
        self.parsing_error.emit(error_msg)

        # Clean up worker - wait for thread to finish first
        if hasattr(self, 'parse_worker') and self.parse_worker:
            if self.parse_worker.isRunning():
                self.parse_worker.wait(5000)  # Wait up to 5 seconds
            self.parse_worker.deleteLater()
            self.parse_worker = None

        logger.error(f"Failed to parse dialogue: {error_msg}")

    def save_dialogue(self, file_path: Optional[Path] = None) -> bool:
        """Save dialogue to file"""
        if not self.current_dialogue:
            return False

        try:
            save_path = file_path or self.current_file
            if not save_path:
                return False

            self.fmf_parser.save_to_file(self.current_dialogue, save_path)
            self.current_file = save_path
            self.is_modified = False
            logger.info(f"Saved dialogue to {save_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save dialogue: {e}")
            return False

    def get_current_dialogue(self) -> Optional[Dialogue]:
        """Get current dialogue"""
        return self.current_dialogue

    def get_current_node(self) -> Optional[DialogueNode]:
        """Get currently selected node.
        
        Returns the node at the currently selected index, or None if no node is selected.
        Use set_selected_node() to update the selected node.
        """
        if not self.current_dialogue:
            return None
        if self._selected_node_index < 0 or self._selected_node_index >= len(self.current_dialogue.nodes):
            return None
        return self.current_dialogue.nodes[self._selected_node_index]
    
    def set_selected_node(self, index: int) -> None:
        """Set the currently selected node index.
        
        Args:
            index: The index of the node to select, or -1 to deselect
        """
        self._selected_node_index = index
        if index >= 0:
            self.node_selected.emit(index)
        logger.debug(f"Node selected: {index}")

    def add_node(self, node: DialogueNode):
        """Add a new node to the dialogue"""
        if not self.current_dialogue:
            return

        self.current_dialogue.nodes.append(node)
        self.current_dialogue.nodecount += 1
        self.mark_modified()
        logger.info(f"Added node: {node.nodename}")

    def update_node(self, index: int, node: DialogueNode):
        """Update existing node"""
        if not self.current_dialogue or index >= len(self.current_dialogue.nodes):
            return

        self.current_dialogue.nodes[index] = node
        self.mark_modified()
        logger.info(f"Updated node: {node.nodename}")

    def delete_node(self, index: int):
        """Delete node at index"""
        if not self.current_dialogue or index >= len(self.current_dialogue.nodes):
            return

        node_name = self.current_dialogue.nodes[index].nodename
        del self.current_dialogue.nodes[index]
        self.current_dialogue.nodecount -= 1
        self.mark_modified()
        logger.info(f"Deleted node: {node_name}")

    def mark_modified(self):
        """Mark dialogue as modified"""
        self.is_modified = True
        self.dialogue_changed.emit()

        # Notify plugins
        if self.current_dialogue:
            self.plugin_manager.call_hook(PluginHooks.DIALOGUE_MODIFIED, self.current_dialogue)

    def resolve_nodes(self):
        """Resolve all node references"""
        if self.current_dialogue:
            self.current_dialogue.resolve_nodes()
            logger.info("Resolved node references")

    def get_node_names(self) -> List[str]:
        """Get list of all node names"""
        if not self.current_dialogue:
            return []
        return [node.nodename for node in self.current_dialogue.nodes]

    def find_node_by_name(self, name: str) -> int:
        """Find node index by name"""
        if not self.current_dialogue:
            return -1
        return self.current_dialogue.get_node_index(name)

    def test_dialogue(self) -> Optional[TestReport]:
        """Run comprehensive tests on the current dialogue"""
        if not self.current_dialogue:
            logger.warning("No dialogue loaded for testing")
            return None

        logger.info(f"Running dialogue tests for: {self.current_dialogue.npcname}")
        try:
            report = self.testing_engine.test_dialogue(self.current_dialogue)
            logger.info(f"Dialogue testing completed. Issues found: {len(report.issues)}")
            return report
        except Exception as e:
            logger.error(f"Error during dialogue testing: {e}")
            return None

    def get_test_report_text(self, report: TestReport) -> str:
        """Generate human-readable test report"""
        return self.testing_engine.generate_report_text(report)

    def execute_script(self, script_code: str, node: Optional[DialogueNode] = None,
                      option: Optional[PlayerOption] = None) -> ScriptExecutionReport:
        """Execute a script in the current dialogue context"""
        if not self.current_dialogue:
            return ScriptExecutionReport(
                result=ScriptExecutionReport.ScriptResult.ERROR,
                error_message="No dialogue loaded"
            )

        context = DialogueScriptContext(
            dialogue=self.current_dialogue,
            player=self.player,
            current_node=node,
            selected_option=option,
            variables={var.name: var.value for var in self.current_dialogue.variables}
        )

        return self.scripting_engine.execute_script(script_code, context)

    def validate_script(self, script_code: str) -> dict:
        """Validate script syntax and security"""
        info = self.scripting_engine.get_script_info(script_code)

        # Notify plugins about script validation
        self.plugin_manager.call_hook(PluginHooks.SCRIPT_VALIDATED, script_code, info)

        return info

    def get_plugin_manager(self) -> PluginManager:
        """Get the plugin manager instance"""
        return self.plugin_manager