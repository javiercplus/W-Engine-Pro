from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QLabel, QComboBox, QGroupBox, QFormLayout, QScrollArea
)
from PySide6.QtCore import Qt

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
        self.engine_combo.currentTextChanged.connect(self._change_engine)
        engine_layout.addRow("Active Engine:", self.engine_combo)
        
        self.hwdec_combo = QComboBox()
        self.hwdec_combo.addItems(["auto", "vaapi", "nvdec", "none"])
        self.hwdec_combo.setCurrentText(self.config.get("hwdec", "auto"))
        self.hwdec_combo.currentTextChanged.connect(lambda v: self.config.set("hwdec", v))
        engine_layout.addRow("Hardware Decoding:", self.hwdec_combo)
        
        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)
        
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.auto_start_cb = QCheckBox("Start with System (Auto-Start)")
        self.auto_start_cb.setChecked(self.config.get("autostart", False))
        self.auto_start_cb.stateChanged.connect(lambda s: self.config.set("autostart", s == 2))
        behavior_layout.addWidget(self.auto_start_cb)
        
        self.pause_cb = QCheckBox("Pause when a window is maximized")
        self.pause_cb.setChecked(self.config.get("pause_on_active", True))
        self.pause_cb.stateChanged.connect(lambda s: self.config.set("pause_on_active", s == 2))
        behavior_layout.addWidget(self.pause_cb)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _change_engine(self, engine_name):
        self.config.set("engine", engine_name)
        if self.controller:
            self.controller.start_all(default_engine=engine_name)
