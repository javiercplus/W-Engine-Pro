#!/usr/bin/env python3
import subprocess
import socket
import json
import time
import sys
import os
from Xlib import display, X

VIDEO_PATH = sys.argv[1] if len(sys.argv) > 1 else ""
SOCKET_PATH = "/tmp/mpv-bg-socket"

if not VIDEO_PATH or not os.path.exists(VIDEO_PATH):
    print("Error: El video no existe o no se proporcionó ruta.")
    sys.exit(1)


class BackgroundManager:
    def __init__(self):
        self.display = display.Display()
        self.root = self.display.screen().root
        self.root.set_error_handler(lambda *a, **k: None)

        self.ACTIVE_WINDOW = self.display.intern_atom("_NET_ACTIVE_WINDOW")
        self.WM_STATE = self.display.intern_atom("_NET_WM_STATE")
        self.FULLSCREEN = self.display.intern_atom("_NET_WM_STATE_FULLSCREEN")

        self.root.change_attributes(event_mask=X.PropertyChangeMask)

        self.bg_proc = None
        self.state = "STOPPED"

    def send_mpv(self, command):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect(SOCKET_PATH)
                client.sendall((json.dumps({"command": command}) + "\n").encode())
            return True
        except (OSError, ConnectionRefusedError, json.JSONDecodeError):
            return False

    def get_window_info(self):
        """Retorna (es_escritorio, es_fullscreen)"""
        try:
            win_id = self.root.get_full_property(
                self.ACTIVE_WINDOW, X.AnyPropertyType
            ).value[0]
            if win_id == 0:
                return True, False

            win = self.display.create_resource_object("window", win_id)
            cls = win.get_wm_class()
            is_desktop = cls and cls[1].lower() in ["xfdesktop", "desktop"]

            state = win.get_full_property(self.WM_STATE, X.AnyPropertyType)
            is_fs = state and self.FULLSCREEN in state.value

            return is_desktop, is_fs
        except (X.error, AttributeError, IndexError):
            return True, False

    def manage_bg(self, is_desktop, is_fs):
        if is_fs:
            if self.state != "STOPPED":
                print(
                    "[GAME MODE] Pantalla completa detectada. Matando proceso para liberar recursos."
                )
                self.stop()
        elif is_desktop:
            if self.state == "STOPPED":
                self.start()
            elif self.state == "PAUSED":
                self.send_mpv(["set_property", "pause", False])
                self.state = "PLAYING"
                print("[RESUME] Escritorio visible.")
        else:
            if self.state == "PLAYING":
                self.send_mpv(["set_property", "pause", True])
                self.state = "PAUSED"
                print("[PAUSE] Ventana activa detectada.")

    def start(self):
        self.stop()
        res = (
            subprocess.check_output(
                "xdpyinfo | grep dimensions | awk '{print $2}'", shell=True
            )
            .decode()
            .strip()
        )
        cmd = [
            "mpv",
            "--wid=%WID",
            "--loop",
            "--no-audio",
            "--idle",
            "--vo=gpu",
            "--hwdec=auto",
            f"--input-ipc-server={SOCKET_PATH}",
            VIDEO_PATH,
        ]
        self.bg_proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.state = "PLAYING"
        print("[START] Fondo iniciado.")

    def stop(self):
        if self.bg_proc:
            self.bg_proc.terminate()
            self.bg_proc = None
        self.state = "STOPPED"

    def run(self):
        self.start()
        print("Optimizador activo. Escuchando eventos del sistema...")

        while True:
            event = self.display.next_event()
            if event.type == X.PropertyNotify and event.atom == self.ACTIVE_WINDOW:
                is_desktop, is_fs = self.get_window_info()
                self.manage_bg(is_desktop, is_fs)


if __name__ == "__main__":
    try:
        manager = BackgroundManager()
        manager.run()
    except KeyboardInterrupt:
        manager.stop()
        print("\nSaliendo...")
