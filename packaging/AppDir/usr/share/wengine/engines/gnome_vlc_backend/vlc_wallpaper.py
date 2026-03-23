#!/usr/bin/env python3
import sys
import os

# WORKAROUND: Fix for PyGObject AttributeError: module 'gi._gi' has no attribute 'pyos_setsig'
# This happens in some Python 3.12/3.13/3.14 environments with older PyGObject
try:
    import gi
    from gi._gi import _API
    if not hasattr(gi._gi, 'pyos_setsig'):
        gi._gi.pyos_setsig = getattr(gi._gi, 'pyos_getsig', None)
except:
    pass

import logging
import ctypes
import json
import socket
import threading
import time

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import vlc

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("W-VLC-Wallpaper")

class VLCWidget(Gtk.DrawingArea):
    def __init__(self, width, height, volume=50, mute=False):
        Gtk.DrawingArea.__init__(self)
        vlc_options = ["--no-disable-screensaver", "--no-video-title-show"]
        self.instance = vlc.Instance(vlc_options)
        self.player = self.instance.media_player_new()
        self.volume = volume
        self.mute = mute

        def handle_embed(*args):
            # The 'Hidamari trick': Embed VLC into a Gtk DrawingArea
            window = self.get_window()
            if window:
                self.player.set_xwindow(window.get_xid())
            return True

        self.connect("realize", handle_embed)
        self.set_size_request(width, height)

    def play_file(self, path):
        media = self.instance.media_new(path)
        media.add_option("input-repeat=65535")
        self.player.set_media(media)
        self.player.audio_set_volume(self.volume)
        self.player.audio_set_mute(self.mute)
        self.player.play()

    def set_volume(self, volume):
        self.volume = volume
        self.player.audio_set_volume(volume)

    def set_mute(self, mute):
        self.mute = mute
        self.player.audio_set_mute(mute)

    def cleanup(self):
        if self.player:
            self.player.stop()
            self.player.release()
        if self.instance:
            self.instance.release()

class WallpaperWindow(Gtk.ApplicationWindow):
    def __init__(self, monitor_idx, rect, video_path, volume=50, mute=False):
        super(WallpaperWindow, self).__init__()
        self.set_title(f"W-Engine-VLC-Wallpaper-{monitor_idx}")
        self.set_default_size(rect.width, rect.height)
        self.move(rect.x, rect.y)

        # Make it a desktop-type window
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_app_paintable(True)
        self.set_keep_below(True)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        # Transparency support
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.vlc_widget = VLCWidget(rect.width, rect.height, volume, mute)
        self.add(self.vlc_widget)
        self.vlc_widget.show()

        # Disable input interception by VLC
        self.vlc_widget.player.video_set_mouse_input(False)
        self.vlc_widget.player.video_set_key_input(False)

        self.connect("destroy", self.on_destroy)
        self.show_all()
        
        # Start playback after showing
        GLib.idle_add(lambda: self.vlc_widget.play_file(video_path))

    def on_destroy(self, *args):
        self.vlc_widget.cleanup()

class WallpaperManager(Gtk.Application):
    def __init__(self, video_path, volume=50, mute=False, socket_path="/tmp/wengine-vlc.sock"):
        super(WallpaperManager, self).__init__(application_id="org.wengine.vlc_wallpaper")
        self.video_path = video_path
        self.volume = volume
        self.mute = mute
        self.socket_path = socket_path
        self.windows = []

        # X11 Thread init for HW acceleration (even on Wayland/XWayland)
        try:
            for libname in ["libX11.so", "libX11.so.6"]:
                try:
                    x11 = ctypes.cdll.LoadLibrary(libname)
                    x11.XInitThreads()
                    break
                except: pass
        except: pass

    def do_activate(self):
        display = Gdk.Display.get_default()
        n_monitors = display.get_n_monitors()
        
        for i in range(n_monitors):
            monitor = display.get_monitor(i)
            rect = monitor.get_geometry()
            # Only play audio on primary monitor
            vol = self.volume if i == 0 else 0
            win = WallpaperWindow(i, rect, self.video_path, vol, self.mute)
            self.add_window(win)
            self.windows.append(win)

        # Start IPC server
        threading.Thread(target=self._run_ipc_server, daemon=True).start()

    def _run_ipc_server(self):
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        server.listen(1)
        
        while True:
            conn, _ = server.accept()
            try:
                data = conn.recv(1024).decode()
                if not data: continue
                msg = json.loads(data)
                cmd = msg.get("command", [])
                self._handle_command(cmd)
            except Exception as e:
                logger.error(f"IPC Error: {e}")
            finally:
                conn.close()

    def _handle_command(self, cmd):
        if not cmd: return
        name = cmd[0]
        args = cmd[1:]

        GLib.idle_add(lambda: self._execute_command_ui(name, args))

    def _execute_command_ui(self, name, args):
        if name == "set_property":
            prop = args[0]
            val = args[1]
            if prop == "volume":
                self.volume = int(val)
                if self.windows: self.windows[0].vlc_widget.set_volume(self.volume)
            elif prop == "mute":
                self.mute = (val == "yes" or val is True)
                for win in self.windows: win.vlc_widget.set_mute(self.mute)
            elif prop == "pause":
                paused = (val is True or val == "yes")
                for win in self.windows:
                    if paused: win.vlc_widget.player.pause()
                    else: win.vlc_widget.player.play()
        elif name == "quit":
            self.quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: vlc_wallpaper.py <video_path> [volume] [mute] [socket_path]")
        sys.exit(1)
    
    path = sys.argv[1]
    vol = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    mute = (sys.argv[3].lower() == "true") if len(sys.argv) > 3 else False
    sock = sys.argv[4] if len(sys.argv) > 4 else "/tmp/wengine-vlc.sock"
    
    app = WallpaperManager(path, vol, mute, sock)
    app.run(None)
