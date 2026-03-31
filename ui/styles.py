# Dynamic Stylesheet Template
STYLE_TEMPLATE = """
QMainWindow {
    background-color: transparent;
    color: {{TEXT_COLOR}};
}

QWidget {
    background-color: transparent;
    color: {{TEXT_COLOR}};
    font-family: "{{FONT_FAMILY}}";
    font-size: 14px;
}

/* Base container that actually holds the content should have the BG_COLOR if transparency is 100% or RGBA if not */
#central_widget_container {
    background-color: {{BG_COLOR}};
}

/* Specific background for all containers to match UI_BG */
QStackedWidget, QScrollArea, QFrame, QGroupBox, QListView, PropertiesPanel, Sidebar, QLabel {
    background-color: transparent;
    border-color: {{ACCENT_COLOR}};
}

QLabel { color: {{TEXT_COLOR}}; }

QLineEdit, QSpinBox, QComboBox {
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    padding: 6px;
    color: {{TEXT_COLOR}};
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid {{ACCENT_COLOR}};
}

QPushButton {
    background-color: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 10px 20px;
    color: {{TEXT_COLOR}};
    font-weight: 500;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.22);
    border: 1px solid {{ACCENT_COLOR}};
}

QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.08);
    margin-top: 1px; /* Subtle push */
}

/* Navigation Buttons */
QPushButton#nav_btn {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px 12px;
}

QPushButton#nav_btn:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

QPushButton#nav_btn[active="true"] {
    background-color: rgba(255, 255, 255, 0.12);
    color: {{ACCENT_COLOR}};
    border-bottom: 2px solid {{ACCENT_COLOR}};
}

/* Action Buttons (Apply, Stop, Add, etc.) */
QPushButton#apply_btn, QPushButton#add_btn, QPushButton#stop_btn, QPushButton#remove_btn {
    background-color: {{ACCENT_COLOR}};
    color: white; 
    font-weight: bold;
    border: 1px solid rgba(255, 255, 255, 0.1);
    min-width: 110px; /* Reduced from 140px */
    padding: 6px 12px;  /* Reduced padding */
    font-size: 13px;    /* Slightly smaller font for better fit */
}

QPushButton#apply_btn:hover, QPushButton#add_btn:hover, QPushButton#stop_btn:hover {
    background-color: {{ACCENT_COLOR}};
    /* GLOW EFFECT using Accent Color */
    border: 1px solid white;
}

/* Subtle Remove Button */
QPushButton#remove_btn {
    background-color: rgba(198, 40, 40, 0.7); /* More opaque/subtle red */
}

QPushButton#remove_btn:hover {
    background-color: rgba(211, 47, 47, 0.9);
    border: 1px solid {{ACCENT_COLOR}}; /* Accent glow even on delete */
}

QPushButton#apply_btn:pressed, QPushButton#stop_btn:pressed, QPushButton#remove_btn:pressed {
    background-color: rgba(0, 0, 0, 0.4);
}

QSlider::groove:horizontal {
    border: 1px solid rgba(255, 255, 255, 0.1);
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    margin: 2px 0;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: {{ACCENT_COLOR}};
    border: none;
    width: 12px;
    height: 12px;
    margin: -5px 0;
    border-radius: 6px;
}

QSlider::sub-page:horizontal {
    background: {{ACCENT_COLOR}};
    border-radius: 2px;
}

QListView::item:selected {
    background-color: {{ACCENT_COLOR}};
    color: {{BG_COLOR}};
}

QScrollBar::handle:vertical {
    background: {{ACCENT_COLOR}};
    opacity: 0.5;
}

/* Fix for About Page Container */
#about_container {
    background-color: {{BG_COLOR}};
    border: 2px solid {{ACCENT_COLOR}};
    border-radius: 24px;
}

/* Menu Styles */
QMenu {
    background-color: {{BG_COLOR}};
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    color: {{TEXT_COLOR}};
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: {{ACCENT_COLOR}};
    color: white;
}

QMenu::separator {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 4px 8px;
}

QMenuBar {
    background-color: {{BG_COLOR}};
    color: {{TEXT_COLOR}};
}

QMenuBar::item {
    padding: 6px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: {{ACCENT_COLOR}};
    color: white;
    border-radius: 4px;
}

/* ToolTip */
QToolTip {
    background-color: {{BG_COLOR}};
    color: {{TEXT_COLOR}};
    border: 1px solid {{ACCENT_COLOR}};
    border-radius: 4px;
    padding: 4px;
}
"""

# Kept for backward compatibility if needed
DARK_THEME = (
    STYLE_TEMPLATE.replace("{{BG_COLOR}}", "#1e1e1e")
    .replace("{{TEXT_COLOR}}", "#ffffff")
    .replace("{{ACCENT_COLOR}}", "#007acc")
    .replace("{{FONT_FAMILY}}", "Segoe UI")
)
CLARO_THEME = (
    STYLE_TEMPLATE.replace("{{BG_COLOR}}", "#f5f5f7")
    .replace("{{TEXT_COLOR}}", "#1d1d1f")
    .replace("{{ACCENT_COLOR}}", "#007acc")
    .replace("{{FONT_FAMILY}}", "Segoe UI")
)
MATERIAL_DARK_THEME = (
    STYLE_TEMPLATE.replace("{{BG_COLOR}}", "#121212")
    .replace("{{TEXT_COLOR}}", "#e1e1e1")
    .replace("{{ACCENT_COLOR}}", "#007acc")
    .replace("{{FONT_FAMILY}}", "Segoe UI")
)
FUSION_V15_THEME = (
    STYLE_TEMPLATE.replace("{{BG_COLOR}}", "#0f0c29")
    .replace("{{TEXT_COLOR}}", "#00d2ff")
    .replace("{{ACCENT_COLOR}}", "#007acc")
    .replace("{{FONT_FAMILY}}", "Segoe UI")
)
