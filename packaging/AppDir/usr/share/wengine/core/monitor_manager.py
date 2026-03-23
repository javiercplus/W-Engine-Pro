from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication
import logging


class MonitorManager(QObject):
    """
    Detects monitors using pure Qt6 APIs.
    """

    def __init__(self):
        super().__init__()

    def get_monitors(self):
        """
        Returns a list of connected monitors.
        """
        monitors = []
        screens = QGuiApplication.screens()

        for i, screen in enumerate(screens):
            geo = screen.geometry()
            monitors.append(
                {
                    "id": i,
                    "name": screen.name(),
                    "resolution": (geo.width(), geo.height()),
                    "position": (geo.x(), geo.y()),
                    "qt_screen": screen,
                }
            )
            logging.info(
                f"Monitor detected: {screen.name()} {geo.width()}x{geo.height()}"
            )

        return monitors
