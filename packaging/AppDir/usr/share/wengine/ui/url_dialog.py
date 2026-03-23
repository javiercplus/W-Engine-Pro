from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QMessageBox,
)
import re


class UrlDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Wallpaper from URL")
        self.setFixedSize(500, 300)
        self.result_data = None

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/video.mp4")
        self.url_input.textChanged.connect(self.detect_type)
        form.addRow("URL:", self.url_input)

        self.name_input = QLineEdit()
        form.addRow("Name:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Auto Detect", "Video", "Web", "Stream", "YouTube"])
        form.addRow("Type:", self.type_combo)

        layout.addLayout(form)

        self.preview_label = QLabel("Enter a URL to preview type...")
        self.preview_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.preview_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.add_btn = QPushButton("Add Wallpaper")
        self.add_btn.setObjectName("add_btn")
        self.add_btn.clicked.connect(self.validate_and_accept)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.add_btn)
        layout.addLayout(btn_layout)

    def detect_type(self):
        url = self.url_input.text().strip()
        if not url:
            self.preview_label.setText("Enter a URL...")
            return

        w_type = "Web"
        if re.search(r"\.(mp4|webm|mkv|avi)$", url, re.I):
            w_type = "Video"
        elif "youtube.com" in url or "youtu.be" in url:
            w_type = "YouTube"
        elif url.endswith(".html") or url.endswith(".php"):
            w_type = "Web"
        elif url.endswith(".gif"):
            w_type = "Video"

        if self.type_combo.currentText() == "Auto Detect":
            self.preview_label.setText(f"Detected Type: {w_type}")

        if not self.name_input.text():
            self.name_input.setText(url.split("/")[-1])

    def validate_and_accept(self):
        url = self.url_input.text().strip()
        name = self.name_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid URL.")
            return

        w_type = self.type_combo.currentText()
        if w_type == "Auto Detect":
            if "youtube" in url:
                w_type = "YouTube"
            elif url.endswith(".mp4"):
                w_type = "Video"
            else:
                w_type = "Web"

        self.result_data = {"name": name or "New Wallpaper", "url": url, "type": w_type}
        self.accept()
