import os
import time
import socket
import json
import logging
import subprocess
import sys
from engines.base_backend import BaseBackend
from core.process_manager import ProcessManager

logger = logging.getLogger("GnomeVlcEngine")

class GnomeVlcEngine(BaseBackend):
    def __init__(self):
        self.proc_manager = ProcessManager()
        self.socket_path = "/tmp/wengine-vlc.sock"
        self.active_sockets = [self.socket_path]

    def start(self, config, video_path):
        self.stop()
        time.sleep(0.3)

        # 1. SET STATIC BLUR BACKGROUND (Transition)
        from core.desktop_helper import DesktopHelper
        DesktopHelper.set_static_blur_background(video_path)

        # Locate the helper script
        script_path = os.path.join(os.path.dirname(__file__), "vlc_wallpaper.py")
        
        volume = config.get_setting("volume", 50)
        mute = str(config.get_setting("mute", False)).lower()
        
        cmd = [
            "/usr/bin/python3",
            script_path,
            os.path.abspath(video_path),
            str(volume),
            mute,
            self.socket_path
        ]

        # AISLAMIENTO DE ENTORNO:
        # Si estamos en un AppImage, el PYTHONPATH apunta a Python 3.14.
        # El sistema usa 3.12. Debemos limpiar el entorno para que el proceso
        # hijo use sus propias librerías del sistema sin interferencias.
        env = os.environ.copy()
        for var in [
            "PYTHONPATH",
            "PYTHONHOME",
            "LD_LIBRARY_PATH",
            "LD_PRELOAD",
            "QT_PLUGIN_PATH",
        ]:
            if var in env:
                del env[var]

        logger.info(f"Starting GNOME VLC Engine: {' '.join(cmd)}")
        self.proc_manager.start("gnome-vlc-wallpaper", cmd, env=env)
        
        # Wait for socket to be ready
        for _ in range(30):
            if os.path.exists(self.socket_path):
                return True
            time.sleep(0.1)
        
        return False

    def stop(self):
        self.send_command("quit")
        self.proc_manager.stop("gnome-vlc-wallpaper")
        if os.path.exists(self.socket_path):
            try: os.remove(self.socket_path)
            except: pass

    def update_setting(self, key, value):
        if key in ["volume", "mute"]:
            return self.send_command("set_property", key, value)
        return False

    def send_command(self, command, *args):
        if not os.path.exists(self.socket_path):
            return False
        
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(0.5)
                client.connect(self.socket_path)
                msg = {"command": [command] + list(args)}
                client.sendall((json.dumps(msg) + "\n").encode())
                return True
        except:
            return False
