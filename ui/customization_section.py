"""
Customization section module for W-Engine Pro settings.
Provides theme, color, and language customization with dynamic translation support.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QColorDialog,
    QFontComboBox,
    QMessageBox,
    QGroupBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core import i18n

class CustomizationSection(QWidget):
    """Theme and language customization section with runtime retranslation."""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self._retranslate_ui()
    
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 0)
        
        # Language Selection
        self.lang_group = QGroupBox()
        lang_layout = QFormLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Español"])
        current_lang = self.config.get("language", "en")
        lang_map = {"en": "English", "es": "Español"}
        self.language_combo.setCurrentText(lang_map.get(current_lang, "English"))
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        lang_layout.addRow(QLabel(), self.language_combo)
        
        self.lang_group.setLayout(lang_layout)
        self.layout.addWidget(self.lang_group)
        
        # Theme Selection
        self.theme_group = QGroupBox()
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([i18n.t("dark"), i18n.t("light"), i18n.t("material_dark"), i18n.t("fusion_v15")])
        if self.config:
            current_theme = self.config.get("theme", "Dark")
            # try to map internal to display
            self.theme_combo.setCurrentText(current_theme if current_theme in [i18n.t("dark"), i18n.t("light")] else current_theme)
            self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addRow(QLabel(i18n.t("theme") + ":"), self.theme_combo)
        
        self.transparency_spin = QSpinBox()
        self.transparency_spin.setRange(30, 100)
        self.transparency_spin.setSuffix("%")
        if self.config:
            val = self.config.get("window_transparency", 100)
            self.transparency_spin.setValue(int(val))
            self.transparency_spin.valueChanged.connect(
                lambda v: self.config.set("window_transparency", v)
            )
        theme_layout.addRow(QLabel("Transparency:"), self.transparency_spin)
        
        self.font_combo = QFontComboBox()
        if self.config:
            self.font_combo.setCurrentFont(self.config.get("ui_font", "Segoe UI"))
            self.font_combo.currentFontChanged.connect(
                lambda f: self.config.set("ui_font", f.family())
            )
        theme_layout.addRow(QLabel("Font:"), self.font_combo)
        
        self.theme_group.setLayout(theme_layout)
        self.layout.addWidget(self.theme_group)
        
        # Color Customization
        self.color_group = QGroupBox()
        color_layout = QGridLayout()
        self.color_buttons = {}
        
        self.colors_config = [
            (i18n.t("accent_color") if hasattr(i18n, 'accent_color') else "Accent Color", "accent_color", "#3498db"),
            ("UI Background", "ui_bg_color", "#1e1e1e"),
            ("Text Color", "ui_text_color", "#ffffff"),
        ]
        
        for i, (label, key, default) in enumerate(self.colors_config):
            color_layout.addWidget(QLabel(f"{label}:"), i, 0)
            btn = QPushButton()
            btn.setFixedSize(60, 25)
            val = self.config.get(key, default)
            btn.setStyleSheet(f"background-color: {val}; border: 1px solid #555;")
            btn.clicked.connect(
                lambda checked=False, k=key, b=btn: self._pick_color(k, b)
            )
            color_layout.addWidget(btn, i, 1)
            self.color_buttons[key] = btn
        
        self.color_group.setLayout(color_layout)
        self.layout.addWidget(self.color_group)
        
        self.layout.addStretch()
    
    def _on_language_changed(self, text):
        lang_map = {"English": "en", "Español": "es"}
        lang_code = lang_map.get(text, "en")
        self.config.set("language", lang_code)
        
        i18n.set_language(lang_code)
        # Try to update UI texts immediately
        self._retranslate_ui()
        parent = self.parent()
        if parent and hasattr(parent, "_retranslate_ui"):
            parent._retranslate_ui()
        QMessageBox.information(self, i18n.t("language_changed"), i18n.t("language_changed_msg"))
    
    def _on_theme_changed(self, theme_name):
        # Keep existing preset mappings but do not rely on hardcoded language
        presets = {
            i18n.t("dark"): ("#1e1e1e", "#ffffff", "#3498db"),
            i18n.t("light"): ("#f5f5f7", "#1d1d1f", "#3498db"),
            i18n.t("material_dark"): ("#121212", "#e1e1e1", "#3498db"),
            i18n.t("fusion_v15"): ("#0f0c29", "#00d2ff", "#3498db"),
        }
        
        if theme_name in presets:
            bg, text, accent = presets[theme_name]
            self.config.set("theme", theme_name)
            self.config.set("ui_bg_color", bg)
            self.config.set("ui_text_color", text)
            self.config.set("accent_color", accent)
            self._refresh_colors()
    
    def _refresh_colors(self):
        for key, btn in self.color_buttons.items():
            val = self.config.get(key, "#ffffff")
            btn.setStyleSheet(f"background-color: {val}; border: 1px solid #555;")
    
    def _pick_color(self, key, button):
        current = QColor(self.config.get(key, "#ffffff"))
        color = QColorDialog.getColor(current, self, i18n.t("select_color") if hasattr(i18n, 'select_color') else "Select Color")
        if color.isValid():
            hex_color = color.name()
            button.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #555;")
            self.config.set(key, hex_color)

    def _retranslate_ui(self):
        # update visible labels and group titles
        self.lang_group.setTitle(i18n.t("language") if i18n.t("language") else "Language")
        self.theme_group.setTitle(i18n.t("theme") if i18n.t("theme") else "Theme")
        self.color_group.setTitle(i18n.t("customization") if i18n.t("customization") else "Custom Colors")
