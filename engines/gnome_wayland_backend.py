import os
import time
import socket
import json
import logging
import shutil
import subprocess
from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from engines.base_backend import BaseBackend
from core.process_manager import ProcessManager
from core.desktop_helper import DesktopHelper


class GnomeWaylandBackend(BaseBackend):
    """
    Enhanced backend for GNOME (both Wayland and X11) using the 'Hidamari trick'
    and specialized GNOME extension support.
    """

    def __init__(self):
        self.proc_manager = ProcessManager()
        self.web_view = None
        self.base_socket_path = "/tmp/mpv-bg-socket-gnome"
        self.active_sockets = []

        # Intentar usar el mpv del bundle si estamos en un AppImage
        self.mpv_bin = "mpv"
        appdir = os.environ.get("APPDIR")
        if appdir and os.path.exists(os.path.join(appdir, "usr/bin/mpv")):
            self.mpv_bin = os.path.join(appdir, "usr/bin/mpv")
        else:
            self.mpv_bin = shutil.which("mpv")

        self.original_bg = (None, None)

    def start(self, config, video_path):
        self.stop()
        time.sleep(0.2)

        # 0. SAVE ORIGINAL BACKGROUND
        # We check if it's already one of our blurred ones to avoid saving a previous blur
        current_uri, current_uri_dark = DesktopHelper.get_current_background()
        if not "w_engine_blur_bg.png" in str(current_uri):
            self.original_bg = (current_uri, current_uri_dark)
            logging.info(f"Original background saved: {self.original_bg}")

        # 1. SET STATIC BLUR BACKGROUND (Transition)
        # This prevents a black screen/flicker while mpv loads.
        DesktopHelper.set_static_blur_background(video_path)

        engine_type = config.get_setting("engine", "mpv")

        if engine_type == "web":
            return self._start_web(video_path)
        else:
            success = self._start_mpv(config, video_path)
            QTimer.singleShot(1000, lambda: self._check_health())
            return success

    def _start_mpv(self, config, video_path):
        socket_path = f"{self.base_socket_path}-0"
        if os.path.exists(socket_path):
            try:
                os.remove(socket_path)
            except OSError:
                pass

        cmd = [self.mpv_bin] + self._build_mpv_args(config, socket_path)
        cmd.append(video_path)

        logging.info(f"[GnomeBackend] Starting MPV: {' '.join(cmd)}")
        self.proc_manager.start("gnome-mpv", cmd)
        self.active_sockets = [socket_path]
        return True

    def _build_mpv_args(self, config, socket_path):
        is_wayland = DesktopHelper.is_wayland()

        args = [
            "--force-window=yes",
            "--title=W-Engine-Gnome-Wallpaper",
            "--no-osc",
            "--no-osd-bar",
            "--no-input-default-bindings",
            f"--loop-file={'inf' if config.get_setting('loop', 'Loop') == 'Loop' else 'no'}",
            "--vo=gpu",
            f"--input-ipc-server={socket_path}",
            "--geometry=100%x100%",
            "--on-all-workspaces=yes",
            f"--hwdec={config.get_setting('hwdec', 'auto-safe')}",
            "--panscan=1.0",
            "--x11-name=wengine-wallpaper",
            "--no-keep-open",
            f"--mute={'yes' if config.get_setting('mute', False) else 'no'}",
        ]

        if is_wayland:
            args.append("--gpu-context=wayland")
        else:
            args.append("--gpu-context=x11")

        # Initial Pause Support
        if config.get_setting("_initial_pause", False):
            args.append("--pause")

        # 1. Video Quality / Resolution
        resolution_map = {
            "1080p (Full HD)": "scale=-1:1080",
            "720p (HD)": "scale=-1:720",
            "480p (SD)": "scale=-1:480",
        }
        res_setting = config.get_setting("video_resolution", "Nativa")
        if res_setting in resolution_map:
            args.append(f"--vf={resolution_map[res_setting]}")

        # 2. FPS Limit
        fps_limit = config.get_setting("fps_limit", 60)
        args.append(f"--override-display-fps={fps_limit}")

        # 3. GPU API
        gpu_api = config.get_setting("gpu_api", "auto")
        if gpu_api != "auto":
            args.append(f"--gpu-api={gpu_api}")

        # Cache flags from RendererManager
        cache_flags = config.get_setting("_mpv_cache_flags", [])
        args.extend(cache_flags)

        # Live properties
        for prop in ["brightness", "contrast", "saturation"]:
            val = config.get_setting(prop, 0)
            args.append(f"--{prop}={val}")

        # Gamma mapping: UI (0.1 to 5.0, neutral 1.0) -> MPV (-100 to 100, neutral 0)
        gamma_ui = config.get_setting("gamma", 1.0)
        if gamma_ui > 1.0:
            gamma_mpv = int((gamma_ui - 1.0) / 4.0 * 100)
        else:
            gamma_mpv = int((gamma_ui - 1.0) / 0.9 * 100)
        args.append(f"--gamma={gamma_mpv}")

        return [a for a in args if a]

    def _check_health(self):
        if not self.proc_manager.is_running("gnome-mpv"):
            logging.error("[GnomeBackend] MPV process died immediately.")

    def _start_web(self, url):
        logging.info(f"[GnomeBackend] Starting Web Engine: {url}")

        if not self.web_view:
            self.web_view = QWebEngineView()
            self.web_view.setWindowFlags(
                Qt.WindowType.Desktop
                | Qt.FramelessWindowHint
                | Qt.WindowStaysOnBottomHint
                | Qt.WindowDoesNotAcceptFocus
                | Qt.Tool
            )
            self.web_view.setAttribute(Qt.WA_TranslucentBackground)

            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
            settings.setAttribute(
                QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
            )

            from PySide6.QtGui import QGuiApplication

            screen = QGuiApplication.primaryScreen().geometry()
            self.web_view.setGeometry(screen)

        if url.startswith("http"):
            self.web_view.setUrl(QUrl(url))
        else:
            self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(url)))

        self.web_view.show()
        return True

    def stop(self):
        self.proc_manager.stop("gnome-mpv")

        if self.web_view:
            self.web_view.hide()

        import subprocess

        subprocess.run(
            ["pkill", "-f", "mpv.*mpv-bg-socket-gnome"], stderr=subprocess.DEVNULL
        )

        for s in self.active_sockets:
            if os.path.exists(s):
                try:
                    os.remove(s)
                except OSError:
                    pass
        self.active_sockets = []

        # 3. RESTORE ORIGINAL BACKGROUND
        if self.original_bg and self.original_bg[0]:
            logging.info(f"Restoring original background: {self.original_bg}")
            DesktopHelper.set_background(self.original_bg[0])
            self.original_bg = (None, None)

    def update_setting(self, key, value):
        logging.info(
            f"[GNOME_WAYLAND_BACKEND_DEBUG] update_setting received: key={key}, value={value}"
        )
        property_map = {
            "mute": "mute",
            "brightness": "brightness",
            "contrast": "contrast",
            "saturation": "saturation",
            "gamma": "gamma",
        }

        if key in property_map:
            mpv_prop = property_map[key]
            if key == "mute":
                value = "yes" if value else "no"
            elif key == "gamma":
                # Gamma mapping
                try:
                    gamma_ui = float(value)
                    if gamma_ui > 1.0:
                        value = int((gamma_ui - 1.0) / 4.0 * 100)
                    else:
                        value = int((gamma_ui - 1.0) / 0.9 * 100)
                except:
                    value = 0
            logging.info(
                f"[GNOME_WAYLAND_BACKEND_DEBUG] sending command: set_property, {mpv_prop}, {value}"
            )
            return self.send_command("set_property", mpv_prop, value)
        return False

    def send_command(self, command, *args):
        if not self.active_sockets:
            return False

        success = True
        for socket_path in self.active_sockets:
            if not os.path.exists(socket_path):
                success = False
                continue

            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(0.5)
                    client.connect(socket_path)
                    msg = {"command": [command] + list(args)}
                    client.sendall((json.dumps(msg) + "\n").encode())
            except (socket.error, socket.timeout):
                success = False
        return success
