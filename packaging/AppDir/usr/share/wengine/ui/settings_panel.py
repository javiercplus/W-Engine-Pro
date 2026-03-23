from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QScrollArea,
    QFrame,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt
from core.desktop_helper import DesktopHelper


class SettingsPanel(QWidget):
    def __init__(self, config, controller):
        super().__init__()
        self.config = config
        self.controller = controller

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)

        engine_group = QGroupBox("Engine & Performance")
        engine_layout = QFormLayout()

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["mpv", "web", "parallax"])
        self.engine_combo.setCurrentText(self.config.get("engine", "mpv"))
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        engine_layout.addRow("Active Engine:", self.engine_combo)

        self.hwdec_combo = QComboBox()
        self.hwdec_combo.addItems(["auto", "vaapi", "nvdec", "none"])
        self.hwdec_combo.setCurrentText(self.config.get("hwdec", "auto"))
        self.hwdec_combo.currentTextChanged.connect(
            lambda v: self.config.set("hwdec", v)
        )
        engine_layout.addRow("Hardware Decoding:", self.hwdec_combo)

        self.playback_mode_combo = QComboBox()
        self.playback_mode_combo.addItems(
            ["Auto", "Disk (Low RAM)", "Memory (High Perf)"]
        )
        self.playback_mode_combo.setCurrentText(self.config.get_playback_mode())
        self.playback_mode_combo.currentTextChanged.connect(
            self.config.set_playback_mode
        )
        self.playback_mode_combo.setToolTip(
            "Auto: Decide based on RAM and file size.\nDisk: Read directly (minimal RAM usage).\nMemory: Cache video in RAM for maximum smoothness."
        )
        engine_layout.addRow("Playback Mode:", self.playback_mode_combo)

        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)

        # GNOME Specific Section
        if DesktopHelper.is_gnome():
            gnome_group = QGroupBox("Optimización GNOME")
            gnome_layout = QVBoxLayout()

            gnome_info = QLabel(
                "GNOME requiere una extensión para fijar el fondo de pantalla correctamente (especialmente en Wayland)."
            )
            gnome_info.setWordWrap(True)
            gnome_layout.addWidget(gnome_info)

            self.install_ext_btn = QPushButton("Instalar Extensión de GNOME")
            self.install_ext_btn.clicked.connect(self._install_gnome_extension)
            gnome_layout.addWidget(self.install_ext_btn)

            if DesktopHelper.is_extension_installed():
                self.install_ext_btn.setText("Reinstalar / Actualizar Extensión")

                open_ext_btn = QPushButton("Abrir App de Extensiones")
                open_ext_btn.clicked.connect(DesktopHelper.open_extensions_app)
                gnome_layout.addWidget(open_ext_btn)

            gnome_group.setLayout(gnome_layout)
            layout.addWidget(gnome_group)

        behavior_group = QGroupBox("Behavior & Smart Pause")
        behavior_layout = QFormLayout()

        self.auto_start_cb = QCheckBox("Start with System (Auto-Start)")
        self.auto_start_cb.setChecked(self.config.get("autostart", False))
        self.auto_start_cb.stateChanged.connect(self._on_autostart_changed)
        behavior_layout.addRow(self.auto_start_cb)

        # Smart Pause Options
        self.pause_mode_combo = QComboBox()
        self.pause_mode_combo.addItems(
            ["Desactivado", "Ventana Activa", "Ventana Maximizada", "Pantalla Completa"]
        )

        # Sync with config
        is_pause_enabled = self.config.get("pause_on_active", True)
        current_pause_mode = self.config.get("pause_mode", "Fullscreen")

        if not is_pause_enabled:
            self.pause_mode_combo.setCurrentText("Desactivado")
        else:
            mode_map_inv = {
                "Any Window": "Ventana Activa",
                "Maximized": "Ventana Maximizada",
                "Fullscreen": "Pantalla Completa",
            }
            self.pause_mode_combo.setCurrentText(
                mode_map_inv.get(current_pause_mode, "Pantalla Completa")
            )

        self.pause_mode_combo.currentTextChanged.connect(self._on_pause_mode_changed)
        behavior_layout.addRow("Smart Pause Mode:", self.pause_mode_combo)

        self.cpu_limit_combo = QComboBox()
        self.cpu_limit_combo.addItems(["50%", "70%", "85%", "95%", "Nunca"])
        current_cpu = self.config.get("pause_cpu_threshold", 85)
        self.cpu_limit_combo.setCurrentText(
            f"{current_cpu}%" if current_cpu < 100 else "Nunca"
        )
        self.cpu_limit_combo.currentTextChanged.connect(self._on_cpu_limit_changed)
        behavior_layout.addRow("Pausar si CPU >:", self.cpu_limit_combo)

        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _on_autostart_changed(self, state):
        enabled = (state == 2)
        self.config.set("autostart", enabled)
        DesktopHelper.setup_autostart(enabled)

    def _on_engine_changed(self, engine_name):
        self.config.set("engine", engine_name)
        if self.controller:
            self.controller.start_all(default_engine=engine_name)

    def _on_pause_mode_changed(self, text):
        mode_map = {
            "Ventana Activa": "Any Window",
            "Ventana Maximizada": "Maximized",
            "Pantalla Completa": "Fullscreen",
        }

        if text == "Desactivado":
            self.config.set("pause_on_active", False)
        else:
            self.config.set("pause_on_active", True)
            self.config.set("pause_mode", mode_map.get(text, "Fullscreen"))

    def _on_cpu_limit_changed(self, text):
        if text == "Nunca":
            self.config.set("pause_cpu_threshold", 100)
        else:
            limit = int(text.replace("%", ""))
            self.config.set("pause_cpu_threshold", limit)

    def _install_gnome_extension(self):
        success, message = DesktopHelper.install_extension()
        if success:
            QMessageBox.information(self, "Extensión Instalada", message)
            self.install_ext_btn.setText("Reinstalar / Actualizar Extensión")
        else:
            QMessageBox.critical(
                self, "Error", f"No se pudo instalar la extensión: {message}"
            )
