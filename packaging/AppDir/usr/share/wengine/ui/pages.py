from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QGridLayout,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSlider,
    QFormLayout,
    QGroupBox,
    QSpacerItem,
    QSizePolicy,
    QColorDialog,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal, QUrl, QTimer, QSize
from PySide6.QtGui import QIcon, QColor, QDesktopServices, QPixmap
from ui.wallpaper_grid import WallpaperGrid
import os


class BasePage(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)


class LibraryPage(BasePage):
    wallpaperSelected = Signal(object)
    addUrlRequested = Signal()

    def __init__(self, parent=None):
        super().__init__("Biblioteca", parent)

        action_bar = QHBoxLayout()

        self.add_url_btn = QPushButton("Añadir desde URL")
        self.add_url_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_url_btn.clicked.connect(self.addUrlRequested.emit)
        action_bar.addWidget(self.add_url_btn)

        self.open_folder_btn = QPushButton("Abrir carpeta")
        self.open_folder_btn.setIcon(QIcon.fromTheme("folder-open"))
        self.open_folder_btn.clicked.connect(self.open_wallpaper_folder)
        action_bar.addWidget(self.open_folder_btn)

        action_bar.addStretch()
        self.layout.addLayout(action_bar)

        self.grid = WallpaperGrid()
        self.grid.clicked.connect(self.wallpaperSelected.emit)
        self.layout.addWidget(self.grid)

        self.selection_tray = QGroupBox("Fondos Seleccionados")
        self.selection_tray.setMaximumHeight(180)
        tray_layout = QVBoxLayout(self.selection_tray)

        from PySide6.QtWidgets import QListWidget

        self.selection_list = QListWidget()
        self.selection_list.setFlow(QListWidget.LeftToRight)
        self.selection_list.setIconSize(QSize(160, 90))
        self.selection_list.setViewMode(QListWidget.IconMode)
        self.selection_list.setResizeMode(QListWidget.Adjust)
        self.selection_list.setMovement(QListWidget.Static)
        tray_layout.addWidget(self.selection_list)

        self.layout.addWidget(self.selection_tray)

    def update_selection_list(self, items):
        """Updates the tray list with selected items (name + icon)."""
        from PySide6.QtWidgets import QListWidgetItem

        self.selection_list.clear()
        for item in items:
            new_item = QListWidgetItem(item.icon(), item.text())
            self.selection_list.addItem(new_item)

    def open_wallpaper_folder(self):
        path = os.path.expanduser("~/Vídeos/Wallpapers/")
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))


class MonitorPage(BasePage):
    def __init__(self, config=None, parent=None):
        super().__init__("Monitores", parent)
        self.config = config

        group = QGroupBox("Configuración de Pantallas")
        form = QFormLayout(group)

        self.monitor_combo = QComboBox()
        self.monitor_combo.addItems(["Auto", "Pantalla 1", "Pantalla 2"])
        if self.config:
            self.monitor_combo.setCurrentText(self.config.get("target_monitor", "Auto"))
            self.monitor_combo.currentTextChanged.connect(
                lambda v: self.config.set("target_monitor", v)
            )
        form.addRow("Seleccionar Monitor:", self.monitor_combo)

        self.layout.addWidget(group)

        layout_group = QGroupBox("Modo de Disposición")
        layout_form = QFormLayout(layout_group)
        self.layout_mode = QComboBox()
        self.layout_mode.addItems(["Individual", "Duplicado", "Extendido (Span)"])
        if self.config:
            self.layout_mode.setCurrentText(
                self.config.get("layout_mode", "Individual")
            )
            self.layout_mode.currentTextChanged.connect(
                lambda v: self.config.set("layout_mode", v)
            )
        layout_form.addRow("Modo:", self.layout_mode)
        self.layout.addWidget(layout_group)

        self.layout.addStretch()


