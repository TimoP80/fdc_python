"""
Skeuomorphic UI Demo Application
Demonstrates all skeuomorphic widgets and themes.

This module provides a complete demo of the skeuomorphic design system
including all themes, widgets, and interactive elements.
"""

import sys
import logging
from typing import Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QProgressBar, QCheckBox, QRadioButton,
    QComboBox, QLineEdit, QTextEdit, QGroupBox, QScrollArea,
    QTabWidget, QSpinBox, QDoubleSpinBox, QButtonGroup,
    QMainWindow, QStatusBar
)

# Import skeuomorphic modules
from ui.skeuomorphic_theme import (
    get_theme_manager, SkeuomorphicThemeManager,
    set_skeuomorphic_theme, apply_skeuomorphic_theme,
    SkeuomorphicTheme, MahoganyBrassTheme, BrushedSteelBlueTheme,
    IvoryLeatherGoldTheme, CarbonFiberOrangeTheme, VintageCreamCopperTheme
)
from ui.skeuomorphic_widgets import (
    SkeuomorphicButton, SkeuomorphicSlider, SkeuomorphicProgressBar,
    SkeuomorphicToggle, SkeuomorphicScrollBar, SkeuomorphicPanel,
    apply_skeuomorphic_theme as apply_widget_theme
)
from ui.skeuomorphic_window import (
    SkeuomorphicWindow, SkeuomorphicTitleBar, create_skeuomorphic_window
)

logger = logging.getLogger(__name__)


# =============================================================================
# DEMO WIDGETS
# =============================================================================

