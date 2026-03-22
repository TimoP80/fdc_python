"""
NPC Editor - Comprehensive NPC Property Editor
A PyQt6-based GUI for editing NPC properties including:
- Name, appearance, behavior patterns
- Attributes (SPECIAL), inventory items
- Dialogue options, AI behavior settings
- Relationship parameters
"""

import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QTableWidget,
    QTableWidgetItem, QGroupBox, QFormLayout, QScrollArea,
    QSlider, QCheckBox, QColorDialog, QFileDialog, QMessageBox,
    QGridLayout, QFrame, QSplitter, QToolButton, QProgressBar,
    QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette

from models.npc import (
    Npc, NpcClass, Gender, Appearance, NpcAttribute, SkillValue,
    InventoryItem, BehaviorPattern, AiSettings, AiPackage,
    Relationship, RelationshipType, ReputationType, NpcDialogue,
    Skill
)
from ui.fallout_theme import FalloutColors, FalloutFonts

logger = logging.getLogger(__name__)


class ValidationLabel(QLabel):
    """Custom label that shows validation status"""
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._is_valid = True
        self._message = ""
        self.update_appearance()
    
    def set_valid(self, is_valid: bool, message: str = ""):
        self._is_valid = is_valid
        self._message = message
        self.update_appearance()
    
    def update_appearance(self):
        if self._is_valid:
            self.setStyleSheet(f"color: {FalloutColors.TERMINAL_GREEN};")
            self.setText("✓")
        else:
            self.setStyleSheet(f"color: {FalloutColors.STATUS_RED}; font-weight: bold;")
            self.setText(f"✗ {self._message}")


class FalloutTabWidget(QTabWidget):
    """Custom tab widget with Fallout styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {FalloutColors.PANEL_BORDER};
                background-color: {FalloutColors.PANEL_BACKGROUND};
            }}
            QTabBar::tab {{
                background-color: {FalloutColors.DARK_OLIVE_GREEN};
                color: {FalloutColors.TEXT_NORMAL};
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid {FalloutColors.PANEL_BORDER};
            }}
            QTabBar::tab:selected {{
                background-color: {FalloutColors.OLIVE_DRAB};
                color: {FalloutColors.FALLOUT_YELLOW};
            }}
            QTabBar::tab:hover {{
                background-color: {FalloutColors.FADED_GREEN};
            }}
        """)


