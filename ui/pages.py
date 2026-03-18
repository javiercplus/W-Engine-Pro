from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, 
    QGridLayout, QPushButton, QComboBox, QCheckBox, QSlider, QFormLayout,
    QGroupBox, QSpacerItem, QSizePolicy, QColorDialog
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

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.layout.addWidget(self.title_label)

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
            self.monitor_combo.currentTextChanged.connect(lambda v: self.config.set("target_monitor", v))
        form.addRow("Seleccionar Monitor:", self.monitor_combo)
        
        self.layout.addWidget(group)
        
        layout_group = QGroupBox("Modo de Disposición")
        layout_form = QFormLayout(layout_group)
        self.layout_mode = QComboBox()
        self.layout_mode.addItems(["Individual", "Duplicado", "Extendido (Span)"])
        if self.config:
             self.layout_mode.setCurrentText(self.config.get("layout_mode", "Individual"))
             self.layout_mode.currentTextChanged.connect(lambda v: self.config.set("layout_mode", v))
        layout_form.addRow("Modo:", self.layout_mode)
        self.layout.addWidget(layout_group)
        
        self.layout.addStretch()

class DesignPage(BasePage):
    def __init__(self, config=None, parent=None):
        super().__init__("Personalización", parent)
        self.config = config
        
        theme_group = QGroupBox("Interfaz y Estilo")
        theme_form = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Oscuro", "Claro", "Material Dark", "Fusión V15"])
        if self.config:
            self.theme_combo.setCurrentText(self.config.get("theme", "Oscuro"))
            self.theme_combo.currentTextChanged.connect(lambda v: self.config.set("theme", v))
        theme_form.addRow("Tema Visual:", self.theme_combo)
        
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["80%", "100%", "125%", "150%", "200%"])
        if self.config:
            self.scale_combo.setCurrentText(self.config.get("ui_scaling", "100%"))
            self.scale_combo.currentTextChanged.connect(lambda v: self.config.set("ui_scaling", v))
        theme_form.addRow("Escala de Interfaz:", self.scale_combo)
        
        self.layout.addWidget(theme_group)
        
        color_group = QGroupBox("Colores")
        color_layout = QHBoxLayout(color_group)
        
        color_label = QLabel("Color de Acento:")
        color_layout.addWidget(color_label)
        
        self.color_preview = QPushButton()
        self.color_preview.setFixedSize(60, 25)
        current_color = self.config.get("accent_color", "#3498db") if self.config else "#3498db"
        self.color_preview.setStyleSheet(f"background-color: {current_color}; border: 1px solid #555;")
        self.color_preview.clicked.connect(self.pick_color)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        
        self.layout.addWidget(color_group)
        
        self.layout.addStretch()

    def pick_color(self):
        current = QColor(self.config.get("accent_color", "#3498db"))
        color = QColorDialog.getColor(current, self, "Seleccionar Color de Acento")
        if color.isValid():
            hex_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #555;")
            if self.config:
                self.config.set("accent_color", hex_color)

class SettingsPage(BasePage):
    def __init__(self, config=None, parent=None):
        super().__init__("Ajustes del Sistema", parent)
        self.config = config
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        gen_group = QGroupBox("General")
        gen_form = QFormLayout(gen_group)
        
        self.auto_start = QCheckBox("Iniciar con el sistema (Auto-Start)")
        if self.config:
            self.auto_start.setChecked(self.config.get("autostart", False))
            self.auto_start.stateChanged.connect(lambda s: self.config.set("autostart", s == 2))
        gen_form.addRow(self.auto_start)
        
        self.pause_active = QCheckBox("Pausar cuando hay aplicaciones en pantalla completa")
        if self.config:
            self.pause_active.setChecked(self.config.get("pause_on_active", True))
            self.pause_active.stateChanged.connect(lambda s: self.config.set("pause_on_active", s == 2))
        gen_form.addRow(self.pause_active)
        
        self.pause_mode = QComboBox()
        self.pause_mode.addItems(["Fullscreen", "Maximized", "Any Window"])
        if self.config:
            self.pause_mode.setCurrentText(self.config.get("pause_mode", "Fullscreen"))
            self.pause_mode.currentTextChanged.connect(lambda v: self.config.set("pause_mode", v))
        gen_form.addRow("Modo de Pausa:", self.pause_mode)
        
        container_layout.addWidget(gen_group)
        
        perf_group = QGroupBox("Rendimiento y Video")
        perf_form = QFormLayout(perf_group)
        
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["mpv", "web", "parallax"])
        if self.config:
            self.engine_combo.setCurrentText(self.config.get("engine", "mpv"))
            self.engine_combo.currentTextChanged.connect(lambda v: self.config.set("engine", v))
        perf_form.addRow("Motor de Renderizado:", self.engine_combo)
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["Nativa", "1080p (Full HD)", "720p (HD)", "480p (SD)"])
        if self.config:
            self.resolution_combo.setCurrentText(self.config.get("video_resolution", "Nativa"))
            self.resolution_combo.currentTextChanged.connect(
                lambda v: self.config.set("video_resolution", v))
        perf_form.addRow("Resolución de Video:", self.resolution_combo)
        
        self.hwdec_combo = QComboBox()
        self.hwdec_combo.addItems(["auto", "vaapi", "nvdec", "none"])
        if self.config:
            self.hwdec_combo.setCurrentText(self.config.get("hwdec", "auto"))
            self.hwdec_combo.currentTextChanged.connect(lambda v: self.config.set("hwdec", v))
        perf_form.addRow("Decodificación de Hardware:", self.hwdec_combo)
        
        self.gpu_api = QComboBox()
        self.gpu_api.addItems(["vulkan", "opengl"])
        if self.config:
            api = self.config.get("gpu_api", "vulkan")
            if api not in ["vulkan", "opengl"]: api = "vulkan"
            self.gpu_api.setCurrentText(api)
            self.gpu_api.currentTextChanged.connect(lambda v: self.config.set("gpu_api", v))
        perf_form.addRow("API de GPU:", self.gpu_api)
        
        self.fps_limit = QSlider(Qt.Horizontal)
        self.fps_limit.setRange(15, 144)
        if self.config:
            val = self.config.get("fps_limit", 60)
            try:
                self.fps_limit.setValue(int(val))
            except:
                self.fps_limit.setValue(60)
            self.fps_limit.valueChanged.connect(lambda v: self.config.set("fps_limit", v))
        perf_form.addRow("Límite de FPS:", self.fps_limit)
        
        container_layout.addWidget(perf_group)
        
        audio_group = QGroupBox("Audio")
        audio_form = QFormLayout(audio_group)
        self.mute_audio = QCheckBox("Silenciar audio por defecto")
        if self.config:
            self.mute_audio.setChecked(self.config.get("mute", False))
            self.mute_audio.stateChanged.connect(lambda s: self.config.set("mute", s == 2))
        audio_form.addRow(self.mute_audio)
        container_layout.addWidget(audio_group)
        
        container_layout.addStretch()
        scroll.setWidget(container)
        self.layout.addWidget(scroll)

class AboutPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("", parent)
        
        for i in reversed(range(self.layout.count())): 
            item = self.layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)

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
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Trinity.svg")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setStyleSheet("background: transparent; margin-bottom: 5px;")
        card_layout.addWidget(icon_label)

        self.author_label = QLabel("ALEXANDER GOMEZ")

        self.author_label.setObjectName("author_name")
        self.author_label.setAlignment(Qt.AlignCenter)
        self.author_label.setStyleSheet("font-size: 32px; font-weight: 900; color: #007acc; background: transparent;")
        card_layout.addWidget(self.author_label)
        
        by_label = QLabel("GAMING OF DEMON")
        by_label.setStyleSheet("font-size: 13px; color: #555; font-weight: 800; letter-spacing: 5px; margin-bottom: 15px; background: transparent;")
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
        self.discord_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://discord.gg/xTdmDHfgZT")))
        card_layout.addWidget(self.discord_btn)

        self.layout.addWidget(self.card)

        footer = QLabel("v1.0.0 PRO EDITION • 2026")
        footer.setStyleSheet("color: #333; font-size: 10px; font-weight: bold; margin-top: 15px;")
        footer.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(footer)

        self.scroll_timer = QTimer(self)
        self.scroll_timer.setInterval(50)
        self.scroll_timer.timeout.connect(self._auto_scroll)
        self.scroll_pos = 0

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.scroll_timer.start)

        self.inner_scroll.verticalScrollBar().sliderPressed.connect(self._on_user_interaction)
        self.inner_scroll.verticalScrollBar().sliderMoved.connect(self._on_user_interaction)
        self.inner_scroll.verticalScrollBar().valueChanged.connect(self._on_value_changed)

    def showEvent(self, event):
        """Start auto-scroll when page becomes visible."""
        super().showEvent(event)
        self.scroll_pos = 0
        if hasattr(self, 'inner_scroll'):
            self.inner_scroll.verticalScrollBar().setValue(0)
        if hasattr(self, 'inactivity_timer'):
            self.inactivity_timer.start(6000)

    def hideEvent(self, event):
        """Stop all timers when page is hidden."""
        super().hideEvent(event)
        if hasattr(self, 'scroll_timer'):
            self.scroll_timer.stop()
        if hasattr(self, 'inactivity_timer'):
            self.inactivity_timer.stop()

    def _on_user_interaction(self):
        """User is manually scrolling."""
        if hasattr(self, 'scroll_timer'):
            self.scroll_timer.stop()
        if hasattr(self, 'inactivity_timer'):
            self.inactivity_timer.start(4000)

    def _on_value_changed(self, value):
        """Detect manual scroll wheel or keyboard interaction."""
        if value != self.scroll_pos:
            if hasattr(self, 'scroll_timer'):
                self.scroll_timer.stop()
            if hasattr(self, 'inactivity_timer'):
                self.inactivity_timer.start(4000)

    def _auto_scroll(self):
        if not hasattr(self, 'inner_scroll'):
            return
        v_bar = self.inner_scroll.verticalScrollBar()
        if self.scroll_pos < v_bar.maximum():
            self.scroll_pos += 1
            v_bar.setValue(self.scroll_pos)
        else:
            self.scroll_pos = -50
            v_bar.setValue(0)
            if hasattr(self, 'scroll_timer'):
                self.scroll_timer.stop()
            if hasattr(self, 'inactivity_timer'):
                self.inactivity_timer.start(4000)

    def update_accent_color(self, hex_color):
        """Updates the UI elements to match the new accent color."""
        if hasattr(self, 'shadow'):
            self.shadow.setColor(QColor(hex_color))
        if hasattr(self, 'author_label'):
            self.author_label.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {hex_color}; background: transparent;")