class DesignPage(BasePage):
    def __init__(self, config=None, parent=None):
        super().__init__("Personalización", parent)
        self.config = config

        style_group = QGroupBox("Estilo de la Interfaz")
        style_form = QFormLayout(style_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Oscuro", "Claro", "Material Dark", "Fusión V15"])
        if self.config:
            self.theme_combo.setCurrentText(self.config.get("theme", "Oscuro"))
            self.theme_combo.currentTextChanged.connect(self._on_theme_preset_changed)
        style_form.addRow("Tema Predeterminado:", self.theme_combo)

        self.transparency_spin = QSpinBox()
        self.transparency_spin.setRange(30, 100)
        self.transparency_spin.setSuffix("%")
        if self.config:
            val = self.config.get("window_transparency", 100)
            self.transparency_spin.setValue(int(val))
            self.transparency_spin.valueChanged.connect(
                lambda v: self.config.set("window_transparency", v)
            )
        style_form.addRow("Transparencia:", self.transparency_spin)

        from PySide6.QtWidgets import QFontComboBox

        self.font_combo = QFontComboBox()
        if self.config:
            self.font_combo.setCurrentFont(self.config.get("ui_font", "Segoe UI"))
            self.font_combo.currentFontChanged.connect(
                lambda f: self.config.set("ui_font", f.family())
            )
        style_form.addRow("Tipografía:", self.font_combo)

        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["80%", "90%", "100%", "110%", "125%", "150%"])
        if self.config:
            self.scale_combo.setCurrentText(self.config.get("ui_scaling", "100%"))
            self.scale_combo.currentTextChanged.connect(
                lambda v: self.config.set("ui_scaling", v)
            )
        style_form.addRow("Escala de Interfaz:", self.scale_combo)

        self.enable_anim = QCheckBox("Activar Animaciones (Transiciones)")
        if self.config:
            self.enable_anim.setChecked(self.config.get("ui_animations", True))
            self.enable_anim.stateChanged.connect(
                lambda s: self.config.set("ui_animations", s == 2)
            )
        style_form.addRow(self.enable_anim)

        self.enable_effects = QCheckBox("Activar Efectos Visuales (Sombras/Glow)")
        if self.config:
            self.enable_effects.setChecked(self.config.get("ui_effects", True))
            self.enable_effects.stateChanged.connect(
                lambda s: self.config.set("ui_effects", s == 2)
            )
        style_form.addRow(self.enable_effects)

        self.layout.addWidget(style_group)

        color_group = QGroupBox("Colores Personalizados")
        self.color_layout = QGridLayout(color_group)
        self.color_buttons = {}

        # Color Matrix
        self.colors_config = [
            ("Color de Acento", "accent_color", "#3498db"),
            ("Fondo de Interfaz", "ui_bg_color", "#1e1e1e"),
            ("Color de Texto", "ui_text_color", "#ffffff"),
        ]

        self._refresh_color_grid()

        self.layout.addWidget(color_group)
        self.layout.addStretch()

    def _refresh_color_grid(self):
        # Clear existing buttons
        for i in reversed(range(self.color_layout.count())):
            item = self.color_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        for i, (label, key, default) in enumerate(self.colors_config):
            self.color_layout.addWidget(QLabel(f"{label}:"), i, 0)
            btn = QPushButton()
            btn.setFixedSize(60, 25)
            val = self.config.get(key, default)
            btn.setStyleSheet(f"background-color: {val}; border: 1px solid #555;")
            btn.clicked.connect(
                lambda checked=False, k=key, b=btn: self.pick_color(k, b)
            )
            self.color_layout.addWidget(btn, i, 1)
            self.color_buttons[key] = btn

    def _on_theme_preset_changed(self, theme_name):
        presets = {
            "Oscuro": ("#1e1e1e", "#ffffff", "#007acc"),
            "Claro": ("#f5f5f7", "#1d1d1f", "#007acc"),
            "Material Dark": ("#121212", "#e1e1e1", "#007acc"),
            "Fusión V15": ("#0f0c29", "#00d2ff", "#007acc"),
        }

        if theme_name in presets:
            bg, text, accent = presets[theme_name]
            self.config.set("theme", theme_name)
            self.config.set("ui_bg_color", bg)
            self.config.set("ui_text_color", text)
            self.config.set("accent_color", accent)
            self._refresh_color_grid()

    def pick_color(self, key, button):
        current = QColor(self.config.get(key, "#ffffff"))
        color = QColorDialog.getColor(current, self, "Seleccionar Color")
        if color.isValid():
            hex_color = color.name()
            button.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #555;"
            )
            if self.config:
                self.config.set(key, hex_color)
                # Auto-detect contrast if changing background
                if key == "ui_bg_color":
                    self._auto_contrast_text(color)

    def _auto_contrast_text(self, bg_color):
        # Simple luminance check
        lum = (
            0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        ) / 255
        new_text_color = "#000000" if lum > 0.5 else "#ffffff"
        # We don't force it, but we could. For now let's just update the config
        # to suggest it if the user hasn't set a custom one.
        self.config.set("ui_text_color", new_text_color)


