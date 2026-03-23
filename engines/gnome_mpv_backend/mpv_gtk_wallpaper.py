#!/usr/bin/env python3
import sys
import os
import logging
import json
import socket
import threading
import time
import ctypes

# Forzar X11 para el truco de incrustación
os.environ["GDK_BACKEND"] = "x11"

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import subprocess

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("W-MPV-Integrated")

class WallpaperWindow(Gtk.Window):
    def __init__(self, monitor_idx, rect, video_path, socket_path, resolution="Nativa"):
        super(WallpaperWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title(f"W-Engine-MPV-Wallpaper-{monitor_idx}")
        self.set_default_size(rect.width, rect.height)
        self.move(rect.x, rect.y)

        # W-Engine Native Trick: Window Type DESKTOP
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_keep_below(True)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.area = Gtk.DrawingArea()
        self.add(self.area)
        self.area.show()

        self.video_path = video_path
        self.socket_path = socket_path
        self.resolution = resolution
        self.mpv_proc = None

        self.connect("realize", self.on_realize)
        self.connect("destroy", self.on_destroy)
        self.show_all()

    def on_realize(self, widget):
        # Obtener el ID de la ventana de X11
        window = self.get_window()
        xid = window.get_xid()
        
        # Lanzar MPV incrustado en esta ventana
        cmd = [
            "mpv",
            f"--wid={xid}",
            "--vo=gpu",
            "--gpu-context=x11",
            f"--input-ipc-server={self.socket_path}",
            "--loop-file=inf",
            "--no-osc",
            "--no-osd-bar",
            "--no-input-default-bindings",
            "--idle=yes"
        ]

        # Aplicar resolución si no es Nativa
        resolution_map = {
            "1080p (Full HD)": "scale=-1:1080",
            "720p (HD)": "scale=-1:720",
            "480p (SD)": "scale=-1:480",
        }
        if self.resolution in resolution_map:
            cmd.append(f"--vf={resolution_map[self.resolution]}")

        cmd.append(self.video_path)
        
        # Limpiar entorno para que MPV use las del sistema
        env = os.environ.copy()
        for var in ["PYTHONPATH", "PYTHONHOME", "LD_LIBRARY_PATH"]:
            if var in env: del env[var]
            
        logger.info(f"Starting MPV embedded in XID: {xid} with resolution: {self.resolution}")
        self.mpv_proc = subprocess.Popen(cmd, env=env)

    def on_destroy(self, *args):
        if self.mpv_proc:
            self.mpv_proc.terminate()

class WallpaperManager(Gtk.Application):
    def __init__(self, video_path, socket_path, resolution="Nativa"):
        super(WallpaperManager, self).__init__(
            application_id=f"org.wengine.mpv_integrated.p{os.getpid()}",
            flags=gi.repository.Gio.ApplicationFlags.NON_UNIQUE
        )
        self.video_path = video_path
        self.socket_path = socket_path
        self.resolution = resolution

    def do_activate(self):
        display = Gdk.Display.get_default()
        n_monitors = display.get_n_monitors()
        
        # Native integrated engine window
        monitor = display.get_monitor(0)
        rect = monitor.get_geometry()
        win = WallpaperWindow(0, rect, self.video_path, self.socket_path, self.resolution)
        self.add_window(win)

if __name__ == "__main__":
    path = sys.argv[1]
    sock = sys.argv[2]
    res = sys.argv[3] if len(sys.argv) > 3 else "Nativa"
    app = WallpaperManager(path, sock, res)
    app.run(None)
