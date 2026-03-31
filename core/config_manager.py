import json
import os
import logging
from core.event_bus import EventBus
from PySide6.QtCore import QTimer, QObject, Signal
from typing import Any


class ConfigManager(QObject):
    setting_changed = Signal(str, Any)

    def __init__(self):
        super().__init__()
        self.config_path = os.path.expanduser("~/.config/w-engine-pro/config.json")
        self.data = {}

        # Create save_timer before loading so _load can safely call it.
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save)

        self.event_bus = EventBus.instance()
        self._load()

    def _load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    self.data = json.load(f)
            except Exception as e:
                logging.error(f"Error loading config: {e}")
                self.data = {}
        else:
            self.data = {}

        # Force mute default to True (wallpaper should be silent by default)
        if self.data.get("mute") is False:
            self.data["mute"] = True
            self.save_timer.start(500)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def get_setting(self, key, default=None):
        """Alias for get to ensure compatibility with all modules."""
        return self.get(key, default)

    def get_playback_mode(self):
        return self.get("playback_mode", "Auto")

    def set_playback_mode(self, mode):
        self.set("playback_mode", mode)

    def set(self, key, value):
        if self.data.get(key) != value:
            self.data[key] = value
            self.setting_changed.emit(key, value)
            self.event_bus.emit("config_changed", {"key": key, "value": value})

            # Skip saving for volatile keys (starting with _)
            if key.startswith("_"):
                return

            self.save_timer.start(500)

    def get_volatile(self, key, default=None):
        """Gets a volatile setting (those starting with _)."""
        if not key.startswith("_"):
            key = "_" + key
        return self.get(key, default)

    def set_volatile(self, key, value):
        """Sets a setting without saving it to disk. Automatically adds underscore prefix if missing."""
        if not key.startswith("_"):
            key = "_" + key
        self.set(key, value)

    def set_setting(self, key, value):
        """Alias for set to ensure compatibility with all modules."""
        self.set(key, value)

    def _save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.data, f, indent=4)
            logging.debug(f"Config saved to {self.config_path}")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
