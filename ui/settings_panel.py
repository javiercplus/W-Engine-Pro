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
    QTabWidget,
)
from PySide6.QtCore import Qt
from core.desktop_helper import DesktopHelper
from ui.customization_section import CustomizationSection
from core import i18n

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

        # Use tabs to separate engine-related settings and interface/customization
        self.tabs = QTabWidget()

        # Engine tab
        engine_tab = QWidget()
        engine_layout = QVBoxLayout(engine_tab)

        engine_group = QGroupBox()
        engine_group_layout = QFormLayout()

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["mpv", "web", "parallax"])
        self.engine_combo.setCurrentText(self.config.get("engine", "mpv"))
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        engine_group_layout.addRow(QLabel(i18n.t("engine_settings") + ":"), self.engine_combo)

        self.hwdec_combo = QComboBox()
        self.hwdec_combo.addItems(["auto", "vaapi", "nvdec", "none"])
        self.hwdec_combo.setCurrentText(self.config.get("hwdec", "auto"))
        self.hwdec_combo.currentTextChanged.connect(
            lambda v: self.config.set("hwdec", v)
        )
        engine_group_layout.addRow(QLabel(i18n.t("hardware_decoding") + ":"), self.hwdec_combo)

        self.playback_mode_combo = QComboBox()
        self.playback_mode_combo.addItems(
            [i18n.t("auto"), i18n.t("disk"), i18n.t("memory")]
        )
        self.playback_mode_combo.setCurrentText(self.config.get_playback_mode())
        self.playback_mode_combo.currentTextChanged.connect(
            self.config.set_playback_mode
        )
        self.playback_mode_combo.setToolTip(
            "Auto: Decide based on RAM and file size.\nDisk: Read directly (minimal RAM usage).\nMemory: Cache video in RAM for maximum smoothness."
        )
        engine_group_layout.addRow(QLabel(i18n.t("playback_mode") + ":"), self.playback_mode_combo)

        engine_group.setLayout(engine_group_layout)
        engine_layout.addWidget(engine_group)

        # GNOME Specific Section
        if DesktopHelper.is_gnome():
            gnome_group = QGroupBox()
            gnome_layout = QVBoxLayout()

            gnome_info = QLabel(
                "GNOME requires an extension to pin wallpapers correctly (especially on Wayland)."
            )
            gnome_info.setWordWrap(True)
            gnome_layout.addWidget(gnome_info)

            self.install_ext_btn = QPushButton("Install GNOME Extension")
            self.install_ext_btn.clicked.connect(self._install_gnome_extension)
            gnome_layout.addWidget(self.install_ext_btn)

            if DesktopHelper.is_extension_installed():
                self.install_ext_btn.setText("Reinstall / Update Extension")

                open_ext_btn = QPushButton("Open Extensions App")
                open_ext_btn.clicked.connect(DesktopHelper.open_extensions_app)
                gnome_layout.addWidget(open_ext_btn)

            gnome_group.setLayout(gnome_layout)
            engine_layout.addWidget(gnome_group)

        # Behavior group (engine-related)
        behavior_group = QGroupBox()
        behavior_layout = QFormLayout()

        self.auto_start_cb = QCheckBox(i18n.t("autostart"))
        self.auto_start_cb.setChecked(self.config.get("autostart", False))
        self.auto_start_cb.stateChanged.connect(self._on_autostart_changed)
        behavior_layout.addRow(self.auto_start_cb)

        # Smart Pause Options
        self.pause_mode_combo = QComboBox()
        self.pause_mode_combo.addItems(
            [i18n.t("disabled"), i18n.t("pause_window"), i18n.t("pause_maximized"), i18n.t("pause_fullscreen")]
        )

        # Sync with config
        is_pause_enabled = self.config.get("pause_on_active", True)
        current_pause_mode = self.config.get("pause_mode", "Fullscreen")

        if not is_pause_enabled:
            self.pause_mode_combo.setCurrentText(i18n.t("disabled"))
        else:
            mode_map_inv = {
                "Any Window": i18n.t("pause_window"),
                "Maximized": i18n.t("pause_maximized"),
                "Fullscreen": i18n.t("pause_fullscreen"),
            }
            self.pause_mode_combo.setCurrentText(
                mode_map_inv.get(current_pause_mode, i18n.t("pause_fullscreen"))
            )

        self.pause_mode_combo.currentTextChanged.connect(self._on_pause_mode_changed)
        behavior_layout.addRow(QLabel(i18n.t("playback_mode") + ":"), self.pause_mode_combo)

        self.cpu_limit_combo = QComboBox()
        self.cpu_limit_combo.addItems(["50%", "70%", "85%", "95%", "Never"])
        current_cpu = self.config.get("pause_cpu_threshold", 85)
        self.cpu_limit_combo.setCurrentText(
            f"{current_cpu}%" if current_cpu < 100 else "Never"
        )
        self.cpu_limit_combo.currentTextChanged.connect(self._on_cpu_limit_changed)
        behavior_layout.addRow(QLabel("Pause if CPU >:"), self.cpu_limit_combo)

        behavior_group.setLayout(behavior_layout)
        engine_layout.addWidget(behavior_group)

        engine_layout.addStretch()
        self.tabs.addTab(engine_tab, i18n.t("engine_settings"))

        # Interface tab (customization)
        interface_tab = QWidget()
        interface_layout = QVBoxLayout(interface_tab)

        self.customization_section = CustomizationSection(self.config, parent=self)
        interface_layout.addWidget(self.customization_section)
        interface_layout.addStretch()
        self.tabs.addTab(interface_tab, i18n.t("interface_settings"))

        layout.addWidget(self.tabs)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _retranslate_ui(self):
        # Update tab texts and any dynamic labels
        self.tabs.setTabText(0, i18n.t("engine_settings"))
        self.tabs.setTabText(1, i18n.t("interface_settings"))
        # ensure customization section also updates
        if hasattr(self, 'customization_section'):
            self.customization_section._retranslate_ui()

    def _on_autostart_changed(self, state):
        enabled = (state == 2)
        self.config.set("autostart", enabled)
        DesktopHelper.setup_autostart(enabled)

    def _on_engine_changed(self, engine_name):
        self.config.set("engine", engine_name)
        if self.controller:
            self.controller.start_all(default_engine=engine_name)

    def _on_pause_mode_changed(self, text):
        # map back from translated text to internal values
        inv_map = {
            i18n.t("pause_window"): "Any Window",
            i18n.t("pause_maximized"): "Maximized",
            i18n.t("pause_fullscreen"): "Fullscreen",
        }

        if text == i18n.t("disabled"):
            self.config.set("pause_on_active", False)
        else:
            self.config.set("pause_on_active", True)
            self.config.set("pause_mode", inv_map.get(text, "Fullscreen"))

    def _on_cpu_limit_changed(self, text):
        if text == "Never":
            self.config.set("pause_cpu_threshold", 100)
        else:
            limit = int(text.replace("%", ""))
            self.config.set("pause_cpu_threshold", limit)

    def _install_gnome_extension(self):
        success, message = DesktopHelper.install_extension()
        if success:
            QMessageBox.information(self, "Extension Installed", message)
            self.install_ext_btn.setText("Reinstall / Update Extension")
        else:
            QMessageBox.critical(
                self, "Error", f"Could not install extension: {message}"
            )
