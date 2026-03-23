from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QHBoxLayout,
    QListWidget,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QSlider,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from typing import Any


class PropertiesPanel(QWidget):
    propertyChanged = Signal(str, Any)
    removeRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)

        # Debouncing to prevent IPC flooding and lag
        self._pending_updates = {}
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(
            40
        )  # 40ms is the sweet spot for responsiveness
        self._debounce_timer.timeout.connect(self._emit_pending_updates)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        self.preview_box = QLabel()
        self.preview_box.setFixedSize(290, 165)
        self.preview_box.setStyleSheet(
            "background-color: #000; border: 1px solid #444; border-radius: 4px;"
        )
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

    def _queue_update(self, key, value):
        self._pending_updates[key] = value
        self._debounce_timer.start()

    def _emit_pending_updates(self):
        for key, value in self._pending_updates.items():
            self.propertyChanged.emit(key, value)
        self._pending_updates.clear()

    def create_properties_group(self):
        self.prop_group = QGroupBox("Ajustes de Reproducción")
        form_layout = QFormLayout()

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(
            lambda v: self._queue_update("volume", v)
        )
        form_layout.addRow("Volumen:", self.volume_slider)

        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(
            lambda v: self._queue_update("brightness", v)
        )
        form_layout.addRow("Brillo:", self.brightness_slider)

        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(
            lambda v: self._queue_update("contrast", v)
        )
        form_layout.addRow("Contraste:", self.contrast_slider)

        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.valueChanged.connect(
            lambda v: self._queue_update("saturation", v)
        )
        form_layout.addRow("Saturación:", self.saturation_slider)

        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setRange(10, 500)  # 0.1 to 5.0
        self.gamma_slider.setValue(100)  # 1.0
        self.gamma_slider.valueChanged.connect(
            lambda v: self._queue_update("gamma", v / 100.0)
        )
        form_layout.addRow("Gamma:", self.gamma_slider)

        self.loop_combo = QComboBox()
        self.loop_combo.addItems(["Loop", "Stop"])
        self.loop_combo.currentTextChanged.connect(
            lambda t: self.propertyChanged.emit("loop", t)
        )
        form_layout.addRow("Bucle:", self.loop_combo)

        self.prop_group.setLayout(form_layout)
        self.layout.addWidget(self.prop_group)

    def create_slideshow_group(self):

        self.slideshow_group = QGroupBox("Configuración de Slideshow")
        form = QFormLayout(self.slideshow_group)

        self.random_check = QCheckBox("Temas Aleatorios")
        self.random_check.toggled.connect(
            lambda v: self.propertyChanged.emit("slideshow_random", v)
        )
        form.addRow(self.random_check)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setSuffix(" min")
        self.interval_spin.setValue(30)
        self.interval_spin.valueChanged.connect(
            lambda v: self.propertyChanged.emit("slideshow_interval", v)
        )
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
                self.preview_box.setPixmap(
                    pixmap.scaled(
                        self.preview_box.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
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

        self.brightness_slider.setValue(config.get("brightness", 0))
        self.contrast_slider.setValue(config.get("contrast", 0))
        self.saturation_slider.setValue(config.get("saturation", 0))
        self.gamma_slider.setValue(int(config.get("gamma", 1.0) * 100))

        loop = config.get("loop", "Loop")
        if loop == "Reverse":
            loop = "Loop"
        self.loop_combo.setCurrentText(loop)

        is_random = config.get("slideshow_random", False)
        self.random_check.setChecked(is_random)

        interval = config.get("slideshow_interval", 30)
        self.interval_spin.setValue(interval)

        self.blockSignals(False)
