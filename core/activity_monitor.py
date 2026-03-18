import time
import logging
import os
from PySide6.QtCore import QObject, Signal

try:
    from Xlib import display, X
    X11_AVAILABLE = True
except ImportError:
    X11_AVAILABLE = False

class ActivityMonitor(QObject):
    """Monitorea la actividad de ventanas en X11 para pausar el fondo."""
    activityStateChanged = Signal(bool)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._running = False
        self._last_state = None

    def run(self):
        if os.environ.get('WAYLAND_DISPLAY') or not X11_AVAILABLE:
            logging.warning("El monitoreo de actividad solo es compatible con X11. La función de pausa automática se desactivará.")
            return

        self._running = True
        d = display.Display()
        root = d.screen().root

        NET_ACTIVE_WINDOW = d.intern_atom('_NET_ACTIVE_WINDOW')
        NET_WM_STATE = d.intern_atom('_NET_WM_STATE')
        NET_WM_STATE_FULLSCREEN = d.intern_atom('_NET_WM_STATE_FULLSCREEN')
        NET_WM_STATE_MAXIMIZED_VERT = d.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT')
        NET_WM_STATE_MAXIMIZED_HORZ = d.intern_atom('_NET_WM_STATE_MAXIMIZED_HORZ')
        NET_WM_WINDOW_TYPE = d.intern_atom('_NET_WM_WINDOW_TYPE')
        NET_WM_WINDOW_TYPE_DESKTOP = d.intern_atom('_NET_WM_WINDOW_TYPE_DESKTOP')

        our_pid = os.getpid()

        while self._running:
            should_pause = False
            try:
                d.sync()
                
                active_win_prop = root.get_full_property(NET_ACTIVE_WINDOW, X.AnyPropertyType)
                if not active_win_prop:
                    active_win_id = 0
                else:
                    active_win_id = active_win_prop.value[0]
                
                if active_win_id == root.id or active_win_id == 0:
                    should_pause = False
                else:
                    try:
                        active_window = d.create_resource_object('window', active_win_id)
                        
                        win_pid_prop = active_window.get_full_property(d.intern_atom('_NET_WM_PID'), X.AnyPropertyType)
                        if win_pid_prop and win_pid_prop.value[0] == our_pid:
                            should_pause = False
                        else:
                            win_type_prop = active_window.get_full_property(NET_WM_WINDOW_TYPE, X.AnyPropertyType)
                            if win_type_prop and NET_WM_WINDOW_TYPE_DESKTOP in win_type_prop.value:
                                should_pause = False
                            else:
                                wm_state_prop = active_window.get_full_property(NET_WM_STATE, X.AnyPropertyType)
                                states = wm_state_prop.value if wm_state_prop else []
                                
                                is_fullscreen = NET_WM_STATE_FULLSCREEN in states
                                is_maximized = (NET_WM_STATE_MAXIMIZED_VERT in states or 
                                                NET_WM_STATE_MAXIMIZED_HORZ in states)

                                pause_mode = self.config.get("pause_mode", "Fullscreen")
                                
                                if pause_mode == "Fullscreen":
                                    should_pause = is_fullscreen
                                elif pause_mode == "Maximized":
                                    should_pause = is_fullscreen or is_maximized
                                elif pause_mode == "Any Window":
                                    should_pause = True
                    except (X.error.BadWindow, X.error.BadValue, AttributeError):
                        should_pause = False
            except Exception as e:
                logging.debug(f"[ActivityMonitor] Error in loop: {e}")
                should_pause = False

            if should_pause != self._last_state:
                self.activityStateChanged.emit(should_pause)
                self._last_state = should_pause
            
            time.sleep(1.0)

    def stop(self):
        self._running = False