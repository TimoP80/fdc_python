"""
Fallout 2 Theme Module
Complete visual redesign to authentically replicate the distinctive rusty, 
post-apocalyptic aesthetic of the classic Fallout 2 interface from 1998.
"""

from PyQt6.QtGui import QColor, QPalette, QFont, QLinearGradient, QConicalGradient
from PyQt6.QtCore import Qt, QSize, QRect, QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsEffect, QGraphicsBlurEffect


# =============================================================================
# FALLOUT 2 COLOR PALETTE
# =============================================================================

class FalloutColors:
    """Authentic Fallout 2 color palette"""
    
    # Primary Colors - Olive Drab Greens
    OLIVE_DRAB = "#6b8e23"
    DARK_OLIVE_GREEN = "#556b2f"
    MUDDY_GREEN = "#4a5d23"
    MILITARY_GREEN = "#3d4f2a"
    FADED_GREEN = "#5c7a3a"
    
    # Secondary Colors - Rust Orange-Browns
    RUST_ORANGE = "#b7410e"
    DARK_RUST = "#8b3a0e"
    BURNISHED_BROWN = "#8b4513"
    RUST_BROWN = "#7c4a1c"
    COPPER_RUST = "#8b5a2b"
    
    # Muted Browns
    MUTED_BROWN = "#5c4033"
    DARK_BROWN = "#3d2b1f"
    EARTH_BROWN = "#4a3728"
    WOOD_BROWN = "#5d4a3a"
    FADED_BROWN = "#6b5b4b"
    
    # Signature Yellow Highlighting
    FALLOUT_YELLOW = "#ffcc00"
    BRIGHT_YELLOW = "#ffdd44"
    WARNING_YELLOW = "#ffbb00"
    GOLD_YELLOW = "#d4a017"
    AMBER = "#ffbf00"
    
    # Terminal Green (Pip-Boy style)
    TERMINAL_GREEN = "#33ff33"
    DIM_GREEN = "#1a8c1a"
    BRIGHT_GREEN = "#66ff66"
    CRT_GREEN = "#00ff00"
    MATRIX_GREEN = "#00cc00"
    
    # Background Colors
    DARK_SLATE = "#1a1a1a"
    CHARCOAL = "#2d2d2d"
    DARK_METAL = "#3a3a3a"
    PIPBOY_SCREEN = "#0d1a0d"
    
    # Panel Colors
    PANEL_BACKGROUND = "#2a2a28"
    PANEL_BORDER = "#5c5c5c"
    PANEL_HIGHLIGHT = "#4a4a48"
    PANEL_SHADOW = "#1a1a1a"
    
    # Text Colors
    TEXT_NORMAL = "#c4b998"
    TEXT_DIM = "#8b8b7a"
    TEXT_BRIGHT = "#e8dca8"
    TEXT_TERMINAL = "#33ff33"
    
    # Status Colors
    STATUS_RED = "#cc3333"
    STATUS_ORANGE = "#cc6633"
    STATUS_YELLOW = "#cccc33"


# =============================================================================
# FALLOUT 2 FONTS
# =============================================================================

class FalloutFonts:
    """Font definitions for Fallout 2 aesthetic"""
    
    # Primary UI Font - bitmap style
    @staticmethod
    def get_ui_font():
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        font.setBold(True)
        return font
    
    # Typewriter Font for dialogs
    @staticmethod
    def get_typewriter_font():
        font = QFont()
        font.setFamily("Courier New")
        font.setPointSize(11)
        font.setBold(False)
        return font
    
    # Terminal Font
    @staticmethod
    def get_terminal_font():
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(12)
        font.setBold(False)
        return font
    
    # Header Font
    @staticmethod
    def get_header_font():
        font = QFont()
        font.setFamily("Impact")
        font.setPointSize(14)
        font.setBold(True)
        return font
    
    # Special Stat Font
    @staticmethod
    def get_stat_font():
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(9)
        font.setBold(True)
        return font


# =============================================================================
# FALLOUT 2 STYLESHEET
# =============================================================================

