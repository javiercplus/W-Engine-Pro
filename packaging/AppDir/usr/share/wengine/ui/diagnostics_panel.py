import json
import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QGridLayout,
    QScrollArea,
    QTextEdit,
)
from PySide6.QtCore import Qt, QTimer


class DiagnosticsPanel(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        main_layout = QVBoxLayout(self)

        # Scroll Area for diagnostic cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        container = QWidget()
        self.grid = QGridLayout(container)

        self.create_status_cards()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Actions Area
        actions_group = QGroupBox("System Actions")
        actions_layout = QHBoxLayout(actions_group)

        self.restart_btn = QPushButton("Restart Engine")
        self.restart_btn.clicked.connect(
            lambda: self.controller.renderer.restart(
                self.controller.config,
                (
                    self.controller.last_video
                    if hasattr(self.controller, "last_video")
                    else None
                ),
            )
        )

        self.safe_mode_btn = QPushButton("Force Safe Mode")
        self.safe_mode_btn.clicked.connect(self._toggle_safe_mode)

        self.export_btn = QPushButton("Export Diagnostic (JSON)")
        self.export_btn.clicked.connect(self._export_to_clipboard)

        actions_layout.addWidget(self.restart_btn)
        actions_layout.addWidget(self.safe_mode_btn)
        actions_layout.addWidget(self.export_btn)

        main_layout.addWidget(actions_group)

        # Auto-refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)

    def showEvent(self, event):
        super().showEvent(event)
        self.timer.start(2000)
        self.refresh()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()

    def create_status_cards(self):
        # We'll keep labels in a dict for easy updating
        self.status_labels = {}

        metrics = [
            ("Backend", "backend"),
            ("Protocol", "protocol"),
            ("Compositor", "compositor"),
            ("GPU Vendor", "gpu_vendor"),
            ("IPC Status", "ipc_ok"),
            ("Safe Mode", "safe_mode"),
            ("Playback Mode", "playback_mode"),
            ("Resolved Mode", "current_playback_mode"),
            ("Cache Config", "cache_status"),
            ("RAM Usage", "ram_usage_mb"),
            ("CPU Load", "cpu_percent"),
        ]

        for i, (label_text, key) in enumerate(metrics):
            row, col = i // 3, i % 3
            group = QGroupBox(label_text)
            layout = QVBoxLayout(group)
            val_label = QLabel("...")
            val_label.setAlignment(Qt.AlignCenter)
            val_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #3498db;"
            )
            layout.addWidget(val_label)
            self.status_labels[key] = val_label
            self.grid.addWidget(group, row, col)

    def refresh(self):
        data = self.controller.get_diagnostics()

        for key, label in self.status_labels.items():
            val = data.get(key)
            if key == "ipc_ok":
                val = "CONNECTED" if val else "FAILED"
            elif key == "safe_mode":
                val = "ACTIVE" if val else "Normal"
            elif key == "ram_usage_mb":
                val = f"{val} MB"
            elif key == "cpu_percent":
                val = f"{val}%"
            elif key == "cache_status":
                size = data.get("cache_size", "0")
                secs = data.get("cache_secs", 0)
                val = f"{size} / {secs}s"

            label.setText(str(val))

            # Highlight failures
            if key == "ipc_ok" and not data.get("ipc_ok"):
                label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            elif key == "safe_mode" and data.get("safe_mode"):
                label.setStyleSheet("color: #f39c12; font-weight: bold;")
            elif key == "current_playback_mode":
                color = "#2ecc71" if val == "Memory" else "#3498db"
                label.setStyleSheet(f"color: {color}; font-weight: bold;")
            else:
                label.setStyleSheet("color: #3498db; font-weight: bold;")

    def _toggle_safe_mode(self):
        self.controller.renderer.safe_mode = not self.controller.renderer.safe_mode
        self.refresh()

    def _export_to_clipboard(self):
        data = self.controller.get_diagnostics()
        data["exported_at"] = datetime.datetime.utcnow().isoformat()
        json_str = json.dumps(data, indent=4)

        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(json_str)
        self.export_btn.setText("Copied to Clipboard!")
        QTimer.singleShot(
            2000, lambda: self.export_btn.setText("Export Diagnostic (JSON)")
        )
