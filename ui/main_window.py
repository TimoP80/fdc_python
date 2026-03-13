"""
Main application window for Fallout Dialogue Creator
"""

import logging

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QListWidget, QListWidgetItem,
    QTabWidget, QStatusBar, QMenuBar, QMenu, QMessageBox, QFileDialog,
    QProgressDialog, QFrame, QLabel, QDialog, QApplication, QCheckBox,
    QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence, QFont

from core.dialog_manager import DialogManager
from core.plugin_system import PluginHooks
from core.settings import Settings
from models.dialogue import Dialogue, DialogueNode
from ui.diagram_widget import DiagramWidget
from ui.fallout_theme import FalloutUIHelpers, FalloutColors
from ui.fallout_widgets import (
    FalloutButton, SpecialStatBar, FalloutPanel, 
    CRTScanlineOverlay, TerminalTextEdit, FalloutTreeWidget,
    FalloutListWidget, WornMetalPanel
)

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, dialog_manager: DialogManager, settings: Settings):
        super().__init__()
        self.dialog_manager = dialog_manager
        self.settings = settings

        # Apply Fallout theme
        self._apply_fallout_theme()
        
        self.setup_ui()
        self.setup_menus()
        
        # Notify plugins that menu bar has been created
        self.dialog_manager.plugin_manager.call_hook(PluginHooks.UI_MENU_BAR_CREATED, self.menuBar())
        
        self.setup_connections()
        self.apply_settings()

        # Initialize with new dialogue
        self.dialog_manager.new_dialogue()

    def _apply_fallout_theme(self):
        """Apply the Fallout 2 theme to this window"""
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            FalloutUIHelpers.apply_theme(app)
        
        # Set window-specific styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {FalloutColors.DARK_SLATE};
                border: 2px solid {FalloutColors.PANEL_BORDER};
            }}
        """)

    def setup_ui(self):
        """Setup the main UI components"""
        self.setWindowTitle("Fallout Dialogue Creator 2.0")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget with Fallout panel styling
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

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
        self.status_bar.showMessage("Ready | WELCOME TO THE WASTELAND")

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
        right_widget = FalloutPanel("metal")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(4)

        # Node info section
        node_info_label = QLabel("NPC TEXT:")
        node_info_label.setStyleSheet(f"""
            QLabel {{
                color: {FalloutColors.FALLOUT_YELLOW};
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
                padding: 4px;
            }}
        """)
        right_layout.addWidget(node_info_label)

        self.node_info_edit = QTextEdit()
        self.node_info_edit.setPlaceholderText("Enter NPC dialogue text here...")
        self.node_info_edit.setMaximumHeight(100)
        self.node_info_edit.textChanged.connect(self.on_node_text_changed)
        right_layout.addWidget(self.node_info_edit)

        # Player options list
        options_label = QLabel("PLAYER OPTIONS:")
        options_label.setStyleSheet(f"""
            QLabel {{
                color: {FalloutColors.FALLOUT_YELLOW};
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
                padding: 4px;
            }}
        """)
        right_layout.addWidget(options_label)

        self.options_list = FalloutListWidget()
        self.options_list.itemDoubleClicked.connect(self.on_option_double_clicked)
        self.options_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.options_list.customContextMenuRequested.connect(self.on_option_context_menu)
        right_layout.addWidget(self.options_list)

        # Option controls
        option_controls_layout = QHBoxLayout()

        add_option_btn = FalloutButton("Add Option", "rust")
        add_option_btn.clicked.connect(self.on_add_option)
        option_controls_layout.addWidget(add_option_btn)

        delete_option_btn = FalloutButton("Delete Option", "danger")
        delete_option_btn.clicked.connect(self.on_delete_option)
        option_controls_layout.addWidget(delete_option_btn)

        option_controls_layout.addStretch()
        right_layout.addLayout(option_controls_layout)

        # Node notes
        notes_label = QLabel("DESIGNER NOTES:")
        notes_label.setStyleSheet(f"""
            QLabel {{
                color: {FalloutColors.FALLOUT_YELLOW};
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
                padding: 4px;
            }}
        """)
        right_layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add designer notes here...")
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
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {FalloutColors.DARK_METAL};
                border-bottom: 2px solid {FalloutColors.PANEL_BORDER};
                padding: 2px;
            }}
            QMenuBar::item {{
                background-color: {FalloutColors.DARK_METAL};
                color: {FalloutColors.TEXT_NORMAL};
                padding: 6px 12px;
                border: 1px solid transparent;
            }}
            QMenuBar::item:selected {{
                background-color: {FalloutColors.OLIVE_DRAB};
                color: {FalloutColors.FALLOUT_YELLOW};
                border: 1px solid {FalloutColors.RUST_ORANGE};
            }}
            QMenu {{
                background-color: {FalloutColors.PANEL_BACKGROUND};
                border: 2px solid {FalloutColors.PANEL_BORDER};
                padding: 4px;
            }}
            QMenu::item {{
                background-color: transparent;
                color: {FalloutColors.TEXT_NORMAL};
                padding: 6px 30px 6px 20px;
            }}
            QMenu::item:selected {{
                background-color: {FalloutColors.OLIVE_DRAB};
                color: {FalloutColors.FALLOUT_YELLOW};
            }}
        """)

        # ==========================================
        # FILE MENU
        # ==========================================
        file_menu = menubar.addMenu("&File")

        # New dialogue
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("Create a new dialogue")
        new_action.triggered.connect(self.on_new_dialogue)
        file_menu.addAction(new_action)

        # Open dialogue
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an existing FMF dialogue file")
        open_action.triggered.connect(self.on_open_dialogue)
        file_menu.addAction(open_action)

        # Recent files submenu
        self.recent_files_menu = file_menu.addMenu("Recent &Files")
        self.recent_files_menu.setStatusTip("Open recently used files")
        self._populate_recent_files_menu()

        file_menu.addSeparator()

        # Save dialogue
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("Save the current dialogue")
        save_action.triggered.connect(self.on_save_dialogue)
        file_menu.addAction(save_action)

        # Save As
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip("Save the dialogue with a new name")
        save_as_action.triggered.connect(self.on_save_dialogue_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Import submenu
        import_menu = file_menu.addMenu("&Import")
        import_ddf_action = QAction("Import from &DDF...", self)
        import_ddf_action.setStatusTip("Import dialogue from DDF format")
        import_ddf_action.triggered.connect(self.on_import_ddf)
        import_menu.addAction(import_ddf_action)

        import_msg_action = QAction("Import from &MSG...", self)
        import_msg_action.setStatusTip("Import messages from MSG format")
        import_msg_action.triggered.connect(self.on_import_msg)
        import_menu.addAction(import_msg_action)

        # Export submenu
        export_menu = file_menu.addMenu("&Export")
        export_ssl_action = QAction("Export to &SSL...", self)
        export_ssl_action.setStatusTip("Export dialogue to SSL script file")
        export_ssl_action.triggered.connect(self.on_export_ssl)
        export_menu.addAction(export_ssl_action)

        export_msg_action = QAction("Export to &MSG...", self)
        export_msg_action.setStatusTip("Export dialogue to MSG file")
        export_msg_action.triggered.connect(self.on_export_msg)
        export_menu.addAction(export_msg_action)

        export_ddf_action = QAction("Export to &DDF...", self)
        export_ddf_action.setStatusTip("Export dialogue to DDF file")
        export_ddf_action.triggered.connect(self.on_export_ddf)
        export_menu.addAction(export_ddf_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ==========================================
        # EDIT MENU
        # ==========================================
        edit_menu = menubar.addMenu("&Edit")

        # Undo
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setStatusTip("Undo last action")
        undo_action.triggered.connect(self.on_undo)
        edit_menu.addAction(undo_action)

        # Redo
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setStatusTip("Redo last undone action")
        redo_action.triggered.connect(self.on_redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Cut
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.setStatusTip("Cut selected text to clipboard")
        cut_action.triggered.connect(self.on_cut)
        edit_menu.addAction(cut_action)

        # Copy
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.setStatusTip("Copy selected text to clipboard")
        copy_action.triggered.connect(self.on_copy)
        edit_menu.addAction(copy_action)

        # Paste
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.setStatusTip("Paste text from clipboard")
        paste_action.triggered.connect(self.on_paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        # Delete
        delete_action = QAction("&Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.setStatusTip("Delete selected item")
        delete_action.triggered.connect(self.on_delete)
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        # Select All
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.setStatusTip("Select all items")
        select_all_action.triggered.connect(self.on_select_all)
        edit_menu.addAction(select_all_action)

        edit_menu.addSeparator()

        # Find submenu
        find_menu = edit_menu.addMenu("&Find")
        find_action = QAction("&Find Text...", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.setStatusTip("Find text in dialogue")
        find_action.triggered.connect(self.on_find)
        find_menu.addAction(find_action)

        find_next_action = QAction("Find &Next", self)
        find_next_action.setShortcut(QKeySequence.StandardKey.FindNext)
        find_next_action.setStatusTip("Find next occurrence")
        find_next_action.triggered.connect(self.on_find_next)
        find_menu.addAction(find_next_action)

        find_node_action = QAction("Find &Node...", self)
        find_node_action.setShortcut("Ctrl+Shift+N")
        find_node_action.setStatusTip("Find a node by name")
        find_node_action.triggered.connect(self.on_find_node)
        find_menu.addAction(find_node_action)

        # ==========================================
        # VIEW MENU
        # ==========================================
        view_menu = menubar.addMenu("&View")

        # Panels submenu
        panels_menu = view_menu.addMenu("&Panels")

        # Toggle left panel
        self.toggle_left_panel_action = QAction("&Left Panel (Nodes)", self)
        self.toggle_left_panel_action.setCheckable(True)
        self.toggle_left_panel_action.setChecked(True)
        self.toggle_left_panel_action.setStatusTip("Show/hide the left panel")
        self.toggle_left_panel_action.triggered.connect(self.on_toggle_left_panel)
        panels_menu.addAction(self.toggle_left_panel_action)

        # Toggle right panel
        self.toggle_right_panel_action = QAction("&Right Panel (Editor)", self)
        self.toggle_right_panel_action.setCheckable(True)
        self.toggle_right_panel_action.setChecked(True)
        self.toggle_right_panel_action.setStatusTip("Show/hide the right panel")
        self.toggle_right_panel_action.triggered.connect(self.on_toggle_right_panel)
        panels_menu.addAction(self.toggle_right_panel_action)

        # Toggle toolbar
        self.toggle_toolbar_action = QAction("&Toolbar", self)
        self.toggle_toolbar_action.setCheckable(True)
        self.toggle_toolbar_action.setChecked(True)
        self.toggle_toolbar_action.setStatusTip("Show/hide the toolbar")
        self.toggle_toolbar_action.triggered.connect(self.on_toggle_toolbar)
        panels_menu.addAction(self.toggle_toolbar_action)

        # Toggle status bar
        self.toggle_statusbar_action = QAction("&Status Bar", self)
        self.toggle_statusbar_action.setCheckable(True)
        self.toggle_statusbar_action.setChecked(True)
        self.toggle_statusbar_action.setStatusTip("Show/hide the status bar")
        self.toggle_statusbar_action.triggered.connect(self.on_toggle_statusbar)
        panels_menu.addAction(self.toggle_statusbar_action)

        view_menu.addSeparator()

        # Zoom submenu
        zoom_menu = view_menu.addMenu("&Zoom")

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.setStatusTip("Zoom in on the diagram")
        zoom_in_action.triggered.connect(self.on_zoom_in)
        zoom_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.setStatusTip("Zoom out on the diagram")
        zoom_out_action.triggered.connect(self.on_zoom_out)
        zoom_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("&Reset Zoom", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.setStatusTip("Reset zoom to default")
        zoom_reset_action.triggered.connect(self.on_zoom_reset)
        zoom_menu.addAction(zoom_reset_action)

        zoom_fit_action = QAction("&Fit to View", self)
        zoom_fit_action.setShortcut("Ctrl+9")
        zoom_fit_action.setStatusTip("Fit diagram to view")
        zoom_fit_action.triggered.connect(self.on_fit_to_view)
        zoom_menu.addAction(zoom_fit_action)

        view_menu.addSeparator()

        # Tab navigation
        nodes_tab_action = QAction("Go to &Nodes Tab", self)
        nodes_tab_action.setShortcut("Ctrl+1")
        nodes_tab_action.setStatusTip("Switch to Nodes tab")
        nodes_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(nodes_tab_action)

        floats_tab_action = QAction("Go to &Float Messages Tab", self)
        floats_tab_action.setShortcut("Ctrl+2")
        floats_tab_action.setStatusTip("Switch to Float Messages tab")
        floats_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(floats_tab_action)

        skill_tab_action = QAction("Go to &Skill Checks Tab", self)
        skill_tab_action.setShortcut("Ctrl+3")
        skill_tab_action.setStatusTip("Switch to Skill Checks tab")
        skill_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(skill_tab_action)

        scripts_tab_action = QAction("Go to Scri&pts Tab", self)
        scripts_tab_action.setShortcut("Ctrl+4")
        scripts_tab_action.setStatusTip("Switch to Scripts tab")
        scripts_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction(scripts_tab_action)

        diagram_tab_action = QAction("Go to &Diagram Tab", self)
        diagram_tab_action.setShortcut("Ctrl+5")
        diagram_tab_action.setStatusTip("Switch to Diagram tab")
        diagram_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        view_menu.addAction(diagram_tab_action)

        view_menu.addSeparator()

        # Fullscreen
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.setStatusTip("Toggle fullscreen mode")
        fullscreen_action.triggered.connect(self.on_toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # ==========================================
        # DIALOGUE MENU
        # ==========================================
        dialogue_menu = menubar.addMenu("&Dialogue")

        # Node operations
        add_node_action = QAction("&Add Node", self)
        add_node_action.setShortcut("Ctrl+Shift+A")
        add_node_action.setStatusTip("Add a new dialogue node")
        add_node_action.triggered.connect(self.on_add_node)
        dialogue_menu.addAction(add_node_action)

        delete_node_action = QAction("&Delete Node", self)
        delete_node_action.setShortcut("Ctrl+Shift+D")
        delete_node_action.setStatusTip("Delete the selected node")
        delete_node_action.triggered.connect(self.on_delete_node)
        dialogue_menu.addAction(delete_node_action)

        dialogue_menu.addSeparator()

        # Option operations
        add_option_action = QAction("Add &Option", self)
        add_option_action.setShortcut("Ctrl+Shift+O")
        add_option_action.setStatusTip("Add a new player option to current node")
        add_option_action.triggered.connect(self.on_add_option)
        dialogue_menu.addAction(add_option_action)

        delete_option_action = QAction("Delete O&ption", self)
        delete_option_action.setShortcut("Ctrl+Shift+X")
        delete_option_action.setStatusTip("Delete selected option")
        delete_option_action.triggered.connect(self.on_delete_option)
        dialogue_menu.addAction(delete_option_action)

        dialogue_menu.addSeparator()

        # Node navigation
        go_to_node_action = QAction("&Go to Node...", self)
        go_to_node_action.setShortcut("Ctrl+G")
        go_to_node_action.setStatusTip("Navigate to a specific node")
        go_to_node_action.triggered.connect(self.on_go_to_node)
        dialogue_menu.addAction(go_to_node_action)

        next_node_action = QAction("Go to &Next Node", self)
        next_node_action.setShortcut("Ctrl+Shift+Right")
        next_node_action.setStatusTip("Navigate to next node")
        next_node_action.triggered.connect(self.on_next_node)
        dialogue_menu.addAction(next_node_action)

        prev_node_action = QAction("Go to &Previous Node", self)
        prev_node_action.setShortcut("Ctrl+Shift+Left")
        prev_node_action.setStatusTip("Navigate to previous node")
        prev_node_action.triggered.connect(self.on_previous_node)
        dialogue_menu.addAction(prev_node_action)

        dialogue_menu.addSeparator()

        # Validation
        validate_action = QAction("&Validate Dialogue", self)
        validate_action.setShortcut("Ctrl+Shift+V")
        validate_action.setStatusTip("Validate the current dialogue for errors")
        validate_action.triggered.connect(self.on_validate_dialogue)
        dialogue_menu.addAction(validate_action)

        # ==========================================
        # TOOLS MENU
        # ==========================================
        tools_menu = menubar.addMenu("&Tools")

        # Plugin Manager
        plugin_manager_action = QAction("&Plugin Manager", self)
        plugin_manager_action.setStatusTip("Manage plugins and extensions")
        plugin_manager_action.triggered.connect(self.on_plugin_manager)
        tools_menu.addAction(plugin_manager_action)

        # Plugin Designer
        plugin_designer_action = QAction("Plugin &Designer", self)
        plugin_designer_action.setStatusTip("Visually design new plugins")
        plugin_designer_action.triggered.connect(self.on_plugin_designer)
        tools_menu.addAction(plugin_designer_action)

        tools_menu.addSeparator()

        # Script Compiler configuration
        script_compiler_action = QAction("Configure Script &Compiler", self)
        script_compiler_action.setToolTip("Configure the path to the SSL script compiler (sslc.exe)")
        script_compiler_action.setStatusTip("Configure the SSL compiler path")
        script_compiler_action.triggered.connect(self.on_configure_script_compiler)
        tools_menu.addAction(script_compiler_action)

        tools_menu.addSeparator()

        # Compile script
        compile_action = QAction("&Compile Script", self)
        compile_action.setShortcut("F7")
        compile_action.setStatusTip("Compile the SSL script")
        compile_action.triggered.connect(self.on_compile_script)
        tools_menu.addAction(compile_action)

        # Test Dialogue
        test_action = QAction("&Test Dialogue", self)
        test_action.setShortcut("Ctrl+T")
        test_action.setStatusTip("Run dialogue testing")
        test_action.triggered.connect(self.on_test_dialogue)
        tools_menu.addAction(test_action)

        tools_menu.addSeparator()

        # Settings
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Configure application settings")
        settings_action.triggered.connect(self.on_settings)
        tools_menu.addAction(settings_action)

        # ==========================================
        # HELP MENU
        # ==========================================
        help_menu = menubar.addMenu("&Help")

        # Documentation
        docs_action = QAction("&Documentation", self)
        docs_action.setShortcut("F1")
        docs_action.setStatusTip("View application documentation")
        docs_action.triggered.connect(self.on_documentation)
        help_menu.addAction(docs_action)

        # Keyboard shortcuts
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("Ctrl+/")
        shortcuts_action.setStatusTip("View keyboard shortcuts")
        shortcuts_action.triggered.connect(self.on_keyboard_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        # Check for updates
        updates_action = QAction("Check for &Updates", self)
        updates_action.setStatusTip("Check for application updates")
        updates_action.triggered.connect(self.on_check_updates)
        help_menu.addAction(updates_action)

        help_menu.addSeparator()

        # About
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Fallout Dialogue Creator")
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

        # Populate float nodes from the dialogue
        for float_node in dialogue.floatnodes:
            # Show node name and message count
            message_count = len(float_node.messages)
            item_text = f"{float_node.nodename} ({message_count} messages)"
            self.float_list.addItem(item_text)

    def populate_skill_list(self):
        """Populate the skill checks list"""
        self.skill_list.clear()

        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return

        # Collect all skill checks from all dialogue nodes
        for node in dialogue.nodes:
            for skill_check in node.skillchecks:
                # Show node name and skill info
                skill_name = skill_check.get_skill_name()
                item_text = f"{node.nodename}: {skill_name} (DC {skill_check.required_value})"
                self.skill_list.addItem(item_text)

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
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit, QCheckBox, QSpinBox
        from ui.fallout_widgets import FalloutButton, FalloutDialogFrame
        
        colors = FalloutColors()

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
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors.DARK_SLATE};
            }}
            QLabel {{
                color: {colors.TEXT_NORMAL};
                font-family: Consolas;
                font-size: 10pt;
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(8)

        # Header
        header = QLabel("EDIT PLAYER OPTION")
        header.setStyleSheet(f"""
            QLabel {{
                color: {colors.FALLOUT_YELLOW};
                font-family: Consolas;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px;
                border-bottom: 2px solid {colors.RUST_ORANGE};
            }}
        """)
        layout.addWidget(header)

        # Option text
        text_layout = QHBoxLayout()
        text_label = QLabel("Option Text:")
        text_label.setStyleSheet(f"color: {colors.FALLOUT_YELLOW};")
        text_layout.addWidget(text_label)
        self.option_text_edit = QLineEdit(option.optiontext)
        text_layout.addWidget(self.option_text_edit)
        layout.addLayout(text_layout)

        # Node link
        link_layout = QHBoxLayout()
        link_label = QLabel("Link to Node:")
        link_label.setStyleSheet(f"color: {colors.FALLOUT_YELLOW};")
        link_layout.addWidget(link_label)
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
        reaction_label = QLabel("Reaction:")
        reaction_label.setStyleSheet(f"color: {colors.FALLOUT_YELLOW};")
        reaction_layout.addWidget(reaction_label)
        self.reaction_combo = QComboBox()
        from models.dialogue import Reaction
        self.reaction_combo.addItems([r.name for r in Reaction])
        self.reaction_combo.setCurrentIndex(option.reaction.value)
        reaction_layout.addWidget(self.reaction_combo)
        layout.addLayout(reaction_layout)

        # ==============================================
        # Skill Check Section
        # ==============================================
        skill_check_group = QGroupBox("Skill Check (Optional)")
        skill_check_layout = QVBoxLayout(skill_check_group)
        
        # Enable skill check checkbox
        self.skill_check_enabled = QCheckBox("Enable Skill Check")
        self.skill_check_enabled.setStyleSheet(f"color: {colors.FALLOUT_YELLOW};")
        from models.dialogue import SkillCheck, Skill
        has_skill_check = option.has_skill_check and option.skill_check is not None
        self.skill_check_enabled.setChecked(has_skill_check)
        skill_check_layout.addWidget(self.skill_check_enabled)
        
        # Skill check details (inside a frame that can be enabled/disabled)
        skill_details_layout = QVBoxLayout()
        
        # Skill selection
        skill_row = QHBoxLayout()
        skill_row.addWidget(QLabel("Skill:"))
        self.skill_combo = QComboBox()
        # Add all Fallout skills
        skill_names = [Skill.get_name(i) for i in range(20)]
        self.skill_combo.addItems(skill_names)
        
        # Set current skill if exists
        if has_skill_check:
            skill_val = option.skill_check.check_what
            if isinstance(skill_val, Skill):
                self.skill_combo.setCurrentIndex(skill_val.value)
            else:
                self.skill_combo.setCurrentIndex(skill_val)
        else:
            self.skill_combo.setCurrentIndex(Skill.SPEECH.value)
        
        skill_row.addWidget(self.skill_combo)
        skill_details_layout.addLayout(skill_row)
        
        # Required value
        value_row = QHBoxLayout()
        value_row.addWidget(QLabel("Required Value:"))
        self.skill_value_spin = QSpinBox()
        self.skill_value_spin.setRange(0, 300)
        self.skill_value_spin.setValue(option.skill_check.required_value if has_skill_check else 50)
        value_row.addWidget(self.skill_value_spin)
        skill_details_layout.addLayout(value_row)
        
        # Modifier
        modifier_row = QHBoxLayout()
        modifier_row.addWidget(QLabel("Modifier:"))
        self.skill_modifier_spin = QSpinBox()
        self.skill_modifier_spin.setRange(-100, 100)
        self.skill_modifier_spin.setValue(option.skill_check.modifier if has_skill_check else 0)
        modifier_row.addWidget(self.skill_modifier_spin)
        skill_details_layout.addLayout(modifier_row)
        
        # Success/Failure nodes
        success_row = QHBoxLayout()
        success_row.addWidget(QLabel("Success Node:"))
        self.success_node_combo = QComboBox()
        self.success_node_combo.addItems(["(none)"] + node_names)
        if has_skill_check and option.skill_check.successnode:
            idx = self.dialog_manager.find_node_by_name(option.skill_check.successnode)
            if idx >= 0:
                self.success_node_combo.setCurrentIndex(idx + 1)
        success_row.addWidget(self.success_node_combo)
        skill_details_layout.addLayout(success_row)
        
        failure_row = QHBoxLayout()
        failure_row.addWidget(QLabel("Failure Node:"))
        self.failure_node_combo = QComboBox()
        self.failure_node_combo.addItems(["(none)"] + node_names)
        if has_skill_check and option.skill_check.failurenode:
            idx = self.dialog_manager.find_node_by_name(option.skill_check.failurenode)
            if idx >= 0:
                self.failure_node_combo.setCurrentIndex(idx + 1)
        failure_row.addWidget(self.failure_node_combo)
        skill_details_layout.addLayout(failure_row)
        
        # Success/Failure response text
        success_text_row = QHBoxLayout()
        success_text_row.addWidget(QLabel("Success Response:"))
        self.success_response_edit = QLineEdit(option.success_response if has_skill_check else "")
        success_text_row.addWidget(self.success_response_edit)
        skill_details_layout.addLayout(success_text_row)
        
        failure_text_row = QHBoxLayout()
        failure_text_row.addWidget(QLabel("Failure Response:"))
        self.failure_response_edit = QLineEdit(option.failure_response if has_skill_check else "")
        failure_text_row.addWidget(self.failure_response_edit)
        skill_details_layout.addLayout(failure_text_row)
        
        skill_check_layout.addWidget(skill_details_widget)
        layout.addWidget(skill_check_group)
        
        # Enable/disable skill check details based on checkbox
        skill_details_widget = QWidget()
        skill_details_widget.setLayout(skill_details_layout)
        skill_details_widget.setEnabled(has_skill_check)
        
        # Connect checkbox to enable/disable
        self.skill_check_enabled.toggled.connect(skill_details_widget.setEnabled)

        # Notes
        notes_layout = QVBoxLayout()
        notes_label = QLabel("Notes:")
        notes_label.setStyleSheet(f"color: {colors.FALLOUT_YELLOW};")
        notes_layout.addWidget(notes_label)
        self.option_notes_edit = QTextEdit(option.notes)
        self.option_notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.option_notes_edit)
        layout.addLayout(notes_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = FalloutButton("Save", "rust")
        save_button.clicked.connect(lambda: self.save_option(dialog, node_index, option_index))
        cancel_button = FalloutButton("Cancel", "standard")
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
        from models.dialogue import Reaction, SkillCheck, Skill
        option.reaction = Reaction(self.reaction_combo.currentIndex())
        option.notes = self.option_notes_edit.toPlainText()
        
        # Save skill check data
        if self.skill_check_enabled.isChecked():
            option.has_skill_check = True
            
            # Create skill check if it doesn't exist
            if option.skill_check is None:
                option.skill_check = SkillCheck()
            
            # Update skill check values
            option.skill_check.check_what = Skill(self.skill_combo.currentIndex())
            option.skill_check.required_value = self.skill_value_spin.value()
            option.skill_check.modifier = self.skill_modifier_spin.value()
            
            # Get success/failure nodes
            success_idx = self.success_node_combo.currentIndex()
            option.skill_check.successnode = self.success_node_combo.currentText() if success_idx > 0 else ""
            
            failure_idx = self.failure_node_combo.currentIndex()
            option.skill_check.failurenode = self.failure_node_combo.currentText() if failure_idx > 0 else ""
            
            # Save response texts
            option.success_response = self.success_response_edit.text()
            option.failure_response = self.failure_response_edit.text()
        else:
            option.has_skill_check = False
            option.skill_check = None

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

    @pyqtSlot()
    def on_plugin_designer(self):
        """Show plugin designer window"""
        self.show_plugin_designer()

    def show_plugin_designer(self):
        """Display the plugin designer window"""
        from ui.plugin_designer import PluginDesignerWindow
        
        designer = PluginDesignerWindow(self)
        designer.exec()

    @pyqtSlot()
    def on_configure_script_compiler(self):
        """Show script compiler configuration dialog"""
        self.show_script_compiler_config()

    def show_script_compiler_config(self):
        """Display the script compiler configuration dialog"""
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
            QPushButton, QFileDialog, QMessageBox, QGroupBox
        )
        from pathlib import Path
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Script Compiler")
        dialog.setModal(True)
        dialog.resize(600, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Description
        desc_label = QLabel(
            "Configure the path to the SSL script compiler (sslc.exe). "
            "This compiler is used to compile Fallout scripting language files."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Path input group
        path_group = QGroupBox("Compiler Path")
        path_layout = QVBoxLayout(path_group)
        
        # Current path display
        current_path_label = QLabel("Current path:")
        path_layout.addWidget(current_path_label)
        
        path_hbox = QHBoxLayout()
        self.compiler_path_edit = QLineEdit()
        self.compiler_path_edit.setPlaceholderText("Select a compiler executable...")
        
        # Load current value
        current_path = self.settings.get('script_compiler_path', '')
        if current_path:
            self.compiler_path_edit.setText(current_path)
        else:
            # Show default path as hint
            from core.script_compiler import DEFAULT_COMPILER_PATH
            if DEFAULT_COMPILER_PATH.exists():
                self.compiler_path_edit.setText(str(DEFAULT_COMPILER_PATH))
                self.compiler_path_edit.setPlaceholderText("Using default path")
        
        path_hbox.addWidget(self.compiler_path_edit)
        
        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.setToolTip("Browse for sslc.exe")
        browse_btn.clicked.connect(lambda: self._browse_compiler_path(dialog))
        path_hbox.addWidget(browse_btn)
        
        path_layout.addLayout(path_hbox)
        
        # Validation message
        self.compiler_validation_label = QLabel()
        self.compiler_validation_label.setStyleSheet("color: red;")
        path_layout.addWidget(self.compiler_validation_label)
        
        # Validate on text change
        self.compiler_path_edit.textChanged.connect(
            lambda: self._validate_compiler_path_input(self.compiler_validation_label)
        )
        
        layout.addWidget(path_group)
        
        # Buttons
        button_box = QHBoxLayout()
        button_box.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(lambda: self._save_compiler_path(dialog))
        button_box.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_box.addWidget(cancel_btn)
        
        layout.addLayout(button_box)
        
        # Initial validation
        self._validate_compiler_path_input(self.compiler_validation_label)
        
        dialog.exec()

    def _browse_compiler_path(self, parent_dialog: QDialog):
        """Open file dialog to browse for compiler executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent_dialog,
            "Select Script Compiler",
            "",
            "Executables (*.exe *.bat *.cmd *.com);;All Files (*)"
        )
        
        if file_path:
            self.compiler_path_edit.setText(file_path)

    def _validate_compiler_path_input(self, validation_label: QLabel):
        """Validate the compiler path input and show error message"""
        path_text = self.compiler_path_edit.text().strip()
        
        if not path_text:
            validation_label.setText("")
            validation_label.setStyleSheet("color: gray;")
            validation_label.setText("Path not set - will use default if available")
            return
        
        is_valid, error_msg = self.settings.validate_script_compiler_path(path_text)
        
        if is_valid:
            validation_label.setText("✓ Valid compiler path")
            validation_label.setStyleSheet("color: green;")
        else:
            validation_label.setText(f"✗ {error_msg}")
            validation_label.setStyleSheet("color: red;")

    def _save_compiler_path(self, dialog: QDialog):
        """Save the compiler path setting"""
        path_text = self.compiler_path_edit.text().strip()
        
        # Validate if path is not empty
        if path_text:
            is_valid, error_msg = self.settings.validate_script_compiler_path(path_text)
            if not is_valid:
                QMessageBox.warning(
                    dialog,
                    "Invalid Path",
                    f"The specified path is invalid:\n{error_msg}\n\n"
                    "Please select a valid compiler executable."
                )
                return
        
        # Save the path (empty string means use default)
        self.settings.set('script_compiler_path', path_text)
        
        QMessageBox.information(
            dialog,
            "Settings Saved",
            "Script compiler path has been configured.\n"
            "The compiler will be used when compiling scripts."
        )
        
        dialog.accept()

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

    # ==============================================
    # FILE MENU HANDLERS
    # ==============================================

    def _populate_recent_files_menu(self):
        """Populate the recent files submenu"""
        self.recent_files_menu.clear()
        
        recent_files = self.settings.get('recent_files', [])
        if not recent_files:
            empty_action = QAction("No recent files", self)
            empty_action.setEnabled(False)
            self.recent_files_menu.addAction(empty_action)
            return
        
        for file_path in recent_files[:10]:  # Limit to 10 recent files
            from pathlib import Path
            file_name = Path(file_path).name
            action = QAction(file_name, self)
            action.setData(file_path)
            action.triggered.connect(lambda checked, path=file_path: self._open_recent_file(path))
            self.recent_files_menu.addAction(action)
        
        self.recent_files_menu.addSeparator()
        
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_files_menu.addAction(clear_action)

    def _open_recent_file(self, file_path: str):
        """Open a recent file"""
        from pathlib import Path
        if self.check_save_changes():
            path = Path(file_path)
            if path.exists():
                self.dialog_manager.load_dialogue(path)
            else:
                QMessageBox.warning(self, "File Not Found", f"The file {file_path} no longer exists.")
                self._remove_from_recent_files(file_path)

    def _remove_from_recent_files(self, file_path: str):
        """Remove a file from recent files list"""
        recent_files = self.settings.get('recent_files', [])
        if file_path in recent_files:
            recent_files.remove(file_path)
            self.settings.set('recent_files', recent_files)
            self._populate_recent_files_menu()

    def _clear_recent_files(self):
        """Clear all recent files"""
        self.settings.set('recent_files', [])
        self._populate_recent_files_menu()

    def on_import_ddf(self):
        """Handle import from DDF action - NOT YET IMPLEMENTED"""
        # DDF import requires a parser that isn't available yet
        QMessageBox.information(self, "Import DDF", 
            "DDF import is not yet implemented.\n\n"
            "This feature will allow importing dialogues from DDF format.")

    def on_import_msg(self):
        """Handle import from MSG action - NOT YET IMPLEMENTED"""
        # MSG import requires a parser that isn't available yet
        QMessageBox.information(self, "Import MSG", 
            "MSG import is not yet implemented.\n\n"
            "This feature will allow importing messages from MSG format.")

    def on_export_ssl(self):
        """Handle export to SSL action"""
        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            QMessageBox.warning(self, "No Dialogue", "No dialogue is currently loaded.")
            return
        
        default_name = dialogue.name + ".ssl" if dialogue.name else "dialogue.ssl"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to SSL", str(self.settings.get_dialogue_path() / default_name),
            "SSL Files (*.ssl);;All Files (*)"
        )
        if file_path:
            try:
                from pathlib import Path
                from core.ssl_exporter import SSLExporter
                
                exporter = SSLExporter()
                ssl_output = exporter.export(dialogue)
                
                output_path = Path(file_path)
                output_path.write_text(ssl_output, encoding='utf-8')
                
                self.status_bar.showMessage(f"Exported to SSL: {file_path}")
                QMessageBox.information(self, "Export Successful", 
                    f"Dialogue exported to SSL successfully!\n\nFile: {file_path}")
            except Exception as e:
                logger.error(f"SSL export failed: {e}")
                QMessageBox.critical(self, "Export Failed", 
                    f"Failed to export dialogue to SSL:\n\n{str(e)}")

    def on_export_msg(self):
        """Handle export to MSG action"""
        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            QMessageBox.warning(self, "No Dialogue", "No dialogue is currently loaded.")
            return
        
        default_name = dialogue.name + ".msg" if dialogue.name else "dialogue.msg"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to MSG", str(self.settings.get_dialogue_path() / default_name),
            "MSG Files (*.msg);;All Files (*)"
        )
        if file_path:
            try:
                from pathlib import Path
                from core.msg_exporter import MSGExporter
                
                exporter = MSGExporter()
                msg_output = exporter.export(dialogue)
                
                output_path = Path(file_path)
                output_path.write_text(msg_output, encoding='utf-8')
                
                self.status_bar.showMessage(f"Exported to MSG: {file_path}")
                QMessageBox.information(self, "Export Successful", 
                    f"Dialogue exported to MSG successfully!\n\nFile: {file_path}")
            except Exception as e:
                logger.error(f"MSG export failed: {e}")
                QMessageBox.critical(self, "Export Failed", 
                    f"Failed to export dialogue to MSG:\n\n{str(e)}")

    def on_export_ddf(self):
        """Handle export to DDF action"""
        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            QMessageBox.warning(self, "No Dialogue", "No dialogue is currently loaded.")
            return
        
        default_name = dialogue.name + ".ddf" if dialogue.name else "dialogue.ddf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to DDF", str(self.settings.get_dialogue_path() / default_name),
            "DDF Files (*.ddf);;All Files (*)"
        )
        if file_path:
            try:
                from pathlib import Path
                from core.ddf_output import DDFExporter
                
                exporter = DDFExporter()
                ddf_lines = exporter.export_to_ddf(dialogue)
                
                output_path = Path(file_path)
                output_path.write_text('\n'.join(ddf_lines), encoding='utf-8')
                
                self.status_bar.showMessage(f"Exported to DDF: {file_path}")
                QMessageBox.information(self, "Export Successful", 
                    f"Dialogue exported to DDF successfully!\n\nFile: {file_path}")
            except Exception as e:
                logger.error(f"DDF export failed: {e}")
                QMessageBox.critical(self, "Export Failed", 
                    f"Failed to export dialogue to DDF:\n\n{str(e)}")

    # ==============================================
    # EDIT MENU HANDLERS
    # ==============================================

    def on_undo(self):
        """Handle undo action"""
        # Try to get the focused widget and perform undo
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, 'undo'):
            focused_widget.undo()
        else:
            self.status_bar.showMessage("Undo not available")

    def on_redo(self):
        """Handle redo action"""
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, 'redo'):
            focused_widget.redo()
        else:
            self.status_bar.showMessage("Redo not available")

    def on_cut(self):
        """Handle cut action"""
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, 'cut'):
            focused_widget.cut()
        else:
            self.status_bar.showMessage("Cut not available")

    def on_copy(self):
        """Handle copy action"""
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, 'copy'):
            focused_widget.copy()
        else:
            # If nothing is focused or focused widget doesn't support copy,
            # try to copy the currently selected node
            current_item = self.nodes_tree.currentItem()
            if current_item:
                clipboard = QApplication.clipboard()
                clipboard.setText(current_item.text(0))
                self.status_bar.showMessage("Copied node name to clipboard")

    def on_paste(self):
        """Handle paste action"""
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, 'paste'):
            focused_widget.paste()
        else:
            self.status_bar.showMessage("Paste not available")

    def on_delete(self):
        """Handle delete action - delegates to node or option deletion"""
        # Check if we have a selected option
        selected_options = self.options_list.selectedItems()
        if selected_options:
            self.on_delete_option()
            return
        
        # Check if we have a selected node
        current_item = self.nodes_tree.currentItem()
        if current_item:
            self.on_delete_node()
            return
        
        self.status_bar.showMessage("Nothing selected to delete")

    def on_select_all(self):
        """Handle select all action"""
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, 'selectAll'):
            focused_widget.selectAll()
        else:
            self.status_bar.showMessage("Select all not available")

    def on_find(self):
        """Handle find text action"""
        self.show_find_dialog()

    def on_find_next(self):
        """Handle find next action"""
        if hasattr(self, 'last_search_text') and self.last_search_text:
            self._perform_find(self.last_search_text)
        else:
            self.on_find()

    def on_find_node(self):
        """Handle find node action"""
        self.show_find_node_dialog()

    def show_find_dialog(self):
        """Show find text dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Find Text")
        dialog.setModal(True)
        dialog.resize(400, 150)
        
        layout = QVBoxLayout(dialog)
        
        # Search text
        label = QLabel("Search for:")
        layout.addWidget(label)
        
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Enter text to search...")
        layout.addWidget(search_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        find_button = QPushButton("Find")
        find_button.setDefault(True)
        button_layout.addWidget(find_button)
        
        close_button = QPushButton("Close")
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        def do_find():
            text = search_edit.text()
            if text:
                self.last_search_text = text
                self._perform_find(text)
        
        find_button.clicked.connect(do_find)
        search_edit.returnPressed.connect(do_find)
        close_button.clicked.connect(dialog.accept)
        
        dialog.exec()

    def _perform_find(self, text: str):
        """Perform the actual find operation"""
        # Search in node text
        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            return
        
        found = False
        for i, node in enumerate(dialogue.nodes):
            if text.lower() in node.npctext.lower():
                # Select this node
                self.nodes_tree.setCurrentItem(self.nodes_tree.topLevelItem(i))
                self.display_node(i)
                self.status_bar.showMessage(f"Found in node: {node.nodename}")
                found = True
                break
            # Also search in options
            for opt in node.options:
                if text.lower() in opt.optiontext.lower():
                    self.nodes_tree.setCurrentItem(self.nodes_tree.topLevelItem(i))
                    self.display_node(i)
                    self.status_bar.showMessage(f"Found in option of node: {node.nodename}")
                    found = True
                    break
            if found:
                break
        
        if not found:
            self.status_bar.showMessage(f"Text '{text}' not found")

    def show_find_node_dialog(self):
        """Show find node dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
        
        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            QMessageBox.warning(self, "No Dialogue", "No dialogue is currently loaded.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Find Node")
        dialog.setModal(True)
        dialog.resize(350, 120)
        
        layout = QVBoxLayout(dialog)
        
        # Node selection
        label = QLabel("Select node:")
        layout.addWidget(label)
        
        node_combo = QComboBox()
        node_names = self.dialog_manager.get_node_names()
        node_combo.addItems(node_names)
        layout.addWidget(node_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        go_button = QPushButton("Go To")
        go_button.setDefault(True)
        button_layout.addWidget(go_button)
        
        close_button = QPushButton("Cancel")
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        def go_to():
            node_name = node_combo.currentText()
            node_index = self.dialog_manager.find_node_by_name(node_name)
            if node_index >= 0:
                self.nodes_tree.setCurrentItem(self.nodes_tree.topLevelItem(node_index))
                self.display_node(node_index)
            dialog.accept()
        
        go_button.clicked.connect(go_to)
        close_button.clicked.connect(dialog.accept)
        
        dialog.exec()

    # ==============================================
    # VIEW MENU HANDLERS
    # ==============================================

    def on_toggle_left_panel(self):
        """Toggle left panel visibility"""
        # Find the splitter that contains left widget
        # For simplicity, we'll use the tab widget visibility
        if hasattr(self, 'tab_widget'):
            visible = self.toggle_left_panel_action.isChecked()
            self.tab_widget.setVisible(visible)
            self.status_bar.showMessage(f"Left panel {'shown' if visible else 'hidden'}")

    def on_toggle_right_panel(self):
        """Toggle right panel visibility - NOT YET IMPLEMENTED"""
        # TODO: Implement right panel toggle - requires identifying the right panel widget
        visible = self.toggle_right_panel_action.isChecked()
        self.status_bar.showMessage(f"Right panel toggle not yet implemented ({'shown' if visible else 'hidden'})")

    def on_toggle_toolbar(self):
        """Toggle toolbar visibility"""
        toolbar = self.findChildren(__import__('PyQt6.QtWidgets', fromlist=['QToolBar']).QToolBar)
        if toolbar:
            visible = self.toggle_toolbar_action.isChecked()
            toolbar[0].setVisible(visible)
            self.status_bar.showMessage(f"Toolbar {'shown' if visible else 'hidden'}")

    def on_toggle_statusbar(self):
        """Toggle status bar visibility"""
        visible = self.toggle_statusbar_action.isChecked()
        self.statusBar().setVisible(visible)
        self.status_bar.showMessage(f"Status bar {'shown' if visible else 'hidden'}")

    def on_zoom_in(self):
        """Handle zoom in action"""
        self.diagram_widget.zoom_in()
        self.status_bar.showMessage("Zoomed in")

    def on_zoom_out(self):
        """Handle zoom out action"""
        self.diagram_widget.zoom_out()
        self.status_bar.showMessage("Zoomed out")

    def on_zoom_reset(self):
        """Handle zoom reset action"""
        self.diagram_widget.reset_zoom()
        self.status_bar.showMessage("Zoom reset to 100%")

    def on_fit_to_view(self):
        """Handle fit to view action"""
        self.diagram_widget.fit_to_view()
        self.status_bar.showMessage("Fitted to view")

    def on_toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ==============================================
    # DIALOGUE MENU HANDLERS
    # ==============================================

    def on_go_to_node(self):
        """Handle go to node action"""
        self.show_find_node_dialog()

    def on_next_node(self):
        """Navigate to next node"""
        current_item = self.nodes_tree.currentItem()
        if current_item:
            current_index = self.nodes_tree.indexOfTopLevelItem(current_item)
            if current_index < self.nodes_tree.topLevelItemCount() - 1:
                self.nodes_tree.setCurrentItem(self.nodes_tree.topLevelItem(current_index + 1))
                self.display_node(current_index + 1)
        else:
            # Go to first node if none selected
            if self.nodes_tree.topLevelItemCount() > 0:
                self.nodes_tree.setCurrentItem(self.nodes_tree.topLevelItem(0))
                self.display_node(0)

    def on_previous_node(self):
        """Navigate to previous node"""
        current_item = self.nodes_tree.currentItem()
        if current_item:
            current_index = self.nodes_tree.indexOfTopLevelItem(current_item)
            if current_index > 0:
                self.nodes_tree.setCurrentItem(self.nodes_tree.topLevelItem(current_index - 1))
                self.display_node(current_index - 1)

    def on_validate_dialogue(self):
        """Handle validate dialogue action"""
        dialogue = self.dialog_manager.get_current_dialogue()
        if not dialogue:
            QMessageBox.warning(self, "No Dialogue", "No dialogue is currently loaded.")
            return
        
        # Run validation
        issues = []
        
        # Check for nodes without options
        for i, node in enumerate(dialogue.nodes):
            if not node.options:
                issues.append(f"Node '{node.nodename}' has no player options")
        
        # Check for orphaned options (no link)
        for i, node in enumerate(dialogue.nodes):
            for opt in node.options:
                if not opt.nodelink:
                    issues.append(f"Node '{node.nodename}' has an option with no target node")
        
        # Check for duplicate node names
        node_names = [n.nodename for n in dialogue.nodes]
        duplicates = [name for name in node_names if node_names.count(name) > 1]
        if duplicates:
            issues.append(f"Duplicate node names found: {', '.join(set(duplicates))}")
        
        # Show results
        if issues:
            result_text = "VALIDATION ISSUES FOUND:\n\n" + "\n".join([f"• {issue}" for issue in issues])
            QMessageBox.warning(self, "Validation Results", result_text)
        else:
            QMessageBox.information(self, "Validation Results", 
                "✓ Dialogue validation passed!\n\nNo issues found.")

    # ==============================================
    # TOOLS MENU HANDLERS
    # ==============================================

    def on_compile_script(self):
        """Handle compile script action - NOT YET IMPLEMENTED"""
        # Script compilation uses the core/script_compiler.py module but
        # requires the external sslc.exe compiler to be available
        QMessageBox.information(self, "Compile Script", 
            "Script compilation requires the SSL compiler (sslc.exe)\n"
            "to be configured in Settings.\n\n"
            "Use 'Test Dialogue' to validate dialogue structure.")

    def on_settings(self):
        """Handle settings action"""
        self.show_settings_dialog()

    def show_settings_dialog(self):
        """Show settings configuration dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QGroupBox, QComboBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        font_group = QGroupBox("Font Settings")
        font_layout = QVBoxLayout(font_group)
        
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(QLabel("Font Family:"))
        font_family_combo = QComboBox()
        font_family_combo.addItems(["Consolas", "Courier New", "Monaco", "Lucida Console"])
        current_family = self.settings.get('font_family', 'Consolas')
        font_family_combo.setCurrentText(current_family)
        font_family_layout.addWidget(font_family_combo)
        font_layout.addLayout(font_family_layout)
        
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Font Size:"))
        font_size_combo = QComboBox()
        font_size_combo.addItems([str(i) for i in range(8, 20)])
        current_size = self.settings.get('font_size', 10)
        font_size_combo.setCurrentText(str(current_size))
        font_size_layout.addWidget(font_size_combo)
        font_layout.addLayout(font_size_layout)
        
        general_layout.addWidget(font_group)
        general_layout.addStretch()
        
        tabs.addTab(general_tab, "General")
        
        # Paths tab
        paths_tab = QWidget()
        paths_layout = QVBoxLayout(paths_tab)
        
        compiler_group = QGroupBox("Script Compiler")
        compiler_layout = QVBoxLayout(compiler_group)
        
        compiler_path_layout = QHBoxLayout()
        compiler_path_layout.addWidget(QLabel("Compiler Path:"))
        compiler_path_edit = QLineEdit(self.settings.get('script_compiler_path', ''))
        compiler_path_edit.setPlaceholderText("Leave empty for default")
        compiler_path_layout.addWidget(compiler_path_edit)
        
        compiler_browse_btn = QPushButton("Browse...")
        compiler_path_layout.addWidget(compiler_browse_btn)
        
        compiler_layout.addLayout(compiler_path_layout)
        paths_layout.addWidget(compiler_group)
        paths_layout.addStretch()
        
        tabs.addTab(paths_tab, "Paths")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        def save_settings():
            # Save font settings
            self.settings.set('font_family', font_family_combo.currentText())
            self.settings.set('font_size', int(font_size_combo.currentText()))
            self.settings.set('script_compiler_path', compiler_path_edit.text())
            
            # Apply settings
            self.apply_settings()
            
            QMessageBox.information(dialog, "Settings Saved", "Settings have been saved and applied.")
            dialog.accept()
        
        save_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()

    # ==============================================
    # HELP MENU HANDLERS
    # ==============================================

    def on_documentation(self):
        """Handle documentation action"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Documentation")
        dialog.setModal(True)
        dialog.resize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Documentation browser
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        
        doc_content = """
        <h1>Fallout Dialogue Creator 2.0 - Documentation</h1>
        
        <h2>Overview</h2>
        <p>Fallout Dialogue Creator is a tool for creating and editing dialogue for Fallout 1 and Fallout 2 games.</p>
        
        <h2>Getting Started</h2>
        <ul>
        <li><b>File Menu:</b> Create, open, save, import, and export dialogue files</li>
        <li><b>Edit Menu:</b> Standard editing operations (undo, copy, paste, etc.)</li>
        <li><b>View Menu:</b> Customize the interface view</li>
        <li><b>Dialogue Menu:</b> Node and option management</li>
        <li><b>Tools Menu:</b> Plugin management, script compilation, testing</li>
        <li><b>Help Menu:</b> Documentation and about information</li>
        </ul>
        
        <h2>Keyboard Shortcuts</h2>
        <ul>
        <li><b>Ctrl+N:</b> New dialogue</li>
        <li><b>Ctrl+O:</b> Open dialogue</li>
        <li><b>Ctrl+S:</b> Save dialogue</li>
        <li><b>Ctrl+T:</b> Test dialogue</li>
        <li><b>Ctrl+G:</b> Go to node</li>
        <li><b>F1:</b> Documentation</li>
        <li><b>F7:</b> Compile script</li>
        </ul>
        
        <h2>Dialogue Structure</h2>
        <p>A dialogue consists of nodes, where each node represents an NPC speaking line.
        Each node can have multiple player options that link to other nodes.</p>
        
        <h2>Support</h2>
        <p>For bug reports and feature requests, please visit the project repository.</p>
        """
        
        browser.setHtml(doc_content)
        layout.addWidget(browser)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()

    def on_keyboard_shortcuts(self):
        """Handle keyboard shortcuts action"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.setModal(True)
        dialog.resize(500, 600)
        
        layout = QVBoxLayout(dialog)
        
        browser = QTextBrowser()
        
        shortcuts_content = """
        <h1>Keyboard Shortcuts</h1>
        
        <h2>File Operations</h2>
        <table>
        <tr><td><b>Ctrl+N</b></td><td>New dialogue</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Open dialogue</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save dialogue</td></tr>
        <tr><td><b>Ctrl+Shift+S</b></td><td>Save dialogue as</td></tr>
        </table>
        
        <h2>Edit Operations</h2>
        <table>
        <tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
        <tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
        <tr><td><b>Ctrl+X</b></td><td>Cut</td></tr>
        <tr><td><b>Ctrl+C</b></td><td>Copy</td></tr>
        <tr><td><b>Ctrl+V</b></td><td>Paste</td></tr>
        <tr><td><b>Ctrl+A</b></td><td>Select all</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>Find text</td></tr>
        </table>
        
        <h2>View Operations</h2>
        <table>
        <tr><td><b>Ctrl+1-5</b></td><td>Switch between tabs</td></tr>
        <tr><td><b>Ctrl+0</b></td><td>Reset zoom</td></tr>
        <tr><td><b>Ctrl++</b></td><td>Zoom in</td></tr>
        <tr><td><b>Ctrl+-</b></td><td>Zoom out</td></tr>
        <tr><td><b>F11</b></td><td>Toggle fullscreen</td></tr>
        </table>
        
        <h2>Dialogue Operations</h2>
        <table>
        <tr><td><b>Ctrl+G</b></td><td>Go to node</td></tr>
        <tr><td><b>Ctrl+Shift+A</b></td><td>Add node</td></tr>
        <tr><td><b>Ctrl+Shift+D</b></td><td>Delete node</td></tr>
        <tr><td><b>Ctrl+Shift+O</b></td><td>Add option</td></tr>
        <tr><td><b>Ctrl+Shift+X</b></td><td>Delete option</td></tr>
        <tr><td><b>Ctrl+Shift+V</b></td><td>Validate dialogue</td></tr>
        <tr><td><b>Ctrl+Shift+N</b></td><td>Find node</td></tr>
        </table>
        
        <h2>Tools</h2>
        <table>
        <tr><td><b>Ctrl+T</b></td><td>Test dialogue</td></tr>
        <tr><td><b>F7</b></td><td>Compile script</td></tr>
        <tr><td><b>Ctrl+,</b></td><td>Open settings</td></tr>
        </table>
        
        <h2>Help</h2>
        <table>
        <tr><td><b>F1</b></td><td>Open documentation</td></tr>
        <tr><td><b>Ctrl+/</b></td><td>Show shortcuts</td></tr>
        </table>
        """
        
        browser.setHtml(shortcuts_content)
        layout.addWidget(browser)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()

    def on_check_updates(self):
        """Handle check for updates action"""
        QMessageBox.information(self, "Check for Updates", 
            "You are running Fallout Dialogue Creator 2.0.\n"
            "No automatic update check is configured.\n\n"
            "Visit the project repository for the latest version.")

    def closeEvent(self, event):
        """Handle application close"""
        if not self.check_save_changes():
            event.ignore()
        else:
            event.accept()