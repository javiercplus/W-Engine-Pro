import time
import logging
import os
import psutil
from PySide6.QtCore import QObject, Signal, QThread
from core.desktop_helper import DesktopHelper
from core.logger import log_event

try:
    from Xlib import display, X

    X11_AVAILABLE = True
except ImportError:
    X11_AVAILABLE = False


class ActivityMonitor(QObject):
    """
    Intelligent scheduler for auto-pausing the wallpaper.
    Monitors:
    - Fullscreen/Maximized windows (X11)
    - CPU Usage (Global)
    """

    activityStateChanged = Signal(bool)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._running = False
        self._last_pause_state = False
        self.profile = DesktopHelper.get_profile()
        self._display = None
        self._pause_reason = ""
        self._my_pid = os.getpid()

    def run(self):
        self._running = True
        logging.info(f"[ActivityMonitor] Started. My PID: {self._my_pid}")

        while self._running:
            try:
                should_pause = self._check_should_pause()

                if should_pause != self._last_pause_state:
                    log_event(
                        "INFO",
                        f"Smart Pause triggered: {should_pause}",
                        reason=self._pause_reason if should_pause else "active",
                    )
                    self.activityStateChanged.emit(should_pause)
                    self._last_pause_state = should_pause
            except Exception as e:
                logging.error(f"Error in ActivityMonitor loop: {e}")

            time.sleep(3.0)

    def _get_display(self):
        if not self._display:
            try:
                self._display = display.Display()
            except OSError:
                return None
        return self._display

    def _check_should_pause(self):
        # 1. Config Check
        if not self.config.get_setting("pause_on_active", True):
            return False

        # 2. CPU Threshold Check
        cpu_limit = self.config.get_setting("pause_cpu_threshold", 85)
        if psutil.cpu_percent() > cpu_limit:
            self._pause_reason = "high_cpu"
            return True

        # 3. Window State (X11 only for now)
        if X11_AVAILABLE and self.profile.protocol == "x11":
            pause_mode = self.config.get_setting("pause_mode", "Fullscreen")
            if self._check_x11_window_state(pause_mode):
                return True

        return False

    def _check_x11_window_state(self, mode):
        d = self._get_display()
        if not d:
            return False

        try:
            root = d.screen().root
            NET_ACTIVE_WINDOW = d.intern_atom("_NET_ACTIVE_WINDOW")
            NET_WM_PID = d.intern_atom("_NET_WM_PID")
            WM_CLASS = d.intern_atom("WM_CLASS")
            NET_WM_WINDOW_TYPE = d.intern_atom("_NET_WM_WINDOW_TYPE")

            # Atoms for window types
            TYPE_DESKTOP = d.intern_atom("_NET_WM_WINDOW_TYPE_DESKTOP")
            TYPE_DOCK = d.intern_atom("_NET_WM_WINDOW_TYPE_DOCK")

            NET_WM_STATE = d.intern_atom("_NET_WM_STATE")
            NET_WM_STATE_FULLSCREEN = d.intern_atom("_NET_WM_STATE_FULLSCREEN")

            active_win_prop = root.get_full_property(
                NET_ACTIVE_WINDOW, X.AnyPropertyType
            )
            if not active_win_prop:
                return False

            active_win_id = active_win_prop.value[0]
            if active_win_id == 0:
                return False

            win = d.create_resource_object("window", active_win_id)

            # 1. PID Check (Always play if it's our own window)
            try:
                pid_prop = win.get_full_property(NET_WM_PID, X.AnyPropertyType)
                if pid_prop and pid_prop.value[0] == self._my_pid:
                    return False
            except (AttributeError, IndexError):
                pass

            # 2. Window Type Check (Ignore Desktop and Panels/Docks)
            try:
                type_prop = win.get_full_property(NET_WM_WINDOW_TYPE, X.AnyPropertyType)
                if type_prop and (
                    TYPE_DESKTOP in type_prop.value or TYPE_DOCK in type_prop.value
                ):
                    return False
            except (AttributeError,):
                pass

            # 3. WM_CLASS Check (Ignore System/Compositor windows)
            try:
                wm_class = win.get_full_property(WM_CLASS, X.AnyPropertyType)
                if wm_class:
                    cls_name = b"".join(wm_class.value).lower()
                    ignored = [
                        b"xfdesktop",
                        b"xfce4-panel",
                        b"plasmashell",
                        b"kwin",
                        b"conky",
                    ]
                    if any(c in cls_name for c in ignored):
                        return False
            except (AttributeError,):
                pass

            # 4. Mode-specific checks
            if mode == "Any Window":
                self._pause_reason = "any_window_active"
                return True

            wm_state = win.get_full_property(NET_WM_STATE, X.AnyPropertyType)
            if wm_state and NET_WM_STATE_FULLSCREEN in wm_state.value:
                self._pause_reason = "fullscreen_window"
                return True
        except Exception as e:
            logging.debug(f"X11 Check Error: {e}")
            self._display = None
        return False

    def stop(self):
        self._running = False
