from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
import logging
import os
from engines.base_engine import WallpaperEngineInterface


class WebEngine(WallpaperEngineInterface):
    """
    Web renderer using QtWebEngine (Chromium-based).
    Supports HTML/JS wallpapers.
    """

    def __init__(self):
        self.webview = None
        self.surface_widget = None
        self.monitor_info = None

    def init(self, surface_handle, monitor_info):
        """
        surface_handle: In the Qt implementation, we expect this to be the window ID,
        but since we are inside the same process using Qt, we might need the actual QWidget
        to embed the QWebEngineView.

        However, SurfaceManager returns an integer ID.
        If we want to embed, we should probably pass the QWidget itself or find it.

        For now, let's assume we can reparent the QWebEngineView to the window ID,
        or better, update SurfaceManager to return the QWidget if possible,
        OR finding the widget by ID (QWindow::fromWinId).
        """
        self.monitor_id = monitor_info.get("id", 0)

        self.webview = QWebEngineView()

        settings = self.webview.settings()
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

        self.webview.page().setBackgroundColor(Qt.transparent)

        self.webview.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool
        )
        self.webview.setAttribute(Qt.WA_TranslucentBackground)
        self.webview.resize(
            monitor_info["resolution"][0], monitor_info["resolution"][1]
        )
        self.webview.move(monitor_info["position"][0], monitor_info["position"][1])

    def start(self):
        if self.webview:
            self.webview.show()
            logging.info("QtWebEngine started.")

    def stop(self):
        if self.webview:
            self.webview.close()
            self.webview.deleteLater()
            self.webview = None
            logging.info("QtWebEngine stopped.")

    def set_wallpaper(self, path):
        if self.webview:
            if path.startswith("http"):
                self.webview.setUrl(QUrl(path))
            else:
                self.webview.setUrl(QUrl.fromLocalFile(path))
            logging.info(f"Web loading: {path}")

    def pause(self):
        pass

    def resume(self):
        pass

    def set_transition(self, type):
        pass

    def reload(self):
        if self.webview:
            self.webview.reload()
