from PySide6.QtWidgets import QListView, QAbstractItemView
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QColor
from PySide6.QtCore import QSize, Qt

class WallpaperGrid(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWordWrap(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setIconSize(QSize(200, 150))
        self.setGridSize(QSize(220, 200))
        self.setUniformItemSizes(True)
        self.setSpacing(10)
        
        self.model = QStandardItemModel()
        self.setModel(self.model)

    def add_wallpaper(self, name, type_label, thumbnail_path=None, data=None):
        item = QStandardItem(name)
        
        if thumbnail_path:
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                item.setIcon(QIcon(pixmap))
            else:
                self._set_placeholder(item)
        else:
            self._set_placeholder(item)
            
        item.setToolTip(f"{name}\nType: {type_label}")
        item.setData(type_label, Qt.UserRole + 1)
        item.setData(data, Qt.UserRole + 2)
        
        self.model.appendRow(item)

    def _set_placeholder(self, item):
        pixmap = QPixmap(200, 150)
        pixmap.fill(QColor("#333333"))
        item.setIcon(QIcon(pixmap))

    def clear(self):
        self.model.clear()