class FalloutStylesheet:
    """Complete QSS stylesheet for Fallout 2 aesthetic"""
    
    @staticmethod
    def get_main_stylesheet():
        return """
        /* ===================================================================
           FALLOUT 2 MAIN STYLESHEET
           Authentic rusty, post-apocalyptic aesthetic
           =================================================================== */
        
        /* --- Main Window --- */
        QMainWindow {
            background-color: #1a1a1a;
            border: 2px solid #5c5c5c;
        }
        
        QMainWindow::title {
            background-color: #2d2d2d;
            text-align: center;
            padding: 4px;
            border-bottom: 2px solid #5c5c5c;
        }
        
        /* --- Menu Bar --- */
        QMenuBar {
            background-color: #2d2d2d;
            border-bottom: 2px solid #5c5c5c;
            padding: 2px;
        }
        
        QMenuBar::item {
            background-color: #2d2d2d;
            color: #c4b998;
            padding: 6px 12px;
            border: 1px solid transparent;
        }
        
        QMenuBar::item:selected {
            background-color: #556b2f;
            color: #ffcc00;
            border: 1px solid #b7410e;
        }
        
        QMenuBar::item:pressed {
            background-color: #b7410e;
            color: #ffffff;
        }
        
        /* --- Menus --- */
        QMenu {
            background-color: #2a2a28;
            border: 2px solid #5c5c5c;
            padding: 4px;
        }
        
        QMenu::item {
            background-color: transparent;
            color: #c4b998;
            padding: 6px 30px 6px 20px;
            border: 1px solid transparent;
        }
        
        QMenu::item:selected {
            background-color: #556b2f;
            color: #ffcc00;
            border: 1px solid #b7410e;
        }
        
        QMenu::separator {
            height: 2px;
            background-color: #5c5c5c;
            margin: 4px 0px;
        }
        
        QMenu::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #5c5c5c;
        }
        
        /* --- Tool Bar --- */
        QToolBar {
            background-color: #3a3a3a;
            border: 2px solid #5c5c5c;
            padding: 4px;
            spacing: 8px;
        }
        
        QToolBar::separator {
            background-color: #5c5c5c;
            width: 2px;
            margin: 4px;
        }
        
        /* --- Push Buttons --- */
        QPushButton {
            background-color: #4a5d23;
            color: #d4c4a8;
            border: 2px outset #6b8e23;
            border-top-color: #6b8e23;
            border-left-color: #6b8e23;
            border-right-color: #3d4f2a;
            border-bottom-color: #3d4f2a;
            border-radius: 4px;
            padding: 6px 16px;
            font-family: Consolas;
            font-size: 10pt;
            font-weight: bold;
            min-height: 28px;
        }
        
        QPushButton:hover {
            background-color: #556b2f;
            color: #ffcc00;
            border: 2px outset #8fa863;
            border-top-color: #8fa863;
            border-left-color: #8fa863;
            border-right-color: #556b2f;
            border-bottom-color: #556b2f;
        }
        
        QPushButton:pressed {
            background-color: #3d4f2a;
            color: #ffffff;
            border: 2px inset #3d4f2a;
            border-top-color: #2d3f1a;
            border-left-color: #2d3f1a;
            border-right-color: #6b8e23;
            border-bottom-color: #6b8e23;
        }
        
        QPushButton:disabled {
            background-color: #3a3a3a;
            color: #5c5c5c;
            border: 2px solid #3a3a3a;
        }
        
        QPushButton:focus {
            border: 2px solid #ffcc00;
            border-top-color: #ffdd44;
            border-left-color: #ffdd44;
            border-right-color: #cc9900;
            border-bottom-color: #cc9900;
        }
        
        /* --- Rust/Metal Button Style --- */
        QPushButton#rustButton {
            background-color: #7c4a1c;
            border: 2px outset #b7410e;
            border-radius: 4px;
        }
        
        QPushButton#rustButton:hover {
            background-color: #8b4513;
            border: 2px solid #ffcc00;
        }
        
        /* --- Terminal/CRT Button Style --- */
        QPushButton#terminalButton {
            background-color: #0d1a0d;
            color: #33ff33;
            border: 2px solid #1a8c1a;
            font-family: Consolas;
            font-size: 11pt;
        }
        
        QPushButton#terminalButton:hover {
            background-color: #1a3a1a;
            color: #66ff66;
            border: 2px solid #33ff33;
        }
        
        /* --- Line Edit --- */
        QLineEdit {
            background-color: #1a1a1a;
            color: #c4b998;
            border: 2px inset #3a3a3a;
            border-top-color: #0d0d0d;
            border-left-color: #0d0d0d;
            border-right-color: #4a4a4a;
            border-bottom-color: #4a4a4a;
            border-radius: 3px;
            padding: 4px 8px;
            font-family: Consolas;
            font-size: 10pt;
        }
        
        QLineEdit:focus {
            border: 2px inset #6b8e23;
            border-top-color: #8fa863;
            border-left-color: #8fa863;
            border-right-color: #4a5d23;
            border-bottom-color: #4a5d23;
            background-color: #222222;
        }
        
        QLineEdit:disabled {
            background-color: #2a2a2a;
            color: #5c5c5c;
            border: 2px inset #3a3a3a;
        }
        
        /* --- Text Edit --- */
        QTextEdit, QPlainTextEdit {
            background-color: #1a1a1a;
            color: #c4b998;
            border: 2px inset #3a3a3a;
            border-top-color: #0d0d0d;
            border-left-color: #0d0d0d;
            border-right-color: #4a4a4a;
            border-bottom-color: #4a4a4a;
            border-radius: 3px;
            padding: 4px;
            font-family: Courier New;
            font-size: 10pt;
            selection-background-color: #6b8e23;
            selection-color: #ffcc00;
        }
        
        QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px inset #6b8e23;
            border-top-color: #8fa863;
            border-left-color: #8fa863;
            border-right-color: #4a5d23;
            border-bottom-color: #4a5d23;
        }
        
        /* --- Terminal Style Text Edit --- */
        QTextEdit#terminalEdit, QPlainTextEdit#terminalEdit {
            background-color: #0d1a0d;
            color: #33ff33;
            border: 2px solid #1a8c1a;
            font-family: Consolas;
            font-size: 11pt;
            selection-background-color: #1a8c1a;
            selection-color: #33ff33;
        }
        
        /* --- Combo Box --- */
        QComboBox {
            background-color: #2d2d2d;
            color: #c4b998;
            border: 2px solid #5c5c5c;
            border-radius: 2px;
            padding: 4px 8px;
            font-family: Consolas;
            font-size: 10pt;
        }
        
        QComboBox:hover {
            border: 2px solid #b7410e;
            color: #ffcc00;
        }
        
        QComboBox:focus {
            border: 2px solid #ffcc00;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #c4b998;
            margin-right: 5px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #2a2a28;
            color: #c4b998;
            border: 2px solid #5c5c5c;
            selection-background-color: #556b2f;
            selection-color: #ffcc00;
            padding: 4px;
        }
        
        /* --- Spin Box --- */
        QSpinBox, QDoubleSpinBox {
            background-color: #2d2d2d;
            color: #c4b998;
            border: 2px solid #5c5c5c;
            border-radius: 2px;
            padding: 4px;
            font-family: Consolas;
        }
        
        QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #ffcc00;
        }
        
        QSpinBox::up-button, QDoubleSpinBox::up-button {
            background-color: #4a5d23;
            border: 1px solid #5c5c5c;
        }
        
        QSpinBox::down-button, QDoubleSpinBox::down-button {
            background-color: #4a5d23;
            border: 1px solid #5c5c5c;
        }
        
        /* --- List Widget --- */
        QListWidget, QListView {
            background-color: #2d2d2d;
            color: #c4b998;
            border: 2px solid #5c5c5c;
            border-radius: 2px;
            padding: 4px;
            font-family: Consolas;
            font-size: 10pt;
            outline: 0;
        }
        
        QListWidget::item:selected, QListView::item:selected {
            background-color: #556b2f;
            color: #ffcc00;
            border: 1px solid #b7410e;
        }
        
        QListWidget::item:hover, QListView::item:hover {
            background-color: #3a3a3a;
            color: #e8dca8;
        }
        
        /* --- Tree Widget --- */
        QTreeWidget, QTreeView {
            background-color: #2d2d2d;
            color: #c4b998;
            border: 2px solid #5c5c5c;
            border-radius: 2px;
            padding: 4px;
            font-family: Consolas;
            font-size: 10pt;
            outline: 0;
        }
        
        QTreeWidget::item:selected, QTreeView::item:selected {
            background-color: #556b2f;
            color: #ffcc00;
        }
        
        QTreeWidget::item:hover, QTreeView::item:hover {
            background-color: #3a3a3a;
            color: #e8dca8;
        }
        
        QHeaderView::section {
            background-color: #3a3a3a;
            color: #c4b998;
            border: 1px solid #5c5c5c;
            padding: 6px;
            font-family: Consolas;
            font-weight: bold;
        }
        
        /* --- Tab Widget --- */
        QTabWidget::pane {
            background-color: #2a2a28;
            border: 2px solid #5c5c5c;
            border-radius: 2px;
        }
        
        QTabBar::tab {
            background-color: #3a3a3a;
            color: #c4b998;
            border: 2px solid #5c5c5c;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 8px 16px;
            font-family: Consolas;
            font-weight: bold;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #2a2a28;
            color: #ffcc00;
            border-bottom: 2px solid #2a2a28;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #4a4a48;
            color: #ffcc00;
        }
        
        QTabBar::tab:disabled {
            background-color: #3a3a3a;
            color: #5c5c5c;
        }
        
        /* --- Splitter --- */
        QSplitter::handle {
            background-color: #5c5c5c;
            border: 1px solid #3a3a3a;
        }
        
        QSplitter::handle:horizontal {
            width: 4px;
        }
        
        QSplitter::handle:vertical {
            height: 4px;
        }
        
        QSplitter::handle:hover {
            background-color: #b7410e;
        }
        
        /* --- Scroll Bar --- */
        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 14px;
            border: 1px solid #5c5c5c;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #4a5d23;
            border: 1px solid #5c5c5c;
            border-radius: 2px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #556b2f;
            border: 1px solid #b7410e;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        
        QScrollBar:horizontal {
            background-color: #2d2d2d;
            height: 14px;
            border: 1px solid #5c5c5c;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #4a5d23;
            border: 1px solid #5c5c5c;
            border-radius: 2px;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #556b2f;
            border: 1px solid #b7410e;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        /* --- Progress Bar --- */
        QProgressBar {
            background-color: #2d2d2d;
            border: 2px solid #5c5c5c;
            border-radius: 4px;
            text-align: center;
            color: #c4b998;
            font-family: Consolas;
            font-weight: bold;
        }
        
        QProgressBar::chunk {
            background-color: #6b8e23;
            border-radius: 2px;
        }
        
        /* --- Status Bar --- */
        QStatusBar {
            background-color: #2d2d2d;
            color: #c4b998;
            border-top: 2px solid #5c5c5c;
            font-family: Consolas;
            font-size: 9pt;
        }
        
        QStatusBar QLabel {
            color: #c4b998;
        }
        
        /* --- Tool Tip --- */
        QToolTip {
            background-color: #3a3a3a;
            color: #ffcc00;
            border: 2px solid #b7410e;
            padding: 4px;
            font-family: Consolas;
            font-size: 9pt;
        }
        
        /* --- Group Box --- */
        QGroupBox {
            background-color: #2a2a28;
            border: 2px outset #5c5c5c;
            border-top-color: #6a6a6a;
            border-left-color: #6a6a6a;
            border-right-color: #4a4a4a;
            border-bottom-color: #4a4a4a;
            border-radius: 4px;
            margin-top: 14px;
            padding-top: 14px;
            font-family: Consolas;
            font-weight: bold;
            color: #d4c4a8;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 2px 10px;
            color: #ffcc00;
            background-color: #3a3a38;
            border: 1px solid #5c5c5c;
            border-radius: 2px;
        }
        
        /* --- Dialog --- */
        QDialog {
            background-color: #2a2a28;
            border: 3px outset #5c5c5c;
            border-top-color: #6a6a6a;
            border-left-color: #6a6a6a;
            border-right-color: #3a3a3a;
            border-bottom-color: #3a3a3a;
        }
        
        /* --- Check Box --- */
        QCheckBox {
            color: #c4b998;
            font-family: Consolas;
            font-size: 10pt;
            spacing: 8px;
        }
        
        QCheckBox:hover {
            color: #ffcc00;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #5c5c5c;
            border-radius: 2px;
            background-color: #2d2d2d;
        }
        
        QCheckBox::indicator:checked {
            background-color: #556b2f;
            border: 2px solid #ffcc00;
        }
        
        QCheckBox::indicator:checked:hover {
            background-color: #6b8e23;
            border: 2px solid #ffcc00;
        }
        
        /* --- Radio Button --- */
        QRadioButton {
            color: #c4b998;
            font-family: Consolas;
            font-size: 10pt;
            spacing: 8px;
        }
        
        QRadioButton:hover {
            color: #ffcc00;
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #5c5c5c;
            border-radius: 8px;
            background-color: #2d2d2d;
        }
        
        QRadioButton::indicator:checked {
            background-color: #556b2f;
            border: 2px solid #ffcc00;
        }
        
        /* --- Slider --- */
        QSlider::groove:horizontal {
            background-color: #2d2d2d;
            border: 1px solid #5c5c5c;
            height: 8px;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal {
            background-color: #556b2f;
            border: 2px solid #5c5c5c;
            width: 16px;
            margin: -4px 0;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal:hover {
            background-color: #6b8e23;
            border: 2px solid #ffcc00;
        }
        
        QSlider::groove:vertical {
            background-color: #2d2d2d;
            border: 1px solid #5c5c5c;
            width: 8px;
            border-radius: 4px;
        }
        
        QSlider::handle:vertical {
            background-color: #556b2f;
            border: 2px solid #5c5c5c;
            height: 16px;
            margin: 0 -4px;
            border-radius: 4px;
        }
        
        /* --- Dock Widget --- */
        QDockWidget {
            background-color: #2a2a28;
            border: 2px solid #5c5c5c;
            titlebar-close-icon: url(close.png);
            titlebar-normal-icon: url(undock.png);
        }
        
        QDockWidget::title {
            background-color: #3a3a3a;
            text-align: center;
            padding: 4px;
            border-bottom: 2px solid #5c5c5c;
        }
        
        /* --- CRT Screen Effect Overlay --- */
        QLabel#crtOverlay {
            background-color: transparent;
            border: none;
        }
        """
    
    @staticmethod
    def get_panel_stylesheet():
        """Stylesheet for Fallout-style panels"""
        return """
        /* --- Fallout Panel Styles --- */
        
        /* Standard Panel */
        .fallout-panel {
            background-color: #2a2a28;
            border: 3px solid #5c5c5c;
            border-radius: 4px;
        }
        
        /* Worn Metal Panel */
        .fallout-panel-metal {
            background-color: #3a3a3a;
            border: 3px outset #6a6a6a;
            border-radius: 4px;
        }
        
        /* Rusty Panel */
        .fallout-panel-rust {
            background-color: #5d4a3a;
            border: 3px solid #8b3a0e;
            border-radius: 4px;
        }
        
        /* Pip-Boy Style Panel */
        .fallout-panel-pipboy {
            background-color: #0d1a0d;
            border: 2px solid #1a8c1a;
            border-radius: 4px;
        }
        
        /* Stat Bar Background */
        .fallout-stat-bar-bg {
            background-color: #1a1a1a;
            border: 2px inset #3a3a3a;
            border-radius: 2px;
        }
        """
    
    @staticmethod
    def get_button_stylesheet():
        """Additional button styles"""
        return """
        /* --- Fallout Button Styles --- */
        
        /* Main Action Button */
        .btn-main {
            background-color: #556b2f;
            color: #ffcc00;
            border: 3px outset #6b8e23;
            border-radius: 4px;
            padding: 8px 20px;
            font-family: Consolas;
            font-weight: bold;
            font-size: 11pt;
        }
        
        .btn-main:hover {
            background-color: #6b8e23;
            border: 3px solid #ffcc00;
        }
        
        .btn-main:pressed {
            background-color: #4a5d23;
            border: 3px inset #4a5d23;
        }
        
        /* Danger/Delete Button */
        .btn-danger {
            background-color: #7c3010;
            color: #ffcc00;
            border: 2px outset #b7410e;
            border-radius: 4px;
            font-weight: bold;
        }
        
        .btn-danger:hover {
            background-color: #8b3a0e;
            border: 2px solid #ffcc00;
        }
        
        /* Terminal Button */
        .btn-terminal {
            background-color: #0d1a0d;
            color: #33ff33;
            border: 2px solid #1a8c1a;
            border-radius: 2px;
            font-family: Consolas;
            font-size: 11pt;
            padding: 6px 12px;
        }
        
        .btn-terminal:hover {
            background-color: #1a2a1a;
            color: #66ff66;
            border: 2px solid #33ff33;
        }
        
        .btn-terminal:pressed {
            background-color: #0a150a;
            color: #1a8c1a;
        }
        
        /* Small Icon Button */
        .btn-icon {
            background-color: transparent;
            border: none;
            padding: 4px;
            min-width: 24px;
            min-height: 24px;
        }
        
        .btn-icon:hover {
            background-color: #3a3a3a;
            border: 1px solid #5c5c5c;
        }
        """


