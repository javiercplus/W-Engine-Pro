from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QStackedWidget, QLabel, QFrame, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QObject, Slot, QTimer
from PySide6.QtGui import QIcon, QColor
import os
import logging
import random

from ui.sidebar import Sidebar
from ui.pages import LibraryPage, MonitorPage, DesignPage, SettingsPage, AboutPage
from ui.properties_panel import PropertiesPanel
from ui.url_dialog import UrlDialog
from ui.styles import DARK_THEME
from core.event_bus import EventBus

class LibraryLoaderWorker(QThread):
    itemLoaded = Signal(str, str, str, str)
    finished = Signal()

    def __init__(self, resources):
        super().__init__()
        self.resources = resources

    def run(self):
        if not self.resources: return
        wallpapers = self.resources.list_local_wallpapers()
        for v in wallpapers:
            name = os.path.basename(v)
            thumb = self.resources.get_thumbnail(v)
            self.itemLoaded.emit(name, "Video", thumb, v)
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self, controller=None, config=None, resources=None):
        super().__init__()
        self.controller = controller
        self.config = config
        self.resources = resources
        
        self.setWindowTitle("W-Engine Pro")
        self.resize(1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_v_layout = QVBoxLayout(central_widget)
        self.main_v_layout.setContentsMargins(0, 0, 0, 0)
        self.main_v_layout.setSpacing(0)
        
        self.sidebar = Sidebar()
        self.sidebar.pageChanged.connect(self.switch_page)
        self.sidebar.stopAllRequested.connect(self.on_stop_all)
        self.main_v_layout.addWidget(self.sidebar)
        
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.main_v_layout.addWidget(self.content_splitter)
        
        self.pages = QStackedWidget()
        
        self.lib_page = LibraryPage()
        self.lib_page.grid.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.lib_page.addUrlRequested.connect(self.open_url_dialog)
        
        self.mon_page = MonitorPage(config=self.config)
        self.design_page = DesignPage(config=self.config)
        self.settings_page = SettingsPage(config=self.config)
        self.about_page = AboutPage()
        
        self.pages.addWidget(self.lib_page)
        self.pages.addWidget(self.mon_page)
        self.pages.addWidget(self.design_page)
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(self.about_page)
        
        self.content_splitter.addWidget(self.pages)
        
        self.props_panel = PropertiesPanel()
        self.props_panel.propertyChanged.connect(self.on_property_changed)
        self.props_panel.removeRequested.connect(self.on_remove_requested)
        self.content_splitter.addWidget(self.props_panel)
        
        self.selection_timer = QTimer(self)
        self.selection_timer.setSingleShot(True)
        self.selection_timer.setInterval(150)
        self.selection_timer.timeout.connect(self._apply_selection_debounced)

        self.content_splitter.setSizes([850, 350])

        self.slideshow_timer = QTimer(self)
        self.slideshow_timer.timeout.connect(self._on_slideshow_timeout)
        self.current_playlist = []
        self.current_playlist_index = -1

        self.event_bus = EventBus.instance()
        self.event_bus.event_occurred.connect(self._on_event)
        
        self._apply_initial_style()
        
        self._start_library_loading()

    def _apply_initial_style(self):
        theme_name = self.config.get("theme", "Oscuro")
        accent_color = self.config.get("accent_color", "#3498db")
        self._apply_theme(theme_name, accent_color)
        if hasattr(self, 'about_page'):
            self.about_page.update_accent_color(accent_color)

    @Slot(str, object)
    def _on_event(self, event_name, data):
        if event_name == "config_changed":
            key = data.get("key")
            value = data.get("value")
            self._apply_config_change(key, value)

    def _apply_config_change(self, key, value):
        if key == "theme":
            accent_color = self.config.get("accent_color", "#3498db")
            self._apply_theme(value, accent_color)
        elif key == "accent_color":
            theme_name = self.config.get("theme", "Oscuro")
            self._apply_theme(theme_name, value)
            if hasattr(self, 'about_page'):
                self.about_page.update_accent_color(value)
        elif key in ["slideshow_interval", "slideshow_random"]:
            self._restart_slideshow_timer()

    def _apply_theme(self, theme_name, accent_color):
        from ui.styles import DARK_THEME, CLARO_THEME, MATERIAL_DARK_THEME, FUSION_V15_THEME
        
        themes = {
            "Oscuro": DARK_THEME,
            "Claro": CLARO_THEME,
            "Material Dark": MATERIAL_DARK_THEME,
            "Fusión V15": FUSION_V15_THEME
        }
        
        style_sheet = themes.get(theme_name, DARK_THEME)
        
        style_sheet = style_sheet.replace("#007acc", accent_color)
        
        from PySide6.QtGui import QPalette, QColor
        palette = self.palette()
        q_accent = QColor(accent_color)
        palette.setColor(QPalette.Highlight, q_accent)
        palette.setColor(QPalette.Accent, q_accent)
        palette.setColor(QPalette.Link, q_accent)
        self.setPalette(palette)
        
        self.setStyleSheet(style_sheet)
        logging.info(f"Applied theme: {theme_name} with accent color: {accent_color}")

    def switch_page(self, name):
        widgets = {
            "library": self.lib_page,
            "monitors": self.mon_page,
            "design": self.design_page,
            "settings": self.settings_page,
            "about": self.about_page
        }
        target = widgets.get(name)
        if target:
            self.pages.setCurrentWidget(target)

    def on_stop_all(self):
        if self.controller:
            self.controller.stop_all()
        self.slideshow_timer.stop()

    def _start_library_loading(self):
        self.lib_page.grid.clear()
        self.loader_thread = LibraryLoaderWorker(self.resources)
        self.loader_thread.itemLoaded.connect(self._on_wallpaper_loaded)
        self.loader_thread.start()

    def _on_wallpaper_loaded(self, name, w_type, thumb, path):
        self.lib_page.grid.add_wallpaper(name, w_type, thumbnail_path=thumb, data=path)

    def on_selection_changed(self, selected, deselected):
        self.selection_timer.start()

    def _apply_selection_debounced(self):
        """Processes the selection after a short delay (debounced)."""
        indexes = self.lib_page.grid.selectionModel().selectedIndexes()
        if not indexes:
            self.slideshow_timer.stop()
            self.current_playlist = []
            self.lib_page.update_selection_list([])
            return

        new_playlist = []
        items = []
        for idx in indexes:
            item = self.lib_page.grid.model.itemFromIndex(idx)
            if item:
                new_playlist.append({
                    'path': item.data(Qt.UserRole + 2),
                    'type': item.data(Qt.UserRole + 1),
                    'name': item.text()
                })
                items.append(item)
        
        self.current_playlist = new_playlist
        self.lib_page.update_selection_list(items)
        self.current_playlist_index = -1 

        last_item = items[-1]
        path = last_item.data(Qt.UserRole + 2)
        w_type = last_item.data(Qt.UserRole + 1)
        name = last_item.text()
        
        pixmap = last_item.icon().pixmap(290, 165)
        self.props_panel.load_wallpaper(name, w_type, path, config=self.config)
        self.props_panel.preview_box.setPixmap(pixmap)
        
        try: self.props_panel.apply_btn.clicked.disconnect()
        except: pass
        self.props_panel.apply_btn.clicked.connect(lambda: self._apply_selection(self.current_playlist))

    def _apply_selection(self, playlist):
        if not playlist: return
        if len(playlist) > 1:
            self.current_playlist_index = -1
            self._restart_slideshow_timer()
            self._on_slideshow_timeout()
        else:
            self._apply_wallpaper(playlist[0]['path'])

    def _restart_slideshow_timer(self):
        if len(self.current_playlist) <= 1:
            return
        interval = self.config.get("slideshow_interval", 30)
        self.slideshow_timer.start(interval * 60 * 1000)
        logging.info(f"Slideshow timer started: {interval} min")

    def _on_slideshow_timeout(self):
        if not self.current_playlist:
            return

        if self.config.get("slideshow_random", False):
            self.current_playlist_index = random.randint(0, len(self.current_playlist) - 1)
        else:
            self.current_playlist_index = (self.current_playlist_index + 1) % len(self.current_playlist)

        target = self.current_playlist[self.current_playlist_index]
        logging.info(f"Slideshow: Switching to {target['name']}")
        self._apply_wallpaper(target['path'])

    def _apply_wallpaper(self, path):
        if self.controller:
            for m in self.controller.monitors:
                self.controller.set_wallpaper_for_monitor(m['id'], path)

    def on_wallpaper_selected(self, index):
        pass

    def on_remove_requested(self):
        indexes = self.lib_page.grid.selectionModel().selectedIndexes()
        if not indexes:
            logging.info("Intento de eliminar sin selección activa.")
            return

        # Filtrar por filas únicas para evitar procesar la misma fila varias veces
        unique_rows = sorted(list(set(idx.row() for idx in indexes)), reverse=True)
        count = len(unique_rows)
        
        if count == 1:
            item = self.lib_page.grid.model.item(unique_rows[0])
            msg = f"¿Estás seguro de que deseas eliminar '{item.text()}'?"
        else:
            msg = f"¿Estás seguro de que deseas eliminar {count} elemento(s)?"

        res = QMessageBox.question(self, "Confirmar Eliminación", msg, 
                                 QMessageBox.Yes | QMessageBox.No)
        
        if res == QMessageBox.Yes:
            for row in unique_rows:
                item = self.lib_page.grid.model.item(row)
                if not item: continue
                
                path = item.data(Qt.UserRole + 2)
                
                # Intentar borrar el archivo físico si es local
                if path and os.path.exists(path) and os.path.isfile(path):
                    try:
                        os.remove(path)
                        logging.info(f"Archivo físico eliminado: {path}")
                    except Exception as e:
                        logging.error(f"No se pudo eliminar el archivo {path}: {e}")
                
                self.lib_page.grid.model.removeRow(row)
            
            # Limpiar selección y refrescar interfaz
            self.lib_page.grid.clearSelection()
            self.on_selection_changed(None, None)
            logging.info(f"Eliminados {count} elementos de la biblioteca.")

    def on_property_changed(self, key, value):
        logging.info(f"[UI] Property changed: {key} = {value}")
        if self.config: 
            self.config.set(key, value)

    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        if self.isVisible():
            self.hide()
            event.ignore()

    def open_url_dialog(self):
        dialog = UrlDialog(self)
        if dialog.exec():
            data = dialog.result_data
            if data: 
                self.lib_page.grid.add_wallpaper(data['name'], data['type'], data=data['url'])
