"""
Theme Manager Dialog for Fallout Dialogue Creator
Provides a UI for browsing, previewing, and activating themes
"""

import logging
from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QComboBox, 
    QLineEdit, QGroupBox, QFrame, QScrollArea, QWidget,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPalette, QFont, QBrush

from core.theme_manager import ThemeManager, Theme, ThemeCategory, ThemeError

logger = logging.getLogger(__name__)


class ThemePreviewWidget(QFrame):
    """Widget that shows a preview of a theme"""
    
    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the preview UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setMinimumSize(200, 150)
        self.setMaximumSize(200, 150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Title
        title_label = QLabel(self.theme.name)
        title_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Color preview grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)
        
        colors = [
            ("Primary", self.theme.primary_color),
            ("Secondary", self.theme.secondary_color),
            ("Background", self.theme.background_color),
            ("Text", self.theme.text_color),
            ("Accent", self.theme.accent_color),
            ("Border", self.theme.border_color),
        ]
        
        for i, (name, color) in enumerate(colors):
            row, col = i // 3, i % 3
            
            color_frame = QFrame()
            color_frame.setFixedSize(50, 30)
            color_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border: 1px solid {self.theme.border_color};
                }}
            """)
            grid_layout.addWidget(color_frame, row, col)
        
        layout.addLayout(grid_layout)
        
        # Category label
        category_label = QLabel(f"Category: {self.theme.category.value}")
        category_label.setFont(QFont("Consolas", 8))
        category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(category_label)
        
        # Author/version
        info_label = QLabel(f"v{self.theme.version} by {self.theme.author}")
        info_label.setFont(QFont("Consolas", 7))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet(f"color: {self.theme.text_color};")
        layout.addWidget(info_label)
        
        # Apply theme-specific styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.panel_background};
                border: 2px solid {self.theme.border_color};
            }}
            QLabel {{
                color: {self.theme.text_color};
            }}
        """)


class ThemeListItem(QListWidgetItem):
    """Custom list item for theme display"""
    
    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        
        # Set display text
        display_text = f"{theme.name}"
        if theme.is_builtin:
            display_text += " (Built-in)"
        if not theme.is_compatible:
            display_text += " [Error]"
        
        self.setText(display_text)
        
        # Set icon/color indicator
        if not theme.is_compatible:
            # Red indicator for incompatible themes
            self.setForeground(QBrush(QColor("#ff4444")))
        elif theme.is_builtin:
            # Green indicator for built-in themes
            self.setForeground(QBrush(QColor("#44ff44")))
        else:
            # Yellow for custom themes
            self.setForeground(QBrush(QColor("#ffff44")))
        
        # Store theme reference
        self.setData(Qt.ItemDataRole.UserRole, theme)