# =============================================================================
# FALLOUT 2 PALETTE CREATOR
# =============================================================================

class FalloutPalette:
    """Create Qt Palettes with Fallout 2 colors"""
    
    @staticmethod
    def create_standard_palette() -> QPalette:
        """Create the main application palette"""
        palette = QPalette()
        colors = FalloutColors()
        
        # Window
        palette.setColor(QPalette.ColorRole.Window, QColor(colors.DARK_SLATE))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.TEXT_NORMAL))
        
        # Base
        palette.setColor(QPalette.ColorRole.Base, QColor(colors.CHARCOAL))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.DARK_METAL))
        
        # Tool Tip
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.DARK_METAL))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.FALLOUT_YELLOW))
        
        # Text
        palette.setColor(QPalette.ColorRole.Text, QColor(colors.TEXT_NORMAL))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors.TEXT_BRIGHT))
        
        # Button
        palette.setColor(QPalette.ColorRole.Button, QColor(colors.MILITARY_GREEN))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.TEXT_NORMAL))
        
        # Highlight
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.OLIVE_DRAB))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.FALLOUT_YELLOW))
        
        # Link
        palette.setColor(QPalette.ColorRole.Link, QColor(colors.RUST_ORANGE))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(colors.COPPER_RUST))
        
        # Disabled
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(colors.TEXT_DIM))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colors.TEXT_DIM))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(colors.TEXT_DIM))
        
        return palette
    
    @staticmethod
    def create_terminal_palette() -> QPalette:
        """Create Pip-Boy terminal palette"""
        palette = QPalette()
        colors = FalloutColors()
        
        # Window - dark green screen
        palette.setColor(QPalette.ColorRole.Window, QColor(colors.PIPBOY_SCREEN))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.TERMINAL_GREEN))
        
        # Base
        palette.setColor(QPalette.ColorRole.Base, QColor(colors.PIPBOY_SCREEN))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.DIM_GREEN))
        
        # Text - bright green
        palette.setColor(QPalette.ColorRole.Text, QColor(colors.TERMINAL_GREEN))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors.BRIGHT_GREEN))
        
        # Button - darker green
        palette.setColor(QPalette.ColorRole.Button, QColor(colors.DIM_GREEN))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.TERMINAL_GREEN))
        
        # Highlight - selection green
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.DIM_GREEN))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.BRIGHT_GREEN))
        
        return palette