class SkeuomorphicDemoWidget(QWidget):
    """
    Main demo widget showcasing all skeuomorphic elements.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._theme = get_theme_manager().get_current_theme()
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the demo UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Skeuomorphic UI Components Demo")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #e8d4c0;
                padding: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Create scroll area for all demos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(500)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Buttons section
        scroll_layout.addWidget(self._create_button_section())
        
        # Sliders section
        scroll_layout.addWidget(self._create_slider_section())
        
        # Progress section
        scroll_layout.addWidget(self._create_progress_section())
        
        # Toggles section
        scroll_layout.addWidget(self._create_toggle_section())
        
        # Inputs section
        scroll_layout.addWidget(self._create_input_section())
        
        # Dropdowns section
        scroll_layout.addWidget(self._create_dropdown_section())
        
        # Checkboxes and radios section
        scroll_layout.addWidget(self._create_check_radio_section())
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
    def _create_button_section(self) -> QWidget:
        """Create button demonstration section"""
        group = QGroupBox("Buttons with Tactile Depression Effects")
        group.setMinimumHeight(200)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Row 1: Standard buttons
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        
        self.btn_primary = SkeuomorphicButton("Primary", self)
        self.btn_primary.set_button_type('primary')
        self.btn_primary.clicked.connect(lambda: self._on_button_click("Primary"))
        
        self.btn_secondary = SkeuomorphicButton("Secondary", self)
        self.btn_secondary.clicked.connect(lambda: self._on_button_click("Secondary"))
        
        self.btn_success = SkeuomorphicButton("Success", self)
        self.btn_success.set_button_type('success')
        
        self.btn_danger = SkeuomorphicButton("Danger", self)
        self.btn_danger.set_button_type('danger')
        
        row1.addWidget(self.btn_primary)
        row1.addWidget(self.btn_secondary)
        row1.addWidget(self.btn_success)
        row1.addWidget(self.btn_danger)
        row1.addStretch()
        
        layout.addLayout(row1)
        
        # Row 2: Disabled and icons
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        
        btn_disabled = SkeuomorphicButton("Disabled", self)
        btn_disabled.setEnabled(False)
        
        btn_large = SkeuomorphicButton("Large Button", self)
        btn_large.setMinimumSize(200, 50)
        
        btn_small = SkeuomorphicButton("Small", self)
        btn_small.setMinimumSize(80, 30)
        
        row2.addWidget(btn_disabled)
        row2.addWidget(btn_large)
        row2.addWidget(btn_small)
        row2.addStretch()
        
        layout.addLayout(row2)
        
        # Row 3: Custom styled buttons
        row3 = QHBoxLayout()
        
        btn_custom1 = QPushButton("Wood Theme", self)
        btn_custom1.setMinimumHeight(40)
        
        btn_custom2 = QPushButton("Metal Theme", self)
        btn_custom2.setMinimumHeight(40)
        
        row3.addWidget(btn_custom1)
        row3.addWidget(btn_custom2)
        row3.addStretch()
        
        layout.addLayout(row3)
        
        return group
        
    def _create_slider_section(self) -> QWidget:
        """Create slider demonstration section"""
        group = QGroupBox("Textured Sliders with 3D Grips")
        group.setMinimumHeight(180)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Horizontal slider
        h_layout = QVBoxLayout()
        
        label_h = QLabel("Horizontal Slider")
        h_layout.addWidget(label_h)
        
        self.slider_h = SkeuomorphicSlider(self)
        self.slider_h.set_range(0, 100)
        self.slider_h.set_value(50)
        self.slider_h.valueChanged.connect(self._on_slider_changed)
        h_layout.addWidget(self.slider_h)
        
        layout.addLayout(h_layout)
        
        # Slider with labels
        h_layout2 = QVBoxLayout()
        
        label_labeled = QLabel("Slider with Value Display: 50")
        h_layout2.addWidget(label_labeled)
        
        slider_labeled = SkeuomorphicSlider(self)
        slider_labeled.set_range(0, 200)
        slider_labeled.set_value(75)
        h_layout2.addWidget(slider_labeled)
        
        layout.addLayout(h_layout2)
        
        # Disabled slider
        slider_disabled = SkeuomorphicSlider(self)
        slider_disabled.set_range(0, 100)
        slider_disabled.set_value(30)
        slider_disabled.setEnabled(False)
        layout.addWidget(slider_disabled)
        
        return group
        
    def _create_progress_section(self) -> QWidget:
        """Create progress bar demonstration section"""
        group = QGroupBox("Authentic Progress Indicators")
        group.setMinimumHeight(150)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Progress bar with value
        h_layout1 = QHBoxLayout()
        
        label1 = QLabel("Progress:")
        h_layout1.addWidget(label1)
        
        self.progress_bar = SkeuomorphicProgressBar(self)
        self.progress_bar.set_range(0, 100)
        self.progress_bar.set_value(60)
        h_layout1.addWidget(self.progress_bar, 1)
        
        layout.addLayout(h_layout1)
        
        # Progress bar controls
        h_layout2 = QHBoxLayout()
        
        btn_decrease = QPushButton("-10%", self)
        btn_decrease.clicked.connect(lambda: self._adjust_progress(-10))
        
        btn_reset = QPushButton("Reset", self)
        btn_reset.clicked.connect(lambda: self.progress_bar.set_value(0))
        
        btn_increase = QPushButton("+10%", self)
        btn_increase.clicked.connect(lambda: self._adjust_progress(10))
        
        h_layout2.addWidget(btn_decrease)
        h_layout2.addWidget(btn_reset)
        h_layout2.addWidget(btn_increase)
        h_layout2.addStretch()
        
        layout.addLayout(h_layout2)
        
        # Indeterminate progress
        h_layout3 = QHBoxLayout()
        
        label3 = QLabel("Indeterminate:")
        h_layout3.addWidget(label3)
        
        progress_indet = SkeuomorphicProgressBar(self)
        progress_indet.set_indeterminate(True)
        h_layout3.addWidget(progress_indet, 1)
        
        layout.addLayout(h_layout3)
        
        return group
        
    def _create_toggle_section(self) -> QWidget:
        """Create toggle switch demonstration section"""
        group = QGroupBox("Tactile Toggle Switches")
        group.setMinimumHeight(120)
        
        layout = QHBoxLayout(group)
        layout.setSpacing(30)
        
        # Toggle 1
        v_layout1 = QVBoxLayout()
        label1 = QLabel("Feature Enabled")
        v_layout1.addWidget(label1, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.toggle1 = SkeuomorphicToggle(self)
        self.toggle1.setChecked(False)
        self.toggle1.toggled.connect(lambda checked: label1.setText(f"Feature {'Enabled' if checked else 'Disabled'}"))
        v_layout1.addWidget(self.toggle1, 0, Qt.AlignmentFlag.AlignHCenter)
        
        layout.addLayout(v_layout1)
        
        # Toggle 2
        v_layout2 = QVBoxLayout()
        label2 = QLabel("Notifications")
        v_layout2.addWidget(label2, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.toggle2 = SkeuomorphicToggle(self)
        self.toggle2.setChecked(True)
        v_layout2.addWidget(self.toggle2, 0, Qt.AlignmentFlag.AlignHCenter)
        
        layout.addLayout(v_layout2)
        
        # Toggle 3 (disabled)
        v_layout3 = QVBoxLayout()
        label3 = QLabel("Disabled")
        v_layout3.addWidget(label3, 0, Qt.AlignmentFlag.AlignHCenter)
        
        toggle3 = SkeuomorphicToggle(self)
        toggle3.setEnabled(False)
        v_layout3.addWidget(toggle3, 0, Qt.AlignmentFlag.AlignHCenter)
        
        layout.addLayout(v_layout3)
        
        layout.addStretch()
        
        return group
        
    def _create_input_section(self) -> QWidget:
        """Create input field demonstration section"""
        group = QGroupBox("Text Inputs with Depth")
        group.setMinimumHeight(180)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Single line input
        h_layout1 = QHBoxLayout()
        
        label1 = QLabel("Name:")
        h_layout1.addWidget(label1)
        
        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("Enter your name...")
        h_layout1.addWidget(self.line_edit, 1)
        
        layout.addLayout(h_layout1)
        
        # Password input
        h_layout2 = QHBoxLayout()
        
        label2 = QLabel("Password:")
        h_layout2.addWidget(label2)
        
        line_password = QLineEdit(self)
        line_password.setEchoMode(QLineEdit.EchoMode.Password)
        line_password.setPlaceholderText("Enter password...")
        h_layout2.addWidget(line_password, 1)
        
        layout.addLayout(h_layout2)
        
        # Number input
        h_layout3 = QHBoxLayout()
        
        label3 = QLabel("Value:")
        h_layout3.addWidget(label3)
        
        spin_box = QSpinBox(self)
        spin_box.setRange(0, 1000)
        spin_box.setValue(500)
        
        double_spin = QDoubleSpinBox(self)
        double_spin.setRange(0, 100)
        double_spin.setValue(50.5)
        
        h_layout3.addWidget(spin_box)
        h_layout3.addWidget(double_spin)
        
        layout.addLayout(h_layout3)
        
        # Text edit
        h_layout4 = QHBoxLayout()
        
        label4 = QLabel("Notes:")
        h_layout4.addWidget(label4)
        
        text_edit = QTextEdit(self)
        text_edit.setPlaceholderText("Enter notes...")
        text_edit.setMaximumHeight(60)
        h_layout4.addWidget(text_edit, 1)
        
        layout.addLayout(h_layout4)
        
        return group
        
    def _create_dropdown_section(self) -> QWidget:
        """Create dropdown demonstration section"""
        group = QGroupBox("Ornate Dropdown Menus")
        group.setMinimumHeight(120)
        
        layout = QHBoxLayout(group)
        layout.setSpacing(20)
        
        # ComboBox 1
        v_layout1 = QVBoxLayout()
        
        label1 = QLabel("Select Option:")
        v_layout1.addWidget(label1)
        
        combo1 = QComboBox(self)
        combo1.addItems(["Option 1", "Option 2", "Option 3", "Option 4"])
        
        v_layout1.addWidget(combo1)
        
        layout.addLayout(v_layout1)
        
        # ComboBox 2
        v_layout2 = QVBoxLayout()
        
        label2 = QLabel("Choose Theme:")
        v_layout2.addWidget(label2)
        
        combo2 = QComboBox(self)
        combo2.addItems([
            "Mahogany & Brass",
            "Brushed Steel & Blue",
            "Ivory Leather & Gold",
            "Carbon Fiber & Orange",
            "Vintage Cream & Copper"
        ])
        
        v_layout2.addWidget(combo2)
        
        layout.addLayout(v_layout2)
        
        # Disabled ComboBox
        v_layout3 = QVBoxLayout()
        
        label3 = QLabel("Disabled:")
        v_layout3.addWidget(label3)
        
        combo3 = QComboBox(self)
        combo3.addItems(["Cannot Select"])
        combo3.setEnabled(False)
        
        v_layout3.addWidget(combo3)
        
        layout.addLayout(v_layout3)
        
        layout.addStretch()
        
        return group
        
    def _create_check_radio_section(self) -> QWidget:
        """Create checkbox and radio button demonstration"""
        group = QGroupBox("Checkboxes and Radio Buttons")
        group.setMinimumHeight(120)
        
        layout = QHBoxLayout(group)
        layout.setSpacing(40)
        
        # Checkboxes
        v_check = QVBoxLayout()
        
        label_check = QLabel("Options:")
        v_check.addWidget(label_check)
        
        check1 = QCheckBox("Enable Feature", self)
        check1.setChecked(True)
        
        check2 = QCheckBox("Show Notifications", self)
        
        check3 = QCheckBox("Auto-save", self)
        check3.setChecked(True)
        
        v_check.addWidget(check1)
        v_check.addWidget(check2)
        v_check.addWidget(check3)
        
        layout.addLayout(v_check)
        
        # Radio buttons
        v_radio = QVBoxLayout()
        
        label_radio = QLabel("Mode:")
        v_radio.addWidget(label_radio)
        
        radio_group = QButtonGroup(self)
        
        radio1 = QRadioButton("Mode A", self)
        radio1.setChecked(True)
        
        radio2 = QRadioButton("Mode B", self)
        
        radio3 = QRadioButton("Mode C", self)
        
        radio_group.addButton(radio1)
        radio_group.addButton(radio2)
        radio_group.addButton(radio3)
        
        v_radio.addWidget(radio1)
        v_radio.addWidget(radio2)
        v_radio.addWidget(radio3)
        
        layout.addLayout(v_radio)
        
        layout.addStretch()
        
        return group
        
    def _on_button_click(self, button_name: str):
        """Handle button click"""
        logger.info(f"Button clicked: {button_name}")
        
    def _on_slider_changed(self, value: int):
        """Handle slider value change"""
        logger.info(f"Slider value: {value}")
        
    def _adjust_progress(self, delta: int):
        """Adjust progress bar value"""
        new_value = max(0, min(100, self.progress_bar.value() + delta))
        self.progress_bar.set_value(new_value)


# =============================================================================
# THEME PREVIEW WIDGET
# =============================================================================

class ThemePreviewWidget(QWidget):
    """
    Widget for previewing different skeuomorphic themes.
    """
    
    themeChanged = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._theme_manager = get_theme_manager()
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup theme preview UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Theme Selection")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Theme buttons
        themes = self._theme_manager.get_available_themes()
        
        for key, name in themes.items():
            btn = QPushButton(name, self)
            btn.clicked.connect(lambda checked, k=key: self._select_theme(k))
            layout.addWidget(btn)
            
        layout.addStretch()
        
    def _select_theme(self, theme_key: str):
        """Select a theme"""
        self._theme_manager.set_theme(theme_key)
        self.themeChanged.emit(theme_key)


# =============================================================================
# MAIN DEMO WINDOW
# =============================================================================

class SkeuomorphicDemoWindow(QMainWindow):
    """
    Main window for the skeuomorphic demo application.
    """
    
    def __init__(self):
        super().__init__()
        self._theme_manager = get_theme_manager()
        
        # Set initial theme
        self._theme_manager.set_theme('mahogany')
        
        self._setup_ui()
        self._apply_theme()
        
    def _setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle("Skeuomorphic UI Demo")
        self.setMinimumSize(900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left panel - Theme selector
        left_panel = QWidget()
        left_panel.setMinimumWidth(200)
        left_panel.setMaximumWidth(250)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        # Theme preview
        self.theme_preview = ThemePreviewWidget(self)
        self.theme_preview.themeChanged.connect(self._on_theme_changed)
        left_layout.addWidget(self.theme_preview)
        
        # Theme info
        info_label = QLabel(
            "Select a theme to preview the skeuomorphic styling.\n\n"
            "Each theme features:\n"
            "• Distinct material textures\n"
            "• Custom color palettes\n"
            "• Realistic depth effects\n"
            "• Tactile feedback"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #9aa0a8; font-size: 9pt; padding: 10px;")
        left_layout.addWidget(info_label)
        
        main_layout.addWidget(left_panel)
        
        # Right panel - Demo content
        self.demo_widget = SkeuomorphicDemoWidget(self)
        main_layout.addWidget(self.demo_widget, 1)
        
        # Status bar
        self.statusBar().showMessage("Ready - Select a theme to customize the UI")
        
    def _apply_theme(self):
        """Apply the current theme to the application"""
        stylesheet = self._theme_manager.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
            
    def _on_theme_changed(self, theme_key: str):
        """Handle theme change"""
        self._apply_theme()
        self.statusBar().showMessage(f"Theme changed to: {theme_key}", 3000)
        logger.info(f"Theme changed to: {theme_key}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_demo():
    """Run the skeuomorphic demo application"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Skeuomorphic UI Demo")
    app.setApplicationVersion("1.0.0")
    
    # Apply default theme
    theme_manager = get_theme_manager()
    theme_manager.set_theme('mahogany')
    theme_manager.apply_to_app(app)
    
    # Create and show window
    window = SkeuomorphicDemoWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    run_demo()