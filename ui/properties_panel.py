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

from core import i18n


class PropertiesPanel(QWidget):
    propertyChanged = Signal(str, Any)
    removeRequested = Signal()
    stopAllRequested = Signal()
    startRequested = Signal()

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
        self.preview_box.setText(i18n.t("select_wallpaper"))
        self.layout.addWidget(self.preview_box)

        self.stop_btn = QPushButton(i18n.t("stop"))
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.clicked.connect(self._on_stop_btn_clicked)
        self.layout.addWidget(self.stop_btn)

        self.title_label = QLabel(i18n.t("no_selection"))
        self.title_label.setObjectName("title")
        self.layout.addWidget(self.title_label)

        self.type_label = QLabel(f"{i18n.t('type_label')}: -")
        self.layout.addWidget(self.type_label)

        self.create_properties_group()

        self.create_slideshow_group()

        self.layout.addStretch()

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setObjectName("remove_btn")
        self.remove_btn.clicked.connect(self.removeRequested.emit)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("apply_btn")

        actions_layout.addWidget(self.remove_btn)
        actions_layout.addWidget(self.apply_btn)
        actions_layout.addStretch()
        self.layout.addLayout(actions_layout)

    def _queue_update(self, key, value):
        self._pending_updates[key] = value
        self._debounce_timer.start()

    def _emit_pending_updates(self):
        for key, value in self._pending_updates.items():
            self.propertyChanged.emit(key, value)
        self._pending_updates.clear()

    def _on_stop_btn_clicked(self):
        if self.stop_btn.text() == i18n.t("stop"):
            self.stopAllRequested.emit()
        else:
            self.startRequested.emit()

    def update_stop_button_state(self, is_running):
        if is_running:
            self.stop_btn.setText(i18n.t("stop"))
        else:
            self.stop_btn.setText(i18n.t("start"))

    def create_properties_group(self):
        self.prop_group = QGroupBox(i18n.t("playback_settings"))
        form_layout = QFormLayout()

        self.mute_check = QCheckBox(i18n.t("mute_audio"))
        self.mute_check.setChecked(True)
        self.mute_check.toggled.connect(
            lambda v: self._queue_update("mute", v)
        )
        form_layout.addRow("", self.mute_check)

        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(
            lambda v: self._queue_update("brightness", v)
        )
        form_layout.addRow(i18n.t("brightness") + ":", self.brightness_slider)

        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(
            lambda v: self._queue_update("contrast", v)
        )
        form_layout.addRow(i18n.t("contrast") + ":", self.contrast_slider)

        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.valueChanged.connect(
            lambda v: self._queue_update("saturation", v)
        )
        form_layout.addRow(i18n.t("saturation") + ":", self.saturation_slider)

        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setRange(10, 500)  # 0.1 to 5.0
        self.gamma_slider.setValue(100)  # 1.0
        self.gamma_slider.valueChanged.connect(
            lambda v: self._queue_update("gamma", v / 100.0)
        )
        form_layout.addRow(i18n.t("gamma") + ":", self.gamma_slider)

        self.loop_combo = QComboBox()
        self.loop_combo.addItems([i18n.t("loop_one"), i18n.t("stop_loop")])
        self.loop_combo.currentTextChanged.connect(
            lambda t: self.propertyChanged.emit("loop", t)
        )
        form_layout.addRow(i18n.t("loop") + ":", self.loop_combo)

        self.prop_group.setLayout(form_layout)
        self.layout.addWidget(self.prop_group)

    def create_slideshow_group(self):

        self.slideshow_group = QGroupBox(i18n.t("slideshow_settings"))
        form = QFormLayout(self.slideshow_group)

        self.random_check = QCheckBox(i18n.t("random_themes"))
        self.random_check.toggled.connect(
            lambda v: self.propertyChanged.emit("slideshow_random", v)
        )
        form.addRow(self.random_check)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setSuffix(" " + i18n.t("minutes"))
        self.interval_spin.setValue(30)
        self.interval_spin.valueChanged.connect(
            lambda v: self.propertyChanged.emit("slideshow_interval", v)
        )
        form.addRow(i18n.t("change_every") + ":", self.interval_spin)

        self.layout.addWidget(self.slideshow_group)

    def load_wallpaper(self, name, w_type, path, thumbnail=None, config=None):
        self.title_label.setText(name)
        self.type_label.setText(f"{i18n.t('type_label')}: {w_type}")

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
        self.preview_box.setText(f"{i18n.t('preview')}\n{name}")

    def update_from_config(self, config):
        """Syncs sliders and combos with current config values."""
        self.blockSignals(True)

        self.mute_check.setChecked(config.get("mute", True))

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