# =============================================================================
# FALLOUT UI COMPONENTS
# =============================================================================

class FalloutUIHelpers:
    """Helper functions for creating Fallout-style UI elements"""
    
    @staticmethod
    def apply_theme(app: QApplication):
        """Apply the complete Fallout theme to an application"""
        # Set palette
        app.setPalette(FalloutPalette.create_standard_palette())
        
        # Set stylesheet
        full_stylesheet = (
            FalloutStylesheet.get_main_stylesheet() + 
            FalloutStylesheet.get_panel_stylesheet() +
            FalloutStylesheet.get_button_stylesheet()
        )
        app.setStyleSheet(full_stylesheet)
        
        # Set default font
        app.setFont(FalloutFonts.get_ui_font())
        
        # Set stylesheet for all widgets
        app.setProperty("falloutTheme", True)
    
    @staticmethod
    def create_fallout_title(text: str) -> str:
        """Create a Fallout-style title with ASCII art border"""
        return f"""
╔══════════════════════════════════════════════╗
║        {text.upper():^36}        ║
╚══════════════════════════════════════════════╝
        """
    
    @staticmethod
    def create_stat_bar_html(value: int, max_value: int = 10, 
                             bar_color: str = None) -> str:
        """Create HTML for a SPECIAL stat bar"""
        if bar_color is None:
            bar_color = FalloutColors.OLIVE_DRAB
            
        percentage = (value / max_value) * 100
        
        # Color based on value
        if value <= 2:
            color = FalloutColors.STATUS_RED
        elif value <= 5:
            color = FalloutColors.STATUS_ORANGE
        else:
            color = bar_color
            
        return f"""
        <div style="
            background-color: #1a1a1a;
            border: 2px inset #3a3a3a;
            border-radius: 2px;
            height: 16px;
            width: 120px;
        ">
            <div style="
                background-color: {color};
                height: 100%;
                width: {percentage}%;
                border-radius: 1px;
            "></div>
        </div>
        """
    
    @staticmethod
    def create_crt_effect_css() -> str:
        """CSS for CRT scanline and flicker effects"""
        return """
        QWidget {
            /* Subtle scanline overlay */
            background-image: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 0, 0, 0.1) 2px,
                rgba(0, 0, 0, 0.1) 4px
            );
        }
        
        /* Screen flicker animation */
        @keyframes fallout-flicker {
            0% { opacity: 1.0; }
            92% { opacity: 1.0; }
            93% { opacity: 0.9; }
            94% { opacity: 1.0; }
            97% { opacity: 0.95; }
            98% { opacity: 1.0; }
            100% { opacity: 1.0; }
        }
        
        /* Glitch effect */
        @keyframes fallout-glitch {
            0% { transform: translate(0); }
            20% { transform: translate(-2px, 2px); }
            40% { transform: translate(-2px, -2px); }
            60% { transform: translate(2px, 2px); }
            80% { transform: translate(2px, -2px); }
            100% { transform: translate(0); }
        }
        """
    
    @staticmethod
    def get_worn_border_style() -> str:
        """Get stylesheet for worn/damaged border effect"""
        return """
            border-top: 2px solid #5c5c5c;
            border-left: 2px solid #5c5c5c;
            border-right: 2px solid #3a3a3a;
            border-bottom: 2px solid #3a3a3a;
            border-radius: 3px;
        """
    
    @staticmethod
    def get_rust_border_style() -> str:
        """Get stylesheet for rusty border effect"""
        return """
            border: 3px outset #8b4513;
            border-radius: 4px;
        """
    
    @staticmethod
    def get_depressed_border_style() -> str:
        """Get stylesheet for depressed/inset border effect"""
        return """
            border: 2px inset #5c5c5c;
            border-radius: 2px;
        """


