import os
import time
import socket
import json
import logging
import subprocess
import sys
from engines.base_backend import BaseBackend
from core.process_manager import ProcessManager

logger = logging.getLogger("GnomeIntegratedEngine")

class GnomeIntegratedEngine(BaseBackend):
    def __init__(self):
        self.proc_manager = ProcessManager()
        self.socket_path = "/tmp/wengine-mpv.sock"
        self.active_sockets = [self.socket_path]

    def start(self, config, video_path):
        self.stop()
        time.sleep(0.3)

        # 1. SET STATIC BLUR BACKGROUND
        from core.desktop_helper import DesktopHelper
        DesktopHelper.set_static_blur_background(video_path)

        # Usar el nuevo script de integración nativa con MPV
        script_path = os.path.join(os.path.dirname(__file__), "mpv_gtk_wallpaper.py")
        
        # Obtener resolución de la configuración
        res_setting = config.get_setting("video_resolution", "Nativa")
        
        cmd = [
            sys.executable,
            script_path,
            os.path.abspath(video_path),
            self.socket_path,
            res_setting
        ]

        # Limpieza de entorno
        env = os.environ.copy()
        for var in ["PYTHONPATH", "PYTHONHOME", "LD_LIBRARY_PATH"]:
            if var in env: del env[var]
        env["GDK_BACKEND"] = "x11"

        logger.info(f"Starting GNOME Integrated-MPV Engine: {' '.join(cmd)}")
        self.proc_manager.start("gnome-integrated-wallpaper", cmd, env=env)
        
        # Wait for socket to be ready
        for _ in range(100): # 10 seconds total
            if os.path.exists(self.socket_path):
                return True
            time.sleep(0.1)
        
        return False

    def stop(self):
        self.send_command("quit")
        self.proc_manager.stop("gnome-integrated-wallpaper")
        if os.path.exists(self.socket_path):
            try: os.remove(self.socket_path)
            except: pass

    def update_setting(self, key, value):
        if key == "mute":
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
