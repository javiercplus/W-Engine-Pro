from PySide6.QtCore import QObject, Qt, QCoreApplication
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QGuiApplication, QWindow
import os
import logging
import time

try:
    from Xlib import display, X
    from Xlib.ext import shape
    X11_AVAILABLE = True
except ImportError:
    X11_AVAILABLE = False

class SurfaceManager(QObject):
    """
    Gestiona la superficie de la ventana del fondo de pantalla.
    Maneja el posicionamiento en capas para X11 (Desktop Window) y Wayland.
    """

    def __init__(self, monitor_id=0):
        super().__init__()
        self.monitor_id = monitor_id
        self.widget = QWidget()
        self.is_wayland = os.environ.get('WAYLAND_DISPLAY') is not None
        self._setup_surface()

    def _setup_surface(self):
        flags = (
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnBottomHint | 
            Qt.WindowDoesNotAcceptFocus |
            Qt.WindowTransparentForInput |
            Qt.ToolTip
        )
        
        
        self.widget.setWindowFlags(flags)
        
        self.widget.setAttribute(Qt.WA_NoSystemBackground)
        self.widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.widget.setAttribute(Qt.WA_ShowWithoutActivating)
        self.widget.setAttribute(Qt.WA_NativeWindow)
        
        screens = QGuiApplication.screens()
        if self.monitor_id < len(screens):
            geo = screens[self.monitor_id].geometry()
            self.widget.setGeometry(geo)
            logging.info(f"Superficie {self.monitor_id} posicionada en: {geo}")

    def show(self):
        self.widget.show()
        
        QCoreApplication.processEvents()
        

    def _apply_x11_layers(self):
        d = None
        try:
            d = display.Display()
            win_id = int(self.widget.winId())
            window = d.create_resource_object('window', win_id)
            
            atom_type = d.intern_atom('_NET_WM_WINDOW_TYPE')
            atom_desktop = d.intern_atom('_NET_WM_WINDOW_TYPE_DESKTOP')
            window.change_property(atom_type, 4, 32, [atom_desktop])
            
            atom_state = d.intern_atom('_NET_WM_STATE')
            states = [
                d.intern_atom('_NET_WM_STATE_BELOW'),
                d.intern_atom('_NET_WM_STATE_SKIP_TASKBAR'),
                d.intern_atom('_NET_WM_STATE_SKIP_PAGER'),
                d.intern_atom('_NET_WM_STATE_STICKY')
            ]
            window.change_property(atom_state, 4, 32, states)

            window.shape_rectangles(shape.SO.Set, shape.SK.Input, 0, 0, 0, [])

            
            d.sync()
            logging.info(f"Capas X11 aplicadas exitosamente a ventana {win_id}")
        except Exception as e:
            logging.error(f"Error en capas X11: {e}")
        finally:
            if d:
                d.close()

    def get_surface_handle(self):
        return int(self.widget.winId())

    def destroy(self):
        self.widget.hide()
        self.widget.close()
        self.widget.deleteLater()