# =============================================================================
# SPECIAL STAT WIDGET
# =============================================================================

class SpecialStatBar:
    """Widget for displaying SPECIAL stat bars like in Fallout"""
    
    @staticmethod
    def create_html(stat_name: str, value: int, max_value: int = 10) -> str:
        """Create HTML for a SPECIAL stat display"""
        colors = FalloutColors()
        
        # Determine color based on value
        if value <= 2:
            value_color = colors.STATUS_RED
        elif value <= 5:
            value_color = colors.STATUS_ORANGE
        else:
            value_color = colors.FALLOUT_YELLOW
            
        percentage = (value / max_value) * 100
        
        return f"""
        <div style="
            font-family: Consolas;
            color: {colors.TEXT_NORMAL};
            display: flex;
            align-items: center;
            gap: 8px;
        ">
            <span style="
                color: {value_color};
                font-weight: bold;
                width: 20px;
            ">{stat_name}</span>
            <div style="
                background-color: #1a1a1a;
                border: 2px inset #3a3a3a;
                border-radius: 2px;
                height: 12px;
                width: 100px;
                position: relative;
            ">
                <div style="
                    background-color: {value_color};
                    height: 100%;
                    width: {percentage}%;
                    border-radius: 1px;
                "></div>
            </div>
            <span style="
                color: {value_color};
                font-weight: bold;
                width: 15px;
            ">{value}</span>
        </div>
        """


