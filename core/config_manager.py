import json
import logging
import os
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal

from core.event_bus import EventBus


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

        # Mute setting is now controlled entirely by user config
        # No default value is forced on startup

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
        """
        Set a configuration key and emit appropriate signals/events.

        This implementation is defensive:
        - Emitting signals and events is wrapped to avoid crashing callers
          if a subscriber misbehaves.
        - Certain keys that control playback or theming are persisted
          immediately to disk (best-effort) to avoid losing critical state
          when the application is closed quickly after a change.
        - Volatile keys (prefixed with '_') are not saved.
        """
        if self.data.get(key) != value:
            self.data[key] = value

            # Emit the local Qt signal safely.
            try:
                self.setting_changed.emit(key, value)
            except Exception as e:
                logging.error(
                    f"[ConfigManager] Error emitting setting_changed for {key}: {e}"
                )

            logging.info(
                f"[ConfigManager] Emitting config_changed: key={key}, value={value}"
            )

            # Emit via the event bus safely.
            try:
                self.event_bus.emit("config_changed", {"key": key, "value": value})
            except Exception as e:
                logging.error(
                    f"[ConfigManager] Error emitting event_bus 'config_changed' for {key}: {e}"
                )

            # Skip saving for volatile keys (starting with _)
            if key.startswith("_"):
                return

            # Keys that should be persisted immediately to reduce chance of loss.
            immediate_persist_keys = {
                "mute",
                "volume",
                "loop",
                "fit",
                "brightness",
                "contrast",
                "saturation",
                "gamma",
                "playback_mode",
                # Theme-related keys
                "theme",
                "accent_color",
                "ui_bg_color",
                "ui_text_color",
                "ui_font",
                "window_transparency",
            }

            if key in immediate_persist_keys:
                # Stop any pending timer saves and attempt an immediate, best-effort save.
                try:
                    if hasattr(self, "save_timer") and self.save_timer.isActive():
                        self.save_timer.stop()
                except Exception:
                    # If we can't inspect/stop the timer, continue to try saving.
                    pass

                try:
                    # Use internal save routine; _save does fsync/flush attempts.
                    self._save()
                except Exception as e:
                    logging.error(
                        f"[ConfigManager] Immediate save failed for {key}: {e}"
                    )
                return

            # Otherwise debounce the save to avoid frequent disk writes.
            try:
                self.save_timer.start(500)
            except Exception as e:
                logging.error(f"[ConfigManager] Failed to start save timer: {e}")

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
        # Stop the save timer if it's still active to avoid overlapping saves
        try:
            if hasattr(self, "save_timer") and self.save_timer.isActive():
                self.save_timer.stop()
        except Exception:
            # If anything goes wrong checking/stopping the timer, continue to save
            pass

        try:
            # Write and flush to ensure the file is written to disk promptly.
            # Also attempt to fsync to reduce the chance of the data being lost
            # on abrupt termination (best-effort; ignore failures).
            with open(self.config_path, "w") as f:
                json.dump(self.data, f, indent=4)
                try:
                    f.flush()
                except Exception:
                    pass
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            logging.debug(f"Config saved to {self.config_path}")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
