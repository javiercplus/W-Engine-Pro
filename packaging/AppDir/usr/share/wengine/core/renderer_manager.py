import os
import logging
import gc
import psutil
from core.desktop_helper import DesktopHelper
from engines.x11_backend import X11Backend
from engines.wayland_backend import WaylandBackend
from engines.gnome_wayland_backend import GnomeWaylandBackend
from engines.gnome_vlc_backend import GnomeVlcEngine
from core.logger import log_event


class RendererManager:
    """
    Manages the rendering process natively.
    All packaging-specific logic (Flatpak/AppImage) has been removed for native stability.
    """

    def __init__(self):
        self.profile = DesktopHelper.get_profile()
        self.backend = self._initialize_backend()
        self.safe_mode = False
        self.last_config = None
        self.last_video = None
        self.playback_mode = "Auto"
        self.current_mode = "Disk"
        self.cache_info = {"size": "0", "secs": 0}

        from core.process_manager import ProcessManager

        ProcessManager().set_error_callback(self._on_critical_error)

    def _on_critical_error(self, name, error_type):
        self.profile.metrics.restarts += 1
        if error_type == "gpu_fail" and not self.safe_mode:
            self.safe_mode = True
            if self.last_config and self.last_video:
                self.restart(self.last_config, self.last_video)

    def _initialize_backend(self):
        best = self.profile.get_best_backend()
        # Selección nativa de backend
        if best == "gnome_fake":
            return GnomeVlcEngine()
        elif best == "x11":
            return X11Backend()
        else:
            return WaylandBackend()

    def is_running(self):
        return any(
            name.startswith(("x11-wallpaper", "wayland-wallpaper", "gnome-mpv"))
            for name in self.backend.proc_manager.processes.keys()
        )

    def apply_mode_live(self, mode):
        if not self.last_video:
            return
        self.playback_mode = mode
        self.current_mode, reason = self.resolve_playback_mode(self.last_video)
        ram_free = psutil.virtual_memory().available
        flags, size, secs = self._calculate_cache_params(self.current_mode, ram_free)
        self.cache_info = {"size": size, "secs": secs}
        if self.current_mode == "Memory":
            self.send_command("set_property", "cache", "yes")
            self.send_command("set_property", "demuxer-max-bytes", size)
            self.send_command("set_property", "cache-secs", secs)
        else:
            self.send_command("set_property", "cache", "no")

    def send_command(self, command, *args):
        return self.backend.send_command(command, *args)

    def update_setting(self, key, value):
        return self.backend.update_setting(key, value)

    def restart(self, config, video_path, initial_pause=False):
        self.stop()
        return self.start(config, video_path, initial_pause)

    def start(self, config, video_path, initial_pause=False):
        if not video_path:
            return False
        self.last_config = config
        self.last_video = video_path

        # Pasar info del compositor al backend
        config.set_volatile("compositor", self.profile.compositor)

        self.playback_mode = config.get_setting("playback_mode", "Auto")
        ram_info = psutil.virtual_memory()

        self.current_mode, reason = self.resolve_playback_mode(video_path)
        cache_flags, size, secs = self._calculate_cache_params(
            self.current_mode, ram_info.available
        )
        self.cache_info = {"size": size, "secs": secs}

        config.set_setting("_initial_pause", initial_pause)
        config.set_setting("_mpv_cache_flags", cache_flags)

        return self.backend.start(config, video_path)

    def get_active_sockets(self):
        if hasattr(self.backend, "active_sockets"):
            return self.backend.active_sockets
        return []

    def resolve_playback_mode(self, video_path):
        if "Memory" in self.playback_mode:
            return "Memory", "user_forced"
        if "Disk" in self.playback_mode:
            return "Disk", "user_forced"
        ram_info = psutil.virtual_memory()
        available_gb = ram_info.available / 1024**3
        try:
            file_size_mb = os.path.getsize(video_path) / 1024**2
            if available_gb < 1.5:
                return "Disk", "low_ram"
            if file_size_mb < 200 and available_gb > 2:
                return "Memory", "light_video"
        except:
            pass
        return "Disk", "heavy_video"

    def _calculate_cache_params(self, mode, ram_free):
        if mode == "Disk":
            return ["--cache=no"], "0", 0
        ram_free_gb = ram_free / 1024**3
        if ram_free_gb > 4:
            size, secs = "400M", 120
        elif ram_free_gb > 2:
            size, secs = "200M", 60
        else:
            size, secs = "50M", 30
        return (
            [
                "--cache=yes",
                f"--cache-secs={secs}",
                f"--demuxer-max-bytes={size}",
                "--demuxer-readahead-secs=30",
            ],
            size,
            secs,
        )

    def stop(self):
        if self.backend:
            self.backend.stop()
            gc.collect()