# =============================================================================
# DIALOG TEXT FORMATTING
# =============================================================================

class FalloutDialogFormat:
    """Formatting utilities for Fallout-style dialog text"""
    
    @staticmethod
    def format_npc_text(text: str) -> str:
        """Format NPC dialog text with Fallout styling"""
        colors = FalloutColors()
        
        # Wrap in terminal-style box
        return f"""
        <div style="
            background-color: {colors.PANEL_BACKGROUND};
            border: 2px solid {colors.PANEL_BORDER};
            border-radius: 4px;
            padding: 12px;
            font-family: 'Courier New', Consolas;
            font-size: 11pt;
            color: {colors.TEXT_NORMAL};
            line-height: 1.4;
        ">{text}</div>
        """
    
    @staticmethod
    def format_option_text(text: str, is_selected: bool = False) -> str:
        """Format player option text"""
        colors = FalloutColors()
        
        if is_selected:
            bg_color = colors.OLIVE_DRAB
            text_color = colors.FALLOUT_YELLOW
            border_color = colors.RUST_ORANGE
        else:
            bg_color = colors.CHARCOAL
            text_color = colors.TEXT_NORMAL
            border_color = colors.PANEL_BORDER
            
        return f"""
        <div style="
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: 3px;
            padding: 8px 12px;
            margin: 2px 0;
            font-family: Consolas;
            font-size: 10pt;
            color: {text_color};
        ">
            ► {text}
        </div>
        """
    
    @staticmethod
    def format_terminal_text(text: str) -> str:
        """Format text for Pip-Boy terminal display"""
        colors = FalloutColors()
        
        return f"""
        <div style="
            background-color: {colors.PIPBOY_SCREEN};
            border: 2px solid {colors.DIM_GREEN};
            border-radius: 4px;
            padding: 8px;
            font-family: Consolas;
            font-size: 11pt;
            color: {colors.TERMINAL_GREEN};
            line-height: 1.3;
        ">{text}</div>
        """
    
    @staticmethod
    def format_header(text: str) -> str:
        """Format section header"""
        colors = FalloutColors()
        
        return f"""
        <div style="
            color: {colors.FALLOUT_YELLOW};
            font-family: Consolas;
            font-size: 12pt;
            font-weight: bold;
            padding: 8px 0;
            border-bottom: 2px solid {colors.RUST_ORANGE};
            margin-bottom: 8px;
        ">{text.upper()}</div>
        """


# =============================================================================
# EXPORT FOR EASY IMPORTING
# =============================================================================

__all__ = [
    'FalloutColors',
    'FalloutFonts', 
    'FalloutStylesheet',
    'FalloutPalette',
    'FalloutUIHelpers',
    'SpecialStatBar',
    'FalloutDialogFormat',
]