class BasicInfoWidget(QWidget):
    """Widget for NPC basic information (name, description, etc.)"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._connect_signals()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Basic Information")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        # Form layout for basic fields
        form = QFormLayout()
        form.setSpacing(8)
        
        # Name field
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter NPC name...")
        self._name_edit.setMaxLength(32)
        self._name_validation = ValidationLabel()
        form.addRow("Name:", self._name_edit)
        
        # Description
        self._description_edit = QTextEdit()
        self._description_edit.setPlaceholderText("Enter NPC description...")
        self._description_edit.setMaximumHeight(80)
        form.addRow("Description:", self._description_edit)
        
        # Comments/Notes
        self._comments_edit = QTextEdit()
        self._comments_edit.setPlaceholderText("Designer notes...")
        self._comments_edit.setMaximumHeight(60)
        form.addRow("Comments:", self._comments_edit)
        
        layout.addLayout(form)
        
        # Classification group
        class_group = QGroupBox("Classification")
        class_layout = QFormLayout()
        
        # NPC Class
        self._class_combo = QComboBox()
        for cls in NpcClass:
            self._class_combo.addItem(cls.name.replace('_', ' ').title(), cls.value)
        class_layout.addRow("Class:", self._class_combo)
        
        # Gender
        self._gender_combo = QComboBox()
        for gender in Gender:
            if gender != Gender.NONE:
                self._gender_combo.addItem(gender.name.title(), gender.value)
        class_layout.addRow("Gender:", self._gender_combo)
        
        # Age
        self._age_spin = QSpinBox()
        self._age_spin.setRange(0, 200)
        self._age_spin.setSuffix(" years")
        class_layout.addRow("Age:", self._age_spin)
        
        # FMF File
        self._fmf_file_edit = QLineEdit()
        self._fmf_file_edit.setPlaceholderText("Associated .fmf file...")
        self._fmf_file_btn = QPushButton("Browse...")
        fmf_layout = QHBoxLayout()
        fmf_layout.addWidget(self._fmf_file_edit)
        fmf_layout.addWidget(self._fmf_file_btn)
        class_layout.addRow("FMF File:", fmf_layout)
        
        class_group.setLayout(class_layout)
        layout.addWidget(class_group)
        
        layout.addStretch()
    
    def _connect_signals(self):
        self._name_edit.textChanged.connect(self._on_name_changed)
        self._description_edit.textChanged.connect(self._on_data_changed)
        self._comments_edit.textChanged.connect(self._on_data_changed)
        self._class_combo.currentIndexChanged.connect(self._on_data_changed)
        self._gender_combo.currentIndexChanged.connect(self._on_data_changed)
        self._age_spin.valueChanged.connect(self._on_data_changed)
        self._fmf_file_edit.textChanged.connect(self._on_data_changed)
        self._fmf_file_btn.clicked.connect(self._on_browse_fmf)
    
    def _load_data(self):
        self._name_edit.setText(self._npc.name)
        self._description_edit.setText(self._npc.description)
        self._comments_edit.setText(self._npc.comments)
        
        # Set class combo
        idx = self._class_combo.findData(self._npc.npc_class.value)
        if idx >= 0:
            self._class_combo.setCurrentIndex(idx)
        
        # Set gender combo
        idx = self._gender_combo.findData(self._npc.gender.value)
        if idx >= 0:
            self._gender_combo.setCurrentIndex(idx)
        
        self._age_spin.setValue(self._npc.age)
        self._fmf_file_edit.setText(self._npc.fmf_file)
    
    def _on_name_changed(self, text: str):
        self._npc.name = text
        if not text or not text.strip():
            self._name_validation.set_valid(False, "Name required")
        elif len(text) > 32:
            self._name_validation.set_valid(False, "Max 32 chars")
        else:
            self._name_validation.set_valid(True)
        self.data_changed.emit()
    
    def _on_data_changed(self):
        self._save_to_npc()
        self.data_changed.emit()
    
    def _on_browse_fmf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select FMF File", "", "FMF Files (*.fmf);;All Files (*)"
        )
        if file_path:
            self._fmf_file_edit.setText(file_path)
    
    def _save_to_npc(self):
        self._npc.name = self._name_edit.text()
        self._npc.description = self._description_edit.toPlainText()
        self._npc.comments = self._comments_edit.toPlainText()
        self._npc.npc_class = NpcClass(self._class_combo.currentData())
        self._npc.gender = Gender(self._gender_combo.currentData())
        self._npc.age = self._age_spin.value()
        self._npc.fmf_file = self._fmf_file_edit.text()
    
    def get_npc(self) -> Npc:
        self._save_to_npc()
        return self._npc
    
    def set_npc(self, npc: Npc):
        self._npc = npc
        self._load_data()


class AppearanceWidget(QWidget):
    """Widget for NPC appearance configuration"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Appearance Configuration")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {FalloutColors.PANEL_BORDER};
                background-color: {FalloutColors.CHARCOAL};
            }}
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Model Files Group
        model_group = QGroupBox("Model Files")
        model_layout = QFormLayout()
        
        self._fid_spin = QSpinBox()
        self._fid_spin.setRange(0, 999999)
        self._fid_spin.setSuffix(" (FRM ID)")
        model_layout.addRow("Base FID:", self._fid_spin)
        
        self._head_fid_spin = QSpinBox()
        self._head_fid_spin.setRange(0, 999999)
        model_layout.addRow("Head FID:", self._head_fid_spin)
        
        self._body_fid_spin = QSpinBox()
        self._body_fid_spin.setRange(0, 999999)
        model_layout.addRow("Body FID:", self._body_fid_spin)
        
        self._anim_code_edit = QLineEdit()
        self._anim_code_edit.setMaxLength(4)
        self._anim_code_edit.setPlaceholderText("e.g., hf")
        model_layout.addRow("Animation:", self._anim_code_edit)
        
        model_group.setLayout(model_layout)
        scroll_layout.addWidget(model_group)
        
        # Colors Group
        colors_group = QGroupBox("Colors")
        colors_layout = QFormLayout()
        
        self._skin_color_btn = QPushButton()
        self._skin_color_btn.setFixedSize(60, 25)
        self._skin_color_btn.clicked.connect(lambda: self._pick_color('skin'))
        colors_layout.addRow("Skin:", self._skin_color_btn)
        
        self._hair_color_btn = QPushButton()
        self._hair_color_btn.setFixedSize(60, 25)
        self._hair_color_btn.clicked.connect(lambda: self._pick_color('hair'))
        colors_layout.addRow("Hair:", self._hair_color_btn)
        
        self._primary_color_btn = QPushButton()
        self._primary_color_btn.setFixedSize(60, 25)
        self._primary_color_btn.clicked.connect(lambda: self._pick_color('primary'))
        colors_layout.addRow("Primary:", self._primary_color_btn)
        
        self._secondary_color_btn = QPushButton()
        self._secondary_color_btn.setFixedSize(60, 25)
        self._secondary_color_btn.clicked.connect(lambda: self._pick_color('secondary'))
        colors_layout.addRow("Secondary:", self._secondary_color_btn)
        
        colors_group.setLayout(colors_layout)
        scroll_layout.addWidget(colors_group)
        
        # Features Group
        features_group = QGroupBox("Features")
        features_layout = QFormLayout()
        
        self._hairstyle_combo = QComboBox()
        self._hairstyle_combo.addItems([
            "Default", "Bald", "Short", "Long", "Ponytail", "Mohawk", "Afro", "Braids", "Custom"
        ])
        features_layout.addRow("Hairstyle:", self._hairstyle_combo)
        
        self._facial_hair_combo = QComboBox()
        self._facial_hair_combo.addItems(["None", "Mustache", "Beard", "Goatee", "Moustache & Beard"])
        features_layout.addRow("Facial Hair:", self._facial_hair_combo)
        
        self._makeup_combo = QComboBox()
        self._makeup_combo.addItems(["None", "Light", "Heavy", "War Paint", "Scar"])
        features_layout.addRow("Makeup:", self._makeup_combo)
        
        self._scars_list = QListWidget()
        self._scars_list.setMaximumHeight(80)
        self._add_scar_btn = QPushButton("Add Scar")
        self._remove_scar_btn = QPushButton("Remove")
        scar_layout = QHBoxLayout()
        scar_layout.addWidget(self._add_scar_btn)
        scar_layout.addWidget(self._remove_scar_btn)
        features_layout.addRow("Scars:", self._scars_list)
        features_layout.addRow("", scar_layout)
        
        features_group.setLayout(features_layout)
        scroll_layout.addWidget(features_group)
        
        # Equipment Appearance Group
        equip_group = QGroupBox("Equipment Appearance")
        equip_layout = QFormLayout()
        
        self._armor_fid_spin = QSpinBox()
        self._armor_fid_spin.setRange(0, 999999)
        equip_layout.addRow("Armor FID:", self._armor_fid_spin)
        
        self._weapon_fid_spin = QSpinBox()
        self._weapon_fid_spin.setRange(0, 999999)
        equip_layout.addRow("Weapon FID:", self._weapon_fid_spin)
        
        equip_group.setLayout(equip_layout)
        scroll_layout.addWidget(equip_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Connect signals
        self._fid_spin.valueChanged.connect(self._on_data_changed)
        self._head_fid_spin.valueChanged.connect(self._on_data_changed)
        self._body_fid_spin.valueChanged.connect(self._on_data_changed)
        self._anim_code_edit.textChanged.connect(self._on_data_changed)
        self._hairstyle_combo.currentIndexChanged.connect(self._on_data_changed)
        self._facial_hair_combo.currentIndexChanged.connect(self._on_data_changed)
        self._makeup_combo.currentIndexChanged.connect(self._on_data_changed)
        self._armor_fid_spin.valueChanged.connect(self._on_data_changed)
        self._weapon_fid_spin.valueChanged.connect(self._on_data_changed)
        self._add_scar_btn.clicked.connect(self._add_scar)
        self._remove_scar_btn.clicked.connect(self._remove_scar)
    
    def _pick_color(self, color_type: str):
        color_map = {
            'skin': (self._npc.appearance.skin_color, lambda c: setattr(self._npc.appearance, 'skin_color', c)),
            'hair': (self._npc.appearance.hair_color, lambda c: setattr(self._npc.appearance, 'hair_color', c)),
            'primary': (self._npc.appearance.primary_color, lambda c: setattr(self._npc.appearance, 'primary_color', c)),
            'secondary': (self._npc.appearance.secondary_color, lambda c: setattr(self._npc.appearance, 'secondary_color', c)),
        }
        
        current_color, setter = color_map[color_type]
        color = QColor(current_color)
        picked = QColorDialog.getColor(color, self, f"Select {color_type.title()} Color")
        
        if picked.isValid():
            hex_color = picked.name()
            setter(hex_color)
            self._update_color_button(color_type, hex_color)
            self.data_changed.emit()
    
    def _update_color_button(self, color_type: str, color: str):
        btn_map = {
            'skin': self._skin_color_btn,
            'hair': self._hair_color_btn,
            'primary': self._primary_color_btn,
            'secondary': self._secondary_color_btn,
        }
        btn = btn_map[color_type]
        btn.setStyleSheet(f"background-color: {color}; border: 1px solid {FalloutColors.PANEL_BORDER};")
    
    def _add_scar(self):
        scar_types = ["Forehead", "Cheek Left", "Cheek Right", "Nose", "Chin", "Eye"]
        item, ok = QInputDialog.getItem(self, "Add Scar", "Select scar location:", scar_types)
        if ok:
            self._scars_list.addItem(item)
            self._npc.appearance.scars.append(item)
            self.data_changed.emit()
    
    def _remove_scar(self):
        current = self._scars_list.currentItem()
        if current:
            self._scars_list.takeItem(self._scars_list.row(current))
            self._npc.appearance.scars.remove(current.text())
            self.data_changed.emit()
    
    def _on_data_changed(self):
        self._save_to_npc()
        self.data_changed.emit()
    
    def _load_data(self):
        app = self._npc.appearance
        self._fid_spin.setValue(app.fid)
        self._head_fid_spin.setValue(app.head_fid)
        self._body_fid_spin.setValue(app.body_fid)
        self._anim_code_edit.setText(app.animation_code)
        
        self._update_color_button('skin', app.skin_color)
        self._update_color_button('hair', app.hair_color)
        self._update_color_button('primary', app.primary_color)
        self._update_color_button('secondary', app.secondary_color)
        
        idx = self._hairstyle_combo.findText(app.hairstyle)
        if idx >= 0:
            self._hairstyle_combo.setCurrentIndex(idx)
        
        idx = self._facial_hair_combo.findText(app.facial_hair)
        if idx >= 0:
            self._facial_hair_combo.setCurrentIndex(idx)
        
        idx = self._makeup_combo.findText(app.makeup)
        if idx >= 0:
            self._makeup_combo.setCurrentIndex(idx)
        
        self._scars_list.clear()
        for scar in app.scars:
            self._scars_list.addItem(scar)
        
        self._armor_fid_spin.setValue(app.armor_fid)
        self._weapon_fid_spin.setValue(app.weapon_fid)
    
    def _save_to_npc(self):
        self._npc.appearance.fid = self._fid_spin.value()
        self._npc.appearance.head_fid = self._head_fid_spin.value()
        self._npc.appearance.body_fid = self._body_fid_spin.value()
        self._npc.appearance.animation_code = self._anim_code_edit.text()
        self._npc.appearance.hairstyle = self._hairstyle_combo.currentText()
        self._npc.appearance.facial_hair = self._facial_hair_combo.currentText()
        self._npc.appearance.makeup = self._makeup_combo.currentText()
        self._npc.appearance.armor_fid = self._armor_fid_spin.value()
        self._npc.appearance.weapon_fid = self._weapon_fid_spin.value()
    
    def get_npc(self) -> Npc:
        self._save_to_npc()
        return self._npc


class AttributesWidget(QWidget):
    """Widget for NPC attributes (SPECIAL and derived stats)"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Attributes & Statistics")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # SPECIAL Stats Group
        special_group = QGroupBox("SPECIAL Stats")
        special_layout = QGridLayout()
        special_layout.setSpacing(8)
        
        special_labels = [
            ("Strength", "S"),
            ("Perception", "P"),
            ("Endurance", "E"),
            ("Charisma", "C"),
            ("Intelligence", "I"),
            ("Agility", "A"),
            ("Luck", "L")
        ]
        
        self._special_spins = {}
        
        for row, (name, abbrev) in enumerate(special_labels):
            label = QLabel(f"{name} ({abbrev}):")
            label.setStyleSheet(f"color: {FalloutColors.TEXT_NORMAL};")
            spin = QSpinBox()
            spin.setRange(1, 10)
            spin.setFixedWidth(80)
            self._special_spins[name.lower()] = spin
            special_layout.addWidget(label, row, 0)
            special_layout.addWidget(spin, row, 1)
        
        self._special_total_label = QLabel("Total: 35")
        self._special_total_label.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-weight: bold;")
        special_layout.addWidget(self._special_total_label, 7, 0, 1, 2)
        
        special_group.setLayout(special_layout)
        scroll_layout.addWidget(special_group)
        
        # Derived Stats Group
        derived_group = QGroupBox("Derived Stats")
        derived_layout = QFormLayout()
        
        self._hp_spin = QSpinBox()
        self._hp_spin.setRange(0, 9999)
        derived_layout.addRow("Current HP:", self._hp_spin)
        
        self._max_hp_spin = QSpinBox()
        self._max_hp_spin.setRange(1, 9999)
        derived_layout.addRow("Max HP:", self._max_hp_spin)
        
        self._ap_spin = QSpinBox()
        self._ap_spin.setRange(0, 100)
        derived_layout.addRow("Action Points:", self._ap_spin)
        
        self._ac_spin = QSpinBox()
        self._ac_spin.setRange(-100, 100)
        derived_layout.addRow("Armor Class:", self._ac_spin)
        
        self._melee_spin = QSpinBox()
        self._melee_spin.setRange(-100, 100)
        derived_layout.addRow("Melee Damage:", self._melee_spin)
        
        self._sequence_spin = QSpinBox()
        self._sequence_spin.setRange(0, 100)
        derived_layout.addRow("Sequence:", self._sequence_spin)
        
        self._heal_rate_spin = QSpinBox()
        self._heal_rate_spin.setRange(0, 100)
        derived_layout.addRow("Healing Rate:", self._heal_rate_spin)
        
        self._crit_chance_spin = QSpinBox()
        self._crit_chance_spin.setRange(0, 100)
        self._crit_chance_spin.setSuffix("%")
        derived_layout.addRow("Critical Chance:", self._crit_chance_spin)
        
        derived_group.setLayout(derived_layout)
        scroll_layout.addWidget(derived_group)
        
        # Resistances Group
        resist_group = QGroupBox("Resistances")
        resist_layout = QFormLayout()
        
        self._rad_resist_spin = QSpinBox()
        self._rad_resist_spin.setRange(0, 100)
        self._rad_resist_spin.setSuffix("%")
        resist_layout.addRow("Radiation:", self._rad_resist_spin)
        
        self._pois_resist_spin = QSpinBox()
        self._pois_resist_spin.setRange(0, 100)
        self._pois_resist_spin.setSuffix("%")
        resist_layout.addRow("Poison:", self._pois_resist_spin)
        
        resist_group.setLayout(resist_layout)
        scroll_layout.addWidget(resist_group)
        
        # Damage Thresholds Group
        dt_group = QGroupBox("Damage Thresholds")
        dt_layout = QGridLayout()
        
        dt_types = [
            "Normal", "Laser", "Fire", "Plasma", "Electrical", "Explosive"
        ]
        self._dt_spins = {}
        
        for col, dtype in enumerate(dt_types):
            label = QLabel(f"{dtype}:")
            spin = QSpinBox()
            spin.setRange(0, 999)
            self._dt_spins[dtype.lower()] = spin
            dt_layout.addWidget(label, 0, col * 2)
            dt_layout.addWidget(spin, 0, col * 2 + 1)
        
        dt_group.setLayout(dt_layout)
        scroll_layout.addWidget(dt_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Connect signals
        for spin in self._special_spins.values():
            spin.valueChanged.connect(self._on_special_changed)
        
        self._hp_spin.valueChanged.connect(self._on_data_changed)
        self._max_hp_spin.valueChanged.connect(self._on_data_changed)
        self._ap_spin.valueChanged.connect(self._on_data_changed)
        self._ac_spin.valueChanged.connect(self._on_data_changed)
        self._melee_spin.valueChanged.connect(self._on_data_changed)
        self._sequence_spin.valueChanged.connect(self._on_data_changed)
        self._heal_rate_spin.valueChanged.connect(self._on_data_changed)
        self._crit_chance_spin.valueChanged.connect(self._on_data_changed)
        self._rad_resist_spin.valueChanged.connect(self._on_data_changed)
        self._pois_resist_spin.valueChanged.connect(self._on_data_changed)
        
        for spin in self._dt_spins.values():
            spin.valueChanged.connect(self._on_data_changed)
    
    def _on_special_changed(self):
        total = 0
        for name, spin in self._special_spins.items():
            value = spin.value()
            total += value
            setattr(self._npc.attributes, name, value)
        
        self._special_total_label.setText(f"Total: {total}")
        
        # Visual feedback if not 40 (standard starting total)
        if total != 40:
            self._special_total_label.setStyleSheet(
                f"color: {FalloutColors.WARNING_YELLOW}; font-weight: bold;"
            )
        else:
            self._special_total_label.setStyleSheet(
                f"color: {FalloutColors.TERMINAL_GREEN}; font-weight: bold;"
            )
        
        self.data_changed.emit()
    
    def _on_data_changed(self):
        self._save_to_npc()
        self.data_changed.emit()
    
    def _load_data(self):
        attr = self._npc.attributes
        
        self._special_spins["strength"].setValue(attr.strength)
        self._special_spins["perception"].setValue(attr.perception)
        self._special_spins["endurance"].setValue(attr.endurance)
        self._special_spins["charisma"].setValue(attr.charisma)
        self._special_spins["intelligence"].setValue(attr.intelligence)
        self._special_spins["agility"].setValue(attr.agility)
        self._special_spins["luck"].setValue(attr.luck)
        
        self._hp_spin.setValue(attr.hit_points)
        self._max_hp_spin.setValue(attr.max_hit_points)
        self._ap_spin.setValue(attr.action_points)
        self._ac_spin.setValue(attr.armor_class)
        self._melee_spin.setValue(attr.melee_damage)
        self._sequence_spin.setValue(attr.sequence)
        self._heal_rate_spin.setValue(attr.healing_rate)
        self._crit_chance_spin.setValue(attr.critical_chance)
        
        self._rad_resist_spin.setValue(attr.radiation_resistance)
        self._pois_resist_spin.setValue(attr.poison_resistance)
        
        self._dt_spins["normal"].setValue(attr.dt_normal)
        self._dt_spins["laser"].setValue(attr.dt_laser)
        self._dt_spins["fire"].setValue(attr.dt_fire)
        self._dt_spins["plasma"].setValue(attr.dt_plasma)
        self._dt_spins["electrical"].setValue(attr.dt_electrical)
        self._dt_spins["explosive"].setValue(attr.dt_explosive)
    
    def _save_to_npc(self):
        attr = self._npc.attributes
        
        attr.strength = self._special_spins["strength"].value()
        attr.perception = self._special_spins["perception"].value()
        attr.endurance = self._special_spins["endurance"].value()
        attr.charisma = self._special_spins["charisma"].value()
        attr.intelligence = self._special_spins["intelligence"].value()
        attr.agility = self._special_spins["agility"].value()
        attr.luck = self._special_spins["luck"].value()
        
        attr.hit_points = self._hp_spin.value()
        attr.max_hit_points = self._max_hp_spin.value()
        attr.action_points = self._ap_spin.value()
        attr.armor_class = self._ac_spin.value()
        attr.melee_damage = self._melee_spin.value()
        attr.sequence = self._sequence_spin.value()
        attr.healing_rate = self._heal_rate_spin.value()
        attr.critical_chance = self._crit_chance_spin.value()
        
        attr.radiation_resistance = self._rad_resist_spin.value()
        attr.poison_resistance = self._pois_resist_spin.value()
        
        attr.dt_normal = self._dt_spins["normal"].value()
        attr.dt_laser = self._dt_spins["laser"].value()
        attr.dt_fire = self._dt_spins["fire"].value()
        attr.dt_plasma = self._dt_spins["plasma"].value()
        attr.dt_electrical = self._dt_spins["electrical"].value()
        attr.dt_explosive = self._dt_spins["explosive"].value()
    
    def get_npc(self) -> Npc:
        self._save_to_npc()
        return self._npc


class SkillsWidget(QWidget):
    """Widget for NPC skill configuration"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Skills Configuration")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        # Info label
        info = QLabel("Configure NPC skill values (base + bonus = total)")
        info.setStyleSheet(f"color: {FalloutColors.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(info)
        
        # Skills table
        self._skills_table = QTableWidget()
        self._skills_table.setColumnCount(4)
        self._skills_table.setHorizontalHeaderLabels(["Skill", "Base", "Bonus", "Total"])
        self._skills_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Populate with skills
        skills = [s for s in Skill if s.value in range(20)]
        self._skills_table.setRowCount(len(skills))
        
        self._skill_spins = {}
        
        for row, skill in enumerate(skills):
            # Skill name
            name_item = QTableWidgetItem(Skill.get_name(skill.value))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._skills_table.setItem(row, 0, name_item)
            
            # Base value spin
            base_spin = QSpinBox()
            base_spin.setRange(0, 300)
            base_spin.setValue(0)
            self._skills_table.setCellWidget(row, 1, base_spin)
            self._skill_spins[skill] = {'base': base_spin}
            
            # Bonus value spin
            bonus_spin = QSpinBox()
            bonus_spin.setRange(0, 100)
            bonus_spin.setValue(0)
            self._skills_table.setCellWidget(row, 2, bonus_spin)
            self._skill_spins[skill]['bonus'] = bonus_spin
            
            # Total label
            total_label = QLabel("0")
            total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            total_label.setStyleSheet(f"color: {FalloutColors.TERMINAL_GREEN}; font-weight: bold;")
            self._skills_table.setCellWidget(row, 3, total_label)
            self._skill_spins[skill]['total'] = total_label
        
        self._skills_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {FalloutColors.CHARCOAL};
                color: {FalloutColors.TEXT_NORMAL};
                gridline-color: {FalloutColors.PANEL_BORDER};
                border: 1px solid {FalloutColors.PANEL_BORDER};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {FalloutColors.DARK_OLIVE_GREEN};
                color: {FalloutColors.TEXT_NORMAL};
                padding: 5px;
                border: 1px solid {FalloutColors.PANEL_BORDER};
            }}
        """)
        
        layout.addWidget(self._skills_table)
        
        # Connect signals
        for skill, widgets in self._skill_spins.items():
            widgets['base'].valueChanged.connect(lambda v, s=skill: self._on_skill_changed(s))
            widgets['bonus'].valueChanged.connect(lambda v, s=skill: self._on_skill_changed(s))
    
    def _on_skill_changed(self, skill: Skill):
        widgets = self._skill_spins[skill]
        base = widgets['base'].value()
        bonus = widgets['bonus'].value()
        total = base + bonus
        widgets['total'].setText(str(total))
        
        # Update NPC skill
        for sv in self._npc.skills:
            if sv.skill == skill:
                sv.value = base
                sv.bonus = bonus
                break
        
        self.data_changed.emit()
    
    def _load_data(self):
        for skill, widgets in self._skill_spins.items():
            for sv in self._npc.skills:
                if sv.skill == skill:
                    widgets['base'].setValue(sv.value)
                    widgets['bonus'].setValue(sv.bonus)
                    widgets['total'].setText(str(sv.total))
                    break
    
    def get_npc(self) -> Npc:
        return self._npc


class InventoryWidget(QWidget):
    """Widget for NPC inventory management"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Inventory Management")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self._add_btn = QPushButton("Add Item")
        self._add_btn.setIcon(QIcon.fromTheme("list-add"))
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setIcon(QIcon.fromTheme("list-remove"))
        self._edit_btn = QPushButton("Edit")
        
        toolbar.addWidget(self._add_btn)
        toolbar.addWidget(self._edit_btn)
        toolbar.addWidget(self._remove_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Inventory table
        self._inventory_table = QTableWidget()
        self._inventory_table.setColumnCount(6)
        self._inventory_table.setHorizontalHeaderLabels([
            "PID", "Item Name", "Qty", "Condition", "Charges", "Equipped"
        ])
        self._inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self._inventory_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {FalloutColors.CHARCOAL};
                color: {FalloutColors.TEXT_NORMAL};
                gridline-color: {FalloutColors.PANEL_BORDER};
            }}
            QHeaderView::section {{
                background-color: {FalloutColors.DARK_OLIVE_GREEN};
                color: {FalloutColors.TEXT_NORMAL};
                padding: 5px;
            }}
        """)
        
        layout.addWidget(self._inventory_table)
        
        # Connect signals
        self._add_btn.clicked.connect(self._add_item)
        self._remove_btn.clicked.connect(self._remove_item)
        self._edit_btn.clicked.connect(self._edit_item)
    
    def _add_item(self):
        dialog = InventoryItemDialog(self)
        if dialog.exec():
            item = dialog.get_item()
            self._npc.inventory.append(item)
            self._load_data()
            self.data_changed.emit()
    
    def _remove_item(self):
        current_row = self._inventory_table.currentRow()
        if current_row >= 0:
            self._npc.inventory.pop(current_row)
            self._load_data()
            self.data_changed.emit()
    
    def _edit_item(self):
        current_row = self._inventory_table.currentRow()
        if current_row >= 0:
            item = self._npc.inventory[current_row]
            dialog = InventoryItemDialog(self, item)
            if dialog.exec():
                self._npc.inventory[current_row] = dialog.get_item()
                self._load_data()
                self.data_changed.emit()
    
    def _load_data(self):
        self._inventory_table.setRowCount(len(self._npc.inventory))
        
        for row, item in enumerate(self._npc.inventory):
            self._inventory_table.setItem(row, 0, QTableWidgetItem(str(item.pid)))
            self._inventory_table.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_item = QTableWidgetItem(item.item_name)
            self._inventory_table.setItem(row, 1, name_item)
            
            qty_item = QTableWidgetItem(str(item.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._inventory_table.setItem(row, 2, qty_item)
            
            cond_item = QTableWidgetItem(f"{item.condition}%")
            cond_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._inventory_table.setItem(row, 3, cond_item)
            
            charges_item = QTableWidgetItem(str(item.charges))
            charges_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._inventory_table.setItem(row, 4, charges_item)
            
            equipped_item = QTableWidgetItem("✓" if item.is_equipped else "")
            equipped_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if item.is_equipped:
                equipped_item.setBackground(QColor(FalloutColors.DARK_OLIVE_GREEN))
            self._inventory_table.setItem(row, 5, equipped_item)
    
    def get_npc(self) -> Npc:
        return self._npc


class InventoryItemDialog(QDialog):
    """Dialog for editing inventory items"""
    
    def __init__(self, parent=None, item: Optional[InventoryItem] = None):
        super().__init__(parent)
        self._item = item or InventoryItem()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        self.setWindowTitle("Edit Inventory Item")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self._pid_spin = QSpinBox()
        self._pid_spin.setRange(0, 999999)
        layout.addRow("Proto ID (PID):", self._pid_spin)
        
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Item name...")
        layout.addRow("Item Name:", self._name_edit)
        
        self._quantity_spin = QSpinBox()
        self._quantity_spin.setRange(1, 9999)
        layout.addRow("Quantity:", self._quantity_spin)
        
        self._condition_spin = QSpinBox()
        self._condition_spin.setRange(0, 100)
        self._condition_spin.setSuffix("%")
        layout.addRow("Condition:", self._condition_spin)
        
        self._charges_spin = QSpinBox()
        self._charges_spin.setRange(0, 999)
        layout.addRow("Charges:", self._charges_spin)
        
        self._equipped_check = QCheckBox("Equipped")
        layout.addRow("", self._equipped_check)
        
        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow("", btn_layout)
    
    def _load_data(self):
        self._pid_spin.setValue(self._item.pid)
        self._name_edit.setText(self._item.item_name)
        self._quantity_spin.setValue(self._item.quantity)
        self._condition_spin.setValue(self._item.condition)
        self._charges_spin.setValue(self._item.charges)
        self._equipped_check.setChecked(self._item.is_equipped)
    
    def get_item(self) -> InventoryItem:
        self._item.pid = self._pid_spin.value()
        self._item.item_name = self._name_edit.text()
        self._item.quantity = self._quantity_spin.value()
        self._item.condition = self._condition_spin.value()
        self._item.charges = self._charges_spin.value()
        self._item.is_equipped = self._equipped_check.isChecked()
        return self._item


class BehaviorWidget(QWidget):
    """Widget for NPC behavior patterns"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Behavior Patterns")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Personality Group
        personality_group = QGroupBox("Personality")
        personality_layout = QFormLayout()
        
        # Aggression slider
        aggro_layout = QHBoxLayout()
        self._aggression_slider = QSlider(Qt.Orientation.Horizontal)
        self._aggression_slider.setRange(0, 100)
        self._aggression_value = QLabel("0")
        aggro_layout.addWidget(self._aggression_slider)
        aggro_layout.addWidget(self._aggression_value)
        personality_layout.addRow("Aggression:", aggro_layout)
        
        # Cowardice slider
        coward_layout = QHBoxLayout()
        self._cowardice_slider = QSlider(Qt.Orientation.Horizontal)
        self._cowardice_slider.setRange(0, 100)
        self._cowardice_value = QLabel("0")
        coward_layout.addWidget(self._cowardice_slider)
        coward_layout.addWidget(self._cowardice_value)
        personality_layout.addRow("Cowardice:", coward_layout)
        
        # Enthusiasm slider
        enth_layout = QHBoxLayout()
        self._enthusiasm_slider = QSlider(Qt.Orientation.Horizontal)
        self._enthusiasm_slider.setRange(0, 100)
        self._enthusiasm_value = QLabel("50")
        enth_layout.addWidget(self._enthusiasm_slider)
        enth_layout.addWidget(self._enthusiasm_value)
        personality_layout.addRow("Enthusiasm:", enth_layout)
        
        personality_group.setLayout(personality_layout)
        scroll_layout.addWidget(personality_group)
        
        # AI Group
        ai_group = QGroupBox("AI Configuration")
        ai_layout = QFormLayout()
        
        self._ai_number_spin = QSpinBox()
        self._ai_number_spin.setRange(0, 9999)
        ai_layout.addRow("AI Number:", self._ai_number_spin)
        
        self._ai_package_combo = QComboBox()
        for pkg in AiPackage:
            self._ai_package_combo.addItem(pkg.name.replace('_', ' ').title(), pkg.value)
        ai_layout.addRow("AI Package:", self._ai_package_combo)
        
        self._script_id_spin = QSpinBox()
        self._script_id_spin.setRange(0, 99999)
        ai_layout.addRow("Script ID:", self._script_id_spin)
        
        self._script_name_edit = QLineEdit()
        self._script_name_edit.setPlaceholderText("Script procedure name...")
        ai_layout.addRow("Script Name:", self._script_name_edit)
        
        ai_group.setLayout(ai_layout)
        scroll_layout.addWidget(ai_group)
        
        # Movement Group
        movement_group = QGroupBox("Movement")
        movement_layout = QFormLayout()
        
        self._movement_combo = QComboBox()
        self._movement_combo.addItems(["Walk", "Run", "Swim", "Fly"])
        movement_layout.addRow("Movement Type:", self._movement_combo)
        
        self._run_distance_spin = QSpinBox()
        self._run_distance_spin.setRange(0, 100)
        movement_layout.addRow("Run Distance:", self._run_distance_spin)
        
        movement_group.setLayout(movement_layout)
        scroll_layout.addWidget(movement_group)
        
        # Combat Group
        combat_group = QGroupBox("Combat")
        combat_layout = QFormLayout()
        
        self._combat_style_combo = QComboBox()
        self._combat_style_combo.addItems([
            "Default", "Aggressive", "Defensive", "Melee", "Ranged", "Stealth"
        ])
        combat_layout.addRow("Combat Style:", self._combat_style_combo)
        
        self._primary_weapon_edit = QLineEdit()
        self._primary_weapon_edit.setPlaceholderText("Primary weapon name...")
        combat_layout.addRow("Primary Weapon:", self._primary_weapon_edit)
        
        self._secondary_weapon_edit = QLineEdit()
        self._secondary_weapon_edit.setPlaceholderText("Secondary weapon name...")
        combat_layout.addRow("Secondary Weapon:", self._secondary_weapon_edit)
        
        combat_group.setLayout(combat_layout)
        scroll_layout.addWidget(combat_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Connect signals
        self._aggression_slider.valueChanged.connect(self._on_aggression_changed)
        self._cowardice_slider.valueChanged.connect(self._on_cowardice_changed)
        self._enthusiasm_slider.valueChanged.connect(self._on_enthusiasm_changed)
        
        self._ai_number_spin.valueChanged.connect(self._on_data_changed)
        self._ai_package_combo.currentIndexChanged.connect(self._on_data_changed)
        self._script_id_spin.valueChanged.connect(self._on_data_changed)
        self._script_name_edit.textChanged.connect(self._on_data_changed)
        
        self._movement_combo.currentIndexChanged.connect(self._on_data_changed)
        self._run_distance_spin.valueChanged.connect(self._on_data_changed)
        
        self._combat_style_combo.currentIndexChanged.connect(self._on_data_changed)
        self._primary_weapon_edit.textChanged.connect(self._on_data_changed)
        self._secondary_weapon_edit.textChanged.connect(self._on_data_changed)
    
    def _on_aggression_changed(self, value: int):
        self._aggression_value.setText(str(value))
        self._npc.behavior.aggression = value
        self._update_personality_color(self._aggression_value, value)
        self.data_changed.emit()
    
    def _on_cowardice_changed(self, value: int):
        self._cowardice_value.setText(str(value))
        self._npc.behavior.cowardice = value
        self._update_personality_color(self._cowardice_value, value)
        self.data_changed.emit()
    
    def _on_enthusiasm_changed(self, value: int):
        self._enthusiasm_value.setText(str(value))
        self._npc.behavior.enthusiasm = value
        self._update_personality_color(self._enthusiasm_value, value)
        self.data_changed.emit()
    
    def _update_personality_color(self, label: QLabel, value: int):
        if value < 33:
            label.setStyleSheet(f"color: {FalloutColors.TERMINAL_GREEN};")
        elif value < 66:
            label.setStyleSheet(f"color: {FalloutColors.WARNING_YELLOW};")
        else:
            label.setStyleSheet(f"color: {FalloutColors.STATUS_RED};")
    
    def _on_data_changed(self):
        self._save_to_npc()
        self.data_changed.emit()
    
    def _load_data(self):
        bhv = self._npc.behavior
        
        self._aggression_slider.setValue(bhv.aggression)
        self._cowardice_slider.setValue(bhv.cowardice)
        self._enthusiasm_slider.setValue(bhv.enthusiasm)
        
        self._ai_number_spin.setValue(bhv.ai_number)
        idx = self._ai_package_combo.findData(bhv.ai_package.value)
        if idx >= 0:
            self._ai_package_combo.setCurrentIndex(idx)
        self._script_id_spin.setValue(bhv.script_id)
        self._script_name_edit.setText(bhv.script_name)
        
        idx = self._movement_combo.findText(bhv.movement_type)
        if idx >= 0:
            self._movement_combo.setCurrentIndex(idx)
        self._run_distance_spin.setValue(bhv.run_distance)
        
        idx = self._combat_style_combo.findText(bhv.combat_style)
        if idx >= 0:
            self._combat_style_combo.setCurrentIndex(idx)
        self._primary_weapon_edit.setText(bhv.primary_weapon)
        self._secondary_weapon_edit.setText(bhv.secondary_weapon)
    
    def _save_to_npc(self):
        bhv = self._npc.behavior
        bhv.aggression = self._aggression_slider.value()
        bhv.cowardice = self._cowardice_slider.value()
        bhv.enthusiasm = self._enthusiasm_slider.value()
        
        bhv.ai_number = self._ai_number_spin.value()
        bhv.ai_package = AiPackage(self._ai_package_combo.currentData())
        bhv.script_id = self._script_id_spin.value()
        bhv.script_name = self._script_name_edit.text()
        
        bhv.movement_type = self._movement_combo.currentText()
        bhv.run_distance = self._run_distance_spin.value()
        
        bhv.combat_style = self._combat_style_combo.currentText()
        bhv.primary_weapon = self._primary_weapon_edit.text()
        bhv.secondary_weapon = self._secondary_weapon_edit.text()
    
    def get_npc(self) -> Npc:
        self._save_to_npc()
        return self._npc


class AiSettingsWidget(QWidget):
    """Widget for advanced AI behavior settings"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("AI Behavior Settings")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # General AI Group
        general_group = QGroupBox("General AI")
        general_layout = QFormLayout()
        
        self._brain_type_combo = QComboBox()
        self._brain_type_combo.addItems([
            "Default", "Guard", "Follower", "Scavenger", "Trader", "Feral"
        ])
        general_layout.addRow("Brain Type:", self._brain_type_combo)
        
        self._packet_combo = QComboBox()
        for pkg in AiPackage:
            self._packet_combo.addItem(pkg.name.replace('_', ' ').title(), pkg.value)
        general_layout.addRow("Packet Type:", self._packet_combo)
        
        self._team_id_spin = QSpinBox()
        self._team_id_spin.setRange(0, 255)
        general_layout.addRow("Team ID:", self._team_id_spin)
        
        self._ai_group_spin = QSpinBox()
        self._ai_group_spin.setRange(0, 255)
        general_layout.addRow("AI Group:", self._ai_group_spin)
        
        general_group.setLayout(general_layout)
        scroll_layout.addWidget(general_group)
        
        # Perception Group
        perception_group = QGroupBox("Perception")
        perception_layout = QFormLayout()
        
        self._perception_spin = QSpinBox()
        self._perception_spin.setRange(0, 100)
        perception_layout.addRow("Perception Radius:", self._perception_spin)
        
        self._vision_spin = QSpinBox()
        self._vision_spin.setRange(0, 100)
        perception_layout.addRow("Vision Range:", self._vision_spin)
        
        self._hearing_spin = QSpinBox()
        self._hearing_spin.setRange(0, 100)
        perception_layout.addRow("Hearing Range:", self._hearing_spin)
        
        perception_group.setLayout(perception_layout)
        scroll_layout.addWidget(perception_group)
        
        # Combat Group
        combat_group = QGroupBox("Combat")
        combat_layout = QFormLayout()
        
        self._attack_rate_spin = QSpinBox()
        self._attack_rate_spin.setRange(0, 10)
        combat_layout.addRow("Attack Rate:", self._attack_rate_spin)
        
        self._min_hit_spin = QSpinBox()
        self._min_hit_spin.setRange(0, 100)
        self._min_hit_spin.setSuffix("%")
        combat_layout.addRow("Min Hit Chance:", self._min_hit_spin)
        
        self._max_dist_spin = QSpinBox()
        self._max_dist_spin.setRange(0, 100)
        combat_layout.addRow("Max Distance:", self._max_dist_spin)
        
        self._min_dist_spin = QSpinBox()
        self._min_dist_spin.setRange(0, 100)
        combat_layout.addRow("Min Distance:", self._min_dist_spin)
        
        combat_group.setLayout(combat_layout)
        scroll_layout.addWidget(combat_group)
        
        # Movement Group
        movement_group = QGroupBox("Movement")
        movement_layout = QFormLayout()
        
        self._wander_spin = QSpinBox()
        self._wander_spin.setRange(0, 50)
        movement_layout.addRow("Wander Radius:", self._wander_spin)
        
        self._walk_speed_spin = QDoubleSpinBox()
        self._walk_speed_spin.setRange(0.1, 10.0)
        self._walk_speed_spin.setSingleStep(0.1)
        movement_layout.addRow("Walk Speed:", self._walk_speed_spin)
        
        self._run_speed_spin = QDoubleSpinBox()
        self._run_speed_spin.setRange(0.1, 20.0)
        self._run_speed_spin.setSingleStep(0.1)
        movement_layout.addRow("Run Speed:", self._run_speed_spin)
        
        movement_group.setLayout(movement_layout)
        scroll_layout.addWidget(movement_group)
        
        # Special Behaviors Group
        special_group = QGroupBox("Special Behaviors")
        special_layout = QVBoxLayout()
        
        self._critical_check = QCheckBox("Critical NPC (cannot be killed)")
        special_layout.addWidget(self._critical_check)
        
        self._loot_check = QCheckBox("Can Loot Bodies")
        special_layout.addWidget(self._loot_check)
        
        self._help_check = QCheckBox("Can Call for Help")
        special_layout.addWidget(self._help_check)
        
        self._help_radius_spin = QSpinBox()
        self._help_radius_spin.setRange(0, 50)
        help_layout = QHBoxLayout()
        help_layout.addWidget(self._help_check)
        help_layout.addWidget(QLabel("Radius:"))
        help_layout.addWidget(self._help_radius_spin)
        special_layout.addLayout(help_layout)
        
        self._fear_spin = QSpinBox()
        self._fear_spin.setRange(0, 100)
        fear_layout = QHBoxLayout()
        fear_layout.addWidget(QLabel("Fear Trigger:"))
        fear_layout.addWidget(self._fear_spin)
        special_layout.addLayout(fear_layout)
        
        special_group.setLayout(special_layout)
        scroll_layout.addWidget(special_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Connect signals for combo boxes (use currentIndexChanged)
        self._brain_type_combo.currentIndexChanged.connect(self._on_data_changed)
        self._packet_combo.currentIndexChanged.connect(self._on_data_changed)
        
        # Connect signals for spin boxes (use valueChanged)
        for widget in [self._team_id_spin, self._ai_group_spin, self._perception_spin,
                       self._vision_spin, self._hearing_spin, self._attack_rate_spin,
                       self._min_hit_spin, self._max_dist_spin, self._min_dist_spin,
                       self._wander_spin, self._walk_speed_spin, self._run_speed_spin]:
            widget.valueChanged.connect(self._on_data_changed)
        
        for widget in [self._critical_check, self._loot_check, self._help_check]:
            widget.stateChanged.connect(self._on_data_changed)
    
    def _on_data_changed(self):
        self._save_to_npc()
        self.data_changed.emit()
    
    def _load_data(self):
        ai = self._npc.ai_settings
        
        idx = self._brain_type_combo.findText(ai.brain_type)
        if idx >= 0:
            self._brain_type_combo.setCurrentIndex(idx)
        
        idx = self._packet_combo.findData(ai.packet_type.value)
        if idx >= 0:
            self._packet_combo.setCurrentIndex(idx)
        
        self._team_id_spin.setValue(ai.team_id)
        self._ai_group_spin.setValue(ai.ai_group)
        
        self._perception_spin.setValue(ai.perception_radius)
        self._vision_spin.setValue(ai.vision_range)
        self._hearing_spin.setValue(ai.hearing_range)
        
        self._attack_rate_spin.setValue(ai.attack_rate)
        self._min_hit_spin.setValue(ai.min_hit_chance)
        self._max_dist_spin.setValue(ai.max_distance)
        self._min_dist_spin.setValue(ai.min_distance)
        
        self._wander_spin.setValue(ai.wander_radius)
        self._walk_speed_spin.setValue(ai.walk_speed)
        self._run_speed_spin.setValue(ai.run_speed)
        
        self._critical_check.setChecked(ai.is_critical)
        self._loot_check.setChecked(ai.can_loot)
        self._help_check.setChecked(ai.can_call_help)
        self._help_radius_spin.setValue(ai.help_radius)
        self._fear_spin.setValue(ai.fear_trigger)
    
    def _save_to_npc(self):
        ai = self._npc.ai_settings
        
        ai.brain_type = self._brain_type_combo.currentText()
        ai.packet_type = AiPackage(self._packet_combo.currentData())
        ai.team_id = self._team_id_spin.value()
        ai.ai_group = self._ai_group_spin.value()
        
        ai.perception_radius = self._perception_spin.value()
        ai.vision_range = self._vision_spin.value()
        ai.hearing_range = self._hearing_spin.value()
        
        ai.attack_rate = self._attack_rate_spin.value()
        ai.min_hit_chance = self._min_hit_spin.value()
        ai.max_distance = self._max_dist_spin.value()
        ai.min_distance = self._min_dist_spin.value()
        
        ai.wander_radius = self._wander_spin.value()
        ai.walk_speed = self._walk_speed_spin.value()
        ai.run_speed = self._run_speed_spin.value()
        
        ai.is_critical = self._critical_check.isChecked()
        ai.can_loot = self._loot_check.isChecked()
        ai.can_call_help = self._help_check.isChecked()
        ai.help_radius = self._help_radius_spin.value()
        ai.fear_trigger = self._fear_spin.value()
    
    def get_npc(self) -> Npc:
        self._save_to_npc()
        return self._npc


class RelationshipWidget(QWidget):
    """Widget for NPC relationship parameters"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Relationship Parameters")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Player Relationship Group
        player_group = QGroupBox("Player Relationship")
        player_layout = QFormLayout()
        
        self._relation_combo = QComboBox()
        for rel_type in RelationshipType:
            self._relation_combo.addItem(rel_type.name.replace('_', ' ').title(), rel_type.value)
        player_layout.addRow("Relation Type:", self._relation_combo)
        
        self._relation_mod_spin = QSpinBox()
        self._relation_mod_spin.setRange(-100, 100)
        relation_layout = QHBoxLayout()
        relation_layout.addWidget(self._relation_mod_spin)
        self._relation_bar = QProgressBar()
        self._relation_bar.setRange(-100, 100)
        self._relation_bar.setValue(0)
        self._relation_bar.setFixedHeight(15)
        relation_layout.addWidget(self._relation_bar)
        player_layout.addRow("Modifier:", relation_layout)
        
        player_group.setLayout(player_layout)
        scroll_layout.addWidget(player_group)
        
        # Faction Group
        faction_group = QGroupBox("Faction")
        faction_layout = QFormLayout()
        
        self._faction_id_spin = QSpinBox()
        self._faction_id_spin.setRange(0, 9999)
        faction_layout.addRow("Faction ID:", self._faction_id_spin)
        
        self._faction_name_edit = QLineEdit()
        self._faction_name_edit.setPlaceholderText("Faction name...")
        faction_layout.addRow("Faction Name:", self._faction_name_edit)
        
        self._faction_standing_spin = QSpinBox()
        self._faction_standing_spin.setRange(-100, 100)
        faction_layout.addRow("Standing:", self._faction_standing_spin)
        
        faction_group.setLayout(faction_layout)
        scroll_layout.addWidget(faction_group)
        
        # Reputation & Karma Group
        rep_karma_group = QGroupBox("Reputation & Karma")
        rep_karma_layout = QFormLayout()
        
        self._reputation_spin = QSpinBox()
        self._reputation_spin.setRange(-1000, 1000)
        rep_karma_layout.addRow("Reputation:", self._reputation_spin)
        
        self._rep_type_combo = QComboBox()
        for rep_type in ReputationType:
            self._rep_type_combo.addItem(rep_type.name.replace('_', ' ').title(), rep_type.value)
        rep_karma_layout.addRow("Reputation Type:", self._rep_type_combo)
        
        self._karma_combo = QComboBox()
        self._karma_combo.addItems([
            "Neutral", "Good", "Bad", "Killed Children", "Killed Elders", 
            "Slaver", "Childkiller"
        ])
        rep_karma_layout.addRow("Karma:", self._karma_combo)
        
        rep_karma_group.setLayout(rep_karma_layout)
        scroll_layout.addWidget(rep_karma_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Connect signals
        self._relation_combo.currentIndexChanged.connect(self._on_data_changed)
        self._relation_mod_spin.valueChanged.connect(self._on_relation_changed)
        self._faction_id_spin.valueChanged.connect(self._on_data_changed)
        self._faction_name_edit.textChanged.connect(self._on_data_changed)
        self._faction_standing_spin.valueChanged.connect(self._on_data_changed)
        self._reputation_spin.valueChanged.connect(self._on_data_changed)
        self._rep_type_combo.currentIndexChanged.connect(self._on_data_changed)
        self._karma_combo.currentIndexChanged.connect(self._on_data_changed)
    
    def _on_relation_changed(self, value: int):
        self._relation_bar.setValue(value)
        
        # Update color based on value
        if value < -33:
            self._relation_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {FalloutColors.PANEL_BORDER};
                    background-color: {FalloutColors.CHARCOAL};
                }}
                QProgressBar::chunk {{
                    background-color: {FalloutColors.STATUS_RED};
                }}
            """)
        elif value < 33:
            self._relation_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {FalloutColors.PANEL_BORDER};
                    background-color: {FalloutColors.CHARCOAL};
                }}
                QProgressBar::chunk {{
                    background-color: {FalloutColors.WARNING_YELLOW};
                }}
            """)
        else:
            self._relation_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {FalloutColors.PANEL_BORDER};
                    background-color: {FalloutColors.CHARCOAL};
                }}
                QProgressBar::chunk {{
                    background-color: {FalloutColors.TERMINAL_GREEN};
                }}
            """)
        
        self._save_to_npc()
        self.data_changed.emit()
    
    def _on_data_changed(self):
        self._save_to_npc()
        self.data_changed.emit()
    
    def _load_data(self):
        rel = self._npc.relationship
        
        idx = self._relation_combo.findData(rel.relation_type.value)
        if idx >= 0:
            self._relation_combo.setCurrentIndex(idx)
        
        self._relation_mod_spin.setValue(rel.relation_modifier)
        self._relation_bar.setValue(rel.relation_modifier)
        
        self._faction_id_spin.setValue(rel.faction_id)
        self._faction_name_edit.setText(rel.faction_name)
        self._faction_standing_spin.setValue(rel.faction_standing)
        
        self._reputation_spin.setValue(rel.reputation)
        idx = self._rep_type_combo.findData(rel.reputation_type.value)
        if idx >= 0:
            self._rep_type_combo.setCurrentIndex(idx)
        
        idx = self._karma_combo.findText(rel.karma_level)
        if idx >= 0:
            self._karma_combo.setCurrentIndex(idx)
    
    def _save_to_npc(self):
        rel = self._npc.relationship
        
        rel.relation_type = RelationshipType(self._relation_combo.currentData())
        rel.relation_modifier = self._relation_mod_spin.value()
        
        rel.faction_id = self._faction_id_spin.value()
        rel.faction_name = self._faction_name_edit.text()
        rel.faction_standing = self._faction_standing_spin.value()
        
        rel.reputation = self._reputation_spin.value()
        rel.reputation_type = ReputationType(self._rep_type_combo.currentData())
        rel.karma_level = self._karma_combo.currentText()
    
    def get_npc(self) -> Npc:
        self._save_to_npc()
        return self._npc


class DialogueLinkWidget(QWidget):
    """Widget for NPC dialogue configuration"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Dialogue Configuration")
        title.setFont(FalloutFonts.get_ui_font())
        title.setStyleSheet(f"color: {FalloutColors.FALLOUT_YELLOW}; font-size: 14px;")
        layout.addWidget(title)
        
        # Dialogue File Group
        file_group = QGroupBox("Dialogue File")
        file_layout = QFormLayout()
        
        self._dialogue_file_edit = QLineEdit()
        self._dialogue_file_edit.setPlaceholderText("Path to .lst dialogue file...")
        self._browse_btn = QPushButton("Browse...")
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self._dialogue_file_edit)
        browse_layout.addWidget(self._browse_btn)
        file_layout.addRow("Dialogue File:", browse_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Dialogue Nodes Group
        nodes_group = QGroupBox("Dialogue Nodes")
        nodes_layout = QFormLayout()
        
        self._default_node_edit = QLineEdit()
        self._default_node_edit.setPlaceholderText("Node name...")
        nodes_layout.addRow("Default Node:", self._default_node_edit)
        
        self._greeting_node_edit = QLineEdit()
        self._greeting_node_edit.setPlaceholderText("Node name...")
        nodes_layout.addRow("Greeting:", self._greeting_node_edit)
        
        self._trade_node_edit = QLineEdit()
        self._trade_node_edit.setPlaceholderText("Node name...")
        nodes_layout.addRow("Trade:", self._trade_node_edit)
        
        self._death_node_edit = QLineEdit()
        self._death_node_edit.setPlaceholderText("Node name...")
        nodes_layout.addRow("On Death:", self._death_node_edit)
        
        self._knockout_node_edit = QLineEdit()
        self._knockout_node_edit.setPlaceholderText("Node name...")
        nodes_layout.addRow("Knocked Out:", self._knockout_node_edit)
        
        nodes_group.setLayout(nodes_layout)
        layout.addWidget(nodes_group)
        
        # Reaction Table Group
        reaction_group = QGroupBox("Reaction Table")
        reaction_layout = QVBoxLayout()
        
        self._reaction_tree = QTreeWidget()
        self._reaction_tree.setHeaderLabels(["Condition", "Node"])
        self._reaction_tree.setColumnCount(2)
        
        self._add_reaction_btn = QPushButton("Add Reaction")
        self._remove_reaction_btn = QPushButton("Remove")
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._add_reaction_btn)
        btn_layout.addWidget(self._remove_reaction_btn)
        btn_layout.addStretch()
        
        reaction_layout.addWidget(self._reaction_tree)
        reaction_layout.addLayout(btn_layout)
        
        reaction_group.setLayout(reaction_layout)
        layout.addWidget(reaction_group)
        
        layout.addStretch()
        
        # Connect signals
        self._dialogue_file_edit.textChanged.connect(self._on_data_changed)
        self._browse_btn.clicked.connect(self._browse_dialogue)
        self._default_node_edit.textChanged.connect(self._on_data_changed)
        self._greeting_node_edit.textChanged.connect(self._on_data_changed)
        self._trade_node_edit.textChanged.connect(self._on_data_changed)
        self._death_node_edit.textChanged.connect(self._on_data_changed)
        self._knockout_node_edit.textChanged.connect(self._on_data_changed)
    
    def _browse_dialogue(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Dialogue File", "", "Dialogue Files (*.lst);;All Files (*)"
        )
        if file_path:
            self._dialogue_file_edit.setText(file_path)
    
    def _on_data_changed(self):
        self._save_to_npc()
        self.data_changed.emit()
    
    def _load_data(self):
        dlg = self._npc.dialogue
        
        self._dialogue_file_edit.setText(dlg.dialogue_file)
        self._default_node_edit.setText(dlg.default_node)
        self._greeting_node_edit.setText(dlg.greeting_node)
        self._trade_node_edit.setText(dlg.trade_node)
        self._death_node_edit.setText(dlg.death_node)
        self._knockout_node_edit.setText(dlg.knocked_out_node)
    
    def _save_to_npc(self):
        dlg = self._npc.dialogue
        
        dlg.dialogue_file = self._dialogue_file_edit.text()
        dlg.default_node = self._default_node_edit.text()
        dlg.greeting_node = self._greeting_node_edit.text()
        dlg.trade_node = self._trade_node_edit.text()
        dlg.death_node = self._death_node_edit.text()
        dlg.knocked_out_node = self._knockout_node_edit.text()
    
    def get_npc(self) -> Npc:
        self._save_to_npc()
        return self._npc