class ThemeManagerDialog(QDialog):
    """
    Theme Manager Dialog
    Allows users to browse, preview, and activate themes
    """
    
    # Signal emitted when theme is activated
    theme_activated = pyqtSignal(str)
    
    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._setup_ui()
        self._load_themes()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Theme Manager")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Theme Manager")
        header_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        main_layout.addWidget(header_label)
        
        # Filter controls
        filter_group = QGroupBox("Filter & Search")
        filter_layout = QHBoxLayout(filter_group)
        
        # Category filter
        category_label = QLabel("Category:")
        filter_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        for category in ThemeCategory:
            self.category_combo.addItem(category.value.capitalize(), category)
        filter_layout.addWidget(self.category_combo)
        
        # Search box
        search_label = QLabel("Search:")
        filter_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search themes...")
        self.search_edit.setMaximumWidth(200)
        filter_layout.addWidget(self.search_edit)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Reload all themes")
        filter_layout.addWidget(self.refresh_button)
        
        filter_layout.addStretch()
        
        main_layout.addWidget(filter_group)
        
        # Theme list and preview
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Theme list
        list_group = QGroupBox("Available Themes")
        list_layout = QVBoxLayout(list_group)
        
        self.theme_list = QListWidget()
        self.theme_list.setMinimumWidth(250)
        self.theme_list.setMaximumWidth(350)
        list_layout.addWidget(self.theme_list)
        
        content_layout.addWidget(list_group)
        
        # Preview panel
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_widget = None
        self.preview_placeholder = QLabel("Select a theme to preview")
        self.preview_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_placeholder.setMinimumSize(200, 150)
        preview_layout.addWidget(self.preview_placeholder)
        
        # Theme info
        self.info_label = QLabel("No theme selected")
        self.info_label.setWordWrap(True)
        preview_layout.addWidget(self.info_label)
        
        content_layout.addWidget(preview_group)
        
        main_layout.addLayout(content_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Activate button
        self.activate_button = QPushButton("Activate Theme")
        self.activate_button.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.activate_button.setEnabled(False)
        button_layout.addWidget(self.activate_button)
        
        button_layout.addStretch()
        
        # Close button
        self.close_button = QPushButton("Close")
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Consolas", 8))
        main_layout.addWidget(self.status_label)
    
    def _load_themes(self):
        """Load themes into the list"""
        self.theme_list.clear()
        
        themes = self.theme_manager.get_themes()
        
        for theme in themes:
            item = ThemeListItem(theme, self.theme_list)
            self.theme_list.addItem(item)
        
        # Select active theme
        active_theme_id = self.theme_manager.get_active_theme_id()
        if active_theme_id:
            for i in range(self.theme_list.count()):
                item = self.theme_list.item(i)
                if item.theme.id == active_theme_id:
                    self.theme_list.setCurrentItem(item)
                    break
        
        self._update_status(f"Loaded {len(themes)} themes")
    
    def _connect_signals(self):
        """Connect signals and slots"""
        self.theme_list.currentItemChanged.connect(self._on_theme_selected)
        self.category_combo.currentIndexChanged.connect(self._on_filter_changed)
        self.search_edit.textChanged.connect(self._on_filter_changed)
        self.refresh_button.clicked.connect(self._on_refresh)
        self.activate_button.clicked.connect(self._on_activate)
        self.close_button.clicked.connect(self.accept)
        
        # Theme manager signals
        self.theme_manager.themes_updated.connect(self._load_themes)
        self.theme_manager.theme_error.connect(self._on_theme_error)
    
    def _on_theme_selected(self, current: Optional[ThemeListItem], 
                          previous: Optional[ThemeListItem]):
        """Handle theme selection change"""
        if current is None:
            self.activate_button.setEnabled(False)
            self.preview_placeholder.show()
            if self.preview_widget:
                self.preview_widget.hide()
            self.info_label.setText("No theme selected")
            return
        
        theme = current.theme
        
        # Show preview
        self.preview_placeholder.hide()
        if self.preview_widget:
            self.preview_widget.hide()
        
        self.preview_widget = ThemePreviewWidget(theme, self.preview_placeholder.parent())
        # Find the preview layout and add the widget
        preview_group = self.preview_placeholder.parent()
        for child in preview_group.findChildren(ThemePreviewWidget):
            child.hide()
        
        # Add to layout
        layout = preview_group.layout()
        layout.insertWidget(0, self.preview_widget)
        
        # Update info
        info_text = f"<b>{theme.name}</b><br>"
        info_text += f"Category: {theme.category.value}<br>"
        info_text += f"Author: {theme.author}<br>"
        info_text += f"Version: {theme.version}<br>"
        info_text += f"<br>{theme.description}"
        
        if not theme.is_compatible:
            info_text += f"<br><br><span style='color: red;'>Error: {theme.error_message}</span>"
        
        self.info_label.setText(info_text)
        
        # Enable activate button if compatible
        self.activate_button.setEnabled(theme.is_compatible)
        
        # Mark active theme
        active_id = self.theme_manager.get_active_theme_id()
        if theme.id == active_id:
            self.activate_button.setText("Currently Active")
            self.activate_button.setEnabled(False)
        else:
            self.activate_button.setText("Activate Theme")
            self.activate_button.setEnabled(theme.is_compatible)
    
    def _on_filter_changed(self):
        """Handle filter changes"""
        category = self.category_combo.currentData()
        search_text = self.search_edit.text()
        
        themes = self.theme_manager.filter_themes(category, search_text)
        
        # Save current selection
        current_theme_id = None
        current_item = self.theme_list.currentItem()
        if current_item:
            current_theme_id = current_item.theme.id
        
        # Update list
        self.theme_list.clear()
        for theme in themes:
            item = ThemeListItem(theme, self.theme_list)
            self.theme_list.addItem(item)
        
        # Restore selection
        if current_theme_id:
            for i in range(self.theme_list.count()):
                item = self.theme_list.item(i)
                if item.theme.id == current_theme_id:
                    self.theme_list.setCurrentItem(item)
                    break
        
        self._update_status(f"Showing {len(themes)} of {len(self.theme_manager.get_themes())} themes")
    
    def _on_refresh(self):
        """Handle refresh button click"""
        self._update_status("Refreshing themes...")
        self.theme_manager.refresh_themes()
        self._load_themes()
        self._update_status("Themes refreshed")
    
    def _on_activate(self):
        """Handle activate button click"""
        current_item = self.theme_list.currentItem()
        if current_item is None:
            return
        
        theme = current_item.theme
        
        if not theme.is_compatible:
            QMessageBox.warning(
                self,
                "Cannot Activate Theme",
                f"This theme cannot be activated due to the following error:\n\n{theme.error_message}"
            )
            return
        
        # Activate theme
        success = self.theme_manager.set_active_theme(theme.id)
        
        if success:
            self._update_status(f"Activated theme: {theme.name}")
            self.theme_activated.emit(theme.id)
            
            # Update button state
            self.activate_button.setText("Currently Active")
            self.activate_button.setEnabled(False)
            
            # Update list to show active theme
            for i in range(self.theme_list.count()):
                item = self.theme_list.item(i)
                if item.theme.id == theme.id:
                    # Force refresh of item display
                    self.theme_list.repaint()
                    break
        else:
            QMessageBox.warning(
                self,
                "Activation Failed",
                "Failed to activate the selected theme. Check the logs for details."
            )
    
    def _on_theme_error(self, error_message: str):
        """Handle theme errors"""
        QMessageBox.warning(self, "Theme Error", error_message)
    
    def _update_status(self, message: str):
        """Update status bar"""
        self.status_label.setText(message)


def show_theme_manager(theme_manager: ThemeManager, parent=None) -> bool:
    """
    Show the theme manager dialog
    
    Args:
        theme_manager: The theme manager instance
        parent: Parent widget
        
    Returns:
        True if a theme was activated, False otherwise
    """
    dialog = ThemeManagerDialog(theme_manager, parent)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted
