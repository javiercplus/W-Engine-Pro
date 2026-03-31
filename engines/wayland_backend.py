import json
import logging
import os
import shutil
import subprocess
import threading
import time

from engines.base_backend import BaseBackend
from core.process_manager import ProcessManager
from core.utils import (
    build_common_mpv_args,
    clean_environment,
    gamma_ui_to_mpv,
    send_ipc_command,
    wait_for_ipc,
)

SWAYSOCK_DEFAULT = "/run/user/1000/sway.sock"
SOCKET_BASE_PATH = "/tmp/mpv-bg-socket-wayland"
APP_ID = "W-Engine-Wallpaper"

STARTUP_DELAY = 0.3
KDE_RULES_DELAY = 1.0
WAYLAND_RULES_DELAY = 1.5
SWAY_RULES_DELAY = 2.0
SWAYMSG_TIMEOUT = 3
IPC_WAIT_ATTEMPTS = 10
IPC_POLL_INTERVAL = 0.1
SOCKET_TIMEOUT = 0.05


class WaylandBackend(BaseBackend):
    def __init__(self):
        self.proc_manager = ProcessManager()
        self.base_socket_path = SOCKET_BASE_PATH
        self.active_sockets = []
        self.mpvpaper_bin = shutil.which("mpvpaper")

    def start(self, config, video_path):
        self.stop()
        time.sleep(STARTUP_DELAY)

        compositor = config.get_volatile("compositor", "").lower()
        is_kde = "kde" in compositor or "plasma" in compositor

        if not is_kde:
            from core.desktop_helper import DesktopHelper
            DesktopHelper.set_static_blur_background(video_path)

        if is_kde:
            return self._start_kde_native(config, video_path)

        clean_env = clean_environment()
        app_env = os.environ.copy()

        if not self.mpvpaper_bin:
            return self._start_fallback_mpv(config, video_path, clean_env, app_env)

        return self._start_mpvpaper(config, video_path, clean_env)

    def _start_kde_native(self, config, video_path):
        from core.desktop_helper import DesktopHelper

        logging.info("[WaylandBackend] Using KDE Plasma native method for wallpaper.")
        DesktopHelper.set_background(video_path)
        return True

    def _start_fallback_mpv(self, config, video_path, clean_env, app_env):
        logging.warning("[WaylandBackend] mpvpaper not found. Falling back to floating mpv.")

        socket_path = f"{self.base_socket_path}-0"
        if os.path.exists(socket_path):
            try:
                os.remove(socket_path)
            except OSError:
                pass

        mpv_bin, use_env = self._resolve_mpv_binary(clean_env, app_env)
        if not mpv_bin:
            logging.error("[WaylandBackend] mpv not found. Cannot fallback.")
            return False

        cmd = [mpv_bin] + self._build_mpv_args(config, socket_path)
        cmd += [
            "--gpu-context=wayland",
            "--force-window=yes",
            "--no-border",
            f"--wayland-app-id={APP_ID}",
            f"--title={APP_ID}",
            video_path,
        ]

        self.proc_manager.start("wayland-fallback", cmd, env=use_env)
        self.active_sockets = [socket_path]

        self._apply_window_rules(APP_ID)
        return wait_for_ipc(self.active_sockets, IPC_WAIT_ATTEMPTS, IPC_POLL_INTERVAL)

    def _start_mpvpaper(self, config, video_path, clean_env):
        target_monitor = config.get_setting("target_monitor", "Auto")
        outputs = ["*"] if target_monitor == "Auto" else [target_monitor]

        self.active_sockets = []
        for i, out in enumerate(outputs):
            socket_path = f"{self.base_socket_path}-{i}"
            if os.path.exists(socket_path):
                try:
                    os.remove(socket_path)
                except OSError:
                    pass

            mpv_opts = self._build_mpv_args(config, socket_path)
            cmd = [self.mpvpaper_bin]
            # mpvpaper expects all mpv options as a single string after -o.
            # Join the generated args so mpv receives them correctly.
            opts_str = " ".join(mpv_opts)
            if opts_str:
                cmd.extend(["-o", opts_str])

            cmd += [out, video_path]
            self.proc_manager.start(f"wayland-wallpaper-{i}", cmd, env=clean_env)
            self.active_sockets.append(socket_path)

        return wait_for_ipc(self.active_sockets, IPC_WAIT_ATTEMPTS, IPC_POLL_INTERVAL)

    def _resolve_mpv_binary(self, clean_env, app_env):
        appdir = os.environ.get("APPDIR")
        if appdir:
            bundled = os.path.join(appdir, "usr/bin/mpv")
            if os.path.exists(bundled):
                return bundled, app_env

        system = shutil.which("mpv")
        if system:
            return system, clean_env

        return None, None

    def _apply_window_rules(self, app_id):
        compositor = self._detect_compositor()
        if compositor == "sway":
            self._apply_sway_rules(app_id)
        elif compositor == "hyprland":
            self._apply_hyprland_rules(app_id)
        else:
            logging.warning(f"[WaylandBackend] Unsupported compositor for window rules: {compositor}")

    def _detect_compositor(self):
        xdg = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "sway" in xdg or os.path.exists(os.environ.get("SWAYSOCK", SWAYSOCK_DEFAULT)):
            return "sway"
        if "hyprland" in xdg or os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return "hyprland"
        if "gnome" in xdg:
            return "gnome"
        if "kde" in xdg or "plasma" in xdg:
            return "kde"
        return "unknown"

    def _apply_sway_rules(self, app_id):
        time.sleep(SWAY_RULES_DELAY)

        try:
            window_id = self._find_sway_window(app_id)
            if not window_id:
                logging.warning(f"[WaylandBackend] Window not found for app_id={app_id}")
                return

            logging.info(f"[WaylandBackend] Found window {window_id} for {app_id}")

            commands = [
                f"[con_id={window_id}] floating enable",
                f"[con_id={window_id}] border none",
                f"[con_id={window_id}] fullscreen enable",
            ]

            for cmd in commands:
                result = subprocess.run(
                    ["swaymsg", cmd],
                    capture_output=True, text=True, timeout=SWAYMSG_TIMEOUT
                )
                if result.returncode != 0:
                    logging.warning(f"[WaylandBackend] swaymsg failed: {cmd}")

            logging.info(f"[WaylandBackend] Sway rules applied for {app_id}")

        except subprocess.TimeoutExpired:
            logging.warning("[WaylandBackend] Timeout applying Sway rules")
        except FileNotFoundError:
            logging.warning("[WaylandBackend] swaymsg not found")
        except Exception as e:
            logging.error(f"[WaylandBackend] Error applying Sway rules: {e}")

    def _find_sway_window(self, app_id):
        result = subprocess.run(
            ["swaymsg", "-t", "get_tree"],
            capture_output=True, text=True, timeout=SWAYMSG_TIMEOUT
        )

        if result.returncode != 0:
            return None

        tree = json.loads(result.stdout)
        for output in tree.get("nodes", []):
            for node_type in ("nodes", "floating_nodes"):
                for node in output.get(node_type, []):
                    window_id = self._find_window_in_tree(node, app_id)
                    if window_id:
                        return window_id
        return None

    def _find_window_in_tree(self, node, app_id):
        if not isinstance(node, dict):
            return None

        if node.get("app_id") == app_id:
            return node.get("id")

        for key in ("nodes", "floating_nodes", "focus"):
            for child in node.get(key, []):
                result = self._find_window_in_tree(child, app_id)
                if result:
                    return result
        return None

    def _apply_hyprland_rules(self, app_id):
        time.sleep(WAYLAND_RULES_DELAY)

        try:
            result = subprocess.run(
                ["hyprctl", "clients", "-j"],
                capture_output=True, text=True, timeout=SWAYMSG_TIMEOUT
            )

            if result.returncode != 0:
                return

            clients = json.loads(result.stdout)
            for client in clients:
                if app_id in (client.get("class", "") + client.get("title", "")):
                    addr = client.get("address", "")
                    for prop in ("watermark", "noBorder", "fullscreen"):
                        subprocess.run(
                            ["hyprctl", "dispatcher", "setprop", addr, prop, "true"],
                            capture_output=True
                        )
                    logging.info(f"[WaylandBackend] Hyprland rules applied for {app_id}")
                    break

        except subprocess.TimeoutExpired:
            logging.warning("[WaylandBackend] Timeout applying Hyprland rules")
        except FileNotFoundError:
            logging.warning("[WaylandBackend] hyprctl not found")
        except Exception as e:
            logging.error(f"[WaylandBackend] Error applying Hyprland rules: {e}")

    def stop(self):
        for name in list(self.proc_manager.processes.keys()):
            if name.startswith("wayland-wallpaper") or name == "wayland-fallback":
                self.proc_manager.stop(name)

        subprocess.run(["pkill", "-f", "mpvpaper"], stderr=subprocess.DEVNULL)
        subprocess.run(
            ["pkill", "-f", "mpv.*mpv-bg-socket-wayland"], stderr=subprocess.DEVNULL
        )

        for s in self.active_sockets:
            if os.path.exists(s):
                try:
                    os.remove(s)
                except OSError:
                    pass
        self.active_sockets = []

    def update_setting(self, key, value):
        logging.debug(f"[WaylandBackend] update_setting: {key}={value}")

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

            logging.debug(f"[WaylandBackend] set_property: {mpv_prop}={value}")
            return send_ipc_command(self.active_sockets, "set_property", mpv_prop, value, timeout=SOCKET_TIMEOUT)

        if key == "loop":
            if value == "Loop":
                send_ipc_command(self.active_sockets, "set_property", "loop-file", "inf")
                send_ipc_command(self.active_sockets, "set_property", "pause", False)
            else:
                send_ipc_command(self.active_sockets, "set_property", "loop-file", "no")
                send_ipc_command(self.active_sockets, "set_property", "pause", True)
            return True

        return False

    def send_command(self, command, *args):
        return send_ipc_command(self.active_sockets, command, *args, timeout=SOCKET_TIMEOUT)

    def _build_mpv_args(self, config, socket_path, wid_needed=False):
        return build_common_mpv_args(config, socket_path, wid_needed)
