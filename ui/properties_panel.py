from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSlider, QComboBox, QGroupBox, QFormLayout, QHBoxLayout, QListWidget, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

class PropertiesPanel(QWidget):
    propertyChanged = Signal(str, object)
    removeRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)
        
        self.preview_box = QLabel()
        self.preview_box.setFixedSize(290, 165)
        self.preview_box.setStyleSheet("background-color: #000; border: 1px solid #444; border-radius: 4px;")
        self.preview_box.setAlignment(Qt.AlignCenter)
        self.preview_box.setText("Selecciona un fondo")
        self.layout.addWidget(self.preview_box)
        
        self.title_label = QLabel("Sin Selección")
        self.title_label.setObjectName("title")
        self.layout.addWidget(self.title_label)
        
        self.type_label = QLabel("Tipo: -")
        self.layout.addWidget(self.type_label)
        
        self.create_properties_group()
        
        self.create_slideshow_group()
        
        self.layout.addStretch()

        actions_layout = QHBoxLayout()
        self.remove_btn = QPushButton("Eliminar")
        self.remove_btn.setObjectName("remove_btn")
        self.remove_btn.clicked.connect(self.removeRequested.emit)
        
        self.apply_btn = QPushButton("Aplicar Ahora")
        self.apply_btn.setObjectName("apply_btn")
        
        actions_layout.addWidget(self.remove_btn)
        actions_layout.addWidget(self.apply_btn)
        self.layout.addLayout(actions_layout)

    def create_properties_group(self):
        self.prop_group = QGroupBox("Ajustes de Reproducción")
        form_layout = QFormLayout()
        
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(50, 200)
        self.rate_slider.setValue(100)
        self.rate_slider.valueChanged.connect(lambda v: self.propertyChanged.emit("playback_rate", v/100.0))
        form_layout.addRow("Velocidad:", self.rate_slider)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(lambda v: self.propertyChanged.emit("volume", v))
        form_layout.addRow("Volumen:", self.volume_slider)
        
        self.loop_combo = QComboBox()
        self.loop_combo.addItems(["Loop", "Stop"])
        self.loop_combo.currentTextChanged.connect(lambda t: self.propertyChanged.emit("loop", t))
        form_layout.addRow("Bucle:", self.loop_combo)
        
        self.prop_group.setLayout(form_layout)
        self.layout.addWidget(self.prop_group)

    def create_slideshow_group(self):
        self.slideshow_group = QGroupBox("Configuración de Slideshow")
        form = QFormLayout(self.slideshow_group)
        
        self.random_check = QCheckBox("Temas Aleatorios")
        self.random_check.toggled.connect(lambda v: self.propertyChanged.emit("slideshow_random", v))
        form.addRow(self.random_check)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setSuffix(" min")
        self.interval_spin.setValue(30)
        self.interval_spin.valueChanged.connect(lambda v: self.propertyChanged.emit("slideshow_interval", v))
        form.addRow("Cambiar cada:", self.interval_spin)
        
        self.layout.addWidget(self.slideshow_group)

    def load_wallpaper(self, name, w_type, path, thumbnail=None, config=None):
        self.title_label.setText(name)
        self.type_label.setText(f"Tipo: {w_type}")
        
        if config:
            self.update_from_config(config)
        
        if thumbnail:
            pixmap = QPixmap(thumbnail)
            if not pixmap.isNull():
                self.preview_box.setPixmap(pixmap.scaled(
                    self.preview_box.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))
                return
        elif self.preview_box.pixmap():
            return

        self.preview_box.clear()
        self.preview_box.setText(f"Vista previa\n{name}")

    def update_from_config(self, config):
        """Syncs sliders and combos with current config values."""
        self.blockSignals(True)
        
        volume = config.get("volume", 50)
        self.volume_slider.setValue(volume)
        
        rate = config.get("playback_rate", 1.0)
        self.rate_slider.setValue(int(rate * 100))
        
        loop = config.get("loop", "Loop")
        if loop == "Reverse": loop = "Loop"
        self.loop_combo.setCurrentText(loop)

        is_random = config.get("slideshow_random", False)
        self.random_check.setChecked(is_random)

        interval = config.get("slideshow_interval", 30)
        self.interval_spin.setValue(interval)
        
        self.blockSignals(False)
