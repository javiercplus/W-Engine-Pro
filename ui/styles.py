DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
    color: #ffffff;
}

QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 14px;
}

/* Page Title */
QLabel#page_title {
    font-size: 24px;
    font-weight: bold;
    color: white;
    margin-bottom: 10px;
}

/* Top Bar */
QTabBar::tab {
    background: #2a2a2a;
    color: #b0b0b0;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #3a3a3a;
    color: #ffffff;
    border-bottom: 2px solid #007acc;
}

QTabBar::tab:hover {
    background: #3a3a3a;
    color: #ffffff;
}

QLineEdit {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}

QLineEdit:focus {
    border: 1px solid #007acc;
}

QPushButton {
    background-color: #3a3a3a;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #4a4a4a;
}

QPushButton:pressed {
    background-color: #2a2a2a;
}

/* Professional Sliders */
QSlider::groove:horizontal {
    border: 1px solid #3a3a3a;
    height: 4px;
    background: #252526;
    margin: 2px 0;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #007acc;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #e0e0e0;
    border: 1px solid #5c5c5c;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #ffffff;
    border: 1px solid #007acc;
}

/* Grid & Lists */
QListView {
    background-color: #252526;
    border: none;
    outline: none;
}

QListView::item {
    background-color: #2a2a2a;
    border-radius: 6px;
    padding: 5px;
    margin: 5px;
}

QListView::item:selected {
    background-color: #007acc;
    color: white;
    border: 1px solid #007acc;
}

QListView::item:hover {
    background-color: #353535;
}

/* Properties Panel */
PropertiesPanel {
    background-color: #252526;
    border-left: 1px solid #333;
}

PropertiesPanel QLabel#title {
    font-size: 16px;
    font-weight: bold;
    color: white;
}

PropertiesPanel QGroupBox {
    border: 1px solid #3a3a3a;
    margin-top: 15px;
    padding-top: 10px;
    font-weight: bold;
}

QPushButton#apply_btn {
    background-color: #007acc;
    color: white;
    font-weight: bold;
}

QPushButton#apply_btn:hover {
    background-color: #007acc;
    border: 1px solid white;
}

QPushButton#add_btn {
    background-color: #007acc;
    color: white;
    font-weight: bold;
}

QPushButton#add_btn:hover {
    background-color: #007acc;
    border: 1px solid white;
}

QPushButton#remove_btn {
    background-color: #442222;
    color: #ffaaaa;
    border: 1px solid #663333;
}

QPushButton#remove_btn:hover {
    background-color: #552222;
}

/* About Page Styles */
QWidget#about_container {
    background-color: #111111;
    border-radius: 30px;
    border: 1px solid #222;
}

/* Force transparency on ALL labels inside the container to remove grey/black boxes */
QWidget#about_container QLabel {
    background-color: transparent !important;
}

QLabel#author_name {
    font-size: 38px;
    font-weight: 900;
    color: #007acc;
    background-color: transparent;
}

QLabel#about_description {
    font-size: 16px;
    color: #aaaaaa;
    background-color: transparent;
}

QPushButton#discord_btn {
    background-color: #007acc;
    color: white;
    font-weight: bold;
    font-size: 16px;
    padding: 0px 20px; /* Vertical padding can cause bugs with fixed height */
    border-radius: 14px;
    border: none;
    text-align: center;
}

QPushButton#discord_btn:hover {
    background-color: #007acc;
    border: 2px solid white;
}

/* Glow Frame effect (Invisible container, only for shadow) */
QFrame#glow_frame {
    background-color: transparent;
    border: none;
}

/* Properties Panel */
QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
    color: #b0b0b0;
}

QLabel {
    color: #cccccc;
}

/* Splitter */
QSplitter::handle {
    background-color: #2a2a2a;
    width: 2px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #3a3a3a;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Sidebar Styles */
Sidebar {
    background-color: #1e1e1e;
    border-bottom: 1px solid #333;
}

QPushButton#nav_btn {
    background-color: transparent;
    border: none;
    color: #cccccc;
    text-align: center;
    padding: 5px 15px;
    font-size: 14px;
    border-radius: 5px;
    margin: 5px 2px;
}