class SettingsPage(BasePage):
    def __init__(self, config=None, controller=None, parent=None):
        super().__init__("Ajustes del Sistema", parent)
        self.config = config
        self.controller = controller

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        container_layout = QVBoxLayout(container)

        # --- GRUPO GENERAL ---
        gen_group = QGroupBox("General")
        gen_form = QFormLayout(gen_group)

        self.auto_start = QCheckBox("Iniciar con el sistema (Auto-Start)")
        if self.config:
            self.auto_start.setChecked(self.config.get("autostart", False))
            self.auto_start.stateChanged.connect(
                lambda s: self.config.set("autostart", s == 2)
            )
        gen_form.addRow(self.auto_start)

        self.pause_active = QCheckBox("Pausar automáticamente cuando hay:")
        if self.config:
            self.pause_active.setChecked(self.config.get("pause_on_active", True))
            self.pause_active.stateChanged.connect(
                lambda s: self.config.set("pause_on_active", s == 2)
            )
        gen_form.addRow(self.pause_active)

        self.pause_mode = QComboBox()
        self.pause_mode.addItems(["Ventana activa", "Maximizada", "Pantalla completa"])

        self.mode_map = {
            "Ventana activa": "Any Window",
            "Maximizada": "Maximized",
            "Pantalla completa": "Fullscreen",
        }
        self.inv_mode_map = {v: k for k, v in self.mode_map.items()}

        if self.config:
            current_internal = self.config.get("pause_mode", "Fullscreen")
            self.pause_mode.setCurrentText(
                self.inv_mode_map.get(current_internal, "Pantalla completa")
            )
            self.pause_mode.currentTextChanged.connect(self._on_pause_mode_changed)

        gen_form.addRow("Modo de Pausa:", self.pause_mode)
        container_layout.addWidget(gen_group)

        # --- GRUPO RENDIMIENTO ---
        perf_group = QGroupBox("Rendimiento y Video")
        perf_form = QFormLayout(perf_group)

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["mpv", "web", "parallax"])
        if self.config:
            self.engine_combo.setCurrentText(self.config.get("engine", "mpv"))
            self.engine_combo.currentTextChanged.connect(
                lambda v: self.config.set("engine", v)
            )
        perf_form.addRow("Motor de Renderizado:", self.engine_combo)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(
            ["Nativa", "1080p (Full HD)", "720p (HD)", "480p (SD)"]
        )
        if self.config:
            self.resolution_combo.setCurrentText(
                self.config.get("video_resolution", "Nativa")
            )
            self.resolution_combo.currentTextChanged.connect(
                lambda v: self.config.set("video_resolution", v)
            )
        perf_form.addRow("Resolución de Video:", self.resolution_combo)

        self.hwdec_combo = QComboBox()
        self.hwdec_combo.addItems(["auto", "vaapi", "nvdec", "none"])
        if self.config:
            self.hwdec_combo.setCurrentText(self.config.get("hwdec", "auto"))
            self.hwdec_combo.currentTextChanged.connect(
                lambda v: self.config.set("hwdec", v)
            )
        perf_form.addRow("Decodificación de Hardware:", self.hwdec_combo)

        self.gpu_api = QComboBox()
        self.gpu_api.addItems(["vulkan", "opengl"])
        if self.config:
            api = self.config.get("gpu_api", "vulkan")
            if api not in ["vulkan", "opengl"]:
                api = "vulkan"
            self.gpu_api.setCurrentText(api)
            self.gpu_api.currentTextChanged.connect(
                lambda v: self.config.set("gpu_api", v)
            )
        perf_form.addRow("API de GPU:", self.gpu_api)

        self.cache_combo = QComboBox()
        self.cache_combo.addItems(["Disco (Estándar)", "RAM (Ultra)"])
        if self.config:
            is_ram = self.config.get("video_cache", "disk") == "ram"
            self.cache_combo.setCurrentText(
                "RAM (Ultra)" if is_ram else "Disco (Estándar)"
            )
            self.cache_combo.currentTextChanged.connect(self._on_cache_mode_changed)
        perf_form.addRow("Carga de Video:", self.cache_combo)

        self.fps_limit = QSpinBox()
        self.fps_limit.setRange(15, 144)
        self.fps_limit.setSuffix(" FPS")
        if self.config:
            val = self.config.get("fps_limit", 60)
            try:
                self.fps_limit.setValue(int(val))
            except:
                self.fps_limit.setValue(60)
            self.fps_limit.valueChanged.connect(
                lambda v: self.config.set("fps_limit", v)
            )
        perf_form.addRow("Límite de FPS:", self.fps_limit)
        container_layout.addWidget(perf_group)

        # --- GRUPO AUDIO ---
        audio_group = QGroupBox("Audio")
        audio_form = QFormLayout(audio_group)
        self.mute_audio = QCheckBox("Silenciar audio por defecto")
        if self.config:
            self.mute_audio.setChecked(self.config.get("mute", False))
            self.mute_audio.stateChanged.connect(
                lambda s: self.config.set("mute", s == 2)
            )
        audio_form.addRow(self.mute_audio)
        container_layout.addWidget(audio_group)

        # --- OPTIMIZACIÓN GNOME ---
        from core.desktop_helper import DesktopHelper

        if DesktopHelper.is_gnome():
            gnome_group = QGroupBox("Optimización para GNOME")
            gnome_layout = QVBoxLayout(gnome_group)
            info_label = QLabel("En GNOME Wayland, se requiere una pequeña extensión.")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #aaa; font-size: 11px;")
            gnome_layout.addWidget(info_label)
            self.install_gnome_btn = QPushButton("Instalar Extensión de Fondo")
            if DesktopHelper.is_extension_installed():
                self.install_gnome_btn.setText("Reinstalar / Actualizar Extensión")
            self.install_gnome_btn.clicked.connect(self._on_install_gnome_ext)
            gnome_layout.addWidget(self.install_gnome_btn)
            container_layout.addWidget(gnome_group)

        container_layout.addStretch()
        scroll.setWidget(container)
        self.layout.addWidget(scroll)

    def _on_pause_mode_changed(self, text):
        if hasattr(self, "mode_map") and text in self.mode_map:
            internal_val = self.mode_map[text]
            self.config.set("pause_mode", internal_val)

    def _on_cache_mode_changed(self, text):
        val = "Memory" if "RAM" in text else "Disk"
        self.config.set("video_cache", val)

    def _on_install_gnome_ext(self):
        from core.desktop_helper import DesktopHelper
        from PySide6.QtWidgets import QMessageBox

        success, message = DesktopHelper.install_extension()
        if success:
            QMessageBox.information(self, "GNOME Helper", message)
            self.install_gnome_btn.setText("Extensión Instalada")
        else:
            QMessageBox.critical(
                self, "Error", f"No se pudo instalar la extensión: {message}"
            )
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #aaa; font-size: 11px;")
            gnome_layout.addWidget(info_label)

            self.install_gnome_btn = QPushButton("Instalar Extensión de Fondo")
            if DesktopHelper.is_extension_installed():
                self.install_gnome_btn.setText("Reinstalar / Actualizar Extensión")

            self.install_gnome_btn.clicked.connect(self._on_install_gnome_ext)
            gnome_layout.addWidget(self.install_gnome_btn)

            container_layout.addWidget(gnome_group)

        container_layout.addStretch()
        scroll.setWidget(container)
        self.layout.addWidget(scroll)

    def _on_install_gnome_ext(self):
        from core.desktop_helper import DesktopHelper
        from PySide6.QtWidgets import QMessageBox

        success, message = DesktopHelper.install_extension()
        if success:
            QMessageBox.information(self, "GNOME Helper", message)
            self.install_gnome_btn.setText("Extensión Instalada")
        else:
            QMessageBox.critical(
                self, "Error", f"No se pudo instalar la extensión: {message}"
            )


class AboutPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("", parent)

        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        self.layout.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setObjectName("about_container")
        self.card.setFixedSize(600, 550)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setSpacing(10)
        card_layout.setAlignment(Qt.AlignTop)

        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(60)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor("#007acc"))
        self.card.setGraphicsEffect(self.shadow)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "Trinity.svg"
        )
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        icon_label.setStyleSheet("background: transparent; margin-bottom: 5px;")
        card_layout.addWidget(icon_label)

        self.author_label = QLabel("ALEXANDER GOMEZ")

        self.author_label.setObjectName("author_name")
        self.author_label.setAlignment(Qt.AlignCenter)
        self.author_label.setStyleSheet(
            "font-size: 32px; font-weight: 900; color: #007acc; background: transparent;"
        )
        card_layout.addWidget(self.author_label)

        by_label = QLabel("GAMING OF DEMON")
        by_label.setStyleSheet(
            "font-size: 13px; color: #555; font-weight: 800; letter-spacing: 5px; margin-bottom: 15px; background: transparent;"
        )
        by_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(by_label)

        self.inner_scroll = QScrollArea()
        self.inner_scroll.setWidgetResizable(True)
        self.inner_scroll.setFrameShape(QFrame.NoFrame)
        self.inner_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.inner_scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 20, 10, 20)
        scroll_layout.setSpacing(20)

        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setTextFormat(Qt.RichText)

        about_text = (
            "<div style='line-height: 160%; color: #aaa;'>"
            "W-Engine Pro nace de la necesidad de contar con un entorno de escritorio dinámico, "
            "moderno y profesional en Linux, comparable a soluciones como Wallpaper Engine en otros sistemas operativos.<br><br>"
            "Este proyecto tiene como objetivo ofrecer una herramienta ligera, eficiente y fácil de usar, "
            "permitiendo a los usuarios personalizar su escritorio mediante fondos animados y contenido "
            "multimedia de alta calidad, sin comprometer el rendimiento del sistema.<br><br>"
            "A diferencia de soluciones tradicionales, W-Engine Pro incorpora un motor inteligente de "
            "detección de actividad, capaz de optimizar automáticamente el uso de recursos. Esto permite "
            "pausar o reducir la carga del sistema cuando el usuario está ejecutando tareas exigentes, "
            "logrando un equilibrio ideal entre estética y rendimiento.<br><br>"
            "<b style='color: white; font-size: 18px;'> Características principales</b><br>"
            "• Soporte para fondos animados (video y renderizado)<br>"
            "• Reproducción de wallpapers mediante URL/enlace directo<br>"
            "• Actualización en tiempo real sin reiniciar el motor<br>"
            "• Sistema de configuración dinámica sincronizada con la interfaz<br>"
            "• Auto-guardado inteligente sin interrupciones<br>"
            "• Soporte multi-monitor<br>"
            "• Arquitectura optimizada para bajo consumo de CPU/GPU<br><br>"
            "<b style='color: white; font-size: 18px;'> Filosofía del proyecto</b><br>"
            "W-Engine Pro está diseñado bajo una arquitectura modular y reactiva, donde cada componente "
            "del sistema se comunica de forma eficiente para permitir cambios instantáneos.<br><br>"
            "El enfoque principal es brindar máxima fluidez, alta personalización, control total del "
            "usuario y compatibilidad con múltiples entornos Linux.<br><br>"
            "<b style='color: white; font-size: 18px;'> Funciones experimentales</b><br>"
            "Algunas características avanzadas dependen del entorno de escritorio y se encuentran en desarrollo:<br>"
            "• Integración del wallpaper como fondo real sin cubrir iconos<br>"
            "• Compatibilidad avanzada con distintos gestores de ventanas<br>"
            "• Soporte limitado en Wayland debido a restricciones del sistema<br><br>"
            "<b style='color: white; font-size: 18px;'> Compatibilidad</b><br>"
            "• KDE Plasma (X11): Estable<br>"
            "• XFCE: Estable<br>"
            "• GNOME (X11): Parcial<br>"
            "• Wayland: Experimental<br><br>"
            "<b style='color: white; font-size: 18px;'> Tecnologías</b><br>"
            "• Python 3 / Qt6<br>"
            "• OpenGL / Renderizado por hardware<br>"
            "• Arquitectura desacoplada (Engine + UI)<br><br>"
            "<b style='color: white; font-size: 18px;'> Desarrollo</b><br>"
            "Desarrollado como un proyecto independiente enfocado en llevar la personalización del "
            "escritorio Linux a un nuevo nivel, combinando rendimiento, estética y control.<br><br>"
            "Actualmente en desarrollo activo, con mejoras constantes en estabilidad, rendimiento y nuevas funcionalidades.<br><br>"
            "<b style='color: white; font-size: 18px;'> Visión</b><br>"
            "Convertirse en una alternativa nativa sólida y eficiente en Linux para la personalización "
            "avanzada del escritorio, manteniendo un equilibrio perfecto entre potencia y ligereza."
            "</div>"
        )
        self.desc_label.setText(about_text)
        self.desc_label.setStyleSheet("background: transparent;")
        scroll_layout.addWidget(self.desc_label)

        self.inner_scroll.setWidget(scroll_content)
        card_layout.addWidget(self.inner_scroll)

        card_layout.addSpacing(10)
        self.discord_btn = QPushButton(" UNIRSE AL DISCORD")
        self.discord_btn.setObjectName("discord_btn")
        self.discord_btn.setCursor(Qt.PointingHandCursor)
        self.discord_btn.setMinimumHeight(55)
        self.discord_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://discord.gg/xTdmDHfgZT"))
        )
        card_layout.addWidget(self.discord_btn)

        # Centering the card vertically and horizontally
        self.layout.addStretch(1)
        self.layout.addWidget(self.card, 0, Qt.AlignCenter)
        self.layout.addStretch(1)

        # --- FOOTER (BOTÓN LOGS + VERSIÓN) ---
        footer_container = QWidget()
        footer_layout = QHBoxLayout(footer_container)
        footer_layout.setContentsMargins(10, 0, 10, 5)

        self.logs_btn = QPushButton(" VER LOGS")
        self.logs_btn.setFixedWidth(100)
        self.logs_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.03);
                color: #444;
                font-size: 10px;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 4px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                color: #666;
            }
        """)
        self.logs_btn.setCursor(Qt.PointingHandCursor)
        self.logs_btn.clicked.connect(self._open_logs)
        footer_layout.addWidget(self.logs_btn, 0, Qt.AlignLeft)

        footer_label = QLabel("v1.5 BETA EDITION • 2026")
        footer_label.setStyleSheet("color: #333; font-size: 10px; font-weight: bold;")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(footer_label, 1)

        footer_layout.addSpacing(100)  # Right balance

        self.layout.addWidget(footer_container)

        self.scroll_timer = QTimer(self)
        self.scroll_timer.setInterval(50)
        self.scroll_timer.timeout.connect(self._auto_scroll)
        self.scroll_pos = 0

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.scroll_timer.start)

        self.inner_scroll.verticalScrollBar().sliderPressed.connect(
            self._on_user_interaction
        )
        self.inner_scroll.verticalScrollBar().sliderMoved.connect(
            self._on_user_interaction
        )
        self.inner_scroll.verticalScrollBar().valueChanged.connect(
            self._on_value_changed
        )

    def showEvent(self, event):
        """Start auto-scroll when page becomes visible."""
        super().showEvent(event)
        self.scroll_pos = 0
        if hasattr(self, "inner_scroll"):
            self.inner_scroll.verticalScrollBar().setValue(0)
        if hasattr(self, "inactivity_timer"):
            self.inactivity_timer.start(6000)

    def hideEvent(self, event):
        """Stop all timers when page is hidden."""
        super().hideEvent(event)
        if hasattr(self, "scroll_timer"):
            self.scroll_timer.stop()
        if hasattr(self, "inactivity_timer"):
            self.inactivity_timer.stop()

    def _on_user_interaction(self):
        """User is manually scrolling."""
        if hasattr(self, "scroll_timer"):
            self.scroll_timer.stop()
        if hasattr(self, "inactivity_timer"):
            self.inactivity_timer.start(4000)

    def _on_value_changed(self, value):
        """Detect manual scroll wheel or keyboard interaction."""
        if value != self.scroll_pos:
            if hasattr(self, "scroll_timer"):
                self.scroll_timer.stop()
            if hasattr(self, "inactivity_timer"):
                self.inactivity_timer.start(4000)

    def _auto_scroll(self):
        if not hasattr(self, "inner_scroll"):
            return
        v_bar = self.inner_scroll.verticalScrollBar()
        if self.scroll_pos < v_bar.maximum():
            self.scroll_pos += 1
            v_bar.setValue(self.scroll_pos)
        else:
            self.scroll_pos = -50
            v_bar.setValue(0)
            if hasattr(self, "scroll_timer"):
                self.scroll_timer.stop()
            if hasattr(self, "inactivity_timer"):
                self.inactivity_timer.start(4000)

    def _open_logs(self):
        log_path = os.path.expanduser("~/.config/w-engine-pro/engine.log")
        if os.path.exists(log_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(log_path))
        else:
            log_dir = os.path.dirname(log_path)
            if os.path.exists(log_dir):
                QDesktopServices.openUrl(QUrl.fromLocalFile(log_dir))

    def update_accent_color(self, hex_color):
        """Updates the UI elements to match the new accent color."""
        if hasattr(self, "shadow"):
            self.shadow.setColor(QColor(hex_color))
        if hasattr(self, "author_label"):
            self.author_label.setStyleSheet(
                f"font-size: 32px; font-weight: 900; color: {hex_color}; background: transparent;"
            )

        if hasattr(self, "discord_btn"):
            # 1. Update the button's base style
            self.discord_btn.setStyleSheet(f"""
                QPushButton#discord_btn {{
                    background-color: {hex_color};
                    color: white;
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 12px;
                    font-weight: 900;
                    font-size: 16px;
                    letter-spacing: 2px;
                    padding: 10px;
                }}
                QPushButton#discord_btn:hover {{
                    background-color: white;
                    color: {hex_color};
                    border: 2px solid {hex_color};
                }}
            """)

            # 2. Apply or update the REAL GLOW EFFECT (Drop Shadow)
            from PySide6.QtWidgets import QGraphicsDropShadowEffect

            if not hasattr(self, "btn_glow"):
                self.btn_glow = QGraphicsDropShadowEffect()
                self.btn_glow.setBlurRadius(25)
                self.btn_glow.setXOffset(0)
                self.btn_glow.setYOffset(0)
                self.discord_btn.setGraphicsEffect(self.btn_glow)

            self.btn_glow.setColor(QColor(hex_color))
