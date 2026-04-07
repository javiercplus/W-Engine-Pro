import logging
import os
import random
from typing import Any

from PySide6.QtCore import QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core import i18n
from core.desktop_helper import DesktopHelper
from core.event_bus import EventBus
from ui.diagnostics_panel import DiagnosticsPanel
from ui.pages import AboutPage, LibraryPage, MonitorPage
from ui.properties_panel import PropertiesPanel
from ui.settings_panel import SettingsPanel
from ui.sidebar import Sidebar
from ui.styles import STYLE_TEMPLATE
from ui.url_dialog import UrlDialog


class ThumbnailLoaderWorker(QThread):
    """Worker to load thumbnail in background and update UI when ready."""

    thumbnailReady = Signal(str, str)  # url, thumbnail_path

    def __init__(self, resources, url):
        super().__init__()
        self.resources = resources
        self.url = url

    def run(self):
        if self.resources and self.url:
            thumb_path = self.resources.get_thumbnail(self.url)
            if thumb_path:
                self.thumbnailReady.emit(self.url, thumb_path)


class LibraryLoaderWorker(QThread):
    itemLoaded = Signal(str, str, str, str)
    finished = Signal()

    def __init__(self, resources, config=None):
        super().__init__()
        self.resources = resources
        self.config = config

    def run(self):
        # Load local wallpapers
        if self.resources:
            wallpapers = self.resources.list_local_wallpapers()
            for v in wallpapers:
                name = os.path.basename(v)
                thumb = self.resources.get_thumbnail(v)
                self.itemLoaded.emit(name, "Video", thumb, v)

        # Load remote wallpapers from config
        if self.config:
            remote_list = self.config.get_setting("remote_wallpapers", [])
            for entry in remote_list:
                if isinstance(entry, dict):
                    url = entry.get("url")
                    name = entry.get("name", url.split("/")[-1] if url else "Remote")
                    w_type = entry.get("type", "Web")
                elif isinstance(entry, str):
                    url = entry
                    name = url.split("/")[-1]
                    w_type = "Web"
                else:
                    continue

                # Generate thumbnail for remote URLs
                thumb = None
                if self.resources and url:
                    thumb = self.resources.get_thumbnail(url)

                self.itemLoaded.emit(name, w_type, thumb, url)

        self.finished.emit()