QPushButton#nav_btn:hover {
    background-color: #2d2d2d;
    color: white;
}

QPushButton#nav_btn[active="true"] {
    background-color: #3d3d3d;
    color: #007acc;
    font-weight: bold;
    border-bottom: 4px solid #007acc;
}

QPushButton#stop_btn {
    background-color: #3d3d3d;
    border: 1px solid #007acc;
    color: #ffffff;
    padding: 5px 15px;
    font-size: 13px;
    border-radius: 5px;
    margin: 5px 10px;
    font-weight: bold;
}

QPushButton#stop_btn:hover {
    background-color: #007acc;
    border: 1px solid white;
}

QLabel#logo_label {
    color: white;
    font-size: 18px;
    font-weight: bold;
    margin: 0 20px;
    border: none;
}
"""

CLARO_THEME = """
QMainWindow {
    background-color: #f5f5f7;
    color: #1d1d1f;
}

QWidget {
    background-color: #f5f5f7;
    color: #1d1d1f;
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 14px;
}

QLabel#page_title {
    font-size: 24px;
    font-weight: bold;
    color: #1d1d1f;
    margin-bottom: 10px;
}

QTabBar::tab {
    background: #e5e5e7;
    color: #86868b;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #1d1d1f;
    border-bottom: 2px solid #007acc;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 4px;
    padding: 6px;
    color: #1d1d1f;
}

QPushButton {
    background-color: #e5e5e7;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    color: #1d1d1f;
}

QPushButton:hover {
    background-color: #d2d2d7;
}

QSlider::groove:horizontal {
    border: 1px solid #d2d2d7;
    height: 4px;
    background: #e5e5e7;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #007acc;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}

QListView {
    background-color: #ffffff;
}

QListView::item {
    background-color: #f5f5f7;
    color: #1d1d1f;
}

QListView::item:selected {
    background-color: #007acc;
    color: white;
}

PropertiesPanel {
    background-color: #ffffff;
    border-left: 1px solid #d2d2d7;
}

PropertiesPanel QLabel#title {
    color: #1d1d1f;
}

QGroupBox {
    border: 1px solid #d2d2d7;
    color: #1d1d1f;
}

QGroupBox::title {
    color: #86868b;
}

Sidebar {
    background-color: #ffffff;
    border-bottom: 1px solid #d2d2d7;
}

QPushButton#nav_btn {
    color: #86868b;
}

QPushButton#nav_btn[active="true"] {
    color: #007acc;
    border-bottom: 4px solid #007acc;
}

QLabel#logo_label {
    color: #1d1d1f;
}
"""

MATERIAL_DARK_THEME = """
QMainWindow {
    background-color: #121212;
}

QWidget {
    background-color: #121212;
    color: #e1e1e1;
}

QListView::item {
    background-color: #1e1e1e;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

QPushButton {
    background-color: #1e1e1e;
    border-radius: 8px;
}

QPushButton#apply_btn, QPushButton#add_btn, QPushButton#stop_btn {
    background-color: #007acc;
    color: #121212;
}

QSlider::sub-page:horizontal {
    background: #007acc;
}

Sidebar {
    background-color: #1a1a1a;
}

QPushButton#nav_btn[active="true"] {
    color: #007acc;
    border-bottom: 4px solid #007acc;
}
"""

FUSION_V15_THEME = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
}

QWidget {
    background: transparent;
    color: #00d2ff;
}

QGroupBox, QListView, PropertiesPanel, Sidebar {
    background-color: rgba(20, 20, 40, 0.7);
    border: 1px solid #007acc;
    border-radius: 8px;
}

QPushButton {
    background-color: rgba(0, 210, 255, 0.1);
    border: 1px solid #007acc;
    color: #007acc;
    text-shadow: 0 0 5px #007acc;
}

QPushButton:hover {
    background-color: rgba(0, 210, 255, 0.3);
}

QSlider::sub-page:horizontal {
    background: #007acc;
}

QLabel#logo_label {
    color: #007acc;
    font-weight: 900;
}
"""
