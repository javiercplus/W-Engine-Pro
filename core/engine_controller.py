import logging
import os
from typing import Any

from PySide6.QtCore import QObject, QThread, QTimer, Slot
from PySide6.QtGui import QGuiApplication

from core.activity_monitor import ActivityMonitor
from core.event_bus import EventBus
from core.health_monitor import HealthMonitor
from core.renderer_manager import RendererManager


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

        # Health Monitor for IPC
        self.health_monitor = HealthMonitor(self.renderer)
        self.health_monitor.start()

        # Environment Information
        profile = self.renderer.profile
        logging.info(
            f"[Controller] Env: {profile.protocol.upper()} | "
            f"DE: {profile.compositor} | "
            f"GPU: {profile.gpu_vendor} | "
            f"Best Backend: {profile.get_best_backend()}"
        )

        # Activity monitor setup
        self.activity_monitor = ActivityMonitor(self.config)
        self.activity_monitor.activityStateChanged.connect(self._on_activity_pause)
        self.monitor_thread = QThread()
        self.activity_monitor.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.activity_monitor.run)

        if self.config and self.config.get_setting("pause_on_active", True):
            self.monitor_thread.start()

    @Slot(bool)
    def _on_activity_pause(self, should_pause):
        if self.config and not self.config.get_setting("pause_on_active", True):
            return

        if should_pause:
            logging.info("[Controller] Auto-pause triggered by activity.")
            self.health_monitor.set_paused(True)
            self.renderer.send_command("set_property", "pause", True)
        else:
            logging.info("[Controller] Auto-resume.")
            self.health_monitor.set_paused(self.is_paused)
            self.renderer.send_command("set_property", "pause", self.is_paused)

    @Slot(str, Any)
    def _on_event(self, event_name, data):
        if event_name == "config_changed":
            key = data.get("key")
            value = data.get("value")
            self._apply_config_change(key, value)

    def _apply_config_change(self, key, value):
        logging.info(
            f"[CONTROLLER_DEBUG] Applying config change: key={key}, value={value}"
        )
        logging.debug(f"Applying config change: {key} = {value}")

        dynamic_keys = [
            "volume",
            "mute",
            "loop",
            "fit",
            "brightness",
            "contrast",
            "saturation",
            "gamma",
            "pause_mode",
        ]
        if key in dynamic_keys:
            self.renderer.update_setting(key, value)
            return

        if key == "playback_mode":
            if self.renderer.is_running():
                self.renderer.apply_mode_live(value)
            else:
                self.apply_playback_mode(value)
            return

        restart_keys = [
            "engine",
            "gpu_api",
            "hwdec",
            "fps_limit",
            "video_resolution",
            "draw_mode",
            "target_monitor",
            "layout_mode",
            "video_cache",
        ]
        if key in restart_keys:
            if self.active_wallpapers:
                logging.info(f"Restarting all renderers due to config: {key}")

                self.health_monitor.trigger_grace_period(10.0)

                current_activity_pause = getattr(
                    self.activity_monitor, "_last_pause_state", False
                )
                current_pause_state = self.is_paused or current_activity_pause

                self.health_monitor.set_paused(current_pause_state)

                for monitor_id, video_path in list(self.active_wallpapers.items()):
                    self.renderer.restart(
                        self.config, video_path, initial_pause=current_pause_state
                    )
            return

        if key == "pause_on_active":
            if value:
                if not self.monitor_thread.isRunning():
                    self.monitor_thread.start()
            else:
                self.activity_monitor.stop()
                self.monitor_thread.quit()
                self.monitor_thread.wait(1000)

    def apply_playback_mode(self, mode):
        logging.info(f"[Controller] Playback mode set to: {mode}")
        if self.active_wallpapers:
            monitor_id = next(iter(self.active_wallpapers))
            video_path = self.active_wallpapers[monitor_id]
            self.renderer.restart(self.config, video_path)

    def _detect_monitors(self):
        mons = []
        screens = QGuiApplication.screens()
        for i, screen in enumerate(screens):
            mons.append({"id": i, "name": screen.name(), "geometry": screen.geometry()})
        return mons

    def start_all(self, default_engine="mpv"):
        last_wp = self.config.get_setting("last_wallpaper")
        if last_wp:
            self.set_wallpaper_for_monitor(0, last_wp)

    def stop_all(self):
        self.renderer.stop()
        self.active_wallpapers.clear()

    def pause_all(self):
        self.is_paused = not self.is_paused
        self.health_monitor.set_paused(self.is_paused)
        self.renderer.send_command("set_property", "pause", self.is_paused)
        logging.info(f"[Controller] {'Paused' if self.is_paused else 'Resumed'}")

    def set_wallpaper_for_monitor(self, monitor_id, video_path):
        if self.active_wallpapers.get(monitor_id) == video_path:
            return

        if self.config:
            self.config.set_setting("last_wallpaper", video_path)

        self.active_wallpapers[monitor_id] = video_path
        self.health_monitor.trigger_grace_period(20.0)
        self.renderer.restart(self.config, video_path)

    def shutdown(self):
        logging.info("[Controller] Shutting down...")
        self.health_monitor.stop()
        if self.monitor_thread.isRunning():
            self.activity_monitor.stop()
            self.monitor_thread.quit()
            if not self.monitor_thread.wait(1000):
                self.monitor_thread.terminate()
                self.monitor_thread.wait()

        self.stop_all()

    def get_diagnostics(self) -> dict:
        """Collects all real-time engine and system status for the UI."""
        import time

        import psutil

        now = time.time()
        if not hasattr(self, "_diag_cache"):
            self._diag_cache = {"last_update": 0, "battery": None, "cpu_percent": 0}

        if now - self._diag_cache["last_update"] > 2.0:
            self._diag_cache["battery"] = psutil.sensors_battery()
            self._diag_cache["cpu_percent"] = psutil.cpu_percent()
            self._diag_cache["last_update"] = now

        battery = self._diag_cache["battery"]
        cpu_percent = self._diag_cache["cpu_percent"]

        # Check IPC status for all active sockets
        active_sockets = self.renderer.get_active_sockets()
        ipc_ok = False
        if active_sockets:
            for s in active_sockets:
                try:
                    if os.path.exists(s) and self.health_monitor._check_ipc(s):
                        ipc_ok = True
                        break
                    else:
                        logging.debug(f"[Diagnostics] IPC check failed for {s}")
                except Exception as e:
                    logging.debug(f"[Diagnostics] IPC check error: {e}")
                    break
        else:
            logging.debug("[Diagnostics] No active sockets found")

        return {
            "backend": self.renderer.backend.__class__.__name__,
            "protocol": self.renderer.profile.protocol,
            "compositor": self.renderer.profile.compositor,
            "gpu_vendor": self.renderer.profile.gpu_vendor,
            "safe_mode": self.renderer.safe_mode,
            "playback_mode": self.config.get_setting("playback_mode", "Auto"),
            "current_playback_mode": self.renderer.current_mode,
            "cache_size": self.renderer.cache_info["size"],
            "cache_secs": self.renderer.cache_info["secs"],
            "ipc_ok": ipc_ok,
            "monitors": [m["name"] for m in self.monitors],
            "ram_usage_mb": int(psutil.Process().memory_info().rss / 1024 / 1024),
            "cpu_percent": cpu_percent,
            "battery": (
                {
                    "percent": int(battery.percent) if battery else 100,
                    "plugged": battery.power_plugged if battery else True,
                }
                if battery
                else None
            ),
            "metrics": self.renderer.profile.metrics.to_dict(),
        }