class MainWindow(QMainWindow):
    theme_changed = Signal()

    def __init__(self, controller=None, config=None, resources=None):
        super().__init__()
        self.controller = controller
        self.config = config
        self.resources = resources
        self._apply_selection_connection = (
            None  # Track specific connection for wallpaper selection
        )

        self.setWindowTitle(i18n.t("app_name"))
        self.resize(1200, 800)

        # Explicitly set window flags to ensure maximize button is available
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        )

        # Allow resizing and maximizing
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        central_widget = QWidget()
        central_widget.setObjectName("central_widget_container")
        self.setCentralWidget(central_widget)

        # This is key for transparency in the central widget
        central_widget.setAutoFillBackground(False)

        self.main_v_layout = QVBoxLayout(central_widget)
        self.main_v_layout.setContentsMargins(0, 0, 0, 0)
        self.main_v_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.pageChanged.connect(self.switch_page)
        self.sidebar.fullscreenRequested.connect(self.toggle_fullscreen)
        self.main_v_layout.addWidget(self.sidebar)

        self.content_splitter = QSplitter(Qt.Horizontal)
        self.main_v_layout.addWidget(self.content_splitter)

        self.pages = QStackedWidget()

        self.lib_page = LibraryPage()
        self.lib_page.grid.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )
        self.lib_page.addUrlRequested.connect(self.open_url_dialog)

        self.mon_page = MonitorPage(config=self.config)
        self.diag_page = DiagnosticsPanel(controller=self.controller)
        self.settings_page = SettingsPanel(
            config=self.config, controller=self.controller
        )
        self.about_page = AboutPage()

        self.pages.addWidget(self.lib_page)
        self.pages.addWidget(self.mon_page)
        self.pages.addWidget(self.diag_page)
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(self.about_page)

        self.content_splitter.addWidget(self.pages)

        self.props_panel = PropertiesPanel(config=self.config)
        self.props_panel.propertyChanged.connect(self.on_property_changed)
        self.props_panel.removeRequested.connect(self.on_remove_requested)
        self.props_panel.stopAllRequested.connect(self.on_stop_all)
        self.props_panel.startRequested.connect(self.on_start_requested)
        self.props_panel.applyRequested.connect(self.on_apply_settings_requested)

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

        self.theme_timer = QTimer(self)
        self.theme_timer.setSingleShot(True)
        self.theme_timer.setInterval(100)
        self.theme_timer.timeout.connect(
            lambda: self._apply_theme(
                self.config.get("theme", "Oscuro"),
                self.config.get("accent_color", "#3498db"),
            )
        )

        self._apply_initial_style()

        self._start_library_loading()

        # GNOME Wayland experimental indicator in window title
        self._check_gnome_experimental()

    def _check_gnome_experimental(self):
        """Check if running on GNOME Wayland and add experimental indicator to title."""
        try:
            profile = DesktopHelper.get_profile()
            is_gnome = "gnome" in profile.compositor.lower()
            is_wayland = profile.protocol.lower() == "wayland"

            if is_gnome and is_wayland:
                self._gnome_experimental_indicator = True
                # Update window title to show experimental status
                base_title = i18n.t("app_name")
                self.setWindowTitle(f"{base_title} ⚠️ Experimental")
                logging.info("[GNOME] Experimental indicator added to window title")
        except Exception as e:
            logging.warning(f"Failed to check GNOME environment: {e}")

    def _apply_initial_style(self):
        theme_name = self.config.get("theme", "Oscuro")
        accent_color = self.config.get("accent_color", "#3498db")
        text_color = self.config.get("ui_text_color", "#ffffff")

        from ui.sidebar import set_icon_theme_color

        set_icon_theme_color(text_color)

        self._apply_theme(theme_name, accent_color)
        if hasattr(self, "about_page"):
            self.about_page.update_accent_color(accent_color)

    @Slot(str, Any)
    def _on_event(self, event_name, data):
        logging.info(f"[DEBUG] MainWindow._on_event: {event_name} - {data}")
        if event_name == "config_changed":
            key = data.get("key")
            value = data.get("value")
            self._apply_config_change(key, value)

    def _apply_config_change(self, key, value):
        theme_keys = [
            "theme",
            "accent_color",
            "ui_bg_color",
            "ui_text_color",
            "ui_font",
            "ui_scaling",
            "ui_animations",
            "ui_effects",
        ]
        if key in theme_keys:
            logging.info(f"Theme change detected for key: {key}")
            self.theme_timer.start()  # Debounced update
            if key == "accent_color" and hasattr(self, "about_page"):
                self.about_page.update_accent_color(value)
        elif key == "window_transparency":
            self.theme_timer.start()
        elif key in ["slideshow_interval", "slideshow_random"]:
            self._restart_slideshow_timer()

    def _apply_theme(self, theme_name, accent_color):
        bg_color = self.config.get("ui_bg_color", "#1e1e1e")
        text_color = self.config.get("ui_text_color", "#ffffff")
        accent_color = self.config.get("accent_color", "#3498db")
        font_family = self.config.get("ui_font", "Segoe UI")
        transparency = self.config.get("window_transparency", 100)

        # PERFORMANCE OPTIMIZATION: Avoid WA_TranslucentBackground unless strictly needed
        # It causes major lag on Linux compositors when moving windows.
        if transparency < 95:
            c = QColor(bg_color)
            alpha = transparency / 100.0
            bg_style = f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        else:
            bg_style = bg_color
            self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Apply style to application instead of window for better performance cache
        style_sheet = (
            STYLE_TEMPLATE.replace("{{BG_COLOR}}", bg_style)
            .replace("{{TEXT_COLOR}}", text_color)
            .replace("{{ACCENT_COLOR}}", accent_color)
            .replace("{{FONT_FAMILY}}", font_family)
        )

        # 3. Dynamic Scaling
        scale_str = self.config.get("ui_scaling", "100%")
        scale_percent = int(scale_str.replace("%", ""))
        base_size = 14
        scaled_size = int(base_size * (scale_percent / 100.0))
        style_sheet = style_sheet.replace(
            "font-size: 14px;", f"font-size: {scaled_size}px;"
        )

        # 4. Animations and Effects
        if not self.config.get("ui_animations", True):
            style_sheet += "\n/* Animations disabled: QSS does not support transition/animation properties */\n"

        if not self.config.get("ui_effects", True):
            # When effects are disabled, we simplify the look but keep the box model stable
            # to prevent overlapping options/collapsed layouts.
            style_sheet += """
                QPushButton, QLineEdit, QComboBox, QSpinBox {
                    border-radius: 0px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                QGroupBox {
                    border-radius: 0px;
                    margin-top: 1.5em;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }
                #about_container {
                    border-radius: 0px;
                }
            """

        logging.debug(f"StyleSheet generated: {len(style_sheet)} chars")
        # 5. Apply to entire Application for better global propagation
        app = QApplication.instance()
        if app:
            app.setStyleSheet(style_sheet)
        else:
            self.setStyleSheet(style_sheet)

        self.theme_changed.emit()

        from ui.sidebar import set_icon_theme_color

        set_icon_theme_color(text_color)
        self.sidebar.refresh_icons()

        # 6. Palette sync for native dialogs
        palette = self.palette()
        q_accent = QColor(accent_color)
        q_bg = QColor(bg_color)
        q_text = QColor(text_color)

        palette.setColor(QPalette.Window, q_bg)
        palette.setColor(QPalette.WindowText, q_text)
        palette.setColor(QPalette.Base, q_bg)
        palette.setColor(QPalette.Text, q_text)
        palette.setColor(QPalette.Button, q_bg)
        palette.setColor(QPalette.ButtonText, q_text)
        palette.setColor(QPalette.Highlight, q_accent)
        self.setPalette(palette)

    def switch_page(self, name):
        widgets = {
            "library": self.lib_page,
            "monitors": self.mon_page,
            "diagnostics": self.diag_page,
            "settings": self.settings_page,
            "about": self.about_page,
        }
        target = widgets.get(name)
        if target:
            self.pages.setCurrentWidget(target)

            # Performance Optimization: Only enable heavy effects on the active page
            if hasattr(self.about_page, "shadow"):
                self.about_page.shadow.setEnabled(name == "about")

    def on_stop_all(self):
        if self.controller and self.controller.renderer.is_running():
            self.controller.stop_all()
        self.slideshow_timer.stop()
        self.props_panel.update_stop_button_state(False)

    def on_start_requested(self):
        if self.current_playlist:
            self._apply_selection(self.current_playlist)
            self.props_panel.update_stop_button_state(True)

    def _start_library_loading(self):
        self.lib_page.grid.clear()
        self.loader_thread = LibraryLoaderWorker(self.resources, self.config)
        self.loader_thread.itemLoaded.connect(self._on_wallpaper_loaded)
        self.loader_thread.finished.connect(self._on_library_load_finished)
        self.loader_thread.start()

    def _on_library_load_finished(self):
        """Restore selection of last wallpaper after library is loaded."""
        if self.config:
            last_wp = self.config.get_setting("last_wallpaper")
            if last_wp:
                # Select by URL/path stored in data
                self.lib_page.grid.select_wallpaper(last_wp)
                # Trigger selection to update UI
                self.on_selection_changed(None, None)

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
                new_playlist.append(
                    {
                        "path": item.data(Qt.UserRole + 2),
                        "type": item.data(Qt.UserRole + 1),
                        "name": item.text(),
                    }
                )
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

        # Disconnect only the specific wallpaper selection connection
        # This preserves other connections like applyRequested for playback settings
        if self._apply_selection_connection is not None:
            try:
                self.props_panel.apply_btn.clicked.disconnect(
                    self._apply_selection_connection
                )
            except (TypeError, RuntimeError):
                pass
            self._apply_selection_connection = None

        # Connect new wallpaper selection handler
        self._apply_selection_connection = lambda: self._apply_selection(
            self.current_playlist
        )
        self.props_panel.apply_btn.clicked.connect(self._apply_selection_connection)

    def _apply_selection(self, playlist):
        if not playlist:
            return
        if len(playlist) > 1:
            self.current_playlist_index = -1
            self._restart_slideshow_timer()
            self._on_slideshow_timeout()
        else:
            self._apply_wallpaper(playlist[0]["path"])

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
            self.current_playlist_index = random.randint(
                0, len(self.current_playlist) - 1
            )
        else:
            self.current_playlist_index = (self.current_playlist_index + 1) % len(
                self.current_playlist
            )

        target = self.current_playlist[self.current_playlist_index]
        logging.info(f"Slideshow: Switching to {target['name']}")
        self._apply_wallpaper(target["path"])

    def _apply_wallpaper(self, path):
        if self.controller:
            for m in self.controller.monitors:
                self.controller.set_wallpaper_for_monitor(m["id"], path)

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
            msg = f"{i18n.t('confirm_delete_single').format(name=item.text())}"
        else:
            msg = i18n.t("confirm_delete_multiple").format(count=count)

        res = QMessageBox.question(
            self, i18n.t("confirm_delete_title"), msg, QMessageBox.Yes | QMessageBox.No
        )

        if res == QMessageBox.Yes:
            removed_urls = []
            for row in unique_rows:
                item = self.lib_page.grid.model.item(row)
                if not item:
                    continue

                path = item.data(Qt.UserRole + 2)
                removed_urls.append(path)

                # Intentar borrar el archivo físico si es local
                if path and os.path.exists(path) and os.path.isfile(path):
                    try:
                        os.remove(path)
                        logging.info(f"Archivo físico eliminado: {path}")
                    except Exception as e:
                        logging.error(f"No se pudo eliminar el archivo {path}: {e}")

                self.lib_page.grid.model.removeRow(row)

            # Eliminar de la configuración los wallpapers remotos y last_wallpaper
            if self.config and removed_urls:
                remote_list = self.config.get_setting("remote_wallpapers", [])
                if remote_list:
                    # Filtrar y mantener solo los que no fueron eliminados
                    new_remote_list = []
                    for entry in remote_list:
                        url = entry.get("url") if isinstance(entry, dict) else entry
                        if url not in removed_urls:
                            new_remote_list.append(entry)

                    # Solo actualizar si hubo cambios
                    if len(new_remote_list) != len(remote_list):
                        self.config.set_setting("remote_wallpapers", new_remote_list)
                        logging.info(
                            f"Eliminados {len(remote_list) - len(new_remote_list)} wallpapers remotos de la configuración"
                        )

                # Si el wallpaper eliminado es el last_wallpaper, limpiar esa configuración
                last_wp = self.config.get_setting("last_wallpaper")
                if last_wp and last_wp in removed_urls:
                    self.config.set_setting("last_wallpaper", None)
                    logging.info("last_wallpaper limpiado de la configuración")

            # Limpiar selección y refrescar interfaz
            self.lib_page.grid.clearSelection()
            self.on_selection_changed(None, None)
            logging.info(f"Eliminados {count} elementos de la biblioteca.")

    def on_property_changed(self, key, value):
        logging.info(f"[UI] Property changed: {key} = {value}")
        if self.config:
            self.config.set(key, value)

    def on_apply_settings_requested(self):
        """Force apply playback settings changes, restarting backend if needed."""
        logging.info("[UI] Apply settings requested - forcing backend restart")
        if self.controller and self.controller.active_wallpapers:
            # Force restart all active wallpapers to apply settings
            for monitor_id, video_path in list(
                self.controller.active_wallpapers.items()
            ):
                logging.info(f"[UI] Restarting wallpaper on monitor {monitor_id}")
                self.controller.renderer.restart(self.config, video_path)
        # Persist config to disk immediately to avoid losing playback settings
        try:
            if self.config:
                if hasattr(self.config, "_save") and callable(
                    getattr(self.config, "_save")
                ):
                    # Internal fast-save
                    self.config._save()
                elif hasattr(self.config, "save") and callable(
                    getattr(self.config, "save")
                ):
                    # Fallback if public API exists
                    self.config.save()
        except Exception as e:
            logging.error(f"[UI] Error saving config after apply: {e}")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        super().keyPressEvent(event)

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
                url = data["url"]
                name = data["name"]
                w_type = data["type"]

                # Persist remote wallpaper in config
                if self.config:
                    remote_list = self.config.get_setting("remote_wallpapers", [])
                    # Avoid duplicates
                    existing_urls = [
                        e.get("url") if isinstance(e, dict) else e for e in remote_list
                    ]
                    if url not in existing_urls:
                        remote_list.append({"name": name, "url": url, "type": w_type})
                        self.config.set_setting("remote_wallpapers", remote_list)

                # Add wallpaper with placeholder thumbnail
                self.lib_page.grid.add_wallpaper(name, w_type, data=url)

                # Start background thumbnail loading
                if self.resources:
                    self.thumb_loader = ThumbnailLoaderWorker(self.resources, url)
                    self.thumb_loader.thumbnailReady.connect(self._on_thumbnail_ready)
                    self.thumb_loader.start()

                # Automatically select and apply the newly added wallpaper
                self.lib_page.grid.select_wallpaper(url)
                # Trigger selection change to apply wallpaper
                self.on_selection_changed(None, None)

    def _on_thumbnail_ready(self, url, thumbnail_path):
        """Update wallpaper thumbnail when background loading completes."""
        self.lib_page.grid.update_thumbnail(url, thumbnail_path)
        # Refresh selection if this is the currently selected wallpaper
        selected_indexes = self.lib_page.grid.selectionModel().selectedIndexes()
        for idx in selected_indexes:
            item = self.lib_page.grid.model.itemFromIndex(idx)
            if item and item.data(Qt.UserRole + 2) == url:
                # Update preview in properties panel
                pixmap = item.icon().pixmap(290, 165)
                self.props_panel.preview_box.setPixmap(pixmap)
                break
