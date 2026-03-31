import json
import logging
import os
import re
import socket
import subprocess
import time

from core.logger import log_event
from core.process_manager import ProcessManager
from engines.base_backend import BaseBackend


class X11Backend(BaseBackend):
    """
    Native X11 Backend.
    Packaging logic (Flatpak/AppImage) removed for system stability.
    """

    def __init__(self):
        self.proc_manager = ProcessManager()
        self.base_socket_path = "/tmp/mpv-bg-socket"
        self.active_sockets = []



    def start(self, config, video_path):
        self.stop()
        time.sleep(0.3)

        # 1. OPTIMIZACIÓN: Set static blur background before engine load for smooth transition
        from core.desktop_helper import DesktopHelper

        DesktopHelper.set_static_blur_background(video_path)

        layout_mode = config.get_setting("layout_mode", "Individual")
        target_monitor = config.get_setting("target_monitor", "Auto")
        xwin_geometries = self._detect_geometries(layout_mode, target_monitor)

        if not xwin_geometries:
            xwin_geometries = [("-fs", "Default")]

        draw_mode = config.get_setting("draw_mode", "Estándar")
        self.active_sockets = []

        # MPV Binary (Native System)
        mpv_bin = "mpv"
        overall_success = False

        # Prefer detecting the desktop window (_NET_WM_WINDOW_TYPE_DESKTOP) via python-xlib.
        # If that fails, fallback to xwininfo, then to the root window id. Use final_wid for mpv --wid.
        root_wid = None

        # First try python-xlib and look explicitly for a window with _NET_WM_WINDOW_TYPE_DESKTOP
        try:
            from Xlib import X, Xatom
            from Xlib import display as xdisplay

            d = xdisplay.Display()
            root = d.screen().root

            # Atoms
            NET_WM_WINDOW_TYPE = d.intern_atom(
                "_NET_WM_WINDOW_TYPE", only_if_exists=True
            )
            NET_WM_WINDOW_TYPE_DESKTOP = d.intern_atom(
                "_NET_WM_WINDOW_TYPE_DESKTOP", only_if_exists=True
            )

            found = None
            if NET_WM_WINDOW_TYPE and NET_WM_WINDOW_TYPE_DESKTOP:
                # BFS search through window tree to find a desktop window
                try:
                    stack = [root]
                    while stack and not found:
                        win = stack.pop(0)
                        try:
                            prop = win.get_full_property(
                                NET_WM_WINDOW_TYPE, X.AnyPropertyType
                            )
                        except Exception:
                            prop = None
                        if prop:
                            # prop.value may be a sequence of atom integers
                            vals = prop.value
                            # compare atom ids
                            if NET_WM_WINDOW_TYPE_DESKTOP in vals:
                                found = win.id
                                break
                        # push children
                        try:
                            children = win.query_tree().children
                            stack.extend(children)
                        except Exception:
                            # ignore windows we cannot inspect
                            pass
                except Exception:
                    logging.exception(
                        "[X11Backend] error scanning window tree for desktop window"
                    )

            if found:
                root_wid = int(found)
                logging.info(
                    f"[X11Backend] desktop window WID from python-xlib: {root_wid}"
                )
            else:
                logging.debug(
                    "[X11Backend] python-xlib did not find a _NET_WM_WINDOW_TYPE_DESKTOP window"
                )
        except Exception:
            logging.exception(
                "[X11Backend] python-xlib lookup for desktop window failed (continuing to fallbacks)"
            )

        # If python-xlib didn't find a desktop window, try xwininfo -root as a fallback
        if not root_wid:
            try:
                out = subprocess.check_output(
                    ["xwininfo", "-root"], stderr=subprocess.DEVNULL
                ).decode(errors="ignore")
                # Prefer explicit "Window id: 0x..." line (case-insensitive)
                m = re.search(r"window id:\s*(0x[0-9a-fA-F]+)", out, re.IGNORECASE)
                if not m:
                    m = re.search(r"(0x[0-9a-fA-F]+)", out)
                if m:
                    try:
                        root_wid = int(m.group(1), 16)
                        logging.info(
                            f"[X11Backend] root WID from xwininfo: {m.group(1)} -> {root_wid}"
                        )
                    except Exception:
                        logging.exception(
                            "[X11Backend] failed to parse hex WID from xwininfo"
                        )
            except FileNotFoundError:
                logging.error(
                    "[X11Backend] xwininfo not found; please install x11-utils (xwininfo) and try again."
                )
            except Exception:
                logging.exception(
                    "[X11Backend] error obtaining root window id via xwininfo"
                )

        # As a last resort, if python-xlib is available but previous search failed, fall back to the display root id
        if not root_wid:
            try:
                from Xlib import display as xdisplay2

                d2 = xdisplay2.Display()
                root_wid = int(d2.screen().root.id)
                logging.info(
                    f"[X11Backend] fallback root WID from python-xlib root: {root_wid}"
                )
            except Exception:
                logging.exception(
                    "[X11Backend] final python-xlib fallback failed to obtain root WID"
                )

        if not root_wid or root_wid == 0:
            logging.error(
                "[X11Backend] root/window id invalid; aborting X11 start without a valid WID."
            )
            return False

        # Use final_wid (decimal string) for mpv
        final_wid = str(root_wid)

        # Use root_wid for all geometries
        for i, (geo, name) in enumerate(xwin_geometries):
            socket_path = f"{self.base_socket_path}-{i}"
            if os.path.exists(socket_path):
                try:
                    os.remove(socket_path)
                except OSError:
                    pass

            mpv_args = self._build_mpv_args(config, socket_path)
            # Replace placeholder with actual root window id (decimal)
            mpv_args = [a.replace("%WID", str(root_wid)) for a in mpv_args]
            full_cmd = [mpv_bin] + mpv_args + [video_path]

            # AISLAMIENTO DE ENTORNO:
            # Limpiamos variables de portabilidad para que mpv use librerías del sistema
            env = os.environ.copy()
            for var in [
                "LD_LIBRARY_PATH",
                "PYTHONPATH",
                "PYTHONHOME",
                "QT_PLUGIN_PATH",
                "LD_PRELOAD",
            ]:
                if var in env:
                    del env[var]

            proc_id = f"x11-wallpaper-{i}"
            # Start mpv directly embedding into the root window
            self.proc_manager.start(proc_id, full_cmd, env=env)
            self.active_sockets.append(socket_path)
            logging.debug(f"[X11Backend] Added socket to active_sockets: {socket_path}")

            # Wait briefly to see if the mpv-created IPC socket appears and mark success
            for _ in range(15):
                if os.path.exists(socket_path):
                    overall_success = True
                    logging.debug(f"[X11Backend] IPC socket confirmed: {socket_path}")
                    break
                time.sleep(0.1)

        self._wait_for_ipc()

        # XFCE Refresh
        import threading

        def refresh():
            time.sleep(0.5)
            subprocess.run(["xfdesktop", "--reload"], stderr=subprocess.DEVNULL)

        if "xfce" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
            threading.Thread(target=refresh, daemon=True).start()

        logging.debug(f"[X11Backend] start() complete. active_sockets: {self.active_sockets}")
        return overall_success

    def _wait_for_ipc(self):
        for _ in range(25):
            if all(os.path.exists(s) for s in self.active_sockets):
                return True
            time.sleep(0.1)
        return False

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
        logging.info(
            f"[X11_BACKEND_DEBUG] update_setting received: key={key}, value={value}"
        )
        property_map = {
            "volume": "volume",
            "mute": "mute",
            "brightness": "brightness",
            "contrast": "contrast",
            "saturation": "saturation",
            "gamma": "gamma",
        }
        if key in property_map:
            mpv_prop = property_map[key]
            original_value = value
            if key == "mute":
                value = "yes" if value else "no"
            elif key == "gamma":
                # Gamma mapping: UI (0.1 to 5.0, neutral 1.0) -> MPV (-100 to 100, neutral 0)
                try:
                    gamma_ui = float(value)
                    if gamma_ui > 1.0:
                        value = int((gamma_ui - 1.0) / 4.0 * 100)
                    else:
                        value = int((gamma_ui - 1.0) / 0.9 * 100)
                except:
                    value = 0
            logging.info(
                f"[X11_BACKEND_DEBUG] sending command: set_property, {mpv_prop}, {value}"
            )
            return self.send_command("set_property", mpv_prop, value)
        elif key == "loop":
            if value == "Loop":
                self.send_command("set_property", "loop-file", "inf")
                self.send_command("set_property", "pause", False)
            else:
                self.send_command("set_property", "loop-file", "no")
                self.send_command("set_property", "pause", True)
            return True
        elif key == "fit":
            return self._update_fit(value)
        return False

    def send_command(self, command, *args):
        if not self.active_sockets:
            return False
        success = True
        for socket_path in self.active_sockets:
            if not os.path.exists(socket_path):
                continue
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(2.0)
                    client.connect(socket_path)
                    msg = {"command": [command] + list(args)}
                    client.sendall((json.dumps(msg) + "\n").encode())
            except:
                success = False
        return success

    def _detect_geometries(self, layout_mode, target_monitor):
        xwin_geometries = []
        try:
            output = subprocess.check_output("xrandr --query", shell=True).decode()
            if layout_mode == "Extendido (Span)":
                match = re.search(r"current (\d+) x (\d+)", output)
                if match:
                    xwin_geometries = [
                        (f"{match.group(1)}x{match.group(2)}+0+0", "Combined")
                    ]
            elif layout_mode == "Duplicado":
                matches = re.finditer(
                    r"(\S+) connected (?:primary )?(\d+x\d+\+\d+\+\d+)", output
                )
                for m in matches:
                    xwin_geometries.append((m.group(2), m.group(1)))
            else:
                if target_monitor == "Auto":
                    match = re.search(
                        r"(\S+) connected primary (\d+x\d+\+\d+\+\d+)", output
                    )
                    if not match:
                        match = re.search(
                            r"(\S+) connected (\d+x\d+\+\d+\+\d+)", output
                        )
                    if match:
                        xwin_geometries = [(match.group(2), match.group(1))]
                else:
                    match = re.search(
                        rf"{re.escape(target_monitor)} connected (?:primary )?(\d+x\d+\+\d+\+\d+)",
                        output,
                    )
                    if match:
                        xwin_geometries = [(match.group(1), target_monitor)]
        except:
            pass
        return xwin_geometries

    def _build_mpv_args(self, config, socket_path):
        args = ["--wid=%WID"]
        args.extend(
            [
                f"--loop-file={'inf' if config.get_setting('loop', 'Loop') == 'Loop' else 'no'}",
                f"--volume={config.get_setting('volume', 50)}",
                f"--mute={'yes' if config.get_setting('mute', False) else 'no'}",
                f"--hwdec={config.get_setting('hwdec', 'auto-safe')}",
                "--vo=gpu",
                "--gpu-context=auto",
                "--profile=low-latency",
                "--panscan=1.0",
                "--keep-open=yes",
                "--force-window=yes",
                f"--input-ipc-server={socket_path}",
                "--no-osc",
                "--no-osd-bar",
                "--no-input-default-bindings",
                "--idle",
                "--audio-fallback-to-null=yes",
            ]
        )
        if config.get_setting("_initial_pause", False):
            args.append("--pause")
        cache_flags = config.get_setting("_mpv_cache_flags", [])
        args.extend(cache_flags)
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

    def _update_fit(self, value):
        if value == "Stretch":
            self.send_command("set_property", "video-zoom", 0)
            self.send_command("set_property", "keepaspect", False)
        elif value == "Cover":
            self.send_command("set_property", "video-zoom", 0)
            self.send_command("set_property", "keepaspect", True)
            self.send_command("set_property", "panscan", 1.0)
        return True
