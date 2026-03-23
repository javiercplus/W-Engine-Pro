from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QPoint
from core.desktop_helper import DesktopHelper
import logging
import json
import os
from engines.base_engine import WallpaperEngineInterface


class ParallaxEngine(WallpaperEngineInterface):
    """
    Parallax renderer using QGraphicsView.
    """

    def __init__(self):
        self.view = None
        self.scene = None
        self.layers = []
        self.monitor_info = None

    def init(self, surface_handle, monitor_info):
        self.monitor_info = monitor_info

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool
        )
        self.view.setAttribute(Qt.WA_TranslucentBackground)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        res = monitor_info["resolution"]
        self.view.resize(res[0], res[1])
        self.view.move(monitor_info["position"][0], monitor_info["position"][1])
        self.scene.setSceneRect(0, 0, res[0], res[1])

    def start(self):
        if self.view:
            self.view.show()
            logging.info("Parallax Engine started.")

    def stop(self):
        if self.view:
            self.view.close()
            self.view.deleteLater()
            self.view = None
            logging.info("Parallax Engine stopped.")

    def set_wallpaper(self, config_path):
        """
        Loads layers from a JSON config or directory.
        """
        if not self.scene:
            return
        self.scene.clear()
        self.layers = []

        try:
            if os.path.isdir(config_path):
                files = sorted(
                    [
                        os.path.join(config_path, f)
                        for f in os.listdir(config_path)
                        if f.endswith(".png")
                    ]
                )
                for i, f in enumerate(files):
                    pix = QPixmap(f)
                    item = QGraphicsPixmapItem(pix)
                    item.setPos(0, 0)
                    self.scene.addItem(item)
                    self.layers.append({"item": item, "depth": (i + 1) * 0.1})
            elif config_path.endswith(".json"):
                pass
        except Exception as e:
            logging.error(f"Error loading parallax: {e}")

    def pause(self):
        pass

    def resume(self):
        pass

    def set_transition(self, type):
        pass

    def reload(self):
        pass
