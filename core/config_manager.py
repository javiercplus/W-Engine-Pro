import json
import os
import logging
from core.event_bus import EventBus
from PySide6.QtCore import QTimer, QObject

class ConfigManager(QObject):
    def __init__(self):
        super().__init__()
        self.config_path = os.path.expanduser("~/.config/w-engine-pro/config.json")
        self.data = {}
        self._load()
        self.event_bus = EventBus.instance()

        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save)

    def _load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = {}
        else:
            self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        if self.data.get(key) != value:
            self.data[key] = value
            self.event_bus.emit("config_changed", {"key": key, "value": value})
            if not self.save_timer.isActive():
                self.save_timer.start(500)
            else:
                self.save_timer.start(500)

    def _save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.data, f, indent=4)
            logging.debug("Config saved to disk.")
        except Exception as e:
            logging.error(f"Error saving config: {e}")