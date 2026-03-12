"""
Main application window for Fallout Dialogue Creator
"""

import logging

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QListWidget, QListWidgetItem,
    QTabWidget, QStatusBar, QMenuBar, QMenu, QMessageBox, QFileDialog,
    QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence, QFont

from core.dialog_manager import DialogManager
from core.settings import Settings
from models.dialogue import Dialogue, DialogueNode
from ui.diagram_widget import DiagramWidget

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, dialog_manager: DialogManager, settings: Settings):
        super().__init__()
        self.dialog_manager = dialog_manager
        self.settings = settings

        self.setup_ui()
        self.setup_menus()
        self.setup_connections()
        self.apply_settings()

        # Initialize with new dialogue
        self.dialog_manager.new_dialogue()

    def setup_ui(self):
        """Setup the main UI components"""
        self.setWindowTitle("Fallout Dialogue Creator 2.0")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Toolbar
        self.setup_toolbar()

        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Dialogue structure
        self.setup_left_panel(splitter)

        # Right panel - Node editor
        self.setup_right_panel(splitter)

        main_splitter.addWidget(splitter)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def setup_left_panel(self, splitter):
        """Setup the left panel with dialogue structure"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Tab widget for different views
        self.tab_widget = QTabWidget()

        # Nodes tab
        self.nodes_tree = QTreeWidget()
        self.nodes_tree.setHeaderLabel("Dialogue Nodes")
        self.nodes_tree.itemSelectionChanged.connect(self.on_node_selected)
        self.nodes_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.nodes_tree.customContextMenuRequested.connect(self.on_node_context_menu)
        self.tab_widget.addTab(self.nodes_tree, "Nodes")

        # Float nodes tab
        self.float_list = QListWidget()
        self.tab_widget.addTab(self.float_list, "Float Messages")

        # Skill checks tab
        self.skill_list = QListWidget()
        self.tab_widget.addTab(self.skill_list, "Skill Checks")

        # Scripts tab
        self.scripts_list = QListWidget()
        self.scripts_list.itemDoubleClicked.connect(self.on_script_double_clicked)
        self.tab_widget.addTab(self.scripts_list, "Scripts")

        # Diagram tab
        self.diagram_widget = DiagramWidget()
        self.tab_widget.addTab(self.diagram_widget, "Diagram")

        left_layout.addWidget(self.tab_widget)

        # Node controls
        controls_layout = QHBoxLayout()

        from PyQt6.QtWidgets import QPushButton
        add_node_btn = QPushButton("Add Node")
        add_node_btn.clicked.connect(self.on_add_node)
        controls_layout.addWidget(add_node_btn)

        delete_node_btn = QPushButton("Delete Node")
        delete_node_btn.clicked.connect(self.on_delete_node)
        controls_layout.addWidget(delete_node_btn)

        controls_layout.addStretch()
        left_layout.addLayout(controls_layout)

        splitter.addWidget(left_widget)
        splitter.setSizes([400, 1000])

    def setup_right_panel(self, splitter):
        """Setup the right panel with node editor"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Node info section
        self.node_info_edit = QTextEdit()
        self.node_info_edit.setPlaceholderText("NPC Text")
        self.node_info_edit.setMaximumHeight(100)
        self.node_info_edit.textChanged.connect(self.on_node_text_changed)
        right_layout.addWidget(self.node_info_edit)

        # Player options list
        self.options_list = QListWidget()
        self.options_list.itemDoubleClicked.connect(self.on_option_double_clicked)
        self.options_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.options_list.customContextMenuRequested.connect(self.on_option_context_menu)
        right_layout.addWidget(self.options_list)

        # Option controls
        option_controls_layout = QHBoxLayout()
        from PyQt6.QtWidgets import QPushButton
        add_option_btn = QPushButton("Add Option")
        add_option_btn.clicked.connect(self.on_add_option)
        option_controls_layout.addWidget(add_option_btn)

        delete_option_btn = QPushButton("Delete Option")
        delete_option_btn.clicked.connect(self.on_delete_option)
        option_controls_layout.addWidget(delete_option_btn)

        option_controls_layout.addStretch()
        right_layout.addLayout(option_controls_layout)

        # Node notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Designer Notes")
        self.notes_edit.setMaximumHeight(150)
        self.notes_edit.textChanged.connect(self.on_node_notes_changed)
        right_layout.addWidget(self.notes_edit)

        splitter.addWidget(right_widget)

    def setup_toolbar(self):
        """Setup main toolbar"""
        from PyQt6.QtWidgets import QToolBar
        toolbar = self.addToolBar("Main")

        # New dialogue
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.on_new_dialogue)
        toolbar.addAction(new_action)

        # Open dialogue
        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.on_open_dialogue)
        toolbar.addAction(open_action)

        # Save dialogue
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.on_save_dialogue)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Add node
        add_node_action = QAction("Add Node", self)
        add_node_action.triggered.connect(self.on_add_node)
        toolbar.addAction(add_node_action)

        # Add option
        add_option_action = QAction("Add Option", self)
        add_option_action.triggered.connect(self.on_add_option)
        toolbar.addAction(add_option_action)

        toolbar.addSeparator()

        # Test dialogue
        test_action = QAction("Test Dialogue", self)
        test_action.triggered.connect(self.on_test_dialogue)
        toolbar.addAction(test_action)

    def setup_menus(self):
        """Setup application menus"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.on_new_dialogue)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.on_open_dialogue)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.on_save_dialogue)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.on_save_dialogue_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        # Dialogue menu
        dialogue_menu = menubar.addMenu("&Dialogue")

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Plugin Manager menu item
        plugin_manager_action = QAction("&Plugin Manager", self)
        plugin_manager_action.triggered.connect(self.on_plugin_manager)
        tools_menu.addAction(plugin_manager_action)

        tools_menu.addSeparator()

        test_action = QAction("&Test Dialogue", self)
        test_action.setShortcut("Ctrl+T")
        test_action.triggered.connect(self.on_test_dialogue)
        tools_menu.addAction(test_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)

    def setup_connections(self):
        """Setup signal connections"""
        self.dialog_manager.dialogue_loaded.connect(self.on_dialogue_loaded)
        self.dialog_manager.dialogue_changed.connect(self.on_dialogue_changed)
        self.dialog_manager.parsing_progress.connect(self.on_parsing_progress)
        self.dialog_manager.parsing_error.connect(self.on_parsing_error)

    def apply_settings(self):
        """Apply settings to UI"""
        font = QFont()
        font.setFamily(self.settings.get('font_family'))
        font.setPointSize(self.settings.get('font_size'))
        self.setFont(font)

    @pyqtSlot(Dialogue)
    def on_dialogue_loaded(self, dialogue: Dialogue):
        """Handle dialogue loaded signal"""
        logger.debug(f"FMF parsing completed successfully - loaded dialogue with {dialogue.nodecount} nodes")
        logger.debug("FMF main window: Dialogue loaded signal received")

        # Add debug logging for UI updates
        logger.debug(f"FMF main window: About to update window title")
        self.update_window_title()
        logger.debug(f"FMF main window: Window title updated")

        logger.debug(f"FMF main window: About to populate nodes tree")
        self.populate_nodes_tree()
        logger.debug(f"FMF main window: Nodes tree populated")

        self.populate_float_list()
        self.populate_skill_list()
        self.populate_scripts_list()

        logger.debug(f"FMF main window: About to update diagram")
        self.diagram_widget.set_dialogue(dialogue)
        logger.debug(f"FMF main window: Diagram updated")

        logger.debug(f"FMF main window: About to update status bar")
        self.status_bar.showMessage(f"Loaded dialogue with {dialogue.nodecount} nodes")
        logger.debug(f"FMF main window: Status bar updated")

        logger.debug("FMF main window: Dialogue loaded handling complete")

    @pyqtSlot()
    def on_dialogue_changed(self):
        """Handle dialogue changed signal"""
        self.update_window_title()
        # Update diagram when dialogue changes
        dialogue = self.dialog_manager.get_current_dialogue()
        self.diagram_widget.set_dialogue(dialogue)

    @pyqtSlot(int, str)
    def on_parsing_progress(self, progress: int, operation: str):
        """Handle parsing progress updates"""
        logger.debug(f"FMF parsing progress: {progress}% - {operation}")
        if not hasattr(self, 'progress_dialog') or self.progress_dialog is None:
            logger.debug("FMF main window: Creating new progress dialog")
            self.progress_dialog = QProgressDialog("Parsing FMF file...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.progress_dialog.setAutoClose(True)
            self.progress_dialog.setAutoReset(True)
            self.progress_dialog.show()
            logger.debug("FMF main window: Progress dialog created and shown")

        logger.debug(f"FMF main window: Updating progress dialog to {progress}% - {operation}")
        self.progress_dialog.setValue(progress)
        self.progress_dialog.setLabelText(operation)

        # Process events to keep UI responsive
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # Force UI update
        if self.progress_dialog:
            self.progress_dialog.repaint()
        logger.debug(f"FMF main window: Progress dialog updated to {progress}%")

        # Close progress dialog when parsing is complete (100%)
        if progress >= 100:
            logger.debug("FMF main window: Progress reached 100%, closing dialog")
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
                logger.debug("FMF main window: Progress dialog closed at 100%")

    @pyqtSlot(str)
    def on_parsing_error(self, error_msg: str):
        """Handle parsing error"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        QMessageBox.critical(self, "Parsing Error", f"Failed to parse FMF file:\n{error_msg}")

    def update_window_title(self):
        """Update window title with current file and modified status"""
        title = "Fallout Dialogue Creator 2.0"
        if self.dialog_manager.current_file:
            title += f" - [{self.dialog_manager.current_file.name}]"
        else:
            title += " - [untitled]"

        if self.dialog_manager.is_modified:
            title += "*"

        self.setWindowTitle(title)

    def populate_nodes_tree(self):
        """Populate the nodes tree widget"""
        self.nodes_tree.clear()

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return

        for node in dialogue.nodes:
            item = QTreeWidgetItem([node.nodename])
            item.setData(0, Qt.ItemDataRole.UserRole, dialogue.nodes.index(node))

            # Add options as children
            for option in node.options:
                option_item = QTreeWidgetItem([f"→ {option.nodelink}"])
                option_item.setData(0, Qt.ItemDataRole.UserRole, node.options.index(option))
                item.addChild(option_item)

            self.nodes_tree.addTopLevelItem(item)

        self.nodes_tree.expandAll()

    def populate_float_list(self):
        """Populate the float messages list"""
        self.float_list.clear()

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return

        # TODO: Implement float messages population when FloatNode model is available
        pass

    def populate_skill_list(self):
        """Populate the skill checks list"""
        self.skill_list.clear()

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return

        # TODO: Implement skill checks population when SkillCheck model is available
        pass

    def populate_scripts_list(self):
        """Populate the scripts list"""
        self.scripts_list.clear()

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return

        # Add custom procedures
        for proc in dialogue.customprocs:
            item = QListWidgetItem(f"Procedure: {proc.name}")
            item.setData(Qt.ItemDataRole.UserRole, ("procedure", dialogue.customprocs.index(proc)))
            self.scripts_list.addItem(item)

        # Add node custom code
        for node in dialogue.nodes:
            if node.customcode.strip():
                item = QListWidgetItem(f"Node: {node.nodename}")
                item.setData(Qt.ItemDataRole.UserRole, ("node", dialogue.nodes.index(node)))
                self.scripts_list.addItem(item)

    @pyqtSlot()
    def on_node_selected(self):
        """Handle node selection in tree"""
        current_item = self.nodes_tree.currentItem()
        if not current_item:
            return

        # Get node index from item data
        node_index = current_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(node_index, int):
            self.display_node(node_index)

    def display_node(self, node_index: int):
        """Display node information in the right panel"""
        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue or node_index >= len(dialogue.nodes):
            return

        node = dialogue.nodes[node_index]

        # Update NPC text
        self.node_info_edit.setPlainText(node.npctext)

        # Update options list
        self.options_list.clear()
        for option in node.options:
            item = QListWidgetItem(option.optiontext)
            item.setData(Qt.ItemDataRole.UserRole, node.options.index(option))
            self.options_list.addItem(item)

        # Update notes
        self.notes_edit.setPlainText(node.notes)

    @pyqtSlot(QListWidgetItem)
    def on_option_double_clicked(self, item: QListWidgetItem):
        """Handle option double-click"""
        # Get the current node
        current_item = self.nodes_tree.currentItem()
        if not current_item:
            return

        node_index = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(node_index, int):
            return

        option_index = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(option_index, int):
            return

        self.edit_option(node_index, option_index)

    @pyqtSlot(QListWidgetItem)
    def on_script_double_clicked(self, item: QListWidgetItem):
        """Handle script double-click"""
        script_data = item.data(Qt.ItemDataRole.UserRole)
        if not script_data or len(script_data) != 2:
            return

        script_type, script_index = script_data
        self.edit_script(script_type, script_index)

    @pyqtSlot()
    def on_node_text_changed(self):
        """Handle NPC text changes"""
        self.update_current_node()

    @pyqtSlot()
    def on_node_notes_changed(self):
        """Handle node notes changes"""
        self.update_current_node()

    def update_current_node(self):
        """Update the currently displayed node with editor changes"""
        current_item = self.nodes_tree.currentItem()
        if not current_item:
            return

        node_index = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(node_index, int):
            return

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue or node_index >= len(dialogue.nodes):
            return

        node = dialogue.nodes[node_index]
        node.npctext = self.node_info_edit.toPlainText()
        node.notes = self.notes_edit.toPlainText()

        self.dialog_manager.mark_modified()

    def edit_option(self, node_index: int, option_index: int):
        """Open option editing dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit, QPushButton

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue or node_index >= len(dialogue.nodes):
            return

        node = dialogue.nodes[node_index]
        if option_index >= len(node.options):
            return

        option = node.options[option_index]

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Player Option")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Option text
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Option Text:"))
        self.option_text_edit = QLineEdit(option.optiontext)
        text_layout.addWidget(self.option_text_edit)
        layout.addLayout(text_layout)

        # Node link
        link_layout = QHBoxLayout()
        link_layout.addWidget(QLabel("Link to Node:"))
        self.node_link_combo = QComboBox()
        node_names = self.dialog_manager.get_node_names()
        self.node_link_combo.addItems(node_names)
        current_link_index = self.dialog_manager.find_node_by_name(option.nodelink)
        if current_link_index >= 0:
            self.node_link_combo.setCurrentIndex(current_link_index)
        link_layout.addWidget(self.node_link_combo)
        layout.addLayout(link_layout)

        # Reaction
        reaction_layout = QHBoxLayout()
        reaction_layout.addWidget(QLabel("Reaction:"))
        self.reaction_combo = QComboBox()
        from models.dialogue import Reaction
        self.reaction_combo.addItems([r.name for r in Reaction])
        self.reaction_combo.setCurrentIndex(option.reaction.value)
        reaction_layout.addWidget(self.reaction_combo)
        layout.addLayout(reaction_layout)

        # Notes
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel("Notes:"))
        self.option_notes_edit = QTextEdit(option.notes)
        self.option_notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.option_notes_edit)
        layout.addLayout(notes_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_option(dialog, node_index, option_index))
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.exec()

    def edit_script(self, script_type: str, script_index: int):
        """Open script editing dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGroupBox, QPlainTextEdit

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return

        script_code = ""
        script_name = ""

        if script_type == "procedure":
            if script_index >= len(dialogue.customprocs):
                return
            proc = dialogue.customprocs[script_index]
            script_code = proc.lines
            script_name = proc.name
        elif script_type == "node":
            if script_index >= len(dialogue.nodes):
                return
            node = dialogue.nodes[script_index]
            script_code = node.customcode
            script_name = node.nodename
        else:
            return

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Script - {script_name}")
        dialog.setModal(True)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        # Script info
        info_group = QGroupBox("Script Information")
        info_layout = QVBoxLayout(info_group)
        info_layout.addWidget(QLabel(f"Type: {script_type.title()}"))
        info_layout.addWidget(QLabel(f"Name: {script_name}"))
        layout.addWidget(info_group)

        # Script editor
        editor_group = QGroupBox("Python Script")
        editor_layout = QVBoxLayout(editor_group)

        self.script_editor = QPlainTextEdit()
        self.script_editor.setPlainText(script_code)
        self.script_editor.setFont(QFont("Consolas", 10))  # Monospace font
        editor_layout.addWidget(self.script_editor)

        layout.addWidget(editor_group)

        # Validation results
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout(validation_group)

        self.validation_text = QTextEdit()
        self.validation_text.setMaximumHeight(100)
        self.validation_text.setReadOnly(True)
        validation_layout.addWidget(self.validation_text)

        validate_button = QPushButton("Validate Script")
        validate_button.clicked.connect(lambda: self.validate_current_script())
        validation_layout.addWidget(validate_button)

        layout.addWidget(validation_group)

        # Buttons
        button_layout = QHBoxLayout()

        test_button = QPushButton("Test Script")
        test_button.clicked.connect(lambda: self.test_current_script(script_type, script_index))
        button_layout.addWidget(test_button)

        button_layout.addStretch()

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_script(dialog, script_type, script_index))
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Initial validation
        self.validate_current_script()

        dialog.exec()

    def validate_current_script(self):
        """Validate the current script in the editor"""
        script_code = self.script_editor.toPlainText()
        info = self.dialog_manager.validate_script(script_code)

        result_text = []
        if info['valid_syntax']:
            result_text.append("✓ Valid Python syntax")
        else:
            result_text.append("✗ Invalid Python syntax")

        if info['security_violations']:
            result_text.append(f"⚠️ Security violations: {len(info['security_violations'])}")
            for violation in info['security_violations'][:5]:  # Show first 5
                result_text.append(f"  - {violation}")
            if len(info['security_violations']) > 5:
                result_text.append(f"  ... and {len(info['security_violations']) - 5} more")
        else:
            result_text.append("✓ No security violations")

        result_text.append(f"Lines: {info['line_count']}, Characters: {info['char_count']}")

        self.validation_text.setPlainText("\n".join(result_text))

    def test_current_script(self, script_type: str, script_index: int):
        """Test the current script"""
        script_code = self.script_editor.toPlainText()

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return

        node = None
        if script_type == "node" and script_index < len(dialogue.nodes):
            node = dialogue.nodes[script_index]

        report = self.dialog_manager.execute_script(script_code, node)

        # Show results
        from PyQt6.QtWidgets import QMessageBox
        if report.result.value == "success":
            QMessageBox.information(
                self, "Script Test",
                f"Script executed successfully!\n\n"
                f"Execution time: {report.execution_time:.3f}s\n"
                f"Output: {report.output}"
            )
        else:
            QMessageBox.warning(
                self, "Script Test Failed",
                f"Script execution failed: {report.result.value}\n\n"
                f"Error: {report.error_message}\n"
                f"Execution time: {report.execution_time:.3f}s"
            )

    def save_script(self, dialog, script_type: str, script_index: int):
        """Save script changes"""
        script_code = self.script_editor.toPlainText()

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return

        if script_type == "procedure":
            if script_index < len(dialogue.customprocs):
                dialogue.customprocs[script_index].lines = script_code
        elif script_type == "node":
            if script_index < len(dialogue.nodes):
                dialogue.nodes[script_index].customcode = script_code

        self.dialog_manager.mark_modified()
        self.populate_scripts_list()  # Refresh the scripts list
        dialog.accept()

    @pyqtSlot()
    def on_add_node(self):
        """Add a new node"""
        from models.dialogue import DialogueNode
        node = DialogueNode(
            nodename=f"Node{len(self.dialog_manager.get_current_dialogue().nodes) + 1}",
            npctext="New node text",
            notes="Node notes"
        )
        self.dialog_manager.add_node(node)
        self.populate_nodes_tree()

    @pyqtSlot()
    def on_delete_node(self):
        """Delete the currently selected node"""
        current_item = self.nodes_tree.currentItem()
        if not current_item:
            return

        node_index = current_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(node_index, int):
            self.dialog_manager.delete_node(node_index)
            self.populate_nodes_tree()

    @pyqtSlot()
    def on_add_option(self):
        """Add a new option to current node"""
        current_item = self.nodes_tree.currentItem()
        if not current_item:
            return

        node_index = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(node_index, int):
            return

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue or node_index >= len(dialogue.nodes):
            return

        from models.dialogue import PlayerOption
        option = PlayerOption(
            optiontext="New option",
            nodelink="",
            notes="Option notes"
        )
        dialogue.nodes[node_index].options.append(option)
        dialogue.nodes[node_index].optioncnt += 1
        self.dialog_manager.mark_modified()
        self.display_node(node_index)

    @pyqtSlot()
    def on_delete_option(self):
        """Delete selected option"""
        current_item = self.nodes_tree.currentItem()
        if not current_item:
            return

        node_index = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(node_index, int):
            return

        selected_items = self.options_list.selectedItems()
        if not selected_items:
            return

        option_index = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if isinstance(option_index, int):
            dialogue = self.dialog_manager.get_current_dialogue()
            if dialogue and node_index < len(dialogue.nodes):
                node = dialogue.nodes[node_index]
                if option_index < len(node.options):
                    del node.options[option_index]
                    node.optioncnt -= 1
                    self.dialog_manager.mark_modified()
                    self.display_node(node_index)

    def save_option(self, dialog, node_index: int, option_index: int):
        """Save option changes"""
        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue or node_index >= len(dialogue.nodes):
            return

        node = dialogue.nodes[node_index]
        if option_index >= len(node.options):
            return

        option = node.options[option_index]
        option.optiontext = self.option_text_edit.text()
        option.nodelink = self.node_link_combo.currentText()
        from models.dialogue import Reaction
        option.reaction = Reaction(self.reaction_combo.currentIndex())
        option.notes = self.option_notes_edit.toPlainText()

        # Update options list display
        self.display_node(node_index)
        self.populate_nodes_tree()  # Refresh tree to show updated option text

        self.dialog_manager.mark_modified()
        dialog.accept()

    def on_node_context_menu(self, position):
        """Show context menu for nodes tree"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        add_node_action = menu.addAction("Add Node")
        add_node_action.triggered.connect(self.on_add_node)

        current_item = self.nodes_tree.currentItem()
        if current_item:
            delete_node_action = menu.addAction("Delete Node")
            delete_node_action.triggered.connect(self.on_delete_node)

        menu.exec(self.nodes_tree.mapToGlobal(position))

    def on_option_context_menu(self, position):
        """Show context menu for options list"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        add_option_action = menu.addAction("Add Option")
        add_option_action.triggered.connect(self.on_add_option)

        selected_items = self.options_list.selectedItems()
        if selected_items:
            edit_option_action = menu.addAction("Edit Option")
            edit_option_action.triggered.connect(lambda: self.on_option_double_clicked(selected_items[0]))

            delete_option_action = menu.addAction("Delete Option")
            delete_option_action.triggered.connect(self.on_delete_option)

        menu.exec(self.options_list.mapToGlobal(position))

    @pyqtSlot()
    def on_new_dialogue(self):
        """Handle new dialogue action"""
        if self.check_save_changes():
            self.dialog_manager.new_dialogue()

    @pyqtSlot()
    def on_open_dialogue(self):
        """Handle open dialogue action"""
        logger.debug("FMF file selection started")
        if not self.check_save_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Dialogue", str(self.settings.get_dialogue_path()),
            "FMF Dialogue Files (*.fmf);;All Files (*)"
        )

        if file_path:
            from pathlib import Path
            self.dialog_manager.load_dialogue(Path(file_path))

    @pyqtSlot()
    def on_save_dialogue(self):
        """Handle save dialogue action"""
        if self.dialog_manager.current_file:
            self.dialog_manager.save_dialogue()
        else:
            self.on_save_dialogue_as()

    @pyqtSlot()
    def on_save_dialogue_as(self):
        """Handle save dialogue as action"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Dialogue", str(self.settings.get_dialogue_path()),
            "FMF Dialogue Files (*.fmf);;All Files (*)"
        )

        if file_path:
            from pathlib import Path
            self.dialog_manager.save_dialogue(Path(file_path))

    def check_save_changes(self) -> bool:
        """Check if there are unsaved changes and prompt to save"""
        if not self.dialog_manager.is_modified:
            return True

        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "The current dialogue has unsaved changes. Save before proceeding?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Save:
            self.on_save_dialogue()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False

    @pyqtSlot()
    def on_plugin_manager(self):
        """Show plugin manager dialog"""
        self.show_plugin_manager()

    def show_plugin_manager(self):
        """Display the plugin manager interface"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QPushButton, QLabel, QGroupBox, QSplitter

        dialog = QDialog(self)
        dialog.setWindowTitle("Plugin Manager")
        dialog.setModal(True)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        # Main splitter
        splitter = QSplitter()
        layout.addWidget(splitter)

        # Left panel - Plugin list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        plugin_list_label = QLabel("Loaded Plugins:")
        left_layout.addWidget(plugin_list_label)

        self.plugin_list = QListWidget()
        self.plugin_list.itemSelectionChanged.connect(self.on_plugin_selected)
        left_layout.addWidget(self.plugin_list)

        # Plugin control buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_plugin_list)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        left_layout.addLayout(button_layout)

        # Right panel - Plugin details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Plugin info group
        info_group = QGroupBox("Plugin Information")
        info_layout = QVBoxLayout(info_group)

        self.plugin_info_text = QTextEdit()
        self.plugin_info_text.setReadOnly(True)
        self.plugin_info_text.setMaximumHeight(150)
        info_layout.addWidget(self.plugin_info_text)

        right_layout.addWidget(info_group)

        # Plugin status group
        status_group = QGroupBox("Plugin Status")
        status_layout = QVBoxLayout(status_group)

        self.plugin_status_text = QTextEdit()
        self.plugin_status_text.setReadOnly(True)
        status_layout.addWidget(self.plugin_status_text)

        right_layout.addWidget(status_group)

        # Plugin hooks group
        hooks_group = QGroupBox("Registered Hooks")
        hooks_layout = QVBoxLayout(hooks_group)

        self.plugin_hooks_text = QTextEdit()
        self.plugin_hooks_text.setReadOnly(True)
        hooks_layout.addWidget(self.plugin_hooks_text)

        right_layout.addWidget(hooks_group)

        # Set up splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])

        # Populate plugin list
        self.refresh_plugin_list()

        dialog.exec()

    def refresh_plugin_list(self):
        """Refresh the plugin list display"""
        self.plugin_list.clear()

        # Get plugin manager from dialog manager
        plugin_manager = self.dialog_manager.plugin_manager

        # Add loaded plugins
        for plugin_name, plugin_instance in plugin_manager.plugins.items():
            item = QListWidgetItem(f"{plugin_name} ({plugin_instance.state.value})")
            item.setData(1, plugin_name)  # Store plugin name in item data
            self.plugin_list.addItem(item)

        # Select first item if available
        if self.plugin_list.count() > 0:
            self.plugin_list.setCurrentRow(0)

    def on_plugin_selected(self):
        """Handle plugin selection in the list"""
        current_item = self.plugin_list.currentItem()
        if not current_item:
            return

        plugin_name = current_item.data(1)
        plugin_manager = self.dialog_manager.plugin_manager

        if plugin_name in plugin_manager.plugins:
            plugin_instance = plugin_manager.plugins[plugin_name]

            # Update plugin info
            info_text = f"""Name: {plugin_instance.info.name}
Version: {plugin_instance.info.version}
Description: {plugin_instance.info.description}
Author: {plugin_instance.info.author}
Type: {plugin_instance.info.plugin_type.value}
Dependencies: {', '.join(plugin_instance.info.dependencies) if plugin_instance.info.dependencies else 'None'}
Requires Restart: {'Yes' if plugin_instance.info.requires_restart else 'No'}"""
            self.plugin_info_text.setPlainText(info_text)

            # Update plugin status
            status_text = f"""State: {plugin_instance.state.value}
Error: {plugin_instance.error_message if plugin_instance.error_message else 'None'}"""
            self.plugin_status_text.setPlainText(status_text)

            # Update hooks
            if plugin_instance.hooks:
                hooks_text = "Registered Hooks:\n" + "\n".join([f"• {hook_name}" for hook_name in plugin_instance.hooks.keys()])
            else:
                hooks_text = "No hooks registered"
            self.plugin_hooks_text.setPlainText(hooks_text)
        else:
            self.plugin_info_text.setPlainText("Plugin not found")
            self.plugin_status_text.setPlainText("")
            self.plugin_hooks_text.setPlainText("")

    @pyqtSlot()
    def on_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About Fallout Dialogue Creator",
            "Fallout Dialogue Creator 2.0\n\n"
            "Modern cross-platform rewrite of the Fallout dialogue editor.\n\n"
            "Built with PyQt6 and Python."
        )

    @pyqtSlot()
    def on_test_dialogue(self):
        """Run dialogue testing"""
        report = self.dialog_manager.test_dialogue()
        if report:
            report_text = self.dialog_manager.get_test_report_text(report)
            self.show_test_report(report_text)
        else:
            QMessageBox.warning(self, "Test Failed", "Failed to run dialogue tests.")

    def show_test_report(self, report_text: str):
        """Show test report in a dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Dialogue Test Report")
        dialog.setModal(True)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        report_edit = QTextEdit()
        report_edit.setPlainText(report_text)
        report_edit.setReadOnly(True)
        report_edit.setFont(QFont("Consolas", 9))
        layout.addWidget(report_edit)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(lambda: self.copy_report_to_clipboard(report_text))
        button_layout.addWidget(copy_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        dialog.exec()

    def copy_report_to_clipboard(self, report_text: str):
        """Copy report text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(report_text)

    def closeEvent(self, event):
        """Handle application close"""
        if not self.check_save_changes():
            event.ignore()
        else:
            event.accept()