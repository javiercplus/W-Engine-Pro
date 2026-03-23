from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize, QUrl
from PySide6.QtGui import QIcon, QFont, QDesktopServices


class Sidebar(QWidget):
    pageChanged = Signal(str)
    stopAllRequested = Signal()
    fullscreenRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)

        # W-Engine Pro Logo as a clickable label
        self.logo = QLabel("W-Engine Pro")
        self.logo.setObjectName("logo_label")
        self.logo.setCursor(Qt.PointingHandCursor)
        self.logo.mousePressEvent = lambda e: QDesktopServices.openUrl(
            QUrl("https://github.com/ErzaGOD19/W-Engine-Pro")
        )
        layout.addWidget(self.logo)

        self.nav_buttons = {}
        self.add_nav_item("library", "Biblioteca", "view-grid")
        self.add_nav_item("monitors", "Monitores", "video-display")
        self.add_nav_item("design", "Personalización", "applications-graphics")
        self.add_nav_item("diagnostics", "Diagnóstico", "utilities-system-monitor")
        self.add_nav_item("settings", "Ajustes", "emblem-system")
        self.add_nav_item("about", "Acerca de", "help-about")

        layout.addStretch()

        self.stop_btn = QPushButton("Detener Todo")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setIcon(QIcon.fromTheme("process-stop"))
        self.stop_btn.clicked.connect(self.stopAllRequested.emit)
        layout.addWidget(self.stop_btn)

        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.setObjectName("fullscreen_btn")
        self.fullscreen_btn.setCursor(Qt.PointingHandCursor)
        self.fullscreen_btn.setIcon(QIcon.fromTheme("view-fullscreen"))
        self.fullscreen_btn.setToolTip("Pantalla Completa (F11)")
        self.fullscreen_btn.clicked.connect(self.fullscreenRequested.emit)
        layout.addWidget(self.fullscreen_btn)

        self.version = QLabel("v1.5 Beta")
        self.version.setStyleSheet(
            "color: #666; font-size: 10px; margin-right: 10px; border: none;"
        )
        self.version.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version)

        self.set_active("library")

    def add_nav_item(self, name, label, icon_name):
        btn = QPushButton(f" {label}")
        btn.setObjectName("nav_btn")
        btn.setCursor(Qt.PointingHandCursor)
        icon = QIcon.fromTheme(icon_name)
        if not icon.isNull():
            btn.setIcon(icon)

        btn.clicked.connect(lambda: self.on_btn_clicked(name))
        self.nav_buttons[name] = btn
        self.layout().addWidget(btn)

    def on_btn_clicked(self, name):
        self.set_active(name)
        self.pageChanged.emit(name)

    def set_active(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.setProperty("active", btn_name == name)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
