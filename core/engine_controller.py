from core.renderer_manager import RendererManager
from core.event_bus import EventBus
from core.activity_monitor import ActivityMonitor
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QObject, Slot, QThread
import logging

class EngineController(QObject):
    def __init__(self, config_manager=None):
        super().__init__()
        self.config = config_manager
        self.renderer = RendererManager()
        self.monitors = self._detect_monitors()
        self.active_wallpapers = {}
        self.is_paused = False

        self.event_bus = EventBus.instance()
        self.event_bus.event_occurred.connect(self._on_event)

        self.activity_monitor = ActivityMonitor(self.config)
        self.activity_monitor.activityStateChanged.connect(self._on_activity_pause)
        self.monitor_thread = QThread()
        self.activity_monitor.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.activity_monitor.run)

        if self.config and self.config.get("pause_on_active", True):
            self.monitor_thread.start()

    @Slot(bool)
    def _on_activity_pause(self, should_pause):
        if self.config and not self.config.get("pause_on_active", True):
            return

        if should_pause:
            logging.info("[Controller] Pausa automática por actividad detectada.")
            self.renderer.send_command("set_property", "pause", True)
        else:
            logging.info("[Controller] Reanudación automática.")
            self.renderer.send_command("set_property", "pause", self.is_paused)

    @Slot(str, object)
    def _on_event(self, event_name, data):
        if event_name == "config_changed":
            key = data.get("key")
            value = data.get("value")
            self._apply_config_change(key, value)

    def _apply_config_change(self, key, value):
        logging.debug(f"Applying config change: {key} = {value}")

        dynamic_keys = ["volume", "mute", "playback_rate", "loop"]
        if key in dynamic_keys:
            self.renderer.update_setting(key, value)
            return

        restart_keys = [
            "engine", "gpu_api", "hwdec", "fps_limit", 
            "video_resolution", "draw_mode", "target_monitor", "layout_mode"
        ]
        if key in restart_keys:
            if self.active_wallpapers:
                monitor_id = next(iter(self.active_wallpapers))
                video_path = self.active_wallpapers[monitor_id]
                logging.info(f"Restarting renderer for setting change: {key}")
                self.renderer.restart(self.config, video_path)
            return

        if key == "pause_on_active":
            if value:
                if not self.monitor_thread.isRunning():
                    self.monitor_thread.start()
            else:
                self.activity_monitor.stop()
                self.monitor_thread.quit()
                self.monitor_thread.wait()

        ui_keys = ["theme", "ui_scaling", "accent_color"]
        if key in ui_keys:
            logging.debug(f"UI setting '{key}' changed. UI should handle this.")

    def _detect_monitors(self):
        """Detecta monitores usando Qt."""
        mons = []
        screens = QGuiApplication.screens()
        for i, screen in enumerate(screens):
            mons.append({
                "id": i,
                "name": screen.name(),
                "geometry": screen.geometry()
            })
        return mons

    def start_all(self, default_engine="mpv"):
        """Restaura los fondos guardados o inicia el default."""
        last_wp = self.config.get("last_wallpaper")
        if last_wp:
             self.set_wallpaper_for_monitor(0, last_wp)

    def stop_all(self):
        self.renderer.stop()
        self.active_wallpapers.clear()

    def pause_all(self):
        self.is_paused = not self.is_paused
        self.renderer.send_command("set_property", "pause", self.is_paused)
        print(f"[Controller] {'Pausado' if self.is_paused else 'Reanudado'}")

    def set_wallpaper_for_monitor(self, monitor_id, video_path):
        if self.active_wallpapers.get(monitor_id) == video_path:
            return

        if self.config:
            self.config.set("last_wallpaper", video_path)

        self.active_wallpapers[monitor_id] = video_path
        self.renderer.restart(self.config, video_path)

    def shutdown(self):
        self.activity_monitor.stop()
        self.monitor_thread.quit()
        self.monitor_thread.wait()
        self.stop_all()