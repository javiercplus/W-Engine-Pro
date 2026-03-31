import json
import logging
import os
import re
import socket
import subprocess
import threading
import time

from core.process_manager import ProcessManager
from core.utils import (
    build_common_mpv_args,
    clean_environment,
    gamma_ui_to_mpv,
    send_ipc_command,
    wait_for_ipc,
)
from engines.base_backend import BaseBackend

SOCKET_BASE_PATH = "/tmp/mpv-bg-socket"
STARTUP_DELAY = 0.3
XFCE_REFRESH_DELAY = 0.5
IPC_WAIT_ATTEMPTS = 25
IPC_POLL_INTERVAL = 0.1
SOCKET_TIMEOUT = 2.0


class X11Backend(BaseBackend):
    """Native X11 backend for embedding mpv into the root window."""

    def __init__(self):
        self.proc_manager = ProcessManager()
        self.base_socket_path = SOCKET_BASE_PATH
        self.active_sockets = []

    def start(self, config, video_path):
        self.stop()
        time.sleep(STARTUP_DELAY)

        from core.desktop_helper import DesktopHelper
        DesktopHelper.set_static_blur_background(video_path)

        layout_mode = config.get_setting("layout_mode", "Individual")
        target_monitor = config.get_setting("target_monitor", "Auto")
        geometries = self._detect_geometries(layout_mode, target_monitor)
        if not geometries:
            geometries = [("-fs", "Default")]

        root_wid = self._find_root_window_id()
        if not root_wid:
            logging.error("[X11Backend] Invalid root window ID. Aborting.")
            return False

        draw_mode = config.get_setting("draw_mode", "Estándar")
        self.active_sockets = []

        for i, (geo, name) in enumerate(geometries):
            socket_path = f"{self.base_socket_path}-{i}"
            self._remove_socket_if_exists(socket_path)

            mpv_args = self._build_mpv_args(config, socket_path)
            mpv_args = [a.replace("%WID", str(root_wid)) for a in mpv_args]
            full_cmd = ["mpv"] + mpv_args + [video_path]

            env = clean_environment()
            proc_id = f"x11-wallpaper-{i}"
            self.proc_manager.start(proc_id, full_cmd, env=env)
            self.active_sockets.append(socket_path)

        success = wait_for_ipc(self.active_sockets, IPC_WAIT_ATTEMPTS, IPC_POLL_INTERVAL)
        self._refresh_xfce_if_needed()
        return success

    def _remove_socket_if_exists(self, socket_path):
        if os.path.exists(socket_path):
            try:
                os.remove(socket_path)
            except OSError:
                pass

    def _find_root_window_id(self):
        """Find the root/desktop window ID using multiple fallback strategies."""
        wid = self._find_desktop_window_xlib()
        if wid:
            return wid

        wid = self._find_root_window_xwininfo()
        if wid:
            return wid

        return self._fallback_to_xlib_root()

    def _find_desktop_window_xlib(self):
        """Try to find a window with _NET_WM_WINDOW_TYPE_DESKTOP via python-xlib."""
        try:
            from Xlib import X
            from Xlib.display import Display

            display = Display()
            root = display.screen().root

            net_wm_window_type = display.intern_atom("_NET_WM_WINDOW_TYPE", only_if_exists=True)
            net_wm_desktop = display.intern_atom("_NET_WM_WINDOW_TYPE_DESKTOP", only_if_exists=True)

            if not (net_wm_window_type and net_wm_desktop):
                return None

            found = self._bfs_find_desktop_window(root, net_wm_window_type, net_wm_desktop)
            if found:
                logging.info(f"[X11Backend] Desktop window WID from python-xlib: {found}")
            return found

        except Exception:
            logging.debug("[X11Backend] python-xlib desktop window search failed")
            return None

    def _bfs_find_desktop_window(self, root, window_type_atom, desktop_atom):
        """BFS through window tree to find a desktop-type window."""
        from Xlib import X

        queue = [root]
        while queue:
            win = queue.pop(0)
            try:
                prop = win.get_full_property(window_type_atom, X.AnyPropertyType)
                if prop and desktop_atom in prop.value:
                    return int(win.id)
            except Exception:
                pass

            try:
                queue.extend(win.query_tree().children)
            except Exception:
                pass
        return None

    def _find_root_window_xwininfo(self):
        """Fallback: get root window ID from xwininfo."""
        try:
            out = subprocess.check_output(
                ["xwininfo", "-root"], stderr=subprocess.DEVNULL
            ).decode(errors="ignore")

            match = re.search(r"window id:\s*(0x[0-9a-fA-F]+)", out, re.IGNORECASE)
            if not match:
                match = re.search(r"(0x[0-9a-fA-F]+)", out)

            if match:
                wid = int(match.group(1), 16)
                logging.info(f"[X11Backend] Root WID from xwininfo: {match.group(1)} -> {wid}")
                return wid

        except FileNotFoundError:
            logging.error("[X11Backend] xwininfo not found. Install x11-utils.")
        except Exception:
            logging.debug("[X11Backend] xwininfo fallback failed")

        return None

    def _fallback_to_xlib_root(self):
        """Last resort: use python-xlib to get root window ID."""
        try:
            from Xlib.display import Display

            display = Display()
            wid = int(display.screen().root.id)
            logging.info(f"[X11Backend] Fallback root WID from python-xlib: {wid}")
            return wid
        except Exception:
            logging.debug("[X11Backend] Final python-xlib fallback failed")
            return None

    def _refresh_xfce_if_needed(self):
        """Reload xfdesktop on XFCE to apply wallpaper changes."""
        if "xfce" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
            return

        def _refresh():
            time.sleep(XFCE_REFRESH_DELAY)
            subprocess.run(["xfdesktop", "--reload"], stderr=subprocess.DEVNULL)

        threading.Thread(target=_refresh, daemon=True).start()

    def stop(self):
        for name in list(self.proc_manager.processes.keys()):
            if name.startswith("x11-wallpaper"):
                self.proc_manager.stop(name)

        subprocess.run(["pkill", "-f", "mpv.*mpv-bg-socket"], stderr=subprocess.DEVNULL)

        for s in self.active_sockets:
            if os.path.exists(s):
                try:
                    os.remove(s)
                except OSError:
                    pass
        self.active_sockets = []

    def update_setting(self, key, value):
        logging.debug(f"[X11Backend] update_setting: {key}={value}")

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
                value = gamma_ui_to_mpv(value)

            logging.debug(f"[X11Backend] set_property: {mpv_prop}={value}")
            return send_ipc_command(self.active_sockets, "set_property", mpv_prop, value, timeout=SOCKET_TIMEOUT)

        if key == "loop":
            if value == "Loop":
                send_ipc_command(self.active_sockets, "set_property", "loop-file", "inf")
                send_ipc_command(self.active_sockets, "set_property", "pause", False)
            else:
                send_ipc_command(self.active_sockets, "set_property", "loop-file", "no")
                send_ipc_command(self.active_sockets, "set_property", "pause", True)
            return True

        if key == "fit":
            return self._update_fit(value)

        return False

    def send_command(self, command, *args):
        return send_ipc_command(self.active_sockets, command, *args, timeout=SOCKET_TIMEOUT)

    def _build_mpv_args(self, config, socket_path):
        args = build_common_mpv_args(config, socket_path, wid_needed=True)
        args.append("--audio-fallback-to-null=yes")
        args.append("--force-window=yes")

        if config.get_setting("_initial_pause", False):
            args.append("--pause")

        return args

    def _detect_geometries(self, layout_mode, target_monitor):
        try:
            output = subprocess.check_output("xrandr --query", shell=True).decode()
        except Exception:
            return []

        if layout_mode == "Extendido (Span)":
            return self._get_span_geometry(output)
        elif layout_mode == "Duplicado":
            return self._get_duplicate_geometry(output)
        else:
            return self._get_individual_geometry(output, target_monitor)

    def _get_span_geometry(self, output):
        """Get combined screen geometry for span mode."""
        match = re.search(r"current (\d+) x (\d+)", output)
        if match:
            return [(f"{match.group(1)}x{match.group(2)}+0+0", "Combined")]
        return []

    def _get_duplicate_geometry(self, output):
        """Get all connected outputs for duplicate mode."""
        matches = re.finditer(
            r"(\S+) connected (?:primary )?(\d+x\d+\+\d+\+\d+)", output
        )
        return [(m.group(2), m.group(1)) for m in matches]

    def _get_individual_geometry(self, output, target_monitor):
        """Get single monitor geometry for individual mode."""
        if target_monitor == "Auto":
            match = re.search(r"(\S+) connected primary (\d+x\d+\+\d+\+\d+)", output)
            if not match:
                match = re.search(r"(\S+) connected (\d+x\d+\+\d+\+\d+)", output)
        else:
            match = re.search(
                rf"{re.escape(target_monitor)} connected (?:primary )?(\d+x\d+\+\d+\+\d+)",
                output,
            )

        if match:
            return [(match.group(2), match.group(1) if target_monitor == "Auto" else target_monitor)]
        return []

    def _update_fit(self, value):
        if value == "Stretch":
            send_ipc_command(self.active_sockets, "set_property", "video-zoom", 0)
            send_ipc_command(self.active_sockets, "set_property", "keepaspect", False)
        elif value == "Cover":
            send_ipc_command(self.active_sockets, "set_property", "video-zoom", 0)
            send_ipc_command(self.active_sockets, "set_property", "keepaspect", True)
            send_ipc_command(self.active_sockets, "set_property", "panscan", 1.0)
        return True