class NpcEditorDialog(QDialog):
    """
    Main NPC Editor Dialog
    Provides a comprehensive interface for editing all NPC properties
    """
    
    npc_saved = pyqtSignal(Npc)
    
    def __init__(self, npc: Optional[Npc] = None, parent=None):
        super().__init__(parent)
        self._npc = npc or Npc()
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        self.setWindowTitle("NPC Editor")
        self.setMinimumSize(900, 700)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("NPC Configuration Editor")
        header.setFont(FalloutFonts.get_ui_font())
        header.setStyleSheet(f"""
            color: {FalloutColors.FALLOUT_YELLOW};
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            background-color: {FalloutColors.DARK_OLIVE_GREEN};
            border-bottom: 2px solid {FalloutColors.RUST_ORANGE};
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        # Tab widget
        self._tabs = FalloutTabWidget()
        
        # Create tabs
        self._basic_tab = BasicInfoWidget(self._npc)
        self._tabs.addTab(self._basic_tab, "Basic Info")
        
        self._appearance_tab = AppearanceWidget(self._npc)
        self._tabs.addTab(self._appearance_tab, "Appearance")
        
        self._attributes_tab = AttributesWidget(self._npc)
        self._tabs.addTab(self._attributes_tab, "Attributes")
        
        self._skills_tab = SkillsWidget(self._npc)
        self._tabs.addTab(self._skills_tab, "Skills")
        
        self._inventory_tab = InventoryWidget(self._npc)
        self._tabs.addTab(self._inventory_tab, "Inventory")
        
        self._behavior_tab = BehaviorWidget(self._npc)
        self._tabs.addTab(self._behavior_tab, "Behavior")
        
        self._ai_tab = AiSettingsWidget(self._npc)
        self._tabs.addTab(self._ai_tab, "AI Settings")
        
        self._relationship_tab = RelationshipWidget(self._npc)
        self._tabs.addTab(self._relationship_tab, "Relationships")
        
        self._dialogue_tab = DialogueLinkWidget(self._npc)
        self._tabs.addTab(self._dialogue_tab, "Dialogue")
        
        main_layout.addWidget(self._tabs)
        
        # Validation status bar
        self._validation_label = QLabel()
        self._validation_label.setStyleSheet(f"""
            color: {FalloutColors.TEXT_DIM};
            padding: 5px;
            background-color: {FalloutColors.CHARCOAL};
        """)
        main_layout.addWidget(self._validation_label)
        
        # Button box
        btn_box = QHBoxLayout()
        
        self._validate_btn = QPushButton("Validate")
        self._validate_btn.clicked.connect(self._validate)
        
        self._reset_btn = QPushButton("Reset")
        self._reset_btn.clicked.connect(self._reset)
        
        self._save_btn = QPushButton("Save")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._save)
        
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        
        btn_box.addWidget(self._validate_btn)
        btn_box.addStretch()
        btn_box.addWidget(self._reset_btn)
        btn_box.addWidget(self._save_btn)
        btn_box.addWidget(self._cancel_btn)
        
        main_layout.addLayout(btn_box)
        
        # Initial validation
        self._validate()
    
    def _connect_signals(self):
        """Connect all tab data_changed signals"""
        for tab in [self._basic_tab, self._appearance_tab, self._attributes_tab,
                    self._skills_tab, self._inventory_tab, self._behavior_tab,
                    self._ai_tab, self._relationship_tab, self._dialogue_tab]:
            if hasattr(tab, 'data_changed'):
                tab.data_changed.connect(self._on_data_changed)
    
    def _on_data_changed(self):
        """Handle any data change"""
        self._npc.is_modified = True
        self._validate()
    
    def _validate(self):
        """Validate the NPC data"""
        is_valid = self._npc.validate()
        
        if is_valid:
            self._validation_label.setText(
                f"✓ Validation passed - {len(self._npc.inventory)} items in inventory"
            )
            self._validation_label.setStyleSheet(f"""
                color: {FalloutColors.TERMINAL_GREEN};
                padding: 5px;
                background-color: {FalloutColors.CHARCOAL};
            """)
        else:
            errors = "\n  • ".join(self._npc.validation_errors[:5])
            if len(self._npc.validation_errors) > 5:
                errors += f"\n  ... and {len(self._npc.validation_errors) - 5} more"
            
            self._validation_label.setText(
                f"✗ Validation failed:\n  • {errors}"
            )
            self._validation_label.setStyleSheet(f"""
                color: {FalloutColors.STATUS_RED};
                padding: 5px;
                background-color: {FalloutColors.CHARCOAL};
            """)
        
        return is_valid
    
    def _reset(self):
        """Reset all changes"""
        reply = QMessageBox.question(
            self, "Reset Changes",
            "Are you sure you want to reset all changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._npc = Npc()
            self._reload_tabs()
            self._validate()
    
    def _reload_tabs(self):
        """Reload all tabs with current NPC data"""
        self._basic_tab.set_npc(self._npc)
        self._appearance_tab.set_npc(self._npc)
        self._attributes_tab.set_npc(self._npc)
        self._skills_tab.set_npc(self._npc)
        self._inventory_tab.set_npc(self._npc)
        self._behavior_tab.set_npc(self._npc)
        self._ai_tab.set_npc(self._npc)
        self._relationship_tab.set_npc(self._npc)
        self._dialogue_tab.set_npc(self._npc)
    
    def _save(self):
        """Save the NPC data"""
        if not self._validate():
            reply = QMessageBox.warning(
                self, "Validation Failed",
                "NPC has validation errors. Save anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Get all data from tabs
        self._npc = self._basic_tab.get_npc()
        self._npc = self._appearance_tab.get_npc()
        self._npc = self._attributes_tab.get_npc()
        self._npc = self._skills_tab.get_npc()
        self._npc = self._inventory_tab.get_npc()
        self._npc = self._behavior_tab.get_npc()
        self._npc = self._ai_tab.get_npc()
        self._npc = self._relationship_tab.get_npc()
        self._npc = self._dialogue_tab.get_npc()
        
        self._npc.is_modified = False
        self.npc_saved.emit(self._npc)
        self.accept()
    
    def get_npc(self) -> Npc:
        """Get the edited NPC"""
        return self._npc
    
    def set_npc(self, npc: Npc):
        """Set the NPC to edit"""
        self._npc = npc
        self._reload_tabs()
        self._validate()


# Need to import QInputDialog for scar addition
from PyQt6.QtWidgets import QInputDialog
